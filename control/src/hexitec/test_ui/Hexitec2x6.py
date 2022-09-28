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

    READ_REG_VALUE = 0x41
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
        scratch0 = self.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
        # # print(scratch0)
        # scratch1 = self.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
        # # print(scratch1)
        # scratch2 = self.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
        # scratch3 = self.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
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
        fpga_dna0 = self.x10g_rdma.read(0x0000800C, 'Read FPGA DNA part 1')
        fpga_dna1 = self.x10g_rdma.read(0x00008010, 'Read FPGA DNA part 2')
        fpga_dna2 = self.x10g_rdma.read(0x00008014, 'Read FPGA DNA part 3')
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

    def displ_envs(self, read_sensors):
        """Display environmental data in human readable format."""
        read_sensors = read_sensors[1:]  # Omit start of sequence character, matching existing 2x2 source code formatting
        sensors_values = "{}".format(''.join([chr(x) for x in read_sensors]))   # Turn list of integers into ASCII string
        # print(" ASCII string: {}".format(sensors_values))
        print(" ambient: ({0}) {1:3.3f} C. humidity: ({2}) {3:3.3f} %. asic1: ({4}) {5:3.3f} C. asic2: ({6}) {7:3.3f} C. adc: ({8}) {9:3.3f} C.".format(
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
        print("{0:05} UART: {1:08X} tx_buff_full: {2:0X} tx_buff_empty: {3:0X} rx_buff_full: {4:0X} rx_buff_empty: {5:0X} rx_pkt_done: {6:0X}".format(
            counter, uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done))

###
    def convert_list_to_string(self, int_list):
        """Convert list of integer into ASCII string.

        I.e. integer_list = [42, 144, 70, 70, 13], returns '*\x90FF\r'
        """
        return "{}".format(''.join([chr(x) for x in int_list]))

    def send_cmd(self, cmd):
        """Send a command string to the microcontroller."""
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
        print("R: {}. {}".format(response, counter))
        return response
        # return self.x10g_rdma.uart_rx(0x0)

    def debug_register(self, msb, lsb):  # pragma: no cover
        """Debug function: Display contents of register."""
        self.send_cmd([0x23, self.VSR_ADDRESS[1], self.READ_REG_VALUE,
                       msb, lsb, 0x0D])
        vsr2 = self.read_response()
        # reply = self.convert_list_to_string(self.read_response()[1:])
        # print(" VSR2,reply: {}".format(reply))
        # vsr2 = reply.strip("\r")[1:]
        time.sleep(0.25)
        self.send_cmd([0x23, self.VSR_ADDRESS[0], self.READ_REG_VALUE,
                       msb, lsb, 0x0D])
        # reply = self.convert_list_to_string(self.read_response()[1:])
        # vsr1 = reply.strip("\r")[1:]
        vsr1 = self.read_response()
        # return (vsr2, vsr1)
        # print("vsr2: {}".format(vsr2))
        # print("vsr1: {}".format(vsr1))
        vsr2 = vsr2[2:-1]
        vsr1 = vsr1[2:-1]
        # print("vsr2: {}".format(vsr2))
        # print("vsr1: {}".format(vsr1))
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

    def module_mask(self, module):
        return ((1 << (module -1)) | (1 << (module + 8 -1)))
    def negative_module_mask(self, module):
        return ~(1 << (module - 1)) | (1 << (module + 8 - 1))

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
        vsr_ctrl_addr =  Hexitec2x6.vsr_ctrl_offset
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
        vsr_ctrl_addr =  Hexitec2x6.vsr_ctrl_offset
        # STEP 1: vsr_ctrl disable $::vsr_target_idx
        mod_mask = self.negative_module_mask(vsr_number) #1)
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
        vsr_ctrl_addr =  Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | 0x3F # Switching all six VSRs on, i.e. set 6 bits on
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all VSRs on")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("All VSRs enabled")

    def enable_all_hv(self):
        """Switch all HVs on."""
        vsr_ctrl_addr =  Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | Hexitec2x6.hvs_bit_mask # Switching all six HVs on
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all HVs on")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("All HVs on")

    def enable_hv(self, hv_number):
        """Switch on a single VSR's power."""
        vsr_ctrl_addr =  Hexitec2x6.vsr_ctrl_offset
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
        vsr_ctrl_addr =  Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value & 0x3F # Switching all six HVs off
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all HVs off")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.DISABLE_VSR])
        print("All HVs off")

    def disable_all_vsrs(self):
        """Switch all VSRs off."""
        vsr_ctrl_addr =  Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value & Hexitec2x6.hvs_bit_mask # Switching all six VSRs off
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all VSRs off")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.DISABLE_VSR])
        print("All VSRs disabled")

    def power_status(self):
        """Reads out the status register to check what is switched on and off."""
        read_value = self.x10g_rdma.read(Hexitec2x6.vsr_ctrl_offset, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        print(" *** Register status: 0x{0:08X}".format(read_value))

    def set_vsr_row_s1_clock(self, vsr_address):
        """Set row s1 clock."""
        self.send_cmd([vsr_address, self.SEND_REG_BURST, 0x30, 0x32, 0x30, 0x32])
        read_sensors = self.read_response()
        print("Reg 0x02, Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))
        self.send_cmd([vsr_address, self.SEND_REG_BURST, 0x30, 0x33, 0x30, 0x34])
        read_sensors = self.read_response()
        print("Reg 0x03, Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))

    def get_vsr_row_s1_clock(self, vsr_number):
        """Get row s1 clock."""
        self.send_cmd([vsr_number, self.READ_REG_VALUE, 0x30, 0x32])
        read_sensors = self.read_response()
        print("Reg 0x02, Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))
        self.send_cmd([vsr_number, self.READ_REG_VALUE, 0x30, 0x33])
        read_sensors = self.read_response()
        print("Reg 0x03, Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))

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
    # hxt.read_scratch_registers()

    try:
        vsr_number = 0x90
        hxt.set_vsr_row_s1_clock(vsr_number)
        hxt.get_vsr_row_s1_clock(vsr_number)

        # # Enable VSR(s)..
        # hxt.enable_vsr_or_hv(1, Hexitec2x6.enable_vsrs_mask)  # Switches a single VSR on
        # hxt.enable_vsr_or_hv(1, Hexitec2x6.hvs_bit_mask)  # Switches a single HV on
        # hxt.enable_vsr_or_hv(2, Hexitec2x6.enable_vsrs_mask)

        # # hxt.disable_all_hv()    # Working
        # hxt.disable_all_vsrs()  # Working
        # # hxt.disable_all_hv()
        # hxt.power_status()
        # hxt.enable_vsr(1)  # Switches a single VSR on
        # hxt.enable_vsr(2)
        # hxt.power_status()
        # hxt.power_status()
        # hxt.disable_vsr(1)
        # # hxt.enable_all_hv()
        # hxt.enable_hv(1)
        # hxt.power_status()
        # hxt.power_status()
        # hxt.enable_vsr(2)
        # hxt.power_status()


        # hxt.x10g_rdma.uart_tx([0x92, 0xE3])
        # print("third VSR enabled")
        # hxt.dump_all_registers()
        # # WHOIS COMMAND #

        # # as_uart_tx 0xFF 0xF7 "" 0x0  0
        # print("Calling uart_tx(0xFF, 0xF7)")
        # hxt.x10g_rdma.uart_tx([0xFF, 0xF7])
        # # hxt.await_uart_ready()    # Why doesn't it work with whois?
        # time.sleep(0.25)
        # read_sensors = hxt.x10g_rdma.uart_rx(0x0)
        # print("Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))

        # SCRATCH REGISTER #

        # # Scratch Registers; Writing, Reading
        # hxt.x10g_rdma.write(0x8030, 0x10203040, burst_len=1, comment="Set Scratch Reg1 value")
        # scratch0 = hxt.x10g_rdma.read(0x00008030, comment='Read Scratch Register 1')
        # print("Reg   1: {0:08X}".format(scratch0[0]))

        # hxt.x10g_rdma.write(0x8030, 0x4000003320000011, burst_len=2, comment="Set Scratch Reg12 value")
        # scratch12 = hxt.x10g_rdma.read(0x00008030, burst_len=2, comment='Read Scratch Register 1 2')
        # print("Reg  12: {}".format(', '.join("{0:8X}".format(x) for x in scratch12)))

        # hxt.x10g_rdma.write(0x8030, 0x600005554000033322200001, burst_len=3, comment="Set Scratch Reg123 value")
        # scratch123 = hxt.x10g_rdma.read(0x00008030, burst_len=3, comment='Read Scratch Register 1 2 3')
        # print("Reg 123: {}".format(', '.join("{0:8X}".format(x) for x in scratch123)))

        # hxt.x10g_rdma.write(0x8030, 0x81657777666600054444000322220001, burst_len=4, comment="Set Scratch Reg1234 value")
        # scratch1234 = hxt.x10g_rdma.read(0x00008030, burst_len=4, comment='Read Scratch Register 1 2 3 4')
        # print("Reg1234: {}".format(', '.join("{0:8X}".format(x) for x in scratch1234)))
        pass
    except (socket.error, struct.error) as e:
        print(" *** Scratch register error: {} ***".format(e))

    # uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done = hxt.x10g_rdma.read_uart_status()
    # print("      UART: {1:08X} tx_buff_full: {2:0X} tx_buff_empty: {3:0X} rx_buff_full: {4:0X} rx_buff_empty: {5:0X} rx_pkt_done: {6:0X}".format(
    #     0, uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done))

    # # Request and receive environmental data #
    # print("Calling uart_tx(0x90, 0x52, \"\", 0x0)")
    # hxt.x10g_rdma.uart_tx([0x90, 0x52])
    # hxt.await_uart_ready()
    # read_sensors = hxt.x10g_rdma.uart_rx(0x0)
    # print("Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))
    # # Display the environmentals values
    # read_sensors = read_sensors[1:]     # Omit start of sequence character, matching existing 2x2 source code formatting
    # sensors_values = "{}".format(''.join([chr(x) for x in read_sensors]))   # Turn list of integers into ASCII string
    # print(" ASCII string: {}".format(sensors_values))
    # ambient_hex = sensors_values[1:5]
    # humidity_hex = sensors_values[5:9]
    # asic1_hex = sensors_values[9:13]
    # asic2_hex = sensors_values[13:17]
    # adc_hex = sensors_values[17:21]
    # print(" * ambient_hex:  {} -> {} Celsius".format(sensors_values[1:5], hxt.get_ambient_temperature(sensors_values[1:5])))
    # print(" * humidity_hex: {} -> {}".format(sensors_values[5:9], hxt.get_humidity(sensors_values[5:9])))
    # print(" * asic1_hex:    {} -> {} Celsius".format(sensors_values[9:13], hxt.get_asic_temperature(sensors_values[9:13])))
    # print(" * asic2_hex:    {} -> {} Celsius".format(sensors_values[13:17], hxt.get_asic_temperature(sensors_values[13:17])))
    # print(" * adc_hex:      {} -> {} Celsius".format(sensors_values[17:21], hxt.get_adc_temperature(sensors_values[17:21])))

    # try:
    #     # Request and receive environmental data #
    #     the_start = time.time()
    #     for index in range(0x90, 0x96):
    #         # print("Calling uart_tx([0x{0:X}, 0x52])".format(index), flush=True)
    #         hxt.x10g_rdma.uart_tx([index, 0x52])
    #         hxt.await_uart_ready()
    #         read_sensors = hxt.x10g_rdma.uart_rx(0x0)
    #         # print("Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)), flush=True)
    #         # Display the environmentals values
    #         hxt.displ_envs(read_sensors)

    #     the_end = time.time()
    #     print("Entire loop took: {}".format(the_end - the_start))
    #     pass
    # except (socket.error, struct.error) as e:
    #     print(" *** Environmental data error: {} ***".format(e))

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
