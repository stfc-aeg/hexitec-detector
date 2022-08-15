"""
Hexitec2x6: Exercises UDP control plane.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

from RdmaUDP import RdmaUDP


class Hexitec2x6():
    """
    Hexitec 2x6 class.

    Test we can access scratch registers in the KinteX FPGA.
    """

    def __init__(self, debug=False):
        """."""
        self.debug = debug
        # Control IP addresses
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
                                 9000, 3, self.debug)
        self.x10g_rdma.setDebug(self.debug)
        self.x10g_rdma.ack = False  # True
        return self.x10g_rdma.error_OK

    def read_scratch_registers(self):
        """Read scratch registers."""
        scratch0 = self.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
        # print(scratch0)
        scratch1 = self.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
        # print(scratch1)
        scratch2 = self.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
        scratch3 = self.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
        print("Scratch: 0x{0:08x}{1:08x}{2:08x}{3:08X}".format(scratch3, scratch2, scratch1, scratch0))

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
        deassert_all = 0x0
        assert_bit = 0x1
        uart_status_offset = 0x10
        uart_rx_ctrl_offset = 0x14
        rx_buff_strb_mask = 0x2
        rx_buff_empty_mask = 0x8
        rx_buff_level_mask = 0xFF00
        rx_buff_data_mask = 0xFF0000
##
        uart_status_addr = uart_address + uart_status_offset
        uart_rx_ctrl_addr = uart_address + uart_rx_ctrl_offset
        print("Read targeting address: {}".format(uart_status_addr))
        read_value = self.x10g_rdma.read(uart_status_addr, 'Read UART Buffer Status (0)')  # read_axi $uart_status_addr 1
        rx_status_masked = (read_value & rx_buff_empty_mask)
        rx_has_data_flag = not rx_status_masked
        print("read_value: {0:08X} ({1:08X} & {2}) = {3}".format(read_value, read_value, rx_buff_empty_mask, rx_has_data_flag))
        # set rx_has_data_flag [ expr { ! ([ read_axi $uart_status_addr 1 ]  & $::rx_buff_empty_mask) } ]

        rx_data = []
        while (rx_has_data_flag):
            print("-=-=-=-")
            buffer_status = self.x10g_rdma.read(uart_status_addr, 'Read UART Buffer status (1)')
            buff_level = (buffer_status & rx_buff_level_mask) >> 8
            print("buff_level: ", buff_level)
            self.x10g_rdma.write(uart_rx_ctrl_addr, rx_buff_strb_mask, "Write RX Buffer Strobe")
            self.x10g_rdma.write(uart_rx_ctrl_addr, deassert_all, "Write RX Deassert All")
            # print("Write {0:08X} {1:X}".format(uart_rx_ctrl_addr, rx_buff_strb_mask))
            # print("Write {0:08X} {1:X}".format(uart_rx_ctrl_addr, deassert_all))
            uart_status = self.x10g_rdma.read(uart_status_addr, 'Read UART Buffer status (2)')
            rx_d = (uart_status & rx_buff_data_mask) >> 16
            print(" rx_d: {0} ({1:02X})".format(rx_d, rx_d))
            rx_data.append(rx_d)
            read_value = self.x10g_rdma.read(uart_status_addr, 'Read UART Buffer status (3)')
            rx_has_data_flag = not (read_value & rx_buff_empty_mask)
        return rx_data

        # while { $rx_has_data_flag } {
        #     # set buff_level [ expr { ( [ read_axi $uart_status_addr 1 ] & $::rx_buff_level_mask ) >> 8 } ]
        #     # write_axi $uart_rx_ctrl_addr $::rx_buff_strb_mask
        #     # write_axi $uart_rx_ctrl_addr $::deassert_all
        #     # set rx_d [ expr { ( [ read_axi $uart_status_addr 1 ] & $::rx_buff_data_mask ) >> 16 } ]
        #     # lappend rx_data [ format %02X $rx_d ]
        #     # set rx_has_data_flag [ expr { ! ([ read_axi $uart_status_addr 1 ]  & $::rx_buff_empty_mask) } ]
        # }

    def uart_tx(self, vsr_addr, vsr_cmd, vsr_data="", uart_addr=0x0):
        """Replicating functionality of the tickle function: as_uart_tx."""
        deassert_all = 0x0
        uart_status_offset = 0x10
        uart_rx_ctrl_offset = 0x14
        uart_tx_ctrl_offset = 0xC
        tx_fill_strb_mask = 0x2
        tx_buff_strb_mask = 0x4
        tx_data_mask = 0xFF00
        vsr_start_char = 0x23
        vsr_end_char = 0x0D
        uart_tx_ctrl_addr = uart_addr + uart_tx_ctrl_offset
        uart_status_addr = uart_addr + uart_status_offset
        uart_rx_ctrl_addr = uart_addr + uart_rx_ctrl_offset

# TODO: Continue translating this:
# proc as_uart_tx { vsr_addr vsr_cmd { vsr_data "" } { uart_addr 0x0 } { lines "" } { hw_axi_idx 0 } } {
#     # puts " uart_tx_ctrl_addr = $uart_addr + $::uart_tx_ctrl_offset" # 0x0C
#     # puts " uart_status_addr  = $uart_addr + $::uart_status_offset"  # 0x10
#     # puts " uart_rx_ctrl_addr = $uart_addr + $::uart_rx_ctrl_offset" # 0x14
#     set uart_tx_ctrl_addr [ expr { $uart_addr + $::uart_tx_ctrl_offset } ]
#     set uart_status_addr  [ expr { $uart_addr + $::uart_status_offset } ]
#     set uart_rx_ctrl_addr [ expr { $uart_addr + $::uart_rx_ctrl_offset } ]

#     set vsr_seq $::vsr_start_char
#     lappend vsr_seq $vsr_addr
#     lappend vsr_seq $vsr_cmd
#     if { $vsr_data ne "" } {
#         foreach d $vsr_data {
#             lappend vsr_seq $d
#         }
#     }
#     lappend vsr_seq $::vsr_end_char
#     puts -nonewline "...sending: $vsr_seq"
#     foreach b $vsr_seq {
#         write_axi $uart_tx_ctrl_addr [ expr { $b << 8 } ]
#         write_axi $uart_tx_ctrl_addr [ expr { ( [ read_axi $uart_tx_ctrl_addr 1 ]  & $::tx_data_mask ) | $::tx_fill_strb_mask } ]
#         write_axi $uart_tx_ctrl_addr [ expr { $b << 8 } ]
#     }
#     write_axi $uart_tx_ctrl_addr $::tx_buff_strb_mask
#     write_axi $uart_tx_ctrl_addr $::deassert_all
#     # Wait for sequence to be transmitted via UART, and allow time for response
#     after $::uart_tx_delay
#     return $lines

# }

    def disconnect(self):
        """."""
        self.x10g_rdma.close()

# Testing functionality for Matt Robert 's scripting
def prod_list(bytes):
    """."""
    bytes_list = []
    for idx in range(len(bytes)):
        bytes_list.append(bytes[idx])
    return bytes_list

def display_register_information(name, read_bytes):
    r"""Take a bytes object, display its name, length, address and value.

    I.e. b"\x02\x00\x00\x01\x04\x00\x02\x00\x00b\x00\x00'\xb8`\xb4"
    Contain address: 0x00020004, Value: 0x00006200, Length: 16
    """
    bytes_list = prod_list(read_bytes)
    print("Reg: {}, length: {}".format(name, len(read_bytes)))
    print("     address: 0x{0:02x}{1:02x}{2:02x}{3:02x}".format(bytes_list[7], bytes_list[6], bytes_list[5], bytes_list[4]))
    print("       Value: 0x{0:02x}{1:02x}{2:02x}{3:02x}".format(bytes_list[11], bytes_list[10], bytes_list[9], bytes_list[8]))


if __name__ == '__main__':  # pragma: no cover

    hxt = Hexitec2x6(False)
    hxt.connect()
    # hxt.read_scratch_registers()
    # Testing out translating tickle script into Python:
    # rx = hxt.uart_rx(0x0)
    # print("rx: ", rx)
    # hxt.read_scratch_registers()
    # hxt.write_scratch_registers()
    # hxt.read_scratch_registers()
    # # hxt.read_fpga_dna_registers()
    for index in range(100):
        print(index)
        hxt.x10g_rdma.write(0x8030, 0x10203040, "New Scratch Register1 value")
        scratch0 = hxt.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
        print("Reg1: {0:08X}".format(scratch0))
        hxt.x10g_rdma.write(0x8034, 0x71625344, "New Scratch Register2 value")
        scratch1 = hxt.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
        print("Reg2: {0:08X}".format(scratch1))
        hxt.x10g_rdma.write(0x8038, 0xBEEFBEEF, "New Scratch Register3 value")
        scratch2 = hxt.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
        print("Reg3: {0:08X}".format(scratch2))
        hxt.x10g_rdma.write(0x803C, 0xDEADDEAD, "New Scratch Register4 value")
        scratch3 = hxt.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
        print("Scratch: 0x{0:08X}{1:08X}{2:08X}{3:08X}".format(scratch3, scratch2, scratch1, scratch0))
        break
        # # This matches writes made by rdma.py:
        # hxt.x10g_rdma.write(0x8030, 0xBAB00EFE, "New Scratch Register1 value")
        # scratch0 = hxt.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
        # print("Reg1: {0:08X}".format(scratch0))
        # hxt.x10g_rdma.write(0x8034, 0x23232323, "New Scratch Register2 value")
        # scratch1 = hxt.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
        # print("Reg2: {0:08X}".format(scratch1))
        # hxt.x10g_rdma.write(0x8038, 0x45454545, "New Scratch Register3 value")
        # scratch2 = hxt.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
        # print("Reg3: {0:08X}".format(scratch2))
        # hxt.x10g_rdma.write(0x803C, 0x67676767, "New Scratch Register4 value")
        # scratch3 = hxt.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
        # print("Scratch: 0x{0:08X}{1:08X}{2:08X}{3:08X}".format(scratch3, scratch2, scratch1, scratch0))
        # break

    hxt.disconnect()
