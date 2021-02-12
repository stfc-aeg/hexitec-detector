#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 16 08:02:14 2019

@author: jpe87
"""

import tkinter as tk
import time
import datetime
from QemCam import QemCam


class TestGuiError(Exception):
    """Simple exception class for script to wrap lower-level exceptions."""

    pass


vsr_addr = 0x90
global number_of_frames
global debug

debug = False
qemcamera = QemCam(debug)

# 10G RDMA IP addresses
qemcamera.server_ctrl_ip_addr = "10.0.2.2"
qemcamera.camera_ctrl_ip_addr = "10.0.2.1"

# 10G image stream Ip addresses
qemcamera.server_data_ip_addr = "10.0.4.2"
qemcamera.camera_data_ip_addr = "10.0.4.1"

if debug:
    print("james_gui.py:")
    print("  RDMA IP addresses")
    print("	\tserver_ctrl_ip_addr	{}".format(qemcamera.server_ctrl_ip_addr))
    print("	\tcamera_ctrl_ip_addr	{}".format(qemcamera.camera_ctrl_ip_addr))

    # 10G image stream Ip addresses
    print("  Image Stream IP addresses")
    print("	\tserver_data_ip_addr	{}".format(qemcamera.server_data_ip_addr))
    print("	\tcamera_data_ip_addr	{}".format(qemcamera.camera_data_ip_addr))
    print("___________________________________________________________ ")

number_of_frames = 20

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
    "IMAGE 1",
    "IMAGE 2",
    "IMAGE 3",
    "IMAGE 4"
]

SETCLR = [
    "SET",
    "CLEAR"
]

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
    "0xF"
]

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
    "0xF"
]

BITVALUE = [
    "Bit0",
    "Bit1",
    "Bit2",
    "Bit3",
    "Bit4",
    "Bit5",
    "Bit6",
    "Bit7"
]

DARKCORRECTION = [
    "DARK CORRECTION OFF",
    "DARK CORRECTION ON"
]

READOUTMODE = [
    "SINGLE",
    "2x2"
]

file_counter = 0


def get_gui_number_of_frames():
    num = entry_2.get()
    # Try convert a str to int
    # If unable eg. int('hello') or int('5.5')
    # then show an error.
    try:
        num = int(num)
    # ValueError is the type of error expected from this conversion
    except ValueError:
        print('Non-Int Error, Please enter an integer')
        num = 20
    else:
        print("GUI setting number of frames to:- ")
        print(num)
    return(num)


#  This function sends a command string to the microcontroller
def send_cmd(cmd):

    while len(cmd)%4 != 0:
        cmd.append(13)
    print("Length of command - ", len(cmd), len(cmd) % 4)
    for i in range(0, len(cmd) // 4):
        #print format(cmd[(i*4)+3], '02x'), format(cmd[(i*4)+2], '02x'), format(cmd[(i*4)+1], '02x'), format(cmd[(i*4)], '02x') 
        #reg_value = 256*256*256*cmd[(i*4)+3] + 256*256*cmd[(i*4)+2] + 256*cmd[(i*4)+1] + cmd[(i*4)] 
        reg_value = 256*256*256*cmd[(i*4)] + 256*256*cmd[(i*4)+1] + 256*cmd[(i*4)+2] + cmd[(i*4)+3] 
        #print reg_value
        #print format(reg_value, '08x')
        qemcamera.x10g_rdma.write(0xE0000100, reg_value, 'Write 4 Bytes')
        time.sleep(0.25)


#  This function will display the returned voltages returned by the 0x50 instruction
def display_voltages(f):
    for i in range(1, len(f)-2, 4):
        s = 0
        s = s + get_dec(f[i+3]) + get_dec(f[i+2])*16 + get_dec(f[i+1])*256 + get_dec(f[i])*4096
        j = (i-2)//4+1
        if j == 9:
            print("Voltage %.d %.2f" %(j+1, s*2.048/4096))
        else:
            print("Voltage %.d %.2f" %(j+1, s*3.3/4096))


#  Simple function to return the decimal value of a number in ASCII(0-9, A-F)
def get_dec(a):
    r = 0
    if a >= 48:
        if a <= 57:
            r = a - 48
        if a > 57:
            r = a - 55
    return(r)


# Displays the returned response from the microcontroller
def read_response():
    data_counter = 0
    f = []
    ABORT_VALUE = 10000
    RETURN_START_CHR = 42
    CARRIAGE_RTN = 13
    FIFO_EMPTY_FLAG = 1
    empty_count = 0
    daty = RETURN_START_CHR

    while daty != CARRIAGE_RTN:
        fifo_empty = FIFO_EMPTY_FLAG

        while fifo_empty == FIFO_EMPTY_FLAG and empty_count < ABORT_VALUE:
            fifo_empty = qemcamera.x10g_rdma.read(0xE0000011, 'FIFO EMPTY FLAG')
            empty_count = empty_count + 1
        dat = qemcamera.x10g_rdma.read(0xE0000200, 'Data')
        daty = dat // 256 // 256 // 256%256
        f.append(daty)
        if debug:
            print("Got data:- ")
            print("Bytes are:- ")
            print(format(daty, '02x'))
        daty = dat // 256 // 256%256
        f.append(daty)
        if debug:
            print(format(daty, '02x'))
        daty = dat // 256%256
        f.append(daty)
        if debug:
            print(format(daty, '02x'))
        daty = dat%256
        f.append(daty)
        if debug:
            print(format(daty, '02x'))
        data_counter = data_counter + 1
        if empty_count == ABORT_VALUE:
            raise TestGuiError("Abort in read_response()")
            daty = CARRIAGE_RTN
        empty_count = 0

    if debug:
        print("Counter is :- ", data_counter)
        print("Length is:-", len(f))
    fifo_empty = qemcamera.x10g_rdma.read(0xE0000011, 'Data')
    print("FIFO should be empty ", fifo_empty)

    s = ''
    for i in range(1, data_counter * 4):
        s = s + chr(f[i])

    if debug:
        print("String :- ", s)
        print(f[0])
        print(f[1])

    return(s)


def cam_connect():
    global label1
    label1.config(text="Links not locked")
    success = qemcamera.connect()
    if (success):
        print("Camera is connected")
        send_cmd([0x23, 0x90, 0xE3, 0x0D])
        time.sleep(1)
        send_cmd([0x23, 0x91, 0xE3, 0x0D])
        print("Wait 10 seconds for VSRs' FPGAs to initialise..")
        waiting = "."
        for index in range(10):
            print("\r{}".format(waiting))
            waiting += "."
            time.sleep(1)
        print("Enable modules")
    else:
        print("\nFailed to establish connection!\nAborted.")


def cam_disconnect():
    send_cmd([0x23, 0x90, 0xE2, 0x0D])
    send_cmd([0x23, 0x91, 0xE2, 0x0D])
    print("Modules Disabled")
    qemcamera.disconnect()
    print("Camera is Dis-connected")


def initialise_sensor():
    global number_of_frames

    label1.config(text="Links not locked")
    qemcamera.x10g_rdma.write(0x60000002, 0, 'Disable State Machine Trigger')
    print("Disable State Machine Enabling signal")

    if variable1.get() == OPTIONS[0]:
        qemcamera.x10g_rdma.write(0x60000004, 0, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 1_1')
        print("VSR_1")
        tk.vsr_addr = 0x90
    if variable1.get() == OPTIONS[1]:
        qemcamera.x10g_rdma.write(0x60000004, 2, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 1_2')
        print("VSR_1")
        tk.vsr_addr = 0x90
    if variable1.get() == OPTIONS[2]:
        qemcamera.x10g_rdma.write(0x60000004, 4, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 2_1')
        print("VSR 2")
        tk.vsr_addr = 0x91
    if variable1.get() == OPTIONS[3]:
        qemcamera.x10g_rdma.write(0x60000004, 6, 'Set bit 0 to 1 to generate test pattern in FEMII, bits [2:1] select which of the 4 sensors is read - data 2_2')
        print("VSR 2")
        tk.vsr_addr = 0x91

    if variable8.get() == READOUTMODE[0]:
        print("Disable synchronisation SM start")
        send_cmd([0x23, tk.vsr_addr, 0x40, 0x30, 0x41, 0x30, 0x30, 0x0D])
        read_response()
        print("Reading out single sensor")
    elif variable8.get() == READOUTMODE[1]:
        # Need to set up triggering MODE here
        # Enable synchronisation SM start via trigger 1
        print("Enable synchronisation SM start via trigger 1")
        send_cmd([0x23, tk.vsr_addr, 0x42, 0x30, 0x41, 0x30, 0x31, 0x0D])
        read_response()
        # Enable synchronisation SM start on rising or falling edge of ADC clock
        # Experiment with this bit
#        send_cmd([0x23, tk.vsr_addr, 0x43, 0x31, 0x34, 0x30, 0x31, 0x0D])
#        read_response()        
        print("Reading out 2x2 sensors")
    print(variable1.get())

    number_of_frames = get_gui_number_of_frames()

    print("Communicating with - ", tk.vsr_addr)
    # Set Frame Gen Mux Frame Gate
    qemcamera.x10g_rdma.write(0x60000001, 2, 'Set Frame Gen Mux Frame Gate - works set to 2')
    #Followinbg line is important
    qemcamera.x10g_rdma.write(0xD0000001, number_of_frames - 1, 'Frame Gate set to number_of_frames')

    # Send this command to Enable Test Pattern in my VSR design
    print("Setting Number of Frames to ", number_of_frames)
    print("Enable Test Pattern in my VSR design")
    # Use Sync clock from DAQ board
    print("Use Sync clock from DAQ board")
    send_cmd([0x23, tk.vsr_addr, 0x42, 0x30, 0x31, 0x31, 0x30, 0x0D])
    read_response()
    print("Enable LVDS outputs")
    set_register_vsr1_command  = [0x23, 0x90, 0x42, 0x30, 0x31, 0x32, 0x30, 0x0D]
    set_register_vsr2_command  = [0x23, 0x91, 0x42, 0x30, 0x31, 0x32, 0x30, 0x0D]
    send_cmd(set_register_vsr1_command)
    read_response()
    send_cmd(set_register_vsr2_command)
    read_response()
    print("LVDS outputs enabled")
    print("Read LO IDLE")
    send_cmd([0x23, tk.vsr_addr, 0x40, 0x46, 0x45, 0x41, 0x41, 0x0D])
    read_response()
    print("Read HI IDLE")
    send_cmd([0x23, tk.vsr_addr, 0x40, 0x46, 0x46, 0x4E, 0x41, 0x0D])
    read_response()
    # This sets up test pattern on LVDS outputs
    print("Set up LVDS test pattern")
    send_cmd([0x23, tk.vsr_addr, 0x43, 0x30, 0x31, 0x43, 0x30, 0x0D])
    read_response()
    # Use default test pattern of 1000000000000000
    send_cmd([0x23, tk.vsr_addr, 0x42, 0x30, 0x31, 0x38, 0x30, 0x0D])
    read_response()

    full_empty = qemcamera.x10g_rdma.read(0x60000011, 'Check EMPTY Signals')
    print("Check EMPTY Signals", full_empty)
    full_empty = qemcamera.x10g_rdma.read(0x60000012, 'Check FULL Signals')
    print("Check FULL Signals", full_empty)


def calibrate_sensor():
    global label1
    label1.config(text="Links not locked")
    print("setting image size")
    # 80x80 pixels 14 bits
    #qemcamera.set_image_size(80,80,14,16)

    if variable8.get() == READOUTMODE[0]:
        print("Reading out single sensor")
        qemcamera.set_image_size(80, 80, 14, 16)
        mux_mode = 0
    elif variable8.get() == READOUTMODE[1]:
        #qemcamera.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
        mux_mode = 8
        qemcamera.set_image_size(160, 160, 14, 16)
        print("Reading out 2x2 sensors")

    # Set VCAL
    send_cmd([0x23, tk.vsr_addr, 0x42, 0x31, 0x38, 0x30, 0x31, 0x0D])
    read_response()
    print("Clear bit 5")
    send_cmd([0x23, tk.vsr_addr, 0x43, 0x32, 0x34, 0x32, 0x30, 0x0D])
    read_response()

    # Set bit 4 of Reg24
    send_cmd([0x23, tk.vsr_addr, 0x42, 0x32, 0x34, 0x31, 0x30, 0x0D])
    read_response()

    print("Set bit 6")
    send_cmd([0x23, tk.vsr_addr, 0x43, 0x32, 0x34, 0x34, 0x30, 0x0D])  # Clear Reg Bit
    read_response()
    send_cmd([0x23, tk.vsr_addr, 0x41, 0x30, 0x31, 0x0D])              # Read Reg Bit
    read_response()
    send_cmd([0x23, tk.vsr_addr, 0x42, 0x32, 0x34, 0x32, 0x32, 0x0D])  # Set Reg Bit
    read_response()

    if variable1.get() == OPTIONS[0]:
        qemcamera.x10g_rdma.write(0x60000002, 1, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
        print("CALIBRATING VSR_1")    
    if variable1.get() == OPTIONS[1]:
        qemcamera.x10g_rdma.write(0x60000002, 1, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
        print("CALIBRATING VSR_1")    
    if variable1.get() == OPTIONS[2]:
        qemcamera.x10g_rdma.write(0x60000002, 2, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
        print("CALIBRATING VSR_2")  
    if variable1.get() == OPTIONS[3]:
        qemcamera.x10g_rdma.write(0x60000002, 2, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
        print("CALIBRATING VSR_2")  

    # Send command on CMD channel to FEMII
    #qemcamera.x10g_rdma.write(0x60000002, 3, 'Trigger Cal process : Bit1 - VSR2, Bit 0 - VSR1 ')
    qemcamera.x10g_rdma.write(0x60000002, 0, 'Un-Trigger Cal process')

    # Reading back Sync register
    synced = qemcamera.x10g_rdma.read(0x60000010, 'Check LVDS has synced')
    print("Sync Register value")

    full_empty = qemcamera.x10g_rdma.read(0x60000011, 'Check FULL EMPTY Signals')
    print("Check EMPTY Signals", full_empty)

    full_empty = qemcamera.x10g_rdma.read(0x60000012, 'Check FULL FULL Signals')
    print("Check FULL Signals", full_empty)

    if synced == 15:
        print("All Links on VSR's 1 and 2 synchronised")
        label1.config(text="All Links on VSR's 1 and 2 synchronised")  
        #qemcamera.x10g_rdma.write(0x60000002, 4, 'Enable state machines in VSRs ')
        print("Starting State Machine in VSR's")  
    elif synced == 12:
        print("Both Links on VSR 2 synchronised")
        label1.config(text="Both Links on VSR 2 synchronised")        
    elif synced == 3:
        print("Both Links on VSR 1 synchronised")
        label1.config(text="Both Links on VSR 1 synchronised")
    else:
        print(synced)

    # Send this command to Disable Test Pattern in my VSR design
    send_cmd([0x23, 0x92, 0x00, 0x0D])  

    # Clear training enable
    send_cmd([0x23, tk.vsr_addr, 0x43, 0x30, 0x31, 0x43, 0x30, 0x0D])
    read_response()

    print("Clear bit 5 - VCAL ENABLED")
    send_cmd([0x23, tk.vsr_addr, 0x43, 0x32, 0x34, 0x32, 0x30, 0x0D])
    read_response()

    if variable7.get() == DARKCORRECTION[0]:
        #  Log image to file
        print("DARK CORRECTION OFF")
        send_cmd([0x23, tk.vsr_addr, 0x43, 0x32, 0x34, 0x30, 0x38, 0x0D])
        read_response()
    elif variable7.get() == DARKCORRECTION[1]:
        #  Log image to file
        print("DARK CORRECTION ON")
        send_cmd([0x23, tk.vsr_addr, 0x42, 0x32, 0x34, 0x30, 0x38, 0x0D])    
        read_response()

    # Read Reg24
    send_cmd([0x23, tk.vsr_addr, 0x41, 0x32, 0x34, 0x0D])
    read_response()
    # Don't print reply as is in Python 3 - locks up shell (but not program execution)
    # reply = read_response()
    # print("reading Register 0x24")
    # # print(type(reply), type(reply.encode()))
    # print(reply.encode())

    send_cmd([0x23, tk.vsr_addr, 0x41, 0x38, 0x39, 0x0D])
    read_response()

    time.sleep(3)

    print("Poll register 0x89")
    send_cmd([0x23, tk.vsr_addr, 0x41, 0x38, 0x39, 0x0D])
    read_response()
    # Don't print reply as is in Python 3 - locks up shell (but not program execution)
    # r = read_response()
    # print("Bit 1 should be 1") 
    # print(type(r))
    # print(r.encode())
    print("Read reg 1")
    send_cmd([0x23, tk.vsr_addr, 0x41, 0x30, 0x31, 0x0D])
    read_response()

    full_empty = qemcamera.x10g_rdma.read(0x60000011, 'Check FULL EMPTY Signals')
    print("Check EMPTY Signals", full_empty)

    full_empty = qemcamera.x10g_rdma.read(0x60000012, 'Check FULL FULL Signals')
    print("Check FULL Signals", full_empty)


def acquire_data():

    full_empty = qemcamera.x10g_rdma.read(0x60000011, 'Check FULL EMPTY Signals')
    print("Check EMPTY Signals", full_empty)

    full_empty = qemcamera.x10g_rdma.read(0x60000012, 'Check FULL FULL Signals')
    print("Check FULL Signals", full_empty)

    global number_of_frames

    if variable8.get() == READOUTMODE[0]:
        print("Reading out single sensor")
        mux_mode = 0
    elif variable8.get() == READOUTMODE[1]:
        #qemcamera.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')
        mux_mode = 8
        print("Reading out 2x2 sensors")

    if variable1.get() == OPTIONS[0]:
        qemcamera.x10g_rdma.write(0x60000004, 0 + mux_mode, 'Sensor 1 1')
        print("Sensor 1 1")
    if variable1.get() == OPTIONS[1]:
        qemcamera.x10g_rdma.write(0x60000004, 2 + mux_mode, 'Sensor 1 2')
        print("Sensor 1 2")
    if variable1.get() == OPTIONS[2]:
        qemcamera.x10g_rdma.write(0x60000004, 4 + mux_mode, 'Sensor 2 1')
        print("Sensor 2 1") 
    if variable1.get() == OPTIONS[3]:
        qemcamera.x10g_rdma.write(0x60000004, 6 + mux_mode, 'Sensor 2 2')
        print("Sensor 2 2")

    # Flush the input FIFO buffers
    qemcamera.x10g_rdma.write(0x60000002, 32, 'Clear Input Buffers')
    qemcamera.x10g_rdma.write(0x60000002, 0, 'Clear Input Buffers')
    time.sleep(1)
    full_empty = qemcamera.x10g_rdma.read(0x60000011, 'Check EMPTY Signals')
    print("Check EMPTY Signals", full_empty)
    full_empty = qemcamera.x10g_rdma.read(0x60000012, 'Check FULL Signals')
    print("Check FULL Signals", full_empty)

    if variable8.get() == READOUTMODE[1]:
        qemcamera.x10g_rdma.write(0x60000002, 4, 'Enable State Machine')

    inputValue = textBox.get("1.0", "end-1c")

    file_string = '/tmp/Hexitec' + datetime.datetime.now().strftime("%b_%d_%H%M%S_") + variable1.get() + '_' + inputValue
    print(file_string) 
    print("number of Frames :=", number_of_frames)

    theStart = time.time()
    if variable2.get() == IMAGE[0]:
        #  Log image to file
        print("Logging Image to HDF5 file")
        qemcamera.log_image_stream(file_string, number_of_frames)  
    if variable2.get() == IMAGE[1]:
        #  Log image to file
        print("Logging Image to BIN file")
        qemcamera.log_image_stream_bin(file_string, number_of_frames)  
    if variable2.get() == IMAGE[2]:
        #  Stream image
        print("Streaming Image")
        qemcamera.display_image_stream(number_of_frames)
    if variable2.get() == IMAGE[3]:
        #  Data Capture only
        print("Data Capture on Wireshark only - no image")
        qemcamera.data_stream(number_of_frames)
        #
        waited = 0.0
        delay = 0.10
        #
        resp = 0
        #for wait in range(40):
        while resp < 1:
            resp = qemcamera.x10g_rdma.read(0x60000014, 'Check data transfer completed?')
            # print("Transfer complete = ", resp)
            time.sleep(delay)
            waited += delay
        print(waited)
        print("  *** Waited %s second(s) ***" % waited)
        #

    # Stop the state machine
    qemcamera.x10g_rdma.write(0x60000002, 0, 'Dis-Enable State Machine')
    theEnd = time.time()
    print("Aquasition Complete, clear enable signal")    
    qemcamera.x10g_rdma.write(0xD0000000, 2, 'Clear enable signal')
    qemcamera.x10g_rdma.write(0xD0000000, 0, 'Clear enable signal')

    # Clear the Mux Mode bit
    if variable1.get() == OPTIONS[0]:
        qemcamera.x10g_rdma.write(0x60000004, 0, 'Sensor 1 1')
        print("Sensor 1 1")
    if variable1.get() == OPTIONS[1]:
        qemcamera.x10g_rdma.write(0x60000004, 2, 'Sensor 1 2')
        print("Sensor 1 2")
    if variable1.get() == OPTIONS[2]:
        qemcamera.x10g_rdma.write(0x60000004, 4, 'Sensor 2 1')
        print("Sensor 2 1") 
    if variable1.get() == OPTIONS[3]:
        qemcamera.x10g_rdma.write(0x60000004, 6, 'Sensor 2 2')
        print("Sensor 2 2")
    full_empty = qemcamera.x10g_rdma.read(0x60000011, 'Check EMPTY Signals')
    print("Check EMPTY Signals", full_empty)
    full_empty = qemcamera.x10g_rdma.read(0x60000012, 'Check FULL Signals')
    print("Check FULL Signals", full_empty)
    no_frames = qemcamera.x10g_rdma.read(0xD0000001, 'Check Number of Frames setting') + 1
    print("Number of Frames", no_frames)

    print("Output from Sensor") 
    m0 = qemcamera.x10g_rdma.read(0x70000010, 'frame last length')
    print("frame last length", m0)
    m0 = qemcamera.x10g_rdma.read(0x70000011, 'frame max length')
    print("frame max length", m0)
    m0 = qemcamera.x10g_rdma.read(0x70000012, 'frame min length')
    print("frame min length", m0)
    m0 = qemcamera.x10g_rdma.read(0x70000013, 'frame number')
    print("frame number", m0)
    m0 = qemcamera.x10g_rdma.read(0x70000014, 'frame last clock cycles')
    print("frame last clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x70000015, 'frame max clock cycles')
    print("frame max clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x70000016, 'frame min clock cycles')
    print("frame min clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x70000017, 'frame data total')
    print("frame data total", m0)
    m0 = qemcamera.x10g_rdma.read(0x70000018, 'frame data total clock cycles')
    print("frame data total clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x70000019, 'frame trigger count')
    print("frame trigger count", m0)
    m0 = qemcamera.x10g_rdma.read(0x7000001A, 'frame in progress flag')
    print("frame in progress flag", m0)

    print("Output from Frame Gate")
    m0 = qemcamera.x10g_rdma.read(0x80000010, 'frame last length')
    print("frame last length", m0)
    m0 = qemcamera.x10g_rdma.read(0x80000011, 'frame max length')
    print("frame max length", m0)
    m0 = qemcamera.x10g_rdma.read(0x80000012, 'frame min length')
    print("frame min length", m0)
    m0 = qemcamera.x10g_rdma.read(0x80000013, 'frame number')
    print("frame number", m0)
    m0 = qemcamera.x10g_rdma.read(0x80000014, 'frame last clock cycles')
    print("frame last clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x80000015, 'frame max clock cycles')
    print("frame max clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x80000016, 'frame min clock cycles')
    print("frame min clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x80000017, 'frame data total')
    print("frame data total", m0)
    m0 = qemcamera.x10g_rdma.read(0x80000018, 'frame data total clock cycles')
    print("frame data total clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x80000019, 'frame trigger count')
    print("frame trigger count", m0)
    m0 = qemcamera.x10g_rdma.read(0x8000001A, 'frame in progress flag')
    print("frame in progress flag", m0)

    print("Input to XAUI") 
    m0 = qemcamera.x10g_rdma.read(0x90000010, 'frame last length')
    print("frame last length", m0)
    m0 = qemcamera.x10g_rdma.read(0x90000011, 'frame max length')
    print("frame max length", m0)
    m0 = qemcamera.x10g_rdma.read(0x90000012, 'frame min length')
    print("frame min length", m0)
    m0 = qemcamera.x10g_rdma.read(0x90000013, 'frame number')
    print("frame number", m0)
    m0 = qemcamera.x10g_rdma.read(0x90000014, 'frame last clock cycles')
    print("frame last clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x90000015, 'frame max clock cycles')
    print("frame max clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x90000016, 'frame min clock cycles')
    print("frame min clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x90000017, 'frame data total')
    print("frame data total", m0)
    m0 = qemcamera.x10g_rdma.read(0x90000018, 'frame data total clock cycles')
    print("frame data total clock cycles", m0)
    m0 = qemcamera.x10g_rdma.read(0x90000019, 'frame trigger count')
    print("frame trigger count", m0)
    m0 = qemcamera.x10g_rdma.read(0x9000001A, 'frame in progress flag')
    print("frame in progress flag", m0)

    print(" ACQUISITION TOOK %s" % (theEnd - theStart))


def set_up_state_machine():
    print("Setting up state machine")
    #  Thes are used to set up the state machine
    sm_timing1  = [0x23, tk.vsr_addr, 0x42, 0x30, 0x37, 0x30, 0x33, 0x0D]
    # sm_timing2  = [0x23, tk.vsr_addr, 0x42, 0x30, 0x32, 0x30, 0x31, 0x0D]
    sm_timing2  = [0x23, tk.vsr_addr, 0x42, 0x30, 0x32, 0x46, 0x34, 0x0D]
    sm_timing3  = [0x23, tk.vsr_addr, 0x42, 0x30, 0x34, 0x30, 0x31, 0x0D]
    # sm_timing4  = [0x23, tk.vsr_addr, 0x42, 0x30, 0x35, 0x30, 0x36, 0x0D]
    sm_timing4  = [0x23, tk.vsr_addr, 0x42, 0x30, 0x35, 0x30, 0x35, 0x0D]
    sm_timing5  = [0x23, tk.vsr_addr, 0x42, 0x30, 0x39, 0x30, 0x32, 0x0D]
    sm_timing6  = [0x23, tk.vsr_addr, 0x42, 0x30, 0x45, 0x30, 0x41, 0x0D]
    sm_timing7  = [0x23, tk.vsr_addr, 0x42, 0x31, 0x42, 0x30, 0x38, 0x0D]
    sm_timing8  = [0x23, tk.vsr_addr, 0x42, 0x31, 0x34, 0x30, 0x31, 0x0D]

    send_cmd(sm_timing1)
    read_response()
    send_cmd(sm_timing2)
    read_response()
    send_cmd(sm_timing3)
    read_response()
    send_cmd(sm_timing4)
    read_response()
    send_cmd(sm_timing5)
    read_response()
    send_cmd(sm_timing6)
    read_response()
    send_cmd(sm_timing7)
    read_response()
    send_cmd(sm_timing8)
    read_response()

    #  Try setting vcal2 -> VCAL1 21/01/2019
    send_cmd([0x23, tk.vsr_addr, 0x42, 0x31, 0x38, 0x30, 0x31, 0x0D])
    read_response()

    print("    sm_timing2(Register 002, row->S1) ", make_list_hexadecimal(sm_timing2))
    print("    sm_timing3(Register 004, S1_SPH) ", make_list_hexadecimal(sm_timing3))
    print("    sm_timing4(Register 005, SPH_S2) ", make_list_hexadecimal(sm_timing4))

    print("Finished Setting up state machine")


def make_list_hexadecimal(value):
    value_hexadecimal = []
    for val in value:
        value_hexadecimal.append("0x%x" % val)
    return value_hexadecimal


def load_pwr_cal_read_enables():
    enable_sm     = [0x23, tk.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31, 0x0D]
    disable_sm    = [0x23, tk.vsr_addr, 0x43, 0x30, 0x31, 0x30, 0x31, 0x0D]
    diff_cal      = [0x23, tk.vsr_addr, 0x42, 0x38, 0x46, 0x30, 0x31, 0x0D]

    col_read_enable1   = [0x23, tk.vsr_addr, 0x44, 0x36, 0x31, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
    col_read_enable2   = [0x23, tk.vsr_addr, 0x44, 0x43, 0x32, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
    col_power_enable1  = [0x23, tk.vsr_addr, 0x44, 0x34, 0x44, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
    col_power_enable2  = [0x23, tk.vsr_addr, 0x44, 0x41, 0x45, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]

    #col_cal_enable1    = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
    #col_cal_enable2    = [0x23, tk.vsr_addr, 0x44, 0x42, 0x38, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
    #col_cal_enable1a    = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x30, 0x30, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    #col_cal_enable1a    = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # JE orgin:
    col_cal_enable1a    = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # 30/07 JE alt:
    col_cal_enable1a    = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x46, 0x46, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]

    col_cal_enable1b    = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x46, 0x30, 0x30, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    col_cal_enable1c    = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # Uncalibrated(Image4) column option:
    col_cal_enable1d    = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]

    # JE orgin:
    col_cal_enable2a    = [0x23, tk.vsr_addr, 0x44, 0x42, 0x38, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # 30/07 alt:
    col_cal_enable2a    = [0x23, tk.vsr_addr, 0x44, 0x42, 0x38, 0x46, 0x46, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]


    col_cal_enable2b    = [0x23, tk.vsr_addr, 0x44, 0x42, 0x38, 0x30, 0x30, 0x30, 0x30, 0x46, 0x30, 0x30, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    col_cal_enable2c    = [0x23, tk.vsr_addr, 0x44, 0x42, 0x38, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # Uncalibrated(Image4) column option:
    col_cal_enable2d    = [0x23, tk.vsr_addr, 0x44, 0x42, 0x38, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]

    row_read_enable1   = [0x23, tk.vsr_addr, 0x44, 0x34, 0x33, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
    row_read_enable2   = [0x23, tk.vsr_addr, 0x44, 0x41, 0x34, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
    row_power_enable1  = [0x23, tk.vsr_addr, 0x44, 0x32, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
    row_power_enable2  = [0x23, tk.vsr_addr, 0x44, 0x39, 0x30, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x0D]
    
    #row_cal_enable1    = [0x23, tk.vsr_addr, 0x44, 0x33, 0x39, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
    #row_cal_enable2    = [0x23, tk.vsr_addr, 0x44, 0x39, 0x41, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x46, 0x30, 0x0D]
    #row_cal_enable1a    = [0x23, tk.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # JE original:
    row_cal_enable1a    = [0x23, tk.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # 30/07 JE alt:
    row_cal_enable1a    = [0x23, tk.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    
    
    row_cal_enable1b    = [0x23, tk.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    row_cal_enable1c    = [0x23, tk.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # Uncalibrated(Image4) row option:
    row_cal_enable1d    = [0x23, tk.vsr_addr, 0x44, 0x33, 0x39, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    
    # JE original:
    row_cal_enable2a    = [0x23, tk.vsr_addr, 0x44, 0x39, 0x41, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # 30/07 JE alt:
    row_cal_enable2a    = [0x23, tk.vsr_addr, 0x44, 0x39, 0x41, 0x30, 0x30, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]

    row_cal_enable2b    = [0x23, tk.vsr_addr, 0x44, 0x39, 0x41, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    row_cal_enable2c    = [0x23, tk.vsr_addr, 0x44, 0x39, 0x41, 0x30, 0x30, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # Uncalibrated(Image4) row option:
    row_cal_enable2d    = [0x23, tk.vsr_addr, 0x44, 0x39, 0x41, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]

    # col_cal_enable1a = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    # col_cal_enable2a = [0x23, tk.vsr_addr, 0x44, 0x42, 0x38, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    col_cal_enable1a = [0x23, tk.vsr_addr, 0x44, 0x35, 0x37, 0x46, 0x30, 0x46, 0x46, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]
    col_cal_enable2a = [0x23, tk.vsr_addr, 0x44, 0x42, 0x38, 0x46, 0x30, 0x46, 0x46, 0x46, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0D]


    print("Use different CAL data")  
    send_cmd(diff_cal)
    read_response()

    send_cmd(disable_sm)
    read_response()
    
    print("Loading Power, Cal and Read Enables")    
    print("Column power enable")
    send_cmd(col_power_enable1)
    read_response()
    send_cmd(col_power_enable2)
    read_response()

    print("Row power enable")
    send_cmd(row_power_enable1)
    read_response()
    send_cmd(row_power_enable2)
    read_response()

    if variable9.get() == TESTMODEIMAGE[0]:    
        print("Column cal enable A")
        send_cmd(col_cal_enable1a)
        read_response()
        send_cmd(col_cal_enable2a)
        read_response()
        print("Row cal enable A")
        send_cmd(row_cal_enable1a)
        read_response()
        send_cmd(row_cal_enable2a)
        read_response()
    elif variable9.get() == TESTMODEIMAGE[1]:
        print("Column cal enable B")
        send_cmd(col_cal_enable1b)
        read_response()
        send_cmd(col_cal_enable2b)
        read_response()
        print("Row cal enable B")
        send_cmd(row_cal_enable1b)
        read_response()
        send_cmd(row_cal_enable2b)
        read_response()
    elif variable9.get() == TESTMODEIMAGE[2]:
        print("Column cal enable C")
        send_cmd(col_cal_enable1c)
        read_response()
        send_cmd(col_cal_enable2c)
        read_response()
        print("Row cal enable C")
        send_cmd(row_cal_enable1c)
        read_response()
        send_cmd(row_cal_enable2c)
        read_response()
    elif variable9.get() == TESTMODEIMAGE[3]:
        print("Column cal enable D")
        send_cmd(col_cal_enable1d)
        read_response()
        send_cmd(col_cal_enable2d)
        read_response()
        print("Row cal enable D")
        send_cmd(row_cal_enable1d)
        read_response()
        send_cmd(row_cal_enable2d)
        read_response()
        
    print("Column read enable")
    send_cmd(col_read_enable1)
    read_response()
    send_cmd(col_read_enable2)
    read_response()
 
    print("Row read enable")
    send_cmd(row_read_enable1)
    read_response()
    send_cmd(row_read_enable2)
    read_response()

    print("Power, Cal and Read Enables have been loaded") 
       
    send_cmd(enable_sm)
    read_response()


def write_dac_values():
    print("Writing DAC values")
    send_cmd([0x23, tk.vsr_addr, 0x54, 0x30, 0x32, 0x41, 0x41, 0x30, 0x35, 0x35, 0x35, 0x30, 0x35, 0x35, 0x35, 0x30, 0x30, 0x30, 0x30, 0x30, 0x38, 0x45, 0x38, 0x0D])
    read_response()
    print("DAC values set")


def enable_adc():
    print("Enabling ADC")
    adc_disable   = [0x23, tk.vsr_addr, 0x55, 0x30, 0x32, 0x0D]
    enable_sm     = [0x23, tk.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31, 0x0D]
    adc_enable    = [0x23, tk.vsr_addr, 0x55, 0x30, 0x33, 0x0D]
    adc_set       = [0x23, tk.vsr_addr, 0x53, 0x31, 0x36, 0x30, 0x39, 0x0D]
    aqu1          = [0x23, tk.vsr_addr, 0x40, 0x32, 0x34, 0x32, 0x32, 0x0D]
    aqu2          = [0x23, tk.vsr_addr, 0x40, 0x32, 0x34, 0x32, 0x38, 0x0D]   
    
    send_cmd(adc_disable)
    read_response()
    print("Enable SM")
    send_cmd(enable_sm)
    read_response()
    send_cmd(adc_enable)
    read_response()
    
    send_cmd(adc_set)
    read_response() 
    send_cmd(aqu1)
    read_response()
    send_cmd(aqu2)
    read_response()
    
    # Disable  ADC test testmode
    send_cmd([0x23, tk.vsr_addr, 0x53, 0x30, 0x44, 0x30, 0x30, 0x0d])
    read_response() 


def enable_adc_testmode():
    print("Enabling ADC Testmode")   
    # Set ADC test testmode
    send_cmd([0x23, tk.vsr_addr, 0x53, 0x30, 0x44, 0x34, 0x38, 0x0d])
    read_response() 
    # 0x3FC0 - Word 1
    send_cmd([0x23, tk.vsr_addr, 0x53, 0x31, 0x39, 0x43, 0x30, 0x0d])
    read_response()
    send_cmd([0x23, tk.vsr_addr, 0x53, 0x31, 0x41, 0x33, 0x46, 0x0d])
    read_response()   
    
    if variable9.get() == TESTMODEIMAGE[0]:
        # 0x3FFB - Word 2
        send_cmd([0x23, tk.vsr_addr, 0x53, 0x31, 0x42, 0x46, 0x42, 0x0d])
        read_response()
        send_cmd([0x23, tk.vsr_addr, 0x53, 0x31, 0x43, 0x33, 0x46, 0x0d])
        read_response()  
    elif variable9.get() == TESTMODEIMAGE[1]:
        # 0x1FFF - Word 2
        send_cmd([0x23, tk.vsr_addr, 0x53, 0x31, 0x42, 0x46, 0x46, 0x0d])
        read_response()
        send_cmd([0x23, tk.vsr_addr, 0x53, 0x31, 0x43, 0x31, 0x46, 0x0d])
        read_response()  
    elif variable9.get() == TESTMODEIMAGE[2]:
        # 0x3FF7 - Word 2
        send_cmd([0x23, 0x90, 0x53, 0x31, 0x42, 0x46, 0x37, 0x0d])
        read_response()
        send_cmd([0x23, 0x90, 0x53, 0x31, 0x43, 0x33, 0x46, 0x0d])
        read_response()
    elif variable9.get() == TESTMODEIMAGE[3]:
        # 0x3BFF - Word 2
        send_cmd([0x23, 0x90, 0x53, 0x31, 0x42, 0x46, 0x46, 0x0d])
        read_response()
        send_cmd([0x23, 0x90, 0x53, 0x31, 0x43, 0x33, 0x42, 0x0d])
        read_response()           
  
    
def modify_register():
        cmd_string = [0x23, tk.vsr_addr, 0x42, 0x32, 0x34, 0x30, 0x31, 0x0D]
        if variable3.get() == SETCLR[0]:
            print("0x42")
            cmd_string[2] = 0x42
        elif variable3.get() == SETCLR[1]:
            cmd_string[2] = 0x43

        if variable4.get() == REGADDRMSB[0]:
            print("0x30")
            cmd_string[3] = 0x30            
        elif variable4.get() == REGADDRMSB[1]:
            print("0x31")
            cmd_string[3] = 0x31            
        elif variable4.get() == REGADDRMSB[2]:
            print("0x32")
            cmd_string[3] = 0x32            
        elif variable4.get() == REGADDRMSB[3]:
            print("0x33")
            cmd_string[3] = 0x33            
        elif variable4.get() == REGADDRMSB[4]:
            print("0x34")
            cmd_string[3] = 0x34            
        elif variable4.get() == REGADDRMSB[5]:
            print("0x35")
            cmd_string[3] = 0x35            
        elif variable4.get() == REGADDRMSB[6]:
            print("0x36")
            cmd_string[3] = 0x36            
        elif variable4.get() == REGADDRMSB[7]:
            print("0x37")
            cmd_string[3] = 0x37            
        elif variable4.get() == REGADDRMSB[8]:
            print("0x38")
            cmd_string[3] = 0x38            
        elif variable4.get() == REGADDRMSB[9]:
            print("0x39")
            cmd_string[3] = 0x39            
        elif variable4.get() == REGADDRMSB[10]:
            print("0x41")
            cmd_string[3] = 0x41            
        elif variable4.get() == REGADDRMSB[11]:
            print("0x42")
            cmd_string[3] = 0x42            
        elif variable4.get() == REGADDRMSB[12]:
            print("0x43")
            cmd_string[3] = 0x43            
        elif variable4.get() == REGADDRMSB[13]:
            print("0x44")
            cmd_string[3] = 0x44            
        elif variable4.get() == REGADDRMSB[14]:
            print("0x45")
            cmd_string[3] = 0x45            
        elif variable4.get() == REGADDRMSB[15]:
            print("0x46")
            cmd_string[3] = 0x46  
            
        if variable5.get() == REGADDRLSB[0]:
            print("0x30")
            cmd_string[4] = 0x30
        elif variable5.get() == REGADDRLSB[1]:
            print("0x31")
            cmd_string[4] = 0x31
        elif variable5.get() == REGADDRLSB[2]:
            print("0x32")
            cmd_string[4] = 0x32
        elif variable5.get() == REGADDRLSB[3]:
            print("0x33")
            cmd_string[4] = 0x33
        elif variable5.get() == REGADDRLSB[4]:
            print("0x34")
            cmd_string[4] = 0x34
        elif variable5.get() == REGADDRLSB[5]:
            print("0x35")
            cmd_string[4] = 0x35
        elif variable5.get() == REGADDRLSB[6]:
            print("0x36")
            cmd_string[4] = 0x36
        elif variable5.get() == REGADDRLSB[7]:
            print("0x37")
            cmd_string[4] = 0x37
        elif variable5.get() == REGADDRLSB[8]:
            print("0x38")
            cmd_string[4] = 0x38
        elif variable5.get() == REGADDRLSB[9]:
            print("0x39")
            cmd_string[4] = 0x39
        elif variable5.get() == REGADDRLSB[10]:
            print("0x41")
            cmd_string[4] = 0x41
        elif variable5.get() == REGADDRLSB[11]:
            print("0x42")
            cmd_string[4] = 0x42
        elif variable5.get() == REGADDRLSB[12]:
            print("0x43")
            cmd_string[4] = 0x43
        elif variable5.get() == REGADDRLSB[13]:
            print("0x44")
            cmd_string[4] = 0x44
        elif variable5.get() == REGADDRLSB[14]:
            print("0x45")
            cmd_string[4] = 0x45
        elif variable5.get() == REGADDRLSB[15]:
            print("0x46")
            cmd_string[4] = 0x46

        if variable6.get() == BITVALUE[0]:
            print("0x30")
            print("0x31")
            cmd_string[5] = 0x30
            cmd_string[6] = 0x31
        elif variable6.get() == BITVALUE[1]:
            print("0x30")
            print("0x32")
            cmd_string[5] = 0x30
            cmd_string[6] = 0x32
        elif variable6.get() == BITVALUE[2]:
            print("0x30")
            print("0x34")
            cmd_string[5] = 0x30
            cmd_string[6] = 0x34
        elif variable6.get() == BITVALUE[3]:
            print("0x30")
            print("0x38")
            cmd_string[5] = 0x30
            cmd_string[6] = 0x38
        elif variable6.get() == BITVALUE[4]:
            print("0x31")
            print("0x30")
            cmd_string[5] = 0x31
            cmd_string[6] = 0x30
        elif variable6.get() == BITVALUE[5]:
            print("0x32")
            print("0x30")
            cmd_string[5] = 0x32
            cmd_string[6] = 0x30
        elif variable6.get() == BITVALUE[6]:
            print("0x34")
            print("0x30")
            cmd_string[5] = 0x34
            cmd_string[6] = 0x30
        elif variable6.get() == BITVALUE[7]:
            print("0x38")
            print("0x30")
            cmd_string[5] = 0x38
            cmd_string[6] = 0x30
        print(cmd_string)
        send_cmd(cmd_string)
        ret = read_response()
        print(ret)


def initialise_system():
    # Does init, load, set up, write, enable, calibrate all in one fell swoooop
    start = time.time()
    try:
        print(" -=-=-=-=-=-=-=-=-  Setup System to config VSR 2.. -=-=-=-=-=-=-=-=- ")
        variable1.set(OPTIONS[2])
        print("variable1: ", variable1.get())
        initialise_sensor()
        print(" -=-=-=-=- sensors initialised! -=-=-=-=- ")
        load_pwr_cal_read_enables()
        print(" -=-=-=-=- load power / calibrate / read / whatever / done! -=-=-=-=- ")
        set_up_state_machine()
        print(" -=-=-=-=- state machine set up! -=-=-=-=- ")
        write_dac_values()
        print(" -=-=-=-=- dac values written! -=-=-=-=- ")
        enable_adc()
        print(" -=-=-=-=- adc enabled! -=-=-=-=- ")
        calibrate_sensor()
        print(" -=-=-=-=- VSR 2 all Done -=-=-=-=-")
    except Exception as e:
        print(("Failed to initialise VSR2: %s" % e))
        return

    time.sleep(1)

    try:
        print(" -=-=-=-=-=-=-=-=-  Setup System to config VSR 1.. -=-=-=-=-=-=-=-=- ")
        variable1.set(OPTIONS[0])
        print("variable1: ", variable1.get())
        initialise_sensor()
        print(" -=-=-=-=- sensors initialised! -=-=-=-=- ")
        load_pwr_cal_read_enables()
        print(" -=-=-=-=- load power / calibrate / read / whatever / done! -=-=-=-=- ")
        set_up_state_machine()
        print(" -=-=-=-=- state machine set up! -=-=-=-=- ")
        write_dac_values()
        print(" -=-=-=-=- dac values written! -=-=-=-=- ")
        enable_adc()
        print(" -=-=-=-=- adc enabled! -=-=-=-=- ")
        calibrate_sensor()
        print(" -=-=-=-=- VSR 1 all Done -=-=-=-=-")
    except Exception as e:
        print(("Failed to initialise VSR1: %s" % e))
        return
    stop = time.time()
    print(" -=-=-=-=- Took %s seconds -=-=-=-=-" %(stop - start))


root = tk.Tk()
frame = tk.Frame(root)
frame.pack()

variable1 = tk.StringVar(frame)
variable1.set(OPTIONS[0]) # default value
variable2 = tk.StringVar(frame)
variable2.set(IMAGE[0]) # default value
variable3 = tk.StringVar(frame)
variable3.set(SETCLR[0]) # default value
variable4 = tk.StringVar(frame)
variable4.set(REGADDRMSB[2]) # default value
variable5 = tk.StringVar(frame)
variable5.set(REGADDRLSB[4]) # default value
variable6 = tk.StringVar(frame)
variable6.set(BITVALUE[0]) # default value
variable7 = tk.StringVar(frame)
variable7.set(DARKCORRECTION[0]) # default value
variable8 = tk.StringVar(frame)
variable8.set(READOUTMODE[1]) # default value
variable9 = tk.StringVar(frame)
variable9.set(TESTMODEIMAGE[0]) # default value

w1 = tk.OptionMenu(frame, variable1, *OPTIONS)
w1.pack(side=tk.BOTTOM)
w8 = tk.OptionMenu(frame, variable8, *READOUTMODE)
w8.pack(side=tk.BOTTOM)
w2 = tk.OptionMenu(frame, variable2, *IMAGE)
w2.pack(side=tk.BOTTOM)
w3 = tk.OptionMenu(frame, variable3, *SETCLR)
w3.pack(side=tk.BOTTOM)
w4 = tk.OptionMenu(frame, variable4, *REGADDRMSB)
w4.pack(side=tk.BOTTOM)
w5 = tk.OptionMenu(frame, variable5, *REGADDRLSB)
w5.pack(side=tk.BOTTOM)
w6 = tk.OptionMenu(frame, variable6, *BITVALUE)
w6.pack(side=tk.BOTTOM)
w7 = tk.OptionMenu(frame, variable7, *DARKCORRECTION)
w7.pack(side=tk.BOTTOM)
w9 = tk.OptionMenu(frame, variable9, *TESTMODEIMAGE)
w9.pack(side=tk.BOTTOM)

button0 = tk.Button(frame, 
                   text="CONNECT", 
                   fg="green",
                   command=cam_connect)
button0.pack(side=tk.BOTTOM)

button101 = tk.Button(frame,
                      text="INIT_SYSTEM",
                      fg="CYAN",
                      command=initialise_system)
button101.pack(side=tk.BOTTOM)

button2 = tk.Button(frame, 
                   text="INITIALISE", 
                   fg="red",
                   command=initialise_sensor)
button2.pack(side=tk.BOTTOM)
button7 = tk.Button(frame, 
                   text="LOAD PWR/CAL/READ ENABLES", 
                   fg="red",
                   command=load_pwr_cal_read_enables)
button7.pack(side=tk.BOTTOM)
button6 = tk.Button(frame, 
                   text="SET UP SM", 
                   fg="red",
                   command=set_up_state_machine)
button6.pack(side=tk.BOTTOM)
button8 = tk.Button(frame, 
                   text="WRITE DAC VALUES", 
                   fg="red",
                   command=write_dac_values)
button8.pack(side=tk.BOTTOM)
button9 = tk.Button(frame, 
                   text="ENABLE ADC", 
                   fg="red",
                   command=enable_adc)
button9.pack(side=tk.BOTTOM)
button10 = tk.Button(frame, 
                   text="ENABLE ADC TESTMODE", 
                   fg="red",
                   command=enable_adc_testmode)
button10.pack(side=tk.BOTTOM)
button4 = tk.Button(frame, 
                   text="CALIBRATE", 
                   fg="red",     
                   command=calibrate_sensor)
button4.pack(side=tk.BOTTOM)

textBox = tk.Text(root, height=1, width=20)
textBox.insert(tk.END, 'filename')
textBox.pack()
entry_2 = tk.Entry(root)
entry_2.pack()
button5 = tk.Button(frame, 
                   text="AQUIRE DATA", 
                   fg="red",
                   command=acquire_data)
button5.pack(side=tk.BOTTOM)
button1 = tk.Button(frame, 
                   text="DISS-CONNECT", 
                   fg="red",
                   command=cam_disconnect)
button1.pack(side=tk.BOTTOM)
button12 = tk.Button(frame, 
                   text="MODIFY_REGISTER", 
                   fg="green",
                   command=modify_register)
# button12["state"] = "disabled"
button12.pack(side=tk.BOTTOM)
button13 = tk.Button(frame, 
                   text="READ VOLTAGES", 
                   fg="green")
button13["state"] = "disabled"
button13.pack(side=tk.BOTTOM)

label1 = tk.Label(frame, text="Links Not Locked")
label1.pack()

entry_2.insert(0, 10)

root.mainloop()
