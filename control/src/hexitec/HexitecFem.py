"""
HexitecFEM for Hexitec ODIN control.

Christian Angelsen, STFC Detector Systems Software Group, 2019.
"""

from __future__ import division
import numpy as np
# Required to convert str to bool:
import distutils.util

import time
from datetime import datetime
from datetime import timezone
import logging
import configparser
import psutil
from json.decoder import JSONDecodeError
import struct
import json

from RdmaUdp import *
from udpcore.UdpCore import *
from boardcfgstatus.BoardCfgStatus import *
from hexitec_vsr.VsrModule import VsrModule
import hexitec.ALL_RDMA_REGISTERS as HEX_REGISTERS

from socket import error as socket_error
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor
from concurrent import futures


class HexitecFem():
    """
    Hexitec Fem class. Represents a single FEM-II module.

    Controls and configures each FEM-II module ready for a DAQ via UDP.
    """

    # Thread executor used for functions handling rdma transactions
    thread_executor = futures.ThreadPoolExecutor(max_workers=1)

    vsr_base_address = 0x90

    HEX_ASCII_CODE = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                      0x41, 0x42, 0x43, 0x44, 0x45, 0x46]

    DAC_SCALE_FACTOR = 0.732

    TRIGGERINGOPTIONS = ["triggered", "none"]

    def __init__(self, parent, config):
        """
        Initialize the HexitecFem object.

        This constructor initializes the HexitecFem object.
        :param parent: Reference to adapter object
        :param config: dictionary of configuration settings
        """
        # Give access to parent class (Hexitec)
        self.parent = parent
        self.x10g_rdma = None

        # Construct path to hexitec installed config files
        self.control_config_path = self.parent.control_config_path

        # 10G RDMA IP addresses
        self.server_ctrl_ip = None
        self.server_ctrl_mac = None
        self.server_ctrl_ip = "10.0.1.1"
        self.camera_ctrl_ip = "10.0.1.100"
        self.server_ctrl_port = 61649
        self.camera_ctrl_port = 61648

        self.farm_mode_prepared = False
        self.farm_mode_file = self.control_config_path + config.get("farm_mode", None)

        self.number_frames = 10

        self.hardware_connected = False
        self.hardware_busy = False

        self.health = True

        # Variables supporting frames to duration conversion
        self.row_s1 = 1
        self.s1_sph = 1
        self.sph_s2 = 1
        self.frame_rate = 9118.87   # Corresponds to the above three settings
        self.duration = 1
        self.duration_enable = False
        self.duration_remaining = 0
        self.bias_level = 0
        self.gain_integer = -1
        self.gain_string = "high"
        self.adc1_delay = -1
        self.delay_sync_signals = -1
        self.vcal_on = -1
        self.vcal2_vcal1 = -1
        self.umid_value = -1
        self.vcal_value = -1

        self.vsrs_selected = 0
        self.vsr_addr_mapping = {1: 0x90, 2: 0x91, 3: 0x92, 4: 0x93, 5: 0x94, 6: 0x95}
        self.number_vsrs = len(self.vsr_addr_mapping.keys())
        self.broadcast_VSRs = None
        self.vsr_list = []
        self.vcal_enabled = 0

        # Acquisition completed, note completion timestamp
        self.acquisition_completed = False

        self.debug = False
        # Diagnostics:
        self.exception_triggered = False
        self.acquisition_duration = ""

        self.status_message = ""
        self.status_error = ""
        self.cancel_acquisition = False

        # 6 VSRs x 7 sensors each, 7 lists with sensor data
        self.ambient_list = [0, 0, 0, 0, 0, 0]
        self.humidity_list = [0, 0, 0, 0, 0, 0]
        self.asic1_list = [0, 0, 0, 0, 0, 0]
        self.asic2_list = [0, 0, 0, 0, 0, 0]
        self.adc_list = [0, 0, 0, 0, 0, 0]
        self.hv_list = [0, 0, 0, 0, 0, 0]
        self.sync_list = [0, 0, 0, 0, 0, 0]

        self.hv_bias_enabled = False
        self.system_initialised = False

        self.read_firmware_version = True
        self.firmware_date = "N/A"
        self.firmware_time = "N/A"
        self.firmware_version = "N/A"

        # Variables supporting handling of ini-style hexitec config file
        self.hexitec_config = self.control_config_path + "hexitec_unified_CSD__performance.ini"
        self.hexitec_parameters = {}

        self.acquire_start_time = ""
        self.acquire_stop_time = ""
        self.acquire_time = 0.0
        self.offsets_timestamp = "0"

        # Track history of errors
        self.errors_history = []
        timestamp = self.create_iso_timestamp()
        self.errors_history.append([timestamp, "Initialised OK."])
        self.last_message_timestamp = ''
        self.log_messages = [timestamp, "initialised OK"]

        self.environs_in_progress = False

        # Did Hardware finish sending data?
        self.all_data_sent = 0

        # Support hardware triggering
        self.start_trigger = False
        self.enable_trigger_mode = False
        self.enable_trigger_input = False
        self.triggering_mode = "none"
        self.triggering_frames = 10
        self.synchronisation_mode_enable = False

        param_tree_dict = {
            "diagnostics": {
                "acquire_start_time": (lambda: self.acquire_start_time, None),
                "acquire_stop_time": (lambda: self.acquire_stop_time, None),
                "acquire_time": (lambda: self.acquire_time, None),
            },
            "offsets_timestamp": (lambda: self.offsets_timestamp, None),
            "hv_bias_enabled": (lambda: self.hv_bias_enabled, None),
            "debug": (self.get_debug, self.set_debug),
            "all_data_sent": (lambda: self.all_data_sent, self.set_all_data_sent),
            "frame_rate": (lambda: self.frame_rate, None),
            "health": (lambda: self.health, None),
            "errors_history": (lambda: self.errors_history, None),
            'log_messages': (lambda: self.log_messages, None),
            'last_message_timestamp': (lambda: self.last_message_timestamp, self.get_log_messages),
            "status_message": (self._get_status_message, None),
            "status_error": (self._get_status_error, None),
            "number_frames": (self.get_number_frames, self.set_number_frames),
            "duration": (self.get_duration, self.set_duration),
            "duration_remaining": (lambda: self.duration_remaining, None),
            "hexitec_config": (lambda: self.hexitec_config, self.set_hexitec_config),
            "read_sensors": (None, self.read_sensors),
            "environs_in_progress": (lambda: self.environs_in_progress, None),
            "hardware_connected": (lambda: self.hardware_connected, None),
            "hardware_busy": (lambda: self.hardware_busy, None),
            "triggering": {
                "start_trigger": (lambda: self.start_trigger, self.set_start_trigger),
                "enable_trigger_mode": (lambda: self.enable_trigger_mode, self.set_enable_trigger_mode),
                "enable_trigger_input": (lambda: self.enable_trigger_input, self.set_enable_trigger_input),
                "triggering_mode": (lambda: self.triggering_mode, self.set_triggering_mode),
                "triggering_frames": (lambda: self.triggering_frames, self.set_triggering_frames)
            },
            "system_initialised": (lambda: self.system_initialised, None),
            "firmware_date": (lambda: self.firmware_date, None),
            "firmware_time": (lambda: self.firmware_time, None),
            "firmware_version": (lambda: self.firmware_version, None),
            "vsr_ambient_list": (lambda: self.ambient_list, None),
            "vsr_humidity_list": (lambda: self.humidity_list, None),
            "vsr_asic1_list": (lambda: self.asic1_list, None),
            "vsr_asic2_list": (lambda: self.asic2_list, None),
            "vsr_adc_list": (lambda: self.adc_list, None),
            "vsr_hv_list": (lambda: self.hv_list, None),
            "vcal_enabled": (lambda: self.vcal_enabled, None),
            "vsr_sync_list": (lambda: self.sync_list, None)
        }

        self.param_tree = ParameterTree(param_tree_dict)

        self.data_lane1 = None
        self.data_lane2 = None
        self.farm_mode_targets = None
        self.verify_parameters = True
        self.connect_only_once = True

    def load_farm_mode_json_parameters(self):
        """Load Farm Mode settings from file."""
        try:
            if not self.farm_mode_file:
                raise FileNotFoundError("File undefined")

            with open(self.farm_mode_file, "r") as f:
                config = json.load(f)
                self.camera_ctrl_ip = config.get("camera_ctrl_ip")
                self.camera_ctrl_mac = config.get("camera_ctrl_mac")
                self.server_ctrl_port = int(config.get("server_ctrl_port"))
                self.camera_ctrl_port = int(config.get("camera_ctrl_port"))
                self.control_interface = config.get("control_interface")
                self.control_qsfp_idx = int(config.get("control_qsfp_idx", 1))  # Not from .json
                self.control_lane = int(config.get("control_lane", 1))
                self.data1_interface = config.get("data1_interface")
                self.data1_lane = int(config.get("data1_lane", 2))
                self.data2_interface = config.get("data2_interface")
                self.data2_lane = int(config.get("data2_lane", 3))

                src_dst_port_int = (self.server_ctrl_port << 16) + self.camera_ctrl_port
                self.src_dst_port = src_dst_port_int

                self.farm_server_1_ip = config.get("farm_server_1_ip")
                self.farm_server_1_mac = config.get("farm_server_1_mac")
                self.farm_camera_1_ip = config.get("farm_camera_1_ip")
                self.farm_camera_1_mac = config.get("farm_camera_1_mac")
                self.farm_server_2_ip = config.get("farm_server_2_ip")
                self.farm_server_2_mac = config.get("farm_server_2_mac")
                self.farm_camera_2_ip = config.get("farm_camera_2_ip")
                self.farm_camera_2_mac = config.get("farm_camera_2_mac")
                # self.display_debugging(f"farm_camera_1_ip: {self.farm_camera_1_ip} farm_camera_2_ip: {self.farm_camera_2_ip}")

                self.farm_target_ip = config.get("farm_target_ip")
                self.farm_target_mac = config.get("farm_target_mac")
                self.farm_target_port = config.get("farm_target_port")
                # Farm mode parameters may contain one or more entries
                iface = self.control_interface
                self.server_ctrl_ip, self.server_ctrl_mac = self.extract_interface_parameters(iface)
                self.farm_target_ip = self.extract_string_parameters(self.farm_target_ip)
                self.farm_target_mac = self.extract_string_parameters(self.farm_target_mac)
                self.farm_target_port = self.extract_int_parameters(self.farm_target_port)
        except FileNotFoundError as e:
            raise HexitecFemError("Farm Mode: No Config File: ", str(e))
        except TypeError as e:
            raise HexitecFemError("Farm Mode: Config File: ", str(e))
        except JSONDecodeError as e:
            raise HexitecFemError("Farm Mode: Bad json: ", str(e))

    def extract_interface_parameters(self, iface):
        """Extract IP, Mac addresses from specified interface."""
        ip_address = None
        mac_address = None
        if_addrs = psutil.net_if_addrs()
        interfaces = if_addrs.keys()
        if iface not in interfaces:
            raise HexitecFemError(f"Unknown interface: '{iface}'!")
        # Sort through interface names, addresses
        for interface_name, interface_addresses in if_addrs.items():
            if iface in interface_name:
                for interface_param in interface_addresses:
                    if str(interface_param.family) == "AddressFamily.AF_INET":
                        ip_address = str(interface_param.address)
                    if str(interface_param.family) == "AddressFamily.AF_PACKET":
                        mac_address = str(interface_param.address)
        if ip_address is None:
            e = f"Control Interface '{iface}' couldn't parse IP from '{ip_address}';Check power?"
            raise ParameterTreeError(e)
        if mac_address is None:
            e = f"Control Interface '{iface}' couldn't parse MAC from '{mac_address}';Check power?"
            raise ParameterTreeError(e)
        return ip_address, mac_address

    def extract_string_parameters(self, param):
        """Extract one or more string parameters."""
        try:
            s = param.split(" ")
        except AttributeError:
            raise HexitecFemError(f"Undefined param '{param}'")
        return s

    def extract_int_parameters(self, param):
        """Extract one or more int parameters."""
        string_list = self.extract_string_parameters(param)
        int_list = []
        for index in string_list:
            int_list.append(int(index))
        return int_list

    def __del__(self):
        """Ensure rdma connection closed."""
        if self.x10g_rdma is not None:
            self.x10g_rdma.close()

    def prepare_farm_mode(self):
        """Load and verify farm mode parameters."""
        configOK = True
        try:
            self.load_farm_mode_json_parameters()
            # Avoid verification, if unit testing..
            if self.verify_parameters:
                iface = self.control_interface
                self.verify_farm_mode_parameters(iface)
            self.farm_mode_prepared = True
        except HexitecFemError as e:
            configOK = False
            self.flag_error("Prepare Farm Mode Error", str(e))
        return configOK

    def verify_farm_mode_parameters(self, iface):
        """Verify farm mode parameters correctly set."""
        self.server_ctrl_ip, self.server_ctrl_mac = self.extract_interface_parameters(iface)

        # Check Farm mode configuration not mismatched
        number_ips = len(self.farm_target_ip)
        number_macs = len(self.farm_target_mac)
        number_ports = len(self.farm_target_port)
        if (number_ips != number_macs) or (number_macs != number_ports):    # pragma: no cover
            e = f"Farm Mode: IP/MAC/port mismatch ({number_ips}/{number_macs}/{number_ports})"
            raise HexitecFemError(e)
        self.farm_mode_targets = number_ips

    def configure_camera_interfaces(self):
        """Configure IP, Mac and port parameters for detector's Control and Data interfaces."""
        Hex2x6CtrlRdma = RdmaUDP(local_ip=self.server_ctrl_ip, local_port=self.server_ctrl_port,
                                 rdma_ip=self.camera_ctrl_ip, rdma_port=self.camera_ctrl_port,
                                 multicast=True, debug=False)
        ctrl_lane = \
            UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name=self.control_interface,
                    qsfp_idx=self.control_qsfp_idx, lane=self.control_lane)

        self._set_status_message("Set Control params..")
        IOLoop.instance().call_later(2, self.configure_control_with_multicast,
                                     Hex2x6CtrlRdma, ctrl_lane)

    def configure_control_with_multicast(self, Hex2x6CtrlRdma, ctrl_lane):  # pragma: no cover
        """Configure Control link's parameters."""
        try:
            ctrl_lane.set_dst_mac(mac=self.server_ctrl_mac, response_check=False)
            time.sleep(0.001)
            ctrl_lane.set_dst_ip(ip=self.server_ctrl_ip, response_check=False)
            time.sleep(0.001)
            ctrl_lane.set_src_dst_port(port=self.src_dst_port, response_check=False)
            time.sleep(0.001)
            ctrl_lane.set_src_mac(mac=self.camera_ctrl_mac, response_check=False)
            time.sleep(0.001)
            ctrl_lane.set_src_ip(ip=self.camera_ctrl_ip, response_check=False)

            # Close multicast connection
            Hex2x6CtrlRdma.__del__()

            self._set_status_message("Setting Data Lane 1..")
            IOLoop.instance().call_later(2, self.setup_data_lane_1)
        except socket_error as e:
            self.hardware_connected = False
            self.hardware_busy = False
            self.flag_error("Setup Control", str(e))

    def setup_data_lane_1(self):    # pragma: no cover
        """Setup Data Lane 1's parameters."""
        try:
            # Connect with Control interface
            Hex2x6CtrlRdma = RdmaUDP(local_ip=self.server_ctrl_ip, local_port=self.server_ctrl_port,
                                     rdma_ip=self.camera_ctrl_ip, rdma_port=self.camera_ctrl_port,
                                     multicast=False, debug=False)
            ctrl_lane = \
                UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name=self.control_interface,
                        qsfp_idx=self.control_qsfp_idx, lane=self.control_lane)
            ctrl_lane.set_filtering(enable=True, response_check=True)
            time.sleep(0.001)
            ctrl_lane.set_arp_timeout_length()
            time.sleep(0.001)

            self.data_lane1 = \
                UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name=self.data1_interface,
                        qsfp_idx=1, lane=self.data1_lane)
            self._set_status_message("Setting Data Lane 2..")
            IOLoop.instance().call_later(2, self.setup_data_lane_2, Hex2x6CtrlRdma, ctrl_lane)
        except socket_error as e:
            self.hardware_connected = False
            self.hardware_busy = False
            self.flag_error("Setup Data Lane 1", str(e))

    def setup_data_lane_2(self, Hex2x6CtrlRdma, ctrl_lane):     # pragma: no cover
        """Setup Data Lane 2's parameters."""
        try:
            self.data_lane2 = \
                UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name=self.data2_interface,
                        qsfp_idx=1, lane=self.data2_lane)
            self._set_status_message("Configuring Farm Mode..")
            IOLoop.instance().call_later(2, self.setup_farm_mode, Hex2x6CtrlRdma, ctrl_lane)
        except socket_error as e:
            self.hardware_connected = False
            self.hardware_busy = False
            self.flag_error("Setup Data Lane 2", str(e))

    def setup_farm_mode(self, Hex2x6CtrlRdma, ctrl_lane):   # pragma: no cover
        """Configure data lanes for Farm Mode."""
        # Source = Camera, Destination: PC
        try:
            self.data_lane1.set_dst_ip(ip=self.farm_server_1_ip)
            time.sleep(0.001)
            self.data_lane1.set_dst_mac(mac=self.farm_server_1_mac)
            time.sleep(0.001)
            self.data_lane1.set_src_ip(ip=self.farm_camera_1_ip)
            time.sleep(0.001)
            self.data_lane1.set_src_mac(mac=self.farm_camera_1_mac)
            time.sleep(0.001)
            self.data_lane1.set_src_dst_port(port=self.src_dst_port)
            time.sleep(0.001)

            self.data_lane2.set_dst_ip(ip=self.farm_server_2_ip)
            time.sleep(0.001)
            self.data_lane2.set_dst_mac(mac=self.farm_server_2_mac)
            time.sleep(0.001)
            self.data_lane2.set_src_ip(ip=self.farm_camera_2_ip)
            time.sleep(0.001)
            self.data_lane2.set_src_mac(mac=self.farm_camera_2_mac)
            time.sleep(0.001)
            self.data_lane2.set_src_dst_port(port=self.src_dst_port)
            time.sleep(0.001)

            fr = self.parent.daq.get_adapter_config("fr")
            addresses, ports = self.extract_frame_receiver_interfaces(fr)

            # Generate MAC addresses
            macs = []
            for i in range(len(addresses)):
                if self.farm_server_1_ip == addresses[i]:
                    # Farm Server 1
                    mac = self.farm_server_1_mac
                elif self.farm_server_2_ip == addresses[i]:
                    # Farm Server 2
                    mac = self.farm_server_2_mac
                else:
                    self.flag_error(f"Farm Mode IP {addresses[i]} not in Farm Mode config")
                macs.append(mac)
            ips1, ips2, macs1, macs2, ports1, ports2 = self.determine_farm_mode_config(addresses, macs, ports, self.triggering_frames)

            lut_entries = len(ips1)
            self.farm_mode_targets = lut_entries * 2

            self.data_lane1.set_lut_mode_ip(ips1)
            self.data_lane2.set_lut_mode_ip(ips2)
            self.data_lane1.set_lut_mode_mac(macs1)
            self.data_lane2.set_lut_mode_mac(macs2)
            self.data_lane1.set_lut_mode_port(ports1)
            self.data_lane2.set_lut_mode_port(ports2)

            address = HEX_REGISTERS.HEXITEC_2X6_NOF_LUT_MODE_ENTRIES['addr']
            Hex2x6CtrlRdma.udp_rdma_write(address=address, data=lut_entries, burst_len=1)
            self.data_lane1.set_lut_mode()
            self.data_lane2.set_lut_mode()
            Hex2x6CtrlRdma.__del__()

            if self.connect_only_once:
                self.connect()
                # Power up the VSRs
                self.power_up_modules()
                self.connect_only_once = False
            else:
                self.initialise_system()
        except socket_error as e:
            self.hardware_connected = False
            self.hardware_busy = False
            self.flag_error("Farm Mode Config failed", str(e))

    def determine_farm_mode_config(self, ip_addresses, macs, ports, frames_per_trigger):
        """Determine Farm Mode configuration, based on Odin instances and frames per trigger"""
        lut_entries = frames_per_trigger * (len(ip_addresses) // 2)
        ip_lut1 = []
        ip_lut2 = []
        mac_lut1 = []
        mac_lut2 = []
        port_lut1 = []
        port_lut2 = []
        frame_count = 0
        current_instance = 0
        index = 0
        offset = 0
        while index < lut_entries:
            if (offset % 2) == 0:
                if (index % 2) == 0:  # Even
                    ip_lut1.append(ip_addresses[current_instance])
                    mac_lut1.append(macs[current_instance])
                    port_lut1.append(ports[current_instance])
                else:
                    ip_lut2.append(ip_addresses[current_instance+1])
                    mac_lut2.append(macs[current_instance+1])
                    port_lut2.append(ports[current_instance+1])
            else:
                if (index % 2) == 0:  # Even
                    ip_lut1.append(ip_addresses[current_instance+1])
                    mac_lut1.append(macs[current_instance+1])
                    port_lut1.append(ports[current_instance+1])
                else:
                    ip_lut2.append(ip_addresses[current_instance])
                    mac_lut2.append(macs[current_instance])
                    port_lut2.append(ports[current_instance])
            frame_count += 1
            if frame_count == frames_per_trigger:
                frame_count = 0
                current_instance += 2
                offset += 1
            index += 1
        return ip_lut1, ip_lut2, mac_lut1, mac_lut2, port_lut1, port_lut2

    def populate_lists(self, entries):
        """Spread entries of one list into 2 lists, of equal lengths.

        I.e. even length: [1, 2, 3, 4] -> [1, 3], [2, 4]
        or uneven length: [1, 2, 3] -> [1, 3, 2], [2, 1, 3].
        """
        number_entries = len(entries)
        original_number_entries = number_entries
        if number_entries % 2 == 1:
            number_entries = number_entries * 2
        lut1 = []
        lut2 = []
        for index in range(number_entries):
            i = index % original_number_entries
            if (index % 2) == 1:  # Odd
                lut2.append(entries[i])
            else:  # Even (includes 0..)
                lut1.append(entries[i])
        return lut1, lut2

    def extract_frame_receiver_interfaces(self, frame_receivers):
        """Extract frame receiver addresses and ports from the frame receivers list."""
        addresses = []
        ports = []
        for instance in frame_receivers:
            if instance is None:
                continue
            addresses = self.extract_entries_from_string(instance.get("rx_address_list", None), addresses)
            ports = self.extract_entries_from_string(instance.get("rx_ports", None), ports)
        # Convert ports from list of strings, to list of integers
        ports = list(map(int, ports))
        return addresses, ports

    def extract_entries_from_string(self, comma_separated_string, list_of_entries):
        """Extract entries from a comma separated string and append each entry to list of entries.

        For example: comma_separated_string: '10.0.2.1,10.0.1.1'
        is appended to list_of_entries, that becomes: ['10.0.2.1', '10.0.1.1']
        """
        if comma_separated_string is None:
            # This FR is not connected, return list unchanged
            return list_of_entries
        list_of_strings = comma_separated_string.split(",")
        for entry in list_of_strings:
            list_of_entries.append(entry.strip(" "))
        return list_of_entries

    def connect(self):
        """Set up hardware connection."""
        try:
            self.x10g_rdma = RdmaUDP(local_ip=self.server_ctrl_ip, local_port=self.server_ctrl_port,
                                     rdma_ip=self.camera_ctrl_ip, rdma_port=self.camera_ctrl_port,
                                     udptimeout=2, debug=False, uart_offset=0x0)
            self.broadcast_VSRs = \
                VsrModule(self.x10g_rdma, slot=0, init_time=0, addr_mapping=self.vsr_addr_mapping)
            self.vsr_list = []
            self.vsr_list.append(
                VsrModule(self.x10g_rdma, slot=1, init_time=0, addr_mapping=self.vsr_addr_mapping))
            self.vsr_list.append(
                VsrModule(self.x10g_rdma, slot=2, init_time=0, addr_mapping=self.vsr_addr_mapping))
            self.vsr_list.append(
                VsrModule(self.x10g_rdma, slot=3, init_time=0, addr_mapping=self.vsr_addr_mapping))
            self.vsr_list.append(
                VsrModule(self.x10g_rdma, slot=4, init_time=0, addr_mapping=self.vsr_addr_mapping))
            self.vsr_list.append(
                VsrModule(self.x10g_rdma, slot=5, init_time=0, addr_mapping=self.vsr_addr_mapping))
            self.vsr_list.append(
                VsrModule(self.x10g_rdma, slot=6, init_time=0, addr_mapping=self.vsr_addr_mapping))
        except socket_error as e:
            raise socket_error("Failed to setup Control connection: %s" % e)
        return

    def check_hardware_ready(self, action):
        """Helper function checking hardware connected and not busy.

        Raise Exception if hardware not connected, or hardware busy.
        """
        if self.hardware_connected is not True:
            error = f"Can't {action} without a connection"
            self.flag_error(error, "")
            raise ParameterTreeError(error)
        if self.hardware_busy:
            error = f"Can't {action}, Hardware busy"
            self.flag_error(error, "")
            raise ParameterTreeError(error)
        else:
            self._set_status_error("")

    def check_system_initialised(self, action):
        """Helper function checking system initialised.

        Raise Exception if system not initialised.
        """
        if self.system_initialised is not True:
            error = f"Can't {action}, system not initialised"
            self.flag_error(error, "")
            raise ParameterTreeError(error)
        else:
            self._set_status_error("")

    def environs(self, msg=None):
        """Readout environmental data if hardware connected and not busy."""
        self.check_hardware_ready("read sensors")
        IOLoop.instance().add_callback(self.read_sensors)

    @run_on_executor(executor='thread_executor')
    def read_sensors(self, msg=None):
        """Read environmental sensors and updates parameter tree with results."""
        try:
            self.hardware_busy = True
            self.environs_in_progress = True
            current_state = self.parent.software_state
            self.parent.software_state = "Environs"
            # Note once, when firmware was built
            if self.read_firmware_version:
                board_status = BoardCfgStatus(self.x10g_rdma,
                                              rdma_offset=rdma.get_id_offset(HEX_REGISTERS.IC_OFFSETS,
                                                                             'BOARD_BUILD_INFO_ID'))
                fw_version = board_status.get_fpga_fw_version()
                build_date = board_status.get_fpga_build_date()
                build_time = board_status.get_fpga_build_time()
                self.firmware_date = build_date
                self.firmware_time = build_time
                self.firmware_version = fw_version
                self.read_firmware_version = False

            for vsr in self.vsr_list:
                self.read_temperatures_humidity_values(vsr)
                self.read_pwr_voltages(vsr)  # pragma: no cover
        except HexitecFemError as e:
            self.flag_error("Failed to read sensors", str(e))
        except Exception as e:
            self.flag_error("Reading sensors failed", str(e))
        else:
            self.parent.software_state = current_state
            self._set_status_message("VSRs sensors read")
        self.environs_in_progress = False
        self.hardware_busy = False

    def disconnect(self):
        """Disconnect hardware connection."""
        # Close network socket without hardware interactions if leak fault detected
        if self.parent.leak_fault_counter > 0:
            # Ensure VSR connections exist
            if self.broadcast_VSRs is not None:
                self.broadcast_VSRs.set_leak_detector_fault(True)
            if (len(self.vsr_list) > 0):
                for vsr in self.vsr_list:
                    vsr.set_leak_detector_fault(True)
        self.connect_only_once = True
        del self.broadcast_VSRs
        del self.vsr_list[:]
        self.x10g_rdma.close()

    def cleanup(self):
        """Cleanup connection."""
        self.disconnect()

    def _get_status_message(self):
        return self.status_message

    def _set_status_message(self, message):
        self.status_message = message

    def _get_status_error(self):
        return self.status_error

    def _set_status_error(self, error):
        self.health = True if error == "" else False
        self.status_error = str(error)

    def set_duration_enable(self, duration_enable):
        """Set duration (enable) or number of frames (disable)."""
        self.duration_enable = duration_enable

    def get_number_frames(self):
        """Get number of frames."""
        return self.number_frames

    def set_number_frames(self, frames):
        """Set number of frames, initialise frame_rate if not set."""
        if self.frame_rate == 0:
            self.calculate_frame_rate()
        if self.number_frames != frames:
            self.number_frames = frames
            self.duration = self.number_frames / self.frame_rate
            self.parent.set_duration(self.duration)

    def get_duration(self):
        """Set acquisition duration."""
        return self.duration

    def set_duration(self, duration):
        """Set duration, calculate frames to acquire using frame rate."""
        if self.frame_rate == 0:
            self.calculate_frame_rate()
        self.duration = duration
        frames = self.duration * self.frame_rate
        # Ensure even number of frames
        if frames % 2:
            frames = self.parent.round_to_even(frames)
        self.number_frames = int(round(frames))

    def get_health(self):
        """Get FEM health status."""
        return self.health

    def connect_hardware(self, msg=None):
        """Establish Hardware connection."""
        try:
            if not self.farm_mode_prepared:
                self.parent.software_state = "Cold"
                return
            if self.hardware_connected:
                error = "Connection already established"
                self.flag_error(error, "")
                raise ParameterTreeError(error)
            else:
                self._set_status_error("")
            self.hardware_busy = True
            self.hardware_connected = True
            # Configure control, data lines unless already configured
            # - Insist Control interface configured on every connect
            if self.parent.cold_start:
                # Configure Control, Camera interfaces
                self.configure_camera_interfaces()
                self.parent.cold_start = True
            else:
                self.connect()
                # Power up the VSRs
                self.power_up_modules()
        except HexitecFemError as e:
            self.flag_error("Connection Error", str(e))
            self.hardware_connected = False
            self.hardware_busy = False
            raise ParameterTreeError(f"Connection Error: {e}")
        except socket.error as e:
            self.flag_error("Connection Socket Error", str(e))
            self._set_status_message("Is the camera powered?")
            self.hardware_connected = False
            self.hardware_busy = False
            raise ParameterTreeError(f"Connection Socket Error: {e}")

    def power_up_modules(self):
        """Power up and enable VSRs."""
        try:
            self.data_path_reset()
            self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL['addr'],
                                          data=0x0, burst_len=1)
            self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL['addr'],
                                          data=0x1, burst_len=1)

            self.hardware_connected = True
            self._set_status_message("Camera connected.")
            logging.debug("UDP connection established")
            # Power up VSRs
            success = self.broadcast_VSRs.enable_module()
            vsr_statuses = self.broadcast_VSRs._get_status(hv=False, all_vsrs=True)
            logging.debug("Power Status: {}".format(vsr_statuses))
            if not success:
                logging.debug("Power Status: {}".format(vsr_statuses))
                message = "Not all VSRs powered up"
                error = "{}".format(vsr_statuses)
                self.flag_error(message, error)
                return

            # Switch HV (Power Board) on
            success = self.broadcast_VSRs.hv_enable()
            hv_statuses = self.broadcast_VSRs._get_status(hv=True, all_vsrs=True)
            logging.debug("HV Status: {}".format(hv_statuses))
            if not success:
                logging.debug("HV Status: {}".format(hv_statuses))
                message = "VSRs' HV didn't turn on"
                error = "{}".format(hv_statuses)
                self.flag_error(message, error)
                return
            powering_delay = 10
            logging.debug("VSRs enabled; Waiting {} seconds".format(powering_delay))
            self._set_status_message("Waiting {} seconds (VSRs booting)".format(powering_delay))
            IOLoop.instance().call_later(powering_delay, self.cam_connect_completed)
        except socket_error as e:
            self.flag_error("Power up modules Error", str(e))
            self.hardware_connected = False
            self.hardware_busy = False
            # End of the line, cannot raise exception beyond scheduled callback function
            self.parent.leak_fault_counter = 1
            self.disconnect()

    def initialise_hardware(self, msg=None):
        """Initialise sensors, load enables, etc to initialise both VSR boards."""
        self.check_hardware_ready("initialise hardware")
        try:
            self.hardware_busy = True
            self.parent.software_state = "Initialising"
            # Seup Farm Mode (again), then initialise
            self.setup_data_lane_1()
        except Exception as e:
            error = "Camera initialisation failed"
            self.flag_error(error, str(e))
            self.hardware_busy = False
            raise ParameterTreeError(f"{error}: {str(e)}")

    def collect_data(self, msg=None):
        """Acquire data from camera."""
        try:
            self.hardware_busy = True
            self._set_status_message("Acquiring data..")
            self.acquire_data()
        except Exception as e:
            error = "Data acquisition failed"
            self.flag_error(error, str(e))
            self.hardware_busy = False
            # End of the line, cannot raise exception beyond scheduled callback function

    def disconnect_hardware(self, msg=None):
        """Disconnect camera."""
        try:
            if self.hardware_connected is False:
                raise HexitecFemError("No connection to disconnect")
            else:
                self._set_status_error("")
            self.hardware_connected = False
            self._set_status_message("Disconnecting camera..")
            self.cam_disconnect()
            self._set_status_message("Camera disconnected")
            self.parent.software_state = "Disconnected"
            # Disconnecting hardware automatically disables HV
            self.hv_bias_enabled = False
        except HexitecFemError as e:
            self.flag_error("Failed to disconnect", str(e))
        except Exception as e:
            self.flag_error("Disconnection failed", str(e))

    def set_debug(self, debug):
        """Set debug messages on or off."""
        self.debug = debug

    def set_all_data_sent(self, all_data_sent):
        """Set whether all data has been sent (hardware simulation)."""
        self.all_data_sent = all_data_sent

    def get_debug(self):
        """Get debug messages status."""
        return self.debug

    def cam_connect_completed(self):
        """Complete VSRs boot up."""
        logging.debug("Modules Enabled")
        self._set_status_message("VSRs booted")
        self.hardware_busy = False
        self.parent.daq.commit_configuration()
        self.parent.software_state = "Idle"

    def cam_disconnect(self):
        """Send commands to disconnect camera."""
        self.hardware_connected = False
        try:
            # Only disable VSRs if detector is (still) powered
            if self.parent.leak_fault_counter == 0:
                self.vsr_list[0].disable_vsr(0xFF)
                logging.debug("Modules Disabled")
            self.disconnect()
            logging.debug("Camera is Disconnected")
        except struct.error as e:
            self.flag_error("Couldn't disconnect camera", str(e))
            self.parent.leak_fault_counter = 1
            self.disconnect()
        except socket_error as e:
            self.flag_error("Unable to disconnect camera", str(e))
            raise HexitecFemError(e)
        except AttributeError as e:
            error = "Unable to disconnect camera: No active connection"
            self.flag_error(error, str(e))
            raise HexitecFemError("%s; %s" % (e, "No active connection"))
        self.system_initialised = False

    def acquire_data(self):
        """Acquire data, poll fem for completion."""
        try:
            logging.info("Initiate Data Capture")
            self.acquire_time = 0
            self.acquire_start_time = self.create_iso_timestamp()
            self.acquire_stop_time = "0"

            logging.debug("Reset frame number")
            self.frame_reset_to_zero()

            logging.debug("Reset path and clear buffers")
            self.data_path_reset()

            logging.debug(f"Set number frames to: {self.number_frames}")
            self.set_nof_frames(self.number_frames)

            logging.debug("Enable data")
            self.data_en(enable=True)
            time.sleep(0.2)

            # Stop data flow (free acquisition mode), reset setting if number of frames mode
            logging.debug("Disable data")
            self.data_en(enable=False)

            IOLoop.instance().call_later(0.1, self.check_acquire_finished)
        except Exception as e:
            error = "Failed to start acquire_data"
            self.flag_error(error, str(e))
            self.hardware_busy = False
            self.parent.daq.in_progress = False
            raise ParameterTreeError(error) from None

    def check_acquire_finished(self):
        """Check whether all data transferred, until completed or cancelled by user."""
        try:
            # Stop if user clicked the Disconnect button
            if (self.cancel_acquisition):
                logging.debug("Acquire cancellation initiated")
                self.acquire_data_completed()
                return
            else:
                status = \
                    self.x10g_rdma.udp_rdma_read(
                        address=HEX_REGISTERS.HEXITEC_2X6_HEADER_STATUS['addr'],
                        burst_len=1)[0]
                # 0 during data transmission, 65536 when completed
                self.all_data_sent = (status & 65536)
                if self.all_data_sent == 0:
                    IOLoop.instance().call_later(0.1, self.check_acquire_finished)
                    return
                else:
                    self.acquire_data_completed()
                    return
        except HexitecFemError as e:
            self.flag_error("Failed to collect data", str(e))
        except Exception as e:
            self.flag_error("Data acquisition failed", str(e))
        self.hardware_busy = False

        # Acquisition interrupted
        self.acquisition_completed = True

    def acquire_data_completed(self):
        """Reset variables and read out Firmware monitors post data transfer."""
        self.acquire_stop_time = self.create_iso_timestamp()

        if self.cancel_acquisition:
            logging.info("Cancelling Acquisition..")
            for vsr in self.vsr_list:
                vsr.disable_vsr()
            # Issue abort, assert register
            self.abort_data_acquisition(enable=True)
            # Deassert data enable
            self.data_en(enable=False)
            # Deassert abort
            self.abort_data_acquisition(enable=False)
            #
            self.data_path_reset()
            logging.info("Acquisition cancelled")
            # Reset variables
            self.cancel_acquisition = False
            self.hardware_busy = False
            self.acquisition_completed = True
            self._set_status_message("Acquire cancelled")
            self.system_initialised = False
            return

        # Workout exact duration of fem data transmission:
        start_ = datetime.fromisoformat(self.acquire_start_time)
        stop_ = datetime.fromisoformat(self.acquire_stop_time)
        self.acquire_time = (stop_ - start_).total_seconds()

        logging.debug("Sending {} frames took {} seconds".format(str(self.number_frames),
                                                                 self.acquire_time))
        duration = "Requested {} frames, sending took {} seconds".format(self.number_frames,
                                                                         self.acquire_time)
        self._set_status_message(duration)
        # Save duration to separate parameter tree entry:
        self.acquisition_duration = duration

        logging.debug("Acquisition Completed, enable signal cleared")

        # Fem finished sending data/monitoring info, clear hardware busy
        self.hardware_busy = False

        # Wrap up by updating GUI

        # Acquisition completed, note completion
        self.acquisition_completed = True
        self.all_data_sent = 0

    def run_collect_offsets(self):
        """Run collect offsets sequence if connected and hardware not busy."""
        self.check_hardware_ready("collect offsets")
        self.check_system_initialised("collect offsets")
        self.collect_offsets()

    @run_on_executor(executor='thread_executor')
    def collect_offsets(self):
        """Run collect offsets sequence.

        Stop state machine, gathers offsets, calculats average picture, re-starts state machine.
        """
        # beginning = time.time()
        try:
            self.hardware_busy = True
            current_state = self.parent.software_state
            self.parent.software_state = "Offsets"

            # 2. Stop the state machine
            self.stop_sm()
            # 3. Set register 0x24 to 0x22
            self.set_dc_controls(True, False)
            # 4. Start the state machine
            self.start_sm()
            # 5. Wait > 8182 * frame time (~1 second, 9118.87Hz)
            self.await_dc_captured()
            # 6. Stop state machine
            self.stop_sm()
            # (7. Setting Register 0x24 to 0x28 - Redundant)
            # 8. Start state machine
            self.start_sm()
            # Ensure VCAL remains on:
            self.clr_dc_controls(False, False)

            self._set_status_message("Offsets collections operation completed.")
            self.parent.software_state = current_state
            # Timestamp when offsets collected
            self.offsets_timestamp = self.create_iso_timestamp()
            # ending = time.time()
            # self.display_debugging(f"offsets took: {ending-beginning}")
        except Exception as e:
            self.flag_error("Failed to collect offsets", str(e))
        self.hardware_busy = False

    def stop_sm(self):
        """Stop the state machine in VSRs."""
        for vsr in self.vsr_list:
            # Stop trigger state machine - Otherwise VSRs collect dark currents too quickly
            vsr.stop_trigger_sm()
            vsr.disable_sm()

    def set_dc_controls(self, capt_avg_pict, spectroscopic_mode_en):
        """Set DC control(s) in all VSRs."""
        for vsr in self.vsr_list:
            vsr.set_dc_control_bits(capt_avg_pict, self.vcal_enabled, spectroscopic_mode_en)

    def clr_dc_controls(self, capt_avg_pict, spectroscopic_mode_en):
        """Clear DC control(s) in all VSRs."""
        for vsr in self.vsr_list:
            vsr.clr_dc_control_bits(capt_avg_pict, self.vcal_enabled, spectroscopic_mode_en)

    def start_sm(self):
        """Start the state machine in VSRs."""
        for vsr in self.vsr_list:
            vsr.enable_sm()
            # Restart trigger state machine
            vsr.start_trigger_sm()

    def await_dc_captured(self):
        """Wait for the Dark Correction frames to be collected."""
        expected_duration = 8192 / self.frame_rate
        timeout = (expected_duration * 1.2) + 1
        poll_beginning = time.time()
        self._set_status_message("Collecting dark images..")
        dc_ready = False
        while not dc_ready:
            dc_statuses = self.check_dc_statuses()
            dc_ready = self.are_dc_ready(dc_statuses)
            if self.debug:   # pragma: no cover
                logging.debug("Register 0x89: {0}, Done? {1} Timing: {2:2.5} s".format(
                    dc_statuses, dc_ready, time.time() - poll_beginning))
            if time.time() - poll_beginning > timeout:
                raise HexitecFemError("Dark images timed out. R.89: {}".format(dc_statuses))

    def check_dc_statuses(self):
        """Check Register 89 status in all VSRs."""
        replies = []
        for vsr in self.vsr_list:
            replies.append(vsr.read_pll_status())
        return replies

    def are_dc_ready(self, dc_statuses):
        """Check whether bit 0: 'Capture DC ready' set."""
        all_dc_ready = True
        for status in dc_statuses:
            dc_ready = status & 1
            if not dc_ready:
                all_dc_ready = False
        return all_dc_ready

    def load_pwr_cal_read_enables(self, vsr):
        """Load power, calibration and read enables - optionally from hexitec file."""
        if vsr.addr not in self.vsr_addr_mapping.values():
            raise HexitecFemError("Unknown VSR address! (%s)" % vsr.addr)
        # Address 0x90 = vsr1, 0x91 = vsr2, .. , 0x95 = vsr6. Therefore:
        vsr_num = vsr.addr - 143

        logging.debug("Loading Power, Cal and Read Enables")
        # logging.debug("Column Read Enable")

        # # Column Read Enable ASIC1 (Reg 0x61) - checked 2
        # asic1_col_read_enable = self._extract_80_bits("ColumnEn_", vsr_num, 1, "Channel")
        # enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
        #                     0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # # self.load_enables_settings(vsr, 0x36, 0x31, asic1_col_read_enable, enables_defaults)

        # # Column Read Enable ASIC2 (Reg 0xC2) - checked 1
        # asic2_col_read_enable = self._extract_80_bits("ColumnEn_", vsr_num, 2, "Channel")
        # enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
        #                     0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # # self.load_enables_settings(vsr, 0x43, 0x32, asic2_col_read_enable, enables_defaults)

        logging.debug("Column Power Enable")

        # # Column Power Enable ASIC1 (Reg 0x4D) - checked 2
        # asic1_col_power_enable = self._extract_80_bits("ColumnPwr", vsr_num, 1, "Channel")
        # enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
        #                     0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # # self.load_enables_settings(vsr, 0x34, 0x44, asic1_col_power_enable, enables_defaults)

        # # Column Power Enable ASIC2 (Reg 0xAE) - checked 1
        # asic2_col_power_enable = self._extract_80_bits("ColumnPwr", vsr_num, 2, "Channel")
        # enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
        #                     0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # # self.load_enables_settings(vsr, 0x41, 0x45, asic2_col_power_enable, enables_defaults)

        logging.debug("Column Calibration Enable")
        # Column Calibrate Enable ASIC1 (Reg 0x57) - checked 3
        asic1_col_cal_enable = self._extract_80_bits("ColumnCal", vsr_num, 1, "Channel")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        if asic1_col_cal_enable[0] > -1:
            # vsr.debug = True
            vsr.set_column_calibration_mask(asic1_col_cal_enable, asic=1)
        else:
            vsr.set_column_calibration_mask(enables_defaults, asic=1)

        # Column Calibrate Enable ASIC2 (Reg 0xB8) - checked 3
        asic2_col_cal_enable = self._extract_80_bits("ColumnCal", vsr_num, 2, "Channel")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        if asic2_col_cal_enable[0] > -1:
            vsr.set_column_calibration_mask(asic2_col_cal_enable, asic=2)
        else:
            vsr.set_column_calibration_mask(enables_defaults, asic=2)

        logging.debug("Row Read Enable")

        # # Row Read Enable ASIC1 (Reg 0x43) - chcked 5
        # asic1_row_enable = self._extract_80_bits("RowEn_", vsr_num, 1, "Block")
        # enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
        #                     0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # # self.load_enables_settings(vsr, 0x34, 0x33, asic1_row_enable, enables_defaults)

        # # Row Read Enable ASIC2 (Reg 0xA4) - checked 4
        # asic2_row_enable = self._extract_80_bits("RowEn_", vsr_num, 2, "Block")
        # enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
        #                     0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # # self.load_enables_settings(vsr, 0x41, 0x34, asic2_row_enable, enables_defaults)

        logging.debug("Row Power Enable")

        # # Row Power Enable ASIC1 (Reg 0x2F) - checked 5
        # asic1_row_power_enable = self._extract_80_bits("RowPwr", vsr_num, 1, "Block")
        # enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
        #                     0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # # self.load_enables_settings(vsr, 0x32, 0x46, asic1_row_power_enable, enables_defaults)

        # # Row Power Enable ASIC2 (Reg 0x90) - chcked 4
        # asic2_row_power_enable = self._extract_80_bits("RowPwr", vsr_num, 2, "Block")
        # enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
        #                     0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # # self.load_enables_settings(vsr, 0x39, 0x30, asic2_row_power_enable, enables_defaults)

        logging.debug("Row Calibration Enable")

        # Row Calibrate Enable ASIC1 (Reg 0x39) - chcked 6
        asic1_row_cal_enable = self._extract_80_bits("RowCal", vsr_num, 1, "Block")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        if asic1_row_cal_enable[0] > -1:
            vsr.set_row_calibration_mask(asic1_row_cal_enable, asic=1)
        else:
            vsr.set_row_calibration_mask(enables_defaults, asic=1)

        # Row Calibrate Enable ASIC2 (Reg 0x9A) - checked 6
        asic2_row_cal_enable = self._extract_80_bits("RowCal", vsr_num, 2, "Block")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        if asic2_row_cal_enable[0] > -1:
            vsr.set_row_calibration_mask(asic2_row_cal_enable, asic=2)
        else:
            vsr.set_row_calibration_mask(enables_defaults, asic=2)

        logging.debug("Power, Cal and Read Enables have been loaded")

    @run_on_executor(executor='thread_executor')
    def initialise_system(self):
        """Configure in full all VSRs.

        Initialise, load enables, set up state machine, write to DAC and enable ADCs.
        """
        try:
            expected_duration = 8192 / self.frame_rate
            timeout = (expected_duration * 1.2) + 1
            self.hardware_busy = True
            # Reset sync status
            for vsr in self.vsr_list:
                index = vsr.addr - self.vsr_base_address
                self.sync_list[index] = 0
                # Stop trigger state machine - Otherwise VSRs will not initialise/updated
                vsr.stop_trigger_sm()

            for vsr in self.vsr_list:
                vsr_id = vsr.addr-143
                logging.debug(" --- Initialising VSR: 0x{0:X} ---".format(vsr_id))
                self._set_status_message("Initialising VSR{}..".format(vsr_id))
                vsr.enable_vcal(self.vcal_enabled)
                self.initialise_vsr(vsr)
                # Check PLLs locked
                bPolling = True
                time_taken = 0
                beginning = time.time()
                while bPolling:
                    pll_lock = vsr.read_pll_status()
                    if pll_lock & 1:
                        bPolling = False
                    else:
                        time.sleep(0.1)
                        time_taken += 0.1
                    if time.time() - beginning > timeout:
                        logging.error("VSR{0:X} R.89 took long: {1:2.5} s".format(
                            vsr_id, time_taken))
                        raise HexitecFemError(f"VSR{vsr_id} Timed out awaiting DC Capture Ready")

                logging.debug("VSR{0:X} DC Capture ready took: {1} s".format(
                    vsr_id, round(time_taken, 3)))

            logging.debug("LVDS Training")
            self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                          data=0x10, burst_len=1, comment=" ")  # EN_TRAINING
            time.sleep(0.2)
            self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                          data=0x00, burst_len=1, comment=" ")  # Disable training

            lock_status = self.x10g_rdma.udp_rdma_read(address=0x3e8, burst_len=self.number_vsrs)
            for vsr in self.vsr_list:
                if lock_status[vsr.slot-1] == 255:
                    logging.debug(f"VSR{vsr.slot} lock_status: {lock_status[vsr.slot-1]}")
                else:
                    logging.error(f"VSR{vsr.slot} lock_status: {lock_status[vsr.slot-1]}")

            vsr_status_addr = HEX_REGISTERS.HEXITEC_2X6_VSR0_STATUS['addr']
            for vsr in self.vsr_list:
                index = vsr.addr - self.vsr_base_address
                locked = self.x10g_rdma.udp_rdma_read(vsr_status_addr, burst_len=1,
                                                      comment=f"VSR {index} status register")[0]
                if (locked == 0xFF):
                    logging.debug("VSR{0} Locked (0x{1:X})".format(index+1, locked))
                else:
                    message = "VSR{0} Error".format(index+1)
                    error = "Incomplete lock (0x{0:X})".format(locked)
                    self.flag_error(message, error)
                vsr_status_addr += 4
                # Record sync status
                self.sync_list[index] = locked

            logging.debug("Disabling training for vsr(s)..")
            for vsr in self.vsr_list:
                vsr._disable_training()

            self.start_trigger = True

            self.configure_hardware_triggering()

            self.x10g_rdma.udp_rdma_write(address=0x1c, data=0x1, burst_len=1)
            logging.debug("fpga state machine enabled")

            self._set_status_message("Initialisation completed. VSRs configured.")
            self.parent.software_state = "Ready"
            self.system_initialised = True
        except HexitecFemError as e:
            self.flag_error("Failed to initialise camera", str(e))
        except OSError as e:
            self.flag_error("Detector initialisation failed", str(e))
            self.parent.leak_fault_counter = 1
            self.hardware_connected = True
        except Exception as e:
            self.flag_error("Camera initialisation failed", str(e))
        self.hardware_busy = False

    def initialise_vsr(self, vsr):
        """Initialise a VSR."""
        # Original aSpect VSR config recipe split into sections of block quotes
        """
        90	42	01	10	;Select external Clock
        90	42	07	03	;Enable PLLs
        90	42	02	01	;LowByte Row S1
        """
        # Select external Clock, Enable PLLs: Set by vsr.initialise()
        # Config settings in VsrModule - Calling vsr.initialise() writes settings to FPGA registers
        vsr.set_rows1_clock(self.row_s1)
        """
        90	42	04	01	;S1Sph
        90	42	05	06	;SphS2
        90	42	09	02	;ADC Clock Delay    (self.adc1_delay)
        90	42	0E	0A	;FVAL/LVAL Delay    (adc_signal_delay)
        90	42	1B	08	;SM wait Clock Row
        90	42	14	01	;Start SM on falling edge
        90	42	01	20	;Enable LVDS Interface
        """
        vsr.set_s1sph(self.s1_sph)
        vsr.set_sphs2(self.sph_s2)
        vsr.set_gain(self.gain_string)
        if self.adc1_delay > -1:
            vsr.set_adc_clock_delay(self.adc1_delay)
        if self.delay_sync_signals > -1:
            vsr.set_adc_signal_delay(self.delay_sync_signals)
        # Start SM on falling edge - Value never changes (See: vsr.start_sm_on_writing_edge())
        # vsr.set_sm_row_wait_clock(0x08) - Never changes
        # Enable LVD interface - Value never changes (See: vsr.assert_serial_iface_rst)

        """
        90	44	61	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Column Read En
        90	44	4D	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Column PWR En
        90	44	57	00	00	00	00	00	00	00	00	00	00	;Column Cal En
        90	44	43	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Row Read En
        90	44	2F	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Row PWR En
        90	44	39	00	00	00	00	00	00	00	00	00	00	;Row Cal En
        90	54	01	FF	0F	FF	05	55	00	00	08	E8	;Write DAC
        """
        self.load_pwr_cal_read_enables(vsr)

        self.write_dac_values(vsr)
        """
        90	55	02	;Disable ADC/Enable DAC
        90	43	01	01	;Disable SM
        90	42	01	01	;Enable SM
        90	55	03	;Enable ADC/Enable DAC
        90	53	16	09	;Write ADC Register
        """
        # Default values never change
        """
        90	40	24	22	;Disable Vcal/Capture Avg Picture
        90	40	24	28	;Disable Vcal/En DC spectroscopic mode
        90	42	01	80	;Enable Training
        90	42	18	01	;Low Byte SM Vcal Clock
        90	43	24	20	;Enable Vcal
        90	42	24	20	;Disable Vcal
        """
        # Only Low Byte SM Vcal Clock changes
        if self.vcal2_vcal1 > -1:
            vsr.set_sm_vcal_clock(self.vcal2_vcal1)

        logging.debug("Writing config to VSR..")
        vsr.initialise()

    def configure_hardware_triggering(self):
        """Configures hardware triggering options."""
        try:
            for vsr in self.vsr_list:
                vsr.set_trigger_mode_number_frames(self.triggering_frames)
                vsr.write_trigger_mode_number_frames()

                if self.enable_trigger_mode:
                    vsr.enable_trigger_mode_trigger_two_and_three()
                else:
                    vsr.disable_trigger_mode_trigger_two_and_three()

                if self.enable_trigger_input:
                    vsr.enable_trigger_input_two_and_three()
                else:
                    vsr.disable_trigger_input_two_and_three()

                if self.start_trigger:
                    vsr.start_trigger_sm()
                else:
                    vsr.stop_trigger_sm()
        except Exception as e:
            self.flag_error("Configure hardware triggering Error", str(e))

    def display_debugging(self, message):  # pragma: no cover
        timestamp = self.create_iso_timestamp()
        # Append to errors_history list, nested list of timestamp, error message
        self.errors_history.append([timestamp, message])

    def write_dac_values(self, vsr):
        """Update DAC values, provided by hexitec file."""
        logging.debug("Updating DAC values")
        if self.umid_value > -1:
            vsr.set_dac_umid(self.umid_value)
        if self.vcal_value > -1:
            vsr.set_dac_vcal(self.vcal_value)

    def calculate_frame_rate(self):
        """Calculate variables to determine frame rate (See ASICTimingRateDefault.xlsx)."""
        # Calculate RowReadClks
        ADC_Clk = 21250000          # B2
        ASIC_Clk1 = ADC_Clk * 2     # B3 = B2 * 2
        ASIC_Clk2 = 1 / ASIC_Clk1   # B4 = 1 / B3
        Rows = 80                   # B6; Hard coded yes?
        Columns = 20                # B7; Hard coded too?
        WaitCol = 1                 # B9; Hard coded too?
        WaitRow = 8                 # B10
        # self.row_s1                 # B12 from hexitecVSR file
        # self.s1_sph                 # B13 from file
        # self.sph_s2                 # B14 from file

        # B16 = ((B7 + B9 + B12 + B13 + B14) * 2) + 10
        RowReadClks = ((Columns + WaitCol + self.row_s1 + self.s1_sph + self.sph_s2) * 2) + 10
        # B18 = B6 * B16 + 4 + (B10 * 2)
        frameReadClks = (Rows * RowReadClks) + 4 + (WaitRow * 2)

        # B20 = (B18 * 3) + 2) * (B4 / 3)
        frame_time = ((frameReadClks * 3) + 2) * (ASIC_Clk2 / 3)
        # B21 = 1 / B20
        frame_rate = 1 / frame_time

        self.frame_rate = frame_rate
        if self.duration_enable:
            # With duration enabled, recalculate number of frames in case clocks changed
            self.set_duration(self.duration)
            self.parent.set_number_frames(self.number_frames)

    def read_pwr_voltages(self, vsr):
        """Read and convert power data into voltages."""
        if vsr.addr not in self.vsr_addr_mapping.values():
            raise HexitecFemError("HV: Invalid VSR address(0x{0:02X})".format(vsr.addr))
        index = vsr.addr - self.vsr_base_address
        if (0 <= index <= self.number_vsrs-1):
            self.hv_list[index] = vsr.get_power_sensors()

    def read_temperatures_humidity_values(self, vsr):
        """Read and convert sensor data into temperatures and humidity values."""
        if vsr.addr not in self.vsr_addr_mapping.values():
            raise HexitecFemError("Sensors: Invalid VSR address(0x{0:02X})".format(vsr.addr))
        sensors_values = vsr._get_env_sensors()

        index = vsr.addr - self.vsr_base_address
        if (0 <= index <= self.number_vsrs-1):
            self.ambient_list[index] = float(sensors_values[0])
            self.humidity_list[index] = float(sensors_values[1])
            self.asic1_list[index] = float(sensors_values[2])
            self.asic2_list[index] = float(sensors_values[3])
            self.adc_list[index] = float(sensors_values[4])

    def set_hexitec_config(self, filename):
        """Check whether file exists, load parameters from file."""
        self.parent.daq.check_daq_acquiring_data("hexitec config file")
        # Use existing filename if none supplied
        if len(filename) > 0:
            filename = self.control_config_path + filename
            try:
                with open(filename, 'r') as f:  # noqa: F841
                    pass
                self.hexitec_config = filename
                logging.debug("hexitec_config: '%s'" % (self.hexitec_config))
            except IOError as e:
                self.flag_error("Cannot open provided hexitec file", str(e))
                return

        try:
            logging.debug("Loading INI file settings..")
            # Read INI file contents, parse key/value pairs into hexitec_parameters argument
            self.read_ini_file(self.hexitec_config, self.hexitec_parameters, debug=False)

            # Recalculate frame rate
            row_s1 = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Row -> S1',
                                           bit_range=14)
            if row_s1 > -1:
                self.row_s1 = row_s1

            s1_sph = self._extract_integer(self.hexitec_parameters, 'Control-Settings/S1 -> Sph',
                                           bit_range=6)
            if s1_sph > -1:
                self.s1_sph = s1_sph

            sph_s2 = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Sph -> S2',
                                           bit_range=6)
            if sph_s2 > -1:
                self.sph_s2 = sph_s2

            bias_level = self._extract_integer(self.hexitec_parameters,
                                               'Control-Settings/HV_Bias', bit_range=15)
            if bias_level > -1:
                self.bias_level = bias_level

            vsrs_selected = self._extract_integer(self.hexitec_parameters,
                                                  'Control-Settings/VSRS_selected', bit_range=6)
            if vsrs_selected > -1:
                self.vsrs_selected = vsrs_selected
                self.populate_vsr_addr_mapping(self.vsrs_selected)

            self.gain_integer = \
                self._extract_integer(self.hexitec_parameters, 'Control-Settings/Gain', bit_range=1)
            if self.gain_integer > -1:
                if self.gain_integer == 0:
                    self.gain_string = "high"
                else:
                    self.gain_string = "low"
            self.adc1_delay = self._extract_integer(
                self.hexitec_parameters, 'Control-Settings/ADC1 Delay', bit_range=2)
            self.delay_sync_signals = \
                self._extract_integer(self.hexitec_parameters,
                                      'Control-Settings/delay sync signals', bit_range=8)
            self.vcal_on = \
                self._extract_integer(self.hexitec_parameters, 'Control-Settings/vcal_enabled',
                                      bit_range=1)
            if self.vcal_on > -1:
                if self.vcal_on == 0:
                    self.vcal_enabled = False
                else:
                    self.vcal_enabled = True
            self.vcal2_vcal1 = self._extract_integer(
                self.hexitec_parameters, 'Control-Settings/VCAL2 -> VCAL1', bit_range=15)
            self.umid_value = self._extract_exponential(self.hexitec_parameters,
                                                        'Control-Settings/Uref_mid', bit_range=12)
            self.vcal_value = self._extract_float(self.hexitec_parameters, 'Control-Settings/VCAL')
            self.calculate_frame_rate()
        except HexitecFemError as e:
            self.flag_error("INI File Key Error", str(e))

    def populate_vsr_addr_mapping(self, vsrs_selected):
        """Populate VSRs mapping according to ini file entry."""
        self.vsr_addr_mapping = {}
        vsr_number = 1
        for index in range(6):
            if (vsrs_selected >> index) & 1:
                self.vsr_addr_mapping[vsr_number] = 0x90+index
                vsr_number += 1
        # Returning mapping for debugging purposes only, not necessary
        return self.vsr_addr_mapping

    def set_start_trigger(self, start_trigger):
        self.start_trigger = start_trigger

    def set_enable_trigger_mode(self, enable_trigger_mode):
        self.enable_trigger_mode = enable_trigger_mode

    def set_enable_trigger_input(self, enable_trigger_input):
        self.enable_trigger_input = enable_trigger_input

    def set_triggering_mode(self, triggering_mode):
        """Sets the triggering mode.

        :param triggering_mode: 'triggered' or 'none'
        """
        self.parent.daq.check_daq_acquiring_data("trigger mode")
        triggering_mode = triggering_mode.lower()
        if (triggering_mode not in self.TRIGGERINGOPTIONS):
            raise ParameterTreeError("Must be one of: triggered or none")

        if triggering_mode == "none":
            self.enable_trigger_input = False
            self.enable_trigger_mode = False
            # TODO Restore this line:
            self.parent.daq._set_max_frames_received(0)
            # self.parent.daq._set_max_frames_received(self.triggering_frames)
            self.parent.daq.pass_pixel_spectra = True
        elif triggering_mode == "triggered":
            self.enable_trigger_input = True
            self.enable_trigger_mode = True
            # Number of Frames to near infinity (>5 days of acquisition)
            self.parent.set_number_frames(4294967290)
            self.parent.set_duration_enable(False)
            # TODO set_max_frames_received redundant for EPAC configuration?
            self.parent.daq._set_max_frames_received(0)
            self.parent.daq.pass_pixel_spectra = False
        # Triggering mode changed, must reinitialise system
        self.system_initialised = False
        self.triggering_mode = triggering_mode

    def set_triggering_frames(self, triggering_frames):
        """Sets the number of hardware frames when running in triggering mode.

        :param triggering_frames: Number of frames to trigger on.
        """
        self.parent.daq.check_daq_acquiring_data("trigger frames")
        if isinstance(triggering_frames, int):
            self.triggering_frames = triggering_frames
            # TODO set_max_frames_received redundant for EPAC configuration?
            self.parent.daq._set_max_frames_received(0)
        else:
            raise ParameterTreeError("Not an integer!")
        # Triggering mode changed, must reinitialise system
        self.system_initialised = False

    def convert_string_exponential_to_integer(self, exponent):
        """Convert aspect format to fit dac format.

        Aspect's exponent format looks like: 1,003000E+2
        Convert to float (eg: 100.3), rounding to nearest
        int before scaling to fit DAC range.
        """
        number_string = str(exponent)
        number_string = number_string.replace(",", ".")
        number_float = float(number_string)
        number_int = int(round(number_float))
        return number_int

    def _extract_exponential(self, parameter_dict, descriptor, bit_range):
        """Extract exponential descriptor from parameter_dict, check it's within bit_range."""
        valid_range = [0, 1 << bit_range]
        setting = -1
        try:
            unscaled_setting = parameter_dict[descriptor]
            scaled_setting = self.convert_string_exponential_to_integer(unscaled_setting)
            if scaled_setting >= valid_range[0] and scaled_setting <= valid_range[1]:
                setting = int(scaled_setting // self.DAC_SCALE_FACTOR)
            else:
                logging.error("Error parsing %s, got: %s (scaled: % s) but valid range: %s-%s" %
                              (descriptor, unscaled_setting, scaled_setting, valid_range[0],
                               valid_range[1]))
                setting = -1
        except KeyError:
            raise HexitecFemError("ERROR: No '%s' Key defined!" % descriptor)
        return setting

    def convert_aspect_float_to_dac_value(self, number_float):
        """Convert aspect float format to fit dac format.

        Convert float (eg: 1.3V) to mV (*1000), scale to fit DAC range
        before rounding to nearest int.
        """
        milli_volts = number_float * 1000
        number_scaled = int(round(milli_volts // self.DAC_SCALE_FACTOR))
        return number_scaled

    def _extract_float(self, parameter_dict, descriptor):
        """Extract descriptor from parameter_dict, check within 0.0 - 3.0 (hardcoded) range."""
        valid_range = [0.0, 3.0]
        setting = -1
        try:
            setting = float(parameter_dict[descriptor])
            if setting >= valid_range[0] and setting <= valid_range[1]:
                # Convert from volts to DAQ format
                setting = self.convert_aspect_float_to_dac_value(setting)
            else:
                logging.error("Error parsing float %s, got: %s but valid range: %s-%s" %
                              (descriptor, setting, valid_range[0], valid_range[1]))
                setting = -1
        except KeyError:
            raise HexitecFemError("Missing Key: '%s'" % descriptor)
        return setting

    def _extract_integer(self, parameter_dict, descriptor, bit_range):
        """Extract integer descriptor from parameter_dict, check it's within bit_range."""
        valid_range = [0, 1 << bit_range]
        setting = -1
        try:
            setting = int(parameter_dict[descriptor])
            if setting >= valid_range[0] and setting <= valid_range[1]:
                pass
            else:
                error = "Error parsing parameter %s, got: %s but valid range: %s-%s" % \
                        (descriptor, setting, valid_range[0], valid_range[1])
                logging.error(error)
                self.flag_error(error)
                setting = -1
        except KeyError:
            raise HexitecFemError("Missing Key: '%s'" % descriptor)
        return setting

    def _extract_boolean(self, parameter_dict, descriptor):
        """Extract boolean of descriptor from parameter_dict.

        True values: y, yes, t, true, on and 1.
        False values: n, no, f, false, off and 0.
        """
        try:
            parameter = parameter_dict[descriptor]
            setting = bool(distutils.util.strtobool(parameter))
        except ValueError:
            logging.error("ERROR: Invalid choice for %s!" % descriptor)
            raise HexitecFemError("ERROR: Invalid choice for %s!" % descriptor)
        except KeyError:
            raise HexitecFemError("Missing Key: '%s'" % descriptor)
        return setting

    def _extract_80_bits(self, param, vsr, asic, channel_or_block):  # noqa: C901
        """Extract 80 bits from four (20 bit) channels, assembling one ASIC's row/column."""
        # vsr = 1
        # asic = 1
        # param = "ColumnEn_"
        # channel_or_block = "Channel"
        # Example Column variable: 'Sensor-Config_V1_S1/ColumnEn_1stChannel'
        # Examples Row variable:   'Sensor-Config_V1_S1/RowPwr4thBlock'

        string_list = [-1]

        key = 'Sensor-Config_V%s_S%s/%s1st%s' % (vsr, asic, param, channel_or_block)
        try:
            first_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return string_list

        key = 'Sensor-Config_V%s_S%s/%s2nd%s' % (vsr, asic, param, channel_or_block)
        try:
            second_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return string_list

        key = 'Sensor-Config_V%s_S%s/%s3rd%s' % (vsr, asic, param, channel_or_block)
        try:
            third_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return string_list

        key = 'Sensor-Config_V%s_S%s/%s4th%s' % (vsr, asic, param, channel_or_block)
        try:
            fourth_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return string_list

        entirety = first_channel + second_channel + third_channel + fourth_channel
        # Convert string to bytes (to support Python 3)
        entirety = entirety.encode("utf-8")
        # Pixels appear in 8 bit reverse order, reverse bit order accordingly
        # More info: https://docs.scipy.org/doc/numpy/user/basics.byteswapping.html
        big_end_arr = np.ndarray(shape=(10,), dtype='>i8', buffer=entirety)
        rev_order = big_end_arr.byteswap()
        entirety = rev_order.tobytes()

        # Turn string of 80 bits into list of 10 strings
        byte_list = []
        for index in range(0, len(entirety), 8):
            byte_list.append(entirety[index:index + 8])

        # Convert strings into 8 byte integers
        string_list = []
        for binary in byte_list:
            int_byte = int(binary, 2)
            string_list.append(int_byte)

        return string_list

    def extract_channel_data(self, parameter_dict, key):
        """Extract value of key from parameters_dict's dictionary."""
        channel = parameter_dict[key]
        if len(channel) != 20:
            logging.error("Invalid length (%s != 20) detected in key: %s" % (len(channel), key))
            raise HexitecFemError("Invalid length of value in '%s'" % key)
        return channel

    def convert_to_aspect_format(self, value):
        """Convert integer to Aspect's hexadecimal notation e.g. 31 (0x1F) -> 0x31, 0x46."""
        hex_string = "{:02x}".format(value)
        high_string = hex_string[0]
        low_string = hex_string[1]
        high_int = int(high_string, 16)
        low_int = int(low_string, 16)
        high_encoded = self.HEX_ASCII_CODE[high_int]
        low_encoded = self.HEX_ASCII_CODE[low_int]
        return high_encoded, low_encoded

    def read_ini_file(self, filename, parameter_dict, debug=False):
        """Read filename, parse case sensitive keys decoded as strings into parameter_dict."""
        parser = configparser.ConfigParser()
        # Maintain case-sensitivity:
        parser.optionxform = str
        parser.read(filename)
        for section in parser.sections():
            for key, value in parser.items(section):
                parameter_dict[section + "/" + key] = value.strip("\"")

    def translate_to_normal_hex(self, value):
        """Translate Aspect encoding into 0-F equivalent scale."""
        if value not in self.HEX_ASCII_CODE:
            raise HexitecFemError("Invalid Hexadecimal value {0:X}".format(value))
        if value < 0x3A:
            value -= 0x30
        else:
            value -= 0x37
        return value

    def convert_hv_to_hex(self, hv_value):
        """Convert HV voltage into hexadecimal value."""
        return int((hv_value / 1250) * 0xFFF)

    def convert_bias_to_dac_values(self, hv):
        """Convert bias level to DAC formatted values.

        I.e. 21 V -> 0x0041 (0x30, 0x30, 0x34, 0x31)
        """
        hv_hex = self.convert_hv_to_hex(hv)
        hv_hex_msb = hv_hex >> 8
        hv_hex_lsb = hv_hex & 0xFF
        hv_msb = self.convert_to_aspect_format(hv_hex_msb)
        hv_lsb = self.convert_to_aspect_format(hv_hex_lsb)
        return hv_msb, hv_lsb

    def hv_on(self):
        """Switch HV on."""
        self.check_hardware_ready("switch HV on")
        logging.debug("Going to set HV bias to -{} volts".format(self.bias_level))
        hv_msb, hv_lsb = self.convert_bias_to_dac_values(self.bias_level)
        # Can call hv_on function on any VSR object
        self.vsr_list[0].hv_on(hv_msb, hv_lsb)
        self.hv_bias_enabled = True
        self._set_status_message(f"HV bias set to -{self.bias_level} V")
        logging.debug("HV now ON")

    def hv_off(self):
        """Switch HV off."""
        self.check_hardware_ready("switch HV off")
        logging.debug("Disable: [0xE2]")
        # Can call hv_off function on any VSR object
        self.vsr_list[0].hv_off()
        self._set_status_message("HV turned off")
        self.hv_bias_enabled = False
        logging.debug("HV now OFF")

    def reset_error(self):
        """Reset error message."""
        self._set_status_error("")
        self._set_status_message("")
        self.parent.software_state = "Cleared"

    def flag_error(self, message, e=None):
        """Place software into error state, unless already Interlocked."""
        error_message = "{}".format(message)
        if e:
            error_message += ": {}".format(e)
        self._set_status_error(error_message)
        logging.error(error_message)
        if self.parent.software_state != "Interlocked":
            self.parent.software_state = "Error"
        timestamp = self.create_iso_timestamp()
        # Append to errors_history list, nested list of timestamp, error message
        self.errors_history.append([timestamp, error_message])

    def create_iso_timestamp(self):
        """Returns an ISO formatted timestamp of now."""
        return datetime.now(timezone.utc).astimezone().isoformat()

    def get_log_messages(self, last_message_timestamp):
        """This method gets the log messages that are appended to the log message deque by the
        log function, and adds them to the log_messages variable. If a last message timestamp is
        provided, it will only get the subsequent log messages if there are any, otherwise it will
        get all of the messages from the deque.
        """
        logs = []
        if self.last_message_timestamp != "":
            # Display any new message
            for index, (timestamp, log_message) in enumerate(self.errors_history):
                if timestamp > last_message_timestamp:
                    logs = self.errors_history[index:]
                    break
        else:
            logs = self.errors_history
            self.last_message_timestamp = self.create_iso_timestamp()

        self.log_messages = [(str(timestamp), log_message) for timestamp, log_message in logs]

    def set_bit(self, register, field):
        reg_value = int(self.x10g_rdma.udp_rdma_read(register['addr'])[0])
        ctrl_reg = rdma.set_field(register, field, reg_value, 1)
        self.x10g_rdma.udp_rdma_write(register['addr'], ctrl_reg)

    def reset_bit(self, register, field):
        reg_value = int(self.x10g_rdma.udp_rdma_read(register['addr'])[0])
        ctrl_reg = rdma.clr_field(register, field, reg_value)
        self.x10g_rdma.udp_rdma_write(register['addr'], ctrl_reg)

    def data_path_reset(self):
        """Take Kintex data path out of reset."""
        self.reset_bit(HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL, "HEXITEC_RST")
        self.set_bit(HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL, "HEXITEC_RST")

    def frame_reset_to_zero(self):
        """Reset Firmware frame number to 0."""
        self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_FRAME_PRELOAD_LOWER['addr'],
                                      data=0x0, burst_len=1)
        self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_FRAME_PRELOAD_UPPER['addr'],
                                      data=0x0, burst_len=1)
        self.set_bit(HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL, "FRAME_COUNTER_LOAD")
        self.reset_bit(HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL, "FRAME_COUNTER_LOAD")

    def set_nof_frames(self, number_frames):
        """Set number of frames in Firmware."""
        # Frame limited mode
        self.set_bit(HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL, "ACQ_NOF_FRAMES_EN")
        self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_ACQ_NOF_FRAMES_LOWER['addr'],
                                      data=number_frames, burst_len=1)

    def data_en(self, enable=True):
        if enable:
            self.set_bit(HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL, "DATA_EN")
        else:
            self.reset_bit(HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL, "DATA_EN")

    def abort_data_acquisition(self, enable=True):
        """Abort hexitec data acquisition.

        enable=True: assert the abort register, i.e. abort
        enable=False: de-assert the abort register
        """
        if enable:
            self.set_bit(HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL, "HEXITEC_ACQ_ABORT")
        else:
            self.reset_bit(HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL, "HEXITEC_ACQ_ABORT")


class HexitecFemError(Exception):   # pragma: no cover
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass
