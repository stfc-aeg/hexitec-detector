"""
Test Cases for HexitecAdapter, Hexitec in hexitec.HexitecDAQ, hexitec.Hexitec.

Christian Angelsen, STFC Detector Systems Software Group
"""

from hexitec.adapter import HexitecAdapter, Hexitec, HexitecDetectorDefaults
from odin.adapters.parameter_tree import ParameterTreeError

from json.decoder import JSONDecodeError
import unittest
import pytest
import os

from unittest.mock import Mock, MagicMock, patch, mock_open


class DetectorAdapterTestFixture(object):
    """Test fixture class."""

    def __init__(self):
        """Initialise object."""
        cwd = os.getcwd()
        base_path_index = cwd.rfind("control")  # i.e. /path/to/hexitec-detector
        repo_path = cwd[:base_path_index - 1]
        data_config_path = repo_path + "/data/config/"
        control_config_path = cwd + "/config/"
        self.options = {
            "control_config": f"{control_config_path}",
            "data_config": f"{data_config_path}",
            "fem":
                """
                camera_ctrl_ip = 127.0.0.1,
                camera_data_ip = 127.0.0.1
                """
        }
        with patch("hexitec.adapter.HexitecFem"), patch("hexitec.adapter.HexitecDAQ"):
            with patch("hexitec.adapter.Hexitec.start_polling"):

                self.adapter = HexitecAdapter(**self.options)
                self.detector = self.adapter.hexitec  # shortcut, makes assert lines shorter
                self.path = "detector/acquisition/number_frames"
                self.put_data = 1024
                self.request = Mock()
                self.request.configure_mock(
                    headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                    body=self.put_data
                )
                self.request_again = Mock()
                self.request_again.configure_mock(
                    headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                    body=5
                )
        self.fake_fp = MagicMock()
        self.fake_fr = MagicMock()
        self.fake_fi = MagicMock()
        self.fake_proxy = MagicMock()

        # Once the odin_data adapter is refactored to use param tree,
        # this structure will need fixing
        self.fp_data = {
            "value": [
                {
                    "status": {
                        "configuration_complete": True,
                    },
                    "connected": True,
                    "plugins": {
                        "names": [
                            "correction",
                            "hdf",
                            "view"
                        ]

                    },
                    "hdf": {
                        "frames_written": 0,
                        "frames_processed": 0,
                        "writing": True
                    },
                    "histogram": {
                        "frames_processed": 2
                    },
                }
            ]
        }
        self.fi_data = {
            "config_dir": "fake/config_dir",
            "fr_config_files": [
                "first.config",
                "not.config",
                "hexitec_fr.config"
            ],
            "fp_config_files": [
                "not.config",
                "hexitec_fp.config"
            ]
        }
        self.proxy_data = {
            "leak": {
                "system": {
                    "fault": False,
                    "warning": True
                },
                'status': {
                    'leak': {
                        'status_code': 200,
                        'error': 'OK'
                    }
                }
            }
        }

        # set up fake adapters
        fp_return = Mock()
        fp_return.configure_mock(data=self.fp_data)
        self.fake_fp.get = Mock(return_value=fp_return)
        fr_return = Mock()
        # fr_return.configure_mock(data=self.fr_data)
        self.fake_fr.get = Mock(return_value=fr_return)

        proxy_return = Mock()
        proxy_return.configure_mock(data=self.proxy_data)
        self.fake_proxy.get = Mock(return_value=proxy_return)

        fi_return = Mock()
        fi_return.configure_mock(data=self.fi_data)

        self.adapters = {
            "fp": self.fake_fp,
            "fr": self.fake_fr,
            "proxy": self.fake_proxy,
            "file_interface": self.fake_fi
        }
        self.config = \
            {'daq/addition_enable': False, 'daq/bin_end': 8000, 'daq/bin_start': 0,
             'daq/bin_width': 10.0, 'daq/calibration_enable': False, 'daq/compression_type': 'none',
             'daq/discrimination_enable': False, 'daq/file_dir': '/tmp/', 'daq/file_name': 'a',
             'daq/gradients_filename': 'm_2x6.txt', 'daq/image_frequency': 1000000,
             'daq/intercepts_filename': 'c_2x6.txt', 'daq/lvframes_dataset_name': 'raw_frames',
             'daq/lvframes_frequency': 0, 'daq/lvframes_per_second': 2,
             'daq/lvspectra_frequency': 0, 'daq/lvspectra_per_second': 1,
             'daq/max_frames_received': 1000000, 'daq/pass_processed': True, 'daq/pass_raw': True,
             'daq/pixel_grid_size': 5, 'daq/threshold_filename': 'thresh_2x6.txt',
             'daq/threshold_lower': 0, 'daq/threshold_mode': 'filename',
             'daq/threshold_upper': 4400, 'daq/threshold_value': 120, 'duration': 60,
             'duration_enable': True, 'fem/hexitec_config': 'hexitec_2x6.ini', 'number_frames': 8,
             'fem/triggering_frames': 1, 'fem/triggering_mode': 'triggered'}


class TestAdapter(unittest.TestCase):
    """Unit tests for the adapter class."""

    def setUp(self):
        """Set up test fixture for each unit test."""
        self.test_adapter = DetectorAdapterTestFixture()

    # @pytest.mark.skip("Test Skipped")
    def test_adapter_get(self):
        """Test that a call to the detector adapter's GET method returns the correct response."""
        # Hack: Initialise adapters in adapter.py
        self.test_adapter.adapter.adapters = self.test_adapter.adapters

        expected_response = {
            'number_frames': 10
        }
        response = self.test_adapter.adapter.get(
            self.test_adapter.path,
            self.test_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200

    def test_adapter_get_fp_adapter(self):
        """Test that a call to the detector adapter's GET method returns the correct response."""
        # Hack: Initialise adapters in adapter.py
        self.test_adapter.adapter.adapters = self.test_adapter.adapters

        expected_response = {
            'frames_written': 0,
            'frames_processed': 0,
            'writing': True
        }
        response = self.test_adapter.adapter.get(
            "fp/",
            self.test_adapter.request)
        assert response.status_code == 200
        assert expected_response == response.data['value'][0]['hdf']

    def test_adapter_get_error(self):
        """Test adapter handles invalid GET."""
        false_path = "not/a/path"
        expected_response = {
            'error': "Invalid path: {}".format(false_path)
        }
        response = self.test_adapter.adapter.get(
            false_path,
            self.test_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 400

    def test_adapter_get_raises_parameter_tree_exception(self):
        """Test adapter handles parameter tree exception."""
        path = "fp/"
        expected_response = {
            'error': "Invalid path: {}".format(path)
        }

        # Mock logging to provoke ParameterTree exception
        with patch("logging.debug") as mock_log:
            mock_log.side_effect = ParameterTreeError()
            response = self.test_adapter.adapter.get(
                path,
                self.test_adapter.request)
            assert response.data == expected_response
            assert response.status_code == 400

    def test_adapter_put(self):
        """Test that a normal PUT works ok."""
        expected_response = {
            'number_frames': self.test_adapter.put_data
        }
        self.test_adapter.adapter.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.hardware_busy = False
        response = self.test_adapter.adapter.put(
            self.test_adapter.path,
            self.test_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200
        assert self.test_adapter.detector.number_frames == self.test_adapter.put_data

    def test_adapter_put_config_file(self):
        """Test that PUT config_file/ works ok."""
        self.test_adapter.adapter.adapters = self.test_adapter.adapters
        self.test_adapter.adapter.put(
            "fp/config/config_file",
            self.test_adapter.request)

    def test_adapter_put_type_error(self):
        """Test that PUT handles TypeError exception."""
        self.test_adapter.adapter.adapters = self.test_adapter.adapters
        self.test_adapter.adapter.adapters["fp"].put = Mock()
        self.test_adapter.adapter.adapters["fp"].put.side_effect = TypeError("Error")
        request = Mock()
        body = Mock()
        body.side_effect = TypeError("")
        request.configure_mock(
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            body=body
        )
        response = self.test_adapter.adapter.put(
            "fp/config/config_file",
            request)
        error = {'error': 'Failed to decode PUT request body: Error'}
        assert response.data == error
        assert response.status_code == 400

    def test_adapter_put_error(self):
        """Test adapter handles invalid PUT."""
        false_path = "not/a/path"
        expected_response = {
            'error': "Invalid path: {}".format(false_path)
        }

        response = self.test_adapter.adapter.put(
            false_path,
            self.test_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 400
        assert self.test_adapter.detector.number_frames == 10

    def test_adapter_delete(self):
        """Test that adapter's DELETE function works."""
        expected_response = '{}: DELETE on path {}'.format("HexitecAdapter", self.test_adapter.path)
        response = self.test_adapter.adapter.delete(self.test_adapter.path,
                                                    self.test_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200


class TestDetector(unittest.TestCase):
    """Unit tests for detector class."""

    def setUp(self):
        """Set up test fixture for each unit test."""
        self.test_adapter = DetectorAdapterTestFixture()

    def test_detector_init(self):
        """Test function initialises detector OK."""
        defaults = HexitecDetectorDefaults()

        assert self.test_adapter.detector.file_dir == defaults.save_dir
        assert isinstance(self.test_adapter.detector.fem, MagicMock)
        fem = self.test_adapter.detector.fem
        fem.connect()
        fem.connect.assert_called_with()

    def test_detector_init_default_fem(self):
        """Test that the detector correctly sets up the default fem if none provided."""
        defaults = HexitecDetectorDefaults()

        with patch("hexitec.adapter.HexitecFem") as mock_fem, patch("hexitec.adapter.HexitecDAQ"):

            detector = Hexitec({})

            mock_fem.assert_called_with(
                parent=detector,
                config=defaults.fem
            )

    def test_start_polling(self):
        """Test start polling works."""
        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.start_polling()
            i = mock_loop.instance()
            # Patching only recognises last (delayed) function called
            # i.call_later.assert_called_with(1.0, self.test_adapter.detector.load_odin)
            i.call_later.assert_called_with(2.0, self.test_adapter.detector.polling)

    def test_update_meta(self):
        """Test update meta works."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        meta = {"Sample": 5, "test": False}
        self.test_adapter.detector.update_meta(meta)
        assert self.test_adapter.detector.xtek_meta == meta

    def test_check_archiver_running(self):
        """Test function working."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        response = {'status': {'archiver': {'status_code': 200, 'error': 'OK'}}}
        self.test_adapter.detector.get_proxy_adapter_data = Mock(return_value=response)
        self.test_adapter.detector.fem.flag_error = Mock()
        self.test_adapter.detector.check_archiver_running()
        self.test_adapter.detector.fem.flag_error.assert_not_called()

    def test_check_archiver_running_flags_unresponsive_archiver(self):
        """Test function will flag if archiver doesn't respond."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        response = {'status': {'archiver': {
            'status_code': 502, 'error': "HTTPConnectionPool(host='..', port=8888): <SNIP>"
        }}}
        self.test_adapter.detector.get_proxy_adapter_data = Mock(return_value=response)
        self.test_adapter.detector.fem.flag_error = Mock()
        self.test_adapter.detector.check_archiver_running()
        archiver_status = response['status']['archiver']['status_code']
        error = f"Archiver not responding, HTTP code: {archiver_status}"
        self.test_adapter.detector.fem.flag_error.assert_called_with(error)
        assert self.test_adapter.detector.archiver_status == archiver_status

    def test_report_leak_detector_error(self):
        """Test reporting leak detector errors working."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        e_message = "sample error"
        self.test_adapter.detector.fem.create_iso_timestamp = Mock()
        self.test_adapter.detector.report_leak_detector_error(e_message)
        assert self.test_adapter.detector.status_error == e_message
        assert self.test_adapter.detector.leak_error == e_message

    def test_get_proxy_adapter_data_exception(self):
        """Test function handles KeyError."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        # Simulate proxy adapter not loaded:
        del self.test_adapter.detector.adapters["proxy"]
        warning = {'Error': 'Adapter proxy not found'}
        with patch("logging.warning") as mock_log:
            rc = self.test_adapter.detector.get_proxy_adapter_data("proxy")
            mock_log.assert_called()
            assert rc == warning

    def test_parse_leak_detector_response(self):
        """Test parsing leak detector data working."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        r = {
            'leak': {
                'system': {
                    'status': 'OK',
                    'fault': False,
                    'warning': False
                }
            },
            'status': {
                'leak': {
                    'status_code': 200,
                    'error': 'OK'
                }
            }
        }
        fault, warning = self.test_adapter.detector.parse_leak_detector_response(r)
        assert r["leak"]["system"]["fault"] == fault
        assert r["leak"]["system"]["warning"] == warning

    def test_poll_fem_handles_polling_leak_detector_issue_just_cleared(self):
        """Test poll fem handles leak detector issue just resolved."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.acquisition_completed = True
        self.test_adapter.detector.fem._get_status_error = Mock(return_value="")
        self.test_adapter.detector.fem._get_status_message = Mock(return_value="")
        self.test_adapter.detector.get_frames_processed = Mock(return_value=10)
        leak_fault = False
        leak_warning = True
        rv = (leak_fault, leak_warning)
        self.test_adapter.detector.parse_leak_detector_response = Mock(return_value=rv)
        self.test_adapter.detector.software_state = "Interlocked"
        self.test_adapter.detector.fem.health = True
        self.test_adapter.detector.leak_fault = False
        self.test_adapter.detector.leak_warning = False
        self.test_adapter.detector.leak_health = False
        self.test_adapter.detector.poll_fem()
        # Ensure shutdown_processing() was called [it changes the following bool]
        assert self.test_adapter.detector.acquisition_in_progress is False
        assert self.test_adapter.detector.fem.acquisition_completed is False
        assert self.test_adapter.detector.leak_fault is False
        assert self.test_adapter.detector.leak_warning is True
        assert self.test_adapter.detector.software_state == "Cleared"
        assert self.test_adapter.detector.system_health is True

    def test_poll_fem_handles_no_leak_issue_but_fem_fault(self):
        """Test poll fem handles leak detector fine but fem issue."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.acquisition_completed = True
        self.test_adapter.detector.fem._get_status_error = Mock(return_value="Error")
        self.test_adapter.detector.fem._get_status_message = Mock(return_value="")
        self.test_adapter.detector.get_frames_processed = Mock(return_value=10)
        leak_fault = False
        leak_warning = True
        rv = (leak_fault, leak_warning)
        self.test_adapter.detector.parse_leak_detector_response = Mock(return_value=rv)
        self.test_adapter.detector.software_state = "Idle"
        self.test_adapter.detector.fem.health = False
        self.test_adapter.detector.leak_fault = False
        self.test_adapter.detector.leak_warning = False
        self.test_adapter.detector.leak_health = False
        self.test_adapter.detector.poll_fem()
        # Ensure shutdown_processing() was called [it changes the following bool]
        assert self.test_adapter.detector.acquisition_in_progress is False
        assert self.test_adapter.detector.fem.acquisition_completed is False
        assert self.test_adapter.detector.leak_fault is leak_fault
        assert self.test_adapter.detector.leak_warning is leak_warning
        assert self.test_adapter.detector.software_state == "Error"

    def test_poll_fem_handles_leak_fault(self):
        """Test poll fem handles leak detector fault."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.acquisition_completed = False
        self.test_adapter.detector.fem._get_status_error = Mock(return_value="Error")
        self.test_adapter.detector.fem._get_status_message = Mock(return_value="")
        leak_fault = True
        leak_warning = True
        rv = (leak_fault, leak_warning)
        self.test_adapter.detector.parse_leak_detector_response = Mock(return_value=rv)
        self.test_adapter.detector.fem.health = False
        self.test_adapter.detector.leak_fault = True
        self.test_adapter.detector.leak_error = ""
        rv = {"leak": {"system": {"fault": True, "warning": True}}}
        self.test_adapter.detector.get_proxy_adapter_data = Mock(return_value=rv)
        self.test_adapter.detector.report_leak_detector_error = Mock()
        self.test_adapter.detector.poll_fem()
        error = "Leak Detector fault!"
        self.test_adapter.detector.report_leak_detector_error.assert_called_with(error)
        assert self.test_adapter.detector.software_state == "Interlocked"

    def test_poll_fem_handles_exception(self):
        """Test poll fem handles KeyError."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.hardware_connected = False
        self.test_adapter.detector.fem.create_iso_timestamp = Mock()
        self.test_adapter.detector.fem.health = False
        self.test_adapter.detector.leak_fault = True
        self.test_adapter.detector.get_proxy_adapter_data = Mock()
        self.test_adapter.detector.get_proxy_adapter_data.side_effect = KeyError()
        self.test_adapter.detector._set_leak_error = Mock()
        self.test_adapter.detector.software_state = "Connected"
        with patch("logging.error") as mock_log:
            self.test_adapter.detector.poll_fem()
            mock_log.assert_called()
            assert self.test_adapter.detector.software_state == "Interlocked"
            assert self.test_adapter.detector.status_error == "Leak Detector unreachable!"
            self.test_adapter.detector.fem.create_iso_timestamp.assert_called()
            self.test_adapter.detector._set_leak_error.assert_called()

    def test_detector_shutdown_processing_correct(self):
        """Test function shuts down processing."""
        self.test_adapter.detector.daq.shutdown_processing = False
        self.test_adapter.detector.acquisition_in_progress = True

        self.test_adapter.detector.shutdown_processing()

        assert self.test_adapter.detector.daq.shutdown_processing is True
        assert self.test_adapter.detector.acquisition_in_progress is False

    def test_detector_get_od_status_fp(self):
        """Test detector handles valid fp adapter request."""
        with patch("hexitec.adapter.ApiAdapterRequest") as mock_request:

            # Initialise adapters in adapter
            self.test_adapter.detector.adapters = self.test_adapter.adapters

            rc_value = self.test_adapter.detector._get_od_status("fp")
            config = None

            # Doublechecking _get_od_status() fp adapter's get() - redundant?
            mock_request.assert_called_with(config, content_type="application/json")

            assert self.test_adapter.fp_data["value"] == rc_value

    def test_detector_get_od_status_misnamed_adapter(self):
        """Test detector throws exception on misnamed adapter."""
        with patch("hexitec.adapter.ApiAdapterRequest"):
            # Initialise adapters in adapter
            self.test_adapter.detector.adapters = self.test_adapter.adapters
            adapter = "wRong"
            rc_value = self.test_adapter.detector._get_od_status(adapter)
            response = [{"Error": "Adapter {} not found".format(adapter)}]
            assert response == rc_value

    def test_connect_hardware(self):
        """Test function works OK."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state == "Cold"
        self.test_adapter.detector.fem.connect_hardware = Mock()
        self.test_adapter.detector.connect_hardware("")
        self.test_adapter.detector.fem.connect_hardware.assert_called()
        assert self.test_adapter.detector.software_state == "Connecting"

    def test_connect_hardware_handles_interlocked(self):
        """Test function prevents connecting when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        error = "Interlocked: Can't connect with camera"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.connect_hardware("")
        assert exc_info.value.args[0] == error

    def test_apply_config(self):
        """Test function works OK."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        # self.test_adapter.detector.daq.in_progress = False
        self.test_adapter.detector.prepare_fem_farm_mode = Mock()
        self.test_adapter.detector.fem.set_hexitec_config = Mock()
        self.test_adapter.detector.apply_config("")
        self.test_adapter.detector.prepare_fem_farm_mode.assert_called()
        self.test_adapter.detector.fem.set_hexitec_config.assert_called()

    def test_initialise_hardware(self):
        """Test function initialises hardware."""
        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.initialise_hardware("")
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.5, self.test_adapter.detector.monitor_fem_progress)

    def test_initialise_hardware_handles_interlocked(self):
        """Test function prevents initialisation when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        rv = "Interlocked: Can't initialise Hardware"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=rv)
        with pytest.raises(ParameterTreeError, match=rv):
            self.test_adapter.detector.initialise_hardware("")

    def test_disconnect_hardware(self):
        """Test function disconnects hardware."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.hardware_busy = False
        self.test_adapter.detector.fem.hardware_connected = True
        self.test_adapter.detector.fem.disconnect_hardware = Mock()
        # Only change to ensure function working ok:
        self.test_adapter.detector.disconnect_hardware("")
        self.test_adapter.detector.fem.disconnect_hardware.assert_called()

    def test_disconnect_hardware_stalled_daq_and_hardware(self):
        """Test function gracefully handles stalled daq, hardware."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.hardware_busy = True
        self.test_adapter.detector.fem.hardware_connected = True
        software_state = "Acquiring"
        self.test_adapter.detector.software_state = software_state
        error = f"Cannot Disconnect while: {software_state}"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.disconnect_hardware("")
        assert exc_info.value.args[0] == error

    def test_disconnect_hardware_handles_interlocked(self):
        """Test function prevents disconnecting when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        error = "Interlocked: Can't disconnect Hardware"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.disconnect_hardware("")
        assert exc_info.value.args[0] == error

    def test_disconnect_hardware_no_connection(self):
        """Test function prevents disconnecting when connection to disconnect."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.hardware_connected = False
        self.test_adapter.detector.fem.hardware_busy = False
        self.test_adapter.detector.software_state = "Disconnected"
        error = "No connection to disconnect"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.disconnect_hardware("")
        assert exc_info.value.args[0] == error

    def test_strip_base_path(self):
        """Test function correctly strips out base path."""
        keyword = "data/"
        path = self.test_adapter.detector.data_config_path + 'm_2x6.txt'
        stripped_path = "config/m_2x6.txt"
        returned_string = self.test_adapter.detector.strip_base_path(path, keyword)
        assert returned_string == stripped_path

    def test_save_odin(self):
        """Test function works ok."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        with patch("builtins.open", mock_open(read_data="data")):
            with patch("json.dump"):
                self.test_adapter.detector.save_odin("")

    def test_save_odin_handles_exception(self):
        """Test function handles Exception."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        odin_config_file = self.test_adapter.detector.odin_config_file
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            with patch("json.dump") as mock_dump:
                mock_dump.side_effect = Exception()
                self.test_adapter.detector.save_odin("")
                m = "Saving Odin config"
                self.test_adapter.detector.fem.flag_error.assert_called_with(m, "")
                mock_file.assert_called_with(odin_config_file, "w")

    def test_load_odin_duration_enable(self):
        """Test function works ok."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        config = self.test_adapter.config
        self.test_adapter.detector.set_duration = Mock()
        with patch("builtins.open", mock_open(read_data="read_data")):
            with patch("json.load") as mockery:
                mockery.return_value = config
                self.test_adapter.detector.load_odin("")
        self.test_adapter.detector.set_duration.assert_called()

    def test_load_odin_duration_disabled(self):
        """Test function works ok with duration disabled."""
        config = self.test_adapter.config
        config['duration_enable'] = False
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.hardware_busy = False
        self.test_adapter.detector.set_duration_enable = Mock()
        with patch("builtins.open", mock_open(read_data="read_data")):
            with patch("json.load") as mockery:
                mockery.return_value = config
                self.test_adapter.detector.load_odin("")
        self.test_adapter.detector.set_duration_enable.assert_called()

    def test_load_odin_handles_file_not_found_error(self):
        """Test function handles FileNotFoundError."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.hardware_busy = False
        with patch("json.load") as mock_load:
            mock_load.side_effect = FileNotFoundError()
            self.test_adapter.detector.load_odin("")
            m = "Loading Odin config - file missing"
            self.test_adapter.detector.fem.flag_error.assert_called_with(m, "")

    def test_load_odin_handles_json_decode_error(self):
        """Test function handles JSONDecodeError."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        with patch("json.load") as mock_load:
            doc = """{"plugin":{"disc": "all"}},{"exec":{"index": "fake.json"}}]"""
            e_msg = "Fake Exception"
            mock_load.side_effect = JSONDecodeError(e_msg, doc, 0)
            self.test_adapter.detector.load_odin("")
            m = "Loading Odin config - Bad json?"
            e = "Fake Exception: line 1 column 1 (char 0)"
            self.test_adapter.detector.fem.flag_error.assert_called_with(m, e)

    def test_load_odin_handles_exception(self):
        """Test function handles exception."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        with patch("json.load") as mock_load:
            mock_load.side_effect = Exception()
            self.test_adapter.detector.load_odin("")
            m = "Loading Odin values"
            self.test_adapter.detector.fem.flag_error.assert_called_with(m, "")

    def test_set_duration_enable_to_true(self):
        """Test function can update duration enable to True."""
        self.test_adapter.detector.fem.hardware_busy = False
        self.test_adapter.detector.set_duration_enable(True)
        assert self.test_adapter.detector.duration_enable is True

    def test_set_duration_enable_to_false(self):
        """Test function can update duration enable to False."""
        self.test_adapter.detector.fem.hardware_busy = False
        self.test_adapter.detector.set_duration_enable(False)
        assert self.test_adapter.detector.duration_enable is False

    def test_set_duration_enable_handles_interlocked(self):
        """Test function prevents updating duration enabled when interlocked."""
        self.test_adapter.detector.software_state = "Interlocked"
        self.test_adapter.detector.fem.hardware_busy = False
        error = "Interlocked: Can't update duration enable"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.set_duration_enable(False)
        assert exc_info.value.args[0] == error

    def test_set_duration_enable_blocked_while_busy(self):
        """Test function cannot set duration enable while hardware busy."""
        self.test_adapter.detector.fem.hardware_busy = True
        error = "Cannot update duration enable while: Cold"
        with pytest.raises(ParameterTreeError, match=error):
            self.test_adapter.detector.set_duration_enable(True)

    def test_set_duration_enable_blocked_in_triggered_mode(self):
        """Test function cannot set duration enable in triggered mode."""
        self.test_adapter.detector.fem.triggering_mode = "triggered"
        self.test_adapter.detector.fem.hardware_busy = False
        error = "Cannot set duration enable in triggered mode"
        with pytest.raises(ParameterTreeError, match=error) as exc_info:
            self.test_adapter.detector.set_duration_enable(True)
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.fem.flag_error.called_with(error)

    def test_set_number_frames(self):
        """Test function sets number of frames."""
        self.test_adapter.detector.fem.hardware_busy = False
        frames = 12
        self.test_adapter.detector.set_number_frames(frames)
        assert self.test_adapter.detector.number_frames == frames

        with pytest.raises(ParameterTreeError, match="frames must be above 0!"):
            self.test_adapter.detector.set_number_frames(-1)

    def test_set_number_frames_blocked_in_triggered_mode(self):
        """Test function cannot set number of frames in triggered mode."""
        self.test_adapter.detector.fem.triggering_mode = "triggered"
        self.test_adapter.detector.fem.hardware_busy = False
        error = "Cannot set number of frames in triggered mode"
        with pytest.raises(ParameterTreeError, match=error) as exc_info:
            self.test_adapter.detector.set_number_frames(8)
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.fem.flag_error.called_with(error)

    def test_set_number_frames_blocked_while_busy(self):
        """Test function cannot set number of frames while hardware busy."""
        self.test_adapter.detector.software_state = "Cold"
        self.test_adapter.detector.fem.hardware_busy = True
        error = "Cannot update number of frames while: Cold"
        with pytest.raises(ParameterTreeError, match=error):
            self.test_adapter.detector.set_number_frames(8)

    def test_set_number_frames_handles_interlocked(self):
        """Test function prevents updating number of frames when interlocked."""
        self.test_adapter.detector.software_state = "Interlocked"
        self.test_adapter.detector.fem.hardware_busy = False
        error = "Interlocked: Can't update number frames"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.set_number_frames(False)
        assert exc_info.value.args[0] == error

    def test_set_triggering_mode(self):
        """Test function sets triggering mode."""
        self.test_adapter.detector.software_state = "Idle"
        self.test_adapter.detector.fem.hardware_busy = False
        triggering_mode = "triggered"
        self.test_adapter.detector.set_triggering_mode(triggering_mode)
        assert self.test_adapter.detector.fem.set_triggering_mode.called_with(triggering_mode)

    def test_set_triggering_mode_handles_interlocked(self):
        """Test function prevents updating triggering mode when interlocked."""
        self.test_adapter.detector.software_state = "Interlocked"
        self.test_adapter.detector.fem.hardware_busy = False
        error = "Interlocked: Can't update triggering mode"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.set_triggering_mode("triggered")
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.report_leak_detector_error.assert_called_with(error)

    def test_set_triggering_mode_handles_hardware_busy(self):
        """Test function prevents updating triggering mode when hardware busy."""
        self.test_adapter.detector.software_state = "Idle"
        self.test_adapter.detector.fem.hardware_busy = True
        error = "Cannot update triggering mode while: Idle"
        with pytest.raises(ParameterTreeError, match=error) as exc_info:
            self.test_adapter.detector.set_triggering_mode("mode")
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.fem.flag_error.assert_called_with(error)

    def test_set_triggering_frames(self):
        """Test function sets triggering frames."""
        self.test_adapter.detector.software_state = "Idle"
        self.test_adapter.detector.fem.hardware_busy = False
        frames = 5
        self.test_adapter.detector.set_triggering_frames(frames)
        assert self.test_adapter.detector.fem.set_triggering_frames.called
        self.test_adapter.detector.fem.set_triggering_frames.assert_called_with(frames)

    def test_set_triggering_frames_handles_interlocked(self):
        """Test function prevents updating triggering frames when interlocked."""
        self.test_adapter.detector.software_state = "Interlocked"
        self.test_adapter.detector.fem.hardware_busy = False
        error = "Interlocked: Can't update triggering frames"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.set_triggering_frames(5)
        assert exc_info.value.args[0] == error

    def test_set_triggering_frames_blocked_while_busy(self):
        """Test function cannot set triggering frames while hardware busy."""
        self.test_adapter.detector.fem.hardware_busy = True
        error = "Cannot update triggering frames while: Cold"
        with pytest.raises(ParameterTreeError, match=error):
            self.test_adapter.detector.set_triggering_frames(8)

    def test_set_duration(self):
        """Test function sets acquisition duration."""
        self.test_adapter.detector.fem.hardware_busy = False
        duration = 2
        self.test_adapter.detector.set_duration(duration)
        assert self.test_adapter.detector.duration == duration

        with pytest.raises(ParameterTreeError, match="duration must be above 0!"):
            self.test_adapter.detector.set_duration(-1)

    def test_set_duration_blocked_while_busy(self):
        """Test function cannot set acquisition duration while hardware busy."""
        self.test_adapter.detector.fem.hardware_busy = True
        with pytest.raises(ParameterTreeError, match="Cannot update duration while: Cold"):
            self.test_adapter.detector.set_duration(5)

    def test_set_duration_handles_interlocked(self):
        """Test function prevents updating duration when interlocked."""
        self.test_adapter.detector.software_state = "Interlocked"
        self.test_adapter.detector.fem.hardware_busy = False
        error = "Interlocked: Can't update duration"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.set_duration(5)
        assert exc_info.value.args[0] == error

    def test_set_duration_handles_triggered_mode(self):
        """Test function prevents updating duration during triggered mode."""
        self.test_adapter.detector.fem.triggering_mode = "triggered"
        self.test_adapter.detector.fem.hardware_busy = False
        error = "Cannot set duration in triggered mode"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.set_duration(5)
        assert exc_info.value.args[0] == error

    def test_set_elog(self):
        """Test function sets elog correctly."""
        self.test_adapter.detector.fem.hardware_busy = False
        entry = "Captain's log"
        self.test_adapter.detector.set_elog(entry)
        assert self.test_adapter.detector.elog == entry

    def test_set_elog_blocked_while_busy(self):
        """Test function cannot set elog message while hardware busy."""
        self.test_adapter.detector.fem.hardware_busy = True
        entry = "Captain's log"
        with pytest.raises(ParameterTreeError, match="Cannot update eLog message while: Cold"):
            self.test_adapter.detector.set_elog(entry)

    def test_set_elog_handles_interlocked(self):
        """Test function prevents updating elog when interlocked."""
        self.test_adapter.detector.software_state = "Interlocked"
        self.test_adapter.detector.fem.hardware_busy = False
        error = "Interlocked: Can't update eLog message"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.set_elog("different message")
        assert exc_info.value.args[0] == error

    def test_set_number_nodes(self):
        """Test function sets number of nodes."""
        number_nodes = 3
        self.test_adapter.detector.set_number_nodes(number_nodes)
        assert number_nodes == self.test_adapter.detector.number_nodes

    def test_detector_initialize(self):
        """Test function can initialise adapters."""
        adapters = {
            "proxy": Mock(),
            "file_interface": Mock(),
            "fp": Mock(),
            "fr": Mock(),
        }

        self.test_adapter.adapter.initialize(adapters)

        assert adapters == self.test_adapter.detector.adapters
        self.test_adapter.detector.daq.initialize.assert_called_with(adapters)

    def test_detector_set_acq(self):
        """Test function can set number of frames."""
        self.test_adapter.detector.fem.hardware_busy = False
        frames = 10
        self.test_adapter.detector.set_number_frames(frames)
        assert self.test_adapter.detector.number_frames == frames

    def test_detector_start_acquisition_correct(self):
        """Test acquisition function works."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )
        self.test_adapter.detector.fem.check_hardware_ready = Mock()
        self.test_adapter.detector.fem.check_system_initialised = Mock()
        self.test_adapter.detector.daq.commit_configuration = Mock()
        self.test_adapter.detector.daq.prepare_odin = Mock()
        number_frames = 10
        self.test_adapter.detector.number_frames = number_frames

        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.start_acquisition("data")
            instance = mock_loop.instance()
            instance.add_callback.assert_called_with(self.test_adapter.detector.await_daq_configuring_fps)

    def test_await_daq_configuring_fps_wait_while_busy_configuring(self):
        """Test function handles daq busy configuring frameProcessors."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )
        self.test_adapter.detector.daq.busy_configuring_fps = True

        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.await_daq_configuring_fps()
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.05,
                                            self.test_adapter.detector.await_daq_configuring_fps)

    def test_await_daq_configuring_fps_handle_configuring_finished(self):
        """Test function handles daq no longer busy."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )
        self.test_adapter.detector.daq.busy_configuring_fps = False
        number_frames = 10
        self.test_adapter.detector.number_frames = number_frames

        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.daq.in_error = False
            self.test_adapter.detector.await_daq_configuring_fps()
            instance = mock_loop.instance()
            instance.add_callback.assert_called_with(self.test_adapter.detector.await_daq_ready)

        self.test_adapter.detector.daq.prepare_daq.assert_called_with(number_frames)
        assert self.test_adapter.detector.daq.in_error is False
        assert self.test_adapter.detector.acquisition_in_progress is True
        assert self.test_adapter.detector.software_state == "Acquiring"

    def test_detector_start_acquisition_handles_interlocked(self):
        """Test function prevents acquisition when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        error = "Interlocked: Can't acquire data"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.start_acquisition("")
        assert exc_info.value.args[0] == error

    def test_detector_start_acquisition_fails_on_hardware_busy(self):
        """Test function fails when hardware already busy."""
        self.test_adapter.detector.fem.hardware_connected = True
        self.test_adapter.detector.fem.hardware_busy = True
        error = "Can't acquire data, Hardware busy"
        self.test_adapter.detector.fem.check_hardware_ready = Mock()
        self.test_adapter.detector.fem.check_hardware_ready.side_effect = \
            ParameterTreeError(error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.start_acquisition("")
        assert exc_info.value.args[0] == error

    def test_detector_start_acquisition_fails_without_connection(self):
        """Test function fails without established hardware connection."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        error = "Can't acquire data without a connection"
        self.test_adapter.detector.fem.check_hardware_ready = Mock()
        self.test_adapter.detector.fem.check_hardware_ready.side_effect = \
            ParameterTreeError(error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.start_acquisition("")
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.fem.check_hardware_ready.assert_called_with("acquire data")

    def test_acquire_data_fails_system_not_initialised(self):
        """Test function prevents an initialised system from collecting data."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        error = "Can't acquire data, system not initialised"
        self.test_adapter.detector.fem.check_hardware_ready = Mock()
        self.test_adapter.detector.fem.check_system_initialised = Mock()
        self.test_adapter.detector.fem.check_system_initialised.side_effect = \
            ParameterTreeError(error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.start_acquisition("")
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.fem.check_system_initialised.assert_called_with("acquire data")

    def test_detector_start_acquisition_prevents_new_acquisition_whilst_one_in_progress(self):
        """Test adapter won't start acquisition whilst one already in progress."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=True
        )
        self.test_adapter.detector.fem.check_system_initialised = Mock()
        error = "Acquistion already in progress"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.start_acquisition("data")
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.daq.prepare_odin.assert_not_called()

    def test_await_daq_ready_waits_for_daq(self):
        """Test adapter's await_daq_ready waits for DAQ to be ready."""
        self.test_adapter.detector.daq.configure_mock(
            file_writing=False
        )
        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.daq.in_error = False
            self.test_adapter.detector.daq.hdf_is_reset = False
            self.test_adapter.detector.await_daq_ready()
            instance = mock_loop.instance()
            instance.call_later.assert_called_with(0.03, self.test_adapter.detector.await_daq_ready)

    def test_await_daq_ready_handles_daq_error_gracefully(self):
        """Test adapter's await_daq_ready will reset variables, exit function."""
        self.test_adapter.detector.daq.configure_mock(
            file_writing=False
        )
        self.test_adapter.detector.acquisition_in_progress = True
        self.test_adapter.detector.await_daq_ready()
        assert self.test_adapter.detector.acquisition_in_progress is False

    def test_await_daq_ready_triggers_fem(self):
        """Test adapter's await_daq_ready triggers FEM(s) when ready."""
        self.test_adapter.detector.daq.configure_mock(
            file_writing=True
        )
        self.test_adapter.detector.daq.in_error = False

        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.await_daq_ready()
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.08,
                                            self.test_adapter.detector.trigger_fem_acquisition)

    def test_trigger_fem_acquisition(self):
        """Test trigger data acquisition in FEM(s)."""
        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.trigger_fem_acquisition()
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.0, self.test_adapter.detector.monitor_fem_progress)

    def test_monitor_fem_progress_loop_if_hardware_busy(self):
        """Test function calls itself while fem busy sending data."""
        self.test_adapter.detector.fem.hardware_busy = True

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.monitor_fem_progress()
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.5, self.test_adapter.detector.monitor_fem_progress)

    def test_monitor_fem_progress_resets_variables_on_completion(self):
        """Test function resets variables when all data has been sent.

        Testing scenario: user requested 10 frames on cold start, therefore
        system is acquiring two frames as part of initialisation.
        """
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        frames = 10
        self.test_adapter.detector.number_frames = frames
        self.test_adapter.detector.fem.hardware_busy = False
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.reset_state_variables = Mock()

        with patch("hexitec.adapter.IOLoop"):

            self.test_adapter.detector.monitor_fem_progress()
            assert self.test_adapter.detector.number_frames == frames
            assert self.test_adapter.detector.acquisition_in_progress is False
            self.test_adapter.detector.reset_state_variables.assert_called()

    def test_reset_state_variables(self):
        """Test function resets state variables."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.acquisition_in_progress = True
        self.test_adapter.detector.reset_state_variables()
        assert self.test_adapter.detector.acquisition_in_progress is False

    def test_stop_acquisition(self):
        """Test function can cancel (in software) ongoing acquisition."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Acquiring"
        self.test_adapter.detector.fem.cancel_acquisition = False
        self.test_adapter.detector.stop_acquisition()
        assert self.test_adapter.detector.fem.cancel_acquisition is True

    def test_stop_acquisition_no_acquisition(self):
        """Test function blocks cancel if no acquisition running."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Idle"
        self.test_adapter.detector.shutdown_processing = Mock()
        error = "No acquisition in progress"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.stop_acquisition()
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.fem.flag_error.assert_called_with(error)
        self.test_adapter.detector.shutdown_processing.assert_not_called()

    def test_stop_acquisition_handles_interlocked(self):
        """Test function prevents cancelling acquisition when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        rv = "Interlocked: Can't cancel acquisition"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=rv)
        with pytest.raises(ParameterTreeError, match=rv):
            self.test_adapter.detector.stop_acquisition("")

    def test_collect_offsets(self):
        """Test function initiates collect offsets."""
        self.test_adapter.detector.fem.hardware_busy = False
        self.test_adapter.detector.collect_offsets("")
        self.test_adapter.detector.fem.run_collect_offsets.assert_called()

    def test_collect_offsets_handles_interlocked(self):
        """Test function prevents offsets collected when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        rv = "Interlocked: Can't collect offsets"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=rv)
        with pytest.raises(ParameterTreeError, match=rv):
            self.test_adapter.detector.collect_offsets("")

    def test_prepare_fem_farm_mode(self):
        """Test function calls fem's prepare_farm_mode function."""
        self.test_adapter.detector.fem.prepare_hardware = Mock()
        self.test_adapter.detector.prepare_fem_farm_mode("")
        self.test_adapter.detector.fem.prepare_farm_mode.assert_called()

    def test_prepare_fem_farm_mode_handles_exception(self):
        """Test function handles exception."""
        e = "Error"
        self.test_adapter.detector.fem.prepare_farm_mode = Mock()
        self.test_adapter.detector.fem.prepare_farm_mode.side_effect = Exception(e)
        error = f"Prepare fem farm mode: {e}"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.prepare_fem_farm_mode("")
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.fem.flag_error.assert_called_with(error)

    def test_prepare_fem_farm_mode_handles_interlocked(self):
        """Test function prevents setting farm mode when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        error = "Interlocked: Can't load fem farm mode"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=error)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.prepare_fem_farm_mode("")
        assert exc_info.value.args[0] == error

    def test_hv_on(self):
        """Test function switches HV on."""
        self.test_adapter.detector.hv_on("")
        self.test_adapter.detector.fem.hv_on.assert_called()

    def test_hv_on_handles_exception(self):
        """Test function handles exception."""
        e = "Error"
        self.test_adapter.detector.fem.hv_on = Mock()
        self.test_adapter.detector.fem.hv_on.side_effect = Exception(e)
        error = f"Switching on HV: {e}"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.hv_on("")
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.fem.flag_error.assert_called_with(error)

    def test_hv_on_handles_interlocked(self):
        """Test function prevents switching on HV when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        rv = "Interlocked: Can't switch on HV"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=rv)
        with pytest.raises(ParameterTreeError, match=rv):
            self.test_adapter.detector.hv_on("")

    def test_hv_off(self):
        """Test function switches HV off."""
        self.test_adapter.detector.hv_off("")
        self.test_adapter.detector.fem.hv_off.assert_called()

    def test_hv_off_handles_exception(self):
        """Test function handles exception."""
        e = "Error"
        self.test_adapter.detector.fem.hv_off = Mock()
        self.test_adapter.detector.fem.hv_off.side_effect = Exception(e)
        error = f"Switching off HV: {e}"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_adapter.detector.hv_off("")
        assert exc_info.value.args[0] == error
        self.test_adapter.detector.fem.flag_error.assert_called_with(error)

    def test_hv_off_handles_interlocked(self):
        """Test function prevents switching off HV when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        rv = "Interlocked: Can't switch off HV"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=rv)
        with pytest.raises(ParameterTreeError, match=rv):
            self.test_adapter.detector.hv_off("")

    def test_environs(self):
        """Test function calls readout environmental data."""
        self.test_adapter.detector.environs("")
        self.test_adapter.detector.fem.environs.assert_called()

    def test_environs_handles_interlocked(self):
        """Test function prevents reading environs when interlocked."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.software_state = "Interlocked"
        rv = "Interlocked: Can't read environs"
        self.test_adapter.detector.report_leak_detector_error = Mock(return_value=rv)
        with pytest.raises(ParameterTreeError, match=rv):
            self.test_adapter.detector.environs("")

    def test_reset_error(self):
        """Test function reset the error message."""
        self.test_adapter.detector.status_error = "Error"
        self.test_adapter.detector.status_message = "message"
        self.test_adapter.detector.system_health = False
        self.test_adapter.detector.reset_error("")
        self.test_adapter.detector.fem.reset_error.assert_called()
        assert self.test_adapter.detector.status_error == ""
        assert self.test_adapter.detector.status_message == ""
        assert self.test_adapter.detector.system_health is True

    def test_reset_error_leak_fault(self):
        """Test function handle leak detector fault."""
        self.test_adapter.detector.software_date = "Idle"
        self.test_adapter.detector.status_error = "Error"
        self.test_adapter.detector.status_message = "message"
        self.test_adapter.detector.system_health = False
        self.test_adapter.detector.leak_health = False
        leak_error = "Leak Error!"
        self.test_adapter.detector.leak_error = leak_error
        self.test_adapter.detector.reset_error("")
        self.test_adapter.detector.fem.reset_error.assert_called()
        assert self.test_adapter.detector.status_error == leak_error
        assert self.test_adapter.detector.status_message == ""
        assert self.test_adapter.detector.software_state == "Interlocked"
        assert self.test_adapter.detector.system_health is False

        # self.test_adapter.detector.adapters = self.test_adapter.adapters
    def test_reset_error_fem_error(self):
        """Test function handle fem error."""
        self.test_adapter.detector.software_state = "Idle"
        self.test_adapter.detector.status_error = "Error"
        self.test_adapter.detector.status_message = "message"
        self.test_adapter.detector.fem_health = False
        self.test_adapter.detector.leak_health = True
        # leak_error = "Leak Error!"
        # self.test_adapter.detector.leak_error = leak_error
        self.test_adapter.detector.reset_error("")
        self.test_adapter.detector.fem.reset_error.assert_called()
        # assert self.test_adapter.detector.status_error == leak_error
        assert self.test_adapter.detector.status_message == ""
        assert self.test_adapter.detector.software_state == "Error"
        assert self.test_adapter.detector.system_health is False
