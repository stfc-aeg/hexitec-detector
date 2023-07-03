import os.path
import time
from RdmaUdp import *
from boardcfgstatus.BoardCfgStatus import *
from hexitec_vsr.VsrModule import *
from udpcore.UdpCore import *
import ALL_RDMA_REGISTERS as HEX_REGISTERS


def get_env_values(vsrs):

    for vsr in vsrs:
        print(f"[INFO] Slot: {vsr.get_slot()} | VSR Address: {hex(vsr.get_addr())}")
        print(f"[INFO] Status: {vsr.get_module_status()} | H/V Status: {vsr.get_hv_status()}")
        print(f"[INFO] Status: {vsr.get_module_status()} | H/V Status: {vsr.get_hv_status()}")

        print(f"[INFO]: VSR{vsr.slot} temperature: {vsr.get_temperature()}")

        print(f"[INFO]: VSR{vsr.slot} humidity: {vsr.get_humidity()}")

        for asic in [1, 2]:
            print(f"[INFO]: VSR{vsr.slot} ASIC{asic} temp: {vsr.get_asic_temperature(idx=asic)} C   ***")

        print(f"[INFO]: VSR{vsr.slot} adc temperature: {vsr.get_adc_temperature()}")

        print(vsr.get_power())
        print("-"*80)


def path_reset():
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL['addr'],
                                  data=0x0,  burst_len=1)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL['addr'],
                                  data=0x1, burst_len=1)


def data_en(enable=True):
    if enable:
        Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                      data=0x1, burst_len=1)
    else:
        Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                      data=0x0, burst_len=1)


def frame_reset_to_zero():
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_FRAME_PRELOAD_LOWER['addr'],
                                  data=0x0, burst_len=1)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_FRAME_PRELOAD_UPPER['addr'],
                                  data=0x0, burst_len=1)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL['addr'],
                                  data=0x1, burst_len=1)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL['addr'],
                                  data=0x0, burst_len=1)


def set_nof_frames(number_frames):
    answer = input("Do you want to capture set number of frames? y/n")
    if answer == '' or answer == 'y':
        Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL['addr'],
                                      data=0x100, burst_len=1)
        print("Frame limited mode")
        Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_ACQ_NOF_FRAMES_LOWER['addr'],
                                      data=number_frames, burst_len=1)
        print("Number of frames set to 0x{0:X}".format(number_frames))
    else:
        print("Free acquisition mode")


def convert_to_aspect_format(value):
    """Convert integer to Aspect's hexadecimal notation e.g. 31 (0x1F) -> 0x31, 0x46."""
    HEX_ASCII_CODE = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                      0x41, 0x42, 0x43, 0x44, 0x45, 0x46]
    hex_string = "{:02x}".format(value)
    high_string = hex_string[0]
    low_string = hex_string[1]
    high_int = int(high_string, 16)
    low_int = int(low_string, 16)
    high_encoded = HEX_ASCII_CODE[high_int]
    low_encoded = HEX_ASCII_CODE[low_int]
    # print(" *** conv_to_aspect_..({}) -> {}, {}".format(value, high_encoded, low_encoded))
    return high_encoded, low_encoded


def convert_hv_to_hex(hv_value):
    """Convert HV voltage into hexadecimal value."""
    return int((hv_value / 1250) * 0xFFF)


def convert_bias_to_dac_values(hv):
    """Convert bias level to DAC formatted values.

    I.e. 21 V -> 0x0041 (0x30, 0x30, 0x34, 0x31)
    """
    hv_hex = convert_hv_to_hex(hv)
    # print(" Selected hv: {0}. Converted to hex: {1:04X}".format(hv, hv_hex))
    hv_hex_msb = hv_hex >> 8
    hv_hex_lsb = hv_hex & 0xFF
    hv_msb = convert_to_aspect_format(hv_hex_msb)
    hv_lsb = convert_to_aspect_format(hv_hex_lsb)
    # print(" Conv'd to aSp_M: {}".format(hv_msb))
    # print(" Conv'd to aSp_L: {}".format(hv_lsb))
    return hv_msb, hv_lsb


if __name__ == '__main__':
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

    ### reset the datapath
    print("Executing: reset output path")
    path_reset()

    board_cfg_status = BoardCfgStatus(Hex2x6CtrlRdma,
                                      rdma_offset=rdma.get_id_offset(HEX_REGISTERS.IC_OFFSETS,
                                                                     'BOARD_BUILD_INFO_ID'))
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

    vsr_addr_mapping = {1: 0x90, 2: 0x91, 3: 0x92, 4: 0x93, 5: 0x94, 6: 0x95}
    all_vsrs = VsrAssembly(Hex2x6CtrlRdma, init_time=10, addr_mapping=vsr_addr_mapping)

    # Enable module, VSRs
    init_vsrs_etc = True
    if init_vsrs_etc:
        vsr_assembly = time.time()
        all_vsrs.enable_module()
        finished_modules = time.time()
        print(f" .enable_module() took: {finished_modules - vsr_assembly}")
        all_vsrs.enable_vsr()
        ending = time.time()
        print(f" .enable_vsr()    took: {ending - finished_modules}")
    print("Module(s) & VSR(s) ready")

    """:obj:`dict` A dictionary mapping VSR slot to VSR addr. This is hardware build dependent and can be determined by :meth:`VsrModule.lookup`"""
    vsrs = list()
    for vsr in vsr_addr_mapping.keys():
        vsrs.append(VsrModule(Hex2x6CtrlRdma, slot=vsr, init_time=10, addr_mapping=vsr_addr_mapping))

    get_env_values(vsrs)
    time.sleep(1)

    bias_level = 10
    hv_msb, hv_lsb = convert_bias_to_dac_values(bias_level)
    print(f" HV Bias (-{bias_level}) : {hv_msb[0]:X} {hv_msb[1]:X} | {hv_lsb[0]:X} {hv_lsb[1]:X}")
    vsrs[0].hv_on(hv_msb, hv_lsb)
    time.sleep(1)

    print("Enable HV on each VSR")
    for vsr in vsrs:
        rc = vsr.hv_enable()
        if rc == 0:
            print(f" VSR{vsr.slot} Failed to enable HV!")

    time.sleep(1)
    for vsr in vsrs:
        pwr = vsr.get_power_sensors()
        print(f"After,  power sens: {pwr}")

    vcal_enabled = False
    print(f" *** VCAL: {vcal_enabled}")
    vcal_param = "0.10"
    vcal = vsrs[0]._extract_float(vcal_param, 'Control-Settings/VCAL')
    print(f"  vcal: {vcal} (0x{vcal:x}) from input: {vcal_param}")

    umid_param = "1,00000E+3"
    umid = vsrs[0]._extract_exponential(umid_param, 'Control-Settings/Uref_mid', bit_range=12)
    print(f"  umid: {umid} (0x{umid:x}) from input: {umid_param}")

    # column_calibration_mask = [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11]
    # row_calibration_mask = [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11]
    column_calibration_mask = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    row_calibration_mask = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

    print("Config VCAL, DAC, Umid")
    for vsr in vsrs:
        vsr.enable_vcal(vcal_enabled)
        vsr.set_column_calibration_mask(column_calibration_mask)
        vsr.set_row_calibration_mask(row_calibration_mask)

        # Set VCAL magnitude; 0x0CC (.15V) 111 (0.2) 155 (0.25) 199 (.3)
        vsr.set_dac_vcal(vcal)
        # Set umid magnitude; 0x0555 (1.0V)
        vsr.set_dac_umid(umid)

    print("Init VSRs")
    for vsr in vsrs:
        vsr.initialise()
        ppl_lock = vsr._fpga_reg_read(VSR_FPGA_REGISTERS.REG137['addr'])
        while True:
            if ppl_lock & 1:
                break
            time.sleep(0.1)
            ppl_lock = vsr._fpga_reg_read(VSR_FPGA_REGISTERS.REG137['addr'])
        print("-" * 80)

    Hex2x6CtrlRdma.udp_rdma_write(address=HEXITEC_2X6_VSR_DATA_CTRL['addr'], data=0x10,
                                  burst_len=1, comment=" ")  # EN_TRAINING
    time.sleep(0.2)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEXITEC_2X6_VSR_DATA_CTRL['addr'], data=0x00,
                                  burst_len=1, comment=" ")  # Disable training

    number_vsrs = len(vsr_addr_mapping.keys())
    vsr_lock_status = Hex2x6CtrlRdma.udp_rdma_read(address=0x3e8, burst_len=number_vsrs)
    for vsr in vsrs:
        if vsr_lock_status[vsr.slot-1] == 255:
            print(f"[INFO]  VSR{vsr.slot} lock_status: {vsr_lock_status[vsr.slot-1]}")
        else:
            print(f"[ERROR] VSR{vsr.slot} lock_status: {vsr_lock_status[vsr.slot-1]}")

    # input("Press enter to disable vsr training")
    print("Disabling training for vsr(s)..")
    for vsr in vsrs:
        vsr._disable_training()
        # vsr.start_trigger_sm()
        # print(f"sm triggered for vsr{vsr.slot}")
    print("-"*10)

    Hex2x6CtrlRdma.udp_rdma_write(address=0x1c, data=0x1, burst_len=1)
    print("fpga state machine enabled")

    print("-=-=-=-=- Dark Images -=-=-=-=-")
    for vsr in vsrs:
        vsr.collect_offsets()
    print("-=-=-=-=-     Done    -=-=-=-=-")

    ### reset the frame number
    print("Executing: reset frame number")
    frame_reset_to_zero()

    set_nof_frames(0x11)

    input("Press enter to enable data (200 ms)")
    data_en(enable=True)
    print("data enabled")
    time.sleep(0.2)

    ### stop the data flow
    print("Executing: disable data")
    data_en(enable=False)
