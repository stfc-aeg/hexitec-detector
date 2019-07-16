
#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:58:52 2018

@author: rha73
"""

import sys
import numpy as np
from RdmaUDP import *
from ImageStreamUDP import *
from socket import error as socket_error
import time
import numpy as np
import cv2
import h5py

class QemCam(object):

    def __init__(self):
        # qem 1 ctrl_ip addresses
        self.server_ctrl_ip_addr='10.0.2.2'
        self.camera_ctrl_ip_addr='10.0.2.1'
        # qem 1 data_ip addresses
        self.server_data_ip_addr = "10.0.4.2" #"10.0.1.2"
        self.camera_data_ip_addr = "10.0.4.1" #"10.0.1.1"
        # qem 1 base addresses
        self.udp_10G_data    = 0x00000000 
        self.udp_10g_control = 0x10000000
        self.frame_gen_0     = 0x20000000
        self.frm_chk_0       = 0x30000000
        self.frm_gen_1       = 0x40000000
        self.frm_chk_1       = 0x50000000 
        self.top_reg         = 0x60000000
        self.mon_data_in     = 0x70000000
        self.mon_data_out    = 0x80000000
        self.mon_rdma_in     = 0x90000000
        self.mon_rdma_out    = 0xA0000000
        self.sequencer       = 0xB0000000
        self.receiver        = 0xC0000000
        self.frm_gate        = 0xD0000000
        self.Unused_0        = 0xE0000000
        self.Unused_1        = 0xF0000000
        #
        self.image_size_x    = 0x100
        self.image_size_y    = 0x100
        self.image_size_p    = 0x8
        self.image_size_f    = 0x8
        
        self.pixel_extract   = [16,14,13,12,11]
        #
        self.debug_level = -1
        self.delay = 0
        self.strm_mtu = 8000
        self.rdma_mtu = 8000
        #
        self.frame_time = 1
        ### DEBUGGING ###
        self.udp_connection = True

    def __del__(self):
        self.x10g_rdma.close()
        #TODO: Redundant: ?
        if self.udp_connection: self.x10g_stream.close()
        
    def connect(self):
        try:
            self.x10g_rdma = RdmaUDP(self.server_ctrl_ip_addr, 61650, self.server_ctrl_ip_addr, 61651,
                                    self.camera_ctrl_ip_addr, 61650, self.camera_ctrl_ip_addr, 61651, 2000000, 9000, 20)
            self.x10g_rdma.setDebug(False)
            self.x10g_rdma.ack = True
        except socket_error as e:
            raise socket_error("Failed to setup Control connection: %s" % e)

        try:
            #TODO: Redundant: ?
            if self.udp_connection:
                self.x10g_stream = ImageStreamUDP(self.server_data_ip_addr, 61650, self.server_data_ip_addr, 61651,
                                                self.camera_data_ip_addr, 61650, self.camera_data_ip_addr, 61651, 1000000000, 9000, 20)
        except socket_error as e:
            raise socket_error("Failed to setup Data connection: %s" % e)

        return
    
    def print_ram_depth(self):
        ram_depth = self.x10g_rdma.read(0xB0000010, 'qem sequencer ram depth reg 0')
        print "%-32s %-8i" % ("-> sequencer ram depth :" ,ram_depth/8 )
        time.sleep(self.delay)
        return
    
    def stop_sequencer(self):
        #print "%-32s %s" % ("-> Stopping sequencer:", "")
        self.x10g_rdma.write(0xB0000000, 0x0, 'qem seq null')
        time.sleep(self.delay)
        self.x10g_rdma.write(0xB0000000, 0x2, 'qem seq stop')
        time.sleep(self.delay)
        return
    
    def start_sequencer(self):
        #print "%-32s %s" % ("-> Starting sequencer:", "")
        self.x10g_rdma.write(0xB0000000, 0x0, 'qem seq null')
        time.sleep(self.delay)
        self.x10g_rdma.write(0xB0000000, 0x1, 'qem seq stop')
        time.sleep(self.delay)
        return
    def set_test_mode(self):
        self.x10g_rdma.write(self.receiver, 0x1, 'select camera test mode')
        return
    def unset_test_mode(self):
        self.x10g_rdma.write(self.receiver, 0x0, 'select camera test mode')
        return
    def start_test_mode(self):
        self.x10g_rdma.write(self.receiver, 0x3, 'select camera test mode')
        return
    
    def get_aligner_status(self):
        address = self.receiver | 0x14
        aligner_status = self.x10g_rdma.read(address, 'aligner status word')
        aligner_status_0 = aligner_status & 0xFFFF
        aligner_status_1 = aligner_status >> 16 & 0xFFFF
        #print "%-32s %04X %04X" % ("-> aligner status:" ,aligner_status_1, aligner_status_0)
        time.sleep(self.delay)
        return [aligner_status_1, aligner_status_0]
    
    def set_idelay(self, data_1=0x00,cdn_1=0x00, data_0=0x00, cdn_0=0x00):
        #print data_1, cdn_1, data_0, cdn_0
        data_cdn_word = data_1 << 24 | cdn_1 << 16 | data_0 << 8 | cdn_0
        address = self.receiver | 0x02
        #print "%-32s %08X" % ('-> set data cdn idelay control word:', data_cdn_word)
        self.x10g_rdma.write(address, data_cdn_word, 'data_cdn_idelay word')
        #issue load command
        address = self.receiver | 0x00
        self.x10g_rdma.write(address, 0x00, 'set delay load low')
        self.x10g_rdma.write(address, 0x10, 'set delay load high')
        self.x10g_rdma.write(address, 0x00, 'set delay load low')
        address = self.receiver | 0x12
        data_cdn_idelay_word = self.x10g_rdma.read(address, 'data_cdn_idelay word')
        return data_cdn_idelay_word
    
    def set_ivsr(self, data_1=0x00, data_0=0x00, cdn_1=0x00, cdn_0=0x00):
        #print data_1, cdn_1, data_0, cdn_0
        data_cdn_word = data_1 << 24 | data_0 << 16 | cdn_1 << 8 | cdn_0
        address = self.receiver | 0x03
        #print "%-32s %08X" % ('-> set data cdn idelay control word:', data_cdn_word)
        self.x10g_rdma.write(address, data_cdn_word, 'data_cdn_ivsr word')
        return
    
    def set_scsr(self, data_1=0x00, data_0=0x00, cdn_1=0x00, cdn_0=0x00):
        #print data_1, cdn_1, data_0, cdn_0
        data_cdn_word = data_1 << 24 | data_0 << 16 | cdn_1 << 8 | cdn_0
        address = self.receiver | 0x05
        #print "%-32s %08X" % ('-> set data cdn idelay control word:', data_cdn_word)
        self.x10g_rdma.write(address, data_cdn_word, 'data_cdn_ivsr word')
        return
    
    def set_pixel_count_per_image(self, pixel_count_max):
        
        number_bytes = pixel_count_max * 2
        number_bytes_r4 = pixel_count_max % 4
        number_bytes_r8 = number_bytes % 8
        first_packets = number_bytes/self.strm_mtu
        last_packet_size = number_bytes % self.strm_mtu
        lp_number_bytes_r8 = last_packet_size % 8
        lp_number_bytes_r32 = last_packet_size % 32
        size_status = number_bytes_r4 + number_bytes_r8 + lp_number_bytes_r8 + lp_number_bytes_r32
        
        if size_status != 0:
            print "%-32s %8i %8i %8i %8i %8i %8i" % ('-> size error', number_bytes, number_bytes_r4, number_bytes_r8, first_packets, lp_number_bytes_r8, lp_number_bytes_r32 )
        else:   
            address = self.receiver | 0x01
            data = (pixel_count_max & 0x1FFFF) -1
            self.x10g_rdma.write(address, data, 'pixel count max')
        return
    
    #TODO: Redundant: ?
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
        first_packets = number_bytes/self.strm_mtu
        last_packet_size = number_bytes % self.strm_mtu
        lp_number_bytes_r8 = last_packet_size % 8
        lp_number_bytes_r32 = last_packet_size % 32
        size_status = number_bytes_r4 + number_bytes_r8 + lp_number_bytes_r8 + lp_number_bytes_r32
        # calculate pixel packing settings
        if p_size >= 11 and p_size <= 14 and f_size == 16:
            pixel_extract = self.pixel_extract.index(p_size)
            pixel_count_max = pixel_count_max/2
        elif p_size == 8 and f_size == 8:
            pixel_extract = self.pixel_extract.index(p_size*2)
            pixel_count_max = pixel_count_max/4
        else:
            size_status =size_status + 1
            
        # set up registers if no size errors     
        if size_status != 0:
            print "%-32s %8i %8i %8i %8i %8i %8i" % ('-> size error', number_bytes, number_bytes_r4, number_bytes_r8, first_packets, lp_number_bytes_r8, lp_number_bytes_r32 )
        else:   
            address = self.receiver | 0x01
            data = (pixel_count_max & 0x1FFFF) -1
            self.x10g_rdma.write(address, data, 'pixel count max')
            self.x10g_rdma.write(self.receiver+4, 0x3, 'pixel bit size => 16 bit')
            
        #TODO: Redundant: ?
        if self.udp_connection: self.x10g_stream.set_image_size(x_size, y_size, f_size)    # MAYBE, sets vars used elsewhere in ISUDP..?

        return
    
    def set_sub_image_merge_factor(self, merger_factor):
        
        return
    
    def get_idelay_lock_status(self):
        address = self.receiver | 0x13
        #print "%-32s %08X" % ('-> set data cdn idelay control word:', data_cdn_word)
        data_locked_word = self.x10g_rdma.read(address, 'data_cdn_idelay word')
        data_locked_flag = data_locked_word & 0x00000001
        return data_locked_flag
    
    def get_cdn_data_timing_values(self):
        address = self.receiver | 0x16
        cdn_data_timing_word_0 = self.x10g_rdma.read(address, 'cdn-data timing word')
        address = self.receiver | 0x17
        cdn_data_timing_word_1 = self.x10g_rdma.read(address, 'cdn-data timing word')
        address = self.receiver | 0x15
        cdn_data_timing_valid_word = self.x10g_rdma.read(address, 'cdn-data timing word')
        
        cdn_cdn_gap_0  = cdn_data_timing_word_0 >>  0 & 0xFF
        cdn_sub_pat_0  = cdn_data_timing_word_0 >>  8 & 0xFF
        cdn_dat_gap_0  = cdn_data_timing_word_0 >> 16 & 0xFF
        data_sub_pat_0 = cdn_data_timing_word_0 >> 24 & 0xFF
        cdn_data_timing_bytes_0 = [cdn_cdn_gap_0,cdn_sub_pat_0, cdn_dat_gap_0, data_sub_pat_0]
        
        cdn_cdn_gap_1  = cdn_data_timing_word_1 >>  0 & 0xFF
        cdn_sub_pat_1  = cdn_data_timing_word_1 >>  8 & 0xFF
        cdn_dat_gap_1  = cdn_data_timing_word_1 >> 16 & 0xFF
        data_sub_pat_1 = cdn_data_timing_word_1 >> 24 & 0xFF
        cdn_data_timing_bytes_1 = [cdn_cdn_gap_1,cdn_sub_pat_1, cdn_dat_gap_1, data_sub_pat_1]
        
        cdn_data_timing_valid_flag_0 = cdn_data_timing_valid_word & 0x01
        cdn_data_timing_valid_flag_1 = cdn_data_timing_valid_word >> 1 & 0x01
        return [cdn_data_timing_bytes_1, cdn_data_timing_bytes_0, cdn_data_timing_valid_flag_0, cdn_data_timing_valid_flag_1]
    
    def turn_rdma_debug_0n(self):
        self.x10g_rdma.debug = True
        return
    
    def turn_rdma_debug_0ff(self):
        self.x10g_rdma.debug = False
        return
    
        
    def load_vectors_from_file(self, vector_file_name='default.txt'):
        print "%-32s %s" % ("-> loading vector file:",vector_file_name)

        #extract lines into array
        with open(vector_file_name, 'r') as f:
            data = f.readlines()
          
            init_length  = int(data[0])
            loop_length  = int(data[1])
            #signal_names = data[2]
            
            #format_data = "%64s" % data[0]
            #print format_data
          
            number_vectors = len(data)-3
          
            print "%-32s %-8i" % ("-> vectors loaded:" ,number_vectors)
            print "%-32s %-8i" % ("-> loop position :" ,loop_length)
            print "%-32s %-8i" % ("-> init position :" ,init_length )
            f.close()
            
        self.stop_sequencer()
        
        #load sequencer RAM
        print "%-32s %s" % ("-> Loading Sequncer RAM:", "")
        for seq_address in range(number_vectors):
            words = data[seq_address+3].split()
            format_words = "%64s" % words[0]
            vector = int(words[0],2)
            lower_vector_word = vector & 0xFFFFFFFF
            upper_vector_word = vector >> 32
            if self.debug_level == 0 : print "%64s %016X %8X %8X" % (format_words, vector, upper_vector_word, lower_vector_word)
            #load fpga block ram
            ram_address = seq_address * 2 + 0xB1000000
            self.x10g_rdma.write(ram_address, lower_vector_word, 'qem seq ram loop 0')
            time.sleep(self.delay)
            ram_address = ram_address + 1
            self.x10g_rdma.write(ram_address, upper_vector_word, 'qem seq ram loop 0')
            time.sleep(self.delay)
            
        #set init  limit
        self.x10g_rdma.write(0xB0000001, init_length - 1, 'qem seq init limit')
        
        time.sleep(self.delay)
        
        #set loop limit
        self.x10g_rdma.write(0xB0000002, loop_length - 1, 'qem seq loop limit')
        time.sleep(self.delay)
          
        self.start_sequencer()
        
        return
    
    def restart_sequencer(self):
        self.stop_sequencer()
        self.start_sequencer()
        return
    
    def frame_gate_trigger(self):
        self.x10g_rdma.write(self.frm_gate+0,0x0,          'frame gate trigger off')
        self.x10g_rdma.write(self.frm_gate+0,0x1,          'frame gate trigger on')
        self.x10g_rdma.write(self.frm_gate+0,0x0,          'frame gate trigger off')
        return
        
    def frame_gate_settings(self, frame_number, frame_gap):
        #self.x10g_rdma.write(self.frm_gate+1,frame_number, 'frame gate frame number')
        self.x10g_rdma.write(self.frm_gate+1,frame_number, 'frame gate frame number')
        self.x10g_rdma.write(self.frm_gate+2,frame_gap,    'frame gate frame gap')
        return

    #TODO: Redundant ?
    def display_image_stream(self, num_images):
        if self.udp_connection: 
            self.frame_gate_settings(0, 0)
            self.frame_gate_settings(num_images-1, 0)
            image_count = 1
            if self.udp_connection:
                print "UDP streaming disabled, aborting.."
                return
            while image_count <= num_images :  
                self.frame_gate_trigger()    
                print "Triggering"
                sensor_image = self.x10g_stream.get_image()
                cv2.imshow('image',sensor_image)
                cv2.waitKey(self.frame_time)
                image_count = image_count+1                
        return

    def log_image_stream(self, file_name, num_images):
        self.frame_gate_settings(num_images-1, 0)
        self.frame_gate_trigger()
        # Redundant: ?
        if self.udp_connection: 
            #get the image set
            print "\t\t log_image_stream() 4"
            image_set = self.x10g_stream.get_image_set(num_images)
            print "\t\t log_image_stream() 5"
            #write to hdf5 file
            file_name = file_name + '.h5'
            h5f = h5py.File(file_name,'w')
            h5f.create_dataset('dataset_1', data=image_set)
            h5f.close()
        
        #print image_set
        return

    def data_stream(self, num_images):
        self.frame_gate_settings(num_images-1, 0)
        self.frame_gate_trigger()
        return

    #TODO: Redundant ?
    def log_image_stream_bin(self, file_name, num_images):
        if self.udp_connection:
            self.frame_gate_settings(num_images-1, 0)
            self.frame_gate_trigger()
            #get the image set
            image_set = self.x10g_stream.get_image_set(num_images)
            #write to binary file n * x * y uint16
            file_name = file_name + '.bin'
            f=open(file_name,"wb")
            f.write(image_set)
            f.close()
            
            print "written array:", image_set.shape, image_set.dtype,"->", file_name
        return

    
    def frame_stats(self):
        
        self.x10g_rdma.read(self.mon_data_in+0x10, 'frame last length')
        self.x10g_rdma.read(self.mon_data_in+0x11, 'frame max length')
        self.x10g_rdma.read(self.mon_data_in+0x12, 'frame min length')
        self.x10g_rdma.read(self.mon_data_in+0x13, 'frame number')
        self.x10g_rdma.read(self.mon_data_in+0x14, 'frame last clock cycles')
        self.x10g_rdma.read(self.mon_data_in+0x15, 'frame max clock cycles')
        self.x10g_rdma.read(self.mon_data_in+0x16, 'frame min clock cycles')
        self.x10g_rdma.read(self.mon_data_in+0x17, 'frame data total')
        self.x10g_rdma.read(self.mon_data_in+0x18, 'frame data total clock cycles')
        self.x10g_rdma.read(self.mon_data_in+0x19, 'frame trigger count')
        self.x10g_rdma.read(self.mon_data_in+0x1A, 'frame in progress flag')
        
        return
    
    
    def set_clock(self):
        print "-> set clock not implemented yet..."
        return
    
    def i2c_write(self,address=0x0, data=0x0):
        print "-> set clock not implemented yet..."
        
        return
    
    def i2c_read(self, i2c_addr=0x0):
        print "-> set clock not implemented yet..."
        #setup i2c read command - read + address + data
        address = self.top_reg | 0x08
        i2c_address = i2c_addr & 0x7F
        i2c_cmd_addr_data = 0x8000 | i2c_address << 8 
        self.x10g_rdma.write(address, i2c_cmd_addr_data, 'i2c cmd-address-data')
        # i2c trigger command
        address = self.top_reg | 0x09
        self.x10g_rdma.write(address, 0x0, 'i2c trigger low')
        self.x10g_rdma.write(address, 0x1, 'i2c trigger high')
        self.x10g_rdma.write(address, 0x0, 'i2c trigger low')
        #poll until done
        time.sleep(0.01)
        # check error status
        i2c_status = self.x10g_rdma.read(address, 0x0, 'i2c status')
        if i2c_status != 0x0 :
            print "%-32s %1X" % ("-> i2c satus:", i2c_status)
        # read i2c data
        address = self.top_reg | 0x18
        i2c_data = self.x10g_rdma.read(address, 'i2c read data') & 0xFF
        return i2c_data
        
    def disconnect(self):
        self.x10g_rdma.close()
        if self.udp_connection: self.x10g_stream.close()
        return
