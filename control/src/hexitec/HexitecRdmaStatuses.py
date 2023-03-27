"""
HexitecRdmaStatuses.py: Start exercising new RDMA class.

Christian Angelsen, STFC Detector Systems Software Group, 2023.
"""

import time
import os.path

try:
    from hexitec.rdma_control.RdmaUdp import RdmaUDP
    from hexitec.rdma_control.BoardCfgStatus import construct_fpga_dna, \
        decode_fw_version, decode_build_info
    from hexitec.rdma_control.VsrModule import VsrModule
    from hexitec.rdma_control.RDMA_REGISTERS import BOARD_BUILD_INFO_SRC_VERSION, \
        BOARD_BUILD_INFO_BUILD_DATE, BOARD_BUILD_INFO_DNA_0, BOARD_BUILD_INFO_SCRATCH_1, \
        HEXITEC_2X6_VSR_DATA_CTRL, \
        HEXITEC_2X6_VSR0_STATUS  # , HEXITEC_2X6_VSR1_STATUS, HEXITEC_2X6_VSR2_STATUS, \
    #     HEXITEC_2X6_VSR3_STATUS, HEXITEC_2X6_VSR4_STATUS, HEXITEC_2X6_VSR5_STATUS
    # from hexitec.rdma_control.rdma_register_helpers import calc_shiftr, get_mmap_info, \
    #     get_mmap_field_info, get_field,, decode_field, encode_field, set_field, \
    #     clr_field
except ModuleNotFoundError:
    print("Silent ModuleNotFoundError ************")
    # from RdmaUdp import *
    # from BoardCfgStatus import *
    # from VsrModule import *
    # from RDMA_REGISTERS import *


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
                                  data=[0x11110001, 0x22220002, 0x33330003, 0x44440004],
                                  burst_len=4, cmd_no=0xAA, comment=scratch_1_comment)

    # Read scratch registers values
    burst_len = 4
    scratch = Hex2x6CtrlRdma.udp_rdma_read(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
                                           burst_len=burst_len, cmd_no=0xBB,
                                           comment=scratch_1_comment)
    old_scratch = [f"0x{hex(reg)[2:].zfill(8).upper()}" for reg in scratch]
    print(f"Scratch register: {old_scratch}")

    vsr_addr_mapping = {1: 0x90, 2: 0x91, 3: 0x92, 4: 0x93, 5: 0x94, 6: 0x95}
    """:obj:`dict` A dictionary mapping VSR slot to VSR addr. This is hardware build dependent
        and can be determined by :meth:`VsrModule.lookup`"""

    vsr_1 = VsrModule(Hex2x6CtrlRdma, slot=1, addr_mapping=vsr_addr_mapping)
    vsr_status = vsr_1._get_status(hv=False, all_vsrs=True)
    hv_status = vsr_1._get_status(hv=True, all_vsrs=True)
    print("Beforehand")
    print(f"[INFO] Status:     {vsr_status}")
    print(f"[INFO] H/V Status: {hv_status}")

    # # TODO Switches VSR 1 on, enables HV - Verified
    # # Turn VSR1 on
    # print(f"[INFO] Slot: {vsr_1.get_slot()} | VSR Address: {hex(vsr_1.get_addr())}")
    # print(f"[INFO] Status: {vsr_1._get_status()} | H/V Status: {vsr_1.get_hv_status()}")
    # print("Enabling module(s)..")
    # vsr_1.enable_module()
    # print("Turning HV on..")
    # vsr_1.hv_enable()
    # print(f"[INFO] Status: {vsr_1._get_status()} | H/V Status: {vsr_1.get_hv_status()}")

    # # Check statuses
    # module_status = vsr_1.get_module_status()
    # print(f"VSR1 Module status: {module_status}")
    # hv_status = vsr_1.get_hv_status()
    # print(f"VSR1 HV Status:     {hv_status}")

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

    # reg_addr_h, reg_addr_l = 0x36, 0x31
    # print("Testing reading vsr register {0:X} {1:X}".format(reg_addr_h, reg_addr_l))
    # reply = vsr_1._read_vsr_register(reg_addr_h, reg_addr_l)
    # print(f"  {reply}")

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
    # TODO Switches off all VSRs - Verified
    # print("Switching OFF all VSRs..")
    # success = vsr_1._ctrl(True, op="disable")
    # if not success:
    #     print("Failed to disable all VSRs")

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

    # # TODO HEXITEC_2X6_VSRx_STATUS - Long-winded - Verified
    # index = 1
    # locked = Hex2x6CtrlRdma.udp_rdma_read(address=HEXITEC_2X6_VSR0_STATUS['addr'],
    #                                       burst_len=1, cmd_no=0,
    #                                       comment=HEXITEC_2X6_VSR0_STATUS['description'])[0]
    # print(f" VSR{index} locked? 0x{locked:X}")
    # index += 1
    # locked = Hex2x6CtrlRdma.udp_rdma_read(address=HEXITEC_2X6_VSR1_STATUS['addr'],
    #                                       burst_len=1, cmd_no=0,
    #                                       comment=HEXITEC_2X6_VSR1_STATUS['description'])[0]
    # print(f" VSR{index} locked? 0x{locked:X}")
    # index += 1
    # locked = Hex2x6CtrlRdma.udp_rdma_read(address=HEXITEC_2X6_VSR2_STATUS['addr'],
    #                                       burst_len=1, cmd_no=0,
    #                                       comment=HEXITEC_2X6_VSR2_STATUS['description'])[0]
    # print(f" VSR{index} locked? 0x{locked:X}")
    # index += 1
    # locked = Hex2x6CtrlRdma.udp_rdma_read(address=HEXITEC_2X6_VSR3_STATUS['addr'],
    #                                       burst_len=1, cmd_no=0,
    #                                       comment=HEXITEC_2X6_VSR3_STATUS['description'])[0]
    # print(f" VSR{index} locked? 0x{locked:X}")
    # index += 1
    # locked = Hex2x6CtrlRdma.udp_rdma_read(address=HEXITEC_2X6_VSR4_STATUS['addr'],
    #                                       burst_len=1, cmd_no=0,
    #                                       comment=HEXITEC_2X6_VSR4_STATUS['description'])[0]
    # print(f" VSR{index} locked? 0x{locked:X}")
    # index += 1
    # locked = Hex2x6CtrlRdma.udp_rdma_read(address=HEXITEC_2X6_VSR5_STATUS['addr'],
    #                                       burst_len=1, cmd_no=0,
    #                                       comment=HEXITEC_2X6_VSR5_STATUS['description'])[0]
    # print(f" VSR{index} locked? 0x{locked:X} - Comment: {HEXITEC_2X6_VSR5_STATUS['description']}")

    # TODO HEXITEC_2X6_VSRx_STATUS - More concise.. - Verified
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

    #     reg07 = []
    #     reg89 = []
    #     for vsr in VSR_ADDRESS:
    #         (address_h, address_l) = (0x30, 0x37)
    # #         r7_list, r7_value = hxt.read_register07(vsr)
    # #         reg07.append(r7_value)
    #         (address_h, address_l) = (0x38, 0x39)
    #         r89_list, r89_value = hxt.read_register89(vsr)
    #         reg89.append(r89_value)
    #         s1_low_resp, s1_low_reply = hxt.read_and_response(vsr, 0x30, 0x32)
    #         s1_high_resp, s1_high_reply = hxt.read_and_response(vsr, 0x30, 0x33)
    #         sph_resp, sph_reply = hxt.read_and_response(vsr, 0x30, 0x34)
    #         s2_resp, s2_reply = hxt.read_and_response(vsr, 0x30, 0x35)
    #         print("VSR{} Row S1: 0x{}{}. S1Sph : 0x{}. SphS2 : 0x{}".format(
    #             vsr-143, s1_high_reply, s1_low_reply, sph_reply, s2_reply))

    #     print(" All vsrs, reg07: {}".format(reg07))
    #     print("           reg89: {}".format(reg89))

    # except (socket.error, struct.error) as e:
    #     print(" *** Caught Exception: {} ***".format(e))

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
