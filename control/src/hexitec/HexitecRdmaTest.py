"""
"""
import os.path
import random

try:
    from hexitec.rdma_control.RdmaUdp import *
    from hexitec.rdma_control.BoardCfgStatus import *
    from hexitec.rdma_control.VsrModule import *
    from hexitec.rdma_control.RDMA_REGISTERS import *
    from hexitec.rdma_control.rdma_register_helpers import *
except ModuleNotFoundError:
    print("Silent ModuleNotFoundError ************")
    from RdmaUdp import *
    from BoardCfgStatus import *
    from VsrModule import *
    from RDMA_REGISTERS import *
    from rdma_register_helpers import *


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



    board_cfg_status = BoardCfgStatus(Hex2x6CtrlRdma)
    print(f"{board_cfg_status.get_fpga_fw_version()}")
    print(f"{board_cfg_status.get_fpga_build_date()}")
    print(f"{board_cfg_status.get_fpga_build_time()}")
    print(f"{board_cfg_status.get_fpga_dna()}")
    print(f"{board_cfg_status.get_fpga_fw_git_hash()}")
    input()

    # scratch_1_comment = f"{BOARD_BUILD_INFO_SCRATCH_1['description']}"
    # Hex2x6CtrlRdma.udp_rdma_write(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
    #                               data=[0x11110000, 0x22220000, 0x33330000, 0x44440000], burst_len=4, cmd_no=0xAA,
    #                               comment=scratch_1_comment)

    vsr_addr_mapping = {1: 0x90, 2: None, 3: None, 4: None, 5: None, 6: None}
    """:obj:`dict` A dictionary mapping VSR slot to VSR addr. This is hardware build dependent and can be determined by :meth:`VsrModule.lookup`"""

    vsr_1 = VsrModule(Hex2x6CtrlRdma, slot=1, addr_mapping=vsr_addr_mapping)
    print(f"[INFO] Slot: {vsr_1.get_slot()} | VSR Address: {hex(vsr_1.get_addr())}")
    print(f"[INFO] Status: {vsr_1._get_status()} | H/V Status: {vsr_1.get_hv_status()}")
    vsr_1.enable_module()
    print(f"[INFO] Status: {vsr_1._get_status()} | H/V Status: {vsr_1.get_hv_status()}")

    for i in range(0, 100):
        print(f"[INFO]: VSR{vsr_1.slot} temperature: {vsr_1.get_temperature()}")
        time.sleep(0.5)

    i = 0
    min_burst = 1
    max_burst = 4
    for i in range(0, 2**24):
        burst_len = random.randint(min_burst, max_burst)
        i += 1
        expected_data = [ f"0x{hex(i + x)[2:].zfill(8).upper()}" for x in range(burst_len) ]
        scratch = Hex2x6CtrlRdma.udp_rdma_read(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
                                               burst_len=burst_len, cmd_no=0xBB,
                                               comment=scratch_1_comment)
        old_scratch = [ f"0x{hex(reg)[2:].zfill(8).upper()}" for reg in scratch ]
        Hex2x6CtrlRdma.udp_rdma_write(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
                                      data=[i + x for x in range(burst_len) ],
                                      burst_len=burst_len, cmd_no=0xCC,
                                      comment=scratch_1_comment)
        scratch = Hex2x6CtrlRdma.udp_rdma_read(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
                                               burst_len=burst_len, cmd_no=0xDD,
                                               comment=scratch_1_comment)
        new_scratch = [ f"0x{hex(reg)[2:].zfill(8).upper()}" for reg in scratch ]
        if expected_data == new_scratch:
            result = "<PASS>"
        else:
            result = "<FAIL>"

        print(f"{info_hdr}[{i}] R/W Test {result}: {old_scratch} --> {new_scratch}")
