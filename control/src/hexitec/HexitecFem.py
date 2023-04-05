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
import logging
import configparser
import os

# # # from hexitec.test_ui.RdmaUDP import RdmaUDP
# # from hexitec.RdmaUDP import RdmaUDP     # Satisfy tox
from hexitec.RDMA_REGISTERS import HEXITEC_2X6_VSR_DATA_CTRL, HEXITEC_2X6_VSR0_STATUS
from hexitec.RdmaUdp import RdmaUDP
from hexitec.VsrModule import VsrModule

from socket import error as socket_error
from odin.adapters.parameter_tree import ParameterTree

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

    SEND_REG_VALUE = 0x40   # Verified to work with F/W UART
    READ_REG_VALUE = 0x41   # Verified to work with F/W UART
    SET_REG_BIT = 0x42      # Tolerated in collect_offsets
    CLR_REG_BIT = 0x43      # Not verified, tolerated in: enable_adc, "Enable Vcal", collect_offsets
    SEND_REG_BURST = 0x44   # Avoid - fills up UART (FIFO?)
    READ_PWR_VOLT = 0x50    # Not used
    WRITE_REG_VAL = 0x53    # Avoid
    WRITE_DAC_VAL = 0x54    # Tolerated in: write_dac_values
    CTRL_ADC_DAC = 0x55     # Tolerated twice in: enable_adc

    # Define timestamp format
    DATE_FORMAT = '%Y%m%d_%H%M%S.%f'

    UART_MAX_RETRIES = 15001

    def __init__(self, parent,
                 server_ctrl_ip_addr='10.0.2.2', camera_ctrl_ip_addr='10.0.2.1',
                 server_data_ip_addr='10.0.4.2', camera_data_ip_addr='10.0.4.1'):
        """
        Initialize the HexitecFem object.

        This constructor initializes the HexitecFem object.
        :param parent: Reference to adapter object
        :param server_ctrl_ip_addr: PC interface for control path
        :param camera_ctrl_ip_addr: FEM interface for control path
        :param server_data_ip_addr: PC interface for data path
        :param camera_data_ip_addr: FEM interface for data path
        """
        # Give access to parent class (Hexitec)
        self.parent = parent
        self.x10g_rdma = None

        # 10G RDMA IP addresses
        self.server_ctrl_ip_addr = server_ctrl_ip_addr
        self.camera_ctrl_ip_addr = camera_ctrl_ip_addr

        self.number_frames = 10

        self.hardware_connected = False
        self.hardware_busy = False
        self.ignore_busy = False

        self.health = True

        # Construct path to hexitec source code
        cwd = os.getcwd()
        index = cwd.rfind("control")
        self.base_path = cwd[:index]

        # Variables supporting frames to duration conversion
        self.row_s1 = 135
        self.s1_sph = 1
        self.sph_s2 = 5
        self.frame_rate = 1589.34   # Corresponds to the above three settings
        self.duration = 1
        self.duration_enabled = False
        self.duration_remaining = 0

        self.bias_level = 0

        self.vsrs_selected = 0
        self.vsr_addr_mapping = {1: 0x90, 2: 0x91, 3: 0x92, 4: 0x93, 5: 0x94, 6: 0x95}
        self.broadcast_VSRs = None
        self.vsr_list = []

        # Acquisition completed, note completion timestamp
        self.acquisition_completed = False

        self.debug = False
        # Diagnostics:
        self.exception_triggered = False
        self.successful_reads = 0
        self.acquisition_duration = ""

        self.status_message = ""
        self.status_error = ""
        self.stop_acquisition = False

        # 6 VSRs x 7 sensors each, 7 lists with sensor data
        self.ambient_list = [0, 0, 0, 0, 0, 0]
        self.humidity_list = [0, 0, 0, 0, 0, 0]
        self.asic1_list = [0, 0, 0, 0, 0, 0]
        self.asic2_list = [0, 0, 0, 0, 0, 0]
        self.adc_list = [0, 0, 0, 0, 0, 0]
        self.hv_list = [0, 0, 0, 0, 0, 0]
        self.sync_list = [0, 0, 0, 0, 0, 0]

        self.hv_bias_enabled = False

        self.read_firmware_version = True
        self.firmware_date = "N/A"
        self.firmware_time = "N/A"

        # Variables supporting handling of ini-style hexitec config file
        self.hexitec_config = self.base_path + "control/config/hexitec_unified_CSD__performance.ini"
        self.hexitec_parameters = {}

        self.acquire_start_time = ""
        self.acquire_stop_time = ""
        self.acquire_time = 0.0
        self.acquire_timestamp = 0
        self.offsets_timestamp = 0

        # Track history of errors
        self.errors_history = []
        timestamp = self.create_timestamp()
        self.errors_history.append([timestamp, "Initialised OK."])
        self.last_message_timestamp = ''
        self.log_messages = [timestamp, "initialised OK"]

        self.environs_in_progress = False

        # Simulate (for now) whether Hardware finished sending data
        self.all_data_sent = 0

        param_tree_dict = {
            "diagnostics": {
                "successful_reads": (lambda: self.successful_reads, None),
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
            'last_message_timestamp': (lambda: self.last_message_timestamp, self.get_log_messsages),
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
            "firmware_date": (lambda: self.firmware_date, None),
            "firmware_time": (lambda: self.firmware_time, None),
            "vsr_ambient_list": (lambda: self.ambient_list, None),
            "vsr_humidity_list": (lambda: self.humidity_list, None),
            "vsr_asic1_list": (lambda: self.asic1_list, None),
            "vsr_asic2_list": (lambda: self.asic2_list, None),
            "vsr_adc_list": (lambda: self.adc_list, None),
            "vsr_hv_list": (lambda: self.hv_list, None),
            "vsr_sync_list": (lambda: self.sync_list, None)
        }
        self.waited = 0.0

        self.param_tree = ParameterTree(param_tree_dict)
        # Track any readback inaccurate value(s)
        self.error_list = []
        self.error_count = 0

    def __del__(self):
        """Ensure rdma connection closed."""
        if self.x10g_rdma is not None:
            self.x10g_rdma.close()

    def connect(self, bDebug=False):
        """Set up hardware connection."""
        try:
            self.x10g_rdma = RdmaUDP(local_ip=self.server_ctrl_ip_addr, local_port=61649,
                                     rdma_ip=self.camera_ctrl_ip_addr, rdma_port=61648, debug=False)
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

    @run_on_executor(executor='thread_executor')
    def read_sensors(self, msg=None):
        """Read environmental sensors and updates parameter tree with results."""
        try:
            # TODO: Implement 2x6 version
            # Note once, when firmware was built
            # if self.read_firmware_version:
            #     fw_date = self.x10g_rdma.read(0x8008, burst_len=1, comment='FIRMWARE DATE')
            #     fw_time = self.x10g_rdma.read(0x800C, burst_len=1, comment='FIRMWARE TIME')
            #     fw_date = fw_date[0]
            #     fw_time = fw_time[0]
            #     fw_time = "{0:06X}".format(fw_time)
            #     fw_date = "{0:08X}".format(fw_date)
            #     year = fw_date[0:4]
            #     month = fw_date[4:6]
            #     day = fw_date[6:8]
            #     self.firmware_date = "{0:.2}/{1:.2}/{2:.4}".format(day, month, year)
            #     self.firmware_time = "{0:.2}:{1:.2}:{2:.4}".format(fw_time[0:2], fw_time[2:4],
            #                                                        fw_time[4:6])
            #     self.read_firmware_version = False
            beginning = time.time()
            self.environs_in_progress = True
            self.parent.software_state = "Environs"
            for vsr in self.vsr_list:
                self.read_temperatures_humidity_values(vsr)
                self.read_pwr_voltages(vsr)  # pragma: no cover
            ending = time.time()
            print(" Environmental data took: {}".format(ending - beginning))
        except HexitecFemError as e:
            self.flag_error("Failed to read sensors", str(e))
        except Exception as e:
            self.flag_error("Reading sensors failed", str(e))
        else:
            self.environs_in_progress = False
            self.parent.software_state = "Idle"
            self._set_status_message("VSRs sensors read")

    def disconnect(self):
        """Disconnect hardware connection."""
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

    def set_duration_enable(self, duration_enabled):
        """Set duration (enable) or number of frames (disable)."""
        self.duration_enabled = duration_enabled

    def get_number_frames(self):
        """Get number of frames."""
        return self.number_frames

    def set_number_frames(self, frames):
        """Set number of frames, initialise frame_rate if not set."""
        if self.frame_rate == 0:
            self.calculate_frame_rate()
        # print("\n\tfem.set_number_frames({}) > number_frames {} duration {}\n".format(
        #     frames, self.number_frames, self.number_frames / self.frame_rate))
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
        # print("\n\tfem.set_duration({}) frames {}\n".format(
        #     duration, self.duration * self.frame_rate))
        self.duration = duration
        frames = self.duration * self.frame_rate
        self.number_frames = int(round(frames))

    def get_health(self):
        """Get FEM health status."""
        return self.health

    # # TODO: Still need IOLoop call if sensor polling is scrapped?
    # def _start_polling(self):
    #     IOLoop.instance().add_callback(self.poll_sensors)   # Not polling sensors

    # # TODO: redundant ?
    # def poll_sensors(self):
    #     """Poll hardware while connected but not busy initialising, collecting offsets, etc."""
    #     # if self.hardware_connected and (self.hardware_busy is False):
    #     #     self.read_sensors()
    #     #     print(" * poll_sensors() not reading sensors *")
    #     IOLoop.instance().call_later(3.0, self.poll_sensors)

    def connect_hardware(self, msg=None):
        """Establish Hardware connection."""
        try:
            if self.hardware_connected:
                raise HexitecFemError("Connection already established")
            else:
                self._set_status_error("")
            self.hardware_busy = True
            self.power_up_modules()
        except HexitecFemError as e:
            self.flag_error("Error", str(e))
            self._set_status_message("Is the camera powered?")
        except Exception as e:
            self.flag_error("Camera connection", str(e))

    def power_up_modules(self):
        """Power up and enable VSRs."""
        try:
            self.connect()
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
            # TODO Tie-in rechecking against vsrs_selected?!
            # self.x10g_rdma.enable_all_vsrs()
            # expected_value = self.vsrs_selected
            # read_value = self.x10g_rdma.power_status()
            # # Ensure selected VSR(s) were switched on
            # read_value = read_value & expected_value
            # if (read_value == expected_value):
            #     logging.debug("Power OK: 0x{0:08X}".format(read_value))
            # else:
            #     message = "Not all VSRs powered up"
            #     error = "Expected 0x{0:02X}, got 0x{1:02X}".format(expected_value, read_value)
            #     self.flag_error(message, error)

            # Switch HV on
            success = self.broadcast_VSRs.hv_enable()
            hv_statuses = self.broadcast_VSRs._get_status(hv=True, all_vsrs=True)
            logging.debug("HV Status: 0x{}".format(hv_statuses))
            if not success:
                logging.debug("HV Status: {}".format(hv_statuses))
                message = "VSRs' HV didn't turn on"
                error = "{}".format(hv_statuses)
                self.flag_error(message, error)
                return
            # TODO tie-in with check-in against vsrs_selected?!
            # self.x10g_rdma.enable_all_hvs()
            # expected_value = (self.vsrs_selected << 8) | self.vsrs_selected
            # read_value = self.x10g_rdma.power_status()
            # read_value = read_value & expected_value
            # if (read_value == expected_value):
            #     logging.debug("HV OK: 0x{0:08X}".format(read_value))
            # else:
            #     message = "Not all VSRs' HV on"
            #     error = "Expected 0x{0:02X}, got 0x{1:02X}".format(expected_value, read_value)
            #     self.flag_error(message, error)
            # print("\n FAKE initialisation\n")
            powering_delay = 10  # 1
            logging.debug("VSRs enabled; Waiting {} seconds".format(powering_delay))
            self._set_status_message("Waiting {} seconds (VSRs booting)".format(powering_delay))
            IOLoop.instance().call_later(powering_delay, self.cam_connect)
        except socket_error as e:
            self.hardware_connected = False
            self.hardware_busy = False
            raise HexitecFemError(e)

    def initialise_hardware(self, msg=None):
        """Initialise sensors, load enables, etc to initialise both VSR boards."""
        try:
            if self.hardware_connected is not True:
                raise HexitecFemError("No connection established")
            if self.hardware_busy:
                raise HexitecFemError("Can't initialise, Hardware busy")
            else:
                self._set_status_error("")
            self.hardware_busy = True
            self.parent.software_state = "Initialising"
            self.initialise_system()
        except HexitecFemError as e:
            self.flag_error("Failed to initialise camera", str(e))
        except Exception as e:
            error = "Camera initialisation failed"
            self.flag_error(error, str(e))

    def collect_data(self, msg=None):
        """Acquire data from camera."""
        try:
            if self.hardware_connected is not True:
                raise HexitecFemError("No connection established")
            if self.hardware_busy and (self.ignore_busy is False):
                raise HexitecFemError("Hardware sensors busy initialising")
            else:
                self._set_status_error("")
            # Clear ignore_busy if set
            if self.ignore_busy:
                self.ignore_busy = False
            self.hardware_busy = True
            self.parent.software_state = "Acquiring"
            self._set_status_message("Acquiring data..")
            self.acquire_data()
        except HexitecFemError as e:
            self.flag_error("Failed to collect data", str(e))
        except Exception as e:
            self.flag_error("Data collection failed", str(e))

    def disconnect_hardware(self, msg=None):
        """Disconnect camera."""
        try:
            if self.hardware_connected is False:
                raise HexitecFemError("No connection to disconnect")
            else:
                self._set_status_error("")
            # Stop acquisition if it's hung
            if self.hardware_busy:
                self.stop_acquisition = True
            self.hardware_connected = False
            self._set_status_message("Disconnecting camera..")
            self.cam_disconnect()
            self._set_status_message("Camera disconnected")
            self.parent.software_state = "Disconnected"
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
        # print("\n self.all_data_sent ({}) = all_data_sent ({})\n".format(
        #     self.all_data_sent, all_data_sent))

    def get_debug(self):
        """Get debug messages status."""
        return self.debug

    def send_cmd(self, cmd):
        """Send a command string to the microcontroller."""
        # TODO Address hack of: Add start, end characters at respective ends of cmd:
        cmd.insert(0, 0x23)
        cmd.append(0xd)
        # print(" *FEM Send to UART: {}  ({})".format(' '.join("0x{0:02X}".format(x) for x in cmd), cmd))
        self.x10g_rdma.uart_write(cmd, cmd_no=0)

    def read_response(self):
        """Read a VSR's microcontroller response, passed on by the FEM."""
        counter = 0
        rx_pkt_done = 0
        while not rx_pkt_done:
            _, _, _, _, _, rx_pkt_done = self.x10g_rdma.read_uart_status()
            # uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done \
            #     = self.x10g_rdma.read_uart_status()
            # if (counter % 10) == 0:
            #     msg = " FEM {0:05} UART: {1:08X} tx_buff_full: {2:0X} tx_buff_empty: {3:0X}".format(
            #         counter, uart_status, tx_buff_full, tx_buff_empty)
            #     print("{0} rx_buff_full: {1:0X} rx_buff_empty: {2:0X} rx_pkt_done: {3:0X}".format(
            #         msg, rx_buff_full, rx_buff_empty, rx_pkt_done))
            counter += 1
            if counter == HexitecFem.UART_MAX_RETRIES:
                logging.error("read_response, UART timed out")
                raise HexitecFemError("UART read timed out")
        response = self.x10g_rdma.uart_read(cmd_no=0)
        # print("R: {}.  ({}). {}".format(
        #     ' '.join("0x{0:02X}".format(x) for x in response), response, counter))
        return response

    def cam_connect(self):
        """Send init command(s) to VSRs."""
        try:
            self.send_cmd([0xFF, 0xE3])
            logging.debug("Init modules (Sent 0xE3)")
            self._set_status_message("Waiting 5 seconds (VSRs initialising)")
            IOLoop.instance().call_later(5, self.cam_connect_completed)
            # IOLoop.instance().call_later(0.5, self.cam_connect_completed)
        except socket_error as e:
            self.hardware_connected = False
            self.hardware_busy = False
            self.flag_error("Failed to initialise modules", str(e))

    def cam_connect_completed(self):
        """Complete VSRs boot up."""
        logging.debug("Modules Enabled")
        self._set_status_message("VSRs booted")
        self.hardware_busy = False
        self.parent.software_state = "Idle"
        # # Start polling thread (connect successfully set up)
        # if len(self.status_error) == 0:
        #     self._start_polling()

    def cam_disconnect(self):
        """Send commands to disconnect camera."""
        self.hardware_connected = False
        try:
            self.send_cmd([0xFF, 0xE2])
            logging.debug("Modules Disabled")
            self.disconnect()
            logging.debug("Camera is Disconnected")
        except socket_error as e:
            self.flag_error("Unable to disconnect camera", str(e))
            raise HexitecFemError(e)
        except AttributeError as e:
            error = "Unable to disconnect camera: No active connection"
            self.flag_error(error, str(e))
            raise HexitecFemError("%s; %s" % (e, "No active connection"))

    def print_firmware_info(self):  # pragma: no cover
        """Print info on the aSpect firmware loaded.

        0x80: F/W customer ID
        0x81: F/W Project ID
        0x82: F/W Version ID.
        """
        print("__________F/W Customer, Project, and Version IDs__________")
        for index in range(3):
            (vsr2, vsr1) = self.debug_register(0x38, 0x30+index)
            print("   Register 0x8{}, VSR2: {} VSR1: {}".format(index, vsr2, vsr1))
        print("__________________________________________________________")

    # TODO: Reconstruct when data readout available
    # @run_on_executor(executor='thread_executor')
    def acquire_data(self):
        """Acquire data, poll fem for completion and read out fem monitors."""
        try:
            logging.info("Initiate Data Capture")
            self.acquire_start_time = self.create_timestamp()

            # TODO: Placeholder for triggering daq

            # How to convert datetime object to float?
            self.acquire_timestamp = time.time()    # Utilised by adapter's watchdog

            self.waited = 0.1
            IOLoop.instance().call_later(0.1, self.check_acquire_finished)
        except Exception as e:
            self.flag_error("Failed to start acquire_data", str(e))

    def check_acquire_finished(self):
        """Check whether all data transferred, until completed or cancelled by user."""
        # print(" \n fem.acquire_data()")
        try:
            # delay = 0.10
            # reply = 0
            # Stop if user clicked on Cancel button
            if (self.stop_acquisition):
                logging.debug(" -=-=-=- HexitecFem told to cancel acquisition -=-=-=-")
                self.acquire_data_completed()
                return
            else:
                # Temporary hack - Wait until hardware finished sending data (simulated for now) #
                # reply = self.x10g_rdma.read(
                #     0x60000014, burst_len=1, comment='Check data transfer completed?')
                if self.all_data_sent == 0:
                    # print(" *** Awaiting data.. ***")
                    IOLoop.instance().call_later(0.5, self.check_acquire_finished)
                    return
                else:
                    # print(" *** Data Received! ***" )
                    # Original code resumes here: #
                    self.acquire_data_completed()
                    return
                # else:
                #     self.waited += delay
                #     if self.duration_enabled:
                #         self.duration_remaining = round((self.duration - self.waited), 1)
                #         if self.duration_remaining < 0:
                #             self.duration_remaining = 0
                #         # print("\t dur'n_remain'g: {} secs".format(self.duration_remaining))
                #     IOLoop.instance().call_later(delay, self.check_acquire_finished)
                #     return
        except HexitecFemError as e:
            self.flag_error("Failed to collect data", str(e))
        except Exception as e:
            self.flag_error("Data collection failed", str(e))

        # Acquisition interrupted
        self.acquisition_completed = True

    # TODO: To be expanded
    def acquire_data_completed(self):
        """Reset variables and read out Firmware monitors post data transfer."""
        # print("\n fem.acquire_data_completed()")
        self.acquire_stop_time = self.create_timestamp()

        if self.stop_acquisition:
            logging.info("Cancelling Acquisition..")
            # TODO Verify working okay: ?
            for vsr in self.vsr_list:
                self.send_cmd([vsr.addr, 0xE2])
            logging.info("Acquisition cancelled")
            # Reset variables
            self.stop_acquisition = False
            self.hardware_busy = False
            self.acquisition_completed = True
            self._set_status_message("User cancelled collection")
            return
        else:
            waited = str(round(self.waited, 3))
            logging.debug("Capturing {} frames took {} s".format(str(self.number_frames), waited))
            duration = "Requested {} frame(s), took {} seconds".format(self.number_frames, waited)
            self._set_status_message(duration)
            # Save duration to separate parameter tree entry:
            self.acquisition_duration = duration

        logging.debug("Acquisition Completed, enable signal cleared")

        # Fem finished sending data/monitoring info, clear hardware busy
        self.hardware_busy = False

        # Workout exact duration of fem data transmission:
        self.acquire_time = float(self.acquire_stop_time.split("_")[1]) \
            - float(self.acquire_start_time.split("_")[1])
        start_ = datetime.strptime(self.acquire_start_time, HexitecFem.DATE_FORMAT)
        stop_ = datetime.strptime(self.acquire_stop_time, HexitecFem.DATE_FORMAT)
        self.acquire_time = (stop_ - start_).total_seconds()

        # Wrap up by updating GUI

        # Acquisition completed, note completion
        self.acquisition_completed = True
        self.parent.software_state = "Idle"

    # TODO: Will become redundant
    def read_receive_from_all(self, op_command, register_h, register_l):  # pragma: no coverage
        """Read and receive from all VSRs."""
        reply = []
        for vsr in self.vsr_list:
            self.send_cmd([vsr.addr, op_command, register_h, register_l])
            resp = self.read_response()
            resp = resp[2:-1]
            resp = self.convert_list_to_string(resp)
            reply.append(resp)
        return reply

    # TODO: Will become redundant
    def write_receive_to_all(self, op_command, register_h, register_l,
                             value_h, value_l):  # pragma: no coverage
        """Write and receive to all VSRs."""
        for vsr in self.vsr_list:
            self.send_cmd([vsr.addr, op_command, register_h, register_l, value_h, value_l])
            self.read_response()

    # TODO: Will become redundant
    def are_capture_dc_ready(self, vsrs_register_89):  # pragma: no coverage
        """Check status of Register 89, bit 0: Capture DC ready."""
        vsrs_ready = True
        for vsr in vsrs_register_89:
            dc_capture_ready = ord(vsr[1]) & 1
            if not dc_capture_ready:
                vsrs_ready = False
        return vsrs_ready

    @run_on_executor(executor='thread_executor')
    def collect_offsets(self):
        """Run collect offsets sequence.

        Stop state machine, gathers offsets, calculats average picture, re-starts state machine.
        """
        try:
            # beginning = time.time()

            if self.hardware_connected is not True:
                raise HexitecFemError("Can't collect offsets while disconnected")
            if self.hardware_busy:
                raise HexitecFemError("Can't collect offsets, Hardware busy")
            else:
                self._set_status_error("")
            self.hardware_busy = True
            self.parent.software_state = "Offsets"

            vsrs_register_24 = self.read_receive_from_all(HexitecFem.READ_REG_VALUE, 0x32, 0x34)
            logging.debug("Reading back register 24; {}".format(vsrs_register_24))

            # 1. System is fully initialised (Done already)

            # 2. Stop the state machine

            self.write_receive_to_all(HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31)

            # 3. Set reg 0x24 to 0x22

            logging.debug("Gathering offsets..")
            # Send reg value; Register 0x24, bits5,1: disable VCAL, capture average picture:
            self.write_receive_to_all(HexitecFem.SEND_REG_VALUE, 0x32, 0x34, 0x32, 0x32)

            # 4. Start the state machine

            self.write_receive_to_all(HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31)

            # 5. Wait > 8192 * frame time (~1 second, @ 9118.87Hz)

            expected_duration = 8192 / self.parent.fem.frame_rate
            timeout = (expected_duration * 1.2) + 1
            # print(" *** expected: {} timeout: {}".format(expected_duration, timeout))
            poll_beginning = time.time()
            self._set_status_message("Collecting dark images..")
            dc_captured = False
            while not dc_captured:
                vsrs_register_89 = self.read_receive_from_all(
                    HexitecFem.READ_REG_VALUE, 0x38, 0x39)
                dc_captured = self.are_capture_dc_ready(vsrs_register_89)
                if self.debug:   # pragma: no coverage
                    logging.debug("Register 0x89: {0}, Done? {1} Timing: {2:2.5} s".format(
                        vsrs_register_89, dc_captured, time.time() - poll_beginning))
                if time.time() - poll_beginning > timeout:
                    raise HexitecFemError("Dark images timed out. R.89: {}".format(
                        vsrs_register_89))
            # poll_ending = time.time()
            # print(" *** collect offsets polling took: {0} seconds @ {1:4.1f}Hz**".format(
            #     poll_ending - poll_beginning, self.parent.fem.frame_rate))

            # 6. Stop state machine
            self.write_receive_to_all(HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31)

            # 7. Set reg 0x24 to 0x28

            logging.debug("Offsets collected")
            # Send reg value; Register 0x24, bits5,3: disable VCAL, enable spectroscopic mode:
            self.write_receive_to_all(HexitecFem.SEND_REG_VALUE, 0x32, 0x34, 0x32, 0x38)

            # 8. Start state machine

            self.write_receive_to_all(HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31)

            logging.debug("Ensure VCAL remains on")
            self.write_receive_to_all(HexitecFem.CLR_REG_BIT, 0x32, 0x34, 0x32, 0x30)

            self._set_status_message("Offsets collections operation completed.")
            self.parent.software_state = "Idle"
            # Timestamp when offsets collected
            self.offsets_timestamp = self.create_timestamp()
            # # String format can be turned into millisecond format:
            # date_time = datetime.strptime(self.offsets_timestamp, HexitecFem.DATE_FORMAT)
            # ts = date_time.timestamp() * 1000
            # # convert timestamp to string in dd-mm-yyyy HH:MM:SS
            # str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")
            # print("Offsets timestamp, format of dd-mm-yyyy HH:MM:SS: ", str_date_time)
            # ending = time.time()
            # print("     collect_offsets took: {}".format(ending-beginning))
        except HexitecFemError as e:
            self.flag_error("Offsets", str(e))
        except Exception as e:
            self.flag_error("Failed to collect offsets", str(e))
        self.hardware_busy = False

    def load_enables_settings(self, vsr, address_h, address_l,
                              enables_settings, enables_defaults):
        """Load 20 bytes into 10 registers starting from address_h, address_l.

        address_h, address_l is the VSR register to target.
        enables_settings contain values read from ini file, otherwise enables_default utilised.
        """
        # Check list of (-1, -1) tuples wasn't returned
        if enables_settings[0][0] > 0:
            asic1_command = []
            for msb, lsb in enables_settings:
                asic1_command.append(msb)
                asic1_command.append(lsb)
            register_values = asic1_command
            # print("  ... producing register_values: {}  ".format(
            #     ' '.join("0x{0:02X}".format(x) for x in register_values)))
            # print("   i.e.:  {}".format(register_values))
            self.enables_write_and_read_verify(
                vsr, address_h, address_l, register_values)
        else:
            # No ini file loaded, use default values
            self.enables_write_and_read_verify(vsr, address_h, address_l, enables_defaults)

    def enables_write_and_read_verify(self, vsr, address_h, address_l, write_list):
        """Write enables to a block of registers, confirm written ok."""
        number_registers = 10
        self.block_write_custom_length(vsr, number_registers, address_h, address_l, write_list)

        resp_list, reply_list = self.block_read_and_response(vsr, number_registers,
                                                             address_h, address_l)
        read_list = []
        for a, b in resp_list:
            read_list.append(a)
            read_list.append(b)
        # Confirm read back values match written values
        if not (write_list == read_list):
            # Disagreed. Check again:
            resp_list, reply_list = self.block_read_and_response(vsr, number_registers,
                                                                 address_h, address_l)
            read_list = []
            for a, b in resp_list:
                read_list.append(a)
                read_list.append(b)
            if not (write_list == read_list):
                logging.error(" ** Readback value(s) still inaccurate:")
                logging.error(" **    Wrote: {}".format(write_list))
                logging.error(" **    Read : {}".format(read_list))
                self.error_list.append(" VSR {2:X} Register 0x{0}{1}: ERROR".format(
                    chr(address_h), chr(address_l), vsr))
                self.error_list.append("     Wrote: {}".format(write_list))
                self.error_list.append("     Read : {}".format(read_list))

    def load_pwr_cal_read_enables(self, vsr):
        """Load power, calibration and read enables - optionally from hexitec file."""
        if vsr.addr not in self.vsr_addr_mapping.values():
            raise HexitecFemError("Unknown VSR address! (%s)" % vsr.addr)
        # Address 0x90 = vsr1, 0x91 = vsr2, .. , 0x95 = vsr6. Therefore:
        vsr_num = vsr.addr - 143

        logging.debug("Loading Power, Cal and Read Enables")
        # logging.debug("Column Read Enable")

        # Column Read Enable ASIC1 (Reg 0x61) - checked 2
        asic1_col_read_enable = self._extract_80_bits("ColumnEn_", vsr_num, 1, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(vsr, 0x36, 0x31, asic1_col_read_enable, enables_defaults)

        # Column Read Enable ASIC2 (Reg 0xC2) - checked 1
        asic2_col_read_enable = self._extract_80_bits("ColumnEn_", vsr_num, 2, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(vsr, 0x43, 0x32, asic2_col_read_enable, enables_defaults)

        logging.debug("Column Power Enable")

        # Column Power Enable ASIC1 (Reg 0x4D) - checked 2
        asic1_col_power_enable = self._extract_80_bits("ColumnPwr", vsr_num, 1, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(vsr, 0x34, 0x44, asic1_col_power_enable, enables_defaults)

        # Column Power Enable ASIC2 (Reg 0xAE) - checked 1
        asic2_col_power_enable = self._extract_80_bits("ColumnPwr", vsr_num, 2, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(vsr, 0x41, 0x45, asic2_col_power_enable, enables_defaults)

        logging.debug("Column Calibration Enable")

        # Column Calibrate Enable ASIC1 (Reg 0x57) - checked 3
        asic1_col_cal_enable = self._extract_80_bits("ColumnCal", vsr_num, 1, "Channel")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        self.load_enables_settings(vsr, 0x35, 0x37, asic1_col_cal_enable, enables_defaults)

        # Column Calibrate Enable ASIC2 (Reg 0xB8) - checked 3
        asic2_col_cal_enable = self._extract_80_bits("ColumnCal", vsr_num, 2, "Channel")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        self.load_enables_settings(vsr, 0x42, 0x38, asic2_col_cal_enable, enables_defaults)

        logging.debug("Row Read Enable")

        # Row Read Enable ASIC1 (Reg 0x43) - chcked 5
        asic1_row_enable = self._extract_80_bits("RowEn_", vsr_num, 1, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(vsr, 0x34, 0x33, asic1_row_enable, enables_defaults)

        # Row Read Enable ASIC2 (Reg 0xA4) - checked 4
        asic2_row_enable = self._extract_80_bits("RowEn_", vsr_num, 2, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(vsr, 0x41, 0x34, asic2_row_enable, enables_defaults)

        logging.debug("Row Power Enable")

        # Row Power Enable ASIC1 (Reg 0x2F) - checked 5
        asic1_row_power_enable = self._extract_80_bits("RowPwr", vsr_num, 1, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(vsr, 0x32, 0x46, asic1_row_power_enable, enables_defaults)

        # Row Power Enable ASIC2 (Reg 0x90) - chcked 4
        asic2_row_power_enable = self._extract_80_bits("RowPwr", vsr_num, 2, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(vsr, 0x39, 0x30, asic2_row_power_enable, enables_defaults)

        logging.debug("Row Calibration Enable")

        # Row Calibrate Enable ASIC1 (Reg 0x39) - chcked 6
        asic1_row_cal_enable = self._extract_80_bits("RowCal", vsr_num, 1, "Block")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        self.load_enables_settings(vsr, 0x33, 0x39, asic1_row_cal_enable, enables_defaults)

        # Row Calibrate Enable ASIC2 (Reg 0x9A) - checked 6
        asic2_row_cal_enable = self._extract_80_bits("RowCal", vsr_num, 2, "Block")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        self.load_enables_settings(vsr, 0x39, 0x41, asic2_row_cal_enable, enables_defaults)

        logging.debug("Power, Cal and Read Enables have been loaded")

    def make_list_hexadecimal(self, value):  # pragma: no cover
        """Debug function: Turn decimal list into hexadecimal list."""
        value_hexadecimal = []
        for val in value:
            value_hexadecimal.append("0x%x" % val)
        return value_hexadecimal

    def get_vsr_register_value(self, vsr_number, address_h, address_l):
        """Read the VSR register At address_h, address_l."""
        self.send_cmd([vsr_number, self.READ_REG_VALUE, address_h, address_l])
        resp = self.read_response()  # ie resp = [42, 144, 48, 49, 13]
        # Omit start char, vsr & register addresses, and end char
        reply = resp[2:-1]
        # Turn list of integers into ASCII string
        reply = "{}".format(''.join([chr(x) for x in reply]))
        # print(" *** (R) Reg 0x{0:X}{1:X}, Received ({2}) from UART: {3}".format(address_h-0x30,
        #       address_l-0x30, len(resp), ' '.join("0x{0:02X}".format(x) for x in resp)))
        return resp, reply

    def read_register89(self, vsr_number):
        """Read out register 89."""
        (address_h, address_l) = (0x38, 0x39)
        # print("Read Register 0x{0}{1}".format(address_h-0x30, address_l-0x30))
        return self.get_vsr_register_value(vsr_number, address_h, address_l)

    def read_register07(self, vsr_number):  # pragma: no coverage
        """Read out register 07."""
        # time.sleep(0.25)
        (address_h, address_l) = (0x30, 0x37)
        # print("Read Register 0x{0}{1}".format(address_h-0x30, address_l-0x30))
        return self.get_vsr_register_value(vsr_number, address_h, address_l)

    @run_on_executor(executor='thread_executor')
    def initialise_system(self):
        """Configure in full all VSRs.

        Initialise, load enables, set up state machine, write to DAC and enable ADCs.
        """
        try:
            beginning = time.time()
            self.hardware_busy = True
            for vsr in self.vsr_list:
                logging.debug(" --- Initialising VSR: 0x{0:X} ---".format(vsr.addr))
                self._set_status_message("Initialising VSR{}..".format(vsr.addr-143))
                self.initialise_vsr(vsr)
                # Check PLLs locked
                bPolling = True
                time_taken = 0
                while bPolling:
                    r89_list, r89_value = self.read_register89(vsr.addr)
                    LSB = ord(r89_value[1])
                    # Is PLL locked? (bit1 high)
                    if LSB & 2:
                        bPolling = False
                    else:
                        # print(" R.89: {} {}".format(r89_value, r89_value[1], ord(r89_value[1])))
                        time.sleep(0.1)
                        time_taken += 0.1
                    if time_taken > 0.4:
                        raise HexitecFemError("Timed out polling register 0x89;PLL still disabled")

            logging.debug("LVDS Training")
            self.x10g_rdma.udp_rdma_write(address=HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                          data=0x10, burst_len=1, cmd_no=0x0,
                                          comment=HEXITEC_2X6_VSR_DATA_CTRL['description'])
            time.sleep(0.2)
            self.x10g_rdma.udp_rdma_write(address=HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                          data=0x10, burst_len=1, cmd_no=0x0,
                                          comment=HEXITEC_2X6_VSR_DATA_CTRL['description'])

            vsr_status_addr = HEXITEC_2X6_VSR0_STATUS['addr']
            for vsr in self.vsr_list:
                index = vsr.addr - self.vsr_base_address
                locked = self.x10g_rdma.udp_rdma_read(vsr_status_addr, burst_len=1, cmd_no=0,
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

            self._set_status_message("Initialisation completed. VSRs configured.")
            print(" -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=- ")
            ending = time.time()
            print("     initialisation took: {}".format(ending-beginning))

            # DEBUGGING Info:
            self.debugging_function()
            # DEBUGGING completed
            self.parent.software_state = "Idle"
        except HexitecFemError as e:
            self.flag_error("Failed to initialise camera", str(e))
        except Exception as e:
            self.flag_error("Camera initialisation failed", str(e))
        self.hardware_busy = False

    def debugging_function(self):  # pragma: no coverage
        """Provides additional debugging information for initialise_system()"""
        reg07 = []
        reg89 = []
        print("VSR Row S1: (H, L). S1Sph  SphS2: adc clk dly: . FVAL/LVAL:  VCAL2 (H, L) Gain")
        # TODO dbg info on {vsr.addr}
        for vsr in self.vsr_list:
            # print(f" TODO: dbg info on {vsr.addr}")
            r7_list, r7_value = self.read_register07(vsr.addr)
            reg07.append(r7_value)
            r89_list, r89_value = self.read_register89(vsr.addr)
            reg89.append(r89_value)

            s1_high_resp, s1_high_reply = vsr.read_and_response(0x30, 0x33)
            s1_low_resp, s1_low_reply = vsr.read_and_response(0x30, 0x32)
            sph_resp, sph_reply = vsr.read_and_response(0x30, 0x34)
            s2_resp, s2_reply = vsr.read_and_response(0x30, 0x35)
            # ADC Clock Delay
            adc_clock_resp, adc_clock_reply = vsr.read_and_response(0x30, 0x39)
            # FVAL/LVAL Delay
            vals_delay_resp, vals_delay_reply = vsr.read_and_response(0x30, 0x45)
            # VCAL2 -> VCAL1 high byte
            vcal_high_resp, vcal_high_reply = vsr.read_and_response(0x31, 0x39)
            # VCAL2 -> VCAL1 low byte
            vcal_low_resp, vcal_low_reply = vsr.read_and_response(0x31, 0x38)
            gain_resp, gain_reply = vsr.read_and_response(0x30, 0x36)  # Gain
            print(" {} {} {} {}    {}     {}        {}             {}            {} {} {}".format(
                vsr.addr-143, s1_high_reply, s1_low_reply,
                "         ",
                sph_reply,
                s2_reply,
                adc_clock_reply,
                vals_delay_reply,
                vcal_high_reply, vcal_low_reply,
                gain_reply))
        print(" All vsrs, reg07: {}".format(reg07))
        print("           reg89: {}".format(reg89))

    # TODO: Will become redundant
    def initialise_vsr(self, vsr):  # pragma: no coverage
        """Initialise a VSR."""
        value_002 = 0x30, 0x31  # RowS1 Low Byte value: 1 = maximum frame rate
        value_003 = 0x30, 0x30  # RowS1 High Byte value : 0 = ditto
        value_004 = 0x30, 0x31  # S1 -> Sph, 6 bits : 1 = ... Yes, what?
        value_005 = 0x30, 0x36  # SphS2, 6 bits : 6 = ... Yes, what?
        value_006 = 0x30, 0x31  # Gain, 1 bit : 0 = High Gain; 1 = Low Gain
        value_009 = 0x30, 0x32  # ADC1 Delay, 5 bits : 2 = 2 clock cycles
        value_00E = 0x30, 0x41
        value_018 = 0x30, 0x31  # VCAL2 -> VCAL1 Low Byte, 8 bits: 1 = 1 clock cycle
        value_019 = 0x30, 0x30  # VCAL2 -> VCAL1 High Byte, 7 bits

        if self.row_s1 > -1:
            # Valid value, within range
            self.row_s1_low = self.row_s1 & 0xFF
            self.row_s1_high = self.row_s1 >> 8
            value_002 = self.convert_to_aspect_format(self.row_s1_low)
            value_003 = self.convert_to_aspect_format(self.row_s1_high)
            # print(" *** Row_s1: {0} -> high: {1} low: {2} ".format(
            #     self.row_s1, self.row_s1_high, self.row_s1_low))
            # print("     R.02          0x{0:X} 0x{1:X}".format(value_002[0], value_002[1]))
            # print("     R.03          0x{0:X} 0x{1:X}".format(value_003[0], value_003[1]))
        if self.s1_sph > -1:
            value_004 = self.convert_to_aspect_format(self.s1_sph)
            # print(" *** s1_sph: {0}          ".format(self.s1_sph))
            # print("     R.04          0x{0:X} 0x{1:X}".format(value_004[0], value_004[1]))
        if self.sph_s2 > -1:
            value_005 = self.convert_to_aspect_format(self.sph_s2)
            # print(" *** sph_s2: {0}          ".format(self.sph_s2))
            # print("     R.05          0x{0:X} 0x{1:X}".format(value_005[0], value_005[1]))
        gain = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Gain', bit_range=1)
        if gain > -1:
            value_006 = self.convert_to_aspect_format(gain)
        adc1_delay = self._extract_integer(
            self.hexitec_parameters, 'Control-Settings/ADC1 Delay', bit_range=2)
        if adc1_delay > -1:
            value_009 = self.convert_to_aspect_format(adc1_delay)
        delay_sync_signals = self._extract_integer(
            self.hexitec_parameters, 'Control-Settings/delay sync signals', bit_range=8)
        if delay_sync_signals > -1:
            value_00E = self.convert_to_aspect_format(delay_sync_signals)
        vcal2_vcal1 = self._extract_integer(
            self.hexitec_parameters, 'Control-Settings/VCAL2 -> VCAL1', bit_range=15)
        if vcal2_vcal1 > -1:
            vcal2_vcal1_low = vcal2_vcal1 & 0xFF
            vcal2_vcal1_high = vcal2_vcal1 >> 8
            value_018 = self.convert_to_aspect_format(vcal2_vcal1_low)
            value_019 = self.convert_to_aspect_format(vcal2_vcal1_high)
        """
        90	42	01	10	;Select external Clock
        90	42	07	03	;Enable PLLs
        90	42	02	01	;LowByte Row S1
        """
        delayed = False  # Debugging: Extra 0.2 second delay between read, write?
        masked = False
        # Select external Clock
        vsr.write_and_response(0x30, 0x31, 0x31, 0x30)
        # Enable PLLs; 1 = Enable PLL; 2 = Enable ADC PLL
        vsr.write_and_response(0x30, 0x37, 0x30, 0x33)
        vsr.write_and_response(0x30, 0x32, value_002[0], value_002[1],
                               masked=masked, delay=delayed)   # LowByte Row S1
        vsr.write_and_response(0x30, 0x33, value_003[0], value_003[1],
                               masked=masked, delay=delayed)   # HighByte Row S1
        """
        90	42	04	01	;S1Sph
        90	42	05	06	;SphS2
        90	42	09	02	;ADC Clock Delay
        90	42	0E	0A	;FVAL/LVAL Delay
        90	42	1B	08	;SM wait Clock Row
        90	42	14	01	;Start SM on falling edge
        90	42	01	20	;Enable LVDS Interface
        """
        vsr.write_and_response(0x30, 0x34, value_004[0], value_004[1],
                               masked=masked, delay=delayed)     # S1Sph
        vsr.write_and_response(0x30, 0x35, value_005[0], value_005[1],
                               masked=masked, delay=delayed)     # SphS2
        vsr.write_and_response(0x30, 0x36, value_006[0], value_006[1], delay=delayed)  # Gain
        # ADC Clock Delay:
        vsr.write_and_response(0x30, 0x39, value_009[0], value_009[1], delay=delayed)
        # FVAL/LVAL Delay:
        vsr.write_and_response(0x30, 0x45, value_00E[0], value_00E[1], delay=delayed)
        # SM wait Low Row, 8 bits:
        vsr.write_and_response(0x31, 0x42, 0x30, 0x38)
        # Start SM on falling edge ('0' = rising edge) of ADC-CLK:
        vsr.write_and_response(0x31, 0x34, 0x30, 0x31)

        vsr.write_and_response(0x30, 0x31, 0x32, 0x30)    # Enable LVDS Interface (Serial interface reset on MR's)
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
        self.enable_adc(vsr)
        """
        90	40	24	22	;Disable Vcal/Capture Avg Picture
        90	40	24	28	;Disable Vcal/En DC spectroscopic mode
        90	42	01	80	;Enable Training
        90	42	18	01	;Low Byte SM Vcal Clock
        90	43	24	20	;Enable Vcal
        90	42	24	20	;Disable Vcal
        """
        # Disable Vcal/Capture Avg Picture (False=don't mask)
        vsr.write_and_response(0x32, 0x34, 0x32, 0x32, False)
        # print("Disable Vcal/En DC spectroscopic mode")
        # Disable Vcal/En DC spectroscopic mode (False=don't mask)
        vsr.write_and_response(0x32, 0x34, 0x32, 0x38, False)
        logging.debug("Enable Training")
        vsr.write_and_response(0x30, 0x31, 0x38, 0x30)    # Enable Training

        # TODO: Inserting VCal setting here

        # Send VCAL2 -> VCAL1 low byte to Register 0x02 (Accepts 8 bits)
        vsr.write_and_response(0x31, 0x38, value_018[0], value_018[1], False)
        # Send VCAL2 -> VCAL1 high byte to Register 0x03 (Accepts 7 bits)
        vsr.write_and_response(0x31, 0x39, value_019[0], value_019[1], False)
        logging.debug("Enable Vcal")  # 90	43	24	20	;Enable Vcal
        self.send_cmd([vsr.addr, 0x43, 0x32, 0x34, 0x32, 0x30])
        self.read_response()
        # vsr.write_and_response(0x32, 0x34, 0x32, 0x30)     # Disable Vcal

        """MR's tcl script also also set these two:"""
        # set queue_1 { { 0x40 0x01 0x30    "Disable_Training" } \
        #             { 0x40 0x0A 0x01      "Enable_Triggered_SM_Start" }
        # }

    def read_and_response(self, vsr, address_h, address_l, delay=False):
        """Send a read and read the reply."""
        if delay:
            time.sleep(0.1)
        self.send_cmd([vsr, 0x41, address_h, address_l])
        if delay:
            time.sleep(0.1)
        resp = self.read_response()  # ie resp = [42, 144, 48, 49, 13]
        # Omit start char, vsr address and end char
        reply = resp[2:-1]
        # Turn list of integers into ASCII string
        reply = "{}".format(''.join([chr(x) for x in reply]))
        # print(" RR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        return resp, reply

    def write_and_response(self, vsr, address_h, address_l, value_h, value_l,
                           masked=True, delay=False):
        """Write value_h, value_l to address_h, address_l of vsr, if not masked
        then register value overwritten."""
        resp, reply = self.read_and_response(vsr, address_h, address_l)
        resp = resp[2:-1]   # Extract payload
        if masked:
            value_h, value_l = self.mask_aspect_encoding(value_h, value_l, resp)
        # print("   WaR Write: {} {} {} {} {}".format(vsr, address_h, address_l, value_h, value_l))
        if delay:
            time.sleep(0.1)
        self.send_cmd([vsr, 0x40, address_h, address_l, value_h, value_l])
        if delay:
            time.sleep(0.1)
        resp = self.read_response()  # ie resp = [42, 144, 48, 49, 13]
        if delay:
            time.sleep(0.1)
        reply = resp[4:-1]  # Omit start char, vsr & register addresses, and end char
        # Turn list of integers into ASCII string
        reply = "{}".format(''.join([chr(x) for x in reply]))
        # print(" WR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        if ((resp[4] != value_h) or (resp[5] != value_l)):
            print("H? {} L? {}".format(resp[4] == value_h, resp[5] == value_l))
            print("WaR. reply: {} (resp: {}) VS H: {} L: {}".format(reply, resp, value_h, value_l))
            print("WaR. (resp: {} {}) VS H: {} L: {}".format(resp[4], resp[5], value_h, value_l))
            raise HexitecFemError("Readback value did not match written!")
        return resp, reply

    def block_write_and_response(self, vsr, number_registers, address_h, address_l,
                                 value_h, value_l):
        """Write value_h, value_l to address_h, address_l of vsr, span number_registers."""
        most_significant, least_significant = self.expand_addresses(number_registers,
                                                                    address_h, address_l)
        for index in range(number_registers):
            # print("   BWaR Write: {} {} {} {} {}".format(
            #     vsr, most_significant[index], least_significant[index], value_h, value_l))
            self.write_and_response(vsr, most_significant[index], least_significant[index],
                                    value_h, value_l, False)

    def block_write_custom_length(self, vsr, number_registers, address_h, address_l, write_values):
        """Write write_values starting with address_h, address_l of vsr, span number_registers."""
        if (number_registers * 2) != len(write_values):
            err1 = "Mismatch! number_registers"
            err2 = "isn't half of write_values"
            raise HexitecFemError("{} ({}) {} ({}).".format(
                err1, number_registers, err2, len(write_values)))
        values_list = write_values.copy()
        most_significant, least_significant = self.expand_addresses(
            number_registers, address_h, address_l)
        for index in range(number_registers):
            value_h = values_list.pop(0)
            value_l = values_list.pop(0)
            # print("   BWCL Write: {0:X} {1:X} {2:X} {3:X} {4:X}".format(
            #     vsr.addr, most_significant[index], least_significant[index], value_h, value_l))
            vsr.write_and_response(
                most_significant[index], least_significant[index], value_h, value_l, False)

    def expand_addresses(self, number_registers, address_h, address_l):
        """Expand addresses by the number_registers specified.

        ie If (number_registers, address_h, address_l) = (10, 0x36, 0x31)
        would produce 10 addresses of:
        (0x36 0x31) (0x36 0x32) (0x36 0x33) (0x36 0x34) (0x36 0x35)
        (0x36 0x36) (0x36 0x37) (0x36 0x38) (0x36 0x39) (0x36 0x41)
        """
        most_significant = []
        least_significant = []
        for index in range(address_l, address_l+number_registers):
            most_significant.append(address_h)
            least_significant.append(address_l)
            address_l += 1
            if address_l == 0x3A:
                address_l = 0x41
            if address_l == 0x47:
                address_h += 1
                if address_h == 0x3A:
                    address_h = 0x41
                address_l = 0x30
        return most_significant, least_significant

    def block_read_and_response(self, vsr, number_registers, address_h, address_l):
        """Read from address_h, address_l of vsr, covering number_registers registers."""
        most_significant, least_significant = self.expand_addresses(number_registers, address_h,
                                                                    address_l)
        resp_list = []
        reply_list = []
        for index in range(number_registers):
            resp, reply = vsr.read_and_response(most_significant[index], least_significant[index])
            # print(" BRaR: {} and {}".format(resp, reply))
            resp_list.append(resp[2:-1])
            reply_list.append(reply)
        return resp_list, reply_list

    def write_dac_values(self, vsr):
        """Write values to DAC, optionally provided by hexitec file."""
        logging.debug("Writing DAC values")
        vcal = [0x30, 0x31, 0x46, 0x46]     # [0x30, 0x32, 0x41, 0x41]
        umid = [0x30, 0x46, 0x46, 0x46]     # [0x30, 0x35, 0x35, 0x35]
        hv = [0x30, 0x35, 0x35, 0x35]
        dctrl = [0x30, 0x30, 0x30, 0x30]
        rsrv2 = [0x30, 0x38, 0x45, 0x38]

        umid_value = self._extract_exponential(self.hexitec_parameters,
                                               'Control-Settings/Uref_mid', bit_range=12)
        # print("\n *** umid_value: {0} \n".format(umid_value))
        if umid_value > -1:
            # Valid value, within range
            umid_high = (umid_value >> 8) & 0x0F
            umid_low = umid_value & 0xFF
            umid[0], umid[1] = self.convert_to_aspect_format(umid_high)
            umid[2], umid[3] = self.convert_to_aspect_format(umid_low)
            # print(" *** umid: {0} -> high: {1} low: {2} ".format(umid_value, umid_high, umid_low))
            # print("                   0x{0:X} 0x{1:X}".format(umid[0], umid[1]))
            # print("                   0x{0:X} 0x{1:X}".format(umid[2], umid[3]))

        vcal_value = self._extract_float(self.hexitec_parameters, 'Control-Settings/VCAL')
        if vcal_value > -1:
            # Valid value, within range
            vcal_high = (vcal_value >> 8) & 0x0F
            vcal_low = vcal_value & 0xFF
            vcal[0], vcal[1] = self.convert_to_aspect_format(vcal_high)
            vcal[2], vcal[3] = self.convert_to_aspect_format(vcal_low)

        # print(" *** umid_value: {} vcal_value: {}".format(umid_value, vcal_value))
        self.send_cmd([vsr.addr, HexitecFem.WRITE_DAC_VAL,
                       vcal[0], vcal[1], vcal[2], vcal[3],       # Vcal, e.g. 0x0111 = 0.2V
                       umid[0], umid[1], umid[2], umid[3],       # Umid, e.g. 0x0555 = 1.0V
                       hv[0], hv[1], hv[2], hv[3],               # reserve1, 0x0555 = 1V (HV ~-250)
                       dctrl[0], dctrl[1], dctrl[2], dctrl[3],   # DET ctrl, 0x000
                       rsrv2[0], rsrv2[1], rsrv2[2], rsrv2[3]])  # reserve2, 0x08E8 = 1.67V
        self.read_response()
        logging.debug("DAC values set")

    def enable_adc(self, vsr):
        """Enable the ADCs."""
        vsr.addr = vsr.addr
        logging.debug("Disable ADC/Enable DAC")     # 90 55 02 ;Disable ADC/Enable DAC
        self.send_cmd([vsr.addr, HexitecFem.CTRL_ADC_DAC, 0x30, 0x32])
        self.read_response()

        logging.debug("Disable SM")      # 90 43 01 01 ;Disable SM
        self.send_cmd([vsr.addr, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31])
        self.read_response()

        logging.debug("Enable SM")     # 90 42 01 01 ;Enable SM
        self.send_cmd([vsr.addr, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31])
        self.read_response()

        logging.debug("Enable ADC/Enable DAC")  # 90 55 03  ;Enable ADC/Enable DAC
        self.send_cmd([vsr.addr, HexitecFem.CTRL_ADC_DAC, 0x30, 0x33])
        self.read_response()

        logging.debug("Write ADC register")     # 90 53 16 09   ;Write ADC Register
        self.send_cmd([vsr.addr, 0x53, 0x31, 0x36, 0x30, 0x39])  # Works just as the one below
        self.read_response()
        # self.write_and_response(vsr.addr, 0x31, 0x36, 0x30, 0x39)

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
        if self.duration_enabled:
            # print("\n\tfem.calculate_frame_rate() (duration {} setting parent's
            # number_frames {})\n".format(self.duration, self.number_frames))
            # With duration enabled, recalculate number of frames in case clocks changed
            self.set_duration(self.duration)
            self.parent.set_number_frames(self.number_frames)

    def convert_list_to_string(self, int_list):
        r"""Convert list of integer into ASCII string.

        I.e. integer_list = [42, 144, 70, 70, 13], returns '*\x90FF\r'
        """
        return "{}".format(''.join([chr(x) for x in int_list]))

    def read_pwr_voltages(self, vsr):
        """Read and convert power data into voltages."""
        if vsr.addr not in self.vsr_addr_mapping.values():
            raise HexitecFemError("HV: Invalid VSR address(0x{0:02X})".format(vsr.addr))
        index = vsr.addr - self.vsr_base_address
        if (0 <= index <= 5):
            self.hv_list[index] = vsr._get_power_sensors()
        else:
            raise HexitecFemError("Power Voltages: Invalid VSR index: {}".format(index))

    def read_temperatures_humidity_values(self, vsr):
        """Read and convert sensor data into temperatures and humidity values."""
        if vsr.addr not in self.vsr_addr_mapping.values():
            raise HexitecFemError("Sensors: Invalid VSR address(0x{0:02X})".format(vsr.addr))
        sensors_values = vsr._get_env_sensors()

        if self.debug:   # pragma: no coverage
            logging.debug("VSR: %s sensors_values: %s len: %s" % (format(vsr.addr, '#02x'),
                          sensors_values, len(sensors_values)))

        index = vsr.addr - self.vsr_base_address
        if (0 <= index <= 5):
            self.ambient_list[index] = sensors_values[0]
            self.humidity_list[index] = sensors_values[1]
            self.asic1_list[index] = sensors_values[2]
            self.asic2_list[index] = sensors_values[3]
            self.adc_list[index] = sensors_values[4]
        else:
            raise HexitecFemError("Sensors: Invalid VSR index: {}".format(index))

    def set_hexitec_config(self, filename):
        """Check whether file exists, load parameters from file."""
        filename = self.base_path + filename
        try:
            with open(filename, 'r') as f:  # noqa: F841
                pass
            self.hexitec_config = filename
            logging.debug("hexitec_config: '%s'" % (self.hexitec_config))
        except IOError as e:
            self.flag_error("Cannot open provided hexitec file", str(e))
            return

        try:
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

            # print("row_s1: {} from {}".format(self.row_s1, row_s1))
            # print("s1_sph: {} from {}".format(self.s1_sph, s1_sph))
            # print("sph_s2: {} from {}".format(self.sph_s2, sph_s2))
            # print("bias:   {} from {}".format(self.bias_level, bias_level))
            # print(" vsrs: {}".format(self.vsrs_selected))
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
                logging.error("Error parsing parameter %s, got: %s but valid range: %s-%s" %
                              (descriptor, setting, valid_range[0], valid_range[1]))
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

        bDebug = False
        # if param == "ColumnCal":
        #     bDebug = True

        aspect_list = [(-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1),
                       (-1, -1), (-1, -1), (-1, -1)]

        key = 'Sensor-Config_V%s_S%s/%s1st%s' % (vsr, asic, param, channel_or_block)
        try:
            first_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return aspect_list

        key = 'Sensor-Config_V%s_S%s/%s2nd%s' % (vsr, asic, param, channel_or_block)
        try:
            second_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return aspect_list

        key = 'Sensor-Config_V%s_S%s/%s3rd%s' % (vsr, asic, param, channel_or_block)
        try:
            third_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return aspect_list

        key = 'Sensor-Config_V%s_S%s/%s4th%s' % (vsr, asic, param, channel_or_block)
        try:
            fourth_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return aspect_list

        entirety = first_channel + second_channel + third_channel + fourth_channel
        if bDebug:  # pragma: no cover
            print("   1st: %s" % first_channel)
            print("   2nd: %s" % second_channel)
            print("   3rd: %s" % third_channel)
            print("   4th: %s" % fourth_channel)
            print("   entirety: %s" % entirety)
        # Convert string to bytes (to support Python 3)
        entirety = entirety.encode("utf-8")
        # Pixels appear in 8 bit reverse order, reverse bit order accordingly
        # More info: https://docs.scipy.org/doc/numpy/user/basics.byteswapping.html
        big_end_arr = np.ndarray(shape=(10,), dtype='>i8', buffer=entirety)
        rev_order = big_end_arr.byteswap()
        entirety = rev_order.tobytes()

        byte_list = []
        for index in range(0, len(entirety), 8):
            byte_list.append(entirety[index:index + 8])

        aspect_list = []
        for binary in byte_list:
            decimal = int(binary, 2)
            aspect = self.convert_to_aspect_format(decimal)
            aspect_list.append(aspect)
            if bDebug:  # pragma: no cover
                print("\t\tVSR: %s   bin: %s dec: %s" % (vsr, binary, "{:02x}".format(decimal)))

        # Turns aspect_list into tupples of (MSB, LSB), e.g.
        # [(70, 70), (70, 70), (70, 70), (70, 70), (70, 70), (70, 70), (70, 70), (69, 55),
        #  (57, 53), (51, 49)]

        return aspect_list

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
        # print(" *** conv_to_aspect_..({}) -> {}, {}".format(value, high_encoded, low_encoded))
        return high_encoded, low_encoded

    def read_ini_file(self, filename, parameter_dict, debug=False):
        """Read filename, parse case sensitive keys decoded as strings into parameter_dict."""
        parser = configparser.ConfigParser()
        if debug:  # pragma: no cover
            print("---------------------------------------------------------------------")
        # Maintain case-sensitivity:
        parser.optionxform = str
        parser.read(filename)
        for section in parser.sections():
            if debug:  # pragma: no cover
                print("Section: ", section)
            for key, value in parser.items(section):
                parameter_dict[section + "/" + key] = value.strip("\"")
                if debug:  # pragma: no cover
                    print("   " + section + "/" + key + " => " + value.strip("\""))
        if debug:  # pragma: no cover
            print("---------------------------------------------------------------------")

    def translate_to_normal_hex(self, value):
        """Translate Aspect encoding into 0-F equivalent scale."""
        if value not in self.HEX_ASCII_CODE:
            raise HexitecFemError("Invalid Hexadecimal value {0:X}".format(value))
        if value < 0x3A:
            value -= 0x30
        else:
            value -= 0x37
        return value

    def mask_aspect_encoding(self, value_h, value_l, resp):
        """Mask values honouring aspect encoding.

        Aspect: 0x30 = 1, 0x31 = 1, .., 0x39 = 9, 0x41 = A, 0x42 = B, .., 0x46 = F.
        Therefore increase values between 0x39 and 0x41 by 7 to match aspect's legal range.
        I.e. 0x39 | 0x32 = 0x3B, + 7 = 0x42.
        """
        value_h = self.translate_to_normal_hex(value_h)
        value_l = self.translate_to_normal_hex(value_l)
        resp[0] = self.translate_to_normal_hex(resp[0])
        resp[1] = self.translate_to_normal_hex(resp[1])
        masked_h = value_h | resp[0]
        masked_l = value_l | resp[1]
        # print("h: {0:X} r: {1:X} = {2:X} masked: {3:X} I.e. {4:X}".format(
        #     value_h, resp[0], value_h | resp[0], masked_h, self.HEX_ASCII_CODE[masked_h]))
        # print("l: {0:X} r: {1:X} = {2:X} masked: {3:X} I.e. {4:X}".format(
        #     value_l, resp[1], value_l | resp[1], masked_l, self.HEX_ASCII_CODE[masked_l]))
        return self.HEX_ASCII_CODE[masked_h], self.HEX_ASCII_CODE[masked_l]

    # TODO: Scale with num of VSRs..
    def debug_register(self, msb, lsb):  # pragma: no cover
        """Debug function: Display contents of register."""
        self.send_cmd([self.vsr_list[0].addr, self.READ_REG_VALUE,
                       msb, lsb])
        vsr2 = self.read_response()
        time.sleep(0.25)
        self.send_cmd([self.vsr_list[1].addr, self.READ_REG_VALUE,
                       msb, lsb])
        vsr1 = self.read_response()
        vsr2 = vsr2[2:-1]
        vsr1 = vsr1[2:-1]
        return (vsr2, vsr1)

    @run_on_executor(executor='thread_executor')
    def dump_all_registers(self):  # pragma: no cover
        """Dump register 0x00 - 0xff contents to screen.

        aSpect's address format: 0x3F -> 0x33, 0x46 (i.e. msb, lsb)
        See HEX_ASCII_CODE, and section 3.3, page 11 of revision 0.5:
        aS_AM_Hexitec_VSR_Interface.pdf
        """
        try:
            for msb in range(1):
                for lsb in range(2, 6):
                    (vsr2, vsr1) = self.debug_register(self.HEX_ASCII_CODE[msb],
                                                       self.HEX_ASCII_CODE[lsb])
                    print("  * Register: {}{}: VSR2: {}.{} VSR1: {}.{}".format(hex(msb),
                          hex(lsb)[-1], chr(vsr2[0]), chr(vsr2[1]), chr(vsr1[0]), chr(vsr1[1])))
                    time.sleep(0.25)
        except Exception as e:
            logging.error("dump_all_registers: {}".format(e))

    def convert_hex_to_hv(self, hex_value):
        """Convert hexadecimal value into HV voltage."""
        return (hex_value / 0xFFF) * 1250

    def convert_hv_to_hex(self, hv_value):
        """Convert HV voltage into hexadecimal value."""
        return int((hv_value / 1250) * 0xFFF)

    def convert_bias_to_dac_values(self, hv):
        """Convert bias level to DAC formatted values.

        I.e. 21 V -> 0x0041 (0x30, 0x30, 0x34, 0x31)
        """
        hv_hex = self.convert_hv_to_hex(hv)
        # print(" Selected hv: {0}. Converted to hex: {1:04X}".format(hv, hv_hex))
        hv_hex_msb = hv_hex >> 8
        hv_hex_lsb = hv_hex & 0xFF
        hv_msb = self.convert_to_aspect_format(hv_hex_msb)
        hv_lsb = self.convert_to_aspect_format(hv_hex_lsb)
        # print(" Conv'd to aSp_M: {}".format(hv_msb))
        # print(" Conv'd to aSp_L: {}".format(hv_lsb))
        return hv_msb, hv_lsb

    def hv_on(self):
        """Switch HV on."""
        logging.debug("Enable: [0xE3]")
        self.send_cmd([0xC0, 0xE3])
        time.sleep(0.5)

        logging.debug("Going to set HV bias to -{} volts".format(self.bias_level))
        hv_msb, hv_lsb = self.convert_bias_to_dac_values(self.bias_level)

        logging.debug("Write DAC: [0x54]")
        self.send_cmd([0xC0, 0x54, 0x30, 0x30, 0x30, 0x30,
                       0x30, 0x30, 0x30, 0x30,
                       0x30, 0x30, 0x30, 0x30,
                       hv_msb[0], hv_msb[1], hv_lsb[0], hv_lsb[1],
                       0x30, 0x30, 0x30, 0x30,
                       0x30, 0x30, 0x30, 0x30,
                       0x30, 0x30, 0x30, 0x30,
                       0x30, 0x30, 0x30, 0x30])
        self.read_response()
        self.hv_bias_enabled = True
        logging.debug("HV now ON")

    def hv_off(self):
        """Switch HV off."""
        logging.debug("Disable: [0xE2]")
        self.send_cmd([0xC0, 0xE2])
        # logging.debug("disabled, all done!")
        self.hv_bias_enabled = False
        logging.debug("HV now OFF")

    def environs(self):
        """Readout environmental data."""
        IOLoop.instance().add_callback(self.read_sensors)

    def reset_error(self):
        """Reset error message."""
        self._set_status_error("")
        self._set_status_message("")
        self.parent.software_state = "Cleared"

    def flag_error(self, message, e=None):
        """Place software into error state."""
        error_message = "{}".format(message)
        if e:
            error_message += ": {}".format(e)
        self._set_status_error(error_message)
        logging.error(error_message)
        self.parent.software_state = "Error"
        timestamp = self.create_timestamp()
        # Append to errors_history list, nested list of timestamp, error message
        self.errors_history.append([timestamp, error_message])

    def create_timestamp(self):
        """Returns timestamp of now."""
        return '{}'.format(datetime.now().strftime(HexitecFem.DATE_FORMAT))

    def get_log_messsages(self, last_message_timestamp):
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
            self.last_message_timestamp = self.create_timestamp()

        self.log_messages = [(str(timestamp), log_message) for timestamp, log_message in logs]


class HexitecFemError(Exception):   # pragma: no cover
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass
