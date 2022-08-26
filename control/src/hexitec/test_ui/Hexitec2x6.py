"""
Hexitec2x6: Exercises UDP control plane.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

import sys
from RdmaUDP import RdmaUDP
from ast import literal_eval
import time  # DEBUGGING only

# TEMPORARY: Global variables to support tickle translation
deassert_all = 0x0
uart_status_offset = 0x10
uart_rx_ctrl_offset = 0x14
uart_tx_ctrl_offset = 0xC
tx_fill_strb_mask = 0x2
tx_buff_strb_mask = 0x4
tx_data_mask = 0xFF00
vsr_start_char = 0x23
vsr_end_char = 0x0D
#
assert_bit = 0x1
rx_buff_strb_mask = 0x2
rx_buff_empty_mask = 0x8
rx_buff_level_mask = 0xFF00
rx_buff_data_mask = 0xFF0000

class Hexitec2x6():
    """
    Hexitec 2x6 class.

    Test we can access scratch registers in the KinteX FPGA.
    """

    def __init__(self, esdg_lab=False, debug=False):
        """."""
        self.debug = debug
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
                                 9000, 2, self.debug)
        self.x10g_rdma.setDebug(self.debug)
        self.x10g_rdma.ack = False  # True
        return self.x10g_rdma.error_OK

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
        self.x10g_rdma.write(0x8030, 0x12345678, "New Scratch Register1 value")
        self.x10g_rdma.write(0x8034, 0x9ABCDEF1, "New Scratch Register2 value")
        self.x10g_rdma.write(0x8038, 0xAAAAAAAA, "New Scratch Register3 value")
        self.x10g_rdma.write(0x803C, 0x60054003, "New Scratch Register4 value")

    def read_fpga_dna_registers(self):
        """Read the three DNA registers."""
        fpga_dna0 = self.x10g_rdma.read(0x0000800C, 'Read FPGA DNA part 1')
        fpga_dna1 = self.x10g_rdma.read(0x00008010, 'Read FPGA DNA part 2')
        fpga_dna2 = self.x10g_rdma.read(0x00008014, 'Read FPGA DNA part 3')
        print("FPGA DNA: 0x{0:08X} {1:08X} {2:08X}".format(fpga_dna2, fpga_dna1, fpga_dna0))

    def uart_rx(self, uart_address):
        """Replicating functionality of the tickle function: as_uart_rx."""
        debug = False    # True
        uart_status_addr = uart_address + uart_status_offset
        uart_rx_ctrl_addr = uart_address + uart_rx_ctrl_offset
        read_value = self.x10g_rdma.read(uart_status_addr, burst_len=1, comment='Read UART Buffer Status (0)')
        buff_level = (read_value[0] & rx_buff_level_mask) >> 8
        rx_d = (read_value[0] & rx_buff_data_mask) >> 16
        if debug:
            print(" init_buff_status: {0} (0x{1:08X})".format(read_value[0], read_value[0]))
            print(" buff_level: {0} rx_d: {1} (0x{2:X}) [IGNORED - Like tickle script]".format(buff_level, rx_d, rx_d))
        rx_status_masked = (read_value[0] & rx_buff_empty_mask)
        rx_has_data_flag = not rx_status_masked
        rx_data = []
        while (rx_has_data_flag):
            self.x10g_rdma.write(uart_rx_ctrl_addr, rx_buff_strb_mask, burst_len=1, comment="Write RX Buffer Strobe")
            read_value = self.x10g_rdma.read(uart_rx_ctrl_addr, burst_len=1, comment='Read (back) UART RX Status Reg (0)')
            # print(" (strb)  uart_rx_ctrl: {0} (0x{1:08X})".format(read_value[0], read_value[0]))
            self.x10g_rdma.write(uart_rx_ctrl_addr, deassert_all, burst_len=1, comment="Write RX Deassert All")
            read_value = self.x10g_rdma.read(uart_rx_ctrl_addr, burst_len=1, comment='Read (back) UART RX Status Reg (1)')
            # print(" (deass) uart_rx_ctrl: {0} (0x{1:08X})".format(read_value[0], read_value[0]))
            buffer_status = self.x10g_rdma.read(uart_status_addr, burst_len=1, comment='Read UART Buffer status (1)')
            buff_level = (buffer_status[0] & rx_buff_level_mask) >> 8
            uart_status = self.x10g_rdma.read(uart_status_addr, burst_len=1, comment='Read UART Buffer status (2)')
            rx_d = (uart_status[0] & rx_buff_data_mask) >> 16
            if debug:
                print(" buffer_status: {0} (0x{1:08X})".format(buffer_status[0], buffer_status[0]))
                print(" buff_level: {0} rx_d: {1} (0x{2:X})".format(buff_level, rx_d, rx_d))
            rx_data.append(rx_d)
            read_value = self.x10g_rdma.read(uart_status_addr, burst_len=1, comment='Read UART Buffer status (3)')
            rx_has_data_flag = not (read_value[0] & rx_buff_empty_mask)
        return rx_data

    def uart_tx(self, vsr_addr, vsr_cmd, vsr_data="", uart_addr=0x0):
        """Replicating functionality of the tickle function: as_uart_tx."""
        debug = False    # True
        uart_tx_ctrl_addr = uart_addr + uart_tx_ctrl_offset
        uart_status_addr = uart_addr + uart_status_offset
        # uart_rx_ctrl_addr = uart_addr + uart_rx_ctrl_offset   # Unused

        vsr_seq = [vsr_start_char, vsr_addr, vsr_cmd]
        if vsr_data != "":
            for d in vsr_data:
                vsr_seq.append(d)
        vsr_seq.append(vsr_end_char)
        if debug:
            print("... sending: {}".format(' '.join("0x{0:02X}".format(x) for x in vsr_seq)))
        for b in vsr_seq:
            self.x10g_rdma.write(uart_tx_ctrl_addr, b << 8, burst_len=1, comment="Write '{0:X}' to TX Buffer".format(b))
            read_tx_value = self.x10g_rdma.read(uart_tx_ctrl_addr, burst_len=1, comment="Read TX Buffer")

            read_tx_value = read_tx_value[0]
            if debug:
                # print(" * write 0x{0:02X} [ ( [ {1} & 0x{2:04X} ) | 0x{3:02}]".format(uart_tx_ctrl_addr, read_tx_value, tx_data_mask, tx_fill_strb_mask))
                print(" TX buffer contain: {0} (0x{1:02X})".format(read_tx_value, read_tx_value))
            write_value = ((read_tx_value & tx_data_mask) | tx_fill_strb_mask)

            self.x10g_rdma.write(uart_tx_ctrl_addr, write_value, burst_len=1, comment="Write '{0:X}' to TX Buffer".format(write_value))
            self.x10g_rdma.write(uart_tx_ctrl_addr, b << 8, burst_len=1, comment="Write '{0:X}' to TX Buffer (Again)".format(b))

            self.x10g_rdma.write(uart_tx_ctrl_addr, tx_buff_strb_mask, burst_len=1, comment="Write TX Buffer Strobe")
            self.x10g_rdma.write(uart_tx_ctrl_addr, deassert_all, burst_len=1, comment="Write TX Deassert All")

            self.x10g_rdma.read(uart_tx_ctrl_addr, burst_len=1, comment="Read TX Buffer")

        self.x10g_rdma.write(uart_tx_ctrl_addr, tx_buff_strb_mask, burst_len=1, comment="Write TX Buffer Strobe")
        # Redundant: ?
        # self.x10g_rdma.write(uart_tx_ctrl_addr, deassert_all, burst_len=1, comment="Write TX Deassert All")

    def disconnect(self):
        """."""
        self.x10g_rdma.close()

if __name__ == '__main__':  # pragma: no cover
    esdg_lab = literal_eval(sys.argv[1])
    debug = literal_eval(sys.argv[2])
    hxt = Hexitec2x6(esdg_lab=esdg_lab, debug=debug)
    hxt.connect()
    # hxt.read_scratch_registers()

    # Testing out translating tickle script into Python:
    print("Calling as_uart_tx(0xFF, 0xF7, \"\", 0x0)")
    tx = hxt.uart_tx(0xFF, 0xF7, "", 0x0)
    time.sleep(0.25)
    rx = hxt.uart_rx(0x0)
    print("Received from UART: {}".format(' '.join("0x{0:02X}".format(x) for x in rx)))

    # # hxt.read_fpga_dna_registers()

    # hxt.x10g_rdma.write(0x8030, 0x20000001, burst_len=1, comment="New Scratch Register1 value")
    # hxt.x10g_rdma.write(0x8030, 0x4000003320000011, burst_len=2, comment="New Scratch Register12 value")
    # hxt.x10g_rdma.write(0x8030, 0x600005554000033322200001, burst_len=3, comment="New Scratch Register123 value")
    # hxt.x10g_rdma.write(0x8030, 0x81657777666600054444000322220001, burst_len=4, comment="New Scratch Register1234 value")

    # scratch1 = hxt.x10g_rdma.read(0x00008030, comment='Read Scratch Register 1')
    # print("Reg   1, raw: {}".format(scratch1))
    # scratch12 = hxt.x10g_rdma.read(0x00008030, burst_len=2, comment='Read Scratch Register 1, 2')
    # print("Reg  12, raw: {}".format(scratch12))
    # scratch123 = hxt.x10g_rdma.read(0x00008030, burst_len=3, comment='Read Scratch Register 1, 2, 3')
    # print("Reg 123, raw: {}".format(scratch123))
    # scratch1234 = hxt.x10g_rdma.read(0x00008030, burst_len=4, comment='Read Scratch Register 1, 2, 3, 4')
    # print("Reg1234, raw: {}".format(scratch1234))

    # for index in range(100):
    #     print(index)
    #     hxt.x10g_rdma.write(0x8030, 0x81657777666600054444000322220001, burst_len=4, comment="New Scratch Register1234 value")
    #     scratch1234 = hxt.x10g_rdma.read(0x00008030, burst_len=4, comment='Read Scratch Register 1, 2, 3, 4')

    #     hxt.x10g_rdma.write(0x8030, 0x10203040, "New Scratch Register1 value")
    #     scratch0 = hxt.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
    #     # print("Reg1: {0:08X}".format(scratch0))
    #     hxt.x10g_rdma.write(0x8034, 0x71625344, "New Scratch Register2 value")
    #     scratch1 = hxt.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
    #     # print("Reg2: {0:08X}".format(scratch1))
    #     hxt.x10g_rdma.write(0x8038, 0xBEEFBEEF, "New Scratch Register3 value")
    #     scratch2 = hxt.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
    #     # print("Reg3: {0:08X}".format(scratch2))
    #     hxt.x10g_rdma.write(0x803C, 0xDEADDEAD, "New Scratch Register4 value")
    #     scratch3 = hxt.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
    #     print("{4:000} Scratch: 0x{0:08X}{1:08X}{2:08X}{3:08X}".format(scratch3, scratch2, scratch1, scratch0, index))
    #     break
    #     # # This matches writes made by rdma.py:
    #     # hxt.x10g_rdma.write(0x8030, 0xBAB00EFE, "New Scratch Register1 value")
    #     # scratch0 = hxt.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
    #     # print("Reg1: {0:08X}".format(scratch0))
    #     # hxt.x10g_rdma.write(0x8034, 0x23232323, "New Scratch Register2 value")
    #     # scratch1 = hxt.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
    #     # print("Reg2: {0:08X}".format(scratch1))
    #     # hxt.x10g_rdma.write(0x8038, 0x45454545, "New Scratch Register3 value")
    #     # scratch2 = hxt.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
    #     # print("Reg3: {0:08X}".format(scratch2))
    #     # hxt.x10g_rdma.write(0x803C, 0x67676767, "New Scratch Register4 value")
    #     # scratch3 = hxt.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
    #     # print("Scratch: 0x{0:08X}{1:08X}{2:08X}{3:08X}".format(scratch3, scratch2, scratch1, scratch0))
    #     # break

    hxt.disconnect()
