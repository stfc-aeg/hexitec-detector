import os.path
import time
from RdmaUdp import *
from boardcfgstatus.BoardCfgStatus import *
from hexitec_vsr.VsrModule import *
from udpcore.UdpCore import *
import ALL_RDMA_REGISTERS as HEX_REGISTERS
# import pandas as pd
# import time
# import matplotlib.pyplot as plt


def get_env_values(vsrs):

    for vsr in vsrs:
        print(f"[INFO] Slot: {vsr.get_slot()} | VSR Address: {hex(vsr.get_addr())}")
        print(f"[INFO] Status: {vsr.get_module_status()} | H/V Status: {vsr.get_hv_status()}")
        #15 seconds later, the fpga on the vsr should be powered and initialised
        print(f"[INFO] Status: {vsr.get_module_status()} | H/V Status: {vsr.get_hv_status()}")

        print(f"[INFO]: VSR{vsr.slot} temperature: {vsr.get_temperature()}")

        print(f"[INFO]: VSR{vsr.slot} humidity: {vsr.get_humidity()}")

        for asic in [1,2]:
            print(f"[INFO]: VSR{vsr.slot} ASIC{asic} temperature: {vsr.get_asic_temperature(idx=asic)}")

        print(f"[INFO]: VSR{vsr.slot} adc temperature: {vsr.get_adc_temperature()}")

        print(vsr.get_power())
        print("-"*80)

def path_reset():
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_TIG_CTRL['addr'],data= 0x0,  burst_len=1)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_TIG_CTRL['addr'], data=0x1, burst_len=1)

def data_en(enable = True):
    if enable:
        Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL['addr'], data=0x1, burst_len=1)
    else:
        Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL['addr'], data=0x0, burst_len=1)

def frame_reset_to_zero():
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_FRAME_PRELOAD_LOWER['addr'], data=0x0,
                                    burst_len=1)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_FRAME_PRELOAD_UPPER['addr'], data=0x0,
                                    burst_len=1)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL['addr'], data=0x1,
                                    burst_len=1)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL['addr'], data=0x0,
                                    burst_len=1)


if __name__ == '__main__':
    hostname = os.getenv('HOSTNAME').split('.')[0]
    print(f"Running on: {hostname}")
    if hostname.lower() == "te7hexidaq":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="10.0.3.1", local_port=61649,
                                 rdma_ip="10.0.3.2", rdma_port=61648, debug=False, uart_offset=0xC)
    elif hostname.lower() == "te7wendolene":
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                                 rdma_ip="192.168.4.2", rdma_port=61648, debug=False, uart_offset=0xC)
    else:
        Hex2x6CtrlRdma = RdmaUDP(local_ip="192.168.4.1", local_port=61649,
                                 rdma_ip="192.168.4.2", rdma_port=61648, debug=False, uart_offset=0xC)

    board_cfg_status = BoardCfgStatus(Hex2x6CtrlRdma,
                                      rdma_offset=rdma.get_id_offset(HEX_REGISTERS.IC_OFFSETS, 'BOARD_BUILD_INFO_ID'))
    print(f"{board_cfg_status.get_fpga_fw_version()}")
    print(f"{board_cfg_status.get_fpga_build_date()}")
    print(f"{board_cfg_status.get_fpga_build_time()}")
    print(f"{board_cfg_status.get_fpga_dna()}")
    print(f"{board_cfg_status.get_fpga_fw_git_hash()}")
    info_hdr = board_cfg_status.get_info_header()
    print(f"{info_hdr}")

    scratch_regs = board_cfg_status.read_scratch_regs(size=4)
    print(f"scratch registers: {[hex(i) for i in scratch_regs]}")
    board_cfg_status.write_scratch_regs([0x11110000, 0x22220000, 0x33330000, 0x44440000])
    scratch_regs = board_cfg_status.read_scratch_regs(size=4)
    print(f"scratch registers: {[hex(i) for i in scratch_regs]}")
    print("\n")

    # starting = time.time()
    vsr_addr_mapping = {1: 0x90, 2: 0x91, 3: 0x92, 4: 0x93, 5: 0x94, 6: 0x95}
    all_vsrs = VsrAssembly(Hex2x6CtrlRdma, init_time=10, addr_mapping=vsr_addr_mapping)
    vsr_assembly = time.time()
    # print(f" VsrAssembly() took: {vsr_assembly - starting}")
    all_vsrs.enable_module()
    finished_modules = time.time()
    print(f" .enable_module() took: {finished_modules - vsr_assembly}")
    all_vsrs.enable_vsr()
    ending = time.time()
    print(f" .enable_vsr() took: {ending - finished_modules}")
    print("Module(s) & VSR(s) ready")
    """:obj:`dict` A dictionary mapping VSR slot to VSR addr. This is hardware build dependent and can be determined by :meth:`VsrModule.lookup`"""
    vsrs = list()
    for vsr in vsr_addr_mapping.keys():
        vsrs.append(VsrModule(Hex2x6CtrlRdma, slot=vsr, init_time=10, addr_mapping=vsr_addr_mapping))

    # input("press enter to enable data")
    # Hex2x6CtrlRdma.udp_rdma_write(address=0x20, data=0x1, burst_len=4)  # EN_DATA
    # print("data enabled")

    for vsr in vsrs:
        # print(f"pll lock value before initialise for vsr {vsr.slot}: ",
        #       vsr._fpga_reg_read(VSR_FPGA_REGISTERS.REG137['addr']))
        vsr.initialise()
        ppl_lock = vsr._fpga_reg_read(VSR_FPGA_REGISTERS.REG137['addr'])
        while True:
            if ppl_lock & 1:
                break
            time.sleep(0.1)
            ppl_lock = vsr._fpga_reg_read(VSR_FPGA_REGISTERS.REG137['addr'])
        print(f"pll lock value after initialise for vsr {vsr.slot}: ",
              ppl_lock)
        print("-" * 80)

    # input("Press enter to enable & disable training")
    Hex2x6CtrlRdma.udp_rdma_write(address=HEXITEC_2X6_VSR_DATA_CTRL['addr'], data=0x10 , burst_len=1, comment=" ") #EN_TRAINING
    time.sleep(0.2)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEXITEC_2X6_VSR_DATA_CTRL['addr'], data=0x00, burst_len=1, comment=" ") # Disable training

    number_vsrs = len(vsr_addr_mapping.keys())
    vsr_lock_status =  Hex2x6CtrlRdma.udp_rdma_read(address=0x3e8, burst_len=number_vsrs)
    for vsr in vsrs:
        if vsr_lock_status[vsr.slot-1] == 255:
            print(f"[INFO]  VSR{vsr.slot} lock_status: {vsr_lock_status[vsr.slot-1]}")
        else:
            print(f"[ERROR] VSR{vsr.slot} lock_status: {vsr_lock_status[vsr.slot-1]}")

    # input("Press enter to disable vsr training")
    for vsr in vsrs:
        vsr._disable_training()
        print(f"training disabled for vsr{vsr.slot}")
        # vsr.start_trigger_sm()
        # print(f"sm triggered for vsr{vsr.slot}")
    print("-"*10)

    # input("Press enter to enable sm")
    Hex2x6CtrlRdma.udp_rdma_write(address=0x1c, data=0x1, burst_len=1) #EN_SM
    print("fpga state machine enabled")

    # Collect offsets, switching HV on, checking HV power - Not part of aspect's readout recipe
    print("-=-=-=-=- Dark Images -=-=-=-=-")
    for vsr in vsrs:
        vsr.collect_offsets()
    print("-=-=-=-=-     Done    -=-=-=-=-")

    # input("press enter to enable data synth")
    # Hex2x6CtrlRdma.udp_rdma_write(address=0x20, data=0x80, burst_len=1)  # EN_SYNTH_DATA
    # print("data synth enabled")
    #
    # input("press enter to enable data along with synth")
    # Hex2x6CtrlRdma.udp_rdma_write(address=0x20, data=0x81, burst_len=1)  # EN_DATA
    # print("data and synth enabled")

    ### reset the frame number
    print("Executing: reset frame number")
    frame_reset_to_zero()

    ### reset the datapath
    print("Executing: reset output path")
    path_reset()

    print("Allow F/W time to exit reset state")
    time.sleep(1)

    input("Press enter to enable data (200 ms)")
    data_en(enable=True)
    print("data enabled")
    time.sleep(0.2)

    ### stop the data flow
    print("Executing: disable data")
    data_en(enable=False)
