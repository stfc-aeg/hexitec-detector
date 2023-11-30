"""
Test Cases for the Hexitec Fem in hexitec.

Christian Angelsen, STFC Detector Systems Software Group
"""

import unittest
import pytest
import time
import sys
import os

from hexitec.HexitecFem import HexitecFem, HexitecFemError
from hexitec.adapter import HexitecAdapter
from hexitec_vsr.VsrModule import VsrModule

from json.decoder import JSONDecodeError
from socket import error as socket_error
from datetime import datetime

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, call, patch, mock_open
else:                         # pragma: no cover
    from mock import Mock, call, patch


class FemTestFixture(object):
    """Set up a text fixture."""

    def __init__(self):
        """Initialise object."""
        self.ip = "127.0.0.1"

        self.options = {
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

        # Construct paths relative to current working directory
        cwd = os.getcwd()
        base_path_index = cwd.rfind("hexitec-detector")
        base_path = cwd[:base_path_index]
        self.odin_control_path = base_path + "hexitec-detector/control"
        self.odin_data_path = base_path + "hexitec-detector/data"


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
        with patch('json.load') as mock_load:
            with patch("builtins.open", mock_open(read_data="data")):
                # self.test_fem.fem.verify_farm_mode_parameters = Mock()
                mock_load.return_value = farm_mode_json
                self.test_fem.fem.prepare_farm_mode()
        self.test_fem.fem.verify_parameters = True

    def tearDown(self):
        """Tear down test fixture after each unit test."""
        del self.test_fem

    # def test_connect(self):
    #     """Assert the connect method creates the rdma as expected."""
    #     with patch("hexitec.HexitecFem.RdmaUDP") as mock_rdma:
    #         self.test_fem.fem.connect()

    #         mock_rdma.assert_called_with(local_ip='127.0.0.1', local_port=61649,
    #                                      rdma_ip='127.0.0.1', rdma_port=61648,
    #                                      debug=False)

    def test_connect_fails(self):
        """Assert the connect method Exception handling works."""
        with patch('hexitec.HexitecFem.RdmaUDP') as rdma_mock:
            rdma_mock.side_effect = socket_error()
            with pytest.raises(socket_error) as exc_info:
                self.test_fem.fem.connect()
            assert exc_info.type is socket_error
            assert exc_info.value.args[0] == "Failed to setup Control connection: "

    def test_get_log_messages_display_new_messages(self):
        """Test the function displays new messages."""
        datestamp = self.test_fem.fem.create_timestamp()
        log_messages = [(datestamp, 'Initialised OK.')]
        self.test_fem.fem.last_message_timestamp = "something"
        self.test_fem.fem.get_log_messages("")
        # Test part of timestamp, as milliseconds will not agree anyway
        assert self.test_fem.fem.log_messages[0][:-4] == log_messages[0][:-4]
        assert self.test_fem.fem.log_messages[0][1] == log_messages[0][1]

    def test_get_log_messages_display_all_messages(self):
        """Test the function displays all messages."""
        datestamp = self.test_fem.fem.create_timestamp()
        log_messages = [(datestamp, 'Initialised OK.')]
        self.test_fem.fem.get_log_messages("")
        # Test part of timestamp, as milliseconds will not agree anyway
        assert self.test_fem.fem.log_messages[0][:-4] == log_messages[0][:-4]
        assert self.test_fem.fem.log_messages[0][1] == log_messages[0][1]

    # TODO Update when Hardware available to test firmware info
    def test_read_sensorsworking_ok(self):
        """Test the read_sensors function works."""
        with patch('hexitec.HexitecFem.RdmaUDP'):
            self.test_fem.fem.vsr_addr = 144
            self.test_fem.fem.read_firmware_version = True
            # firmware_date = "11/03/2020"
            # firmware_time = "09:43"
            self.test_fem.fem.x10g_rdma.read = Mock()
            self.test_fem.fem.x10g_rdma.read.side_effect = [285417504, 2371]
            self.test_fem.fem.read_temperatures_humidity_values = Mock()
            # self.test_fem.fem.read_temperatures
            self.test_fem.fem.read_pwr_voltages = Mock()
            self.test_fem.fem.read_sensors()
            time.sleep(0.2)
            assert self.test_fem.fem.vsr_addr == 144
            assert self.test_fem.fem.environs_in_progress is False
            assert self.test_fem.fem.parent.software_state == "Idle"
            # assert self.test_fem.fem.firmware_date == firmware_date
            # assert self.test_fem.fem.firmware_time == firmware_time
            # assert self.test_fem.fem.read_firmware_version is False
            # assert self.test_fem.fem.firmware_date == ""

    # @pytest.mark.slow
    def test_read_sensors_Exception(self):
        """Test the read_sensors handles Exception."""
        with patch('hexitec.HexitecFem.RdmaUDP'):
            self.test_fem.fem.read_firmware_version = False
            self.test_fem.fem.read_temperatures_humidity_values = Mock()
            self.test_fem.fem.read_temperatures_humidity_values.side_effect = Exception()
            self.test_fem.fem.read_sensors()
            time.sleep(0.5)
            error = "Reading sensors failed"
            assert self.test_fem.fem._get_status_error() == error

    # @pytest.mark.slow
    def test_read_sensors_HexitecFemError(self):
        """Test the read_sensors handles HexitecFemError."""
        with patch('hexitec.HexitecFem.RdmaUDP'):
            self.test_fem.fem.read_firmware_version = False
            self.test_fem.fem.read_temperatures_humidity_values = Mock()
            self.test_fem.fem.read_temperatures_humidity_values.side_effect = HexitecFemError()
            self.test_fem.fem.read_sensors()
            time.sleep(0.5)
            error = "Failed to read sensors"
            assert self.test_fem.fem._get_status_error() == error
        assert self.test_fem.fem.parent.software_state == "Error"

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
        self.test_fem.fem.duration_enabled = True
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

    # def test_poll_sensors_calls_self(self):
    #     """Test poll_sensors() calls itself."""
    #     with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
    #         self.test_fem.fem.poll_sensors()
    #         mock_loop.instance().call_later.assert_called_with(3.0, self.test_fem.fem.poll_sensors)

    def test_connect_hardware_already_connected_fails(self):
        """Test that connecting with connection already established handles failure."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.connect_hardware()
        assert self.test_fem.fem._get_status_error() == "Connection Error: Connection already established"

    def test_connect_hardware_handles_Exception(self):
        """Test that connecting with hardware handles failure."""
        self.test_fem.fem.configure_camera_interfaces = Mock(side_effect=HexitecFemError(""))
        self.test_fem.fem.connect_hardware()
        assert self.test_fem.fem._get_status_error() == "Connection Error"

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
        self.test_fem.fem.farm_mode_file = "/no/such/file.txt"
        with pytest.raises(HexitecFemError) as exc_info:
            rc = self.test_fem.fem.load_farm_mode_json_parameters()

    def test_load_farm_mode_json_parameters_handles_json_decode_exception(self):
        """Test that function handles JSON Decode Exception."""
        self.test_fem.fem.farm_mode_file = "odin_config.json"   # Contains invalid json
        with pytest.raises(HexitecFemError) as exc_info:
            rc = self.test_fem.fem.load_farm_mode_json_parameters()

    def test_verify_farm_mode_parameters(self):
        """Test that Farm mode parameters can be verified."""
        self.test_fem.fem.verify_farm_mode_parameters("lo")
        ip = '127.0.0.1'
        mac = '00:00:00:00:00:00'
        assert self.test_fem.fem.server_ctrl_ip == ip
        assert self.test_fem.fem.server_ctrl_mac == mac
        assert self.test_fem.fem.number_nodes == 2

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
            rc = self.test_fem.fem.extract_interface_parameters("invalid_iface")

    def test_extract_string_parameters_handles_exception(self):
        """Test that function handles Exception."""
        with pytest.raises(HexitecFemError) as exc_info:
            rc = self.test_fem.fem.extract_string_parameters(["list", "not_supported"])

    def test_prepare_hardware(self):
        """Test prepare hardware work OK."""
        self.test_fem.fem.prepare_farm_mode = Mock(return_value=True)
        self.test_fem.fem.configure_camera_interfaces = Mock()
        with patch("hexitec.HexitecFem.RdmaUDP"):
            success = self.test_fem.fem.prepare_hardware()
            assert success is True

    def test_prepare_hardware_handles_error(self):
        """Test prepare hardware handle error(s)."""
        self.test_fem.fem.prepare_farm_mode = Mock(return_value=False)
        self.test_fem.fem.power_up_modules = Mock()
        with patch("hexitec.HexitecFem.RdmaUDP"):
            success = self.test_fem.fem.prepare_hardware()
            assert success is False

    # def test
    def test_initialise_hardware_fails_if_not_connected(self):
        """Test function fails when no connection established."""
        self.test_fem.fem.initialise_hardware()
        error = "Failed to initialise camera: No connection established"
        assert self.test_fem.fem._get_status_error() == error

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
            mock_loop.instance().call_later.assert_called_with(10, self.test_fem.fem.cam_connect_completed)

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
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True

        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.power_up_modules()
        assert exc_info.type is HexitecFemError
        assert self.test_fem.fem.hardware_connected is False
        assert self.test_fem.fem.hardware_busy is False

    def test_initialise_hardware_fails_if_hardware_busy(self):
        """Test function fails when hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        self.test_fem.fem.initialise_hardware()
        error = "Failed to initialise camera: Can't initialise, Hardware busy"
        assert self.test_fem.fem.status_error == error

    def test_collect_data_fails_on_hardware_busy(self):
        """Test function fails when hardware already busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        self.test_fem.fem.ignore_busy = False
        self.test_fem.fem.collect_data()
        error = "Failed to collect data: Hardware sensors busy initialising"
        assert self.test_fem.fem._get_status_error() == error

    def test_collect_data_fails_without_connection(self):
        """Test function fails without established hardware connection."""
        self.test_fem.fem.hardware_connected = False
        self.test_fem.fem.collect_data()
        error = "Failed to collect data: No connection established"
        assert self.test_fem.fem._get_status_error() == error

    def test_collect_data_fails_on_exception(self):
        """Test function can handle unexpected exception."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.acquire_data = Mock()
        self.test_fem.fem.acquire_data.side_effect = AttributeError()
        self.test_fem.fem.collect_data()
        error = "Data collection failed"
        assert self.test_fem.fem.status_error == error

    def test_collect_data_works(self):
        """Test function works all right."""
        # Ensure correct circumstances
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.ignore_busy = True
        # Reset variables, to be checked post run
        self.test_fem.fem.acquisition_completed = False
        self.test_fem.fem.acquire_data = Mock()
        self.test_fem.fem.collect_data()
        assert self.test_fem.fem.hardware_busy is True
        self.test_fem.fem.acquire_data.assert_called()

    def test_disconnect_hardware(self):
        """Test the function works ok."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.disconnect_hardware()
        assert self.test_fem.fem.hardware_connected is False

    def test_disconnect_hardware_fails_without_connection(self):
        """Test function fails without established hardware connection."""
        self.test_fem.fem.hardware_connected = False
        self.test_fem.fem.disconnect_hardware()
        error = "Failed to disconnect: No connection to disconnect"
        assert self.test_fem.fem._get_status_error() == error

    def test_disconnect_hardware_handle_hardware_stuck(self):
        """Test function can handle if acquisition's stuck."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        self.test_fem.fem.cam_disconnect = Mock()
        self.test_fem.fem.disconnect_hardware()
        assert self.test_fem.fem.stop_acquisition is True

    def test_disconnect_hardware_handle_exception(self):
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
        self.test_fem.fem.cam_connect_completed()
        assert self.test_fem.fem.hardware_busy is False
        assert self.test_fem.fem.parent.software_state == "Idle"

    def test_cam_disconnect(self):
        """Test function works ok."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.disconnect = Mock()
        self.test_fem.fem.cam_disconnect()

    @patch('hexitec_vsr.VsrModule')
    def test_cam_disconnect_fails_network_error(self, mocked_vsr_module):
        """Test function handles socket error."""
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.vsr_list[0].disable_vsr.side_effect = socket_error()

        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.cam_disconnect()
        assert exc_info.type is HexitecFemError
        assert self.test_fem.fem.hardware_connected is False

    @patch('hexitec_vsr.VsrModule')
    def test_cam_disconnect_fails_attribute_error(self, mocked_vsr_module):
        """Test function handles attribute error."""
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.vsr_list[0].disable_vsr.side_effect = AttributeError()

        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.cam_disconnect()
        assert exc_info.type is HexitecFemError
        assert self.test_fem.fem.hardware_connected is False

    def test_acquire_data(self):
        """Test function handles normal configuration."""
        DATE_FORMAT = self.test_fem.fem.DATE_FORMAT
        acquire_start_time = '%s' % (datetime.now().strftime(DATE_FORMAT))
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.acquire_data()
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.1, self.test_fem.fem.check_acquire_finished)
            # Don't compare last 5 chars as corresponds to < 100 milliseconds:
            assert self.test_fem.fem.acquire_start_time[:-5] == acquire_start_time[:-5]

    def test_acquire_data_handles_exception(self):
        """Test function handles exception."""
        with patch("hexitec.HexitecFem.IOLoop"):
            with patch("time.time") as mock_time:
                mock_time.side_effect = Exception()
                with pytest.raises(Exception) as exc_info:
                    self.test_fem.fem.acquire_data()
                assert exc_info.type is Exception

    def test_check_acquire_finished_handles_cancel(self):
        """Test check_acquire_finished calls acquire_data_completed if acquire cancelled."""
        with patch("hexitec.HexitecFem.IOLoop"):
            self.test_fem.fem.stop_acquisition = True
            self.test_fem.fem.acquire_data_completed = Mock()

            self.test_fem.fem.check_acquire_finished()
            self.test_fem.fem.acquire_data_completed.assert_called()
            # assert self.test_fem.fem.acquisition_completed is True

    # TODO Modify/remove?
    # def test_check_acquire_finished_handles_data_being_sent(self):
    #     """Test check_acquire_finished calls itself while data being transferred."""
    #     with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
    #         self.test_fem.fem.stop_acquisition = False
    #         # TODO: Faking all_data_sent = 0 (ongoing) until firmware can readout data..
    #         self.test_fem.fem.all_data_sent = 0
    #         # self.test_fem.fem.x10g_rdma.read = Mock()
    #         # self.test_fem.fem.x10g_rdma.read.side_effect = [1]  # >0 Signals all data sent
    #         # self.test_fem.fem.acquire_data_completed = Mock()
    #         self.test_fem.fem.check_acquire_finished()
    #         i = mock_loop.instance()
    #         i.call_later.assert_called_with(0.5, self.test_fem.fem.check_acquire_finished)

    def test_check_acquire_finished_handles_data_transmission_complete(self):
        """Test check_acquire_finished handles data transmited."""
        self.test_fem.fem.stop_acquisition = False
        # TODO: Faking all_data_sent = 1 (done) until firmware can readout data..
        self.test_fem.fem.all_data_sent = 1
        self.test_fem.fem.acquire_data_completed = Mock()
        self.test_fem.fem.check_acquire_finished()
        self.test_fem.fem.acquire_data_completed.assert_called()

    # TODO: revisit and fix
    # # def test_check_acquire_finished_handles_negative_duration_remaining(self):
    # #     """Test check_acquire_finished handles data sent, edge case of 'negative' duration."""
    # #     # Because polling at 1Hz, will reached -0.1s once all data sent,
    # #     #   which is 'rounded' to 0.0
    # #     with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
    # #         self.test_fem.fem.stop_acquisition = False
    # #         self.test_fem.fem.x10g_rdma.read = Mock()
    # #         self.test_fem.fem.x10g_rdma.read.side_effect = [0]  # >0 Signals all data sent
    # #         self.test_fem.fem.duration_enabled = True
    # #         self.test_fem.fem.duration = 0.0
    # #         self.test_fem.fem.check_acquire_finished()
    # #         instance = mock_loop.instance().
    # #         instance.call_later.assert_called_with(0.1,
    # #                                                self.test_fem.fem.check_acquire_finished)
    # #         assert self.test_fem.fem.waited == 0.1
    # #         assert self.test_fem.fem.duration_remaining == 0.0

    def test_check_acquire_finished_handles_HexitecFemError(self):
        """Test check_acquire_finished handles HexitecFemError exception."""
        self.test_fem.fem.stop_acquisition = True
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
        self.test_fem.fem.stop_acquisition = True
        self.test_fem.fem.acquisition_completed = False
        self.test_fem.fem.acquire_data_completed = Mock()
        e_msg = "Badder Error"
        self.test_fem.fem.acquire_data_completed.side_effect = Exception(e_msg)

        self.test_fem.fem.check_acquire_finished()
        error = "Data collection failed: {}".format(e_msg)
        assert self.test_fem.fem._get_status_error() == error
        assert self.test_fem.fem.acquisition_completed is True

    def test_acquire_data_completed_handles_manual_stop(self):
        """Test function handles user stopping acquisition."""
        self.test_fem.fem.stop_acquisition = True
        self.test_fem.fem.send_cmd = Mock()

        self.test_fem.fem.acquire_data_completed()

        assert self.test_fem.fem.stop_acquisition is False
        assert self.test_fem.fem.hardware_busy is False
        assert self.test_fem.fem.acquisition_completed is True

    def test_acquire_data_completed_works(self):
        """Test function handles normal end of acquisition."""
        DATE_FORMAT = self.test_fem.fem.DATE_FORMAT
        self.test_fem.fem.acquire_start_time = '%s' % (datetime.now().strftime(DATE_FORMAT))
        self.test_fem.fem.acquire_data_completed()
        assert self.test_fem.fem.hardware_busy is False
        assert self.test_fem.fem.acquisition_completed is True
        assert self.test_fem.fem.parent.software_state == "Idle"
        # TODO: usually takes ~2.6e-05s, better way to test this?
        # assert pytest.approx(self.test_fem.fem.acquire_time) == 0.01

    # @pytest.mark.slow
    def test_collect_offsets_handles_hardware_disconnected(self):
        """Test function handles hardware disconnected."""
        self.test_fem.fem.hardware_connected = False
        self.test_fem.fem.collect_offsets()
        time.sleep(0.1)
        error = \
            "Offsets: Can't collect offsets while disconnected"
        assert self.test_fem.fem._get_status_error() == error

    # @pytest.mark.slow
    def test_collect_offsets_handles_hardware_busy(self):
        """Test function handles hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        self.test_fem.fem.collect_offsets()
        time.sleep(0.1)
        error = "Offsets: Can't collect offsets, Hardware busy"
        assert self.test_fem.fem._get_status_error() == error

    # TODO Modify/remove?
    # # @pytest.mark.slow
    # def test_collect_offsets_fails_unknown_exception(self):
    #     """Test function fails unexpected exception."""
    #     self.test_fem.fem.hardware_connected = True
    #     self.test_fem.fem.hardware_busy = False
    #     self.test_fem.fem.send_cmd = Mock()
    #     self.test_fem.fem.send_cmd.side_effect = AttributeError()
    #     self.test_fem.fem.collect_offsets()
    #     time.sleep(0.1)
    #     error = "Failed to collect offsets"
    #     assert self.test_fem.fem.status_error == error

    # # def test_load_pwr_cal_read_enables_fails_unknown_vsr(self):
    # #     """Test function handles unknown VSR address."""
    # #     vsr_addr = 25
    # #     self.test_fem.fem.vsr_addr = vsr_addr
    # #     with pytest.raises(HexitecFemError) as exc_info:
    # #         self.test_fem.fem.load_pwr_cal_read_enables()
    # #     assert exc_info.type is HexitecFemError
    # #     assert exc_info.value.args[0] == "Unknown VSR address! (%s)" % vsr_addr

    # def test_write_dac_values(self):
    #     """Test function handles writing dac values ok."""
    #     self.test_fem.fem.send_cmd = Mock()
    #     vsr_addr = HexitecFem.VSR_ADDRESS[1]
    #     self.test_fem.fem.vsr_addr = vsr_addr

    #     params = \
    #         {'Control-Settings/VCAL': '0.3',
    #          'Control-Settings/Uref_mid': '1,000000E+3'}

    #     self.test_fem.fem.hexitec_parameters = params
    #     self.test_fem.fem.write_dac_values(vsr_addr)

    #     vcal = [0x30, 0x31, 0x39, 0x39]
    #     umid = [0x30, 0x35, 0x35, 0x36]
    #     hv = [0x30, 0x35, 0x35, 0x35]
    #     dctrl = [0x30, 0x30, 0x30, 0x30]
    #     rsrv2 = [0x30, 0x38, 0x45, 0x38]

    #     scommand = [vsr_addr, self.test_fem.fem.WRITE_DAC_VAL,
    #                 vcal[0], vcal[1], vcal[2], vcal[3],
    #                 umid[0], umid[1], umid[2], umid[3],
    #                 hv[0], hv[1], hv[2], hv[3],
    #                 dctrl[0], dctrl[1], dctrl[2], dctrl[3],
    #                 rsrv2[0], rsrv2[1], rsrv2[2], rsrv2[3]]

    #     self.test_fem.fem.send_cmd.assert_has_calls([call(scommand)])

    def test_initialise_hardware_fails_unknown_exception(self):
        """Test function fails unexpected exception."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.initialise_system = Mock()
        self.test_fem.fem.initialise_system.side_effect = AttributeError()
        self.test_fem.fem.initialise_hardware()
        error = "Camera initialisation failed"
        assert self.test_fem.fem.status_error == error

    # # @pytest.mark.slow
    # def test_initialise_system(self):
    #     """Test function initialises the system ok."""
    #     self.test_fem.fem.initialise_vsr = Mock()
    #     self.test_fem.fem.read_register89 = Mock()
    #     self.test_fem.fem.debugging_function = Mock()
    #     # TODO: Work out which values system normally return...:
    #     self.test_fem.fem.read_register89.return_value = [[6, 6, 6, 6, 6, 6], "666666"]
    #     self.test_fem.fem.x10g_rdma.write = Mock()
    #     self.test_fem.fem.x10g_rdma.read = Mock()
    #     self.test_fem.fem.x10g_rdma.read.return_value = [0xFF]

    #     self.test_fem.fem.initialise_system()
    #     time.sleep(0.5)
    #     # self.test_fem.fem.x10g_rdma.write.assert_has_calls([
    #     #     call(0x00000020, 0x10, burst_len=1, comment="Enabling training"),
    #     #     call(0x00000020, 0x00, burst_len=1, comment="Disabling training")
    #     # ])
    #     time.sleep(0.5)
    #     vsr_status_addr = 0x000003E8
    #     index = 0
    #     self.test_fem.fem.x10g_rdma.read.assert_has_calls([
    #         call(vsr_status_addr, burst_len=1, comment="Read vsr{}_status".format(index)),
    #         call(vsr_status_addr+4, burst_len=1, comment="Read vsr{}_status".format(index+1)),
    #         call(vsr_status_addr+8, burst_len=1, comment="Read vsr{}_status".format(index+2)),
    #         call(vsr_status_addr+12, burst_len=1, comment="Read vsr{}_status".format(index+3)),
    #         call(vsr_status_addr+16, burst_len=1, comment="Read vsr{}_status".format(index+4)),
    #         call(vsr_status_addr+20, burst_len=1, comment="Read vsr{}_status".format(index+5)),
    #     ])
    #     assert self.test_fem.fem.parent.software_state == "Idle"

    # def test_initialise_system_flags_unsynced_vsr(self):
    #     """Test function handles an unsynced vsr."""
    #     self.test_fem.fem.initialise_vsr = Mock()
    #     self.test_fem.fem.read_register89 = Mock()
    #     self.test_fem.fem.debugging_function = Mock()
    #     self.test_fem.fem.read_register89.return_value = [[6, 6, 6, 6, 6, 6], "666666"]
    #     self.test_fem.fem.x10g_rdma.write = Mock()
    #     self.test_fem.fem.x10g_rdma.read = Mock()
    #     self.test_fem.fem.x10g_rdma.read.return_value = [0xF0]

    #     self.test_fem.fem.initialise_system()
    #     time.sleep(0.5)
    #     self.test_fem.fem.x10g_rdma.write.assert_has_calls([
    #         call(0x00000020, 0x10, burst_len=1, comment="Enabling training"),
    #         call(0x00000020, 0x00, burst_len=1, comment="Disabling training")
    #     ])
    #     time.sleep(0.5)
    #     vsr_status_addr = 0x000003E8
    #     index = 0
    #     self.test_fem.fem.x10g_rdma.read.assert_has_calls([
    #         call(vsr_status_addr, burst_len=1, comment="Read vsr{}_status".format(index)),
    #         call(vsr_status_addr+4, burst_len=1, comment="Read vsr{}_status".format(index+1)),
    #         call(vsr_status_addr+8, burst_len=1, comment="Read vsr{}_status".format(index+2)),
    #         call(vsr_status_addr+12, burst_len=1, comment="Read vsr{}_status".format(index+3)),
    #         call(vsr_status_addr+16, burst_len=1, comment="Read vsr{}_status".format(index+4)),
    #         call(vsr_status_addr+20, burst_len=1, comment="Read vsr{}_status".format(index+5)),
    #     ])

    def test_initialise_system_handles_HexitecFemError(self):
        """Test function handles HexitecFemError."""
        self.test_fem.fem.initialise_vsr = Mock()
        self.test_fem.fem.initialise_vsr.side_effect = HexitecFemError("E")
        self.test_fem.fem.initialise_system()
        time.sleep(0.5)
        assert self.test_fem.fem.status_error == "Failed to initialise camera: {}".format("E")

    def test_initialise_system_handles_Exception(self):
        """Test function handles Exception."""
        self.test_fem.fem.initialise_vsr = Mock()
        self.test_fem.fem.initialise_vsr.side_effect = Exception("E")
        self.test_fem.fem.initialise_system()
        time.sleep(0.5)
        assert self.test_fem.fem.status_error == "Camera initialisation failed: {}".format("E")

    # # TODO: Prevent unrelated unit tests failing: ??
    # # test_read_sensors_Exception - AssertionError: assert '' == 'Uncaught Exc...sors failed: '
    # # test_read_sensors_HexitecFemError - AssertionError: assert '' == 'Failed to read sensors: '
    # # @pytest.mark.skip
    # def test_initialise_system_fails_if_unsynced(self):
    #     """Test function handles unsuccessful LVDS sync."""
    #     self.test_fem.fem.initialise_vsr = Mock()
    #     self.test_fem.fem.read_register89 = Mock()
    #     # self.test_fem.fem.debugging_function = Mock()
    #     self.test_fem.fem.read_register89.return_value = [[6, 6, 6, 6, 6, 6], "111111"]
    #     # with patch('time.sleep') as fake_sleep:
    #     #     fake_sleep.side_effect = None
    #     fake_sleep = patch('time.sleep')
    #     fake_sleep.start()
    #     with patch('logging.error') as mock_log:
    #         self.test_fem.fem.initialise_system()
    #         time.sleep(0.5)
    #         # assert self.test_fem.fem.status_error == "Failed to initialise camera"
    #         mock_log.assert_called()
    #     fake_sleep.stop()

    # def test_initialise_system_fails_if_unsynced(self):
    #     """Test function handles unsuccessful LVDS sync."""
    #     self.test_fem.fem.VSR_ADDRESS = []
    #     self.test_fem.fem.x10g_rdma.write = Mock()
    #     # self.test_fem.fem.debugging_function = Mock()
    #     # self.test_fem.fem.read_register89.return_value = [[6, 6, 6, 6, 6, 6], "111111"]
    #     # with patch('time.sleep') as fake_sleep:
    #     #     fake_sleep.side_effect = None
    #     fake_sleep = patch('time.sleep')
    #     fake_sleep.start()
    #     with patch('logging.error') as mock_log:
    #         self.test_fem.fem.initialise_system()
    #         time.sleep(0.5)
    #         # assert self.test_fem.fem.status_error == "Failed to initialise camera"
    #         mock_log.assert_called()
    #     fake_sleep.stop()

    def test_calculate_frame_rate(self):
        """Test calculate_frame_rate works."""
        row_s1 = 5
        s1_sph = 1
        sph_s2 = 5
        self.test_fem.fem.row_s1 = row_s1
        self.test_fem.fem.s1_sph = s1_sph
        self.test_fem.fem.sph_s2 = sph_s2
        self.test_fem.fem.duration_enabled = True
        self.test_fem.fem.calculate_frame_rate()
        duration = 2
        self.test_fem.fem.frame_rate = 0
        self.test_fem.fem.set_duration(duration)
        assert self.test_fem.fem.frame_rate == 7154.079227920547
        assert self.test_fem.fem.number_frames == 14308

    # def test_read_pwr_voltages_vsr1(self):
    #     """Test function handles power voltages ok."""
    #     self.test_fem.fem.send_cmd = Mock()
    #     response = [42, 144, 48, 50, 69, 53, 48, 53, 68, 48, 48, 56, 67, 66, 48, 48, 48, 52, 48,
    #                 67, 49, 49, 48, 70, 69, 56, 48, 55, 69, 50, 48, 56, 56, 66, 49, 50, 48, 67,
    #                 49, 65, 49, 65, 48, 48, 48, 50, 48, 48, 48, 48, 13]
    #     vsr_addr = HexitecFem.VSR_ADDRESS[0]
    #     self.test_fem.fem.vsr_addr = vsr_addr
    #     self.test_fem.fem.debug = True
    #     self.test_fem.fem.read_pwr_voltages()
    #     # Note current setting, change Register 143 (0x8F) -> 1, confirm changed
    #     power_command = [vsr_addr, HexitecFem.READ_PWR_VOLT]
    #     self.test_fem.fem.send_cmd.assert_has_calls([call(power_command)])
    #     assert self.test_fem.fem.hv_list[0] == -6.832187142856924

    # def test_read_pwr_voltages_bad_vsr(self):
    #     """Test function handles unexpected vsr."""
    #     vsr_addr = 151
    #     self.test_fem.fem.vsr_addr = vsr_addr
    #     self.test_fem.fem.debug = True
    #     with pytest.raises(HexitecFemError) as exc_info:
    #         self.test_fem.fem.read_pwr_voltages()
    #     assert exc_info.type is HexitecFemError
    #     assert exc_info.value.args[0] == "HV: Invalid VSR address(0x{0:02X})".format(vsr_addr)

    # def test_read_pwr_voltages_handles_incomplete_data(self):
    #     """Test function handles incomplete data received."""
    #     self.test_fem.fem.send_cmd = Mock()
    #     vsr_addr = HexitecFem.VSR_ADDRESS[0]
    #     response = [42, vsr_addr, 48, 50, 69, 54, 48, 53, 67, 13]
    #     self.test_fem.fem.vsr_addr = vsr_addr
    #     self.test_fem.fem.debug = True
    #     returned_value = self.test_fem.fem.read_pwr_voltages()
    #     assert returned_value is None

    # # TODO: Shortly redundant:
    # def test_read_temperatures_humidity_values_vsr1(self):
    #     """Test function handle sensor values ok."""
    #     self.test_fem.fem.send_cmd = Mock()
    #     vsr_addr = HexitecFem.VSR_ADDRESS[0]
    #     self.test_fem.fem.vsr_addr = vsr_addr
    #     self.test_fem.fem.debug = True
    #     self.test_fem.fem.read_temperatures_humidity_values()
    #     command = [vsr_addr, 0x52]
    #     vsr1_ambient = 22.7658837890625
    #     vsr1_humidity = 39.12855725947967
    #     vsr1_asic1 = 160.0
    #     vsr1_asic2 = 160.0
    #     vsr1_adc = 24.6875
    #     self.test_fem.fem.send_cmd.assert_has_calls([call(command)])
    #     assert self.test_fem.fem.ambient_list[0] == vsr1_ambient
    #     assert self.test_fem.fem.humidity_list[0] == vsr1_humidity
    #     assert self.test_fem.fem.asic1_list[0] == vsr1_asic1
    #     assert self.test_fem.fem.asic2_list[0] == vsr1_asic2
    #     assert self.test_fem.fem.adc_list[0] == vsr1_adc

    # def test_read_temperatures_humidity_values_bad_vsr(self):
    #     """Test function handle misconfigured VSR."""
    #     self.test_fem.fem.send_cmd = Mock()
    #     vsr_addr = 151  # HexitecFem.VSR_ADDRESS[5]
    #     self.test_fem.fem.vsr_addr = vsr_addr
    #     self.test_fem.fem.debug = True
    #     with pytest.raises(HexitecFemError) as exc_info:
    #         self.test_fem.fem.read_temperatures_humidity_values()
    #     assert exc_info.type is HexitecFemError
        # assert exc_info.value.args[0] == \
        #     "Sensors: Invalid VSR address(0x{0:02X})".format(vsr_addr)

    # def test_read_temperature_humidity_values_handle_wrong_value(self):
    #     """Test function handles bad sensor values."""
    #     self.test_fem.fem.send_cmd = Mock()
    #     return_value = self.test_fem.fem.read_temperatures_humidity_values()
    #     assert return_value is None

    # def test_read_temperature_humidity_values_handle_bad_vsr(self):
    #     """Test function handles bad sensor values."""
    #     self.test_fem.fem.send_cmd = Mock()
    #     return_value = self.test_fem.fem.read_temperatures_humidity_values()
    #     assert return_value is None

    def test_set_hexitec_config(self):
        """Test function handles configuration file ok."""
        filename = "control/test/hexitec/config/hexitec_test_config.ini"

        self.test_fem.fem.set_hexitec_config(filename)

        assert self.test_fem.fem.row_s1 == 25
        assert self.test_fem.fem.s1_sph == 13
        assert self.test_fem.fem.sph_s2 == 57
        assert self.test_fem.fem.bias_level == 15
        assert self.test_fem.fem.vsrs_selected == 63

    def test_set_hexitec_config_fails_invalid_filename(self):
        """Test function fails on invalid file name."""
        filename = "invalid/file.name"
        rc = self.test_fem.fem.set_hexitec_config(filename)
        error = "Cannot open provided hexitec file: [Errno 2] No such file or directory:"
        # Skipping end of status_error (beyond 71 characters) as file path irrelevant here
        assert self.test_fem.fem.status_error[:71] == error
        assert rc is None

    def test_set_hexitec_config_fails_missing_key(self):
        """Test function fails if filename misses a key."""
        filename = "control/test/hexitec/config/hexitec_test_config.ini"
        error = "INI File Key Error: artificial error"
        self.test_fem.fem._extract_integer = Mock()
        self.test_fem.fem._extract_integer.side_effect = HexitecFemError(error[20:])
        self.test_fem.fem.set_hexitec_config(filename)
        assert self.test_fem.fem.status_error == error

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

    def test_mask_aspect_encoding(self):
        """Test function handles a few sample masking tasks."""
        value_h, value_l = 0x31, 0x32
        resp = [0x32, 0x34]
        masked_h, masked_l = self.test_fem.fem.mask_aspect_encoding(value_h, value_l, resp)
        assert (masked_h, masked_l) == (0x33, 0x36)

        value_h, value_l = 0x31, 0x33
        resp = [0x45, 0x39]
        masked_h, masked_l = self.test_fem.fem.mask_aspect_encoding(value_h, value_l, resp)
        assert (masked_h, masked_l) == (0x46, 0x42)

    def test_convert_hex_to_hv(self):
        """Test function works ok."""
        hex_val = 0x0034
        rc = self.test_fem.fem.convert_hex_to_hv(hex_val)
        assert rc == 15.873015873015873

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
    # def test_hv_on(self):
    #     """Test function works ok."""
    #     self.test_fem.fem.send_cmd = Mock()
    #     self.test_fem.fem.convert_bias_to_dac_values = Mock()
    #     self.test_fem.fem.convert_bias_to_dac_values.return_value = [[1, 2], [3, 4]]
    #     self.test_fem.fem.hv_bias_enabled = False
    #     self.test_fem.fem.hv_on()
    #     self.test_fem.fem.send_cmd.assert_called()
    #     self.test_fem.fem.convert_bias_to_dac_values.assert_called()
    #     assert self.test_fem.fem.hv_bias_enabled is True

    @patch('hexitec_vsr.VsrModule')
    def test_hv_off(self, mocked_vsr_module):
        """Test function works ok."""
        vsr_list = [mocked_vsr_module]
        self.test_fem.fem.vsr_list = vsr_list
        self.test_fem.fem.hv_bias_enabled = True
        self.test_fem.fem.hv_off()
        self.test_fem.fem.vsr_list[0].hv_off.assert_called()
        assert self.test_fem.fem.hv_bias_enabled is False

    def test_environs(self):
        """Test function works ok."""
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.environs()
            i = mock_loop.instance()
            i.add_callback.assert_called_with(self.test_fem.fem.read_sensors)

    def test_reset_error(self):
        """Test function works ok."""
        self.test_fem.fem._set_status_message("Some Error")
        self.test_fem.fem.reset_error()
        assert self.test_fem.fem._get_status_error() == ""

    def test_create_timestamp(self):
        """Test function works ok."""
        timestamp = '{}'.format(datetime.now().strftime(HexitecFem.DATE_FORMAT))
        ts = self.test_fem.fem.create_timestamp()
        assert timestamp[:-4] == ts[:-4]
