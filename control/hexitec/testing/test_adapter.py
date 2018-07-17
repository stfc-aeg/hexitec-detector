"""
test_adapter.py - test cases for the ExcaliburAdapter API adapter class for the ODIN server

Tim Nicholls, STFC Application Engineering Group
"""

import sys
import json
from nose.tools import *

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from excalibur.adapter import ExcaliburAdapter
from excalibur.detector import ExcaliburDetectorError

class ExcaliburAdapterFixture(object):

    @classmethod
    def setup_class(cls, **adapter_params):
        cls.adapter = ExcaliburAdapter(**adapter_params)
        cls.path = 'status/fem'
        cls.request = Mock()
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}


class TestExcaliburAdapter(ExcaliburAdapterFixture):

    @classmethod
    def setup_class(cls):

        adapter_params = {
            'detector_fems': '192.168.0.1:6969, 192.168.0.2:6969, 192.168.0.3:6969',
            'powercard_fem_idx': 0,
            'chip_enable_mask': '0xff, 0x3f, 0x7f'
        }
        super(TestExcaliburAdapter, cls).setup_class(**adapter_params)

    def test_adapter_name(self):

        assert_equal(self.adapter.name, 'ExcaliburAdapter')

    def test_adapter_single_fem(self):
        adapter_params = {'detector_fems': '192.168.0.1:6969'}
        adapter = ExcaliburAdapter(**adapter_params)
        assert_equal(len(adapter.detector.fems), 1)

    def test_adapter_bad_fem_config(self):
        adapter_params = {'detector_fems': '192.168.0.1 6969, 192.168.0.2:6969'}
        adapter = ExcaliburAdapter(**adapter_params)
        assert_equal(adapter.detector, None)

    def test_adapter_bad_powercard_idx(self):
        adapter_params = {
            'detector_fems': '192.168.0.1:6969, 192.168.0.2:6969',
            'powercard_fem_idx': 'nonsense'
        }
        adapter = ExcaliburAdapter(**adapter_params)
        assert_equal(adapter.detector.powercard_fem_idx, None)
        
    def test_adapter_bad_chip_mask(self):
        adapter_params = {
            'detector_fems': '192.168.0.1:6969, 192.168.0.2:6969',
            'chip_enable_mask': '0xff, 0x3f, 1.235',
        }
        adapter = ExcaliburAdapter(**adapter_params)
        assert_equal(adapter.detector.chip_enable_mask, None)
        
    def test_adapter_get(self):
        response = self.adapter.get(self.path, self.request)
        assert_true(isinstance(response.data, dict))
        assert_equal(response.status_code, 200)

    def test_adapter_get_raises_400(self):
        adapter_params = {
            'detector_fems': '192.168.0.1:6969, 192.168.0.2:6969',
            'chip_enable_mask': '0xff, 0x3f',
        }
        adapter = ExcaliburAdapter(**adapter_params)
        adapter.detector.get = Mock()
        adapter.detector.get.side_effect = ExcaliburDetectorError('detector error')
        response = adapter.get(self.path, self.request)
        assert_equal(response.status_code, 400)
        
    def test_adapter_put(self):     
        self.request.body = json.dumps({'connect': {'state': True}})
        put_path = 'command'
        response = self.adapter.put(put_path, self.request)
        assert_true(isinstance(response.data, dict))
        assert_equal(response.status_code, 200)
        
    def test_adapter_put_raises_400(self):
        adapter_params = {
            'detector_fems': '192.168.0.1:6969, 192.168.0.2:6969',
            'chip_enable_mask': '0xff, 0x3f',
        }
        adapter = ExcaliburAdapter(**adapter_params)
        adapter.detector.put = Mock()
        adapter.detector.put.side_effect = ExcaliburDetectorError('detector error')
        response = adapter.put(self.path, self.request)
        assert_equal(response.status_code, 400)

    def test_adapter_bad_path(self):
        response = self.adapter.put('bad_path', self.request)
        assert_equal(response.status_code, 400)

    def test_adapter_delete(self):
        expected_response = {
            'response': '{}: DELETE on path {}'.format(self.adapter.name, self.path)
        }
        response = self.adapter.delete(self.path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 200)


class TestExcaliburAdapterNoFems(ExcaliburAdapterFixture):

    @classmethod
    def setup_class(cls):
        super(TestExcaliburAdapterNoFems, cls).setup_class()

    def test_adapter_no_fems(self):
        assert_equal(self.adapter.detector, None)

    def test_adapter_no_fems_get(self):
        response = self.adapter.get(self.path, self.request)
        assert_equal(response.status_code, 500)
