"""
"""
import os.path
import time


from RdmaUdp import *
from udpcore.UdpCore import *


if __name__ == '__main__':
    # Example of usage.
    hostname = os.getenv('HOSTNAME').split('.')[0]
    print(f"Running on: {hostname}")
    if hostname.lower() == "te7hexidaq":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="10.0.3.1", local_port=61649,
                                 rdma_ip="10.0.3.2", rdma_port=61648, debug=False)
    elif hostname.lower() == "te7wendolene":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                                 rdma_ip="192.168.4.2", rdma_port=61648, debug=False)
    else:
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                                 rdma_ip="192.168.4.2", rdma_port=61648, debug=False)

    # UDP CONFIG #

    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="enp94s0f3", qsfp_idx=1, lane=1)
    time.sleep(2)
    data_lane1 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="enp94s0f1", qsfp_idx=1, lane=2)
    time.sleep(2)
    data_lane2 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="enp94s0f2", qsfp_idx=1, lane=3)
    time.sleep(2)

    data_lane2.set_lut_mode_ip(["10.0.1.1", "10.0.1.1", "10.0.1.1", "10.0.1.1", "10.0.1.1",
                                "10.0.1.1", "10.0.1.1", "10.0.1.1", "10.0.1.1", "10.0.1.1"])

    data_lane1.set_lut_mode_ip(["10.0.2.1", "10.0.2.1", "10.0.2.1", "10.0.2.1", "10.0.2.1",
                                "10.0.2.1", "10.0.2.1", "10.0.2.1", "10.0.2.1", "10.0.2.1"])

    data_lane2.set_lut_mode_mac(["9c:69:b4:60:b8:25", "9c:69:b4:60:b8:25", "9c:69:b4:60:b8:25",
                                 "9c:69:b4:60:b8:25", "9c:69:b4:60:b8:25", "9c:69:b4:60:b8:25",
                                 "9c:69:b4:60:b8:25", "9c:69:b4:60:b8:25"])

    data_lane1.set_lut_mode_mac(["9c:69:b4:60:b8:26", "9c:69:b4:60:b8:26", "9c:69:b4:60:b8:26",
                                 "9c:69:b4:60:b8:26", "9c:69:b4:60:b8:26", "9c:69:b4:60:b8:26",
                                 "9c:69:b4:60:b8:26", "9c:69:b4:60:b8:26"])

    data_lane2.set_lut_mode_port([61649, 61649, 61649, 61649, 61649, 61649, 61649, 61649])

    data_lane1.set_lut_mode_port([61649, 61649, 61649, 61649, 61649, 61649, 61649, 61649])

    data_lane1.set_lut_mode()  # enp94s0f1
    data_lane2.set_lut_mode()  # enp94s0f2
