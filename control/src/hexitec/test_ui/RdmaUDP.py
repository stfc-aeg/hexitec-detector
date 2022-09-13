"""
Rdma - UDP 10 G access.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

import socket
import struct
import time


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

# TODO: This global variable to be removed post debugging
SLEEP_DELAY = 0.000   # 2


class RdmaUDP(object):

    def __init__(self, local_ip='192.168.0.1', local_port=65535,
                 rdma_ip='192.168.0.2', rdma_port=65536,
                 UDPMTU=9000, UDPTimeout=5, debug=False, unique_cmd_no=False):

        self.debug = debug
        if self.debug:
            print("RdmaUDP:")
            print("	Binding: ({}, {})".format(local_ip, local_port))
            print(" Send to: ({}, {})".format(rdma_ip, rdma_port))
            print(" UDPMaxRx: {}".format(UDPMTU))
            print("___________________________________________________________ ")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(UDPTimeout)
        self.error_OK = True

        try:
            self.socket.bind((local_ip, local_port))
        except socket.error as e:
            error_string = "  Error: '{}' ".format(e)
            error_string += "on TX Socket: {}:{}".format(local_ip, local_port)
            print(error_string)
            self.error_OK = False

        self.rdma_ip = rdma_ip
        self.rdma_port = rdma_port
        self.UDPMaxRx = UDPMTU
        self.ack = False
        self.unique_cmd_no = unique_cmd_no
        if self.unique_cmd_no:
            self.cmd_no = -1
        else:
            self.cmd_no = 0

    def __del__(self):
        self.socket.close()

    def read(self, address, burst_len=1, comment=''):
        burst_len = burst_len
        if self.unique_cmd_no:
            self.cmd_no += 1
        else:
            self.cmd_no = 0
        op_code = 1
        if self.debug:
            print(" R. burst_len: {0:X} cmd_no: {1:0X} op_code: {2:0X} address: 0x{3:0X} comment: \"{4}\" ***".format(
                  burst_len, self.cmd_no, op_code, address, comment))
        # H = burst len, B = cmd no, B = Op code, I = start address
        # H = unsigned short (2), B = unsigned char (1), I = signed int (4 Bytes)
        command = struct.pack('=HBBI', burst_len, self.cmd_no, op_code, address)
        data = (0, )
        try:
            self.socket.sendto(command, (self.rdma_ip, self.rdma_port))
        except socket.error as e:
            print(" *** Read (W) Error: {0}. burst_len: {1:X} cmd_no: {2:0X} op_code: {3:0X} address: 0x{4:0X} comment: \"{5}\" ***".format(e,
                  burst_len, self.cmd_no, op_code, address, comment))
            raise socket.error(e)
        try:
            # Receive acknowledge packet
            response = self.socket.recv(self.UDPMaxRx)
            header_str = "HBBI"   # Equivalent length: 8
            payload_length = len(response) - 8  # 8 = header length
            payload_length = payload_length // 4    # 32 bit word, therefore 4 bytes per word
            packet_str = header_str + "I" * payload_length
            padding = (burst_len % 2)
            if payload_length != (burst_len + padding):
                print("read expected {}, received {}, words!".format(burst_len, payload_length))
                return data
            decoded = struct.unpack(packet_str, response)
            if padding:
                data = decoded[4:-padding]  # Omit burst_len, cmd_no, op_code, address and padding present at the end
            else:
                data = decoded[4:]  # Omit burst_len, cmd_no, op_code, address
            if self.ack:
                print("R decoded 0x{0:08X} : 0x{1} \"{2}\"".format(address, ''.join("{0:X}".format(x) for x in data), comment))
        except socket.error as e:
            print(" *** Read (R) Error: {0}. burst_len: {1:X} cmd_no: {2:0X} op_code: {3:0X} address: 0x{4:0X} comment: \"{5}\" ***".format(e,
                  burst_len, self.cmd_no, op_code, address, comment))
            raise socket.error(e)
        except struct.error as e:
            print(" *** Read Error: {} ***".format(e))
        time.sleep(SLEEP_DELAY)
        return data

    def write(self, address, data, burst_len=1, comment=''):
        burst_len = burst_len
        if self.unique_cmd_no:
            self.cmd_no += 1
        else:
            self.cmd_no = 0
        op_code = 0
        if self.debug:
            print(" W. burst_len: {0:X} cmd_no: {1:X} op_code: {2:X} address: 0x{3:X} data: {4:X} comment: \"{5}\" ***".format(
                  burst_len, self.cmd_no, op_code, address, data, comment))
            # print(" W. burst_len: {0:X} cmd_no: {1:X} op_code: {2:X} address: 0x{3:X} data: {4} comment: \"{5}\" ***".format(
            #       burst_len, self.cmd_no, op_code, ', '.join("0x{0:X}".format(x) for x in address), data, comment))
        # H = burst len, B = cmd no, B = Op code, I = address, I = data
        # H = unsigned short (2), B = unsigned char (1), I = signed int (4 Bytes)
        header_str = "HBBI"   # Equivalent length: 8
        packet_str = header_str + "I" * burst_len
        if burst_len == 1:
            command = struct.pack(packet_str, burst_len, self.cmd_no, op_code, address, data)
        elif burst_len == 2:
            data = (data & 0xFFFFFFFF), (data >> 32)
            command = struct.pack(packet_str, burst_len, self.cmd_no, op_code, address, data[0], data[1])
            # print("data: {0:08X} {1:08X}".format(data[0], data[1]))
        elif burst_len == 3:
            data = (data & 0xFFFFFFFF), ((data >> 32) & 0xFFFFFFFF), (data >> 64)
            command = struct.pack(packet_str, burst_len, self.cmd_no, op_code, address, data[0], data[1], data[2])
            # print("data: {0:08X} {1:08X} {2:08X}".format(data[0], data[1], data[2]))
        elif burst_len == 4:
            data = (data & 0xFFFFFFFF), ((data >> 32) & 0xFFFFFFFF), ((data >> 64) & 0xFFFFFFFF), (data >> 96)
            command = struct.pack(packet_str, burst_len, self.cmd_no, op_code, address, data[0], data[1], data[2], data[3])
            # print("data: {0:08X} {1:08X} {2:08X} {3:08X}".format(data[0], data[1], data[2], data[3]))
        else:
            print("burst_length of: {} is not supported".format(burst_len))
            return -1
        # Send the single write command packet
        try:
            self.socket.sendto(command, (self.rdma_ip, self.rdma_port))
        except socket.error as e:
            print(" *** Write (W) Error: {0}. burst_len: {1:0X} cmd_no: {2:X} op_code: {3:0X} address: 0x{4:X} data: {5:0X} comment: \"{6}\" ***".format(e,
                  burst_len, self.cmd_no, op_code, address, data, comment))
            raise socket.error(e)
        try:
            # Receive acknowledgement
            response = self.socket.recv(self.UDPMaxRx)
            if self.ack:
                header_str = "HBBI"   # Equivalent length: 8
                payload_length = len(response) - 8  # 8 = header length
                payload_length = payload_length // 4    # 32 bit word, therefore 4 bytes per word
                packet_str = header_str + "I" * payload_length
                padding = (burst_len % 2)
                decoded = struct.unpack(packet_str, response)
                # decoded = struct.unpack('=HBBII', response) # Fine
                # decoded = struct.unpack(command, response) # struct.error: bad char in struct format
                # if padding:
                #     data = decoded[4:-padding]  # Omit burst_len, cmd_no, op_code, address and padding present at the end
                # else:
                #     data = decoded[4:]  # Omit burst_len, cmd_no, op_code, address
                # print("W Ack Raw: {}".format(decoded))
                print('W decoded: {} Comment: \"{}\" Length: {}'.format(', '.join("0x{0:X}".format(x) for x in decoded), comment, len(response)))
        except socket.error as e:
            print(" *** Write (R) Error: {0}. burst_len: {1:0X} cmd_no: {2:X} op_code: {3:0X} address: 0x{4:X} data: {5:0X} comment: \"{6}\" ***".format(e,
                  burst_len, self.cmd_no, op_code, address, data, comment))
            raise socket.error(e)
        except struct.error as e:
            print(" *** Write Error: {} ***".format(e))
        time.sleep(SLEEP_DELAY)

    def close(self):
        self.socket.close()

    def setDebug(self, enabled=True):
        self.debug = enabled

    def uart_rx(self, uart_address):
        """Receive all data available in the UART."""
        debug = False    # True
        uart_status_addr = uart_address + uart_status_offset
        uart_rx_ctrl_addr = uart_address + uart_rx_ctrl_offset
        read_value = self.read(uart_status_addr, burst_len=1, comment='Read UART Buffer Status (0)')
        buff_level = (read_value[0] & rx_buff_level_mask) >> 8
        rx_d = (read_value[0] & rx_buff_data_mask) >> 16
        if debug:
            print(" RX init_buff_status: {0} (0x{1:08X})".format(read_value[0], read_value[0]))
            print(" RX buff_level: {0} rx_d: {1} (0x{2:X}) [IGNORED - Like tickle script]".format(buff_level, rx_d, rx_d))
        rx_status_masked = (read_value[0] & rx_buff_empty_mask)
        rx_has_data_flag = not rx_status_masked
        rx_data = []
        while (rx_has_data_flag):
            self.write(uart_rx_ctrl_addr, rx_buff_strb_mask, burst_len=1, comment="Write RX Buffer Strobe")
            read_value = self.read(uart_rx_ctrl_addr, burst_len=1, comment='Read (back) UART RX Status Reg (0)')
            self.write(uart_rx_ctrl_addr, deassert_all, burst_len=1, comment="Write RX Deassert All")
            read_value = self.read(uart_rx_ctrl_addr, burst_len=1, comment='Read (back) UART RX Status Reg (1)')
            buffer_status = self.read(uart_status_addr, burst_len=1, comment='Read UART Buffer status (1)')
            buff_level = (buffer_status[0] & rx_buff_level_mask) >> 8
            uart_status = self.read(uart_status_addr, burst_len=1, comment='Read UART Buffer status (2)')
            rx_d = (uart_status[0] & rx_buff_data_mask) >> 16
            if debug:
                print(" RX buffer_status: {0} (0x{1:08X})".format(buffer_status[0], buffer_status[0]))
                print(" RX buff_level: {0} rx_d: {1} (0x{2:X})".format(buff_level, rx_d, rx_d))
            rx_data.append(rx_d)
            read_value = self.read(uart_status_addr, burst_len=1, comment='Read UART Buffer status (3)')
            rx_has_data_flag = not (read_value[0] & rx_buff_empty_mask)
        # print("(RdmaUDP) UART RX'd: {}".format(' '.join("0x{0:02X}".format(x) for x in rx_data)))
        return rx_data

    def uart_tx(self, cmd):
        """Transmit command to the UART."""
        debug = False   # True
        uart_tx_ctrl_addr = uart_tx_ctrl_offset
        uart_status_addr = uart_status_offset

        vsr_seq = [vsr_start_char]
        for d in cmd:
            vsr_seq.append(d)
        vsr_seq.append(vsr_end_char)
        if debug:
            print("... sending: {}".format(' '.join("0x{0:02X}".format(x) for x in vsr_seq)))
        try:
            # Clear tx ctrl reg:
            self.write(uart_tx_ctrl_addr, deassert_all, burst_len=1, comment="Write TX Deassert All")
            for b in vsr_seq:
                # Write byte
                self.write(uart_tx_ctrl_addr, b << 8, burst_len=1, comment="Write '{0:X}' Byte to TX Buffer".format(b))
                # Read byte back
                read_tx_value = self.read(uart_tx_ctrl_addr, burst_len=1, comment="Read TX Buffer")
                read_tx_value = read_tx_value[0]
                if debug:
                    print(" TX buffer contain: {0} (0x{1:02X})".format(read_tx_value, read_tx_value))
                write_value = ((read_tx_value & tx_data_mask) | tx_fill_strb_mask)
                # Write byte with flag(s)
                self.write(uart_tx_ctrl_addr, write_value, burst_len=1, comment="Write '{0:X}' Byte+flag(s) to TX Buffer".format(write_value))

                self.write(uart_tx_ctrl_addr, deassert_all, burst_len=1, comment="Write TX Deassert All")

                self.read(uart_tx_ctrl_addr, burst_len=1, comment="Read TX Buffer") # Redundant? TBD

            self.write(uart_tx_ctrl_addr, tx_buff_strb_mask, burst_len=1, comment="Write TX Buffer Strobe")
            # Tidy up/Clear tx ctrl reg:
            self.write(uart_tx_ctrl_addr, deassert_all, burst_len=1, comment="Write TX Deassert All")

        except Exception as e:
            print(" *** uart_tx error: {} ***".format(e))
