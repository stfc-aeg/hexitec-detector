"""
Test Cases for the Hexitec DAQ in hexitec.HexitecDAQ
Christian Angelsen, STFC Detector Systems Software Group
"""

import sys
import pytest

from odin.adapters.adapter import ApiAdapterRequest

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
                        "frames_written": 0
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

        connected = test_daq.daq.is_od_connected(test_daq.fr_data['value'][0])
        assert connected

    def test_is_fp_connected_with_status(self, test_daq):

        connected = test_daq.daq.is_od_connected(test_daq.fp_data['value'][0])
        assert connected

    def test_is_fr_connected_without_status(self, test_daq):

        connected = test_daq.daq.is_od_connected(adapter="fr")
        assert connected

    def test_is_fp_connected_without_status(self, test_daq):

        connected = test_daq.daq.is_od_connected(adapter="fp")
        assert connected

    def test_is_fr_configured_with_status(self, test_daq):

        configured = test_daq.daq.is_fr_configured(test_daq.fr_data['value'][0])
        assert configured

    def test_is_fp_configured_with_status(self, test_daq):

        configured = test_daq.daq.is_fp_configured(test_daq.fp_data['value'][0])
        assert configured

    def test_is_fr_configured_without_status(self, test_daq):

        configured = test_daq.daq.is_fr_configured()
        assert configured

    def test_is_fp_configured_without_status(self, test_daq):

        configured = test_daq.daq.is_fp_configured()
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
            call("config/hdf/file/path", ANY),
            call("config/hdf/file/name", ANY),
            call("config/hdf/write", ANY),
            call("config/histogram/max_frames_received", ANY),
            call("config/hdf/frames", ANY)
        ])
        assert test_daq.daq.file_writing is True

    def test_config_odin_data(self, test_daq):
        with patch("hexitec.HexitecDAQ.ApiAdapterRequest") as mock_request:
            test_daq.daq.config_dir = "fake/dir"
            test_daq.daq.config_files["fp"] = "fp_hexitec.config"

            test_daq.daq.config_odin_data("fp")
            config = "/{}/{}".format(test_daq.daq.config_dir, test_daq.daq.config_files["fp"])

            mock_request.assert_called_with(config, content_type="application/json")
            test_daq.fake_fp.put.assert_called_with("config/config_file", mock_request())

    def test_processing_check_loop(self, test_daq):
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            test_daq.daq.frame_end_acquisition = 10

            test_daq.daq.acquisition_check_loop()
            mock_loop.instance().call_later.assert_called_with(.5, test_daq.daq.processing_check_loop)

            mock_loop.reset_mock()

            test_daq.fp_data["value"][0]["hdf"]["frames_processed"] = 10
            test_daq.fp_data["value"][0]["hdf"]["writing"] = False

            test_daq.daq.processing_check_loop()
            mock_loop.instance().call_later.assert_not_called()

    def test_start_acquisition(self, test_daq):
        with patch("hexitec.HexitecDAQ.IOLoop") as mock_loop:

            test_daq.fp_data["value"][0]["hdf"]["frames_processed"] = 0
            test_daq.daq.first_initialisation = False
            test_daq.daq.start_acquisition(10)

            assert test_daq.daq.frame_start_acquisition == 0
            assert test_daq.daq.frame_end_acquisition == 10
            assert test_daq.daq.in_progress is True
            assert test_daq.daq.file_writing is True

            mock_loop.instance().call_later.assert_called_with(.5, test_daq.daq.acquisition_check_loop)

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

            mock_loop.instance().call_later.assert_called_with(.5, test_daq.daq.acquisition_check_loop)

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
            
