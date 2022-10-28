"""
HexitecSanityChecker: Tests the 2x6 System Firmware.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

import sys
from RdmaUDP import RdmaUDP
from ast import literal_eval
import socket
import struct
import time  # DEBUGGING only


class HexitecSanityChecker():
    """
    Hexitec 2x6 class.

    Test we can access scratch registers in the KinteX FPGA.
    """

    READ_REG_VALUE = 0x41
    SET_REG_BIT = 0x42
    SEND_REG_BURST = 0x44

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

    def read_scratch_registers(self):
        """Read scratch registers."""
        scratch0 = self.x10g_rdma.read(0x00008030, burst_len=1, comment='Read Scratch Register 1')
        # # print(scratch0)
        # scratch1 = self.x10g_rdma.read(0x00008034, burst_len=1, comment='Read Scratch Register 2')
        # # print(scratch1)
        # scratch2 = self.x10g_rdma.read(0x00008038, burst_len=1, comment='Read Scratch Register 3')
        # scratch3 = self.x10g_rdma.read(0x0000803C, burst_len=1, comment='Read Scratch Register 4')
        # print("Scratch: 0x{0:08x}{1:08x}{2:08x}{3:08X}".format(scratch3, scratch2, scratch1, scratch0))
        print("Scratch: 0x{0:08x}".format(scratch0))

    def write_scratch_registers(self):
        """Write values to the four scratch registers."""
        self.x10g_rdma.write(0x8030, 0x12345678, burst_len=1, comment="New Scratch Register1 value")
        self.x10g_rdma.write(0x8034, 0x9ABCDEF1, burst_len=1, comment="New Scratch Register2 value")
        self.x10g_rdma.write(0x8038, 0xAAAAAAAA, burst_len=1, comment="New Scratch Register3 value")
        self.x10g_rdma.write(0x803C, 0x60054003, burst_len=1, comment="New Scratch Register4 value")

    def read_fpga_dna_registers(self):
        """Read the three DNA registers."""
        fpga_dna0 = self.x10g_rdma.read(0x0000800C, burst_len=1, comment='Read FPGA DNA part 1')
        fpga_dna1 = self.x10g_rdma.read(0x00008010, burst_len=1, comment='Read FPGA DNA part 2')
        fpga_dna2 = self.x10g_rdma.read(0x00008014, burst_len=1, comment='Read FPGA DNA part 3')
        print("FPGA DNA: 0x{0:08X} {1:08X} {2:08X}".format(fpga_dna2, fpga_dna1, fpga_dna0))

    def get_ambient_temperature(self, hex_val):
        """Calculate ambient temperature."""
        try:
            return ((int(hex_val, 16) * 175.72) / 65536) - 46.84
        except ValueError as e:
            print("Error converting ambient temperature: %s" % e)
            return -100

    def get_humidity(self, hex_val):
        """Calculate humidity."""
        try:
            return ((int(hex_val, 16) * 125) / 65535) - 6
        except ValueError as e:
            print("Error converting humidity: %s" % e)
            return -100

    def get_asic_temperature(self, hex_val):
        """Calculate ASIC temperature."""
        try:
            return int(hex_val, 16) * 0.0625
        except ValueError as e:
            print("Error converting ASIC temperature: %s" % e)
            return -100

    def get_adc_temperature(self, hex_val):
        """Calculate ADC Temperature."""
        try:
            return int(hex_val, 16) * 0.0625
        except ValueError as e:
            print("Error converting ADC temperature: %s" % e)
            return -100

    def display_environs(self, read_sensors):
        """Display environmental data in human readable format."""
        read_sensors = read_sensors[1:]  # Omit start of sequence character, matching existing 2x2 source code formatting
        sensors_values = "{}".format(''.join([chr(x) for x in read_sensors]))   # Turn list of integers into ASCII string
        # print(" ASCII string: {}".format(sensors_values))
        # print(" ambient:           humidity:          asic1:             asic2:          adc: ")
        print(" ({0}) {1:3.3f} C.  ({2}) {3:3.3f} %.  ({4}) {5:3.3f} C.  ({6}) {7:3.3f}  ({8}) {9:3.3f} C.".format(
            sensors_values[1:5], hxt.get_ambient_temperature(sensors_values[1:5]),
            sensors_values[5:9], hxt.get_humidity(sensors_values[5:9]),
            sensors_values[9:13], hxt.get_asic_temperature(sensors_values[9:13]),
            sensors_values[13:17], hxt.get_asic_temperature(sensors_values[13:17]),
            sensors_values[17:21], hxt.get_adc_temperature(sensors_values[17:21])))

    def await_uart_ready(self):
        """Wait until uart has received incoming data."""
        rx_pkt_done = 0
        counter = 0
        while not rx_pkt_done:
            uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done = hxt.x10g_rdma.read_uart_status()
            counter += 1
            if counter > 15000:
                raise Exception("Timed out waiting for UART data")
        # print("{0:05} UART: {1:08X} tx_buff_full: {2:0X} tx_buff_empty: {3:0X} rx_buff_full: {4:0X} rx_buff_empty: {5:0X} rx_pkt_done: {6:0X}".format(
        #     counter, uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done))

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
        reply = resp[2:-1]                                      # Omit start char, and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" *** (R) Reg 0x{0:X}{1:X}, Received ({2}) from UART: {3}".format(address_high-0x30, address_low-0x30,
        #       len(resp), ' '.join("0x{0:02X}".format(x) for x in resp)))
        return resp, reply

    def set_vsr_register_value(self, vsr_number, address_high, address_low, value_high, value_low):
        """Write the VSR register At address_high, address_low."""
        # self.send_cmd([vsr_number, self.SET_REG_BIT, address_high, address_low, value_high, value_low])
        # self.send_cmd([vsr_number, self.SEND_REG_BURST, address_high, address_low, value_high, value_low])
        self.send_cmd([vsr_number, 0x40, address_high, address_low, value_high, value_low])
        time.sleep(0.25)
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        reply = resp[4:-1]                                      # Omit start char, vsr & register addresses, and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" *** (W) Reg 0x{0:X}{1:X}, Received ({2}) from UART: {3}".format(
        #       address_high-0x30, address_low-0x30, len(read_sensors),
        #       ' '.join("0x{0:02X}".format(x) for x in resp)))
        return resp, reply

    def uart_reset(self):
        """Test if we can reset the UART."""
        uart_tx_ctrl_offset = 0xC
        uart_rx_ctrl_offset = 0x14
        uart_reset_mask = 0x1
        deassert_all = 0x0
        uart_tx_ctrl_addr = uart_tx_ctrl_offset
        uart_rx_ctrl_addr = uart_rx_ctrl_offset
        print("aSpect_UART_Tx_Control: RESET")
        # hxt.x10g_rdma.write(0x8030, 0x10203040, burst_len=1, comment="Set Scratch Reg1 value"
        self.x10g_rdma.write(uart_tx_ctrl_addr, uart_reset_mask, burst_len=1, comment="Apply UART Tx reset mask")
        self.x10g_rdma.write(uart_tx_ctrl_addr, deassert_all, burst_len=1, comment="Apply Tx deassert")
        # Allow reset to propagate through UART logic
        time.sleep(0.2)
        print("aSpect_UART_Rx_Control: RESET")
        self.x10g_rdma.write(uart_rx_ctrl_addr, uart_reset_mask, burst_len=1, comment="Apply UART Rx reset mask")
        self.x10g_rdma.write(uart_rx_ctrl_addr, deassert_all, burst_len=1, comment="Apply Rx deassert")
        # Allow reset to propagate through UART logic
        time.sleep(0.2)

    def compare(self, description, value_a, value_b):
        """Determine whether value_a and value_b are same or different."""
        if value_a == value_b:
            print("   {0} : PASSED.".format(description, value_a, value_b))
            # print("   {0} : PASSED. {1:X} == {2:X}".format(description, value_a, value_b))
        else:
            print(" ! {0} : FAILED, Read: {1:X} != Expected: {2:X}".format(description, value_a, value_b))

    def examine_whois_reply(self, response):
        """Examine WHOIS response from UART.

        Typically, all 6 VSRs combined response should be:
        0x90 0x34 0x91 0x34 0x92 0x34 0x93 0x34 0x94 0x34 0x95 0x34 0xC0 0x31
        """
        # response = [144, 52, 145, 52, 146, 52, 147, 52, 148, 52, 149, 52, 192, 49]
        if len(response) != 14:
            print(" WHOIS: Expected 14 bytes response, but got {}".format(len(response)))
            return -1
        ending_character = 0x31
        # Check ending characters there
        if (response[-1] != ending_character):
            print(" WHOIS: Response missing ending 0x{0:X} character".format(ending_character))
            return -1
        # Check 0xC0 also present
        if (response[-2] != 0xC0):
            print(" WHOIS: Response missing 0x{0:X} character".format(0xC0))
            return -1
        response = response[:-2]      # Omit final two Bytes
        # Separate out VSRs, responses
        for index in range(len(response)//2):
            vsr = response.pop(0)
            reply = response.pop(0)
            if (reply == 0x34):
                print("   WHOIS VSR 0x{0:X} : PASSED.".format(vsr))
            else:
                print(" ! WHOIS VSR 0x{0:X} : FAILED, replied 0x{1:X}".format(vsr, reply))

    def hammer_register(self):
        """Write, readback incremental values ensuring VSR register handle each new value."""
        vsr_number = 0x90
        # Readout S1 (Low) (register 002)
        # print("Readout S1 (Low) (register 002)")
        (address_high, address_low) = (0x30, 0x32)
        (value_high, value_low) = (0x30, 0x31)
        print("Writing Register 0x{0}{1}, values: {2:X}, {3:X}".format(
            address_high-0x30, address_low-0x30, value_high, value_low))
        for index in range(8):
            print("Write S1 (Low) (Reg 002), values: {0:X}, {1:X}".format(value_high, value_low))
            resp, reply = hxt.set_vsr_register_value(vsr_number, address_high, address_low, value_high, value_low)
            # print("   W.resp: {}. reply: {}".format(resp, reply))
            # print("   H: {} v {}, L: {} v {}".format(value_high, resp[4], value_low, resp[5]))
            # print("   W.H? {}, L? {}".format(value_high == resp[4], value_low == resp[5]))
            if (value_high != resp[4]) or (value_low != resp[5]):
                print(" ! W Reg 0x{0}{1} FAILED, wrote: {2:X}, {3:X} but returned: {4:X} {5:X}".format(
                    address_high-0x30, address_low-0x30, value_high, value_low, resp[4], resp[5]))

            resp, reply = hxt.get_vsr_register_value(vsr_number, address_high, address_low)
            # print("   R.resp: {}. reply: {}".format(resp, reply))
            # print("H: {} v {} L: {} v {}".format(resp[2], )
            # print("   R. H: {} v {}, L: {} v {}".format(value_high, resp[2], value_low, resp[3]))
            # print("   R. H? {} L? {}".format(value_high == resp[2], value_low == resp[3]))
            if (value_high != resp[2]) or (value_low != resp[3]):
                print(" ! R Reg 0x{0}{1} FAILED, expected: {2:X}, {3:X} but read: {4:X} {5:X}".format(
                    address_high-0x30, address_low-0x30, value_high, value_low, resp[2], resp[3]))
            value_low += 1


if __name__ == '__main__':  # pragma: no cover
    if (len(sys.argv) != 4):
        print("Correct usage: ")
        print("python HexitecSanityChecker.py <esdg_lab> <debug> <unique_cmd_no>")
        print(" i.e. to not use esdg_lab addresses but enable debugging, and unique headers:")
        print("python HexitecSanityChecker.py False True True")
        sys.exit(-1)

    esdg_lab = literal_eval(sys.argv[1])
    debug = literal_eval(sys.argv[2])
    unique_cmd_no = literal_eval(sys.argv[3])
    hxt = HexitecSanityChecker(esdg_lab=esdg_lab, debug=debug, unique_cmd_no=unique_cmd_no)
    hxt.connect()

    try:
        print(" * Reload bitstream before executing * ")
        print(" ------ Running Sanity Checker ------")
        expected_value = 0x0   # 0x1
        read_value = hxt.x10g_rdma.power_status()
        if (read_value == expected_value):
            print("   VSRs Power Status: 0x{0:08X} - All unpowered.".format(read_value))
        else:
            print(" ! VSR(s) already powered. Expected 0x{0:02X} not 0x{1:02X}".format(expected_value, read_value))
    except socket.error as e:
        print(" Failed to establish connection with Hardware: {} ".format(e))
        sys.exit(-1)

    try:
        # VSR_ADDRESS = [0x90]
        # hxt.x10g_rdma.enable_vsr(1)  # Switches a single VSR on
        print("Switch on VSRs..")
        VSR_ADDRESS = range(0x90, 0x96, 1)
        hxt.x10g_rdma.enable_all_vsrs()   # Switches on all VSR

        expected_value = 0x3F
        read_value = hxt.x10g_rdma.power_status()
        if (read_value == expected_value):
            print("   VSRs Power Status: 0x{0:08X} - All VSRs powered.".format(read_value))
        else:
            print(" ! VSR Power Issue(s). Expected 0x{0:02X} not 0x{1:02X}".format(expected_value, read_value))

        this_delay = 10
        print("Waiting {} seconds.. (VSRs booting)".format(this_delay))
        time.sleep(this_delay)

        # print("Init modules (Send 0xE3..)")
        hxt.x10g_rdma.uart_tx([0xFF, 0xE3])
        print("Waiting 5 sec.. (VSRs initialising")
        time.sleep(5)

        print("Sending WHOIS Command..")
        print(" ------ WHOIS Reply ------")
        hxt.x10g_rdma.uart_tx([0xFF, 0xF7])
        time.sleep(1)
        read_sensors = hxt.x10g_rdma.uart_rx(0x0)
        # print("Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))
        # print(" unmolested: {}".format(read_sensors))
        hxt.examine_whois_reply(read_sensors)

        # sys.exit(1)
        vsr_number = 0x91

        # hxt.uart_reset()  # Didn't work

        print(" ------ Scratch Registers ------")

        scratch1 = hxt.x10g_rdma.read(0x00008030, comment='Read Scratch Register 1')
        hxt.compare("Read Scratch Register 1", scratch1[0], 0x11111111)

        scratch2 = hxt.x10g_rdma.read(0x00008034, burst_len=1, comment='Read Scratch Register 2')
        hxt.compare("Read Scratch Register 2", scratch2[0], 0x22222222)

        scratch3 = hxt.x10g_rdma.read(0x00008038, burst_len=1, comment='Read Scratch Register 3')
        hxt.compare("Read Scratch Register 3", scratch3[0], 0x33333333)

        scratch4 = hxt.x10g_rdma.read(0x0000803C, burst_len=1, comment='Read Scratch Register 4')
        hxt.compare("Read Scratch Register 4", scratch4[0], 0x44444444)

        new_value = 0x87654321
        hxt.x10g_rdma.write(0x8030, new_value, burst_len=2, comment="Set Scratch Reg12 value")
        scratch1 = hxt.x10g_rdma.read(0x00008030, burst_len=1, comment='Read Scratch Register 2')
        hxt.compare("Write Scratch Register 1", scratch1[0], new_value)

        new_value = 0x4000003320000011
        hxt.x10g_rdma.write(0x8030, new_value, burst_len=2, comment="Set Scratch Reg12 value")
        scratch12 = hxt.x10g_rdma.read(0x00008030, burst_len=2, comment='Read Scratch Register 1 2')
        int_value = (scratch12[1] << 32) + scratch12[0]
        hxt.compare("Write Scratch Registers 1&2", int_value, new_value)

        new_value = 0x600005554000033322200001
        hxt.x10g_rdma.write(0x8030, new_value, burst_len=3, comment="Set Scratch Reg123 value")
        scratch123 = hxt.x10g_rdma.read(0x00008030, burst_len=3, comment='Read Scratch Register 1 2 3')
        int_value = (scratch123[2] << 64) + (scratch123[1] << 32) + scratch123[0]
        hxt.compare("Write Scratch Registers 1-3", int_value, new_value)

        new_value = 0x81657777666600054444000322220001
        hxt.x10g_rdma.write(0x8030, new_value, burst_len=4, comment="Set Scratch Reg1234 value")
        scratch1234 = hxt.x10g_rdma.read(0x00008030, burst_len=4, comment='Read Scratch Register 1 2 3 4')
        int_value = (scratch1234[3] << 96) + (scratch1234[2] << 64) + (scratch1234[1] << 32) + scratch1234[0]
        hxt.compare("Write Scratch Registers 1-4", int_value, new_value)

        print(" ------ Environmental Data ------")
        # Request and receive environmental data #
        the_start = time.time()
        print(" ambient:          humidity:         asic1:             asic2:          adc: ")
        for index in range(0x90, 0x96):
            # print("Calling uart_tx([0x{0:X}, 0x52])".format(index), flush=True)
            hxt.x10g_rdma.uart_tx([index, 0x52])
            hxt.await_uart_ready()
            read_sensors = hxt.x10g_rdma.uart_rx(0x0)
            # print("Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)), flush=True)
            # Display the environmentals values
            hxt.display_environs(read_sensors)

        the_end = time.time()
        print("Entire loop took: {}".format(the_end - the_start))

        # Test writing and reading repeatedly to same register with incremental values
        hxt.hammer_register()

    except (socket.error, struct.error) as e:
        print(" *** Unexpected exception: {} ***".format(e))


        # # (address_high, address_low) = (0x30, 0x33)
        # # (value_high, value_low) = (0x30, 0x31)
        # # print("Write S1 (High) (register 003), values: {0:X}, {1:X}".format(value_high, value_low))
        # # hxt.set_vsr_register_value(vsr_number, address_high, address_low, value_high, value_low)
        # # time.sleep(0.25)


        # # Readout S1 (High) (register 003)
        # vsr_number = 0x90
        # print("Readout S1 (High) (register 003)")
        # (address_high, address_low) = (0x30, 0x33)
        # hxt.get_vsr_register_value(vsr_number, address_high, address_low)

        # # Readout S1_SPH (register 004)
        # vsr_number = 0x90
        # print("Readout S1_SPH (register 004)")
        # (address_high, address_low) = (0x30, 0x34)
        # hxt.get_vsr_register_value(vsr_number, address_high, address_low)

        # # Readout SPH_S2 (register 005)
        # vsr_number = 0x90
        # print("Readout SPH_S2 (register 005)")
        # (address_high, address_low) = (0x30, 0x35)
        # hxt.get_vsr_register_value(vsr_number, address_high, address_low)

    # uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done = hxt.x10g_rdma.read_uart_status()
    # print("      UART: {1:08X} tx_buff_full: {2:0X} tx_buff_empty: {3:0X} rx_buff_full: {4:0X} rx_buff_empty: {5:0X} rx_pkt_done: {6:0X}".format(
    #     0, uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done))

    # SCRATCH REGISTERS #

    # for index in range(100):
    #     # hxt.x10g_rdma.write(0x8030, 0x81657777666600054444000322220001, burst_len=4, comment="New Scratch Register1234 value")
    #     # scratch1234 = hxt.x10g_rdma.read(0x00008030, burst_len=4, comment='Read Scratch Register 1, 2, 3, 4')
    #     hxt.x10g_rdma.write(0x8030, 0x10203040, burst_len=1, comment="New Scratch Register1 value")
    #     scratch0 = hxt.x10g_rdma.read(0x00008030, burst_len=1, comment='Read Scratch Register 1')
    #     # print("Reg1: {0:08X}".format(scratch0))
    #     hxt.x10g_rdma.write(0x8034, 0x71625344, burst_len=1, comment="New Scratch Register2 value")
    #     scratch1 = hxt.x10g_rdma.read(0x00008034, burst_len=1, comment='Read Scratch Register 2')
    #     # print("Reg2: {0:08X}".format(scratch1))
    #     hxt.x10g_rdma.write(0x8038, 0xBEEFBEEF, burst_len=1, comment="New Scratch Register3 value")
    #     scratch2 = hxt.x10g_rdma.read(0x00008038, burst_len=1, comment='Read Scratch Register 3')
    #     # print("Reg3: {0:08X}".format(scratch2))
    #     hxt.x10g_rdma.write(0x803C, 0xDEADDEAD, burst_len=1, comment="New Scratch Register4 value")
    #     scratch3 = hxt.x10g_rdma.read(0x0000803C, burst_len=1, comment='Read Scratch Register 4')
    #     print("{4:000} Scratch: 0x{0:08X}{1:08X}{2:08X}{3:08X}".format(scratch3[0], scratch2[0], scratch1[0], scratch0[0], index))

    hxt.disconnect()
