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

from hexitec.RdmaUDP import RdmaUDP

from concurrent import futures
from socket import error as socket_error
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor


class HexitecFem():
    """
    Hexitec Fem class. Represents a single FEM-II module.

    Controls and configures each FEM-II module ready for a DAQ via UDP.
    """

    thread_executor = futures.ThreadPoolExecutor(max_workers=2)

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

    VSR_ADDRESS = [
        0x90,
        0x91
    ]

    SENSORS_READOUT_OK = 7

    HEX_ASCII_CODE = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                      0x41, 0x42, 0x43, 0x44, 0x45, 0x46]

    DAC_SCALE_FACTOR = 0.732

    SEND_REG_VALUE = 0x40
    READ_REG_VALUE = 0x41
    SET_REG_BIT = 0x42
    CLR_REG_BIT = 0x43
    SEND_REG_BURST = 0x44
    SEND_REG_STREAM = 0x46  # Currently unused
    READ_PWR_VOLT = 0x50
    WRITE_REG_VAL = 0x53
    WRITE_DAC_VAL = 0x54
    CTRL_ADC_DAC = 0x55

    # Define timestamp format
    DATE_FORMAT = '%Y%m%d_%H%M%S.%f'

    def __init__(self, parent, fem_id=1,
                 server_ctrl_ip_addr='10.0.2.2', camera_ctrl_ip_addr='10.0.2.1',
                 server_data_ip_addr='10.0.4.2', camera_data_ip_addr='10.0.4.1'):
        """
        Initialize the HexitecFem object.

        This constructor initializes the HexitecFem object.
        :param parent: Reference to adapter object
        :param fem_id: HexitecFem object identifier
        :param server_ctrl_ip_addr: PC interface for control path
        :param camera_ctrl_ip_addr: FEM interface for control path
        :param server_data_ip_addr: PC interface for data path
        :param camera_data_ip_addr: FEM interface for data path
        """
        # Give access to parent class (Hexitec) - for potential future use
        self.parent = parent
        self.id = int(fem_id)
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

        self.first_initialisation = True
        self.hardware_connected = False
        self.hardware_busy = False
        self.ignore_busy = False

        self.health = True

        # Construct path to hexitec source code
        cwd = os.getcwd()
        index = cwd.find("control")
        self.base_path = cwd[:index]

        # Variables supporting frames to duration conversion
        self.row_s1 = 135
        self.s1_sph = 1
        self.sph_s2 = 5
        self.frame_rate = 0
        self.duration = 1
        self.duration_enabled = False

        self.bias_refresh_interval = 60.0
        self.bias_voltage_refresh = False
        self.time_refresh_voltage_held = 3.0
        self.bias_voltage_settle_time = 2.0

        # Acquisition completed, note completion timestamp
        self.acquisition_completed = False

        self.debug = False
        self.debug_register24 = False
        # Diagnostics:
        self.exception_triggered = False
        self.successful_reads = 0
        self.acquisition_duration = ""

        self.status_message = ""
        self.status_error = ""
        self.stop_acquisition = False
        self.initialise_progress = 0
        self.operation_percentage_complete = 0
        self.operation_percentage_steps = 108

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

        param_tree_dict = {
            "diagnostics": {
                "successful_reads": (lambda: self.successful_reads, None),
                "acquire_start_time": (lambda: self.acquire_start_time, None),
                "acquire_stop_time": (lambda: self.acquire_stop_time, None),
                "acquire_time": (lambda: self.acquire_time, None),
            },
            "id": (lambda: self.id, None),
            "debug": (self.get_debug, self.set_debug),
            "frame_rate": (lambda: self.frame_rate, None),
            "health": (lambda: self.health, None),
            "status_message": (self._get_status_message, None),
            "status_error": (self._get_status_error, None),
            "initialise_progress": (self._get_initialise_progress, None),
            "operation_percentage_complete": (self._get_operation_percentage_complete, None),
            "number_frames": (self.get_number_frames, self.set_number_frames),
            "duration": (self.get_duration, self.set_duration),
            "hexitec_config": (lambda: self.hexitec_config, self._set_hexitec_config),
            "read_sensors": (None, self.read_sensors),
            "hardware_connected": (lambda: self.hardware_connected, None),
            "hardware_busy": (lambda: self.hardware_busy, None),
            "firmware_date": (lambda: self.firmware_date, None),
            "firmware_time": (lambda: self.firmware_time, None),
            "vsr1_sync": (lambda: self.vsr1_sync, None),
            "vsr2_sync": (lambda: self.vsr2_sync, None),
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
            }
        }

        self.param_tree = ParameterTree(param_tree_dict)

    def __del__(self):
        """Ensure rdma connection closed."""
        if self.x10g_rdma is not None:
            self.x10g_rdma.close()

    def connect(self, bDebug=False):
        """Set up hardware connection."""
        try:
            self.x10g_rdma = RdmaUDP(self.server_ctrl_ip_addr, 61650,
                                     self.server_ctrl_ip_addr, 61651,
                                     self.camera_ctrl_ip_addr, 61650,
                                     self.camera_ctrl_ip_addr, 61651,
                                     2000000, 9000, 20)
            self.x10g_rdma.setDebug(False)
            self.x10g_rdma.ack = True
        except socket_error as e:
            raise socket_error("Failed to setup Control connection: %s" % e)
        return

    def read_sensors(self, msg=None):
        """Read environmental sensors and updates parameter tree with results."""
        try:
            # Note once, when firmware was built
            if self.read_firmware_version:
                date = self.x10g_rdma.read(0x60000015, 'FIRMWARE DATE')
                time = self.x10g_rdma.read(0x60000016, 'FIRMWARE TIME')
                date = format(date, '#010x')
                time = format(time, '#06x')
                self.firmware_date = "{0:.2}/{1:.2}/{2:.4}".format(date[2:4], date[4:6], date[6:10])
                self.firmware_time = "{0:.2}:{1:.2}".format(time[2:4], time[4:6])
                self.read_firmware_version = False
            vsr = self.vsr_addr
            self.vsr_addr = HexitecFem.VSR_ADDRESS[0]
            self.read_temperatures_humidity_values()
            self.read_pwr_voltages()  # pragma: no cover
            self.vsr_addr = HexitecFem.VSR_ADDRESS[1]  # pragma: no cover
            self.read_temperatures_humidity_values()  # pragma: no cover
            self.read_pwr_voltages()  # pragma: no cover
            self.vsr_addr = vsr  # pragma: no cover
        except (HexitecFemError, ParameterTreeError) as e:
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

    def set_image_size(self, x_size, y_size, p_size, f_size):
        """Set image size, function inherited from JE/RH."""
        # set image size globals
        self.image_size_x = x_size
        self.image_size_y = y_size
        self.image_size_p = p_size
        self.image_size_f = f_size
        # check parameters againts ethernet packet and local link frame size compatibility
        pixel_count_max = x_size * y_size
        number_bytes = pixel_count_max * 2
        number_bytes_r4 = pixel_count_max % 4
        number_bytes_r8 = number_bytes % 8
        first_packets = number_bytes // self.strm_mtu
        last_packet_size = number_bytes % self.strm_mtu
        lp_number_bytes_r8 = last_packet_size % 8
        lp_number_bytes_r32 = last_packet_size % 32
        size_status = number_bytes_r4 + number_bytes_r8 + lp_number_bytes_r8 + lp_number_bytes_r32
        # calculate pixel packing settings
        if p_size >= 11 and p_size <= 14 and f_size == 16:
            pixel_count_max = pixel_count_max // 2
        elif p_size == 8 and f_size == 8:
            pixel_count_max = pixel_count_max // 4  # pragma: no cover
        else:
            size_status = size_status + 1

        # Set up registers if no size errors
        if size_status != 0:
            logging.error("%-32s %8i %8i %8i %8i %8i %8i" %
                          ('Size error', number_bytes, number_bytes_r4, number_bytes_r8,
                           first_packets, lp_number_bytes_r8, lp_number_bytes_r32))
        else:
            address = self.rdma_addr["receiver"] | 0x01
            data = (pixel_count_max & 0x1FFFF) - 1
            self.x10g_rdma.write(address, data, 'pixel count max')
            self.x10g_rdma.write(self.rdma_addr["receiver"] + 4, 0x3, 'pixel bit size => 16 bit')
        return

    def frame_gate_trigger(self):
        """Reset monitors, pulse frame gate."""
        # the reset of monitors suggested by Rob:
        self.x10g_rdma.write(self.rdma_addr["reset_monitor"] + 0, 0x0, 'reset monitor off')
        self.x10g_rdma.write(self.rdma_addr["reset_monitor"] + 0, 0x1, 'reset monitor on')
        self.x10g_rdma.write(self.rdma_addr["reset_monitor"] + 0, 0x0, 'reset monitor off')

        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 0, 0x0, 'frame gate trigger off')
        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 0, 0x1, 'frame gate trigger on')
        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 0, 0x0, 'frame gate trigger off')

    def frame_gate_settings(self, frame_number, frame_gap):
        """Set frame gate settings."""
        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 1, frame_number,
                             'frame gate frame number')
        self.x10g_rdma.write(self.rdma_addr["frm_gate"] + 2, frame_gap, 'frame gate frame gap')

    def data_stream(self, num_images):
        """Trigger FEM to output data."""
        self.frame_gate_settings(num_images - 1, 0)
        self.frame_gate_trigger()

    def _get_operation_percentage_complete(self):
        return self.operation_percentage_complete

    def _get_initialise_progress(self):
        return self.initialise_progress

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
        self.frame_rate = 1 if (self.frame_rate == 0) else self.frame_rate

        if self.number_frames != frames:
            self.number_frames = frames
            self.duration = self.number_frames / self.frame_rate

    def get_duration(self):
        """Set acquisition duration."""
        return self.duration

    def set_duration(self, duration):
        """Set duration, calculate frames to acquire using frame rate."""
        self.duration = duration
        frames = self.duration * self.frame_rate
        self.number_frames = int(round(frames))

    def get_health(self):
        """Get FEM health status."""
        return self.health

    def get_id(self):
        """Get FEM id."""
        return self.id

    def _start_polling(self):  # pragma: no cover
        IOLoop.instance().add_callback(self.poll_sensors)

    def poll_sensors(self):
        """Poll hardware while connected but not busy initialising, collecting offsets, etc."""
        if self.hardware_connected and (self.hardware_busy is False):
            self.read_sensors()
        IOLoop.instance().call_later(1.0, self.poll_sensors)

    def connect_hardware(self, msg=None):
        """Connect with hardware, wait 10 seconds for the VSRs' FPGAs to initialise."""
        try:
            if self.hardware_connected:
                raise ParameterTreeError("Connection already established")
            else:
                self._set_status_error("")
            self.operation_percentage_complete = 0
            self._set_status_message("Connecting to camera..")
            self.cam_connect()
            self._set_status_message("Camera connected. Waiting for VSRs' FPGAs \
                to initialise..")
            self._wait_while_fpgas_initialise()
            self.initialise_progress = 0
        except ParameterTreeError as e:
            self._set_status_error("%s" % str(e))
        except HexitecFemError as e:
            self._set_status_error("Failed to connect with camera: %s" % str(e))
            self._set_status_message("Is the camera powered?")
            logging.error("%s" % str(e))
        except Exception as e:
            error = "Uncaught Exception; Camera connection: %s" % str(e)
            self._set_status_error(error)
            logging.error("Camera connection: %s" % str(e))
            # Cannot raise error beyond current thread

        print("\n\nReinstate polling before merging with master !\n\n")
        # # Start polling thread (connect successfully set up)
        # if len(self.status_error) == 0:
        #     self._start_polling()

    @run_on_executor(executor='thread_executor')
    def initialise_hardware(self, msg=None):
        """Initialise sensors, load enables, etc to initialise both VSR boards."""
        try:
            if self.hardware_connected is not True:
                raise ParameterTreeError("No connection established")
            if self.hardware_busy:
                raise HexitecFemError("Hardware sensors busy initialising")
            else:
                self._set_status_error("")

            if self.debug_register24:  # pragma: no cover
                (vsr2, vsr1) = self.debug_reg24()
                print("\n")
                logging.debug("  * 00 *** init_HW, nowt chngd; Reg 0x24: %s, %s ***" % (vsr2, vsr1))

            self.hardware_busy = True
            self.operation_percentage_complete = 0
            self.operation_percentage_steps = 108
            self.initialise_system()
            if self.first_initialisation:
                # On cold start: Fudge initialisation to include silently capturing data without
                #    writing to disk, giving the user option to collect images with offsets
                #    without requiring a dummy data collection
                # "Tell" collect_data function hardware isn't busy, or it'll throw error
                self.ignore_busy = True
                if self.parent.daq.in_progress:
                    logging.warning("Cannot Start Acquistion: Already in progress")
                else:
                    # Start daq, expecting to collect 2 token frames
                    #   Token gesture as file writing disabled
                    self.parent.daq.start_acquisition(2)
                    for fem in self.parent.fems:
                        fem.collect_data()
            else:
                # Not cold initialisation, clear hardware_busy here
                self.hardware_busy = False
            self.initialise_progress = 0
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Failed to initialise camera: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Camera initialisation failed: %s" % str(e))
            logging.error("%s" % str(e))

    @run_on_executor(executor='thread_executor')
    def collect_data(self, msg=None):
        """Acquire data from camera."""
        try:
            if self.hardware_connected is not True:
                raise ParameterTreeError("No connection established")
            if self.hardware_busy and (self.ignore_busy is False):
                raise HexitecFemError("Hardware sensors busy initialising")
            else:
                self._set_status_error("")
            # Clear ignore_busy if set
            if self.ignore_busy:
                self.ignore_busy = False
            self.hardware_busy = True
            self.operation_percentage_complete = 0
            self.operation_percentage_steps = 100
            self._set_status_message("Acquiring data..")
            self.acquire_data()
            self.operation_percentage_complete = 100
            self.initialise_progress = 0
            # Acquisition completed, note completion
            self.acquisition_completed = True
            # Don't clear hardware_busy, wait for acquire_data() to clear it
            if self.first_initialisation:
                self._set_status_message("Initialisation from cold completed")
                self.first_initialisation = False
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Failed to collect data: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Data collection failed: %s" % str(e))
            logging.error("%s" % str(e))

    def disconnect_hardware(self, msg=None):
        """Disconnect camera."""
        try:
            if self.hardware_connected is False:
                raise ParameterTreeError("No connection to disconnect")
            else:
                self._set_status_error("")
            # Stop acquisition if it's hung
            if self.operation_percentage_complete < 100:
                self.stop_acquisition = True
            self.hardware_connected = False
            self.operation_percentage_complete = 0
            self._set_status_message("Disconnecting camera..")
            self.cam_disconnect()
            self._set_status_message("Camera disconnected")
            self.operation_percentage_complete = 100
            self.initialise_progress = 0
        except (HexitecFemError, ParameterTreeError) as e:
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

    def _wait_while_fpgas_initialise(self):
        """Set up to wait 10 seconds to allow VSRs' FPGAs to initialise."""
        self.hardware_busy = True
        self.start = time.time()
        self.delay = 10
        IOLoop.instance().call_later(1.0, self.initialisation_check_loop)

    def initialisation_check_loop(self):
        """Check for error and call itself each second until 10 second delay fulfilled."""
        if len(self.status_error) > 0:
            self.operation_percentage_complete = 0
            self.hardware_busy = False
            return
        self.delay = time.time() - self.start
        self.operation_percentage_complete += 10
        if (self.delay < 10):
            IOLoop.instance().call_later(1.0, self.initialisation_check_loop)
        else:
            self.hardware_busy = False
            self._set_status_message("Camera connected. FPGAs initialised.")

    def send_cmd(self, cmd, track_progress=True):
        """Send a command string to the microcontroller."""
        if track_progress:
            self.initialise_progress += 1
            self.operation_percentage_complete = (self.initialise_progress * 100) \
                // self.operation_percentage_steps

        while len(cmd) % 4 != 0:
            cmd.append(13)
        if self.debug:
            logging.debug("Length of command - %s %s" % (len(cmd), len(cmd) % 4))

        for i in range(0, len(cmd) // 4):
            reg_value = 256 * 256 * 256 * cmd[(i * 4)] + 256 * 256 * cmd[(i * 4) + 1] \
                + 256 * cmd[(i * 4) + 2] + cmd[(i * 4) + 3]
            self.x10g_rdma.write(0xE0000100, reg_value, 'Write 4 Bytes')

    def read_response(self):
        """Read a VSR's microcontroller response, passed on by the FEM."""
        data_counter = 0
        f = []
        ABORT_VALUE = 10000
        RETURN_START_CHR = 42
        CARRIAGE_RTN = 13
        FIFO_EMPTY_FLAG = 1
        empty_count = 0
        daty = RETURN_START_CHR
        # Example: daty will contain:
        # 0x23, self.vsr_addr, HexitecFem.SEND_REG_VALUE, 0x30, 0x41, 0x30, 0x30, 0x0D

        # JE modifications
        daty1, daty2 = RETURN_START_CHR, RETURN_START_CHR
        daty3, daty4 = RETURN_START_CHR, RETURN_START_CHR

        while daty != CARRIAGE_RTN:

            fifo_empty = FIFO_EMPTY_FLAG

            while fifo_empty == FIFO_EMPTY_FLAG and empty_count < ABORT_VALUE:
                fifo_empty = self.x10g_rdma.read(0xE0000011, 'FIFO EMPTY FLAG')
                empty_count = empty_count + 1

            dat = self.x10g_rdma.read(0xE0000200, 'Data')

            daty = (dat >> 24) & 0xFF
            f.append(daty)
            daty1 = daty

            daty = (dat >> 16) & 0xFF
            f.append(daty)
            daty2 = daty

            daty = (dat >> 8) & 0xFF
            f.append(daty)
            daty3 = daty

            daty = dat & 0xFF
            f.append(daty)
            daty4 = daty

            if self.debug:
                logging.debug('{0:0{1}x} {2:0{3}x} {4:0{5}x} {6:0{7}x}'.format(daty1, 2, daty2, 2,
                                                                               daty3, 2, daty4, 2))

            data_counter = data_counter + 1
            if empty_count == ABORT_VALUE:
                logging.error("Error: read_response from FEM aborted")
                self.exception_triggered = True
                raise HexitecFemError("read_response aborted")
            empty_count = 0

        # Diagnostics: Count number of successful reads before 1st Exception thrown
        if self.exception_triggered is False:
            self.successful_reads += 1

        if self.debug:
            logging.debug("Counter is :- %s Length is:- %s" % (data_counter, len(f)))

        fifo_empty = self.x10g_rdma.read(0xE0000011, 'Data')
        if self.debug:
            logging.debug("FIFO should be empty: %s" % fifo_empty)
        s = ''

        for i in range(1, data_counter * 4):
            s = s + chr(f[i])

        if self.debug:
            logging.debug("String :- %s" % s)
            logging.debug(f[0])
            logging.debug(f[1])
            logging.debug(f[2])
            logging.debug(f[3])

        return s

    def cam_connect(self):
        """Send commands to connect camera."""
        self.hardware_connected = True
        logging.debug("Connecting camera")
        try:
            self.connect()
            logging.debug("Camera connected")
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], 0xE3, 0x0D])
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], 0xE3, 0x0D])
            logging.debug("Modules Enabled")
        except socket_error as e:
            self.hardware_connected = False
            raise HexitecFemError(e)

    def cam_disconnect(self):
        """Send commands to disconnect camera."""
        self.hardware_connected = False
        try:
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], 0xE2, 0x0D])
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], 0xE2, 0x0D])
            logging.debug("Modules Disabled")
            self.disconnect()
            logging.debug("Camera is Disconnected")
        except socket_error as e:
            logging.error("Unable to disconnect camera: %s" % str(e))
            raise HexitecFemError(e)
        except AttributeError as e:
            logging.error("Unable to disconnect camera: %s" % "No active connection")
            raise HexitecFemError("%s; %s" % (e, "No active connection"))

    def initialise_sensor(self):
        """Initialise sensors attached to selected VSR."""
        self.x10g_rdma.write(0x60000002, 0, 'Disable State Machine Trigger')
        logging.debug("Disable State Machine Enabling signal")

        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.x10g_rdma.write(0x60000004, 0, 'Set bit 0 to 1 to generate test pattern in FEMII, \
                bits [2:1] select which of the 4 sensors is read - data 1_1')
            logging.debug("Initialising sensors on board VSR_1")
            self.vsr_addr = HexitecFem.VSR_ADDRESS[0]
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.x10g_rdma.write(0x60000004, 4, 'Set bit 0 to 1 to generate test pattern in FEMII, \
                bits [2:1] select which of the 4 sensors is read - data 2_1')
            logging.debug("Initialising sensors on board VSR 2")
            self.vsr_addr = HexitecFem.VSR_ADDRESS[1]

        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            logging.debug("Disable synchronisation SM start")
            self.send_cmd([0x23, self.vsr_addr, HexitecFem.SEND_REG_VALUE, 0x30, 0x41,
                           0x30, 0x30, 0x0D])
            self.read_response()
            logging.debug("Reading out single sensor")
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            logging.debug("Enable synchronisation SM start via trigger 1")
            self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT, 0x30, 0x41,
                           0x30, 0x31, 0x0D])
            self.read_response()
            logging.debug("Reading out 2x2 sensors")

        logging.debug("Communicating with - %s" % self.vsr_addr)
        # Set Frame Gen Mux Frame Gate
        self.x10g_rdma.write(0x60000001, 2, 'Set Frame Gen Mux Frame Gate - works set to 2')

        logging.debug("Enable Test Pattern in my VSR design")
        # Use Sync clock from DAQ board
        logging.debug("Use Sync clock from DAQ board")
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x31, 0x30, 0x0D])
        self.read_response()

        logging.debug("Enable LVDS outputs")
        set_register_vsr1_command = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.SET_REG_BIT,
                                     0x30, 0x31, 0x32, 0x30, 0x0D]
        set_register_vsr2_command = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.SET_REG_BIT,
                                     0x30, 0x31, 0x32, 0x30, 0x0D]
        self.send_cmd(set_register_vsr1_command)
        self.read_response()
        self.send_cmd(set_register_vsr2_command)
        self.read_response()
        logging.debug("LVDS outputs enabled")

        # TODO: Did James mean "0x45" rather than "0x4E"..?
        #       The register is called "Serial Training Pattern" in documentation
        logging.debug("Read LO IDLE")
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SEND_REG_VALUE,
                       0x46, 0x45, 0x41, 0x41, 0x0D])
        self.read_response()
        logging.debug("Read HI IDLE")
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SEND_REG_VALUE,
                       0x46, 0x46, 0x4E, 0x41, 0x0D])
        self.read_response()

        # This sets up test pattern on LVDS outputs
        logging.debug("Set up LVDS test pattern")
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x43, 0x30, 0x0D])
        self.read_response()
        # Use default test pattern of 1000000000000000
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x38, 0x30, 0x0D])
        self.read_response()

        full_empty = self.x10g_rdma.read(0x60000011, 'Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.x10g_rdma.read(0x60000012, 'Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)

    def debug_reg24(self):  # pragma: no cover
        """Debug function: Display contents of register 24."""
        self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.READ_REG_VALUE,
                       0x32, 0x34, 0x0D])
        vsr2 = self.read_response().strip("\r")
        self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.READ_REG_VALUE,
                       0x32, 0x34, 0x0D])
        vsr1 = self.read_response().strip("\r")
        return (vsr2, vsr1)

    def calibrate_sensor(self):  # noqa: C901
        """Calibrate sensors attached to targeted VSR."""
        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            logging.debug("Reading out single sensor")
            self.set_image_size(80, 80, 14, 16)
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            self.set_image_size(160, 160, 14, 16)
            logging.debug("Reading out 2x2 sensors")

        logging.debug("Clear bit 5")
        # Clear bit; Register 0x24, bit5: disable VCAL (i.e. VCAL is here ENABLED)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.CLR_REG_BIT, 0x32, 0x34, 0x32, 0x30, 0x0D])
        self.read_response()

        if self.debug_register24:  # pragma: no cover
            (vsr2, vsr1) = self.debug_reg24()
            print("\n")
            logging.debug("  * 02 *** cal_sen, CLR bit5;   Reg 0x24: %s, %s ***" % (vsr2, vsr1))

        # Set bit; Reg24, bit4: send average picture
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT, 0x32, 0x34, 0x31, 0x30, 0x0D])
        self.read_response()
        if self.debug_register24:  # pragma: no cover
            (vsr2, vsr1) = self.debug_reg24()
            print("\n")
            logging.debug("  * 03 *** cal_sen, SET bit4;   Reg 0x24: %s, %s ***" % (vsr2, vsr1))

        logging.debug("Set bit 6")
        # Clear bit; Register 0x24, bit6: test mode
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.CLR_REG_BIT, 0x32, 0x34, 0x34, 0x30, 0x0D])
        self.read_response()
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.READ_REG_VALUE, 0x30, 0x31, 0x0D])
        self.read_response()
        if self.debug_register24:  # pragma: no cover
            (vsr2, vsr1) = self.debug_reg24()
            print("\n")
            logging.debug("  * 04 *** cal_sen, CLR bit6;   Reg 0x24: %s, %s ***" % (vsr2, vsr1))

        # Slows data coll'ns down (by adding 8k extra frames..)       # JE original
        # Set bit; Register 0x24, bit5 (disable VCAL), bit1 (capture average picture)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT, 0x32, 0x34, 0x32, 0x32, 0x0D])
        self.read_response()
        if self.debug_register24:  # pragma: no cover
            (vsr2, vsr1) = self.debug_reg24()
            print("\n")
            logging.debug("  * 05 *** cal_sen, SET b5,b1;  Reg 0x24: %s, %s ***" % (vsr2, vsr1))

        # #Makes data acquisition as fast as it should be (no extra 8k for offsets..)    # My mod
        # # Set bit; Register 0x24, bit5 (disable VCAL)
        # self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT, 0x32, 0x34, 0x32, 0x30, 0x0D])
        # self.read_response()
        # if self.debug_register24:  # pragma: no cover
        #     (vsr2, vsr1) = self.debug_reg24()
        #     print("\n")
        #     logging.debug("  * X6 *** cal_sen, SET b5;     Reg 0x24: %s, %s ***" % (vsr2, vsr1))

        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.x10g_rdma.write(0x60000002, 1, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            logging.debug("CALIBRATING VSR_1")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.x10g_rdma.write(0x60000002, 2, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            logging.debug("CALIBRATING VSR_2")

        # Send command on CMD channel to FEMII
        self.x10g_rdma.write(0x60000002, 0, 'Un-Trigger Cal process')

        # Reading back Sync register
        synced = self.x10g_rdma.read(0x60000010, 'Check LVDS has synced')
        logging.debug("Sync Register value")

        full_empty = self.x10g_rdma.read(0x60000011, 'Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)

        full_empty = self.x10g_rdma.read(0x60000012, 'Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)

        # Check whether the currently selected VSR has synchronised or not
        if synced == 15:  # pragma: no cover
            logging.debug("All Links on VSR's 1 and 2 synchronised")
            logging.debug("Starting State Machine in VSR's")
        elif synced == 12:  # pragma: no cover
            logging.debug("Both Links on VSR 2 synchronised")
        elif synced == 3:  # pragma: no cover
            logging.debug("Both Links on VSR 1 synchronised")
        else:
            logging.debug(synced)

        if (self.vsr_addr == HexitecFem.VSR_ADDRESS[0]):
            self.vsr1_sync = synced
        elif (self.vsr_addr == HexitecFem.VSR_ADDRESS[1]):
            self.vsr2_sync = synced

        # Clear training enable
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x43, 0x30, 0x0D])
        self.read_response()

        logging.debug("Clear bit 5 - VCAL ENABLED")
        # Clear bit; Register 0x24, bit5: disable VCAL (i.e. VCAL is here ENABLED)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.CLR_REG_BIT, 0x32, 0x34,
                       0x32, 0x30, 0x0D])
        self.read_response()

        if self.debug_register24:  # pragma: no cover
            (vsr2, vsr1) = self.debug_reg24()
            print("\n")
            logging.debug("  * 06 *** cal_sen, CLR b5;     Reg 0x24: %s, %s ***" % (vsr2, vsr1))

        logging.debug("DARK CORRECTION ON")
        # Set bit; Register 0x24, bit3: enable DC spectroscopic mode
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT, 0x32, 0x34,
                       0x30, 0x38, 0x0D])
        self.read_response()
        if self.debug_register24:  # pragma: no cover
            (vsr2, vsr1) = self.debug_reg24()
            print("\n")
            logging.debug("  * 08 *** cal_sen, SET b3;     Reg 0x24: %s, %s ***" % (vsr2, vsr1))

        # Read Reg24
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.READ_REG_VALUE, 0x32, 0x34, 0x0D])
        if self.debug:
            logging.debug("Reading Register 0x24")
            logging.debug(self.read_response())
        else:
            self.read_response()

        self.send_cmd([0x23, self.vsr_addr, HexitecFem.READ_REG_VALUE, 0x38, 0x39, 0x0D])
        self.read_response()

        if self.debug:
            logging.debug("Poll register 0x89")
        bPolling = True
        time_taken = 0
        while bPolling:
            self.send_cmd([0x23, self.vsr_addr, HexitecFem.READ_REG_VALUE, 0x38, 0x39, 0x0D])
            reply = self.read_response()
            reply = reply.strip()
            Bit1 = int(reply[-1], 16)
            if self.debug:
                logging.debug("Register 0x89, Bit1: %s" % Bit1)
            # Is PLL locked? (Bit1 high)
            if Bit1 & 2:
                bPolling = False
            else:
                time.sleep(0.1)
                time_taken += 0.1
            if time_taken > 3.0:
                raise HexitecFemError("Timed out polling register 0x89; PLL remains disabled")
        if self.debug:
            logging.debug("Bit 1 should be 1")
            logging.debug(reply)
            logging.debug("Read reg 1")
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.READ_REG_VALUE, 0x30, 0x31, 0x0D])
        self.read_response()

        full_empty = self.x10g_rdma.read(0x60000011, 'Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)

        full_empty = self.x10g_rdma.read(0x60000012, 'Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)

        return synced

    def acquire_data(self):  # noqa: C901
        """Acquire data, polls fem for completion and reads out fem monitors."""
        # If called as part of cold initialisation, only need one frame so
        #   temporarily overwrite UI's number of frames for this call only
        number_frames = self.number_frames
        if self.first_initialisation:
            # Don't set to 1, as rdma write subtracts 1 (and 0 = continuous readout!)
            self.number_frames = 2

        self.x10g_rdma.write(0xD0000001, self.number_frames - 1, 'Frame Gate set to \
            self.number_frames')

        full_empty = self.x10g_rdma.read(0x60000011, 'Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)

        full_empty = self.x10g_rdma.read(0x60000012, 'Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)

        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            logging.debug("Reading out single sensor")
            mux_mode = 0
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            mux_mode = 8
            logging.debug("Reading out 2x2 sensors")

        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.x10g_rdma.write(0x60000004, 0 + mux_mode, 'Sensor 1 1')
            logging.debug("Sensor 1 1")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.x10g_rdma.write(0x60000004, 4 + mux_mode, 'Sensor 2 1')
            logging.debug("Sensor 2 1")

        # Flush the input FIFO buffers
        self.x10g_rdma.write(0x60000002, 32, 'Clear Input Buffers')
        self.x10g_rdma.write(0x60000002, 0, 'Clear Input Buffers')
        full_empty = self.x10g_rdma.read(0x60000011, 'Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.x10g_rdma.read(0x60000012, 'Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)

        if self.sensors_layout == HexitecFem.READOUTMODE[1]:
            self.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')

        if self.debug:
            logging.debug("number of Frames := %s" % self.number_frames)

        if self.debug_register24:  # pragma: no cover
            (vsr2, vsr1) = self.debug_reg24()
            print("\n")
            logging.debug("    ****** ACQUISITION;  Reg 0x24: %s, %s ***" % (vsr2, vsr1))

        logging.debug("Initiate Data Capture")
        self.data_stream(self.number_frames)
        self.acquire_start_time = '%s' % (datetime.now().strftime(HexitecFem.DATE_FORMAT))
        # How to convert datetime object to float?
        self.acquire_timestamp = time.time()

        waited = 0.0
        delay = 0.10
        resp = 0
        while True:
            resp = self.x10g_rdma.read(0x60000014, 'Check data transfer completed?')
            if resp > 0:
                break
            time.sleep(delay)
            waited += delay
            if (self.stop_acquisition):
                logging.error(" -=-=-=- HEXITECFEM INSTRUCTED TO STOP ACQUISITION -=-=-=-")
                break

        self.acquire_stop_time = '%s' % (datetime.now().strftime(HexitecFem.DATE_FORMAT))

        # Stop the state machine
        self.x10g_rdma.write(0x60000002, 0, 'Dis-Enable State Machine')

        # Clear enable signal
        self.x10g_rdma.write(0xD0000000, 2, 'Clear enable signal')
        self.x10g_rdma.write(0xD0000000, 0, 'Clear enable signal')

        if self.stop_acquisition:
            logging.error("Acquisition stopped prematurely")
            # Reset variables
            self.stop_acquisition = False
            self.operation_percentage_complete = 100
            self.initialise_progress = 0
            self.hardware_busy = False
            raise HexitecFemError("Acquire interrupted")
        else:
            logging.debug("Capturing {} frames took {} s".format(str(self.number_frames),
                                                                 str(waited)))
            duration = "Requested %s frame(s), took %s seconds" % (self.number_frames, str(waited))
            self._set_status_message(duration)
            # Save duration to separate parameter tree entry:
            self.acquisition_duration = duration

        logging.debug("Acquisition Completed, enable signal cleared")

        # Clear the Mux Mode bit
        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.x10g_rdma.write(0x60000004, 0, 'Sensor 1 1')
            logging.debug("Sensor 1 1")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.x10g_rdma.write(0x60000004, 4, 'Sensor 2 1')
            logging.debug("Sensor 2 1")
        full_empty = self.x10g_rdma.read(0x60000011, 'Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.x10g_rdma.read(0x60000012, 'Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        no_frames = self.x10g_rdma.read(0xD0000001, 'Check Number of Frames setting') + 1
        logging.debug("Number of Frames: %s" % no_frames)

        logging.debug("Output from Sensor")
        m0 = self.x10g_rdma.read(0x70000010, 'frame last length')
        logging.debug("frame last length: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000011, 'frame max length')
        logging.debug("frame max length: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000012, 'frame min length')
        logging.debug("frame min length: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000013, 'frame number')
        logging.debug("frame number: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000014, 'frame last clock cycles')
        logging.debug("frame last clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000015, 'frame max clock cycles')
        logging.debug("frame max clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000016, 'frame min clock cycles')
        logging.debug("frame min clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000017, 'frame data total')
        logging.debug("frame data total: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000018, 'frame data total clock cycles')
        logging.debug("frame data total clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x70000019, 'frame trigger count')
        logging.debug("frame trigger count: %s" % m0)
        m0 = self.x10g_rdma.read(0x7000001A, 'frame in progress flag')
        logging.debug("frame in progress flag: %s" % m0)

        logging.debug("Output from Frame Gate")
        m0 = self.x10g_rdma.read(0x80000010, 'frame last length')
        logging.debug("frame last length: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000011, 'frame max length')
        logging.debug("frame max length: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000012, 'frame min length')
        logging.debug("frame min length: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000013, 'frame number')
        logging.debug("frame number: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000014, 'frame last clock cycles')
        logging.debug("frame last clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000015, 'frame max clock cycles')
        logging.debug("frame max clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000016, 'frame min clock cycles')
        logging.debug("frame min clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000017, 'frame data total')
        logging.debug("frame data total: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000018, 'frame data total clock cycles')
        logging.debug("frame data total clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x80000019, 'frame trigger count')
        logging.debug("frame trigger count: %s" % m0)
        m0 = self.x10g_rdma.read(0x8000001A, 'frame in progress flag')
        logging.debug("frame in progress flag: %s" % m0)

        logging.debug("Input to XAUI")  # Conn'd to 10G core going out
        m0 = self.x10g_rdma.read(0x90000010, 'frame last length')
        logging.debug("frame last length: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000011, 'frame max length')
        logging.debug("frame max length: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000012, 'frame min length')
        logging.debug("frame min length: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000013, 'frame number')
        logging.debug("frame number: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000014, 'frame last clock cycles')
        logging.debug("frame last clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000015, 'frame max clock cycles')
        logging.debug("frame max clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000016, 'frame min clock cycles')
        logging.debug("frame min clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000017, 'frame data total')
        logging.debug("frame data total: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000018, 'frame data total clock cycles')
        logging.debug("frame data total clock cycles: %s" % m0)
        m0 = self.x10g_rdma.read(0x90000019, 'frame trigger count')
        logging.debug("frame trigger count: %s" % m0)
        m0 = self.x10g_rdma.read(0x9000001A, 'frame in progress flag')
        logging.debug("frame in progress flag: %s" % m0)

        # Fem finished sending data/monitoring info, clear hardware busy
        self.hardware_busy = False

        # Workout exact duration of fem data transmission:
        self.acquire_time = float(self.acquire_stop_time.split("_")[1]) \
            - float(self.acquire_start_time.split("_")[1])
        start_ = datetime.strptime(self.acquire_start_time, HexitecFem.DATE_FORMAT)
        stop_ = datetime.strptime(self.acquire_stop_time, HexitecFem.DATE_FORMAT)
        self.acquire_time = (stop_ - start_).total_seconds()

        if self.first_initialisation:
            self.number_frames = number_frames

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
        # TODO: What's register_007 called?
        value_007 = 0x30, 0x33  # UNNAMED, 2 bits : 1 = Enable PLL; 2 = Enable ADC PLL (3 = both)
        value_009 = 0x30, 0x32  # ADC1 Delay, 5 bits : 2 = 2 clock cycles
        value_00E = 0x30, 0x41
        value_018 = 0x30, 0x31  # VCAL2 -> VCAL1 Low Byte, 8 bits: 1 = 1 clock cycle
        value_019 = 0x30, 0x30  # VCAL2 -> VCAL1 High Byte, 7 bits
        value_01B = 0x30, 0x38  # Wait Clock Row, 8 bits
        value_014 = 0x30, 0x31  # Start SM on '1' falling edge ('0' = rising edge) of ADC-CLK

        # # TODO: Find/Determine settings name in hexitec file?
        # noname = self._extract_integer(self.hexitec_parameters, 'Control-Settings/??',
        #                                bit_range=2)
        # if noname > -1:
        #     value_007 = self.convert_to_aspect_format(noname)
        # Send noname (Enable PPL, ADC PPL) to Register 0x07 (Accepts 2 bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_007[0], register_007[1], value_007[0], value_007[1], 0x0D])
        self.read_response()

        if self.row_s1 > -1:
            # Valid value, within range
            self.row_s1_low = self.row_s1 & 0xFF
            self.row_s1_high = self.row_s1 >> 8
            value_002 = self.convert_to_aspect_format(self.row_s1_low)
            value_003 = self.convert_to_aspect_format(self.row_s1_high)
        # Send RowS1 low byte to Register 0x02 (Accepts 8 bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                       register_002[0], register_002[1], value_002[0], value_002[1], 0x0D])
        self.read_response()
        # Send RowS1 high byte to Register 0x03 (Accepts 6 bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                       register_003[0], register_003[1], value_003[0], value_003[1], 0x0D])
        self.read_response()

        if self.s1_sph > -1:
            value_004 = self.convert_to_aspect_format(self.s1_sph)
        # Send S1SPH to Register 0x04 (Accepts 6 bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                       register_004[0], register_004[1], value_004[0], value_004[1], 0x0D])
        self.read_response()

        if self.sph_s2 > -1:
            value_005 = self.convert_to_aspect_format(self.sph_s2)
        # Send SphS2  to Register 0x05 (Accepts 6 Bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                       register_005[0], register_005[1], value_005[0], value_005[1], 0x0D])
        self.read_response()

        # # Debuggery
        # print("\n")
        # print("  row_S1,       value_002: 0x%x, 0x%x       value_003: 0x%x, 0x%x" %
        #       (value_002[0], value_002[1], value_003[0], value_003[1]))
        # print("  S1_SpH,       value_004: 0x%x, 0x%x" % (value_004[0], value_004[1]))
        # print("  Sph_s2,       value_005: 0x%x, 0x%x\n" % (value_005[0], value_005[1]))

        # sm_timing2 = [0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
        #               register_002[0], register_002[1], value_002[0], value_002[1], 0x0D]
        # S1_SPH = self.make_list_hexadecimal([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
        #                                      register_004[0], register_004[1],
        #                                      value_004[0], value_004[1], 0x0D])
        # SPH_S2 = self.make_list_hexadecimal([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
        #                                      register_005[0], register_005[1],
        #                                      value_005[0], value_005[1], 0x0D])
        # print("  sm_timing2, ", self.make_list_hexadecimal(sm_timing2))
        # print("  S1_SPH, ", S1_SPH)
        # print("  SPH_S2, ", SPH_S2)
        # print("\n")

        # TODO: What should default value be? (not set by JE previously!)
        gain = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Gain', bit_range=1)
        if gain > -1:
            value_006 = self.convert_to_aspect_format(gain)
        # Send Gain to Register 0x06 (Accepts 1 Bit)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_006[0], register_006[1], value_006[0], value_006[1], 0x0D])
        self.read_response()

        adc1_delay = self._extract_integer(self.hexitec_parameters, 'Control-Settings/ADC1 Delay',
                                           bit_range=2)
        if adc1_delay > -1:
            value_009 = self.convert_to_aspect_format(adc1_delay)
        # Send ADC1 Delay to Register 0x09 (Accepts 2 Bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_009[0], register_009[1], value_009[0], value_009[1], 0x0D])
        self.read_response()

        delay_sync_signals = self._extract_integer(self.hexitec_parameters,
                                                   'Control-Settings/delay sync signals',
                                                   bit_range=8)
        if delay_sync_signals > -1:
            value_00E = self.convert_to_aspect_format(delay_sync_signals)
        # Send delay sync signals to Register 0x0E (Accepts 8 Bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_00E[0], register_00E[1], value_00E[0], value_00E[1], 0x0D])
        self.read_response()

        # # TODO: Name for this setting in .ini file ??
        # wait_clock_row = self._extract_integer(self.hexitec_parameters,
        #                                        'Control-Settings/???', bit_range=8)
        # if wait_clock_row > -1:
        #     value_01B = self.convert_to_aspect_format(wait_clock_row)
        # Send wait clock wait to Register 01B (Accepts 8 Bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_01B[0], register_01B[1], value_01B[0], value_01B[1], 0x0D])
        self.read_response()

        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_014[0], register_014[1], value_014[0], value_014[1], 0x0D])
        self.read_response()

        vcal2_vcal1 = self._extract_integer(self.hexitec_parameters,
                                            'Control-Settings/VCAL2 -> VCAL1', bit_range=15)
        if vcal2_vcal1 > -1:
            vcal2_vcal1_low = vcal2_vcal1 & 0xFF
            vcal2_vcal1_high = vcal2_vcal1 >> 8
            value_018 = self.convert_to_aspect_format(vcal2_vcal1_low)
            value_019 = self.convert_to_aspect_format(vcal2_vcal1_high)
        # Send VCAL2 -> VCAL1 low byte to Register 0x02 (Accepts 8 bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_018[0], register_018[1], value_018[0], value_018[1], 0x0D])
        self.read_response()
        # Send VCAL2 -> VCAL1 high byte to Register 0x03 (Accepts 7 bits)
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.SET_REG_BIT,
                      register_019[0], register_019[1], value_019[0], value_019[1], 0x0D])
        self.read_response()

        # # DEBUG
        # print("");print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-");print("")
        # print(" VCAL2, L:", self.make_list_hexadecimal([0x23, self.vsr_addr,
        #       HexitecFem.SET_REG_BIT, register_018[0], register_018[1],
        #       value_018[0], value_018[1], 0x0D]))
        # print(" VCAL2, H:", self.make_list_hexadecimal([0x23, self.vsr_addr,
        #       HexitecFem.SET_REG_BIT, register_019[0], register_019[1],
        #       value_019[0], value_019[1], 0x0D]))
        # print("");print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-");print("")

        # Recalculate frame_rate, et cetera if new clock values provided by .ini
        self.calculate_frame_rate()

        logging.debug("Finished Setting up state machine")

    @run_on_executor(executor='thread_executor')
    def collect_offsets(self):
        """Run collect offsets sequence.

        Stop state machine, gathers offsets, calculats average picture, re-starts state machine.
        """
        try:
            if self.hardware_connected is not True:
                raise ParameterTreeError("Can't collect offsets while disconnected")
            if self.hardware_busy:
                raise HexitecFemError("Hardware sensors busy initialising")
            else:
                self._set_status_error("")

            self.hardware_busy = True
            self.operation_percentage_complete = 0
            self.operation_percentage_steps = 15

            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0],
                          HexitecFem.READ_REG_VALUE, 0x32, 0x34, 0x0D])
            vsr1 = self.read_response()
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1],
                          HexitecFem.READ_REG_VALUE, 0x32, 0x34, 0x0D])
            vsr2 = self.read_response()
            logging.debug("Reading back register 24; VSR1: '%s' VSR2: '%s'" %
                          (vsr1.replace('\r', ''), vsr2.replace('\r', '')))

            # Set bit; Register 0x24, bit4: send average picture
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0],
                          HexitecFem.SET_REG_BIT, 0x32, 0x34, 0x31, 0x30, 0x0D])
            self.read_response()
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1],
                          HexitecFem.SET_REG_BIT, 0x32, 0x34, 0x31, 0x30, 0x0D])
            self.read_response()
            if self.debug_register24:  # pragma: no cover
                (vsr2, vsr1) = self.debug_reg24()
                print("\n")
                logging.debug("  * 09 *** coll_off, SET b4;    Reg 0x24: %s, %s ***" % (vsr2, vsr1))

            # Send reg value; Register 0x24, bits5,1: disable VCAL, capture average picture:
            enable_dc_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.SEND_REG_VALUE,
                              0x32, 0x34, 0x32, 0x32, 0x0D]
            enable_dc_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.SEND_REG_VALUE,
                              0x32, 0x34, 0x32, 0x32, 0x0D]
            # Send reg value; Register 0x24, bits5,3: disable VCAL, enable spectroscopic mode:
            disable_dc_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.SEND_REG_VALUE,
                               0x32, 0x34, 0x32, 0x38, 0x0D]
            disable_dc_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.SEND_REG_VALUE,
                               0x32, 0x34, 0x32, 0x38, 0x0D]
            enable_sm_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.SET_REG_BIT,
                              0x30, 0x31, 0x30, 0x31, 0x0D]
            enable_sm_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.SET_REG_BIT,
                              0x30, 0x31, 0x30, 0x31, 0x0D]
            disable_sm_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.CLR_REG_BIT,
                               0x30, 0x31, 0x30, 0x30, 0x0D]
            disable_sm_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.CLR_REG_BIT,
                               0x30, 0x31, 0x30, 0x30, 0x0D]

            # 1. System is fully initialised (Done already)

            # 2. Stop the state machine

            self.send_cmd(disable_sm_vsr1)
            self.read_response()
            self.send_cmd(disable_sm_vsr2)
            self.read_response()

            # 3. Set reg 0x24 to 0x22

            logging.debug("Gathering offsets..")
            self.send_cmd(enable_dc_vsr1)
            self.read_response()
            self.send_cmd(enable_dc_vsr2)
            self.read_response()
            if self.debug_register24:  # pragma: no cover
                (vsr2, vsr1) = self.debug_reg24()
                print("\n")
                logging.debug("  * 10 *** coll_off, SET b1,5;  Reg 0x24: %s, %s ***" % (vsr2, vsr1))

            # 4. Start the state machine

            self.send_cmd(enable_sm_vsr1)
            self.read_response()
            self.send_cmd(enable_sm_vsr2)
            self.read_response()

            # 5. Wait > 8192 * frame time (1 second)

            time.sleep(1)

            # 6. Stop state machine

            self.send_cmd(disable_sm_vsr1)
            self.read_response()
            self.send_cmd(disable_sm_vsr2)
            self.read_response()

            # 7. Set reg 0x24 to 0x28

            logging.debug("Offsets collected")
            self.send_cmd(disable_dc_vsr1)
            self.read_response()
            self.send_cmd(disable_dc_vsr2)
            self.read_response()
            if self.debug_register24:  # pragma: no cover
                (vsr2, vsr1) = self.debug_reg24()
                print("\n")
                logging.debug("  * 11 *** coll_off, SET b3,5;  Reg 0x24: %s, %s ***" % (vsr2, vsr1))

            # 8. Start state machine

            self.send_cmd(enable_sm_vsr1)
            self.read_response()
            self.send_cmd(enable_sm_vsr2)
            self.read_response()

            logging.debug("Ensure VCAL remains on")
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.CLR_REG_BIT,
                           0x32, 0x34, 0x32, 0x30, 0x0D])
            self.read_response()
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.CLR_REG_BIT,
                           0x32, 0x34, 0x32, 0x30, 0x0D])
            self.read_response()

            if self.debug_register24:  # pragma: no cover
                (vsr2, vsr1) = self.debug_reg24()
                print("\n")
                logging.debug("  * 12 *** coll_off, SET b5;    Reg 0x24: %s, %s ***" % (vsr2, vsr1))

            self.operation_percentage_complete = 100
            self._set_status_message("Offsets collections operation completed.")
            self.hardware_busy = False
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Can't collect offsets while disconnected: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Failed to collect offsets: %s" % str(e))
            logging.error("%s" % str(e))

    def load_pwr_cal_read_enables(self):  # noqa: C901
        """Load power, calibration and read enables - optionally from hexitec file."""
        # The default values are either 20 times 0 (0x30), or 20 times F (0x46)
        #   Make a list for each of these scenarios: (and use where needed)
        list_of_46s = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                       0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        list_of_30s = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                       0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        enable_sm = [0x23, self.vsr_addr, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]
        disable_sm = [0x23, self.vsr_addr, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]

        vsr = -1
        if self.vsr_addr == HexitecFem.VSR_ADDRESS[0]:  # 0x90
            vsr = 1
        else:
            if self.vsr_addr == HexitecFem.VSR_ADDRESS[1]:  # 0x91
                vsr = 2
            else:
                raise HexitecFemError("Unknown VSR address! (%s)" % self.vsr_addr)

        register_061 = [0x36, 0x31]   # Column Read Enable ASIC1
        register_0C2 = [0x43, 0x32]   # Column Read Enable ASIC2
        value_061 = list_of_46s
        value_0C2 = list_of_46s

        asic1_read_enable = self._extract_80_bits(self.hexitec_parameters, "ColumnEn_",
                                                  vsr, 1, "Channel")
        # Check list of (-1, -1) tuples wasn't returned
        if asic1_read_enable[0][0] > 0:
            asic1_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_061[0], register_061[1]]
            for msb, lsb in asic1_read_enable:
                asic1_command.append(msb)
                asic1_command.append(lsb)
            asic1_command.append(0x0D)
            # Column Read Enable, for ASIC1 (Reg 0x61)
            col_read_enable1 = asic1_command
        else:
            # No ini file loaded, use default values
            col_read_enable1 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST, register_061[0],
                                register_061[1], value_061[0], value_061[1], value_061[2],
                                value_061[3], value_061[4], value_061[5], value_061[6],
                                value_061[7], value_061[8], value_061[9], value_061[10],
                                value_061[11], value_061[12], value_061[13], value_061[14],
                                value_061[15], value_061[16], value_061[17], value_061[18],
                                value_061[19], 0x0D]

        asic2_read_enable = self._extract_80_bits(self.hexitec_parameters, "ColumnEn_",
                                                  vsr, 2, "Channel")
        if asic2_read_enable[0][0] > 0:
            asic2_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_0C2[0], register_0C2[1]]
            for msb, lsb in asic2_read_enable:
                asic2_command.append(msb)
                asic2_command.append(lsb)
            asic2_command.append(0x0D)
            col_read_enable2 = asic2_command
        else:
            # Column Read Enable, for ASIC2 (Reg 0xC2)
            col_read_enable2 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                                register_0C2[0], register_0C2[1], value_0C2[0], value_0C2[1],
                                value_0C2[2], value_0C2[3], value_0C2[4], value_0C2[5],
                                value_0C2[6], value_0C2[7], value_0C2[8], value_0C2[9],
                                value_0C2[10], value_0C2[11], value_0C2[12], value_0C2[13],
                                value_0C2[14], value_0C2[15], value_0C2[16], value_0C2[17],
                                value_0C2[18], value_0C2[19], 0x0D]

        # Column Power Enable

        register_04D = [0x34, 0x44]   # Column Power Enable ASIC1 (Reg 0x4D)
        register_0AE = [0x41, 0x45]   # Column Power Enable ASIC2 (Reg 0xAE)
        value_04D = list_of_46s
        value_0AE = list_of_46s

        asic1_power_enable = self._extract_80_bits(self.hexitec_parameters, "ColumnPwr",
                                                   vsr, 1, "Channel")
        if asic1_power_enable[0][0] > 0:
            asic1_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_04D[0], register_04D[1]]
            for msb, lsb in asic1_power_enable:
                asic1_command.append(msb)
                asic1_command.append(lsb)
            asic1_command.append(0x0D)
            col_power_enable1 = asic1_command
        else:
            # Column Power Enable, for ASIC1 (Reg 0x4D)
            col_power_enable1 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                                 register_04D[0], register_04D[1], value_04D[0], value_04D[1],
                                 value_04D[2], value_04D[3], value_04D[4], value_04D[5],
                                 value_04D[6], value_04D[7], value_04D[8], value_04D[9],
                                 value_04D[10], value_04D[11], value_04D[12], value_04D[13],
                                 value_04D[14], value_04D[15], value_04D[16], value_04D[17],
                                 value_04D[18], value_04D[19], 0x0D]

        asic2_power_enable = self._extract_80_bits(self.hexitec_parameters, "ColumnPwr",
                                                   vsr, 2, "Channel")
        if asic2_power_enable[0][0] > 0:
            asic2_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_0AE[0], register_0AE[1]]
            for msb, lsb in asic2_power_enable:
                asic2_command.append(msb)
                asic2_command.append(lsb)
            asic2_command.append(0x0D)
            col_power_enable2 = asic2_command
        else:
            # Column Power Enable, for ASIC2 (Reg 0xAE)
            col_power_enable2 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                                 register_0AE[0], register_0AE[1], value_0AE[0], value_0AE[1],
                                 value_0AE[2], value_0AE[3], value_0AE[4], value_0AE[5],
                                 value_0AE[6], value_0AE[7], value_0AE[8], value_0AE[9],
                                 value_0AE[10], value_0AE[11], value_0AE[12], value_0AE[13],
                                 value_0AE[14], value_0AE[15], value_0AE[16], value_0AE[17],
                                 value_0AE[18], value_0AE[19], 0x0D]

        # Column Calibration Enable

        register_057 = [0x35, 0x37]   # Column Calibrate Enable ASIC1 (Reg 0x57)
        register_0B8 = [0x42, 0x38]   # Column Calibrate Enable ASIC2 (Reg 0xB8)
        value_057 = list_of_30s
        value_0B8 = list_of_30s

        asic1_cal_enable = self._extract_80_bits(self.hexitec_parameters, "ColumnCal",
                                                 vsr, 1, "Channel")
        if asic1_cal_enable[0][0] > 0:
            asic1_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_057[0], register_057[1]]
            for msb, lsb in asic1_cal_enable:
                asic1_command.append(msb)
                asic1_command.append(lsb)
            asic1_command.append(0x0D)
            col_cal_enable1 = asic1_command
        else:
            # Column Calibrate Enable, for ASIC1 (Reg 0x57)
            col_cal_enable1 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                               register_057[0], register_057[1], value_057[0], value_057[1],
                               value_057[2], value_057[3], value_057[4], value_057[5],
                               value_057[6], value_057[7], value_057[8], value_057[9],
                               value_057[10], value_057[11], value_057[12], value_057[13],
                               value_057[14], value_057[15], value_057[16], value_057[17],
                               value_057[18], value_057[19], 0x0D]

        asic2_cal_enable = self._extract_80_bits(self.hexitec_parameters, "ColumnCal",
                                                 vsr, 2, "Channel")
        if asic2_cal_enable[0][0] > 0:
            asic2_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_0B8[0], register_0B8[1]]
            for msb, lsb in asic2_cal_enable:
                asic2_command.append(msb)
                asic2_command.append(lsb)
            asic2_command.append(0x0D)
            col_cal_enable2 = asic2_command
        else:
            # Column Calibrate Enable, for ASIC2 (Reg 0xB8)
            col_cal_enable2 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                               register_0B8[0], register_0B8[1], value_0B8[0], value_0B8[1],
                               value_0B8[2], value_0B8[3], value_0B8[4], value_0B8[5],
                               value_0B8[6], value_0B8[7], value_0B8[8], value_0B8[9],
                               value_0B8[10], value_0B8[11], value_0B8[12], value_0B8[13],
                               value_0B8[14], value_0B8[15], value_0B8[16], value_0B8[17],
                               value_0B8[18], value_0B8[19], 0x0D]

        # Row Read Enable

        register_043 = [0x34, 0x33]   # Row Read Enable ASIC1
        register_0A4 = [0x41, 0x34]   # Row Read Enable ASIC2
        value_043 = list_of_46s
        value_0A4 = list_of_46s

        asic1_cal_enable = self._extract_80_bits(self.hexitec_parameters, "RowEn_",
                                                 vsr, 1, "Block")
        if asic1_cal_enable[0][0] > 0:
            asic1_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_043[0], register_043[1]]
            for msb, lsb in asic1_cal_enable:
                asic1_command.append(msb)
                asic1_command.append(lsb)
            asic1_command.append(0x0D)
            row_read_enable1 = asic1_command
        else:
            # Row Read Enable, for ASIC1 (Reg 0x43)
            row_read_enable1 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                                register_043[0], register_043[1], value_043[0], value_043[1],
                                value_043[2], value_043[3], value_043[4], value_043[5],
                                value_043[6], value_043[7], value_043[8], value_043[9],
                                value_043[10], value_043[11], value_043[12], value_043[13],
                                value_043[14], value_043[15], value_043[16], value_043[17],
                                value_043[18], value_043[19], 0x0D]

        asic2_cal_enable = self._extract_80_bits(self.hexitec_parameters, "RowEn_", vsr, 2, "Block")
        if asic2_cal_enable[0][0] > 0:
            asic2_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_0A4[0], register_0A4[1]]
            for msb, lsb in asic2_cal_enable:
                asic2_command.append(msb)
                asic2_command.append(lsb)
            asic2_command.append(0x0D)
            row_read_enable2 = asic2_command
        else:
            # Row Read Enable, for ASIC2 (Reg 0xA4)
            row_read_enable2 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                                register_0A4[0], register_0A4[1], value_0A4[0], value_0A4[1],
                                value_0A4[2], value_0A4[3], value_0A4[4], value_0A4[5],
                                value_0A4[6], value_0A4[7], value_0A4[8], value_0A4[9],
                                value_0A4[10], value_0A4[11], value_0A4[12], value_0A4[13],
                                value_0A4[14], value_0A4[15], value_0A4[16], value_0A4[17],
                                value_0A4[18], value_0A4[19], 0x0D]

        # Row Power Enable

        register_02F = [0x32, 0x46]   # Row Power Enable ASIC1 (Reg 0x2F)
        register_090 = [0x39, 0x30]   # Row Power Enable ASIC2 (Reg 0x90)
        value_02F = list_of_46s
        value_090 = list_of_46s

        asic1_pwr_enable = self._extract_80_bits(self.hexitec_parameters, "RowPwr", vsr, 1, "Block")
        if asic1_pwr_enable[0][0] > 0:
            asic1_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_02F[0], register_02F[1]]
            for msb, lsb in asic1_pwr_enable:
                asic1_command.append(msb)
                asic1_command.append(lsb)
            asic1_command.append(0x0D)
            row_power_enable1 = asic1_command
        else:
            # Row Power Enable, for ASIC1 (Reg 0x2F)
            row_power_enable1 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                                 register_02F[0], register_02F[1], value_02F[0], value_02F[1],
                                 value_02F[2], value_02F[3], value_02F[4], value_02F[5],
                                 value_02F[6], value_02F[7], value_02F[8], value_02F[9],
                                 value_02F[10], value_02F[1], value_02F[2], value_02F[3],
                                 value_02F[14], value_02F[15], value_02F[16], value_02F[17],
                                 value_02F[18], value_02F[19], 0x0D]

        asic2_pwr_enable = self._extract_80_bits(self.hexitec_parameters, "RowPwr", vsr, 2, "Block")
        if asic2_pwr_enable[0][0] > 0:
            asic2_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_090[0], register_090[1]]
            for msb, lsb in asic2_pwr_enable:
                asic2_command.append(msb)
                asic2_command.append(lsb)
            asic2_command.append(0x0D)
            row_power_enable2 = asic2_command
        else:
            # Row Power Enable, for ASIC2 (Reg 0x90)
            row_power_enable2 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                                 register_090[0], register_090[1], value_090[0], value_090[1],
                                 value_090[2], value_090[3], value_090[4], value_090[5],
                                 value_090[6], value_090[7], value_090[8], value_090[9],
                                 value_090[10], value_090[11], value_090[12], value_090[13],
                                 value_090[14], value_090[15], value_090[16], value_090[17],
                                 value_090[18], value_090[19], 0x0D]

        # Row Calibration Enable

        register_039 = [0x33, 0x39]   # Row Calibrate Enable ASIC1 (Reg 0x39)
        register_09A = [0x39, 0x41]   # Row Calibrate Enable ASIC2 (Reg 0x9A)
        value_039 = list_of_30s
        value_09A = list_of_30s

        asic1_cal_enable = self._extract_80_bits(self.hexitec_parameters, "RowCal", vsr, 1, "Block")
        if asic1_cal_enable[0][0] > 0:
            asic1_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_039[0], register_039[1]]
            for msb, lsb in asic1_cal_enable:
                asic1_command.append(msb)
                asic1_command.append(lsb)
            asic1_command.append(0x0D)
            row_cal_enable1 = asic1_command
        else:
            # Row Calibrate Enable, for ASIC1 (Reg 0x39)
            row_cal_enable1 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                               register_039[0], register_039[1], value_039[0], value_039[1],
                               value_039[2], value_039[3], value_039[4], value_039[5],
                               value_039[6], value_039[7], value_039[8], value_039[9],
                               value_039[10], value_039[11], value_039[12], value_039[13],
                               value_039[14], value_039[15], value_039[16], value_039[17],
                               value_039[18], value_039[19], 0x0D]

        asic2_cal_enable = self._extract_80_bits(self.hexitec_parameters, "RowCal", vsr, 2, "Block")
        if asic2_cal_enable[0][0] > 0:
            asic2_command = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_09A[0], register_09A[1]]
            for msb, lsb in asic2_cal_enable:
                asic2_command.append(msb)
                asic2_command.append(lsb)
            asic2_command.append(0x0D)
            row_cal_enable2 = asic2_command
        else:
            # Row Calibrate Enable, for ASIC2 (Reg 0x9A)
            row_cal_enable2 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_BURST,
                               register_09A[0], register_09A[1], value_09A[0], value_09A[1],
                               value_09A[2], value_09A[3], value_09A[4], value_09A[5],
                               value_09A[6], value_09A[7], value_09A[8], value_09A[9],
                               value_09A[10], value_09A[11], value_09A[12], value_09A[13],
                               value_09A[14], value_09A[15], value_09A[16], value_09A[17],
                               value_09A[18], value_09A[19], 0x0D]

        self.send_cmd(disable_sm)
        self.read_response()

        logging.debug("Loading Power, Cal and Read Enables")
        logging.debug("Column power enable")
        self.send_cmd(col_power_enable1)    # 0x4D
        self.read_response()
        self.send_cmd(col_power_enable2)
        self.read_response()

        logging.debug("Row power enable")
        self.send_cmd(row_power_enable1)    # 0x2F
        self.read_response()

        self.send_cmd(row_power_enable2)
        self.read_response()

        # Default selection
        logging.debug("Column cal enable D")
        self.send_cmd(col_cal_enable1)      # 0x57
        self.read_response()
        self.send_cmd(col_cal_enable2)
        self.read_response()
        logging.debug("Row cal enable D")
        self.send_cmd(row_cal_enable1)      # 0x39
        self.read_response()
        self.send_cmd(row_cal_enable2)
        self.read_response()

        logging.debug("Column read enable")
        self.send_cmd(col_read_enable1)     # 0x61
        self.read_response()
        self.send_cmd(col_read_enable2)
        self.read_response()

        logging.debug("Row read enable")
        self.send_cmd(row_read_enable1)     # 0x43
        self.read_response()
        self.send_cmd(row_read_enable2)
        self.read_response()

        logging.debug("Power, Cal and Read Enables have been loaded")

        self.send_cmd(enable_sm)
        self.read_response()

    def write_dac_values(self):
        """Write values to DAC, optionally provided by hexitec file."""
        logging.debug("Writing DAC values")
        vcal = [0x30, 0x32, 0x41, 0x41]
        umid = [0x30, 0x35, 0x35, 0x35]
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

        self.send_cmd([0x23, self.vsr_addr, HexitecFem.WRITE_DAC_VAL,
                       vcal[0], vcal[1], vcal[2], vcal[3],      # Vcal, e.g. 0x0111 =: 0.2V
                       umid[0], umid[1], umid[2], umid[3],      # Umid, e.g. 0x0555 =: 1.0V
                       hv[0], hv[1], hv[2], hv[3],              # reserve1, 0x0555 =: 1V (HV ~-250V)
                       dctrl[0], dctrl[1], dctrl[2], dctrl[3],  # DET ctrl, 0x000
                       rsrv2[0], rsrv2[1], rsrv2[2], rsrv2[3],  # reserve2, 0x08E8 =: 1.67V
                       0x0D])
        self.read_response()
        logging.debug("DAC values set")

    def make_list_hexadecimal(self, value):  # pragma: no cover
        """Debug function: Turn decimal list into hexadecimal list."""
        value_hexadecimal = []
        for val in value:
            value_hexadecimal.append("0x%x" % val)
        return value_hexadecimal

    def enable_adc(self):
        """Enable the ADCs."""
        logging.debug("Enabling ADC")
        adc_disable = [0x23, self.vsr_addr, HexitecFem.CTRL_ADC_DAC, 0x30, 0x32, 0x0D]
        enable_sm = [0x23, self.vsr_addr, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]
        adc_enable = [0x23, self.vsr_addr, HexitecFem.CTRL_ADC_DAC, 0x30, 0x33, 0x0D]
        adc_set = [0x23, self.vsr_addr, HexitecFem.WRITE_REG_VAL, 0x31, 0x36, 0x30, 0x39, 0x0D]
        # Send reg value; Register 0x24, bits5,1: disable VCAL, capture average picture:
        aqu1 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_VALUE, 0x32, 0x34, 0x32, 0x32, 0x0D]
        # Send reg value; Register 0x24, bits5,3: disable VCAL, enable spectroscopic mode:
        aqu2 = [0x23, self.vsr_addr, HexitecFem.SEND_REG_VALUE, 0x32, 0x34, 0x32, 0x38, 0x0D]

        self.send_cmd(adc_disable)
        self.read_response()
        logging.debug("Enable SM")
        self.send_cmd(enable_sm)
        self.read_response()
        self.send_cmd(adc_enable)
        self.read_response()

        self.send_cmd(adc_set)
        self.read_response()
        self.send_cmd(aqu1)
        self.read_response()
        if self.debug_register24:  # pragma: no cover
            (vsr2, vsr1) = self.debug_reg24()
            print("\n")
            logging.debug("  * 13 *** ena_adc,  SET b1,5;  Reg 0x24: %s, %s ***" % (vsr2, vsr1))
        self.send_cmd(aqu2)
        self.read_response()
        if self.debug_register24:  # pragma: no cover
            (vsr2, vsr1) = self.debug_reg24()
            print("\n")
            logging.debug("  * 14 *** ena_adc,  SET b3,5;  Reg 0x24: %s, %s ***" % (vsr2, vsr1))

        # Disable ADC test testmode
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.WRITE_REG_VAL, 0x30, 0x44, 0x30, 0x30, 0x0d])
        self.read_response()

    def initialise_system(self):
        """Configure in full VSR2, then VSR1.

        Initialise, load enables, set up state machine, write to DAC and enable ADCs.
        """
        enable_sm_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.SET_REG_BIT,
                          0x30, 0x31, 0x30, 0x31, 0x0D]
        enable_sm_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.SET_REG_BIT,
                          0x30, 0x31, 0x30, 0x31, 0x0D]
        disable_sm_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.CLR_REG_BIT,
                           0x30, 0x31, 0x30, 0x30, 0x0D]
        disable_sm_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.CLR_REG_BIT,
                           0x30, 0x31, 0x30, 0x30, 0x0D]

        # Note current setting, change Register 143 (0x8F) -> 1, confirm changed
        self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.READ_REG_VALUE,
                       0x38, 0x46, 0x0D])
        self.read_response()
        self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.SET_REG_BIT,
                       0x38, 0x46, 0x30, 0x31, 0x0D])
        self.read_response()

        # Repeat with other VSR board
        self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.READ_REG_VALUE,
                       0x38, 0x46, 0x0D])
        self.read_response()
        self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.SET_REG_BIT,
                       0x38, 0x46, 0x30, 0x31, 0x0D])
        self.read_response()

        # Stop the state machine

        self.send_cmd(disable_sm_vsr1)
        self.read_response()
        self.send_cmd(disable_sm_vsr2)
        self.read_response()

        # Re-Start the state machine

        self.send_cmd(enable_sm_vsr1)
        self.read_response()
        self.send_cmd(enable_sm_vsr2)
        self.read_response()

        ###

        self._set_status_message("Configuring VSR2")
        self.selected_sensor = HexitecFem.OPTIONS[2]

        self.initialise_sensor()
        self._set_status_message("VSR2: Sensors initialised.")

        self.set_up_state_machine()
        self._set_status_message("VSR2: State Machine setup")

        self.write_dac_values()
        self._set_status_message("VSR2: DAC values written")

        self.enable_adc()
        self._set_status_message("VSR2: ADC enabled")

        self.load_pwr_cal_read_enables()
        self._set_status_message("VSR2: Loaded Power, Calibrate, Read Enables")

        synced_status = self.calibrate_sensor()
        logging.debug("Calibrated sensor returned synchronised status: %s" % synced_status)

        self._set_status_message("Configuring VSR1")
        self.selected_sensor = HexitecFem.OPTIONS[0]

        self.initialise_sensor()
        self._set_status_message("VSR1: Sensors initialised")

        self.set_up_state_machine()
        self._set_status_message("VSR1: State Machine setup")

        self.write_dac_values()
        self._set_status_message("VSR1: DAC values written")

        self.enable_adc()
        self._set_status_message("VSR1: ADC enabled")

        self.load_pwr_cal_read_enables()
        self._set_status_message("VSR1: Loaded Power, Calibrate, Read Enables")

        synced_status = self.calibrate_sensor()
        logging.debug("Calibrated sensor returned synchronised status: %s" % synced_status)

        self._set_status_message("Initialisation completed. VSR2 and VS1 configured.")
        print(" -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=-  -=-=-=- ")

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
            # With duration enabled, recalculate number of frames in case clocks changed
            self.set_duration(self.duration)
            self.parent.set_number_frames(self.number_frames)

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

        print("\t\tRow Pwr Ena ASIC1:  %s \t\tRow Cal Ena ASIC1: %s \t\tRow Rd Ena ASIC1: %s"
              % (row_power_enable1, row_cal_enable1, row_read_enable1))

        # COLUMN, ASIC 1

        cpe1 = [0x4d, 0x56]
        col_power_enable1 = self.read_back_register(vsr_addr, cpe1)
        cce1 = [0x57, 0x60]
        col_cal_enable1 = self.read_back_register(vsr_addr, cce1)
        cre1 = [0x61, 0x6a]
        col_read_enable1 = self.read_back_register(vsr_addr, cre1)

        print("\t\tCol Pwr Ena ASIC1: %s \t\tCol Cal Ena ASIC1: %s \t\tCol Rd Ena ASIC1: %s"
              % (col_power_enable1, col_cal_enable1, col_read_enable1))

        print("---------------------------------------------------------------------------------")
        # ROW, ASIC 2

        rpe2 = [0x90, 0x99]
        row_power_enable2 = self.read_back_register(vsr_addr, rpe2)
        rce2 = [0x9A, 0xA3]
        row_cal_enable2 = self.read_back_register(vsr_addr, rce2)
        rre2 = [0xA4, 0xAD]
        row_read_enable2 = self.read_back_register(vsr_addr, rre2)

        print("\t\tRow Pwr Ena ASIC2: %s \t\tRow Cal Ena ASIC2:  %s \t\tRow Rd Ena ASIC2: %s"
              % (row_power_enable2, row_cal_enable2, row_read_enable2))

        # COLUMN, ASIC 2

        cpe2 = [0xAE, 0xB7]
        col_power_enable2 = self.read_back_register(vsr_addr, cpe2)
        cce2 = [0xB8, 0xC1]
        col_cal_enable2 = self.read_back_register(vsr_addr, cce2)
        cre2 = [0xC2, 0xCB]
        col_read_enable2 = self.read_back_register(vsr_addr, cre2)

        print("\t\tCol Pwr Ena ASIC2: %s \t\tCol Cal Ena ASIC2: %s \t\tCol Rd Ena ASIC2: %s"
              % (col_power_enable2, col_cal_enable2, col_read_enable2))

        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")

    def read_back_register(self, vsr_addr, boundaries):  # pragma: no cover
        """Debug function: Actual hardware interaction with VCAL registers."""
        register_reply = []
        for idx in range(boundaries[0], boundaries[1] + 1, 1):
            formatted_address = self.convert_to_aspect_format(idx)
            command = [0x23, vsr_addr, HexitecFem.READ_REG_VALUE,
                       formatted_address[0], formatted_address[1], 0x0D]
            self.send_cmd(command)
            # A typical reply: "\x90FF\r\r\r\r"
            # After strip() -> "\x90FF"
            # After [1:]    -> "FF"
            # register_reply.append(self.read_response().strip()[1:])
            register_reply.append(self.read_response().strip())
        return register_reply

    def read_pwr_voltages(self):
        """Read and convert power data into voltages."""
        self.send_cmd([0x23, self.vsr_addr, HexitecFem.READ_PWR_VOLT, 0x0D], False)
        sensors_values = self.read_response()
        sensors_values = sensors_values.strip()

        if self.debug:
            logging.debug("VSR: %s Power values: %s len: %s" % (format(self.vsr_addr, '#02x'),
                          sensors_values, len(sensors_values)))

        if (self.vsr_addr == HexitecFem.VSR_ADDRESS[0]):
            self.vsr1_hv = self.get_hv_value(sensors_values)
        else:
            if (self.vsr_addr == HexitecFem.VSR_ADDRESS[1]):
                self.vsr2_hv = self.get_hv_value(sensors_values)

    def get_hv_value(self, sensors_values):
        """Take the full string of voltages and extract the HV value."""
        try:
            # Calculate V10, the 3.3V reference voltage
            reference_voltage = int(sensors_values[37:41], 16) * (2.048 / 4095)
            # Calculate HV rails
            u1 = int(sensors_values[1:5], 16) * (reference_voltage / 2**12)
            # Apply conversion gain # Added 56V following HV tests
            hv_monitoring_voltage = u1 * 1621.65 - 1043.22 + 56
            return hv_monitoring_voltage
        except ValueError as e:
            logging.error("VSR %s: Error obtaining HV value: %s" %
                          (format(self.vsr_addr, '#02x'), e))
            return -1

    def read_temperatures_humidity_values(self):
        """Read and convert sensor data into temperatures and humidity values."""
        self.send_cmd([0x23, self.vsr_addr, 0x52, 0x0D], False)
        sensors_values = self.read_response()
        sensors_values = sensors_values.strip()
        if self.debug:
            logging.debug("VSR: %s sensors_values: %s len: %s" % (format(self.vsr_addr, '#02x'),
                          sensors_values, len(sensors_values)))

        # Check register value is OK, otherwise sensor values weren't read out
        initial_value = -1
        try:
            initial_value = int(sensors_values[1])
        except ValueError as e:
            logging.error("Failed to readout intelligible sensor values: %s" % e)
            return

        if initial_value == HexitecFem.SENSORS_READOUT_OK:
            ambient_hex = sensors_values[1:5]
            humidity_hex = sensors_values[5:9]
            asic1_hex = sensors_values[9:13]
            asic2_hex = sensors_values[13:17]
            adc_hex = sensors_values[17:21]

            if (self.vsr_addr == HexitecFem.VSR_ADDRESS[0]):
                self.vsr1_ambient = self.get_ambient_temperature(ambient_hex)
                self.vsr1_humidity = self.get_humidity(humidity_hex)
                self.vsr1_asic1 = self.get_asic_temperature(asic1_hex)
                self.vsr1_asic2 = self.get_asic_temperature(asic2_hex)
                self.vsr1_adc = self.get_adc_temperature(adc_hex)
            else:
                if (self.vsr_addr == HexitecFem.VSR_ADDRESS[1]):
                    self.vsr2_ambient = self.get_ambient_temperature(ambient_hex)
                    self.vsr2_humidity = self.get_humidity(humidity_hex)
                    self.vsr2_asic1 = self.get_asic_temperature(asic1_hex)
                    self.vsr2_asic2 = self.get_asic_temperature(asic2_hex)
                    self.vsr2_adc = self.get_adc_temperature(adc_hex)
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
            logging.debug("hexitec_config: '%s' Filename: '%s'" % (self.hexitec_config, filename))
        except IOError as e:
            logging.error("Cannot open provided hexitec file: %s" % e)
            raise ParameterTreeError("Error: %s" % e)

        self.read_ini_file(self.hexitec_config, self.hexitec_parameters, debug=False)

        bias_refresh_interval = self._extract_integer(self.hexitec_parameters,
                                                      'Bias_Voltage/Bias_Refresh_Interval',
                                                      bit_range=32)
        if bias_refresh_interval > -1:
            self.bias_refresh_interval = bias_refresh_interval / 1000.0

        bias_voltage_refresh = self._extract_boolean(self.hexitec_parameters,
                                                     'Bias_Voltage/Bias_Voltage_Refresh')
        if bias_voltage_refresh > -1:
            self.bias_voltage_refresh = bias_voltage_refresh

        time_refresh_voltage_held = self._extract_integer(self.hexitec_parameters,
                                                          'Bias_Voltage/Time_Refresh_Voltage_Held',
                                                          bit_range=32)
        if time_refresh_voltage_held > -1:
            self.time_refresh_voltage_held = time_refresh_voltage_held / 1000.0

        bias_voltage_settle_time = self._extract_integer(self.hexitec_parameters,
                                                         'Bias_Voltage/Bias_Voltage_Settle_Time',
                                                         bit_range=32)
        if bias_voltage_settle_time > -1:
            self.time_refresh_voltage_held = time_refresh_voltage_held / 1000.0
            self.bias_voltage_settle_time = bias_voltage_settle_time / 1000.0

        # Recalculate frame rate
        self.row_s1 = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Row -> S1',
                                            bit_range=14)
        self.s1_sph = self._extract_integer(self.hexitec_parameters, 'Control-Settings/S1 -> Sph',
                                            bit_range=6)
        self.sph_s2 = self._extract_integer(self.hexitec_parameters, 'Control-Settings/Sph -> S2',
                                            bit_range=6)
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

    def _extract_80_bits(self, parameter_dict, param, vsr, asic, channel_or_block):  # noqa: C901
        """Extract 80 bits from four (20 bit) channels, assembling one ASIC's row/column."""
        # key = "ColumnEn_"
        # vsr = 1
        # asic = 1
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
            first_channel = self.extract_channel_data(parameter_dict, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return aspect_list

        key = 'Sensor-Config_V%s_S%s/%s2nd%s' % (vsr, asic, param, channel_or_block)
        try:
            second_channel = self.extract_channel_data(parameter_dict, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return aspect_list

        key = 'Sensor-Config_V%s_S%s/%s3rd%s' % (vsr, asic, param, channel_or_block)
        try:
            third_channel = self.extract_channel_data(parameter_dict, key)
        except KeyError:
            logging.debug("WARNING: Missing key %s - was .ini file loaded?" % key)
            return aspect_list

        key = 'Sensor-Config_V%s_S%s/%s4th%s' % (vsr, asic, param, channel_or_block)
        try:
            fourth_channel = self.extract_channel_data(parameter_dict, key)
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
                print('Section:', section)
            for key, value in parser.items(section):
                parameter_dict[section + "/" + key] = value.strip("\"")
                if debug:  # pragma: no cover
                    print("   " + section + "/" + key + " => " + value.strip("\""))
        if debug:  # pragma: no cover
            print("---------------------------------------------------------------------")


class HexitecFemError(Exception):
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass
