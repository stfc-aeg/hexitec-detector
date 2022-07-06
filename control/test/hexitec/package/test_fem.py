"""
Test Cases for the Hexitec Fem in hexitec.

Christian Angelsen, STFC Detector Systems Software Group
"""

import unittest
import pytest
import sys
import os

from hexitec.HexitecFem import HexitecFem, HexitecFemError
from hexitec.adapter import HexitecAdapter

from odin.adapters.parameter_tree import ParameterTreeError

from socket import error as socket_error

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, call, patch, ANY
else:                         # pragma: no cover
    from mock import Mock, call, patch, ANY


class FemTestFixture(object):
    """Set up a text fixture."""

    def __init__(self):
        """Initialise object."""
        self.ip = "127.0.0.1"

        self.options = {
            "fem":
                """
                server_ctrl_ip = 127.0.0.1,
                camera_ctrl_ip = 127.0.0.1,
                server_data_ip = 127.0.0.1,
                camera_data_ip = 127.0.0.1
                """
        }

        # FPGA base addresses
        self.rdma_addr = {
            "receiver": 0xC0000000,
            "frm_gate": 0xD0000000,
            "reset_monitor": 0x90000000
        }

        with patch("hexitec.HexitecDAQ.ParameterTree"):
            self.adapter = HexitecAdapter(**self.options)
            self.detector = self.adapter.hexitec  # shortcut, makes assert lines shorter

            with patch("hexitec.HexitecFem.RdmaUDP"):
                self.fem = HexitecFem(self.detector, self.ip,
                                      self.ip, self.ip, self.ip)
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

    def test_connect(self):
        """Assert the connect method creates the rdma as expected."""
        with patch("hexitec.HexitecFem.RdmaUDP") as mock_rdma:
            self.test_fem.fem.connect()

            mock_rdma.assert_called_with(self.test_fem.ip, 61650,
                                         self.test_fem.ip, 61651,
                                         self.test_fem.ip, 61650,
                                         self.test_fem.ip, 61651,
                                         2000000, 9000, 20)
            assert self.test_fem.fem.x10g_rdma.ack is True

    def test_connect_fails(self):
        """Assert the connect method Exception handling works."""
        with patch('hexitec.HexitecFem.RdmaUDP') as rdma_mock:
            rdma_mock.side_effect = socket_error()
            with pytest.raises(socket_error) as exc_info:
                self.test_fem.fem.connect()
            assert exc_info.type is socket_error
            assert exc_info.value.args[0] == "Failed to setup Control connection: "

    def test_read_sensors_working_ok(self):
        """Test the read_sensors function works."""
        with patch('hexitec.HexitecFem.RdmaUDP'):
            self.test_fem.fem.vsr_addr = 144
            self.test_fem.fem.read_firmware_version = True
            firmware_date = "11/03/2020"
            firmware_time = "09:43"
            self.test_fem.fem.x10g_rdma.read = Mock()
            self.test_fem.fem.x10g_rdma.read.side_effect = [285417504, 2371]
            self.test_fem.fem.read_sensors()
            assert self.test_fem.fem.vsr_addr == 144
            assert self.test_fem.fem.firmware_date == firmware_date
            assert self.test_fem.fem.firmware_time == firmware_time
            # assert self.test_fem.fem.read_firmware_version is False
            # assert self.test_fem.fem.firmware_date == ""

    def test_read_sensors_Exception(self):
        """Test the read_sensors handles Exception."""
        with patch('hexitec.HexitecFem.RdmaUDP'):
            self.test_fem.fem.read_firmware_version = True
            self.test_fem.fem.x10g_rdma.read = Mock()
            self.test_fem.fem.x10g_rdma.read.side_effect = Exception()
            self.test_fem.fem.read_sensors()
            error = "Uncaught Exception; Reading sensors failed: "
            assert self.test_fem.fem._get_status_error() == error

    def test_read_sensors_HexitecFemError(self):
        """Test the read_sensors handles Exception."""
        with patch('hexitec.HexitecFem.RdmaUDP'):
            self.test_fem.fem.read_firmware_version = True
            self.test_fem.fem.x10g_rdma.read = Mock()
            self.test_fem.fem.x10g_rdma.read.side_effect = HexitecFemError()
            self.test_fem.fem.read_sensors()
            error = "Failed to read sensors: "
            assert self.test_fem.fem._get_status_error() == error

    def test_cleanup(self):
        """Test cleanup function works ok."""
        self.test_fem.fem.cleanup()
        self.test_fem.fem.x10g_rdma.close.assert_called_with()

    def test_set_image_size(self):
        """Test setting image size handled ok."""
        address_pixel_count = self.test_fem.rdma_addr['receiver'] | 0x01
        address_pixel_size = self.test_fem.rdma_addr['receiver'] + 4

        self.test_fem.fem.set_image_size(160, 160, 14, 16)

        assert self.test_fem.fem.image_size_x == 160
        assert self.test_fem.fem.image_size_y == 160
        assert self.test_fem.fem.image_size_p == 14
        assert self.test_fem.fem.image_size_f == 16

        pixel_count_max = (160 * 160) // 2
        data = (pixel_count_max & 0x1FFFF) - 1
        self.test_fem.fem.x10g_rdma.write.assert_has_calls(
            [call(address_pixel_count, data, ANY),
                call(address_pixel_size, 0x3, ANY)]
        )

        # Repeat for 80x80, single sensor?
        # self.test_fem.fem.set_image_size(102, 288, 11, 16)
        self.test_fem.fem.set_image_size(80, 80, 14, 16)

        assert self.test_fem.fem.image_size_x == 80
        assert self.test_fem.fem.image_size_y == 80
        assert self.test_fem.fem.image_size_p == 14
        assert self.test_fem.fem.image_size_f == 16

        pixel_count_max = (80 * 80) // 2
        data = (pixel_count_max & 0x1FFFF) - 1
        self.test_fem.fem.x10g_rdma.write.assert_has_calls(
            [call(address_pixel_count, data, ANY),
                call(address_pixel_size, 0x3, ANY)]
        )

    def test_set_image_size_wrong_pixel(self):
        """Test setting wrong pixel size handled ok."""
        self.test_fem.fem.set_image_size(102, 288, 0, 16)

        assert self.test_fem.fem.image_size_x == 102
        assert self.test_fem.fem.image_size_y == 288
        assert self.test_fem.fem.image_size_p == 0
        assert self.test_fem.fem.image_size_f == 16

        assert not self.test_fem.fem.x10g_rdma.write.called

    def test_data_stream(self):
        """Also covers frame_gate_settings(), frame_gate_trigger()."""
        frame_num = 10
        frame_gap = 0
        # data_stream subtracts 1 from frame_num before
        #   passing it onto frame_gate_settings
        self.test_fem.fem.data_stream(frame_num+1)

        self.test_fem.fem.x10g_rdma.write.assert_has_calls([
            call(self.test_fem.rdma_addr["frm_gate"] + 1, frame_num, ANY),
            call(self.test_fem.rdma_addr["frm_gate"] + 2, frame_gap, ANY),
            call(self.test_fem.rdma_addr["reset_monitor"], 0, ANY),
            call(self.test_fem.rdma_addr["reset_monitor"], 1, ANY),
            call(self.test_fem.rdma_addr["reset_monitor"], 0, ANY),
            call(self.test_fem.rdma_addr["frm_gate"], 0, ANY),
            call(self.test_fem.rdma_addr["frm_gate"], 1, ANY),
            call(self.test_fem.rdma_addr["frm_gate"], 0, ANY)
        ])

    def test_set_duration_enable(self):
        """Test set_duration_enable works."""
        self.test_fem.fem.duration_enabled = False
        self.test_fem.fem.set_duration_enable(True)
        assert self.test_fem.fem.duration_enabled is True

    def test_set_duration(self):
        """Test set_duration works."""
        # Ensure clocks configured
        row_s1 = 5
        s1_sph = 1
        sph_s2 = 5
        self.test_fem.fem.row_s1 = row_s1
        self.test_fem.fem.s1_sph = s1_sph
        self.test_fem.fem.sph_s2 = sph_s2
        self.test_fem.fem.calculate_frame_rate()
        duration = 1
        self.test_fem.fem.set_duration(duration)
        assert self.test_fem.fem.number_frames == 7154

    def test_get_health(self):
        """Test obtaining health variable works."""
        health = False
        self.test_fem.fem.health = health
        assert self.test_fem.fem.get_health() is health

    def test_poll_sensors_calls_self(self):
        """Test poll_sensors() calls itself after 1 seconds."""
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.hardware_connected = True
            self.test_fem.fem.hardware_busy = False
            self.test_fem.fem.poll_sensors()

            mock_loop.instance().call_later.assert_called_with(1.0, self.test_fem.fem.poll_sensors)

    def test_connect_hardware_fails(self):
        """Test that connecting with hardware handles failure."""
        with patch('hexitec.HexitecFem.RdmaUDP') as rdma_mock:

            # Fein error connecting to camera
            rdma_mock.side_effect = HexitecFemError()
            self.test_fem.fem.connect_hardware()

            assert self.test_fem.fem._get_status_error() == "Failed to connect with camera: "
            assert self.test_fem.fem._get_status_message() == "Is the camera powered?"

            # Fein unexpected Exception connecting to camera
            self.test_fem.fem.hardware_connected = False
            rdma_mock.side_effect = Exception()
            self.test_fem.fem.connect_hardware()

            error = "Uncaught Exception; Camera connection: "
            assert self.test_fem.fem._get_status_error() == error

        # Don't Mock, error because we couldn't setup a connection
        self.test_fem.fem.connect_hardware("test")
        assert self.test_fem.fem._get_status_error() == "Connection already established"

    def test_connect_hardware(self):
        """Test connecting with hardware works."""
        with patch("hexitec.HexitecFem.RdmaUDP"):

            self.test_fem.fem.connect_hardware("test")
            assert self.test_fem.fem.hardware_connected is True

    def test_initialise_hardware_fails_if_not_connected(self):
        """Test function fails when no connection established."""
        self.test_fem.fem.initialise_hardware()
        error = "Failed to initialise camera: No connection established"
        assert self.test_fem.fem._get_status_error() == error

    def test_initialise_hardware_fails_if_hardware_busy(self):
        """Test function fails when hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        self.test_fem.fem.initialise_hardware()
        error = "Failed to initialise camera: Hardware sensors busy initialising"
        assert self.test_fem.fem.status_error == error

    def test_initialise_hardware_fails_unknown_exception(self):
        """Test function fails unexpected exception."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.initialise_system = Mock()
        self.test_fem.fem.initialise_system.side_effect = AttributeError()
        self.test_fem.fem.initialise_hardware()
        error = "Uncaught Exception; Camera initialisation failed: "
        assert self.test_fem.fem.status_error == error

    def test_initialise_hardware_handles_fudge_initialisation(self):
        """Test function handles initialisation from cold."""
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:

            self.test_fem.fem.hardware_connected = True
            self.test_fem.fem.hardware_busy = False
            self.test_fem.fem.debug_register24 = False
            self.test_fem.fem.initialise_system = Mock()
            self.test_fem.fem.first_initialisation = True
            self.test_fem.fem.parent.daq = Mock(in_progress=False)
            self.test_fem.fem.parent.daq.prepare_odin = Mock()
            self.test_fem.fem.parent.daq.prepare_daq = Mock()
            self.test_fem.fem.initialise_hardware()
            self.test_fem.fem.parent.daq.prepare_daq.assert_called_with(2)
            mock_loop.instance().call_later.assert_called_with(0.1,
                                                               self.test_fem.fem.check_all_processes_ready)

    def test_initialise_hardware_handles_fudge_initialisation_prepare_odin_error(self):
        """Test cold initialisation handles prepare_odin error."""
        with patch("hexitec.HexitecFem.IOLoop"):

            self.test_fem.fem.hardware_connected = True
            self.test_fem.fem.hardware_busy = False
            self.test_fem.fem.debug_register24 = False
            self.test_fem.fem.initialise_system = Mock()
            self.test_fem.fem.first_initialisation = True
            self.test_fem.fem.parent.daq = Mock(in_progress=False)
            self.test_fem.fem.parent.daq.prepare_odin = Mock()
            self.test_fem.fem.parent.daq.prepare_odin = False
            self.test_fem.fem.parent.daq.prepare_daq = Mock()
            self.test_fem.fem.initialise_hardware()
            self.test_fem.fem.parent.daq.prepare_daq.assert_not_called()

    def test_check_all_processes_ready_handles_daq_error(self):
        """Test function handles daq error gracefully."""
        self.test_fem.fem.first_initialisation = True
        self.test_fem.fem.parent.daq.in_error = True
        self.test_fem.fem.check_all_processes_ready()

        assert self.test_fem.fem.hardware_busy is False
        assert self.test_fem.fem.ignore_busy is False

    def test_check_all_processes_ready_handles_daq_in_progress(self):
        """Test function handles daq in progress."""
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.parent.daq.in_error = False
            self.test_fem.fem.parent.daq.in_progress = False
            self.test_fem.fem.check_all_processes_ready()
            mock_loop.instance().call_later.assert_called_with(0.5,
                                                               self.test_fem.fem.check_all_processes_ready)

    def test_check_all_processes_ready_works(self):
        """Test function collect data in normal operation."""
        self.test_fem.fem.parent.daq.in_error = False
        self.test_fem.fem.parent.daq.in_progress = True
        self.test_fem.fem.collect_data = Mock()
        self.test_fem.fem.check_all_processes_ready()
        self.test_fem.fem.collect_data.assert_called()

    def test_initialise_hardware_handles_daq_busy(self):
        """Test function handles cold start with daq already busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.debug_register24 = False
        self.test_fem.fem.initialise_system = Mock()
        self.test_fem.fem.first_initialisation = True
        self.test_fem.fem.parent.daq = Mock(in_progress=True)
        self.test_fem.fem.initialise_hardware()

    def test_initialise_hardware_handles_warm_initialisation(self):
        """Test function handles fudge free initialisation."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.debug_register24 = False
        self.test_fem.fem.initialise_system = Mock()
        self.test_fem.fem.first_initialisation = False
        self.test_fem.fem.initialise_hardware()

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
        self.test_fem.fem.collect_data("test")
        assert self.test_fem.fem._get_status_error() == "Failed to collect data: No connection established"

    def test_collect_data_fails_on_exception(self):
        """Test function can handle unexpected exception."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.acquire_data = Mock()
        self.test_fem.fem.acquire_data.side_effect = AttributeError()
        self.test_fem.fem.collect_data()
        error = "Uncaught Exception; Data collection failed: "
        assert self.test_fem.fem.status_error == error

    def test_collect_data_works(self):
        """Test function works all right."""
        # Ensure correct circumstances
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.ignore_busy = True
        self.test_fem.fem.first_initialisation = True
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

    def test_disconnect_hardware_handle_hardware_stuck(self):
        """Test the function works ok."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        self.test_fem.fem.disconnect_hardware()
        assert self.test_fem.fem.hardware_connected is False
        assert self.test_fem.fem.stop_acquisition is True

    def test_disconnect_hardware_fails_without_connection(self):
        """Test function fails without established hardware connection."""
        self.test_fem.fem.hardware_connected = False
        self.test_fem.fem.disconnect_hardware()
        error = "Failed to disconnect: No connection to disconnect"
        assert self.test_fem.fem._get_status_error() == error

    def test_disconnect_hardware_fails_on_exception(self):
        """Test function can handle unexpected exception."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.cam_disconnect = Mock()
        self.test_fem.fem.cam_disconnect.side_effect = AttributeError()
        self.test_fem.fem.disconnect_hardware()
        error = "Uncaught Exception; Disconnection failed: "
        assert self.test_fem.fem._get_status_error() == error

    def test_accessor_functions(self):
        """Test access functions handle bools."""
        number_frames = 1001
        self.test_fem.fem.set_number_frames(number_frames)
        assert self.test_fem.fem.get_number_frames() == number_frames

        for bEnabled in True, False:
            self.test_fem.fem.set_debug(bEnabled)
            assert self.test_fem.fem.get_debug() == bEnabled

    def test_send_cmd(self):
        """Test send_cmd working ok."""
        self.test_fem.fem.debug = True
        cmd = [35, 144, 68, 65, 52, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70,
               70, 70, 70, 70, 70, 13, 13]
        encoded_value = [596657217, 877020742, 1179010630, 1179010630, 1179010630, 1179010630,
                         1175260429]
        self.test_fem.fem.send_cmd(cmd)

        self.test_fem.fem.x10g_rdma.write.assert_has_calls([
            call(0xE0000100, encoded_value[0], ANY),
            call(0xE0000100, encoded_value[1], ANY),
            call(0xE0000100, encoded_value[2], ANY),
            call(0xE0000100, encoded_value[3], ANY),
            call(0xE0000100, encoded_value[4], ANY),
            call(0xE0000100, encoded_value[5], ANY),
            call(0xE0000100, encoded_value[6], ANY)
        ])

    def test_read_response(self):
        """Test function works ok."""
        self.test_fem.fem.set_debug(True)
        return_values = [0, 714158145, 0, 808520973, 0, 13]
        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effect = return_values
        address = 0xE0000011
        status = self.test_fem.fem.read_response()
        self.test_fem.fem.x10g_rdma.read.assert_called_with(address, ANY)
        assert status == '\x910A01\r\r'

    def test_read_response_failed(self):
        """Test the function fails receiving badly formatted data."""
        self.test_fem.fem.x10g_rdma.read = Mock(return_value=1)
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.read_response()
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == "read_response aborted"

    def test_cam_connect(self):
        """Test function works ok."""
        self.test_fem.fem.connect = Mock()
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.cam_connect()

    def test_cam_connect_fails_network_error(self):
        """Test function handles socket error."""
        self.test_fem.fem.connect = Mock()
        self.test_fem.fem.connect.side_effect = socket_error()
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.cam_connect()
        assert exc_info.type is HexitecFemError
        assert self.test_fem.fem.hardware_connected is False

    def test_cam_disconnect(self):
        """Test function works ok."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.disconnect = Mock()
        self.test_fem.fem.cam_disconnect()

    def test_cam_disconnect_fails_network_error(self):
        """Test function handles socket error."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.send_cmd.side_effect = socket_error()

        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.cam_disconnect()
        assert exc_info.type is HexitecFemError
        assert self.test_fem.fem.hardware_connected is False

    def test_cam_disconnect_fails_attribute_error(self):
        """Test function handles attribute error."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.send_cmd.side_effect = AttributeError()
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.cam_disconnect()
        assert exc_info.type is HexitecFemError
        assert self.test_fem.fem.hardware_connected is False

    def test_initialise_sensor(self):
        """Test function works ok."""
        # Ensure appropriate configuration
        self.test_fem.fem.selected_sensor = self.test_fem.fem.OPTIONS[0]
        self.test_fem.fem.sensors_layout = self.test_fem.fem.READOUTMODE[1]
        self.test_fem.fem.read_response = Mock()
        self.test_fem.fem.send_cmd = Mock()

        empty_signals = 65535
        full_signals = 255
        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effect = [empty_signals, full_signals]
        self.test_fem.fem.initialise_sensor()

        self.test_fem.fem.x10g_rdma.write.assert_has_calls([
            call(0x60000002, 0, ANY),
            call(0x60000004, 0, ANY),
            call(0x60000001, 2, ANY),
        ])
        assert self.test_fem.fem.vsr_addr == self.test_fem.fem.VSR_ADDRESS[0]

    def test_initialise_sensor2(self):
        """Test function works ok, testing the path the previous function doesn't cover."""
        # Ensure appropriate configuration
        self.test_fem.fem.selected_sensor = self.test_fem.fem.OPTIONS[2]
        self.test_fem.fem.sensors_layout = self.test_fem.fem.READOUTMODE[0]
        self.test_fem.fem.read_response = Mock()
        self.test_fem.fem.send_cmd = Mock()

        empty_signals = 65535
        full_signals = 255
        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effect = [empty_signals, full_signals]
        self.test_fem.fem.initialise_sensor()

        self.test_fem.fem.x10g_rdma.write.assert_has_calls([
            call(0x60000002, 0, ANY),
            call(0x60000004, 4, ANY),
            call(0x60000001, 2, ANY),
        ])
        assert self.test_fem.fem.vsr_addr == self.test_fem.fem.VSR_ADDRESS[1]

    def test_calibrate_sensor_1_sensor(self):
        """Test function handles single sensor."""
        self.test_fem.fem.sensors_layout = self.test_fem.fem.READOUTMODE[0]
        self.test_fem.fem.vsr_addr = self.test_fem.fem.VSR_ADDRESS[1]
        self.test_fem.fem.selected_sensor = HexitecFem.OPTIONS[2]
        self.test_fem.fem.read_response = Mock(return_value="06")
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effects = 65535
        self.test_fem.fem.debug = True
        self.test_fem.fem.calibrate_sensor()
        assert self.test_fem.fem.image_size_x == 80
        assert self.test_fem.fem.image_size_y == 80

    def test_calibrate_sensor_2x2_sensors(self):
        """Test function handles 2x2 sensors."""
        self.test_fem.fem.sensors_layout = self.test_fem.fem.READOUTMODE[1]
        self.test_fem.fem.vsr_addr = self.test_fem.fem.VSR_ADDRESS[0]
        self.test_fem.fem.selected_sensor = HexitecFem.OPTIONS[0]
        self.test_fem.fem.read_response = Mock(return_value="06")
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effects = 65535
        self.test_fem.fem.debug = True
        self.test_fem.fem.calibrate_sensor()
        assert self.test_fem.fem.image_size_x == 160
        assert self.test_fem.fem.image_size_y == 160

    def test_calibrate_sensor_fails_wrong_rdma_read(self):
        """Test function handles rdma read return wrong value."""
        self.test_fem.fem.sensors_layout = self.test_fem.fem.READOUTMODE[1]
        self.test_fem.fem.selected_sensor = HexitecFem.OPTIONS[0]
        self.test_fem.fem.read_response = Mock(return_value="01")
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effects = 65535

        with patch('time.sleep') as fake_sleep:
            fake_sleep.side_effect = None

            with pytest.raises(HexitecFemError) as exc_info:
                self.test_fem.fem.calibrate_sensor()
            assert exc_info.type is HexitecFemError
            assert exc_info.value.args[0] == "Timed out polling register 0x89; PLL remains disabled"

        assert self.test_fem.fem.image_size_x == 160
        assert self.test_fem.fem.image_size_y == 160

    def test_acquire_data_2x2_system(self):
        """Test function handles normal configuration."""
        self.test_fem.fem.first_initialisation = True
        self.test_fem.fem.sensors_layout = HexitecFem.READOUTMODE[1]
        self.test_fem.fem.selected_sensor = HexitecFem.OPTIONS[2]
        self.test_fem.fem.debug = True

        empty_signals = 65535
        full_signals = 255
        transfer_ongoing = 0
        transfer_completed = 1
        number_frames = 2
        # Output from Sensor
        s_frame_last_length = 51200
        s_frame_max_length = 76960
        s_frame_min_length = 51200
        s_frame_number = 9
        s_frame_last_clock_cycles = 23015
        s_frame_max_clock_cycles = 4112394392
        s_frame_min_clock_cycles = 23015
        s_frame_data_total = 538080
        s_frame_data_total_clock_cycles = 1278212083
        s_frame_trigger_count = 0
        s_frame_in_progress_flag = 0
        # Output from frame Gate
        fg_frame_last_length = 51200
        fg_frame_max_length = 51200
        fg_frame_min_length = 51200
        fg_frame_number = 6
        fg_frame_last_clock_cycles = 23015
        fg_frame_max_clock_cycles = 4112417407
        fg_frame_min_clock_cycles = 23015
        fg_frame_data_total = 307200
        fg_frame_data_total_clock_cycles = 1278186053
        fg_frame_trigger_count = 0
        fg_frame_in_progress_flag = 0
        # Input to XAUI
        xaui_frame_last_length = 51200
        xaui_frame_max_length = 51200
        xaui_frame_min_length = 51200
        xaui_frame_number = 6
        xaui_frame_last_clock_cycles = 23015
        xaui_frame_max_clock_cycles = 4112417407
        xaui_frame_min_clock_cycles = 23015
        xaui_frame_data_total = 307200
        xaui_frame_data_total_clock_cycles = 1278186053
        xaui_frame_trigger_count = 0
        xaui_frame_in_progress_flag = 0

        side = [empty_signals, full_signals, empty_signals, full_signals, transfer_ongoing,
                transfer_completed,
                empty_signals, full_signals, number_frames, s_frame_last_length, s_frame_max_length,
                s_frame_min_length, s_frame_number, s_frame_last_clock_cycles,
                s_frame_max_clock_cycles, s_frame_min_clock_cycles, s_frame_data_total,
                s_frame_data_total_clock_cycles, s_frame_trigger_count, s_frame_in_progress_flag,
                # Frame Gate:
                fg_frame_last_length, fg_frame_max_length, fg_frame_min_length, fg_frame_number,
                fg_frame_last_clock_cycles, fg_frame_max_clock_cycles, fg_frame_min_clock_cycles,
                fg_frame_data_total, fg_frame_data_total_clock_cycles, fg_frame_trigger_count,
                fg_frame_in_progress_flag,
                # Input to XAUI
                xaui_frame_last_length, xaui_frame_max_length, xaui_frame_min_length,
                xaui_frame_number, xaui_frame_last_clock_cycles, xaui_frame_max_clock_cycles,
                xaui_frame_min_clock_cycles, xaui_frame_data_total,
                xaui_frame_data_total_clock_cycles, xaui_frame_trigger_count,
                xaui_frame_in_progress_flag]

        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effect = side
        self.test_fem.fem.acquire_data()

        self.test_fem.fem.x10g_rdma.read.assert_has_calls([
            call(0x60000011, ANY),
            call(0x60000012, ANY),
            call(0x60000011, ANY),
            call(0x60000012, ANY)
        ])

    def test_check_acquire_finished_handles_cancel(self):
        """Test check_acquire_finished calls acquire_data_completed if acquire cancelled."""
        with patch("hexitec.HexitecFem.IOLoop"):
            self.test_fem.fem.stop_acquisition = True
            self.test_fem.fem.x10g_rdma.write = Mock()
            self.test_fem.fem.acquire_data_completed = Mock()
            rc_value = self.test_fem.fem.check_acquire_finished()
            assert rc_value is None

    def test_check_acquire_finished_handles_all_data_sent(self):
        """Test check_acquire_finished calls acquire_data_completed if all data transferred."""
        with patch("hexitec.HexitecFem.IOLoop"):
            self.test_fem.fem.stop_acquisition = False
            self.test_fem.fem.x10g_rdma.read = Mock()
            self.test_fem.fem.x10g_rdma.read.side_effect = [1]  # >0 Signals all data sent
            self.test_fem.fem.x10g_rdma.write = Mock()
            self.test_fem.fem.acquire_data_completed = Mock()
            rc_value = self.test_fem.fem.check_acquire_finished()
            assert rc_value is None

    def test_check_acquire_finished_handles_data_being_transmitted(self):
        """Test check_acquire_finished handles normal data transmission."""
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.stop_acquisition = False
            self.test_fem.fem.x10g_rdma.read = Mock()
            self.test_fem.fem.x10g_rdma.read.side_effect = [0]  # >0 Signals all data sent
            self.test_fem.fem.duration_enabled = True
            self.test_fem.fem.duration = 2.0
            self.test_fem.fem.check_acquire_finished()
            mock_loop.instance().call_later.assert_called_with(0.1, self.test_fem.fem.check_acquire_finished)
            assert self.test_fem.fem.waited == 0.1
            assert self.test_fem.fem.duration_remaining == 1.9

    def test_check_acquire_finished_handles_negative_duration_remaining(self):
        """Test check_acquire_finished handles data sent, edge case of 'negative' duration."""
        # Because polling at 1Hz, will reached -0.1s once all data sent, which is 'rounded' to 0.0
        with patch("hexitec.HexitecFem.IOLoop") as mock_loop:
            self.test_fem.fem.stop_acquisition = False
            self.test_fem.fem.x10g_rdma.read = Mock()
            self.test_fem.fem.x10g_rdma.read.side_effect = [0]  # >0 Signals all data sent
            self.test_fem.fem.duration_enabled = True
            self.test_fem.fem.duration = 0.0
            self.test_fem.fem.check_acquire_finished()
            mock_loop.instance().call_later.assert_called_with(0.1, self.test_fem.fem.check_acquire_finished)
            assert self.test_fem.fem.waited == 0.1
            assert self.test_fem.fem.duration_remaining == 0.0

    def test_check_acquire_finished_handles_HexitecFemError(self):
        """Test check_choir_finished handles HexitecFemError exception."""
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
        """Test check_choir_finished handles bog standard exception."""
        self.test_fem.fem.stop_acquisition = True
        self.test_fem.fem.acquisition_completed = False
        self.test_fem.fem.acquire_data_completed = Mock()
        e_msg = "Badder Error"
        self.test_fem.fem.acquire_data_completed.side_effect = Exception(e_msg)

        self.test_fem.fem.check_acquire_finished()
        error = "Uncaught Exception; Data collection failed: {}".format(e_msg)
        assert self.test_fem.fem._get_status_error() == error
        assert self.test_fem.fem.acquisition_completed is True

    def test_acquire_data_single_sensor(self):
        """Test function handles single sensor selected."""
        self.test_fem.fem.first_initialisation = True
        self.test_fem.fem.sensors_layout = HexitecFem.READOUTMODE[0]
        self.test_fem.fem.selected_sensor = HexitecFem.OPTIONS[0]
        self.test_fem.fem.debug = True

        empty_signals = 65535
        full_signals = 255
        transfer_completed = 1
        number_frames = 2
        # Output from Sensor
        s_frame_last_length = 51200
        s_frame_max_length = 76960
        s_frame_min_length = 51200
        s_frame_number = 9
        s_frame_last_clock_cycles = 23015
        s_frame_max_clock_cycles = 4112394392
        s_frame_min_clock_cycles = 23015
        s_frame_data_total = 538080
        s_frame_data_total_clock_cycles = 1278212083
        s_frame_trigger_count = 0
        s_frame_in_progress_flag = 0
        # Output from frame Gate
        fg_frame_last_length = 51200
        fg_frame_max_length = 51200
        fg_frame_min_length = 51200
        fg_frame_number = 6
        fg_frame_last_clock_cycles = 23015
        fg_frame_max_clock_cycles = 4112417407
        fg_frame_min_clock_cycles = 23015
        fg_frame_data_total = 307200
        fg_frame_data_total_clock_cycles = 1278186053
        fg_frame_trigger_count = 0
        fg_frame_in_progress_flag = 0
        # Input to XAUI
        xaui_frame_last_length = 51200
        xaui_frame_max_length = 51200
        xaui_frame_min_length = 51200
        xaui_frame_number = 6
        xaui_frame_last_clock_cycles = 23015
        xaui_frame_max_clock_cycles = 4112417407
        xaui_frame_min_clock_cycles = 23015
        xaui_frame_data_total = 307200
        xaui_frame_data_total_clock_cycles = 1278186053
        xaui_frame_trigger_count = 0
        xaui_frame_in_progress_flag = 0

        side = [empty_signals, full_signals, empty_signals, full_signals, transfer_completed,
                empty_signals, full_signals, number_frames, s_frame_last_length, s_frame_max_length,
                s_frame_min_length, s_frame_number, s_frame_last_clock_cycles, s_frame_max_clock_cycles,
                s_frame_min_clock_cycles, s_frame_data_total, s_frame_data_total_clock_cycles,
                s_frame_trigger_count, s_frame_in_progress_flag,
                # Frame Gate:
                fg_frame_last_length, fg_frame_max_length, fg_frame_min_length, fg_frame_number,
                fg_frame_last_clock_cycles, fg_frame_max_clock_cycles, fg_frame_min_clock_cycles,
                fg_frame_data_total, fg_frame_data_total_clock_cycles, fg_frame_trigger_count,
                fg_frame_in_progress_flag,
                # Input to XAUI
                xaui_frame_last_length, xaui_frame_max_length, xaui_frame_min_length, xaui_frame_number,
                xaui_frame_last_clock_cycles, xaui_frame_max_clock_cycles, xaui_frame_min_clock_cycles,
                xaui_frame_data_total, xaui_frame_data_total_clock_cycles, xaui_frame_trigger_count,
                xaui_frame_in_progress_flag]

        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effect = side
        self.test_fem.fem.acquire_data()
        # Calls to self.test_fem.fem.x10g_rdma.read() already covered in previous unit test

    def test_acquire_data_completed_handles_manual_stop(self):
        """Test function handles user stopping acquisition."""
        self.test_fem.fem.sensors_layout = HexitecFem.READOUTMODE[0]
        self.test_fem.fem.selected_sensor = HexitecFem.OPTIONS[0]

        self.test_fem.fem.stop_acquisition = True
        self.test_fem.fem.read_response = Mock(return_value="0")
        self.test_fem.fem.send_cmd = Mock()

        empty_signals = 65535
        full_signals = 255
        transfer_ongoing = 0

        side = [empty_signals, full_signals, empty_signals, full_signals, transfer_ongoing]

        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effect = side

        self.test_fem.fem.acquire_data_completed()

        assert self.test_fem.fem.hardware_busy is False
        assert self.test_fem.fem.acquisition_completed is True
        assert self.test_fem.fem.first_initialisation is False

    def test_acquire_data_completed_vsr2_works(self):
        """Test function handles normal end of acquisition, targeting VSR2."""
        from datetime import datetime
        DATE_FORMAT = self.test_fem.fem.DATE_FORMAT
        self.test_fem.fem.acquire_start_time = '%s' % (datetime.now().strftime(DATE_FORMAT))
        self.test_fem.fem.first_initialisation = True
        self.test_fem.fem.sensors_layout = HexitecFem.READOUTMODE[1]
        self.test_fem.fem.selected_sensor = HexitecFem.OPTIONS[2]
        self.test_fem.fem.debug = True

        empty_signals = 65535
        full_signals = 255
        number_frames = 2
        # Output from Sensor
        s_frame_last_length = 51200
        s_frame_max_length = 76960
        s_frame_min_length = 51200
        s_frame_number = 9
        s_frame_last_clock_cycles = 23015
        s_frame_max_clock_cycles = 4112394392
        s_frame_min_clock_cycles = 23015
        s_frame_data_total = 538080
        s_frame_data_total_clock_cycles = 1278212083
        s_frame_trigger_count = 0
        s_frame_in_progress_flag = 0
        # Output from frame Gate
        fg_frame_last_length = 51200
        fg_frame_max_length = 51200
        fg_frame_min_length = 51200
        fg_frame_number = 6
        fg_frame_last_clock_cycles = 23015
        fg_frame_max_clock_cycles = 4112417407
        fg_frame_min_clock_cycles = 23015
        fg_frame_data_total = 307200
        fg_frame_data_total_clock_cycles = 1278186053
        fg_frame_trigger_count = 0
        fg_frame_in_progress_flag = 0
        # Input to XAUI
        xaui_frame_last_length = 51200
        xaui_frame_max_length = 51200
        xaui_frame_min_length = 51200
        xaui_frame_number = 6
        xaui_frame_last_clock_cycles = 23015
        xaui_frame_max_clock_cycles = 4112417407
        xaui_frame_min_clock_cycles = 23015
        xaui_frame_data_total = 307200
        xaui_frame_data_total_clock_cycles = 1278186053
        xaui_frame_trigger_count = 0
        xaui_frame_in_progress_flag = 0

        side = [empty_signals, full_signals, number_frames, s_frame_last_length, s_frame_max_length,
                s_frame_min_length, s_frame_number, s_frame_last_clock_cycles,
                s_frame_max_clock_cycles, s_frame_min_clock_cycles, s_frame_data_total,
                s_frame_data_total_clock_cycles, s_frame_trigger_count, s_frame_in_progress_flag,
                # Frame Gate:
                fg_frame_last_length, fg_frame_max_length, fg_frame_min_length, fg_frame_number,
                fg_frame_last_clock_cycles, fg_frame_max_clock_cycles, fg_frame_min_clock_cycles,
                fg_frame_data_total, fg_frame_data_total_clock_cycles, fg_frame_trigger_count,
                fg_frame_in_progress_flag,
                # Input to XAUI
                xaui_frame_last_length, xaui_frame_max_length, xaui_frame_min_length,
                xaui_frame_number, xaui_frame_last_clock_cycles, xaui_frame_max_clock_cycles,
                xaui_frame_min_clock_cycles, xaui_frame_data_total,
                xaui_frame_data_total_clock_cycles, xaui_frame_trigger_count,
                xaui_frame_in_progress_flag
                ]

        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effect = side
        self.test_fem.fem.acquire_data_completed()

        self.test_fem.fem.x10g_rdma.read.assert_has_calls([
            call(0x60000011, ANY),
            call(0x60000012, ANY),
            call(0xD0000001, ANY),
            # Output from Sensor
            call(0x70000010, ANY),
            call(0x70000011, ANY),
            call(0x70000012, ANY),
            call(0x70000013, ANY),
            call(0x70000014, ANY),
            call(0x70000015, ANY),
            call(0x70000016, ANY),
            call(0x70000017, ANY),
            call(0x70000018, ANY),
            call(0x70000019, ANY),
            call(0x7000001A, ANY),
            # Output from Frame Gate
            call(0x80000010, 'frame last length'),
            call(0x80000011, 'frame max length'),
            call(0x80000012, 'frame min length'),
            call(0x80000013, 'frame number'),
            call(0x80000014, 'frame last clock cycles'),
            call(0x80000015, 'frame max clock cycles'),
            call(0x80000016, 'frame min clock cycles'),
            call(0x80000017, 'frame data total'),
            call(0x80000018, 'frame data total clock cycles'),
            call(0x80000019, 'frame trigger count'),
            call(0x8000001A, 'frame in progress flag'),
            # Input to XAUI
            call(0x90000010, 'frame last length'),
            call(0x90000011, 'frame max length'),
            call(0x90000012, 'frame min length'),
            call(0x90000013, 'frame number'),
            call(0x90000014, 'frame last clock cycles'),
            call(0x90000015, 'frame max clock cycles'),
            call(0x90000016, 'frame min clock cycles'),
            call(0x90000017, 'frame data total'),
            call(0x90000018, 'frame data total clock cycles'),
            call(0x90000019, 'frame trigger count'),
            call(0x9000001A, 'frame in progress flag'),
        ])

    def test_acquire_data_completed_vsr1_works(self):
        """Test function handles normal end of acquisition, targeting VSR1."""
        from datetime import datetime
        DATE_FORMAT = self.test_fem.fem.DATE_FORMAT
        self.test_fem.fem.acquire_start_time = '%s' % (datetime.now().strftime(DATE_FORMAT))
        self.test_fem.fem.first_initialisation = True
        self.test_fem.fem.sensors_layout = HexitecFem.READOUTMODE[1]
        self.test_fem.fem.selected_sensor = HexitecFem.OPTIONS[0]
        self.test_fem.fem.debug = True

        empty_signals = 65535
        full_signals = 255
        number_frames = 2
        # Output from Sensor
        s_frame_last_length = 51200
        s_frame_max_length = 76960
        s_frame_min_length = 51200
        s_frame_number = 9
        s_frame_last_clock_cycles = 23015
        s_frame_max_clock_cycles = 4112394392
        s_frame_min_clock_cycles = 23015
        s_frame_data_total = 538080
        s_frame_data_total_clock_cycles = 1278212083
        s_frame_trigger_count = 0
        s_frame_in_progress_flag = 0
        # Output from frame Gate
        fg_frame_last_length = 51200
        fg_frame_max_length = 51200
        fg_frame_min_length = 51200
        fg_frame_number = 6
        fg_frame_last_clock_cycles = 23015
        fg_frame_max_clock_cycles = 4112417407
        fg_frame_min_clock_cycles = 23015
        fg_frame_data_total = 307200
        fg_frame_data_total_clock_cycles = 1278186053
        fg_frame_trigger_count = 0
        fg_frame_in_progress_flag = 0
        # Input to XAUI
        xaui_frame_last_length = 51200
        xaui_frame_max_length = 51200
        xaui_frame_min_length = 51200
        xaui_frame_number = 6
        xaui_frame_last_clock_cycles = 23015
        xaui_frame_max_clock_cycles = 4112417407
        xaui_frame_min_clock_cycles = 23015
        xaui_frame_data_total = 307200
        xaui_frame_data_total_clock_cycles = 1278186053
        xaui_frame_trigger_count = 0
        xaui_frame_in_progress_flag = 0

        side = [empty_signals, full_signals, number_frames, s_frame_last_length, s_frame_max_length,
                s_frame_min_length, s_frame_number, s_frame_last_clock_cycles,
                s_frame_max_clock_cycles, s_frame_min_clock_cycles, s_frame_data_total,
                s_frame_data_total_clock_cycles, s_frame_trigger_count, s_frame_in_progress_flag,
                # Frame Gate:
                fg_frame_last_length, fg_frame_max_length, fg_frame_min_length, fg_frame_number,
                fg_frame_last_clock_cycles, fg_frame_max_clock_cycles, fg_frame_min_clock_cycles,
                fg_frame_data_total, fg_frame_data_total_clock_cycles, fg_frame_trigger_count,
                fg_frame_in_progress_flag,
                # Input to XAUI
                xaui_frame_last_length, xaui_frame_max_length, xaui_frame_min_length,
                xaui_frame_number, xaui_frame_last_clock_cycles, xaui_frame_max_clock_cycles,
                xaui_frame_min_clock_cycles, xaui_frame_data_total,
                xaui_frame_data_total_clock_cycles, xaui_frame_trigger_count,
                xaui_frame_in_progress_flag
                ]

        self.test_fem.fem.x10g_rdma.read = Mock()
        self.test_fem.fem.x10g_rdma.read.side_effect = side
        self.test_fem.fem.acquire_data_completed()

        self.test_fem.fem.x10g_rdma.read.assert_has_calls([
            call(0x60000011, ANY),
            call(0x60000012, ANY),
            call(0xD0000001, ANY),
            # Output from Sensor
            call(0x70000010, ANY),
            call(0x70000011, ANY),
            call(0x70000012, ANY),
            call(0x70000013, ANY),
            call(0x70000014, ANY),
            call(0x70000015, ANY),
            call(0x70000016, ANY),
            call(0x70000017, ANY),
            call(0x70000018, ANY),
            call(0x70000019, ANY),
            call(0x7000001A, ANY),
            # Output from Frame Gate
            call(0x80000010, 'frame last length'),
            call(0x80000011, 'frame max length'),
            call(0x80000012, 'frame min length'),
            call(0x80000013, 'frame number'),
            call(0x80000014, 'frame last clock cycles'),
            call(0x80000015, 'frame max clock cycles'),
            call(0x80000016, 'frame min clock cycles'),
            call(0x80000017, 'frame data total'),
            call(0x80000018, 'frame data total clock cycles'),
            call(0x80000019, 'frame trigger count'),
            call(0x8000001A, 'frame in progress flag'),
            # Input to XAUI
            call(0x90000010, 'frame last length'),
            call(0x90000011, 'frame max length'),
            call(0x90000012, 'frame min length'),
            call(0x90000013, 'frame number'),
            call(0x90000014, 'frame last clock cycles'),
            call(0x90000015, 'frame max clock cycles'),
            call(0x90000016, 'frame min clock cycles'),
            call(0x90000017, 'frame data total'),
            call(0x90000018, 'frame data total clock cycles'),
            call(0x90000019, 'frame trigger count'),
            call(0x9000001A, 'frame in progress flag'),
        ])

    def test_set_up_state_machine(self):
        """Test function works ok."""
        self.test_fem.fem.read_response = Mock(return_value="0")

        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.calculate_frame_rate = Mock()

        self.test_fem.fem.hexitec_parameters = {'Control-Settings/Gain': '0',
                                                'Control-Settings/ADC1 Delay': '2',
                                                'Control-Settings/delay sync signals': '10',
                                                'Control-Settings/Row -> S1': '5',
                                                'Control-Settings/S1 -> Sph': '1',
                                                'Control-Settings/Sph -> S2': '5',
                                                'Control-Settings/VCAL2 -> VCAL1': '1'}

        self.test_fem.fem.set_up_state_machine()

        vsr = self.test_fem.fem.vsr_addr

        # Establish register values (r0XX), default values (v0XX)
        r002 = 0x30, 0x32
        r003 = 0x30, 0x33
        r004 = 0x30, 0x34
        r005 = 0x30, 0x35
        r006 = 0x30, 0x36
        r007 = 0x30, 0x37
        r009 = 0x30, 0x39
        r00E = 0x30, 0x45
        r018 = 0x31, 0x38
        r019 = 0x31, 0x39
        r01B = 0x31, 0x42
        r014 = 0x31, 0x34
        v002 = 0x30, 0x31
        v003 = 0x30, 0x30
        v004 = 0x30, 0x31
        v005 = 0x30, 0x36
        v006 = 0x30, 0x31
        v007 = 0x30, 0x33
        v009 = 0x30, 0x32
        v00E = 0x30, 0x41
        v018 = 0x30, 0x31
        v019 = 0x30, 0x30
        v01B = 0x30, 0x38
        v014 = 0x30, 0x31

        # Default clock settings in HexitecFem determined default values for
        # Registers 002 - 005. Update defaults accordingly:
        row_s1 = self.test_fem.fem.row_s1
        if row_s1 > -1:
            row_s1_low = row_s1 & 0xFF
            row_s1_high = row_s1 >> 8
            v002 = self.test_fem.fem.convert_to_aspect_format(row_s1_low)
            v003 = self.test_fem.fem.convert_to_aspect_format(row_s1_high)

        s1_sph = self.test_fem.fem.s1_sph
        if s1_sph > -1:
            v004 = self.test_fem.fem.convert_to_aspect_format(s1_sph)

        sph_s2 = self.test_fem.fem.sph_s2
        if sph_s2 > -1:
            v005 = self.test_fem.fem.convert_to_aspect_format(sph_s2)

        gain = self.test_fem.fem._extract_integer(self.test_fem.fem.hexitec_parameters, 'Control-Settings/Gain', bit_range=1)
        if gain > -1:
            v006 = self.test_fem.fem.convert_to_aspect_format(gain)

        self.test_fem.fem.send_cmd.assert_has_calls([
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r007[0], r007[1], v007[0], v007[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r002[0], r002[1], v002[0], v002[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r003[0], r003[1], v003[0], v003[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r004[0], r004[1], v004[0], v004[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r005[0], r005[1], v005[0], v005[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r006[0], r006[1], v006[0], v006[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r009[0], r009[1], v009[0], v009[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r00E[0], r00E[1], v00E[0], v00E[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r01B[0], r01B[1], v01B[0], v01B[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r014[0], r014[1], v014[0], v014[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r018[0], r018[1], v018[0], v018[1], 0x0D]),
            call([0x23, vsr, HexitecFem.SET_REG_BIT, r019[0], r019[1], v019[0], v019[1], 0x0D]),
        ])

    def calculate_register_values(self, cmd):
        """Calculate registry value like HexitecFem.send_cmd()."""
        while len(cmd) % 4 != 0:
            cmd.append(13)

        register_values = []
        for i in range(0, len(cmd) // 4):
            reg_value = 256 * 256 * 256 * cmd[(i * 4)] + 256 * 256 * cmd[(i * 4) + 1] \
                + 256 * cmd[(i * 4) + 2] + cmd[(i * 4) + 3]
            register_values.append(reg_value)
        return register_values

    def test_collect_offsets(self):
        """Test function handles ok."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False

        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.read_response = Mock(return_value='1A')

        with patch('time.sleep') as fake_sleep:
            fake_sleep.side_effect = None
            self.test_fem.fem.collect_offsets()

        vsr1 = HexitecFem.VSR_ADDRESS[0]
        vsr2 = HexitecFem.VSR_ADDRESS[1]
        self.test_fem.fem.send_cmd.assert_has_calls([
            call([0x23, vsr1, HexitecFem.READ_REG_VALUE, 0x32, 0x34, 0x0D]),
            call([0x23, vsr2, HexitecFem.READ_REG_VALUE, 0x32, 0x34, 0x0D]),
            # 2. Stop the state machine
            call([0x23, vsr1, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]),
            call([0x23, vsr2, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]),
            # 3. Set register 0x24 to 0x22
            call([0x23, vsr1, HexitecFem.SEND_REG_VALUE, 0x32, 0x34, 0x32, 0x32, 0x0D]),
            call([0x23, vsr2, HexitecFem.SEND_REG_VALUE, 0x32, 0x34, 0x32, 0x32, 0x0D]),
            # 4. Start the state machine
            call([0x23, vsr1, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]),
            call([0x23, vsr2, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]),
            # 5 (wait 1 second), 6. Stop the state machine
            call([0x23, vsr1, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]),
            call([0x23, vsr2, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]),
            # 7. Set register 0x24 to 0x28
            call([0x23, vsr1, HexitecFem.SEND_REG_VALUE, 0x32, 0x34, 0x32, 0x38, 0x0D]),
            call([0x23, vsr2, HexitecFem.SEND_REG_VALUE, 0x32, 0x34, 0x32, 0x38, 0x0D]),
            # 8. Start state machine (same as 4)
            call([0x23, vsr1, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]),
            call([0x23, vsr2, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]),
            # Ensure VCAL remains on
            call([0x23, vsr1, HexitecFem.CLR_REG_BIT, 0x32, 0x34, 0x32, 0x30, 0x0D]),
            call([0x23, vsr2, HexitecFem.CLR_REG_BIT, 0x32, 0x34, 0x32, 0x30, 0x0D]),
        ])

    def test_collect_offsets_handles_hardware_disconnected(self):
        """Test function handles hardware disconnected."""
        self.test_fem.fem.hardware_connected = False
        self.test_fem.fem.collect_offsets()
        error = "Can't collect offsets while disconnected: Can't collect offsets while disconnected"
        assert self.test_fem.fem._get_status_error() == error

    def test_collect_offsets_handles_hardware_busy(self):
        """Test function handles hardware busy."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = True
        self.test_fem.fem.collect_offsets()
        error = "Can't collect offsets while disconnected: Hardware sensors busy initialising"
        assert self.test_fem.fem._get_status_error() == error

    def test_collect_offsets_fails_unknown_exception(self):
        """Test function fails unexpected exception."""
        self.test_fem.fem.hardware_connected = True
        self.test_fem.fem.hardware_busy = False
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.send_cmd.side_effect = AttributeError()
        self.test_fem.fem.collect_offsets()
        error = "Uncaught Exception; Failed to collect offsets: "
        assert self.test_fem.fem.status_error == error

    def test_load_pwr_cal_read_enables_handles_defaults(self):
        """Test function handles default values in the absence of ini config file."""
        vsr_addr = HexitecFem.VSR_ADDRESS[0]

        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.read_response = Mock()

        list_of_46s = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                       0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        list_of_30s = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                       0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]

        register_061 = [0x36, 0x31]   # Column Read Enable ASIC1
        register_0C2 = [0x43, 0x32]   # Column Read Enable ASIC2
        value_061 = list_of_46s
        value_0C2 = list_of_46s

        enable_sm = [0x23, vsr_addr, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]
        disable_sm = [0x23, vsr_addr, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]

        # Column Power Enable

        register_04D = [0x34, 0x44]   # Column Power Enable ASIC1 (Reg 0x4D)
        register_0AE = [0x41, 0x45]   # Column Power Enable ASIC2 (Reg 0xAE)
        value_04D = list_of_46s
        value_0AE = list_of_46s

        # Column Power Enable, for ASIC1 (Reg 0x4D)
        col_power_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_04D[0], register_04D[1], value_04D[0], value_04D[1],
                             value_04D[2], value_04D[3], value_04D[4], value_04D[5],
                             value_04D[6], value_04D[7], value_04D[8], value_04D[9],
                             value_04D[10], value_04D[11], value_04D[12], value_04D[13],
                             value_04D[14], value_04D[15], value_04D[16], value_04D[17],
                             value_04D[18], value_04D[19], 0x0D]

        # Column Power Enable, for ASIC2 (Reg 0xAE)
        col_power_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_0AE[0], register_0AE[1], value_0AE[0], value_0AE[1],
                             value_0AE[2], value_0AE[3], value_0AE[4], value_0AE[5],
                             value_0AE[6], value_0AE[7], value_0AE[8], value_0AE[9],
                             value_0AE[10], value_0AE[11], value_0AE[12], value_0AE[13],
                             value_0AE[14], value_0AE[15], value_0AE[16], value_0AE[17],
                             value_0AE[18], value_0AE[19], 0x0D]

        # Row Power Enable

        register_02F = [0x32, 0x46]   # Row Power Enable ASIC1 (Reg 0x2F)
        register_090 = [0x39, 0x30]   # Row Power Enable ASIC2 (Reg 0x90)
        value_02F = list_of_46s
        value_090 = list_of_46s

        # Row Power Enable, for ASIC1 (Reg 0x2F)
        row_power_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_02F[0], register_02F[1], value_02F[0], value_02F[1],
                             value_02F[2], value_02F[3], value_02F[4], value_02F[5],
                             value_02F[6], value_02F[7], value_02F[8], value_02F[9],
                             value_02F[10], value_02F[1], value_02F[2], value_02F[3],
                             value_02F[14], value_02F[15], value_02F[16], value_02F[17],
                             value_02F[18], value_02F[19], 0x0D]

        # Row Power Enable, for ASIC2 (Reg 0x90)
        row_power_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_090[0], register_090[1], value_090[0], value_090[1],
                             value_090[2], value_090[3], value_090[4], value_090[5],
                             value_090[6], value_090[7], value_090[8], value_090[9],
                             value_090[10], value_090[11], value_090[12], value_090[13],
                             value_090[14], value_090[15], value_090[16], value_090[17],
                             value_090[18], value_090[19], 0x0D]

        # Column Calibration Enable

        register_057 = [0x35, 0x37]   # Column Calibrate Enable ASIC1 (Reg 0x57)
        register_0B8 = [0x42, 0x38]   # Column Calibrate Enable ASIC2 (Reg 0xB8)
        value_057 = list_of_30s
        value_0B8 = list_of_30s

        # Column Calibrate Enable, for ASIC1 (Reg 0x57)
        col_cal_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                           register_057[0], register_057[1], value_057[0], value_057[1],
                           value_057[2], value_057[3], value_057[4], value_057[5],
                           value_057[6], value_057[7], value_057[8], value_057[9],
                           value_057[10], value_057[11], value_057[12], value_057[13],
                           value_057[14], value_057[15], value_057[16], value_057[17],
                           value_057[18], value_057[19], 0x0D]

        # Column Calibrate Enable, for ASIC2 (Reg 0xB8)
        col_cal_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                           register_0B8[0], register_0B8[1], value_0B8[0], value_0B8[1],
                           value_0B8[2], value_0B8[3], value_0B8[4], value_0B8[5],
                           value_0B8[6], value_0B8[7], value_0B8[8], value_0B8[9],
                           value_0B8[10], value_0B8[11], value_0B8[12], value_0B8[13],
                           value_0B8[14], value_0B8[15], value_0B8[16], value_0B8[17],
                           value_0B8[18], value_0B8[19], 0x0D]

        # Row Calibration Enable

        register_039 = [0x33, 0x39]   # Row Calibrate Enable ASIC1 (Reg 0x39)
        register_09A = [0x39, 0x41]   # Row Calibrate Enable ASIC2 (Reg 0x9A)
        value_039 = list_of_30s
        value_09A = list_of_30s

        # Row Calibrate Enable, for ASIC1 (Reg 0x39)
        row_cal_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                           register_039[0], register_039[1], value_039[0], value_039[1],
                           value_039[2], value_039[3], value_039[4], value_039[5],
                           value_039[6], value_039[7], value_039[8], value_039[9],
                           value_039[10], value_039[11], value_039[12], value_039[13],
                           value_039[14], value_039[15], value_039[16], value_039[17],
                           value_039[18], value_039[19], 0x0D]

        # Row Calibrate Enable, for ASIC2 (Reg 0x9A)
        row_cal_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                           register_09A[0], register_09A[1], value_09A[0], value_09A[1],
                           value_09A[2], value_09A[3], value_09A[4], value_09A[5],
                           value_09A[6], value_09A[7], value_09A[8], value_09A[9],
                           value_09A[10], value_09A[11], value_09A[12], value_09A[13],
                           value_09A[14], value_09A[15], value_09A[16], value_09A[17],
                           value_09A[18], value_09A[19], 0x0D]

        register_061 = [0x36, 0x31]   # Column Read Enable ASIC1
        register_0C2 = [0x43, 0x32]   # Column Read Enable ASIC2
        value_061 = list_of_46s
        value_0C2 = list_of_46s

        # No ini file loaded, use default values
        col_read_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST, register_061[0],
                            register_061[1], value_061[0], value_061[1], value_061[2],
                            value_061[3], value_061[4], value_061[5], value_061[6],
                            value_061[7], value_061[8], value_061[9], value_061[10],
                            value_061[11], value_061[12], value_061[13], value_061[14],
                            value_061[15], value_061[16], value_061[17], value_061[18],
                            value_061[19], 0x0D]

        # Column Read Enable, for ASIC2 (Reg 0xC2)
        col_read_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                            register_0C2[0], register_0C2[1], value_0C2[0], value_0C2[1],
                            value_0C2[2], value_0C2[3], value_0C2[4], value_0C2[5],
                            value_0C2[6], value_0C2[7], value_0C2[8], value_0C2[9],
                            value_0C2[10], value_0C2[11], value_0C2[12], value_0C2[13],
                            value_0C2[14], value_0C2[15], value_0C2[16], value_0C2[17],
                            value_0C2[18], value_0C2[19], 0x0D]

        # No ini file loaded, use default values
        col_read_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST, register_061[0],
                            register_061[1], value_061[0], value_061[1], value_061[2],
                            value_061[3], value_061[4], value_061[5], value_061[6],
                            value_061[7], value_061[8], value_061[9], value_061[10],
                            value_061[11], value_061[12], value_061[13], value_061[14],
                            value_061[15], value_061[16], value_061[17], value_061[18],
                            value_061[19], 0x0D]
        # Column Read Enable, for ASIC2 (Reg 0xC2)
        col_read_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                            register_0C2[0], register_0C2[1], value_0C2[0], value_0C2[1],
                            value_0C2[2], value_0C2[3], value_0C2[4], value_0C2[5],
                            value_0C2[6], value_0C2[7], value_0C2[8], value_0C2[9],
                            value_0C2[10], value_0C2[11], value_0C2[12], value_0C2[13],
                            value_0C2[14], value_0C2[15], value_0C2[16], value_0C2[17],
                            value_0C2[18], value_0C2[19], 0x0D]

        # Row Read Enable

        register_043 = [0x34, 0x33]   # Row Read Enable ASIC1
        register_0A4 = [0x41, 0x34]   # Row Read Enable ASIC2
        value_043 = list_of_46s
        value_0A4 = list_of_46s

        # Row Read Enable, for ASIC1 (Reg 0x43)
        row_read_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                            register_043[0], register_043[1], value_043[0], value_043[1],
                            value_043[2], value_043[3], value_043[4], value_043[5],
                            value_043[6], value_043[7], value_043[8], value_043[9],
                            value_043[10], value_043[11], value_043[12], value_043[13],
                            value_043[14], value_043[15], value_043[16], value_043[17],
                            value_043[18], value_043[19], 0x0D]

        # Row Read Enable, for ASIC2 (Reg 0xA4)
        row_read_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                            register_0A4[0], register_0A4[1], value_0A4[0], value_0A4[1],
                            value_0A4[2], value_0A4[3], value_0A4[4], value_0A4[5],
                            value_0A4[6], value_0A4[7], value_0A4[8], value_0A4[9],
                            value_0A4[10], value_0A4[11], value_0A4[12], value_0A4[13],
                            value_0A4[14], value_0A4[15], value_0A4[16], value_0A4[17],
                            value_0A4[18], value_0A4[19], 0x0D]

        self.test_fem.fem.load_pwr_cal_read_enables()

        self.test_fem.fem.send_cmd.assert_has_calls([
            call(disable_sm),
            call(col_power_enable1),
            call(col_power_enable2),
            call(row_power_enable1),
            call(row_power_enable2),
            call(col_cal_enable1),
            call(col_cal_enable2),
            call(row_cal_enable1),
            call(row_cal_enable2),
            call(col_read_enable1),
            call(col_read_enable2),
            call(row_read_enable1),
            call(row_read_enable2),
            call(enable_sm),
        ])

    def test_load_pwr_cal_read_enables_handles_configured_values(self):
        """Test function handles values provided by an (simulated) ini config file."""
        vsr_addr = HexitecFem.VSR_ADDRESS[1]
        self.test_fem.fem.vsr_addr = vsr_addr

        params = \
            {'Bias_Voltage/Bias_Voltage_Refresh': 'False',
             'Bias_Voltage/Bias_Refresh_Interval': '18000',
             'Bias_Voltage/Time_Refresh_Voltage_Held': '3000',
             'Bias_Voltage/Bias_Voltage_Settle_Time': '2000',
             'Control-Settings/Gain': '0', 'Control-Settings/ADC1 Delay': '2',
             'Control-Settings/delay sync signals': '10', 'Control-Settings/Row -> S1': '5',
             'Control-Settings/S1 -> Sph': '1', 'Control-Settings/Sph -> S2': '5',
             'Control-Settings/VCAL2 -> VCAL1': '1', 'Control-Settings/VCAL': '0.4',
             'Control-Settings/Uref_mid': '1,000000E+3',
             'Sensor-Config_V1_S1/ColumnEn_1stChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnPwr1stChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnCal1stChannel': '00110011001100110011',
             'Sensor-Config_V1_S1/ColumnEn_2ndChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnPwr2ndChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnCal2ndChannel': '00110011001100110011',
             'Sensor-Config_V1_S1/ColumnEn_3rdChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnPwr3rdChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnCal3rdChannel': '00110011001100110011',
             'Sensor-Config_V1_S1/ColumnEn_4thChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnPwr4thChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnCal4thChannel': '00110011001100110011',
             'Sensor-Config_V1_S1/RowEn_1stBlock': '11111111111111111111',
             'Sensor-Config_V1_S1/RowPwr1stBlock': '11111111111111111111',
             'Sensor-Config_V1_S1/RowCal1stBlock': '00110011001100110011',
             'Sensor-Config_V1_S1/RowEn_2ndBlock': '11111111111111111111',
             'Sensor-Config_V1_S1/RowPwr2ndBlock': '11111111111111111111',
             'Sensor-Config_V1_S1/RowCal2ndBlock': '00110011001100110011',
             'Sensor-Config_V1_S1/RowEn_3rdBlock': '11111111111111111111',
             'Sensor-Config_V1_S1/RowPwr3rdBlock': '11111111111111111111',
             'Sensor-Config_V1_S1/RowCal3rdBlock': '00110011001100110011',
             'Sensor-Config_V1_S1/RowEn_4thBlock': '11111111111111111111',
             'Sensor-Config_V1_S1/RowPwr4thBlock': '11111111111111111111',
             'Sensor-Config_V1_S1/RowCal4thBlock': '00110011001100110011',
             'Sensor-Config_V1_S2/ColumnEn_1stChannel': '11111111111111111111',
             'Sensor-Config_V1_S2/ColumnPwr1stChannel': '11111111111111111111',
             'Sensor-Config_V1_S2/ColumnCal1stChannel': '10110101101011010110',
             'Sensor-Config_V1_S2/ColumnEn_2ndChannel': '11111111111111111111',
             'Sensor-Config_V1_S2/ColumnPwr2ndChannel': '11111111111111111111',
             'Sensor-Config_V1_S2/ColumnCal2ndChannel': '10110101101011010110',
             'Sensor-Config_V1_S2/ColumnEn_3rdChannel': '11111111111111111111',
             'Sensor-Config_V1_S2/ColumnPwr3rdChannel': '11111111111111111111',
             'Sensor-Config_V1_S2/ColumnCal3rdChannel': '10110101101011010110',
             'Sensor-Config_V1_S2/ColumnEn_4thChannel': '11111111111111111111',
             'Sensor-Config_V1_S2/ColumnPwr4thChannel': '11111111111111111111',
             'Sensor-Config_V1_S2/ColumnCal4thChannel': '10110101101011010110',
             'Sensor-Config_V1_S2/RowEn_1stBlock': '11111111111111111111',
             'Sensor-Config_V1_S2/RowPwr1stBlock': '11111111111111111111',
             'Sensor-Config_V1_S2/RowCal1stBlock': '10110101101011010110',
             'Sensor-Config_V1_S2/RowEn_2ndBlock': '11111111111111111111',
             'Sensor-Config_V1_S2/RowPwr2ndBlock': '11111111111111111111',
             'Sensor-Config_V1_S2/RowCal2ndBlock': '10110101101011010110',
             'Sensor-Config_V1_S2/RowEn_3rdBlock': '11111111111111111111',
             'Sensor-Config_V1_S2/RowPwr3rdBlock': '11111111111111111111',
             'Sensor-Config_V1_S2/RowCal3rdBlock': '10110101101011010110',
             'Sensor-Config_V1_S2/RowEn_4thBlock': '11111111111111111111',
             'Sensor-Config_V1_S2/RowPwr4thBlock': '11111111111111111111',
             'Sensor-Config_V1_S2/RowCal4thBlock': '10110101101011010110',
             'Sensor-Config_V2_S1/ColumnEn_1stChannel': '11111111111111111111',
             'Sensor-Config_V2_S1/ColumnPwr1stChannel': '11111111111111111111',
             'Sensor-Config_V2_S1/ColumnCal1stChannel': '10101010101010101010',
             'Sensor-Config_V2_S1/ColumnEn_2ndChannel': '11111111111111111111',
             'Sensor-Config_V2_S1/ColumnPwr2ndChannel': '11111111111111111111',
             'Sensor-Config_V2_S1/ColumnCal2ndChannel': '10101010101010101010',
             'Sensor-Config_V2_S1/ColumnEn_3rdChannel': '11111111111111111111',
             'Sensor-Config_V2_S1/ColumnPwr3rdChannel': '11111111111111111111',
             'Sensor-Config_V2_S1/ColumnCal3rdChannel': '10101010101010101010',
             'Sensor-Config_V2_S1/ColumnEn_4thChannel': '11111111111111111111',
             'Sensor-Config_V2_S1/ColumnPwr4thChannel': '11111111111111111111',
             'Sensor-Config_V2_S1/ColumnCal4thChannel': '10101010101010101010',
             'Sensor-Config_V2_S1/RowEn_1stBlock': '11111111111111111111',
             'Sensor-Config_V2_S1/RowPwr1stBlock': '11111111111111111111',
             'Sensor-Config_V2_S1/RowCal1stBlock': '10101010101010101010',
             'Sensor-Config_V2_S1/RowEn_2ndBlock': '11111111111111111111',
             'Sensor-Config_V2_S1/RowPwr2ndBlock': '11111111111111111111',
             'Sensor-Config_V2_S1/RowCal2ndBlock': '10101010101010101010',
             'Sensor-Config_V2_S1/RowEn_3rdBlock': '11111111111111111111',
             'Sensor-Config_V2_S1/RowPwr3rdBlock': '11111111111111111111',
             'Sensor-Config_V2_S1/RowCal3rdBlock': '10101010101010101010',
             'Sensor-Config_V2_S1/RowEn_4thBlock': '11111111111111111111',
             'Sensor-Config_V2_S1/RowPwr4thBlock': '11111111111111111111',
             'Sensor-Config_V2_S1/RowCal4thBlock': '10101010101010101010',
             'Sensor-Config_V2_S2/ColumnEn_1stChannel': '11111111111111111111',
             'Sensor-Config_V2_S2/ColumnPwr1stChannel': '11111111111111111111',
             'Sensor-Config_V2_S2/ColumnCal1stChannel': '00000000000000000000',
             'Sensor-Config_V2_S2/ColumnEn_2ndChannel': '11111111111111111111',
             'Sensor-Config_V2_S2/ColumnPwr2ndChannel': '11111111111111111111',
             'Sensor-Config_V2_S2/ColumnCal2ndChannel': '00000000000000000000',
             'Sensor-Config_V2_S2/ColumnEn_3rdChannel': '11111111111111111111',
             'Sensor-Config_V2_S2/ColumnPwr3rdChannel': '11111111111111111111',
             'Sensor-Config_V2_S2/ColumnCal3rdChannel': '00000000000000000000',
             'Sensor-Config_V2_S2/ColumnEn_4thChannel': '11111111111111111111',
             'Sensor-Config_V2_S2/ColumnPwr4thChannel': '11111111111111111111',
             'Sensor-Config_V2_S2/ColumnCal4thChannel': '00000000000000000000',
             'Sensor-Config_V2_S2/RowEn_1stBlock': '11111111111111111111',
             'Sensor-Config_V2_S2/RowPwr1stBlock': '11111111111111111111',
             'Sensor-Config_V2_S2/RowCal1stBlock': '00000000000000000000',
             'Sensor-Config_V2_S2/RowEn_2ndBlock': '11111111111111111111',
             'Sensor-Config_V2_S2/RowPwr2ndBlock': '11111111111111111111',
             'Sensor-Config_V2_S2/RowCal2ndBlock': '00000000000000000000',
             'Sensor-Config_V2_S2/RowEn_3rdBlock': '11111111111111111111',
             'Sensor-Config_V2_S2/RowPwr3rdBlock': '11111111111111111111',
             'Sensor-Config_V2_S2/RowCal3rdBlock': '00000000000000000000',
             'Sensor-Config_V2_S2/RowEn_4thBlock': '11111111111111111111',
             'Sensor-Config_V2_S2/RowPwr4thBlock': '11111111111111111111',
             'Sensor-Config_V2_S2/RowCal4thBlock': '00000000000000000000'}

        self.test_fem.fem.hexitec_parameters = params

        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.read_response = Mock()

        list_of_46s = [0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46,
                       0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46, 0x46]
        list_of_30s = [0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
                       0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]

        register_061 = [0x36, 0x31]   # Column Read Enable ASIC1
        register_0C2 = [0x43, 0x32]   # Column Read Enable ASIC2
        value_061 = list_of_46s
        value_0C2 = list_of_46s

        enable_sm = [0x23, vsr_addr, HexitecFem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]
        disable_sm = [0x23, vsr_addr, HexitecFem.CLR_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]

        # Column Power Enable

        register_04D = [0x34, 0x44]   # Column Power Enable ASIC1 (Reg 0x4D)
        register_0AE = [0x41, 0x45]   # Column Power Enable ASIC2 (Reg 0xAE)
        value_04D = list_of_46s
        value_0AE = list_of_46s

        # Column Power Enable, for ASIC1 (Reg 0x4D)
        col_power_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_04D[0], register_04D[1], value_04D[0], value_04D[1],
                             value_04D[2], value_04D[3], value_04D[4], value_04D[5],
                             value_04D[6], value_04D[7], value_04D[8], value_04D[9],
                             value_04D[10], value_04D[11], value_04D[12], value_04D[13],
                             value_04D[14], value_04D[15], value_04D[16], value_04D[17],
                             value_04D[18], value_04D[19], 0x0D]

        # Column Power Enable, for ASIC2 (Reg 0xAE)
        col_power_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_0AE[0], register_0AE[1], value_0AE[0], value_0AE[1],
                             value_0AE[2], value_0AE[3], value_0AE[4], value_0AE[5],
                             value_0AE[6], value_0AE[7], value_0AE[8], value_0AE[9],
                             value_0AE[10], value_0AE[11], value_0AE[12], value_0AE[13],
                             value_0AE[14], value_0AE[15], value_0AE[16], value_0AE[17],
                             value_0AE[18], value_0AE[19], 0x0D]

        # Row Power Enable

        register_02F = [0x32, 0x46]   # Row Power Enable ASIC1 (Reg 0x2F)
        register_090 = [0x39, 0x30]   # Row Power Enable ASIC2 (Reg 0x90)
        value_02F = list_of_46s
        value_090 = list_of_46s

        # Row Power Enable, for ASIC1 (Reg 0x2F)
        row_power_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_02F[0], register_02F[1], value_02F[0], value_02F[1],
                             value_02F[2], value_02F[3], value_02F[4], value_02F[5],
                             value_02F[6], value_02F[7], value_02F[8], value_02F[9],
                             value_02F[10], value_02F[1], value_02F[2], value_02F[3],
                             value_02F[14], value_02F[15], value_02F[16], value_02F[17],
                             value_02F[18], value_02F[19], 0x0D]

        # Row Power Enable, for ASIC2 (Reg 0x90)
        row_power_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                             register_090[0], register_090[1], value_090[0], value_090[1],
                             value_090[2], value_090[3], value_090[4], value_090[5],
                             value_090[6], value_090[7], value_090[8], value_090[9],
                             value_090[10], value_090[11], value_090[12], value_090[13],
                             value_090[14], value_090[15], value_090[16], value_090[17],
                             value_090[18], value_090[19], 0x0D]

        # Column Calibration Enable

        register_057 = [0x35, 0x37]   # Column Calibrate Enable ASIC1 (Reg 0x57)
        register_0B8 = [0x42, 0x38]   # Column Calibrate Enable ASIC2 (Reg 0xB8)
        value_057 = [53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53]
        value_0B8 = list_of_30s

        # Column Calibrate Enable, for ASIC1 (Reg 0x57)
        col_cal_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                           register_057[0], register_057[1], value_057[0], value_057[1],
                           value_057[2], value_057[3], value_057[4], value_057[5],
                           value_057[6], value_057[7], value_057[8], value_057[9],
                           value_057[10], value_057[11], value_057[12], value_057[13],
                           value_057[14], value_057[15], value_057[16], value_057[17],
                           value_057[18], value_057[19], 0x0D]

        # Column Calibrate Enable, for ASIC2 (Reg 0xB8)
        col_cal_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                           register_0B8[0], register_0B8[1], value_0B8[0], value_0B8[1],
                           value_0B8[2], value_0B8[3], value_0B8[4], value_0B8[5],
                           value_0B8[6], value_0B8[7], value_0B8[8], value_0B8[9],
                           value_0B8[10], value_0B8[11], value_0B8[12], value_0B8[13],
                           value_0B8[14], value_0B8[15], value_0B8[16], value_0B8[17],
                           value_0B8[18], value_0B8[19], 0x0D]

        # Row Calibration Enable

        register_039 = [0x33, 0x39]   # Row Calibrate Enable ASIC1 (Reg 0x39)
        register_09A = [0x39, 0x41]   # Row Calibrate Enable ASIC2 (Reg 0x9A)
        value_039 = [53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53]
        value_09A = list_of_30s

        # Row Calibrate Enable, for ASIC1 (Reg 0x39)
        row_cal_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                           register_039[0], register_039[1], value_039[0], value_039[1],
                           value_039[2], value_039[3], value_039[4], value_039[5],
                           value_039[6], value_039[7], value_039[8], value_039[9],
                           value_039[10], value_039[11], value_039[12], value_039[13],
                           value_039[14], value_039[15], value_039[16], value_039[17],
                           value_039[18], value_039[19], 0x0D]

        # Row Calibrate Enable, for ASIC2 (Reg 0x9A)
        row_cal_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                           register_09A[0], register_09A[1], value_09A[0], value_09A[1],
                           value_09A[2], value_09A[3], value_09A[4], value_09A[5],
                           value_09A[6], value_09A[7], value_09A[8], value_09A[9],
                           value_09A[10], value_09A[11], value_09A[12], value_09A[13],
                           value_09A[14], value_09A[15], value_09A[16], value_09A[17],
                           value_09A[18], value_09A[19], 0x0D]

        register_061 = [0x36, 0x31]   # Column Read Enable ASIC1
        register_0C2 = [0x43, 0x32]   # Column Read Enable ASIC2
        value_061 = list_of_46s
        value_0C2 = list_of_46s

        # No ini file loaded, use default values
        col_read_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST, register_061[0],
                            register_061[1], value_061[0], value_061[1], value_061[2],
                            value_061[3], value_061[4], value_061[5], value_061[6],
                            value_061[7], value_061[8], value_061[9], value_061[10],
                            value_061[11], value_061[12], value_061[13], value_061[14],
                            value_061[15], value_061[16], value_061[17], value_061[18],
                            value_061[19], 0x0D]

        # Column Read Enable, for ASIC2 (Reg 0xC2)
        col_read_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                            register_0C2[0], register_0C2[1], value_0C2[0], value_0C2[1],
                            value_0C2[2], value_0C2[3], value_0C2[4], value_0C2[5],
                            value_0C2[6], value_0C2[7], value_0C2[8], value_0C2[9],
                            value_0C2[10], value_0C2[11], value_0C2[12], value_0C2[13],
                            value_0C2[14], value_0C2[15], value_0C2[16], value_0C2[17],
                            value_0C2[18], value_0C2[19], 0x0D]

        # No ini file loaded, use default values
        col_read_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST, register_061[0],
                            register_061[1], value_061[0], value_061[1], value_061[2],
                            value_061[3], value_061[4], value_061[5], value_061[6],
                            value_061[7], value_061[8], value_061[9], value_061[10],
                            value_061[11], value_061[12], value_061[13], value_061[14],
                            value_061[15], value_061[16], value_061[17], value_061[18],
                            value_061[19], 0x0D]

        # Column Read Enable, for ASIC2 (Reg 0xC2)
        col_read_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                            register_0C2[0], register_0C2[1], value_0C2[0], value_0C2[1],
                            value_0C2[2], value_0C2[3], value_0C2[4], value_0C2[5],
                            value_0C2[6], value_0C2[7], value_0C2[8], value_0C2[9],
                            value_0C2[10], value_0C2[11], value_0C2[12], value_0C2[13],
                            value_0C2[14], value_0C2[15], value_0C2[16], value_0C2[17],
                            value_0C2[18], value_0C2[19], 0x0D]

        # Row Read Enable

        register_043 = [0x34, 0x33]   # Row Read Enable ASIC1
        register_0A4 = [0x41, 0x34]   # Row Read Enable ASIC2
        value_043 = list_of_46s
        value_0A4 = list_of_46s

        # Row Read Enable, for ASIC1 (Reg 0x43)
        row_read_enable1 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                            register_043[0], register_043[1], value_043[0], value_043[1],
                            value_043[2], value_043[3], value_043[4], value_043[5],
                            value_043[6], value_043[7], value_043[8], value_043[9],
                            value_043[10], value_043[11], value_043[12], value_043[13],
                            value_043[14], value_043[15], value_043[16], value_043[17],
                            value_043[18], value_043[19], 0x0D]

        # Row Read Enable, for ASIC2 (Reg 0xA4)
        row_read_enable2 = [0x23, vsr_addr, HexitecFem.SEND_REG_BURST,
                            register_0A4[0], register_0A4[1], value_0A4[0], value_0A4[1],
                            value_0A4[2], value_0A4[3], value_0A4[4], value_0A4[5],
                            value_0A4[6], value_0A4[7], value_0A4[8], value_0A4[9],
                            value_0A4[10], value_0A4[11], value_0A4[12], value_0A4[13],
                            value_0A4[14], value_0A4[15], value_0A4[16], value_0A4[17],
                            value_0A4[18], value_0A4[19], 0x0D]

        self.test_fem.fem.load_pwr_cal_read_enables()

        self.test_fem.fem.send_cmd.assert_has_calls([
            call(disable_sm),
            call(col_power_enable1),
            call(col_power_enable2),
            call(row_power_enable1),
            call(row_power_enable2),
            call(col_cal_enable1),
            call(col_cal_enable2),
            call(row_cal_enable1),
            call(row_cal_enable2),
            call(col_read_enable1),
            call(col_read_enable2),
            call(row_read_enable1),
            call(row_read_enable2),
            call(enable_sm),
        ])

    def test_load_pwr_cal_read_enables_fails_unknown_vsr(self):
        """Test function handles unknown VSR address."""
        vsr_addr = 25
        self.test_fem.fem.vsr_addr = vsr_addr
        with pytest.raises(HexitecFemError) as exc_info:
            self.test_fem.fem.load_pwr_cal_read_enables()
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == "Unknown VSR address! (%s)" % vsr_addr

    def test_write_dac_values(self):
        """Test function handles writing dac values ok."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.read_response = Mock()
        vsr_addr = HexitecFem.VSR_ADDRESS[1]
        self.test_fem.fem.vsr_addr = vsr_addr

        params = \
            {'Control-Settings/VCAL': '0.3',
             'Control-Settings/Uref_mid': '1,000000E+3'}

        self.test_fem.fem.hexitec_parameters = params
        self.test_fem.fem.write_dac_values()

        vcal = [0x30, 0x31, 0x39, 0x39]
        umid = [0x30, 0x35, 0x35, 0x36]
        hv = [0x30, 0x35, 0x35, 0x35]
        dctrl = [0x30, 0x30, 0x30, 0x30]
        rsrv2 = [0x30, 0x38, 0x45, 0x38]

        scommand = [0x23, vsr_addr, self.test_fem.fem.WRITE_DAC_VAL,
                    vcal[0], vcal[1], vcal[2], vcal[3],
                    umid[0], umid[1], umid[2], umid[3],
                    hv[0], hv[1], hv[2], hv[3],
                    dctrl[0], dctrl[1], dctrl[2], dctrl[3],
                    rsrv2[0], rsrv2[1], rsrv2[2], rsrv2[3],
                    0x0D]

        self.test_fem.fem.send_cmd.assert_has_calls([call(scommand)])

    def test_enable_adc(self):
        """Test function handles enables ADCs ok."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.read_response = Mock()
        vsr_addr = HexitecFem.VSR_ADDRESS[0]
        self.test_fem.fem.vsr_addr = vsr_addr

        self.test_fem.fem.enable_adc()

        adc_disable = [0x23, vsr_addr, self.test_fem.fem.CTRL_ADC_DAC, 0x30, 0x32, 0x0D]
        enable_sm = [0x23, vsr_addr, self.test_fem.fem.SET_REG_BIT, 0x30, 0x31, 0x30, 0x31, 0x0D]
        adc_enable = [0x23, vsr_addr, self.test_fem.fem.CTRL_ADC_DAC, 0x30, 0x33, 0x0D]
        adc_set = [0x23, vsr_addr, self.test_fem.fem.WRITE_REG_VAL, 0x31, 0x36, 0x30, 0x39, 0x0D]

        self.test_fem.fem.send_cmd.assert_has_calls([
            call(adc_disable),
            call(enable_sm),
            call(adc_enable),
            call(adc_set)
        ])

    def test_initialise_system(self):
        """Test function initialises the system ok."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.read_response = Mock()
        vsr_addr = HexitecFem.VSR_ADDRESS[0]
        self.test_fem.fem.vsr_addr = vsr_addr

        self.test_fem.fem.selected_sensor = HexitecFem.OPTIONS[2]
        self.test_fem.fem.initialise_sensor = Mock()
        self.test_fem.fem.set_up_state_machine = Mock()
        self.test_fem.fem.write_dac_values = Mock()
        self.test_fem.fem.enable_adc = Mock()
        self.test_fem.fem.load_pwr_cal_read_enables = Mock()
        self.test_fem.fem.calibrate_sensor = Mock()

        self.test_fem.fem.initialise_system()

        # Note current setting, change Register 143 (0x8F) -> 1, confirm changed
        read_vsr2_reg08F = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.READ_REG_VALUE,
                            0x38, 0x46, 0x0D]
        set_vsr2_reg08F = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.SET_REG_BIT,
                           0x38, 0x46, 0x30, 0x31, 0x0D]

        # Repeat with other VSR board
        read_vsr1_reg08F = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.READ_REG_VALUE,
                            0x38, 0x46, 0x0D]
        set_vsr1_reg08F = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.SET_REG_BIT,
                           0x38, 0x46, 0x30, 0x31, 0x0D]

        disable_sm_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.CLR_REG_BIT,
                           0x30, 0x31, 0x30, 0x31, 0x0D]
        disable_sm_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.CLR_REG_BIT,
                           0x30, 0x31, 0x30, 0x31, 0x0D]
        enable_sm_vsr1 = [0x23, HexitecFem.VSR_ADDRESS[0], HexitecFem.SET_REG_BIT,
                          0x30, 0x31, 0x30, 0x31, 0x0D]
        enable_sm_vsr2 = [0x23, HexitecFem.VSR_ADDRESS[1], HexitecFem.SET_REG_BIT,
                          0x30, 0x31, 0x30, 0x31, 0x0D]

        self.test_fem.fem.send_cmd.assert_has_calls([
            call(read_vsr2_reg08F),
            call(set_vsr2_reg08F),
            call(read_vsr1_reg08F),
            call(set_vsr1_reg08F),
            call(disable_sm_vsr1),
            call(disable_sm_vsr2),
            call(enable_sm_vsr1),
            call(enable_sm_vsr2)
        ])

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
        assert self.test_fem.fem.frame_rate == 7154.079227920547

    def test_read_pwr_voltages_vsr1(self):
        """Test function handles power voltages ok."""
        self.test_fem.fem.send_cmd = Mock()
        response = "02E405D108B000020BF90FD207EF088F12281A4400000001"
        self.test_fem.fem.read_response = Mock(return_value=response)
        vsr_addr = HexitecFem.VSR_ADDRESS[0]
        self.test_fem.fem.vsr_addr = vsr_addr
        self.test_fem.fem.debug = True

        self.test_fem.fem.read_pwr_voltages()

        # Note current setting, change Register 143 (0x8F) -> 1, confirm changed
        power_command = [0x23, vsr_addr, HexitecFem.READ_PWR_VOLT, 0x0D]
        self.test_fem.fem.send_cmd.assert_has_calls([call(power_command)])
        assert self.test_fem.fem.vsr1_hv == -2.001293772893632

    def test_read_pwr_voltages_vsr2(self):
        """Test function handles power voltages ok."""
        self.test_fem.fem.send_cmd = Mock()
        response = "02E505D008C400040BFD0FE807F008A612201A4600030000"
        self.test_fem.fem.read_response = Mock(return_value=response)
        vsr_addr = HexitecFem.VSR_ADDRESS[1]
        self.test_fem.fem.vsr_addr = vsr_addr
        self.test_fem.fem.debug = True

        self.test_fem.fem.read_pwr_voltages()

        # Note current setting, change Register 143 (0x8F) -> 1, confirm changed
        power_command = [0x23, vsr_addr, HexitecFem.READ_PWR_VOLT, 0x0D]
        self.test_fem.fem.send_cmd.assert_has_calls([call(power_command)])
        assert self.test_fem.fem.vsr2_hv == -0.37647571428567517

    def test_get_hv_value_handles_value_error(self):
        """Test function handles HV value error."""
        return_value = self.test_fem.fem.get_hv_value("0")
        assert return_value == -1

    def test_read_temperatures_humidity_values_vsr2(self):
        """Test function handle sensor values ok."""
        self.test_fem.fem.send_cmd = Mock()
        response = "7C00270802A702B002D60F"
        self.test_fem.fem.read_response = Mock(return_value=response)
        vsr_addr = HexitecFem.VSR_ADDRESS[1]
        self.test_fem.fem.vsr_addr = vsr_addr
        self.test_fem.fem.debug = True

        self.test_fem.fem.read_temperatures_humidity_values()

        command = [0x23, vsr_addr, 0x52, 0x0D]
        vsr2_ambient = 38.27437499999999
        vsr2_humidity = 13.05851834897383
        vsr2_asic1 = 42.4375
        vsr2_asic2 = 43.0
        vsr2_adc = 45.375

        self.test_fem.fem.send_cmd.assert_has_calls([call(command)])
        assert self.test_fem.fem.vsr2_ambient == vsr2_ambient
        assert self.test_fem.fem.vsr2_humidity == vsr2_humidity
        assert self.test_fem.fem.vsr2_asic1 == vsr2_asic1
        assert self.test_fem.fem.vsr2_asic2 == vsr2_asic2
        assert self.test_fem.fem.vsr2_adc == vsr2_adc

    def test_read_temperatures_humidity_values_vsr1(self):
        """Test function handle sensor values ok."""
        self.test_fem.fem.send_cmd = Mock()
        response = "78882A7002BC0A0002C90F"
        self.test_fem.fem.read_response = Mock(return_value=response)
        vsr_addr = HexitecFem.VSR_ADDRESS[0]
        self.test_fem.fem.vsr_addr = vsr_addr
        self.test_fem.fem.debug = True

        self.test_fem.fem.read_temperatures_humidity_values()

        command = [0x23, vsr_addr, 0x52, 0x0D]
        vsr1_ambient = 35.8934033203125
        vsr1_humidity = 14.721751735713742
        vsr1_asic1 = 43.75
        vsr1_asic2 = 160.0
        vsr1_adc = 44.5625

        self.test_fem.fem.send_cmd.assert_has_calls([call(command)])
        assert self.test_fem.fem.vsr1_ambient == vsr1_ambient
        assert self.test_fem.fem.vsr1_humidity == vsr1_humidity
        assert self.test_fem.fem.vsr1_asic1 == vsr1_asic1
        assert self.test_fem.fem.vsr1_asic2 == vsr1_asic2
        assert self.test_fem.fem.vsr1_adc == vsr1_adc

    def test_read_temperature_humidity_values_handle_wrong_value(self):
        """Test function handles bad sensor values."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.read_response = Mock(return_value="xy")
        return_value = self.test_fem.fem.read_temperatures_humidity_values()
        assert return_value is None

    def test_read_temperature_humidity_values_handle_bad_vsr(self):
        """Test function handles bad sensor values."""
        self.test_fem.fem.send_cmd = Mock()
        self.test_fem.fem.read_response = Mock(return_value="01")
        return_value = self.test_fem.fem.read_temperatures_humidity_values()
        assert return_value is None

    def test_get_ambient_temperature(self):
        """Test temperature calculation work for different values."""
        temperature_conversions = []
        temperature_conversions.append((-41.34875, "0800"))
        temperature_conversions.append((0.00186401367187, '443e'))
        temperature_conversions.append((25.0020666504, '68aa'))
        temperature_conversions.append((60.0007415771, '9ba7'))
        for temperature, hex_value in temperature_conversions:
            calculated_temperature = self.test_fem.fem.get_ambient_temperature(hex_value)
            assert pytest.approx(calculated_temperature) == temperature

    def test_get_ambient_temperature_fails_bad_input(self):
        """Test function fails bad input."""
        bad_hex_value = "2g5"
        return_value = self.test_fem.fem.get_ambient_temperature(bad_hex_value)
        assert return_value == -100

    def test_get_humidity(self):
        """Test humidity calculation work for different values."""
        humidity_conversions = []
        humidity_conversions.append((0.0006103608758678547, '0c4a'))
        humidity_conversions.append((20.2226291294728, '35B4'))
        humidity_conversions.append((40.875715266651405, '6000'))
        humidity_conversions.append((100.00061036087587, 'd916'))
        for humidity, hex_value in humidity_conversions:
            calculated_humidity = self.test_fem.fem.get_humidity(hex_value)
            assert pytest.approx(calculated_humidity) == humidity

    def test_get_humidity_fails_bad_input(self):
        """Test function fails bad input."""
        bad_hex_value = "25%"
        return_value = self.test_fem.fem.get_humidity(bad_hex_value)
        assert return_value == -100

    def test_get_asic_temperature(self):
        """Test function calculates ASIC temperatures correct."""
        asic_conversions = []
        asic_conversions.append((0, "0"))
        asic_conversions.append((25, "190"))
        asic_conversions.append((42.4375, "02A7"))
        asic_conversions.append((50, "320"))
        asic_conversions.append((160, "A00"))
        for asic, hex_value in asic_conversions:
            calculated_asic = self.test_fem.fem.get_asic_temperature(hex_value)
            assert pytest.approx(calculated_asic) == asic

    def test_get_asic_temperature_fails_bad_input(self):
        """Test function fails bad input."""
        bad_hex_value = "25.0"
        return_value = self.test_fem.fem.get_asic_temperature(bad_hex_value)
        assert return_value == -100

    def test_get_adc_temperature(self):
        """Test function calculates adc temperatures correct."""
        adc_conversions = []
        adc_conversions.append((0, "0"))
        adc_conversions.append((25, "190"))
        adc_conversions.append((42.4375, "02A7"))
        adc_conversions.append((50, "320"))
        adc_conversions.append((160, "A00"))
        for adc, hex_value in adc_conversions:
            calculated_adc = self.test_fem.fem.get_adc_temperature(hex_value)
            assert pytest.approx(calculated_adc) == adc

    def test_get_adc_temperature_fails_bad_input(self):
        """Test function fails bad input."""
        bad_hex_value = "25z"
        return_value = self.test_fem.fem.get_adc_temperature(bad_hex_value)
        assert return_value == -100

    def test_set_hexitec_config(self):
        """Test function handles configuration file ok."""
        filename = "control/test/hexitec/config/hexitec_test_config.ini"

        self.test_fem.fem._set_hexitec_config(filename)

        assert self.test_fem.fem.bias_refresh_interval == 130.0
        assert self.test_fem.fem.bias_voltage_refresh is True
        assert self.test_fem.fem.time_refresh_voltage_held == 8.0
        assert self.test_fem.fem.bias_voltage_settle_time == 4.0
        assert self.test_fem.fem.row_s1 == 25
        assert self.test_fem.fem.s1_sph == 13
        assert self.test_fem.fem.sph_s2 == 57

    def test_set_hexitec_config_fails_invalid_filename(self):
        """Test function fails on invalid file name."""
        filename = "invalid/file.name"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_fem.fem._set_hexitec_config(filename)
        assert exc_info.type is ParameterTreeError

    def test_extract_exponential_fails_out_of_range_value(self):
        """Test function fails on value outside of valid range of values."""
        hexitec_parameters = {'Control-Settings/Uref_mid': '4,097000E+3'}
        umid = self.test_fem.fem._extract_exponential(hexitec_parameters,
                                                      'Control-Settings/Uref_mid', bit_range=12)
        assert umid == -1

    def test_extract_exponential_fails_missing_key(self):
        """Test function fails on missing key (i.e. setting)."""
        hexitec_parameters = {'Control-Settings/U___ref_mid': '1,000000E+3'}
        umid = self.test_fem.fem._extract_exponential(hexitec_parameters,
                                                      'Control-Settings/Uref_mid', bit_range=1)
        assert umid == -1

    def test_extract_float_fails_out_of_range_value(self):
        """Test function fails on value outside of valid range of values."""
        hexitec_parameters = {'Control-Settings/VCAL': '3.1'}
        vcal_value = self.test_fem.fem._extract_float(hexitec_parameters, 'Control-Settings/VCAL')
        assert vcal_value == -1

    def test_extract_float_fails_missing_key(self):
        """Test function fails on missing key (i.e. setting)."""
        hexitec_parameters = {'Control-Settings/___L': '1.3'}
        vcal_value = self.test_fem.fem._extract_float(hexitec_parameters,
                                                      'Control-Settings/VCAL')
        assert vcal_value == -1

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
        delay = self.test_fem.fem._extract_integer(hexitec_parameters,
                                                   'Control-Settings/ADC1 Delay', bit_range=2)
        assert delay == -1

    def test_extract_boolean_fails_invalid_value(self):
        """Test function fails non-Boolean value."""
        hexitec_parameters = {'Bias_Voltage/Bias_Voltage_Refresh': '_x?'}
        bias = self.test_fem.fem._extract_boolean(hexitec_parameters,
                                                  'Bias_Voltage/Bias_Voltage_Refresh')
        assert bias == -1

    def test_extract_80_bits(self):
        """Test function correctly extracts 80 bits from 4 channels."""
        vsr = 1
        all_80b = [(70, 70), (70, 70), (70, 70), (70, 70), (70, 70), (70, 70), (70, 70),
                   (70, 70), (70, 70), (70, 70)]
        params = \
            {'Sensor-Config_V1_S1/ColumnEn_1stChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnEn_2ndChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnEn_3rdChannel': '11111111111111111111',
             'Sensor-Config_V1_S1/ColumnEn_4thChannel': '11111111111111111111'}

        channel1 = self.test_fem.fem._extract_80_bits(params, "ColumnEn_", vsr, 1, "Channel")
        assert channel1 == all_80b

    def test_extract_80_bits_missing_configuration(self):
        """Test function fails if any of the four channels not configured."""
        vsr = 1
        params = {}

        channel1 = self.test_fem.fem._extract_80_bits(params, "ColumnEn_", vsr, 1, "Channel")
        assert channel1[0] == (-1, -1)

        params['Sensor-Config_V1_S1/ColumnEn_1stChannel'] = '11111111111111111111'

        channel2 = self.test_fem.fem._extract_80_bits(params, "ColumnEn_", vsr, 1, "Channel")
        assert channel2[0] == (-1, -1)

        params['Sensor-Config_V1_S1/ColumnEn_2ndChannel'] = '11111111111111111111'

        channel3 = self.test_fem.fem._extract_80_bits(params, "ColumnEn_", vsr, 1, "Channel")
        assert channel3[0] == (-1, -1)

        params['Sensor-Config_V1_S1/ColumnEn_3rdChannel'] = '11111111111111111111'

        channel4 = self.test_fem.fem._extract_80_bits(params, "ColumnEn_", vsr, 1, "Channel")
        assert channel4[0] == (-1, -1)

    def test_extract_channel_data_fails_wrong_value_length(self):
        """Test function fails if provided value is a wrong length."""
        params = {'Sensor-Config_V1_S1/ColumnEn_1stChannel': '111111111111111111'}
        key = 'Sensor-Config_V1_S1/ColumnEn_1stChannel'

        with pytest.raises(HexitecFemError) as exc_info:
            first_channel = self.test_fem.fem.extract_channel_data(params, key)
            assert first_channel is None
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == "Invalid length of value in '%s'" % key
