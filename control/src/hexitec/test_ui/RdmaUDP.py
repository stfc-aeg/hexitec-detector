"""
Rdma - UDP 10 G access.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

import socket
import struct
import time

# TODO: This global variable to be removed post debugging
SLEEP_DELAY = 0.000   # 2

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

    def read(self, address, burst_len=1, comment=''):
        burst_len = burst_len
        cmd_no = 0
        op_code = 1
        # H = burst len, B = cmd no, B = Op code, I = start addr
        # H = unsigned short (2), B = unsigned char (1), I = signed int (4 Bytes)
        command = struct.pack('=HBBI', burst_len, cmd_no, op_code, address)
        data = 0
        try:
            self.socket.sendto(command, (self.rdma_ip, self.rdma_port))
            # Receive acknowledge packet
            response = self.socket.recv(self.UDPMaxRx)
            data = 0x00000000
            header_str = "HBBI"   # Equivalent length: 8
            payload_length = len(response) - 8  # 8 = header length
            payload_length = payload_length // 4    # 32 bit word, therefore 4 bytes per word
            packet_str = header_str + "I" * payload_length
            padding = (burst_len % 2)
            if payload_length != (burst_len + padding):
                raise Exception("read expected {}, received {}, words!".format(burst_len, payload_length))
            decoded = struct.unpack(packet_str, response)
            if self.debug:
                print('R decoded: {}'.format(', '.join("0x{0:X}".format(x) for x in decoded)))
            if padding:
                data = decoded[4:-padding]  # Omit burst_len, cmd_no, op_code, address and padding present at the end
            else:
                data = decoded[4:]  # Omit burst_len, cmd_no, op_code, address
            if self.ack:
                print("R 0x{0:08X} : 0x{1} \"{2}\"".format(address, ''.join("{0:X}".format(x) for x in data), comment))
        except socket.error as e:
            print(" *** Read Error: {1} Address: 0x{0:08X} ***".format(address, e))
        except struct.error as e:
            print(" *** Read Error: {} ***".format(e))
        time.sleep(SLEEP_DELAY)
        return data

    def write(self, address, data, comment=''):
        if self.ack:
            print("W 0x{0:08X} : 0x{1:08X} {2}".format(address, data, comment))
        command = struct.pack('=BBBBII', 1, 0, 0, 0, address, data)
        # print(" rdma.write(address={0:08X}, data={1:08X}), command: {2}, or: ".format(
        #         address, data, struct.unpack('=BBBBII', command)), command)#;return 0
        # Send the single write command packet
        try:
            self.socket.sendto(command, (self.rdma_ip, self.rdma_port))
            # Receive acknowledgement
            response = self.socket.recv(self.UDPMaxRx)
            if self.ack:
                if len(response) == 12:
                    decoded = struct.unpack('=BBBBII', response)
                    print("Ack 0x{0:08X} : 0x{1:08X}".format(decoded[4], decoded[5]))
                elif len(response) == 16:
                    decoded = struct.unpack('=BBBBIII', response)
                    print("Ack 0x{0:08X} : 0x{1:08X}".format(decoded[4], decoded[5]))
                else:
                    print("Write Ack of unexpected length: {}".format(len(response)))
        except socket.error as e:
            print(" *** Write Error: {2} Address: 0x{0:08X} Data: 0x{1:08X} ***".format(address, data, e))
        time.sleep(SLEEP_DELAY)

    def close(self):
        self.socket.close()

    def setDebug(self, enabled=True):
        self.debug = enabled
