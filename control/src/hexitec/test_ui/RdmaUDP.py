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
            print("	Binding to:   ({}, {})".format(MasterTxUDPIPAddress, MasterTxUDPIPPort))
            print(" Transmitting: ({}, {})".format(TargetRxUDPIPAddress, TargetRxUDPIPPort))
            print("___________________________________________________________ ")

        self.txsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        timeval = struct.pack('ll', 5, 100)
        self.txsocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
        self.error_OK = True

        try:
            self.txsocket.bind((MasterTxUDPIPAddress, MasterTxUDPIPPort))
        except socket.error as e:
            error_string = "  Error: '{}' ".format(e)
            error_string += "on TX Socket: {}:{}".format(MasterRxUDPIPAddress, MasterRxUDPIPPort)
            print(error_string)
            self.error_OK = False

        self.TgtRxUDPIPAddr = TargetRxUDPIPAddress
        self.TgtRxUDPIPPrt = TargetRxUDPIPPort
        self.UDPMaxRx = UDPMTU
        self.ack = False

    def __del__(self):
        self.txsocket.close()

    def read(self, address, comment=''):
        command = struct.pack('=BBBBI', 2, 0, 0, 1, address)
        # print("Going to send the command: ({})".format(type(command)));print(command)#;return 0
        self.txsocket.sendto(command, (self.TgtRxUDPIPAddr, self.TgtRxUDPIPPrt))
        print("read, acknowledged: ", self.ack)
        if self.ack:
            response = self.txsocket.recv(self.UDPMaxRx)
            data = 0x00000000
            if len(response) == 16:
                decoded = struct.unpack('=BBBBIII', response)
                data = decoded[5]
            else:
                print(" Read ack Error! Response (length:{}) != 16".format(len(response)))

        if self.debug:
            print('R %08X : %08X %s' % (address, data, comment))

        return data

    def write(self, address, data, comment=''):
        if self.debug:
            print('W %08X : %08X %s' % (address, data, comment))

        command = struct.pack('=BBBBII', 1, 0, 0, 0, address, data)
        # print("Going to send the (Write) command: ({})".format(type(command)));print(command)#;return 0
        # Send the single write command packet
        self.txsocket.sendto(command, (self.TgtRxUDPIPAddr, self.TgtRxUDPIPPrt))
        print("writing, acknowledged: ", self.ack)
        if self.ack:
            # Receive acknowledge packet
            response = self.txsocket.recv(self.UDPMaxRx)
            # TODO: Remove as redundant?
            if len(response) == 16:
                decoded = struct.unpack('=BBBBIII', response)
                print("Ack: %08X : %08X " % (decoded[4], decoded[5]))
            else:
                print("Write ack Error! Response (length: {}) != 16".format(len(response)))

    def close(self):
        self.txsocket.close()

    def setDebug(self, enabled=True):
        self.debug = enabled
