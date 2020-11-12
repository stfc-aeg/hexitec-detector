"""Show frame rate equivalent to the input clock settings.

Christian Angelsen, STFC Detector Systems Software Group. 22 October 2020.
"""

import sys
from QemCam import *
from socket import error as socket_error


def change_udp_register_value(register, value):
    """Set the register to value.

    Simple script used to update UDP register values, targeting
    0x00000000 - Data
    0x10000000 - Control
    """
    register = int(register, 16)
    value = int(value, 16)

    try:
        qemcamera = QemCam()
        qemcamera.connect()

        print(" Setting register ", hex(register), " to value: ", hex(value))

        qemcamera.x10g_rdma.write(register, value, 'N/A')

        qemcamera.disconnect()
        print("Register successfully updated.")
    except socket_error as e:
        print("ERROR: %s" % e)


if __name__ == '__main__':
    try:
        change_udp_register_value(sys.argv[1], sys.argv[2])
    except IndexError:
        print("Usage:")
        print("change_udp_register_value.py <register> <value>")
        print("such as:")
        print("change_udp_register_value.py 0x00000000 0x00000062")
