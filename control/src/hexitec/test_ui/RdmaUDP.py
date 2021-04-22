#

import socket
import struct


class RdmaUDP(object):

    def __init__(self, MasterTxUDPIPAddress='192.168.0.1', MasterTxUDPIPPort=65535,
                 MasterRxUDPIPAddress='192.168.0.1', MasterRxUDPIPPort=65536,
                 TargetRxUDPIPAddress='192.168.0.2', TargetRxUDPIPPort=65536,
                 RxUDPBuf=1024, UDPMTU=9000, UDPTimeout=10, debug=False):

        self.debug = debug
        if self.debug:
            print("RdmaUDP:")
            print("  RDMA IP addresses")
            print("	\trxsocket.bind({}, {})".format(MasterRxUDPIPAddress, MasterRxUDPIPPort))
            print("	\ttxsocket.bind({}, {})".format(MasterTxUDPIPAddress, MasterTxUDPIPPort))

            print("  Target, read & write target this through txsocket")
            print("	\tTargetRxUDPIPAddress	{}".format(TargetRxUDPIPAddress))
            print("	\tTargetRxUDPIPPort   	{}".format(TargetRxUDPIPPort))
            print("___________________________________________________________ ")

        self.txsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rxsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.rxsocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RxUDPBuf)
        timeval = struct.pack('ll', 5, 100)
        self.rxsocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
        self.error_OK = True

        try:
            self.rxsocket.bind((MasterRxUDPIPAddress, MasterRxUDPIPPort))
        except socket.error as e:
            error_string = "  Error: '{}' ".format(e)
            error_string += "on RX Socket: {}:{}".format(MasterRxUDPIPAddress, MasterRxUDPIPPort)
            print(error_string)
            self.error_OK = False

        try:
            self.txsocket.bind((MasterTxUDPIPAddress, MasterTxUDPIPPort))
        except socket.error as e:
            error_string = "  Error: '{}' ".format(e)
            error_string += "on TX Socket: {}:{}".format(MasterRxUDPIPAddress, MasterRxUDPIPPort)
            print(error_string)
            self.error_OK = False

        self.rxsocket.setblocking(1)

        self.TgtRxUDPIPAddr = TargetRxUDPIPAddress
        self.TgtRxUDPIPPrt = TargetRxUDPIPPort

        self.UDPMaxRx = UDPMTU

        self.ack = False

    def __del__(self):
        self.txsocket.close()
        self.rxsocket.close()

    def read(self, address, comment=''):
        command = struct.pack('=BBBBIQBBBBIQQQQQ', 1, 0, 0, 3, address, 0, 9, 0, 0,
                              255, 0, 0, 0, 0, 0, 0)
        self.txsocket.sendto(command, (self.TgtRxUDPIPAddr, self.TgtRxUDPIPPrt))

        if self.ack:
            response = self.rxsocket.recv(self.UDPMaxRx)
            data = 0x00000000
            if len(response) == 56:
                decoded = struct.unpack('=IIIIQQQQQ', response)
                data = decoded[3]

        if self.debug:
            print('R %08X : %08X %s' % (address, data, comment))

        return data

    def write(self, address, data, comment=''):
        if self.debug:
            print('W %08X : %08X %s' % (address, data, comment))

        # Create single write command + 5 data cycle nop command for padding
        command = struct.pack('=BBBBIQBBBBIQQQQQ', 1, 0, 0, 2, address,
                              data, 9, 0, 0, 255, 0, 0, 0, 0, 0, 0)

        # Send the single write command packet
        self.txsocket.sendto(command, (self.TgtRxUDPIPAddr, self.TgtRxUDPIPPrt))

        if self.ack:
            # Receive acknowledge packet
            response = self.rxsocket.recv(self.UDPMaxRx)
            if len(response) == 48:
                decoded = struct.unpack('=IIIIQQQQ', response)

    def block_read(self, address, length, comment=''):
        length = length // 4 - 1
        command = struct.pack('=BBBBI', length, 0, 0, 0, 1, address)

        self.txsocket.sendto(command, (self.TargetRxUDPIPAddr, self.TargetRxUDPIPPrt))

        if self.ack:
            response = self.rxsocket.recv(self.UDPMaxRx)

        return response

    def block_write(self, address, data, comment=''):

        if self.debug:
            print('W %08X : %08X %s' % (address, data, comment))

        # Create block write command
        length = len(data) // 4 - 1
        command = struct.pack('=BBBBI', length, 0, 0, 0, address)
        command = command + data
        print(len(command))

        # Send the single write command packet
        self.txsocket.sendto(command, (self.TgtRxUDPIPAddr, self.TgtRxUDPIPPrt))

        if self.ack:
            # Receive acknowledge packet
            response = self.rxsocket.recv(self.UDPMaxRx)
            print(len(response))

    def block_nop(self, comment=''):
        if self.debug:
            print('W %08X : %08X %s' % (comment))

        # Create block nop command
        command = struct.pack('=BBBBIQQQQQ', 255, 0, 0, 4, 0, 0, 0, 0, 0, 0)

        # Send the single write command packet
        self.txsocket.sendto(command, (self.TargetRxUDPIPAddr, self.TargetRxUDPIPPrt))

        if self.ack:
            # Receive acknowledge packet
            response = self.rxsocket.recv(self.UDPMaxRx)
            print(len(response))

    def close(self):
        self.txsocket.close()
        self.rxsocket.close()

    def setDebug(self, enabled=True):
        self.debug = enabled
