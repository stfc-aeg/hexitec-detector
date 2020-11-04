#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created 25/04/2018

@author: aod, ckd
"""

from QemCam import *

qemcamera = QemCam()

print " Reading out DATA block of registers's settings.. (0x00000000 - 0x0000000F)"
print qemcamera.server_ctrl_ip_addr

qemcamera.connect()

data = qemcamera.x10g_rdma.read(0x00000000, 'FEM MAC [MSB]')
print "0x00000000 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x00000001, 'PC MAC [MSB], FEM MAC [LSB]')
print "0x00000001 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x00000002, 'PC MAC [LSB]')
print "0x00000002 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x00000003, 'N/A')
print "0x00000003 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x00000004, 'N/A')
print "0x00000004 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x00000005, 'N/A')
print "0x00000005 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x00000006, 'N/A')
print "0x00000006 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x00000007, 'PC IP')
print "0x00000007 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x00000008, 'TX Port, (half of) FEM IP ??')
print "0x00000008 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x00000009, 'RX Port')
print "0x00000009 = %.8x" % data

data = qemcamera.x10g_rdma.read(0x0000000A, 'N/A')
print "0x0000000A = %.8x" % data

data = qemcamera.x10g_rdma.read(0x0000000B, 'N/A')
print "0x0000000B = %.8x" % data

data = qemcamera.x10g_rdma.read(0x0000000C, 'N/A')
print "0x0000000C = %.8x" % data

data = qemcamera.x10g_rdma.read(0x0000000D, 'N/A')
print "0x0000000D = %.8x" % data

data = qemcamera.x10g_rdma.read(0x0000000E, 'N/A')
print "0x0000000E = %.8x" % data

data = qemcamera.x10g_rdma.read(0x0000000F, 'N/A')
print "0x0000000F = %.8x" % data

qemcamera.disconnect()
