#

import socket
import struct
import time

class RdmaUDP(object):

    def __init__(self, MasterTxUDPIPAddress='192.168.0.1', MasterTxUDPIPPort=65535, MasterRxUDPIPAddress='192.168.0.1', MasterRxUDPIPPort=65536,TargetTxUDPIPAddress='192.168.0.2', TargetTxUDPIPPort=65535, TargetRxUDPIPAddress='192.168.0.2', TargetRxUDPIPPort=65536, RxUDPBuf = 1024, UDPMTU=9000, UDPTimeout=10):

        self.txsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rxsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.rxsocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RxUDPBuf)

        self.rxsocket.bind((MasterRxUDPIPAddress, MasterRxUDPIPPort))
        self.txsocket.bind((MasterTxUDPIPAddress, MasterTxUDPIPPort))

        #self.rxsocket.settimeout(None)
        #self.txsocket.settimeout(None)

        self.rxsocket.setblocking(1)
        #self.txsocket.setblocking(1)

        self.TgtRxUDPIPAddr = TargetRxUDPIPAddress
        self.TgtRxUDPIPPrt  = TargetRxUDPIPPort

        self.UDPMaxRx = UDPMTU

        self.debug = False

        self.ack = False

    def __del__(self):
        self.txsocket.close()
        self.rxsocket.close()

    def read(self, address, comment=''):

        command = struct.pack('=BBBBIQBBBBIQQQQQ', 1,0,0,3, address, 0, 9,0,0,255, 0, 0,0,0,0,0)
        self.txsocket.sendto(command,(self.TgtRxUDPIPAddr,self.TgtRxUDPIPPrt))

        if self.ack:
            response = self.rxsocket.recv(self.UDPMaxRx)
            data = 0x00000000
            if len(response) == 56:
                decoded = struct.unpack('=IIIIQQQQQ', response)
                data = decoded[3]
                #print [hex(val) for val in decoded]

        if self.debug:
            print 'R %08X : %08X %s' % (address, data, comment)

        return data

    def write(self, address, data, comment=''):

        if self.debug:
            print 'W %08X : %08X %s' % (address, data, comment)

        #create single write command + 5 data cycle nop command for padding
        command = struct.pack('=BBBBIQBBBBIQQQQQ', 1,0,0,2, address, data, 9,0,0,255,0, 0,0,0,0,0)

        #Send the single write command packet
        self.txsocket.sendto(command,(self.TgtRxUDPIPAddr,self.TgtRxUDPIPPrt))

        if self.ack:
            #receive acknowledge packet
            response = self.rxsocket.recv(self.UDPMaxRx)
            #time.sleep(10)
            if len(response) == 48:
                decoded = struct.unpack('=IIIIQQQQ', response)
                #print decoded

        return

    def block_read(self, address, length, comment=''):
        length = length/4 - 1
        command = struct.pack('=BBBBI', length,0,0,0,1, address)

        self.txsocket.sendto(command,(self.TargetRxUDPIPAddr,self.TargetRxUDPIPPrt))

        if self.ack:
            response = self.rxsocket.recv(self.UDPMaxRx)
            #time.sleep(10)
            #decoded = struct.unpack('=I', response)
            #decoded = 0x00000000
            #print len(response)

        if self.debug:
            print 'R %08X : %08X %s' % (address, decoded, comment)

        return decoded

    def block_write(self, address, data, comment=''):

        if self.debug:
            print 'W %08X : %08X %s' % (address, data, comment)

        #create block write command
        length = len(data)/4-1
        command = struct.pack('=BBBBI', length,0,0,0, address)
        command= command+data
        print len(command)

        #Send the single write command packet
        self.txsocket.sendto(command,(self.TgtRxUDPIPAddr,self.TgtRxUDPIPPrt))

        if self.ack:
            #receive acknowledge packet
            response = self.rxsocket.recv(self.UDPMaxRx)
            #time.sleep(10)
            #decoded = struct.unpack('=II', response)
            print len(response)

        return

    def block_nop(self, comment=''):

        if self.debug:
            print 'W %08X : %08X %s' % (comment)

        #create block nop command
        command = struct.pack('=BBBBIQQQQQ',255,0,0,4, 0, 0,0,0,0,0)

        #Send the single write command packet
        self.txsocket.sendto(command,(self.TargetRxUDPIPAddr,self.TargetRxUDPIPPrt))

        if self.ack:
            #receive acknowledge packet
            response = self.rxsocket.recv(self.UDPMaxRx)
            #time.sleep(10)
            #decoded = struct.unpack('=I', response)
            print len(response)

        return

    def close(self):
        self.txsocket.close()
        self.rxsocket.close()

        return

    def setDebug(self, enabled=True):
        self.debug = enabled

        return

