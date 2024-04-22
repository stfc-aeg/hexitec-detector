"""
Test Cases for HexitecAdapter, Hexitec in hexitec.HexitecDAQ, hexitec.Hexitec.

Christian Angelsen, STFC Detector Systems Software Group
"""

from hexitec.adapter import HexitecAdapter, Hexitec, HexitecDetectorDefaults
from odin.adapters.parameter_tree import ParameterTreeError

from json.decoder import JSONDecodeError
import unittest
import pytest
import time
import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, patch, mock_open
else:                         # pragma: no cover
    from mock import Mock, MagicMock, patch


class DetectorAdapterTestFixture(object):
    """Test fixture class."""

    def __init__(self):
        """Initialise object."""
        self.options = {
            "fem":
                """
                camera_ctrl_ip = 127.0.0.1,
                camera_data_ip = 127.0.0.1
                """
        }
        # TODO: Below "hack" prevents polling randomly failing tests relying on add_callback
        # assertion; Needs reworking once watchdog(s) ready to be unit tested
        with patch('hexitec.adapter.HexitecFem'), patch('hexitec.adapter.HexitecDAQ'):
            with patch('hexitec.adapter.Hexitec._start_polling'):  # TODO: To be amended

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

        # set up fake adapters
        fp_return = Mock()
        fp_return.configure_mock(data=self.fp_data)
        self.fake_fp.get = Mock(return_value=fp_return)
        fr_return = Mock()
        # fr_return.configure_mock(data=self.fr_data)
        self.fake_fr.get = Mock(return_value=fr_return)

        fi_return = Mock()
        fi_return.configure_mock(data=self.fi_data)

        self.adapters = {
            "fp": self.fake_fp,
            "fr": self.fake_fr,
            "file_interface": self.fake_fi
        }


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
        with patch('logging.debug') as mock_log:
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

        with patch('hexitec.adapter.HexitecFem') as mock_fem, patch('hexitec.adapter.HexitecDAQ'):

            detector = Hexitec({})

            mock_fem.assert_called_with(
                parent=detector,
                config=defaults.fem
            )

    def test_update_meta(self):
        """Test update meta works."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        meta = {"Sample": 5, "test": False}
        self.test_adapter.detector.update_meta(meta)
        assert self.test_adapter.detector.xtek_meta == meta

    def test_poll_fem_handles_mid_acquisition(self):
        """Test poll fem handles mid acquisition."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.acquisition_completed = True
        self.test_adapter.detector.fem.health = True
        self.test_adapter.detector.poll_fem()
        # Ensure shutdown_processing() was called [it changes the following bool]
        assert self.test_adapter.detector.acquisition_in_progress is False

    def test_poll_fem_handles_processing_completed(self):
        """Test poll fem handles processing completed."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.acquisition_completed = True
        self.test_adapter.detector.get_frames_processed = Mock(return_value=10)
        self.test_adapter.detector.fem.health = True
        self.test_adapter.detector.poll_fem()

        # Ensure shutdown_processing() was called [it changes the following bool]
        assert self.test_adapter.detector.acquisition_in_progress is False
        assert self.test_adapter.detector.fem.acquisition_completed is False

    def test_check_daq_watchdog(self):
        """Test daq watchdog works."""
        self.test_adapter.detector.daq.in_progress = True
        # Ensure time difference is three seconds while timeout artificially at 0 seconds
        self.test_adapter.detector.daq.processing_timestamp = time.time() - 3
        self.test_adapter.detector.daq_idle_timeout = 0

        self.test_adapter.detector.check_daq_watchdog()
        # Ensure shutdown_processing() was called [it changes the following two bools]
        assert self.test_adapter.detector.daq.shutdown_processing is True
        assert self.test_adapter.detector.acquisition_in_progress is False

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
        self.test_adapter.detector.fem.connect_hardware = Mock()
        self.test_adapter.detector.connect_hardware("")
        self.test_adapter.detector.fem.connect_hardware.assert_called()

    def test_initialise_hardware(self):
        """Test function initialises hardware.

        First initialisation means 2 frames should be collected.
        """
        frames = 10
        self.test_adapter.detector.number_frames = frames

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.initialise_hardware("")

            assert self.test_adapter.detector.backed_up_number_frames == frames
            # assert self.test_adapter.detector.number_frames == 2
            i = mock_loop.instance()
            i.call_later.assert_called_with(0.5, self.test_adapter.detector.monitor_fem_progress)

    def test_disconnect_hardware(self):
        """Test function disconnects hardware."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.daq.in_progress = False
        # Only change to ensure function working ok:
        self.test_adapter.detector.system_health = False
        self.test_adapter.detector.disconnect_hardware("")
        self.test_adapter.detector.system_health is True

    def test_disconnect_hardware_stalled_daq_and_hardware(self):
        """Test function gracefully handles stalled daq, hardware."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.daq.in_progress = True
        self.test_adapter.detector.fem.hardware_busy = True
        with patch("hexitec.adapter.IOLoop") as mock:
            self.test_adapter.detector.cancel_acquisition = Mock()
            self.test_adapter.detector.shutdown_processing = Mock()
            self.test_adapter.detector.disconnect_hardware("")
            assert self.test_adapter.detector.acquisition_in_progress is False
            self.test_adapter.detector.cancel_acquisition.assert_called_with()
            self.test_adapter.detector.shutdown_processing.assert_called_with()
            i = mock.instance()
            i.call_later.assert_called_with(0.2, self.test_adapter.detector.fem.disconnect_hardware)

    def test_trip_base_path(self):
        """Test function correctly strips out base path."""
        keyword = "data"
        path = '/hxt_sw/src/hexitec-detector/data/config/m_2x6.txt'
        stripped_path = "data/config/m_2x6.txt"
        returned_string = self.test_adapter.detector.strip_base_path(path, keyword)
        assert returned_string == stripped_path

    def test_save_odin(self):
        """Test function works ok."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        with patch("builtins.open", mock_open(read_data="data")):
            with patch('json.dump'):
                self.test_adapter.detector.save_odin("")

    def test_save_odin_handles_exception(self):
        """Test function handles Exception."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        odin_config_file = self.test_adapter.detector.odin_config_file
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            with patch('json.dump') as mock_dump:
                mock_dump.side_effect = Exception()
                self.test_adapter.detector.save_odin("")
                m = "Saving Odin config"
                self.test_adapter.detector.fem.flag_error.assert_called_with(m, "")
                mock_file.assert_called_with(odin_config_file, "w")

    def test_load_odin(self):
        """Test function works ok."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        with patch("builtins.open", mock_open(read_data="data")):
            with patch('json.load'):
                self.test_adapter.detector.load_odin("")

    def test_load_odin_handles_file_not_found_error(self):
        """Test function handles FileNotFoundError."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        with patch('json.load') as mock_load:
            mock_load.side_effect = FileNotFoundError()
            self.test_adapter.detector.load_odin("")
            m = "Loading Odin config - file missing"
            self.test_adapter.detector.fem.flag_error.assert_called_with(m, "")

    def test_load_odin_handles_json_decode_error(self):
        """Test function handles JSONDecodeError."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        with patch('json.load') as mock_load:
            doc = """{"plugin":{"disc": "all"}},{"exec":{"index": "fake.json"}}]"""
            e_msg = "Fake Exception"
            mock_load.side_effect = JSONDecodeError(e_msg, doc, 0)
            self.test_adapter.detector.load_odin("")
            m = "Loading Odin config - Bad json?"
            e = "Fake Exception: line 1 column 1 (char 0)"
            self.test_adapter.detector.fem.flag_error.assert_called_with(m, e)

    def test_set_duration_enable_true(self):
        """Test function can update duration enable to True."""
        self.test_adapter.detector.set_duration_enable(True)
        assert self.test_adapter.detector.duration_enable is True

    def test_set_duration_enable_False(self):
        """Test function can update duration enable to False."""
        self.test_adapter.detector.set_duration_enable(False)
        assert self.test_adapter.detector.duration_enable is False

    def test_set_number_frames(self):
        """Test function sets number of frames."""
        frames = 12
        self.test_adapter.detector.set_number_frames(frames)
        assert self.test_adapter.detector.number_frames == frames

        with pytest.raises(ParameterTreeError, match="frames must be above 0!"):
            self.test_adapter.detector.set_number_frames(-1)

    def test_set_duration(self):
        """Test function sets collection duration."""
        duration = 2
        self.test_adapter.detector.set_duration(duration)
        assert self.test_adapter.detector.duration == duration

        with pytest.raises(ParameterTreeError, match="duration must be above 0!"):
            self.test_adapter.detector.set_duration(-1)

    def test_set_elog(self):
        """Test function sets elog correctly."""
        entry = "Captain's log"
        self.test_adapter.detector.set_elog(entry)
        assert self.test_adapter.detector.elog == entry

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
        frames = 10
        self.test_adapter.detector.set_number_frames(frames)
        assert self.test_adapter.detector.number_frames == frames

    def test_detector_acquisition_clears_previous_daq_errors(self):
        """Test function clears any previous daq error."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )
        self.test_adapter.detector.daq.in_error = True
        self.test_adapter.detector.adapters = self.test_adapter.adapters

        with patch("hexitec.adapter.IOLoop"):
            self.test_adapter.detector.acquisition("data")
            assert self.test_adapter.detector.daq.in_error is False

    def test_detector_acquisition_correct(self):
        """Test acquisition function works."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )

        self.test_adapter.detector.adapters = self.test_adapter.adapters

        self.test_adapter.detector.acquisition("data")
        self.test_adapter.detector.daq.prepare_daq.assert_called_with(10)

    def test_detector_acquisition_prevents_new_acquisition_whilst_one_in_progress(self):
        """Test adapter won't start acquisition whilst one already in progress."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=True
        )
        self.test_adapter.detector.acquisition("data")
        self.test_adapter.detector.daq.prepare_odin.assert_not_called()

    def test_detector_acquisition_prevents_acquisition_if_odin_not_ready(self):
        """Test adapter won't start acquisition while FR/FP not ready."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )
        self.test_adapter.detector.daq.prepare_odin = Mock(return_value=False)
        self.test_adapter.detector.acquisition("data")
        self.test_adapter.detector.daq.prepare_odin.assert_called()
        self.test_adapter.detector.daq.prepare_daq.assert_not_called()

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

    def test_cancel_acquisition(self):
        """Test function can cancel (in software) ongoing acquisition."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )

        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fem.stop_acquisition = False
        self.test_adapter.detector.cancel_acquisition()

        assert self.test_adapter.detector.fem.stop_acquisition is True

    def test_collect_offsets(self):
        """Test function initiates collect offsets."""
        self.test_adapter.detector.fem.hardware_busy = False
        self.test_adapter.detector._collect_offsets("")
        self.test_adapter.detector.fem.collect_offsets.assert_called()

    def test_commit_configuration(self):
        """Test function calls daq's commit_configuration."""
        self.test_adapter.detector.commit_configuration("")
        self.test_adapter.detector.daq.commit_configuration.assert_called()

    def test_commit_configuration_handles_exception(self):
        """Test function handles exception."""
        e = "Error"
        self.test_adapter.detector.fem.prepare_hardware = Mock()
        self.test_adapter.detector.fem.prepare_hardware.side_effect = Exception(e)
        self.test_adapter.detector.commit_configuration("")
        self.test_adapter.detector.daq.commit_configuration.assert_not_called()
        self.test_adapter.detector.fem.flag_error.assert_called_with(e)

    def test_hv_on(self):
        """Test function switches HV on."""
        self.test_adapter.detector.hv_on("")
        self.test_adapter.detector.fem.hv_on.assert_called()

    def test_hv_off(self):
        """Test function switches HV off."""
        self.test_adapter.detector.hv_off("")
        self.test_adapter.detector.fem.hv_off.assert_called()

    def test_environs(self):
        """Test function calls readout environmental data."""
        self.test_adapter.detector.environs("")
        self.test_adapter.detector.fem.environs.assert_called()

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
