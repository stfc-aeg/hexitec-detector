"""
Test Cases for the Hexitec DAQ in hexitec.HexitecDAQ
Christian Angelsen, STFC Detector Systems Software Group
"""

import sys
import pytest
import time
import os.path
import h5py

from odin.adapters.adapter import ApiAdapterRequest
from odin.adapters.parameter_tree import ParameterTreeError

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, call, patch, ANY
else:                         # pragma: no cover
    from mock import Mock, MagicMock, call, patch, ANY

from hexitec.HexitecDAQ import HexitecDAQ
from hexitec.adapter import HexitecAdapter, Hexitec


class DAQTestFixture(object):

    def __init__(self):

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
        self.file_dir = "/fake/directory"
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
                    },
                    "reorder": {
                        "raw_data": False
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

        self.daq.initialize(self.adapters)


@pytest.fixture
def test_daq():
    """Test Fixture for testing the DAQ"""

    test_daq = DAQTestFixture()
    yield test_daq


class TestDAQ():

    def test_init(self, test_daq):
        with patch("hexitec.HexitecDAQ.ParameterTree"):
            daq = HexitecDAQ(parent=None, save_file_dir="/fake/directory", 
                                            save_file_name="fake_file.txt")
        assert daq.file_dir == test_daq.file_dir
        assert daq.file_name == test_daq.file_name
        assert daq.in_progress is False
        assert daq.is_initialised is False

    def test_initialize(self, test_daq):
        test_daq.daq.adapters = {}
        test_daq.daq.initialize(test_daq.adapters)

        assert test_daq.daq.adapters == test_daq.adapters
        test_daq.fake_fi.get.assert_called()
        assert test_daq.daq.config_files['fr'] == "hexitec_fr.config"
        assert test_daq.daq.config_dir == test_daq.fi_data["config_dir"]
        assert test_daq.daq.is_initialised is True

    def test_get_od_status_fr(self, test_daq):

        status = test_daq.daq.get_od_status("fr")
        assert status == test_daq.fr_data['value'][0]

    def test_get_od_status_fp(self, test_daq):

        status = test_daq.daq.get_od_status("fp")
        assert status == test_daq.fp_data['value'][0]

    def test_get_od_status_incorrect(self, test_daq):

        status = test_daq.daq.get_od_status("fake")
        assert status == {"Error": "Adapter fake not found"}

    def test_get_od_status_not_init(self, test_daq):

        with patch("hexitec.HexitecDAQ.ParameterTree"):
            daq = HexitecDAQ(test_daq.file_dir, test_daq.file_name)
        status = daq.get_od_status("fp")
        assert status == {"Error": "Adapter not initialised with references yet"}

    def test_get_od_status_no_dict(self, test_daq):
        new_fr_data = {}

        with patch.dict(test_daq.fr_data, new_fr_data, clear=True):

            status = test_daq.daq.get_od_status("fr")
            assert status == {"Error": "Adapter fr not found"}

    def test_is_fr_connected_with_status(self, test_daq):

        connected = test_daq.daq._is_od_connected(test_daq.fr_data['value'][0])
        assert connected

    def test_is_fp_connected_with_status(self, test_daq):

        connected = test_daq.daq._is_od_connected(test_daq.fp_data['value'][0])
        assert connected

    def test_is_fr_connected_without_status(self, test_daq):

        connected = test_daq.daq._is_od_connected(adapter="fr")
        assert connected

    def test_is_fp_connected_without_status(self, test_daq):

        connected = test_daq.daq._is_od_connected(adapter="fp")
        assert connected

    def test_is_fr_configured_with_status(self, test_daq):

        configured = test_daq.daq._is_fr_configured(test_daq.fr_data['value'][0])
        assert configured

    def test_is_fp_configured_with_status(self, test_daq):

        configured = test_daq.daq._is_fp_configured(test_daq.fp_data['value'][0])
        assert configured

    def test_is_fr_configured_without_status(self, test_daq):

        configured = test_daq.daq._is_fr_configured()
        assert configured

    def test_is_fp_configured_without_status(self, test_daq):

        configured = test_daq.daq._is_fp_configured()
        assert configured

    def test_get_config(self, test_daq):

        fp_file = test_daq.daq.get_config_file("fp")
        assert fp_file == "hexitec_fp.config"

    def test_get_config_file_not_found(self, test_daq):
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
        with patch.dict(test_daq.fi_data, new_dict, clear=True):
            fr_file = test_daq.daq.get_config_file("fr")

        assert fr_file == "first.config"

    def test_get_config_bad_key(self, test_daq):

        value = test_daq.daq.get_config_file("bad_key")
        assert value == ""

    def test_get_config_pre_init(self, test_daq):

        with patch("hexitec.HexitecDAQ.ParameterTree"):
            daq = HexitecDAQ(test_daq.file_dir, test_daq.file_name)
        value = daq.get_config_file("fr")
        assert value == ""

    def test_set_data_dir(self, test_daq):

        test_daq.daq.set_data_dir("new/fake/dir/")
        assert test_daq.daq.file_dir == "new/fake/dir/"

    def test_set_file_name(self, test_daq):

        test_daq.daq.set_file_name("new_file_name.hdf")
        assert test_daq.daq.file_name == "new_file_name.hdf"

    def test_set_writing(self, test_daq):

        test_daq.daq.set_file_writing(True)

        test_daq.fake_fp.put.assert_has_calls([
            # TODO: REPLACE ANY WITH ApiAdapterRequest
            call("config/hdf/frames", ANY),
            call("config/hdf/file/path", ANY),
            call("config/hdf/file/name", ANY),
            call("config/hdf/write", ANY),
            call("config/histogram/max_frames_received", ANY)
        ])
        assert test_daq.daq.file_writing is True

    def test_config_odin_data(self, test_daq):
        with patch("hexitec.HexitecDAQ.ApiAdapterRequest") as mock_request:
            test_daq.daq.config_dir = "fake/dir"
            test_daq.daq.config_files["fp"] = "fp_hexitec.config"

            test_daq.daq._config_odin_data("fp")
            config = "/{}/{}".format(test_daq.daq.config_dir, test_daq.daq.config_files["fp"])

            mock_request.assert_called_with(config, content_type="application/json")
            test_daq.fake_fp.put.assert_called_with("config/config_file", mock_request())

    def test_start_acquisition(self, test_daq):
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            test_daq.fp_data["value"][0]["hdf"]["frames_processed"] = 0
            test_daq.daq.first_initialisation = False
            test_daq.daq.start_acquisition(10)

            assert test_daq.daq.frame_start_acquisition == 0
            assert test_daq.daq.frame_end_acquisition == 10
            assert test_daq.daq.in_progress is True
            assert test_daq.daq.file_writing is True

            mock_loop.instance().call_later.assert_called_with(1.3, test_daq.daq.acquisition_check_loop)

    def test_start_acquisition_needs_configure(self, test_daq):
        new_fp_data = {
            "value": [{
                "connected": True
            }]
        }
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop, \
             patch("hexitec.HexitecDAQ.ApiAdapterRequest") as mock_request, \
             patch.dict(test_daq.fr_data['value'][0]['status'], {"configuration_complete": False}, clear=True), \
             patch.dict(test_daq.fp_data, new_fp_data, clear=True):

            test_daq.daq.first_initialisation = False
            test_daq.daq.start_acquisition(10)

            test_daq.fake_fp.put.assert_any_call("config/config_file", mock_request())
            test_daq.fake_fr.put.assert_called_with("config/config_file", mock_request())

            assert test_daq.daq.frame_start_acquisition == 0
            assert test_daq.daq.frame_end_acquisition == 10
            assert test_daq.daq.in_progress is True
            assert test_daq.daq.file_writing is True

            mock_loop.instance().call_later.assert_called_with(1.3, test_daq.daq.acquisition_check_loop)

    def test_start_acquisition_fr_disconnected(self, test_daq):
        new_fr_data = {
            "not_value": False
            # "value": [{
            #     # "connected": False
            # }]
        }

        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop, \
             patch("hexitec.HexitecDAQ.ApiAdapterRequest") as mock_request, \
             patch.dict(test_daq.fr_data, new_fr_data, clear=True):

            test_daq.daq.start_acquisition(10)

            assert test_daq.daq.file_writing is False
            assert test_daq.daq.in_progress is False

            mock_loop.instance().add_callback.assert_not_called()

    def test_start_acquisition_fp_disconnected(self, test_daq):
        new_fp_data = {
            "not_value": False
            # "value": [{
            #     # "connected": False
            # }]
        }

        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop, \
             patch("hexitec.HexitecDAQ.ApiAdapterRequest") as mock_request, \
             patch.dict(test_daq.fp_data, new_fp_data, clear=True):

            test_daq.daq.start_acquisition(10)

            assert test_daq.daq.file_writing is False
            assert test_daq.daq.in_progress is False

            mock_loop.instance().add_callback.assert_not_called()

    def test_acquisition_check_loop(self, test_daq):
        """Test that function calls itself if hardware busy."""
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            test_daq.adapter.hexitec.fems[0].hardware_busy = True

            test_daq.daq.acquisition_check_loop()
            mock_loop.instance().call_later.assert_called_with(.5, test_daq.daq.acquisition_check_loop)

    def test_processing_check_loop(self, test_daq):
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            # Covers lines 254-260
            test_daq.daq.first_initialisation = True
            test_daq.daq.processing_check_loop()
            mock_loop.instance().call_later.assert_called_with(2.0, test_daq.daq.stop_acquisition)

            # This block actually tests acquisition_check_loop but if I move it
            # into the previous test function, it fails.....
            test_daq.daq.frame_end_acquisition = 10
            test_daq.daq.acquisition_check_loop()
            test_daq.daq.first_initialisation = False
            mock_loop.instance().call_later.assert_called_with(.5, test_daq.daq.processing_check_loop)

            # Cover lines 274-281
            # # assert test_daq.daq.first_initialisation is True # first_init == False
            test_daq.fp_data["value"][0]["hdf"]["frames_processed"] = 10
            test_daq.daq.plugin = "hdf"
            test_daq.daq.processing_check_loop()
            # assert test_daq.daq.frame_end_acquisition == 10   # frame_end_acquisition == 10
            # # assert test_daq.daq.ps == test_daq.daq.plugin
            # # mock_loop.instance().call_later.assert_called_with(1.0, test_daq.daq.stop_acquisition)
            mock_loop.instance().call_later.assert_called_with(1.0, test_daq.daq.hdf_closing_loop)

            # Covers lines 296
            test_daq.daq.plugin = "histogram"
            test_daq.daq.parent.fems[0].hardware_busy = True
            test_daq.daq.frame_end_acquisition = 10
            test_daq.daq.processing_check_loop()
            mock_loop.instance().call_later.assert_called_with(.5, test_daq.daq.processing_check_loop)

            # Covers lines 283-290
            test_daq.daq.first_initialisation = False
            test_daq.daq.parent.fems[0].hardware_busy = True
            test_daq.daq.frame_end_acquisition = 10
            test_daq.daq.shutdown_processing = True
            test_daq.daq.processing_check_loop()
            mock_loop.instance().add_callback.assert_called_with(test_daq.daq.stop_acquisition)

            # Covers lines 292-4
            test_daq.daq.frames_processed = 5
            test_daq.daq.processing_check_loop()
            assert pytest.approx(test_daq.daq.processed_timestamp) == time.time()

    def test_stop_acquisition(self, test_daq):
        assert test_daq.daq.file_writing is False

        test_daq.daq.file_writing = True
        assert test_daq.daq.file_writing is True

        test_daq.daq.stop_acquisition()
        assert test_daq.daq.file_writing is False

    # def test_prepare_hdf_file(self, test_daq):

    #     file_name = "/tmp/mytestfile.hdf5"
    #     if os.path.isfile(file_name):
    #         os.remove(file_name)
    #     else:
    #         print("No file existed, going ahead..")
    #     empty_hdf_file = h5py.File("/tmp/mytestfile.hdf5", "w")

    #     with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:#, \
    #         # with patch('foo.config', new=config_test):  # Use config_test in lieu of foo.config

    #         # Cover line 322-24, 339-53
    #         # h5py.File = Mock(return_value="whatever")
    #         # h5py.File returns h5py._hl.files.File
    #         test_daq.daq.hdf_retry = 6
    #         test_daq.daq.hdf_file_location = Mock(return_value=empty_hdf_file)
    #         # test_daq.adapter.hexitec.param_tree.get = Mock(return_value=dict)
    #         # test_daq.daq.write_method data
    #         test_daq.daq.prepare_hdf_file()  # Fails on: parent_metadata_group = hdf_file.create_group("hexitec")

    #         assert test_daq.daq.hdf_retry == 0

    #     empty_hdf_file.close()

    # TODO: Abandon this unit test if the previous can be made to work..
    # def test_write_metadata(self, test_daq):
    #     # <class 'h5py._hl.group.Group'> <class 'dict'>
    #     # <HDF5 group "/hexitec" (0 members)>
    #     # ______________________________________________________________________
    #     #
    #     metadata_group = Mock(return_value=h5py._hl.group.Group)
    #     param_tree_dict = {'odin_version': '0.3.1+102.g01c51d7', 'tornado_version': '4.5.3'}
    #     with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:
    #         test_daq.daq.write_metadata(metadata_group, param_tree_dict)
    #       # mock_loop.instance().call_later.assert_called_with(0.5, test_daq.daq.hdf_closing_loop)

    def test_hdf_closing_loop(self, test_daq):
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            # Cover lines 304-307
            test_daq.fp_data["value"][0]["hdf"]["writing"] = True
            test_daq.daq.hdf_closing_loop()
            mock_loop.instance().call_later.assert_called_with(0.5, test_daq.daq.hdf_closing_loop)

            # Cover lines 308-316
            test_daq.fp_data["value"][0]["hdf"]["writing"] = False
            test_daq.daq.in_progress = True
            test_daq.daq.hdf_closing_loop()
            assert test_daq.daq.in_progress is False

            # Cover lines (312), 321, 333-337
            test_daq.fp_data["value"][0]["hdf"]["writing"] = False
            test_daq.daq.in_progress = True
            os.path.exists = Mock(return_value="True")
            h5py.File = Mock(return_value="whatever")
            h5py.File.side_effect = IOError(Mock(status=404)) #, 'not found')
            test_daq.adapter.hexitec.fems[0].status_error  # (.status_message)
            test_daq.daq.hdf_retry = 6
            test_daq.daq.hdf_closing_loop()
            assert test_daq.daq.in_progress is False
            assert test_daq.adapter.hexitec.fems[0].status_error[:25] == "Error reopening HDF file:"

    def test_flatten_dict(self, test_daq):
        test_dict = {"test": 5, "tree": {"branch_1": 1.1, "branch_2": 1.2}}
        flattened_dict = {'test': 5, 'tree/branch_1': 1.1, 'tree/branch_2': 1.2}

        d = test_daq.daq._flatten_dict(test_dict)
        assert d == flattened_dict

    def test_set_number_frames(self, test_daq):
        number_frames = 25
        test_daq.daq.set_number_frames(number_frames)
        assert number_frames == test_daq.daq.number_frames

    def test_set_addition_enable(self, test_daq):
        addition_enable = True
        test_daq.daq._set_addition_enable(addition_enable)
        assert addition_enable is test_daq.daq.addition_enable

        addition_enable = False
        test_daq.daq._set_addition_enable(addition_enable)
        assert addition_enable is test_daq.daq.addition_enable

    def test_set_calibration_enable(self, test_daq):
        calibration_enable = True
        test_daq.daq._set_calibration_enable(calibration_enable)
        assert calibration_enable is test_daq.daq.calibration_enable

        calibration_enable = False
        test_daq.daq._set_calibration_enable(calibration_enable)
        assert calibration_enable is test_daq.daq.calibration_enable

    def test_set_discrimination_enable(self, test_daq):
        discrimination_enable = True
        test_daq.daq._set_discrimination_enable(discrimination_enable)
        assert discrimination_enable is test_daq.daq.discrimination_enable

        discrimination_enable = False
        test_daq.daq._set_discrimination_enable(discrimination_enable)
        assert discrimination_enable is test_daq.daq.discrimination_enable

    def test_set_next_frame_enable(self, test_daq):
        next_frame_enable = True
        test_daq.daq._set_next_frame_enable(next_frame_enable)
        assert next_frame_enable is test_daq.daq.next_frame_enable

        next_frame_enable = False
        test_daq.daq._set_next_frame_enable(next_frame_enable)
        assert next_frame_enable is test_daq.daq.next_frame_enable

    def test_set_pixel_grid_size(self, test_daq):
        pixel_grid_size = 3
        test_daq.daq._set_pixel_grid_size(pixel_grid_size)
        assert pixel_grid_size == test_daq.daq.pixel_grid_size

        with pytest.raises(ParameterTreeError, match="Must be either 3 or 5"):
            test_daq.daq._set_pixel_grid_size(4)

    def test_set_gradients_filename(self, test_daq):
        gradients_filename = "/u/ckd27546/develop/projects/odin-demo/hexitec-detector/data/frameProcessor/m_2018_01_001_400V_20C.txt"
        test_daq.daq._set_gradients_filename(gradients_filename)
        assert gradients_filename == test_daq.daq.gradients_filename

        with pytest.raises(ParameterTreeError, match="Gradients file doesn't exist"):
            test_daq.daq._set_gradients_filename("rubbish_filename.txt")

    def test_set_intercepts_filename(self, test_daq):
        path = "/u/ckd27546/develop/projects/odin-demo/hexitec-detector/data/frameProcessor/"
        intercepts_filename = path + "c_2018_01_001_400V_20C.txt"
        test_daq.daq._set_intercepts_filename(intercepts_filename)
        assert intercepts_filename == test_daq.daq.intercepts_filename

        with pytest.raises(ParameterTreeError, match="Intercepts file doesn't exist"):
            test_daq.daq._set_intercepts_filename("rubbish_filename.txt")

    def test_update_datasets_frame_dimensions(self, test_daq):

        test_daq.daq.update_datasets_frame_dimensions()

        test_daq.fake_fp.put.assert_has_calls([
            call("config/hdf/dataset/processed_frames", ANY),
            call("config/hdf/dataset/raw_frames", ANY)
        ])

    def test_set_bin_end(self, test_daq):
        bin_end = 8000
        test_daq.daq._set_bin_end(bin_end)
        assert bin_end == test_daq.daq.bin_end

        # self.bin_end = bin_end
        # self.update_histogram_dimensions()

    def test_set_bin_start(self, test_daq):
        bin_start = 0
        test_daq.daq._set_bin_start(bin_start)
        assert bin_start == test_daq.daq.bin_start

    def test_set_bin_width(self, test_daq):
        bin_width = 10
        test_daq.daq._set_bin_width(bin_width)
        assert bin_width == test_daq.daq.bin_width

    # def update_histogram_dimensions(self):
    #     """Update histograms' dimensions in the relevant datasets."""
    #     self.number_histograms = int((self.bin_end - self.bin_start) / self.bin_width)
    #     # spectra_bins dataset
    #     payload = '{"dims": [%s], "chunks": [1, %s]}' % \
    #         (self.number_histograms, self.number_histograms)
    #     command = "config/hdf/dataset/" + "spectra_bins"
    #     request = ApiAdapterRequest(str(payload), content_type="application/json")
    #     self.adapters["fp"].put(command, request)

    #     # pixel_spectra dataset
    #     payload = '{"dims": [%s, %s], "chunks": [1, %s, %s]}' % \
    #         (self.pixels, self.number_histograms, self.pixels, self.number_histograms)
    #     command = "config/hdf/dataset/" + "pixel_spectra"
    #     request = ApiAdapterRequest(str(payload), content_type="application/json")
    #     self.adapters["fp"].put(command, request)

    #     # summed_spectra dataset
    #     payload = '{"dims": [%s], "chunks": [1, %s]}' % \
    #         (self.number_histograms, self.number_histograms)
    #     command = "config/hdf/dataset/" + "summed_spectra"
    #     request = ApiAdapterRequest(str(payload), content_type="application/json")
    #     self.adapters["fp"].put(command, request)

    def test_set_max_frames_received(self, test_daq):
        max_frames = 100
        test_daq.daq._set_max_frames_received(max_frames)
        assert max_frames == test_daq.daq.max_frames_received

    def test_set_pass_processed(self, test_daq):
        pass_processed = 10
        test_daq.daq._set_pass_processed(pass_processed)
        assert pass_processed == test_daq.daq.pass_processed

    def test_set_raw_data(self, test_daq):
        raw_data = True
        test_daq.daq._set_raw_data(raw_data)
        assert raw_data is test_daq.daq.raw_data

        raw_data = False
        test_daq.daq._set_raw_data(raw_data)
        assert raw_data is test_daq.daq.raw_data

    def test_set_threshold_filename(self, test_daq):
        path = "/u/ckd27546/develop/projects/odin-demo/hexitec-detector/data/frameProcessor/"
        threshold_filename = path + "thresh_2018_01_001_400V_20C.txt"
        test_daq.daq._set_threshold_filename(threshold_filename)
        assert threshold_filename == test_daq.daq.threshold_filename

        with pytest.raises(ParameterTreeError, match="Threshold file doesn't exist"):
            test_daq.daq._set_threshold_filename("rubbish_filename.txt")

    def test_set_threshold_mode(self, test_daq):
        threshold_mode = "value"
        test_daq.daq._set_threshold_mode(threshold_mode)
        assert threshold_mode == test_daq.daq.threshold_mode

        with pytest.raises(ParameterTreeError, match="Must be one of: value, filename or none"):
            test_daq.daq._set_threshold_mode("rubbish_filename.txt")

    def test_set_threshold_value(self, test_daq):
        threshold_value = 101
        test_daq.daq._set_threshold_value(threshold_value)
        assert test_daq.daq.threshold_value == threshold_value

    def test_access_sensors_layout(self, test_daq):
        sensors_layout = "2x2"
        test_daq.daq._set_sensors_layout(sensors_layout)
        assert test_daq.daq._get_sensors_layout() == sensors_layout

    # TODO: Work out how to mock parameter tree?
    # def test_commit_configuration(self, test_daq):
    #     #
    #     with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

    #         test_daq.daq.gcf = Mock()
    #         # test_daq.daq.gcf.generate_config_files() = Mock(return_value="str1", "str2")

    #         test_daq.daq.acquisition_check_loop()
    #         test_daq.daq.commit_configuration()
    #         mock_loop.instance().call_later.assert_called_with(.5, test_daq.daq.acquisition_check_loop)

    # def test_submit_configuration(self, test_daq):
    #     #
    #     test_daq.daq.submit_configurations()

#GFC will turn parameter tree into:
#   OrderedDict([('reorder', {'raw_data': True}), ('threshold', {'threshold_value': 99, 'threshold_filename': '', 'threshold_mode': 'none'}), ('next_frame', {'enable': True}), ('calibration', {'enable': False, 'intercepts_filename': '', 'gradients_filename': ''}), ('addition', {'enable': False, 'pixel_grid_size': 3}), ('discrimination', {'enable': False, 'pixel_grid_size': 5}), ('histogram', {'max_frames_received': 10, 'bin_end': 8000, 'bin_width': 10.0, 'bin_start': 0})]) <class 'collections.OrderedDict'>
