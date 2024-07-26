"""
Test Cases for the Hexitec RdmaUDP in hexitec.

Christian Angelsen, STFC Detector Systems Software Group
"""

from socket import error as socket_error
from RdmaUdp import *

import pytest
import struct
import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
else:                         # pragma: no cover
    from mock import Mock, patch


class RdmaUDPTestFixture(object):
    """Test fixture class."""

    def __init__(self):
        """Initialise object."""
        self.master_ip = "127.0.0.1"
        self.master_port = 61649
        self.target_ip = "127.0.0.2"
        self.fake_ip = "199.192.105.5"
        self.target_port = 61648
        self.UDPMTU = 12
        with patch("RdmaUdp.socket"):
            self.rdma = RdmaUDP(self.master_ip, self.master_port,
                                self.target_ip, self.target_port,
                                self.UDPMTU, udptimeout=5,
                                speed="10G", uart_offset=0x0,
                                debug=True)

        self.socket = Mock()
        self.test_data = 8
        self.test_address = 256
        self.burst_len = 1
        self.cmd_no = 0
        self.op_code = 1    # 0 = write, 1 = read
        return_struct = struct.pack('=HBBLI', self.burst_len, self.cmd_no, self.op_code,
                                    self.test_address, self.test_data)
        self.socket.recv = Mock(return_value=return_struct)
        self.rdma.socket = self.socket


@pytest.fixture
def test_rdma():
    """Test Fixture for testing the RdmaUDP."""
    test_rdma = RdmaUDPTestFixture()
    yield test_rdma


class TestRdmaUDP():
    """Test suit."""

    # TODO Fix?
    # def test_init(self, test_rdma):
    #     """Tests that the socket of the RDMA were bound correctly."""
    #     print(" speed? ", test_rdma.rdma.speed)
    #     print("  rdma_ip: ", test_rdma.rdma.rdma_ip)
    #     test_rdma.socket.bind.assert_called_with(
    #         (test_rdma.master_ip, test_rdma.master_port)
    #     )

    def test_connect_socket_fails(self, test_rdma):
        """Test unavailable IP will throw socket error."""
        with patch("hexitec.HexitecFem.RdmaUDP") as rdma_mock:
            rdma_mock.side_effect = socket_error()
            udptimeout = 5
            with pytest.raises(socket_error) as exc_info:
                self.rdma = RdmaUDP(test_rdma.fake_ip, test_rdma.master_port,
                                    test_rdma.target_ip, test_rdma.master_port,
                                    test_rdma.UDPMTU, udptimeout, "10G", 0x0,
                                    debug=True)
            e = "Error: [Errno 99] Cannot assign requested address"
            assert exc_info.type is socket_error
            assert exc_info.value.args[0] == e

    def test_read_single_register(self, test_rdma):
        """Test the read method handles reading a single register."""
        read_command = struct.pack('=HBBI', test_rdma.burst_len, test_rdma.cmd_no,
                                   test_rdma.op_code, test_rdma.test_address)
        data = test_rdma.rdma.udp_rdma_read(test_rdma.test_address)
        test_rdma.socket.sendto.assert_called_with(read_command,
                                                   (test_rdma.target_ip, test_rdma.target_port))
        test_rdma.socket.recv.assert_called_with(test_rdma.UDPMTU)
        # Read out data will be tuple of one member (given burst_len=1)
        assert data[0] == test_rdma.test_data

    def test_read_handles_write_socket_error(self, test_rdma):
        """Test the read method handles a write socket exception."""
        read_command = struct.pack('=HBBI', test_rdma.burst_len, test_rdma.cmd_no,
                                   test_rdma.op_code, test_rdma.test_address)
        test_rdma.socket.sendto = Mock()
        test_rdma.socket.sendto.side_effect = socket_error()
        with pytest.raises(socket_error) as exc_info:
            test_rdma.rdma.udp_rdma_read(test_rdma.test_address)
        test_rdma.socket.sendto.assert_called_with(
            read_command, (test_rdma.rdma.rdma_ip, test_rdma.rdma.rdma_port))
        assert exc_info.type is socket_error

    # TODO Fix?
#     def test_read_handles_struct_error(self, test_rdma):
#         """Test the read method handles struct error."""
#         burst_len = 3
#         read_command = struct.pack('=HBBI', burst_len, test_rdma.cmd_no,
#                                    test_rdma.op_code, test_rdma.test_address)
#         with pytest.raises(struct.error) as exc_info:
#             test_rdma.rdma.udp_rdma_read(test_rdma.test_address, burst_len=burst_len)
#         test_rdma.socket.sendto.assert_called_with(
#             read_command, (test_rdma.rdma.rdma_ip, test_rdma.rdma.rdma_port))
#         test_rdma.socket.recv.assert_called_with(test_rdma.rdma.UDPMTU)
#         assert exc_info.type is struct.error
#         assert str(exc_info.value.args[0]) == f"expected {burst_len}, received {2} words!"

    def test_read_handles_read_socket_error(self, test_rdma):
        """Test the read method handles a read socket exception."""
        read_command = struct.pack('=HBBI', test_rdma.burst_len, test_rdma.cmd_no,
                                   test_rdma.op_code, test_rdma.test_address)
        test_rdma.socket.sendto = Mock()
        test_rdma.socket.recv = Mock()
        test_rdma.socket.recv.side_effect = socket_error()
        with pytest.raises(socket_error) as exc_info:
            test_rdma.rdma.udp_rdma_read(test_rdma.test_address)
        assert exc_info.type is socket_error
        test_rdma.socket.sendto.assert_called_with(
            read_command, (test_rdma.rdma.rdma_ip, test_rdma.rdma.rdma_port))

#     # # TODO: AMEND, TEST - Test case when padding = 0?
#     # def test_read_two_registers(self, test_rdma):
#     #     """Test the read method handles reading two registers."""
#     #     # read_command = struct.pack('=HBBI', test_rdma.burst_len, test_rdma.cmd_no,
#     #     #                             test_rdma.op_code, test_rdma.test_address)

#     #     # data = test_rdma.rdma.udp_rdma_read(test_rdma.test_address)
#     #     # test_rdma.socket.sendto.assert_called_with(
#     #     #     read_command, (test_rdma.target_ip, test_rdma.target_port))
#     #     # test_rdma.socket.recv.assert_called_with(test_rdma.UDPMTU)
#     #     # # Read out data will be tuple of one member (given burst_len=1)
#     #     # assert data[0] == test_rdma.test_data

    # TODO Fix?
    # def test_write(self, test_rdma):
    #     """Test the write method works ok."""
    #     op_code = 0     # 0 = write, 1 = read
    #     write_command = struct.pack('=HBBII', test_rdma.burst_len, test_rdma.cmd_no, op_code,
    #                                 test_rdma.test_address, test_rdma.test_data)
    #     test_rdma.rdma.udp_rdma_write(test_rdma.test_address, test_rdma.test_data)
    #     test_rdma.socket.sendto.assert_called_with(write_command,
    #                                                (test_rdma.target_ip, test_rdma.target_port))
    #     test_rdma.socket.recv.assert_called_with(test_rdma.UDPMTU)

    def test_write_handles_write_socket_error(self, test_rdma):
        """Test the write method handles write socket error."""
        op_code = 0     # 0 = write, 1 = read
        write_command = struct.pack('=HBBII', test_rdma.burst_len, test_rdma.cmd_no, op_code,
                                    test_rdma.test_address, test_rdma.test_data)

        test_rdma.socket.sendto = Mock()
        test_rdma.socket.sendto.side_effect = socket_error()
        with pytest.raises(socket_error) as exc_info:
            test_rdma.rdma.udp_rdma_write(test_rdma.test_address, test_rdma.test_data)
        assert exc_info.type is socket_error
        test_rdma.socket.sendto.assert_called_with(write_command,
                                                   (test_rdma.target_ip, test_rdma.target_port))

    def test_write_handles_read_socket_error(self, test_rdma):
        """Test the write method handles read socket error."""
        op_code = 0     # 0 = write, 1 = read
        write_command = struct.pack('=HBBII', test_rdma.burst_len, test_rdma.cmd_no, op_code,
                                    test_rdma.test_address, test_rdma.test_data)

        test_rdma.socket.sendto = Mock()
        test_rdma.socket.recv = Mock()
        test_rdma.socket.recv.side_effect = socket_error()
        test_rdma.ack = False
        test_rdma.debug = False
        with pytest.raises(socket_error) as exc_info:
            test_rdma.rdma.udp_rdma_write(test_rdma.test_address, test_rdma.test_data)
        assert exc_info.type is socket_error
        test_rdma.socket.sendto.assert_called_with(write_command,
                                                   (test_rdma.target_ip, test_rdma.target_port))
        test_rdma.socket.recv.assert_called_with(8)

    def test_write_handles_read_struct_error(self, test_rdma):
        """Test the write method handles read struct error."""
        op_code = 0     # 0 = write, 1 = read
        write_command = struct.pack('=HBBII', test_rdma.burst_len, test_rdma.cmd_no, op_code,
                                    test_rdma.test_address, test_rdma.test_data)

        test_rdma.socket.sendto = Mock()
        test_rdma.socket.recv = Mock()
        test_rdma.socket.recv.side_effect = struct.error()
        test_rdma.rdma.ack = False
        test_rdma.rdma.debug = False
        with pytest.raises(struct.error) as exc_info:
            test_rdma.rdma.udp_rdma_write(test_rdma.test_address, test_rdma.test_data)
        assert exc_info.type is struct.error
        test_rdma.socket.sendto.assert_called_with(write_command,
                                                   (test_rdma.target_ip, test_rdma.target_port))
        test_rdma.socket.recv.assert_called_with(8)

# # #
# # from path import Path

# # def sanitize_line_ending(filename):
# #     """ Converts the line endings of the file to the line endings
# #         of the current system.
# #     """
# #     input_path = Path(filename)

# #     with input_path.in_place() as (reader, writer):
# #         for line in reader:
# #             writer.write(line)
# # #
# # @mock.patch('downloader.helpers.Path')
# # def test_sanitize_line_endings(self, mock_path):
# #     mock_path.return_value.in_place.return_value = (1,2)
# #     helpers.sanitize_line_ending('varun.txt')
# # #
# #     # TODO: Fix after reading:
# # https://stackoverflow.com/questions/31477825/unable-to-return-a-tuple-when-mocking-a-function
# #     # TODO: The above 18 lines forms part of the same example
# #     def test_read_uart_status(self, test_rdma):
# #         """Test function works ok."""
# #         # self.test_fem.fem.set_debug(True)
# # #  uart_status: (853266,)
# # # 00084 UART: 000D0512 tx_buff_full: 0 tx_buff_empty: 1 rx_buff_full: 0 rx_buff_empty: 0
# # #             rx_pkt_done: 1
# #         test_rdma.rdma.
# #         read_values = tuple((853266, 0))
# #         # test_rdma.rdma.udp_rdma_write(test_rdma.test_address, test_rdma.test_data
# #         test_rdma.rdma.udp_rdma_read = Mock()
# #         test_rdma.rdma.udp_rdma_read.side_effect = read_values

# #         address = 0x10
# #         burst_len=1
# #         comment="Read UART Status"
# #         returned_values = test_rdma.rdma.udp_rdma_read_uart_status()
# #         expected_values = (0x000D0512, 0, 1, 0, 0, 1)
# #         test_rdma.rdma.udp_rdma_read.assert_called_with(
# #             address, burst_len=1, comment='Read UART Status')
# #         assert returned_values == expected_values

    # TODO Fix when UART polling ported
    # def test_read_uart_status_handles_exception(self, test_rdma):
    #     """Test function works ok."""
    #     e = "Oops"
    #     test_rdma.rdma.udp_rdma_read = Mock()
    #     test_rdma.rdma.udp_rdma_read.side_effect = Exception(e)
    #     msg = "read_uart_status: {}".format(e)
    #     with pytest.raises(Exception) as exc_info:
    #         test_rdma.rdma.read_uart_status()
    #     assert exc_info.type is Exception
    #     assert exc_info.value.args[0] == msg

    def test_close(self, test_rdma):
        """Test socket's closed."""
        test_rdma.rdma.socket.close = Mock()
        test_rdma.rdma.close()
        test_rdma.rdma.socket.close.assert_called()
