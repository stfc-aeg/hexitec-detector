"""
Test Cases for the Hexitec Fem in hexitec.

Christian Angelsen, STFC Detector Systems Software Group
"""

import asyncio
import unittest
import pytest
import os

from odin.adapters.parameter_tree import ParameterTreeError
from hexitec.HexitecFem import HexitecFem, HexitecFemError
from hexitec.adapter import HexitecAdapter

from socket import error as socket_error
from datetime import datetime
from datetime import timezone
import socket

from unittest.mock import Mock, call, patch, mock_open, MagicMock


# Custom decorator to support testing of asynchronous functions
def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


class FemTestFixture(object):
    """Set up a text fixture."""

    def __init__(self):
        """Initialise object."""
        cwd = os.getcwd()
        base_path_index = cwd.rfind("control")  # i.e. /path/to/hexitec-detector
        repo_path = cwd[:base_path_index - 1]
        self.data_config_path = repo_path + "/data/config/"
        self.control_config_path = cwd + "/test/hexitec/config/"
        self.options = {
            "control_config": f"{self.control_config_path}",
            "fem":
                """
                farm_mode = /some/config.json
                """
        }

        self.config = {
            "farm_mode": "/some/config.json"
        }

        with patch("hexitec.HexitecDAQ.ParameterTree"):
            self.adapter = HexitecAdapter(**self.options)
            self.detector = self.adapter.hexitec  # shortcut, makes assert lines shorter

            with patch("hexitec.HexitecFem.RdmaUDP"):
                self.fem = HexitecFem(self.detector, self.config)
                self.fem.connect()


class TestFem(unittest.TestCase):
    """Unit tests for the fem class."""

    def setUp(self):
        """Set up test fixture for each unit test."""
        self.test_fem = FemTestFixture()
        farm_mode_json = {
            "camera_ctrl_ip": "10.0.1.100",
            "camera_ctrl_mac": "62:00:00:00:01:0A",
            "server_ctrl_port": "61649",
            "camera_ctrl_port": "61648",
            "control_interface": "lo",
            "control_lane": "1",
            "data1_interface": "lo",
            "data1_lane": "2",
            "data2_interface": "lo",
            "data2_lane": "3",
            "farm_server_1_ip": "10.0.1.2",
            "farm_server_1_mac": "5c:6f:69:f8:57:d0",
            "farm_camera_1_ip": "10.0.1.101",
            "farm_camera_1_mac": "62:00:00:00:01:0B",
            "farm_server_2_ip": "10.0.1.3",
            "farm_server_2_mac": "5c:6f:69:f8:a3:e0",
            "farm_camera_2_ip": "10.0.1.102",
            "farm_camera_2_mac": "62:00:00:00:01:0C",
            "farm_target_ip": "10.0.1.2 10.0.1.3",
            "farm_target_mac": "5c:6f:69:f8:57:d0 5c:6f:69:f8:a3:e0",
            "farm_target_port": "61649 61649"
        }
        self.test_fem.fem.verify_parameters = False
        with patch("json.load") as mock_load:
            with patch("builtins.open", mock_open(read_data="data")):
                # self.test_fem.fem.verify_farm_mode_parameters = Mock()
                mock_load.return_value = farm_mode_json
                self.test_fem.fem.prepare_farm_mode()
        self.test_fem.fem.verify_parameters = True

    def tearDown(self):
        """Tear down test fixture after each unit test."""
        del self.test_fem

    def test_setup_farm_mode_fails(self):
        """Assert function's Exception handling works."""
        with patch("hexitec.HexitecFem.RdmaUDP") as rdma_mock:
            rdma_mock.side_effect = socket_error()
            self.test_fem.fem.data_lane1 = Mock()
            self.test_fem.fem.data_lane1.set_dst_ip.side_effect = socket_error()
            self.test_fem.fem.flag_error = Mock()
            Hex2x6Ctrl = Mock()
            ctrl_lane = Mock()
            # with pytest.raises(socket_error) as exc_info:
            self.test_fem.fem.setup_farm_mode(Hex2x6Ctrl, ctrl_lane)
            self.test_fem.fem.flag_error.assert_called_with("Farm Mode Config failed", "")

    def test_extract_frame_receiver_interface(self):
        """Test extracting frame receiver interface parameters from frameReceiver."""
        value = \
            [
                {
                    "ctrl_endpoint": "tcp://127.0.0.1:5110",
                    "decoder_path": "lib/",
                    "decoder_type": "Hexitec",
                    "frame_count": 0,
                    "frame_ready_endpoint": "tcp://127.0.0.1:5101",
                    "frame_release_endpoint": "tcp://127.0.0.1:5102",
                    "rx_address": "192.168.0.27",
                    "rx_address_list": "192.168.0.27, 130.246.17.170",
                    "rx_endpoint": "inproc://rx_channel",
                    "rx_ports": "61649,61649",
                    "rx_recv_buffer_size": 30000000,
                    "rx_type": "udp",
                    "shared_buffer_name": "HexitecFrameBuffer0"
                },
                {
                    "ctrl_endpoint": "tcp://127.0.0.1:5111",
                    "decoder_path": "lib/",
                    "decoder_type": "Hexitec",
                    "frame_count": 0,
                    "frame_ready_endpoint": "tcp://127.0.0.1:5201",
                    "frame_release_endpoint": "tcp://127.0.0.1:5202",
                    "max_buffer_mem": 500000000,
                    "rx_address": "192.168.0.27",
                    "rx_address_list": "192.168.0.27, 130.246.17.170",
                    "rx_endpoint": "inproc://rx_channel",
                    "rx_ports": "61651,61651",
                    "rx_recv_buffer_size": 30000000,
                    "rx_type": "udp",
                    "shared_buffer_name": "HexitecFrameBuffer1"
                },
                None
            ]
        addresses, ports = self.test_fem.fem.extract_frame_receiver_interfaces(value)
        assert addresses == ['192.168.0.27', '130.246.17.170', '192.168.0.27', '130.246.17.170']
        assert ports == [61649, 61649, 61651, 61651]

    def test_extract_entries_from_string(self):
        """Test extracting entries from space separated string."""
        test_string = "10.0.2.1,10.0.2.2,10.0.2.3"
        list_of_entries = []
        entries = self.test_fem.fem.extract_entries_from_string(test_string, list_of_entries)
        assert entries == ["10.0.2.1", "10.0.2.2", "10.0.2.3"]

    def test_extract_entries_from_string_handles_disconnected_fr(self):
        """Test function handles disconnected frameReceiver."""
        list_of_entries = ["testing"]
        entries = self.test_fem.fem.extract_entries_from_string(None, list_of_entries)
        assert entries == list_of_entries

    def test_connect(self):
        """Assert the connect method creates the rdma as expected."""
        with patch("hexitec.HexitecFem.RdmaUDP") as mock_rdma:
            self.test_fem.fem.server_ctrl_ip = '127.0.0.1'
            self.test_fem.fem.server_ctrl_port = 61649
            self.test_fem.fem.camera_ctrl_ip = '127.0.0.1'
            self.test_fem.fem.camera_ctrl_port = 61648
            self.test_fem.fem.connect()
            mock_rdma.assert_called_with(local_ip='127.0.0.1', local_port=61649,
                                         rdma_ip='127.0.0.1', rdma_port=61648,
                                         udptimeout=2, debug=False, uart_offset=0)

    def test_connect_fails(self):
        """Assert the connect method Exception handling works."""
        with patch("hexitec.HexitecFem.RdmaUDP") as rdma_mock:
            rdma_mock.side_effect = socket_error()
            with pytest.raises(socket_error) as exc_info:
                self.test_fem.fem.connect()
            assert exc_info.type is socket_error
            assert exc_info.value.args[0] == "Failed to setup Control connection: "

    def test_get_log_messages_display_new_messages(self):
        """Test the function displays new messages."""
        datestamp = self.test_fem.fem.create_iso_timestamp()
        log_messages = [(datestamp, 'Initialised OK.')]
        self.test_fem.fem.last_message_timestamp = "something"
        self.test_fem.fem.get_log_messages("")
        # Test part of timestamp, as milliseconds will not agree anyway
        assert self.test_fem.fem.log_messages[0][:-4] == log_messages[0][:-4]
        assert self.test_fem.fem.log_messages[0][1] == log_messages[0][1]

    def test_get_log_messages_display_all_messages(self):
        """Test the function displays all messages."""
        datestamp = self.test_fem.fem.create_iso_timestamp()
        log_messages = [(datestamp, 'Initialised OK.')]
        self.test_fem.fem.get_log_messages("")
        # Test part of timestamp, as milliseconds will not agree anyway
        assert self.test_fem.fem.log_messages[0][:-4] == log_messages[0][:-4]
        assert self.test_fem.fem.log_messages[0][1] == log_messages[0][1]

    def test_check_hardware_ready(self):
        """Test function working okay."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.flag_error = Mock()
        self.test_fem.fem.check_hardware_ready("test")
        self.test_fem.fem.flag_error.assert_not_called()

    def test_check_hardware_ready_fails_without_hardware_connection(self):
        """Test function fails when hardware not connected."""
        self.test_fem.fem.hardware_connected = False
        self.test_fem.fem.flag_error = Mock()
        error = "Can't test without a connection"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.check_hardware_ready("test")
        assert exc_info.value.args[0] == error

    def test_check_hardware_ready_fails_if_hardware_busy(self):
        """Test function fails when hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        self.test_fem.fem.flag_error = Mock()
        error = "Can't test, Hardware busy"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.check_hardware_ready("test")
        assert exc_info.value.args[0] == error
        self.test_fem.fem.flag_error.assert_called_with(error, "")

    def test_check_system_initialised(self):
        """Test function working ok."""
        self.test_fem.fem.system_initialised = True
        self.test_fem.fem._set_status_error = Mock()
        self.test_fem.fem.check_system_initialised("")
        self.test_fem.fem._set_status_error.assert_called_with("")

    def test_check_system_initialised_fails_if_system_not_initialised(self):
        """Test function fails if system not initialised."""
        self.test_fem.fem.system_initialised = False
        self.test_fem.fem.flag_error = Mock()
        reason = "test"
        error = f"Can't {reason}, system not initialised"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.check_system_initialised(reason)
        assert exc_info.value.args[0] == error
        self.test_fem.fem.flag_error.assert_called_with(error, "")

    def test_environs(self):
        """Test function works ok."""
        self.test_fem.fem.hardware_connected = True
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.environs()
            i = mock_loop.instance()
            i.add_callback.assert_called_with(self.test_fem.fem.read_sensors)

    def test_environs_fails_if_not_connected(self):
        """Test environs fails if no connection established."""
        self.test_fem.fem.hardware_connected = False
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.environs()
        error = "Can't read sensors without a connection"
        assert exc_info.value.args[0] == error
        assert exc_info.type is ParameterTreeError

    def test_environs_fails_if_hardware_busy(self):
        """Test environs fails if hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.environs()
        error = "Can't read sensors, Hardware busy"
        assert exc_info.value.args[0] == error
        assert exc_info.type is ParameterTreeError

    @patch('hexitec.HexitecFem.BoardCfgStatus')
    @async_test
    async def test_read_sensors_including_firmware_info(self, board_status):
        """Test the read_sensors function reads firmware info."""
        with patch("hexitec.HexitecFem.RdmaUDP"):
            self.test_fem.fem.read_firmware_version = True
            self.test_fem.fem.hardware_connected = True
            self.test_fem.fem.hardware_busy = False
            state = "this"
            self.test_fem.fem.parent.software_state = state
            self.test_fem.fem.parent.software_state == "Idle"
            self.test_fem.fem.x10g_rdma = Mock()
            self.test_fem.fem.read_temperatures_humidity_values = Mock()
            self.test_fem.fem.read_pwr_voltages = Mock()
            await self.test_fem.fem.read_sensors()
            assert self.test_fem.fem.environs_in_progress is False
            assert self.test_fem.fem.parent.software_state == state
            assert self.test_fem.fem.read_firmware_version is False
            # Ensure the three firmware version functions called
            board_status.return_value.get_fpga_fw_version.assert_called()
            board_status.return_value.get_fpga_build_date.assert_called()
            board_status.return_value.get_fpga_build_time.assert_called()

    @async_test
    async def test_read_sensors_Exception(self):
        """Test the read_sensors handles Exception."""
        with patch("hexitec.HexitecFem.RdmaUDP"):
            self.test_fem.fem.read_firmware_version = False
            self.test_fem.fem.hardware_connected = True
            self.test_fem.fem.hardware_busy = False
            self.test_fem.fem.read_temperatures_humidity_values = Mock()
            self.test_fem.fem.read_temperatures_humidity_values.side_effect = Exception()
            await self.test_fem.fem.read_sensors()
            error = "Reading sensors failed"
            assert self.test_fem.fem._get_status_error() == error

    @async_test
    async def test_read_sensors_HexitecFemError(self):
        """Test the read_sensors handles HexitecFemError."""
        with patch("hexitec.HexitecFem.RdmaUDP"):
            self.test_fem.fem.read_firmware_version = False
            self.test_fem.fem.hardware_connected = True
            self.test_fem.fem.hardware_busy = False
            self.test_fem.fem.read_temperatures_humidity_values = Mock()
            self.test_fem.fem.read_temperatures_humidity_values.side_effect = HexitecFemError()
            await self.test_fem.fem.read_sensors()
            error = "Failed to read sensors"
            assert self.test_fem.fem._get_status_error() == error
        assert self.test_fem.fem.parent.software_state == "Error"

    @patch('hexitec_vsr.VsrModule')
    def test_disconnect(self, mocked_vsr_module):
        """Test function working okay."""
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.broadcast_VSRs = mocked_vsr_module
        self.test_fem.fem.parent.leak_fault_counter = 1
        self.test_fem.fem.x10g_rdma = Mock()

        self.test_fem.fem.disconnect()
        self.test_fem.fem.x10g_rdma.close.assert_called()
        # Cannot test whether set_leak_detector () called because vsr(s) objects deleted
        # self.test_fem.fem.vsr_list[0].set_leak_detector_fault.assert_called()

    def test_cleanup(self):
        """Test cleanup function works ok."""
        self.test_fem.fem.cleanup()
        self.test_fem.fem.x10g_rdma.close.assert_called_with()

    def test_set_duration_enable(self):
        """Test set_duration_enable works."""
        self.test_fem.fem.duration_enable = False
        self.test_fem.fem.set_duration_enable(True)
        assert self.test_fem.fem.duration_enable is True

    def test_set_duration(self):
        """Test set_duration works."""
        row_s1 = 5
        s1_sph = 1
        sph_s2 = 5
        self.test_fem.fem.row_s1 = row_s1
        self.test_fem.fem.s1_sph = s1_sph
        self.test_fem.fem.sph_s2 = sph_s2
        self.test_fem.fem.duration_enable = True
        duration = 2
        self.test_fem.fem.calculate_frame_rate()
        self.test_fem.fem.set_duration(duration)
        assert self.test_fem.fem.frame_rate == 7154.079227920547
        assert self.test_fem.fem.number_frames == 14308

    def test_get_health(self):
        """Test obtaining health variable works."""
        health = False
        self.test_fem.fem.health = health
        assert self.test_fem.fem.get_health() is health

    def test_connect_hardware_handles_cold_start(self):
        """Test that connecting from 'cold' works OK."""
        self.test_fem.fem.parent.cold_start = True
        self.test_fem.fem.parent.daq.commit_configuration = Mock()
        self.test_fem.fem.connect_hardware()
        # TODO: Should be False, once S/W can read F/W to determine whether Control intf setup
        assert self.test_fem.fem.parent.cold_start is True

    def test_connect_hardware_handles_non_cold_start(self):
        """Test that connecting works OK."""
        self.test_fem.fem.parent.cold_start = False
        self.test_fem.fem.connect = Mock()
        self.test_fem.fem.connect_hardware()
        self.test_fem.fem.connect.assert_called()

    def test_connect_hardware_already_connected_fails(self):
        """Test that connecting with connection already established is handled."""
        self.test_fem.fem.hardware_connected = True
        e = "Connection already established"
        with pytest.raises(ParameterTreeError, match=e):
            self.test_fem.fem.connect_hardware()
        assert self.test_fem.fem.hardware_connected is True

    @patch("hexitec.HexitecFem.RdmaUDP")
    @patch("hexitec.HexitecFem.UdpCore")
    @patch("hexitec.HexitecFem.IOLoop.instance")
    def test_configure_camera_interfaces(self, mock_ioloop, mock_UdpCore, mock_RdmaUDP):
        """Test function working ok."""
        mocked_loop = MagicMock()
        mock_ioloop.return_value = mocked_loop

        self.test_fem.fem.configure_camera_interfaces()

        mock_RdmaUDP.assert_called_once_with(local_ip=self.test_fem.fem.server_ctrl_ip,
                                             local_port=self.test_fem.fem.server_ctrl_port,
                                             rdma_ip=self.test_fem.fem.camera_ctrl_ip,
                                             rdma_port=self.test_fem.fem.camera_ctrl_port,
                                             multicast=True, debug=False)

        mock_UdpCore.assert_called_once_with(mock_RdmaUDP.return_value, ctrl_flag=True,
                                             iface_name=self.test_fem.fem.control_interface,
                                             qsfp_idx=self.test_fem.fem.control_qsfp_idx,
                                             lane=self.test_fem.fem.control_lane)

        self.assertEqual(self.test_fem.fem.status_message, "Set Control params..")
        # Clutch to avoid flake8 E501 line too long
        config_w_multicast = self.test_fem.fem.configure_control_with_multicast
        mocked_loop.call_later.assert_called_once_with(2, config_w_multicast,
                                                       mock_RdmaUDP.return_value,
                                                       mock_UdpCore.return_value)

    def test_connect_hardware_handles_Exception(self):
        """Test that connecting with hardware handles failure."""
        self.test_fem.fem.parent.daq.commit_configuration = Mock()
        self.test_fem.fem.configure_camera_interfaces = Mock(side_effect=HexitecFemError(""))
        e = "Connection Error"
        with pytest.raises(ParameterTreeError, match=e):
            self.test_fem.fem.connect_hardware()
        assert self.test_fem.fem._get_status_error() == e
        # assert ex
        assert self.test_fem.fem.hardware_connected is False
        assert self.test_fem.fem.hardware_busy is False

    def test_connect_hardware_handles_socket_error(self):
        """Test that connecting with hardware handles socket error."""
        self.test_fem.fem.parent.daq.commit_configuration = Mock()
        self.test_fem.fem.configure_camera_interfaces = Mock(side_effect=socket.error(""))
        e = "Connection Socket Error"
        with pytest.raises(ParameterTreeError, match=e):
            self.test_fem.fem.connect_hardware()
        assert self.test_fem.fem._get_status_error() == e
        assert self.test_fem.fem.hardware_connected is False
        assert self.test_fem.fem.hardware_busy is False

    def test_connect_hardware_without_farm_mode_prepped(self):
        """Test that connecting without farm mode established isn't allowed."""
        self.test_fem.fem.parent.software_state = "Nowt"
        self.test_fem.fem.farm_mode_prepared = False
        self.test_fem.fem.connect_hardware()
        assert self.test_fem.fem.parent.software_state == "Cold"

    def test_prepare_farm_mode(self):
        """Test that function works okay."""
        self.test_fem.fem.load_farm_mode_json_parameters = Mock()
        self.test_fem.fem.verify_farm_mode_parameters = Mock()
        rc = self.test_fem.fem.prepare_farm_mode()
        self.test_fem.fem.load_farm_mode_json_parameters.assert_called()
        self.test_fem.fem.verify_farm_mode_parameters.assert_called()
        assert rc is True

    def test_prepare_farm_mode_handles_error(self):
        """Test that function handles bad json parameter(s)."""
        self.test_fem.fem.load_farm_mode_json_parameters = Mock(side_effect=HexitecFemError(""))
        rc = self.test_fem.fem.prepare_farm_mode()
        assert rc is False

    def test_load_farm_mode_json_parameters_handles_file_not_found(self):
        """Test that function handles file not found Exception."""
        self.test_fem.fem.farm_mode_file = None
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.load_farm_mode_json_parameters()
        assert exc_info.type is HexitecFemError

    def test_load_farm_mode_json_parameters_handles_TypeError(self):
        """Test that function handles TypeError."""
        self.test_fem.fem.farm_mode_file = Mock()
        self.test_fem.fem.farm_mode_file.side_effect = TypeError
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.load_farm_mode_json_parameters()
        assert exc_info.type is HexitecFemError

    def test_verify_farm_mode_parameters(self):
        """Test that Farm mode parameters can be verified."""
        self.test_fem.fem.verify_farm_mode_parameters("lo")
        ip = '127.0.0.1'
        mac = '00:00:00:00:00:00'
        assert self.test_fem.fem.server_ctrl_ip == ip
        assert self.test_fem.fem.server_ctrl_mac == mac
        assert self.test_fem.fem.farm_mode_targets == 2

    # # TODO Cannot set farm_target parameters independently from e_i_p function..
    # def test_verify_farm_mode_parameters_handles_exception(self):
    #     """Test that Farm mode parameters handles mismatched configuration."""
    #     self.test_fem.fem.extract_interface_parameters = Mock(return_value = (1, 2))
    #     self.test_fem.fem.farm_target_ip == ["10.0.0.0 10.0.0.1"]	# 2 IPs
    #     self.test_fem.fem.farm_target_mac == ["00:01:02:03:04:05"]	# 1 MAC address
    #     self.test_fem.fem.farm_target_port == [1, 2, 3]	 # 3 ports
    #     with pytest.raises(HexitecFemError) as exc_info:
    #         self.test_fem.fem.verify_farm_mode_parameters("lo")

    def test_extract_interface_parameter_handles_exception(self):
        """Test that function handles Exception."""
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.extract_interface_parameters("invalid_iface")
        assert exc_info.type is HexitecFemError

    def test_extract_string_parameters_handles_exception(self):
        """Test that function handles Exception."""
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.extract_string_parameters(["list", "not_supported"])
        assert exc_info.type is HexitecFemError

    def test_determine_farm_mode_config(self):
        """Test function works ok."""
        # Farm mode parameters
        ip_addresses = ['10.0.2.1', '10.0.1.1', '10.0.1.1', '10.0.2.1']
        macs = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:26']
        ports = [61651, 61651, 61650, 61650]
        frames_per_trigger = 4
        # Expected farm mode settings
        ip_lut1 = ['10.0.2.1', '10.0.2.1', '10.0.2.1', '10.0.2.1']
        ip_lut2 = ['10.0.1.1', '10.0.1.1', '10.0.1.1', '10.0.1.1']
        mac_lut1 = ['9c:69:b4:60:b8:26', '9c:69:b4:60:b8:26', '9c:69:b4:60:b8:26', '9c:69:b4:60:b8:26']
        mac_lut2 = ['9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25', '9c:69:b4:60:b8:25']
        port_lut1 = [61651, 61651, 61650, 61650]
        port_lut2 = [61651, 61651, 61650, 61650]

        ip1, ip2, mac1, mac2, port1, port2 = \
            self.test_fem.fem.epac_triggering_farm_mode_config(ip_addresses, macs, ports, frames_per_trigger)
        assert ip1 == ip_lut1
        assert ip2 == ip_lut2
        assert mac1 == mac_lut1
        assert mac2 == mac_lut2
        assert port1 == port_lut1
        assert port2 == port_lut2

    def test_populate_lists(self):
        """Test function works ok."""
        self.test_fem.fem.farm_target_ip = ['10.0.1.2', '10.0.1.3', '10.0.1.4', '10.0.1.1']
        ip_lut1 = ['10.0.1.2', '10.0.1.4']
        ip_lut2 = ['10.0.1.3', '10.0.1.1']
        self.test_fem.fem.farm_target_mac = ['5c:6f:69:f8:57:d0', '5c:6f:69:f8:a3:e0',
                                             '5c:6f:69:f8:7a:10']
        mac_lut1 = ['5c:6f:69:f8:57:d0', '5c:6f:69:f8:7a:10', '5c:6f:69:f8:a3:e0']
        mac_lut2 = ['5c:6f:69:f8:a3:e0', '5c:6f:69:f8:57:d0', '5c:6f:69:f8:7a:10']
        lut1, lut2 = self.test_fem.fem.populate_lists(self.test_fem.fem.farm_target_ip)
        assert lut1 == ip_lut1
        assert lut2 == ip_lut2
        lut1, lut2 = self.test_fem.fem.populate_lists(self.test_fem.fem.farm_target_mac)
        assert lut1 == mac_lut1
        assert lut2 == mac_lut2

    def test_initialise_hardware_fails_if_not_connected(self):
        """Test function fails when no connection established."""
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.initialise_hardware()
        error = "Can't initialise hardware without a connection"
        assert exc_info.value.args[0] == error
        assert exc_info.type is ParameterTreeError
        assert self.test_fem.fem.hardware_connected is False
        assert self.test_fem.fem.hardware_busy is False

    def test_initialise_hardware_fails_unknown_exception(self):
        """Test function fails unexpected exception."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.setup_data_lane_1 = Mock()
        self.test_fem.fem.setup_data_lane_1.side_effect = AttributeError()
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.initialise_hardware()
        error = "Camera initialisation failed"
        assert self.test_fem.fem.status_error == error
        assert exc_info.value.args[0] == f"{error}: "
        assert exc_info.type is ParameterTreeError
        assert self.test_fem.fem.hardware_busy is False

    def test_initialise_hardware_fails_if_hardware_busy(self):
        """Test function fails when hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.initialise_hardware()
        error = "Can't initialise hardware, Hardware busy"
        assert exc_info.value.args[0] == error
        assert exc_info.type is ParameterTreeError

    def test_power_up_modules(self):
        """Test function works."""
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.connect = Mock()
            # vsrs_selected = 0x3F
            # self.test_fem.fem.vsrs_selected = vsrs_selected
            # Test VSRs can all be enabled
            self.test_fem.fem.hardware_connected = False
            self.test_fem.fem.broadcast_VSRs.enable_module = Mock(return_value=True)
            status = "fake_status"
            self.test_fem.fem.broadcast_VSRs._get_status = Mock(return_value=status)

            # Test HVs can all be enabled
            self.test_fem.fem.broadcast_VSRs.hv_enable = Mock(return_value=True)
            status = "fake_status"
            self.test_fem.fem.broadcast_VSRs._get_status = Mock(return_value=status)

            self.test_fem.fem.power_up_modules()
            assert self.test_fem.fem.hardware_connected is True
            i = mock_loop.instance()
            i.call_later.assert_called_with(10, self.test_fem.fem.cam_connect_completed)

    def test_power_up_modules_flags_vsr_unpowered(self):
        """Test function works."""
        self.test_fem.fem.connect = Mock()
        # vsrs_selected = 0x3F
        # self.test_fem.fem.vsrs_selected = vsrs_selected
        # Test VSRs can all be enabled
        self.test_fem.fem.hardware_connected = False
        self.test_fem.fem.broadcast_VSRs.enable_module = Mock(return_value=False)
        vsr_statuses = "fake_status"
        self.test_fem.fem.broadcast_VSRs._get_status = Mock(return_value=vsr_statuses)

        # # Test HVs can all be enabled
        # self.test_fem.fem.broadcast_VSRs.hv_enable = Mock(return_value=True)
        # status = "fake_status"
        # self.test_fem.fem.broadcast_VSRs._get_status = Mock(return_value=status)

        self.test_fem.fem.flag_error = Mock()
        self.test_fem.fem.power_up_modules()
        message = "Not all VSRs powered up"
        error = "{}".format(vsr_statuses)
        self.test_fem.fem.flag_error.assert_called_with(message, error)

    def test_power_up_modules_flags_hvs_unpowered(self):
        self.test_fem.fem.connect = Mock()
        # vsrs_selected = 0x3F
        # self.test_fem.fem.vsrs_selected = vsrs_selected
        # Test VSRs can all be enabled
        self.test_fem.fem.hardware_connected = False
        self.test_fem.fem.broadcast_VSRs.enable_module = Mock(return_value=True)
        vsr_statuses = "fake_status"
        self.test_fem.fem.broadcast_VSRs._get_status = Mock(return_value=vsr_statuses)

        # Test HVs can all be enabled
        self.test_fem.fem.broadcast_VSRs.hv_enable = Mock(return_value=False)

        self.test_fem.fem.flag_error = Mock()
        self.test_fem.fem.power_up_modules()
        message = "VSRs' HV didn't turn on"
        error = "{}".format(vsr_statuses)
        self.test_fem.fem.flag_error.assert_called_with(message, error)

    def test_power_up_modules_flags_socket_error(self):
        """Test function will handle if not all of selected HVs are powered on."""
        self.test_fem.fem.data_path_reset = Mock()
        self.test_fem.fem.data_path_reset.side_effect = socket_error()
        self.test_fem.fem.flag_error = Mock()
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True

        error = "Power up modules Error"
        self.test_fem.fem.power_up_modules()
        self.test_fem.fem.flag_error.assert_called_with(error, "")
        assert self.test_fem.fem.hardware_connected is False
        assert self.test_fem.fem.hardware_busy is False

    def test_collect_data_fails_on_exception(self):
        """Test function can handle unexpected exception."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.system_initialised = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.acquire_data = Mock()
        self.test_fem.fem.acquire_data.side_effect = AttributeError()
        error = "Data acquisition failed"
        self.test_fem.fem.flag_error = Mock()
        self.test_fem.fem.collect_data()
        self.test_fem.fem.flag_error.assert_called_with(error, "")

    def test_collect_data_works(self):
        """Test function works all right."""
        # Ensure correct circumstances
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.system_initialised = True
        self.test_fem.fem.hardware_busy = False
        # Reset variables, to be checked post run
        self.test_fem.fem.acquisition_completed = False
        self.test_fem.fem.acquire_data = Mock()
        self.test_fem.fem.collect_data()
        assert self.test_fem.fem.hardware_busy is True
        self.test_fem.fem.acquire_data.assert_called()

    def test_disconnect_hardware(self):
        """Test the function works ok."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hv_bias_enabled = True
        self.test_fem.fem.disconnect_hardware()
        assert self.test_fem.fem.hardware_connected is False
        assert self.test_fem.fem.hv_bias_enabled is False

    def test_disconnect_hardware_fails_without_connection(self):
        """Test function fails without established hardware connection."""
        self.test_fem.fem.hardware_connected = False
        self.test_fem.fem.disconnect_hardware()
        error = "Failed to disconnect: No connection to disconnect"
        assert self.test_fem.fem._get_status_error() == error

    def test_disconnect_hardware_handles_exception(self):
        """Test function can handle Exception thrown."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.cam_disconnect = Mock()
        self.test_fem.fem.cam_disconnect.side_effect = Exception("")
        self.test_fem.fem.disconnect_hardware()
        error = "Disconnection failed"
        assert self.test_fem.fem.status_error == error

    def test_accessor_functions(self):
        """Test access functions handle bools."""
        number_frames = 1001
        self.test_fem.fem.frame_rate = 0
        self.test_fem.fem.set_number_frames(number_frames)
        assert self.test_fem.fem.get_number_frames() == number_frames

        for bEnabled in True, False:
            self.test_fem.fem.set_debug(bEnabled)
            assert self.test_fem.fem.get_debug() == bEnabled

    def test_set_all_data_sent(self):
        """Test function works ok."""
        all_data_sent = 5
        self.test_fem.fem.set_all_data_sent(all_data_sent)
        self.test_fem.fem.all_data_sent == all_data_sent

    def set_all_data_sent(self, all_data_sent):
        """Set whether all data has been sent (hardware simulation)."""
        self.all_data_sent = all_data_sent

    def test_cam_connect_completed(self):
        """Test function works ok."""
        self.test_fem.fem.parent.daq.commit_configuration = Mock()
        self.test_fem.fem.cam_connect_completed()
        assert self.test_fem.fem.hardware_busy is False
        assert self.test_fem.fem.parent.software_state == "Idle"
        self.test_fem.fem.parent.daq.commit_configuration.assert_called()

    def test_cam_disconnect(self):
        """Test function works ok."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.disconnect = Mock()
        self.test_fem.fem.system_initialised = True
        self.test_fem.fem.cam_disconnect()
        assert self.test_fem.fem.system_initialised is False

    def test_cam_disconnect_fails_network_error(self):
        """Test function handles socket error."""
        self.test_fem.fem.disconnect = Mock()
        self.test_fem.fem.disconnect.side_effect = socket_error()

        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.cam_disconnect()
        assert exc_info.type is HexitecFemError
        assert self.test_fem.fem.hardware_connected is False

    def test_cam_disconnect_fails_struct_error(self):
        """Test function handles struct error."""
        import struct
        self.test_fem.fem.disconnect = Mock()
        self.test_fem.fem.disconnect.side_effect = struct.error()
        self.test_fem.fem.parent.leak_fault_counter = 0

        with pytest.raises(struct.error) as exc_info:
            self.test_fem.fem.cam_disconnect()
        assert exc_info.type is struct.error
        assert self.test_fem.fem.hardware_connected is False
        self.test_fem.fem.parent.leak_fault_counter == 1

    def test_cam_disconnect_fails_attribute_error(self):
        """Test function handles attribute error."""
        self.test_fem.fem.disconnect = Mock()
        self.test_fem.fem.disconnect.side_effect = AttributeError()

        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.cam_disconnect()
        assert exc_info.type is HexitecFemError
        assert self.test_fem.fem.hardware_connected is False

    def test_acquire_data_hardware_calls(self):
        """Nominally tests the four hardware functions called by acquire_data.

            Actually just bumps the unit test coverage to 100%.
            TODO Cover four functions directly:
            frame_reset_to_zero, data_path_reset, set_nof_frames, data_en
        """
        with patch("time.sleep"), patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.acquire_data()
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.1, self.test_fem.fem.check_acquire_finished)

    def test_acquire_data(self):
        """Test function handles normal configuration."""
        self.test_fem.fem.frame_reset_to_zero = Mock()
        self.test_fem.fem.data_path_reset = Mock()
        self.test_fem.fem.set_nof_frames = Mock()
        self.test_fem.fem.data_en = Mock()
        number_frames = 10
        self.test_fem.fem.number_frames = number_frames
        with patch("time.sleep"), patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.acquire_data()
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.1, self.test_fem.fem.check_acquire_finished)
            self.test_fem.fem.frame_reset_to_zero.assert_called_once()
            self.test_fem.fem.data_path_reset.assert_called_once()
            self.test_fem.fem.set_nof_frames.assert_called_once_with(number_frames)
            self.test_fem.fem.data_en.assert_has_calls([call(enable=True), call(enable=False)])
            self.assertEqual(self.test_fem.fem.data_en.call_count, 2)

    def test_acquire_data_handles_exception(self):
        """Test function handles exception."""
        self.test_fem.fem.create_iso_timestamp = Mock()
        self.test_fem.fem.create_iso_timestamp.side_effect = Exception()
        self.test_fem.fem.flag_error = Mock()
        with patch("time.sleep"), patch("hexitec.HexitecFem.IOLoop"):
            with pytest.raises(ParameterTreeError) as exc_info:
                self.test_fem.fem.acquire_data()
            error = "Failed to start acquire_data"
            assert exc_info.value.args[0] == error
            assert self.test_fem.fem.hardware_busy is False
            self.test_fem.fem.flag_error.assert_called_with(error, "")

    def test_check_acquire_finished_handles_cancel(self):
        """Test check_acquire_finished calls acquire_data_completed if acquire cancelled."""
        with patch("hexitec.HexitecFem.IOLoop"):
            with patch("logging.debug") as mock_log:
                self.test_fem.fem.cancel_acquisition = True
                self.test_fem.fem.acquire_data_completed = Mock()

                self.test_fem.fem.check_acquire_finished()
                self.test_fem.fem.acquire_data_completed.assert_called()
                mock_log.assert_called_with("Acquire cancellation initiated")

    def test_check_acquire_finished_handles_data_transmission_complete(self):
        """Test check_acquire_finished handles data transmited."""
        self.test_fem.fem.cancel_acquisition = False
        self.test_fem.fem.acquire_data_completed = Mock()
        self.test_fem.fem.check_acquire_finished()
        self.test_fem.fem.acquire_data_completed.assert_called()

    def test_check_acquire_finished_handles_data_transmission_ongoing(self):
        """Test check_acquire_finished handles ongoing data transmission."""
        self.test_fem.fem.cancel_acquisition = False
        self.test_fem.fem.x10g_rdma.udp_rdma_read = Mock()
        self.test_fem.fem.x10g_rdma.udp_rdma_read.return_value = [0]
        self.test_fem.fem.acquire_data_completed = Mock()
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.check_acquire_finished()
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.1, self.test_fem.fem.check_acquire_finished)

    def test_check_acquire_finished_handles_HexitecFemError(self):
        """Test check_acquire_finished handles HexitecFemError exception."""
        self.test_fem.fem.cancel_acquisition = True
        self.test_fem.fem.acquisition_completed = False
        self.test_fem.fem.acquire_data_completed = Mock()
        e_msg = "Bad Error"
        self.test_fem.fem.acquire_data_completed.side_effect = HexitecFemError(e_msg)

        self.test_fem.fem.check_acquire_finished()
        error = "Failed to collect data: {}".format(e_msg)
        assert self.test_fem.fem._get_status_error() == error
        assert self.test_fem.fem.acquisition_completed is True

    def test_check_acquire_finished_handles_exception(self):
        """Test check_acquire_finished handles bog standard exception."""
        self.test_fem.fem.cancel_acquisition = True
        self.test_fem.fem.acquisition_completed = False
        self.test_fem.fem.acquire_data_completed = Mock()
        e_msg = "Badder Error"
        self.test_fem.fem.acquire_data_completed.side_effect = Exception(e_msg)

        self.test_fem.fem.check_acquire_finished()
        error = "Data acquisition failed: {}".format(e_msg)
        assert self.test_fem.fem._get_status_error() == error
        assert self.test_fem.fem.acquisition_completed is True

    def test_acquire_data_completed_handles_manual_stop(self):
        """Test function handles user stopping acquisition."""
        self.test_fem.fem.cancel_acquisition = True
        self.test_fem.fem.send_cmd = Mock()

        self.test_fem.fem.acquire_data_completed()

        assert self.test_fem.fem.cancel_acquisition is False
        assert self.test_fem.fem.hardware_busy is False
        assert self.test_fem.fem.acquisition_completed is True

    def test_acquire_data_completed(self):
        """Test function handles normal end of acquisition."""
        self.test_fem.fem.acquire_start_time = datetime.now(timezone.utc).astimezone().isoformat()
        self.test_fem.fem.parent.software_state = "Cold"
        self.test_fem.fem.acquire_data_completed()
        assert self.test_fem.fem.hardware_busy is False
        assert self.test_fem.fem.acquisition_completed is True
        assert self.test_fem.fem.all_data_sent == 0

    def test_run_collect_offsets(self):
        """Test function working okay."""
        self.test_fem.fem.system_initialised = True
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.collect_offsets = Mock()
        self.test_fem.fem.run_collect_offsets()
        self.test_fem.fem.collect_offsets.assert_called()

    def test_run_collect_offsets_handles_hardware_disconnected(self):
        self.test_fem.fem.hardware_connected = False
        error = "Can't collect offsets without a connection"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.run_collect_offsets()
        assert exc_info.value.args[0] == error

    def test_run_collect_offsets_handles_hardware_busy(self):
        """Test function handles hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        error = "Can't collect offsets, Hardware busy"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.run_collect_offsets()
        assert exc_info.value.args[0] == error

    def test_run_collect_offsets_handles_system_not_initialised(self):
        """Test function handles system not yet initialised."""
        self.test_fem.fem.system_initialised = False
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.flag_error = Mock()
        error = "Can't collect offsets, system not initialised"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.run_collect_offsets()
        assert exc_info.value.args[0] == error
        self.test_fem.fem.flag_error.assert_called_with(error, "")

    @async_test
    async def test_collect_offsets(self):
        """Test function working okay."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.parent.software_state = "Idle"
        self.test_fem.fem.stop_sm = Mock()
        self.test_fem.fem.set_dc_controls = Mock()
        self.test_fem.fem.start_sm = Mock()
        self.test_fem.fem.await_dc_captured = Mock()
        self.test_fem.fem.clr_dc_controls = Mock()
        await self.test_fem.fem.collect_offsets()
        assert self.test_fem.fem.hardware_busy is False
        # State should revert back to previous state on completion
        assert self.test_fem.fem.parent.software_state == "Idle"

    @async_test
    async def test_collect_offsets_handles_exception(self):
        """Test function handles exception."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.stop_sm = Mock()
        self.test_fem.fem.stop_sm.side_effect = AttributeError()
        await self.test_fem.fem.collect_offsets()
        error = "Failed to collect offsets"
        assert self.test_fem.fem.status_error == error

    @patch('hexitec_vsr.VsrModule')
    def test_stop_sm(self, mocked_vsr_module):
        """Test function working okay."""
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.stop_sm()
        self.test_fem.fem.vsr_list[0].disable_sm.assert_called()

    @patch('hexitec_vsr.VsrModule')
    def test_set_dc_controls(self, mocked_vsr_module):
        """Test function working okay."""
        vsr_list = [mocked_vsr_module]
        capt_avg_pict, spectroscopic_mode_en = True, True
        vcal_enabled = self.test_fem.fem.vcal_enabled
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.set_dc_controls(capt_avg_pict, spectroscopic_mode_en)
        self.test_fem.fem.vsr_list[0].set_dc_control_bits.assert_called_with(capt_avg_pict,
                                                                             vcal_enabled,
                                                                             spectroscopic_mode_en)

    @patch('hexitec_vsr.VsrModule')
    def test_clr_dc_controls(self, mocked_vsr_module):
        """Test function working okay."""
        vsr_list = [mocked_vsr_module]
        capt_avg_pict, spectroscopic_mode_en = True, True
        vcal_enabled = self.test_fem.fem.vcal_enabled
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.clr_dc_controls(capt_avg_pict, spectroscopic_mode_en)
        self.test_fem.fem.vsr_list[0].clr_dc_control_bits.assert_called_with(capt_avg_pict,
                                                                             vcal_enabled,
                                                                             spectroscopic_mode_en)

    @patch('hexitec_vsr.VsrModule')
    def test_start_sm(self, mocked_vsr_module):
        """Test function working okay."""
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.start_sm()
        self.test_fem.fem.vsr_list[0].enable_sm.assert_called()

    def test_await_dc_captured(self):
        """Test function working okay."""
        self.test_fem.fem.check_dc_statuses = Mock()
        self.test_fem.fem.check_dc_statuses.return_value = [7, 7, 7, 7, 7, 7]
        self.test_fem.fem.await_dc_captured()

    # Tox/GitHub Actions started failing, pytest: Fine
    def test_await_dc_captured_handles_timeout(self):
        """Test function working okay."""
        dc_statuses = [6, 6, 6, 6, 6, 6]
        self.test_fem.fem.check_dc_statuses = Mock()
        self.test_fem.fem.check_dc_statuses.return_value = dc_statuses

        e = "Dark images timed out. R.89: {}".format(dc_statuses)
        with patch("time.time") as mock_time:
            mock_time.side_effect = [0, 3]
            with pytest.raises(HexitecFemError) as exc_info:
                self.test_fem.fem.await_dc_captured()
            assert exc_info.type is HexitecFemError
            assert exc_info.value.args[0] == "%s" % e

    @patch('hexitec_vsr.VsrModule')
    def test_check_dc_statuses(self, mocked_vsr_module):
        """Test function working okay."""
        mocked_vsr_module.read_pll_status.return_value = 7
        mocked_vsr_module.enable_vcal = Mock()
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        replies = self.test_fem.fem.check_dc_statuses()
        assert replies == [7]

    def test_are_dc_ready_handles_all_ready(self):
        """Test function handle VSRs all return ready."""
        dc_statuses = [7, 7, 7, 7, 7, 7]
        all_dc_ready = self.test_fem.fem.are_dc_ready(dc_statuses)
        assert all_dc_ready is True

    def test_are_dc_ready_handles_not_all_ready(self):
        """Test function handle VSRs not all return ready."""
        dc_statuses = [7, 7, 6, 7, 7, 7]
        all_dc_ready = self.test_fem.fem.are_dc_ready(dc_statuses)
        assert all_dc_ready is False

    @patch('hexitec_vsr.VsrModule')
    def test_load_pwr_cal_read_enables_fails_unknown_vsr(self, mocked_vsr_module):
        """Test function handles unknown VSR address."""
        mocked_vsr_module.addr = 25
        # self.test_fem.fem.vsr_addr = mocked_vsr_module
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.load_pwr_cal_read_enables(mocked_vsr_module)
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == "Unknown VSR address! (%s)" % mocked_vsr_module.addr

    @patch('hexitec_vsr.VsrModule')
    def test_load_pwr_cal_read_enables_default_enables(self, mocked_vsr_module):
        """Test function handles setting default values."""
        mocked_vsr_module.addr = 0x90
        self.test_fem.fem.load_pwr_cal_read_enables(mocked_vsr_module)
        enables_defaults = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        mocked_vsr_module.set_column_calibration_mask.assert_called_with(enables_defaults, asic=2)
        mocked_vsr_module.set_row_calibration_mask.assert_called_with(enables_defaults, asic=2)

    @patch('hexitec_vsr.VsrModule')
    def test_load_pwr_cal_read_enables_custom_enables(self, mocked_vsr_module):
        """Test function handles setting customised values."""
        mocked_vsr_module.addr = 0x90
        self.test_fem.fem._extract_80_bits = Mock()
        enables = [0x30, 0x31, 0x32, 0x33, 0x35, 0x36, 0x37, 0x38, 0x39, 0x41,
                   0x42, 0x43, 0x44, 0x45, 0x46, 0x30, 0x32, 0x34, 0x36, 0x38]
        self.test_fem.fem._extract_80_bits.return_value = enables
        self.test_fem.fem.load_pwr_cal_read_enables(mocked_vsr_module)
        mocked_vsr_module.set_column_calibration_mask.assert_called_with(enables, asic=2)
        mocked_vsr_module.set_row_calibration_mask.assert_called_with(enables, asic=2)

    @patch('hexitec_vsr.VsrModule')
    def test_write_dac_values(self, mocked_vsr_module):
        """Test function handles writing dac values ok."""
        self.test_fem.fem.umid_value = 1
        self.test_fem.fem.vcal_value = 1
        self.test_fem.fem.write_dac_values(mocked_vsr_module.addr)

    @patch('hexitec_vsr.VsrModule')
    @async_test
    async def test_initialise_system(self, mocked_vsr_module):
        """Test function initialises the system ok."""
        self.test_fem.fem.initialise_vsr = Mock()
        mocked_vsr_module.read_pll_status.return_value = 7
        mocked_vsr_module.enable_vcal = Mock()
        mocked_vsr_module.addr = 0x90
        mocked_vsr_module.slot = 1
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list

        self.test_fem.fem.x10g_rdma.udp_rdma_write = Mock()
        self.test_fem.fem.x10g_rdma.udp_rdma_read = Mock()
        self.test_fem.fem.x10g_rdma.udp_rdma_read.return_value = [255]
        await self.test_fem.fem.initialise_system()
        assert self.test_fem.fem.parent.software_state == "Ready"

    @patch('hexitec_vsr.VsrModule')
    @async_test
    async def test_initialise_system_handles_pll_timeout(self, mocked_vsr_module):
        """Test function handles if PLL doesn't lock."""
        self.test_fem.fem.initialise_vsr = Mock()
        mocked_vsr_module.read_pll_status.return_value = 6
        mocked_vsr_module.enable_vcal = Mock()
        mocked_vsr_module.addr = 0x90
        mocked_vsr_module.slot = 1
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list

        self.test_fem.fem.x10g_rdma.udp_rdma_write = Mock()
        self.test_fem.fem.x10g_rdma.udp_rdma_read = Mock()
        self.test_fem.fem.x10g_rdma.udp_rdma_read.return_value = [255]
        with patch("time.time") as mock_time:
            mock_time.side_effect = [0, 3]
            with patch("logging.error") as mock_log:
                await self.test_fem.fem.initialise_system()
                mock_log.assert_called()

    @patch('hexitec_vsr.VsrModule')
    @async_test
    async def test_initialise_system_flags_unsynced_vsr(self, mocked_vsr_module):
        """Test function handles an unsynced vsr."""
        self.test_fem.fem.initialise_vsr = Mock()
        mocked_vsr_module.read_pll_status.return_value = 7
        mocked_vsr_module.enable_vcal = Mock()
        mocked_vsr_module.addr = 0x90
        mocked_vsr_module.slot = 1
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.x10g_rdma.write = Mock()
        self.test_fem.fem.x10g_rdma.udp_rdma_read = Mock()
        self.test_fem.fem.x10g_rdma.udp_rdma_read.return_value = [0xF0]

        with patch("logging.error") as mock_log:
            await self.test_fem.fem.initialise_system()
            mock_log.assert_called_with('VSR1 Error: Incomplete lock (0xF0)')

    @patch('hexitec_vsr.VsrModule')
    @async_test
    async def test_initialise_system_handles_HexitecFemError(self, mocked_vsr_module):
        """Test function handles HexitecFemError."""
        mocked_vsr_module.stop_trigger_sm = Mock()
        mocked_vsr_module.stop_trigger_sm.side_effect = HexitecFemError("E")
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        await self.test_fem.fem.initialise_system()
        assert self.test_fem.fem.status_error == "Failed to initialise camera: {}".format("E")
        assert self.test_fem.fem.parent.software_state == "Error"

    @patch('hexitec_vsr.VsrModule')
    @async_test
    async def test_initialise_system_handles_OSError(self, mocked_vsr_module):
        """Test function handles OSError."""
        mocked_vsr_module.stop_trigger_sm = Mock()
        mocked_vsr_module.stop_trigger_sm.side_effect = OSError("E")
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        await self.test_fem.fem.initialise_system()
        assert self.test_fem.fem.status_error == "Detector initialisation failed: {}".format("E")
        assert self.test_fem.fem.parent.software_state == "Error"

    @patch('hexitec_vsr.VsrModule')
    @async_test
    async def test_initialise_system_handles_Exception(self, mocked_vsr_module):
        """Test function handles Exception."""
        mocked_vsr_module.stop_trigger_sm = Mock()
        mocked_vsr_module.stop_trigger_sm.side_effect = Exception("E")
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        await self.test_fem.fem.initialise_system()
        assert self.test_fem.fem.status_error == "Camera initialisation failed: {}".format("E")
        assert self.test_fem.fem.parent.software_state == "Error"

    @patch("hexitec.HexitecFem.HexitecFem.load_pwr_cal_read_enables")
    @patch("hexitec.HexitecFem.HexitecFem.write_dac_values")
    def test_initialise_vsr(self, mock_write_dac_values, mock_load_pwr_cal_read_enables):
        vsr = MagicMock()
        row_s1 = 1
        s1_sph = 2
        sph_s2 = 3
        adc1_delay = 4
        delay_sync_signals = 5
        vcal2_vcal1 = 6
        self.test_fem.fem.row_s1 = row_s1
        self.test_fem.fem.s1_sph = s1_sph
        self.test_fem.fem.sph_s2 = sph_s2
        self.test_fem.fem.gain_string = "high"
        self.test_fem.fem.adc1_delay = adc1_delay
        self.test_fem.fem.delay_sync_signals = delay_sync_signals
        self.test_fem.fem.vcal2_vcal1 = vcal2_vcal1

        self.test_fem.fem.initialise_vsr(vsr)

        vsr.set_rows1_clock.assert_called_once_with(row_s1)
        vsr.set_s1sph.assert_called_once_with(s1_sph)
        vsr.set_sphs2.assert_called_once_with(sph_s2)
        vsr.set_gain.assert_called_once_with("high")
        vsr.set_adc_clock_delay.assert_called_once_with(adc1_delay)
        vsr.set_adc_signal_delay.assert_called_once_with(delay_sync_signals)
        vsr.set_sm_vcal_clock.assert_called_once_with(vcal2_vcal1)
        mock_load_pwr_cal_read_enables.assert_called_once_with(vsr)
        mock_write_dac_values.assert_called_once_with(vsr)
        vsr.initialise.assert_called_once()

    @patch("hexitec.HexitecFem.HexitecFem.load_pwr_cal_read_enables")
    @patch("hexitec.HexitecFem.HexitecFem.write_dac_values")
    def test_initialise_vsr_no_adc_delay(self, mock_write_dac_values,
                                         mock_load_pwr_cal_read_enables):
        vsr = MagicMock()
        row_s1 = 1
        s1_sph = 2
        sph_s2 = 3
        adc1_delay = -1
        self.test_fem.fem.row_s1 = row_s1
        self.test_fem.fem.s1_sph = s1_sph
        self.test_fem.fem.sph_s2 = sph_s2
        self.test_fem.fem.gain_string = "high"
        self.test_fem.fem.adc1_delay = adc1_delay
        self.test_fem.fem.delay_sync_signals = -1
        self.test_fem.fem.vcal2_vcal1 = -1

        self.test_fem.fem.initialise_vsr(vsr)

        vsr.set_rows1_clock.assert_called_once_with(row_s1)
        vsr.set_s1sph.assert_called_once_with(s1_sph)
        vsr.set_sphs2.assert_called_once_with(sph_s2)
        vsr.set_gain.assert_called_once_with("high")
        vsr.set_adc_clock_delay.assert_not_called()
        vsr.set_adc_signal_delay.assert_not_called()
        vsr.set_sm_vcal_clock.assert_not_called()
        mock_load_pwr_cal_read_enables.assert_called_once_with(vsr)
        mock_write_dac_values.assert_called_once_with(vsr)
        vsr.initialise.assert_called_once()

    @patch('hexitec_vsr.VsrModule')
    def test_configure_hardware_triggering_triggered_mode(self, mocked_vsr_module):
        """Test function working okay."""
        mocked_vsr_module.set_trigger_mode_number_frames = Mock()
        mocked_vsr_module.write_trigger_mode_number_frames = Mock()
        mocked_vsr_module.enable_trigger_mode_trigger_two_and_three = Mock()
        mocked_vsr_module.enable_trigger_input_two_and_three = Mock()
        mocked_vsr_module.start_trigger_sm = Mock()
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.triggering_frames = 15
        self.test_fem.fem.enable_trigger_mode = True
        self.test_fem.fem.enable_trigger_input = True
        self.test_fem.fem.start_trigger = True

        self.test_fem.fem.configure_hardware_triggering()
        self.test_fem.fem.vsr_list[0].set_trigger_mode_number_frames.assert_called_with(15)
        self.test_fem.fem.vsr_list[0].write_trigger_mode_number_frames.assert_called()
        self.test_fem.fem.vsr_list[0].enable_trigger_mode_trigger_two_and_three.assert_called()
        self.test_fem.fem.vsr_list[0].enable_trigger_input_two_and_three.assert_called()
        self.test_fem.fem.vsr_list[0].start_trigger_sm.assert_called()

    @patch('hexitec_vsr.VsrModule')
    def test_configure_hardware_triggering_all_enabled_no_mode(self, mocked_vsr_module):
        """Test function working okay."""
        mocked_vsr_module.set_trigger_mode_number_frames = Mock()
        mocked_vsr_module.write_trigger_mode_number_frames = Mock()
        mocked_vsr_module.disable_trigger_mode_trigger_two_and_three = Mock()
        mocked_vsr_module.disable_trigger_input_two_and_three = Mock()
        mocked_vsr_module.stop_trigger_sm = Mock()
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.triggering_frames = 8
        self.test_fem.fem.enable_trigger_mode = False
        self.test_fem.fem.enable_trigger_input = False
        self.test_fem.fem.start_trigger = False

        self.test_fem.fem.configure_hardware_triggering()
        self.test_fem.fem.vsr_list[0].set_trigger_mode_number_frames.assert_called_with(8)
        self.test_fem.fem.vsr_list[0].write_trigger_mode_number_frames.assert_called()
        self.test_fem.fem.vsr_list[0].disable_trigger_mode_trigger_two_and_three.assert_called()
        self.test_fem.fem.vsr_list[0].disable_trigger_input_two_and_three.assert_called()
        self.test_fem.fem.vsr_list[0].stop_trigger_sm.assert_called()

    @patch('hexitec_vsr.VsrModule')
    def test_configure_hardware_triggering_handles_Exception(self, mocked_vsr_module):
        """Test function working okay."""
        mocked_vsr_module.set_trigger_mode_number_frames = Mock()
        mocked_vsr_module.set_trigger_mode_number_frames.side_effect = Exception("Test Exception")
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.flag_error = Mock()

        self.test_fem.fem.configure_hardware_triggering()
        error = "Configure hardware triggering Error"
        self.test_fem.fem.flag_error(error)

    def test_calculate_frame_rate(self):
        """Test calculate_frame_rate works."""
        row_s1 = 5
        s1_sph = 1
        sph_s2 = 5
        self.test_fem.fem.row_s1 = row_s1
        self.test_fem.fem.s1_sph = s1_sph
        self.test_fem.fem.sph_s2 = sph_s2
        self.test_fem.fem.duration_enable = True
        self.test_fem.fem.calculate_frame_rate()
        duration = 2
        self.test_fem.fem.frame_rate = 0
        self.test_fem.fem.set_duration(duration)
        assert self.test_fem.fem.frame_rate == 7154.079227920547
        assert self.test_fem.fem.number_frames == 14308

    # TODO: Mock vsr.get_power_sensors() returning values
    @patch('hexitec_vsr.VsrModule')
    def test_read_pwr_voltages(self, mocked_vsr_module):
        """Test function working OK."""
        mocked_vsr_module.addr = 0x90
        self.test_fem.fem.read_pwr_voltages(mocked_vsr_module)

    @patch('hexitec_vsr.VsrModule')
    def test_read_pwr_voltages_bad_vsr(self, mocked_vsr_module):
        """Test function handles unexpected vsr."""
        mocked_vsr_module.addr = 151
        e = "HV: Invalid VSR address(0x{0:02X})".format(mocked_vsr_module.addr)
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.read_pwr_voltages(mocked_vsr_module)
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == e

    # TODO: Mock vsr._get_env_sensors() returning values
    @patch('hexitec_vsr.VsrModule')
    def test_read_temperatures_humidity_values(self, mocked_vsr_module):
        """Test function work OK."""
        mocked_vsr_module.addr = 0x90
        self.test_fem.fem.read_temperatures_humidity_values(mocked_vsr_module)

    @patch('hexitec_vsr.VsrModule')
    def test_read_temperatures_humidity_values_handles_bad_vsr(self, mocked_vsr_module):
        """Test function handle misconfigured VSR."""
        mocked_vsr_module.addr = 151
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.read_temperatures_humidity_values(mocked_vsr_module)
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == \
            "Sensors: Invalid VSR address(0x{0:02X})".format(mocked_vsr_module.addr)
    """
    read_pwr_voltages(146) (2) value: -2.618273186812985
    read_temperatures_humidity_values(147) (3) value:
        ('31.089', '30.834', '27.81', '27.88', '33.94')
    read_pwr_voltages(147) (3) value: -4.079540219780256
    read_temperatures_humidity_values(148) (4) value:
        ('32.344', '30.185', '27.5', '28.5', '35.38')
    """

    def test_set_hexitec_config(self):
        """Test function handles configuration file ok."""
        filename = "hexitec_test_config.ini"
        self.test_fem.fem.set_hexitec_config(filename)

        assert self.test_fem.fem.row_s1 == 25
        assert self.test_fem.fem.s1_sph == 13
        assert self.test_fem.fem.sph_s2 == 57
        assert self.test_fem.fem.bias_level == 15
        assert self.test_fem.fem.vsrs_selected == 63

    def test_set_hexitec_config_vcal_off_gain_low(self):
        """Test function handles configuration file ok."""
        filename = "hexitec_test_config2.ini"
        self.test_fem.fem.set_hexitec_config(filename)

        assert self.test_fem.fem.row_s1 == 25
        assert self.test_fem.fem.s1_sph == 13
        assert self.test_fem.fem.sph_s2 == 57
        assert self.test_fem.fem.bias_level == 15
        assert self.test_fem.fem.vsrs_selected == 63

    @patch("builtins.open", new_callable=mock_open)
    def test_set_hexitec_config_fails_invalid_filename(self, mock_open):
        mock_open.side_effect = IOError
        rc = self.test_fem.fem.set_hexitec_config("invalid/file.name")
        error = "Cannot open provided hexitec file"
        assert self.test_fem.fem.status_error == error
        assert rc is None

    def test_set_hexitec_config_fails_missing_key(self):
        """Test function fails if filename misses a key."""
        filename = "hexitec_test_config.ini"
        error = "INI File Key Error: artificial error"
        self.test_fem.fem._extract_integer = Mock()
        self.test_fem.fem._extract_integer.side_effect = HexitecFemError(error[20:])
        self.test_fem.fem.set_hexitec_config(filename)
        assert self.test_fem.fem.status_error == error

    def test_set_start_trigger(self):
        """Test function sets start trigger ok."""
        self.test_fem.fem.start_trigger = False
        self.test_fem.fem.set_start_trigger(True)
        assert self.test_fem.fem.start_trigger is True

    def test_set_enable_trigger_mode(self):
        """Test function sets enable trigger mode ok."""
        self.test_fem.fem.enable_trigger_mode = False
        self.test_fem.fem.set_enable_trigger_mode(True)
        assert self.test_fem.fem.enable_trigger_mode is True

    def test_set_enable_trigger_input(self):
        """Test function sets enable trigger input ok."""
        self.test_fem.fem.enable_trigger_input = False
        self.test_fem.fem.set_enable_trigger_input(True)
        assert self.test_fem.fem.enable_trigger_input is True

    def test_set_triggering_mode_triggered_selected(self):
        """Test function sets triggering mode ok."""
        self.test_fem.fem.parent.daq.check_daq_acquiring_data = Mock()
        self.test_fem.fem.system_initialised = True
        self.test_fem.fem.triggering_mode = "none"
        self.test_fem.fem.set_triggering_mode("triggered")

        self.test_fem.fem.parent.daq.check_daq_acquiring_data.assert_called_with("trigger mode")
        assert self.test_fem.fem.triggering_mode == "triggered"
        assert self.test_fem.fem.enable_trigger_input is True
        assert self.test_fem.fem.enable_trigger_mode is True
        assert self.test_fem.fem.system_initialised is False

    def test_set_triggering_mode_none_selected(self):
        """Test function sets triggering mode ok."""
        self.test_fem.fem.parent.daq.check_daq_acquiring_data = Mock()
        self.test_fem.fem.system_initialised = True
        self.test_fem.fem.triggering_mode = "triggered"
        self.test_fem.fem.set_triggering_mode("none")

        self.test_fem.fem.parent.daq.check_daq_acquiring_data.assert_called_with("trigger mode")
        assert self.test_fem.fem.triggering_mode == "none"
        assert self.test_fem.fem.enable_trigger_input is False
        assert self.test_fem.fem.enable_trigger_mode is False
        assert self.test_fem.fem.system_initialised is False

    def test_set_triggering_mode_handles_undefined_mode(self):
        """Test function sets triggering mode ok."""
        self.test_fem.fem.parent.daq.check_daq_acquiring_data = Mock()
        self.test_fem.fem.system_initialised = True
        self.test_fem.fem.triggering_mode = "none"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.set_triggering_mode("made_up")
        assert exc_info.type is ParameterTreeError
        assert exc_info.value.args[0] == "Must be one of: triggered or none"
        assert self.test_fem.fem.system_initialised is True

    def test_set_triggering_frames(self):
        """Test function sets triggering frames ok."""
        self.test_fem.fem.parent.daq.check_daq_acquiring_data = Mock()
        self.test_fem.fem.triggering_frames = 0

        self.test_fem.fem.set_triggering_frames(10)
        self.test_fem.fem.parent.daq.check_daq_acquiring_data.assert_called_with("trigger frames")
        assert self.test_fem.fem.triggering_frames == 10

    def test_set_triggering_frames_handles_wrong_type(self):
        """Test function sets triggering frames ok."""
        self.test_fem.fem.parent.daq.check_daq_acquiring_data = Mock()
        self.test_fem.fem.system_initialised = True
        self.test_fem.fem.triggering_frames = 0
        wrong_type = "Hello?"

        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.set_triggering_frames(wrong_type)
        self.test_fem.fem.parent.daq.check_daq_acquiring_data.assert_called_with("trigger frames")
        assert exc_info.type is ParameterTreeError
        assert exc_info.value.args[0] == "Not an integer!"
        assert self.test_fem.fem.system_initialised is True

    def test_extract_exponential(self):
        """Test function works ok."""
        hexitec_parameters = {'Control-Settings/Uref_mid': '1,000000E+3'}
        umid = self.test_fem.fem._extract_exponential(hexitec_parameters,
                                                      'Control-Settings/Uref_mid', bit_range=12)
        assert umid == 1366

    def test_extract_exponential_fails_out_of_range_value(self):
        """Test function fails on value outside of valid range of values."""
        hexitec_parameters = {'Control-Settings/Uref_mid': '4,097000E+3'}
        umid = self.test_fem.fem._extract_exponential(hexitec_parameters,
                                                      'Control-Settings/Uref_mid', bit_range=12)
        assert umid == -1

    def test_extract_exponential_fails_missing_key(self):
        """Test function fails on missing key (i.e. setting)."""
        hexitec_parameters = {'Control-Settings/U___ref_mid': '1,000000E+3'}
        key = 'Control-Settings/Uref_mid'
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem._extract_exponential(hexitec_parameters, key, bit_range=1)
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == "ERROR: No '%s' Key defined!" % key

    def test_extract_float(self):
        """Test function works ok."""
        hexitec_parameters = {'Control-Settings/VCAL': '0.1'}
        vcal_value = self.test_fem.fem._extract_float(hexitec_parameters, 'Control-Settings/VCAL')
        assert vcal_value == 136

    def test_extract_float_fails_out_of_range_value(self):
        """Test function fails on value outside of valid range of values."""
        hexitec_parameters = {'Control-Settings/VCAL': '3.1'}
        vcal_value = self.test_fem.fem._extract_float(hexitec_parameters, 'Control-Settings/VCAL')
        assert vcal_value == -1

    def test_extract_float_fails_missing_key(self):
        """Test function fails on missing key (i.e. setting)."""
        hexitec_parameters = {'Control-Settings/___L': '1.3'}
        key = 'Control-Settings/VCAL'
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem._extract_float(hexitec_parameters, key)
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == "Missing Key: '%s'" % key

    def test_extract_integer_fails_out_of_range_value(self):
        """Test fails on value outside of valid range."""
        hexitec_parameters = {'Control-Settings/ADC1 Delay': '-1'}
        delay = self.test_fem.fem._extract_integer(hexitec_parameters,
                                                   'Control-Settings/ADC1 Delay',
                                                   bit_range=2)
        assert delay == -1

    def test_extract_integer_fails_missing_key(self):
        """Test function fails on missing key (i.e. setting)."""
        hexitec_parameters = {'Control-Settings/nonsense': '1.3'}
        key = 'Control-Settings/ADC1 Delay'
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem._extract_integer(hexitec_parameters, key, bit_range=2)
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == "Missing Key: '%s'" % key

    def test_extract_boolean(self):
        """Test function works ok."""
        hexitec_parameters = {'my_bool': 'True'}
        my_bool = self.test_fem.fem._extract_boolean(hexitec_parameters, 'my_bool')
        assert my_bool is True
        hexitec_parameters = {'my_bool': 'False'}
        my_bool = self.test_fem.fem._extract_boolean(hexitec_parameters, 'my_bool')
        assert my_bool is False

    def test_extract_boolean_fails_invalid_value(self):
        """Test function fails non-Boolean value."""
        hexitec_parameters = {'Fake/Some_Bool': '_x?'}
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem._extract_boolean(hexitec_parameters, 'Fake/Some_Bool')
        assert exc_info.type is HexitecFemError

    def test_extract_boolean_fails_keyerror(self):
        """Test function fails KeyError."""
        hexitec_parameters = {'Fake/Some_Bool': '_x?'}
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem._extract_boolean(hexitec_parameters, 'Fake/No_Bool')
        assert exc_info.type is HexitecFemError

    def test_extract_80_bits(self):
        """Test function correctly extracts 80 bits from 4 channels."""
        vsr = 1
        all_80b = [255, 255, 255, 255, 255, 255, 255, 255, 255, 255]

        self.test_fem.fem.hexitec_parameters = \
            {'Sensor-Config_V1_S1/ColumnEn_1stChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnEn_2ndChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnEn_3rdChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnEn_4thChannel': '11111111111111111111'}

        channel1 = self.test_fem.fem._extract_80_bits("ColumnEn_", vsr, 1, "Channel")
        assert channel1 == all_80b

    def test_extract_80_bits_missing_configuration(self):
        """Test function fails if any of the four channels not configured."""
        vsr = 1

        channel1 = self.test_fem.fem._extract_80_bits("ColumnEn_", vsr, 1, "Channel")
        assert channel1 == [-1]

        self.test_fem.fem.hexitec_parameters['Sensor-Config_V1_S1/ColumnEn_1stChannel'] = \
            '11111111111111111111'

        channel2 = self.test_fem.fem._extract_80_bits("ColumnEn_", vsr, 1, "Channel")
        assert channel2 == [-1]

        self.test_fem.fem.hexitec_parameters['Sensor-Config_V1_S1/ColumnEn_2ndChannel'] = \
            '11111111111111111111'

        channel3 = self.test_fem.fem._extract_80_bits("ColumnEn_", vsr, 1, "Channel")
        assert channel3 == [-1]

        self.test_fem.fem.hexitec_parameters['Sensor-Config_V1_S1/ColumnEn_3rdChannel'] = \
            '11111111111111111111'

        channel4 = self.test_fem.fem._extract_80_bits("ColumnEn_", vsr, 1, "Channel")
        assert channel4 == [-1]

    def test_extract_channel_data_fails_wrong_value_length(self):
        """Test function fails if provided value is a wrong length."""
        params = {'Sensor-Config_V1_S1/ColumnEn_1stChannel': '111111111111111111'}
        key = 'Sensor-Config_V1_S1/ColumnEn_1stChannel'
        self.test_fem.fem.hexitec_parameters[key] = '111111111111111111'

        with pytest.raises(HexitecFemError) as exc_info:
            first_channel = self.test_fem.fem.extract_channel_data(params, key)
            assert first_channel is None
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == "Invalid length of value in '%s'" % key

    def test_convert_to_aspect_format(self):
        """Test function works."""
        test_cases = [
            # (input, output1, output2)
            (0, 48, 48),
            (5, 48, 53),
            (137, 56, 57),
            (255, 70, 70),
            (366, 49, 54),
            (666, 50, 57),
            (1666, 54, 56),
            (3865, 70, 49)
        ]
        for avalue, expected_1, expected_2 in test_cases:
            with self.subTest(f"{avalue} -> {expected_1}, {expected_2}"):
                self.assertEqual((expected_1, expected_2),
                                 self.test_fem.fem.convert_to_aspect_format(avalue))

    def test_translate_to_normal_hex(self):
        """Test function work OK.

        See HexitecFem.HEX_ASCII_CODE for valid values
        """
        value = 0x30
        translated_value = self.test_fem.fem.translate_to_normal_hex(value)
        assert translated_value == 0

        value = 0x39
        translated_value = self.test_fem.fem.translate_to_normal_hex(value)
        assert translated_value == 9

        value = 0x41
        translated_value = self.test_fem.fem.translate_to_normal_hex(value)
        assert translated_value == 10

        value = 0x46
        translated_value = self.test_fem.fem.translate_to_normal_hex(value)
        assert translated_value == 15

    def test_translate_to_normal_hex_fails_invalid_values(self):
        """Test function fails if provided value is out of range."""
        bad_values = [0x2F, 0x3A, 0x40, 0x47]
        for value in bad_values:
            with pytest.raises(HexitecFemError) as exc_info:
                translated_value = self.test_fem.fem.translate_to_normal_hex(value)
                assert translated_value is None
            assert exc_info.type is HexitecFemError
            assert exc_info.value.args[0] == "Invalid Hexadecimal value {0:X}".format(value)

    def test_convert_hv_to_hex(self):
        """Test function works ok."""
        hv = 14
        rc = self.test_fem.fem.convert_hv_to_hex(hv)
        assert rc == 0x002D

    def test_convert_bias_to_dac_values(self):
        """Test function works ok."""
        hv = 15
        expected_values = (48, 48, 51, 49)
        hv_msb, hv_lsb = self.test_fem.fem.convert_bias_to_dac_values(hv)
        assert hv_msb, hv_lsb == expected_values

    # TODO Update
    @patch('hexitec_vsr.VsrModule')
    def test_hv_on(self, mocked_vsr_module):
        """Test function works ok."""
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.convert_bias_to_dac_values = Mock()
        self.test_fem.fem.convert_bias_to_dac_values.return_value = [[1, 2], [3, 4]]
        self.test_fem.fem.hv_bias_enabled = False
        self.test_fem.fem.hv_on()
        self.test_fem.fem.vsr_list[0].hv_on.assert_called()
        self.test_fem.fem.convert_bias_to_dac_values.assert_called()
        assert self.test_fem.fem.hv_bias_enabled is True

    def test_hv_on_fails_if_not_connected(self):
        """Test function fails if no camera connection."""
        self.test_fem.fem.hardware_connected = False
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.hv_on()
        assert exc_info.type is ParameterTreeError
        assert exc_info.value.args[0] == "Can't switch HV on without a connection"

    def test_hv_on_fails_if_hardware_busy(self):
        """Test function fails if hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.hv_on()
        assert exc_info.type is ParameterTreeError
        assert exc_info.value.args[0] == "Can't switch HV on, Hardware busy"

    @patch('hexitec_vsr.VsrModule')
    def test_hv_off(self, mocked_vsr_module):
        """Test function works ok."""
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.hv_bias_enabled = True
        self.test_fem.fem.hv_off()
        self.test_fem.fem.vsr_list[0].hv_off.assert_called()
        assert self.test_fem.fem.hv_bias_enabled is False

    def test_hv_off_fails_if_not_connected(self):
        """Test function fails if no camera connection."""
        self.test_fem.fem.hardware_connected = False
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.hv_off()
        assert exc_info.type is ParameterTreeError
        assert exc_info.value.args[0] == "Can't switch HV off without a connection"

    def test_hv_off_fails_if_hardware_busy(self):
        """Test function fails if hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem.hv_off()
        assert exc_info.type is ParameterTreeError
        assert exc_info.value.args[0] == "Can't switch HV off, Hardware busy"

    def test_reset_error(self):
        """Test function works ok."""
        self.test_fem.fem._set_status_message("Some Error")
        self.test_fem.fem.reset_error()
        assert self.test_fem.fem._get_status_error() == ""

    def test_create_iso_timestamp(self):
        """Test function works ok."""
        timestamp = datetime.now(timezone.utc).astimezone().isoformat()
        ts = self.test_fem.fem.create_iso_timestamp()
        # Omit last 9 characters as microseconds differ (timezone info form final 6 characters)
        assert timestamp[:-9] == ts[:-9]


class TestHexitecFem(unittest.TestCase):

    def setUp(self):
        self.parent = MagicMock()
        self.config = {"farm_mode": "farm_mode.json"}
        self.test_fem = HexitecFem(self.parent, self.config)

    @patch("builtins.open", new_callable=mock_open, read_data='{"camera_ctrl_ip": 10.0.1.100}')
    def test_load_farm_mode_json_parameters_handles_json_decode_error(self, mock_open):
        with self.assertRaises(HexitecFemError) as context:
            self.test_fem.load_farm_mode_json_parameters()
        self.assertIn("Farm Mode: Bad json:", str(context.exception))

    @patch("psutil.net_if_addrs")
    def test_extract_interface_parameters_success(self, mock_net_if_addrs):
        mock_net_if_addrs.return_value = {
            "eth0": [
                MagicMock(family="AddressFamily.AF_INET", address="10.0.1.1"),
                MagicMock(family="AddressFamily.AF_PACKET", address="00:11:22:33:44:55")
            ]
        }
        ip_address, mac_address = self.test_fem.extract_interface_parameters("eth0")
        self.assertEqual(ip_address, "10.0.1.1")
        self.assertEqual(mac_address, "00:11:22:33:44:55")

    @patch("psutil.net_if_addrs")
    def test_extract_interface_parameters_handles_unknown_interface(self, mock_net_if_addrs):
        mock_net_if_addrs.return_value = {
            "eth0": [
                MagicMock(family="AddressFamily.AF_INET", address="10.0.1.1"),
                MagicMock(family="AddressFamily.AF_PACKET", address="00:11:22:33:44:55")
            ]
        }
        with self.assertRaises(HexitecFemError) as context:
            self.test_fem.extract_interface_parameters("eth1")
        self.assertIn("Unknown interface: 'eth1'!", str(context.exception))

    @patch("psutil.net_if_addrs")
    def test_extract_interface_parameters_handles_no_ip_address(self, mock_net_if_addrs):
        mock_net_if_addrs.return_value = {
            "eth0": [
                MagicMock(family="AddressFamily.AF_PACKET", address="00:11:22:33:44:55")
            ]
        }
        with self.assertRaises(ParameterTreeError) as context:
            self.test_fem.extract_interface_parameters("eth0")
        self.assertIn("Control Interface 'eth0' couldn't parse IP from 'None';Check power?", str(context.exception))

    @patch("psutil.net_if_addrs")
    def test_extract_interface_parameters_handles_no_mac_address(self, mock_net_if_addrs):
        mock_net_if_addrs.return_value = {
            "eth0": [
                MagicMock(family="AddressFamily.AF_INET", address="10.0.1.1")
            ]
        }
        with self.assertRaises(ParameterTreeError) as context:
            self.test_fem.extract_interface_parameters("eth0")
        self.assertIn("Control Interface 'eth0' couldn't parse MAC from 'None';Check power?", str(context.exception))
