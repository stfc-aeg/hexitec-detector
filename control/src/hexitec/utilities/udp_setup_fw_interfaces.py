"""
"""
import os.path
import time

from RdmaUdp import *
from udpcore.UdpCore import *


def configure_te7hexidaq(Hex2x6CtrlRdma):
    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="enp94s0f3", qsfp_idx=1, lane=1)
    time.sleep(2)

    ctrl_lane.set_dst_mac(mac="9c:69:b4:60:b8:27", response_check=False)
    ctrl_lane.set_dst_ip(ip="10.0.3.1", response_check=False)
    ctrl_lane.set_src_dst_port(port=0xF0D1F0D0, response_check=False)
    ctrl_lane.set_src_mac(mac="62:00:00:00:01:0A", response_check=False)
    ctrl_lane.set_src_ip(ip="10.0.3.2", response_check=False)

    # Re-establish connection without multicast
    Hex2x6CtrlRdma.__del__()
    Hex2x6CtrlRdma = RdmaUDP(local_ip="10.0.3.1", local_port=61649,
                             rdma_ip="10.0.3.2", rdma_port=61648,
                             multicast=False,
                             debug=False)
    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="enp94s0f3", qsfp_idx=1, lane=1)
    time.sleep(2)
    ctrl_lane.set_filtering(enable=True, response_check=True)
    ctrl_lane.set_arp_timeout_length()

    data_lane1 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="enp94s0f1", qsfp_idx=1, lane=2)
    time.sleep(2)
    data_lane2 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="enp94s0f2", qsfp_idx=1, lane=3)
    time.sleep(2)

    # Source = Camera
    data_lane2.set_src_ip(ip="10.0.1.2")
    data_lane2.set_src_mac(mac="62:00:00:00:02:02")
    data_lane2.set_src_dst_port(port=0xF0D1F0D0)

    data_lane1.set_src_ip(ip="10.0.2.2")
    data_lane1.set_src_mac(mac="62:00:00:00:03:02")
    data_lane1.set_src_dst_port(port=0xF0D1F0D0)

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


def configure_te7wendolene(Hex2x6CtrlRdma):
    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="enp2s0f3", qsfp_idx=1, lane=1)
    time.sleep(2)

    ctrl_lane.set_dst_mac(mac="68:05:CA:2D:3A:5B",response_check=False)
    ctrl_lane.set_dst_ip(ip="192.168.4.1", response_check=False)
    ctrl_lane.set_src_dst_port(port=0xF0D1F0D0, response_check=False)
    ctrl_lane.set_src_mac(mac="62:00:00:00:04:02", response_check=False)
    ctrl_lane.set_src_ip(ip="192.168.4.2", response_check=False)

    # Re-establish connection without multicast
    Hex2x6CtrlRdma.__del__()
    Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                             rdma_ip="192.168.4.2", rdma_port=61648,
                             multicast=False, #multcast is FALSE
                             debug=False)
    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="enp2s0f3", qsfp_idx=1, lane=1)
    time.sleep(2)
    ctrl_lane.set_filtering(enable=True, response_check=True)
    ctrl_lane.set_arp_timeout_length()

    data_lane1 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="enp2s0f1", qsfp_idx=1, lane=2)
    time.sleep(2)
    data_lane2 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="enp2s0f2", qsfp_idx=1, lane=3)
    time.sleep(2)

    data_lane2.set_src_ip(ip="192.168.2.2")
    data_lane2.set_src_mac(mac="62:00:00:00:02:02")
    data_lane2.set_src_dst_port(port=0xF0D0F0D1)

    data_lane1.set_src_ip(ip="192.168.3.2")
    data_lane1.set_src_mac(mac="62:00:00:00:03:02")
    data_lane1.set_src_dst_port(port=0xF0D0F0D1)

    data_lane2.set_lut_mode_ip(["192.168.2.1", "192.168.2.3", "192.168.2.4", "192.168.2.5",
                                "192.168.2.6", "192.168.2.7", "192.168.2.8", "192.168.2.9"])

    data_lane1.set_lut_mode_ip(["192.168.3.1", "192.168.3.3", "192.168.3.4", "192.168.3.5",
                                "192.168.3.6", "192.168.3.7", "192.168.3.8", "192.168.3.9"])

    data_lane2.set_lut_mode_mac(["68:05:CA:2D:3A:59", "68:05:CA:2D:3A:53", "68:05:CA:2D:3A:54",
                                 "68:05:CA:2D:3A:55", "68:05:CA:2D:3A:56", "68:05:CA:2D:3A:57",
                                 "68:05:CA:2D:3A:58", "68:05:CA:2D:3A:52"])

    data_lane1.set_lut_mode_mac(["68:05:CA:2D:3A:5A", "68:05:CA:2D:3A:63", "68:05:CA:2D:3A:64",
                                 "68:05:CA:2D:3A:65", "68:05:CA:2D:3A:66", "68:05:CA:2D:3A:67",
                                 "68:05:CA:2D:3A:68", "68:05:CA:2D:3A:62"])

    data_lane2.set_lut_mode_port([61649, 61000, 61001, 61002, 61003, 61004, 61005, 61006])

    data_lane1.set_lut_mode_port([61649, 61000, 61001, 61002, 61003, 61004, 61005, 61006])

    data_lane1.set_lut_mode()  # enp2s0f1
    data_lane2.set_lut_mode()  # enp2s0f2


def configure_hxtdaq1(Hex2x6CtrlRdma):
    """
eno8303: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether b4:45:06:e5:3c:a6 brd ff:ff:ff:ff:ff:ff
    inet 192.168.0.51
    """
    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="eno8303", qsfp_idx=1, lane=1)
    time.sleep(2)

    ctrl_lane.set_dst_mac(mac="b4:45:06:e5:3c:a6", response_check=False)
    ctrl_lane.set_dst_ip(ip="192.168.0.51", response_check=False)
    ctrl_lane.set_src_dst_port(port=0xF0D1F0D0, response_check=False)
    ctrl_lane.set_src_mac(mac="62:00:00:00:01:0A", response_check=False)
    ctrl_lane.set_src_ip(ip="192.168.0.122", response_check=False)

    # Re-establish connection without multicast
    Hex2x6CtrlRdma.__del__()
    Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.0.51", local_port=61649,
                             rdma_ip="192.168.0.122", rdma_port=61648,
                             multicast=False,
                             debug=False)
    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="eno8303", qsfp_idx=1, lane=1)
    time.sleep(2)
    ctrl_lane.set_filtering(enable=True, response_check=True)
    ctrl_lane.set_arp_timeout_length()

    data_lane1 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="ens2f0np0", qsfp_idx=1, lane=2)
    time.sleep(2)
    data_lane2 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="ens2f0np0", qsfp_idx=1, lane=3)
    time.sleep(2)

    # Source = Camera, Destination: PC
    data_lane2.set_src_ip(ip="10.0.1.20")
    data_lane2.set_src_mac(mac="62:00:00:00:02:02")
    data_lane2.set_src_dst_port(port=0xF0D1F0D0)

    data_lane1.set_src_ip(ip="10.0.1.10")
    data_lane1.set_src_mac(mac="62:00:00:00:03:02")
    data_lane1.set_src_dst_port(port=0xF0D1F0D0)

    data_lane2.set_lut_mode_ip(["10.0.1.1", "10.0.1.3", "10.0.1.1", "10.0.1.3", "10.0.1.1",
                                "10.0.1.3", "10.0.1.1", "10.0.1.3", "10.0.1.1", "10.0.1.3"])

    data_lane1.set_lut_mode_ip(["10.0.1.2", "10.0.1.4", "10.0.1.2", "10.0.1.4", "10.0.1.2",
                                "10.0.1.4", "10.0.1.2", "10.0.1.4", "10.0.1.2", "10.0.1.4"])

    data_lane2.set_lut_mode_mac(["5c:6f:69:f8:6b:a0", "5c:6f:69:f8:a3:e0", "5c:6f:69:f8:6b:a0",
                                 "5c:6f:69:f8:a3:e0", "5c:6f:69:f8:6b:a0", "5c:6f:69:f8:a3:e0",
                                 "5c:6f:69:f8:6b:a0", "5c:6f:69:f8:a3:e0"])

    data_lane1.set_lut_mode_mac(["5c:6f:69:f8:57:d0", "5c:6f:69:f8:7a:10", "5c:6f:69:f8:57:d0",
                                 "5c:6f:69:f8:7a:10", "5c:6f:69:f8:57:d0", "5c:6f:69:f8:7a:10",
                                 "5c:6f:69:f8:57:d0", "5c:6f:69:f8:7a:10"])

    data_lane2.set_lut_mode_port([61649, 61649, 61649, 61649, 61649, 61649, 61649, 61649])

    data_lane1.set_lut_mode_port([61649, 61649, 61649, 61649, 61649, 61649, 61649, 61649])

    data_lane1.set_lut_mode()
    data_lane2.set_lut_mode()
    """
# PC 1:
2: ens2f0np0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9216 qdisc mq state UP group default qlen 1000
    link/ether 5c:6f:69:f8:6b:a0 brd ff:ff:ff:ff:ff:ff
    inet 10.0.1.1/24
# PC 2:
ens2f0np0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9216 qdisc mq state UP group default qlen 1000
    link/ether 5c:6f:69:f8:57:d0 brd ff:ff:ff:ff:ff:ff
    inet 10.0.1.2
# PC 3:
ens2f0np0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9216 qdisc mq state UP group default qlen 1000
    link/ether 5c:6f:69:f8:a3:e0 brd ff:ff:ff:ff:ff:ff
    inet 10.0.1.3/
#PC 4:
ens2f0np0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9216 qdisc mq state UP group default qlen 1000
    link/ether 5c:6f:69:f8:7a:10 brd ff:ff:ff:ff:ff:ff
    inet 10.0.1.4/
    """


if __name__ == '__main__':
    # Example of usage.
    hostname = os.getenv('HOSTNAME').split('.')[0]
    print(f"Running on: {hostname}")
    if hostname.lower() == "te7hexidaq":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="10.0.3.1", local_port=61649,
                                 rdma_ip="10.0.3.2", rdma_port=61648,
                                 multicast=True, debug=False)
        configure_te7hexidaq(Hex2x6CtrlRdma)
    elif hostname.lower() == "te7wendolene":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                                 rdma_ip="192.168.4.2", rdma_port=61648,
                                 multicast=True, debug=False)
        configure_te7wendolene(Hex2x6CtrlRdma)
    elif hostname.lower() == "hxtdaq1":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.0.51", local_port=61649,
                                 rdma_ip="192.168.0.122", rdma_port=61648,
                                 multicast=True, debug=False)
        """
eno8303: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether b4:45:06:e5:3c:a6 brd ff:ff:ff:ff:ff:ff
    inet 192.168.0.51
        """
        configure_hxtdaq1(Hex2x6CtrlRdma)
    else:
        print("Unknown host, exiting..")
