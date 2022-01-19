"""Test Cases for HexitecAdapter, Hexitec in hexitec.HexitecDAQ, hexitec.Hexitec.

Christian Angelsen, STFC Detector Systems Software Group
"""

from hexitec.adapter import HexitecAdapter, Hexitec, HexitecDetectorDefaults
from odin.adapters.parameter_tree import ParameterTreeError

import unittest
import pytest
import time
import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, patch
else:                         # pragma: no cover
    from mock import Mock, MagicMock, patch


class DetectorAdapterTestFixture(object):
    """Test fixture class."""

    def __init__(self):
        """Initialise object."""
        self.options = {
            "fem_0":
                """
                id = 0,
                server_ctrl_ip = 127.0.0.1,
                camera_ctrl_ip = 127.0.0.1,
                server_data_ip = 127.0.0.1,
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
        self.fake_fi = MagicMock()

        # once the odin_data adapter is refactored to use param tree, this structure will need fixing
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

        # set up fake adapter
        fp_return = Mock()
        fp_return.configure_mock(data=self.fp_data)
        self.fake_fp.get = Mock(return_value=fp_return)

        fi_return = Mock()
        fi_return.configure_mock(data=self.fi_data)

        self.adapters = {
            "fp": self.fake_fp,
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
        assert len(self.test_adapter.detector.fems) == 1
        assert isinstance(self.test_adapter.detector.fems[0], MagicMock)
        fem = self.test_adapter.detector.fems[0]
        fem.connect()
        fem.connect.assert_called_with()

    def test_detector_init_default_fem(self):
        """Test that the detector correctly sets up the default fem if none provided."""
        defaults = HexitecDetectorDefaults()

        with patch('hexitec.adapter.HexitecFem') as mock_fem, patch('hexitec.adapter.HexitecDAQ'):

            detector = Hexitec({})

            mock_fem.assert_called_with(
                fem_id=defaults.fem["id"],
                parent=detector,
                server_ctrl_ip_addr=defaults.fem["server_ctrl_ip"],
                camera_ctrl_ip_addr=defaults.fem["camera_ctrl_ip"],
                server_data_ip_addr=defaults.fem["server_data_ip"],
                camera_data_ip_addr=defaults.fem["camera_data_ip"]
            )

    def test_detector_init_multiple_fem(self):
        """Test function initialises multiple fems."""
        options = self.test_adapter.options

        options["fem_1"] = """
                id = 0,
                server_ctrl_ip = 127.0.0.2,
                camera_ctrl_ip = 127.0.0.2,
                server_data_ip = 127.0.0.2,
                camera_data_ip = 127.0.0.2
                """
        with patch('hexitec.adapter.HexitecFem'), patch('hexitec.adapter.HexitecDAQ'):

            detector = Hexitec(options)

        assert len(detector.fems) == 2

    def test_poll_fems(self):
        """Test poll fem works."""
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        self.test_adapter.detector.fems[0].acquisition_completed = True
        self.test_adapter.detector.fems[0].health = True
        self.test_adapter.detector.poll_fems()
        # Ensure shutdown_processing() was called [it changes the following bool]
        assert self.test_adapter.detector.acquisition_in_progress is False

    def test_check_fem_watchdog(self):
        """Test fem watchdog works."""
        self.test_adapter.detector.acquisition_in_progress = True
        self.test_adapter.detector.fems[0].hardware_busy = True
        self.test_adapter.detector.fems[0].acquire_timestamp = time.time()
        self.test_adapter.detector.fem_tx_timeout = 0
        self.test_adapter.detector.check_fem_watchdog()
        # Ensure shutdown_processing() was called [it changes the following two bools]
        assert self.test_adapter.detector.daq.shutdown_processing is True
        assert self.test_adapter.detector.acquisition_in_progress is False

    def test_check_daq_watchdog(self):
        """Test daq watchdog works."""
        self.test_adapter.detector.daq.in_progress = True
        # Ensure time difference is three seconds while timeout artificially at 0 seconds
        self.test_adapter.detector.daq.processed_timestamp = time.time() - 3
        self.test_adapter.detector.daq_rx_timeout = 0

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

            assert self.test_adapter.fp_data["value"] == [rc_value]

    def test_detector_get_od_status_misnamed_adapter(self):
        """Test detector throws exception on misnamed adapter."""
        with patch("hexitec.adapter.ApiAdapterRequest"):

            # Initialise adapters in adapter
            self.test_adapter.detector.adapters = self.test_adapter.adapters
            adapter = "wRong"
            rc_value = self.test_adapter.detector._get_od_status(adapter)
            response = {"Error": "Adapter {} not found".format(adapter)}

            assert response == rc_value

    def test_connect_hardware(self):
        """Test function works OK."""
        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.bias_clock_running = False
            self.test_adapter.detector.connect_hardware("")

            mock_loop.instance().add_callback.assert_called_with(self.test_adapter.detector.start_bias_clock)

    def test_start_bias_clock(self):
        """Test function starch bias clock if not already running."""
        self.test_adapter.detector.fems[0].bias_refresh_interval = 60.0
        self.test_adapter.detector.start_bias_clock()
        bias_clock_running = self.test_adapter.detector.bias_clock_running
        init_time = self.test_adapter.detector.bias_init_time
        assert bias_clock_running is True
        assert pytest.approx(init_time) == time.time()

    def test_poll_bias_clock_allow_collection_outside_outside_of_bias_window(self):
        """Test function allows data collection outside bias (blackout) window."""
        bri = 60.0
        bvst = 3.0
        trvh = 2.0
        self.test_adapter.detector.fems[0].bias_refresh_interval = bri
        self.test_adapter.detector.fems[0].bias_voltage_settle_time = bvst
        self.test_adapter.detector.fems[0].time_refresh_voltage_held = trvh
        self.test_adapter.detector.bias_init_time = time.time()

        self.test_adapter.detector.collect_and_bias_time = bri + bvst + trvh

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.poll_bias_clock()
            mock_loop.instance().call_later.assert_called_with(0.1,
                                                               self.test_adapter.detector.poll_bias_clock)

    def test_poll_bias_clock_blocks_collection_during_bias_window(self):
        """Test function blocks data collection during bias window."""
        bri = 60.0
        bvst = 3.0
        trvh = 2.0
        self.test_adapter.detector.fems[0].bias_refresh_interval = bri
        self.test_adapter.detector.fems[0].bias_voltage_settle_time = bvst
        self.test_adapter.detector.fems[0].time_refresh_voltage_held = trvh
        # Trick bias clock to go beyond collection window
        self.test_adapter.detector.bias_init_time = time.time() - bri

        self.test_adapter.detector.collect_and_bias_time = bri + bvst + trvh

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.poll_bias_clock()
            assert self.test_adapter.detector.bias_blocking_acquisition is True
            mock_loop.instance().call_later.assert_called_with(0.1,
                                                               self.test_adapter.detector.poll_bias_clock)

    def test_poll_bias_clock_reset_bias_clock_beyond_blackout_period(self):
        """Test function resets bias clock (collection allowed) when bias blackout exceeded."""
        bri = 60.0
        bvst = 3.0
        trvh = 2.0
        self.test_adapter.detector.fems[0].bias_refresh_interval = bri
        self.test_adapter.detector.fems[0].bias_voltage_settle_time = bvst
        self.test_adapter.detector.fems[0].time_refresh_voltage_held = trvh

        self.test_adapter.detector.collect_and_bias_time = bri + bvst + trvh

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.poll_bias_clock()
            mock_loop.instance().call_later.assert_called_with(0.1,
                                                               self.test_adapter.detector.poll_bias_clock)

    def test_initialise_hardware(self):
        """Test function initialises hardware.

        First initialisation means 2 frames should be collected.
        """
        frames = 10
        self.test_adapter.detector.number_frames = frames
        self.test_adapter.detector.first_initialisation = True

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.initialise_hardware("")

            assert self.test_adapter.detector.acquisition_in_progress is True
            assert self.test_adapter.detector.backed_up_number_frames == frames
            assert self.test_adapter.detector.number_frames == 2
            mock_loop.instance().call_later.assert_called_with(0.5,
                                                               self.test_adapter.detector.check_fem_finished_sending_data)

    def test_disconnect_hardware(self):
        """Test function disconnects hardware and stops bias clock."""
        self.test_adapter.detector.bias_clock_running = True
        self.test_adapter.detector.disconnect_hardware("")
        assert self.test_adapter.detector.bias_clock_running is False

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
        frames = 13
        self.test_adapter.detector.set_number_frames(frames)
        assert self.test_adapter.detector.number_frames == frames

    def test_set_duration(self):
        """Test function sets collection duration."""
        duration = 2
        self.test_adapter.detector.set_duration(duration)
        assert self.test_adapter.detector.duration == duration

    def test_detector_initialize(self):
        """Test function can initialise adapters."""
        adapters = {
            "proxy": Mock(),
            "file_interface": Mock(),
            "fp": Mock(),
        }

        self.test_adapter.adapter.initialize(adapters)

        assert adapters == self.test_adapter.detector.adapters
        self.test_adapter.detector.daq.initialize.assert_called_with(adapters)

    def test_detector_set_acq(self):
        """Test function can set number of frames."""
        self.test_adapter.detector.set_number_frames(5)

        assert self.test_adapter.detector.number_frames == 5

    def test_detector_acquisition_handles_extended_acquisition(self):
        """Test function handles acquisition spanning >1 collection windows."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )

        self.test_adapter.detector.fems[0].bias_voltage_refresh = True
        self.test_adapter.detector.bias_blocking_acquisition = False
        self.test_adapter.detector.fems[0].bias_refresh_interval = 2
        self.test_adapter.detector.bias_init_time = time.time()
        self.test_adapter.detector.adapters = self.test_adapter.adapters

        with patch("hexitec.adapter.IOLoop"):

            self.test_adapter.detector.acquisition("data")
            assert self.test_adapter.detector.extended_acquisition is True

    def test_detector_acquisition_correct(self):
        """Test acquisition function works."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )

        self.test_adapter.detector.fems[0].bias_voltage_refresh = False
        self.test_adapter.detector.first_initialisation = True
        self.test_adapter.detector.adapters = self.test_adapter.adapters

        self.test_adapter.detector.acquisition("data")
        self.test_adapter.detector.daq.start_acquisition.assert_called_with(10)

    def test_detector_acquisition_respects_bias_blocking(self):
        """Test function won't acquire data while bias blocking."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )

        self.test_adapter.detector.fems[0].bias_voltage_refresh = True
        self.test_adapter.detector.bias_blocking_acquisition = True

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.acquisition("data")
            mock_loop.instance().call_later.assert_called_with(0.1,
                                                               self.test_adapter.detector.acquisition)

    def test_detector_acquisition_respects_collection_window(self):
        """Test function won't acquire data time window to small (i.e. < 0s)."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )

        self.test_adapter.detector.fems[0].bias_voltage_refresh = True
        self.test_adapter.detector.bias_blocking_acquisition = False
        self.test_adapter.detector.fems[0].bias_refresh_interval = 2

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.acquisition("data")
            mock_loop.instance().call_later.assert_called_with(0.09,
                                                               self.test_adapter.detector.acquisition)

    def test_await_daq_ready_waits_for_daq(self):
        """Test adapter's await_daq_ready waits for DAQ to be ready."""
        self.test_adapter.detector.daq.configure_mock(
            file_writing=False
        )
        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.await_daq_ready()
            mock_loop.instance().call_later.assert_called_with(0.05,
                                                               self.test_adapter.detector.await_daq_ready)

    def test_await_daq_ready_triggers_fem(self):
        """Test adapter's await_daq_ready triggers FEM(s) when ready."""
        self.test_adapter.detector.daq.configure_mock(
            file_writing=True
        )
        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.await_daq_ready()
            mock_loop.instance().call_later.assert_called_with(0.08,
                                                               self.test_adapter.detector.trigger_fem_acquisition)

    def test_trigger_fem_acquisition(self):
        """Test trigger data acquisition in FEM(s)."""
        with patch("hexitec.adapter.IOLoop") as mock_loop:
            self.test_adapter.detector.trigger_fem_acquisition()
            mock_loop.instance().call_later.assert_called_with(0.0,
                                                               self.test_adapter.detector.check_fem_finished_sending_data)
        init_time = self.test_adapter.detector.fem_start_timestamp
        assert pytest.approx(init_time) == time.time()

    def test_detector_acquisition_prevents_new_acquisition_whilst_one_in_progress(self):
        """Test adapter won't start acquisition whilst one already in progress."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=True
        )
        self.test_adapter.detector.acquisition("data")

        self.test_adapter.detector.daq.start_acquisition.assert_not_called()

    def test_check_fem_finished_sending_data_loop_if_hardware_busy(self):
        """Test function calls itself while fem busy sending data."""
        self.test_adapter.detector.fems[0].hardware_busy = True

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.check_fem_finished_sending_data()
            mock_loop.instance().call_later.assert_called_with(0.5,
                                                               self.test_adapter.detector.check_fem_finished_sending_data)

    def test_check_fem_finished_sending_data_acquire_outstanding_frames(self):
        """Test function calls acquire to collect all required frames.

        Where collection spans single bias window, need to revisit acquisition()
        multiple time(s).
        """
        self.test_adapter.detector.fems[0].hardware_busy = False
        self.test_adapter.detector.extended_acquisition = True
        self.test_adapter.detector.frames_already_acquired = 10
        self.test_adapter.detector.number_frames = 20

        with patch("hexitec.adapter.IOLoop") as mock_loop:

            self.test_adapter.detector.check_fem_finished_sending_data()
            mock_loop.instance().add_callback.assert_called_with(self.test_adapter.detector.acquisition)

    def test_check_fem_finished_sending_data_resets_variables_on_completion(self):
        """Test function resets variables when all data has been sent.

        Testing scenario: user requested 10 frames on cold start, therefore
        system is acquiring two frames as part of initialisation.
        """
        frames = 10
        self.test_adapter.detector.number_frames = 2
        self.test_adapter.detector.number_frames = frames
        self.test_adapter.detector.fems[0].hardware_busy = False
        self.test_adapter.detector.extended_acquisition = False
        self.test_adapter.detector.first_initialisation = True
        self.test_adapter.detector.adapters = self.test_adapter.adapters

        with patch("hexitec.adapter.IOLoop"):

            self.test_adapter.detector.check_fem_finished_sending_data()
            assert self.test_adapter.detector.number_frames == frames
            assert self.test_adapter.detector.initial_acquisition is True
            assert self.test_adapter.detector.extended_acquisition is False
            assert self.test_adapter.detector.acquisition_in_progress is False

    def test_cancel_acquisition(self):
        """Test function can cancel (in software) ongoing acquisition."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )

        self.test_adapter.detector.fems[0].bias_voltage_refresh = False
        self.test_adapter.detector.first_initialisation = True
        self.test_adapter.detector.adapters = self.test_adapter.adapters
        print(self.test_adapter.adapters)
        self.test_adapter.detector.fems[0].stop_acquisition = False
        self.test_adapter.detector.cancel_acquisition()

        assert self.test_adapter.detector.fems[0].stop_acquisition is True

    def test_collect_offsets(self):
        """Test function initiates collect offsets."""
        self.test_adapter.detector.fems[0].hardware_busy = False
        self.test_adapter.detector._collect_offsets("")
        self.test_adapter.detector.fems[0].collect_offsets.assert_called()
        # assert self.test_adapter.detector.fems[0].hardware_busy is True

    def test_commit_configuration(self):
        """Test function calls daq's commit_configuration."""
        self.test_adapter.detector.commit_configuration("")
        self.test_adapter.detector.daq.commit_configuration.assert_called()
