"""
Configures 2x6 Control, Data interfaces through multicast
"""
import time

from RdmaUdp import *
from udpcore.UdpCore import *
import ALL_RDMA_REGISTERS as HEX_REGISTERS


# def set_nof_lut_entries(value=4):
#     Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_NOF_LUT_MODE_ENTRIES['addr'],
#                                   data=value, burst_len=1)

if __name__ == '__main__':
    Hex2x6CtrlRdma = RdmaUDP(local_ip="10.0.1.1", local_port=61649,
                             rdma_ip="10.0.1.100", rdma_port=61648,
                             multicast=True, debug=False)

    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="ens2f0np0", qsfp_idx=1, lane=1)
    time.sleep(2)

    ctrl_lane.set_dst_mac(mac="5c:6f:69:f8:6b:a0", response_check=False)
    ctrl_lane.set_dst_ip(ip="10.0.1.1", response_check=False)
    ctrl_lane.set_src_dst_port(port=0xF0D1F0D0, response_check=False)
    ctrl_lane.set_src_mac(mac="62:00:00:00:01:0A", response_check=False)
    ctrl_lane.set_src_ip(ip="10.0.1.100", response_check=False)

    Hex2x6CtrlRdma.__del__()
    Hex2x6CtrlRdma = RdmaUDP(local_ip="10.0.1.1", local_port=61649,
                             rdma_ip="10.0.1.100", rdma_port=61648,
                             multicast=False, debug=False)
    ctrl_lane = UdpCore(Hex2x6CtrlRdma, ctrl_flag=True, iface_name="ens2f0np0", qsfp_idx=1, lane=1)
    time.sleep(2)
    ctrl_lane.set_filtering(enable=True, response_check=True)
    ctrl_lane.set_arp_timeout_length()

    data_lane1 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="ens2f0np0", qsfp_idx=1, lane=2)
    time.sleep(2)
    data_lane2 = UdpCore(Hex2x6CtrlRdma, ctrl_flag=False, iface_name="ens2f0np0", qsfp_idx=1, lane=3)
    time.sleep(2)

    # Source = Camera, Destination: PC
    data_lane1.set_dst_ip(ip="10.0.1.2")
    data_lane1.set_dst_mac(mac="5c:6f:69:f8:57:d0")
    data_lane1.set_src_ip(ip="10.0.1.101")
    data_lane1.set_src_mac(mac="62:00:00:00:01:0B")
    data_lane1.set_src_dst_port(port=0xF0D1F0D0)

    data_lane2.set_dst_ip(ip="10.0.1.3")
    data_lane2.set_dst_mac(mac="5c:6f:69:f8:a3:e0")
    data_lane2.set_src_ip(ip="10.0.1.102")
    data_lane2.set_src_mac(mac="62:00:00:00:01:0C")
    data_lane2.set_src_dst_port(port=0xF0D1F0D0)

    print("adding farm mode, 4 targets")

    data_lane2.set_lut_mode_ip(["10.0.1.3", "10.0.1.1", "10.0.1.3", "10.0.1.1", "10.0.1.3",
                                "10.0.1.1", "10.0.1.3", "10.0.1.1"])

    data_lane1.set_lut_mode_ip(["10.0.1.2", "10.0.1.4", "10.0.1.2", "10.0.1.4", "10.0.1.2",
                                "10.0.1.4", "10.0.1.2", "10.0.1.4"])

    data_lane2.set_lut_mode_mac(["5c:6f:69:f8:a3:e0", "5c:6f:69:f8:6b:a0", "5c:6f:69:f8:a3:e0",
                                 "5c:6f:69:f8:6b:a0", "5c:6f:69:f8:a3:e0", "5c:6f:69:f8:6b:a0",
                                 "5c:6f:69:f8:a3:e0", "5c:6f:69:f8:6b:a0"])

    data_lane1.set_lut_mode_mac(["5c:6f:69:f8:57:d0", "5c:6f:69:f8:7a:10", "5c:6f:69:f8:57:d0",
                                 "5c:6f:69:f8:7a:10", "5c:6f:69:f8:57:d0", "5c:6f:69:f8:7a:10",
                                 "5c:6f:69:f8:57:d0", "5c:6f:69:f8:7a:10"])

    data_lane2.set_lut_mode_port([61649, 61659, 61649, 61659, 61649, 61659, 61649, 61659])

    data_lane1.set_lut_mode_port([61649, 61649, 61649, 61649, 61649, 61649, 61649, 61649])

    # Determine how many LUT entries to use
    number_nodes = 1
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_NOF_LUT_MODE_ENTRIES['addr'],
                                  data=number_nodes, burst_len=1)
    print(f"Configuring for {number_nodes} lut entries")
    
    data_lane1.set_lut_mode()  # enp2s0f1
    data_lane2.set_lut_mode()  # enp2s0f2
