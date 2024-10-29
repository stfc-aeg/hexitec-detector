"""
Test Cases for GenerateConfigFiles class.

Christian Angelsen, STFC Detector Systems Software Group
"""

from hexitec.GenerateConfigFiles import GenerateConfigFiles

import unittest
import pytest
import json


class ObjectTestFixture(object):
    """Test fixture class."""

    def __init__(self, live_view_selected=True):
        """Initialise object."""
        param_tree = {'file_info':
                      {'file_name': 'default_file', 'enabled': False, 'file_dir': '/tmp/'},
                      'sensors_layout': '2x6',
                      'receiver':
                      {'config_file': '', 'configured': False, 'connected': False},
                      'status': {'in_progress': False, 'daq_ready': False},
                      # The 'config' nested dictionary control which plugin(s) are loaded:
                      'config':
                      {'calibration': {'enable': True, 'intercepts_filename': '',
                                       'gradients_filename': ''},
                       'addition': {'enable': True, 'pixel_grid_size': 3},
                       'discrimination': {'enable': False, 'pixel_grid_size': 5},
                       'histogram': {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10.0,
                                     'max_frames_received': 10, 'pass_processed': True,
                                     'pass_raw': True},
                       'lvframes': {'dataset_name': 'raw_frames', 'frame_frequency': 0,
                                    'live_view_socket_addr': 'tcp://127.0.0.1:5020',
                                    'per_second': 2},
                       'lvspectra': {'dataset_name': 'summed_spectra', 'frame_frequency': 0,
                                     'live_view_socket_addr': 'tcp://127.0.0.1:5021',
                                     'per_second': 1},
                       'threshold': {'threshold_value': 99, 'threshold_filename': '',
                                     'threshold_mode': 'none'},
                       'summed_image': {'threshold_lower': 120, 'threshold_upper': 4800,
                                        'image_frequency': 1}},
                      'processor': {'config_file': '', 'configured': False, 'connected': False}}

        bin_end = param_tree['config']['histogram']['bin_end']
        bin_start = param_tree['config']['histogram']['bin_start']
        bin_width = param_tree['config']['histogram']['bin_width']
        number_histograms = int((bin_end - bin_start) / bin_width)
        master_dataset = "raw_frames"
        extra_datasets = [master_dataset, "processed_frames"]

        self.adapter = GenerateConfigFiles(param_tree, number_histograms, compression_type="blosc",
                                           master_dataset=master_dataset,
                                           extra_datasets=extra_datasets,
                                           live_view_selected=live_view_selected)


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
        """Test function fails on bad settings."""
        settings = {'bad_key_name': 99, 'threshold_filename': '/a/path/and/name.txt',
                    'threshold_mode': 'value'}

        with self.assertRaises(KeyError):
            self.test_detector_adapter.adapter.threshold_settings(settings)

    def test_threshold_settings(self):
        """Test function ok with valid settings."""
        settings = {'threshold_value': 99, 'threshold_filename': '/path/and/filename.txt',
                    'threshold_mode': 'none'}

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
        settings = {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10.0, 'max_frames_received': 10,
                    'pass_processed': True, 'pass_raw': True}

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
            self.test_detector_adapter.adapter.live_view_settings("lvspectra", settings)

    def test_live_view_settings(self):
        """Test function ok with valid settings."""
        plugin_name = "lvframes"
        settings = {'frame_frequency': 5, 'per_second': 1,
                    'live_view_socket_addr': 'tcp://192.168.0.13:5020',
                    'dataset_name': 'processed_frames'}

        correct_live_view_settings = ''',
                {
                    "%s":
                    {
                        "frame_frequency": 5,
                        "per_second": 1,
                        "live_view_socket_addr": "tcp://192.168.0.13:5020",
                        "dataset_name": "processed_frames"
                    }
                }''' % plugin_name
        live_view_config = \
            self.test_detector_adapter.adapter.live_view_settings(plugin_name, settings)
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
        store_temp_name, execute_temp_name, store_string_without_cr, \
            execute_string_without_cr = self.test_detector_adapter.adapter.generate_config_files()
        assert store_temp_name == "/tmp/_tmp_store.json"
        assert execute_temp_name == "/tmp/_tmp_execute.json"

        sl_value = self.test_detector_adapter.adapter.param_tree["sensors_layout"]
        sl_dic = {'sensors_layout': sl_value}
        d = json.loads(store_string_without_cr)
        assert d['index'] == store_temp_name[5:]
        assert d['value'][0]['plugin']['load']['index'] == 'reorder'
        assert d['value'][1]['plugin']['load']['index'] == 'threshold'
        assert d['value'][2]['plugin']['load']['index'] == 'calibration'
        assert d['value'][3]['plugin']['load']['index'] == 'addition'
        assert d['value'][4]['plugin']['load']['index'] == 'summed_image'
        assert d['value'][5]['plugin']['load']['index'] == 'histogram'
        assert d['value'][6]['plugin']['load']['index'] == 'lvframes'
        assert d['value'][7]['plugin']['load']['index'] == 'lvspectra'
        assert d['value'][8]['plugin']['load']['index'] == 'blosc'
        assert d['value'][9]['plugin']['load']['index'] == 'hdf'
        assert d['value'][10]['plugin'] == {'connect': {'index': 'lvframes',
                                            'connection': 'histogram'}}
        assert d['value'][11]['plugin'] == {'connect': {'index': 'lvspectra',
                                            'connection': 'histogram'}}
        assert d['value'][12]['plugin'] == {'connect': {'index': 'reorder',
                                            'connection': 'frame_receiver'}}
        assert d['value'][13]['plugin'] == {'connect':
                                            {'index': 'threshold', 'connection': 'reorder'}}
        assert d['value'][14]['plugin'] == {'connect':
                                            {'index': 'calibration', 'connection': 'threshold'}}
        assert d['value'][15]['plugin'] == {'connect':
                                            {'index': 'addition', 'connection': 'calibration'}}
        assert d['value'][16]['plugin'] == {'connect':
                                            {'index': 'summed_image', 'connection': 'addition'}}
        assert d['value'][17]['plugin'] == {'connect':
                                            {'index': 'histogram', 'connection': 'summed_image'}}
        assert d['value'][18]['plugin'] == {'connect':
                                            {'index': 'blosc', 'connection': 'histogram'}}
        assert d['value'][19]['plugin'] == {'connect': {'index': 'hdf', 'connection': 'blosc'}}
        assert d['value'][20] == {'reorder': sl_dic}
        assert d['value'][21] == {'threshold':
                                  {'threshold_file': '', 'threshold_value': 99,
                                   'threshold_mode': 'none', 'sensors_layout': sl_value}}
        assert d['value'][22] == {'calibration':
                                  {'gradients_file': '', 'intercepts_file': '',
                                   'sensors_layout': sl_value}}
        assert d['value'][23] == {'addition': {'pixel_grid_size': 3, 'sensors_layout': sl_value}}
        assert d['value'][24] == {'summed_image':
                                  {'threshold_lower': 120, 'threshold_upper': 4800,
                                   'sensors_layout': sl_value}}
        assert d['value'][25] == {'histogram':
                                  {'bin_start': 0, 'bin_end': 8000, 'bin_width': 10.0,
                                   'max_frames_received': 10, 'pass_processed': True,
                                   'pass_raw': True, 'sensors_layout': sl_value}}
        assert d['value'][26] == {'blosc': sl_dic}
        assert d['value'][27] == {'lvframes':
                                  {'frame_frequency': 0, 'per_second': 2,
                                   'live_view_socket_addr': 'tcp://127.0.0.1:5020',
                                   'dataset_name': 'raw_frames'}}
        assert d['value'][28] == {'lvspectra':
                                  {'frame_frequency': 0, 'per_second': 1,
                                   'live_view_socket_addr': 'tcp://127.0.0.1:5021',
                                   'dataset_name': 'summed_spectra'}}

        assert execute_string_without_cr == '{"index":"_tmp_store.json"}'


class TestObject2(unittest.TestCase):
    """Unit tests for bad config, live view disabled tests."""

    def setUp(self):
        """Set up test fixture for each unit test."""
        self.test_detector_badadapter = ObjectTestFixture(live_view_selected=False)

    def test_generate_config_files_fails_missing_enable_key(self):
        """Test function fail on missing enable key."""
        # Function should fail if any optional plugin doesn't define the key 'enable'
        with pytest.raises(Exception) as exc_info:
            # 'Pretend' addition doesn't have 'enable' key
            self.test_detector_badadapter.adapter.param_tree['config']['addition'] = {}
            self.test_detector_badadapter.adapter.generate_config_files()
        assert exc_info.type is Exception
        assert exc_info.value.args[0] == "Plugin %s missing 'enable' setting!" % 'addition'

    def testing_bad_config(self):
        """Test function."""
        self.test_detector_badadapter.adapter.generate_config_files()
