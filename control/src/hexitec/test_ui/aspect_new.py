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
        # print(" *** (R) Reg 0x{0:X}{1:X}, Received ({2}) from UART: {3}".format(address_high-0x30, address_low-0x30,
        #       len(resp), ' '.join("0x{0:02X}".format(x) for x in resp)))
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

    def burst_write(self, vsr, number_registers, address_h, address_l, write_values):
        """Write bytes to multiple registers."""
        command = [vsr, 0x44, address_h, address_l]
        for entry in write_values:
            command.append(entry)
        self.send_cmd(command)
        resp = self.read_response()
        reply = resp[4:-1]
        reply = "{}".format(''.join([chr(x) for x in reply]))
        # print(" BR. reply: {} (resp: {})".format(reply, resp))
        return resp, reply

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
        # print(" BRaR, resp_list: {} reply_list {}".format(resp_list, reply_list))
        # raise Exception("Premature!")
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

    def training_preparation(self, vsr):
        """Following Daniel's instructions, minimal requirements initialising a vsr for (LVDS) training."""
        """
        90	42	01	10	;Select external Clock  # Step 7
        90	42	01	20	;Enable LVDS Interface  # Step 16
        90	43	01	01	;Disable SM # Step 25
        90	42	01	01	;Enable SM  # Step 26
        90	42	01	80	;Enable Training    # Step 31
        """
        print("Executing training_preparation..")
        this_delay = False
        self.write_and_response(vsr, 0x30, 0x31, 0x31, 0x30, delay=this_delay)     # Select external Clock
        self.write_and_response(vsr, 0x30, 0x31, 0x32, 0x30, delay=this_delay)     # Enable LVDS Interface
        self.send_cmd([self.vsr_addr, 0x43, 0x30, 0x31, 0x30, 0x31])    # 90 43 01 01 ;Disable SM
        self.read_response()
        self.send_cmd([self.vsr_addr, 0x42, 0x30, 0x31, 0x30, 0x31])    # 90 42 01 01 ;Enable SM
        self.read_response()
        self.write_and_response(vsr, 0x30, 0x31, 0x38, 0x30, delay=this_delay)     # Enable Training
        print(".. Done!")

    def initialise_vsr(self, vsr):
        """Initialise a vsr."""
        # Specified in VSR1_Configure.txt
        """
        90	42	01	10	;Select external Clock
        90	42	07	03	;Enable PLLs
        90	42	02	01	;LowByte Row S1
        """
        self.write_and_response(vsr, 0x30, 0x31, 0x31, 0x30)     # Select external Clock
        self.write_and_response(vsr, 0x30, 0x37, 0x30, 0x33)     # Enable PLLs
        self.write_and_response(vsr, 0x30, 0x32, 0x30, 0x38, delay=False)     # LowByte Row S1
        """
        90	42	04	01	;S1Sph
        90	42	05	06	;SphS2
        90	42	09	02	;ADC Clock Delay
        90	42	0E	0A	;FVAL/LVAL Delay
        90	42	1B	08	;SM wait Clock Row
        90	42	14	01	;Start SM on falling edge
        90	42	01	20	;Enable LVDS Interface
        """
        self.write_and_response(vsr, 0x30, 0x34, 0x30, 0x35, delay=False)     # S1Sph
        self.write_and_response(vsr, 0x30, 0x35, 0x31, 0x32, delay=False)     # SphS2
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
        # # 61; Column Read En, using unique values not just repeating the same value over and over:
        # # resp_list, reply_list = self.block_read_and_response(vsr, number_registers, 0x36, 0x31)
        # # print(" AFTER, Column Read Enable: {}".format(reply_list))
        # self.block_write_custom_length(vsr, number_registers, 0x36, 0x31,
        #                                 # [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
        #                                 #  0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46])
        #                                 [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
        #                                  0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x30, 0x31, 0x32, 0x33])
        # number_registers = 10
        # # As it was:
        # print("Column Read Enable")
        # self.block_write_and_response(vsr, number_registers, 0x36, 0x31, 0x46, 0x46)  # 61; Column Read En
        # print("Column POWER Enable")
        # self.block_write_and_response(vsr, number_registers, 0x34, 0x44, 0x46, 0x46)  # 4D; Column PWR En
        # print("Column calibrate Enable")
        # self.block_write_and_response(vsr, number_registers, 0x35, 0x37, 0x30, 0x30)  # 57; Column Cal En
        # print("Row Read Enable")
        # self.block_write_and_response(vsr, number_registers, 0x34, 0x33, 0x46, 0x46)  # 43; Row Read En
        # print("Row POWER Enable")
        # self.block_write_and_response(vsr, number_registers, 0x32, 0x46, 0x46, 0x46)  # 2F; Row PWR En
        # print("Row calibrate Enable")
        # self.block_write_and_response(vsr, number_registers, 0x33, 0x39, 0x30, 0x30)  # 39; Row Cal En
#
        #     self.readout_vsr_register(vsr, "Column Read  Enable ASIC1", 0x36, 0x31)
        #     self.readout_vsr_register(vsr, "Column Read  Enable ASIC2", 0x43, 0x32)
        #     self.readout_vsr_register(vsr, "Column Power Enable ASIC1", 0x34, 0x44)
        #     self.readout_vsr_register(vsr, "Column Power Enable ASIC2", 0x41, 0x45)
        #     self.readout_vsr_register(vsr, "Column Calib Enable ASIC1", 0x35, 0x37)
        #     self.readout_vsr_register(vsr, "Column Calib Enable ASIC2", 0x42, 0x38)

        #     self.readout_vsr_register(vsr, "Row    Read  Enable ASIC1", 0x34, 0x33)
        #     self.readout_vsr_register(vsr, "Row    Read  Enable ASIC2", 0x41, 0x34)
        #     self.readout_vsr_register(vsr, "Row    Power Enable ASIC1", 0x32, 0x46)
        #     self.readout_vsr_register(vsr, "Row    Power Enable ASIC2", 0x39, 0x30)
        #     self.readout_vsr_register(vsr, "Row    Calib Enable ASIC1", 0x33, 0x39)
        #     self.readout_vsr_register(vsr, "Row    Calib Enable ASIC2", 0x39, 0x41)

        # # Start Writing and reading back values of the enables
        self.program_enables(vsr)

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
        self.write_and_response(vsr, 0x31, 0x38, 0x30, 0x31)     # Low Byte SM Vcal Clock
        # self.write_and_response(vsr, 0x30, 0x32, 0x31, 0x34)     # Low Byte Row S1
        # self.write_and_response(vsr, 0x32, 0x34,	0x32, 0x30) # Enable Vcal
        print("Enable Vcal")  # 90	43	24	20	;Enable Vcal
        self.send_cmd([vsr, 0x43, 0x32, 0x34, 0x32, 0x30])
        self.read_response()
        self.write_and_response(vsr, 0x32, 0x34, 0x32, 0x30)     # Disable Vcal

        """MR's tcl script also also set these two:"""
        # set queue_1 { { 0x40 0x01 0x30                                              "Disable_Training" } \
        #             { 0x40 0x0A 0x01                                              "Enable_Triggered_SM_Start" }
        # }

    def enables_write_and_read_verify(self, vsr, address_h, address_l, write_list):
        """Write and read to verify correct bytes written to register."""
        number_registers = 10
        # self.block_write_custom_length(vsr, number_registers, address_h, address_l, write_list)
        self.burst_write(vsr, number_registers, address_h, address_l, write_list)

        resp_list, reply_list = self.block_read_and_response(vsr, number_registers, address_h, address_l)
        # resp, reply = self.burst_read(vsr, address_h, address_l)
        # print("write_list: {}".format(write_list))
        read_list = []
        for a, b in resp_list:
            read_list.append(a)
            read_list.append(b)
        # print("read_list : {}".format(read_list))
        if not (write_list == read_list):
            print(" Register 0x{0}{1}: ERROR".format(chr(address_h), chr(address_l)))
            print("     Wrote: {}".format(write_list))
            print("     Read : {}".format(read_list))
        # else:
        #     print(" Register 0x{0}{1} -- ALL FINE".format(chr(address_h), chr(address_l)))
        # raise Exception("EXIT!")

    def burst_read(self, vsr, address_h, address_l):
        """Read from address_h, address_l of vsr, covering number_registers registers."""
        self.send_cmd([vsr, 0x41, address_h, address_l])
        resp = self.read_response()
        # print(" BurRd, \n resp: {}\n reply: {}\n".format(resp, reply))
        reply = resp[4:-1]
        reply = "{}".format(''.join([chr(x) for x in reply]))
        return resp, reply

    def program_enables(self, vsr):
        """Write enables to some of the registers."""
        address_h, address_l = 0x36, 0x31   # Register 0x61
        # #write_list: 0x46 0x39 0x33 0x46 0x33 0x45 0x46 0x46 0x46 0x31 0x45 0x37 0x38 0x46 0x46 0x46 0x37 0x43 0x46 0x43
        write_list = [70, 57, 51, 70, 51, 69, 70, 70, 70, 49, 69, 55, 56, 70, 70, 70, 55, 67, 70, 67]
        self.enables_write_and_read_verify(vsr, address_h, address_l, write_list)

        address_h, address_l = 0x43, 0x32   # Register 0xC2
        # #write_list: 0x34 0x38 0x32 0x43 0x46 0x41 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46
        write_list = [52, 56, 50, 67, 70, 65, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70]
        self.enables_write_and_read_verify(vsr, address_h, address_l, write_list)

        address_h, address_l = 0x34, 0x44   # Register 0x4D
        # [D 221014 09:34:39 HexitecFem:1336] Column Power Enable
        # write_list: 0x39 0x31 0x44 0x35 0x46 0x33 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46 0x46
        write_list = [57, 49, 68, 53, 70, 51, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70]
        self.enables_write_and_read_verify(vsr, address_h, address_l, write_list)

        address_h, address_l = 0x41, 0x45   # Register 0xAE
        # Column Power Enable ASIC2
        # write_list: 0x37 0x33 0x30 0x46 0x46 0x42 0x46 0x43 0x46 0x46 0x33 0x46 0x33 0x46 0x43 0x46 0x41 0x43 0x31 0x38
        write_list = [55, 51, 48, 70, 70, 66, 70, 67, 70, 70, 51, 70, 51, 70, 67, 70, 65, 67, 49, 56]
        self.enables_write_and_read_verify(vsr, address_h, address_l, write_list)

        address_h, address_l = 0x35, 0x37   # Register 0x57
        # [D 221014 09:34:39 HexitecFem:1336] Column Power Enable
        # write_list: 0x38 0x39 0x38 0x38 0x41 0x38 0x38 0x38 0x37 0x31 0x38 0x43 0x38 0x38 0x38 0x45 0x38 0x39 0x46 0x39
        write_list = [56, 57, 56, 56, 65, 56, 56, 56, 55, 49, 56, 67, 56, 56, 56, 69, 56, 57, 70, 57]
        self.enables_write_and_read_verify(vsr, address_h, address_l, write_list)

        """
[D 221018 14:46:48 HexitecFem:1417] Column Calibration Enable
  ... producing register_values: 0x38 0x39 0x38 0x38 0x41 0x38 0x38 0x38 0x37 0x31 0x38 0x43 0x38 0x38 0x38 0x45 0x38 0x39 0x46 0x39
   i.e.:  [56, 57, 56, 56, 65, 56, 56, 56, 55, 49, 56, 67, 56, 56, 56, 69, 56, 57, 70, 57]
 Register 0x57 -- ALL FINE
  ... producing register_values: 0x38 0x38 0x38 0x38 0x38 0x38 0x38 0x38 0x33 0x31 0x38 0x38 0x38 0x38 0x33 0x38 0x31 0x45 0x45 0x42
   i.e.:  [56, 56, 56, 56, 56, 56, 56, 56, 51, 49, 56, 56, 56, 56, 51, 56, 49, 69, 69, 66]
 Register 0xB8 -- ALL FINE
[D 221018 14:46:49 HexitecFem:1431] Row Read Enable
  ... producing register_values: 0x37 0x38 0x39 0x45 0x31 0x35 0x33 0x46 0x44 0x46 0x45 0x33 0x42 0x31 0x37 0x45 0x42 0x43 0x43 0x42
   i.e.:  [55, 56, 57, 69, 49, 53, 51, 70, 68, 70, 69, 51, 66, 49, 55, 69, 66, 67, 67, 66]
 Register 0x43 -- ALL FINE
  ... producing register_values: 0x31 0x46 0x46 0x46 0x46 0x38 0x33 0x37 0x43 0x37 0x37 0x46 0x33 0x45 0x44 0x45 0x46 0x38 0x46 0x31
   i.e.:  [49, 70, 70, 70, 70, 56, 51, 55, 67, 55, 55, 70, 51, 69, 68, 69, 70, 56, 70, 49]
 Register 0xA4 -- ALL FINE
[D 221018 14:46:49 HexitecFem:1445] Row Power Enable
  ... producing register_values: 0x33 0x35 0x44 0x42 0x42 0x38 0x46 0x45 0x46 0x46 0x41 0x46 0x38 0x44 0x39 0x39 0x36 0x35 0x43 0x33
   i.e.:  [51, 53, 68, 66, 66, 56, 70, 69, 70, 70, 65, 70, 56, 68, 57, 57, 54, 53, 67, 51]
 Register 0x2F -- ALL FINE
  ... producing register_values: 0x46 0x33 0x46 0x46 0x46 0x46 0x46 0x43 0x37 0x34 0x33 0x46 0x33 0x46 0x33 0x45 0x43 0x46 0x43 0x46
   i.e.:  [70, 51, 70, 70, 70, 70, 70, 67, 55, 52, 51, 70, 51, 70, 51, 69, 67, 70, 67, 70]
 Register 0x90 -- ALL FINE
[D 221018 14:46:50 HexitecFem:1459] Row Calibration Enable
  ... producing register_values: 0x38 0x38 0x38 0x38 0x38 0x38 0x38 0x38 0x31 0x38 0x38 0x38 0x38 0x38 0x43 0x38 0x41 0x43 0x31 0x38
   i.e.:  [56, 56, 56, 56, 56, 56, 56, 56, 49, 56, 56, 56, 56, 56, 67, 56, 65, 67, 49, 56]
 Register 0x39 -- ALL FINE
  ... producing register_values: 0x38 0x38 0x38 0x38 0x38 0x38 0x38 0x38 0x31 0x38 0x38 0x38 0x38 0x38 0x44 0x38 0x43 0x43 0x41 0x36
   i.e.:  [56, 56, 56, 56, 56, 56, 56, 56, 49, 56, 56, 56, 56, 56, 68, 56, 67, 67, 65, 54]
 Register 0x9A -- ALL FINE
"""

    def readout_vsr_register(self, vsr, description, address_h, address_l):
        """Read out VSR register.

        Example: (vsr, description, address_h, address_l) = 1, "Column Read Enable ASIC2", 0x43, 0x32
        """
        number_registers = 10
        resp_list, reply_list = self.block_read_and_response(vsr, number_registers, address_h, address_l)
        print(" {0} (0x{1}{2}): {3}".format(description, chr(address_h), chr(address_l), reply_list))


class HexitecFemError(Exception):
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass


if __name__ == '__main__':  # noqa: C901
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

        VSR_ADDRESS = range(0x90, 0x96)

        # hxt.x10g_rdma.disable_all_vsrs()  # Working
        # # hxt.x10g_rdma.disable_all_hv()
        # read_value = hxt.x10g_rdma.power_status()
        # if (read_value == 0x0):
        #     print(" OK Power: 0x{0:08X}".format(read_value))
        # else:
        #     print(" !! Power: 0x{0:08X}".format(read_value))
        # time.sleep(1)
        hxt.x10g_rdma.enable_all_vsrs()     # Switches all VSRs on
        # hxt.x10g_rdma.enable_vsr(1)  # Switches a single VSR on
        time.sleep(0.5)
        read_value = hxt.x10g_rdma.power_status()
        expected_value = 0x3F   # 0x1
        if (read_value == expected_value):
            print(" OK Power: 0x{0:08X}".format(read_value))
        else:
            print(" !! Power: 0x{0:08X}".format(read_value))
        this_delay = 10
        print("VSR(s) powered; Waiting {} seconds".format(this_delay))
        time.sleep(this_delay)

        # Send to UART: 0x90 0xE3
        # ... sending: 0x23 0x90 0xE3 0x0D
        print("Send E3 to all..")
        hxt.x10g_rdma.uart_tx([0xFF, 0xE3])
        print("Wait 5 sec")
        time.sleep(5)

        # Execute equivalent of VSR1_Configure.txt:
        for vsr in VSR_ADDRESS:
            print(" --- Initialising VSR 0{0:X} ---".format(vsr))
            hxt.initialise_vsr(vsr)
            # Check PLLs locked
            bPolling = True
            time_taken = 0
            while bPolling:
                r89_list, r89_value = hxt.read_register89(vsr)
                LSB = ord(r89_value[1])
                # Is PLL locked? (bit1 high)
                if LSB & 2:
                    bPolling = False
                else:
                    # print(" R.89: {} {}".format(r89_value, r89_value[1], ord(r89_value[1])))
                    time.sleep(0.2)
                    time_taken += 0.2
                if time_taken > 3.0:
                    raise HexitecFemError("Timed out polling VSR{} register 0x89; PLL remains disabled".format(vsr-144))
        ending = time.time()
        print("That took: {}".format(ending - beginning))

        reg07 = []
        reg89 = []
        # print("VSR Row S1: (High, Low). S1Sph  SphS2:  adc clk delay: . FVAL/LVAL:  VCAL2, (H, L) ")
        # print("VSR Row S1: (H, L). S1Sph  SphS2:  adc clk dly: . FVAL/LVAL:  VCAL2, (H, L) Gain")
        for vsr in VSR_ADDRESS:
            number_registers = 10
        #     hxt.readout_vsr_register(vsr, "Column Read  Enable ASIC1", 0x36, 0x31)
        #     hxt.readout_vsr_register(vsr, "Column Read  Enable ASIC2", 0x43, 0x32)
        #     hxt.readout_vsr_register(vsr, "Column Power Enable ASIC1", 0x34, 0x44)
        #     hxt.readout_vsr_register(vsr, "Column Power Enable ASIC2", 0x41, 0x45)
        #     hxt.readout_vsr_register(vsr, "Column Calib Enable ASIC1", 0x35, 0x37)
        #     hxt.readout_vsr_register(vsr, "Column Calib Enable ASIC2", 0x42, 0x38)

        #     hxt.readout_vsr_register(vsr, "Row    Read  Enable ASIC1", 0x34, 0x33)
        #     hxt.readout_vsr_register(vsr, "Row    Read  Enable ASIC2", 0x41, 0x34)
        #     hxt.readout_vsr_register(vsr, "Row    Power Enable ASIC1", 0x32, 0x46)
        #     hxt.readout_vsr_register(vsr, "Row    Power Enable ASIC2", 0x39, 0x30)
        #     hxt.readout_vsr_register(vsr, "Row    Calib Enable ASIC1", 0x33, 0x39)
        #     hxt.readout_vsr_register(vsr, "Row    Calib Enable ASIC2", 0x39, 0x41)

            r7_list, r7_value = hxt.read_register07(vsr)
            reg07.append(r7_value)
            r89_list, r89_value = hxt.read_register89(vsr)
            reg89.append(r89_value)

#             s1_high_resp, s1_high_reply = hxt.read_and_response(vsr, 0x30, 0x33)
#             s1_low_resp, s1_low_reply = hxt.read_and_response(vsr, 0x30, 0x32)
#             sph_resp, sph_reply = hxt.read_and_response(vsr, 0x30, 0x34)
#             s2_resp, s2_reply = hxt.read_and_response(vsr, 0x30, 0x35)
#             adc_clock_resp, adc_clock_reply = hxt.read_and_response(vsr, 0x30, 0x39)  # ADC Clock Delay
#             vals_delay_resp, vals_delay_reply = hxt.read_and_response(vsr, 0x30, 0x45)  # FVAL/LVAL Delay
#             vcal_high_resp, vcal_high_reply = hxt.read_and_response(vsr, 0x31, 0x39)  # VCAL2 -> VCAL1 high byte
#             vcal_low_resp, vcal_low_reply = hxt.read_and_response(vsr, 0x31, 0x38)  # VCAL2 -> VCAL1 low byte
# #
#             gain_resp, gain_reply = hxt.read_and_response(vsr, 0x30, 0x36)  # Gain
#             # DEBUG
#             # reg1_resp, reg1_reply = hxt.read_and_response(vsr, 0x30, 0x31)
#             # print("VSR{} Row S1: {} (S1 High: {}). S1Sph : {}. SphS2 : {}".format(vsr-143, s1_low_reply, s1_high_reply, sph_reply, s2_reply))
#             # print("VSR Row S1: (High, Low). S1Sph  SphS2:  adc clk delay: . FVAL/LVAL:  VCAL2, (H, L) ")
#             # print("VSR Row S1: (H, L). S1Sph  SphS2:  adc clk dly: . FVAL/LVAL:  VCAL2, (H, L) Gain")
#             print(" {}        {}  {}     {}     {}          {}             {}             {} {}  {}".format(
#             # print(" {}            {}  {}      {}     {}          {}               {}            {} {}".format(
#                     vsr-143,
#                     s1_high_reply, s1_low_reply,
#                     sph_reply,
#                     s2_reply,
#                     adc_clock_reply,
#                     vals_delay_reply,
#                     vcal_high_reply, vcal_low_reply,
#                     gain_reply))

        print(" All vsrs, reg07: {}".format(reg07))
        print("           reg89: {}".format(reg89))

    except (socket.error, struct.error) as e:
        print(" *** Caught Exception: {} ***".format(e))

    hxt.disconnect()
