"""
Test Cases for FileInterface.

Christian Angelsen, STFC Detector Systems Software Group
"""

from hexitec.FileInterface import FileInterfaceAdapter
from odin.adapters.parameter_tree import ParameterTreeError

import unittest
import pytest
import time
import sys
import os

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
else:                         # pragma: no cover
    from mock import Mock, patch


class AdapterTestFixture(object):
    """Test fixture class."""

    def __init__(self):
        """Initialise object."""
        # Construct paths relative to current working directory
        cwd = os.getcwd()
        base_path_index = cwd.rfind("hexitec-detector")
        base_path = cwd[:base_path_index]
        self.odin_control_path = base_path + "hexitec-detector/control/"
        self.odin_data_path = base_path + "hexitec-detector/data/"
        self.odin_data_path = self.odin_data_path + "config/"
        self.options = {
            "directories":
                "odin_data = {}".format(self.odin_data_path)
        }

        self.adapter = FileInterfaceAdapter(**self.options)
        self.adp = self.adapter.fileInterface  # shortcut, makes assert lines shorter
        # To test GET valid
        self.path = "odin_version"
        self.put_data = "{}"
        self.request = Mock()
        self.request.configure_mock(
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            body=self.put_data
        )
        # To test PUT valid
        self.put_again = '"1.1"'
        self.request_put = Mock()
        self.request_put.configure_mock(
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            body=self.put_again
        )
        # To test PUT invalid
        self.put_bad = None
        self.request_bad_put = Mock()
        self.request_bad_put.configure_mock(
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            body=self.put_bad
        )

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

        fi_return = Mock()
        fi_return.configure_mock(data=self.fi_data)


class TestAdapter(unittest.TestCase):
    """Unit tests for the FileInterface class."""

    def test_init_bad_path(self):
        """Initialise object."""
        odin_data_path = self.test_adapter.odin_data_path

        # Provoke KeyError
        options = {
            "directories":
                "odin_data   {}/".format(odin_data_path)
        }

        with self.assertRaises(KeyError):
            FileInterfaceAdapter(**options)

    def setUp(self):
        """Set up test fixture for each unit test."""
        self.test_adapter = AdapterTestFixture()

    # TODO Resolve Odin_control 1.4.0 & Python venv
    def test_adapter_get(self):
        """Test the adapter GET method returns the correct response."""
        expected_response = {
            'odin_version': '1.5.0'
        }
        response = self.test_adapter.adapter.get(self.test_adapter.path, self.test_adapter.request)
        print(response.data, type(response.data))
        print(response.data['odin_version'][:5])
        # assert response.data == expected_response
        assert response.data['odin_version'][:5] == expected_response['odin_version']
        assert response.status_code == 200

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
        with patch("logging.debug") as mock_log:
            mock_log.side_effect = ParameterTreeError()
            response = self.test_adapter.adapter.get(
                path,
                self.test_adapter.request)
            assert response.data == expected_response
            assert response.status_code == 400

    def test_adapter_put(self):
        """Test adapter handles valid PUT."""
        path = "odin_version"
        expected_response = {
            'odin_version': '1.1'
        }
        response = self.test_adapter.adapter.put(
            path,
            self.test_adapter.request_put)
        assert response.data == expected_response
        assert response.status_code == 200

    def test_adapter_put_file_interface_error(self):
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

    def test_adapter_put_request_syntax_error(self):
        """Test adapter handles invalid PUT containing request syntax error."""
        path = "odin_version"
        error_part1 = 'Failed to decode PUT request body:'
        error_part2 = "the JSON object must be str, bytes or bytearray, not NoneType"
        expected_response = {
            'error': "{} {}".format(error_part1, error_part2)
        }
        response = self.test_adapter.adapter.put(
            path,
            self.test_adapter.request_bad_put)
        assert response.data == expected_response
        assert response.status_code == 400

    def test_adapter_delete(self):
        """Test that adapter's DELETE function works."""
        expected_response = '{}: DELETE on path {}'.format("FileInterfaceAdapter",
                                                           self.test_adapter.path)
        response = self.test_adapter.adapter.delete(self.test_adapter.path,
                                                    self.test_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200

    def test_adapter_init(self):
        """Test function initialises adapter OK."""
        # Construct paths relative to current working directory
        odin_data_path = self.test_adapter.odin_data_path

        config_dir = "{}".format(odin_data_path)
        assert self.test_adapter.adp.odin_data_config_dir == config_dir

    def test_get_server_uptime(self):
        """Test function get server update okay."""
        start_time = self.test_adapter.adp.init_time
        up_time = self.test_adapter.adp.get_server_uptime()
        assert pytest.approx(up_time, rel=1) == time.time() - start_time

    def test_get_fr_config_files(self):
        """Test function returns fr config files."""
        self.test_adapter.adp.txt_files = ['fr_hexitec_config_0.json', 'fp_hexitec_config_0.json']
        self.test_adapter.adp.get_config_files = Mock()
        txt_files = ['fr_hexitec_config_0.json']
        rc = self.test_adapter.adp.get_fr_config_files()
        assert rc == txt_files
