#from excalibur import fem_api
#import excalibur.fem_api_stub as fem_api
import importlib
import logging

class ExcaliburFemError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ExcaliburFem(object):

    use_stub_api = False
    api_stem = 'excalibur.fem_api'
    _fem_api = None

    def __init__(self, fem_id, fem_address, fem_port, data_address):

        self.fem_handle = None

        if ExcaliburFem._fem_api is None:
            api_module = ExcaliburFem.api_stem
            if ExcaliburFem.use_stub_api:
                api_module = api_module + '_stub'

            try:
                ExcaliburFem._fem_api = importlib.import_module(api_module)
            except ImportError as e:
                raise ExcaliburFemError('Failed to load API module: {}'.format(e))
            else:
                self._fem_api = ExcaliburFem._fem_api

        try:
            self.fem_handle = self._fem_api.initialise(
                fem_id, fem_address, fem_port, data_address
            )
            
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

    def close(self):

        try:
            self._fem_api.close(self.fem_handle)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))
        
    def set_api_trace(self, trace):
        
        try:
            self._fem_api.set_api_trace(self.fem_handle, int(trace))
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

    def get_id(self):

        try:
            fem_id = self._fem_api.get_id(self.fem_handle)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return fem_id

    def get_int(self, chip_id, param_id, size):

        try:
            (rc, values) = self._fem_api.get_int(self.fem_handle, chip_id, param_id, size)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return (rc, values)

    def set_int(self, chip_id, param_id, offset, values):

        try:
            rc = self._fem_api.set_int(self.fem_handle, chip_id, param_id, offset, values)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return rc
 
    def get_short(self, chip_id, param_id, size):

        try:
            (rc, values) = self._fem_api.get_short(self.fem_handle, chip_id, param_id, size)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return (rc, values)

    def set_short(self, chip_id, param_id, offset, values):

        try:
            rc = self._fem_api.set_short(self.fem_handle, chip_id, param_id, offset, values)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return rc
       
    def get_float(self, chip_id, param_id, size):
        
        try:
            (rc, values) = self._fem_api.get_float(self.fem_handle, chip_id, param_id, size)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))
        except Exception as e:
            raise ExcaliburFemError(e)
        
        return (rc, values)

    def set_float(self, chip_id, param_id, offset, values):

        try:
            rc = self._fem_api.set_float(self.fem_handle, chip_id, param_id, offset, values)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return rc

    def set_string(self, chip_id, param_id, offset, values):

        try:
            rc = self._fem_api.set_string(self.fem_handle, chip_id, param_id, offset, values)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return rc
    
    def cmd(self, chip_id, cmd_id):

        try:
            rc = self._fem_api.cmd(self.fem_handle, chip_id, cmd_id)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return rc

    def get_error_msg(self):
        
        try:
            error_msg = self._fem_api.get_error_msg(self.fem_handle)
        except self._fem_api_error as e:
            raise ExcaliburFemError(str(e))

        return error_msg