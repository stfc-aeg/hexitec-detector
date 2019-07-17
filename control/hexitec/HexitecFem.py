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


class HexitecFem():
    """ Hexitec Fem class. Represents a single FEM-II module.
    
    Controls and configures each FEM-II module ready for a DAQ via UDP.
    """
    thread_executor = futures.ThreadPoolExecutor(max_workers=1)

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

    SETCLR = [
    "SET",
    "CLEAR"
    ] #etc

    REGADDRMSB = [
    "0x0",
    "0x1",
    "0x2",
    "0x3",
    "0x4",
    "0x5",
    "0x6",
    "0x7",
    "0x8",
    "0x9",
    "0xA",
    "0xB",
    "0xC",
    "0xD",
    "0xE",
    "0xF"]

    REGADDRLSB = [
    "0x0",
    "0x1",
    "0x2",
    "0x3",
    "0x4",
    "0x5",
    "0x6",
    "0x7",
    "0x8",
    "0x9",
    "0xA",
    "0xB",
    "0xC",
    "0xD",
    "0xE",
    "0xF"]

    BITVALUE = [
    "Bit0",
    "Bit1",
    "Bit2",
    "Bit3",
    "Bit4",
    "Bit5",
    "Bit6",
    "Bit7"]

    DARKCORRECTION = [
    "DARK CORRECTION OFF",
    "DARK CORRECTION ON"]

    READOUTMODE = [
    "SINGLE",
    "2x2"]



    def __init__(self, ip_address='127.0.0.1', port=1232, fem_id=1,
                server_ctrl_ip_addr='10.0.2.2', camera_ctrl_ip_addr='10.0.2.1',
                server_data_ip_addr='10.0.4.2', camera_data_ip_addr='10.0.4.1'):

        self.ip_address = ip_address
        self.port = port
        self.id = int(fem_id)
        self.qemcamera = QemCam()

        # 10G RDMA IP addresses      
        self.qemcamera.server_ctrl_ip_addr = server_ctrl_ip_addr    #'10.0.2.2'
        self.qemcamera.camera_ctrl_ip_addr = camera_ctrl_ip_addr    #'10.0.2.1'

        # 10G image stream Ip addresses
        self.qemcamera.server_data_ip_addr = server_data_ip_addr    #"10.0.4.2"
        self.qemcamera.camera_data_ip_addr = camera_data_ip_addr    #"10.0.4.1"

        self.vsr_addr = 0x90

        self.number_of_frames = 10

        self.hardware_connected = False

        self.debug = False

        param_tree_dict = {
            "ip_addr": (self.get_address, None),    # Replicated, not needed going forwards?
            "port": (self.get_port, None),          # Replicated, not needed going forwards?
            "id": (self.id, None),
            "connect_hardware": (None, self.connect_hardware),
            "initialise_hardware": (None, self.initialise_hardware),
            "collect_data": (None, self.collect_data),
            "disconnect_hardware": (None, self.disconnect_hardware),
            "debug": (self.get_debug, self.set_debug)
        }

        self.param_tree = ParameterTree(param_tree_dict)
        
        self.selected_sensor = HexitecFem.OPTIONS[2]        # "Sensor_2_1"; Replaces variable1
        self.sensors_layout     = HexitecFem.READOUTMODE[1]    # "2x2";        Replaces variable8
        self.output_format      = HexitecFem.IMAGE[3]       # "WireShark"
        self.set_clear          = HexitecFem.SETCLR[0]      # "SET";            Replaces variable3
        self.register_address_msb   = HexitecFem.REGADDRMSB[2]  # "0x2";            Replaces variable4
        self.register_address_lsb   = HexitecFem.REGADDRLSB[4]  # "0x4";            Replaces variable5
        self.bit_value          = HexitecFem.BITVALUE[0]    # "Bit0";           Replaces variable6
        self.dark_correction    = HexitecFem.DARKCORRECTION[0]  # "DARK CORRECTION OFF";    Replaces variable7
        self.test_mode_image    = HexitecFem.TESTMODEIMAGE[3]   # "IMAGE 4";               Replaces variable9

        #TODO: Sort out filename properly
        self.filename = '/tmp/Hexitec'+ datetime.datetime.now().strftime("%b_%d_%H%M%S_")

    ''' Accessor functions '''

    def get_address(self):
        return self.ip_address

    def get_port(self):
        return self.port

    def connect_hardware(self, msg):
        if self.hardware_connected:
            raise ParameterTreeError("Connection already established")
        try:
            self.cam_connect()
            self.hardware_connected = True
        except Exception as e:
            raise ParameterTreeError("Failed to connect with camera: %s" % e)

    def initialise_hardware(self, msg):
        if self.hardware_connected != True:
            raise ParameterTreeError("No connection established")
        try:
            self.initialise_system()
        except HexitecFemError as e:
            raise ParameterTreeError("Failed to initialise camera: %s" % e)
        except Exception:
            raise ParameterTreeError("Failed to initialise Camera")

    def collect_data(self, msg):
        if self.hardware_connected != True:
            raise ParameterTreeError("No connection established")
        try:
            self.acquire_data()
        except Exception:
            raise ParameterTreeError("Failed to collect data")
        
    def disconnect_hardware(self, msg):
        if self.hardware_connected == False:
            raise ParameterTreeError("No connection to disconnect")
        try:
            self.cam_disconnect()
            self.hardware_connected = False
        except Exception:
            raise ParameterTreeError("Disconnection failed")
        
 
    def set_debug(self, debug):
        self.debug = debug

    def get_debug(self):
        return self.debug

    #  This function sends a command string to the microcontroller
    def send_cmd(self, cmd):

        while len(cmd)%4 != 0:
            cmd.append(13)
        if self.debug: print "Length of command - " , len(cmd) , len(cmd)%4      
        #print cmd
        for i in range ( 0 , len(cmd)/4 ):

            #print format(cmd[(i*4)+3], '02x') , format(cmd[(i*4)+2], '02x') , format(cmd[(i*4)+1], '02x') , format(cmd[(i*4)], '02x') 
            #reg_value = 256*256*256*cmd[(i*4)+3] + 256*256*cmd[(i*4)+2] + 256*cmd[(i*4)+1] + cmd[(i*4)] 
            reg_value = 256*256*256*cmd[(i*4)] + 256*256*cmd[(i*4)+1] + 256*cmd[(i*4)+2] + cmd[(i*4)+3] 
            #print reg_value
            #print format(reg_value, '08x')
            self.qemcamera.x10g_rdma.write(0xE0000100, reg_value, 'Write 4 Bytes')
            time.sleep(0.25)


    #TODO: Remove if no use for this function:
    #  This function will display the returned voltages returned by the 0x50 instruction    
    def display_voltages(self, f):
        #print len(f)
        for i in range(1, len(f)-2, 4):
            s = 0
            s = s + self.get_dec(f[i+3]) + self.get_dec(f[i+2])*16 + self.get_dec(f[i+1])*256 + self.get_dec(f[i])*4096
            j = (i-2)/4+1
            if j == 9:
                print "Voltage %.d %.2f" %(j+1, s*2.048/4096)
            else:
                print "Voltage %.d %.2f" %(j+1, s*3.3/4096)

    #  Simple function to return the decimal value of a number in ASCII (0-9, A-F)                       
    def get_dec(self, a):
        r = 0
        if a >= 48:
            if a <= 57:
                r = a - 48
            if a > 57:
                r = a - 55
        return(r)
    
    # Displays the returned response from the microcontroller    
    def read_response(self):
        data_counter = 0
        f = []
        #f.append(dat)
        ABORT_VALUE = 10000
        RETURN_START_CHR = 42
        CARRIAGE_RTN = 13
        FIFO_EMPTY_FLAG = 1
        empty_count = 0
        daty = RETURN_START_CHR
        
        while daty != CARRIAGE_RTN :
            fifo_empty = FIFO_EMPTY_FLAG

            while fifo_empty == FIFO_EMPTY_FLAG and empty_count < ABORT_VALUE:
                #time.sleep(0.5)
                fifo_empty = self.qemcamera.x10g_rdma.read(0xE0000011, 'FIFO EMPTY FLAG')
                #fifo_empty = 0
                #rint "FIFO Empty" , fifo_empty , empty_count
                empty_count = empty_count + 1
            if self.debug: print "Got data:- " 
            dat = self.qemcamera.x10g_rdma.read(0xE0000200, 'Data')
            if self.debug: print "Bytes are:- " 
            daty = dat/256/256/256%256
            f.append(daty)
            if self.debug: print format(daty, '02x')
            daty = dat/256/256%256
            f.append(daty)
            if self.debug: print format(daty, '02x')
            daty = dat/256%256
            f.append(daty)
            if self.debug: print format(daty, '02x')
            daty = dat%256
            f.append(daty)
            if self.debug: print format(daty, '02x')
            data_counter = data_counter + 1
            if empty_count == ABORT_VALUE:
                print "Abort"
                daty = CARRIAGE_RTN
                raise HexitecFemError("read_response aborted")
            empty_count = 0          

        if self.debug: print "Counter is :- " , data_counter 
        if self.debug: print "Length is:-" , len(f)
        fifo_empty = self.qemcamera.x10g_rdma.read(0xE0000011, 'Data')
        if self.debug: print "FIFO should be empty " , fifo_empty    
        s = ''

        for i in range( 1 , data_counter*4):
            if self.debug: print i
            s = s + chr(f[i])
        
        if self.debug: 
            print "String :- " , s
            print f[0] 
            print f[1]
        
        return(s)

    def cam_connect(self):
        
        logging.debug("! cam_connect() ! LINKS NOT LOCKED")
        try:
            self.qemcamera.connect()
            print ("Camera is connected")
            self.send_cmd([0x23, 0x90, 0xE3, 0x0D])
            time.sleep(1)
            self.send_cmd([0x23, 0x91, 0xE3, 0x0D])
            print "Enable modules"
        except socket_error as e:
            logging.error("%s", e)
            # logging.error("Attemped on ")
        except Exception as e:
            raise Exception(e)


    def cam_disconnect(self):
        try:
            self.send_cmd([0x23, 0x90, 0xE2, 0x0D])
            self.send_cmd([0x23, 0x91, 0xE2, 0x0D])
            print "Modules Disabled"
            self.qemcamera.disconnect()
            print ("Camera is Disconnected")
        except socket_error as e:
            logging.error("Unable to disconnect camer: %s", e)
        except AttributeError as e:
            logging.error("Unable to disconnect camera: %s", "No active connection")

    def initialise_sensor(self):
        logging.debug("! initialise_sensor() ! LINKS NOT LOCKED")

        self.qemcamera.x10g_rdma.write(0x60000002, 0, 'Disable State Machine Trigger')
        print "Disable State Machine Enabling signal"
            
        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.qemcamera.x10g_rdma.write(0x60000004, 0, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 1_1')
            print ("VSR_1")
            self.vsr_addr = 0x90
        if self.selected_sensor == HexitecFem.OPTIONS[1]:
            self.qemcamera.x10g_rdma.write(0x60000004, 2, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 1_2')
            print ("VSR_1")
            self.vsr_addr = 0x90
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.qemcamera.x10g_rdma.write(0x60000004, 4, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 2_1')
            print ("VSR 2")
            self.vsr_addr = 0x91  
        if self.selected_sensor == HexitecFem.OPTIONS[3]:
            self.qemcamera.x10g_rdma.write(0x60000004, 6, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 2_2')
            print ("VSR 2")
            self.vsr_addr = 0x91          

        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            print "Disable synchronisation SM start"
            self.send_cmd([0x23, self.vsr_addr, 0x40, 0x30, 0x41, 0x30, 0x30, 0x0D])
            self.read_response()
            print ("Reading out single sensor")
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            # Need to set up triggering MODE here
            # Enable synchronisation SM start via trigger 1
            print "Enable synchronisation SM start via trigger 1"
            self.send_cmd([0x23, self.vsr_addr, 0x42, 0x30, 0x41, 0x30, 0x31, 0x0D])
            self.read_response()
            print ("Reading out 2x2 sensors")
        print self.selected_sensor    

        print "Communicating with - ", self.vsr_addr
        # Set Frame Gen Mux Frame Gate
        self.qemcamera.x10g_rdma.write(0x60000001, 2, 'Set Frame Gen Mux Frame Gate - works set to 2')
        #Followinbg line is important
        self.qemcamera.x10g_rdma.write(0xD0000001, self.number_of_frames-1, 'Frame Gate set to self.number_of_frames')
        
        # Send this command to Enable Test Pattern in my VSR design
        print "Setting Number of Frames to ", self.number_of_frames
        print "Enable Test Pattern in my VSR design"
        # Use Sync clock from DAQ board
        print "Use Sync clock from DAQ board"
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x31, 0x30, 0x0D])
        self.read_response()
        print "Enable LVDS outputs"
        set_register_vsr1_command  = [0x23, 0x90, 0x42, 0x30, 0x31, 0x32, 0x30, 0x0D]
        set_register_vsr2_command  = [0x23, 0x91, 0x42, 0x30, 0x31, 0x32, 0x30, 0x0D]
        self.send_cmd(set_register_vsr1_command)
        self.read_response()
        self.send_cmd(set_register_vsr2_command)
        self.read_response()
        print "LVDS outputs enabled"
        print "Read LO IDLE"
        self.send_cmd([0x23, self.vsr_addr, 0x40, 0x46, 0x45, 0x41, 0x41, 0x0D])
        self.read_response()
        print "Read HI IDLE"
        self.send_cmd([0x23, self.vsr_addr, 0x40, 0x46, 0x46, 0x4E, 0x41, 0x0D])
        self.read_response()
        # This sets up test pattern on LVDS outputs
        print "Set up LVDS test pattern"
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x30, 0x31, 0x43, 0x30, 0x0D])
        self.read_response()
        # Use default test pattern of 1000000000000000
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x38, 0x30, 0x0D])
        self.read_response()
        
        full_empty = self.qemcamera.x10g_rdma.read(0x60000011,  'Check EMPTY Signals')
        print "Check EMPTY Signals", full_empty
        full_empty = self.qemcamera.x10g_rdma.read(0x60000012,  'Check FULL Signals')
        print "Check FULL Signals", full_empty
    
    def calibrate_sensor(self):
        logging.debug("! calibrate_sensor() ! LINKS NOT LOCKED")
        print "setting image size"
        # 80x80 pixels 14 bits
        #self.qemcamera.set_image_size(80,80,14,16)

        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            print ("Reading out single sensor")
            self.qemcamera.set_image_size(80,80,14,16)
            mux_mode = 0
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            #self.qemcamera.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
            mux_mode = 8
            self.qemcamera.set_image_size(160,160,14,16)
            print ("Reading out 2x2 sensors")

        # Set VCAL
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x31, 0x38, 0x30, 0x31, 0x0D])
        self.read_response()
        print "Clear bit 5"
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x32, 0x30, 0x0D])
        self.read_response()
    
        # Set bit 4 of Reg24
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x31, 0x30, 0x0D])
        self.read_response()
        
        print "Set bit 6"
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x34, 0x30, 0x0D])
        self.read_response()
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x30, 0x31, 0x0D])
        self.read_response()
        self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x32, 0x32, 0x0D])
        self.read_response()

        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.qemcamera.x10g_rdma.write(0x60000002, 1, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            print ("CALIBRATING VSR_1")    
        if self.selected_sensor == HexitecFem.OPTIONS[1]:
            self.qemcamera.x10g_rdma.write(0x60000002, 1, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            print ("CALIBRATING VSR_1")    
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.qemcamera.x10g_rdma.write(0x60000002, 2, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            print ("CALIBRATING VSR_2")  
        if self.selected_sensor == HexitecFem.OPTIONS[3]:
            self.qemcamera.x10g_rdma.write(0x60000002, 2, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
            print ("CALIBRATING VSR_2")  
            
        # Send command on CMD channel to FEMII
        #self.qemcamera.x10g_rdma.write(0x60000002, 3, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
        self.qemcamera.x10g_rdma.write(0x60000002, 0, 'Un-Trigger Cal process')

        # Reading back Sync register
        synced = self.qemcamera.x10g_rdma.read(0x60000010,  'Check LVDS has synced')
        print "Sync Register value"

        full_empty = self.qemcamera.x10g_rdma.read(0x60000011,  'Check FULL EMPTY Signals')
        print "Check EMPTY Signals", full_empty

        full_empty = self.qemcamera.x10g_rdma.read(0x60000012,  'Check FULL FULL Signals')
        print "Check FULL Signals", full_empty
        
        # Check whether the currently selected VSR has synchronised or not
        if synced == 15:
            print "All Links on VSR's 1 and 2 synchronised"
            logging.debug("! calibrate_sensor() ! ALL LINKS ON VSR'S 1 AND 2 SYNCHRONISED")
            #self.qemcamera.x10g_rdma.write(0x60000002, 4, 'Enable state machines in VSRs ')
            print ("Starting State Machine in VSR's")  
        elif synced == 12:
            print "Both Links on VSR 2 synchronised"
            logging.debug("! calibrate_sensor() ! BOTH LINKS ON VSR 2 SYNCHRONISED")
        elif synced == 3:
            print "Both Links on VSR 1 synchronised"
            logging.debug("! calibrate_sensor() ! BOTH LINKS ON VSR 1 SYNCHRONISED")
        else:
            print synced        

        # Send this command to Disable Test Pattern in my VSR design
        self.send_cmd([0x23, 0x92, 0x00, 0x0D])
        
        # Clear training enable
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x30, 0x31, 0x43, 0x30, 0x0D])
        self.read_response()

        print "Clear bit 5 - VCAL ENABLED"
        self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x32, 0x30, 0x0D])
        self.read_response()

        if self.dark_correction == HexitecFem.DARKCORRECTION[0]:
            #  Log image to file
            print "DARK CORRECTION OFF"
            self.send_cmd([0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x30, 0x38, 0x0D])
            self.read_response()
        elif self.dark_correction == HexitecFem.DARKCORRECTION[1]:
            #  Log image to file
            print "DARK CORRECTION ON"
            self.send_cmd([0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x30, 0x38, 0x0D])    
            self.read_response()
        
        # Read Reg24
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x32, 0x34,  0x0D])
        if self.debug: print "reading Register 0x24"
        if self.debug: print self.read_response()
        
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x38, 0x39,  0x0D])
        self.read_response()
        
        time.sleep(3)
        
        if self.debug: print "Poll register 0x89"
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x38, 0x39,  0x0D])
        r = self.read_response()
        if self.debug: print "Bit 1 should be 1" 
        if self.debug: print r
        if self.debug: print "Read reg 1"
        self.send_cmd([0x23, self.vsr_addr, 0x41, 0x30, 0x31,  0x0D])
        self.read_response()

        full_empty = self.qemcamera.x10g_rdma.read(0x60000011,  'Check FULL EMPTY Signals')
        print "Check EMPTY Signals", full_empty

        full_empty = self.qemcamera.x10g_rdma.read(0x60000012,  'Check FULL FULL Signals')
        print "Check FULL Signals", full_empty

        return synced
 
    def acquire_data(self):
        
        full_empty = self.qemcamera.x10g_rdma.read(0x60000011,  'Check FULL EMPTY Signals')
        print "Check EMPTY Signals", full_empty

        full_empty = self.qemcamera.x10g_rdma.read(0x60000012,  'Check FULL FULL Signals')
        print "Check FULL Signals", full_empty
        
        if self.sensors_layout == HexitecFem.READOUTMODE[0]:
            print ("Reading out single sensor")
            mux_mode = 0
        elif self.sensors_layout == HexitecFem.READOUTMODE[1]:
            #self.qemcamera.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
            mux_mode = 8
            print ("Reading out 2x2 sensors")
            
        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.qemcamera.x10g_rdma.write(0x60000004, 0 + mux_mode, 'Sensor 1 1')
            print ("Sensor 1 1")
        if self.selected_sensor == HexitecFem.OPTIONS[1]:
            self.qemcamera.x10g_rdma.write(0x60000004, 2 + mux_mode, 'Sensor 1 2')
            print ("Sensor 1 2")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.qemcamera.x10g_rdma.write(0x60000004, 4 + mux_mode, 'Sensor 2 1')
            print ("Sensor 2 1") 
        if self.selected_sensor == HexitecFem.OPTIONS[3]:
            self.qemcamera.x10g_rdma.write(0x60000004, 6 + mux_mode, 'Sensor 2 2')
            print ("Sensor 2 2")
            
        # Flush the input FIFO buffers
        self.qemcamera.x10g_rdma.write(0x60000002, 32, 'Clear Input Buffers')
        self.qemcamera.x10g_rdma.write(0x60000002, 0, 'Clear Input Buffers')
        time.sleep(1)
        full_empty = self.qemcamera.x10g_rdma.read(0x60000011,  'Check EMPTY Signals')
        print "Check EMPTY Signals", full_empty
        full_empty = self.qemcamera.x10g_rdma.read(0x60000012,  'Check FULL Signals')
        print "Check FULL Signals", full_empty
        
        if self.sensors_layout == HexitecFem.READOUTMODE[1]:
            self.qemcamera.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
            
        # file_string = '/tmp/Hexitec'+ datetime.datetime.now().strftime("%b_%d_%H%M%S_") + self.selected_sensor + '_' + inputValue
        file_string = self.filename
        if self.debug:
            print file_string 
            print "number of Frames :=", self.number_of_frames
        
        if self.output_format == HexitecFem.IMAGE[0]:
            #  Log image to file
            print "Logging Image to HDF5 file"
            self.qemcamera.log_image_stream(file_string, self.number_of_frames)  
        if self.output_format == HexitecFem.IMAGE[1]:
            #  Log image to file
            print "Logging Image to BIN file"
            self.qemcamera.log_image_stream_bin(file_string, self.number_of_frames)  
        if self.output_format == HexitecFem.IMAGE[2]:
            #  Stream image 
            print "Streaming Image - THIS OPTION HAS BEEN DISABLED;\n\t\t use the /test_ui/ scripts instead"
            self.qemcamera.display_image_stream(self.number_of_frames)
        if self.output_format == HexitecFem.IMAGE[3]:
            #  Data Capture only
            print "Data Capture on Wireshark only - no image"
            self.qemcamera.data_stream(self.number_of_frames)  
            print "Wait 5 seconds"
            time.sleep(5)
            print "Waited 5 seconds"
            
        # Stop the state machine
        self.qemcamera.x10g_rdma.write(0x60000002, 0, 'Dis-Enable State Machine')
        
        print "Acquisition Complete, clear enable signal"    
        self.qemcamera.x10g_rdma.write(0xD0000000, 2, 'Clear enable signal')
        self.qemcamera.x10g_rdma.write(0xD0000000, 0, 'Clear enable signal')
        
        # Clear the Mux Mode bit
        if self.selected_sensor == HexitecFem.OPTIONS[0]:
            self.qemcamera.x10g_rdma.write(0x60000004, 0, 'Sensor 1 1')
            print ("Sensor 1 1")
        if self.selected_sensor == HexitecFem.OPTIONS[1]:
            self.qemcamera.x10g_rdma.write(0x60000004, 2, 'Sensor 1 2')
            print ("Sensor 1 2")
        if self.selected_sensor == HexitecFem.OPTIONS[2]:
            self.qemcamera.x10g_rdma.write(0x60000004, 4, 'Sensor 2 1')
            print ("Sensor 2 1") 
        if self.selected_sensor == HexitecFem.OPTIONS[3]:
            self.qemcamera.x10g_rdma.write(0x60000004, 6, 'Sensor 2 2')
            print ("Sensor 2 2")
        full_empty = self.qemcamera.x10g_rdma.read(0x60000011,  'Check EMPTY Signals')
        print "Check EMPTY Signals", full_empty
        full_empty = self.qemcamera.x10g_rdma.read(0x60000012,  'Check FULL Signals')
        print "Check FULL Signals", full_empty
        no_frames = self.qemcamera.x10g_rdma.read(0xD0000001,  'Check Number of Frames setting') + 1
        print "Number of Frames", no_frames

        print "Output from Sensor" 
        m0 = self.qemcamera.x10g_rdma.read(0x70000010, 'frame last length')
        print "frame last length", m0
        m0 = self.qemcamera.x10g_rdma.read(0x70000011, 'frame max length')
        print "frame max length", m0
        m0 = self.qemcamera.x10g_rdma.read(0x70000012, 'frame min length')
        print "frame min length", m0
        m0 = self.qemcamera.x10g_rdma.read(0x70000013, 'frame number')
        print "frame number", m0
        m0 = self.qemcamera.x10g_rdma.read(0x70000014, 'frame last clock cycles')
        print "frame last clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x70000015, 'frame max clock cycles')
        print "frame max clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x70000016, 'frame min clock cycles')
        print "frame min clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x70000017, 'frame data total')
        print "frame data total", m0
        m0 = self.qemcamera.x10g_rdma.read(0x70000018, 'frame data total clock cycles')
        print "frame data total clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x70000019, 'frame trigger count')
        print "frame trigger count", m0
        m0 = self.qemcamera.x10g_rdma.read(0x7000001A, 'frame in progress flag')
        print "frame in progress flag", m0

        print "Output from Frame Gate" 
        m0 = self.qemcamera.x10g_rdma.read(0x80000010, 'frame last length')
        print "frame last length", m0
        m0 = self.qemcamera.x10g_rdma.read(0x80000011, 'frame max length')
        print "frame max length", m0
        m0 = self.qemcamera.x10g_rdma.read(0x80000012, 'frame min length')
        print "frame min length", m0
        m0 = self.qemcamera.x10g_rdma.read(0x80000013, 'frame number')
        print "frame number", m0
        m0 = self.qemcamera.x10g_rdma.read(0x80000014, 'frame last clock cycles')
        print "frame last clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x80000015, 'frame max clock cycles')
        print "frame max clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x80000016, 'frame min clock cycles')
        print "frame min clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x80000017, 'frame data total')
        print "frame data total", m0
        m0 = self.qemcamera.x10g_rdma.read(0x80000018, 'frame data total clock cycles')
        print "frame data total clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x80000019, 'frame trigger count')
        print "frame trigger count", m0
        m0 = self.qemcamera.x10g_rdma.read(0x8000001A, 'frame in progress flag')
        print "frame in progress flag", m0    
        
        print "Input to XAUI" 
        m0 = self.qemcamera.x10g_rdma.read(0x90000010, 'frame last length')
        print "frame last length", m0
        m0 = self.qemcamera.x10g_rdma.read(0x90000011, 'frame max length')
        print "frame max length", m0
        m0 = self.qemcamera.x10g_rdma.read(0x90000012, 'frame min length')
        print "frame min length", m0
        m0 = self.qemcamera.x10g_rdma.read(0x90000013, 'frame number')
        print "frame number", m0
        m0 = self.qemcamera.x10g_rdma.read(0x90000014, 'frame last clock cycles')
        print "frame last clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x90000015, 'frame max clock cycles')
        print "frame max clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x90000016, 'frame min clock cycles')
        print "frame min clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x90000017, 'frame data total')
        print "frame data total", m0
        m0 = self.qemcamera.x10g_rdma.read(0x90000018, 'frame data total clock cycles')
        print "frame data total clock cycles", m0
        m0 = self.qemcamera.x10g_rdma.read(0x90000019, 'frame trigger count')
        print "frame trigger count", m0
        m0 = self.qemcamera.x10g_rdma.read(0x9000001A, 'frame in progress flag')
        print "frame in progress flag", m0    

    def set_up_state_machine(self):
        print "Setting up state machine"
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

        print "Finished Setting up state machine"
    
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

        print "Use different CAL data"  
        self.send_cmd(diff_cal)
        self.read_response()

        self.send_cmd(disable_sm)
        self.read_response()

        print "Loading Power, Cal and Read Enables"    
        print "Column power enable"
        self.send_cmd(col_power_enable1)
        self.read_response()
        self.send_cmd(col_power_enable2)
        self.read_response()

        print "Row power enable"
        self.send_cmd(row_power_enable1)
        self.read_response()
        self.send_cmd(row_power_enable2)
        self.read_response()

        if self.test_mode_image == HexitecFem.TESTMODEIMAGE[0]:    
            print "Column cal enable A"
            self.send_cmd(col_cal_enable1a)
            self.read_response()
            self.send_cmd(col_cal_enable2a)
            self.read_response()
            print "Row cal enable A"
            self.send_cmd(row_cal_enable1a)
            self.read_response()
            self.send_cmd(row_cal_enable2a)
            self.read_response()
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[1]:
            print "Column cal enable B"
            self.send_cmd(col_cal_enable1b)
            self.read_response()
            self.send_cmd(col_cal_enable2b)
            self.read_response()
            print "Row cal enable B"
            self.send_cmd(row_cal_enable1b)
            self.read_response()
            self.send_cmd(row_cal_enable2b)
            self.read_response()
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[2]:
            print "Column cal enable C"
            self.send_cmd(col_cal_enable1c)
            self.read_response()
            self.send_cmd(col_cal_enable2c)
            self.read_response()
            print "Row cal enable C"
            self.send_cmd(row_cal_enable1c)
            self.read_response()
            self.send_cmd(row_cal_enable2c)
            self.read_response()
        elif self.test_mode_image == HexitecFem.TESTMODEIMAGE[3]:
            print "Column cal enable D"
            self.send_cmd(col_cal_enable1d)
            self.read_response()
            self.send_cmd(col_cal_enable2d)
            self.read_response()
            print "Row cal enable D"
            self.send_cmd(row_cal_enable1d)
            self.read_response()
            self.send_cmd(row_cal_enable2d)
            self.read_response()
            
        print "Column read enable"
        self.send_cmd(col_read_enable1)
        self.read_response()
        self.send_cmd(col_read_enable2)
        self.read_response()
    
        print "Row read enable"
        self.send_cmd(row_read_enable1)
        self.read_response()
        self.send_cmd(row_read_enable2)
        self.read_response()

        print "Power, Cal and Read Enables have been loaded" 
        
        self.send_cmd(enable_sm)
        self.read_response()
        
    def write_dac_values(self):
        print "Writing DAC values"
        self.send_cmd([0x23, self.vsr_addr, 0x54, 0x30, 0x32, 0x41, 0x41, 0x30, 0x35, 0x35, 0x35,
                       0x30, 0x35, 0x35, 0x35, 0x30, 0x30, 0x30, 0x30, 0x30, 0x38, 0x45, 0x38, 0x0D])
        self.read_response()
        print "DAC values set"
        
    def enable_adc(self):
        print "Enabling ADC"
        adc_disable   = [0x23, self.vsr_addr, 0x55, 0x30, 0x32, 0x0D]
        enable_sm     = [0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31, 0x0D]
        adc_enable    = [0x23, self.vsr_addr, 0x55, 0x30, 0x33, 0x0D]
        adc_set       = [0x23, self.vsr_addr, 0x53, 0x31, 0x36, 0x30, 0x39, 0x0D]
        aqu1          = [0x23, self.vsr_addr, 0x40, 0x32, 0x34, 0x32, 0x32, 0x0D]
        aqu2          = [0x23, self.vsr_addr, 0x40, 0x32, 0x34, 0x32, 0x38, 0x0D]   
        
        self.send_cmd(adc_disable)
        self.read_response()
        print "Enable SM"
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
        print "Enabling ADC Testmode"   
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

    def modify_register(self):
        cmd_string = [0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x30, 0x31, 0x0D ]
        if self.set_clear == HexitecFem.SETCLR[0]:
            print "0x42"
            cmd_string[2] = 0x42
        elif self.set_clear == HexitecFem.SETCLR[1]:
            cmd_string[2] = 0x43
        if self.register_address_msb == HexitecFem.REGADDRMSB[0]:
            print "0x30"
            cmd_string[3] = 0x30            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[1]:
            print "0x31"
            cmd_string[3] = 0x31            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[2]:
            print "0x32"
            cmd_string[3] = 0x32            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[3]:
            print "0x33"
            cmd_string[3] = 0x33            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[4]:
            print "0x34"
            cmd_string[3] = 0x34            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[5]:
            print "0x35"
            cmd_string[3] = 0x35            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[6]:
            print "0x36"
            cmd_string[3] = 0x36            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[7]:
            print "0x37"
            cmd_string[3] = 0x37            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[8]:
            print "0x38"
            cmd_string[3] = 0x38            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[9]:
            print "0x39"
            cmd_string[3] = 0x39            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[10]:
            print "0x41"
            cmd_string[3] = 0x41            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[11]:
            print "0x42"
            cmd_string[3] = 0x42            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[12]:
            print "0x43"
            cmd_string[3] = 0x43            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[13]:
            print "0x44"
            cmd_string[3] = 0x44            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[14]:
            print "0x45"
            cmd_string[3] = 0x45            
        elif self.register_address_msb == HexitecFem.REGADDRMSB[15]:
            print "0x46"
            cmd_string[3] = 0x46  
            
        if self.register_address_lsb == HexitecFem.REGADDRLSB[0]:
            print "0x30"
            cmd_string[4] = 0x30
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[1]:
            print "0x31"
            cmd_string[4] = 0x31
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[2]:
            print "0x32"
            cmd_string[4] = 0x32
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[3]:
            print "0x33"
            cmd_string[4] = 0x33
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[4]:
            print "0x34"
            cmd_string[4] = 0x34
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[5]:
            print "0x35"
            cmd_string[4] = 0x35
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[6]:
            print "0x36"
            cmd_string[4] = 0x36
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[7]:
            print "0x37"
            cmd_string[4] = 0x37
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[8]:
            print "0x38"
            cmd_string[4] = 0x38
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[9]:
            print "0x39"
            cmd_string[4] = 0x39
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[10]:
            print "0x41"
            cmd_string[4] = 0x41
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[11]:
            print "0x42"
            cmd_string[4] = 0x42
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[12]:
            print "0x43"
            cmd_string[4] = 0x43
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[13]:
            print "0x44"
            cmd_string[4] = 0x44
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[14]:
            print "0x45"
            cmd_string[4] = 0x45
        elif self.register_address_lsb == HexitecFem.REGADDRLSB[15]:
            print "0x46"
            cmd_string[4] = 0x46

        if self.bit_value == HexitecFem.BITVALUE[0]:
            print "0x30"
            print "0x31"
            cmd_string[5] = 0x30
            cmd_string[6] = 0x31
        elif self.bit_value == HexitecFem.BITVALUE[1]:
            print "0x30"
            print "0x32"
            cmd_string[5] = 0x30
            cmd_string[6] = 0x32
        elif self.bit_value == HexitecFem.BITVALUE[2]:
            print "0x30"
            print "0x34"
            cmd_string[5] = 0x30
            cmd_string[6] = 0x34
        elif self.bit_value == HexitecFem.BITVALUE[3]:
            print "0x30"
            print "0x38"
            cmd_string[5] = 0x30
            cmd_string[6] = 0x38
        elif self.bit_value == HexitecFem.BITVALUE[4]:
            print "0x31"
            print "0x30"
            cmd_string[5] = 0x31
            cmd_string[6] = 0x30
        elif self.bit_value == HexitecFem.BITVALUE[5]:
            print "0x32"
            print "0x30"
            cmd_string[5] = 0x32
            cmd_string[6] = 0x30
        elif self.bit_value == HexitecFem.BITVALUE[6]:
            print "0x34"
            print "0x30"
            cmd_string[5] = 0x34
            cmd_string[6] = 0x30
        elif self.bit_value == HexitecFem.BITVALUE[7]:
            print "0x38"
            print "0x30"
            cmd_string[5] = 0x38
            cmd_string[6] = 0x30
        print cmd_string
        self.send_cmd(cmd_string)
        ret = self.read_response()
        print ret

    #TODO: Only called by load_image(), so redundant if that f is removed?
    def pixel_value_array(self, my_list = []):
        if my_list[3] < 57:
            my_list[3] = my_list[3] + 1
        elif my_list[3] == 57:
            my_list[3] = 65
        elif  my_list[3] < 70:
            my_list[3] = my_list[3] + 1  
        elif my_list[3] == 70:
            my_list[3] = 48

            if my_list[2] < 57:
                my_list[2] = my_list[2] + 1
            elif my_list[2] == 57:
                my_list[2] = 65
            elif  my_list[2] < 70:
                my_list[2] = my_list[2] + 1  
            elif my_list[2] == 70:
                my_list[2] = 48
                
                if my_list[1] < 57:
                    my_list[1] = my_list[1] + 1
                elif my_list[1] == 57:
                    my_list[1] = 65
                elif  my_list[1] < 70:
                    my_list[1] = my_list[1] + 1  
                elif my_list[1] == 70:
                    my_list[1] = 48
                            
                    if my_list[0] < 57:
                        my_list[0] = my_list[0] + 1
                    elif my_list[0] == 57:
                        my_list[0] = 65
                    elif  my_list[0] < 70:
                        my_list[0] = my_list[0] + 1  
                    elif my_list[0] == 70:
                        my_list[0] = 48                
                
        return my_list
 
    #TODO: Is redundant and can be removed?
    def load_image(self):
        data_input_array = [0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x30, 0x31,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x30, 0x32,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x30, 0x34,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x30, 0x38,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x31, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x32, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x34, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x38, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x31, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x32, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x34, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x38, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x31, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x32, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x34, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x33, 0x46, 0x30, 0x30, 0x30, 0x30]
    
        disable_sm      = [0x23, self.vsr_addr, 0x43, 0x30, 0x31, 0x30, 0x31, 0x0D]
        clr_b1_reg24    = [0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x30, 0x32, 0x0D]
        set_b0_reg24    = [0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x30, 0x31, 0x0D]
        enable_sm       = [0x23, self.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31, 0x0D]
        clr_b0_reg24    = [0x23, self.vsr_addr, 0x43, 0x32, 0x34, 0x30, 0x31, 0x0D]
        set_b4_reg24    = [0x23, self.vsr_addr, 0x42, 0x32, 0x34, 0x31, 0x30, 0x0D]
        
        self.send_cmd(disable_sm)
        self.read_response()
        self.send_cmd(clr_b1_reg24)
        self.read_response()
        self.send_cmd(set_b0_reg24)
        self.read_response()
        self.send_cmd(enable_sm)
        self.read_response()
        
        pixel_value = [0x30, 0x30, 0x30, 0x30]
        cmd_string  = [0x23, self.vsr_addr, 0x46, 0x32, 0x38, 0x32, 0x35, 0x30, 0x30, 0x32,
                       0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32,
                       0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32,
                       0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32,
                       0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32,
                       0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32,
                       0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32,
                       0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32,
                       0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32,
                       0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32,
                       0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32,
                       0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32,
                       0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32,
                       0x36, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x32, 0x36, 0x30, 0x30, 0x0D]

        if self.debug: print len(cmd_string)
        for x in range(0,2):
            if self.debug: print x
            for y in range (0,20):
                # This loads in image data from array
                cmd_string[(y*8)+7] = data_input_array[(y*4)+(x*80)+2]
                cmd_string[(y*8)+8] = data_input_array[(y*4)+(x*80)+3]
                cmd_string[(y*8)+11] = data_input_array[(y*4)+(x*80)+0]
                cmd_string[(y*8)+12] = data_input_array[(y*4)+(x*80)+1]
                
                pixel_value =  self.pixel_value_array(pixel_value) 
            
            print "Sending Image Data Stream"
            print cmd_string

            self.send_cmd(cmd_string)
            ret = self.read_response()
            if self.debug: print ret 
        
        print "set / reset bits"
        self.send_cmd(disable_sm)
        self.read_response()
        self.send_cmd(clr_b0_reg24)
        self.read_response()
        self.send_cmd(set_b4_reg24)
        self.read_response()
        self.send_cmd(enable_sm)
        self.read_response()

    def initialise_system(self):
        # Does init, load, set up, write, enable, calibrate all in one fell swoooop
        #  for VSR2 followed by VSR1
        # try:
        print(" -=-=-=-=-=-=-=-=-  Setup System to config VSR 2.. -=-=-=-=-=-=-=-=- ")
        self.selected_sensor = HexitecFem.OPTIONS[2]
        print "selected_sensor: ", self.selected_sensor
        self.initialise_sensor()
        print(" -=-=-=-=- sensors initialised! -=-=-=-=- ")
        self.load_pwr_cal_read_enables()
        print(" -=-=-=-=- load power / calibrate / read / whatever / done! -=-=-=-=- ")
        self.set_up_state_machine()
        print(" -=-=-=-=- state machine set up! -=-=-=-=- ")
        self.write_dac_values()
        print(" -=-=-=-=- dac values written! -=-=-=-=- ")
        self.enable_adc()
        print(" -=-=-=-=- adc enabled! -=-=-=-=- ")
        synced_status = self.calibrate_sensor()
        print " !!  synchronised: ", synced_status  # == 15..
        # if self.selected_sensor == HexitecFem.OPTIONS[2] and synced_status == 12:
        #     pass
        # else:
        #     raise Exception("VSR 2 Links didn't sync, aborting initialisation")
        # print(" -=-=-=-=- VSR 2 all Done -=-=-=-=-")

        time.sleep(1)

        print(" -=-=-=-=-=-=-=-=-  Setup System to config VSR 1.. -=-=-=-=-=-=-=-=- ")
        self.selected_sensor = HexitecFem.OPTIONS[0]
        print "selected_sensor: ", self.selected_sensor
        self.initialise_sensor()
        print(" -=-=-=-=- sensors initialised! -=-=-=-=- ")
        self.load_pwr_cal_read_enables()
        print(" -=-=-=-=- load power / calibrate / read / whatever / done! -=-=-=-=- ")
        self.set_up_state_machine()
        print(" -=-=-=-=- state machine set up! -=-=-=-=- ")
        self.write_dac_values()
        print(" -=-=-=-=- dac values written! -=-=-=-=- ")
        self.enable_adc()
        print(" -=-=-=-=- adc enabled! -=-=-=-=- ")
        synced_status = self.calibrate_sensor()
        print " !!  synchronised: ", synced_status  # Saying it's 15..
        # if self.selected_sensor == HexitecFem.OPTIONS[0] and synced_status == 15:
        #     pass
        # else:
        #     raise Exception("VSR 1 Links didn't sync, aborting initialisation")
        # print(" -=-=-=-=- VSR 1 all Done -=-=-=-=-")
        # except HexitecFemError as e:
        #     logging.error("Error initialising system: %s", "Abort during read response")


class HexitecFemError(Exception):
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass
    
    
# root = tk.Tk()
# frame = tk.Frame(root)
# frame.pack()

# variable1 = tk.StringVar(frame)
# variable1.set(HexitecFem.OPTIONS[0]) # default value
# variable2 = tk.StringVar(frame)
# variable2.set(HexitecFem.IMAGE[0]) # default value
# variable3 = tk.StringVar(frame)
# variable3.set(HexitecFem.SETCLR[0]) # default value
# variable4 = tk.StringVar(frame)
# variable4.set(HexitecFem.REGADDRMSB[2]) # default value
# variable5 = tk.StringVar(frame)
# variable5.set(HexitecFem.REGADDRLSB[4]) # default value
# variable6 = tk.StringVar(frame)
# variable6.set(HexitecFem.BITVALUE[0]) # default value
# variable7 = tk.StringVar(frame)
# variable7.set(HexitecFem.DARKCORRECTION[0]) # default value
# variable8 = tk.StringVar(frame)
# variable8.set(HexitecFem.READOUTMODE[0]) # default value
# variable9 = tk.StringVar(frame)
# variable9.set(HexitecFem.TESTMODEIMAGE[0]) # default value
# w1 = tk.OptionMenu(frame, variable1, *OPTIONS)
# w1.pack(side=tk.BOTTOM)
# w8 = tk.OptionMenu(frame, variable8, *READOUTMODE)
# w8.pack(side=tk.BOTTOM)
# w2 = tk.OptionMenu(frame, variable2, *IMAGE)
# w2.pack(side=tk.BOTTOM)
# w3 = tk.OptionMenu(frame, variable3, *SETCLR)
# w3.pack(side=tk.BOTTOM)
# w4 = tk.OptionMenu(frame, variable4, *REGADDRMSB)
# w4.pack(side=tk.BOTTOM)
# w5 = tk.OptionMenu(frame, variable5, *REGADDRLSB)
# w5.pack(side=tk.BOTTOM)
# w6 = tk.OptionMenu(frame, variable6, *BITVALUE)
# w6.pack(side=tk.BOTTOM)
# w7 = tk.OptionMenu(frame, variable7, *DARKCORRECTION)
# w7.pack(side=tk.BOTTOM)
# w9 = tk.OptionMenu(frame, variable9, *TESTMODEIMAGE)
# w9.pack(side=tk.BOTTOM)
# button0 = tk.Button(frame, 
#                    text="CONNECT", 
#                    fg="green",
#                    command=cam_connect)
# button0.pack(side=tk.BOTTOM)

# button101 = tk.Button(frame,
#                       text="LIFE-SAVER",
#                       fg="CYAN",
#                       command=initialise_system)
# button101.pack(side=tk.BOTTOM)

# button2 = tk.Button(frame, 
#                    text="INITIALISE", 
#                    fg="red",
#                    command=initialise_sensor)
# button2.pack(side=tk.BOTTOM)
# button7 = tk.Button(frame, 
#                    text="LOAD PWR/CAL/READ ENABLES", 
#                    fg="red",
#                    command=load_pwr_cal_read_enables)
# button7.pack(side=tk.BOTTOM)
# button6 = tk.Button(frame, 
#                    text="SET UP SM", 
#                    fg="red",
#                    command=set_up_state_machine)
# button6.pack(side=tk.BOTTOM)
# button11 = tk.Button(frame, 
#                    text="LOAD IMAGE", 
#                    fg="red",
#                    command=load_image)
# button11.pack(side=tk.BOTTOM)
# button8 = tk.Button(frame, 
#                    text="WRITE DAC VALUES", 
#                    fg="red",
#                    command=write_dac_values)
# button8.pack(side=tk.BOTTOM)
# button9 = tk.Button(frame, 
#                    text="ENABLE ADC", 
#                    fg="red",
#                    command=enable_adc)
# button9.pack(side=tk.BOTTOM)
# button10 = tk.Button(frame, 
#                    text="ENABLE ADC TESTMODE", 
#                    fg="red",
#                    command=enable_adc_testmode)
# button10.pack(side=tk.BOTTOM)
# button4 = tk.Button(frame, 
#                    text="CALIBRATE", 
#                    fg="red",     
#                    command=calibrate_sensor)
# button4.pack(side=tk.BOTTOM)
# textBox = tk.Text(root, height=1, width=20)
# textBox.insert(tk.END, 'filename')
# textBox.pack()
# entry_2 = tk.Entry(root)
# entry_2.pack()
# button5 = tk.Button(frame, 
#                    text="AQUIRE DATA", 
#                    fg="red",
#                    command=acquire_data)
# button5.pack(side=tk.BOTTOM)
# button1 = tk.Button(frame, 
#                    text="DISS-CONNECT", 
#                    fg="red",
#                    command=cam_disconnect)
# button1.pack(side=tk.BOTTOM)
# button12 = tk.Button(frame, 
#                    text="MODIFY_REGISTER", 
#                    fg="green",
#                    command=modify_register)
# button12.pack(side=tk.BOTTOM)
# button12 = tk.Button(frame, 
#                    text="READ VOLTAGES", 
#                    fg="green",
#                    command=read_voltages)
# button12.pack(side=tk.BOTTOM)
# label1 = tk.Label(frame, text="Links Not Locked")
# label1.pack()

# entry_2.insert(0, 10)


# root.mainloop()
