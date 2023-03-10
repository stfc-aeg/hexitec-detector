"""
Rdma - UDP 10 G access.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

import socket
import struct
import time


# TEMPORARY: Global variables to support tickle translation
deassert_all = 0x0
#
uart_status_offset = 0x10
tx_buff_full_mask = 0x1
tx_buff_empty_mask = 0x2
rx_buff_full_mask = 0x4
rx_buff_empty_mask = 0x8
rx_pkt_done_mask = 0x10
rx_buff_level_mask = 0xFF00
rx_buff_data_mask = 0xFF0000
#
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
rx_buff_level_mask = 0xFF00
rx_buff_data_mask = 0xFF0000


class RdmaUDP(object):
    """Class for handling RDMA UDP transactions."""

    enable_vsrs_mask = 0x3F
    hvs_bit_mask = 0x3F00
    vsr_ctrl_offset = 0x18
    ENABLE_VSR = 0xE3
    DISABLE_VSR = 0xE2

    def __init__(self, local_ip='192.168.0.1', local_port=65535,
                 rdma_ip='192.168.0.2', rdma_port=65536,
                 UDPMTU=9000, UDPTimeout=5, debug=False, unique_cmd_no=False):
        """
        Establish UDP connection from (local_ip, local_port) to (rdma_ip, rdma_port).

        :param local_ip: PC IP address
        :param local_port: PC port
        :param rdma_ip: Camera IP address
        :param rdma_port: Camera port
        :param UDPMTU: UDP's Maximum Transmit Unit
        :param UDPTimeout: UDP timeout
        :param debug: Enable debugging
        """
        self.debug = debug
        if self.debug:   # pragma: no coverage
            print("RdmaUDP:")
            print("	Binding: ({}, {})".format(local_ip, local_port))
            print(" Send to: ({}, {})".format(rdma_ip, rdma_port))
            print(" UDPMTU: {}".format(UDPMTU))
            print("___________________________________________________________ ")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(UDPTimeout)
        self.error_OK = True

        try:
            self.socket.bind((local_ip, local_port))
        except (socket.error, OSError) as e:
            error_string = "  Error: '{}' ".format(e)
            error_string += "on TX Socket: {}:{}".format(local_ip, local_port)
            print(error_string)
            self.error_OK = False
            raise socket.error("Error: {}".format(e))

        self.rdma_ip = rdma_ip
        self.rdma_port = rdma_port
        self.UDPMTU = UDPMTU
        self.ack = False
        self.header_size = 8    # 8 bytes header size
        self.bytes_per_word = 4     # 32 bit word, therefore 4 bytes per word
        # Turn header's cmd_no into a packet counter?
        self.unique_cmd_no = unique_cmd_no
        if self.unique_cmd_no:  # pragma: no coverage
            self.cmd_no = -1
        else:
            self.cmd_no = 0

    def __del__(self):
        """Ensure rdma connection closed."""
        self.socket.close()

    def read(self, address, burst_len=1, comment=''):
        """
        Read data from the address.

        Send a read command to the established socket and read back the reply.
        The comment is for info and the other two arguments used to construct the command.
        :param address: The address of the register to update
        :param burst_len: Number of bytes to write
        :param comment: Info describing the transaction
        """
        burst_len = burst_len
        if self.unique_cmd_no:  # pragma: no coverage
            self.cmd_no = (self.cmd_no + 1) & 0xFF
        else:
            self.cmd_no = 0
        op_code = 1
        if self.debug:   # pragma: no coverage
            msg = "R. burst_len: {0:X} cmd_no: {1:0X} op_code: {2:0X}".format(
                    burst_len, self.cmd_no, op_code)
            print("{0} address: 0x{1:0X} comment: \"{2}\"".format(msg, address, comment))
        # H = burst len, B = cmd no, B = Op code, I = start address
        # H = unsigned short (2), B = unsigned char (1), I = signed int (4 Bytes)
        command = struct.pack('=HBBI', burst_len, self.cmd_no, op_code, address)
        data = (0, )
        # Send the single read command packet
        try:
            self.socket.sendto(command, (self.rdma_ip, self.rdma_port))
        except socket.error as e:
            msg = " *** Read (W) Error: {0}. burst_len: {1:X} cmd_no: ".format(e, burst_len)
            print("{0}{1:0X} op_code: {2:0X} address: 0x{3:0X} comment: \"{4}\" ***".format(
                msg, self.cmd_no, op_code, address, comment))
            time.sleep(0.5)
            raise socket.error(e)
        try:
            # Receive acknowledge packet
            response = self.socket.recv(self.UDPMTU)
            header_str = "HBBI"   # Equivalent length: 8
            payload_length = len(response) - self.header_size
            payload_length = payload_length // self.bytes_per_word
            packet_str = header_str + "I" * payload_length
            padding = (burst_len % 2)
            if payload_length != (burst_len + padding):
                raise struct.error("expected {}, received {} words!".format(
                    burst_len, payload_length))
            decoded = struct.unpack(packet_str, response)
            if padding:
                data = decoded[4:-padding]  # Omit burst_len, cmd_no, op_code, address and padding
            else:
                data = decoded[4:]  # Omit burst_len, cmd_no, op_code, address
            if self.ack:
                decoded_str = ' '.join("0x{0:X}".format(x) for x in decoded)
                print("R decoded: {0}. \"{1}\"".format(decoded_str, comment))
        except socket.error as e:
            raise socket.error(e)
        except struct.error as e:
            raise struct.error(e)
        return data

    def debug_var(self, variable):  # pragma: no coverage
        """Debug function that will print contents, type of argument."""
        return ("{} : {}".format(variable, type(variable)))

    def write(self, address, data, burst_len=1, comment=''):
        """
        Write data to the address.

        Send a write command to the established socket and read back the reply.
        The comment is for info and all other arguments used to construct the command.
        :param address: The address of the register to update
        :param data: The data to write to the register
        :param burst_len: Number of bytes to write
        :param comment: Info describing the transaction
        """
        burst_len = burst_len
        if self.unique_cmd_no:  # pragma: no coverage
            self.cmd_no = (self.cmd_no + 1) & 0xFF
        else:
            self.cmd_no = 0
        op_code = 0
        if self.debug:   # pragma: no coverage
            message = " W. burst_len: {0:X} cmd_no: {1:X} op_code: ".format(burst_len, self.cmd_no)
            print("{0}{1:X} address: 0x{2:X} data: {3:X} comment: \"{4}\"".format(message,
                  op_code, address, data, comment))
        # H = burst len, B = cmd no, B = Op code, I = address, I = data
        # H = unsigned short (2), B = unsigned char (1), I = signed int (4 Bytes)
        header_str = "HBBI"   # Equivalent length: 8
        packet_str = header_str + "I" * burst_len
        data = self.convert_to_list(data, burst_len)
        command = struct.pack(packet_str, burst_len, self.cmd_no, op_code, address, *data)
        # Send the single write command packet
        try:
            self.socket.sendto(command, (self.rdma_ip, self.rdma_port))
        except socket.error as e:
            err1 = " *** Write (W) Error: {0}. burst_len: {1:0X} ".format(e, burst_len)
            err2 = "cmd_no: {0:X} op_code: {1:0X} ".format(self.cmd_no, op_code)
            data_str = ' '.join("0x{0:X}".format(x) for x in data)
            err3 = "address: 0x{0:X} data: {1}. ".format(address, data_str)
            print("{0}{1}{2}Comment: \"{3}\" ***".format(err1, err2, err3, comment))
            raise socket.error(e)
        try:
            # Receive acknowledgement
            response = self.socket.recv(self.UDPMTU)
            header_str = "HBBI"   # Equivalent length: 8
            payload_length = len(response) - self.header_size
            payload_length = payload_length // self.bytes_per_word
            packet_str = header_str + "I" * payload_length
            decoded = struct.unpack(packet_str, response)
            if self.ack:
                decoded_str = ' '.join("0x{0:X}".format(x) for x in decoded)
                print('W decoded: {0}. \"{1}\" Length: {2}'.format(decoded_str, comment,
                                                                   len(response)))
            return decoded
        except socket.error as e:
            err1 = " *** Write (R) Error: {0}. burst_len: {1:0X} ".format(e, burst_len)
            err2 = "cmd_no: {0:X} op_code: {1:0X} ".format(self.cmd_no, op_code)
            data_str = ' '.join("0x{0:X}".format(x) for x in data)
            err3 = "address: 0x{0:X} data: {1}. ".format(address, data_str)
            print("{0}{1}{2}Comment: \"{3}\" ***".format(err1, err2, err3, comment))
            raise socket.error(e)
        except struct.error as e:
            print(" *** Write Ack Error: {} ***".format(e))
            raise struct.error("Write: bad reply: {}".format(e))

    def convert_to_list(self, data, burst_len):
        """
        Turn data into reverse ordered list of 32 bit words.

        For example, 0x81657777666600054444000322220001
        would become [22220001, 44440003, 66660005, 81657777]
        """
        data_array = []
        bit_mask = 0xFFFFFFFF
        bit_shifting = 0
        for loop in range(burst_len):
            data_array.append((data >> bit_shifting) & bit_mask)
            bit_shifting += 32
        return data_array

    def close(self):
        """Ensure rdma connection closed."""
        self.socket.close()

    def setDebug(self, enabled=True):   # pragma: no coverage
        """Set debugging."""
        self.debug = enabled

    def uart_rx(self, uart_address):
        """Receive all data available in the UART."""
        debug = False    # True
# #
#        uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done \
#            = hxt.x10g_rdma.read_uart_status()

#         # Check that UART buffer is empty (1 = empty, 0 = has data)
#         is_tx_buff_empty, is_rx_buff_empty = self.check_tx_rx_buffs_empty()
        # print(" uart_tx, rx_buff_empty: {} is_tx_buff_empty: {}, is_rx_buff_empty: {}".format(
        #     rx_buff_empty, is_tx_buff_empty, is_rx_buff_empty))
#         if is_rx_buff_empty == 0:
#             raise Exception("uart_rx: RX Buffer NOT empty!")
# #
        uart_status_addr = uart_address + uart_status_offset
        uart_rx_ctrl_addr = uart_address + uart_rx_ctrl_offset
        read_value = self.read(uart_status_addr, burst_len=1, comment='Read UART Buffer Status 0')
        buff_level = (read_value[0] & rx_buff_level_mask) >> 8
        rx_d = (read_value[0] & rx_buff_data_mask) >> 16
        if debug:   # pragma: no coverage
            print(" RX init_buff_status: {0} (0x{1:08X})".format(read_value[0], read_value[0]))
            print(" RX buff_level: {0} rx_d: {1} (0x{2:X}) [SKIP]".format(buff_level, rx_d, rx_d))
        rx_status_masked = (read_value[0] & rx_buff_empty_mask)
        rx_has_data_flag = not rx_status_masked
        rx_data = []
        while (rx_has_data_flag):
            self.write(uart_rx_ctrl_addr, rx_buff_strb_mask, burst_len=1,
                       comment="Write RX Buffer Strobe")
            read_value = self.read(uart_rx_ctrl_addr, burst_len=1,
                                   comment='Read (back) UART RX Status Reg (0)')
            self.write(uart_rx_ctrl_addr, deassert_all, burst_len=1,
                       comment="Wr RX Deassert All")
            read_value = self.read(uart_rx_ctrl_addr, burst_len=1,
                                   comment='Read (back) UART RX Status Reg (1)')
            buffer_status = self.read(uart_status_addr, burst_len=1,
                                      comment='Read UART Buffer status 1')
            buff_level = (buffer_status[0] & rx_buff_level_mask) >> 8
            uart_status = self.read(uart_status_addr, burst_len=1, comment='Rd UART Buff status 2')
            rx_d = (uart_status[0] & rx_buff_data_mask) >> 16
            if debug:   # pragma: no coverage
                print(" RX buff status: {0} ({1:08X})".format(buffer_status[0], buffer_status[0]))
                print(" RX buff level: {0} rx_d: {1} ({2:X})".format(buff_level, rx_d, rx_d))
            rx_data.append(rx_d)
            read_value = self.read(uart_status_addr, burst_len=1, comment='Rd UART Buff status 3')
            rx_has_data_flag = not (read_value[0] & rx_buff_empty_mask)
        # print("(RdmaUDP) UART RX'd: {}".format(' '.join("0x{0:02X}".format(x) for x in rx_data)))
        return rx_data

    def reset_uart_rx_buffer(self):  # pragma: no coverage
        """Clear all RX data from the UART."""
        debug = False   # True
        uart_status_addr = uart_status_offset
        uart_rx_ctrl_addr = uart_rx_ctrl_offset
        read_value = self.read(uart_status_addr, burst_len=1, comment='Read UART Buffer Status 0')
        buff_level = (read_value[0] & rx_buff_level_mask) >> 8
        rx_d = (read_value[0] & rx_buff_data_mask) >> 16
        if debug:   # pragma: no coverage
            print(" RX init_buff_status: {0} (0x{1:08X})".format(read_value[0], read_value[0]))
            print(" RX buff_level: {0} rx_d: {1} (0x{2:X}) [SKIP]".format(buff_level, rx_d, rx_d))
        rx_status_masked = (read_value[0] & rx_buff_empty_mask)
        rx_has_data_flag = not rx_status_masked
        rx_data = []
        while (rx_has_data_flag):
            self.write(uart_rx_ctrl_addr, rx_buff_strb_mask, burst_len=1,
                       comment="Write RX Buffer Strobe")
            read_value = self.read(uart_rx_ctrl_addr, burst_len=1,
                                   comment='Read (back) UART RX Status Reg (0)')
            self.write(uart_rx_ctrl_addr, deassert_all, burst_len=1, comment="Wr RX Deassert All")
            read_value = self.read(uart_rx_ctrl_addr, burst_len=1,
                                   comment='Read (back) UART RX Status Reg 1')
            buffer_status = self.read(uart_status_addr, burst_len=1,
                                      comment='Read UART Buffer status 1')
            buff_level = (buffer_status[0] & rx_buff_level_mask) >> 8
            uart_status = self.read(uart_status_addr, burst_len=1, comment='Rd UART Buff status 2')
            rx_d = (uart_status[0] & rx_buff_data_mask) >> 16
            if debug:   # pragma: no coverage
                print(" RX buff status: {0} ({1:08X})".format(buffer_status[0], buffer_status[0]))
                print(" RX buff_level: {0} rx_d: {1} (0x{2:X})".format(buff_level, rx_d, rx_d))
            rx_data.append(rx_d)
            read_value = self.read(uart_status_addr, burst_len=1, comment='Rd UART Buff status 3')
            rx_has_data_flag = not (read_value[0] & rx_buff_empty_mask)
        # Clear Rx buffer (Not) empty flag - Redundant?
        # buffer_status = self.read(uart_status_addr, burst_len=1, comment='Rd UART Buff status 1')
        # print(" 1.RX buffer_status: {0} (0x{1:08X})".format(buffer_status[0], buffer_status[0]))

        # self.write(uart_rx_ctrl_addr, 0x0, burst_len=1, comment="Clear RX Buffer Strobe")
        # read_value = self.read(uart_rx_ctrl_addr, burst_len=1,
        #                        comment='Read (back) UART RX Status Reg (3)')
        # self.write(uart_rx_ctrl_addr, 0x1, burst_len=1, comment="Write RX Buffer Strobe")
        # read_value = self.read(uart_rx_ctrl_addr, burst_len=1,
        #                        comment='Read (back) UART RX Status Reg (4)')

        # self.write(uart_rx_ctrl_addr, 0x3, burst_len=1, comment="Write RX Strobe/Reset")
        # read_value = self.read(uart_rx_ctrl_addr, burst_len=1,
        #                        comment='Read (back) UART RX Status Reg (5)')

        # self.write(uart_rx_ctrl_addr, 0x1, burst_len=1, comment="Write RX Buffer Strobe")
        # read_value = self.read(uart_rx_ctrl_addr, burst_len=1,
        #                        comment='Read (back) UART RX Status Reg (6)')

        # self.write(uart_rx_ctrl_addr, deassert_all, burst_len=1, comment="Write RX Deassert All")
        # read_value = self.read(uart_rx_ctrl_addr, burst_len=1,
        #                        comment='Read (back) UART RX Status Reg 1')

        # buffer_status = self.read(uart_status_addr, burst_len=1, comment='Rd UART Buff status 1')
        # print(" 2.RX buffer_status: {0} (0x{1:08X})".format(buffer_status[0], buffer_status[0]))

    def uart_tx(self, cmd):
        """Transmit command to the UART."""
        debug = False   # True
        uart_tx_ctrl_addr = uart_tx_ctrl_offset
        # Check that UART buffer is empty (1 = empty, 0 = has data)
        try:
            is_tx_buff_empty, is_rx_buff_empty = self.check_tx_rx_buffs_empty()
        except HexitecRdmaError as e:
            raise HexitecRdmaError("uart_tx: {}".format(e))
        if is_tx_buff_empty == 0:
            raise Exception("uart_tx: TX Buffer NOT empty!")

        if vsr_start_char in cmd:
            raise Exception("Extra start (0x23) char detected!")
        if vsr_end_char in cmd:
            raise Exception("Extra end (0x0D) char detected!")
        vsr_seq = [vsr_start_char]
        for d in cmd:
            vsr_seq.append(d)
        vsr_seq.append(vsr_end_char)
        if debug:   # pragma: no coverage
            print("... sending: {}".format(' '.join("0x{0:02X}".format(x) for x in vsr_seq)))
        try:
            # Clear tx ctrl reg:
            self.write(uart_tx_ctrl_addr, deassert_all, burst_len=1, comment="Wr TX Deassert All")
            for b in vsr_seq:
                # Write byte
                self.write(uart_tx_ctrl_addr, b << 8, burst_len=1,
                           comment="Write '{0:X}' Byte to TX Buffer".format(b))
                # Read byte back
                read_tx_value = self.read(uart_tx_ctrl_addr, burst_len=1, comment="Read TX Buffer")
                read_tx_value = read_tx_value[0]
                if debug:   # pragma: no coverage
                    print(" TX buffer: {0} (0x{1:02X})".format(read_tx_value, read_tx_value))
                write_value = ((read_tx_value & tx_data_mask) | tx_fill_strb_mask)
                # Write byte with flag(s)
                self.write(uart_tx_ctrl_addr, write_value, burst_len=1,
                           comment="Write '{0:X}' Byte+flag(s) to TX Buffer".format(write_value))

                self.write(uart_tx_ctrl_addr, deassert_all, burst_len=1,
                           comment="Write TX Deassert All")

                self.read(uart_tx_ctrl_addr, burst_len=1, comment="Read TX Buff")  # Redundant? TBD

            self.write(uart_tx_ctrl_addr, tx_buff_strb_mask, burst_len=1,
                       comment="Write TX Buff Strobe")
            # Tidy up/Clear tx ctrl reg:
            self.write(uart_tx_ctrl_addr, deassert_all, burst_len=1, comment="Wr TX Deassert All")

        except socket.error as e:
            raise socket.error(e)
        except struct.error as e:
            message = ' '.join("0x{0:02X}".format(x) for x in cmd)
            raise struct.error("uart_tx([{}]): {}".format(message, e))

    def read_uart_status(self):
        """Poll the UART reg (0x10)."""
        is_tx_buff_full = 0
        is_tx_buff_empty = 0
        is_rx_buff_full = 0
        is_rx_buff_empty = 0
        is_rx_pkt_done = 0
        uart_status = (0, )
        try:
            # self.write(uart_tx_ctrl_addr, deassert_all, burst_len=1, comment="Wr TX Deass't All")
            uart_status = self.read(uart_status_offset, burst_len=1, comment="Read UART Status")
            uart_status = uart_status[0]
            is_tx_buff_full = uart_status & tx_buff_full_mask
            is_tx_buff_empty = (uart_status & tx_buff_empty_mask) >> 1
            is_rx_buff_full = (uart_status & rx_buff_full_mask) >> 2
            is_rx_buff_empty = (uart_status & rx_buff_empty_mask) >> 3
            is_rx_pkt_done = (uart_status & rx_pkt_done_mask) >> 4
        except Exception as e:
            raise HexitecRdmaError("read_uart_status: {}".format(e))
        return uart_status, is_tx_buff_full, is_tx_buff_empty, is_rx_buff_full, \
            is_rx_buff_empty, is_rx_pkt_done

    def check_tx_rx_buffs_empty(self):
        """Check whether tx, rx buffers empty.

        Returns tx, rx status. 1 = Empty, 0 = Has data.
        """
        is_tx_buff_empty = 0
        is_rx_buff_empty = 0
        uart_status = (0, )
        try:
            uart_status = self.read(uart_status_offset, burst_len=1, comment="Read UART Status")
            uart_status = uart_status[0]
            # print(" *** Check_tx_RX_buffs_empty: {0:X}".format(uart_status))
            is_tx_buff_empty = (uart_status & tx_buff_empty_mask) >> 1
            is_rx_buff_empty = (uart_status & rx_buff_empty_mask) >> 3
            # print(" *** tx: {} rx: {}".format(is_tx_buff_empty, is_rx_buff_empty))
        except Exception as e:
            raise HexitecRdmaError("check_tx_rx_buffs_empty: {}".format(e))
        return is_tx_buff_empty, is_rx_buff_empty

    def enable_vsr_or_hv(self, vsr_number, bit_mask):   # pragma: no coverage
        """Control a single VSR's power."""
        vsr_ctrl_addr = RdmaUDP.vsr_ctrl_offset
        # STEP 1: vsr_ctrl enable $::vsr_target_idx
        mod_mask = self.module_mask(vsr_number)
        cmd_mask = bit_mask
        read_value = self.read(vsr_ctrl_addr, burst_len=1,
                               comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | (cmd_mask & mod_mask)
        self.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + vsr_number
        self.uart_tx([vsr_address, RdmaUDP.ENABLE_VSR])
        print("VSR {} enabled".format(vsr_number))

    def enable_vsr(self, vsr_number):   # pragma: no coverage
        """Control a single VSR's power."""
        vsr_ctrl_addr = RdmaUDP.vsr_ctrl_offset
        # STEP 1: vsr_ctrl enable $::vsr_target_idx
        mod_mask = self.module_mask(vsr_number)
        cmd_mask = RdmaUDP.enable_vsrs_mask
        read_value = self.read(vsr_ctrl_addr, burst_len=1,
                               comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | (cmd_mask & mod_mask)
        self.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + vsr_number
        self.uart_tx([vsr_address, RdmaUDP.ENABLE_VSR])
        # print("VSR {} enabled".format(vsr_number))

    def disable_vsr(self, vsr_number):  # pragma: no coverage
        """Control a single VSR's power."""
        vsr_ctrl_addr = RdmaUDP.vsr_ctrl_offset
        # STEP 1: vsr_ctrl disable $::vsr_target_idx
        mod_mask = self.negative_module_mask(vsr_number)
        read_value = self.read(vsr_ctrl_addr, burst_len=1,
                               comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        # print("read_value: {}".format(read_value))
        # print("mod_mask: {}".format(mod_mask))
        masked_value = read_value & mod_mask
        self.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + vsr_number
        self.uart_tx([vsr_address, RdmaUDP.DISABLE_VSR])
        # print("VSR {} disabled".format(vsr_number))

    def enable_all_vsrs(self):
        """Switch all VSRs on."""
        vsr_ctrl_addr = RdmaUDP.vsr_ctrl_offset
        read_value = self.read(vsr_ctrl_addr, burst_len=1,
                               comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | 0x3F    # Switching all six VSRs on, i.e. set 6 bits on
        self.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all VSRs on")
        # time.sleep(1)

    def enable_all_hvs(self):
        """Switch all HVs on."""
        vsr_ctrl_addr = RdmaUDP.vsr_ctrl_offset
        read_value = self.read(vsr_ctrl_addr, burst_len=1,
                               comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | RdmaUDP.hvs_bit_mask    # Switching all six HVs on
        # print(" enable_all_hvs, addr: {0:X} val: {1:X}".format(vsr_ctrl_addr, masked_value))
        self.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all HVs on")
        # time.sleep(1)
        # vsr_address = 0xFF
        # self.uart_tx([vsr_address, RdmaUDP.ENABLE_VSR])
        # print("All HVs on")

    def enable_hv(self, hv_number):
        """Switch on a single VSR's power."""
        vsr_ctrl_addr = RdmaUDP.vsr_ctrl_offset
        # STEP 1: vsr_ctrl enable $::vsr_target_idx
        mod_mask = self.module_mask(hv_number)
        cmd_mask = RdmaUDP.hvs_bit_mask
        read_value = self.read(vsr_ctrl_addr, burst_len=1,
                               comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | (cmd_mask & mod_mask)
        self.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + hv_number
        self.uart_tx([vsr_address, RdmaUDP.ENABLE_VSR])
        # print("HV {} on".format(hv_number))

    def disable_all_hvs(self):
        """Switch all HVs off."""
        vsr_ctrl_addr = RdmaUDP.vsr_ctrl_offset
        read_value = self.read(vsr_ctrl_addr, burst_len=1,
                               comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value & 0x3F    # Switching all six HVs off
        # print(" disable_all_hvs, addr: {0:X} val: {1:X}".format(vsr_ctrl_addr, masked_value))
        self.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all HVs off")
        # time.sleep(1)
        # vsr_address = 0xFF
        # self.uart_tx([vsr_address, RdmaUDP.DISABLE_VSR])
        # print("All HVs off")

    def as_power_status(self):
        """Issue Disable command to aS_PWR_TRIG_HV board (address: 0xC0)."""
        self.uart_tx([0xC0, 0x49])
        # time.sleep(1.5)
        # TODO: Listen for response !
        counter = 0
        rx_pkt_done = 0
        while not rx_pkt_done:
            uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, \
                rx_pkt_done = self.read_uart_status()
            counter += 1
            # if counter % 100 == 0:
            #     msg = "{0:05} UART: {1:08X} tx_buff_full: {2:0X} tx_buff_empty: {3:0X}".format(
            #         counter, uart_status, tx_buff_full, tx_buff_empty)
            #     print("{0} rx_buff_full: {1:0X} rx_buff_empty: {2:0X} rx_pkt_done: {3:0X}".format(
            #         msg, rx_buff_full, rx_buff_empty, rx_pkt_done))
            if counter == 15001:
                print(" *** as_power_status() timed out waiting for uart!")
                break
        time.sleep(1.5)
        response = self.uart_rx(0x0)
        return response

    def as_enable(self):
        """Issue Enable command to aS_PWR_TRIG_HV board (address: 0xC0)."""
        self.uart_tx([0xC0, 0xE3])
        # No response issued

    def as_disable(self):
        """Issue Disable command to aS_PWR_TRIG_HV board (address: 0xC0)."""
        self.uart_tx([0xC0, 0xE2])
        # No response issued

    def disable_all_vsrs(self):
        """Switch all VSRs off."""
        vsr_ctrl_addr = RdmaUDP.vsr_ctrl_offset
        read_value = self.read(vsr_ctrl_addr, burst_len=1,
                               comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value & RdmaUDP.hvs_bit_mask    # Switching all six VSRs off
        self.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all VSRs off")
        # time.sleep(1)
        # vsr_address = 0xFF
        # self.uart_tx([vsr_address, RdmaUDP.DISABLE_VSR])
        # print("All VSRs disabled")

    def power_status(self):
        """Read out the status register to check what is switched on and off."""
        read_value = self.read(RdmaUDP.vsr_ctrl_offset, burst_len=1,
                               comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        # print(" *** Register status: 0x{0:08X}".format(read_value))
        return read_value

    def module_mask(self, module):
        """Bit manipulation for VSR/HV control functions."""
        return ((1 << (module - 1)) | (1 << (module + 8 - 1)))

    def negative_module_mask(self, module):
        """Bit manipulation for VSR/HV control functions."""
        return ~(1 << (module - 1)) | (1 << (module + 8 - 1))


class HexitecRdmaError(Exception):
    """Simple exception class to wrap exceptions."""

    pass
