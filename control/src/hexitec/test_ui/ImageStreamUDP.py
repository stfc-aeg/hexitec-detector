#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 16:53:18 2018

@author: rha73
"""

import socket
import numpy as np


class ImageStreamUDP(object):

    def __init__(self, MasterTxUDPIPAddress='192.168.0.1', MasterTxUDPIPPort=65535,
                 MasterRxUDPIPAddress='192.168.0.1', MasterRxUDPIPPort=65536,
                 TargetRxUDPIPAddress='192.168.0.2', TargetRxUDPIPPort=65536,
                 RxUDPBuf=1024, UDPMTU=9000, UDPTimeout=10, debug=False):

        self.debug = debug
        if self.debug:
            print("ImageStreamUDP")
            print("  RDMA IP addresses")
            print("	\t rxsocket.bind({}, {})".format(MasterRxUDPIPAddress, MasterRxUDPIPPort))
            print("	\t txsocket.bind({}, {})".format(MasterTxUDPIPAddress, MasterTxUDPIPPort))
            print("___________________________________________________________ ")

        self.txsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rxsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.rxsocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RxUDPBuf)

        self.rxsocket.bind((MasterRxUDPIPAddress, MasterRxUDPIPPort))
        self.txsocket.bind((MasterTxUDPIPAddress, MasterTxUDPIPPort))

        self.rxsocket.setblocking(1)

        self.UDPMaxRx = UDPMTU

        self.check_trailer = False

        self.ack = False

        self.image_size_p = 2
        self.image_size_x = 256
        self.sensor_image_1d = np.uint16(np.random.rand(256*256)*32768)
        self.image_size_y = 256
        self.image_mtu = 8000
        self.num_pkt = (self.image_size_x * self.image_size_y * self.image_size_p) // self.image_mtu

        self.sensor_image = np.uint16(np.random.rand(256, 256)*16384)
        self.sensor_image_1d = np.uint16(np.random.rand(256*256)*16384)

    def __del__(self):
        self.txsocket.close()
        self.rxsocket.close()

    def close(self):
        self.txsocket.close()
        self.rxsocket.close()

    def set_image_size(self, x_size, y_size, f_size):
        self.image_size_x = x_size
        self.image_size_y = y_size
        self.sensor_image = np.uint16(np.random.rand(x_size, y_size) * 65535)
        self.sensor_image_1d = np.uint16(np.random.rand(x_size * y_size) * 65535)
        self.sensor_image_ro = np.uint16(np.random.rand(x_size * y_size) * 65535)
        data_size = x_size * y_size * f_size//8
        self.num_pkt = data_size // self.image_mtu
        data_rem = data_size % self.image_mtu
        if data_rem != 0:
            self.num_pkt = self.num_pkt + 1

        print(x_size, y_size, f_size, self.num_pkt)

        return

    def get_image(self):
        pkt_num = 0
        insert_point = 0
        while pkt_num < self.num_pkt:
            # Receive packet up to 8K Bytes
            pkt = self.rxsocket.recv(9000)
            # Extract trailer
            pkt_len = len(pkt)
            if self.check_trailer:
                pkt_top = pkt_len - 8
                frame_number = (ord(pkt[pkt_top+3]) << 24) + (ord(pkt[pkt_top+2]) << 16) + (ord(pkt[pkt_top+1]) << 8) + ord(pkt[pkt_top+0])
                packet_number = (ord(pkt[pkt_top+7]) << 24) + (ord(pkt[pkt_top+6]) << 16) + (ord(pkt[pkt_top+5]) << 8) + ord(pkt[pkt_top+4])
                pkt_str = "%08X %08X %08X %08X" % (pkt_num, pkt_len, frame_number, packet_number)
                print(pkt_str)
            pld_len = (pkt_len-8)//2
            # Build image
            pkt_str = "%08X %08X %08X %08X %08X" % (insert_point, pkt_num, pkt_len, self.num_pkt, pld_len)
            print(pkt_str)
            # print "Printing Header"
            data0 = (ord(pkt[3]) << 24) + (ord(pkt[2]) << 16) + (ord(pkt[1]) << 8) + ord(pkt[0])
            data1 = (ord(pkt[7]) << 24) + (ord(pkt[6]) << 16) + (ord(pkt[5]) << 8) + ord(pkt[4])
            pkt_str = "%08X %08X %08X" % (data1, data0, pkt_num)
            print(pkt_str)
            pkt_array_1d = np.fromstring(pkt[8:], dtype=np.uint16, count=pld_len)
            self.sensor_image_1d[insert_point:insert_point + pld_len] = pkt_array_1d
            insert_point = insert_point + pld_len
            pkt_num = pkt_num + 1
        pixel_count = 0
        for k in range(0, 80):
            for j in range(0, 4):
                for i in range(0, 20):
                    self.sensor_image_ro[pixel_count] = self.sensor_image_1d[(i*4)+j+(k*80)]
                    pixel_count = pixel_count + 1
        print("Pixel Count A")
        print(pixel_count)
        self.sensor_image = self.sensor_image_ro.reshape(self.image_size_x, self.image_size_y)
        return self.sensor_image

    def get_image_set(self, num_images):
        image_array = np.zeros((num_images, self.image_size_x, self.image_size_y), dtype=np.uint16)
        img_num = 0
        while img_num <= num_images-1:
            pkt_num = 1
            insert_point = 0
            while pkt_num <= self.num_pkt:
                # Receive packet up to 8K Bytes
                pkt = self.rxsocket.recv(9000)
                # Extract trailer
                pkt_len = len(pkt)
                print("Image Number:-", img_num)
                print("Packet Length:-", pkt_len)
                pld_len = (pkt_len-8)//2

                pkt_array_1d = np.fromstring(pkt[8:], dtype=np.uint16, count=pld_len)
                self.sensor_image_1d[insert_point:insert_point + pld_len] = pkt_array_1d
                insert_point = insert_point + pld_len

                pkt_num = pkt_num + 1

            image_array[img_num] = self.sensor_image_1d.reshape(self.image_size_x, self.image_size_y)
            img_num = img_num + 1
        return image_array
