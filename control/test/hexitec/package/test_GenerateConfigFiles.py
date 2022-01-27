"""Test Cases for GenerateConfigFiles class.

Christian Angelsen, STFC Detector Systems Software Group
"""

from hexitec.GenerateConfigFiles import GenerateConfigFiles

import unittest
# import pytest
# import time
import sys
import os

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, patch
# else:                         # pragma: no cover
#     from mock import Mock, MagicMock, patch


class ObjectTestFixture(object):
    """Test fixture class."""

    def __init__(self):
        """Initialise object."""

        param_tree = {'file_info': {'file_name': 'default_file', 'enabled': False, 'file_dir': '/tmp/'},
                      'sensors_layout': '1x1', 'receiver':
                      {'config_file': '', 'configured': False, 'connected': False},
                      'in_progress': False,
                      # The 'config' nested dictionary control which plugin(s) are loaded:
                      'config':
                      {'calibration':
                       {'enable': False, 'intercepts_filename': '', 'gradients_filename': ''},
                       'addition':
                       {'enable': True, 'pixel_grid_size': 3},
                       'discrimination': {'enable': False, 'pixel_grid_size': 5},
                       'histogram':
                       {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10.0, 'max_frames_received': 10,
                        'pass_processed': True, 'pass_raw': True},
                       'next_frame': {'enable': False},
                       'threshold':
                       {'threshold_value': 99, 'threshold_filename': '', 'threshold_mode': 'none'},
                       'summed_image': {'threshold_lower': 120, 'threshold_upper': 4800}
                       },
                      'processor': {'config_file': '', 'configured': False, 'connected': False}}

        bin_end = param_tree['config']['histogram']['bin_end']
        bin_start = param_tree['config']['histogram']['bin_start']
        bin_width = param_tree['config']['histogram']['bin_width']
        number_histograms = int((bin_end - bin_start) / bin_width)
        master_dataset = "raw_frames"
        extra_datasets = [master_dataset, "processed_frames"]

        self.adapter = GenerateConfigFiles(param_tree, number_histograms, compression_type="none",
                                           master_dataset=master_dataset, extra_datasets=extra_datasets,
                                           selected_os="CentOS")


class TestObject(unittest.TestCase):
    """Unit tests for the GenerateConfigFiles class."""

    # def test_init_bad_path(self):
    #     """Initialise object."""

    #     param_tree = {'file_info': {'file_name': 'default_file', 'enabled': False, 'file_dir': '/tmp/'},
    #                   'sensors_layout': '1x1', 'receiver':
    #                   {'config_file': '', 'configured': False, 'connected': False},
    #                   'in_progress': False,
    #                   # The 'config' nested dictionary control which plugin(s) are loaded:
    #                   'config':
    #                   {'calibration':
    #                   {'enable': False, 'intercepts_filename': '', 'gradients_filename': ''},
    #                   'addition':
    #                   {'enable': False, 'pixel_grid_size': 3},
    #                   'discrimination': {'enable': False, 'pixel_grid_size': 5},
    #                   'histogram':
    #                   {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10.0, 'max_frames_received': 10,
    #                     'pass_processed': True, 'pass_raw': True},
    #                   'next_frame': {'enable': False},
    #                   'threshold':
    #                   {'threshold_value': 99, 'threshold_filename': '', 'threshold_mode': 'none'},
    #                   'summed_image': {
    #                       'threshold_lower': 120,
    #                       'threshold_upper': 4800}
    #                   },
    #                   'processor': {'config_file': '', 'configured': False, 'connected': False}}

    #     bin_end = param_tree['config']['histogram']['bin_end']
    #     bin_start = param_tree['config']['histogram']['bin_start']
    #     bin_width = param_tree['config']['histogram']['bin_width']
    #     number_histograms = int((bin_end - bin_start) / bin_width)

    #     # Provoke KeyError
    #     options = {
    #         "param_tree":
    #             "{}".format(param_tree),
    #         "number_histograms": "{}".format(number_histograms)
    #     }

    #     # with patch('logging.debug') as mock_log:
    #     with self.assertRaises(KeyError):
    #         new_adapter = GenerateConfigFiles(**options)
    #         # mock_log.assert_called_with('Illegal directory target specified')

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
