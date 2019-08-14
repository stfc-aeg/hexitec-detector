
#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri July 05 15:00:14 2019

@author: ckd27546
"""


import time
import datetime
import logging
from QemCam import *

from concurrent import futures
from socket import error as socket_error
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor
from tornado.escape import json_decode

class HexitecFem():
    """ Hexitec Fem class. Represents a single FEM-II module.
    
    Controls and configures each FEM-II module ready for a DAQ via UDP.
    """
    thread_executor = futures.ThreadPoolExecutor(max_workers=2)

    OPTIONS = [
    "Sensor_1_1",
    "Sensor_1_2",
    "Sensor_2_1",
    "Sensor_2_2"
    ] #etc

    IMAGE = [
    "LOG HDF5 FILE",
    "LOG BIN FILE",
    "STREAM DATA",
    "NETWORK PACKETS ONLY"
    ] #etc

    TESTMODEIMAGE = [
    "IMAGE 1",
    "IMAGE 2",
    "IMAGE 3",
    "IMAGE 4"
    ]

    DARKCORRECTION = [
    0,
    1]

    READOUTMODE = [
    "SINGLE",
    "2x2"]


    def __init__(self, ip_address='127.0.0.1', port=1232, fem_id=1,
                server_ctrl_ip_addr='10.0.2.2', camera_ctrl_ip_addr='10.0.2.1',
                server_data_ip_addr='10.0.4.2', camera_data_ip_addr='10.0.4.1'):

        self.ip_address = ip_address
        self.port = port
        self.id = int(fem_id)
        self.hexitec_camera = QemCam()

        # 10G RDMA IP addresses      
        self.hexitec_camera.server_ctrl_ip_addr = server_ctrl_ip_addr    #'10.0.2.2'
        self.hexitec_camera.camera_ctrl_ip_addr = camera_ctrl_ip_addr    #'10.0.2.1'

        # 10G image stream Ip addresses
        self.hexitec_camera.server_data_ip_addr = server_data_ip_addr    #"10.0.4.2"
        self.hexitec_camera.camera_data_ip_addr = camera_data_ip_addr    #"10.0.4.1"

        self.vsr_addr = 0x90

        self.number_of_frames = 10

        self.hardware_connected = False
        self.hardware_initialising = False

        # Acquisition completed, note completion
        self.acquisition_completed = False
        self.acquisition_timestamp = 0.0

        self.debug = False

        self.status_message = ""
        self.status_error = ""
        self.stop_acquisition = False
        # 
        self.initialise_progress = 0                # Used by initialise_system()
        self.operation_percentage_complete = 0

        self.selected_sensor    = HexitecFem.OPTIONS[2]         # "Sensor_2_1"
        self.sensors_layout     = HexitecFem.READOUTMODE[1]     # "2x2"
        self.dark_correction    = HexitecFem.DARKCORRECTION[0]  # "DARK CORRECTION OFF" = 0
        self.test_mode_image    = HexitecFem.TESTMODEIMAGE[3]   # "IMAGE 4"

        param_tree_dict = {
            "ip_addr": (self.get_address, None),    # Replicated, not needed going forwards?
            "port": (self.get_port, None),          # Replicated, not needed going forwards?
            "id": (self.id, None),
            "connect_hardware": (None, self.connect_hardware),
            "initialise_hardware": (None, self.initialise_hardware),
            "collect_data": (None, self.collect_data),
            "disconnect_hardware": (None, self.disconnect_hardware),
            "debug": (self.get_debug, self.set_debug),
            "status_message": (self._get_status_message, None),
            "status_error": (self._get_status_error, None),
            "initialise_progress": (self._get_initialise_progress, None),
            "operation_percentage_complete": (self._get_operation_percentage_complete, None),
            "stop_acquisition": (None, self._set_stop_acquisition),
            "dark_correction": (self._get_dark_correction, self._set_dark_correction),
            "number_frames": (self._get_number_frames, self._set_number_frames)
        }

        self.param_tree = ParameterTree(param_tree_dict)
        
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

    @run_on_executor(executor='thread_executor')
    def connect_hardware(self, msg):
        try:
            if self.hardware_connected:
                raise ParameterTreeError("Connection already established")
            else:
                self._set_status_error("")
            self._set_status_message("Connecting to camera..")
            self.cam_connect()
            self._set_status_message("Camera connected. Waiting for sensors to initialise..")
            self.hardware_connected = True
            self.hardware_initialising = True
            start = time.time()
            percent_step = 10
            self.operation_percentage_complete = 0
            delay = 0.0
            while (delay < 10):
                time.sleep(1.0)
                self.operation_percentage_complete += percent_step
                delay = time.time() - start
            self.hardware_initialising = False
            self._set_status_message("Camera connected. Sensors initialised.")
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Failed to connect with camera: %s" % str(e))
            self._set_status_message("Is camera powered?")
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Failed to establish camera connection: %s" % str(e))
            logging.error("%s" % str(e))
            # Cannot raise error beyond this thread

    @run_on_executor(executor='thread_executor')
    def initialise_hardware(self, msg):
        try:
            if self.hardware_connected != True:
                raise ParameterTreeError("No connection established")
            if self.hardware_initialising:
                raise HexitecFemError("Hardware sensors busy initialising")
            else:
                self._set_status_error("")
            self.operation_percentage_complete = 0
            self.initialise_system()
            self.initialise_progress = 0
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Failed to initialise camera: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Camera initialisation failed: %s" % str(e))
            logging.error("%s" % str(e))

    @run_on_executor(executor='thread_executor')
    def collect_data(self, msg):
        try:
            if self.hardware_connected != True:
                raise ParameterTreeError("No connection established")
            if self.hardware_initialising:
                raise HexitecFemError("Hardware sensors busy initialising")
            else:
                self._set_status_error("")
            self.operation_percentage_complete = 0
            self._set_status_message("Acquiring data..")
            self.acquire_data()
            self.operation_percentage_complete = 100
            # Acquisition completed, note completion
            self.acquisition_completed = True
            self.acquisition_timestamp = time.time()
        except (HexitecFemError, ParameterTreeError) as e:
            self._set_status_error("Failed to collect data: %s" % str(e))
            logging.error("%s" % str(e))
        except Exception as e:
            self._set_status_error("Uncaught Exception; Data collection failed: %s" % str(e))
            logging.error("%s" % str(e))

    @run_on_executor(executor='thread_executor')
    def disconnect_hardware(self, msg):
        try:
            if self.hardware_connected == False:
                raise ParameterTreeError("No connection to disconnect")
            else:
                self._set_status_error("")
            # Stop acquisition if it's hung
            if self.operation_percentage_complete < 100:
                self.stop_acquisition = True
            #
            self.operation_percentage_complete = 0
            self._set_status_message("Disconnecting camera..")
            self.cam_disconnect()
            self._set_status_message("Camera disconnected")
            self.operation_percentage_complete = 100
            self.hardware_connected = False
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

    #  This function sends a command string to the microcontroller
    def send_cmd(self, cmd):

        self.initialise_progress += 1
        self.operation_percentage_complete = (self.initialise_progress * 100)  / 108;

        while len(cmd)%4 != 0:
            cmd.append(13)
        if self.debug: logging.debug("Length of command - %s %s" % (len(cmd), len(cmd)%4))

        for i in range ( 0 , len(cmd)/4 ):

            reg_value = 256*256*256*cmd[(i*4)] + 256*256*cmd[(i*4)+1] + 256*cmd[(i*4)+2] + cmd[(i*4)+3] 
            self.hexitec_camera.x10g_rdma.write(0xE0000100, reg_value, 'Write 4 Bytes')
            time.sleep(0.25)

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
        
        while daty != CARRIAGE_RTN :
            fifo_empty = FIFO_EMPTY_FLAG

            while fifo_empty == FIFO_EMPTY_FLAG and empty_count < ABORT_VALUE:
                fifo_empty = self.hexitec_camera.x10g_rdma.read(0xE0000011, 'FIFO EMPTY FLAG')
                empty_count = empty_count + 1
            if self.debug: logging.debug("Got data:- ")
            dat = self.hexitec_camera.x10g_rdma.read(0xE0000200, 'Data')
            if self.debug: logging.debug("Bytes are:- ")
            daty = dat/256/256/256%256
            f.append(daty)
            if self.debug: logging.debug(format(daty, '02x'))
            daty = dat/256/256%256
            f.append(daty)
            if self.debug: logging.debug(format(daty, '02x'))
            daty = dat/256%256
            f.append(daty)
            if self.debug: logging.debug(format(daty, '02x'))
            daty = dat%256
            f.append(daty)
            if self.debug: logging.debug(format(daty, '02x'))
            data_counter = data_counter + 1
            if empty_count == ABORT_VALUE:
                logging.error("Error: read_respomse from FEM aborted")
                raise HexitecFemError("read_response aborted")
            empty_count = 0          

        if self.debug: 
            logging.debug("Counter is :- %s" % data_counter)
            logging.debug("Length is:- %s" % len(f))
        fifo_empty = self.hexitec_camera.x10g_rdma.read(0xE0000011, 'Data')
        if self.debug: logging.debug("FIFO should be empty: %s" % fifo_empty)
        s = ''

        for i in range( 1 , data_counter*4):
            # if self.debug: logging.debug(i)
            s = s + chr(f[i])

        if self.debug: 
            logging.debug("String :- %s" % s)
            logging.debug(f[0])
            logging.debug(f[1])

        return(s)

    def cam_connect(self):
        
        logging.debug("Connecting camera")
        try:
            self.hexitec_camera.connect()
            logging.debug("Camera connected")
            self.send_cmd([0x23, 0x90, 0xE3, 0x0D])
            time.sleep(1)
            self.send_cmd([0x23, 0x91, 0xE3, 0x0D])
            logging.debug("Modules Enabled")
        except socket_error as e:
            raise HexitecFemError(e)

    def cam_disconnect(self):
        try:
            self.send_cmd([0x23, 0x90, 0xE2, 0x0D])
            self.send_cmd([0x23, 0x91, 0xE2, 0x0D])
            logging.debug("Modules Disabled")
            self.hexitec_camera.disconnect()
            logging.debug("Camera is Disconnected")
        except socket_error as e:
            logging.error("Unable to disconnect camera: %s" % str(e))
            raise HexitecFemError(e)
        except AttributeError as e:
            logging.error("Unable to disconnect camera: %s" % "No active connection")
            raise HexitecFemError("%s; %s" % (e, "No active connection"))

    def initialise_sensor(self):

        self.hexitec_camera.x10g_rdma.write(0x60000002, 0, 'Disable State Machine Trigger')
        logging.debug("Disable State Machine Enabling signal")
            
        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.hexitec_camera.x10g_rdma.write(0x60000004, 0, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 1_1')
            logging.debug("Initialising sensors on board VSR_1")
            self.vsr_addr = 0x90
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.hexitec_camera.x10g_rdma.write(0x60000004, 4, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 2_1')
            logging.debug("Initialising sensors on board VSR 2")
            self.vsr_addr = 0x91  

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
        self.hexitec_camera.x10g_rdma.write(0x60000001, 2, 'Set Frame Gen Mux Frame Gate - works set to 2')
        #Following line is important
        self.hexitec_camera.x10g_rdma.write(0xD0000001, self.number_of_frames-1, 'Frame Gate set to self.number_of_frames')
        
        # Send this command to Enable Test Pattern in my VSR design
        logging.debug("Setting Number of Frames to %s" % self.number_of_frames)
        logging.debug("Enable Test Pattern in my VSR design")
        # Use Sync clock from DAQ board
        logging.debug("Use Sync clock from DAQ board")
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x31, 0x30, 0x0D])
        self.read_response()
        logging.debug("Enable LVDS outputs")
        set_register_vsr1_command  = [0x23, 0x90, 0x42, 0x30, 0x31, 0x32, 0x30, 0x0D]
        set_register_vsr2_command  = [0x23, 0x91, 0x42, 0x30, 0x31, 0x32, 0x30, 0x0D]
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
        
        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000011,  'Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000012,  'Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
    
    def calibrate_sensor(self):
        # logging.debug("setting image size")
        # 80x80 pixels 14 bits
        #self.hexitec_camera.set_image_size(80,80,14,16)

        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            logging.debug("Reading out single sensor")
            self.hexitec_camera.set_image_size(80,80,14,16)
            mux_mode = 0
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            #self.hexitec_camera.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
            mux_mode = 8
            self.hexitec_camera.set_image_size(160,160,14,16)
            logging.debug("Reading out 2x2 sensors")

        # Set VCAL
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x31, 0x38, 0x30, 0x31, 0x0D])
        self.read_response()
        logging.debug("Clear bit 5")
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x32, 0x30, 0x0D])
        self.read_response()
    
        # Set bit 4 of Reg24
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x31, 0x30, 0x0D])
        self.read_response()
        
        logging.debug("Set bit 6")
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x34, 0x30, 0x0D])
        self.read_response()
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x30, 0x31, 0x0D])
        self.read_response()
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x32, 0x32, 0x0D])
        self.read_response()

        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.hexitec_camera.x10g_rdma.write(0x60000002, 1, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            logging.debug("CALIBRATING VSR_1")    
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.hexitec_camera.x10g_rdma.write(0x60000002, 2, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            logging.debug("CALIBRATING VSR_2")  
            
        # Send command on CMD channel to FEMII
        #self.hexitec_camera.x10g_rdma.write(0x60000002, 3, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
        self.hexitec_camera.x10g_rdma.write(0x60000002, 0, 'Un-Trigger Cal process')

        # Reading back Sync register
        synced = self.hexitec_camera.x10g_rdma.read(0x60000010,  'Check LVDS has synced')
        logging.debug("Sync Register value")

        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000011,  'Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)

        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000012,  'Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        
        # Check whether the currently selected VSR has synchronised or not
        if synced == 15:
            logging.debug("All Links on VSR's 1 and 2 synchronised")
            #self.hexitec_camera.x10g_rdma.write(0x60000002, 4, 'Enable state machines in VSRs ')
            logging.debug("Starting State Machine in VSR's")
        elif synced == 12:
            logging.debug("Both Links on VSR 2 synchronised")
        elif synced == 3:
            logging.debug("Both Links on VSR 1 synchronised")
        else:
            logging.debug(synced)

        # Send this command to Disable Test Pattern in my VSR design
        self.send_cmd([0x23, 0x92, 0x00, 0x0D])
        
        # Clear training enable
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x30, 0x31, 0x43, 0x30, 0x0D])
        self.read_response()

        logging.debug("Clear bit 5 - VCAL ENABLED")
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x32, 0x30, 0x0D])
        self.read_response()

        if self.dark_correction == HexitecFem.DARKCORRECTION[0]:
            #  Log image to file
            logging.debug("DARK CORRECTION OFF")
            self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x30, 0x38, 0x0D])
            self.read_response()
        elif self.dark_correction == HexitecFem.DARKCORRECTION[1]:
            #  Log image to file
            logging.debug("DARK CORRECTION ON")
            self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x30, 0x38, 0x0D])    
            self.read_response()
        
        # Read Reg24
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x32, 0x34, 0x0D])
        if self.debug: logging.debug("reading Register 0x24")
        if self.debug: logging.debug(self.read_response())
        
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x38, 0x39,  0x0D])
        self.read_response()
        
        time.sleep(3)
        
        if self.debug: logging.debug("Poll register 0x89")
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x38, 0x39,  0x0D])
        r = self.read_response()
        if self.debug: logging.debug("Bit 1 should be 1")
        if self.debug: logging.debug(r)
        if self.debug: logging.debug("Read reg 1")
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x30, 0x31,  0x0D])
        self.read_response()

        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000011,  'Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" %  full_empty)

        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000012,  'Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)

        return synced
 
    def acquire_data(self):

        self.hexitec_camera.x10g_rdma.write(0xD0000001, self.number_of_frames-1, 'Frame Gate set to self.number_of_frames')
            
        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000011,  'Check FULL EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)

        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000012,  'Check FULL FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        
        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            logging.debug("Reading out single sensor")
            mux_mode = 0
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            #self.hexitec_camera.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
            mux_mode = 8
            logging.debug("Reading out 2x2 sensors")

        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.hexitec_camera.x10g_rdma.write(0x60000004, 0 + mux_mode, 'Sensor 1 1')
            logging.debug("Sensor 1 1")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.hexitec_camera.x10g_rdma.write(0x60000004, 4 + mux_mode, 'Sensor 2 1')
            logging.debug("Sensor 2 1") 
            
        # Flush the input FIFO buffers
        self.hexitec_camera.x10g_rdma.write(0x60000002, 32, 'Clear Input Buffers')
        self.hexitec_camera.x10g_rdma.write(0x60000002, 0, 'Clear Input Buffers')
        time.sleep(1)
        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000011,  'Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000012,  'Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        
        if self.sensors_layout == HexitecFem.READOUTMODE[1]:
            self.hexitec_camera.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
            
        if self.debug:
            logging.debug("number of Frames := %s" % self.number_of_frames)

        logging.debug("Initiate Data Capture")
        self.hexitec_camera.data_stream(self.number_of_frames)
        #
        waited = 0.0
        delay = 0.10
        resp = 0
        while resp < 1:
            resp = self.hexitec_camera.x10g_rdma.read(0x60000014, 'Check data transfer completed?')
            time.sleep(delay)
            waited += delay
            if (self.stop_acquisition):
                break
        logging.debug("Data Capture took " + str(waited) + " seconds")
        self._set_status_message("Requested %s frame(s), taking %s seconds" % (self.number_of_frames, str(waited)))

        # Stop the state machine
        self.hexitec_camera.x10g_rdma.write(0x60000002, 0, 'Dis-Enable State Machine')

        # Clear enable signal
        self.hexitec_camera.x10g_rdma.write(0xD0000000, 2, 'Clear enable signal')
        self.hexitec_camera.x10g_rdma.write(0xD0000000, 0, 'Clear enable signal')

        if (self.stop_acquisition):
            logging.error("Acquisition interrupted by User")
            self._set_status_message("User interrupted acquisition")
            self.stop_acquisition = False
            raise HexitecFemError("User interrupted")

        logging.debug("Acquisition Completed, enable signal cleared")
        
        # Clear the Mux Mode bit
        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.hexitec_camera.x10g_rdma.write(0x60000004, 0, 'Sensor 1 1')
            logging.debug("Sensor 1 1")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.hexitec_camera.x10g_rdma.write(0x60000004, 4, 'Sensor 2 1')
            logging.debug("Sensor 2 1") 
        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000011,  'Check EMPTY Signals')
        logging.debug("Check EMPTY Signals: %s" % full_empty)
        full_empty = self.hexitec_camera.x10g_rdma.read(0x60000012,  'Check FULL Signals')
        logging.debug("Check FULL Signals: %s" % full_empty)
        no_frames = self.hexitec_camera.x10g_rdma.read(0xD0000001,  'Check Number of Frames setting') + 1
        logging.debug("Number of Frames: %s" % no_frames)

        logging.debug("Output from Sensor")
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000010, 'frame last length')
        logging.debug("frame last length: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000011, 'frame max length')
        logging.debug("frame max length: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000012, 'frame min length')
        logging.debug("frame min length: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000013, 'frame number')
        logging.debug("frame number: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000014, 'frame last clock cycles')
        logging.debug("frame last clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000015, 'frame max clock cycles')
        logging.debug("frame max clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000016, 'frame min clock cycles')
        logging.debug("frame min clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000017, 'frame data total')
        logging.debug("frame data total: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000018, 'frame data total clock cycles')
        logging.debug("frame data total clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x70000019, 'frame trigger count')
        logging.debug("frame trigger count: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x7000001A, 'frame in progress flag')
        logging.debug("frame in progress flag: %s" % m0)

        logging.debug("Output from Frame Gate")
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000010, 'frame last length')
        logging.debug("frame last length: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000011, 'frame max length')
        logging.debug("frame max length: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000012, 'frame min length')
        logging.debug("frame min length: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000013, 'frame number')
        logging.debug("frame number: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000014, 'frame last clock cycles')
        logging.debug("frame last clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000015, 'frame max clock cycles')
        logging.debug("frame max clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000016, 'frame min clock cycles')
        logging.debug("frame min clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000017, 'frame data total')
        logging.debug("frame data total: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000018, 'frame data total clock cycles')
        logging.debug("frame data total clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x80000019, 'frame trigger count')
        logging.debug("frame trigger count: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x8000001A, 'frame in progress flag')
        logging.debug("frame in progress flag: %s" % m0)    
        
        logging.debug("Input to XAUI")
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000010, 'frame last length')
        logging.debug("frame last length: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000011, 'frame max length')
        logging.debug("frame max length: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000012, 'frame min length')
        logging.debug("frame min length: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000013, 'frame number')
        logging.debug("frame number: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000014, 'frame last clock cycles')
        logging.debug("frame last clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000015, 'frame max clock cycles')
        logging.debug("frame max clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000016, 'frame min clock cycles')
        logging.debug("frame min clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000017, 'frame data total')
        logging.debug("frame data total: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000018, 'frame data total clock cycles')
        logging.debug("frame data total clock cycles: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x90000019, 'frame trigger count')
        logging.debug("frame trigger count: %s" % m0)
        m0 = self.hexitec_camera.x10g_rdma.read(0x9000001A, 'frame in progress flag')
        logging.debug("frame in progress flag: %s" % m0)    

    def set_up_state_machine(self):
        logging.debug("Setting up state machine")
        #  Thes are used to set up the state machine
        sm_timing1  = [0x23, self.vsr_addr, 0x42, 0x30, 0x37, 0x30, 0x33, 0x0D ]
        sm_timing2  = [0x23, self.vsr_addr, 0x42, 0x30, 0x32, 0x30, 0x31, 0x0D ]
        sm_timing3  = [0x23, self.vsr_addr, 0x42, 0x30, 0x34, 0x30, 0x31, 0x0D ]
        sm_timing4  = [0x23, self.vsr_addr, 0x42, 0x30, 0x35, 0x30, 0x36, 0x0D ]
        sm_timing5  = [0x23, self.vsr_addr, 0x42, 0x30, 0x39, 0x30, 0x32, 0x0D ]
        sm_timing6  = [0x23, self.vsr_addr, 0x42, 0x30, 0x45, 0x30, 0x41, 0x0D ]
        sm_timing7  = [0x23, self.vsr_addr, 0x42, 0x31, 0x42, 0x30, 0x38, 0x0D ]
        sm_timing8  = [0x23, self.vsr_addr, 0x42, 0x31, 0x34, 0x30, 0x31, 0x0D ]
        
        self.send_cmd(sm_timing1)
        self.read_response()
        self.send_cmd(sm_timing2)
        self.read_response()
        self.send_cmd(sm_timing3)
        self.read_response()
        self.send_cmd(sm_timing4)
        self.read_response()
        self.send_cmd(sm_timing5)
        self.read_response()
        self.send_cmd(sm_timing6)
        self.read_response()
        self.send_cmd(sm_timing7)
        self.read_response()
        self.send_cmd(sm_timing8)
        self.read_response()

        #  Try setting vcal2 -> VCAL1 21/01/2019
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x31, 0x38, 0x30, 0x31, 0x0D])
        self.read_response()

        logging.debug("Finished Setting up state machine")

    def collect_offsets(self):

        print "HexitecFem is deffo gonna collect offsets (Watch this space)"
        
    def load_pwr_cal_read_enables(self):
        enable_sm     = [0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31, 0x0D]
        disable_sm    = [0x23, self.vsr_addr, 0x43, 0x30, 0x31, 0x30, 0x31, 0x0D]
        diff_cal      = [0x23, self.vsr_addr, 0x42, 0x38, 0x46, 0x30, 0x31, 0x0D]
        
        col_read_enable1   = [0x23, self.vsr_addr, 0x44, 0x36, 0x31, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        col_read_enable2   = [0x23, self.vsr_addr, 0x44, 0x43, 0x32, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        col_power_enable1  = [0x23, self.vsr_addr, 0x44, 0x34, 0x44, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        col_power_enable2  = [0x23, self.vsr_addr, 0x44, 0x41, 0x45, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        
        #col_cal_enable1    = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
        #col_cal_enable2    = [0x23, self.vsr_addr, 0x44, 0x42, 0x38, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
        #col_cal_enable1a    = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x30, 0x30, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
        #col_cal_enable1a    = [0x23, self.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
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

        row_read_enable1   = [0x23, self.vsr_addr, 0x44, 0x34, 0x33, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        row_read_enable2   = [0x23, self.vsr_addr, 0x44, 0x41, 0x34, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        row_power_enable1  = [0x23, self.vsr_addr, 0x44, 0x32, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        row_power_enable2  = [0x23, self.vsr_addr, 0x44, 0x39, 0x30, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
        
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
        self.send_cmd([0x23, self.vsr_addr, 0x54, 0x30, 0x32, 0x41, 0x41, 0x30, 0x35, 0x35, 0x35,
                       0x30, 0x35, 0x35, 0x35, 0x30, 0x30, 0x30, 0x30, 0x30, 0x38, 0x45, 0x38, 0x0D])
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
            self.send_cmd([0x23, 0x90, 0x53, 0x31, 0x42, 0x46, 0x37, 0x0d])
            self.read_response()
            self.send_cmd([0x23, 0x90, 0x53, 0x31, 0x43, 0x33, 0x46, 0x0d])
            self.read_response()
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[3]:
            # 0x3BFF - Word 2
            self.send_cmd([0x23, 0x90, 0x53, 0x31, 0x42, 0x46, 0x46, 0x0d])
            self.read_response()
            self.send_cmd([0x23, 0x90, 0x53, 0x31, 0x43, 0x33, 0x42, 0x0d])
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
        logging.debug("Synchronised: %s" % synced_status)  # Saying it's 15..

        self._set_status_message("Initialisation completed. VSR2 and VS1 configured.");
        

class HexitecFemError(Exception):
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass
    
