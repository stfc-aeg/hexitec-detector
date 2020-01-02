#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri July 05 15:00:14 2019

@author: ckd27546
"""


import time
import datetime
import logging
import configparser
#
import threading

from hexitec.RdmaUDP import RdmaUDP

from concurrent import futures
from socket import error as socket_error
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor
from tornado.escape import json_decode

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

    TESTMODEIMAGE = [
        0,
        1,
        2,
        3
    ]

    DARKCORRECTION = [
        0,
        1
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

    HEX_ASCII_CODE = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46]

    # VSR, DAC Documentation: 
    #   VCAL: 0x0111 =: 0.2 V. I.e. 273 = 0.2 or 273/0.2 = 1365
    #   UMID: 0x0555 =: 1.0 V. i.e. 1365 = 1.0
    DAC_SCALE_FACTOR = 1365

    CHANNEL_1_OFFSET = 0
    CHANNEL_2_OFFSET = 5
    CHANNEL_3_OFFSET = 10
    CHANNEL_4_OFFSET = 15

    def __init__(self, parent, ip_address='127.0.0.1', port=1232, fem_id=1,
                server_ctrl_ip_addr='10.0.2.2', camera_ctrl_ip_addr='10.0.2.1',
                server_data_ip_addr='10.0.4.2', camera_data_ip_addr='10.0.4.1',
                callback_function=None):
        # Give access to parent class (Hexitec) - for potential future use
        self.parent = parent
        self.ip_address = ip_address
        self.port = port
        self.id = int(fem_id)
        self.x10g_rdma = None

        self.callback_function = callback_function

        # 10G RDMA IP addresses
        self.server_ctrl_ip_addr = server_ctrl_ip_addr    #'10.0.2.2'
        self.camera_ctrl_ip_addr = camera_ctrl_ip_addr    #'10.0.2.1'

        # 10G image stream Ip addresses - Not actually used anywhere...
        # self.server_data_ip_addr = server_data_ip_addr    #"10.0.4.2"
        # self.camera_data_ip_addr = camera_data_ip_addr    #"10.0.4.1"

        # FPGA base addresses
        self.rdma_addr = {
            "receiver":        0xC0000000,
            "frm_gate":        0xD0000000
        }

        self.image_size_x    = 0x100
        self.image_size_y    = 0x100
        self.image_size_p    = 0x8
        self.image_size_f    = 0x8
        
        self.strm_mtu = 8000

        self.vsr_addr = HexitecFem.VSR_ADDRESS[0]

        self.number_of_frames = 10

        self.hardware_connected = False
        self.hardware_busy = False

        self.health = True

        # Acquisition completed, note completion
        self.acquisition_completed = False
        self.acquisition_timestamp = 0.0

        self.debug = False
        # Diagnostics:
        self.exception_triggered = False
        self.successful_reads = 0

        self.status_message = ""
        self.status_error = ""
        self.stop_acquisition = False
        # 
        self.initialise_progress = 0                            # Used by initialise_system()
        self.operation_percentage_complete = 0
        self.operation_percentage_steps = 108

        self.selected_sensor    = HexitecFem.OPTIONS[2]         # "Sensor_2_1"
        self.sensors_layout     = HexitecFem.READOUTMODE[1]     # "2x2"
        self.dark_correction    = HexitecFem.DARKCORRECTION[0]  # "DARK CORRECTION OFF" = 0
        self.test_mode_image    = HexitecFem.TESTMODEIMAGE[3]   # "IMAGE 4" [3]=without vcal, [0]=vcal on, needed for DC..?

        self.vsr1_ambient    = 0
        self.vsr1_humidity   = 0
        self.vsr1_asic1      = 0
        self.vsr1_asic2      = 0
        self.vsr1_adc        = 0

        self.vsr2_ambient    = 0
        self.vsr2_humidity   = 0
        self.vsr2_asic1      = 0
        self.vsr2_asic2      = 0
        self.vsr2_adc        = 0

        # Variables supporting handling of ini-style aspect config file
        self.aspect_config  = "(Blank)"
        self.aspect_parameters = {}

        param_tree_dict = {
            "diagnostics": {
                "successful_reads": (lambda: self.successful_reads, None),
                "config_sequence": (None, self.config_sequence),
            },
            "ip_addr": (self.get_address, None),    # Replicated, not needed going forwards?
            "port": (self.get_port, None),          # Replicated, not needed going forwards?
            "id": (lambda: self.id, None),
            "debug": (self.get_debug, self.set_debug),
            "health": (lambda: self.health, None),
            "status_message": (self._get_status_message, None),
            "status_error": (self._get_status_error, None),
            "initialise_progress": (self._get_initialise_progress, None),
            "operation_percentage_complete": (self._get_operation_percentage_complete, None),
            "dark_correction": (self._get_dark_correction, self._set_dark_correction),
            "number_frames": (self._get_number_frames, self._set_number_frames),
            "aspect_config": (lambda: self.aspect_config, self._set_aspect_config),
            "read_sensors": (None, self.read_sensors),
            "vsr1_sensors": {
                "ambient": (lambda: self.vsr1_ambient, None),
                "humidity": (lambda: self.vsr1_humidity, None),
                "asic1": (lambda: self.vsr1_asic1, None),
                "asic2": (lambda: self.vsr1_asic2, None),
                "adc": (lambda: self.vsr1_adc, None),
            },
            "vsr2_sensors": {
                "ambient": (lambda: self.vsr2_ambient, None),
                "humidity": (lambda: self.vsr2_humidity, None),
                "asic1": (lambda: self.vsr2_asic1, None),
                "asic2": (lambda: self.vsr2_asic2, None),
                "adc": (lambda: self.vsr2_adc, None),
            }
        }

        self.param_tree = ParameterTree(param_tree_dict)

    def config_sequence(self, cmd):

        print("You send me this: '%s' which is '%s'" % (cmd, type(cmd)))
        print("Hardcoded expression: '%s'" % [0x23, HexitecFem.VSR_ADDRESS[0], 0xE3, 0x0D])
        # Convert str to list of ints:
        cmd = self.convert_cmd_to_list(cmd)
        
        print("What we cooked up:")
        print([0x23, HexitecFem.VSR_ADDRESS[0], cmd, 0x0D])
        # try:
        print("1st..")
        self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], cmd, 0x0D])
        print("2nd..")
        self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], cmd, 0x0D])
        # except Exception as e:
        #     print("BANG, exception! b/c: %s" % e)

    def convert_cmd_to_list(self, cmd):
        no_whites = cmd.replace(" ", "")
        tokenised = no_whites.split(",")
        value_list = []
        for idx in tokenised:
            value_list.append(int(idx, 16))
        return value_list

    def __del__(self):
        if self.x10g_rdma is not None:
            self.x10g_rdma.close()

    def connect(self, bDebug=False):
        try:
            self.x10g_rdma = RdmaUDP(self.server_ctrl_ip_addr, 61650, self.server_ctrl_ip_addr, 61651,
                                    self.camera_ctrl_ip_addr, 61650, self.camera_ctrl_ip_addr, 61651, 2000000, 9000, 20)
            self.x10g_rdma.setDebug(False)
            self.x10g_rdma.ack = True
        except socket_error as e:
            raise socket_error("Failed to setup Control connection: %s" % e)

        return

    def read_sensors(self, msg=None):
        try:
            vsr = self.vsr_addr
            self.vsr_addr = HexitecFem.VSR_ADDRESS[0]
            self.read_temperatures_humidity_values()
            self.vsr_addr = HexitecFem.VSR_ADDRESS[1]
            self.read_temperatures_humidity_values()
            self.vsr_addr = vsr
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Failed to read sensors: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Reading sensors failed: %s" % str(e))
            logging.error("%s" % str(e))

    def disconnect(self):
        # should be called on shutdown to close sockets
        self.x10g_rdma.close()

    def cleanup(self):
        self.disconnect()

    def set_image_size(self, x_size, y_size, p_size, f_size):
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
        first_packets = number_bytes//self.strm_mtu
        last_packet_size = number_bytes % self.strm_mtu
        lp_number_bytes_r8 = last_packet_size % 8
        lp_number_bytes_r32 = last_packet_size % 32
        size_status = number_bytes_r4 + number_bytes_r8 + lp_number_bytes_r8 + lp_number_bytes_r32
        # calculate pixel packing settings
        if p_size >= 11 and p_size <= 14 and f_size == 16:
            # pixel_extract = self.pixel_extract.index(p_size)
            pixel_count_max = pixel_count_max//2
        elif p_size == 8 and f_size == 8:
            # pixel_extract = self.pixel_extract.index(p_size*2)
            pixel_count_max = pixel_count_max//4
        else:
            size_status =size_status + 1
            
        # set up registers if no size errors     
        if size_status != 0:
            print("%-32s %8i %8i %8i %8i %8i %8i" % ('-> size error', number_bytes, number_bytes_r4, number_bytes_r8, first_packets, lp_number_bytes_r8, lp_number_bytes_r32 ))
        else:   
            address = self.rdma_addr["receiver"] | 0x01
            data = (pixel_count_max & 0x1FFFF) -1
            self.x10g_rdma.write(address, data, 'pixel count max')
            self.x10g_rdma.write(self.rdma_addr["receiver"]+4, 0x3, 'pixel bit size => 16 bit')
            
        return
    
    def frame_gate_trigger(self):
        self.x10g_rdma.write(self.rdma_addr["frm_gate"]+0,0x0,          'frame gate trigger off')
        self.x10g_rdma.write(self.rdma_addr["frm_gate"]+0,0x1,          'frame gate trigger on')
        self.x10g_rdma.write(self.rdma_addr["frm_gate"]+0,0x0,          'frame gate trigger off')
        return
        
    def frame_gate_settings(self, frame_number, frame_gap):
        self.x10g_rdma.write(self.rdma_addr["frm_gate"]+1,frame_number, 'frame gate frame number')
        self.x10g_rdma.write(self.rdma_addr["frm_gate"]+2,frame_gap,    'frame gate frame gap')
        return

    # Utilised to trigger data output by HexitecFem
    def data_stream(self, num_images):
        self.frame_gate_settings(num_images-1, 0)
        self.frame_gate_trigger()
        return

    ''' Accessor functions '''

    def _get_operation_percentage_complete(self):
        return self.operation_percentage_complete

    def _get_initialise_progress(self):
        return self.initialise_progress

    def get_address(self):
        return self.ip_address

    def get_port(self):
        return self.port

    def _get_status_message(self):
        return self.status_message

    def _set_status_message(self, message):
        self.status_message = message

    def _get_status_error(self):
        return self.status_error

    def _set_status_error(self, error):
        self.health = True if error == "" else False
        self.status_error = str(error)

    def _set_stop_acquisition(self, stop):
        self.stop_acquisition = stop

    def _get_dark_correction(self):
        return self.dark_correction

    def _set_dark_correction(self, correction):
        self.dark_correction = correction

    def _get_number_frames(self):
        return self.number_of_frames
    
    def _set_number_frames(self, frames):
        self.number_of_frames = frames

    def _set_test_mode_image(self, image):
        self.test_mode_image = image

    def _get_test_mode_image(self):
        return self.test_mode_image

    def get_health(self):
        return self.health

    def get_id(self):
        return self.id

    # @run_on_executor(executor='thread_executor')
    def start_polling(self):
        IOLoop.instance().add_callback(self.poll_sensors)

    def poll_sensors(self):
        # Poll hardware while connected and not busy initialising, 
        #     collecting offsets et cetera
        if self.hardware_connected and (self.hardware_busy == False):
            self.read_sensors()
        IOLoop.instance().call_later(1.0, self.poll_sensors)

    # @run_on_executor(executor='thread_executor')
    def connect_hardware(self, msg=None):
        try:
            if self.hardware_connected:
                raise ParameterTreeError("Connection already established")
            else:
                self._set_status_error("")
            self.operation_percentage_complete = 0
            self._set_status_message("Connecting to camera..")
            self.cam_connect()
            self._set_status_message("Camera connected. Waiting for sensors to initialise..")
            self._wait_while_sensors_initialise()
            self._set_status_message("Camera connected. Sensors initialised.")
            self.initialise_progress = 0
        except ParameterTreeError as e:
            self._set_status_error("%s" % str(e))
        except HexitecFemError as e:
            self._set_status_error("Failed to connect with camera: %s" % str(e))
            self._set_status_message("Is camera powered?")
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Failed to establish camera connection: %s" % str(e))
            logging.error("%s" % str(e))
            # Cannot raise error beyond this thread
        
        # Start polling thread
        self.start_polling()

    @run_on_executor(executor='thread_executor')
    def initialise_hardware(self, msg=None):
        try:
            if self.hardware_connected != True:
                raise ParameterTreeError("No connection established")
            if self.hardware_busy:
                raise HexitecFemError("Hardware sensors busy initialising")
            else:
                self._set_status_error("")
            self.hardware_busy = True
            self.operation_percentage_complete = 0
            self.operation_percentage_steps = 108
            self.initialise_system()
            self.initialise_progress = 0
            self.hardware_busy = False
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Failed to initialise camera: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Camera initialisation failed: %s" % str(e))
            logging.error("%s" % str(e))

    @run_on_executor(executor='thread_executor')
    def collect_data(self, msg=None):
        try:
            if self.hardware_connected != True:
                raise ParameterTreeError("No connection established")
            if self.hardware_busy:
                raise HexitecFemError("Hardware sensors busy initialising")
            else:
                self._set_status_error("")
            self.hardware_busy = True
            self.operation_percentage_complete = 0
            self.operation_percentage_steps = 108           #TODO: Amend to suit this func..!
            self._set_status_message("Acquiring data..")
            self.acquire_data()
            self.operation_percentage_complete = 100
            self.initialise_progress = 0
            # Acquisition completed, note completion
            self.acquisition_completed = True
            self.acquisition_timestamp = time.time()
            self.hardware_busy = False
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Failed to collect data: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Data collection failed: %s" % str(e))
            logging.error("%s" % str(e))

    # @run_on_executor(executor='thread_executor')
    def disconnect_hardware(self, msg=None):
        try:
            if self.hardware_connected == False:
                raise ParameterTreeError("No connection to disconnect")
            else:
                self._set_status_error("")
            # Stop acquisition if it's hung
            if self.operation_percentage_complete < 100:
                self.stop_acquisition = True
            #
            self.hardware_connected = False
            self.operation_percentage_complete = 0
            self._set_status_message("Disconnecting camera..")
            self.cam_disconnect()
            self._set_status_message("Camera disconnected")
            self.operation_percentage_complete = 100
            self.initialise_progress = 0
            # self.hardware_connected = False
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Failed to disconnect: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Disconnection failed: %s" % str(e))
            logging.error("%s" % str(e))

    def set_debug(self, debug):
        self.debug = debug

    def get_debug(self):
        return self.debug

    def _wait_while_sensors_initialise(self):
        """
        Wait 10 seconds to allow sensors in VSRs to initialise
        """
        # logging.debug("\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        # logging.debug("_wait_while..() %s" % threading.current_thread())
        self.hardware_busy = True
        self.start = time.time()
        self.delay = 10
        IOLoop.instance().call_later(1.0, self.initialisation_check_loop)

    def initialisation_check_loop(self):
        # logging.debug("\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        # logging.debug("init_check() %s" % threading.current_thread())
        if len(self.status_error) > 0:
            # Error encountered, return prematurely
            self.operation_percentage_complete = 0
            self.hardware_busy = False
            return
        self.delay = time.time() - self.start
        self.operation_percentage_complete += 10
        if (self.delay < 10):
            IOLoop.instance().call_later(1.0, self.initialisation_check_loop)
        else:
            self.hardware_busy = False

    #  This function sends a command string to the microcontroller
    def send_cmd(self, cmd, track_progress=True):

        if track_progress:
            self.initialise_progress += 1
            self.operation_percentage_complete = (self.initialise_progress * 100)  // self.operation_percentage_steps;

        while len(cmd)%4 != 0:
            cmd.append(13)
        if self.debug: logging.debug("Length of command - %s %s" % (len(cmd), len(cmd)%4))

        for i in range(0, len(cmd)//4):

            reg_value = 256*256*256*cmd[(i*4)] + 256*256*cmd[(i*4)+1] + 256*cmd[(i*4)+2] + cmd[(i*4)+3] 
            self.x10g_rdma.write(0xE0000100, reg_value, 'Write 4 Bytes')
            # time.sleep(0.25)

    # Displays the returned response from the microcontroller
    def read_response(self):
        data_counter = 0
        f = []
        ABORT_VALUE = 10000
        RETURN_START_CHR = 42
        CARRIAGE_RTN = 13
        FIFO_EMPTY_FLAG = 1
        empty_count = 0
        daty = RETURN_START_CHR
        #Example: daty will contain: 0x23, self.vsr_addr, 0x40, 0x30, 0x41, 0x30, 0x30, 0x0D

        # JE mods
        daty1 = RETURN_START_CHR
        daty2 = RETURN_START_CHR
        daty3 = RETURN_START_CHR
        daty4 = RETURN_START_CHR

        # while daty1 != CARRIAGE_RTN and daty2 != CARRIAGE_RTN and daty3 != CARRIAGE_RTN and daty4 != CARRIAGE_RTN: # NEW
        while daty != CARRIAGE_RTN :    # Old

            fifo_empty = FIFO_EMPTY_FLAG

            while fifo_empty == FIFO_EMPTY_FLAG and empty_count < ABORT_VALUE:
                fifo_empty = self.x10g_rdma.read(0xE0000011, 'FIFO EMPTY FLAG')
                empty_count = empty_count + 1

            dat = self.x10g_rdma.read(0xE0000200, 'Data')
            # if dat != 0x01:
            #     logging.debug("dat: %s" % format(dat, '02x'))

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
                logging.debug(format(daty1, '02x') + " " + format(daty2, '02x') + " " + format(daty3, '02x') + " " + format(daty4, '02x'))

            data_counter = data_counter + 1
            if empty_count == ABORT_VALUE:
                logging.error("Error: read_response from FEM aborted")
                self.exception_triggered = True
                raise HexitecFemError("read_response aborted")
            empty_count = 0

        # Diagnostics: Count number of successful reads before 1st exception thrown
        if self.exception_triggered == False:
            self.successful_reads += 1

        if self.debug: 
            logging.debug("Counter is :- %s Length is:- %s" % (data_counter, len(f)))

        fifo_empty = self.x10g_rdma.read(0xE0000011, 'Data')
        if self.debug: logging.debug("FIFO should be empty: %s" % fifo_empty)
        s = ''

        for i in range(1, data_counter*4):
            s = s + chr(f[i])

        if self.debug: 
            logging.debug("String :- %s" % s)
            logging.debug(f[0])
            logging.debug(f[1])
            logging.debug(f[2])
            logging.debug(f[3])

        return(s)

    def cam_connect(self):
        self.hardware_connected = True
        logging.debug("Connecting camera")
        try:
            self.connect()
            logging.debug("Camera connected")
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], 0xE3, 0x0D])
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], 0xE3, 0x0D])
            logging.debug("Modules Enabled")
        except socket_error as e:
            raise HexitecFemError(e)
            self.hardware_connected = False

    def cam_disconnect(self):
        try:
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], 0xE2, 0x0D])
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], 0xE2, 0x0D])
            # self.close()
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

        self.x10g_rdma.write(0x60000002, 0, 'Disable State Machine Trigger')
        logging.debug("Disable State Machine Enabling signal")
            
        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.x10g_rdma.write(0x60000004, 0, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 1_1')
            logging.debug("Initialising sensors on board VSR_1")
            self.vsr_addr = HexitecFem.VSR_ADDRESS[0]
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.x10g_rdma.write(0x60000004, 4, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 2_1')
            logging.debug("Initialising sensors on board VSR 2")
            self.vsr_addr = HexitecFem.VSR_ADDRESS[1]  

        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            logging.debug("Disable synchronisation SM start")
            self.send_cmd([0x23, self.vsr_addr, 0x40, 0x30, 0x41, 0x30, 0x30, 0x0D])
            self.read_response()
            logging.debug("Reading out single sensor")
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            # Need to set up triggering MODE here
            # Enable synchronisation SM start via trigger 1
            logging.debug("Enable synchronisation SM start via trigger 1")
            self.send_cmd([0x23, self.vsr_addr, 0x42, 0x30, 0x41, 0x30, 0x31, 0x0D])
            self.read_response()
            logging.debug("Reading out 2x2 sensors")

        logging.debug("Communicating with - %s" % self.vsr_addr)
        # Set Frame Gen Mux Frame Gate
        self.x10g_rdma.write(0x60000001, 2, 'Set Frame Gen Mux Frame Gate - works set to 2')
        #Following line is important
        self.x10g_rdma.write(0xD0000001, self.number_of_frames-1, 'Frame Gate set to self.number_of_frames')
        
        # Send this command to Enable Test Pattern in my VSR design
        logging.debug("Setting Number of Frames to %s" % self.number_of_frames)
        logging.debug("Enable Test Pattern in my VSR design")
        # Use Sync clock from DAQ board
        logging.debug("Use Sync clock from DAQ board")
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x31, 0x30, 0x0D])
        self.read_response()
        logging.debug("Enable LVDS outputs")
        set_register_vsr1_command  = [0x23, HexitecFem.VSR_ADDRESS[0], 0x42, 0x30, 0x31, 0x32, 0x30, 0x0D]
        set_register_vsr2_command  = [0x23, HexitecFem.VSR_ADDRESS[1], 0x42, 0x30, 0x31, 0x32, 0x30, 0x0D]
        self.send_cmd(set_register_vsr1_command)
        self.read_response()
        self.send_cmd(set_register_vsr2_command)
        self.read_response()
        logging.debug("LVDS outputs enabled")
        logging.debug("Read LO IDLE")
        self.send_cmd([0x23, self.vsr_addr, 0x40, 0x46, 0x45, 0x41, 0x41, 0x0D])
        self.read_response()
        logging.debug("Read HI IDLE")
        self.send_cmd([0x23, self.vsr_addr, 0x40, 0x46, 0x46, 0x4E, 0x41, 0x0D])
        self.read_response()
        # This sets up test pattern on LVDS outputs
        logging.debug("Set up LVDS test pattern")
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x30, 0x31, 0x43, 0x30, 0x0D])
        self.read_response()
        # Use default test pattern of 1000000000000000
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x38, 0x30, 0x0D])
        self.read_response()
        
        full_empty = self.x10g_rdma.read(0x60000011,  'Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.x10g_rdma.read(0x60000012,  'Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
    
    def calibrate_sensor(self):
        # logging.debug("setting image size")
        # 80x80 pixels 14 bits

        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            logging.debug("Reading out single sensor")
            self.set_image_size(80,80,14,16)
            mux_mode = 0
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            #self.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
            mux_mode = 8
            self.set_image_size(160,160,14,16)
            logging.debug("Reading out 2x2 sensors")

        # Set VCAL
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x31, 0x38, 0x30, 0x31, 0x0D])
        self.read_response()
        logging.debug("Clear bit 5")
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x32, 0x30, 0x0D])    # Clear Bit, 20 -> 10100 (Bits: 2 & 4)
        self.read_response()
    
        # Set bit 4 of Reg24
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x31, 0x30, 0x0D])    # Set Bit, 10 -> 1010 (Bits: 1 & 3)
        self.read_response()
        
        logging.debug("Set bit 6")
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x34, 0x30, 0x0D])    # Clear bit, 40 -> 101000 (Bits: 3 & 5)
        self.read_response()
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x30, 0x31, 0x0D])
        self.read_response()
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x32, 0x32, 0x0D])    # Set bit, 22 -> 10110 ( Bits: 1, 2 & 4)
        self.read_response()

        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.x10g_rdma.write(0x60000002, 1, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            logging.debug("CALIBRATING VSR_1")    
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.x10g_rdma.write(0x60000002, 2, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            logging.debug("CALIBRATING VSR_2")  
            
        # Send command on CMD channel to FEMII
        self.x10g_rdma.write(0x60000002, 0, 'Un-Trigger Cal process')

        # Reading back Sync register
        synced = self.x10g_rdma.read(0x60000010,  'Check LVDS has synced')
        logging.debug("Sync Register value")

        full_empty = self.x10g_rdma.read(0x60000011,  'Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)

        full_empty = self.x10g_rdma.read(0x60000012,  'Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        
        # Check whether the currently selected VSR has synchronised or not
        if synced == 15:
            logging.debug("All Links on VSR's 1 and 2 synchronised")
            logging.debug("Starting State Machine in VSR's")
        elif synced == 12:
            logging.debug("Both Links on VSR 2 synchronised")
        elif synced == 3:
            logging.debug("Both Links on VSR 1 synchronised")
        else:
            logging.debug(synced)

        # Send this command to Disable Test Pattern in my VSR design
        # self.send_cmd([0x23, 0x92, 0x00, 0x0D])
        
        # Clear training enable
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x30, 0x31, 0x43, 0x30, 0x0D])
        self.read_response()

        logging.debug("Clear bit 5 - VCAL ENABLED")
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x32, 0x30, 0x0D])        # Clear Bit, 20 -> 10100    (Bits 2 & 4)
        self.read_response()

        if self.dark_correction == HexitecFem.DARKCORRECTION[0]:
            #  Log image to file
            logging.debug("DARK CORRECTION OFF")
            self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x30, 0x38, 0x0D])    # Clear Bit, 08 -> 1000     (Bits: 3)
            self.read_response()
        elif self.dark_correction == HexitecFem.DARKCORRECTION[1]:
            #  Log image to file
            logging.debug("DARK CORRECTION ON")
            self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x30, 0x38, 0x0D])    # Set Bit, 08 -> 1000       (bits 3)
            self.read_response()
        
        # Read Reg24
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x32, 0x34, 0x0D])                    # Read FPGA Reg
        if self.debug: 
            logging.debug("reading Register 0x24")
            logging.debug(self.read_response())
        else:
            self.read_response()
        
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x38, 0x39,  0x0D])
        self.read_response()
        
        
        if self.debug: logging.debug("Poll register 0x89")
        
        bPolling = True
        timeTaken = 0
        while bPolling:
            self.send_cmd([0x23, self.vsr_addr, 0x41, 0x38, 0x39,  0x0D])
            r = self.read_response()
            rr = r.strip()
            Bit1 = int(rr[-1], 16)
            if self.debug:
                logging.debug("Register 0x89, Bit1: %s" % Bit1)
            # Is PLL locked? (ie is Bit 1 high?)
            #   r may be.. "12", "06" or '\xef\xbf\xbd2412'
            if Bit1 & 2:
                bPolling = False
            else:
                time.sleep(0.1)
                timeTaken += 0.1
            if timeTaken > 3.0:
                raise HexitecFemError("Timed out polling register 0x89; PLL remains disabled")

        if self.debug: logging.debug("Bit 1 should be 1")
        if self.debug: logging.debug(r)
        if self.debug: logging.debug("Read reg 1")
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x30, 0x31,  0x0D])
        self.read_response()

        full_empty = self.x10g_rdma.read(0x60000011,  'Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" %  full_empty)

        full_empty = self.x10g_rdma.read(0x60000012,  'Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)

        return synced
 
    def acquire_data(self):

        self.x10g_rdma.write(0xD0000001, self.number_of_frames-1, 'Frame Gate set to self.number_of_frames')
            
        full_empty = self.x10g_rdma.read(0x60000011,  'Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)

        full_empty = self.x10g_rdma.read(0x60000012,  'Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        
        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            logging.debug("Reading out single sensor")
            mux_mode = 0
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            #self.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
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
        time.sleep(1)
        full_empty = self.x10g_rdma.read(0x60000011,  'Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.x10g_rdma.read(0x60000012,  'Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        
        if self.sensors_layout == HexitecFem.READOUTMODE[1]:
            self.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
            
        if self.debug:
            logging.debug("number of Frames := %s" % self.number_of_frames)

        logging.debug("Initiate Data Capture")
        self.data_stream(self.number_of_frames)
        #
        waited = 0.0
        delay = 0.10
        resp = 0
        while resp < 1:
            resp = self.x10g_rdma.read(0x60000014, 'Check data transfer completed?')
            time.sleep(delay)
            waited += delay
            if (self.stop_acquisition):
                break
        logging.debug("Data Capture took " + str(waited) + " seconds")
        self._set_status_message("Requested %s frame(s), took %s seconds" % (self.number_of_frames, str(waited)))

        # Stop the state machine
        self.x10g_rdma.write(0x60000002, 0, 'Dis-Enable State Machine')

        # Clear enable signal
        self.x10g_rdma.write(0xD0000000, 2, 'Clear enable signal')
        self.x10g_rdma.write(0xD0000000, 0, 'Clear enable signal')

        if (self.stop_acquisition):
            logging.error("Acquisition interrupted by User")
            self._set_status_message("User interrupted acquisition")
            self.stop_acquisition = False
            raise HexitecFemError("User interrupted")

        logging.debug("Acquisition Completed, enable signal cleared")
        
        # Clear the Mux Mode bit
        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.x10g_rdma.write(0x60000004, 0, 'Sensor 1 1')
            logging.debug("Sensor 1 1")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.x10g_rdma.write(0x60000004, 4, 'Sensor 2 1')
            logging.debug("Sensor 2 1") 
        full_empty = self.x10g_rdma.read(0x60000011,  'Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.x10g_rdma.read(0x60000012,  'Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        no_frames = self.x10g_rdma.read(0xD0000001,  'Check Number of Frames setting') + 1
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
        
        logging.debug("Input to XAUI")
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

    def set_up_state_machine(self):
        logging.debug("Setting up state machine")

        # Make hardware settings accessible through ini-style config file
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

        value_002 = 0x30, 0x31  # RowS1 Low Byte value: 1 = maximum frame rate
        value_003 = 0x30, 0x30  # RowS1 High Byte value : 0 = ditto
        value_004 = 0x30, 0x31  # S1 -> Sph, 6 bits : 1 = ... Yes, what?
        value_005 = 0x30, 0x36  # SphS2, 6 bits : 6 = ... Yes, what?
        value_006 = 0x30, 0x31  # Gain, 1 bit : 0 = High Gain; 1 = Low Gain
        value_007 = 0x30, 0x33  # UNNAMED, 2 bits : 1 = Enable PLL; 2 = Enable ADC PLL (3 = Enable both)  #TODO: What's it called?
        value_009 = 0x30, 0x32  # ADC1 Delay, 5 bits : 2 = ... 2 clock cycles???                          #TODO: Unit name?
        value_00E = 0x30, 0x41
        value_018 = 0x30, 0x31  # VCAL2 -> VCAL1 Low Byte, 8 bits: 1 = ... 1 clock cycle?                 #TODO: Unit name?   
        value_019 = 0x30, 0x30  # VCAL2 -> VCAL1 High Byte, 7 bits 
        value_01B = 0x30, 0x38  # Wait Clock Row, 8 bits

        #  These are used to set up the state machine
        #sm_timing1  = [0x23, self.vsr_addr, 0x42, 0x30, 0x37, 0x30, 0x33, 0x0D]    # Reg 0x07 -> 3 (Ena PLL, ADC PLL)
        #sm_timing2  = [0x23, self.vsr_addr, 0x42, 0x30, 0x32, 0x30, 0x31, 0x0D]    # Reg 0x02 -> RowS1 (val=0x01)
        #sm_timing3  = [0x23, self.vsr_addr, 0x42, 0x30, 0x34, 0x30, 0x31, 0x0D]    # Reg 0x04 -> S1Sph
        #sm_timing4  = [0x23, self.vsr_addr, 0x42, 0x30, 0x35, 0x30, 0x36, 0x0D]    # Reg 0x05 -> SphS2
        #sm_timing5  = [0x23, self.vsr_addr, 0x42, 0x30, 0x39, 0x30, 0x32, 0x0D]    # Reg 0x09 -> ADC-CLK-delay
        #sm_timing6  = [0x23, self.vsr_addr, 0x42, 0x30, 0x45, 0x30, 0x41, 0x0D]    # Reg 0x0E -> ADC-pipeline SYNC-delay
        #sm_timing7  = [0x23, self.vsr_addr, 0x42, 0x31, 0x42, 0x30, 0x38, 0x0D]    # Reg 0x1B -> waitClkRow
        sm_timing8  = [0x23, self.vsr_addr, 0x42, 0x31, 0x34, 0x30, 0x31, 0x0D]    # Reg 0x14 -> Start SM on falling (0) / rising (1) Edge of ADC-CLK

        # # TODO: Find/Determine settings name in aspect file?
        # unnamed = self._extract_integer('?????', bit_range=2)
        # if unnamed > -1:
        #     value_007 = self.convert_to_aspect_format(unnamed)
        # Send unnamed (Enable PPL, ADC PPL) to Register 0x07 (Accepts 2 bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_007[0], register_007[1], value_007[0], value_007[1], 0x0D])
        self.read_response()

        # Trial obtaining RowS1 Value from config file
        row_s1 = self._extract_integer('Row -> S1', bit_range=14)
        if row_s1 > -1:
            # Valid value, within range
            row_s1_low = row_s1 & 0xFF
            row_s1_high = row_s1 >> 8
            value_002 = self.convert_to_aspect_format(row_s1_low)
            value_003 = self.convert_to_aspect_format(row_s1_high)
        # Send RowS1 low byte to Register 0x02 (Accepts 8 bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_002[0], register_002[1], value_002[0], value_002[1], 0x0D])
        self.read_response()
        # Send RowS1 high byte to Register 0x03 (Accepts 6 bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_003[0], register_003[1], value_003[0], value_003[1], 0x0D])
        self.read_response()

        s1_sph = self._extract_integer('S1 -> Sph', bit_range=6)
        if s1_sph > -1:
            value_004 = self.convert_to_aspect_format(s1_sph)
        # Send S1SPH to Register 0x04 (Accepts 6 bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_004[0], register_004[1], value_004[0], value_004[1], 0x0D])
        self.read_response()

        sph_s2 = self._extract_integer('Sph -> S2', bit_range=6)
        if sph_s2 > -1:
            value_004 = self.convert_to_aspect_format(sph_s2)
        # Send SphS2  to Register 0x05 (Accepts 6 Bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_005[0], register_005[1], value_005[0], value_005[1], 0x0D])
        self.read_response()

        #TODO: What should default value be? (not set by JE previously!)
        gain = self._extract_integer('Gain', bit_range=1)
        if gain > -1:
            value_006 = self.convert_to_aspect_format(gain)
        # Send Gain to Register 0x06 (Accepts 1 Bit)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_006[0], register_006[1], value_006[0], value_006[1], 0x0D])
        self.read_response()

        adc1_delay = self._extract_integer('ADC1 Delay', bit_range=2)
        if adc1_delay > -1:
            value_009 = self.convert_to_aspect_format(adc1_delay)
        # Send ADC1 Delay to Register 0x09 (Accepts 2 Bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_009[0], register_009[1], value_009[0], value_009[1], 0x0D])
        self.read_response()

        delay_sync_signals = self._extract_integer('delay sync signals', bit_range=8)
        if delay_sync_signals > -1:
            value_00E = self.convert_to_aspect_format(delay_sync_signals)
        # Send delay sync signals to Register 0x0E (Accepts 8 Bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_00E[0], register_00E[1], value_00E[0], value_00E[1], 0x0D])
        self.read_response()

        #TODO: Name for this setting in .ini file ??
        # wait_clock_row = self._extract_integer('???', bit_range=8)
        # if wait_clock_row > -1:
        #     value_01B = self.convert_to_aspect_format(wait_clock_row)
        # Send wait clock wait to Register 01B (Accepts 8 Bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_01B[0], register_01B[1], value_01B[0], value_01B[1], 0x0D])
        self.read_response()

        self.send_cmd(sm_timing8)
        self.read_response()

        # vcal Replacement
        vcal2_vcal1 = self._extract_integer('VCAL2 -> VCAL1', bit_range=15)
        if vcal2_vcal1 > -1:
            # Valid value, within range
            vcal2_vcal1_low = vcal2_vcal1 & 0xFF
            vcal2_vcal1_high = vcal2_vcal1 >> 8
            value_018 = self.convert_to_aspect_format(vcal2_vcal1_low)
            value_019 = self.convert_to_aspect_format(vcal2_vcal1_high)
        # Send VCAL2 -> VCAL1 low byte to Register 0x02 (Accepts 8 bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_018[0], register_018[1], value_018[0], value_018[1], 0x0D])
        self.read_response()
        # Send VCAL2 -> VCAL1 high byte to Register 0x03 (Accepts 7 bits)
        self.send_cmd([0x23, self.vsr_addr, 0x42, register_019[0], register_019[1], value_019[0], value_019[1], 0x0D])
        self.read_response()

        logging.debug("Finished Setting up state machine")

    @run_on_executor(executor='thread_executor')
    def collect_offsets(self):

        try:
            if self.hardware_connected != True:
                raise ParameterTreeError("Can't collect offsets without any connection established")
            if self.hardware_busy:
                raise HexitecFemError("Hardware sensors busy initialising")
            else:
                self._set_status_error("")

            self.hardware_busy = True
            self.operation_percentage_complete = 0
            self.operation_percentage_steps = 15

            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], 0x41, 0x32, 0x34, 0x0D])
            vsr1 = self.read_response()
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[1], 0x41, 0x32, 0x34, 0x0D])
            vsr2 = self.read_response()
            logging.debug("Reading back register 24; VSR1: '%s' VSR2: '%s'" % (vsr1.replace('\r', ''), vsr2.replace('\r','')))

            self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x31, 0x30, 0x0D])    # Set Bit, 10 -> 10000 (Bits: 4)
            self.read_response()

            enable_dc_vsr1  = [0x23, HexitecFem.VSR_ADDRESS[0], 0x40, 0x32, 0x34, 0x32, 0x32, 0x0D]  # 0x32, 0x34, 0x32, 0x32, == 24; 22
            enable_dc_vsr2  = [0x23, HexitecFem.VSR_ADDRESS[1], 0x40, 0x32, 0x34, 0x32, 0x32, 0x0D]
            disable_dc_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], 0x40, 0x32, 0x34, 0x32, 0x38, 0x0D]  # 0x32, 0x34, 0x32, 0x38, == 24; 28
            disable_dc_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], 0x40, 0x32, 0x34, 0x32, 0x38, 0x0D]
            enable_sm_vsr1  = [0x23, HexitecFem.VSR_ADDRESS[0], 0x42, 0x30, 0x31, 0x30, 0x31, 0x0D]
            enable_sm_vsr2  = [0x23, HexitecFem.VSR_ADDRESS[1], 0x42, 0x30, 0x31, 0x30, 0x31, 0x0D]
            disable_sm_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], 0x43, 0x30, 0x31, 0x30, 0x30, 0x0D]
            disable_sm_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], 0x43, 0x30, 0x31, 0x30, 0x30, 0x0D]

            # 1. System is fully initialised (Done already)

            # # 2. Stop the state machine

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

            # # 4. Start the state machine

            self.send_cmd(enable_sm_vsr1)
            self.read_response()
            self.send_cmd(enable_sm_vsr2)
            self.read_response()

            # 5. Wait > 8192 * frame time (EITHER 1 sec or loop: 0.25s * 4)

            time.sleep(1)
            # # Register 0x89 (Have offsets collection finished?)
            #       Unstable, crashes frequently
            # check_offsets = [0x23, self.vsr_addr, 0x41, 0x38, 0x49, 0x0D]
            # self.send_cmd(check_offsets)
            # for idx in range(3):
            #     offsets_status = self.read_response()
            #     logging.debug("%s: Offsets status: %s" % (idx, offsets_status.replace('\r', '')))
            #     time.sleep(0.5)

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

            # # 8. Start state machine

            self.send_cmd(enable_sm_vsr1)
            self.read_response()
            self.send_cmd(enable_sm_vsr2)
            self.read_response()

            self.operation_percentage_complete = 100
            self._set_status_message("Offsets collections operation completed.")
            self.hardware_busy = False
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Can't collect offsets without a working connection: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Failed to collect offsets: %s" % str(e))
            logging.error("%s" % str(e))

    def load_pwr_cal_read_enables(self):
        enable_sm     = [0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31, 0x0D]
        disable_sm    = [0x23, self.vsr_addr, 0x43, 0x30, 0x31, 0x30, 0x31, 0x0D]
        diff_cal      = [0x23, self.vsr_addr, 0x42, 0x38, 0x46, 0x30, 0x31, 0x0D]

        register_061 = [0x36, 0x31]   # Column Read Enable ASIC1
        register_0C2 = [0x43, 0x32]   # Column Read Enable ASIC2
        value_061 = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        value_0C2 = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]

        col1_read = self._extract_binary_words('ColumnEn_1stChannel', 2**20)
        if col1_read[0] > -1:
            for idx in range(len(col1_read)):
                # convert_to_aspect_format() turns any value < 16 into a tuple of two
                #   eg: 0x0F -> 30, 48. Only need second value, hence idx [1]
                reg_value = self.convert_to_aspect_format(col1_read[idx])
                value_061[idx + self.CHANNEL_1_OFFSET] = reg_value[1]
                value_0C2[idx + self.CHANNEL_1_OFFSET] = reg_value[1]

        col2_read = self._extract_binary_words('ColumnEn_2ndChannel', 2**20)
        if col2_read[0] > -1:
            for idx in range(len(col2_read)):
                reg_value = self.convert_to_aspect_format(col2_read[idx])
                value_061[idx + self.CHANNEL_2_OFFSET] = reg_value[1]
                value_0C2[idx + self.CHANNEL_2_OFFSET] = reg_value[1]

        col3_read = self._extract_binary_words('ColumnEn_3rdChannel', 2**20)
        if col3_read[0] > -1:
            for idx in range(len(col3_read)):
                reg_value = self.convert_to_aspect_format(col3_read[idx])
                value_061[idx + self.CHANNEL_3_OFFSET] = reg_value[1]
                value_0C2[idx + self.CHANNEL_3_OFFSET] = reg_value[1]

        col4_read = self._extract_binary_words('ColumnEn_4thChannel', 2**20)
        if col4_read[0] > -1:
            for idx in range(len(col4_read)):
                reg_value = self.convert_to_aspect_format(col4_read[idx])
                value_061[idx + self.CHANNEL_4_OFFSET] = reg_value[1]
                value_0C2[idx + self.CHANNEL_4_OFFSET] = reg_value[1]

        # Column Read Enable, for ASIC1 (Reg 0x61)
        col_read_enable1    = [0x23, self.vsr_addr, 0x44, register_061[0], register_061[1], 
                                value_061[0], value_061[1], value_061[2], value_061[3], value_061[4], 
                                value_061[5], value_061[6], value_061[7], value_061[8], value_061[9], 
                                value_061[10], value_061[1], value_061[2], value_061[3], value_061[14], 
                                value_061[15], value_061[1], value_061[2], value_061[3], value_061[19], 
                                0x0D]

        # Column Read Enable, for ASIC2 (Reg 0xC2)
        col_read_enable2    = [0x23, self.vsr_addr, 0x44, register_0C2[0], register_0C2[1], 
                                value_0C2[0], value_0C2[1], value_0C2[2], value_0C2[3], value_0C2[4], 
                                value_0C2[5], value_0C2[6], value_0C2[7], value_0C2[8], value_0C2[9], 
                                value_0C2[10], value_0C2[1], value_0C2[2], value_0C2[3], value_0C2[14], 
                                value_0C2[15], value_0C2[1], value_0C2[2], value_0C2[3], value_0C2[19], 
                                0x0D]

        # Column Power Enable

        register_04D = [0x34, 0x44]   # Column Power Enable ASIC1 (Reg 0x4D)
        register_0AE = [0x41, 0x45]   # Column Power Enable ASIC2 (Reg 0xAE)
        value_04D = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        value_0AE = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]

        col1_power = self._extract_binary_words('ColumnPwr1stChannel', 2**20)
        if col1_power[0] > -1:
            for idx in range(len(col1_power)):
                reg_value = self.convert_to_aspect_format(col1_power[idx])
                value_04D[idx + self.CHANNEL_1_OFFSET] = reg_value[1]
                value_0AE[idx + self.CHANNEL_1_OFFSET] = reg_value[1]

        col2_power = self._extract_binary_words('ColumnPwr2ndChannel', 2**20)
        if col2_power[0] > -1:
            for idx in range(len(col2_power)):
                reg_value = self.convert_to_aspect_format(col2_power[idx])
                value_04D[idx + self.CHANNEL_2_OFFSET] = reg_value[1]
                value_0AE[idx + self.CHANNEL_2_OFFSET] = reg_value[1]

        col3_power = self._extract_binary_words('ColumnPwr3rdChannel', 2**20)
        if col3_power[0] > -1:
            for idx in range(len(col3_power)):
                reg_value = self.convert_to_aspect_format(col3_power[idx])
                value_04D[idx + self.CHANNEL_3_OFFSET] = reg_value[1]
                value_0AE[idx + self.CHANNEL_3_OFFSET] = reg_value[1]

        col4_power = self._extract_binary_words('ColumnPwr4thChannel', 2**20)
        if col4_power[0] > -1:
            for idx in range(len(col4_power)):
                reg_value = self.convert_to_aspect_format(col4_power[idx])
                value_04D[idx + self.CHANNEL_4_OFFSET] = reg_value[1]
                value_0AE[idx + self.CHANNEL_4_OFFSET] = reg_value[1]

        # Column Power Enable, for ASIC1 (Reg 0x4D)
        col_power_enable1    = [0x23, self.vsr_addr, 0x44, register_04D[0], register_04D[1], 
                                value_04D[0], value_04D[1], value_04D[2], value_04D[3], value_04D[4], 
                                value_04D[5], value_04D[6], value_04D[7], value_04D[8], value_04D[9], 
                                value_04D[10], value_04D[1], value_04D[2], value_04D[3], value_04D[14], 
                                value_04D[15], value_04D[1], value_04D[2], value_04D[3], value_04D[19], 
                                0x0D]

        # Column Power Enable, for ASIAE (Reg 0xAE)
        col_power_enable2    = [0x23, self.vsr_addr, 0x44, register_0AE[0], register_0AE[1], 
                                value_0AE[0], value_0AE[1], value_0AE[2], value_0AE[3], value_0AE[4], 
                                value_0AE[5], value_0AE[6], value_0AE[7], value_0AE[8], value_0AE[9], 
                                value_0AE[10], value_0AE[1], value_0AE[2], value_0AE[3], value_0AE[14], 
                                value_0AE[15], value_0AE[1], value_0AE[2], value_0AE[3], value_0AE[19], 
                                0x0D]

        # Column Calibration Enable

        register_057 = [0x35, 0x37]   # Column Calibrate Enable ASIC1 (Reg 0x57)
        register_0B8 = [0x42, 0x38]   # Column Calibrate Enable ASIC2 (Reg 0xB8)
        value_057 = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        value_0B8 = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]

        col1_power = self._extract_binary_words('ColumnCal1stChannel', 2**20)
        if col1_power[0] > -1:
            for idx in range(len(col1_power)):
                reg_value = self.convert_to_aspect_format(col1_power[idx])
                value_057[idx + self.CHANNEL_1_OFFSET] = reg_value[1]
                value_0B8[idx + self.CHANNEL_1_OFFSET] = reg_value[1]

        col2_power = self._extract_binary_words('ColumnCal2ndChannel', 2**20)
        if col2_power[0] > -1:
            for idx in range(len(col2_power)):
                reg_value = self.convert_to_aspect_format(col2_power[idx])
                value_057[idx + self.CHANNEL_2_OFFSET] = reg_value[1]
                value_0B8[idx + self.CHANNEL_2_OFFSET] = reg_value[1]

        col3_power = self._extract_binary_words('ColumnCal3rdChannel', 2**20)
        if col3_power[0] > -1:
            for idx in range(len(col3_power)):
                reg_value = self.convert_to_aspect_format(col3_power[idx])
                value_057[idx + self.CHANNEL_3_OFFSET] = reg_value[1]
                value_0B8[idx + self.CHANNEL_3_OFFSET] = reg_value[1]

        col4_power = self._extract_binary_words('ColumnCal4thChannel', 2**20)
        if col4_power[0] > -1:
            for idx in range(len(col4_power)):
                reg_value = self.convert_to_aspect_format(col4_power[idx])
                value_057[idx + self.CHANNEL_4_OFFSET] = reg_value[1]
                value_0B8[idx + self.CHANNEL_4_OFFSET] = reg_value[1]

        # Column Calibrate Enable, for ASIC1 (Reg 0x57)
        col_cal_enable1    = [0x23, self.vsr_addr, 0x44, register_057[0], register_057[1], 
                                value_057[0], value_057[1], value_057[2], value_057[3], value_057[4], 
                                value_057[5], value_057[6], value_057[7], value_057[8], value_057[9], 
                                value_057[10], value_057[1], value_057[2], value_057[3], value_057[14], 
                                value_057[15], value_057[1], value_057[2], value_057[3], value_057[19], 
                                0x0D]

        # Column Calibrate Enable, for ASIB8 (Reg 0xB8)
        col_cal_enable2    = [0x23, self.vsr_addr, 0x44, register_0B8[0], register_0B8[1], 
                                value_0B8[0], value_0B8[1], value_0B8[2], value_0B8[3], value_0B8[4], 
                                value_0B8[5], value_0B8[6], value_0B8[7], value_0B8[8], value_0B8[9], 
                                value_0B8[10], value_0B8[1], value_0B8[2], value_0B8[3], value_0B8[14], 
                                value_0B8[15], value_0B8[1], value_0B8[2], value_0B8[3], value_0B8[19], 
                                0x0D]

        register_043 = [0x34, 0x33]   # Row Read Enable ASIC1
        register_0A4 = [0x41, 0x34]   # Row Read Enable ASIC2
        value_043 = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        value_0A4 = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]

        row1_read = self._extract_binary_words('RowEn_1stBlock', 2**20)
        if row1_read[0] > -1:
            for idx in range(len(row1_read)):
                reg_value = self.convert_to_aspect_format(row1_read[idx])
                value_043[idx + self.CHANNEL_1_OFFSET] = reg_value[1]
                value_0A4[idx + self.CHANNEL_1_OFFSET] = reg_value[1]

        col2_read = self._extract_binary_words('RowEn_2ndBlock', 2**20)
        if col2_read[0] > -1:
            for idx in range(len(col2_read)):
                reg_value = self.convert_to_aspect_format(col2_read[idx])
                value_043[idx + self.CHANNEL_2_OFFSET] = reg_value[1]
                value_0A4[idx + self.CHANNEL_2_OFFSET] = reg_value[1]

        col3_read = self._extract_binary_words('RowEn_3rdBlock', 2**20)
        if col3_read[0] > -1:
            for idx in range(len(col3_read)):
                reg_value = self.convert_to_aspect_format(col3_read[idx])
                value_043[idx + self.CHANNEL_3_OFFSET] = reg_value[1]
                value_0A4[idx + self.CHANNEL_3_OFFSET] = reg_value[1]

        col4_read = self._extract_binary_words('RowEn_4thBlock', 2**20)
        if col4_read[0] > -1:
            for idx in range(len(col4_read)):
                reg_value = self.convert_to_aspect_format(col4_read[idx])
                value_043[idx + self.CHANNEL_4_OFFSET] = reg_value[1]
                value_0A4[idx + self.CHANNEL_4_OFFSET] = reg_value[1]

        # Row Read Enable, for ASIC1 (Reg 0x43)
        row_read_enable1    = [0x23, self.vsr_addr, 0x44, register_043[0], register_043[1], 
                                value_043[0], value_043[1], value_043[2], value_043[3], value_043[4], 
                                value_043[5], value_043[6], value_043[7], value_043[8], value_043[9], 
                                value_043[10], value_043[1], value_043[2], value_043[3], value_043[14], 
                                value_043[15], value_043[1], value_043[2], value_043[3], value_043[19], 
                                0x0D]

        # Row Read Enable, for ASIC2 (Reg 0xA4)
        row_read_enable2    = [0x23, self.vsr_addr, 0x44, register_0A4[0], register_0A4[1], 
                                value_0A4[0], value_0A4[1], value_0A4[2], value_0A4[3], value_0A4[4], 
                                value_0A4[5], value_0A4[6], value_0A4[7], value_0A4[8], value_0A4[9], 
                                value_0A4[10], value_0A4[1], value_0A4[2], value_0A4[3], value_0A4[14], 
                                value_0A4[15], value_0A4[1], value_0A4[2], value_0A4[3], value_0A4[19], 
                                0x0D]

        # Row Power Enable

        register_02F = [0x32, 0x46]   # Row Power Enable ASIC1 (Reg 0x2F)
        register_090 = [0x39, 0x30]   # Row Power Enable ASIC2 (Reg 0x90)
        value_02F = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        value_090 = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]

        row1_power = self._extract_binary_words('RowPwr1stBlock', 2**20)
        if row1_power[0] > -1:
            for idx in range(len(row1_power)):
                reg_value = self.convert_to_aspect_format(row1_power[idx])
                value_02F[idx + self.CHANNEL_1_OFFSET] = reg_value[1]
                value_090[idx + self.CHANNEL_1_OFFSET] = reg_value[1]

        row2_power = self._extract_binary_words('RowPwr2ndBlock', 2**20)
        if row2_power[0] > -1:
            for idx in range(len(row2_power)):
                reg_value = self.convert_to_aspect_format(row2_power[idx])
                value_02F[idx + self.CHANNEL_2_OFFSET] = reg_value[1]
                value_090[idx + self.CHANNEL_2_OFFSET] = reg_value[1]

        row3_power = self._extract_binary_words('RowPwr3rdBlock', 2**20)
        if row3_power[0] > -1:
            for idx in range(len(row3_power)):
                reg_value = self.convert_to_aspect_format(row3_power[idx])
                value_02F[idx + self.CHANNEL_3_OFFSET] = reg_value[1]
                value_090[idx + self.CHANNEL_3_OFFSET] = reg_value[1]

        row4_power = self._extract_binary_words('RowPwr4thBlock', 2**20)
        if row4_power[0] > -1:
            for idx in range(len(row4_power)):
                reg_value = self.convert_to_aspect_format(row4_power[idx])
                value_02F[idx + self.CHANNEL_4_OFFSET] = reg_value[1]
                value_090[idx + self.CHANNEL_4_OFFSET] = reg_value[1]

        # Row Power Enable, for ASIC1 (Reg 0x2F)
        row_power_enable1    = [0x23, self.vsr_addr, 0x44, register_02F[0], register_02F[1], 
                                value_02F[0], value_02F[1], value_02F[2], value_02F[3], value_02F[4], 
                                value_02F[5], value_02F[6], value_02F[7], value_02F[8], value_02F[9], 
                                value_02F[10], value_02F[1], value_02F[2], value_02F[3], value_02F[14], 
                                value_02F[15], value_02F[1], value_02F[2], value_02F[3], value_02F[19], 
                                0x0D]

        # Row Power Enable, for ASI90 (Reg 0x90)
        row_power_enable2    = [0x23, self.vsr_addr, 0x44, register_090[0], register_090[1], 
                                value_090[0], value_090[1], value_090[2], value_090[3], value_090[4], 
                                value_090[5], value_090[6], value_090[7], value_090[8], value_090[9], 
                                value_090[10], value_090[1], value_090[2], value_090[3], value_090[14], 
                                value_090[15], value_090[1], value_090[2], value_090[3], value_090[19], 
                                0x0D]

        # Row Calibration Enable

        register_039 = [0x33, 0x39]   # Row Calibrate Enable ASIC1 (Reg 0x39)
        register_09A = [0x39, 0x41]   # Row Calibrate Enable ASIC2 (Reg 0x9A)
        value_039 = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        value_09A = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]

        row1_power = self._extract_binary_words('RowCal1stBlock', 2**20)
        if row1_power[0] > -1:
            for idx in range(len(row1_power)):
                reg_value = self.convert_to_aspect_format(row1_power[idx])
                value_039[idx + self.CHANNEL_1_OFFSET] = reg_value[1]
                value_09A[idx + self.CHANNEL_1_OFFSET] = reg_value[1]

        row2_power = self._extract_binary_words('RowCal2ndBlock', 2**20)
        if row2_power[0] > -1:
            for idx in range(len(row2_power)):
                reg_value = self.convert_to_aspect_format(row2_power[idx])
                value_039[idx + self.CHANNEL_2_OFFSET] = reg_value[1]
                value_09A[idx + self.CHANNEL_2_OFFSET] = reg_value[1]

        row3_power = self._extract_binary_words('RowCal3rdBlock', 2**20)
        if row3_power[0] > -1:
            for idx in range(len(row3_power)):
                reg_value = self.convert_to_aspect_format(row3_power[idx])
                value_039[idx + self.CHANNEL_3_OFFSET] = reg_value[1]
                value_09A[idx + self.CHANNEL_3_OFFSET] = reg_value[1]

        row4_power = self._extract_binary_words('RowCal4thBlock', 2**20)
        if row4_power[0] > -1:
            for idx in range(len(row4_power)):
                reg_value = self.convert_to_aspect_format(row4_power[idx])
                value_039[idx + self.CHANNEL_4_OFFSET] = reg_value[1]
                value_09A[idx + self.CHANNEL_4_OFFSET] = reg_value[1]

        # Row Calibrate Enable, for ASIC1 (Reg 0x39)
        row_cal_enable1    = [0x23, self.vsr_addr, 0x42, register_039[0], register_039[1], 
                                value_039[0], value_039[1], value_039[2], value_039[3], value_039[4], 
                                value_039[5], value_039[6], value_039[7], value_039[8], value_039[9], 
                                value_039[10], value_039[1], value_039[2], value_039[3], value_039[14], 
                                value_039[15], value_039[1], value_039[2], value_039[3], value_039[19], 
                                0x0D]

        # Row Calibrate Enable, for ASIC9A (Reg 0x9A)
        row_cal_enable2    = [0x23, self.vsr_addr, 0x42, register_09A[0], register_09A[1], 
                                value_09A[0], value_09A[1], value_09A[2], value_09A[3], value_09A[4], 
                                value_09A[5], value_09A[6], value_09A[7], value_09A[8], value_09A[9], 
                                value_09A[10], value_09A[1], value_09A[2], value_09A[3], value_09A[14], 
                                value_09A[15], value_09A[1], value_09A[2], value_09A[3], value_09A[19], 
                                0x0D]

        # col_read_enable1   = [0x23, self.vsr_addr, 0x44, 0x36, 0x31, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        # col_read_enable2   = [0x23, self.vsr_addr, 0x44, 0x43, 0x32, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        # col_power_enable1  = [0x23, self.vsr_addr, 0x44, 0x34, 0x44, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        # col_power_enable2  = [0x23, self.vsr_addr, 0x44, 0x41, 0x45, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        
        #col_cal_enable1    = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
        #col_cal_enable2    = [0x23, self.vsr_addr, 0x44, 0x42, 0x38, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
        #col_cal_enable1a   = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x30, 0x30, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        #col_cal_enable1a   = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        col_cal_enable1a    = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        col_cal_enable1b    = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x46, 0x30, 0x30, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        col_cal_enable1c    = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        # Uncalibrated (Image4) column option:
        col_cal_enable1d    = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]

        col_cal_enable2a    = [0x23, self.vsr_addr, 0x44, 0x42, 0x38, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        col_cal_enable2b    = [0x23, self.vsr_addr, 0x44, 0x42, 0x38, 0x30, 0x30, 0x30, 0x30, 0x46, 0x30, 0x30, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        col_cal_enable2c    = [0x23, self.vsr_addr, 0x44, 0x42, 0x38, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        # Uncalibrated (Image4) column option:
        col_cal_enable2d    = [0x23, self.vsr_addr, 0x44, 0x42, 0x38, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]

        # row_read_enable1   = [0x23, self.vsr_addr, 0x44, 0x34, 0x33, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        # row_read_enable2   = [0x23, self.vsr_addr, 0x44, 0x41, 0x34, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        # row_power_enable1  = [0x23, self.vsr_addr, 0x44, 0x32, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        # row_power_enable2  = [0x23, self.vsr_addr, 0x44, 0x39, 0x30, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        
        #row_cal_enable1    = [0x23, self.vsr_addr, 0x44, 0x33, 0x39, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
        #row_cal_enable2    = [0x23, self.vsr_addr, 0x44, 0x39, 0x41, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
        #row_cal_enable1a    = [0x23, self.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        row_cal_enable1a    = [0x23, self.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        row_cal_enable1b    = [0x23, self.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        row_cal_enable1c    = [0x23, self.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        # Uncalibrated (Image4) row option:
        row_cal_enable1d    = [0x23, self.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        
        row_cal_enable2a    = [0x23, self.vsr_addr, 0x44, 0x39, 0x41, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        row_cal_enable2b    = [0x23, self.vsr_addr, 0x44, 0x39, 0x41, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        row_cal_enable2c    = [0x23, self.vsr_addr, 0x44, 0x39, 0x41, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        # Uncalibrated (Image4) row option:
        row_cal_enable2d    = [0x23, self.vsr_addr, 0x44, 0x39, 0x41, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]

        logging.debug("Use different CAL data")
        self.send_cmd(diff_cal)
        self.read_response()

        self.send_cmd(disable_sm)
        self.read_response()

        logging.debug("Loading Power, Cal and Read Enables")
        logging.debug("Column power enable")
        self.send_cmd(col_power_enable1)
        self.read_response()
        self.send_cmd(col_power_enable2)
        self.read_response()

        logging.debug("Row power enable")
        self.send_cmd(row_power_enable1)
        self.read_response()
        self.send_cmd(row_power_enable2)
        self.read_response()

        if self.test_mode_image == HexitecFem.TESTMODEIMAGE[0]:    
            logging.debug("Column cal enable A")
            self.send_cmd(col_cal_enable1a)
            self.read_response()
            self.send_cmd(col_cal_enable2a)
            self.read_response()
            logging.debug("Row cal enable A")
            self.send_cmd(row_cal_enable1a)
            self.read_response()
            self.send_cmd(row_cal_enable2a)
            self.read_response()
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[1]:
            logging.debug("Column cal enable B")
            self.send_cmd(col_cal_enable1b)
            self.read_response()
            self.send_cmd(col_cal_enable2b)
            self.read_response()
            logging.debug("Row cal enable B")
            self.send_cmd(row_cal_enable1b)
            self.read_response()
            self.send_cmd(row_cal_enable2b)
            self.read_response()
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[2]:
            logging.debug("Column cal enable C")
            self.send_cmd(col_cal_enable1c)
            self.read_response()
            self.send_cmd(col_cal_enable2c)
            self.read_response()
            logging.debug("Row cal enable C")
            self.send_cmd(row_cal_enable1c)
            self.read_response()
            self.send_cmd(row_cal_enable2c)
            self.read_response()
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[3]:
            logging.debug("Column cal enable D")
            self.send_cmd(col_cal_enable1d)
            self.read_response()
            self.send_cmd(col_cal_enable2d)
            self.read_response()
            logging.debug("Row cal enable D")
            self.send_cmd(row_cal_enable1d)
            self.read_response()
            self.send_cmd(row_cal_enable2d)
            self.read_response()
            
        logging.debug("Column read enable")
        self.send_cmd(col_read_enable1)
        self.read_response()
        self.send_cmd(col_read_enable2)
        self.read_response()
    
        logging.debug("Row read enable")
        self.send_cmd(row_read_enable1)
        self.read_response()
        self.send_cmd(row_read_enable2)
        self.read_response()

        logging.debug("Power, Cal and Read Enables have been loaded")
        
        self.send_cmd(enable_sm)
        self.read_response()
        
    def write_dac_values(self):
        logging.debug("Writing DAC values")
        vcal  = [0x30, 0x32, 0x41, 0x41]
        umid  = [0x30, 0x35, 0x35, 0x35]
        hv    = [0x30, 0x35, 0x35, 0x35]
        dctrl = [0x30, 0x30, 0x30, 0x30]
        rsrv2 = [0x30, 0x38, 0x45, 0x38]

        umid_value = self._extract_exponential('Uref_mid', bit_range=12)
        if umid_value > -1:
            # Valid value, within range
            umid_high = umid_value >> 8
            umid_low = umid_value & 0xFF
            umid[0], umid[1] = self.convert_to_aspect_format(umid_high)
            umid[2], umid[3] = self.convert_to_aspect_format(umid_low)

        self.send_cmd([0x23, self.vsr_addr, 0x54, 
                        vcal[0], vcal[1], vcal[2], vcal[3],     # Vcal, e.g. 0x0111 =: 0.2V
                        umid[0], umid[1], umid[2], umid[3],     # Umid, e.g. 0x0555 =: 1.0V
                        hv[0],   hv[1],   hv[2],   hv[3],       # reserve1, 0x0555 =: 1V (-> HV ca. -250V)
                        dctrl[0], dctrl[1], dctrl[2], dctrl[3], # DET ctrl, 0x000
                        rsrv2[0], rsrv2[1], rsrv2[2], rsrv2[3], # reserve2, 0x08E8 =: 1.67V
                        0x0D])
        self.read_response()
        logging.debug("DAC values set")
        
    def enable_adc(self):
        logging.debug("Enabling ADC")
        adc_disable   = [0x23, self.vsr_addr, 0x55, 0x30, 0x32, 0x0D]
        enable_sm     = [0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31, 0x0D]
        adc_enable    = [0x23, self.vsr_addr, 0x55, 0x30, 0x33, 0x0D]
        adc_set       = [0x23, self.vsr_addr, 0x53, 0x31, 0x36, 0x30, 0x39, 0x0D]
        aqu1          = [0x23, self.vsr_addr, 0x40, 0x32, 0x34, 0x32, 0x32, 0x0D]
        aqu2          = [0x23, self.vsr_addr, 0x40, 0x32, 0x34, 0x32, 0x38, 0x0D]   
        
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
        self.send_cmd(aqu2)
        self.read_response()
        
        # Disable  ADC test testmode
        self.send_cmd([0x23, self.vsr_addr, 0x53, 0x30, 0x44, 0x30, 0x30, 0x0d])
        self.read_response() 

    def enable_adc_testmode(self):
        logging.debug("Enabling ADC Testmode")
        # Set ADC test testmode
        self.send_cmd([0x23, self.vsr_addr, 0x53, 0x30, 0x44, 0x34, 0x38, 0x0d])
        self.read_response() 
        # 0x3FC0 - Word 1
        self.send_cmd([0x23, self.vsr_addr, 0x53, 0x31, 0x39, 0x43, 0x30, 0x0d])
        self.read_response()
        self.send_cmd([0x23, self.vsr_addr, 0x53, 0x31, 0x41, 0x33, 0x46, 0x0d])
        self.read_response()   
        
        if self.test_mode_image == HexitecFem.TESTMODEIMAGE[0]:
            # 0x3FFB - Word 2
            self.send_cmd([0x23, self.vsr_addr, 0x53, 0x31, 0x42, 0x46, 0x42, 0x0d])
            self.read_response()
            self.send_cmd([0x23, self.vsr_addr, 0x53, 0x31, 0x43, 0x33, 0x46, 0x0d])
            self.read_response()  
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[1]:
            # 0x1FFF - Word 2
            self.send_cmd([0x23, self.vsr_addr, 0x53, 0x31, 0x42, 0x46, 0x46, 0x0d])
            self.read_response()
            self.send_cmd([0x23, self.vsr_addr, 0x53, 0x31, 0x43, 0x31, 0x46, 0x0d])
            self.read_response()  
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[2]:
            # 0x3FF7 - Word 2
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], 0x53, 0x31, 0x42, 0x46, 0x37, 0x0d])
            self.read_response()
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], 0x53, 0x31, 0x43, 0x33, 0x46, 0x0d])
            self.read_response()
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[3]:
            # 0x3BFF - Word 2
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], 0x53, 0x31, 0x42, 0x46, 0x46, 0x0d])
            self.read_response()
            self.send_cmd([0x23, HexitecFem.VSR_ADDRESS[0], 0x53, 0x31, 0x43, 0x33, 0x42, 0x0d])
            self.read_response()

    def initialise_system(self):
        # Does init, load, set up, write, enable, calibrate all in one fell swoooop
        #  for VSR2 followed by VSR1

        self._set_status_message("Configuring VSR2");
        self.selected_sensor = HexitecFem.OPTIONS[2]
        self.initialise_sensor()
        
        self._set_status_message("VSR2: Sensors initialised.")
        self.load_pwr_cal_read_enables()

        self._set_status_message("VSR2: Loaded Power, Calibrate, Read Enables")
        self.set_up_state_machine()
        
        self._set_status_message("VSR2: State Machine setup")
        self.write_dac_values()

        self._set_status_message("VSR2: DAC values written")
        self.enable_adc()

        self._set_status_message("VSR2: ADC enabled")
        synced_status = self.calibrate_sensor()
        logging.debug("Synchronised: %s" % synced_status)  # == 15..

        self._set_status_message("Configuring VSR1");
        self.selected_sensor = HexitecFem.OPTIONS[0]
        
        self.initialise_sensor()
        
        self._set_status_message("VSR1: Sensors initialised")
        self.load_pwr_cal_read_enables()

        self._set_status_message("VSR1: Loaded Power, Calibrate, Read Enables")
        self.set_up_state_machine()
        
        self._set_status_message("VSR1: State Machine setup")
        self.write_dac_values()

        self._set_status_message("VSR1: DAC values written")
        self.enable_adc()
        
        self._set_status_message("VSR1: ADC enabled")
        synced_status = self.calibrate_sensor()
        logging.debug("Synchronised: %s" % synced_status)  # Usually it's 15..
        print("----------------------------------------------------------------------------------------------")
        self._set_status_message("Initialisation completed. VSR2 and VS1 configured.");

    def read_temperatures_humidity_values(self):
        self.send_cmd([0x23, self.vsr_addr, 0x52, 0x0D], False)
        sensors_values = self.read_response()
        sensors_values = sensors_values.strip()
        if self.debug: 
            logging.debug("VSR: %s sensors_values: %s len: %s" % (format(self.vsr_addr, '#02x'), sensors_values, len(sensors_values)))

        # Check register value is koshure or sensor values weren't read out
        initial_value = -1
        try:
            initial_value = int(sensors_values[1])
        except ValueError as e:
            logging.error("Failed to readout intelligible sensor values")
            return

        if initial_value == HexitecFem.SENSORS_READOUT_OK:

            ambient_hex     = sensors_values[1:5]
            humidity_hex    = sensors_values[5:9]
            asic1_hex       = sensors_values[9:13]
            asic2_hex       = sensors_values[13:17]
            adc_hex         = sensors_values[17:21]

            if (self.vsr_addr == HexitecFem.VSR_ADDRESS[0]):
                self.vsr1_ambient     = self.get_ambient_temperature(ambient_hex)
                self.vsr1_humidity    = self.get_humidity(humidity_hex)
                self.vsr1_asic1       = self.get_asic_temperature(asic1_hex)
                self.vsr1_asic2       = self.get_asic_temperature(asic2_hex)
                self.vsr1_adc         = self.get_adc_temperature(adc_hex)
            else:
                if (self.vsr_addr == HexitecFem.VSR_ADDRESS[1]):
                    self.vsr2_ambient     = self.get_ambient_temperature(ambient_hex)
                    self.vsr2_humidity    = self.get_humidity(humidity_hex)
                    self.vsr2_asic1       = self.get_asic_temperature(asic1_hex)
                    self.vsr2_asic2       = self.get_asic_temperature(asic2_hex)
                    self.vsr2_adc         = self.get_adc_temperature(adc_hex)
        else:
            logging.warn("VSR 0x%s: Sensor data temporarily unavailable" % format(self.vsr_addr, '02x'))

    # Calculate ambient temperature
    def get_ambient_temperature(self, hex_val):
        try:
            return ((int(hex_val, 16) * 175.72) / 65536) - 46.84
        except ValueError as e:
            logging.error("Error converting ambient temperature: %s" % e)
            return -1

    # Calculate Humidity
    def get_humidity(self, hex_val):
        try:
            return ((int(hex_val, 16) * 125) / 65535) - 6
        except ValueError as e:
            logging.error("Error converting humidity: %s" % e)
            return -1

    # Calculate ASIC temperature
    def get_asic_temperature(self, hex_val):
        try:
            return int(hex_val, 16) * 0.0625
        except ValueError as e:
            logging.error("Error converting ASIC temperature: %s" % e)
            return -1

    # Calculate ADC Temperature
    def get_adc_temperature(self, hex_val):
        try:
            return int(hex_val, 16) * 0.0625
        except ValueError as e:
            logging.error("Error converting ADC temperature: %s" % e)
            return -1

    def _set_aspect_config(self, filename):
        # Check whether file exists..
        try:
            with open(filename, 'r') as f:
                pass
            self.aspect_config = filename
            logging.debug("aspect_config: '%s' Filename: '%s'" % (self.aspect_config, filename))
        except IOError as e:
            logging.error("Cannot open provided aspect file: %s -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-" % e)
            raise ParameterTreeError("Error: %s" % e)
        #
        import pprint
        self.read_ini_file(self.aspect_config)
        pprint.pprint(self.aspect_parameters)

    def _parse_ini_file(self, parameters):
        pass

    def convert_aspect_exponent_to_dac_value(self, exponent):
        ''' Aspect's exponent format looks like: 1,003000E+2
            Convert to float (eg: 100.3), rounding to nearest 
            int before scaling to fit DAC range '''
        number_string = str(exponent)
        # print number_string, type(number_string)
        number_string = number_string.replace(",", ".")
        # print number_string, type(number_string)
        number_float = float(number_string)
        # print number_float, type(number_float)
        number_int = int(round(number_float))
        number_scaled = number_int * self.DAC_SCALE_FACTOR
        return number_scaled

    def _extract_exponential(self, descriptor, bit_range):
        valid_range = [0, 1 << bit_range]
        setting = -1
        try:
            unscaled_setting = self.aspect_parameters[descriptor]
            scaled_setting   = self.convert_aspect_exponent_to_dac_value(unscaled_setting)
            if scaled_setting >= valid_range[0] and scaled_setting <= valid_range[1]:
                setting = scaled_setting
            else:
                logging.error("Error parsing parameter %s, got: %s (scaled: % s) but valid range: %s-%s" % \
                            (descriptor, unscaled_setting, scaled_setting, valid_range[0], valid_range[1]))
                setting = -1
        except KeyError:
            logging.warn("Warn: No '%s' Key defined!" % descriptor)
        return setting

    def _extract_integer(self, descriptor, bit_range):
        valid_range = [0, 1 << bit_range]
        setting = -1
        try:
            setting = int(self.aspect_parameters[descriptor])
            if setting >= valid_range[0] and setting <= valid_range[1]:
                pass
            else:
                logging.error("Error parsing parameter %s, got: %s but valid range: %s-%s" % \
                            (descriptor, setting, valid_range[0], valid_range[1]))
                setting = -1
        except KeyError:
            logging.warn("Warning: No '%s' Key defined!" % descriptor)
        return setting

    def _extract_binary_words(self, descriptor, bit_range):
        valid_range = [0, (1 << bit_range) - 1]
        hex_words = []
        setting = [-1, -1, -1, -1, -1]
        try:
            parameter = self.aspect_parameters[descriptor]
            setting = int(parameter, 2)
            if setting >= valid_range[0] and setting <= valid_range[1]:
                # Split into 5 hexidecimal words (4 bits/word)
                word_length = len(parameter)
                if word_length != 20:
                    logging.error("Error: Key %s is %s chars long, expected: %s" % \
                                (descriptor, word_length, 20))
                    setting = [-1, -1, -1, -1, -1]
                else:
                    for idx in range(0, word_length, 4):
                        value = int(parameter[idx:idx+4], 2)
                        hex_words.append(value)
                    setting = hex_words
            else:
                logging.error("Error parsing parameter %s, got: %s but valid range: %s-%s" % \
                            (descriptor, setting, valid_range[0], valid_range[1]))
                setting = [-1, -1, -1, -1, -1]
        except KeyError:
            logging.warn("Warn: No '%s' Key defined!" % descriptor)
        return setting

    def convert_to_aspect_format(self, value):
        '''  Convert integer to Aspect's hexadecimal notation
                e.g. 31 (=1F) -> 0x31, 0x46
        '''
        hex_string = "{:02x}".format(value)
        #logging.debug("value: {:} Hex: {:}".format(value, hex_string))
        high_string = hex_string[0]
        low_string = hex_string[1]
        high_int = int(high_string, 16)
        low_int = int(low_string, 16)
        high_encoded = self.HEX_ASCII_CODE[high_int]
        low_encoded = self.HEX_ASCII_CODE[low_int]
        #logging.debug("H: {:02x} L: {:02x}".format(high_encoded, low_encoded))
        return high_encoded, low_encoded

    # Read ini-style file - Original implementation
    def read_ini_file_original(self, filename):
        try:
            with open(filename, 'r') as f:
                line = "(blank)"
                while len(line) > 0:
                    line = f.readline()
                    if "[" in line:
                        pass
                    else:
                        try:
                            key, value = line.split("=")
                            key, value = key.strip(), value.strip().strip("\"")
                            if key in self.aspect_parameters and self.aspect_parameters[key] != value:
                                logging.warning("Updating Key '%s' (%s) to '%s'" % \
                                                (key, self.aspect_parameters[key], value))
                            self.aspect_parameters[key] = value
                        except ValueError:
                            #Don't parse empty line(s)
                            pass
        except IOError as e:
            logging.error("Error parsing ini file: %s" % e)

    def read_ini_file(self, filename):
        ''' Read filename, parsing case sensitive keys, decoded as strings '''
        parser = configparser.ConfigParser()
        # Maintain case-sensitivity:
        parser.optionxform=str
        parser.read(filename)
        for sect in parser.sections():
            print('Section:', sect)
            for k,v in parser.items(sect):
                self.aspect_parameters[k] = v.encode("utf-8").strip("\"")


class HexitecFemError(Exception):
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass

