"""
Hexitec2x6: Exercises UDP control plane.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

import sys
from RdmaUDP import RdmaUDP
from ast import literal_eval
import socket
import struct
import time  # DEBUGGING only


class Hexitec2x6():
    """
    Hexitec 2x6 class.

    Test we can access scratch registers in the KinteX FPGA.
    """

    SEND_REG_VALUE = 0x40   # Verified to work with UART
    READ_REG_VALUE = 0x41   # Verified to work with UART
    SET_REG_BIT = 0x42      # Avoid
    CLR_REG_BIT = 0x43      # Not verified, tolerated twice, see enable_adc, "Enable Vcal"
    SEND_REG_BURST = 0x44   # Avoid
    READ_PWR_VOLT = 0x50    # Not used
    WRITE_REG_VAL = 0x53    # Avoid
    WRITE_DAC_VAL = 0x54    # Tolerated in: write_dac_values
    CTRL_ADC_DAC = 0x55     # Tolerated twice in: enable_adc

    VSR_ADDRESS = [
        0x90,
        0x91
    ]

    HEX_ASCII_CODE = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                      0x41, 0x42, 0x43, 0x44, 0x45, 0x46]

    def __init__(self, esdg_lab=False, debug=False, unique_cmd_no=False):
        """."""
        self.debug = debug
        self.unique_cmd_no = unique_cmd_no
        if esdg_lab:
            # Control IP addresses - MR
            self.local_ip = "192.168.4.1"  # Network card
            self.rdma_ip = "192.168.4.2"   # Hexitec 2x6 interface
        else:
            # Control IP addresses - CA
            self.local_ip = "10.0.3.1"  # Network card
            self.rdma_ip = "10.0.3.2"   # Hexitec 2x6 interface
        self.local_port = 61649
        self.rdma_port = 61648
        self.x10g_rdma = None
        self.vsr_addr = 0x90

    def __del__(self):
        """."""
        self.x10g_rdma.close()

    def connect(self):
        """Connect to the 10 G UDP control channel."""
        self.x10g_rdma = RdmaUDP(self.local_ip, self.local_port,
                                 self.rdma_ip, self.rdma_port,
                                 9000, 1, self.debug,
                                 unique_cmd_no)
        self.x10g_rdma.setDebug(self.debug)
        self.x10g_rdma.ack = False  # True
        return self.x10g_rdma.error_OK

    def disconnect(self):
        """."""
        self.x10g_rdma.close()

    def convert_list_to_string(self, int_list):
        """Convert list of integer into ASCII string.

        I.e. integer_list = [42, 144, 70, 70, 13], returns '*\x90FF\r'
        """
        return "{}".format(''.join([chr(x) for x in int_list]))

    def send_cmd(self, cmd):
        """Send a command string to the microcontroller."""
        # print("... sending: {}".format(' '.join("0x{0:02X}".format(x) for x in cmd)))
        self.x10g_rdma.uart_tx(cmd)

    def read_response(self):
        """Read a VSR's microcontroller response, passed on by the FEM."""
        counter = 0
        rx_pkt_done = 0
        while not rx_pkt_done:
            uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done = self.x10g_rdma.read_uart_status()
            counter += 1
            if counter == 15001:
                print("\n\t read_response() timed out waiting for uart!\n")
                break
        response = self.x10g_rdma.uart_rx(0x0)
        # print("R: {}. {}".format(response, counter))
        # print("... receiving: {} ({})".format(' '.join("0x{0:02X}".format(x) for x in response), counter))
        return response
        # return self.x10g_rdma.uart_rx(0x0)

    def get_vsr_register_value(self, vsr_number, address_high, address_low):
        """Read the VSR register At address_high, address_low."""
        self.send_cmd([vsr_number, self.READ_REG_VALUE, address_high, address_low])
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        reply = resp[2:-1]                                      # Omit start char, vsr & register addresses, and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" *** (R) Reg 0x{0:X}{1:X}, Received ({2}) from UART: {3}".format(address_high-0x30, address_low-0x30, len(resp), ' '.join("0x{0:02X}".format(x) for x in resp)))
        return resp, reply

    def read_register89(self, vsr_number):
        """Read out register 89."""
        # time.sleep(0.25)
        (address_high, address_low) = (0x38, 0x39)
        # print("Read Register 0x{0}{1}".format(address_high-0x30, address_low-0x30))
        return self.get_vsr_register_value(vsr_number, address_high, address_low)

    def read_register07(self, vsr_number):
        """Read out register 07."""
        # time.sleep(0.25)
        (address_high, address_low) = (0x30, 0x37)
        # print("Read Register 0x{0}{1}".format(address_high-0x30, address_low-0x30))
        return self.get_vsr_register_value(vsr_number, address_high, address_low)

    def read_and_response(self, vsr, address_h, address_l):
        """Send a read and read the reply."""
        # time.sleep(0.2)
        self.send_cmd([vsr, 0x41, address_h, address_l])
        # time.sleep(0.2)
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        reply = resp[2:-1]                                      # Omit start char, vsr address and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" RR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        return resp, reply

    def write_and_response(self, vsr, address_h, address_l, value_h, value_l, masked=True, delay=False):
        """Write value_h, value_l to address_h, address_l of vsr, if not masked then register value overwritten."""
        resp, reply = self.read_and_response(vsr, address_h, address_l)
        resp = resp[2:-1]   # Extract payload
        if masked:
            value_h = value_h | resp[0]     # Mask existing value with new value
            value_l = value_l | resp[1]     # Mask existing value with new value
        # print("   WaR Write: {} {} {} {} {}".format(vsr, address_h, address_l, value_h, value_l))
        self.send_cmd([vsr, 0x40, address_h, address_l, value_h, value_l])
        if delay:
            time.sleep(0.2)
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        if delay:
            time.sleep(0.2)
        reply = resp[4:-1]                                      # Omit start char, vsr & register addresses, and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" WR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        return resp, reply

    def block_write_and_response(self, vsr, number_registers, address_h, address_l, value_h, value_l):
        """Write value_h, value_l to address_h, address_l of vsr, spanning number_registers."""
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        for index in range(number_registers):
            # print("   BWaR Write: {} {} {} {} {}".format(vsr, most_significant[index], least_significant[index], value_h, value_l))
            self.write_and_response(vsr, most_significant[index], least_significant[index], value_h, value_l, False)

    def block_write_burst(self, vsr, number_registers, address_h, address_l, values_list):
        """Write values_list starting with address_h, address_l of vsr, spanning number_registers."""
        if (number_registers * 2) != len(values_list):
            print("Mismatch! number_registers ({}) isn't half of values_list ({}).".format(number_registers, len(values_list)))
            return -1
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        for index in range(number_registers):
            value_h = values_list.pop(0)
            value_l = values_list.pop(0)
            # print("   BWCL Write: {0:X} {1:X} {2:X} {3:X} {4:X}".format(vsr, most_significant[index], least_significant[index], value_h, value_l))
            self.write_and_response(vsr, most_significant[index], least_significant[index], value_h, value_l, True)

    def block_write_custom_length(self, vsr, number_registers, address_h, address_l, write_values):
        """Write write_values starting with address_h, address_l of vsr, spanning number_registers."""
        if (number_registers * 2) != len(write_values):
            print("Mismatch! number_registers ({}) isn't half of write_values ({}).".format(number_registers, len(write_values)))
            return -1
        values_list = write_values.copy()
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        for index in range(number_registers):
            value_h = values_list.pop(0)
            value_l = values_list.pop(0)
            # print("   BWCL Write: {0:X} {1:X} {2:X} {3:X} {4:X}".format(vsr, most_significant[index], least_significant[index], value_h, value_l))
            self.write_and_response(vsr, most_significant[index], least_significant[index], value_h, value_l, False)

    def expand_addresses(self, number_registers, address_h, address_l):
        """Expand addresses by the number_registers specified.

        ie If (number_registers, address_h, address_l) = (10, 0x36, 0x31)
        would produce 10 addresses of:
        (0x36 0x31) (0x36 0x32) (0x36 0x33) (0x36 0x34) (0x36 0x35)
        (0x36 0x36) (0x36 0x37) (0x36 0x38) (0x36 0x39) (0x36 0x41)
        """
        most_significant = []
        least_significant = []
        for index in range(address_l, address_l+number_registers):
            most_significant.append(address_h)
            least_significant.append(address_l)
            address_l += 1
            if address_l == 0x3A:
                address_l = 0x41
            if address_l == 0x47:
                address_h += 1
                if address_h == 0x3A:
                    address_h = 0x41
                address_l = 0x30
        return most_significant, least_significant

    def block_read_and_response(self, vsr, number_registers, address_h, address_l):
        """Read from address_h, address_l of vsr, covering number_registers registers."""
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        resp_list = []
        reply_list = []
        for index in range(number_registers):
            resp, reply = self.read_and_response(vsr, most_significant[index], least_significant[index])
            resp_list.append(resp[2:-1])
            reply_list.append(reply)
        return resp_list, reply_list

    def write_dac_values(self, vsr_address):
        """Write values to DAC, optionally provided by hexitec file."""
        print("Writing DAC values")
        vcal = [0x30, 0x31, 0x46, 0x46]     # [0x30, 0x32, 0x41, 0x41]
        umid = [0x30, 0x46, 0x46, 0x46]     # [0x30, 0x35, 0x35, 0x35]
        hv = [0x30, 0x35, 0x35, 0x35]
        dctrl = [0x30, 0x30, 0x30, 0x30]
        rsrv2 = [0x30, 0x38, 0x45, 0x38]

        self.send_cmd([vsr_address, 0x54,
                       vcal[0], vcal[1], vcal[2], vcal[3],          # Vcal, e.g. 0x0111 =: 0.2V
                       umid[0], umid[1], umid[2], umid[3],          # Umid, e.g. 0x0555 =: 1.0V
                       hv[0], hv[1], hv[2], hv[3],                  # reserve1, 0x0555 =: 1V (HV ~-250V)
                       dctrl[0], dctrl[1], dctrl[2], dctrl[3],      # DET ctrl, 0x000
                       rsrv2[0], rsrv2[1], rsrv2[2], rsrv2[3]])     # reserve2, 0x08E8 =: 1.67V
        self.read_response()
        print("DAC values set")

    def enable_adc(self, vsr_address):
        """Enable the ADCs."""
        self.vsr_addr = vsr_address
        print("Disable ADC/Enable DAC")     # 90 55 02 ;Disable ADC/Enable DAC
        self.send_cmd([self.vsr_addr, 0x55, 0x30, 0x32])
        self.read_response()

        print("Disable SM")      # 90 43 01 01 ;Disable SM
        self.send_cmd([self.vsr_addr, 0x43, 0x30, 0x31, 0x30, 0x31])
        self.read_response()

        print("Enable SM")     # 90 42 01 01 ;Enable SM
        self.send_cmd([self.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31])
        self.read_response()

        print("Enable ADC/Enable DAC")  # 90 55 03  ;Enable ADC/Enable DAC
        self.send_cmd([self.vsr_addr, 0x55, 0x30, 0x33])
        self.read_response()

        print("Write ADC register")     # 90 53 16 09   ;Write ADC Register
        # self.send_cmd([self.vsr_addr, 0x53, 0x31, 0x36, 0x30, 0x39])  # Avoided
        # self.read_response()
        self.write_and_response(self.vsr_addr, 0x31, 0x36, 0x30, 0x39)

    def initialise_vsr(self, vsr):
        """Initialise a vsr."""
        # Specified in VSR1_Configure.txt
        """
        90	42	01	10	;Select external Clock
        90	42	07	03	;Enable PLLs
        90	42	02	01	;LowByte Row S1
        """
        self.write_and_response(vsr, 0x30, 0x31, 0x31, 0x30)     # Select external Clock
        print("DS: Setting bit 0 in register 07")
        self.write_and_response(vsr, 0x30, 0x37, 0x30, 0x31)     # Enable PLLs
        self.write_and_response(vsr, 0x30, 0x32, 0x30, 0x31, delay=False)     # LowByte Row S1
        """
        90	42	04	01	;S1Sph
        90	42	05	06	;SphS2
        90	42	09	02	;ADC Clock Delay
        90	42	0E	0A	;FVAL/LVAL Delay
        90	42	1B	08	;SM wait Clock Row
        90	42	14	01	;Start SM on falling edge
        90	42	01	20	;Enable LVDS Interface
        """
        self.write_and_response(vsr, 0x30, 0x34, 0x30, 0x31, delay=False)     # S1Sph
        self.write_and_response(vsr, 0x30, 0x35, 0x31, 0x36, delay=False)     # SphS2
        self.write_and_response(vsr, 0x30, 0x39, 0x30, 0x32)     # ADC Clock Delay
        self.write_and_response(vsr, 0x30, 0x45, 0x30, 0x41)     # FVAL/LVAL Delay
        self.write_and_response(vsr, 0x31, 0x42, 0x30, 0x38)     # SM wait Low Row
        self.write_and_response(vsr, 0x31, 0x34, 0x30, 0x31)     # Start SM on falling edge
        self.write_and_response(vsr, 0x30, 0x31, 0x32, 0x30)     # Enable LVDS Interface
        """
        90	44	61	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Column Read En
        90	44	4D	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Column PWR En
        90	44	57	00	00	00	00	00	00	00	00	00	00	;Column Cal En
        90	44	43	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Row Read En
        90	44	2F	FF	FF	FF	FF	FF	FF	FF	FF	FF	FF	;Row PWR En
        90	44	39	00	00	00	00	00	00	00	00	00	00	;Row Cal En
        90	54	01	FF	0F	FF	05	55	00	00	08	E8	;Write DAC
        """
        number_registers = 10
        # As it was:
        print("Column Read Enable")
        self.block_write_and_response(vsr, number_registers, 0x36, 0x31, 0x46, 0x46)  # 61; Column Read En
        print("Column POWER Enable")
        self.block_write_and_response(vsr, number_registers, 0x34, 0x44, 0x46, 0x46)  # 4D; Column PWR En
        print("Column calibrate Enable")
        self.block_write_and_response(vsr, number_registers, 0x35, 0x37, 0x30, 0x30)  # 57; Column Cal En
        print("Row Read Enable")
        self.block_write_and_response(vsr, number_registers, 0x34, 0x33, 0x46, 0x46)  # 43; Row Read En
        print("Row POWER Enable")
        self.block_write_and_response(vsr, number_registers, 0x32, 0x46, 0x46, 0x46)  # 2F; Row PWR En
        print("Row calibrate Enable")
        self.block_write_and_response(vsr, number_registers, 0x33, 0x39, 0x30, 0x30)  # 39; Row Cal En

        self.write_dac_values(vsr)
        """
        90	55	02	;Disable ADC/Enable DAC
        90	43	01	01	;Disable SM
        90	42	01	01	;Enable SM
        90	55	03	;Enable ADC/Enable DAC
        90	53	16	09	;Write ADC Register
        """
        self.enable_adc(vsr)
        """
        90	40	24	22	;Disable Vcal/Capture Avg Picture
        90	40	24	28	;Disable Vcal/En DC spectroscopic mode
        90	42	01	80	;Enable Training
        90	42	18	01	;Low Byte SM Vcal Clock
        90	42	02	14	;Low Byte Row S1
        90	43	24	20	;Enable Vcal
        90	42	24	20	;Disable Vcal
        """
        self.write_and_response(vsr, 0x32, 0x34, 0x32, 0x32)     # Disable Vcal/Capture Avg Picture
        self.write_and_response(vsr, 0x32, 0x34, 0x32, 0x38)     # Disable Vcal/En DC spectroscopic mode

        self.write_and_response(vsr, 0x30, 0x31, 0x38, 0x30)     # Enable Training
        # print(" ! NOT enabling training on vsr - doing it on Kintex instead")
        # print("set re_EN_TRAINING '1'")
        # training_en_mask = 0x10
        # self.x10g_rdma.write(0x00000020, 0x10, burst_len=1, comment="Enabling training")

        # print("Enabling training on VSR: 0x{0:X}".format(vsr))
        # self.send_cmd([vsr, 0x42, 0x30, 0x31, 0x30, 0x38])
        # time.sleep(0.2)

        # print("set re_EN_TRAINING '0'")
        # training_en_mask = 0x00
        # self.x10g_rdma.write(0x00000020, 0x00, burst_len=1, comment="Enabling training")

        self.write_and_response(vsr, 0x31, 0x38, 0x30, 0x31)    # Low Byte SM Vcal Clock
        # self.write_and_response(vsr, 0x30, 0x32, 0x31, 0x34)     # Low Byte Row S1
        # self.write_and_response(vsr, 0x32, 0x34, 0x32, 0x30) # Enable Vcal
        print("Enable Vcal")  # 90	43	24	20	;Enable Vcal
        self.send_cmd([vsr, 0x43, 0x32, 0x34, 0x32, 0x30])
        self.read_response()
        self.write_and_response(vsr, 0x32, 0x34, 0x32, 0x30)     # Disable Vcal

        """MR's tcl script also also set these two:"""
        # set queue_1 { { 0x40 0x01 0x30                                              "Disable_Training" } \
        #             { 0x40 0x0A 0x01                                              "Enable_Triggered_SM_Start" }
        # }

    def enables_write_and_read_verify(self, vsr, address_h, address_l, write_list):
        """."""
        number_registers = 10
        self.block_write_custom_length(vsr, number_registers, address_h, address_l, write_list)

        resp_list, reply_list = self.block_read_and_response(vsr, number_registers, address_h, address_l)
        read_list = []
        for a, b in resp_list:
            read_list.append(a)
            read_list.append(b)
        if not (write_list == read_list):
            print(" Register 0x{0}{1}: ERROR".format(chr(address_h), chr(address_l)))
            print("     Wrote: {}".format(write_list))
            print("     Read : {}".format(read_list))
        else:
            print(" Register 0x{0}{1} -- ALL FINE".format(chr(address_h), chr(address_l)))

    enable_vsrs_mask = 0x3F
    hvs_bit_mask = 0x3F00
    vsr_ctrl_offset = 0x18
    ENABLE_VSR = 0xE3
    DISABLE_VSR = 0xE2

    def enable_vsr_or_hv(self, vsr_number, bit_mask):
        """Control a single VSR's power."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        # STEP 1: vsr_ctrl enable $::vsr_target_idx
        mod_mask = self.module_mask(vsr_number)
        cmd_mask = bit_mask
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | (cmd_mask & mod_mask)
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + vsr_number
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("VSR {} enabled".format(vsr_number))

    def enable_vsr(self, vsr_number):
        """Control a single VSR's power."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        # STEP 1: vsr_ctrl enable $::vsr_target_idx
        mod_mask = self.module_mask(vsr_number)
        cmd_mask = Hexitec2x6.enable_vsrs_mask
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | (cmd_mask & mod_mask)
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + vsr_number
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("VSR {} enabled".format(vsr_number))

    def disable_vsr(self, vsr_number):
        """Control a single VSR's power."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        # STEP 1: vsr_ctrl disable $::vsr_target_idx
        mod_mask = self.negative_module_mask(vsr_number)
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        # print("read_value: {}".format(read_value))
        # print("mod_mask: {}".format(mod_mask))
        masked_value = read_value & mod_mask
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + vsr_number
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.DISABLE_VSR])
        print("VSR {} disabled".format(vsr_number))

    def enable_all_vsrs(self):
        """Switch all VSRs on."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | 0x3F    # Switching all six VSRs on, i.e. set 6 bits on
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all VSRs on")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("All VSRs enabled")

    def enable_all_hv(self):
        """Switch all HVs on."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | Hexitec2x6.hvs_bit_mask     # Switching all six HVs on
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all HVs on")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("All HVs on")

    def enable_hv(self, hv_number):
        """Switch on a single VSR's power."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        # STEP 1: vsr_ctrl enable $::vsr_target_idx
        mod_mask = self.module_mask(hv_number)
        cmd_mask = Hexitec2x6.hvs_bit_mask
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | (cmd_mask & mod_mask)
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + hv_number
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("HV {} on".format(hv_number))

#
    def disable_all_hv(self):
        """Switch all HVs off."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value & 0x3F    # Switching all six HVs off
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all HVs off")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.DISABLE_VSR])
        print("All HVs off")

    def disable_all_vsrs(self):
        """Switch all VSRs off."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value & Hexitec2x6.hvs_bit_mask     # Switching all six VSRs off
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all VSRs off")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.DISABLE_VSR])
        print("All VSRs disabled")

    def power_status(self):
        """Read out the status register to check what is switched on and off."""
        read_value = self.x10g_rdma.read(Hexitec2x6.vsr_ctrl_offset, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        print(" *** Register status: 0x{0:08X}".format(read_value))

    def module_mask(self, module):
        """."""
        return ((1 << (module - 1)) | (1 << (module + 8 - 1)))

    def negative_module_mask(self, module):
        """."""
        return ~(1 << (module - 1)) | (1 << (module + 8 - 1))

    def readout_vsr_register(self, vsr, description, address_h, address_l):
        """Read out VSR register.

        Example: (vsr, description, address_h, address_l) = 1, "Column Read Enable ASIC2", 0x43, 0x32
        """
        number_registers = 10
        resp_list, reply_list = self.block_read_and_response(vsr, number_registers, address_h, address_l)
        print(" {0} (0x{1}{2}): {3}".format(description, chr(address_h), chr(address_l), reply_list))


if __name__ == '__main__':  # pragma: no cover
    if (len(sys.argv) != 4):
        print("Correct usage: ")
        print("python Hexitec2x6.py <esdg_lab> <debug> <unique_cmd_no>")
        print(" i.e. to not use esdg_lab addresses but enable debugging, and unique headers:")
        print("python Hexitec2x6.py False True True")
        sys.exit(-1)

    esdg_lab = literal_eval(sys.argv[1])
    debug = literal_eval(sys.argv[2])
    unique_cmd_no = literal_eval(sys.argv[3])
    hxt = Hexitec2x6(esdg_lab=esdg_lab, debug=debug, unique_cmd_no=unique_cmd_no)
    hxt.connect()
    beginning = time.time()
    try:

        # hxt.x10g_rdma.uart_tx([0x90, 0xF7])
        # response = hxt.read_response()
        # print("WHOIS resp: {}".format(' '.join("0x{0:02X}".format(x) for x in response)))

        # UNCOMMENT THE FOLLOWING 24 LINES - Debugging LVDS training
        # hxt.disable_all_vsrs()  # Working
        # time.sleep(1)
        # hxt.disable_all_hv()
        # hxt.power_status()
        # time.sleep(1)
        # hxt.enable_all_vsrs()

        VSR_ADDRESS = [0x90]    # range(0x90, 0x96, 1)

        # hxt.enable_vsr(1)  # Switches a single VSR on
        hxt.enable_all_vsrs()   # Switches on all VSR
        # time.sleep(1)
        hxt.power_status()
        this_delay = 10
        print("1st VSR enabled; Waiting {} seconds".format(this_delay))
        time.sleep(this_delay)

        print("Init modules (Send 0xE3..)")
        hxt.x10g_rdma.uart_tx([0xFF, 0xE3])
        print("Wait 5 sec")
        time.sleep(5)

        for vsr in VSR_ADDRESS:
            hxt.initialise_vsr(vsr)

        print("set re_EN_TRAINING '1'")
        training_en_mask = 0x10
        hxt.x10g_rdma.write(0x00000020, 0x10, burst_len=1, comment="Enabling training")

        print("Waiting 0.2 seconds..")
        time.sleep(0.2)
        # for vsr in VSR_ADDRESS:
        #     print("Enabling training on VSR: 0x{0:X}".format(vsr))
        #     hxt.send_cmd([vsr, 0x42, 0x30, 0x31, 0x30, 0x38])

        print("set re_EN_TRAINING '0'")
        training_en_mask = 0x00
        hxt.x10g_rdma.write(0x00000020, 0x00, burst_len=1, comment="Enabling training")

        # for vsr in VSR_ADDRESS:
        #     print("Disabling training on VSR: 0x{0:X}".format(vsr))
        #     print("Disabled training")
        #     hxt.send_cmd([vsr, 0x43, 0x30, 0x31, 0x30, 0x38])
        #     print("Enable triggered SM start")
        #     hxt.send_cmd([vsr, 0x40, 0x30, 0x41, 0x30, 0x31])

        # print("Set re_EN_SM '1'")
        # hxt.x10g_rdma.write(0x1C, 0x1, burst_len=1, comment="Set re_EN_SM '1'")
        # print("Set re_EN_DATA '1'")
        # hxt.x10g_rdma.write(0x20, 0x1, burst_len=1, comment="Set re_EN_DATA '1'")

        vsr_status_addr = 0x000003E8  # Flags of interest: locked, +4 to get to the next VSR, et cetera for all VSRs
        # for index in range(6):
        for vsr in VSR_ADDRESS:
            index = vsr - 144
            vsr_status = hxt.x10g_rdma.read(vsr_status_addr, burst_len=1, comment="Read vsr{}_status".format(index))
            vsr_status = vsr_status[0]
            locked = vsr_status & 0xFF
            print("vsr{0}_status 0x{1:08X} = 0x{2:08X}. Locked? 0x{3:X}".format(index, vsr_status_addr, vsr_status, locked))
            vsr_status_addr += 4
            time.sleep(0.5)

    except (socket.error, struct.error) as e:
        print(" *** Caught Exception: {} ***".format(e))

    hxt.disconnect()
