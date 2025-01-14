"""
Test Cases for the Hexitec DAQ in hexitec.HexitecDAQ.

Christian Angelsen, STFC Detector Systems Software Group
"""

import statistics
import unittest
import os.path
import pytest
import time
import sys

from odin.adapters.parameter_tree import ParameterTreeError

from hexitec.HexitecDAQ import HexitecDAQ
from hexitec.adapter import HexitecAdapter

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, call, patch, ANY, mock_open
else:                         # pragma: no cover
    from mock import Mock, MagicMock, call, patch, ANY


class DAQTestFixture(object):
    """Set up DAQ test fixture."""

    def __init__(self):
        """Initialise object."""
        cwd = os.getcwd()
        base_path_index = cwd.rfind("control")  # i.e. /path/to/hexitec-detector
        repo_path = cwd[:base_path_index - 1]
        self.data_config_path = repo_path + "/data/config/"
        self.control_config_path = cwd + "/config/"
        self.options = {
            "control_config": f"{self.control_config_path}",
            "data_config": f"{self.data_config_path}",
            "fem":
                """
                farm_mode = /some/config.json
                """
        }
        self.file_dir = "/fake/directory/"
        self.file_name = "fake_file.txt"

        with patch("hexitec.HexitecDAQ.ParameterTree"):
            self.adapter = HexitecAdapter(**self.options)
            self.detector = self.adapter.hexitec  # shortcut, makes assert lines shorter

            self.daq = HexitecDAQ(self.detector, self.file_dir, self.file_name)

        self.fake_fr = MagicMock()
        self.fake_fp = MagicMock()
        self.fake_fi = MagicMock()
        self.fake_lv = MagicMock()
        self.fake_lh = MagicMock()
        self.fake_archiver = MagicMock()

        # Once the odin_data adapter is refactored to use param tree,
        # this structure will need fixing
        self.fr_data = {
            "value": [
                {
                    "buffers": {
                        "empty": 97564,
                        "mapped": 0,
                        "total": 97564
                    },
                    "connected": True,
                    "status": {
                        "configuration_complete": True
                    },
                    'frames': {
                        'timedout': 0,
                        'received': 3188,
                        'released': 3186,
                        'dropped': 0
                    }
                }
            ]
        }
        self.fp_data = {
            "value": [
                {
                    "connected": True,
                    "plugins": {
                        "names": [
                            "correction",
                            "hdf",
                            "view"
                        ]
                    },
                    "hdf": {
                        "file_name": "test.h5",
                        "frames_written": 0,
                        "frames_processed": 0,
                        "writing": True
                    },
                    "histogram": {
                        "sensors_layout": "2x6",
                        "max_frames_received": 10,
                        "bin_start": 0,
                        "bin_end": 8000,
                        "bin_width": 10.0,
                        "frames_processed": 0,
                        "histograms_written": 0,
                        "histogram_index": 1000,
                        "pass_processed": False,
                        "pass_raw": False,
                        "eoa_processed": False
                    }
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
        self.lv_data = {
            "endpoints": ["tcp://127.0.0.1:5020"]
        }
        self.lh_data = {
            "endpoints": ["tcp://127.0.0.1:5021"]
        }
        self.archiver_data = {
            "files_to_archive": "[]"
        }

        # Set up fake adapters
        fr_return = Mock()
        fr_return.configure_mock(data=self.fr_data)
        self.fake_fr.get = Mock(return_value=fr_return)

        fp_return = Mock()
        fp_return.configure_mock(data=self.fp_data)
        self.fake_fp.get = Mock(return_value=fp_return)

        fi_return = Mock()
        fi_return.configure_mock(data=self.fi_data)
        self.fake_fi.get = Mock(return_value=fi_return)

        lv_return = Mock()
        lv_return.configure_mock(data=self.lv_data)
        self.fake_lv.get = Mock(return_value=lv_return)

        lh_return = Mock()
        lh_return.configure_mock(data=self.lh_data)
        self.fake_lh.get = Mock(return_value=lh_return)

        archiver_return = Mock()
        archiver_return.configure_mock(data=self.archiver_data)
        self.fake_archiver.get = Mock(return_value=archiver_return)

        self.adapters = {
            "fp": self.fake_fp,
            "fr": self.fake_fr,
            "file_interface": self.fake_fi,
            "live_histogram": self.fake_lh,
            "live_view": self.fake_lv,
            "archiver": self.fake_archiver
        }

        gradients_filename = self.data_config_path + "m.txt"
        intercepts_filename = self.data_config_path + "c.txt"

        # Fake parameter tree
        self.parameter_dict = \
            {'odin_version': '0.3.1+102.g01c51d7', 'tornado_version': '4.5.3',
             'server_uptime': 48.4, 'detector':
             {'fem':
              {'diagnostics':
               {'acquire_start_time': '', 'acquire_stop_time': '',
                'acquire_time': 1.303241}, 'debug': False, 'frame_rate': 7154.0,
               'health': True, 'status_message': '', 'status_error': '', 'number_frames': 10,
               'duration': 1, 'hexitec_config': '~/path/to/config_file', 'read_sensors': None,
               'hardware_connected': True, 'hardware_busy': False, 'firmware_date': 'N/A',
               'firmware_time': 'N/A',
               'vsr1_sensors':
               {'ambient': 0, 'humidity': 0, 'asic1': 0, 'asic2': 0, 'adc': 0, 'hv': 0},
               'vsr2_sensors':
               {'ambient': 0, 'humidity': 0, 'asic1': 0, 'asic2': 0, 'adc': 0, 'hv': 0}},
              'daq':
              {'diagnostics':
               {'daq_start_time': '', 'daq_stop_time': '', 'fem_not_busy': ''},
               'receiver': {'connected': True, 'configured': True,
                            'config_file': 'fr_hexitec_config.json'},
               'processor': {'connected': True, 'configured': True, 'config_file': 'file.json'},
               'file_info': {'enabled': False, 'file_name': 'filename', 'file_dir': '/tmp/'},
               'status': {'in_progress': True, 'daq_ready': False},
               'config':
               {'addition': {'enable': False, 'pixel_grid_size': 3},
                'calibration':
                {'enable': False,
                 'gradients_filename': gradients_filename,
                 'intercepts_filename': intercepts_filename},
                'discrimination': {'enable': False, 'pixel_grid_size': 3},
                'histogram':
                {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10, 'max_frames_received': 10,
                 'pass_processed': False, 'pass_raw': True},
                'threshold':
                {'threshold_filename': '', 'threshold_mode': 'value', 'threshold_value': 120}},
               'sensors_layout': '2x6'},
              'connect_hardware': None, 'initialise_hardware': None, 'disconnect_hardware': None,
              'collect_offsets': None, 'commit_configuration': None, 'debug_count': 0,
              'acquisition':
              {'number_frames': 10, 'duration': 1, 'duration_enable': False, 'start_acq': None,
               'stop_acq': None, 'in_progress': False},
              'status':
              {'system_health': True, 'status_message': '', 'status_error': ''}}}

        self.daq.initialize(self.adapters)


class TestDAQ(unittest.TestCase):
    """Unit tests for DAQ class."""

    def setUp(self):
        """Set up test fixture for each unit test."""
        self.test_daq = DAQTestFixture()

    def test_init(self):
        """Test initialisation (part 1)."""
        with patch("hexitec.HexitecDAQ.ParameterTree"):
            pa = self.test_daq.adapter.hexitec
            daq = HexitecDAQ(parent=pa, save_file_dir="/fake/directory/",
                             save_file_name="fake_file.txt")
        assert daq.file_dir == self.test_daq.file_dir
        assert daq.file_name == self.test_daq.file_name
        assert daq.in_progress is False
        assert daq.is_initialised is False

    def test_initialize(self):
        """Test initialisation (part 2)."""
        self.test_daq.daq.adapters = {}
        self.test_daq.daq.initialize(self.test_daq.adapters)

        assert self.test_daq.daq.adapters == self.test_daq.adapters
        self.test_daq.fake_fi.get.assert_called()
        assert self.test_daq.daq.config_files['fr'] == ["hexitec_fr.config"]
        assert self.test_daq.daq.config_dir == self.test_daq.fi_data["config_dir"]
        assert self.test_daq.daq.is_initialised is True

    def test_initialize_missing_adapter(self):
        """Test initialisation (part 3)."""
        mocked_dictionary = Mock()
        mocked_dictionary.items.side_effect = KeyError("whoops")
        self.test_daq.daq.initialize(mocked_dictionary)

    def test_initialize_handles_live_view_error(self):
        """Test initialisation with badly configured live_view adapter."""
        new_lv_data = {}
        with patch.dict(self.test_daq.lv_data, new_lv_data, clear=True):
            self.test_daq.daq.initialize(self.test_daq.adapters)

    def test_initialize_handles_live_histogram_error(self):
        """Test initialisation with badly configured live_histogram adapter."""
        new_lh_data = {}
        with patch.dict(self.test_daq.lh_data, new_lh_data, clear=True):
            self.test_daq.daq.initialize(self.test_daq.adapters)

    def test_calculate_average_occupancy(self):
        """Test function works OK."""
        rc_dict = [{'threshold': {'average_frame_occupancy': 0.01958333335}},
                   {'threshold': {'average_frame_occupancy': 0.01911458334}}]

        self.test_daq.daq.get_adapter_status = Mock(return_value=rc_dict)
        occupancy = self.test_daq.daq.calculate_average_occupancy()
        o_list = []
        o_list.append(rc_dict[0].get('threshold', None).get("average_frame_occupancy", None))
        o_list.append(rc_dict[1].get('threshold', None).get("average_frame_occupancy", None))
        calculated_occupancy = statistics.fmean(o_list)

        assert occupancy == calculated_occupancy

    def test_calculate_average_occupancy_handles_KeyError(self):
        """Test function handles KeyError."""
        rc_dict = [{'threshold': {'average_frame_occupancy': 0.01958333335}},
                   {'threshold': {'average_frame_occupancy': 0.01911458334}}]

        self.test_daq.daq.get_adapter_status = Mock(return_value=rc_dict)
        with patch("statistics.fmean") as stats:
            stats.side_effect = KeyError
            occupancy = self.test_daq.daq.calculate_average_occupancy()
            expected_return_value = [{"Error": "Adapter fp not found"}]
            assert occupancy == expected_return_value

    def test_calculate_average_occupancy_handles_AttributeError(self):
        """Test function handles AttributeError."""
        with patch("statistics.fmean") as stats:
            stats.side_effect = AttributeError
            occupancy = self.test_daq.daq.calculate_average_occupancy()
            expected_return_value = 0.0
            assert occupancy == expected_return_value

    def test_is_fr_connected_with_status(self):
        """Test function works."""
        connected = self.test_daq.daq._is_od_connected(self.test_daq.fr_data['value'])
        assert connected

    def test_is_fp_connected_with_status(self):
        """Test function works."""
        connected = self.test_daq.daq._is_od_connected(self.test_daq.fp_data['value'])
        assert connected

    def test_is_fr_connected_without_status(self):
        """Test function works."""
        connected = self.test_daq.daq._is_od_connected(adapter="fr")
        assert connected

    def test_is_fp_connected_without_status(self):
        """Test function works."""
        connected = self.test_daq.daq._is_od_connected(adapter="fp")
        assert connected

    def test_is_fr_configured_with_status(self):
        """Test function works."""
        configured = self.test_daq.daq._is_fr_configured(self.test_daq.fr_data['value'])
        assert configured

    def test_is_fp_configured_with_status(self):
        """Test function works."""
        configured = self.test_daq.daq._is_fp_configured(self.test_daq.fp_data['value'])
        assert configured

    def test_is_fr_configured_without_status(self):
        """Test function works."""
        configured = self.test_daq.daq._is_fr_configured()
        assert configured

    def test_is_fp_configured_without_status(self):
        """Test function works."""
        configured = self.test_daq.daq._is_fp_configured()
        assert configured

    def test_get_config(self):
        """Test getting config file."""
        fp_file = self.test_daq.daq.get_config_file("fp")
        assert fp_file == ["hexitec_fp.config"]

    # TODO: fix this later/Remove get_config_file() altogether  ?
    # def test_get_config_file_not_found(self):
    #     """Test function works."""
    #     new_dict = {
    #         "config_dir": "fake/config_dir",
    #         "fr_config_files": [
    #             "first.config",
    #             "not.config"
    #         ],
    #         "fp_config_files": [
    #             "not.config",
    #             "hexitec_fp.config"
    #         ]
    #     }
    #     with patch.dict(self.test_daq.fi_data, new_dict, clear=True):
    #         fr_file = self.test_daq.daq.get_config_file("fr")

    #     assert fr_file == "first.config"

    def test_get_config_bad_key(self):
        """Test get on non-existent key."""
        value = self.test_daq.daq.get_config_file("bad_key")
        assert value == []

    def test_get_config_pre_init(self):
        """Test function works."""
        with patch("hexitec.HexitecDAQ.ParameterTree"):
            daq = HexitecDAQ(self.test_daq.adapter.hexitec, self.test_daq.file_dir,
                             self.test_daq.file_name)
        value = daq.get_config_file("fr")
        assert value == []

    def test_set_data_dir(self):
        """Test set data directory."""
        self.test_daq.daq.set_data_dir("new/fake/dir/")
        assert self.test_daq.daq.file_dir == "new/fake/dir/"

    def test_set_file_name(self):
        """Test that file name."""
        self.test_daq.daq.set_file_name("new_file_name.hdf")
        assert self.test_daq.daq.file_name == "new_file_name.hdf"

    def test_set_file_writing_to_true(self):
        """Test set file writing to True."""
        self.test_daq.daq.set_file_writing(True)

        self.test_daq.fake_fp.put.assert_has_calls([
            # TODO: REPLACE ANY WITH ApiAdapterRequest
            call("config/hdf/frames", ANY),
            call("config/hdf/file/path", ANY),
            call("config/hdf/file/name", ANY),
            call("config/hdf/write", ANY),
            call("config/histogram/max_frames_received", ANY)
        ])
        assert self.test_daq.daq.file_writing is True

    def test_set_file_writing_to_false(self):
        """Test set file writing to False."""
        self.test_daq.daq.set_file_writing(False)
        assert self.test_daq.daq.file_writing is False
        assert self.test_daq.daq.hdf_is_reset is False

    def test_check_hdf_reset_calls_itself(self):
        """Test function calls itself if total frames processed non-zero."""
        self.test_daq.daq.get_total_frames_processed = Mock(return_value=1)
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.daq.check_hdf_reset()
            instance = mock_loop.instance()
            instance.call_later.assert_called_with(0.1, self.test_daq.daq.check_hdf_reset)

    def test_check_hdf_reset_works(self):
        """Test function flags hdf reset correctly."""
        self.test_daq.daq.get_total_frames_processed = Mock(return_value=0)
        self.test_daq.daq.hdf_is_reset = False
        self.test_daq.daq.check_hdf_reset()
        assert self.test_daq.daq.hdf_is_reset is True

    def test_start_acquisition(self):
        """Test function works."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            self.test_daq.fp_data["value"][0]["hdf"]["frames_processed"] = 0
            self.test_daq.daq.prepare_odin()
            self.test_daq.daq.prepare_daq(10)

            assert self.test_daq.daq.frame_start_acquisition == 0
            assert self.test_daq.daq.in_progress is True
            assert self.test_daq.daq.daq_ready is False
            assert self.test_daq.daq.file_writing is True

            instance = mock_loop.instance()
            instance.call_later.assert_called_with(1.3, self.test_daq.daq.acquisition_check_loop)

    def test_start_prepare_odin_fr_disconnected(self):
        """Test function raises Exception if fr(s) disconnected."""
        new_fr_data = {
            "not_value": False
        }
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop, \
            patch("hexitec.HexitecDAQ.ApiAdapterRequest"), \
                patch.dict(self.test_daq.fr_data, new_fr_data, clear=True):

            error = "Frame Receiver(s) not connected!"
            with pytest.raises(ParameterTreeError) as exc_info:
                self.test_daq.daq.prepare_odin()
            assert exc_info.value.args[0] == error
            assert exc_info.type is ParameterTreeError

            assert self.test_daq.daq.file_writing is False
            assert self.test_daq.daq.in_progress is False

            mock_loop.instance().add_callback.assert_not_called()

    def test_prepare_odin_fr_not_configured(self):
        """Test function raises Exception if fr(s) not configured."""
        new_fp_data = {
            "value": [{
                "connected": True
            }]
        }
        config = {"configuration_complete": False}
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop, \
            patch("hexitec.HexitecDAQ.ApiAdapterRequest"), \
                patch.dict(self.test_daq.fr_data['value'][0]['status'], config, clear=True), \
                patch.dict(self.test_daq.fp_data, new_fp_data, clear=True):

            error = "Frame Receiver(s) not configured!"
            with pytest.raises(ParameterTreeError) as exc_info:
                self.test_daq.daq.prepare_odin()
            assert exc_info.value.args[0] == error
            assert exc_info.type is ParameterTreeError

            # Check that HexitecDAQ.acquisition_check_loop() not called:
            mock_loop.instance().call_later.assert_not_called()

    def test_prepare_odin_fails_if_no_buffers_available(self):
        """Test function flags if there are no buffers available."""
        self.test_daq.daq.are_buffers_available = Mock(return_value=False)
        self.test_daq.fp_data["value"][0]["hdf"]["frames_processed"] = 0
        error = "FR buffers not available!"
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_daq.daq.prepare_daq(10)
            self.test_daq.daq.prepare_odin()
        assert exc_info.value.args[0] == error
        assert exc_info.type is ParameterTreeError

        assert self.test_daq.daq.frame_start_acquisition == 0
        assert self.test_daq.daq.in_progress is True
        assert self.test_daq.daq.daq_ready is False
        assert self.test_daq.daq.file_writing is True

    def test_prepare_odin_fp_disconnected(self):
        """Test function raises Exception if fp(s) disconnected."""
        new_fp_data = {
            "not_value": False
        }
        error = "Frame Processor(s) not connected!"
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop, \
            patch("hexitec.HexitecDAQ.ApiAdapterRequest"), \
                patch.dict(self.test_daq.fp_data, new_fp_data, clear=True):

            with pytest.raises(ParameterTreeError) as exc_info:
                self.test_daq.daq.prepare_odin()
            assert exc_info.value.args[0] == error
            assert exc_info.type is ParameterTreeError
            assert self.test_daq.daq.file_writing is False
            assert self.test_daq.daq.in_progress is False

            mock_loop.instance().add_callback.assert_not_called()

    def test_prepare_odin_fp_not_configured(self):
        """Test function raises Exception if fp(s) not configured."""
        new_fp_data = {
            "value": [{
                "connected": True
            }]
        }
        config = {"configuration_complete": True}
        with patch("hexitec.HexitecDAQ.IOLoop"), \
            patch("hexitec.HexitecDAQ.ApiAdapterRequest"), \
                patch.dict(self.test_daq.fr_data['value'][0]['status'], config, clear=True), \
                patch.dict(self.test_daq.fp_data, new_fp_data, clear=True):

            error = "Frame Processor(s) not configured!"
            with pytest.raises(ParameterTreeError) as exc_info:
                self.test_daq.daq.prepare_odin()
            assert exc_info.value.args[0] == error
            assert exc_info.type is ParameterTreeError

    def test_are_buffers_available_flag_no_empty_buffers(self):
        """Test function flags if frameReceiver buffers are empty."""
        fr_status = [{'status':
                      {'ipc_configured': True, 'decoder_configured': True,
                       'buffer_manager_configured': True, 'rx_thread_configured': True,
                       'configuration_complete': True},
                      'decoder': {'name': 'HexitecFrameDecoder', 'packets_lost': 0,
                                  'fem_packets_lost': [0]},
                      'buffers': {'total': 97564, 'empty': 97564, 'mapped': 0},
                      'frames': {'timedout': 0, 'received': 0, 'released': 0, 'dropped': 0},
                      'timestamp': '2022-11-23T10:09:24.750775', 'connected': True},
                     {'status':
                      {'ipc_configured': True, 'decoder_configured': True,
                       'buffer_manager_configured': True, 'rx_thread_configured': True,
                       'configuration_complete': True},
                      'buffers': {'total': 97564, 'empty': 0, 'mapped': 0},
                      'frames': {'timedout': 0, 'received': 0, 'released': 0, 'dropped': 0},
                      'timestamp': '2022-11-23T10:09:24.751213', 'connected': True},
                     {'status':
                      {'ipc_configured': True, 'decoder_configured': True,
                       'buffer_manager_configured': True, 'rx_thread_configured': True,
                       'configuration_complete': True},
                      'decoder': {'name': 'HexitecFrameDecoder', 'packets_lost': 0,
                                  'fem_packets_lost': [0]},
                      'buffers': {'total': 97564, 'empty': 97564, 'mapped': 0},
                      'frames': {'timedout': 0, 'received': 0, 'released': 0, 'dropped': 0},
                      'timestamp': '2022-11-23T10:09:24.750283', 'connected': True}]
        status = self.test_daq.daq.are_buffers_available(fr_status)
        assert status is False

    def test_acquisition_check_loop(self):
        """Test that function calls itself if hardware busy."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            self.test_daq.adapter.hexitec.fem.hardware_busy = True

            self.test_daq.daq.acquisition_check_loop()
            instance = mock_loop.instance()
            instance.call_later.assert_called_with(.5, self.test_daq.daq.acquisition_check_loop)

    def test_acquisition_check_loop_polls_processing_once_acquisition_complete(self):
        """Test acquisition check loop polls processing status once fem(s) finished sending data."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.daq.frame_end_acquisition = 10
            self.test_daq.daq.acquisition_check_loop()
            instance = mock_loop.instance()
            instance.call_later.assert_called_with(.5, self.test_daq.daq.processing_check_loop)

    def test_calculate_remaining_collection_time(self):
        """Test the function calculate remaining collection time from fem."""
        now_timestamp = "20240725_112646.951029"
        self.test_daq.daq.parent.fem.acquire_start_time = now_timestamp
        duration = 60
        delay = 2.0
        self.test_daq.daq.parent.fem.duration = duration
        with patch("time.time") as mock_time, patch("datetime.datetime") as mock_dt:
            mock_time.return_value = 1721903208.958006
            mock_dt.strptime.return_value.timestamp = Mock(return_value=1721903206.951029)
            time_remaining = self.test_daq.daq.calculate_remaining_collection_time()
            # Check calculated remaining collection time + delay ~= duration
            assert pytest.approx(time_remaining+delay, 0.1) == duration

    def test_processing_check_loop_polls_file_status_after_processing_complete(self):
        """Test processing check loop polls for processed file closed once processing done."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.fp_data["value"][0]["hdf"]["frames_processed"] = 10
            self.test_daq.daq.plugin = "hdf"
            self.test_daq.daq.frame_end_acquisition = 10
            self.test_daq.daq.processing_check_loop()
            mock_loop.instance().add_callback.assert_called_with(self.test_daq.daq.flush_data)
            mock_loop.instance().call_later.assert_called_with(0.1,
                                                               self.test_daq.daq.hdf_closing_loop)

    def test_processing_check_loop_handles_missing_frames(self):
        """Test processing check loop will stop acquisition if data ceases mid-flow."""
        with patch("hexitec.HexitecDAQ.IOLoop"):
            self.test_daq.daq.parent.fem.hardware_busy = True
            self.test_daq.daq.frame_end_acquisition = 10
            self.test_daq.daq.shutdown_processing = True
            self.test_daq.daq.frames_processed = 0
            self.test_daq.daq.plugin = "hdf"
            self.test_daq.daq.processing_check_loop()
            assert self.test_daq.daq.file_writing is False
            assert self.test_daq.daq.shutdown_processing is False

    def test_processing_check_loop_polling_while_data_being_processed(self):
        """Test processing check loop polls itself while data coming in."""
        with patch("hexitec.HexitecDAQ.IOLoop"):
            self.test_daq.daq.frame_end_acquisition = 10
            self.test_daq.daq.frames_processed = 5
            self.test_daq.daq.plugin = "hdf"
            self.test_daq.daq.processing_check_loop()
            assert pytest.approx(self.test_daq.daq.processing_timestamp) == time.time()

    def test_flush_data(self):
        """Test function flushes out histogram data, calls stop_acquisition."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.daq.flush_data()
            self.test_daq.fake_fp.put.assert_has_calls([
                # TODO: REPLACE ANY WITH ApiAdapterRequest
                call("config/inject_eoa", ANY)
            ])
            instance = mock_loop.instance()
            instance.call_later.assert_called_with(0.02, self.test_daq.daq.monitor_eoa_progress)

    def test_monitor_eoa_progress_handles_processed(self):
        """Test function calls stop_acquisition if eoa completed"""
        self.test_daq.daq.get_eoa_processed_status = Mock(return_value=True)
        self.test_daq.daq.stop_acquisition = Mock()
        self.test_daq.daq.monitor_eoa_progress()
        self.test_daq.daq.stop_acquisition.assert_called()

    def test_monitor_eoa_progress_handles_in_progress(self):
        """Test function calls itself if eoa not completed"""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.daq.monitor_eoa_progress()
            instance = mock_loop.instance()
            instance.call_later.assert_called_with(0.25, self.test_daq.daq.monitor_eoa_progress)

    def test_stop_acquisition_handles_file_shut(self):
        """Test function wraps up acquisition if file shut."""
        self.test_daq.daq.check_hdf_write_statuses = Mock(return_value=False)
        self.test_daq.daq.set_file_writing = Mock()
        self.test_daq.daq.hdf_retry = 3
        self.test_daq.daq.stop_acquisition()
        assert self.test_daq.daq.hdf_retry == 0
        assert self.test_daq.daq.file_writing is False
        self.test_daq.daq.set_file_writing.assert_called()

    def test_stop_acquisition_handles_file_not_shut(self):
        """Test function retries in a second if file not shut."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.daq.set_file_writing = Mock()
            self.test_daq.daq.stop_acquisition()
            # assert self.test_daq.daq.hdf_retry == 1
            self.test_daq.daq.set_file_writing.assert_not_called()
            mock_loop.instance().call_later.assert_called_with(1.0,
                                                               self.test_daq.daq.stop_acquisition)

    def test_stop_acquisition_handles_file_failed_to_shut(self):
        """Test function flags error fifth failed attempt."""
        self.test_daq.daq.set_file_writing = Mock()
        self.test_daq.daq.hdf_retry = 5
        self.test_daq.daq.stop_acquisition()
        error = "DAQ timed out, file didn't close"
        assert self.test_daq.daq.hdf_retry == 0
        assert self.test_daq.daq.parent.fem.status_error == error
        self.test_daq.daq.set_file_writing.assert_called()

    def test_save_dict_contents_to_group_works(self):
        """Test save_dict_contents_to_file function."""
        param_tree_dict = \
            {'CTProfile':
                {'@xmlns:xsi': 'none', 'ManipulatorPosition':
                 {'@Version': '2', 'AxisPosition': ['0', '-397.092']},
                    'CTAxisOffset': '0',
                    'XraySettings': {'kV': '140', 'uA': '70', 'FocusMode': 'autoDefocus'},
                    'ShadingCorrectionProfile':
                        {'IntensifierField': '0', 'GreyLevelTargets':
                            {'Target':
                                    [{'kV': '0', 'uA': '0', 'XrayFilterMaterial': None,
                                      'XrayFilterThickness': '0', 'GreyLevel': '165',
                                      'PercentageWhiteLevel': '0'}]},
                            'UsesMultipleXrayFilters': 'false', 'Mode': 'CT3D',
                            'TiltDegrees': '0'}, 'FluxNormalisationRect':
                    {'Location':
                        {'X': '10', 'Y': '10'},
                        'Size': {'Width': '100', 'Height': '100'},
                        'Height': '100'},
                    'JobGuid': '392c51f4-48c1-49ae-a1a6-2998093e7bc1'},
                'Information': {'@xmlns:xsi': 'none',
                                'JobGuid': '392c51f4-48c1-49ae-a1a6-2998093e7bc1'},
                'list_list': [["String"]],
                'log_messages': []}
        param_tree_dict = self.test_daq.daq._flatten_dict(param_tree_dict)
        import h5py
        with h5py.File("/tmp/dummy.h5", "w") as hdf_file:
            self.test_daq.daq.save_dict_contents_to_file(hdf_file, '/', param_tree_dict)

    def test_save_dict_contents_to_group_handle_mangled_format(self):
        """Test save_dict_contents_to_file handles mangled meta format."""
        key = 'list_list'
        value = [["String"]]
        param_tree_dict = {key: value}
        param_tree_dict = self.test_daq.daq._flatten_dict(param_tree_dict)
        import h5py
        with h5py.File("/tmp/dummy.h5", "w") as hdf_file:
            self.test_daq.daq.save_dict_contents_to_file(hdf_file, '/', param_tree_dict)
            error = "No conversion path for dtype: dtype('<U6')"
            message = "Parsing key: /{} value: {}: {}".format(key, value, error)
            assert self.test_daq.daq.parent.fem.status_error == message

    def test_write_metadata_works(self):
        """Test write_metadata function."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"):
            with patch("h5py._hl.group.Group") as h5_group:
                hdf_file = Mock()
                meta_group = h5_group
                meta_group.name = u'/hexitec'
                param_tree_dict = self.test_daq.daq.parent.param_tree.get('')
                self.test_daq.daq.calibration_enable = True
                # THRESHOLDOPTIONS[1] = "filename"
                self.test_daq.daq.threshold_mode = self.test_daq.daq.THRESHOLDOPTIONS[1]

                with patch("builtins.open", mock_open(read_data="data")):
                    with patch("os.path.isfile") as mock_isfile:
                        mock_isfile.return_value = True
                        rc_value = self.test_daq.daq.write_metadata(meta_group,
                                                                    param_tree_dict,
                                                                    hdf_file)

                key = 'detector/fem/hexitec_config'
                assert key in self.test_daq.daq.config_ds
                assert rc_value == 0

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_write_metadata_handles_IOError(self, mock_file):
        """Test write_metadata handles file reading error."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"):
            with patch("h5py._hl.group.Group") as h5_group:
                hdf_file = Mock()
                meta_group = h5_group
                meta_group.name = u'/hexitec'
                param_tree_dict = self.test_daq.daq.parent.param_tree.get('')

                mock_file.side_effect = IOError(Mock())

                with patch("os.path.isfile") as mock_isfile:
                    mock_isfile.return_value = True

                    rc_value = self.test_daq.daq.write_metadata(meta_group,
                                                                param_tree_dict,
                                                                hdf_file)
                assert rc_value == -1

    def test_write_metadata_handles_exception(self):
        """Test write_metadata handles general file I/O exception."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"):
            with patch("h5py._hl.group.Group") as h5_group:
                hdf_file = Mock()
                meta_group = h5_group
                meta_group.name = u'/hexitec'
                param_tree_dict = self.test_daq.daq.parent.param_tree.get('')

                with patch("builtins.open", mock_open(read_data="data")) as mock_file:
                    mock_file.side_effect = Exception(Mock())

                    with patch("os.path.isfile") as mock_isfile:
                        mock_isfile.return_value = True

                        rc_value = self.test_daq.daq.write_metadata(meta_group,
                                                                    param_tree_dict,
                                                                    hdf_file)
                assert rc_value == -2

    def test_write_metadata_handles_file_missing(self):
        """Test write_metadata handles missing file."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"):
            with patch("h5py._hl.group.Group") as h5_group:
                hdf_file = Mock()
                meta_group = h5_group
                meta_group.name = u'/hexitec'
                param_tree_dict = self.test_daq.daq.parent.param_tree.get('')

                with patch("builtins.open", mock_open(read_data="data")):
                    with patch("os.path.isfile") as mock_isfile:
                        mock_isfile.return_value = False

                        rc_value = self.test_daq.daq.write_metadata(meta_group,
                                                                    param_tree_dict,
                                                                    hdf_file)
                assert rc_value == -3

    def test_hdf_closing_loop_waits_while_file_open(self):
        """Test the function waits while file being written."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.fp_data["value"][0]["hdf"]["writing"] = True
            self.test_daq.daq.hdf_closing_loop()
            mock_loop.instance().call_later.assert_called_with(0.5,
                                                               self.test_daq.daq.hdf_closing_loop)

    def test_hdf_closing_loop_checks_files_exist_before_writing_meta(self):
        """Test the function works."""
        self.test_daq.fp_data["value"][0]["hdf"]["writing"] = False
        self.test_daq.daq.in_progress = True
        self.test_daq.daq.hdf_closing_loop()
        full_filename = self.test_daq.file_dir + self.test_daq.file_name + '.h5'
        assert self.test_daq.daq.hdf_file_location == full_filename

    def test_hdf_closing_loop_handles_file_closed_but_cannot_reopen(self):
        """Test the function handles processed file shut but cannot be reopened.

        When file writer closes file, function calls prepare_hdf_file which should flag
        if unable to reopen processed file (to add meta data).
        """
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File") as mock_h5py:
            with patch("os.path.exists") as mock_exists:
                self.test_daq.fp_data["value"][0]["hdf"]["writing"] = False
                self.test_daq.daq.in_progress = True

                mock_h5py.side_effect = IOError(Mock(status=404))
                mock_exists.return_value = "True"

                self.test_daq.adapter.hexitec.fem.status_error
                self.test_daq.daq.hdf_retry = 6
                self.test_daq.daq.hdf_closing_loop()
                error = "Error reopening HDF file:"
                assert self.test_daq.daq.hdf_retry == 0
                assert self.test_daq.daq.in_progress is False
                assert self.test_daq.adapter.hexitec.fem.status_error[:25] == error

    def test_prepare_hdf_file(self):
        """Test that function prepares processed file."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"):
            self.test_daq.daq.in_progress = True
            self.test_daq.daq.write_metadata = Mock(return_value=0)
            self.test_daq.daq.prepare_hdf_file()

            assert self.test_daq.daq.hdf_retry == 0
            assert self.test_daq.daq.in_progress is False
            assert self.test_daq.daq.parent.fem.status_message == "Meta data added to "
            assert self.test_daq.daq.parent.software_state == "Ready"

    def test_prepare_hdf_file_fails_inaccessible_config_files(self):
        """Test that function flags if a config file is inaccessible to write_metadata."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"):
            self.test_daq.daq.in_progress = True
            self.test_daq.daq.write_metadata = Mock(return_value=-1)
            self.test_daq.daq.prepare_hdf_file()

            assert self.test_daq.daq.hdf_retry == 0
            assert self.test_daq.daq.in_progress is False
            error = "Meta data writer unable to access file(s)!"
            assert self.test_daq.daq.parent.fem.status_error == error

    def test_prepare_hdf_file_fails_ioerror(self):
        """Test function handles repeated I/O error."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File") as mock_file:
            mock_file.side_effect = IOError(Mock(status=404))
            self.test_daq.daq.write_metadata = Mock()
            self.test_daq.daq.hdf_closing_loop = Mock()
            self.test_daq.daq.hdf_closing_loop.side_effect = self.test_daq.daq.prepare_hdf_file()

            self.test_daq.daq.prepare_hdf_file()
            assert self.test_daq.daq.hdf_retry == 2
            assert self.test_daq.daq.in_progress is False

    def test_flatten_dict(self):
        """Test help function."""
        test_dict = {"test": 5, "tree": {"branch_1": 1.1, "branch_2": 1.2}}
        flattened_dict = {'test': 5, 'tree/branch_1': 1.1, 'tree/branch_2': 1.2}

        d = self.test_daq.daq._flatten_dict(test_dict)
        assert d == flattened_dict

    def test_are_processes_configured_fails_unknown_adapter(self):
        """Test returns False for unknown adapter."""
        status = None
        adapter = "rubbish"
        configured = self.test_daq.daq.are_processes_configured(status, adapter)
        assert configured is False

    def test_are_processes_configured_works(self):
        """Test checking node(s) status can be resolved."""
        status = [{'shared_memory': {'configured': True},
                   'plugins': {'names': ['hdf', 'lvframes', 'lvspectra', 'reorder',
                                         'summed_image', 'threshold']},
                   'connected': True}]
        adapter = "fp"
        configured = self.test_daq.daq.are_processes_configured(status, adapter)
        assert configured is True

    def test_get_connection_status_fails_uninitialised_adapters(self):
        """Test returns Error if adapter(s) not initialised."""
        self.test_daq.daq.is_initialised = False
        return_value = self.test_daq.daq.get_connection_status("fp")
        assert return_value == [{"Error": "Adapter not initialised with references yet"}]

    def test_get_connection_status_fails_unknown_adapters(self):
        """Test unknown adapter returns Error."""
        adapter = "unknown"
        return_value = self.test_daq.daq.get_connection_status(adapter)
        assert return_value == [{"Error": "Adapter {} not found".format(adapter)}]

    def test_get_adapter_status_fails_initialised(self):
        """Test uninitialised adapter returns Error."""
        adapter = "fp"
        self.test_daq.daq.is_initialised = False
        return_value = self.test_daq.daq.get_adapter_status(adapter)
        error = [{"Error": "Adapter {} not initialised with references yet".format(adapter)}]
        assert return_value == error

    def test_set_number_frames(self):
        """Test function sets number of frames."""
        number_frames = 25
        self.test_daq.daq.set_number_frames(number_frames)
        assert number_frames == self.test_daq.daq.number_frames

    def test_set_number_nodes(self):
        """Test function sets number of nodes."""
        number_nodes = 3
        self.test_daq.daq.set_number_nodes(number_nodes)
        assert number_nodes == self.test_daq.daq.number_nodes

    def test_set_addition_enable(self):
        """Test function sets addition bool."""
        addition_enable = True
        self.test_daq.daq._set_addition_enable(addition_enable)
        assert addition_enable is self.test_daq.daq.addition_enable

        addition_enable = False
        self.test_daq.daq._set_addition_enable(addition_enable)
        assert addition_enable is self.test_daq.daq.addition_enable

    def test_set_calibration_enable(self):
        """Test function sets calibration bool."""
        calibration_enable = True
        self.test_daq.daq._set_calibration_enable(calibration_enable)
        assert calibration_enable is self.test_daq.daq.calibration_enable

        calibration_enable = False
        self.test_daq.daq._set_calibration_enable(calibration_enable)
        assert calibration_enable is self.test_daq.daq.calibration_enable

    def test_set_discrimination_enable(self):
        """Test function sets discrimination bool."""
        discrimination_enable = True
        self.test_daq.daq._set_discrimination_enable(discrimination_enable)
        assert discrimination_enable is self.test_daq.daq.discrimination_enable

        discrimination_enable = False
        self.test_daq.daq._set_discrimination_enable(discrimination_enable)
        assert discrimination_enable is self.test_daq.daq.discrimination_enable

    def test_set_lvframes_dataset_name(self):
        """Test function sets dataset name."""
        dataset_name = "raw_frames"
        self.test_daq.daq._set_lvframes_dataset_name(dataset_name)
        assert dataset_name is self.test_daq.daq.lvframes_dataset_name

        dataset_name = "processed_frames"
        self.test_daq.daq._set_lvframes_dataset_name(dataset_name)
        assert dataset_name is self.test_daq.daq.lvframes_dataset_name

    def test_set_lvframes_frequency(self):
        """Test function sets frame frequency."""
        lvframes_frequency = 67
        self.test_daq.daq._set_lvframes_frequency(lvframes_frequency)
        assert lvframes_frequency is self.test_daq.daq.lvframes_frequency

        with pytest.raises(ParameterTreeError, match="lvframes_frequency must be positive!"):
            self.test_daq.daq._set_lvframes_frequency(-1)

    def test_set_lvframes_socket_addr(self):
        """Test function sets socket address."""
        socket_addr = "tcp://10.20.30.40:5020"
        self.test_daq.daq._set_lvframes_socket_addr(socket_addr)
        assert socket_addr is self.test_daq.daq.lvframes_socket_addr

    def test_set_lvframes_per_second(self):
        """Test function sets per second."""
        lvframes_per_second = 5
        self.test_daq.daq._set_lvframes_per_second(lvframes_per_second)
        assert lvframes_per_second is self.test_daq.daq.lvframes_per_second

        with pytest.raises(ParameterTreeError, match="lvframes_per_second must be positive!"):
            self.test_daq.daq._set_lvframes_per_second(-1)

    def test_set_lvspectra_dataset_name(self):
        """Test function sets dataset name."""
        dataset_name = "summed_spectra"
        self.test_daq.daq._set_lvspectra_dataset_name(dataset_name)
        assert dataset_name is self.test_daq.daq.lvspectra_dataset_name

    def test_set_lvspectra_frequency(self):
        """Test function sets frame frequency."""
        lvspectra_frequency = 24
        self.test_daq.daq._set_lvspectra_frequency(lvspectra_frequency)
        assert lvspectra_frequency is self.test_daq.daq.lvspectra_frequency

        with pytest.raises(ParameterTreeError, match="lvspectra_frequency must be positive!"):
            self.test_daq.daq._set_lvspectra_frequency(-1)

    def test_set_lvspectra_socket_addr(self):
        """Test function sets socket address."""
        socket_addr = "tcp://50.60.70.80:5021"
        self.test_daq.daq._set_lvspectra_socket_addr(socket_addr)
        assert socket_addr is self.test_daq.daq.lvspectra_socket_addr

    def test_set_lvspectra_per_second(self):
        """Test function sets per second."""
        lvspectra_per_second = 7
        self.test_daq.daq._set_lvspectra_per_second(lvspectra_per_second)
        assert lvspectra_per_second is self.test_daq.daq.lvspectra_per_second

        with pytest.raises(ParameterTreeError, match="lvspectra_per_second must be positive!"):
            self.test_daq.daq._set_lvspectra_per_second(-1)

    def test_set_pixel_grid_size(self):
        """Test function sets pixel grid size."""
        pixel_grid_size = 3
        self.test_daq.daq._set_pixel_grid_size(pixel_grid_size)
        assert pixel_grid_size == self.test_daq.daq.pixel_grid_size

        with pytest.raises(ParameterTreeError, match="Must be either 3 or 5"):
            self.test_daq.daq._set_pixel_grid_size(4)

    def test_set_gradients_filename_correct(self):
        """Test setting gradients file."""
        gradients_filename = "m.txt"
        self.test_daq.daq._set_gradients_filename(gradients_filename)

        # Verify relative paths match:
        gradients_file = self.test_daq.daq.gradients_filename
        verified_filename = os.path.basename(gradients_file)
        assert gradients_filename == verified_filename

    def test_set_gradients_filename_handles_invalid_file(self):
        """Test setting gradients file to invalid file raises exception."""
        with pytest.raises(ParameterTreeError, match="Gradients file doesn't exist"):
            self.test_daq.daq._set_gradients_filename("rubbish_filename.txt")

    def test_set_intercepts_filename_correct(self):
        """Test setting intercepts filename."""
        intercepts_filename = "c.txt"
        self.test_daq.daq._set_intercepts_filename(intercepts_filename)
        # Verify relative paths match:
        intercepts_file = self.test_daq.daq.intercepts_filename
        verified_filename = os.path.basename(intercepts_file)
        assert intercepts_filename == verified_filename

    def test_set_intercepts_filename_handles_invalid_file(self):
        """Test setting intercepts filename to invalid file raises exception."""
        with pytest.raises(ParameterTreeError, match="Intercepts file doesn't exist"):
            self.test_daq.daq._set_intercepts_filename("rubbish_filename.txt")

    def test_set_threshold_filename_correct(self):
        """Test setting threshold file name."""
        threshold_filename = "threshold1.txt"
        self.test_daq.daq._set_threshold_filename(threshold_filename)
        # Verify relative paths match:
        threshold_file = self.test_daq.daq.threshold_filename
        verified_filename = os.path.basename(threshold_file)
        assert threshold_filename == verified_filename

    def test_set_threshold_filename_handles_invalid_file(self):
        """Test setting threshold file name to invalid file raises exception."""
        with pytest.raises(ParameterTreeError, match="Threshold file doesn't exist"):
            self.test_daq.daq._set_threshold_filename("rubbish_filename.txt")

    def test_update_datasets_frame_dimensions(self):
        """Test function updates frame_dimensions."""
        self.test_daq.daq.update_datasets_frame_dimensions()

        self.test_daq.fake_fp.put.assert_has_calls([
            call("config/hdf/dataset/processed_frames", ANY),
            call("config/hdf/dataset/raw_frames", ANY)
        ])

    def test_set_bin_end(self):
        """Test function sets bin_end."""
        bin_end = 8000
        self.test_daq.daq._set_bin_end(bin_end)
        assert bin_end == self.test_daq.daq.bin_end

        with pytest.raises(ParameterTreeError, match="bin_end must be positive!"):
            self.test_daq.daq._set_bin_end(-1)

    def test_set_bin_start(self):
        """Test function sets been_start."""
        bin_start = 0
        self.test_daq.daq._set_bin_start(bin_start)
        assert bin_start == self.test_daq.daq.bin_start

        with pytest.raises(ParameterTreeError, match="bin_start must be positive!"):
            self.test_daq.daq._set_bin_start(-1)

    def test_set_bin_width(self):
        """Test function sets bin_width."""
        bin_width = 10
        self.test_daq.daq._set_bin_width(bin_width)
        assert bin_width == self.test_daq.daq.bin_width

        with pytest.raises(ParameterTreeError, match="bin_width must be positive!"):
            self.test_daq.daq._set_bin_width(-1)

    def test_update_histogram_dimensions(self):
        """Update histograms' dimensions in the relevant datasets."""
        bin_start = 50
        self.test_daq.daq._set_bin_start(bin_start)
        bin_end = 8000
        self.test_daq.daq._set_bin_end(bin_end)
        bin_width = 10
        self.test_daq.daq._set_bin_width(bin_width)
        self.test_daq.daq.update_histogram_dimensions()

        command_spectra = "config/hdf/dataset/" + "spectra_bins"
        command_pixel = "config/hdf/dataset/" + "pixel_spectra"
        command_summed = "config/hdf/dataset/" + "summed_spectra"

        self.test_daq.fake_fp.put.assert_has_calls([
            # TODO: REPLACE ANY WITH ApiAdapterRequest
            call(command_spectra, ANY),
            call(command_pixel, ANY),
            call(command_summed, ANY)
        ])

    def test_set_max_frames_received(self):
        """Test function sets max_frames_received."""
        max_frames = 100
        self.test_daq.daq._set_max_frames_received(max_frames)
        assert max_frames == self.test_daq.daq.max_frames_received

    def test_set_pass_processed(self):
        """Test function sets pass_process bool."""
        pass_processed = 10
        self.test_daq.daq._set_pass_processed(pass_processed)
        assert pass_processed == self.test_daq.daq.pass_processed

    def test_set_pass_raw(self):
        """Test function sets pass_raw bool."""
        pass_raw = True
        self.test_daq.daq._set_pass_raw(pass_raw)
        assert pass_raw is self.test_daq.daq.pass_raw

        pass_raw = False
        self.test_daq.daq._set_pass_raw(pass_raw)
        assert pass_raw is self.test_daq.daq.pass_raw

    def test_set_threshold_mode(self):
        """Test function sets threshold mode."""
        threshold_mode = "value"
        self.test_daq.daq._set_threshold_mode(threshold_mode)
        assert threshold_mode == self.test_daq.daq.threshold_mode

        with pytest.raises(ParameterTreeError, match="Must be one of: value, filename or none"):
            self.test_daq.daq._set_threshold_mode("rubbish_filename.txt")

    def test_set_threshold_value(self):
        """Test function sets threshold value."""
        threshold_value = 101
        self.test_daq.daq._set_threshold_value(threshold_value)
        assert self.test_daq.daq.threshold_value == threshold_value

        with pytest.raises(ParameterTreeError, match="threshold_value must be positive!"):
            self.test_daq.daq._set_threshold_value(-1)

    def test_set_threshold_upper(self):
        """Test function sets Summed Image's threshold upper."""
        threshold_upper = 80
        self.test_daq.daq._set_threshold_upper(threshold_upper)
        assert self.test_daq.daq.threshold_upper == threshold_upper

        with pytest.raises(ParameterTreeError, match="threshold_upper must be positive!"):
            self.test_daq.daq._set_threshold_upper(-1)

    def test_set_threshold_lower(self):
        """Test function sets Summed Image's threshold lower."""
        threshold_lower = 4800
        self.test_daq.daq._set_threshold_lower(threshold_lower)
        assert self.test_daq.daq.threshold_lower == threshold_lower

        with pytest.raises(ParameterTreeError, match="threshold_lower must be positive!"):
            self.test_daq.daq._set_threshold_lower(-1)

    def test_set_image_frequency(self):
        """Test function sets Summed Image's image frequency."""
        image_frequency = 5
        self.test_daq.daq._set_image_frequency(image_frequency)
        assert self.test_daq.daq.image_frequency == image_frequency

        with pytest.raises(ParameterTreeError, match="image_frequency must be positive!"):
            self.test_daq.daq._set_image_frequency(-1)

    def test_access_sensors_layout(self):
        """Test function sets sensors_layout."""
        sensors_layout = "2x6"
        self.test_daq.daq._set_sensors_layout(sensors_layout)
        assert self.test_daq.daq._get_sensors_layout() == sensors_layout

    def test_get_compression_type(self):
        """Test function gets compression type."""
        compression_type = "blosc"
        self.test_daq.daq._set_compression_type(compression_type)
        assert self.test_daq.daq._get_compression_type() == compression_type

    def test_set_compression_type(self):
        """Test function sets compression type."""
        COMPRESSIONOPTIONS = self.test_daq.daq.COMPRESSIONOPTIONS
        error = "Invalid compression type; Valid options: {}".format(COMPRESSIONOPTIONS)
        with pytest.raises(ParameterTreeError) as exc_info:
            self.test_daq.daq._set_compression_type("bad_compressor")
        assert exc_info.type is ParameterTreeError
        assert exc_info.value.args[0] == error

    def test_commit_configuration(self):
        """Test function handles committing configuration ok."""
        config_dict = \
            {'diagnostics': {'daq_start_time': 0, 'daq_stop_time': 0, 'fem_not_busy': 0},
             'receiver':
                {'connected': True, 'configured': True, 'config_file': 'fr_hexitec_config.json'},
             'processor':
                {'connected': True, 'configured': False, 'config_file': 'file.json'},
             'file_info':
                {'enabled': False, 'file_name': 'default_file', 'file_dir': '/tmp/'},
             'status': {'in_progress': False, 'daq_ready': False},
             'config':
                {'addition':
                    {'enable': False, 'pixel_grid_size': 3},
                 'calibration':
                    {'enable': False, 'gradients_filename': '', 'intercepts_filename': ''},
                 'discrimination':
                    {'enable': False, 'pixel_grid_size': 3},
                 'histogram':
                    {'bin_end': 800, 'bin_start': 0, 'bin_width': 10.0, 'max_frames_received': 10,
                     'pass_processed': False, 'pass_raw': True},
                 'lvframes':
                    {'dataset_name': 'raw_frames', 'frame_frequency': 0,
                     'live_view_socket_addr': 'tcp://127.0.0.1:5020', 'per_second': 2},
                 'lvspectra':
                    {'dataset_name': 'summed_spectra', 'frame_frequency': 0,
                     'live_view_socket_addr': 'tcp://127.0.0.1:5021', 'per_second': 1},
                 'threshold':
                    {'threshold_filename': '', 'threshold_mode': 'value', 'threshold_value': 10},
                 'summed_image':
                    {'threshold_lower': 120, 'threshold_upper': 4800}},
                 'sensors_layout': '2x6'}

        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            self.test_daq.daq.param_tree.get = Mock(return_value=config_dict)
            self.test_daq.daq.pass_raw = True
            self.test_daq.daq.pass_processed = True

            self.test_daq.daq.commit_configuration()

            # self.test_daq.fake_fp.put.assert_has_calls([
            #     # TODO: REPLACE ANY WITH ApiAdapterRequest
            #     call("config/config_file/", ANY),
            #     call("config/config_file/", ANY)
            # ])

            instance = mock_loop.instance()
            instance.call_later.assert_called_with(.4, self.test_daq.daq.submit_configuration)

    def test_submit_configuration_hdf_branch(self):
        """Test function handles sample parameter tree ok."""
        # TODO: Unable to return unique values for each call to
        # ...parameter_tree.tree['config'].get()
        # config_dict = \
        #     {
        #         'addition': {'enable': False, 'pixel_grid_size': 3},
        #         'calibration': {'enable': False, 'gradients_filename': '',
        #                         'intercepts_filename': ''},
        #         'discrimination': {'enable': False, 'pixel_grid_size': 3},
        #         'histogram': {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10.0,
        #                       'max_frames_received': 10,
        #                       'pass_processed': False, 'pass_raw': True},
        #         'threshold': {'threshold_filename': '', 'threshold_mode': 'value',
        #                       'threshold_value': 100}
        #     }

        # Mock using single entry parameter tree (i.e. dictionary)
        config_dict = \
            {'addition': {'enable': False}}

        with patch("hexitec.HexitecDAQ.IOLoop"):
            self.test_daq.daq.param_tree.tree.get = Mock(return_value=config_dict)

            self.test_daq.daq.param_tree.tree['config'].get = Mock(return_value={"enable": False})

            self.test_daq.daq.pass_raw = True
            self.test_daq.daq.pass_processed = True

            self.test_daq.daq.submit_configuration()

            self.test_daq.fake_fp.put.assert_has_calls([
                # TODO: REPLACE ANY WITH ApiAdapterRequest
                call("config/addition/enable", ANY)
            ])

    def test_submit_configuration_histogram_branch(self):
        """Test function handles sample parameter tree ok."""
        config_dict = {'discrimination': {'pixel_grid_size': 5}}

        with patch("hexitec.HexitecDAQ.IOLoop"):
            self.test_daq.daq.param_tree.tree.get = Mock(return_value=config_dict)
            self.test_daq.daq.param_tree.tree['config'].get = \
                Mock(return_value={"pixel_grid_size": 5})

            self.test_daq.daq.pass_raw = False
            self.test_daq.daq.pass_processed = False

            self.test_daq.daq.submit_configuration()

            self.test_daq.fake_fp.put.assert_has_calls([
                # TODO: REPLACE ANY WITH ApiAdapterRequest
                call("config/discrimination/pixel_grid_size", ANY)
            ])
