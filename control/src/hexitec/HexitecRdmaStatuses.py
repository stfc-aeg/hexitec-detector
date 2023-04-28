"""
HexitecRdmaStatuses.py: Start exercising new RDMA class.

Christian Angelsen, STFC Detector Systems Software Group, 2023.
"""

import time
import os.path

try:
    from RdmaUdp import *
    from boardcfgstatus.BoardCfgStatus import *
    from hexitec_vsr.VsrModule import VsrModule
    import ALL_RDMA_REGISTERS as HEX_REGISTERS

except ModuleNotFoundError:
    print("Silent ModuleNotFoundError ************")
    from RdmaUdp import *
    print("no second exception")


if __name__ == '__main__':  # pragma: no cover

    hostname = os.getenv('HOSTNAME').split('.')[0]
    print(f"Running on: {hostname}")

    if hostname.lower() == "te7hexidaq":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="10.0.3.1", local_port=61649,
                                 rdma_ip="10.0.3.2", rdma_port=61648,
                                 debug=False, uart_offset=0xC)
    elif hostname.lower() == "te7wendolene":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                                 rdma_ip="192.168.4.2", rdma_port=61648,
                                 debug=False, uart_offset=0xC)
    else:
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                                 rdma_ip="192.168.4.2", rdma_port=61648,
                                 debug=False, uart_offset=0xC)

    board_cfg_status = BoardCfgStatus(
        Hex2x6CtrlRdma, rdma_offset=rdma.get_id_offset(
            HEX_REGISTERS.IC_OFFSETS, 'BOARD_BUILD_INFO_ID'))
    info_hdr = board_cfg_status.get_info_header()
    print(f"{info_hdr}")

    decoded_fw_version = board_cfg_status.get_fpga_fw_version()
    print(f"[INFO]: Firmware version: {decoded_fw_version}")

    decoded_fw_build_date = board_cfg_status.get_fpga_build_date()
    decoded_fw_build_time = board_cfg_status.get_fpga_build_time()
    print(f"[INFO]: {decoded_fw_build_date} - {decoded_fw_build_time}")

    dna = board_cfg_status.get_fpga_dna()
    info_hdr = f"[{dna}|{decoded_fw_version}|{decoded_fw_build_date}|{decoded_fw_build_time}]"
    print(f"{info_hdr}")

    # Write scratch registers
    scratch_regs = board_cfg_status.read_scratch_regs(size=4)
    print(f"0. scratch registers: {[hex(i) for i in scratch_regs]}")
    # Read scratch registers
    board_cfg_status.write_scratch_regs([0x11110000, 0x22220000, 0x33330000, 0x44440000])
    scratch_regs = board_cfg_status.read_scratch_regs(size=4)
    print(f"1. scratch registers: {[hex(i) for i in scratch_regs]}")

    vsr_addr_mapping = {1: 0x90, 2: 0x91, 3: 0x92, 4: 0x93, 5: 0x94, 6: 0x95}
    """:obj:`dict` A dictionary mapping VSR slot to VSR addr. This is hardware build dependent
        and can be determined by :meth:`VsrModule.lookup`"""

    vsr_1 = VsrModule(Hex2x6CtrlRdma, slot=1, addr_mapping=vsr_addr_mapping)
    print("Beforehand")
    print(f"[INFO] Status: {vsr_1.get_module_status()} | H/V Status: {vsr_1.get_hv_status()}")

    # TODO Status of all VSRs
    # vsr_status = vsr_1._get_status(hv=False, all_vsrs=True)
    # hv_status = vsr_1._get_status(hv=True, all_vsrs=True)
    # print("Beforehand")
    # print(f"[INFO] Status:     {vsr_status}")
    # print(f"[INFO] H/V Status: {hv_status}")

    # # Switches VSR 1 on, enables HV - TODO Reverify
    # # Turn VSR1 on
    # print(f"[INFO] Slot: {vsr_1.get_slot()} | VSR Address: {hex(vsr_1.get_addr())}")
    # print(f"[INFO] Status: {vsr_1.get_module_status()} | H/V Status: {vsr_1.get_hv_status()}")
    # print("Enabling module(s)..")
    # vsr_1.enable_module()
    # print("Turning HV on..")
    # vsr_1.hv_enable()
    # print(f"[INFO] Status: {vsr_1._get_status()} | H/V Status: {vsr_1.get_hv_status()}")

    # # Check statuses
    # print(f"[INFO] Status: {vsr_1.get_module_status()} | H/V Status: {vsr_1.get_hv_status()}")

    # TODO: Controlling all VSRs - Verified
    VSRs = VsrModule(Hex2x6CtrlRdma, slot=0, addr_mapping=vsr_addr_mapping)
    print("Switching all VSRs on..")
    success = VSRs.enable_module()
    if not success:
        print("Failed to switch VSRs on!")
    print("Switching all HVs on..")
    success = VSRs.hv_enable()
    if not success:
        print("Failed to enable VSRs HV!")

    vsr_list = []
    # vsr_1 = VsrModule(Hex2x6CtrlRdma, slot=1, addr_mapping=vsr_addr_mapping)
    vsr_list.append(vsr_1)
    vsr_2 = VsrModule(Hex2x6CtrlRdma, slot=2, addr_mapping=vsr_addr_mapping)
    vsr_list.append(vsr_2)
    vsr_3 = VsrModule(Hex2x6CtrlRdma, slot=3, addr_mapping=vsr_addr_mapping)
    vsr_list.append(vsr_3)
    vsr_4 = VsrModule(Hex2x6CtrlRdma, slot=4, addr_mapping=vsr_addr_mapping)
    vsr_list.append(vsr_4)
    vsr_5 = VsrModule(Hex2x6CtrlRdma, slot=5, addr_mapping=vsr_addr_mapping)
    vsr_list.append(vsr_5)
    vsr_6 = VsrModule(Hex2x6CtrlRdma, slot=6, addr_mapping=vsr_addr_mapping)
    vsr_list.append(vsr_6)

    for vsr in vsr_list:
        print(f"[INFO]: VSR{vsr.slot} temperature: {vsr.get_temperature()}")

    # Initialise VSR, train Kintex VLDS, Check VSR locked

    for vsr in vsr_list:
        vsr.initialise()

    print("Did PLL(s) lock?")
    bPolling = True
    while bPolling:
        pll_status = vsr_1.read_pll_status()
        if pll_status & 1:
            bPolling = False
        else:
            time.sleep(0.2)

    # Training Kintex

    VSR_DATA_CTRL = HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL
    Hex2x6CtrlRdma.udp_rdma_write(address=VSR_DATA_CTRL['addr'],
                                  data=0x10, burst_len=1,
                                  comment=VSR_DATA_CTRL['description'])
    time.sleep(0.2)
    Hex2x6CtrlRdma.udp_rdma_write(address=VSR_DATA_CTRL['addr'],
                                  data=0x0, burst_len=1,
                                  comment=VSR_DATA_CTRL['description'])

    # Check VSRs Locked
    vsr_status_addr = HEX_REGISTERS.HEXITEC_2X6_VSR0_STATUS['addr']
    for vsr in vsr_list:
        index = vsr.addr - 144
        locked = Hex2x6CtrlRdma.udp_rdma_read(vsr_status_addr, burst_len=1,
                                              comment=f"VSR {index} status register")[0]
        if (locked == 0xFF):
            print("VSR{0} Locked (0x{1:X})".format(vsr.addr-143, locked))
        else:
            print("VSR{0} incomplete lock! (0x{1:X}) ****".format(vsr.addr-143, locked))
        vsr_status_addr += 4

    print("-=-=-=-=- Dark Images -=-=-=-=-")
    for vsr in vsr_list:
        vsr.collect_offsets()
    print("-=-=-=-=-     Done    -=-=-=-=-")

    print("Controlling the HV - on")
    vsr_1.hv_on()
    time.sleep(1)
    print(" Turning it off now..")
    vsr_1.hv_off()
    print(" All Done")

    print(" Readout HV Power")
    for vsr in vsr_list:
        print(f"VSR{vsr.slot} HV: {round(vsr_1.get_power_sensors(), 2)}")
