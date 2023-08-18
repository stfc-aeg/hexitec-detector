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
                                 rdma_ip="10.0.3.2", rdma_port=61648,
                                 multicast=True,
                                 debug=False)
    elif hostname.lower() == "te7wendolene":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                                 rdma_ip="192.168.4.2", rdma_port=61648,
                                 multicast=True,  # Multicast is TRUE
                                 debug=False)
    else:
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                                 rdma_ip="192.168.4.2", rdma_port=61648, debug=False)

    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="enp94s0f3", qsfp_idx=1, lane=1)
    time.sleep(2)

    ctrl_lane.set_dst_mac(mac="9c:69:b4:60:b8:27", response_check=False)
    ctrl_lane.set_dst_ip(ip="10.0.3.1", response_check=False)
    ctrl_lane.set_src_dst_port(port=0xF0D1F0D0, response_check=False)
    ctrl_lane.set_src_mac(mac="62:00:00:00:01:0A", response_check=False)
    ctrl_lane.set_src_ip(ip="10.0.3.2", response_check=False)

    Hex2x6CtrlRdma.__del__()
    Hex2x6CtrlRdma = RdmaUDP(local_ip="10.0.3.1", local_port=61649,
                             rdma_ip="10.0.3.2", rdma_port=61648,
                             multicast=False,  # Multicast is TRUE
                             debug=False)
    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="enp94s0f3", qsfp_idx=1, lane=1)
    time.sleep(2)
    ctrl_lane.set_filtering(enable=True, response_check=True)
    ctrl_lane.set_arp_timeout_length()

    data_lane1 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="enp94s0f1", qsfp_idx=1, lane=2)
    time.sleep(2)
    data_lane2 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="enp94s0f2", qsfp_idx=1, lane=3)
    time.sleep(2)

    # Source = Camera, Destination: PC
    data_lane1.set_dst_ip(ip="10.0.2.1")
    data_lane1.set_dst_mac(mac="9c:69:b4:60:b8:26")
    data_lane1.set_src_ip(ip="10.0.2.2")
    data_lane1.set_src_mac(mac="62:00:00:00:03:02")
    data_lane1.set_src_dst_port(port=0xF0D1F0D0)

    data_lane2.set_dst_ip(ip="10.0.1.1")
    data_lane2.set_dst_mac(mac="9c:69:b4:60:b8:25")
    data_lane2.set_src_ip(ip="10.0.1.2")
    data_lane2.set_src_mac(mac="62:00:00:00:02:02")
    data_lane2.set_src_dst_port(port=0xF0D1F0D0)
