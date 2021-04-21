"""Test Cases for the Hexitec DAQ in hexitec.HexitecDAQ.

Christian Angelsen, STFC Detector Systems Software Group
"""

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
        self.file_dir = "/fake/directory/"
        self.file_name = "fake_file.txt"

        with patch("hexitec.HexitecDAQ.ParameterTree"):
            self.adapter = HexitecAdapter(**self.options)
            self.detector = self.adapter.hexitec  # shortcut, makes assert lines shorter

            self.daq = HexitecDAQ(self.detector, self.file_dir, self.file_name)

        self.fake_fr = MagicMock()
        self.fake_fp = MagicMock()
        self.fake_fi = MagicMock()

        # once the odin_data adapter is refactored to use param tree, this structure will need fixing
        self.fr_data = {
            "value": [
                {
                    "connected": True,
                    "status": {
                        "configuration_complete": True
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
                            "REORDER?",
                            "view"
                        ]

                    },
                    "hdf": {
                        "frames_written": 0,
                        "frames_processed": 0,
                        "writing": True
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

        # set up fake adapter
        fr_return = Mock()
        fr_return.configure_mock(data=self.fr_data)
        self.fake_fr.get = Mock(return_value=fr_return)
        fp_return = Mock()
        fp_return.configure_mock(data=self.fp_data)
        self.fake_fp.get = Mock(return_value=fp_return)

        fi_return = Mock()
        fi_return.configure_mock(data=self.fi_data)
        self.fake_fi.get = Mock(return_value=fi_return)

        self.adapters = {
            "fp": self.fake_fp,
            "fr": self.fake_fr,
            "file_interface": self.fake_fi
        }

        # Construct paths relative to current working directory
        cwd = os.getcwd()
        base_path_index = cwd.find("hexitec-detector")
        base_path = cwd[:base_path_index]
        self.odin_control_path = base_path + "hexitec-detector/control/"
        self.odin_data_path = base_path + "hexitec-detector/data/"

        gradients_filename = self.odin_data_path + "config/m_2018_01_001_400V_20C.txt"
        intercepts_filename = self.odin_data_path + "config/c_2018_01_001_400V_20C.txt"

        # Fake parameter tree
        self.parameter_dict = \
            {'odin_version': '0.3.1+102.g01c51d7', 'tornado_version': '4.5.3',
             'server_uptime': 48.4, 'detector':
             {'fems':
              {'fem_0':
               {'diagnostics':
                {'successful_reads': 116, 'acquire_start_time': '', 'acquire_stop_time': '',
                 'acquire_time': 1.303241}, 'id': 0, 'debug': False, 'frame_rate': 7154.0,
                'health': True, 'status_message': '', 'status_error': '',
                'initialise_progress': 0,
                'operation_percentage_complete': 100, 'number_frames': 10, 'duration': 1,
                'hexitec_config': '~/path/to/config_file',
                'read_sensors': None, 'hardware_connected': True, 'hardware_busy': False,
                'firmware_date': 'N/A', 'firmware_time': 'N/A',
                'vsr1_sensors':
                {'ambient': 0, 'humidity': 0, 'asic1': 0, 'asic2': 0, 'adc': 0, 'hv': 0},
                'vsr2_sensors':
                {'ambient': 0, 'humidity': 0, 'asic1': 0, 'asic2': 0, 'adc': 0, 'hv': 0}}},
              'daq':
              {'diagnostics':
               {'daq_start_time': '', 'daq_stop_time': '', 'fem_not_busy': ''},
               'receiver': {'connected': True, 'configured': True, 'config_file': 'fr_hexitec_config.json'},
               'processor': {'connected': True, 'configured': True, 'config_file': 'file.json'},
               'file_info': {'enabled': False, 'file_name': 'filename', 'file_dir': '/tmp/'},
               'in_progress': True,
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
                'next_frame': {'enable': False},
                'threshold':
                {'threshold_filename': '', 'threshold_mode': 'value', 'threshold_value': 120}},
               'sensors_layout': '2x2'},
              'connect_hardware': None, 'initialise_hardware': None, 'disconnect_hardware': None,
              'collect_offsets': None, 'commit_configuration': None, 'debug_count': 0,
              'acquisition':
              {'number_frames': 10, 'duration': 1, 'duration_enable': False, 'start_acq': None,
               'stop_acq': None, 'in_progress': False},
              'status':
              {'fem_id': 0, 'system_health': True, 'status_message': '', 'status_error': ''}}}

        self.daq.initialize(self.adapters)


class TestDAQ(unittest.TestCase):
    """Unit tests for DAQ class."""

    def setUp(self):
        """Set up test fixture for each unit test."""
        self.test_daq = DAQTestFixture()

    def test_init(self):
        """Test initialisation (part 1)."""
        with patch("hexitec.HexitecDAQ.ParameterTree"):
            daq = HexitecDAQ(parent=None, save_file_dir="/fake/directory/",
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
        assert self.test_daq.daq.config_files['fr'] == "hexitec_fr.config"
        assert self.test_daq.daq.config_dir == self.test_daq.fi_data["config_dir"]
        assert self.test_daq.daq.is_initialised is True

    def test_get_od_status_fr(self):
        """Test status of fr adapter."""
        status = self.test_daq.daq.get_od_status("fr")
        assert status == self.test_daq.fr_data['value'][0]

    def test_get_od_status_fp(self):
        """Test status of fp adapter."""
        status = self.test_daq.daq.get_od_status("fp")
        assert status == self.test_daq.fp_data['value'][0]

    def test_get_od_status_incorrect(self):
        """Test odin status of 'wrong' adapter."""
        status = self.test_daq.daq.get_od_status("fake")
        assert status == {"Error": "Adapter fake not found"}

    def test_get_od_status_not_init(self):
        """Test status before adapter initialised."""
        with patch("hexitec.HexitecDAQ.ParameterTree"):
            daq = HexitecDAQ(self.test_daq.file_dir, self.test_daq.file_name)
        status = daq.get_od_status("fp")
        assert status == {"Error": "Adapter not initialised with references yet"}

    def test_get_od_status_no_dict(self):
        """Test status before adapter loaded."""
        new_fr_data = {}

        with patch.dict(self.test_daq.fr_data, new_fr_data, clear=True):

            status = self.test_daq.daq.get_od_status("fr")
            assert status == {"Error": "Adapter fr not found"}

    def test_is_fr_connected_with_status(self):
        """Test function works."""
        connected = self.test_daq.daq._is_od_connected(self.test_daq.fr_data['value'][0])
        assert connected

    def test_is_fp_connected_with_status(self):
        """Test function works."""
        connected = self.test_daq.daq._is_od_connected(self.test_daq.fp_data['value'][0])
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
        configured = self.test_daq.daq._is_fr_configured(self.test_daq.fr_data['value'][0])
        assert configured

    def test_is_fp_configured_with_status(self):
        """Test function works."""
        configured = self.test_daq.daq._is_fp_configured(self.test_daq.fp_data['value'][0])
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
        assert fp_file == "hexitec_fp.config"

    def test_get_config_file_not_found(self):
        """Test function works."""
        new_dict = {
            "config_dir": "fake/config_dir",
            "fr_config_files": [
                "first.config",
                "not.config"
            ],
            "fp_config_files": [
                "not.config",
                "hexitec_fp.config"
            ]
        }
        with patch.dict(self.test_daq.fi_data, new_dict, clear=True):
            fr_file = self.test_daq.daq.get_config_file("fr")

        assert fr_file == "first.config"

    def test_get_config_bad_key(self):
        """Test get on non-existent key."""
        value = self.test_daq.daq.get_config_file("bad_key")
        assert value == ""

    def test_get_config_pre_init(self):
        """Test function works."""
        with patch("hexitec.HexitecDAQ.ParameterTree"):
            daq = HexitecDAQ(self.test_daq.file_dir, self.test_daq.file_name)
        value = daq.get_config_file("fr")
        assert value == ""

    def test_set_data_dir(self):
        """Test set data directory."""
        self.test_daq.daq.set_data_dir("new/fake/dir/")
        assert self.test_daq.daq.file_dir == "new/fake/dir/"

    def test_set_file_name(self):
        """Test that file name."""
        self.test_daq.daq.set_file_name("new_file_name.hdf")
        assert self.test_daq.daq.file_name == "new_file_name.hdf"

    def test_set_writing(self):
        """Test set file writing."""
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

    def test_config_odin_data(self):
        """Test configure Odin data works."""
        with patch("hexitec.HexitecDAQ.ApiAdapterRequest") as mock_request:
            self.test_daq.daq.config_dir = "fake/dir"
            self.test_daq.daq.config_files["fp"] = "fp_hexitec.config"

            self.test_daq.daq._config_odin_data("fp")
            config = "/{}/{}".format(self.test_daq.daq.config_dir, self.test_daq.daq.config_files["fp"])

            mock_request.assert_called_with(config, content_type="application/json")
            self.test_daq.fake_fp.put.assert_called_with("config/config_file", mock_request())

    def test_start_acquisition(self):
        """Test function works."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            self.test_daq.fp_data["value"][0]["hdf"]["frames_processed"] = 0
            self.test_daq.daq.first_initialisation = False
            self.test_daq.daq.start_acquisition(10)

            assert self.test_daq.daq.frame_start_acquisition == 0
            assert self.test_daq.daq.frame_end_acquisition == 10
            assert self.test_daq.daq.in_progress is True
            assert self.test_daq.daq.file_writing is True

            mock_loop.instance().call_later.assert_called_with(1.3,
                                                               self.test_daq.daq.acquisition_check_loop)

    def test_start_acquisition_needs_configure(self):
        """Test function works."""
        new_fp_data = {
            "value": [{
                "connected": True
            }]
        }
        config = {"configuration_complete": False}
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop, \
            patch("hexitec.HexitecDAQ.ApiAdapterRequest") as mock_request, \
                patch.dict(self.test_daq.fr_data['value'][0]['status'], config, clear=True), \
                patch.dict(self.test_daq.fp_data, new_fp_data, clear=True):

            self.test_daq.daq.first_initialisation = False
            self.test_daq.daq.start_acquisition(10)

            self.test_daq.fake_fp.put.assert_any_call("config/config_file", mock_request())
            self.test_daq.fake_fr.put.assert_called_with("config/config_file", mock_request())

            assert self.test_daq.daq.frame_start_acquisition == 0
            assert self.test_daq.daq.frame_end_acquisition == 10
            assert self.test_daq.daq.in_progress is True
            assert self.test_daq.daq.file_writing is True

            mock_loop.instance().call_later.assert_called_with(1.3,
                                                               self.test_daq.daq.acquisition_check_loop)

    def test_start_acquisition_fr_disconnected(self):
        """Test acquisition won't start with fr disconnected."""
        new_fr_data = {
            "not_value": False
        }

        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop, \
            patch("hexitec.HexitecDAQ.ApiAdapterRequest"), \
                patch.dict(self.test_daq.fr_data, new_fr_data, clear=True):

            self.test_daq.daq.start_acquisition(10)

            assert self.test_daq.daq.file_writing is False
            assert self.test_daq.daq.in_progress is False

            mock_loop.instance().add_callback.assert_not_called()

    def test_start_acquisition_fp_disconnected(self):
        """Test acquisition won't start with fp disconnected."""
        new_fp_data = {
            "not_value": False
        }

        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop, \
            patch("hexitec.HexitecDAQ.ApiAdapterRequest"), \
                patch.dict(self.test_daq.fp_data, new_fp_data, clear=True):

            self.test_daq.daq.start_acquisition(10)

            assert self.test_daq.daq.file_writing is False
            assert self.test_daq.daq.in_progress is False

            mock_loop.instance().add_callback.assert_not_called()

    def test_acquisition_check_loop(self):
        """Test that function calls itself if hardware busy."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            self.test_daq.adapter.hexitec.fems[0].hardware_busy = True

            self.test_daq.daq.acquisition_check_loop()
            mock_loop.instance().call_later.assert_called_with(.5,
                                                               self.test_daq.daq.acquisition_check_loop)

    def test_processing_check_loop_handles_initial_acquisition(self):
        """Test processing check loop exits initial acquisition without reopening file.

        Any subsequent acquisition should add meta data but not the initial (fudge) one.
        """
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.daq.first_initialisation = True
            self.test_daq.daq.processing_check_loop()
            mock_loop.instance().call_later.assert_called_with(2.0,
                                                               self.test_daq.daq.stop_acquisition)

    def test_acquisition_check_loop_polls_processing_once_acquisition_complete(self):
        """Test acquisition check loop polls processing status once fem(s) finished sending data."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.daq.frame_end_acquisition = 10
            self.test_daq.daq.acquisition_check_loop()
            self.test_daq.daq.first_initialisation = False
            mock_loop.instance().call_later.assert_called_with(.5,
                                                               self.test_daq.daq.processing_check_loop)

    def test_processing_check_loop_polls_file_status_after_processing_complete(self):
        """Test processing check loop polls for processed file closed once processing done."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.daq.first_initialisation = False
            self.test_daq.fp_data["value"][0]["hdf"]["frames_processed"] = 10
            self.test_daq.daq.plugin = "hdf"
            self.test_daq.daq.frame_end_acquisition = 10
            self.test_daq.daq.processing_check_loop()
            mock_loop.instance().call_later.assert_called_with(1.0,
                                                               self.test_daq.daq.hdf_closing_loop)

    def test_processing_check_loop_handles_missing_frames(self):
        """Test processing check loop will stop acquisition if data ceases mid-flow."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
            self.test_daq.daq.first_initialisation = False
            self.test_daq.daq.parent.fems[0].hardware_busy = True
            self.test_daq.daq.frame_end_acquisition = 10
            self.test_daq.daq.shutdown_processing = True
            self.test_daq.daq.processing_check_loop()
            mock_loop.instance().add_callback.assert_called_with(self.test_daq.daq.stop_acquisition)

    def test_processing_check_loop_polling_while_data_being_processed(self):
        """Test processing check loop polls itself while data coming in."""
        with patch("hexitec.HexitecDAQ.IOLoop"):
            self.test_daq.daq.first_initialisation = False
            self.test_daq.daq.frame_end_acquisition = 10
            self.test_daq.daq.frames_processed = 5
            self.test_daq.daq.processing_check_loop()
            assert pytest.approx(self.test_daq.daq.processed_timestamp) == time.time()

    def test_stop_acquisition(self):
        """Test function stops acquisition."""
        assert self.test_daq.daq.file_writing is False

        self.test_daq.daq.file_writing = True
        assert self.test_daq.daq.file_writing is True

        self.test_daq.daq.stop_acquisition()
        assert self.test_daq.daq.file_writing is False

    def test_write_metadata_works(self):
        """Test write_metadata function."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"), patch("h5py._hl.group.Group") as h5_group:
            meta_group = h5_group
            meta_group.name = u'/hexitec'
            param_tree_dict = self.test_daq.daq.parent.param_tree.get('')
            self.test_daq.daq.calibration_enable = True
            self.test_daq.daq.threshold_mode = self.test_daq.daq.THRESHOLDOPTIONS[1]  # = "filename"

            with patch("builtins.open", mock_open(read_data="data")):
                with patch("os.path.isfile") as mock_isfile:
                    mock_isfile.return_value = True
                    rc_value = self.test_daq.daq.write_metadata(meta_group, param_tree_dict)

            key = 'detector/fems/fem_0/hexitec_config'
            assert key in self.test_daq.daq.config_ds
            assert rc_value == 0

    def test_write_metadata_handles_IOError(self):
        """Test write_metadata handles file reading error."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"), patch("h5py._hl.group.Group") as h5_group:
            meta_group = h5_group
            meta_group.name = u'/hexitec'
            param_tree_dict = self.test_daq.daq.parent.param_tree.get('')

            with patch("builtins.open", mock_open(read_data="data")) as mock_file:
                mock_file.side_effect = IOError(Mock())

                with patch("os.path.isfile") as mock_isfile:
                    mock_isfile.return_value = True

                    rc_value = self.test_daq.daq.write_metadata(meta_group, param_tree_dict)
            assert rc_value == -1

    def test_write_metadata_handles_exception(self):
        """Test write_metadata handles general file I/O exception."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"), patch("h5py._hl.group.Group") as h5_group:
            meta_group = h5_group
            meta_group.name = u'/hexitec'
            param_tree_dict = self.test_daq.daq.parent.param_tree.get('')

            with patch("builtins.open", mock_open(read_data="data")) as mock_file:
                mock_file.side_effect = Exception(Mock())

                with patch("os.path.isfile") as mock_isfile:
                    mock_isfile.return_value = True

                    rc_value = self.test_daq.daq.write_metadata(meta_group, param_tree_dict)
            assert rc_value == -2

    def test_write_metadata_handles_file_missing(self):
        """Test write_metadata handles missing file."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"), patch("h5py._hl.group.Group") as h5_group:
            meta_group = h5_group
            meta_group.name = u'/hexitec'
            param_tree_dict = self.test_daq.daq.parent.param_tree.get('')

            with patch("builtins.open", mock_open(read_data="data")):
                with patch("os.path.isfile") as mock_isfile:
                    mock_isfile.return_value = False

                    rc_value = self.test_daq.daq.write_metadata(meta_group, param_tree_dict)
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
        assert self.test_daq.daq.in_progress is False

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

                self.test_daq.adapter.hexitec.fems[0].status_error
                self.test_daq.daq.hdf_retry = 6
                self.test_daq.daq.hdf_closing_loop()
                error = "Error reopening HDF file:"
                assert self.test_daq.daq.in_progress is False
                assert self.test_daq.adapter.hexitec.fems[0].status_error[:25] == error

    def test_prepare_hdf_file(self):
        """Test that function prepares processed file."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"):
            self.test_daq.daq.in_progress = True
            self.test_daq.daq.write_metadata = Mock(return_value=0)
            self.test_daq.daq.prepare_hdf_file()

            assert self.test_daq.daq.hdf_retry == 0
            assert self.test_daq.daq.in_progress is False
            assert self.test_daq.daq.parent.fems[0].status_message == "Meta data added"

    def test_prepare_hdf_file_fails_inaccessible_config_files(self):
        """Test that function flags if a config file is inaccessible to write_metadata."""
        with patch("hexitec.HexitecDAQ.IOLoop"), patch("h5py.File"):
            self.test_daq.daq.in_progress = True
            self.test_daq.daq.write_metadata = Mock(return_value=-1)
            self.test_daq.daq.prepare_hdf_file()

            assert self.test_daq.daq.hdf_retry == 0
            assert self.test_daq.daq.in_progress is False
            error = "Meta data writer unable to access file(s)!"
            assert self.test_daq.daq.parent.fems[0].status_error == error

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

    def test_set_number_frames(self):
        """Test function sets number of frames."""
        number_frames = 25
        self.test_daq.daq.set_number_frames(number_frames)
        assert number_frames == self.test_daq.daq.number_frames

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

    def test_set_next_frame_enable(self):
        """Test function sets next frame bool."""
        next_frame_enable = True
        self.test_daq.daq._set_next_frame_enable(next_frame_enable)
        assert next_frame_enable is self.test_daq.daq.next_frame_enable

        next_frame_enable = False
        self.test_daq.daq._set_next_frame_enable(next_frame_enable)
        assert next_frame_enable is self.test_daq.daq.next_frame_enable

    def test_set_pixel_grid_size(self):
        """Test function sets pixel grid size."""
        pixel_grid_size = 3
        self.test_daq.daq._set_pixel_grid_size(pixel_grid_size)
        assert pixel_grid_size == self.test_daq.daq.pixel_grid_size

        with pytest.raises(ParameterTreeError, match="Must be either 3 or 5"):
            self.test_daq.daq._set_pixel_grid_size(4)

    def test_set_gradients_filename_correct(self):
        """Test setting gradients file."""
        gradients_filename = "data/config/m_2018_01_001_400V_20C.txt"
        self.test_daq.daq._set_gradients_filename(gradients_filename)

        # Verify relative paths match:
        gradients_file = self.test_daq.daq.gradients_filename
        index = gradients_file.find("data")
        verified_filename = gradients_file[index:]
        assert gradients_filename == verified_filename

    def test_set_gradients_filename_handles_invalid_file(self):
        """Test setting gradients file to invalid file raises exception."""
        with pytest.raises(ParameterTreeError, match="Gradients file doesn't exist"):
            self.test_daq.daq._set_gradients_filename("rubbish_filename.txt")

    def test_set_intercepts_filename_correct(self):
        """Test setting intercepts filename."""
        intercepts_filename = "data/config/c_2018_01_001_400V_20C.txt"
        self.test_daq.daq._set_intercepts_filename(intercepts_filename)
        # Verify relative paths match:
        intercepts_file = self.test_daq.daq.intercepts_filename
        index = intercepts_file.find("data")
        verified_filename = intercepts_file[index:]
        assert intercepts_filename == verified_filename

    def test_set_intercepts_filename_handles_invalid_file(self):
        """Test setting intercepts filename to invalid file raises exception."""
        with pytest.raises(ParameterTreeError, match="Intercepts file doesn't exist"):
            self.test_daq.daq._set_intercepts_filename("rubbish_filename.txt")

    def test_set_threshold_filename_correct(self):
        """Test setting threshold file name."""
        threshold_filename = "data/config/thresh_2018_01_001_400V_20C.txt"
        self.test_daq.daq._set_threshold_filename(threshold_filename)
        # Verify relative paths match:
        threshold_file = self.test_daq.daq.threshold_filename
        index = threshold_file.find("data")
        verified_filename = threshold_file[index:]
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

    def test_set_bin_start(self):
        """Test function sets been_start."""
        bin_start = 0
        self.test_daq.daq._set_bin_start(bin_start)
        assert bin_start == self.test_daq.daq.bin_start

    def test_set_bin_width(self):
        """Test function sets bin_width."""
        bin_width = 10
        self.test_daq.daq._set_bin_width(bin_width)
        assert bin_width == self.test_daq.daq.bin_width

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

    def test_access_sensors_layout(self):
        """Test function sets sensors_layout."""
        sensors_layout = "2x2"
        self.test_daq.daq._set_sensors_layout(sensors_layout)
        assert self.test_daq.daq._get_sensors_layout() == sensors_layout

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
             'in_progress': False,
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
                 'next_frame': {'enable': False},
                 'threshold':
                    {'threshold_filename': '', 'threshold_mode': 'value', 'threshold_value': 10}},
                 'sensors_layout': '2x2'}

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

            mock_loop.instance().call_later.assert_called_with(.4, self.test_daq.daq.submit_configuration)

    def test_submit_configuration_hdf_branch(self):
        """Test function handles sample parameter tree ok."""
        # TODO: Unable to return unique values for each call to
        # ...parameter_tree.tree['config'].get()
        # config_dict = \
        #     {
        #         'addition': {'enable': False, 'pixel_grid_size': 3},
        #         'calibration': {'enable': False, 'gradients_filename': '', 'intercepts_filename': ''},
        #         'discrimination': {'enable': False, 'pixel_grid_size': 3},
        #         'histogram': {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10.0, 'max_frames_received': 10,
        #                       'pass_processed': False, 'pass_raw': True},
        #         'next_frame': {'enable': False},
        #         'threshold': {'threshold_filename': '', 'threshold_mode': 'value', 'threshold_value': 100}
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
            self.test_daq.daq.param_tree.tree['config'].get = Mock(return_value={"pixel_grid_size": 5})

            self.test_daq.daq.pass_raw = False
            self.test_daq.daq.pass_processed = False

            self.test_daq.daq.submit_configuration()

            self.test_daq.fake_fp.put.assert_has_calls([
                # TODO: REPLACE ANY WITH ApiAdapterRequest
                call("config/discrimination/pixel_grid_size", ANY)
            ])

# GFC will turn parameter tree into:
#   OrderedDict([('threshold', {'threshold_value': 99,
# 'threshold_filename': '', 'threshold_mode': 'none'}), ('next_frame', {'enable': True}),
# ('calibration', {'enable': False, 'intercepts_filename': '', 'gradients_filename': ''}),
# ('addition', {'enable': False, 'pixel_grid_size': 3}), ('discrimination', {'enable': False,
# 'pixel_grid_size': 5}), ('histogram', {'max_frames_received': 10, 'bin_end': 8000,
# 'bin_width': 10.0, 'bin_start': 0})]) <class 'collections.OrderedDict'>
