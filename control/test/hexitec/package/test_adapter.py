"""Test Cases for HexitecAdapter, Hexitec in hexitec.HexitecDAQ, hexitec.Hexitec.

Christian Angelsen, STFC Detector Systems Software Group
"""

import unittest
import time
import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, patch, ANY
else:                         # pragma: no cover
    from mock import Mock, MagicMock, patch, ANY

from hexitec.adapter import HexitecAdapter, Hexitec, HexitecDetectorDefaults


class DetectorAdapterTestFixture(object):

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
        with patch('hexitec.adapter.HexitecFem'), \
             patch('hexitec.adapter.HexitecDAQ'):

            self.adapter = HexitecAdapter(**self.options)
            self.detector = self.adapter.hexitec  # shortcut, makes assert lines shorter
            self.path = "detector/acquisition/number_frames"
            self.put_data = 1024
            self.request = Mock()
            self.request.configure_mock(
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                body=self.put_data
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

    def setUp(self):
        self.test_adapter = DetectorAdapterTestFixture()

    def test_adapter_get(self):
        """Test that a call to the detector adapter's GET method returns the correct response."""
        expected_response = {
            'number_frames': 10
        }
        response = self.test_adapter.adapter.get(
            self.test_adapter.path,
            self.test_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200

    def test_adapter_get_error(self):
        false_path = "not/a/path"
        expected_response = {
            'error': "Invalid path: {}".format(false_path)
        }
        response = self.test_adapter.adapter.get(
            false_path,
            self.test_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 400

    def test_adapter_put(self):
        """Test that a normal call to the PUT method returns as expected"""
        expected_response = {
            'number_frames': self.test_adapter.put_data
        }

        response = self.test_adapter.adapter.put(
            self.test_adapter.path,
            self.test_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200
        assert self.test_adapter.detector.number_frames == self.test_adapter.put_data

    def test_adapter_put_error(self):
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


class TestDetector(unittest.TestCase):

    def setUp(self):
        self.test_adapter = DetectorAdapterTestFixture()

    def test_detector_init(self):
        defaults = HexitecDetectorDefaults()

        assert self.test_adapter.detector.file_dir == defaults.save_dir
        assert len(self.test_adapter.detector.fems) == 1
        assert isinstance(self.test_adapter.detector.fems[0], MagicMock)
        fem = self.test_adapter.detector.fems[0]
        fem.connect()
        fem.connect.assert_called_with()

    def test_detector_get_od_status_fp(self):

        with patch("hexitec.adapter.ApiAdapterRequest") as mock_request:

            # Initialise adapters in adapter
            self.test_adapter.detector.adapters = self.test_adapter.adapters

            rc_value = self.test_adapter.detector._get_od_status("fp")
            config = None

            # Doublechecking _get_od_status() fp adapter's get() - redundant?
            mock_request.assert_called_with(config, content_type="application/json")

            assert self.test_adapter.fp_data["value"] == [rc_value]

    def test_detector_get_od_status_misnamed_adapter(self):

        with patch("hexitec.adapter.ApiAdapterRequest"):

            # Initialise adapters in adapter
            self.test_adapter.detector.adapters = self.test_adapter.adapters
            adapter = "wRong"
            rc_value = self.test_adapter.detector._get_od_status(adapter)
            response = {"Error": "Adapter {} not found".format(adapter)}

            assert response == rc_value

    def test_detector_init_default_fem(self):
        """Test that the detector correctly sets up the default fem if none provided"""

        defaults = HexitecDetectorDefaults()
        with patch('hexitec.adapter.HexitecFem') as mock_fem, \
             patch('hexitec.adapter.HexitecDAQ'):

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
        options = self.test_adapter.options

        options["fem_1"] = """
                id = 0,
                server_ctrl_ip = 127.0.0.2,
                camera_ctrl_ip = 127.0.0.2,
                server_data_ip = 127.0.0.2,
                camera_data_ip = 127.0.0.2
                """
        with patch('hexitec.adapter.HexitecFem'), \
             patch('hexitec.adapter.HexitecDAQ'):

            detector = Hexitec(options)

        assert len(detector.fems) == 2

    def test_detector_shutdown_processing(self):

        self.test_adapter.detector.daq.shutdown_processing = False
        self.test_adapter.detector.acquisition_in_progress = True

        self.test_adapter.detector.shutdown_processing()

        assert self.test_adapter.detector.daq.shutdown_processing is True
        assert self.test_adapter.detector.acquisition_in_progress is False

    def test_detector_set_acq(self):

        self.test_adapter.detector.set_number_frames(5)

        assert self.test_adapter.detector.number_frames == 5

    def test_detector_acquisition(self):

        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )

        self.test_adapter.detector.fems[0].bias_voltage_refresh = False
        self.test_adapter.detector.first_initialisation = True
        self.test_adapter.detector.adapters = self.test_adapter.adapters

        self.test_adapter.detector.acquisition("data")
        time.sleep(0.6)
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
            time.sleep(0.1)
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
            time.sleep(0.1)
            mock_loop.instance().call_later.assert_called_with(0.09,
                                                               self.test_adapter.detector.acquisition)

    def test_detector_acquisition_handles_extended_acquisition(self):
        """Test function handles acquisition spanning >1 collection windows."""
        self.test_adapter.detector.daq.configure_mock(
            in_progress=False
        )

        self.test_adapter.detector.fems[0].bias_voltage_refresh = True
        self.test_adapter.detector.bias_blocking_acquisition = False
        self.test_adapter.detector.fems[0].bias_refresh_interval = 2
        self.test_adapter.detector.bias_init_time = time.time()

        with patch("hexitec.adapter.IOLoop"):

            self.test_adapter.detector.acquisition("data")
            time.sleep(0.1)
            assert self.test_adapter.detector.extended_acquisition is True

    def test_detector_acquisition_in_progress(self):

        self.test_adapter.detector.daq.configure_mock(
            in_progress=True
        )
        self.test_adapter.detector.acquisition("data")

        self.test_adapter.detector.daq.start_acquisition.assert_not_called()

    # @pytest.mark.skip("WIP")
    def test_detector_initialize(self):

        adapters = {
            "proxy": Mock(),
            "file_interface": Mock(),
            "fp": Mock(),
        }

        self.test_adapter.adapter.initialize(adapters)

        assert adapters == self.test_adapter.detector.adapters

        self.test_adapter.detector.daq.initialize.assert_called_with(adapters)
