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

# from hexitec.test_ui.RdmaUDP import RdmaUDP
from hexitec.RdmaUDP import RdmaUDP     # Satisfy tox

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

    OPTIONS = [
        "Sensor_1_1",
        "Sensor_1_2",
        "Sensor_2_1",
        "Sensor_2_2"
    ]

    IMAGE = [
        "LOG HDF5 FILE",
        "LOG BIN FILE",
        "STREAM DATA",
        "NETWORK PACKETS ONLY"
    ]

    READOUTMODE = [
        "SINGLE",
        "2x2"
    ]

    # VSR_ADDRESS = [0x90]
    VSR_ADDRESS = range(0x90, 0x96, 1)

    SENSORS_READOUT_OK = 7

    HEX_ASCII_CODE = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                      0x41, 0x42, 0x43, 0x44, 0x45, 0x46]

    DAC_SCALE_FACTOR = 0.732

    SEND_REG_VALUE = 0x40   # Verified to work with F/W UART
    READ_REG_VALUE = 0x41   # Verified to work with F/W UART
    SET_REG_BIT = 0x42      # Tolerated in collect_offsets
    CLR_REG_BIT = 0x43      # Not verified, tolerated in: enable_adc, "Enable Vcal", collect_offsets
    SEND_REG_BURST = 0x44   # Avoid - 2x2 usage in load_power_..enables()
    READ_PWR_VOLT = 0x50    # Not used
    WRITE_REG_VAL = 0x53    # Avoid
    WRITE_DAC_VAL = 0x54    # Tolerated in: write_dac_values
    CTRL_ADC_DAC = 0x55     # Tolerated twice in: enable_adc

    # Define timestamp format
    DATE_FORMAT = '%Y%m%d_%H%M%S.%f'

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
        # logging.info("server_ctrl_ip_addr={}, camera_ctrl_ip_addr={}".format(server_ctrl_ip_addr, camera_ctrl_ip_addr))
        # logging.info("server_data_ip_addr={}, camera_data_ip_addr={}".format(server_data_ip_addr, camera_data_ip_addr))
        # Give access to parent class (Hexitec)
        self.parent = parent
        self.x10g_rdma = None

        # 10G RDMA IP addresses
        self.server_ctrl_ip_addr = server_ctrl_ip_addr
        self.camera_ctrl_ip_addr = camera_ctrl_ip_addr

        # FPGA base addresses
        self.rdma_addr = {
            "receiver": 0xC0000000,
            "frm_gate": 0xD0000000,
            "reset_monitor": 0x90000000
        }

        self.image_size_x = 0x100
        self.image_size_y = 0x100
        self.image_size_p = 0x8
        self.image_size_f = 0x8

        self.strm_mtu = 8000

        self.vsr_addr = HexitecFem.VSR_ADDRESS[0]

        self.number_frames = 10
        self.number_frames_backed_up = 0

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
        self.frame_rate = 0
        self.duration = 1
        self.duration_enabled = False
        self.duration_remaining = 0

        self.bias_refresh_interval = 60.0
        self.bias_voltage_refresh = False
        self.time_refresh_voltage_held = 3.0
        self.bias_voltage_settle_time = 2.0

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

        self.selected_sensor = HexitecFem.OPTIONS[2]        # "Sensor_2_1"
        self.sensors_layout = HexitecFem.READOUTMODE[1]     # "2x2"

        self.vsr1_ambient = 0
        self.vsr1_humidity = 0
        self.vsr1_asic1 = 0
        self.vsr1_asic2 = 0
        self.vsr1_adc = 0
        self.vsr1_hv = 0
        self.vsr1_sync = -1

        self.vsr2_ambient = 0
        self.vsr2_humidity = 0
        self.vsr2_asic1 = 0
        self.vsr2_asic2 = 0
        self.vsr2_adc = 0
        self.vsr2_hv = 0
        self.vsr2_sync = -1

        self.vsr3_ambient = 0
        self.vsr3_humidity = 0
        self.vsr3_asic1 = 0
        self.vsr3_asic2 = 0
        self.vsr3_adc = 0
        self.vsr3_hv = 0
        self.vsr3_sync = -1

        self.vsr4_ambient = 0
        self.vsr4_humidity = 0
        self.vsr4_asic1 = 0
        self.vsr4_asic2 = 0
        self.vsr4_adc = 0
        self.vsr4_hv = 0
        self.vsr4_sync = -1

        self.vsr5_ambient = 0
        self.vsr5_humidity = 0
        self.vsr5_asic1 = 0
        self.vsr5_asic2 = 0
        self.vsr5_adc = 0
        self.vsr5_hv = 0
        self.vsr5_sync = -1

        self.vsr6_ambient = 0
        self.vsr6_humidity = 0
        self.vsr6_asic1 = 0
        self.vsr6_asic2 = 0
        self.vsr6_adc = 0
        self.vsr6_hv = 0
        self.vsr6_sync = -1

        # TODO: Placeholder, not yet implemented in hardware
        self.hv_bias_enabled = False

        self.read_firmware_version = True
        self.firmware_date = "N/A"
        self.firmware_time = "N/A"

        # Variables supporting handling of ini-style hexitec config file
        self.hexitec_config = "(Blank)"
        self.hexitec_parameters = {}

        self.acquire_start_time = ""
        self.acquire_stop_time = ""
        self.acquire_time = 0.0
        self.acquire_timestamp = 0
        self.offsets_timestamp = 0

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
            "frame_rate": (lambda: self.frame_rate, None),
            "health": (lambda: self.health, None),
            "status_message": (self._get_status_message, None),
            "status_error": (self._get_status_error, None),
            "number_frames": (self.get_number_frames, self.set_number_frames),
            "duration": (self.get_duration, self.set_duration),
            "duration_remaining": (lambda: self.duration_remaining, None),
            "hexitec_config": (lambda: self.hexitec_config, self._set_hexitec_config),
            "read_sensors": (None, self.read_sensors),
            "hardware_connected": (lambda: self.hardware_connected, None),
            "hardware_busy": (lambda: self.hardware_busy, None),
            "firmware_date": (lambda: self.firmware_date, None),
            "firmware_time": (lambda: self.firmware_time, None),
            "vsr1_sync": (lambda: self.vsr1_sync, None),
            "vsr2_sync": (lambda: self.vsr2_sync, None),
            "vsr3_sync": (lambda: self.vsr1_sync, None),
            "vsr4_sync": (lambda: self.vsr2_sync, None),
            "vsr5_sync": (lambda: self.vsr1_sync, None),
            "vsr6_sync": (lambda: self.vsr2_sync, None),
            "vsr1_sensors": {
                "ambient": (lambda: self.vsr1_ambient, None),
                "humidity": (lambda: self.vsr1_humidity, None),
                "asic1": (lambda: self.vsr1_asic1, None),
                "asic2": (lambda: self.vsr1_asic2, None),
                "adc": (lambda: self.vsr1_adc, None),
                "hv": (lambda: self.vsr1_hv, None),
            },
            "vsr2_sensors": {
                "ambient": (lambda: self.vsr2_ambient, None),
                "humidity": (lambda: self.vsr2_humidity, None),
                "asic1": (lambda: self.vsr2_asic1, None),
                "asic2": (lambda: self.vsr2_asic2, None),
                "adc": (lambda: self.vsr2_adc, None),
                "hv": (lambda: self.vsr2_hv, None),
            },
            "vsr3_sensors": {
                "ambient": (lambda: self.vsr3_ambient, None),
                "humidity": (lambda: self.vsr3_humidity, None),
                "asic1": (lambda: self.vsr3_asic1, None),
                "asic2": (lambda: self.vsr3_asic2, None),
                "adc": (lambda: self.vsr3_adc, None),
                "hv": (lambda: self.vsr3_hv, None),
            },
            "vsr4_sensors": {
                "ambient": (lambda: self.vsr4_ambient, None),
                "humidity": (lambda: self.vsr4_humidity, None),
                "asic1": (lambda: self.vsr4_asic1, None),
                "asic2": (lambda: self.vsr4_asic2, None),
                "adc": (lambda: self.vsr4_adc, None),
                "hv": (lambda: self.vsr4_hv, None),
            },
            "vsr5_sensors": {
                "ambient": (lambda: self.vsr5_ambient, None),
                "humidity": (lambda: self.vsr5_humidity, None),
                "asic1": (lambda: self.vsr5_asic1, None),
                "asic2": (lambda: self.vsr5_asic2, None),
                "adc": (lambda: self.vsr5_adc, None),
                "hv": (lambda: self.vsr5_hv, None),
            },
            "vsr6_sensors": {
                "ambient": (lambda: self.vsr6_ambient, None),
                "humidity": (lambda: self.vsr6_humidity, None),
                "asic1": (lambda: self.vsr6_asic1, None),
                "asic2": (lambda: self.vsr6_asic2, None),
                "adc": (lambda: self.vsr6_adc, None),
                "hv": (lambda: self.vsr6_hv, None),
            }
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
            self.x10g_rdma = RdmaUDP(self.server_ctrl_ip_addr, 61649,
                                     self.camera_ctrl_ip_addr, 61648,
                                     9000, 0.5, self.debug, unique_cmd_no=False)
            self.x10g_rdma.setDebug(False)
            self.x10g_rdma.ack = False  # True
        except socket_error as e:
            raise socket_error("Failed to setup Control connection: %s" % e)
        return

    @run_on_executor(executor='thread_executor')
    def read_sensors(self, msg=None):
        """Read environmental sensors and updates parameter tree with results."""
        try:
            beginning = time.time()
            # Note once, when firmware was built
            # if self.read_firmware_version:
            #     date = self.x10g_rdma.read(0x60000015, burst_len=1, comment='FIRMWARE DATE')
            #     time = self.x10g_rdma.read(0x60000016, burst_len=1, comment='FIRMWARE TIME')
            #     date = format(date, '#010x')
            #     time = format(time, '#06x')
            #     self.firmware_date = "{0:.2}/{1:.2}/{2:.4}".format(date[2:4], date[4:6], date[6:10])
            #     self.firmware_time = "{0:.2}:{1:.2}".format(time[2:4], time[4:6])
            #     self.read_firmware_version = False
            vsr = self.vsr_addr
            for VSR in self.VSR_ADDRESS:
                self.vsr_addr = VSR
                self.read_temperatures_humidity_values()
                self.read_pwr_voltages()  # pragma: no cover
            self.vsr_addr = vsr  # pragma: no cover
            ending = time.time()
            print(" Environmental data took: {}".format(ending - beginning))
        except HexitecFemError as e:
            self._set_status_error("Failed to read sensors: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Reading sensors failed: %s" % str(e))
            logging.error("%s" % str(e))

    def disconnect(self):
        """Disconnect hardware connection."""
        self.x10g_rdma.close()

    def cleanup(self):
        """Cleanup connection."""
        self.disconnect()

    def frame_gate_trigger(self):
        """Reset monitors, pulse frame gate."""
        # the reset of monitors suggested by Rob:
        self.x10g_rdma.write(self.rdma_addr["reset_monitor"] + 0, 0x0, burst_len=1, comment='reset monitor off')
        self.x10g_rdma.write(self.rdma_addr["reset_monitor"] + 0, 0x1, burst_len=1, comment='reset monitor on')
        self.x10g_rdma.write(self.rdma_addr["reset_monitor"] + 0, 0x0, burst_len=1, comment='reset monitor off')

        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 0, 0x0, burst_len=1, comment='frame gate trigger off')
        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 0, 0x1, burst_len=1, comment='frame gate trigger on')
        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 0, 0x0, burst_len=1, comment='frame gate trigger off')

    def frame_gate_settings(self, frame_number, frame_gap):
        """Set frame gate settings."""
        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 1, frame_number, burst_len=1,
                             comment='frame gate frame number')
        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 2, frame_gap, burst_len=1, comment='frame gate frame gap')

    def data_stream(self, num_images):
        """Trigger FEM to output data."""
        self.frame_gate_settings(num_images - 1, 0)
        self.frame_gate_trigger()

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
        # print("\n\tfem.set_number_frames({}) > number_frames {} duration {}\n".format(frames, self.number_frames, self.number_frames / self.frame_rate))
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
        # print("\n\tfem.set_duration({}) frames {}\n".format(duration, self.duration * self.frame_rate))
        self.duration = duration
        frames = self.duration * self.frame_rate
        self.number_frames = int(round(frames))

    def get_health(self):
        """Get FEM health status."""
        return self.health

    def _start_polling(self):  # pragma: no cover
        # TODO: Still need IOLoop call if sensor polling is scrapped
        # IOLoop.instance().call_later(4.0, self.poll_sensors)  # If polling env data
        IOLoop.instance().add_callback(self.poll_sensors)   # Not polling sensors

    def poll_sensors(self):
        """Poll hardware while connected but not busy initialising, collecting offsets, etc."""
        # if self.hardware_connected and (self.hardware_busy is False):
        #     self.read_sensors()
        #     # print(" * poll_sensors() not reading sensors *")
        # IOLoop.instance().call_later(3.0, self.poll_sensors)

    # @run_on_executor(executor='thread_executor')
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
            self._set_status_error("%s" % str(e))
            self._set_status_message("Is the camera powered?")
            logging.error("%s" % str(e))
        except Exception as e:
            error = "Uncaught Exception; Camera connection: %s" % str(e)
            self._set_status_error(error)
            logging.error("Camera connection: %s" % str(e))
            # Cannot raise error beyond current thread

    def power_up_modules(self):
        """Power up and enable VSRs."""
        try:
            self.connect()
            self.hardware_connected = True
            self._set_status_message("Camera connected.")
            logging.debug("UDP connection established")

            self.x10g_rdma.enable_all_vsrs()
            expected_value = 0x3F   # 0x1
            read_value = self.x10g_rdma.power_status()
            if (read_value == expected_value):
                print(" OK Power: 0x{0:08X}".format(read_value))
            else:
                message = "Expected 0x{0:02X} not 0x{1:02X}".format(expected_value, read_value)
                logging.error("Not all VSRs powered up, {}".format(message))
                raise HexitecFemError("Powering VSRs Error, {}".format(message))
            powering_delay = 10
            print("    VSR(s) enabled; Waiting {} seconds".format(powering_delay))
            self._set_status_message("Waiting {} seconds (VSRs booting)".format(powering_delay))
            IOLoop.instance().call_later(powering_delay, self.cam_connect)    # self.powering_modules_completed)
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
            self.initialise_system()
        except HexitecFemError as e:
            self._set_status_error("Failed to initialise camera: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Camera initialisation failed: %s" % str(e))
            logging.error("%s" % str(e))

    def check_all_processes_ready(self):
        """Wait until DAQ, Odin adapters ready or in error."""
        if self.parent.daq.in_error:
            # Reset variables
            self.hardware_busy = False
        elif not self.parent.daq.in_progress:
            IOLoop.instance().call_later(0.5, self.check_all_processes_ready)
        else:
            self.collect_data()

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
            self._set_status_message("Acquiring data..")
            self.acquire_data()
        except HexitecFemError as e:
            self._set_status_error("Failed to collect data: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Data collection failed: %s" % str(e))
            logging.error("%s" % str(e))

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
        except HexitecFemError as e:
            self._set_status_error("Failed to disconnect: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Disconnection failed: %s" % str(e))
            logging.error("%s" % str(e))

    def set_debug(self, debug):
        """Set debug messages on or off."""
        self.debug = debug

    def get_debug(self):
        """Get debug messages status."""
        return self.debug

    def send_cmd(self, cmd):
        """Send a command string to the microcontroller."""
        # print("Send to UART: {}  ({})".format(' '.join("0x{0:02X}".format(x) for x in cmd), cmd))
        self.x10g_rdma.uart_tx(cmd)

    def read_response(self):
        """Read a VSR's microcontroller response, passed on by the FEM."""
        counter = 0
        rx_pkt_done = 0
        while not rx_pkt_done:
            uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done = self.x10g_rdma.read_uart_status()
            counter += 1
            # if counter % 100 == 0:
            #     print("{0:05} UART: {1:08X} tx_buff_full: {2:0X} tx_buff_empty: {3:0X} rx_buff_full: {4:0X} rx_buff_empty: {5:0X} rx_pkt_done: {6:0X}".format(
            #         counter, uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done))
            if counter == 15001:
                logging.error("\n\t read_response() timed out waiting for uart!\n")
                break
        # print("{0:05} UART: {1:08X} tx_buff_full: {2:0X} tx_buff_empty: {3:0X} rx_buff_full: {4:0X} rx_buff_empty: {5:0X} rx_pkt_done: {6:0X}".format(
        #     counter, uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done))

        response = self.x10g_rdma.uart_rx(0x0)
        # print("R: {}.  ({}). {}".format(' '.join("0x{0:02X}".format(x) for x in response), response, counter))
        return response

    def cam_connect(self):
        """Send init command(s) to VSRs."""
        try:
            # for vsr in self.VSR_ADDRESS:
            self.x10g_rdma.uart_tx([0xFF, 0xE3])
            print("\nInit modules (Sent 0xE3..)\n")
            self._set_status_message("Waiting 5 seconds (VSRs initialising)")
            IOLoop.instance().call_later(5, self.cam_connect_completed)
        except socket_error as e:
            self.hardware_connected = False
            self.hardware_busy = False
            raise HexitecFemError(e)

    def cam_connect_completed(self):
        """Complete VSRs initialisation."""
        try:
            self._set_status_message("VSRs initialised")
            print("\n\t INITIALISED\n")
            logging.debug("Modules Enabled")
        except socket_error as e:
            self.hardware_connected = False
            raise HexitecFemError(e)
        self.hardware_busy = False

        # Start polling thread (connect successfully set up)
        if len(self.status_error) == 0:
            self._start_polling()

    def cam_disconnect(self):
        """Send commands to disconnect camera."""
        self.hardware_connected = False
        try:
            for vsr in self.VSR_ADDRESS:
                self.send_cmd([vsr, 0xE2])
            logging.debug("Modules Disabled")
            self.disconnect()
            logging.debug("Camera is Disconnected")
        except socket_error as e:
            logging.error("Unable to disconnect camera: %s" % str(e))
            raise HexitecFemError(e)
        except AttributeError as e:
            logging.error("Unable to disconnect camera: %s" % "No active connection")
            raise HexitecFemError("%s; %s" % (e, "No active connection"))

    def print_firmware_info(self):  # pragma: no cover
        """Print info on loaded firmware.

        0x80: F/W customer ID
        0x81: F/W Project ID
        0x82: F/W Version ID.
        """
        print("__________F/W Customer, Project, and Version IDs__________")
        for index in range(3):
            (vsr2, vsr1) = self.debug_register(0x38, 0x30+index)
            print("   Register 0x8{}, VSR2: {} VSR1: {}".format(index, vsr2, vsr1))
        print("__________________________________________________________")

    # TODO: 2x2 Legacy code, to be reconstructed
    @run_on_executor(executor='thread_executor')
    def acquire_data(self):  # noqa: C901
        """Acquire data, poll fem for completion and read out fem monitors."""
        # If called as part of cold initialisation, only need one frame so
        #   temporarily overwrite UI's number of frames for this call only
        self.number_frames_backed_up = self.number_frames

        self.x10g_rdma.write(0xD0000001, self.number_frames - 1, burst_len=1, comment='Frame Gate set to \
            self.number_frames')

        full_empty = self.x10g_rdma.read(0x60000011, burst_len=1, comment='Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)

        full_empty = self.x10g_rdma.read(0x60000012, burst_len=1, comment='Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)

        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            logging.debug("Reading out single sensor")
            mux_mode = 0
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            mux_mode = 8
            logging.debug("Reading out 2x2 sensors")

        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.x10g_rdma.write(0x60000004, 0 + mux_mode, burst_len=1, comment='Sensor 1 1')
            logging.debug("Sensor 1 1")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.x10g_rdma.write(0x60000004, 4 + mux_mode, burst_len=1, comment='Sensor 2 1')
            logging.debug("Sensor 2 1")

        # Flush the input FIFO buffers
        self.x10g_rdma.write(0x60000002, 32, burst_len=1, comment='Clear Input Buffers')
        self.x10g_rdma.write(0x60000002, 0, burst_len=1, comment='Clear Input Buffers')
        full_empty = self.x10g_rdma.read(0x60000011, burst_len=1, comment='Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.x10g_rdma.read(0x60000012, burst_len=1, comment='Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)

        if self.sensors_layout == HexitecFem.READOUTMODE[1]:
            self.x10g_rdma.write(0x60000002, 4, burst_len=1, comment='Enable State Machine')

        if self.debug:
            logging.debug("number of Frames := %s" % self.number_frames)

        logging.info("Initiate Data Capture")
        self.data_stream(self.number_frames)
        self.acquire_start_time = '%s' % (datetime.now().strftime(HexitecFem.DATE_FORMAT))
        # How to convert datetime object to float?
        self.acquire_timestamp = time.time()    # Utilised by adapter's watchdog

        self.waited = 0.1
        IOLoop.instance().call_later(0.1, self.check_acquire_finished)

    def check_acquire_finished(self):
        """Check whether all data transferred, until completed or cancelled by user."""
        try:
            delay = 0.10
            reply = 0
            # Stop if user clicked on Cancel button
            if (self.stop_acquisition):
                logging.debug(" -=-=-=- HexitecFem told to cancel acquisition -=-=-=-")
                self.acquire_data_completed()
                return
            else:
                reply = self.x10g_rdma.read(0x60000014, burst_len=1, comment='Check data transfer completed?')
                if reply > 0:
                    self.acquire_data_completed()
                    return
                else:
                    self.waited += delay
                    if self.duration_enabled:
                        self.duration_remaining = round((self.duration - self.waited), 1)
                        if self.duration_remaining < 0:
                            self.duration_remaining = 0
                        # print("\t dur'n_remain'g: {} secs".format(self.duration_remaining))
                    IOLoop.instance().call_later(delay, self.check_acquire_finished)
                    return
        except HexitecFemError as e:
            self._set_status_error("Failed to collect data: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Data collection failed: %s" % str(e))
            logging.error("%s" % str(e))

        # Acquisition interrupted
        self.acquisition_completed = True

    # TODO: 2x2 Legacy code, to be reconstructed
    def acquire_data_completed(self):
        """Reset variables and read out Firmware monitors post data transfer."""
        self.acquire_stop_time = '%s' % (datetime.now().strftime(HexitecFem.DATE_FORMAT))
        # Stop the state machine
        self.x10g_rdma.write(0x60000002, 0, burst_len=1, comment='Dis-Enable State Machine')

        # Clear enable signal
        self.x10g_rdma.write(0xD0000000, 2, burst_len=1, comment='Clear enable signal')
        self.x10g_rdma.write(0xD0000000, 0, burst_len=1, comment='Clear enable signal')

        if self.stop_acquisition:
            logging.info("Cancelling Acquisition..")
            for vsr in self.VSR_ADDRESS:
                self.send_cmd([vsr, 0xE2])
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

        # Clear the Mux Mode bit
        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.x10g_rdma.write(0x60000004, 0, burst_len=1, comment='Sensor 1 1')
            logging.debug("Sensor 1 1")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.x10g_rdma.write(0x60000004, 4, burst_len=1, comment='Sensor 2 1')
            logging.debug("Sensor 2 1")
        full_empty = self.x10g_rdma.read(0x60000011, burst_len=1, comment='Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.x10g_rdma.read(0x60000012, burst_len=1, comment='Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        no_frames = self.x10g_rdma.read(0xD0000001, burst_len=1, comment='Check Number of Frames setting') + 1
        logging.debug("Number of Frames: %s" % no_frames)

        logging.debug("Output from Sensor")
        m0 = self.x10g_rdma.read(0x70000010, burst_len=1, comment='frame last length')
        logging.debug("frame last length: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000011, burst_len=1, comment='frame max length')
        logging.debug("frame max length: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000012, burst_len=1, comment='frame min length')
        logging.debug("frame min length: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000013, burst_len=1, comment='frame number')
        logging.debug("frame number: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000014, burst_len=1, comment='frame last clock cycles')
        logging.debug("frame last clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000015, burst_len=1, comment='frame max clock cycles')
        logging.debug("frame max clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000016, burst_len=1, comment='frame min clock cycles')
        logging.debug("frame min clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000017, burst_len=1, comment='frame data total')
        logging.debug("frame data total: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000018, burst_len=1, comment='frame data total clock cycles')
        logging.debug("frame data total clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000019, burst_len=1, comment='frame trigger count')
        logging.debug("frame trigger count: %s" % m0)
        m0 = self.x10g_rdma.read(0x7000001A, burst_len=1, comment='frame in progress flag')
        logging.debug("frame in progress flag: %s" % m0)

        logging.debug("Output from Frame Gate")
        m0 = self.x10g_rdma.read(0x80000010, burst_len=1, comment='frame last length')
        logging.debug("frame last length: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000011, burst_len=1, comment='frame max length')
        logging.debug("frame max length: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000012, burst_len=1, comment='frame min length')
        logging.debug("frame min length: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000013, burst_len=1, comment='frame number')
        logging.debug("frame number: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000014, burst_len=1, comment='frame last clock cycles')
        logging.debug("frame last clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000015, burst_len=1, comment='frame max clock cycles')
        logging.debug("frame max clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000016, burst_len=1, comment='frame min clock cycles')
        logging.debug("frame min clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000017, burst_len=1, comment='frame data total')
        logging.debug("frame data total: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000018, burst_len=1, comment='frame data total clock cycles')
        logging.debug("frame data total clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000019, burst_len=1, comment='frame trigger count')
        logging.debug("frame trigger count: %s" % m0)
        m0 = self.x10g_rdma.read(0x8000001A, burst_len=1, comment='frame in progress flag')
        logging.debug("frame in progress flag: %s" % m0)

        logging.debug("Input to XAUI")  # Conn'd to 10G core going out
        m0 = self.x10g_rdma.read(0x90000010, burst_len=1, comment='frame last length')
        logging.debug("frame last length: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000011, burst_len=1, comment='frame max length')
        logging.debug("frame max length: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000012, burst_len=1, comment='frame min length')
        logging.debug("frame min length: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000013, burst_len=1, comment='frame number')
        logging.debug("frame number: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000014, burst_len=1, comment='frame last clock cycles')
        logging.debug("frame last clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000015, burst_len=1, comment='frame max clock cycles')
        logging.debug("frame max clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000016, burst_len=1, comment='frame min clock cycles')
        logging.debug("frame min clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000017, burst_len=1, comment='frame data total')
        logging.debug("frame data total: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000018, burst_len=1, comment='frame data total clock cycles')
        logging.debug("frame data total clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000019, burst_len=1, comment='frame trigger count')
        logging.debug("frame trigger count: %s" % m0)
        m0 = self.x10g_rdma.read(0x9000001A, burst_len=1, comment='frame in progress flag')
        logging.debug("frame in progress flag: %s" % m0)

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

    # TODO: 2x2 Legacy code, to be removed - checked
    def set_up_state_machine(self):
        """Set up state machine, optionally with values from hexitec ini file."""
        logging.debug("Setting up state machine")

        # Establish register values, default values
        register_002 = 0x30, 0x32
        register_003 = 0x30, 0x33
        register_004 = 0x30, 0x34
        register_005 = 0x30, 0x35
        register_006 = 0x30, 0x36
        register_007 = 0x30, 0x37
        register_009 = 0x30, 0x39
        register_00E = 0x30, 0x45
        register_018 = 0x31, 0x38
        register_019 = 0x31, 0x39
        register_01B = 0x31, 0x42
        register_014 = 0x31, 0x34

        value_002 = 0x30, 0x31  # RowS1 Low Byte value: 1 = maximum frame rate
        value_003 = 0x30, 0x30  # RowS1 High Byte value : 0 = ditto
        value_004 = 0x30, 0x31  # S1 -> Sph, 6 bits : 1 = ... Yes, what?
        value_005 = 0x30, 0x36  # SphS2, 6 bits : 6 = ... Yes, what?
        value_006 = 0x30, 0x31  # Gain, 1 bit : 0 = High Gain; 1 = Low Gain
        value_007 = 0x30, 0x33  # UNNAMED, 2 bits : 1 = Enable PLL; 2 = Enable ADC PLL (3 = both)
        value_009 = 0x30, 0x32  # ADC1 Delay, 5 bits : 2 = 2 clock cycles
        value_00E = 0x30, 0x41
        value_018 = 0x30, 0x31  # VCAL2 -> VCAL1 Low Byte, 8 bits: 1 = 1 clock cycle
        value_019 = 0x30, 0x30  # VCAL2 -> VCAL1 High Byte, 7 bits
        value_01B = 0x30, 0x38  # Wait Clock Row, 8 bits
        value_014 = 0x30, 0x31  # Start SM on '1' falling edge ('0' = rising edge) of ADC-CLK

        # (Enable PPL, ADC PPL) in Register 0x07 (Accepts 2 bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_007[0], register_007[1], value_007[0], value_007[1]])
        self.read_response()

        # print("  {} {} {}".format(self.row_s1, self.s1_sph, self.sph_s2))
        # print(" -------------------------- S1 -------------------------")
        if self.row_s1 > -1:
            # Valid value, within range
            self.row_s1_low = self.row_s1 & 0xFF
            self.row_s1_high = self.row_s1 >> 8
            value_002 = self.convert_to_aspect_format(self.row_s1_low)
            value_003 = self.convert_to_aspect_format(self.row_s1_high)
        # Send RowS1 low byte to Register 0x02 (Accepts 8 bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                       register_002[0], register_002[1], value_002[0], value_002[1]])
        self.read_response()

        # Send RowS1 high byte to Register 0x03 (Accepts 6 bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                       register_003[0], register_003[1], value_003[0], value_003[1]])
        self.read_response()
        # print(" ----------------------- S1_SPH -----------------------")
        if self.s1_sph > -1:
            value_004 = self.convert_to_aspect_format(self.s1_sph)
        # Send S1SPH to Register 0x04 (Accepts 6 bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                       register_004[0], register_004[1], value_004[0], value_004[1]])
        self.read_response()
        # print(" ----------------------- SPH_S2 ----------------------")
        if self.sph_s2 > -1:
            value_005 = self.convert_to_aspect_format(self.sph_s2)
        # Send SphS2  to Register 0x05 (Accepts 6 Bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                       register_005[0], register_005[1], value_005[0], value_005[1]])
        self.read_response()
        # print(" ------------------------------------------------------")
        # # Debugging
        # print("\n")
        # print("row_s1: {}".format(self.row_s1))
        # print("s1_sph: {}".format(self.s1_sph))
        # print("sph_s2: {}".format(self.sph_s2))
        # print("  row_S1, (L)   value_002: 0x%x, 0x%x" % (value_002[0], value_002[1]))
        # print("          (H)   value_003: 0x%x, 0x%x"  % (value_003[0], value_003[1]))
        # print("  S1_SpH,       value_004: 0x%x, 0x%x" % (value_004[0], value_004[1]))
        # print("  Sph_s2,       value_005: 0x%x, 0x%x\n" % (value_005[0], value_005[1]))

        # sm_timing2 = [self.vsr_addr, HexitecFem.SET_REG_BIT,
        #               register_002[0], register_002[1], value_002[0], value_002[1]]
        # S1_SPH = self.make_list_hexadecimal([self.vsr_addr, HexitecFem.SET_REG_BIT,
        #                                      register_004[0], register_004[1],
        #                                      value_004[0], value_004[1]])
        # SPH_S2 = self.make_list_hexadecimal([self.vsr_addr, HexitecFem.SET_REG_BIT,
        #                                      register_005[0], register_005[1],
        #                                      value_005[0], value_005[1]])
        # print("  sm_timing2, ", self.make_list_hexadecimal(sm_timing2))
        # print("  S1_SPH, ", S1_SPH)
        # print("  SPH_S2, ", SPH_S2)
        # print("\n")

        gain = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Gain', bit_range=1)
        if gain > -1:
            value_006 = self.convert_to_aspect_format(gain)
        # Send Gain to Register 0x06 (Accepts 1 Bit)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_006[0], register_006[1], value_006[0], value_006[1]])
        self.read_response()

        adc1_delay = self._extract_integer(self.hexitec_parameters, 'Control-Settings/ADC1 Delay',
                                           bit_range=2)
        if adc1_delay > -1:
            value_009 = self.convert_to_aspect_format(adc1_delay)
        # Send ADC1 Delay to Register 0x09 (Accepts 2 Bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_009[0], register_009[1], value_009[0], value_009[1]])
        self.read_response()

        delay_sync_signals = self._extract_integer(self.hexitec_parameters,
                                                   'Control-Settings/delay sync signals',
                                                   bit_range=8)
        if delay_sync_signals > -1:
            value_00E = self.convert_to_aspect_format(delay_sync_signals)
        # Send delay sync signals to Register 0x0E (Accepts 8 Bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_00E[0], register_00E[1], value_00E[0], value_00E[1]])
        self.read_response()

        # # TODO: Name for this setting in .ini file ??
        # wait_clock_row = self._extract_integer(self.hexitec_parameters,
        #                                        'Control-Settings/???', bit_range=8)
        # if wait_clock_row > -1:
        #     value_01B = self.convert_to_aspect_format(wait_clock_row)
        # Send wait clock wait to Register 01B (Accepts 8 Bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_01B[0], register_01B[1], value_01B[0], value_01B[1]])
        self.read_response()

        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_014[0], register_014[1], value_014[0], value_014[1]])
        self.read_response()

        vcal2_vcal1 = self._extract_integer(self.hexitec_parameters,
                                            'Control-Settings/VCAL2 -> VCAL1', bit_range=15)
        if vcal2_vcal1 > -1:
            vcal2_vcal1_low = vcal2_vcal1 & 0xFF
            vcal2_vcal1_high = vcal2_vcal1 >> 8
            value_018 = self.convert_to_aspect_format(vcal2_vcal1_low)
            value_019 = self.convert_to_aspect_format(vcal2_vcal1_high)
        # Send VCAL2 -> VCAL1 low byte to Register 0x02 (Accepts 8 bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_018[0], register_018[1], value_018[0], value_018[1]])
        self.read_response()
        # Send VCAL2 -> VCAL1 high byte to Register 0x03 (Accepts 7 bits)
        self.send_cmd([self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_019[0], register_019[1], value_019[0], value_019[1]])
        self.read_response()

        # # DEBUG
        # print("");print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-");print("")
        # print(" VCAL2, L:", self.make_list_hexadecimal([self.vsr_addr,
        #       HexitecFem.SET_REG_BIT, register_018[0], register_018[1],
        #       value_018[0], value_018[1]]))
        # print(" VCAL2, H:", self.make_list_hexadecimal([self.vsr_addr,
        #       HexitecFem.SET_REG_BIT, register_019[0], register_019[1],
        #       value_019[0], value_019[1]]))
        # print("");print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-");print("")

        # Recalculate frame_rate, et cetera if new clock values provided by .ini
        self.calculate_frame_rate()

        logging.debug("Finished Setting up state machine")

    def read_receive_from_all(self, op_command, register_h, register_l):
        """Read and receive from all VSRs."""
        reply = []
        for VSR in self.VSR_ADDRESS:
            self.send_cmd([VSR, op_command, register_h, register_l])
            resp = self.read_response()
            resp = resp[2:-1]
            resp = self.convert_list_to_string(resp)
            reply.append(resp)
        return reply

    def write_receive_to_all(self, op_command, register_h, register_l, value_h, value_l):
        """Write and receive to all VSRs."""
        for VSR in self.VSR_ADDRESS:
            self.send_cmd([VSR, op_command, register_h, register_l, value_h, value_l])
            self.read_response()

    def are_capture_dc_ready(self, vsrs_register_89):
        """Check status of Register 89, bit 0: Capture DC ready."""
        vsrs_ready = True
        for vsr in vsrs_register_89:
            dc_capture_ready = ord(vsr[1]) & 1
            if not dc_capture_ready:
                vsrs_ready = False
        return vsrs_ready

    # TODO: 2x2 Legacy code, to be modified
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
                vsrs_register_89 = self.read_receive_from_all(HexitecFem.READ_REG_VALUE, 0x38, 0x39)
                dc_captured = self.are_capture_dc_ready(vsrs_register_89)
                if self.debug:
                    logging.debug("Register 0x89: {0}, Done? {1} Timing: {2:2.5} s".format(vsrs_register_89,
                                  dc_captured, time.time() - poll_beginning))
                if time.time() - poll_beginning > timeout:
                    raise HexitecFemError("Dark images collection timed out. VSRs' R.89: {}".format(vsrs_register_89))
            # poll_ending = time.time()
            # print(" *** collect offsets polling took: {0} seconds @ {1:4.1f}Hz**".format(poll_ending - poll_beginning,
            #     self.parent.fem.frame_rate))

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
            # Timestamp when offsets collected
            self.offsets_timestamp = '%s' % (datetime.now().strftime(HexitecFem.DATE_FORMAT))
            # # String format can be turned into millisecond format:
            # date_time = datetime.strptime(self.offsets_timestamp, HexitecFem.DATE_FORMAT)
            # ts = date_time.timestamp() * 1000
            # # convert timestamp to string in dd-mm-yyyy HH:MM:SS
            # str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")
            # print("Offsets timestamp, format of dd-mm-yyyy HH:MM:SS: ", str_date_time)
            # ending = time.time()
            # print("     collect_offsets took: {}".format(ending-beginning))
        except HexitecFemError as e:
            self._set_status_error("%s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Failed to collect offsets: %s" % str(e))
            logging.error("%s" % str(e))
        self.hardware_busy = False

    def load_enables_settings(self, number_registers, address_h, address_l, enables_settings, enables_defaults):
        """Load 20 bytes into registers starting from address_h, address_l.

        address_h, address_l is the VSR register to target.
        number_registers determining how many registers to target, always 10 for loading enables.
        enables_settings contain values read from ini file, otherwise enables_default utilised.
        """
        # Check list of (-1, -1) tuples wasn't returned
        if enables_settings[0][0] > 0:
            asic1_command = []
            for msb, lsb in enables_settings:
                asic1_command.append(msb)
                asic1_command.append(lsb)
            register_values = asic1_command
            # print("  ... producing register_values: {}  ".format(' '.join("0x{0:02X}".format(x) for x in register_values)))
            # print("   i.e.:  {}".format(register_values))
            # self.block_write_custom_length(self.vsr_addr, number_registers, address_h, address_l, register_values)
            self.enables_write_and_read_verify(self.vsr_addr, address_h, address_l, register_values)
        else:
            print("  EMPTY INI FILE ... defaults: {}  ".format(' '.join("0x{0:02X}".format(x) for x in enables_defaults)))
            # No ini file loaded, use default values
            # self.block_write_custom_length(self.vsr_addr, number_registers, address_h, address_l, enables_defaults)
            self.enables_write_and_read_verify(self.vsr_addr, address_h, address_l, enables_defaults)

    def enables_write_and_read_verify(self, vsr, address_h, address_l, write_list):
        """."""
        number_registers = 10
        self.block_write_custom_length(vsr, number_registers, address_h, address_l, write_list)

        resp_list, reply_list = self.block_read_and_response(vsr, number_registers, address_h, address_l)
        read_list = []
        for a, b in resp_list:
            read_list.append(a)
            read_list.append(b)
        if not (write_list == read_list):
            # Check again:
            resp_list, reply_list = self.block_read_and_response(vsr, number_registers, address_h, address_l)
            read_list = []
            for a, b in resp_list:
                read_list.append(a)
                read_list.append(b)
            if not (write_list == read_list):
                logging.error(" ** Readback value(s) still inaccurate:")
                logging.error(" **    Wrote: {}".format(write_list))
                logging.error(" **    Read : {}".format(read_list))
                self.error_list.append(" VSR {2:X} Register 0x{0}{1}: ERROR".format(chr(address_h), chr(address_l), vsr))
                self.error_list.append("     Wrote: {}".format(write_list))
                self.error_list.append("     Read : {}".format(read_list))
        # else:
        #     print(" Register 0x{0}{1} -- ALL FINE".format(chr(address_h), chr(address_l)))

    def load_pwr_cal_read_enables(self):  # noqa: C901
        """Load power, calibration and read enables - optionally from hexitec file."""
        if self.vsr_addr not in HexitecFem.VSR_ADDRESS:
            raise HexitecFemError("Unknown VSR address! (%s)" % self.vsr_addr)
        # Address 0x90 = vsr1, 0x91 = vsr2, .. , 0x95 = vsr6. Therefore:
        vsr = self.vsr_addr - 143
        number_registers = 10

        logging.debug("Loading Power, Cal and Read Enables")
        # logging.debug("Column Read Enable")

        # Column Read Enable ASIC1 (Reg 0x61)
        asic1_col_read_enable = self._extract_80_bits("ColumnEn_", vsr, 1, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(number_registers, 0x36, 0x31, asic1_col_read_enable, enables_defaults)

        # Column Read Enable ASIC2 (Reg 0xC2)
        asic2_col_read_enable = self._extract_80_bits("ColumnEn_", vsr, 2, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(number_registers, 0x43, 0x32, asic2_col_read_enable, enables_defaults)

        logging.debug("Column Power Enable")

        # Column Power Enable ASIC1 (Reg 0x4D)
        asic1_col_power_enable = self._extract_80_bits("ColumnPwr", vsr, 1, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(number_registers, 0x34, 0x44, asic1_col_power_enable, enables_defaults)

        # Column Power Enable ASIC2 (Reg 0xAE)
        asic2_col_power_enable = self._extract_80_bits("ColumnPwr", vsr, 2, "Channel")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(number_registers, 0x41, 0x45, asic2_col_power_enable, enables_defaults)

        logging.debug("Column Calibration Enable")

        # Column Calibrate Enable ASIC1 (Reg 0x57)
        asic1_col_cal_enable = self._extract_80_bits("ColumnCal", vsr, 1, "Channel")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        self.load_enables_settings(number_registers, 0x35, 0x37, asic1_col_cal_enable, enables_defaults)

        # Column Calibrate Enable ASIC2 (Reg 0xB8)
        asic2_col_cal_enable = self._extract_80_bits("ColumnCal", vsr, 2, "Channel")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        self.load_enables_settings(number_registers, 0x42, 0x38, asic2_col_cal_enable, enables_defaults)

        logging.debug("Row Read Enable")

        # Row Read Enable ASIC1 (Reg 0x43)
        asic1_row_enable = self._extract_80_bits("RowEn_", vsr, 1, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(number_registers, 0x34, 0x33, asic1_row_enable, enables_defaults)

        # Row Read Enable ASIC2 (Reg 0xA4)
        asic2_row_enable = self._extract_80_bits("RowEn_", vsr, 2, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(number_registers, 0x41, 0x34, asic2_row_enable, enables_defaults)

        logging.debug("Row Power Enable")

        # Row Power Enable ASIC1 (Reg 0x2F)
        asic1_row_power_enable = self._extract_80_bits("RowPwr", vsr, 1, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(number_registers, 0x32, 0x46, asic1_row_power_enable, enables_defaults)

        # Row Power Enable ASIC2 (Reg 0x90)
        asic2_row_power_enable = self._extract_80_bits("RowPwr", vsr, 2, "Block")
        enables_defaults = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                            0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        self.load_enables_settings(number_registers, 0x39, 0x30, asic2_row_power_enable, enables_defaults)

        logging.debug("Row Calibration Enable")

        # Row Calibrate Enable ASIC1 (Reg 0x39)
        asic1_row_cal_enable = self._extract_80_bits("RowCal", vsr, 1, "Block")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        self.load_enables_settings(number_registers, 0x33, 0x39, asic1_row_cal_enable, enables_defaults)

        # Row Calibrate Enable ASIC2 (Reg 0x9A)
        asic2_row_cal_enable = self._extract_80_bits("RowCal", vsr, 2, "Block")
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        self.load_enables_settings(number_registers, 0x39, 0x41, asic2_row_cal_enable, enables_defaults)

        logging.debug("Power, Cal and Read Enables have been loaded")

    def readout_vsr_register(self, vsr, description, address_h, address_l):
        """Read out VSR register.

        Example: (vsr, description, address_h, address_l) = 1, "Column Read Enable ASIC2", 0x43, 0x32
        """
        number_registers = 10
        resp_list, reply_list = self.block_read_and_response(vsr, number_registers, address_h, address_l)
        print(" {0} (0x{1}{2}): {3}".format(description, chr(address_h), chr(address_l), reply_list))

    def make_list_hexadecimal(self, value):  # pragma: no cover
        """Debug function: Turn decimal list into hexadecimal list."""
        value_hexadecimal = []
        for val in value:
            value_hexadecimal.append("0x%x" % val)
        return value_hexadecimal

    def get_vsr_register_value(self, vsr_number, address_h, address_l):
        """Read the VSR register At address_h, address_l."""
        self.send_cmd([vsr_number, self.READ_REG_VALUE, address_h, address_l])
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        reply = resp[2:-1]                                      # Omit start char, vsr & register addresses, and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" *** (R) Reg 0x{0:X}{1:X}, Received ({2}) from UART: {3}".format(address_h-0x30, address_l-0x30,
        #       len(resp), ' '.join("0x{0:02X}".format(x) for x in resp)))
        return resp, reply

    def read_register89(self, vsr_number):
        """Read out register 89."""
        # time.sleep(0.25)
        (address_h, address_l) = (0x38, 0x39)
        # print("Read Register 0x{0}{1}".format(address_h-0x30, address_l-0x30))
        return self.get_vsr_register_value(vsr_number, address_h, address_l)

    def read_register07(self, vsr_number):
        """Read out register 07."""
        # time.sleep(0.25)
        (address_h, address_l) = (0x30, 0x37)
        # print("Read Register 0x{0}{1}".format(address_h-0x30, address_l-0x30))
        return self.get_vsr_register_value(vsr_number, address_h, address_l)

    @run_on_executor(executor='thread_executor')
    def initialise_system(self):
        """Configure in full VSR2, then VSR1.

        Initialise, load enables, set up state machine, write to DAC and enable ADCs.
        """
        try:
            beginning = time.time()
            self.hardware_busy = True
            for vsr in self.VSR_ADDRESS:
                self.vsr_addr = vsr     # Largely redundant, only enable_adc(vsr)  ..
                logging.debug(" --- Initialising VSR: 0x{0:X} ---".format(vsr))
                self._set_status_message("Initialising VSR{}".format(vsr-143))
                self.initialise_vsr(vsr)
                # Check PLLs locked
                bPolling = True
                time_taken = 0
                while bPolling:
                    r89_list, r89_value = self.read_register89(vsr)
                    LSB = ord(r89_value[1])
                    # Is PLL locked? (bit1 high)
                    if LSB & 2:
                        bPolling = False
                    else:
                        print(" R.89: {} {}".format(r89_value, r89_value[1], ord(r89_value[1])))
                        time.sleep(0.2)
                        time_taken += 0.2
                    if time_taken > 3.0:
                        raise HexitecFemError("Timed out polling register 0x89; PLL remains disabled")

            logging.debug("set re_EN_TRAINING '1'")
            # training_en_mask = 0x10
            self.x10g_rdma.write(0x00000020, 0x10, burst_len=1, comment="Enabling training")

            logging.debug("Waiting 0.2 seconds..")
            time.sleep(0.2)

            logging.debug("set re_EN_TRAINING '0'")
            # training_en_mask = 0x00
            self.x10g_rdma.write(0x00000020, 0x00, burst_len=1, comment="Enabling training")

            vsr_status_addr = 0x000003E8  # Flags of interest: locked, +4 to get to the next VSR, et cetera for all VSRs
            for vsr in self.VSR_ADDRESS:
                index = vsr - 144
                vsr_status = self.x10g_rdma.read(vsr_status_addr, burst_len=1, comment="Read vsr{}_status".format(index))
                vsr_status = vsr_status[0]
                locked = vsr_status & 0xFF
                # print("vsr{0}_status 0x{1:08X} = 0x{2:08X}. Locked? 0x{3:X}".format(index, vsr_status_addr, vsr_status, locked))
                if (locked == 0xFF):
                    logging.debug("VSR{0} Locked (0x{1:X})".format(vsr-143, locked))
                else:
                    logging.error("VSR{0} incomplete lock! (0x{1:X})".format(vsr-143, locked))
                    raise HexitecFemError("VSR{0} failed to lock! (0x{1:X})".format(vsr-143, locked))
                vsr_status_addr += 4

            self._set_status_message("Initialisation completed. VSRs configured.")
            print(" -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=- ")
            ending = time.time()
            print("     initialisation took: {}".format(ending-beginning))

            # DEBUGGING Info:
            reg07 = []
            reg89 = []
            # print("VSR Row S1: (High, Low). S1Sph  SphS2:  adc clk delay: . FVAL/LVAL:  VCAL2, (H, L) ")
            print("VSR Row S1: (H, L). S1Sph  SphS2:  adc clk dly: . FVAL/LVAL:  VCAL2, (H, L) Gain")
            for vsr in range(0x90, 0x96):
                r7_list, r7_value = self.read_register07(vsr)
                reg07.append(r7_value)
                r89_list, r89_value = self.read_register89(vsr)
                reg89.append(r89_value)

                s1_high_resp, s1_high_reply = self.read_and_response(vsr, 0x30, 0x33)
                s1_low_resp, s1_low_reply = self.read_and_response(vsr, 0x30, 0x32)
                sph_resp, sph_reply = self.read_and_response(vsr, 0x30, 0x34)
                s2_resp, s2_reply = self.read_and_response(vsr, 0x30, 0x35)
                adc_clock_resp, adc_clock_reply = self.read_and_response(vsr, 0x30, 0x39)  # ADC Clock Delay
                vals_delay_resp, vals_delay_reply = self.read_and_response(vsr, 0x30, 0x45)  # FVAL/LVAL Delay
                vcal_high_resp, vcal_high_reply = self.read_and_response(vsr, 0x31, 0x39)  # VCAL2 -> VCAL1 high byte
                vcal_low_resp, vcal_low_reply = self.read_and_response(vsr, 0x31, 0x38)  # VCAL2 -> VCAL1 low byte
                gain_resp, gain_reply = self.read_and_response(vsr, 0x30, 0x36)  # Gain
                print(" {}        {}  {}     {}     {}          {}             {}             {} {}  {}".format(
                      vsr-143, s1_high_reply, s1_low_reply,
                      sph_reply,
                      s2_reply,
                      adc_clock_reply,
                      vals_delay_reply,
                      vcal_high_reply, vcal_low_reply,
                      gain_reply))
            print(" All vsrs, reg07: {}".format(reg07))
            print("           reg89: {}".format(reg89))
        except HexitecFemError as e:
            self._set_status_error("Failed to initialise camera: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Camera initialisation failed: %s" % str(e))
            logging.error("%s" % str(e))
        self.hardware_busy = False

    def initialise_vsr(self, vsr):
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
        if self.s1_sph > -1:
            value_004 = self.convert_to_aspect_format(self.s1_sph)
        if self.sph_s2 > -1:
            value_005 = self.convert_to_aspect_format(self.sph_s2)
        gain = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Gain', bit_range=1)
        if gain > -1:
            value_006 = self.convert_to_aspect_format(gain)
        adc1_delay = self._extract_integer(self.hexitec_parameters, 'Control-Settings/ADC1 Delay',
                                           bit_range=2)
        if adc1_delay > -1:
            value_009 = self.convert_to_aspect_format(adc1_delay)
        delay_sync_signals = self._extract_integer(self.hexitec_parameters,
                                                   'Control-Settings/delay sync signals',
                                                   bit_range=8)
        if delay_sync_signals > -1:
            value_00E = self.convert_to_aspect_format(delay_sync_signals)
        vcal2_vcal1 = self._extract_integer(self.hexitec_parameters,
                                            'Control-Settings/VCAL2 -> VCAL1', bit_range=15)
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
        delayed = False     # Debugging: Extra 0.2 second delay between read, write?
        self.write_and_response(vsr, 0x30, 0x31, 0x31, 0x30)    # Select external Clock
        # self.write_and_response(vsr, 0x30, 0x37, 0x30, 0x33)    # Enable PLLs; 1 = Enable PLL; 2 = Enable ADC PLL
        self.send_cmd([vsr, 0x42, 0x30, 0x37, 0x30, 0x33])  # Enable PLLs; 1 = Enable PLL; 2 = Enable ADC PLL
        self.read_response()
        self.write_and_response(vsr, 0x30, 0x32, value_002[0], value_002[1], delay=delayed)     # LowByte Row S1
        self.write_and_response(vsr, 0x30, 0x33, value_003[0], value_003[1], delay=delayed)    # HighByte Row S1
        """
        90	42	04	01	;S1Sph
        90	42	05	06	;SphS2
        90	42	09	02	;ADC Clock Delay
        90	42	0E	0A	;FVAL/LVAL Delay
        90	42	1B	08	;SM wait Clock Row
        90	42	14	01	;Start SM on falling edge
        90	42	01	20	;Enable LVDS Interface
        """
        self.write_and_response(vsr, 0x30, 0x34, value_004[0], value_004[1], delay=delayed)     # S1Sph
        self.write_and_response(vsr, 0x30, 0x35, value_005[0], value_005[1], delay=delayed)     # SphS2
        # TODO: ADDITIONALLY ADDED, IS THIS NEEDED OR NOT: ??
        self.write_and_response(vsr, 0x30, 0x36, value_006[0], value_006[1], delay=delayed)     # Gain
        # self.write_and_response(vsr, 0x30, 0x39, value_009[0], value_009[1], delay=delayed)     # ADC Clock Delay
        self.send_cmd([vsr, 0x42, 0x30, 0x39, value_009[0], value_009[1]])
        self.read_response()
        # self.write_and_response(vsr, 0x30, 0x45, value_00E[0], value_00E[1], delay=delayed)     # FVAL/LVAL Delay
        self.send_cmd([vsr, 0x42, 0x30, 0x45, value_00E[0], value_00E[1]])
        self.read_response()
        # self.write_and_response(vsr, 0x31, 0x42, 0x30, 0x38)    # SM wait Low Row, 8 bits
        self.send_cmd([vsr, 0x42, 0x31, 0x42, 0x30, 0x38])
        self.read_response()
        # self.write_and_response(vsr, 0x31, 0x34, 0x30, 0x31)    # Start SM on falling edge ('0' = rising edge) of ADC-CLK
        self.send_cmd([vsr, 0x42, 0x31, 0x34, 0x30, 0x31])
        self.read_response()
        self.write_and_response(vsr, 0x30, 0x31, 0x32, 0x30)    # Enable LVDS Interface
        """
        90	44	61	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Column Read En
        90	44	4D	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Column PWR En
        90	44	57	00	00	00	00	00	00	00	00	00	00	;Column Cal En
        90	44	43	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Row Read En
        90	44	2F	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Row PWR En
        90	44	39	00	00	00	00	00	00	00	00	00	00	;Row Cal En
        90	54	01	FF	0F	FF	05	55	00	00	08	E8	;Write DAC
        """
        self.load_pwr_cal_read_enables()
        # number_registers = 10
        # logging.debug("Column Read Enable")
        # self.block_write_and_response(vsr, number_registers, 0x36, 0x31, 0x46, 0x46)  # 61; Column Read En
        # logging.debug("Column POWER Enable")
        # self.block_write_and_response(vsr, number_registers, 0x34, 0x44, 0x46, 0x46)  # 4D; Column PWR En
        # logging.debug("Column calibrate Enable")
        # self.block_write_and_response(vsr, number_registers, 0x35, 0x37, 0x30, 0x30)  # 57; Column Cal En
        # logging.debug("Row Read Enable")
        # self.block_write_and_response(vsr, number_registers, 0x34, 0x33, 0x46, 0x46)  # 43; Row Read En
        # logging.debug("Row POWER Enable")
        # self.block_write_and_response(vsr, number_registers, 0x32, 0x46, 0x46, 0x46)  # 2F; Row PWR En
        # logging.debug("Row calibrate Enable")
        # self.block_write_and_response(vsr, number_registers, 0x33, 0x39, 0x30, 0x30)  # 39; Row Cal En
        # self.write_dac_values(vsr)
        """
        90	55	02	;Disable ADC/Enable DAC
        90	43	01	01	;Enable SM
        90	42	01	01	;Disable SM
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
        self.write_and_response(vsr, 0x32, 0x34, 0x32, 0x32, False)    # Disable Vcal/Capture Avg Picture (False=don't mask)
        # print("Disable Vcal/En DC spectroscopic mode")
        self.write_and_response(vsr, 0x32, 0x34, 0x32, 0x38, False)    # Disable Vcal/En DC spectroscopic mode (False=don't mask)
        logging.debug("Enable Training")
        self.write_and_response(vsr, 0x30, 0x31, 0x38, 0x30)    # Enable Training
        # self.send_cmd([vsr, 0x42, 0x30, 0x31, 0x38, 0x30])
        # self.read_response()

        # self.write_and_response(vsr, 0x31, 0x38, 0x30, 0x31) # Low Byte SM Vcal Clock
        # TODO: Inserting VCal setting here
        # Send VCAL2 -> VCAL1 low byte to Register 0x02 (Accepts 8 bits)
        self.write_and_response(vsr, 0x31, 0x38, value_018[0], value_018[1], False)
        # Send VCAL2 -> VCAL1 high byte to Register 0x03 (Accepts 7 bits)
        self.write_and_response(vsr, 0x31, 0x39, value_019[0], value_019[1], False)
        # self.write_and_response(vsr, 0x32, 0x34,	0x32, 0x30) # Enable Vcal
        logging.debug("Enable Vcal")  # 90	43	24	20	;Enable Vcal
        self.send_cmd([vsr, 0x43, 0x32, 0x34, 0x32, 0x30])
        self.read_response()
        self.write_and_response(vsr, 0x32, 0x34, 0x32, 0x30)     # Disable Vcal

        """MR's tcl script also also set these two:"""
        # set queue_1 { { 0x40 0x01 0x30                                              "Disable_Training" } \
        #             { 0x40 0x0A 0x01                                              "Enable_Triggered_SM_Start" }
        # }

    def read_and_response(self, vsr, address_h, address_l, delay=False):
        """Send a read and read the reply."""
        if delay:
            time.sleep(0.1)
        self.send_cmd([vsr, 0x41, address_h, address_l])
        if delay:
            time.sleep(0.1)
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        reply = resp[2:-1]                                      # Omit start char, vsr address and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" RR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        return resp, reply

    def write_and_response(self, vsr, address_h, address_l, value_h, value_l, masked=True, delay=False):
        """Write value_h, value_l to address_h, address_l of vsr, if not masked then register value overwritten."""
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
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        if delay:
            time.sleep(0.1)
        reply = resp[4:-1]                                      # Omit start char, vsr & register addresses, and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" WR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        if ((resp[4] != value_h) or (resp[5] != value_l)):
            print("H? {} L? {}".format(resp[4] == value_h, resp[5] == value_l))
            print("WaR. reply: {} (resp: {}) VERSUS value_h: {} value_l: {}".format(reply, resp, value_h, value_l))
            print("WaR. (resp: {} {}) VERSUS value_h: {} value_l: {}".format(resp[4], resp[5], value_h, value_l))
            raise HexitecFemError("Readback value did not match written!")
        return resp, reply

    def block_write_and_response(self, vsr, number_registers, address_h, address_l, value_h, value_l):
        """Write value_h, value_l to address_h, address_l of vsr, spanning number_registers."""
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        for index in range(number_registers):
            # print("   BWaR Write: {} {} {} {} {}".format(vsr, most_significant[index], least_significant[index], value_h, value_l))
            self.write_and_response(vsr, most_significant[index], least_significant[index], value_h, value_l, False)

    def block_write_custom_length(self, vsr, number_registers, address_h, address_l, write_values):
        """Write write_values starting with address_h, address_l of vsr, spanning number_registers."""
        if (number_registers * 2) != len(write_values):
            print("Mismatch! number_registers ({}) isn't half of write_values ({}).".format(number_registers, len(write_values)))
            return -1
        values_list = write_values.copy()
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        for index in range(number_registers):
            value_h = values_list.pop(0)
            value_l = values_list.pop(0)
            # print("   BWCL Write: {0:X} {1:X} {2:X} {3:X} {4:X}".format(vsr, most_significant[index], least_significant[index], value_h, value_l))
            self.write_and_response(vsr, most_significant[index], least_significant[index], value_h, value_l, False)

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
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        resp_list = []
        reply_list = []
        for index in range(number_registers):
            resp, reply = self.read_and_response(vsr, most_significant[index], least_significant[index])
            # print(" BRaR: {} and {}".format(resp, reply))
            resp_list.append(resp[2:-1])
            reply_list.append(reply)
        return resp_list, reply_list

    def write_dac_values(self, vsr_address):
        """Write values to DAC, optionally provided by hexitec file."""
        logging.debug("Writing DAC values")
        vcal = [0x30, 0x31, 0x46, 0x46]     # [0x30, 0x32, 0x41, 0x41]
        umid = [0x30, 0x46, 0x46, 0x46]     # [0x30, 0x35, 0x35, 0x35]
        hv = [0x30, 0x35, 0x35, 0x35]
        dctrl = [0x30, 0x30, 0x30, 0x30]
        rsrv2 = [0x30, 0x38, 0x45, 0x38]

        umid_value = self._extract_exponential(self.hexitec_parameters,
                                               'Control-Settings/Uref_mid', bit_range=12)
        if umid_value > -1:
            # Valid value, within range
            umid_high = (umid_value >> 8) & 0x0F
            umid_low = umid_value & 0xFF
            umid[0], umid[1] = self.convert_to_aspect_format(umid_high)
            umid[2], umid[3] = self.convert_to_aspect_format(umid_low)

        vcal_value = self._extract_float(self.hexitec_parameters, 'Control-Settings/VCAL')
        if vcal_value > -1:
            # Valid value, within range
            vcal_high = (vcal_value >> 8) & 0x0F
            vcal_low = vcal_value & 0xFF
            vcal[0], vcal[1] = self.convert_to_aspect_format(vcal_high)
            vcal[2], vcal[3] = self.convert_to_aspect_format(vcal_low)

        # print(" *** umid_value: {} vcal_value: {}".format(umid_value, vcal_value))
        self.send_cmd([vsr_address, HexitecFem.WRITE_DAC_VAL,
                       vcal[0], vcal[1], vcal[2], vcal[3],          # Vcal, e.g. 0x0111 =: 0.2V
                       umid[0], umid[1], umid[2], umid[3],          # Umid, e.g. 0x0555 =: 1.0V
                       hv[0], hv[1], hv[2], hv[3],                  # reserve1, 0x0555 =: 1V (HV ~-250V)
                       dctrl[0], dctrl[1], dctrl[2], dctrl[3],      # DET ctrl, 0x000
                       rsrv2[0], rsrv2[1], rsrv2[2], rsrv2[3]])     # reserve2, 0x08E8 =: 1.67V
        self.read_response()
        logging.debug("DAC values set")

    def enable_adc(self, vsr_address):
        """Enable the ADCs."""
        self.vsr_addr = vsr_address
        logging.debug("Disable ADC/Enable DAC")     # 90 55 02 ;Disable ADC/Enable DAC
        self.send_cmd([self.vsr_addr, HexitecFem.CTRL_ADC_DAC, 0x30, 0x32])
        self.read_response()

        logging.debug("Enable SM")      # 90 43 01 01 ;Enable SM
        self.send_cmd([self.vsr_addr, 0x43, 0x30, 0x31, 0x30, 0x31])
        self.read_response()

        logging.debug("Disable SM")     # 90 42 01 01 #Disable SM
        self.send_cmd([self.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31])
        self.read_response()

        logging.debug("Enable ADC/Enable DAC")  # 90 55 03  ;Enable ADC/Enable DAC
        self.send_cmd([self.vsr_addr, HexitecFem.CTRL_ADC_DAC, 0x30, 0x33])
        self.read_response()

        logging.debug("Write ADC register")     # 90 53 16 09   ;Write ADC Register
        # self.send_cmd([self.vsr_addr, 0x53, 0x31, 0x36, 0x30, 0x39])  # Avoided
        # self.read_response()
        self.write_and_response(self.vsr_addr, 0x31, 0x36, 0x30, 0x39)

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
            # print("\n\tfem.calculate_frame_rate() (duration {} setting parent's number_frames {})\n".format(self.duration, self.number_frames))
            # With duration enabled, recalculate number of frames in case clocks changed
            self.set_duration(self.duration)
            self.parent.set_number_frames(self.number_frames)

    # TODO: To be tested using new 2x6 system hardware
    def print_vcal_registers(self, vsr_addr):  # pragma: no cover
        """Debug function: Print all VCAL (Power, calibrate & read enables) registers."""
        print("---------------------------------------------------------------------------------")
        # ROW, ASIC 1

        rpe1 = [0x2F, 0x38]
        row_power_enable1 = self.read_back_register(vsr_addr, rpe1)
        rce1 = [0x39, 0x42]
        row_cal_enable1 = self.read_back_register(vsr_addr, rce1)
        rre1 = [0x43, 0x4c]
        row_read_enable1 = self.read_back_register(vsr_addr, rre1)
        # print("row_read_enable1: {}".format(row_read_enable1))
        print("\t\tRow Pwr Ena ASIC1:  %s \n\t\tRow Cal Ena ASIC1: %s \n\t\tRow Rd Ena ASIC1: %s"
              % (row_power_enable1, row_cal_enable1, row_read_enable1))

        # COLUMN, ASIC 1

        cpe1 = [0x4d, 0x56]
        col_power_enable1 = self.read_back_register(vsr_addr, cpe1)
        cce1 = [0x57, 0x60]
        col_cal_enable1 = self.read_back_register(vsr_addr, cce1)
        cre1 = [0x61, 0x6a]
        col_read_enable1 = self.read_back_register(vsr_addr, cre1)

        print("\t\tCol Pwr Ena ASIC1: %s \n\t\tCol Cal Ena ASIC1: %s \n\t\tCol Rd Ena ASIC1: %s"
              % (col_power_enable1, col_cal_enable1, col_read_enable1))
        print("---------------------------------------------------------------------------------")
        # ROW, ASIC 2

        rpe2 = [0x90, 0x99]
        row_power_enable2 = self.read_back_register(vsr_addr, rpe2)
        rce2 = [0x9A, 0xA3]
        row_cal_enable2 = self.read_back_register(vsr_addr, rce2)
        rre2 = [0xA4, 0xAD]
        row_read_enable2 = self.read_back_register(vsr_addr, rre2)

        print("\t\tRow Pwr Ena ASIC2: %s \n\t\tRow Cal Ena ASIC2:  %s \n\t\tRow Rd Ena ASIC2: %s"
              % (row_power_enable2, row_cal_enable2, row_read_enable2))

        # COLUMN, ASIC 2

        cpe2 = [0xAE, 0xB7]
        col_power_enable2 = self.read_back_register(vsr_addr, cpe2)
        cce2 = [0xB8, 0xC1]
        col_cal_enable2 = self.read_back_register(vsr_addr, cce2)
        cre2 = [0xC2, 0xCB]
        col_read_enable2 = self.read_back_register(vsr_addr, cre2)

        print("\t\tCol Pwr Ena ASIC2: %s \n\t\tCol Cal Ena ASIC2: %s \n\t\tCol Rd Ena ASIC2: %s"
              % (col_power_enable2, col_cal_enable2, col_read_enable2))
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")

    # TODO: To be tested using new 2x6 system hardware
    def read_back_register(self, vsr_addr, boundaries):  # pragma: no cover
        """Debug function: Actual hardware interaction with VCAL registers."""
        register_reply = []
        for idx in range(boundaries[0], boundaries[1] + 1, 1):
            formatted_address = self.convert_to_aspect_format(idx)
            command = [vsr_addr, HexitecFem.READ_REG_VALUE,
                       formatted_address[0], formatted_address[1]]
            self.send_cmd(command)
            reply = self.convert_list_to_string(self.read_response()[1:])
            register_reply.append(reply.strip())
        return register_reply

    def convert_list_to_string(self, int_list):
        """Convert list of integer into ASCII string.

        I.e. integer_list = [42, 144, 70, 70, 13], returns '*\x90FF\r'
        """
        return "{}".format(''.join([chr(x) for x in int_list]))

    def read_pwr_voltages(self):
        """Read and convert power data into voltages."""
        self.send_cmd([self.vsr_addr, HexitecFem.READ_PWR_VOLT])
        # sensors_values = self.read_response()
        # sensors_values = sensors_values.strip()
        read_sensors = self.read_response()
        # print("Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))
        read_sensors = read_sensors[1:]     # Omit start of sequence character, matching existing 2x2 source code formatting
        sensors_values = self.convert_list_to_string(read_sensors)   # Turn list of integers into ASCII string
        if len(sensors_values) != 50:
            logging.warning("VSR 0x{0:X}: Received incomplete power data".format(self.vsr_addr))
            return None
        # print(" ASCII string: {}".format(sensors_values))

        if self.debug:
            logging.debug("VSR: %s Power values: %s len: %s" % (format(self.vsr_addr, '#02x'),
                          sensors_values.replace('\r', ''), len(sensors_values)))

        if (self.vsr_addr == HexitecFem.VSR_ADDRESS[0]):
            self.vsr1_hv = self.get_hv_value(sensors_values)
            # print(" VSR1_HV: {}".format(self.vsr1_hv))
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[1]):
            self.vsr2_hv = self.get_hv_value(sensors_values)
            # print(" VSR2_hv: {}".format(self.vsr2_hv))
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[2]):
            self.vsr3_hv = self.get_hv_value(sensors_values)
            # print(" VSR3_hv: {}".format(self.vsr3_hv))
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[3]):
            self.vsr4_hv = self.get_hv_value(sensors_values)
            # print(" VSR4_hv: {}".format(self.vsr4_hv))
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[4]):
            self.vsr5_hv = self.get_hv_value(sensors_values)
            # print(" VSR5_hv: {}".format(self.vsr5_hv))
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[5]):
            self.vsr6_hv = self.get_hv_value(sensors_values)
            # print(" VSR6_hv: {}".format(self.vsr6_hv))
        else:
            logging.warning("VSR 0x{0:X}: Didn't expect power readout(!)".format(self.vsr_addr))

    def get_hv_value(self, sensors_values):
        """Take the full string of voltages and extract the HV value."""
        try:
            # Calculate V10, the 3.3V reference voltage
            reference_voltage = int(sensors_values[37:41], 16) * (2.048 / 4095)
            # Calculate HV rails
            u1 = int(sensors_values[1:5], 16) * (reference_voltage / 2**12)
            # Apply conversion gain # Added 56V following HV tests
            hv_monitoring_voltage = u1 * 1621.65 - 1043.22 + 56
            # print("hv value: {}\n\n".format(hv_monitoring_voltage))
            return hv_monitoring_voltage
        except ValueError as e:
            logging.error("VSR %s: Error obtaining HV value: %s" %
                          (format(self.vsr_addr, '#02x'), e))
            return -1

    def read_temperatures_humidity_values(self):
        """Read and convert sensor data into temperatures and humidity values."""
        self.send_cmd([self.vsr_addr, 0x52])
        read_sensors = self.read_response()
        # print("Received ({0}) from 0x{1:02X}: {2}".format(len(read_sensors), self.vsr_addr, ' '.join("0x{0:02X}".format(x) for x in read_sensors)))
        if len(read_sensors) != 25:
            logging.warning("VSR 0x{0:X}: Received incomplete environmental data".format(self.vsr_addr))
            return None
        read_sensors = read_sensors[1:]     # Omit start of sequence character, matching existing 2x2 source code formatting
        sensors_values = self.convert_list_to_string(read_sensors)   # Turn list of integers into ASCII string
        # print(" ASCII string: {}".format(sensors_values))

        if self.debug:
            logging.debug("VSR: %s sensors_values: %s len: %s" % (format(self.vsr_addr, '#02x'),
                          sensors_values, len(sensors_values)))

        ambient_hex = sensors_values[1:5]
        humidity_hex = sensors_values[5:9]
        asic1_hex = sensors_values[9:13]
        asic2_hex = sensors_values[13:17]
        adc_hex = sensors_values[17:21]
        # print(" * ambient_hex:  {} -> {} Celsius".format(sensors_values[1:5], self.get_ambient_temperature(sensors_values[1:5])))
        # print(" * humidity_hex: {} -> {}".format(sensors_values[5:9], self.get_humidity(sensors_values[5:9])))
        # print(" * asic1_hex:    {} -> {} Celsius".format(sensors_values[9:13], self.get_asic_temperature(sensors_values[9:13])))
        # print(" * asic2_hex:    {} -> {} Celsius".format(sensors_values[13:17], self.get_asic_temperature(sensors_values[13:17])))
        # print(" * adc_hex:      {} -> {} Celsius".format(sensors_values[17:21], self.get_adc_temperature(sensors_values[17:21])))

        if (self.vsr_addr == HexitecFem.VSR_ADDRESS[0]):
            self.vsr1_ambient = self.get_ambient_temperature(ambient_hex)
            self.vsr1_humidity = self.get_humidity(humidity_hex)
            self.vsr1_asic1 = self.get_asic_temperature(asic1_hex)
            self.vsr1_asic2 = self.get_asic_temperature(asic2_hex)
            self.vsr1_adc = self.get_adc_temperature(adc_hex)
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[1]):
            self.vsr2_ambient = self.get_ambient_temperature(ambient_hex)
            self.vsr2_humidity = self.get_humidity(humidity_hex)
            self.vsr2_asic1 = self.get_asic_temperature(asic1_hex)
            self.vsr2_asic2 = self.get_asic_temperature(asic2_hex)
            self.vsr2_adc = self.get_adc_temperature(adc_hex)
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[2]):
            self.vsr3_ambient = self.get_ambient_temperature(ambient_hex)
            self.vsr3_humidity = self.get_humidity(humidity_hex)
            self.vsr3_asic1 = self.get_asic_temperature(asic1_hex)
            self.vsr3_asic2 = self.get_asic_temperature(asic2_hex)
            self.vsr3_adc = self.get_adc_temperature(adc_hex)
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[3]):
            self.vsr4_ambient = self.get_ambient_temperature(ambient_hex)
            self.vsr4_humidity = self.get_humidity(humidity_hex)
            self.vsr4_asic1 = self.get_asic_temperature(asic1_hex)
            self.vsr4_asic2 = self.get_asic_temperature(asic2_hex)
            self.vsr4_adc = self.get_adc_temperature(adc_hex)
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[4]):
            self.vsr5_ambient = self.get_ambient_temperature(ambient_hex)
            self.vsr5_humidity = self.get_humidity(humidity_hex)
            self.vsr5_asic1 = self.get_asic_temperature(asic1_hex)
            self.vsr5_asic2 = self.get_asic_temperature(asic2_hex)
            self.vsr5_adc = self.get_adc_temperature(adc_hex)
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[5]):
            self.vsr6_ambient = self.get_ambient_temperature(ambient_hex)
            self.vsr6_humidity = self.get_humidity(humidity_hex)
            self.vsr6_asic1 = self.get_asic_temperature(asic1_hex)
            self.vsr6_asic2 = self.get_asic_temperature(asic2_hex)
            self.vsr6_adc = self.get_adc_temperature(adc_hex)
        else:
            logging.warning("VSR 0x%s: Sensor data temporarily unavailable" %
                            format(self.vsr_addr, '02x'))

    def get_ambient_temperature(self, hex_val):
        """Calculate ambient temperature."""
        try:
            return ((int(hex_val, 16) * 175.72) / 65536) - 46.84
        except ValueError as e:
            logging.error("Error converting ambient temperature: %s" % e)
            return -100

    def get_humidity(self, hex_val):
        """Calculate humidity."""
        try:
            return ((int(hex_val, 16) * 125) / 65535) - 6
        except ValueError as e:
            logging.error("Error converting humidity: %s" % e)
            return -100

    def get_asic_temperature(self, hex_val):
        """Calculate ASIC temperature."""
        try:
            return int(hex_val, 16) * 0.0625
        except ValueError as e:
            logging.error("Error converting ASIC temperature: %s" % e)
            return -100

    def get_adc_temperature(self, hex_val):
        """Calculate ADC Temperature."""
        try:
            return int(hex_val, 16) * 0.0625
        except ValueError as e:
            logging.error("Error converting ADC temperature: %s" % e)
            return -100

    def _set_hexitec_config(self, filename):
        """Check whether file exists, load parameters from file."""
        filename = self.base_path + filename
        try:
            with open(filename, 'r') as f:  # noqa: F841
                pass
            self.hexitec_config = filename
            logging.debug("hexitec_config: '%s'" % (self.hexitec_config))
        except IOError as e:
            logging.error("Cannot open provided hexitec file: %s" % e)
            raise IOError("Error: %s" % e)

        self.read_ini_file(self.hexitec_config, self.hexitec_parameters, debug=False)

        # bias_refresh_interval = self._extract_integer(self.hexitec_parameters,
        #                                               'Bias_Voltage/Bias_Refresh_Interval',
        #                                               bit_range=32)
        # if bias_refresh_interval > -1:
        #     self.bias_refresh_interval = bias_refresh_interval / 1000.0

        # bias_voltage_refresh = self._extract_boolean(self.hexitec_parameters,
        #                                              'Bias_Voltage/Bias_Voltage_Refresh')
        # if bias_voltage_refresh > -1:
        #     self.bias_voltage_refresh = bias_voltage_refresh

        # time_refresh_voltage_held = self._extract_integer(self.hexitec_parameters,
        #                                                   'Bias_Voltage/Time_Refresh_Voltage_Held',
        #                                                   bit_range=32)
        # if time_refresh_voltage_held > -1:
        #     self.time_refresh_voltage_held = time_refresh_voltage_held / 1000.0

        # bias_voltage_settle_time = self._extract_integer(self.hexitec_parameters,
        #                                                  'Bias_Voltage/Bias_Voltage_Settle_Time',
        #                                                  bit_range=32)
        # if bias_voltage_settle_time > -1:
        #     self.time_refresh_voltage_held = time_refresh_voltage_held / 1000.0
        #     self.bias_voltage_settle_time = bias_voltage_settle_time / 1000.0

        # Recalculate frame rate
        self.row_s1 = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Row -> S1',
                                            bit_range=14)
        self.s1_sph = self._extract_integer(self.hexitec_parameters, 'Control-Settings/S1 -> Sph',
                                            bit_range=6)
        self.sph_s2 = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Sph -> S2',
                                            bit_range=6)
        print("row_s1: {} from {}".format(self.row_s1, self._extract_integer(self.hexitec_parameters, 'Control-Settings/Row -> S1', bit_range=14)))
        print("s1_sph: {} from {}".format(self.s1_sph, self._extract_integer(self.hexitec_parameters, 'Control-Settings/S1 -> Sph', bit_range=6)))
        print("sph_s2: {} from {}".format(self.sph_s2, self._extract_integer(self.hexitec_parameters, 'Control-Settings/Sph -> S2', bit_range=6)))
        # print(self.hexitec_parameters)
        self.calculate_frame_rate()

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
        # number_scaled = int(number_int // self.DAC_SCALE_FACTOR)

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
            logging.warning("Warning: No '%s' Key defined!" % descriptor)
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
            logging.warning("Warning: No '%s' Key defined!" % descriptor)
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
            logging.warning("Warning: No '%s' Key defined!" % descriptor)

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
            setting = -1
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

        # TODO: Bit clunky returning so many -1 tuples. Better solution for no ini file loaded?
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
        # print(" *** convert_to_aspect_format({}) -> {}, {}".format(value, high_encoded, low_encoded))
        return high_encoded, low_encoded

    def read_ini_file(self, filename, parameter_dict, debug=False):
        """Read filename, parse case sensitive keys decoded as strings."""
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

    def debug_register(self, msb, lsb):  # pragma: no cover
        """Debug function: Display contents of register."""
        # TODO: Scale with num of VSR..
        # for vsr in self.VSR_ADDRESS:
        self.send_cmd([self.VSR_ADDRESS[1], self.READ_REG_VALUE,
                       msb, lsb])
        vsr2 = self.read_response()
        time.sleep(0.25)
        self.send_cmd([self.VSR_ADDRESS[0], self.READ_REG_VALUE,
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
                    (vsr2, vsr1) = self.debug_register(self.HEX_ASCII_CODE[msb], self.HEX_ASCII_CODE[lsb])
                    print("  * Register: {}{}: VSR2: {}.{} VSR1: {}.{}".format(hex(msb), hex(lsb)[-1],
                          chr(vsr2[0]), chr(vsr2[1]),
                          chr(vsr1[0]), chr(vsr1[1])))
                    time.sleep(0.25)
            # for msb in range(16):
            #     for lsb in range(16):
            #         (vsr2, vsr1) = self.debug_register(self.HEX_ASCII_CODE[msb], self.HEX_ASCII_CODE[lsb])
            #         print(" \t\t\t\t* Register: {}{}: VSR2: {}.{} VSR1: {}.{}".format(hex(msb), hex(lsb)[-1],
            #             chr(vsr2[0]), chr(vsr2[1]),
            #             chr(vsr1[0]), chr(vsr1[1])))
            #         time.sleep(0.25)
        except Exception as e:
            logging.error("dump_all_registers: {}".format(e))

class HexitecFemError(Exception):
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass
