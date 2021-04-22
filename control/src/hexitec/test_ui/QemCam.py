#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:58:52 2018

@author: rha73
"""

from RdmaUDP import RdmaUDP
from ImageStreamUDP import ImageStreamUDP
import time
import cv2
import h5py


class QemCam(object):

    def __init__(self, debug=False):
        self.debug = debug
        # qem 1 ctrl_ip addresses
        self.server_ctrl_ip_addr = "10.0.2.2"
        self.camera_ctrl_ip_addr = "10.0.2.1"
        # qem 1 data_ip addresses
        self.server_data_ip_addr = "10.0.4.2"
        self.camera_data_ip_addr = "10.0.4.1"
        # qem 1 base addresses
        self.top_reg = 0x60000000
        self.mon_data_in = 0x70000000
        self.sequencer = 0xB0000000
        self.receiver = 0xC0000000
        self.frm_gate = 0xD0000000
        #
        self.image_size_x = 0x100
        self.image_size_y = 0x100
        self.image_size_p = 0x8
        self.image_size_f = 0x8

        self.debug_level = -1
        self.delay = 0
        self.strm_mtu = 8000
        #
        self.frame_time = 1

    def __del__(self):
        self.x10g_rdma.close()
        self.x10g_stream.close()

    def connect(self):
        self.x10g_rdma = RdmaUDP(self.server_ctrl_ip_addr, 61650, self.server_ctrl_ip_addr, 61651,
                                 self.camera_ctrl_ip_addr, 61651, 2000000, 9000, 20, self.debug)
        self.x10g_rdma.setDebug(self.debug)
        self.x10g_rdma.ack = True

        self.x10g_stream = ImageStreamUDP(self.server_data_ip_addr, 61650, self.server_data_ip_addr, 61651,
                                          self.camera_data_ip_addr, 61651, 1000000000, 9000, 20, self.debug)
        # self.x10g_stream.setDebug(False)
        # self.x10g_stream.ack = False

        return self.x10g_rdma.error_OK

    def set_image_size(self, x_size, y_size, p_size, f_size):
        # Set image size globals
        self.image_size_x = x_size
        self.image_size_y = y_size
        self.image_size_p = p_size
        self.image_size_f = f_size
        # Check parameters againts ethernet packet and local link frame size compatibility
        pixel_count_max = x_size * y_size
        number_bytes = pixel_count_max * 2
        number_bytes_r4 = pixel_count_max % 4
        number_bytes_r8 = number_bytes % 8
        first_packets = number_bytes // self.strm_mtu
        last_packet_size = number_bytes % self.strm_mtu
        lp_number_bytes_r8 = last_packet_size % 8
        lp_number_bytes_r32 = last_packet_size % 32
        size_status = number_bytes_r4 + number_bytes_r8 + lp_number_bytes_r8 + lp_number_bytes_r32
        # Calculate pixel packing settings
        if p_size >= 11 and p_size <= 14 and f_size == 16:
            pixel_count_max = pixel_count_max // 2
        elif p_size == 8 and f_size == 8:
            pixel_count_max = pixel_count_max // 4
        else:
            size_status = size_status + 1

        # Set up registers if no size errors
        if size_status != 0:
            print("%-32s %8i %8i %8i %8i %8i %8i" % ("-> size error", number_bytes, number_bytes_r4,
                                                     number_bytes_r8, first_packets,
                                                     lp_number_bytes_r8, lp_number_bytes_r32))
        else:
            address = self.receiver | 0x01
            data = (pixel_count_max & 0x1FFFF) - 1
            self.x10g_rdma.write(address, data, "pixel count max")
            self.x10g_rdma.write(self.receiver + 4, 0x3, "pixel bit size => 16 bit")

        self.x10g_stream.set_image_size(x_size, y_size, f_size)

    def frame_gate_trigger(self):
        self.x10g_rdma.write(self.frm_gate + 0, 0x0, "frame gate trigger off")
        self.x10g_rdma.write(self.frm_gate + 0, 0x1, "frame gate trigger on")
        self.x10g_rdma.write(self.frm_gate + 0, 0x0, "frame gate trigger off")

    def frame_gate_settings(self, frame_number, frame_gap):
        self.x10g_rdma.write(self.frm_gate + 1, frame_number, "frame gate frame number")
        self.x10g_rdma.write(self.frm_gate + 2, frame_gap, "frame gate frame gap")

    def display_image_stream(self, num_images):
        self.frame_gate_settings(0, 0)
        image_count = 1
        while image_count <= num_images:
            self.frame_gate_trigger()
            print("Triggering")
            sensor_image = self.x10g_stream.get_image()
            cv2.imshow("image", sensor_image)
            cv2.waitKey(self.frame_time)
            image_count = image_count + 1

    def log_image_stream(self, file_name, num_images):
        self.frame_gate_settings(num_images - 1, 0)
        self.frame_gate_trigger()
        # Get the image set
        image_set = self.x10g_stream.get_image_set(num_images)
        # Write to hdf5 file
        file_name = file_name + ".h5"
        h5f = h5py.File(file_name, "w")
        h5f.create_dataset("dataset_1", data=image_set)
        h5f.close()

    def data_stream(self, num_images):
        self.frame_gate_settings(num_images - 1, 0)
        self.frame_gate_trigger()

    def log_image_stream_bin(self, file_name, num_images):
        self.frame_gate_settings(num_images - 1, 0)
        self.frame_gate_trigger()
        # Get the image set
        image_set = self.x10g_stream.get_image_set(num_images)
        # Write to binary file n * x * y uint16
        file_name = file_name + ".bin"

        f = open(file_name, "wb")
        f.write(image_set)
        f.close()

        print("written array:", image_set.shape, image_set.dtype, "->", file_name)

    def disconnect(self):
        self.x10g_rdma.close()
        self.x10g_stream.close()
