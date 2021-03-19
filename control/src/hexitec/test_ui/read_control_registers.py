#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created 25/04/2018

@author: aod, ckd
"""

from QemCam import QemCam

qemcamera = QemCam()

print(" Reading out CONTROL block of registers' settings.. (0x10000000 - 0x1000000F)")
print(qemcamera.server_ctrl_ip_addr)

qemcamera.connect()

data = qemcamera.x10g_rdma.read(0x10000000, 'FEM MAC [MSB]')
print("0x10000000 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x10000001, 'PC MAC [MSB], FEM MAC [LSB]')
print("0x10000001 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x10000002, 'PC MAC [LSB]')
print("0x10000002 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x10000003, 'N/A')
print("0x10000003 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x10000004, 'N/A')
print("0x10000004 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x10000005, 'N/A')
print("0x10000005 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x10000006, 'N/A')
print("0x10000006 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x10000007, 'PC IP')
print("0x10000007 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x10000008, 'TX Port, (half of) FEM IP ??')
print("0x10000008 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x10000009, 'RX Port')
print("0x10000009 = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x1000000A, 'N/A')
print("0x1000000A = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x1000000B, 'N/A')
print("0x1000000B = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x1000000C, 'N/A')
print("0x1000000C = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x1000000D, 'N/A')
print("0x1000000D = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x1000000E, 'N/A')
print("0x1000000E = %.8x" % data)

data = qemcamera.x10g_rdma.read(0x1000000F, 'N/A')
print("0x1000000F = %.8x" % data)

qemcamera.disconnect()
