"""
HexitecRdmaStatuses.py: Start exercising new RDMA class.

Christian Angelsen, STFC Detector Systems Software Group, 2023.
"""

# import sys
# from RdmaUDP import RdmaUDP
# from ast import literal_eval
# import socket
# import struct
# import time  # DEBUGGING only

import os.path

try:
    from hexitec.rdma_control.RdmaUdp import RdmaUDP
    from hexitec.rdma_control.BoardCfgStatus import BoardCfgStatus, construct_fpga_dna, \
        decode_fw_version, decode_build_info
    from hexitec.rdma_control.VsrModule import *
    from hexitec.rdma_control.RDMA_REGISTERS import *
    from hexitec.rdma_control.rdma_register_helpers import *
except ModuleNotFoundError:
    print("Silent ModuleNotFoundError ************")
    # from RdmaUdp import *
    # from BoardCfgStatus import *
    # from VsrModule import *
    # from RDMA_REGISTERS import *
    # from rdma_register_helpers import *


if __name__ == '__main__':  # pragma: no cover

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

    fw_version = Hex2x6CtrlRdma.udp_rdma_read(address=BOARD_BUILD_INFO_SRC_VERSION['addr'],
                                              burst_len=1, cmd_no=0,
                                              comment=BOARD_BUILD_INFO_SRC_VERSION['description'])
    decoded_fw_version = decode_fw_version(fw_version, as_str=True)
    print(f"[INFO]: Firmware version: {decoded_fw_version}")
    build_info = Hex2x6CtrlRdma.udp_rdma_read(address=BOARD_BUILD_INFO_BUILD_DATE['addr'],
                                              burst_len=2, cmd_no=0,
                                              comment=BOARD_BUILD_INFO_BUILD_DATE['description'])

    decoded_fw_build_date, decoded_fw_build_time = decode_build_info(build_info, as_str=True)
    print(f"[INFO]: {decoded_fw_build_date} - {decoded_fw_build_time}")

    dna = Hex2x6CtrlRdma.udp_rdma_read(address=BOARD_BUILD_INFO_DNA_0['addr'],
                                       burst_len=3, cmd_no=0,
                                       comment=BOARD_BUILD_INFO_DNA_0['description'])
    dna = construct_fpga_dna(dna, full=False)
    info_hdr = f"[{dna}|{decoded_fw_version}|{decoded_fw_build_date}|{decoded_fw_build_time}]"
    print(f"{info_hdr}")

    # Write new values to all of the 4 scratch registers
    scratch_1_comment = f"{BOARD_BUILD_INFO_SCRATCH_1['description']}"
    Hex2x6CtrlRdma.udp_rdma_write(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
                                  data=[0x11110001, 0x22220002, 0x33330003, 0x44440004], burst_len=4, cmd_no=0xAA,
                                  comment=scratch_1_comment)

    # Read scratch registers values
    burst_len = 4
    scratch = Hex2x6CtrlRdma.udp_rdma_read(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
                                            burst_len=burst_len, cmd_no=0xBB,
                                            comment=scratch_1_comment)
    old_scratch = [f"0x{hex(reg)[2:].zfill(8).upper()}" for reg in scratch]
    print(f"Scratch register: {old_scratch}")

    vsr_addr_mapping = {1: 0x90, 2: None, 3: None, 4: None, 5: None, 6: None}
    """:obj:`dict` A dictionary mapping VSR slot to VSR addr. This is hardware build dependent and can be determined by :meth:`VsrModule.lookup`"""

    vsr_1 = VsrModule(Hex2x6CtrlRdma, slot=1, addr_mapping=vsr_addr_mapping)

    # # Turn VSR1 on
    # print(f"[INFO] Slot: {vsr_1.get_slot()} | VSR Address: {hex(vsr_1.get_addr())}")
    # print(f"[INFO] Status: {vsr_1._get_status()} | H/V Status: {vsr_1.get_hv_status()}")
    # vsr_1.enable_module()
    # print(f"[INFO] Status: {vsr_1._get_status()} | H/V Status: {vsr_1.get_hv_status()}")

    # Check statuses
    all_vsrs = True
    module_status = vsr_1.get_module_status(all_vsrs=all_vsrs)
    print(f"Module status: {module_status}")
    hv_status = vsr_1.get_hv_status(all_vsrs=all_vsrs)
    print(f"HV Status:     {hv_status}")

    success = vsr_1.hv_enable()
    if not success:
        print("Failed to enable VSR1's HV")

    scratch = Hex2x6CtrlRdma.udp_rdma_read(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
                                            burst_len=burst_len, cmd_no=0xBB,
                                            comment=scratch_1_comment)
    old_scratch = [f"0x{hex(reg)[2:].zfill(8).upper()}" for reg in scratch]

    print("Switching on all VSRs..")
    success = vsr_1._ctrl(all_vsrs=all_vsrs, op="enable")
    if not success:
        print("Failed to enable all VSRs")
    print("Enabling HV on all VSRs..")
    success = vsr_1._ctrl(all_vsrs=all_vsrs, op="hv_enable")
    if not success:
        print("Failed to enable HV on all VSRs")

    # reg_addr_h, reg_addr_l = 0x36, 0x31
    # print("Testing reading vsr register {0:X} {1:X}".format(reg_addr_h, reg_addr_l))
    # reply = vsr_1._read_vsr_register(reg_addr_h, reg_addr_l)
    # print(f"  {reply}")
    vsr_1.readout_vsr_register("Column Read  Enable ASIC1", 0x36, 0x31)
    vsr_1.readout_vsr_register("Column Read  Enable ASIC2", 0x43, 0x32)
    vsr_1.readout_vsr_register("Column Power Enable ASIC1", 0x34, 0x44)
    vsr_1.readout_vsr_register("Column Power Enable ASIC2", 0x41, 0x45)
    vsr_1.readout_vsr_register("Column Calib Enable ASIC1", 0x35, 0x37)
    vsr_1.readout_vsr_register("Column Calib Enable ASIC2", 0x42, 0x38)

    vsr_1.readout_vsr_register("Row    Read  Enable ASIC1", 0x34, 0x33)
    vsr_1.readout_vsr_register("Row    Read  Enable ASIC2", 0x41, 0x34)
    vsr_1.readout_vsr_register("Row    Power Enable ASIC1", 0x32, 0x46)
    vsr_1.readout_vsr_register("Row    Power Enable ASIC2", 0x39, 0x30)
    vsr_1.readout_vsr_register("Row    Calib Enable ASIC1", 0x33, 0x39)
    vsr_1.readout_vsr_register("Row    Calib Enable ASIC2", 0x39, 0x41)


    print("Switching OFF all VSRs..")
    success = vsr_1._ctrl(all_vsrs=all_vsrs, op="disable")
    if not success:
        print("Failed to disable all VSRs")


    # try:
    #     # VSR_ADDRESS = [0x90]
    #     # hxt.x10g_rdma.enable_vsr(1)  # Switches a single VSR on
    #     VSR_ADDRESS = range(0x90, 0x96, 1)
    #     # VSR_ADDRESS = [0x90, 0x92, 0x93, 0x94, 0x95]
    #     hxt.x10g_rdma.enable_all_vsrs()   # Switches on all VSR

    #     print(" Power status: {0:X}".format(hxt.x10g_rdma.power_status()))
    #     this_delay = 10
    #     print("VSR(s) enabled; Waiting {} seconds".format(this_delay))
    #     time.sleep(this_delay)

    #     print("Init modules (Send 0xE3..)")
    #     hxt.x10g_rdma.uart_tx([0xFF, 0xE3])
    #     print("Wait 5 sec")
    #     time.sleep(5)

    #     # print("uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done")
    #     # Execute equivalent of VSR1_Configure.txt:
    #     for vsr in VSR_ADDRESS:

    #         number_registers = 10
    #         hxt.readout_vsr_register(vsr, "Column Read  Enable ASIC1", 0x36, 0x31)
    #         hxt.readout_vsr_register(vsr, "Column Read  Enable ASIC2", 0x43, 0x32)
    #         hxt.readout_vsr_register(vsr, "Column Power Enable ASIC1", 0x34, 0x44)
    #         hxt.readout_vsr_register(vsr, "Column Power Enable ASIC2", 0x41, 0x45)
    #         hxt.readout_vsr_register(vsr, "Column Calib Enable ASIC1", 0x35, 0x37)
    #         hxt.readout_vsr_register(vsr, "Column Calib Enable ASIC2", 0x42, 0x38)

    #         hxt.readout_vsr_register(vsr, "Row    Read  Enable ASIC1", 0x34, 0x33)
    #         hxt.readout_vsr_register(vsr, "Row    Read  Enable ASIC2", 0x41, 0x34)
    #         hxt.readout_vsr_register(vsr, "Row    Power Enable ASIC1", 0x32, 0x46)
    #         hxt.readout_vsr_register(vsr, "Row    Power Enable ASIC2", 0x39, 0x30)
    #         hxt.readout_vsr_register(vsr, "Row    Calib Enable ASIC1", 0x33, 0x39)
    #         hxt.readout_vsr_register(vsr, "Row    Calib Enable ASIC2", 0x39, 0x41)
    #     ending = time.time()
    #     print("That took: {}".format(ending - beginning))
    #     reg07 = []
    #     reg89 = []
    #     for vsr in VSR_ADDRESS:
    #         r7_list, r7_value = hxt.read_register07(vsr)
    #         reg07.append(r7_value)
    #         r89_list, r89_value = hxt.read_register89(vsr)
    #         reg89.append(r89_value)
    #         s1_low_resp, s1_low_reply = hxt.read_and_response(vsr, 0x30, 0x32)
    #         s1_high_resp, s1_high_reply = hxt.read_and_response(vsr, 0x30, 0x33)
    #         sph_resp, sph_reply = hxt.read_and_response(vsr, 0x30, 0x34)
    #         s2_resp, s2_reply = hxt.read_and_response(vsr, 0x30, 0x35)
    #         print("VSR{} Row S1: 0x{}{}. S1Sph : 0x{}. SphS2 : 0x{}".format(vsr-143, s1_high_reply, s1_low_reply, sph_reply, s2_reply))

    #     print(" All vsrs, reg07: {}".format(reg07))
    #     print("           reg89: {}".format(reg89))

    # except (socket.error, struct.error) as e:
    #     print(" *** Caught Exception: {} ***".format(e))

    # hxt.disconnect()
