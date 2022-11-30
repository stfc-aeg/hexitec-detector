"""
Test Cases for the Hexitec RdmaUDP in hexitec.

Christian Angelsen, STFC Detector Systems Software Group
"""

from socket import error as socket_error
from hexitec.RdmaUDP import RdmaUDP

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
        self.UDPMTU = 9000
        with patch("hexitec.RdmaUDP.socket"):
            self.rdma = RdmaUDP(self.master_ip, self.master_port,
                                self.target_ip, self.target_port,
                                self.UDPMTU, 0.5, debug=True,
                                unique_cmd_no=False)
        self.tx_old_sock = self.rdma.socket

        self.socket = Mock()
        self.test_data = 8
        self.test_address = 256
        self.burst_len = 1
        self.cmd_no = 0
        self.op_code = 1    # 0 = write, 1 = read
        return_struct = struct.pack('=HBBIII', self.burst_len, self.cmd_no, self.op_code, self.test_address, self.test_data, 0)
        self.socket.recv = Mock(return_value=return_struct)
        self.rdma.socket = self.socket

        self.rdma.ack = True
        self.rdma.setDebug()


@pytest.fixture
def test_rdma():
    """Test Fixture for testing the RdmaUDP."""
    test_rdma = RdmaUDPTestFixture()
    yield test_rdma


class TestRdmaUDP():
    """Test suit."""

    def test_init(self, test_rdma):
        """Tests that the socket of the RDMA were bound correctly."""
        test_rdma.tx_old_sock.bind.assert_called_with(
            (test_rdma.master_ip, test_rdma.master_port)
        )

    def test_connect_socket_fails(self, test_rdma):
        """Test unavailable IP will throw socket error."""
        with patch('hexitec.HexitecFem.RdmaUDP') as rdma_mock:
            rdma_mock.side_effect = socket_error()
            with pytest.raises(socket_error) as exc_info:
                self.rdma = RdmaUDP(test_rdma.fake_ip, test_rdma.master_port,
                                    test_rdma.target_ip, test_rdma.master_port,
                                    UDPMTU=test_rdma.UDPMTU, debug=True,
                                    unique_cmd_no=False)
            e = "Error: [Errno 99] Cannot assign requested address"
            assert exc_info.type is socket_error
            assert exc_info.value.args[0] == e

    def test_read_single_register(self, test_rdma):
        """Test that the read method can handle reading a single register."""
        read_command = struct.pack('=HBBI', test_rdma.burst_len, test_rdma.cmd_no,
                                    test_rdma.op_code, test_rdma.test_address)

        data = test_rdma.rdma.read(test_rdma.test_address)
        test_rdma.socket.sendto.assert_called_with(read_command,
                                                      (test_rdma.target_ip, test_rdma.target_port))
        test_rdma.socket.recv.assert_called_with(test_rdma.UDPMTU)
        # Read out data will be tuple of one member (given burst_len=1)
        assert data[0] == test_rdma.test_data

    # TODO: AMEND, TEST
    def test_read_two_registers(self, test_rdma):
        """Test that the read method can handle reading two registers."""
        # read_command = struct.pack('=HBBI', test_rdma.burst_len, test_rdma.cmd_no,
        #                             test_rdma.op_code, test_rdma.test_address)

        # data = test_rdma.rdma.read(test_rdma.test_address)
        # test_rdma.socket.sendto.assert_called_with(read_command,
        #                                               (test_rdma.target_ip, test_rdma.target_port))
        # test_rdma.socket.recv.assert_called_with(test_rdma.UDPMTU)
        # # Read out data will be tuple of one member (given burst_len=1)
        # assert data[0] == test_rdma.test_data

    def test_write(self, test_rdma):
        """Test that the write method calls the relevant socket methods correctly."""
        burst_len = 1
        cmd_no = 0
        op_code = 0     # 0 = write, 1 = read
        test_address = 256
        test_data = 8
        write_command = struct.pack('=HBBII', test_rdma.burst_len, test_rdma.cmd_no, op_code,
                                    test_rdma.test_address, test_rdma.test_data)

        test_rdma.rdma.write(test_rdma.test_address, test_rdma.test_data)
        test_rdma.socket.sendto.assert_called_with(write_command,
                                                      (test_rdma.target_ip, test_rdma.target_port))
    # #     assert test_rdma.rdma.ack is True
    #     #test_rdma ?????
    #     self.socket = Mock()
    #     return_struct = struct.pack('=HBBIII', burst_len, cmd_no, op_code, test_address, test_data, 0)
    #     self.socket.recv = Mock(return_value=return_struct)
    #     self.rdma.socket = self.socket

# #
# from path import Path

# def sanitize_line_ending(filename):
#     """ Converts the line endings of the file to the line endings
#         of the current system.
#     """
#     input_path = Path(filename)

#     with input_path.in_place() as (reader, writer):
#         for line in reader:
#             writer.write(line)
# #
# @mock.patch('downloader.helpers.Path')
# def test_sanitize_line_endings(self, mock_path):
#     mock_path.return_value.in_place.return_value = (1,2)
#     helpers.sanitize_line_ending('varun.txt')
# #
#     # TODO: Fix after reading: https://stackoverflow.com/questions/31477825/unable-to-return-a-tuple-when-mocking-a-function
#     # TODO: The above 18 lines forms part of the same example
#     def test_read_uart_status(self, test_rdma):
#         """Test function works ok."""
#         # self.test_fem.fem.set_debug(True)
# #  uart_status: (853266,)
# # 00084 UART: 000D0512 tx_buff_full: 0 tx_buff_empty: 1 rx_buff_full: 0 rx_buff_empty: 0 rx_pkt_done: 1
#         test_rdma.rdma.
#         read_values = tuple((853266, 0))
#         # test_rdma.rdma.write(test_rdma.test_address, test_rdma.test_data
#         test_rdma.rdma.read = Mock()
#         test_rdma.rdma.read.side_effect = read_values

#         address = 0x10
#         burst_len=1
#         comment="Read UART Status"
#         returned_values = test_rdma.rdma.read_uart_status()
#         expected_values = (0x000D0512, 0, 1, 0, 0, 1)
#         test_rdma.rdma.read.assert_called_with(address, burst_len=1, comment='Read UART Status')
#         assert returned_values == expected_values

    # TODO: how to mock socket.sendto exception?
#     def test_write_handles_socket_exception(self, test_rdma):
#         """Test that the write method handles a socket exception."""
#         op_code = 0     # 0 = write, 1 = read
#         write_command = struct.pack('=HBBII', test_rdma.burst_len, test_rdma.cmd_no, op_code,
#                                     test_rdma.test_address, test_rdma.test_data)
# #
#         with patch('socket.socket') as rdma_mock:
#             rdma_mock.sendto.return_value = socket_error()
#             with pytest.raises(socket_error) as exc_info:
#                 test_rdma.rdma.write(test_rdma.test_address, test_rdma.test_data)
#             e = "Error"
#             assert exc_info.type is socket_error
#             assert exc_info.value.args[0] == e
# #
#         # test_rdma.socket.sendto.assert_called_with(write_command,
#         #                                               (test_rdma.target_ip, test_rdma.target_port))

    # def test_close(self, test_rdma):
    #     """Test sockets closed."""
    #     test_rdma.rdma.close()
    #     # TODO: rdma Mock object, amend to check sockets shut?
    #     # assert test_rdma.rdma.rxsocket._closed is True
    #     # assert test_rdma.rdma.txsocket._closed is True
