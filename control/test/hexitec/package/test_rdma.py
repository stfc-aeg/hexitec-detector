"""Test Cases for the Hexitec RdmaUDP in hexitec.

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
        self.master_port = 8888
        self.target_ip = "127.0.0.2"
        self.fake_ip = "199.192.105.5"
        self.target_port = 8080
        self.UDPMTU = 8000
        with patch("hexitec.RdmaUDP.socket"):
            self.rdma = RdmaUDP(self.master_ip, self.master_port,
                                self.master_ip, self.master_port,
                                self.target_ip, self.target_port,
                                self.target_ip, self.target_port,
                                UDPMTU=self.UDPMTU)
        self.tx_old_sock = self.rdma.txsocket
        self.rx_old_sock = self.rdma.rxsocket

        self.tx_socket = Mock()
        self.rx_socket = Mock()
        self.return_data = 256
        return_struct = struct.pack('=IIIIQQQQQ', 5, 7, 5, self.return_data, 0, 0, 0, 0, 10)
        self.rx_socket.recv = Mock(return_value=return_struct)
        self.rdma.txsocket = self.tx_socket
        self.rdma.rxsocket = self.rx_socket

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
        """Tests that the sockets of the RDMA were bound correctly."""
        test_rdma.rx_old_sock.bind.assert_called_with(
            (test_rdma.master_ip, test_rdma.master_port)
        )
        test_rdma.tx_old_sock.bind.assert_called_with(
            (test_rdma.master_ip, test_rdma.master_port)
        )

    def test_connect_tx_socket_fails(self, test_rdma):
        """Test unavailable IP will throw socket error."""
        with patch('hexitec.HexitecFem.RdmaUDP') as rdma_mock:
            rdma_mock.side_effect = socket_error()
            with pytest.raises(socket_error) as exc_info:
                self.rdma = RdmaUDP(test_rdma.fake_ip, test_rdma.master_port,
                                    test_rdma.target_ip, test_rdma.master_port,
                                    test_rdma.target_ip, test_rdma.target_port,
                                    test_rdma.target_ip, test_rdma.target_port,
                                    UDPMTU=test_rdma.UDPMTU)
            error_message = "[Errno 99] Cannot assign requested address"
            e = "Transmit socket IP:Port {}:8888 {}".format(test_rdma.fake_ip, error_message)
            assert exc_info.type is socket_error
            assert exc_info.value.args[0] == e

    def test_connect_rx_socket_fails(self, test_rdma):
        """Test unavailable IP will throw socket error."""
        with patch('hexitec.HexitecFem.RdmaUDP') as rdma_mock:
            rdma_mock.side_effect = socket_error()
            with pytest.raises(socket_error) as exc_info:
                self.rdma = RdmaUDP(test_rdma.master_ip, test_rdma.master_port,
                                    test_rdma.fake_ip, test_rdma.master_port,
                                    test_rdma.target_ip, test_rdma.target_port,
                                    test_rdma.target_ip, test_rdma.target_port,
                                    UDPMTU=test_rdma.UDPMTU)
            error_message = "[Errno 99] Cannot assign requested address"
            e = "Receive socket IP:Port {}:8888 {}".format(test_rdma.fake_ip, error_message)
            assert exc_info.type is socket_error
            assert exc_info.value.args[0] == e

    def test_read(self, test_rdma):
        """Test that the read method calls the relevant socket methods correctly."""
        test_address = 256
        read_command = struct.pack('=BBBBIQBBBBIQQQQQ', 1, 0, 0, 3, test_address,
                                   0, 9, 0, 0, 255, 0, 0, 0, 0, 0, 0)

        data = test_rdma.rdma.read(test_address)
        test_rdma.tx_socket.sendto.assert_called_with(read_command,
                                                      (test_rdma.target_ip, test_rdma.target_port))
        test_rdma.rx_socket.recv.assert_called_with(test_rdma.UDPMTU)
        assert data == test_rdma.return_data

    def test_write(self, test_rdma):
        """Test that the write method calls the relevant socket methods correctly."""
        test_address = 256
        test_data = 1024
        write_command = struct.pack('=BBBBIQBBBBIQQQQQ', 1, 0, 0, 2, test_address,
                                    test_data, 9, 0, 0, 255, 0, 0, 0, 0, 0, 0)

        test_rdma.rdma.write(test_address, test_data)
        test_rdma.tx_socket.sendto.assert_called_with(write_command,
                                                      (test_rdma.target_ip, test_rdma.target_port))

        assert test_rdma.rdma.ack is True

    def test_close(self, test_rdma):
        """Test sockets closed."""
        test_rdma.rdma.close()
        # TODO: rdma Mock object, amend to check sockets shut?
        # assert test_rdma.rdma.rxsocket._closed is True
        # assert test_rdma.rdma.txsocket._closed is True
