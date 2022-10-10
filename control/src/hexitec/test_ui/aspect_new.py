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
                break
        response = self.x10g_rdma.uart_rx(0x0)
        # print("R: {}. {}".format(response, counter))
        # print("... receiving: {} ({})".format(' '.join("0x{0:02X}".format(x) for x in response), counter))
        return response
        # return self.x10g_rdma.uart_rx(0x0)

    def debug_register(self, msb, lsb):  # pragma: no cover
        """Debug function: Display contents of register."""
        self.send_cmd([0x23, self.VSR_ADDRESS[1], self.READ_REG_VALUE,
                       msb, lsb, 0x0D])
        vsr2 = self.read_response()
        time.sleep(0.25)
        self.send_cmd([0x23, self.VSR_ADDRESS[0], self.READ_REG_VALUE,
                       msb, lsb, 0x0D])
        vsr1 = self.read_response()
        vsr2 = vsr2[2:-1]
        vsr1 = vsr1[2:-1]
        return (vsr2, vsr1)

    def dump_all_registers(self):  # pragma: no cover
        """Dump register 0x00 - 0xff contents to screen.

        aSpect's address format: 0x3F -> 0x33, 0x46 (i.e. msb, lsb)
        See HEX_ASCII_CODE, and section 3.3, page 11 of revision 0.5:
        aS_AM_Hexitec_VSR_Interface.pdf
        """
        for msb in range(16):
            for lsb in range(16):
                (vsr2, vsr1) = self.debug_register(self.HEX_ASCII_CODE[msb], self.HEX_ASCII_CODE[lsb])
                print(" \t\t\t\t* Register: {}{}: VSR2: {}.{} VSR1: {}.{}".format(hex(msb), hex(lsb)[-1],
                      chr(vsr2[0]), chr(vsr2[1]),
                      chr(vsr1[0]), chr(vsr1[1])))
                time.sleep(0.25)

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
        for index in range(number_registers):
            self.read_and_response(vsr, most_significant[index], least_significant[index])

    def write_dac_values(self, vsr_address):
        """Write values to DAC, optionally provided by hexitec file."""
        print("Writing DAC values")
        vcal = [0x30, 0x31, 0x46, 0x46]     # [0x30, 0x32, 0x41, 0x41]
        umid = [0x30, 0x46, 0x46, 0x46]     # [0x30, 0x35, 0x35, 0x35]
        hv = [0x30, 0x35, 0x35, 0x35]
        dctrl = [0x30, 0x30, 0x30, 0x30]
        rsrv2 = [0x30, 0x38, 0x45, 0x38]

        self.send_cmd([#self.
                       vsr_address, 0x54,
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

        print("Enable SM")      # 90 43 01 01 ;Enable SM
        self.send_cmd([self.vsr_addr, 0x43, 0x30, 0x31, 0x30, 0x31])
        self.read_response()

        print("Disable SM")     # 90 42 01 01 #Disable SM
        self.send_cmd([self.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31])
        self.read_response()

        print("Enable ADC/Enable DAC")  # 90 55 03  ;Enable ADC/Enable DAC
        self.send_cmd([self.vsr_addr, 0x55, 0x30, 0x33])
        self.read_response()

        print("Write ADC register")     # 90 53 16 09   ;Write ADC Register
        # self.send_cmd([self.vsr_addr, 0x53, 0x31, 0x36, 0x30, 0x39])  # Avoided
        # self.read_response()
        hxt.write_and_response(self.vsr_addr, 0x31, 0x36, 0x30, 0x39)

    # # TODO: WILL BE REQUIRED LATER ON OR NOT??? - Incomplete
    # def toggle_state_machine(self, vsr, address_h, address_l, value_h, value_l, enable):
    #     """Substitute for using CLR_REG_BIT = 0x43."""
    #     resp, reply = self.read_and_response(vsr, address_h, address_l)
    #     resp = resp[2:-1]   # Extract payload
    #     value_h = value_h | resp[0] # Mask existing value with new value
    #     value_l = value_l | resp[1] # Mask existing value with new value
    #     print("   WaR Write: {} {} {} {} {}".format(vsr, address_h, address_l, value_h, value_l))
    #     self.send_cmd([vsr, 0x40, address_h, address_l, value_h, value_l])
    #     resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
    #     reply = resp[4:-1]                                      # Omit start char, vsr & register addresses, and end char
    #     reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
    #     print(" WR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
    #     return resp, reply

    def initialise_vsr(self, vsr):
        """Initialise a vsr."""
        # Specified in VSR1_Configure.txt
        """
        90	42	01	10	;Select external Clock
        90	42	07	03	;Enable PLLs
        90	42	02	01	;LowByte Row S1
        """
        hxt.write_and_response(vsr, 0x30, 0x31, 0x31, 0x30)     # Select external Clock
        hxt.write_and_response(vsr, 0x30, 0x37, 0x30, 0x33)     # Enable PLLs
        hxt.write_and_response(vsr, 0x30, 0x32, 0x30, 0x38, delay=False)     # LowByte Row S1
        """
        90	42	04	01	;S1Sph
        90	42	05	06	;SphS2
        90	42	09	02	;ADC Clock Delay
        90	42	0E	0A	;FVAL/LVAL Delay
        90	42	1B	08	;SM wait Clock Row
        90	42	14	01	;Start SM on falling edge
        90	42	01	20	;Enable LVDS Interface
        """
        hxt.write_and_response(vsr, 0x30, 0x34, 0x30, 0x35, delay=False)     # S1Sph
        hxt.write_and_response(vsr, 0x30, 0x35, 0x31, 0x32, delay=False)     # SphS2
        hxt.write_and_response(vsr, 0x30, 0x39, 0x30, 0x32)     # ADC Clock Delay
        hxt.write_and_response(vsr, 0x30, 0x45, 0x30, 0x41)     # FVAL/LVAL Delay
        hxt.write_and_response(vsr, 0x31, 0x42, 0x30, 0x38)     # SM wait Low Row
        hxt.write_and_response(vsr, 0x31, 0x34, 0x30, 0x31)     # Start SM on falling edge
        hxt.write_and_response(vsr, 0x30, 0x31, 0x32, 0x30)     # Enable LVDS Interface
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
        print("Column Read Enable")
        hxt.block_write_and_response(vsr, number_registers, 0x36, 0x31, 0x46, 0x46)  # 61; Column Read En
        print("Column POWER Enable")
        hxt.block_write_and_response(vsr, number_registers, 0x34, 0x44, 0x46, 0x46)  # 4D; Column PWR En
        print("Column calibrate Enable")
        hxt.block_write_and_response(vsr, number_registers, 0x35, 0x37, 0x30, 0x30)  # 57; Column Cal En
        print("Row Read Enable")
        hxt.block_write_and_response(vsr, number_registers, 0x34, 0x33, 0x46, 0x46)  # 43; Row Read En
        print("Row POWER Enable")
        hxt.block_write_and_response(vsr, number_registers, 0x32, 0x46, 0x46, 0x46)  # 2F; Row PWR En
        print("Row calibrate Enable")
        hxt.block_write_and_response(vsr, number_registers, 0x33, 0x39, 0x30, 0x30)  # 39; Row Cal En
        hxt.write_dac_values(vsr)
        """
        90	55	02	;Disable ADC/Enable DAC
        90	43	01	01	;Enable SM
        90	42	01	01	;Disable SM
        90	55	03	;Enable ADC/Enable DAC
        90	53	16	09	;Write ADC Register
        """
        hxt.enable_adc(vsr)
        """
        90	40	24	22	;Disable Vcal/Capture Avg Picture
        90	40	24	28	;Disable Vcal/En DC spectroscopic mode
        90	42	01	80	;Enable Training
        90	42	18	01	;Low Byte SM Vcal Clock
        90	42	02	14	;Low Byte Row S1
        90	43	24	20	;Enable Vcal
        90	42	24	20	;Disable Vcal
        """
        hxt.write_and_response(vsr, 0x32, 0x34, 0x32, 0x32)     # Disable Vcal/Capture Avg Picture
        hxt.write_and_response(vsr, 0x32, 0x34, 0x32, 0x38)     # Disable Vcal/En DC spectroscopic mode
        hxt.write_and_response(vsr, 0x30, 0x31, 0x38, 0x30)     # Enable Training
        hxt.write_and_response(vsr, 0x31, 0x38, 0x30, 0x31)     # Low Byte SM Vcal Clock
        # hxt.write_and_response(vsr, 0x30, 0x32, 0x31, 0x34)     # Low Byte Row S1
        # hxt.write_and_response(vsr, 0x32, 0x34,	0x32, 0x30) # Enable Vcal
        print("Enable Vcal")  # 90	43	24	20	;Enable Vcal
        hxt.send_cmd([vsr, 0x43, 0x32, 0x34, 0x32, 0x30])
        hxt.read_response()
        hxt.write_and_response(vsr, 0x32, 0x34, 0x32, 0x30)     # Disable Vcal

        """MR's tcl script also also set these two:"""
        # set queue_1 { { 0x40 0x01 0x30                                              "Disable_Training" } \
        #             { 0x40 0x0A 0x01                                              "Enable_Triggered_SM_Start" }
        # }


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
        # vsr = 0x95
        # """ Revisit trying to substitute 0x43 command word i.e. clear_register_bit later """
#         hxt.toggle_state_machine(vsr, 0x30, 0x31, 0x30, 0x30, True)
# # 90	43	01	01	;Enable SM  # CLR BIT
# # 90	42	01	01	;Disable SM # SET BIT

        # raise socket.error("hello")

        # # # Execute equivalent of VSR1_Configure.txt:
        # for vsr in range(0x90, 0x96):
        #     print(" --- Initialising VSR 0{0:X} ---".format(vsr))
        #     hxt.initialise_vsr(vsr)
        #     # Check PLLs locked
        #     bPolling = True
        #     time_taken = 0
        #     while bPolling:
        #         r89_list, r89_value = hxt.read_register89(vsr)
        #         LSB = ord(r89_value[1])
        #         # Is PLL locked? (bit1 high)
        #         if LSB & 2:
        #             bPolling = False
        #         else:
        #             print(" R.89: {} {}".format(r89_value, r89_value[1], ord(r89_value[1])))
        #             time.sleep(0.2)
        #             time_taken += 0.2
        #         if time_taken > 3.0:
        #             raise HexitecFemError("Timed out polling register 0x89; PLL remains disabled")
        # ending = time.time()
        # print("That took: {}".format(ending - beginning))
        reg07 = []
        reg89 = []
        # print("VSR Row S1: (High, Low). S1Sph  SphS2:  adc clk delay: . FVAL/LVAL:  VCAL2, (H, L) ")
        print("VSR Row S1: (H, L). S1Sph  SphS2:  adc clk dly: . FVAL/LVAL:  VCAL2, (H, L) Gain")
        for vsr in range(0x90, 0x96):
            r7_list, r7_value = hxt.read_register07(vsr)
            reg07.append(r7_value)
            r89_list, r89_value = hxt.read_register89(vsr)
            reg89.append(r89_value)
            
            s1_high_resp, s1_high_reply = hxt.read_and_response(vsr, 0x30, 0x33)
            s1_low_resp, s1_low_reply = hxt.read_and_response(vsr, 0x30, 0x32)
            sph_resp, sph_reply = hxt.read_and_response(vsr, 0x30, 0x34)
            s2_resp, s2_reply = hxt.read_and_response(vsr, 0x30, 0x35)
            adc_clock_resp, adc_clock_reply = hxt.read_and_response(vsr, 0x30, 0x39)  # ADC Clock Delay
            vals_delay_resp, vals_delay_reply = hxt.read_and_response(vsr, 0x30, 0x45)  # FVAL/LVAL Delay
            vcal_high_resp, vcal_high_reply = hxt.read_and_response(vsr, 0x31, 0x39)  # VCAL2 -> VCAL1 high byte
            vcal_low_resp, vcal_low_reply = hxt.read_and_response(vsr, 0x31, 0x38)  # VCAL2 -> VCAL1 low byte
#
            gain_resp, gain_reply = hxt.read_and_response(vsr, 0x30, 0x36)  # Gain
            # print("VSR{} Row S1: {} (S1 High: {}). S1Sph : {}. SphS2 : {}".format(vsr-143, s1_low_reply, s1_high_reply, sph_reply, s2_reply))
            # print("VSR Row S1: (High, Low). S1Sph  SphS2:  adc clk delay: . FVAL/LVAL:  VCAL2, (H, L) ")
            # print("VSR Row S1: (H, L). S1Sph  SphS2:  adc clk dly: . FVAL/LVAL:  VCAL2, (H, L) Gain")
            print(" {}        {}  {}     {}     {}          {}             {}             {} {}  {}".format(
            # print(" {}            {}  {}      {}     {}          {}               {}            {} {}".format(
                    vsr-143,
                    s1_high_reply, s1_low_reply,
                    sph_reply,
                    s2_reply,
                    adc_clock_reply,
                    vals_delay_reply,
                    vcal_high_reply, vcal_low_reply,
                    gain_reply))

        print(" All vsrs, reg07: {}".format(reg07))
        print("           reg89: {}".format(reg89))

        # Test accessing FPGA registers
        # hxt.x10g_rdma.read_fpga_registers(0.2)

    except (socket.error, struct.error) as e:
        print(" *** Caught Exception: {} ***".format(e))

    hxt.disconnect()
