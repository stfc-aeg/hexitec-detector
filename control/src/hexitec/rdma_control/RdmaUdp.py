# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.
"""Classes and functions to connect to, and communicate with `RDMA` control plane via `UDP` Ethernet.

.. important::

   Requires memory mapped :obj:`dict` imported from :mod:`rdma_control.RDMA_REGISTERS` and helper functions
   imported from :mod:`rdma_control.rdma_register_helpers`.

   :mod:`rdma_control.RDMA_REGISTERS` is generated from XML2VHDL output, regenerated at FPGA synthesis time. Please
   ensure the latest version is used in conjunction with :mod:`rdma_control.RdmaUdp` to ensure compatibility with the
   register map in the current FPGA bitstream.

"""
import socket
import struct

try:
    from rdma_control.RDMA_REGISTERS import *
    from rdma_control.rdma_register_helpers import *
except ModuleNotFoundError:
    from RDMA_REGISTERS import *
    from rdma_register_helpers import *

# TODO Temporarily defined here, move elsewhere: ???
tx_buff_full_mask = 0x1
tx_buff_empty_mask = 0x2
rx_buff_full_mask = 0x4
rx_buff_empty_mask = 0x8
rx_pkt_done_mask = 0x10

def _errorResponse(e, msg, etype="socket", address=0, burst_len=1, op_code=0, cmd_no=0, comment="", data=""):
    print(f"[ERROR] *** {msg} ***:")
    print(f"    OP Code: 0x{op_code:02X} | Address: 0x{address:08X} | Burst Length: {burst_len} | CMD No: {cmd_no:02X} <{comment}>")
    if data != "":
        print(f"         Data: {data}")
    print("")
    print(f"{e}")
    if etype.lower == "struct":
        raise struct.error(e)
    else:
        raise socket.error(e)


def _debugMsg(msg, address=0, burst_len=1, op_code=0, cmd_no=0, comment="", data=""):
    print(f"[DEBUG]: {msg}: 0x{op_code:02X} | Address: 0x{address:08X} | Burst Length: {burst_len} | CMD No: 0x{cmd_no:02X} | {comment}")
    if data != "":
        print(f"         Data: {data}")


def get_rdma_opcode(opcode):
    """Converts :obj:`str` operation into corresponding RDMA op-code.

    Args:
        opcode (:obj:`str`): from: `read` or `write`.

    Returns:
        :obj:`int` op-code to place in RDMA packet header.
    """
    if opcode.lower() == "read":
        return 0x01
    elif opcode.lower() == "write":
        return 0x00
    else:
        return 0x01


def iic_qsfp_module_sel(mmap_suffix, idx=1):
    """A basic function to return AXI I\ :sup:`2`\ C controller registers defined in :mod:`rdma_control.RDMA_REGISTERS`.

    Args:
        mmap_suffix (:obj:`str`): :mod:`rdma_control.RDMA_REGISTERS` to return, from:
            `TX_FIFO`, `CTRL_REG`, `ISR`, `STAT_REG`, `SOFTR`, `RX_FIFO`, `RX_FIFO_PIRQ`.
        idx (:obj:`int`, optional): QSFP module AXI I\ :sup:`2`\ C controller registers to select, from:
            `1`, `2`. Default: `1`.

    Returns: :obj:`dict`: an entry from :mod:`rdma_control.RDMA_REGISTERS` in the form: `QSFP_<idx>_<mmap_suffix>`.
    """
    max_modules = 4
    if idx > max_modules:
        print(f"[ERROR] idx <{idx}> exceeds max supported modules <{max_modules}")
        return None

    if mmap_suffix.upper() == "TX_FIFO":
        if idx == 1:
            return QSFP_1_TX_FIFO
        elif idx == 2:
            return QSFP_2_TX_FIFO
        else:
            return QSFP_1_TX_FIFO
    elif mmap_suffix.upper() == "CTRL_REG":
        if idx == 1:
            return QSFP_1_CTRL_REG
        elif idx == 2:
            return QSFP_2_CTRL_REG
        else:
            return QSFP_1_CTRL_REG
    elif mmap_suffix.upper() == "ISR":
        if idx == 1:
            return QSFP_1_ISR
        elif idx == 2:
            return QSFP_2_ISR
        else:
            return QSFP_1_ISR
    elif mmap_suffix.upper() == "STAT_REG":
        if idx == 1:
            return QSFP_1_STAT_REG
        elif idx == 2:
            return QSFP_2_STAT_REG
        else:
            return QSFP_1_STAT_REG
    elif mmap_suffix.upper() == "SOFTR":
        if idx == 1:
            return QSFP_1_SOFTR
        elif idx == 2:
            return QSFP_2_SOFTR
        else:
            return QSFP_1_SOFTR
    elif mmap_suffix.upper() == "RX_FIFO":
        if idx == 1:
            return QSFP_1_RX_FIFO
        elif idx == 2:
            return QSFP_2_RX_FIFO
        else:
            return QSFP_1_RX_FIFO
    elif mmap_suffix.upper() == "RX_FIFO_PIRQ":
        if idx == 1:
            return QSFP_1_RX_FIFO_PIRQ
        elif idx == 2:
            return QSFP_2_RX_FIFO_PIRQ
        else:
            return QSFP_1_RX_FIFO_PIRQ
    else:
        print(f"[ERROR] Unsupported IIC mmap suffix: {mmap_suffix}")
        return None


class RdmaUDP(object):
    """Class for handling `RDMA` based UDP Ethernet transactions.

    .. important::

       Requires memory mapped :obj:`dict` imported from :mod:`rdma_control.RDMA_REGISTERS` and helper functions
       imported from :mod:`rdma_control.rdma_register_helpers`.

       :mod:`rdma_control.RDMA_REGISTERS` is generated from XML2VHDL output, regenerated at FPGA synthesis time. Please
       ensure the latest version is used in conjunction with :mod:`rdma_control.RdmaUdp` to ensure compatibility with the
       register map in the current FPGA bitstream.

    .. note::

       In addition to providing direct access to the FPGA `RDMA` memory-map using :meth:`udp_rdma_read` and
       :meth:`udp_rdma_write`, the FPGA can be used to bridge to connected devices and peripherals to access the
       following:
         - `aSpect` based `UART`
         - `Xilinx` AXI I\ :sup:`2`\ C interfaces to attached `QSFP` modules.

    Args:
        local_ip (:obj:`str`): IP address of the local NIC used to communicate with the remote `RDMA` control plane.
        local_port (:obj:`int`, optional): Port used to connect to remote UDP `RDMA` control plane. Default: `65535`.
        rdma_ip (:obj:`str`): IP address of the remote `RDMA` control plane.
        rdma_port (:obj:`int`, optional): Port used to receive from local NIC. Default: `65536`.
        udpmtu (:obj:`int`, optional): `Maximum Transfer Unit` for connection to `UDP` `RDMA` control plane.
            Default: `9000` (jumbo frame).
        udptimeout (:obj:`int`, optional): Timeout, in seconds, for connection to `UDP` `RDMA` control plane.
            Default: `5`
        speed (:obj:`str`, optional): Speed of the Ethernet connection, from: `10G`, `100G`. Default: `10G`.
        debug (:obj:`bool`): Flag to enable debug messages. Default: `False`.

    """
    def __init__(self, local_ip='192.168.0.1', local_port=65535,
                 rdma_ip='192.168.0.2', rdma_port=65536,
                 udpmtu=9000, udptimeout=5, speed="10G", debug=False):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(udptimeout)
        self.error_OK = True
        self.debug=debug
        self.speed = speed.upper()
        try:
            self.socket.bind((local_ip, local_port))
        except (socket.error, OSError) as e:
            error_string = f"Error: '{e} '"
            error_string += f"on TX Socket: {local_ip}:{local_port}"
            print(error_string)
            self.error_OK = False
            raise socket.error(f"Error: {e}")
        self.rdma_ip = rdma_ip
        self.rdma_port = rdma_port
        self.udpmtu = udpmtu
        # RDMA Header is defined as:
        #     [=] native byte order
        #     [H] unsigned short <Burst Length> | [B] unsigned char <CMD No> | [B] unsigned char <OP Code>
        #     [L] unsigned long <Address>
        self._header_struct_str = "=HBBL"
        self._header_size = 8    # RDMA Header Size, in bytes
        self._header_fields = 4 # Number of fields included in the RDMA header
        self._bytes_per_word = 4 # RDMA Word size, in bytes (AXI4Lite 32b interface)
        # Width of the readout interface influences the amount of padding required in RDMA read responses
        if self.speed == "100G":
            self._bytes_per_readout_iface = 64
        else:
            self._bytes_per_readout_iface = 8


    def __del__(self):
        """Ensure connection safely closed."""
        self.close()


    def close(self):
        """Safely close `UDP` socket connection."""
        self.socket.close()


    def _convert_to_list(self, data, burst_len):
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
            bit_shifting += self._bytes_per_word * 8
        return data_array


    def _RdmaResponseChecker(self, msg, address=0, burst_len=1, op_code=0, cmd_no=0, comment=""):
        response_data = ()
        padding = (burst_len % 2)
        # \TODO padding should be calculated on the readout word width
        # padding = int(burst_len % (self._bytes_per_readout_iface / self._bytes_per_word))
        # ##############################################################################################################
        if op_code == 0x00:
            expected_payload_size = 4
            packet_struct_str = self._header_struct_str
            expected_response_size = self._header_size
        else:
            expected_payload_size = (burst_len * self._bytes_per_word)
            packet_struct_str = self._header_struct_str + ("I" * burst_len)
            expected_response_size = self._header_size + expected_payload_size

        if self.debug:
            print(f"[DEBUG]: RDMA {msg} response:")
            print(f"         Op-Code:                             0x{op_code:02X}")
            print(f"         Readout word size:                   {self._bytes_per_readout_iface} Byte(s) <{self.speed}>")
            print(f"         padding size:                        {padding}")
            print(f"         Unpack string:                       \"{packet_struct_str}\"")
            if expected_payload_size > 0:
                print(f"         RDMA burst size:                     {burst_len}")
            print(f"         RDMA header size:                    {self._header_size} Byte(s)")
            print(f"         expected RDMA response payload size: {expected_payload_size} Byte(s)")
            print(f"         expected Total RDMA response size:   {expected_response_size} Byte(s)")

        try:
            rdma_response = self.socket.recv(expected_response_size)
        except socket.error as e:
            _errorResponse(e, "{msg} acknowledge failed", address=address,
                           burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment)

        response_len = len(rdma_response)

        if self.debug:
            print(f"         Raw response:                        {rdma_response}")
            print(f"         Raw response size:                   {response_len} Byte(s)")

        try:
            decoded_response = struct.unpack(packet_struct_str, rdma_response)
        except struct.error as e:
            _errorResponse(e, f"RMDA {msg} acknowledge failed", etype="struct", address=address,
                           burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment)

        decoded_hex_response = [ hex(x) for x  in decoded_response ]

        if self.debug:
            print(f"[DEBUG]: RDMA {msg} decoded response: {decoded_hex_response}")

        response_data = decoded_response[self._header_fields:]
        response_data = [ x for x in response_data ]

        if self.debug:
            print(f"[DEBUG]: RDMA {msg} response: {response_data}")

        return response_data


    def udp_rdma_read(self, address, burst_len=1, cmd_no=0, comment=''):
        """`UDP` based `RDMA` read.

        Issues an `RDMA` formatted read command to the established socket and returns back the contents.

        Args:
            address (:obj:`int`): Memory location to read.
            burst_len (:obj:`int`, optional): number of consecutive read transactions, starting from :attr:`address`.
                Default: `1`.
            cmd_no (:obj:`int`, optional): Number to include in the constructed `RDMA` header, useful for debugging.
                Default: `0`.
            comment (:obj:`str`, optional):Useful for debugging, will be included in debugging output.
                Default: `""` (empty string).

        Returns:
            :obj:`list` of :obj:`int`: Data stored in :attr:`address` parsed by :meth:`RdmaUDP_RdmaResponseChecker`.
        """
        cmd_no = cmd_no & 0xFF
        op_code = get_rdma_opcode("read")
        if self.debug:
            _debugMsg("RDMA Read", address=address,
                      burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment, data='')

        command = struct.pack(self._header_struct_str,
                              burst_len, cmd_no, op_code, address)

        # Send the RDMA read request:
        try:
            self.socket.sendto(command, (self.rdma_ip, self.rdma_port))
        except socket.error as e:
            _errorResponse(e, "Read failed", address=address,
                           burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment)

        # Read back RDMA response:
        return self._RdmaResponseChecker("Read", address=address,
                                         burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment)


    def udp_rdma_write(self, address, data, burst_len=1, cmd_no=0, comment=''):
        """`UDP` based `RDMA` write.

        Issues an `RDMA` formatted write command and write data to the established socket.

        Args:
            address (:obj:`int`): Memory location to write.
            data (:obj:`list` of :obj:`int`): data to write, starting at :attr:`address`. *Note*, the number items in
                this :obj:`list` must be greater or equal to the requested :attr:`burst_len`. :attr:`burst_len` is used
                to determine the number of consecutive writes to perform, not the number of items in this :obj:`list`.
            burst_len (:obj:`int`, optional): number of consecutive write transactions, starting from :attr:`address`.
                Default: `1`.
            cmd_no (:obj:`int`, optional): Number to include in the constructed `RDMA` header, useful for debugging.
                Default: `0`.
            comment (:obj:`str`, optional):Useful for deugging, will be included in debugging output.
                Default: `""` (empty string).

        Whilst nothing is returned the response from the write command is parsed by :meth:`RdmaUDP_RdmaResponseChecker`.

        Returns:
            Nothing.
        """
        cmd_no = cmd_no & 0xFF
        op_code = get_rdma_opcode("write")
        if self.debug:
            _debugMsg("RDMA Write", address=address,
                      burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment, data=data)
        payload_length = (burst_len * self._bytes_per_word)
        payload_words = payload_length // self._bytes_per_word
        packet_struct_str = self._header_struct_str + ("I" * burst_len)
        cmd_no_0 = cmd_no
        if not isinstance(data, list):
            data_as_list = self._convert_to_list(data, burst_len)
        else:
            data_as_list = data[0:burst_len]
        command_0 = struct.pack(packet_struct_str, burst_len, cmd_no_0, op_code, address, *data_as_list)
        if self.debug:
            print(f"[DEBUG]: RDMA Write request:")
            print(f"         Payload length:       {payload_length} Byte(s) | {payload_words} Word(s)")
            print(f"         Pack string:          {packet_struct_str}")
            print(f"         Raw write data:       {data}")
            print(f"         Prepared write data:  {data_as_list}")
            print(f"         Packed write command: {command_0}")
        # Send the single write command packet
        try:
            self.socket.sendto(command_0, (self.rdma_ip, self.rdma_port))
        except socket.error as e:
            _errorResponse(e, "Write failed", address=address,
                           burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment, data=data)
        # Read back RDMA response:
        write_reponse = self._RdmaResponseChecker("Write", address=address,
                                                  burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment)


    def uart_read(self, cmd_no=0):
        """Performs a UART read operation by checking the `UART` read buffer using :meth:`udp_rdma_read` and :meth:`udp_rdma_write`.

        Args:
            cmd_no (:obj:`int`, optional): Number to include in the constructed `RDMA` header, useful for debugging.
                Default: `0`.

        Returns:
            :obj:`list` of bytes as :obj:`int`: for all data read from the `UART` receive buffer.
        """
        rx_d = list()
        # check RX_BUFF_EMTY
        status_reg = self.udp_rdma_read(HEXITEC_2X6_UART_STATUS['addr'],
                                        burst_len=1, cmd_no=cmd_no,
                                        comment=HEXITEC_2X6_UART_STATUS['description'])[0]
        has_data = not decode_field(HEXITEC_2X6_UART_STATUS, "RX_BUFF_EMTY", status_reg)
        rx_buff_lvl = decode_field(HEXITEC_2X6_UART_STATUS, "RX_BUFF_LEVEL", status_reg)
        while has_data:
            # set RX_BUFF_STRB
            rx_ctrl = self.udp_rdma_read(HEXITEC_2X6_UART_RX_CTRL['addr'],
                                         burst_len=1, cmd_no=cmd_no,
                                         comment=HEXITEC_2X6_UART_RX_CTRL['description'])[0]
            rx_ctrl = set_field(HEXITEC_2X6_UART_RX_CTRL, "RX_BUFF_STRB", rx_ctrl, 1)
            self.udp_rdma_write(HEXITEC_2X6_UART_RX_CTRL['addr'], [rx_ctrl],
                                burst_len=1, cmd_no=cmd_no,
                                comment=HEXITEC_2X6_UART_RX_CTRL['description'])
            # clr RX_BUFF_STRB
            rx_ctrl = self.udp_rdma_read(HEXITEC_2X6_UART_RX_CTRL['addr'],
                                         burst_len=1, cmd_no=cmd_no,
                                         comment=HEXITEC_2X6_UART_RX_CTRL['description'])[0]
            rx_ctrl = clr_field(HEXITEC_2X6_UART_RX_CTRL, "RX_BUFF_STRB", rx_ctrl)
            self.udp_rdma_write(HEXITEC_2X6_UART_RX_CTRL['addr'], [rx_ctrl],
                                burst_len=1, cmd_no=cmd_no,
                                comment=HEXITEC_2X6_UART_RX_CTRL['description'])
            # get RX_DATA and check RX_BUFF_EMTY
            status_reg = self.udp_rdma_read(HEXITEC_2X6_UART_STATUS['addr'],
                                            burst_len=1, cmd_no=cmd_no,
                                            comment=HEXITEC_2X6_UART_STATUS['description'])[0]
            rx_d.append(decode_field(HEXITEC_2X6_UART_STATUS, "RX_DATA", status_reg))
            has_data = not decode_field(HEXITEC_2X6_UART_STATUS, "RX_BUFF_EMTY", status_reg)
        return rx_d


    def uart_write(self, wr_d, cmd_no=0):
        """Performs a UART write operation by transfer :attr:`wr_d` to the `UART` write buffer using :meth:`udp_rdma_read` and :meth:`udp_rdma_write`.

        Args:
            wr_d (:obj:`list` of bytes as :obj:`int`): Data to write to the `UART`. When the entire :obj:`list` has been
                transferred to the `UART` write buffer, the complete buffer will be transmitted.
            cmd_no (:obj:`int`, optional): Number to include in the constructed `RDMA` header, useful for debugging.
                Default: `0`.

        Returns:
            Nothing.
        """
        # queue each byte in the UART Tx FIFO
        for b in wr_d:
            # load TX_DATA and set TX_FILL_STRB
            tx_ctrl = self.udp_rdma_read(HEXITEC_2X6_UART_TX_CTRL['addr'],
                                         burst_len=1, cmd_no=cmd_no,
                                         comment=HEXITEC_2X6_UART_TX_CTRL['description'])[0]
            tx_ctrl = set_field(HEXITEC_2X6_UART_TX_CTRL, "TX_DATA", tx_ctrl, b)
            tx_ctrl = set_field(HEXITEC_2X6_UART_TX_CTRL, "TX_FILL_STRB", tx_ctrl, 1)
            self.udp_rdma_write(HEXITEC_2X6_UART_TX_CTRL['addr'], [tx_ctrl],
                                burst_len=1, cmd_no=cmd_no,
                                comment=HEXITEC_2X6_UART_TX_CTRL['description'])
            # clr TX_FILL_STRB
            tx_ctrl = self.udp_rdma_read(HEXITEC_2X6_UART_TX_CTRL['addr'],
                                         burst_len=1, cmd_no=cmd_no,
                                         comment=HEXITEC_2X6_UART_TX_CTRL['description'])[0]
            tx_ctrl = clr_field(HEXITEC_2X6_UART_TX_CTRL, "TX_FILL_STRB", tx_ctrl)
            self.udp_rdma_write(HEXITEC_2X6_UART_TX_CTRL['addr'], [tx_ctrl],
                                burst_len=1, cmd_no=cmd_no,
                                comment=HEXITEC_2X6_UART_TX_CTRL['description'])
        # transmit all contents of UART Tx FIFO
            # set TX_BUFF_STRB
            tx_ctrl = self.udp_rdma_read(HEXITEC_2X6_UART_TX_CTRL['addr'], burst_len=1, cmd_no=cmd_no,
                                         comment=HEXITEC_2X6_UART_TX_CTRL['description'])[0]
            tx_ctrl = set_field(HEXITEC_2X6_UART_TX_CTRL, "TX_BUFF_STRB", tx_ctrl, 1)
            self.udp_rdma_write(HEXITEC_2X6_UART_TX_CTRL['addr'], [tx_ctrl],
                                burst_len=1, cmd_no=cmd_no,
                                comment=HEXITEC_2X6_UART_TX_CTRL['description'])
            # clr TX_BUFF_STRB
            tx_ctrl = self.udp_rdma_read(HEXITEC_2X6_UART_TX_CTRL['addr'],
                                         burst_len=1, cmd_no=cmd_no,
                                         comment=HEXITEC_2X6_UART_TX_CTRL['description'])[0]
            tx_ctrl = clr_field(HEXITEC_2X6_UART_TX_CTRL, "TX_BUFF_STRB", tx_ctrl)
            self.udp_rdma_write(HEXITEC_2X6_UART_TX_CTRL['addr'], [tx_ctrl],
                                burst_len=1, cmd_no=cmd_no,
                                comment=HEXITEC_2X6_UART_TX_CTRL['description'])

    def read_uart_status(self):
        """Poll the UART reg (0x10)."""
        cmd_no = 0
        op_code = get_rdma_opcode("read")
        address = HEXITEC_2X6_UART_STATUS['addr']
        burst_len = 1
        comment = HEXITEC_2X6_UART_STATUS['description']
        is_tx_buff_full = 0
        is_tx_buff_empty = 0
        is_rx_buff_full = 0
        is_rx_buff_empty = 0
        is_rx_pkt_done = 0
        uart_status = (0, )
        try:
            uart_status = self.udp_rdma_read(address,
                                             burst_len=burst_len, cmd_no=cmd_no,
                                             comment=comment)[0]
            is_tx_buff_full = uart_status & tx_buff_full_mask
            is_tx_buff_empty = (uart_status & tx_buff_empty_mask) >> 1
            is_rx_buff_full = (uart_status & rx_buff_full_mask) >> 2
            is_rx_buff_empty = (uart_status & rx_buff_empty_mask) >> 3
            is_rx_pkt_done = (uart_status & rx_pkt_done_mask) >> 4
        except Exception as e:
            _errorResponse(e, "Read failed", address=address,
                           burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment)
        return uart_status, is_tx_buff_full, is_tx_buff_empty, is_rx_buff_full, \
            is_rx_buff_empty, is_rx_pkt_done

    def toggle_training(self, reg_value):
        """Toggle Training (UART Register 0x20) on then off."""
        cmd_no = 0
        op_code = get_rdma_opcode("write")
        address = HEXITEC_2X6_VSR_DATA_CTRL['addr']
        burst_len = 1
        comment = HEXITEC_2X6_VSR_DATA_CTRL['description']
        uart_status = (0, )
        try:
            self.udp_rdma_write(address, reg_value,
                                burst_len=burst_len, cmd_no=cmd_no,
                                comment=comment)
        except Exception as e:
            _errorResponse(e, "Write failed", address=address,
                           burst_len=burst_len, op_code=op_code, cmd_no=cmd_no, comment=comment)

    def _iic_read_fifo(self, size, idx=1, cmd_no=0):
        """Read `N` words from IIC Rx FIFO.

        """
        rx_fifo_dict = iic_qsfp_module_sel("RX_FIFO", idx=idx)
        b = list()
        for i in range(0, size):
            rx_fifo_reg = self.udp_rdma_read(rx_fifo_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                             comment=rx_fifo_dict['description'])[0]
            b.append(decode_field(rx_fifo_dict, "RX_DATA", rx_fifo_reg))
        return b


    def _iic_write_byte(self, b, idx=1, op="WRITE", dev_addr=0x50, cmd_no=0):
        """Write a single byte to IIC location defined by :obj:`dev_addr`

        """
        tx_fifo_dict = iic_qsfp_module_sel("TX_FIFO", idx=idx)
        cr_dict = iic_qsfp_module_sel("CTRL_REG", idx=idx)
        isr_dict = iic_qsfp_module_sel("ISR", idx=idx)

        if op.lower() == "write":
            dev_addr = dev_addr << 1
        else:
            dev_addr = (dev_addr << 1) | 0x1

        self.udp_rdma_write(tx_fifo_dict['addr'], [dev_addr], burst_len=1, cmd_no=cmd_no,
                            comment=tx_fifo_dict['description'])
        # Enable Transmission
        cr_reg = self.udp_rdma_read(cr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                    comment=cr_dict['description'])[0]
        cr_reg = set_field(cr_dict, "TX", cr_reg, 1)
        cr_reg = set_field(cr_dict, "MSMS", cr_reg, 1)
        cr_reg = set_field(cr_dict, "EN", cr_reg, 1)
        self.udp_rdma_write(cr_dict['addr'], [cr_reg], burst_len=1, cmd_no=cmd_no,
                            comment=cr_dict['description'])

        if not self._poll_iic_isr_flag("INT_2", idx=idx, operation="write device addr",
                                       dev_addr=dev_addr, cmd_no=cmd_no, attempts=1000): return 0

        # Stop Transmission and send byte (this order matches corresponding Tcl code)
        cr_reg = self.udp_rdma_read(cr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                    comment=cr_dict['description'])[0]
        cr_reg = clr_field(cr_dict, "MSMS", cr_reg)
        self.udp_rdma_write(cr_dict['addr'], [cr_reg], burst_len=1, cmd_no=cmd_no,
                            comment=cr_dict['description'])
        self.udp_rdma_write(tx_fifo_dict['addr'], [b], burst_len=1, cmd_no=cmd_no,
                            comment=tx_fifo_dict['description'])

        if not self._poll_iic_isr_flag("INT_2", idx=idx, operation="write byte",
                                       dev_addr=dev_addr, cmd_no=cmd_no, attempts=1000): return 0
        # clear Tx FIFO and completed interrupts:
        isr_reg = self.udp_rdma_read(isr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                     comment=isr_dict['description'])[0]
        # Clear an ISR INT by writing to the location:
        # isr_reg = clr_field(isr_dict, "INT_2", isr_reg)
        isr_reg = set_field(isr_dict, "INT_2", isr_reg, 1)
        self.udp_rdma_write(isr_dict['addr'], [isr_reg], burst_len=1, cmd_no=cmd_no,
                            comment=isr_dict['description'])
        return 1


    def _reset_axi_iic(self, idx=1, cmd_no=0):
        softr_dict = iic_qsfp_module_sel("SOFTR", idx=idx)
        SOFTR_KEY = 0xA
        self.udp_rdma_write(softr_dict['addr'], [SOFTR_KEY], burst_len=1, cmd_no=cmd_no,
                            comment=softr_dict['description'])
        return 1


    def _init_axi_iic(self, idx=1, cmd_no=0):
        ISR_CLR_MASK = 0xFF
        ISR_INIT_VAL = 0xD0 # mask for INT_0, INT_2 and INT_3
        SR_INIT_VAL = 0xC0 # mask for INT_2 and INT_3

        cr_dict = iic_qsfp_module_sel("CTRL_REG", idx=idx)
        isr_dict = iic_qsfp_module_sel("ISR", idx=idx)
        sr_dict = iic_qsfp_module_sel("STAT_REG", idx=idx)

        self._reset_axi_iic(idx=idx, cmd_no=cmd_no)
        cr_reg = self.udp_rdma_read(cr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                    comment=cr_dict['description'])[0]
        cr_reg = set_field(cr_dict, "EN", cr_reg, 1)
        self.udp_rdma_write(cr_dict['addr'], [cr_reg], burst_len=1, cmd_no=cmd_no,
                            comment=cr_dict['description'])

        isr = self.udp_rdma_read(isr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                 comment=isr_dict['description'])[0]
        isr_clr = isr & ISR_CLR_MASK
        self.udp_rdma_write(isr_dict['addr'], [isr_clr], burst_len=1, cmd_no=cmd_no,
                            comment=isr_dict['description'])
        isr = self.udp_rdma_read(isr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                 comment=isr_dict['description'])[0]
        if isr != ISR_INIT_VAL:
            print(f"[ERROR] IIC initialisation failed. Incorrect ISR response, expected: {hex(ISR_INIT_VAL)}, got: {hex(isr)}")
            return 0
        sr = self.udp_rdma_read(sr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                comment=sr_dict['description'])[0]
        if sr != SR_INIT_VAL:
            print(f"[ERROR] IIC initialisation failed. Incorrect SR response, expected: {hex(SR_INIT_VAL)}, got: {hex(sr)}")
            return 0
        return 1


    def _check_iic_module_exists(self, idx=1, dev_addr=0x50, cmd_no=0):
        return self._iic_write_byte(1, idx=idx, op="WRITE", dev_addr=dev_addr, cmd_no=cmd_no)


    def _get_iic_module_info(self, idx=1, dev_addr=0x50, cmd_no=0):
        MAX_CHUNK = 16
        BASE_ID_OFFSET = 0x81
        base_id = list()
        BASE_ID_LENGTH = 63
        EXTENDED_ID_OFFSET = 0xC0
        EXTENDED_ID_LENGTH = 32
        VENDOR_SPECIFIC_ID_OFFSET = 0xF4
        VENDOR_SPECIFIC_ID_LENGTH = 32
        self._init_axi_iic(idx=idx, cmd_no=cmd_no)
        mod_present = self._check_iic_module_exists(idx=idx, dev_addr=dev_addr, cmd_no=cmd_no)
        if mod_present:
            print(f"[INFO]: <{hex(dev_addr)}> IIC device found")
        else:
            print(f"[ERROR]: <{hex(dev_addr)}> No IIC device found")
            return 0

        i = 0
        size = 63
        perph_addr = BASE_ID_OFFSET
        while i < size:
            chunk = MAX_CHUNK if (size - i) > MAX_CHUNK else (size - i)
            print(f"[DEBUG]: size: {size} | i: {i} | chunk size: {chunk} | perph_addr: {hex(perph_addr)}")
            if chunk > 1:
                base_id.extend(self._iic_read(perph_addr, idx=idx, size=chunk - 1, dev_addr=dev_addr, cmd_no=cmd_no))
            i += chunk
            perph_addr += chunk

        print(f"[INFO] Base ID: {base_id}")
        string = ""
        for i in base_id:
           string += chr(i)
        print(f"[INFO]: Base ID: {string}")
        print(f"[DEBUG]: Base ID length: {len(base_id)}")

    def _iic_read(self, addr, idx=1, size=16, dev_addr=0x50, cmd_no=0):
        rd_data = list()

        cr_dict = iic_qsfp_module_sel("CTRL_REG", idx=idx)
        isr_dict = iic_qsfp_module_sel("ISR", idx=idx)
        rx_fifo_pirq_dict = iic_qsfp_module_sel("RX_FIFO_PIRQ", idx=idx)
        tx_fifo_dict = iic_qsfp_module_sel("TX_FIFO", idx=idx)

        # from: https://docs.xilinx.com/v/u/2.0-English/pg090-axi-iic PG090 v2.0 (page 33)
        # IIC Master Receiver with a Repeated Start
        # 1
        self._iic_write_byte(addr, idx=idx, op="WRITE", dev_addr=dev_addr, cmd_no=cmd_no)
        self.udp_rdma_write(rx_fifo_pirq_dict['addr'], [size - 2], burst_len=1, cmd_no=cmd_no,
                            comment=rx_fifo_pirq_dict['description'])
        self.udp_rdma_write(tx_fifo_dict['addr'], [(dev_addr << 1) | 0x1], burst_len=1, cmd_no=cmd_no,
                            comment=tx_fifo_dict['description'])
        # 2 CR MSMS = 1 CR Tx = 0
        cr_reg = self.udp_rdma_read(cr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                    comment=cr_dict['description'])[0]
        cr_reg = clr_field(cr_dict, "TX", cr_reg)
        cr_reg = set_field(cr_dict, "MSMS", cr_reg, 1)
        self.udp_rdma_write(cr_dict['addr'], [cr_reg], burst_len=1, cmd_no=cmd_no,
                            comment=cr_dict['description'])
        # 3
        if not self._poll_iic_isr_flag("INT_3", idx=idx, operation="read byte(s)",
                                       dev_addr=dev_addr, cmd_no=cmd_no, attempts=1000): return 0
        # 4
        cr_reg = self.udp_rdma_read(cr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                    comment=cr_dict['description'])[0]
        cr_reg = set_field(cr_dict, "TXAK", cr_reg, 1)
        self.udp_rdma_write(cr_dict['addr'], [cr_reg], burst_len=1, cmd_no=cmd_no,
                            comment=cr_dict['description'])
        # 5-10 not impletemented skip to
        # 11
        rd_data.extend(self._iic_read_fifo(size - 1, idx=idx, cmd_no=cmd_no))
        self.udp_rdma_write(rx_fifo_pirq_dict['addr'], 0, burst_len=1, cmd_no=cmd_no,
                            comment=rx_fifo_pirq_dict['description'])
        rd_data.extend(self._iic_read_fifo(1, idx=idx, cmd_no=cmd_no))

        isr_reg = self.udp_rdma_read(isr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                     comment=isr_dict['description'])[0]
        isr_reg = set_field(isr_dict, "INT_3", isr_reg, 1)
        self.udp_rdma_write(isr_dict['addr'], [isr_reg], burst_len=1, cmd_no=cmd_no,
                            comment=isr_dict['description'])
        # 12
        if not self._poll_iic_isr_flag("INT_3", idx=idx, operation="read final byte(s)",
                                       dev_addr=dev_addr, cmd_no=cmd_no, attempts=1000): return 0
        # 13
        cr_reg = self.udp_rdma_read(cr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                    comment=cr_dict['description'])[0]
        cr_reg = clr_field(cr_dict, "MSMS", cr_reg)
        self.udp_rdma_write(cr_dict['addr'], [cr_reg], burst_len=1, cmd_no=cmd_no,
                            comment=cr_dict['description'])
        # 14
        rd_data.extend(self._iic_read_fifo(1, idx=idx, cmd_no=cmd_no))
        return rd_data

    def _poll_iic_isr_flag(self, isr, idx=1, operation="", dev_addr=0x50, cmd_no=0, attempts=1000):
        """
        """
        isr_dict = iic_qsfp_module_sel("ISR", idx=idx)

        isr_reg = self.udp_rdma_read(isr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                     comment=isr_dict['description'])[0]
        rx_fifo_not_full = not decode_field(isr_dict, isr, isr_reg)
        timeout_attempt = 0
        while rx_fifo_not_full:
            if timeout_attempt == attempts - 1:
                print(f"[ERROR] <{hex(dev_addr)}> IIC device failed to respond to {operation}.")
                print(f"[ERROR]:    <ISR> response: {hex(isr_reg)} ")
                return 0
            else:
                isr_reg = self.udp_rdma_read(isr_dict['addr'], burst_len=1, cmd_no=cmd_no,
                                             comment=isr_dict['description'])[0]
                rx_fifo_not_full = not decode_field(isr_dict, isr, isr_reg)
                timeout_attempt += 1
        return 1
