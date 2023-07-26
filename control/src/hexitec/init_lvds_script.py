import os.path
import time
from RdmaUdp import *
from boardcfgstatus.BoardCfgStatus import *
from hexitec_vsr.VsrModule import *
from udpcore.UdpCore import *
import ALL_RDMA_REGISTERS as HEX_REGISTERS


DAC_SCALE_FACTOR = 0.732


def get_env_values(vsrs):

    for vsr in vsrs:
        print(f"[INFO] Slot: {vsr.get_slot()} | VSR Address: {hex(vsr.get_addr())}")
        print(f"[INFO] Status: {vsr.get_module_status()} | H/V Status: {vsr.get_hv_status()}")
        print(f"[INFO] Status: {vsr.get_module_status()} | H/V Status: {vsr.get_hv_status()}")

        print(f"[INFO]: VSR{vsr.slot} temperature: {vsr.get_temperature()} °C")

        print(f"[INFO]: VSR{vsr.slot} humidity: {vsr.get_humidity()} %")

        for asic in [1, 2]:
            print(f"[INFO]: VSR{vsr.slot} ASIC{asic} temp: {vsr.get_asic_temperature(idx=asic)} °C")

        print(f"[INFO]: VSR{vsr.slot} adc temperature: {vsr.get_adc_temperature()} °C")

        print(vsr.get_power())
        print("-"*80)


def set_bit(register, field):
    reg_value = int(Hex2x6CtrlRdma.udp_rdma_read(register['addr'])[0])
    ctrl_reg = rdma.set_field(register, field, reg_value, 1)
    Hex2x6CtrlRdma.udp_rdma_write(register['addr'], ctrl_reg)


def reset_bit(register, field):
    reg_value = int(Hex2x6CtrlRdma.udp_rdma_read(register['addr'])[0])
    ctrl_reg = rdma.clr_field(register, field, reg_value)
    Hex2x6CtrlRdma.udp_rdma_write(register['addr'], ctrl_reg)


def path_reset():
    reset_bit(HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL, "HEXITEC_RST")
    set_bit(HEX_REGISTERS.HEXITEC_2X6_HEXITEC_CTRL, "HEXITEC_RST")


def data_en(enable=True):
    if enable:
        set_bit(HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL, "DATA_EN")
    else:
        reset_bit(HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL, "DATA_EN")


def frame_reset_to_zero():
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_FRAME_PRELOAD_LOWER['addr'],
                                  data=0x0, burst_len=1)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_FRAME_PRELOAD_UPPER['addr'],
                                  data=0x0, burst_len=1)
    set_bit(HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL, "FRAME_COUNTER_LOAD")
    reset_bit(HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL, "FRAME_COUNTER_LOAD")


def set_nof_frames(number_frames):
    answer = input("Do you want to capture set number of frames? y/n")
    if answer == '' or answer == 'y':
        set_bit(HEX_REGISTERS.HEXITEC_2X6_HEADER_CTRL, "ACQ_NOF_FRAMES_EN")
        print("Frame limited mode")
        Hex2x6CtrlRdma.udp_rdma_write(address=HEX_REGISTERS.HEXITEC_2X6_ACQ_NOF_FRAMES_LOWER['addr'],
                                      data=number_frames, burst_len=1)
        print("Number of frames set to: {0} 0x{0:X}".format(number_frames))
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


def make_list(pattern):
    """Create a list of 10 entries, each entry is pattern."""
    list_of_patterns = []
    for idx in range(0, 10):
        list_of_patterns.append(pattern)
    return list_of_patterns


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


def convert_string_exponential_to_integer(exponent):
    """Convert aspect format to fit dac format.

    Aspect's exponent format looks like: 1,003000E+2
    Convert to float (eg: 100.3), rounding to nearest
    int before scaling to fit DAC range.
    """
    number_string = str(exponent)
    number_string = number_string.replace(",", ".")
    number_float = float(number_string)
    number_int = int(round(number_float))
    return number_int


def _extract_exponential(parameter_dict, descriptor, bit_range):
    """Extract exponential descriptor from parameter_dict, check it's within bit_range."""
    valid_range = [0, 1 << bit_range]
    setting = -1
    try:
        unscaled_setting = parameter_dict   # [descriptor]
        scaled_setting = convert_string_exponential_to_integer(unscaled_setting)
        if scaled_setting >= valid_range[0] and scaled_setting <= valid_range[1]:
            setting = int(scaled_setting // DAC_SCALE_FACTOR)
        else:
            print("Error parsing %s, got: %s (scaled: % s) but valid range: %s-%s" %
                  (descriptor, unscaled_setting, scaled_setting, valid_range[0],
                   valid_range[1]))
            setting = -1
    except KeyError:
        raise Exception("ERROR: No '%s' Key defined!" % descriptor)
    return setting


def convert_aspect_float_to_dac_value(number_float):
    """Convert aspect float format to fit dac format.

    Convert float (eg: 1.3V) to mV (*1000), scale to fit DAC range
    before rounding to nearest int.
    """
    milli_volts = number_float * 1000
    number_scaled = int(round(milli_volts // DAC_SCALE_FACTOR))
    return number_scaled


def _extract_float(parameter_dict, descriptor):
    """Extract descriptor from parameter_dict, check within 0.0 - 3.0 (hardcoded) range."""
    valid_range = [0.0, 3.0]
    setting = -1
    try:
        setting = float(parameter_dict)  # [descriptor])
        if setting >= valid_range[0] and setting <= valid_range[1]:
            # Convert from volts to DAQ format
            setting = convert_aspect_float_to_dac_value(setting)
        else:
            print("Error parsing float %s, got: %s but valid range: %s-%s" %
                  (descriptor, setting, valid_range[0], valid_range[1]))
            setting = -1
    except KeyError:
        raise Exception("Missing Key: '%s'" % descriptor)
    return setting


def collect_offsets(vsrs, vcal_enabled):
    """Collect offsets across all VSRs in one fell swoop."""
    # 2. Stop the state machine
    stop_sm(vsrs)
    # 3. Set register 0x24 to 0x22
    set_dc_controls(vsrs, True, vcal_enabled, False)
    # 4. Start the state machine
    start_sm(vsrs)
    # 5. Wait > 8182 * frame time (~1 second, 9118.87Hz)
    await_dc_captured(vsrs)
    # 6. Stop state machine
    stop_sm(vsrs)
    # (7. Setting Register 0x24 to 0x28 - Redundant)
    # 8. Start state machine
    start_sm(vsrs)
    # Ensure VCAL remains on:
    clr_dc_controls(vsrs, False, vcal_enabled, False)


def stop_sm(vsrs):
    """Stop the state machine in VSRs."""
    for vsr in vsrs:
        # if vsr.slot == 1:
        #     vsr.debug = True
        vsr.disable_sm()
        # vsr.debug = False


def set_dc_controls(vsrs, capt_avg_pict, vcal_pulse_disable, spectroscopic_mode_en):
    """Set DC control(s) in all VSRs."""
    for vsr in vsrs:
        # if vsr.slot == 1:
        #     vsr.debug = True
        vsr.set_dc_control_bits(capt_avg_pict, vcal_pulse_disable, spectroscopic_mode_en)
        # vsr.debug = False


def clr_dc_controls(vsrs, capt_avg_pict, vcal_pulse_disable, spectroscopic_mode_en):
    """Clear DC control(s) in all VSRs."""
    for vsr in vsrs:
        # if vsr.slot == 1:
        #     vsr.debug = True
        vsr.clr_dc_control_bits(capt_avg_pict, vcal_pulse_disable, spectroscopic_mode_en)
        # vsr.debug = False


def start_sm(vsrs):
    """Start the state machine in VSRs."""
    for vsr in vsrs:
        # if vsr.slot == 1:
        #     vsr.debug = True
        vsr.enable_sm()
        # vsr.debug = False


def await_dc_captured(vsrs):
    """Wait for the Dark Correction frames to be collected."""
    poll_beginning = time.time()
    dc_ready = False
    while not dc_ready:
        dc_statuses = check_dc_statuses(vsrs)
        dc_ready = are_dc_ready(dc_statuses)
    poll_ending = time.time()
    print("[INFO] Collect offsets polling took: {0} seconds ".format(
        round(poll_ending - poll_beginning, 2)))


def check_dc_statuses(vsrs):
    """Check Register 89 status of all six VSRs."""
    replies = []
    for vsr in vsrs:
        replies.append(vsr.read_pll_status())
    return replies


def are_dc_ready(dc_statuses):
    """Check whether bit 0: 'Capture DC ready' set in Register 89."""
    all_dc_ready = True
    for status in dc_statuses:
        dc_ready = status & 1
        if not dc_ready:
            all_dc_ready = False
    return all_dc_ready


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

    # Reset the datapath
    print("Reset output path")
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

    """:obj:`dict` A dictionary mapping VSR slot to VSR addr. This is hardware build dependent and
    can be determined by :meth:`VsrModule.lookup`"""
    vsrs = list()
    for vsr in vsr_addr_mapping.keys():
        vsrs.append(VsrModule(Hex2x6CtrlRdma, slot=vsr, init_time=10,
                              addr_mapping=vsr_addr_mapping))

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

    vcal_enabled = True
    print(f" *** VCAL: {vcal_enabled}")
    vcal_param = "0.10"
    vcal = _extract_float(vcal_param, 'Control-Settings/VCAL')
    print(f"  vcal: {vcal} (0x{vcal:x}) from input: {vcal_param}")

    umid_param = "1,00000E+3"
    umid = _extract_exponential(umid_param, 'Control-Settings/Uref_mid', bit_range=12)
    print(f"  umid: {umid} (0x{umid:x}) from input: {umid_param}")

    # # Clear vcal pattern
    # column_calibration_mask_asic1 = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    # row_calibration_mask_asic1 = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    # column_calibration_mask_asic2 = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    # row_calibration_mask_asic2 = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

    # column_calibration_mask_asic1 = [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11]
    # row_calibration_mask_asic1 = [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11]
    # column_calibration_mask_asic2 = [0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33]
    # row_calibration_mask_asic2 = [0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33]

    column_calibration_mask_asic1 = []
    row_calibration_mask_asic1 = []
    column_calibration_mask_asic2 = []
    row_calibration_mask_asic2 = []
    pattern = 0x1

    print("Config VCAL, DAC, Umid")
    for vsr in vsrs:
        vsr.enable_vcal(vcal_enabled)
        asic = 1
        list_of_patterns = make_list(pattern)
        column_calibration_mask_asic1 = list_of_patterns
        row_calibration_mask_asic1 = list_of_patterns
        pattern += 1
        print(f"[INFO]  VSR{vsr.slot} ASIC: {asic} pattern: 0x{pattern:X}")
        vsr.set_column_calibration_mask(column_calibration_mask_asic1, asic)
        vsr.set_row_calibration_mask(row_calibration_mask_asic1, asic)

        asic = 2
        list_of_patterns = make_list(pattern)
        column_calibration_mask_asic1 = list_of_patterns
        row_calibration_mask_asic1 = list_of_patterns
        pattern += 1
        print(f"[INFO]  VSR{vsr.slot} ASIC: {asic} pattern: 0x{pattern:X}")
        vsr.set_column_calibration_mask(column_calibration_mask_asic1, asic)
        vsr.set_row_calibration_mask(row_calibration_mask_asic1, asic)

        # Set VCAL magnitude; 0x0CC (.15V) 111 (0.2) 155 (0.25) 199 (.3)
        vsr.set_dac_vcal(vcal)
        # Set umid magnitude; 0x0555 (1.0V)
        vsr.set_dac_umid(umid)

    print("Init VSRs")
    for vsr in vsrs:
        vsr.initialise()
        tOut = 0
        while True:
            pll_lock = vsr.read_pll_status()
            if pll_lock & 1:
                print(f"[INFO] VSR{vsr.slot} PLL locked in {tOut} s")
                break
            if tOut > 10:
                print(f"[ERROR] VSR{vsr.slot} PLL timed out!")
                break
            time.sleep(0.1)
            tOut += 0.1
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

    print("Disabling training for vsr(s)..")
    for vsr in vsrs:
        vsr._disable_training()
        # vsr.start_trigger_sm()
        # print(f"sm triggered for vsr{vsr.slot}")
    print("-"*10)

    Hex2x6CtrlRdma.udp_rdma_write(address=0x1c, data=0x1, burst_len=1)
    print("fpga state machine enabled")

    print("-=-=-=-=- Dark Images -=-=-=-=-")
    collect_offsets(vsrs, vcal_enabled)
    print("-=-=-=-=-     Done    -=-=-=-=-")

    # Hex2x6CtrlRdma.dbg = True
    print("  Reset frame number")
    frame_reset_to_zero()

    print("  Set number of frames")
    set_nof_frames(18)

    # input("Press enter to enable data (200 ms)")
    print("  Enable data")
    data_en(enable=True)
    time.sleep(0.2)

    # Stop the data flow
    print("  Disable data")
    data_en(enable=False)
