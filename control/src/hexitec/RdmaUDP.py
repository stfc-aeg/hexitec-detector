"""
RdmaUDP Class.

Read/Write control access to FEM-II via UDP.

James Edwards 2019, Christian Angelsen, STFC Detector Systems Software Group, 2019.
"""

import socket
import struct
import logging


class RdmaUDP(object):
    """RdmaUDP Class, writing access to Firmware registers."""

    def __init__(self, MasterTxUDPIPAddress='192.168.0.1', MasterTxUDPIPPort=61650,
                 MasterRxUDPIPAddress='192.168.0.1', MasterRxUDPIPPort=61651,
                 TargetTxUDPIPAddress='192.168.0.2', TargetTxUDPIPPort=61650,
                 TargetRxUDPIPAddress='192.168.0.2', TargetRxUDPIPPort=61651,
                 RxUDPBuf=1024, UDPMTU=9000, UDPTimeout=10):
        """
        Initialize the RdmaUDP object.

        This constructor initializes the RdmaUDP object.

        :param MasterTxUDPIPAddress: PC network interface
        :param MasterTxUDPIPPort: Communications transmit port
        :param MasterRxUDPIPAddress: PC network interface
        :param MasterRxUDPIPPort: Communications receive port
        :param TargetTxUDPIPAddress: FEM network interface
        :param TargetTxUDPIPPort: Communications transmit port
        :param TargetRxUDPIPAddress: FEM network interface
        :param TargetRxUDPIPPort: Communications receiver port
        :param RxUDPBuf: UDP receive buffer
        :param UDPMTU: UDP Maximum Transmission Unit
        :param UDPTimeout: UDP connection timeout interval
        """
        self.txsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rxsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.rxsocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RxUDPBuf)
        # Set socket timeout
        timeval = struct.pack('ll', 5, 100)
        self.rxsocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)

        try:
            self.rxsocket.bind((MasterRxUDPIPAddress, MasterRxUDPIPPort))
        except socket.error as e:
            raise socket.error("Receive socket IP:Port %s:%s %s" %
                               (MasterRxUDPIPAddress, MasterRxUDPIPPort, e))
        try:
            self.txsocket.bind((MasterTxUDPIPAddress, MasterTxUDPIPPort))
        except socket.error as e:
            raise socket.error("Transmit socket IP:Port %s:%s %s" %
                               (MasterTxUDPIPAddress, MasterTxUDPIPPort, e))

        self.rxsocket.setblocking(1)

        self.TgtRxUDPIPAddr = TargetRxUDPIPAddress
        self.TgtRxUDPIPPrt = TargetRxUDPIPPort
        self.UDPMaxRx = UDPMTU
        self.debug = False
        self.ack = False

    def __del__(self):
        """Close network sockets."""
        self.txsocket.close()
        self.rxsocket.close()

    def read(self, address, comment=''):
        """
        Read 64 bits from the address.

        Sends a read command to the target rx UDP address/port and returns the result.
        :param address: the address to read from
        :param comment: comment to print out
        """
        command = struct.pack('=BBBBIQBBBBIQQQQQ', 1, 0, 0, 3, address,
                              0, 9, 0, 0, 255, 0, 0, 0, 0, 0, 0)
        self.txsocket.sendto(command, (self.TgtRxUDPIPAddr, self.TgtRxUDPIPPrt))
        if self.ack:
            response = self.rxsocket.recv(self.UDPMaxRx)
            data = 0x00000000
            if len(response) == 56:
                decoded = struct.unpack('=IIIIQQQQQ', response)
                data = decoded[3]
        if self.debug:
            logging.debug('R %08X : %08X %s' % (address, data, comment))

        return data

    def write(self, address, data, comment=''):
        """Write data to address."""
        if self.debug:
            logging.debug('W %08X : %08X %s' % (address, data, comment))

        # Create single write command + 5 data cycle nop command for padding
        command = struct.pack('=BBBBIQBBBBIQQQQQ', 1, 0, 0, 2, address, data,
                              9, 0, 0, 255, 0, 0, 0, 0, 0, 0)

        # Send the single write command packet
        self.txsocket.sendto(command, (self.TgtRxUDPIPAddr, self.TgtRxUDPIPPrt))

        if self.ack:
            _ = self.rxsocket.recv(self.UDPMaxRx)

    def close(self):
        """Close sockets."""
        self.txsocket.close()
        self.rxsocket.close()

    def setDebug(self, enabled=True):
        """Set debug messaging."""
        self.debug = enabled
