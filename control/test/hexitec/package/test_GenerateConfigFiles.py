"""
Test Cases for GenerateConfigFiles class.

Christian Angelsen, STFC Detector Systems Software Group
"""

from hexitec.GenerateConfigFiles import GenerateConfigFiles

import unittest
import pytest


class ObjectTestFixture(object):
    """Test fixture class."""

    def __init__(self, selected_os="CentOS", live_view_selected=True):
        """Initialise object."""
        param_tree = {'file_info': {'file_name': 'default_file', 'enabled': False, 'file_dir': '/tmp/'},
                    'sensors_layout': '2x2', 'receiver':
                    {'config_file': '', 'configured': False, 'connected': False},
                    'status': {'in_progress': False, 'daq_ready': False},
                    # The 'config' nested dictionary control which plugin(s) are loaded:
                    'config':
                    {'calibration':
                    {'enable': True, 'intercepts_filename': '', 'gradients_filename': ''},
                    'addition':
                    {'enable': True, 'pixel_grid_size': 3},
                    'discrimination': {'enable': False, 'pixel_grid_size': 5},
                    'histogram':
                    {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10.0, 'max_frames_received': 10,
                        'pass_processed': True, 'pass_raw': True},
                    'live_view':
                    {'dataset_name': 'summed_spectra', 'frame_frequency': 39,
                        'live_view_socket_addr': 'tcp://127.0.0.1:5020', 'per_second': 1},
                    'next_frame': {'enable': True},
                    'threshold':
                    {'threshold_value': 99, 'threshold_filename': '', 'threshold_mode': 'none'},
                    'summed_image': {
                        'threshold_lower': 120,
                        'threshold_upper': 4800,
                        'image_frequency': 1}
                    },
                    'processor': {'config_file': '', 'configured': False, 'connected': False}}

        bin_end = param_tree['config']['histogram']['bin_end']
        bin_start = param_tree['config']['histogram']['bin_start']
        bin_width = param_tree['config']['histogram']['bin_width']
        number_histograms = int((bin_end - bin_start) / bin_width)
        master_dataset = "raw_frames"
        extra_datasets = [master_dataset, "processed_frames"]

        self.adapter = GenerateConfigFiles(param_tree, number_histograms, compression_type="blosc",
                                           master_dataset=master_dataset, extra_datasets=extra_datasets,
                                           selected_os=selected_os, live_view_selected=live_view_selected)


class TestObject(unittest.TestCase):
    """Unit tests for the GenerateConfigFiles class."""

    def setUp(self):
        """Set up test fixture for each unit test."""
        self.test_detector_adapter = ObjectTestFixture()

    def test_boolean_to_string(self):
        """Test True returns 'true' and False 'False'."""
        boolean = True
        response = self.test_detector_adapter.adapter.boolean_to_string(boolean)
        assert response == "true"

    def test_threshold_settings_fails_invalid_config(self):
        """."""
        settings = {'bad_key_name': 99, 'threshold_filename': '/a/path/and/name.txt', 'threshold_mode': 'value'}

        with self.assertRaises(KeyError):
            self.test_detector_adapter.adapter.threshold_settings(settings)

    def test_threshold_settings(self):
        """."""
        settings = {'threshold_value': 99, 'threshold_filename': '/path/and/filename.txt', 'threshold_mode': 'none'}

        correct_threshold_settings = """
                        "threshold_file": "/path/and/filename.txt",
                        "threshold_value": 99,
                        "threshold_mode": "none","""

        threshold_config = self.test_detector_adapter.adapter.threshold_settings(settings)
        assert threshold_config == correct_threshold_settings

    def test_calibration_settings_fails_invalid_config(self):
        """Test function fails on bad settings."""
        settings = {'bad_key_name': 99}

        with self.assertRaises(KeyError):
            self.test_detector_adapter.adapter.calibration_settings(settings)

    def test_calibration_settings(self):
        """Test function ok with valid settings."""
        settings = {'enable': True, 'intercepts_filename': '', 'gradients_filename': ''}

        correct_calibration_settings = """
                        "gradients_file": "",
                        "intercepts_file": "","""

        calibration_config = self.test_detector_adapter.adapter.calibration_settings(settings)
        assert calibration_config == correct_calibration_settings

    def test_histogram_settings_fails_invalid_config(self):
        """Test function fails on bad settings."""
        settings = {'bad_key_name': 99}

        with self.assertRaises(KeyError):
            self.test_detector_adapter.adapter.histogram_settings(settings)

    def test_histogram_settings(self):
        """Test function ok with valid settings."""
        settings = {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10.0, 'max_frames_received': 10, 'pass_processed': True, 'pass_raw': True}

        correct_histogram_settings = """
                        "bin_start": 0,
                        "bin_end": 8000,
                        "bin_width": 10.0,
                        "max_frames_received": 10,
                        "pass_processed": true,
                        "pass_raw": true,"""

        histogram_config = self.test_detector_adapter.adapter.histogram_settings(settings)
        assert histogram_config == correct_histogram_settings

    def test_live_view_settings_fails_invalid_config(self):
        """Test function fails on bad settings."""
        settings = {'bad_key_name': 99}

        with self.assertRaises(KeyError):
            self.test_detector_adapter.adapter.live_view_settings(settings)

    def test_live_view_settings(self):
        """Test function ok with valid settings."""
        settings = {'frame_frequency': 5, 'per_second': 1,
                        'live_view_socket_addr': 'tcp://192.168.0.13:5020',
                        'dataset_name': 'processed_frames'}

        correct_live_view_settings = ''',
                {
                    "live_view":
                    {
                        "frame_frequency": 5,
                        "per_second": 1,
                        "live_view_socket_addr": "tcp://192.168.0.13:5020",
                        "dataset_name": "processed_frames"
                    }
                }'''
        live_view_config = self.test_detector_adapter.adapter.live_view_settings(settings)
        assert live_view_config == correct_live_view_settings

    def test_summed_image_settings_fails_invalid_config(self):
        """Test function fails on bad settings."""
        settings = {'bad_key_name': 99}

        with self.assertRaises(KeyError):
            self.test_detector_adapter.adapter.summed_image_settings(settings)

    def test_summed_image_settings(self):
        """Test function ok with valid settings."""
        settings = {'threshold_lower': 120, 'threshold_upper': 4800}

        correct_summed_image_settings = """
                        "threshold_lower": 120,
                        "threshold_upper": 4800,"""

        summed_image_config = self.test_detector_adapter.adapter.summed_image_settings(settings)
        assert summed_image_config == correct_summed_image_settings

    def test_generate_config_files(self):
        """Test function works ok."""
        self.test_detector_adapter.adapter.generate_config_files()


class TestObject2(unittest.TestCase):
    """Unit tests for bad config, Ubuntu, live view disabled tests."""

    def setUp(self):
        """Set up test fixture for each unit test."""
        self.test_detector_badadapter = ObjectTestFixture("Ubuntu", live_view_selected=False)

    def test_generate_config_files_fails_missing_enable_key(self):
        """Test function fail on missing enable key."""
        # Function should fail if any optional plugin doesn't define the key 'enable'
        with pytest.raises(Exception) as exc_info:
            # 'Pretend' next_frame doesn't have 'enable' key
            self.test_detector_badadapter.adapter.param_tree['config']['next_frame'] = {}
            self.test_detector_badadapter.adapter.generate_config_files()
        assert exc_info.type is Exception
        assert exc_info.value.args[0] == "Plugin %s missing 'enable' setting!" % 'next_frame'

    def testing_ubuntu_config(self):
        """Test function."""
        self.test_detector_badadapter.adapter.generate_config_files()
