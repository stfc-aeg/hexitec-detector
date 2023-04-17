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
    # from BoardCfgStatus import *
    # from VsrModule import *
    # from RDMA_REGISTERS import *


def write_receive_to_all(vsr_list, op_command, register_h, register_l,
                         value_h, value_l):  # pragma: no coverage
    """Write and receive to all VSRs."""
    for vsr in vsr_list:
        vsr.send_cmd([op_command, register_h, register_l, value_h, value_l])
        vsr._read_response()


def convert_list_to_string(int_list):
    r"""Convert list of integer into ASCII string.

    I.e. integer_list = [42, 144, 70, 70, 13], returns '*\x90FF\r'
    """
    return "{}".format(''.join([chr(x) for x in int_list]))


def read_receive_from_all(vsr_list, op_command, register_h, register_l):  # pragma: no coverage
    """Read and receive from all VSRs."""
    reply = []
    for vsr in vsr_list:
        vsr.send_cmd([op_command, register_h, register_l])
        resp = vsr._read_response()
        resp = convert_list_to_string(resp)
        resp = resp[2:-1]
        reply.append(resp)
    return reply


def are_capture_dc_ready(vsrs_register_89):  # pragma: no coverage
    """Check status of Register 89, bit 0: Capture DC ready."""
    vsrs_ready = True
    for vsr in vsrs_register_89:
        dc_capture_ready = ord(vsr[1]) & 1
        if not dc_capture_ready:
            vsrs_ready = False
    return vsrs_ready


def collect_offsets(vsr_list):
    """Run collect offsets sequence.

    Stop state machine, gathers offsets, calculats average picture, re-starts state machine.
    """
    # 1. System is fully initialised (Done already)

    # 2. Stop the state machine

    write_receive_to_all(vsr_list, 0x43, 0x30, 0x31, 0x30, 0x31)

    # 3. Set reg 0x24 to 0x22

    print("Gathering offsets..")
    # Send reg value; Register 0x24, bits5,1: disable VCAL, capture average picture:
    write_receive_to_all(vsr_list, 0x40, 0x32, 0x34, 0x32, 0x32)

    # 4. Start the state machine

    write_receive_to_all(vsr_list, 0x42, 0x30, 0x31, 0x30, 0x31)

    # 5. Wait > 8192 * frame time (~1 second, @ 9118.87Hz)

    expected_duration = 8192 / 9118.87
    timeout = (expected_duration * 1.2) + 1
    # print(" *** expected: {} timeout: {}".format(expected_duration, timeout))
    poll_beginning = time.time()
    print("Collecting dark images..")
    dc_captured = False
    while not dc_captured:
        vsrs_register_89 = read_receive_from_all(vsr_list, 0x41, 0x38, 0x39)
        # print(" *** vsrs_register_89: ", vsrs_register_89)
        dc_captured = are_capture_dc_ready(vsrs_register_89)
        if 0:   # pragma: no coverage
            print("Register 0x89: {0}, Done? {1} Timing: {2:2.5} s".format(
                vsrs_register_89, dc_captured, time.time() - poll_beginning))
        if time.time() - poll_beginning > timeout:
            raise Exception("Dark images timed out. R.89: {}".format(
                vsrs_register_89))

    # 6. Stop state machine
    write_receive_to_all(vsr_list, 0x43, 0x30, 0x31, 0x30, 0x31)

    # 7. Set reg 0x24 to 0x28

    print("Offsets collected")
    # Send reg value; Register 0x24, bits5,3: disable VCAL, enable spectroscopic mode:
    write_receive_to_all(vsr_list, 0x40, 0x32, 0x34, 0x32, 0x38)

    # 8. Start state machine

    write_receive_to_all(vsr_list, 0x42, 0x30, 0x31, 0x30, 0x31)

    print("Ensure VCAL remains on")
    write_receive_to_all(vsr_list, 0x43, 0x32, 0x34, 0x32, 0x30)

    print("Offsets collections operation completed.")


# Copied in from HexitecFem
def fem_enable_adc(vsr):
    """Enable the ADCs."""
    print("Disable ADC/Enable DAC")     # 90 55 02 ;Disable ADC/Enable DAC
    vsr.send_cmd([0x55, 0x30, 0x32])
    vsr._read_response()

    print("Enable SM")      # 90 43 01 01 ;Enable SM
    vsr.send_cmd([0x43, 0x30, 0x31, 0x30, 0x31])
    vsr._read_response()

    print("Disable SM")     # 90 42 01 01 #Disable SM
    vsr.send_cmd([0x42, 0x30, 0x31, 0x30, 0x31])
    vsr._read_response()

    print("Enable ADC/Enable DAC")  # 90 55 03  ;Enable ADC/Enable DAC
    vsr.send_cmd([0x55, 0x30, 0x33])
    vsr._read_response()

    print("Write ADC register")     # 90 53 16 09   ;Write ADC Register
    vsr.send_cmd([0x53, 0x31, 0x36, 0x30, 0x39])  # Works just as the one below
    vsr._read_response()
    # self.write_and_response(vsr.addr, 0x31, 0x36, 0x30, 0x39)


# Copied in from HexitecFem
def write_dac_values(vsr):
    """Write values to DAC, optionally provided by hexitec file."""
    print("Writing DAC values")
    vcal = [0x30, 0x31, 0x46, 0x46]     # [0x30, 0x32, 0x41, 0x41]
    umid = [0x30, 0x46, 0x46, 0x46]     # [0x30, 0x35, 0x35, 0x35]
    hv = [0x30, 0x35, 0x35, 0x35]
    dctrl = [0x30, 0x30, 0x30, 0x30]
    rsrv2 = [0x30, 0x38, 0x45, 0x38]

    # print(" *** umid_value: {} vcal_value: {}".format(umid_value, vcal_value))
    vsr.send_cmd([0x54,
                 vcal[0], vcal[1], vcal[2], vcal[3],       # Vcal, e.g. 0x0111 = 0.2V
                 umid[0], umid[1], umid[2], umid[3],       # Umid, e.g. 0x0555 = 1.0V
                 hv[0], hv[1], hv[2], hv[3],               # reserve1, 0x0555 = 1V (HV ~-250)
                 dctrl[0], dctrl[1], dctrl[2], dctrl[3],   # DET ctrl, 0x000
                 rsrv2[0], rsrv2[1], rsrv2[2], rsrv2[3]])  # reserve2, 0x08E8 = 1.67V
    vsr._read_response()
    print("DAC values set")


# Copied in from HexitecFem
def initialise_vsr(vsr):
    """Initialise a VSR."""
    value_002 = 0x30, 0x31  # RowS1 Low Byte value: 1 = maximum frame rate
    value_003 = 0x30, 0x30  # RowS1 High Byte value : 0 = ditto
    value_004 = 0x30, 0x31  # S1 -> Sph, 6 bits : 1 = ... Yes, what?
    value_005 = 0x30, 0x36  # SphS2, 6 bits : 6 = ... Yes, what?
    value_006 = 0x30, 0x31  # Gain, 1 bit : 0 = High Gain; 1 = Low Gain
    value_009 = 0x30, 0x32  # ADC1 Delay, 5 bits : 2 = 2 clock cycles
    value_00E = 0x30, 0x41
    value_018 = 0x30, 0x31  # VCAL2 -> VCAL1 Low Byte, 8 bits: 1 = 1 clock cycle
    value_019 = 0x30, 0x30  # VCAL2 -> VCAL1 High Byte, 7 bits

    """
    90	42	01	10	;Select external Clock
    90	42	07	03	;Enable PLLs
    90	42	02	01	;LowByte Row S1
    """
    delayed = False  # Debugging: Extra 0.2 second delay between read, write?
    masked = False
    # Select external Clock
    vsr.write_and_response(0x30, 0x31, 0x31, 0x30)
    # Enable PLLs; 1 = Enable PLL; 2 = Enable ADC PLL
    # vsr.write_and_response(0x30, 0x37, 0x30, 0x33)
    vsr.send_cmd([0x42, 0x30, 0x37, 0x30, 0x33])
    vsr._read_response(cmd_no=0)

    vsr.write_and_response(0x30, 0x32, value_002[0], value_002[1],
                           masked=masked, delay=delayed)   # LowByte Row S1
    vsr.write_and_response(0x30, 0x33, value_003[0], value_003[1],
                           masked=masked, delay=delayed)   # HighByte Row S1
    """
    90	42	04	01	;S1Sph
    90	42	05	06	;SphS2
    90	42	09	02	;ADC Clock Delay
    90	42	0E	0A	;FVAL/LVAL Delay
    90	42	1B	08	;SM wait Clock Row
    90	42	14	01	;Start SM on falling edge
    90	42	01	20	;Enable LVDS Interface
    """
    vsr.write_and_response(0x30, 0x34, value_004[0], value_004[1],
                           masked=masked, delay=delayed)     # S1Sph
    vsr.write_and_response(0x30, 0x35, value_005[0], value_005[1],
                           masked=masked, delay=delayed)     # SphS2
    vsr.write_and_response(0x30, 0x36, value_006[0], value_006[1], delay=delayed)  # Gain
    # ADC Clock Delay:
    # vsr.write_and_response(0x30, 0x39, value_009[0], value_009[1], delay=delayed)
    vsr.send_cmd([0x42, 0x30, 0x39, value_009[0], value_009[1]])
    vsr._read_response()
    # FVAL/LVAL Delay:
    # vsr.write_and_response(0x30, 0x45, value_00E[0], value_00E[1], delay=delayed)
    vsr.send_cmd([0x42, 0x30, 0x45, value_00E[0], value_00E[1]])
    vsr._read_response()
    # SM wait Low Row, 8 bits:
    # vsr.write_and_response(0x31, 0x42, 0x30, 0x38)
    vsr.send_cmd([0x42, 0x31, 0x42, 0x30, 0x38])
    vsr._read_response()
    # Start SM on falling edge ('0' = rising edge) of ADC-CLK:
    # vsr.write_and_response(0x31, 0x34, 0x30, 0x31)
    vsr.send_cmd([0x42, 0x31, 0x34, 0x30, 0x31])
    vsr._read_response()
    vsr.write_and_response(0x30, 0x31, 0x32, 0x30)    # Enable LVDS Interface
    """
    90	44	61	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Column Read En
    90	44	4D	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Column PWR En
    90	44	57	00	00	00	00	00	00	00	00	00	00	;Column Cal En
    90	44	43	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Row Read En
    90	44	2F	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Row PWR En
    90	44	39	00	00	00	00	00	00	00	00	00	00	;Row Cal En
    90	54	01	FF	0F	FF	05	55	00	00	08	E8	;Write DAC
    """
    # TODO Not loading any of enables..
    # self.load_pwr_cal_read_enables()

    write_dac_values(vsr)
    """
    90	55	02	;Disable ADC/Enable DAC
    90	43	01	01	;Enable SM
    90	42	01	01	;Disable SM
    90	55	03	;Enable ADC/Enable DAC
    90	53	16	09	;Write ADC Register
    """
    # TODO Converted across HexitecFem's version of the enabling adcs
    fem_enable_adc(vsr)
    """
    90	40	24	22	;Disable Vcal/Capture Avg Picture
    90	40	24	28	;Disable Vcal/En DC spectroscopic mode
    90	42	01	80	;Enable Training
    90	42	18	01	;Low Byte SM Vcal Clock
    90	43	24	20	;Enable Vcal
    90	42	24	20	;Disable Vcal
    """
    # Disable Vcal/Capture Avg Picture (False=don't mask)
    vsr.write_and_response(0x32, 0x34, 0x32, 0x32, False)
    # print("Disable Vcal/En DC spectroscopic mode")
    # Disable Vcal/En DC spectroscopic mode (False=don't mask)
    vsr.write_and_response(0x32, 0x34, 0x32, 0x38, False)
    print("Enable Training")
    vsr.write_and_response(0x30, 0x31, 0x38, 0x30)    # Enable Training
    # self.send_cmd([0x42, 0x30, 0x31, 0x38, 0x30])
    # self._read_response()

    # vsr.write_and_response(0x31, 0x38, 0x30, 0x31) # Low Byte SM Vcal Clock
    # TODO: Inserting VCal setting here
    # Send VCAL2 -> VCAL1 low byte to Register 0x02 (Accepts 8 bits)
    vsr.write_and_response(0x31, 0x38, value_018[0], value_018[1], False)
    # Send VCAL2 -> VCAL1 high byte to Register 0x03 (Accepts 7 bits)
    vsr.write_and_response(0x31, 0x39, value_019[0], value_019[1], False)
    # vsr.write_and_response(0x32, 0x34,	0x32, 0x30) # Enable Vcal
    print("Enable Vcal")  # 90	43	24	20	;Enable Vcal
    vsr.send_cmd([0x43, 0x32, 0x34, 0x32, 0x30])
    vsr._read_response()
    # vsr.write_and_response(0x32, 0x34, 0x32, 0x30)     # Disable Vcal

    """MR's tcl script also also set these two:"""
    # set queue_1 { { 0x40 0x01 0x30    "Disable_Training" } \
    #             { 0x40 0x0A 0x01      "Enable_Triggered_SM_Start" }
    # }


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

    board_cfg_status = BoardCfgStatus(
        Hex2x6CtrlRdma, rdma_offset=rdma.get_id_offset(
            HEX_REGISTERS.IC_OFFSETS, 'BOARD_BUILD_INFO_ID'))
    # print(f"{board_cfg_status.get_fpga_fw_git_hash()}")
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
    print(f"scratch registers: {[hex(i) for i in scratch_regs]}")
    # Read scratch registers
    board_cfg_status.write_scratch_regs([0x11110000, 0x22220000, 0x33330000, 0x44440000])
    scratch_regs = board_cfg_status.read_scratch_regs(size=4)
    print(f"scratch registers: {[hex(i) for i in scratch_regs]}")

    vsr_addr_mapping = {1: 0x90, 2: 0x91, 3: 0x92, 4: 0x93, 5: 0x94, 6: 0x95}
    """:obj:`dict` A dictionary mapping VSR slot to VSR addr. This is hardware build dependent
        and can be determined by :meth:`VsrModule.lookup`"""

    vsr_1 = VsrModule(Hex2x6CtrlRdma, slot=1, addr_mapping=vsr_addr_mapping)
    print("Beforehand")
    print(f"[INFO] Status: {vsr_1.get_module_status()} | H/V Status: {vsr_1.get_hv_status()}")

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

    # # Readout HV voltages - Requires porting _get_power_sensors() - TODO Reverify
    # for idx in range(1):
    #     print(" -=-=-=-=-=-=-=-=-=-=-")
    #     for vsr in vsr_list:
    #         print(f" VSR{vsr.addr-143} HV: {round(vsr._get_power_sensors(), 2)}")

    # New Implementation

    # Initialise VSR, train Kintex VLDS, Check VSR locked - TODO Reverify

    vsr_1.initialise()

    print("Did PLL(s) lock?")
    bPolling = True
    while bPolling:
        pll_status = vsr_1.read_pll_status()
        if pll_status & 1:
            bPolling = False
        else:
            time.sleep(0.2)

    # Training Kintex

    print(f"LVDS Training.. Address: {HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL['addr']:X}")
    VSR_DATA_CTRL = HEX_REGISTERS.HEXITEC_2X6_VSR_DATA_CTRL
    Hex2x6CtrlRdma.udp_rdma_write(address=VSR_DATA_CTRL['addr'],
                                  data=0x10, burst_len=1,
                                  comment=VSR_DATA_CTRL['description'])
    time.sleep(0.2)
    Hex2x6CtrlRdma.udp_rdma_write(address=VSR_DATA_CTRL['addr'],
                                  data=0x10, burst_len=1,
                                  comment=VSR_DATA_CTRL['description'])

    # Check VSR Locked
    vsr_status_addr = HEX_REGISTERS.HEXITEC_2X6_VSR0_STATUS['addr']
    for vsr in vsr_list:
        index = vsr.addr - 144
        locked = Hex2x6CtrlRdma.udp_rdma_read(vsr_status_addr, burst_len=1,
                                              comment=f"VSR {index} status register")
        if (locked == 0xFF):
            print("VSR{0} Locked (0x{1:X})".format(vsr.addr-143, locked))
        else:
            print("VSR{0} incomplete lock! (0x{1:X}) ****".format(vsr.addr-143, locked))
        vsr_status_addr += 4

    # Old Implementation

    # TODO Initialisation - Verified
    number_registers = 1
    the_start = time.time()
    reg07 = []
    reg89 = []
    for vsr in vsr_list:
        print(f" -=-=- VSR{vsr.addr-143} -=-=- ")
        initialise_vsr(vsr)

        bPolling = True
        time_taken = 0
        while bPolling:
            (address_h, address_l) = (0x38, 0x39)
            _, r89_reply_list = vsr.block_read_and_response(number_registers, address_h, address_l)
            LSB = ord(r89_reply_list[0][1])
            # Is PLL locked? (bit1 high)
            if LSB & 2:
                bPolling = False
            else:
                time.sleep(0.2)
                time_taken += 0.2
            if time_taken > 3.0:
                print(" *** VSR{} PLL still disabled! ***".format(vsr-144))
                bPolling = False
        reg89.append(r89_reply_list[0])
        (address_h, address_l) = (0x30, 0x37)
        _, r7_reply_list = vsr.block_read_and_response(number_registers, address_h, address_l)
        reg07.append(r7_reply_list[0])
    print(f"Register 07: {reg07}")
    print(f"Register 89: {reg89}")
    print("LVDS Training..")
    Hex2x6CtrlRdma.udp_rdma_write(address=HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                  data=0x10, burst_len=1, cmd_no=0x0,
                                  comment=HEXITEC_2X6_VSR_DATA_CTRL['description'])
    time.sleep(0.2)
    Hex2x6CtrlRdma.udp_rdma_write(address=HEXITEC_2X6_VSR_DATA_CTRL['addr'],
                                  data=0x10, burst_len=1, cmd_no=0x0,
                                  comment=HEXITEC_2X6_VSR_DATA_CTRL['description'])
    vsr_status_addr = HEXITEC_2X6_VSR0_STATUS['addr']
    for vsr in vsr_list:
        index = vsr.addr - 144
        locked = Hex2x6CtrlRdma.udp_rdma_read(vsr_status_addr, burst_len=1, cmd_no=0,
                                              comment=f"VSR {index} status register")[0]
        if (locked == 0xFF):
            print("VSR{0} Locked (0x{1:X})".format(vsr.addr-143, locked))
        else:
            print("VSR{0} incomplete lock! (0x{1:X}) ****".format(vsr.addr-143, locked))
        vsr_status_addr += 4
    the_stop = time.time()
    print(f"Initialisation took: {the_stop - the_start}")

    # TODO Collect offsets - Verified
    collect_offsets(vsr_list)

    # TODO Switches off all VSRs - Verified
    # print("Switching OFF all VSRs..")
    # success = vsr_1._ctrl(True, op="disable")
    # if not success:
    #     print("Failed to disable all VSRs")

    # # TODO Readout Read, Power, Calibration Enables - Verified
    # rpc_start = time.time()
    # for vsr in vsr_list:
    #     print(f"VSR{vsr.addr-143}")
    #     vsr.readout_vsr_register("Column Read  Enable ASIC1", 0x36, 0x31)
    #     vsr.readout_vsr_register("Column Read  Enable ASIC2", 0x43, 0x32)
    #     vsr.readout_vsr_register("Column Power Enable ASIC1", 0x34, 0x44)
    #     vsr.readout_vsr_register("Column Power Enable ASIC2", 0x41, 0x45)
    #     vsr.readout_vsr_register("Column Calib Enable ASIC1", 0x35, 0x37)
    #     vsr.readout_vsr_register("Column Calib Enable ASIC2", 0x42, 0x38)

    #     vsr.readout_vsr_register("Row    Read  Enable ASIC1", 0x34, 0x33)
    #     vsr.readout_vsr_register("Row    Read  Enable ASIC2", 0x41, 0x34)
    #     vsr.readout_vsr_register("Row    Power Enable ASIC1", 0x32, 0x46)
    #     vsr.readout_vsr_register("Row    Power Enable ASIC2", 0x39, 0x30)
    #     vsr.readout_vsr_register("Row    Calib Enable ASIC1", 0x33, 0x39)
    #     vsr.readout_vsr_register("Row    Calib Enable ASIC2", 0x39, 0x41)
    # rpc_stop = time.time()
    # print(f"Reading out Read, Power, Calib Enables took: {rpc_stop - rpc_start}")
