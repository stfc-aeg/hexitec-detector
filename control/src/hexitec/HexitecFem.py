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
from RdmaUdp import *
from boardcfgstatus.BoardCfgStatus import *
from hexitec_vsr.VsrModule import VsrModule
import hexitec.ALL_RDMA_REGISTERS as HEX_REGISTERS

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
        self.gain_integer = -1
        self.adc1_delay = -1
        self.delay_sync_signals = -1
        self.vcal_on = -1
        self.vcal2_vcal1 = -1
        self.umid_value = -1
        self.vcal_value = -1

        self.vsrs_selected = 0
        self.vsr_addr_mapping = {1: 0x90, 2: 0x91, 3: 0x92, 4: 0x93, 5: 0x94, 6: 0x95}
        self.broadcast_VSRs = None
        self.vsr_list = []
        self.vcal_enabled = 0

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
            "vcal_enabled": (lambda: self.vcal_enabled, None),
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
                                     rdma_ip=self.camera_ctrl_ip_addr, rdma_port=61648,
                                     debug=False, uart_offset=0xC)
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

    # def get_health(self):
    #     """Get FEM health status."""
    #     return self.health

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
            self.data_path_reset()
            self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL['addr'],
                                          data=0x0,  burst_len=1)
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
            #     error = "{}".format(vsr_statuses)
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
        # print(" FEM -> UART: {} ({})".format(' '.join("0x{0:02X}".format(x) for x in cmd), cmd))
        self.x10g_rdma.uart_write(cmd)

    def read_response(self):
        """Read a VSR's microcontroller response, passed on by the FEM."""
        _ = self.x10g_rdma.uart_read_wait()
        # print(f"  read_resp, counter: {counter}")
        response = self.x10g_rdma.uart_read()
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


    # TODO: Reconstruct when data readout available
    # @run_on_executor(executor='thread_executor')
    def acquire_data(self):
        """Acquire data, poll fem for completion and read out fem monitors."""
        try:
            logging.info("Initiate Data Capture")
            self.acquire_start_time = self.create_timestamp()

            logging.debug("Reset frame number")
            self.frame_reset_to_zero()

            logging.debug("Reset path and clear buffers")
            self.data_path_reset()

            logging.debug(f"Set number frames to: {self.number_frames}")
            self.set_nof_frames(self.number_frames)

            # input("Press enter to enable data (200 ms)")
            logging.debug("Enable data")
            self.data_en(enable=True)
            time.sleep(0.2)

            # Stop data flow (free acquisition mode), reset setting if number of frames mode
            logging.debug("Disable data")
            self.data_en(enable=False)

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
                status = self.x10g_rdma.udp_rdma_read(address=HEX_REGISTERS.HEXITEC_2X6_HEADER_STATUS['addr'],
                                                      burst_len=1)[0]
                # 0 during data transmission, 65536 when completed
                self.all_data_sent = (status & 65536)
                # print(f"   *** all_data_sent: {self.all_data_sent:X} status: {status:X}")
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

    def stop_sm(self):
        """Stop the state machine in VSRs."""
        for vsr in self.vsr_list:
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

    def await_dc_captured(self):
        """Wait for the Dark Correction frames to be collected."""
        expected_duration = 8192 / self.parent.fem.frame_rate
        timeout = (expected_duration * 1.2) + 1
        poll_beginning = time.time()
        self._set_status_message("Collecting dark images..")
        dc_ready = False
        while not dc_ready:
            dc_statuses = self.check_dc_statuses()
            dc_ready = self.are_dc_ready(dc_statuses)
            if self.debug:   # pragma: no coverage
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

        # Column Read Enable ASIC1 (Reg 0x61) - checked 2
        asic1_col_read_enable = self._extract_80_bits("ColumnEn_", vsr_num, 1, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # self.load_enables_settings(vsr, 0x36, 0x31, asic1_col_read_enable, enables_defaults)

        # Column Read Enable ASIC2 (Reg 0xC2) - checked 1
        asic2_col_read_enable = self._extract_80_bits("ColumnEn_", vsr_num, 2, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # self.load_enables_settings(vsr, 0x43, 0x32, asic2_col_read_enable, enables_defaults)

        logging.debug("Column Power Enable")

        # Column Power Enable ASIC1 (Reg 0x4D) - checked 2
        asic1_col_power_enable = self._extract_80_bits("ColumnPwr", vsr_num, 1, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # self.load_enables_settings(vsr, 0x34, 0x44, asic1_col_power_enable, enables_defaults)

        # Column Power Enable ASIC2 (Reg 0xAE) - checked 1
        asic2_col_power_enable = self._extract_80_bits("ColumnPwr", vsr_num, 2, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # self.load_enables_settings(vsr, 0x41, 0x45, asic2_col_power_enable, enables_defaults)

        logging.debug("Column Calibration Enable")

        # Column Calibrate Enable ASIC1 (Reg 0x57) - checked 3
        asic1_col_cal_enable = self._extract_80_bits("ColumnCal", vsr_num, 1, "Channel")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        if asic1_col_cal_enable[0] > 0:
            # vsr.debug = True
            vsr.set_column_calibration_mask(asic1_col_cal_enable, asic=1)
        else:
            vsr.set_column_calibration_mask(enables_defaults, asic=1)

        # Column Calibrate Enable ASIC2 (Reg 0xB8) - checked 3
        asic2_col_cal_enable = self._extract_80_bits("ColumnCal", vsr_num, 2, "Channel")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        if asic2_col_cal_enable[0] > 0:
            vsr.set_column_calibration_mask(asic2_col_cal_enable, asic=2)
        else:
            vsr.set_column_calibration_mask(enables_defaults, asic=2)

        logging.debug("Row Read Enable")

        # Row Read Enable ASIC1 (Reg 0x43) - chcked 5
        asic1_row_enable = self._extract_80_bits("RowEn_", vsr_num, 1, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # self.load_enables_settings(vsr, 0x34, 0x33, asic1_row_enable, enables_defaults)

        # Row Read Enable ASIC2 (Reg 0xA4) - checked 4
        asic2_row_enable = self._extract_80_bits("RowEn_", vsr_num, 2, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # self.load_enables_settings(vsr, 0x41, 0x34, asic2_row_enable, enables_defaults)

        logging.debug("Row Power Enable")

        # Row Power Enable ASIC1 (Reg 0x2F) - checked 5
        asic1_row_power_enable = self._extract_80_bits("RowPwr", vsr_num, 1, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # self.load_enables_settings(vsr, 0x32, 0x46, asic1_row_power_enable, enables_defaults)

        # Row Power Enable ASIC2 (Reg 0x90) - chcked 4
        asic2_row_power_enable = self._extract_80_bits("RowPwr", vsr_num, 2, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        # self.load_enables_settings(vsr, 0x39, 0x30, asic2_row_power_enable, enables_defaults)

        logging.debug("Row Calibration Enable")

        # Row Calibrate Enable ASIC1 (Reg 0x39) - chcked 6
        asic1_row_cal_enable = self._extract_80_bits("RowCal", vsr_num, 1, "Block")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        if asic1_row_cal_enable[0] > 0:
            vsr.set_row_calibration_mask(asic1_row_cal_enable, asic=1)
        else:
            vsr.set_row_calibration_mask(enables_defaults, asic=1)

        # Row Calibrate Enable ASIC2 (Reg 0x9A) - checked 6
        asic2_row_cal_enable = self._extract_80_bits("RowCal", vsr_num, 2, "Block")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        if asic2_row_cal_enable[0] > 0:
            vsr.set_row_calibration_mask(asic2_row_cal_enable, asic=2)
        else:
            vsr.set_row_calibration_mask(enables_defaults, asic=2)

        logging.debug("Power, Cal and Read Enables have been loaded")

    def make_list_hexadecimal(self, value):  # pragma: no cover
        """Debug function: Turn decimal list into hexadecimal list."""
        value_hexadecimal = []
        for val in value:
            value_hexadecimal.append("0x%x" % val)
        return value_hexadecimal


   
    @run_on_executor(executor='thread_executor')
    def initialise_system(self):
        """Configure in full all VSRs.

        Initialise, load enables, set up state machine, write to DAC and enable ADCs.
        """
        try:
            expected_duration = 8192 / self.parent.fem.frame_rate
            timeout = (expected_duration * 1.2) + 1
            self.hardware_busy = True
            for vsr in self.vsr_list:
                logging.debug(" --- Initialising VSR: 0x{0:X} ---".format(vsr.addr))
                self._set_status_message("Initialising VSR{}..".format(vsr.addr-143))
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
                            vsr.addr-143, time_taken))
                        raise HexitecFemError("Timed out awaiting DC Capture Ready")

                logging.debug("VSR{0:X} DC Capture ready took: {1} s".format(
                    vsr.addr-143, round(time_taken, 3)))

            logging.debug("LVDS Training")
            self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                          data=0x10, burst_len=1, comment=" ")  # EN_TRAINING
            time.sleep(0.2)
            self.x10g_rdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                          data=0x00, burst_len=1, comment=" ")  # Disable training

            number_vsrs = len(self.vsr_addr_mapping.keys())
            vsr_lock_status = self.x10g_rdma.udp_rdma_read(address=0x3e8, burst_len=number_vsrs)
            for vsr in self.vsr_list:
                if vsr_lock_status[vsr.slot-1] == 255:
                    logging.debug(f"VSR{vsr.slot} lock_status: {vsr_lock_status[vsr.slot-1]}")
                else:
                    logging.error(f"VSR{vsr.slot} lock_status: {vsr_lock_status[vsr.slot-1]}")

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
                # vsr.start_trigger_sm()
                # print(f"sm triggered for vsr{vsr.slot}")
            print("-"*10)

            self.x10g_rdma.udp_rdma_write(address=0x1c, data=0x1, burst_len=1)
            print("fpga state machine enabled")

            self._set_status_message("Initialisation completed. VSRs configured.")
            print(" -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=- ")
            ending = time.time()
            print("     initialisation took: {}".format(ending-beginning))

            # DEBUGGING Info:
            # self.debugging_function()
            # DEBUGGING completed
            self.parent.software_state = "Idle"
        except HexitecFemError as e:
            self.flag_error("Failed to initialise camera", str(e))
        except Exception as e:
            self.flag_error("Camera initialisation failed", str(e))
        self.hardware_busy = False

    def initialise_vsr(self, vsr):  # pragma: no coverage
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

        # # TODO Uncomment whenever hardware available to test against:
        logging.debug("Writing config to VSR..")
        vsr.initialise()


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
        """Update DAC values, provided by hexitec file."""
        logging.debug("Updating DAC values")
        if self.umid_value > -1:
            vsr.set_dac_umid(self.umid_value)
        if self.vcal_value > -1:
            vsr.set_dac_vcal(self.vcal_value)

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
            self.hv_list[index] = vsr.get_power_sensors()
        else:
            raise HexitecFemError("Power Voltages: Invalid VSR index: {}".format(index))

    def read_temperatures_humidity_values(self, vsr):
        """Read and convert sensor data into temperatures and humidity values."""
        if vsr.addr not in self.vsr_addr_mapping.values():
            raise HexitecFemError("Sensors: Invalid VSR address(0x{0:02X})".format(vsr.addr))
        sensors_values = vsr._get_env_sensors()

        index = vsr.addr - self.vsr_base_address
        if (0 <= index <= 5):
            self.ambient_list[index] = float(sensors_values[0])
            self.humidity_list[index] = float(sensors_values[1])
            self.asic1_list[index] = float(sensors_values[2])
            self.asic2_list[index] = float(sensors_values[3])
            self.adc_list[index] = float(sensors_values[4])
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

            self.gain_integer = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Gain', bit_range=1)
            if self.gain_integer > -1:
                if self.gain_integer == 0:
                    self.gain_string = "high"
                else:
                    self.gain_string = "low"
            self.adc1_delay = self._extract_integer(
                self.hexitec_parameters, 'Control-Settings/ADC1 Delay', bit_range=2)
            self.delay_sync_signals = self._extract_integer(
                self.hexitec_parameters, 'Control-Settings/delay sync signals', bit_range=8)
            self.vcal_on = self._extract_integer(self.hexitec_parameters, 'Control-Settings/vcal_enabled',
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
            # print("\n *** self.umid_value: {0} \n".format(self.umid_value))

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

        int_list = [-1]

        key = 'Sensor-Config_V%s_S%s/%s1st%s' % (vsr, asic, param, channel_or_block)
        try:
            first_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return int_list

        key = 'Sensor-Config_V%s_S%s/%s2nd%s' % (vsr, asic, param, channel_or_block)
        try:
            second_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return int_list

        key = 'Sensor-Config_V%s_S%s/%s3rd%s' % (vsr, asic, param, channel_or_block)
        try:
            third_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return int_list

        key = 'Sensor-Config_V%s_S%s/%s4th%s' % (vsr, asic, param, channel_or_block)
        try:
            fourth_channel = self.extract_channel_data(self.hexitec_parameters, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return int_list

        entirety = first_channel + second_channel + third_channel + fourth_channel
        if bDebug:  # pragma: no cover
            print("   1st: %s" % first_channel)
            print("   2nd: %s" % second_channel)
            print("   3rd: %s" % third_channel)
            print(f"   4th: {fourth_channel}, ({type(fourth_channel)})")
            print("   entirety: %s" % entirety)
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
        int_list = []
        for binary in byte_list:
            int_byte = int(binary, 2)
            int_list.append(int_byte)
            if bDebug:  # pragma: no cover
                print("\t\tVSR: %s   bin: %s dec: %s" % (vsr, binary, "{:02x}".format(int_byte)))

        return int_list

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

    # def mask_aspect_encoding(self, value_h, value_l, resp):
    #     """Mask values honouring aspect encoding.

    #     Aspect: 0x30 = 1, 0x31 = 1, .., 0x39 = 9, 0x41 = A, 0x42 = B, .., 0x46 = F.
    #     Therefore increase values between 0x39 and 0x41 by 7 to match aspect's legal range.
    #     I.e. 0x39 | 0x32 = 0x3B, + 7 = 0x42.
    #     """
    #     value_h = self.translate_to_normal_hex(value_h)
    #     value_l = self.translate_to_normal_hex(value_l)
    #     resp[0] = self.translate_to_normal_hex(resp[0])
    #     resp[1] = self.translate_to_normal_hex(resp[1])
    #     masked_h = value_h | resp[0]
    #     masked_l = value_l | resp[1]
    #     # print("h: {0:X} r: {1:X} = {2:X} masked: {3:X} I.e. {4:X}".format(
    #     #     value_h, resp[0], value_h | resp[0], masked_h, self.HEX_ASCII_CODE[masked_h]))
    #     # print("l: {0:X} r: {1:X} = {2:X} masked: {3:X} I.e. {4:X}".format(
    #     #     value_l, resp[1], value_l | resp[1], masked_l, self.HEX_ASCII_CODE[masked_l]))
    #     return self.HEX_ASCII_CODE[masked_h], self.HEX_ASCII_CODE[masked_l]



    @run_on_executor(executor='thread_executor')

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
        logging.debug("Going to set HV bias to -{} volts".format(self.bias_level))
        self._set_status_message(f"HV bias set to -{self.bias_level} V")
        hv_msb, hv_lsb = self.convert_bias_to_dac_values(self.bias_level)
        print(f" HV Bias (-{self.bias_level}) : {hv_msb[0]:X} {hv_msb[1]:X}",
              " | {hv_lsb[0]:X} {hv_lsb[1]:X}")

        self.vsr_list[0].hv_on(hv_msb, hv_lsb)
        self.hv_bias_enabled = True
        logging.debug("HV now ON")

    def hv_off(self):
        """Switch HV off."""
        logging.debug("Disable: [0xE2]")
        self.send_cmd([0xC0, 0xE2])
        self._set_status_message("HV turned off")
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
        logging.debug("Number of frames set to 0x{0:X}".format(number_frames))

    def data_en(self, enable=True):
        if enable:
            self.set_bit(HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL, "DATA_EN")
        else:
            self.reset_bit(HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL, "DATA_EN")


class HexitecFemError(Exception):   # pragma: no cover
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass
