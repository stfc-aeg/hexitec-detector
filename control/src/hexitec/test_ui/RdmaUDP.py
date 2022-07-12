"""
Rdma - UDP 10 G access.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

import socket
import struct
import time


class RdmaUDP(object):

    def __init__(self, local_ip='192.168.0.1', local_port=65535,
                 rdma_ip='192.168.0.2', rdma_port=65536,
                 UDPMTU=9000, UDPTimeout=5, debug=False):

        self.debug = debug
        if self.debug:
            print("RdmaUDP:")
            print("	Binding: ({}, {})".format(local_ip, local_port))
            print(" Send to: ({}, {})".format(rdma_ip, rdma_port))
            print("___________________________________________________________ ")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(UDPTimeout)
        self.error_OK = True

        try:
            self.socket.bind((local_ip, local_port))
        except socket.error as e:
            error_string = "  Error: '{}' ".format(e)
            error_string += "on TX Socket: {}:{}".format(local_ip, local_port)
            print(error_string)
            self.error_OK = False

        self.rdma_ip = rdma_ip
        self.rdma_port = rdma_port
        self.UDPMaxRx = UDPMTU
        self.ack = False

    def __del__(self):
        self.socket.close()

    def read(self, address, comment=''):
        command = struct.pack('=BBBBI', 2, 0, 0, 1, address)
        data = 0
        try:
            self.socket.sendto(command, (self.rdma_ip, self.rdma_port))
            if self.ack:
                print("Read is going for acknowledgement receiving data..")
                # Receive acknowledge packet
                response = self.socket.recv(self.UDPMaxRx)
                data = 0x00000000
                if len(response) == 12:
                    decoded = struct.unpack('=BBBBII', response)
                    data = decoded[5]
                elif len(response) == 16:
                    decoded = struct.unpack('=BBBBIII', response)
                    data = decoded[5]
                else:
                    print("Read Ack of unexpected length: {}".format(len(response)))
                print("R 0x{0:08X} : 0x{1:08X} {2}".format(address, data, comment))
        except socket.error as e:
            print("Read Error: {1} Address: 0x{0:08X} ".format(address, e))
        time.sleep(2)
        return data

    def write(self, address, data, comment=''):
        if self.ack:
            print("W 0x{0:08X} : 0x{1:08X} {2}".format(address, data, comment))
        command = struct.pack('=BBBBII', 1, 0, 0, 0, address, data)
        # Send the single write command packet
        try:
            self.socket.sendto(command, (self.rdma_ip, self.rdma_port))
            if self.ack:
                print("Write is going for acknowledgement receiving data..")
                # Receive acknowledge packet
                response = self.socket.recv(self.UDPMaxRx)
                if len(response) == 12:
                    decoded = struct.unpack('=BBBBII', response)
                    print("Ack 0x{0:08X} : 0x{1:08X}".format(decoded[4], decoded[5]))
                elif len(response) == 16:
                    decoded = struct.unpack('=BBBBIII', response)
                    print("Ack 0x{0:08X} : 0x{1:08X}".format(decoded[4], decoded[5]))
                else:
                    print("Write Ack of unexpected length: {}".format(len(response)))
        except socket.error as e:
            print("Write Error: {2} Address: 0x{0:08X} Data: 0x{1:08X}".format(address, data, e))
        time.sleep(2)

    def close(self):
        self.socket.close()

    def setDebug(self, enabled=True):
        self.debug = enabled
