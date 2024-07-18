"""
"""
import os.path
import random

from . import HEX_RDMA_REGISTERS as RDMA_REGS
import RdmaUdp
import BoardCfgStatus


try:
    from rdma_control.RdmaUdp import *
    from rdma_control.BoardCfgStatus import *
    from rdma_control.VsrModule import *
except ModuleNotFoundError:
    from RdmaUdp import *
    from BoardCfgStatus import *
    from VsrModule import *

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

    board_cfg_status = BoardCfgStatus(Hex2x6CtrlRdma, rdma_offset=rdma.get_id_offset(RDMA_REGS.BOARD_BUILD_INFO_ID))
    print(f"{board_cfg_status.get_fpga_fw_version()}")
    print(f"{board_cfg_status.get_fpga_build_date()}")
    print(f"{board_cfg_status.get_fpga_build_time()}")
    print(f"{board_cfg_status.get_fpga_dna()}")
    print(f"{board_cfg_status.get_fpga_fw_git_hash()}")
    info_hdr = board_cfg_status.get_info_header()
    print(f"{info_hdr}")

    vsr_addr_mapping = {1: 0x91, 2: None, 3: None, 4: None, 5: None, 6: None}
    """:obj:`dict` A dictionary mapping VSR slot to VSR addr. This is hardware build dependent and can be determined by :meth:`VsrModule.lookup`"""

    vsr_1 = VsrModule(Hex2x6CtrlRdma, slot=1, init_time=15, addr_mapping=vsr_addr_mapping)
    vsr_1.set_row_column()
    input()
    # vsr_1 = VsrModule(Hex2x6CtrlRdma, slot=1, addr_mapping=None)
    print(f"[INFO] Slot: {vsr_1.get_slot()} | VSR Address: {hex(vsr_1.get_addr())}")
    print(f"[INFO] Status: {vsr_1.get_module_status()} | H/V Status: {vsr_1.get_hv_status()}")
    vsr_1.enable_module()
    print(f"[INFO] Status: {vsr_1.get_module_status()} | H/V Status: {vsr_1.get_hv_status()}")

    for i in range(0, 5):
        print(f"[INFO]: VSR{vsr_1.slot} temperature: {vsr_1.get_temperature()}")
        time.sleep(1)

    print(f"[INFO] VSR{vsr_1.slot} FPGA Firmware Version: {vsr_1.get_firmware_version()}")
    print(f"[INFO] VSR{vsr_1.slot} FPGA Customer ID: {vsr_1.get_customer_id()}")
    print(f"[INFO] VSR{vsr_1.slot} FPGA Project ID: {vsr_1.get_project_id()}")

    vsr_1.initialise()

    if False:
        scratch_regs = board_cfg_status.read_scratch_regs(size=4)
        print(f"scratch registers: {[hex(i) for i in scratch_regs]}")
        board_cfg_status.write_scratch_regs([0x11110000, 0x22220000, 0x33330000, 0x44440000])
        scratch_regs = board_cfg_status.read_scratch_regs(size=4)
        print(f"scratch registers: {[hex(i) for i in scratch_regs]}")
        i = 0
        min_burst = 1
        max_burst = 4
        for i in range(0, 2**24):
            burst_len = random.randint(min_burst, max_burst)
            i += 1
            expected_data = [ f"0x{hex(i + x)[2:].zfill(8).upper()}" for x in range(burst_len) ]
            scratch = board_cfg_status.read_scratch_regs(size=burst_len)
            old_scratch = [ f"0x{hex(reg)[2:].zfill(8).upper()}" for reg in scratch ]
            board_cfg_status.write_scratch_regs([i + x for x in range(burst_len)])
            scratch = board_cfg_status.read_scratch_regs(size=burst_len)
            new_scratch = [ f"0x{hex(reg)[2:].zfill(8).upper()}" for reg in scratch ]
            if expected_data == new_scratch:
                result = "<PASS>"
            else:
                result = "<FAIL>"
            print(f"{info_hdr}[{i}] R/W Test {result}: {old_scratch} --> {new_scratch}")
