import sys

import pytest
import logging

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, patch, ANY
else:                         # pragma: no cover
    from mock import Mock, MagicMock, patch, ANY

#TODO: Hate this hacky way, find better
sys.modules['odin_data.frame_processor_adapter'] = MagicMock()
sys.modules['odin_data.frame_receiver_adapter'] = MagicMock()

#from qemii.detector.adapter import QemDetectorAdapter, QemDetector, QemDetectorDefaults
from hexitec.adapter import HexitecAdapter, Hexitec, HexitecDetectorDefaults

class DetectorAdapterTestFixture(object):

    def __init__(self):
        self.options = {
            "fem_0":
                """
                ip_addr = 192.168.0.122,
                port = 8888,
                id = 0,
                server_ctrl_ip = 127.0.0.1,
                camera_ctrl_ip = 127.0.0.1,
                server_data_ip = 127.0.0.1,
                camera_data_ip = 127.0.0.1
                """
        }
        with patch('hexitec.adapter.HexitecFem'), \
             patch('hexitec.adapter.HexitecDAQ'), \
             patch('hexitec.adapter.FrameProcessorAdapter'), \
             patch('hexitec.adapter.FrameReceiverAdapter'):

            self.adapter = HexitecAdapter(**self.options)
            self.detector = self.adapter.hexitec  # shortcut, makes assert lines shorter
            self.path = "detector/acquisition/num_frames"
            self.put_data = 1024
            self.request = Mock()
            self.request.configure_mock(
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                body=self.put_data
            )


@pytest.fixture
def test_detector_adapter():

    test_detector_adapter = DetectorAdapterTestFixture()
    yield test_detector_adapter


def log_message_seen(caplog, level, message):  # TODO: put this in a test util thing
    """Test if a certain message of a certain level exists in the captured log"""
    for record in caplog.records:
        if record.levelno == level and message in record.getMessage():
            return True

    return False


class TestDetectorAdapter():

    def test_adapter_get(self, test_detector_adapter):
        """Test that a call to the GET method of the detector adapter returns the correct response"""
        expected_response = {
            'num_frames': 20
        }
        response = test_detector_adapter.adapter.get(
            test_detector_adapter.path,
            test_detector_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200

    # def test_adapter_get_error(self, test_detector_adapter):
    #     false_path = "not/a/path"
    #     expected_response = {
    #         'error': "Invalid path: {}".format(false_path)
    #     }
    #     response = test_detector_adapter.adapter.get(
    #         false_path,
    #         test_detector_adapter.request)
    #     assert response.data == expected_response
    #     assert response.status_code == 400

    # def test_adapter_put(self, test_detector_adapter):
    #     """Test that a normal call to the PUT method returns as expected"""
    #     expected_response = {
    #         'num_frames': test_detector_adapter.put_data
    #     }

    #     response = test_detector_adapter.adapter.put(
    #         test_detector_adapter.path,
    #         test_detector_adapter.request)
    #     assert response.data == expected_response
    #     assert response.status_code == 200
    #     assert test_detector_adapter.detector.acq_num == test_detector_adapter.put_data

    # def test_adapter_put_error(self, test_detector_adapter):
    #     false_path = "not/a/path"
    #     expected_response = {
    #         'error': "Failed to decode PUT request body: Invalid path: {}".format(false_path)
    #     }

    #     response = test_detector_adapter.adapter.put(
    #         false_path,
    #         test_detector_adapter.request)
    #     assert response.data == expected_response
    #     assert response.status_code == 400
    #     assert test_detector_adapter.detector.acq_num == 4096


class TestDetector():

    def test_detector_init(self, test_detector_adapter):
        defaults = HexitecDetectorDefaults()
        
        assert test_detector_adapter.detector.file_dir == defaults.save_dir
        assert len(test_detector_adapter.detector.fems) == 1
        assert isinstance(test_detector_adapter.detector.fems[0], MagicMock)
        fem = test_detector_adapter.detector.fems[0]
        fem.connect()
        fem.connect.assert_called_with()

    def test_detector_init_default_fem(self, test_detector_adapter):
        """Test that the detector correctly sets up the default fem if none provided"""

        defaults = HexitecDetectorDefaults()
        with patch('hexitec.adapter.HexitecFem') as mock_fem, \
             patch('hexitec.adapter.HexitecDAQ'):

            detector = Hexitec({})

            mock_fem.assert_called_with(
                ip_address=defaults.fem["ip_addr"],
                port=defaults.fem["port"],
                fem_id=defaults.fem["id"],
                server_ctrl_ip_addr=defaults.fem["server_ctrl_ip"],
                camera_ctrl_ip_addr=defaults.fem["camera_ctrl_ip"],
                server_data_ip_addr=defaults.fem["server_data_ip"],
                camera_data_ip_addr=defaults.fem["camera_data_ip"]
            )

    def test_detector_init_multiple_fem(self, test_detector_adapter):
        options = test_detector_adapter.options

        options["fem_1"] = """
                ip_addr = 192.168.0.123,
                port = 8080,
                id = 0,
                server_ctrl_ip = 127.0.0.2,
                camera_ctrl_ip = 127.0.0.2,
                server_data_ip = 127.0.0.2,
                camera_data_ip = 127.0.0.2
                """
        with patch('hexitec.adapter.HexitecFem') as mock_fem, \
             patch('hexitec.adapter.HexitecDAQ'):
            
            detector = Hexitec(options)

        assert len(detector.fems) == 2

    def test_detector_set_acq(self, test_detector_adapter):

        test_detector_adapter.detector.set_number_frames(5)

        assert test_detector_adapter.detector.number_frames == 5

    # def test_detector_acqusition(self, test_detector_adapter):

    #     test_detector_adapter.detector.daq.configure_mock(
    #         in_progress=False
    #     )

    #     test_detector_adapter.detector.fems[0].get_idelay_lock_status = Mock(return_value=False)

    #     test_detector_adapter.detector.acquisition("data")

    #     test_detector_adapter.detector.daq.start_acquisition.assert_called_with(4096)
    #     fem = test_detector_adapter.detector.fems[0]
    #     fem.setup_camera.assert_called_with()

    # def test_detector_acqusition_in_progress(self, test_detector_adapter):

    #     test_detector_adapter.detector.daq.configure_mock(
    #         in_progress=True
    #     )
    #     test_detector_adapter.detector.acquisition("data")

    #     test_detector_adapter.detector.daq.start_acquisition.assert_not_called()

    # def test_detector_initialize(self, test_detector_adapter, caplog):
        
    #     adapters = {
    #         "proxy": Mock(),
    #         "file_interface": Mock(),  # ensuring out of order from list still works
    #         "fp": Mock(),
    #         # "fr": Mock(),  # remove to test warning message
    #         "not_wanted": Mock()  # ensure unused adapter not added
    #     }

    #     test_detector_adapter.adapter.initialize(adapters)
    #     del adapters["not_wanted"]  # remove for comparsion

    #     assert adapters == test_detector_adapter.detector.adapters
    #     assert log_message_seen(caplog, logging.WARNING, "fr Adapter not found in Adapter List")

    #     test_detector_adapter.detector.calibrator.initialize.assert_called_with(adapters)
    #     test_detector_adapter.detector.daq.initialize.assert_called_with(adapters)
                   
    # def test_detector_cleanup(self, test_detector_adapter):
    #     """Test that the adatper cleanup method correctly calls other cleanup methods"""
    #     test_detector_adapter.adapter.cleanup()

    #     test_detector_adapter.detector.fems[0].cleanup.assert_called_with()
