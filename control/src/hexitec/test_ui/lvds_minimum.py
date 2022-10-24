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
        # print("   WaR. RD1 reply: {} (resp: {})".format(reply, resp))
        resp = resp[2:-1]   # Extract payload
        if masked:
            value_h = value_h | resp[0]     # Mask existing value with new value
            value_l = value_l | resp[1]     # Mask existing value with new value
        # print("   WaR Write: {0:X} {1:X} {2:X} {3:X} {4:X}".format(vsr, address_h, address_l, value_h, value_l))
        self.send_cmd([vsr, 0x40, address_h, address_l, value_h, value_l])
        if delay:
            time.sleep(0.2)
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        if delay:
            time.sleep(0.2)
        reply = resp[4:-1]                                      # Omit start char, vsr & register addresses, and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print("   WR. RD2 reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        return resp, reply

    def initialise_vsr(self, vsr):
        """Initialise a vsr."""
        # Specified in VSR1_Configure.txt
        """
        90	42	01	10	;Select external Clock
        90	42	07	03	;Enable PLLs
        """
        self.write_and_response(vsr, 0x30, 0x31, 0x31, 0x30)     # Select external Clock
        # self.send_cmd([vsr, 0x42, 0x30, 0x31, 0x31, 0x30])
        # self.read_response()
        """
        90	42	01	20	;Enable LVDS Interface
        """
        print("Enable LVDS Interface")
        self.write_and_response(vsr, 0x30, 0x31, 0x32, 0x30)     # Enable LVDS Interface
        # self.send_cmd([vsr, 0x42, 0x30, 0x31, 0x32, 0x30])
        # self.read_response()
        """
        90	43	01	01	;Disable SM
        90	42	01	01	;Enable SM
        """
        print("Disable SM")      # 90 43 01 01 ;Disable SM
        self.send_cmd([vsr, 0x43, 0x30, 0x31, 0x30, 0x31])
        self.read_response()
        print("Enable SM")     # 90 42 01 01 ;Enable SM
        self.send_cmd([vsr, 0x42, 0x30, 0x31, 0x30, 0x31])
        self.read_response()
        """
        90	42	01	80	;Enable Training
        """
        # self.write_and_response(vsr, 0x30, 0x31, 0x38, 0x30)     # Enable Training
        self.send_cmd([vsr, 0x42, 0x30, 0x31, 0x38, 0x30])
        self.read_response()
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


    enable_vsrs_mask = 0x3F
    hvs_bit_mask = 0x3F00
    vsr_ctrl_offset = 0x18
    ENABLE_VSR = 0xE3
    DISABLE_VSR = 0xE2

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
        VSR_ADDRESS = [0x90]
        hxt.enable_vsr(1)  # Switches a single VSR on
        # VSR_ADDRESS = range(0x90, 0x96, 1)
        # hxt.enable_all_vsrs()   # Switches on all VSR

        hxt.power_status()
        this_delay = 10
        print("VSR(s) enabled; Waiting {} seconds".format(this_delay))
        time.sleep(this_delay)

        print("Init modules (Send 0xE3..)")
        hxt.x10g_rdma.uart_tx([0xFF, 0xE3])
        # hxt.x10g_rdma.uart_tx([0x90, 0xE3])
        print("Wait 5 sec")
        time.sleep(5)

        for vsr in VSR_ADDRESS:
            hxt.initialise_vsr(vsr)

        print("set re_EN_TRAINING '1'")
        training_en_mask = 0x10
        hxt.x10g_rdma.write(0x00000020, 0x10, burst_len=1, comment="Enabling training")

        print("Waiting 0.2 seconds..")
        time.sleep(0.2)

        print("set re_EN_TRAINING '0'")
        training_en_mask = 0x00
        hxt.x10g_rdma.write(0x00000020, 0x00, burst_len=1, comment="Enabling training")

        vsr_status_addr = 0x000003E8  # Flags of interest: locked, +4 to get to the next VSR, et cetera for all VSRs
        for vsr in VSR_ADDRESS:
            index = vsr - 144
            vsr_status = hxt.x10g_rdma.read(vsr_status_addr, burst_len=1, comment="Read vsr{}_status".format(index))
            vsr_status = vsr_status[0]
            locked = vsr_status & 0xFF
            print("vsr{0}_status 0x{1:08X} = 0x{2:08X}. Locked? 0x{3:X}".format(index, vsr_status_addr, vsr_status, locked))
            vsr_status_addr += 4
            # time.sleep(0.5)

    except (socket.error, struct.error) as e:
        print(" *** Caught Exception: {} ***".format(e))

    hxt.disconnect()
