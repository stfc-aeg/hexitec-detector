import requests
import json
import pprint
import time
import logging
from collections import OrderedDict

class ExcaliburDefinitions(object):

    ERROR_OK = 0
    ERROR_FEM = 1
    ERROR_REQUEST = 2
    
    ALL_FEMS = 0
    ALL_CHIPS = 0
    
    FEM_PIXELS_PER_CHIP = 256 * 256
    
    FEM_TRIGMODE_INTERNAL = 0
    FEM_TRIGMODE_EXTERNAL = 1
    FEM_TRIGMODE_SYNC = 2
    FEM_TRIGMODE_NAMES = ('internal', 'external', 'extsync')
    
    FEM_READOUT_MODE_SEQUENTIAL = 0
    FEM_READOUT_MODE_CONTINUOUS = 1
    FEM_READOUT_MODE_NAMES = ('sequential', 'continuous')
    
    FEM_COLOUR_MODE_FINEPITCH = 0
    FEM_COLOUR_MODE_SPECTROSCOPIC = 1
    FEM_COLOUR_MODE_NAMES = ('fine pitch', 'spectroscopic')
    
    FEM_CSMSPM_MODE_SINGLE = 0
    FEM_CSMSPM_MODE_SUMMING = 1
    FEM_CSMSPM_MODE_NAMES = ('single pixel', 'charge summing')
    
    FEM_DISCCSMSPM_DISCL = 0
    FEM_DISCCSMSPM_DISCH = 1
    FEM_DISCCSMSPM_NAMES = ('DiscL', 'DiscH')
    
    FEM_EQUALIZATION_MODE_OFF = 0
    FEM_EQUALIZATION_MODE_ON = 1
    FEM_EQUALIZATION_MODE_NAMES = ('off', 'on')
    
    FEM_GAIN_MODE_SHGM = 0
    FEM_GAIN_MODE_HGM = 1
    FEM_GAIN_MODE_LGM = 2
    FEM_GAIN_MODE_SLGM = 3
    FEM_GAIN_MODE_NAMES = ('SHGM', 'HGM', 'LGM', 'SLGM')
    
    FEM_OPERATION_MODE_NORMAL = 0
    FEM_OPERATION_MODE_BURST = 1
    FEM_OPERATION_MODE_HISTOGRAM = 2
    FEM_OPERATION_MODE_DACSCAN = 3
    FEM_OPERATION_MODE_MAXTRIXREAD = 4
    FEM_OPERATION_MODE_NAMES = ('normal', 'burst', 'histogram', 'dac scan', 'matrix read')
    
    FEM_LFSR_BYPASS_MODE_DISABLED = 0
    FEM_LFSR_BYPASS_MODE_ENABLED = 1 
    FEM_LFSR_BYPASS_MODE_NAMES = ('disabled', 'enabled')
    
    FEM_COUNTER_DEPTH_MAP = {1: 0, 6: 1, 12: 2, 24: 3}
    
    @classmethod
    def _resolve_mode_name(cls, mode, names):  
        try:
            name = names[mode]
        except:
            name = 'unknown'
        return name 
    
    @classmethod
    def trigmode_name(cls, mode):
        return cls._resolve_mode_name(mode, cls.FEM_TRIGMODE_NAMES)
    
    @classmethod
    def readout_mode_name(cls, mode):
        return cls._resolve_mode_name(mode, cls.FEM_READOUT_MODE_NAMES)

    @classmethod
    def colour_mode_name(cls, mode):
        return cls._resolve_mode_name(mode, cls.FEM_COLOUR_MODE_NAMES)
        
    @classmethod
    def csmspm_mode_name(cls, mode):
        return cls._resolve_mode_name(mode, cls.FEM_CSMSPM_MODE_NAMES)

    @classmethod
    def disccsmspm_name(cls, mode):
        return cls._resolve_mode_name(mode, cls.FEM_DISCCSMSPM_NAMES)
    
    @classmethod
    def equalisation_mode_name(cls, mode):
        return cls._resolve_mode_name(mode, cls.FEM_EQUALIZATION_MODE_NAMES)

    @classmethod
    def gain_mode_name(cls, mode):
        return cls._resolve_mode_name(mode, cls.FEM_GAIN_MODE_NAMES)

    @classmethod
    def operation_mode_name(cls, mode):
        return cls._resolve_mode_name(mode, cls.FEM_OPERATION_MODE_NAMES)
    
    @classmethod
    def lfsr_bypass_mode_name(cls, mode):
        return cls._resolve_mode_name(mode, cls.FEM_LFSR_BYPASS_MODE_NAMES)
    
    @classmethod
    def counter_depth(cls, depth):
        return cls.FEM_COUNTER_DEPTH_MAP[depth] if depth in cls.FEM_COUNTER_DEPTH_MAP else -1

class ExcaliburParameter(OrderedDict):
    
    def __init__(self, param, value, fem=ExcaliburDefinitions.ALL_FEMS, 
                 chip=ExcaliburDefinitions.ALL_CHIPS, offset=None):
        
        super(ExcaliburParameter, self).__init__()
        self['param'] = param
        self['value'] = value
        self['fem'] = fem
        self['chip'] = chip
        if offset is not None:
            self['offset'] = offset 
        
    def get(self):
        
        if hasattr(self, 'offset'):
            ret_vals = (self.param, self.value, self.fem, self.chip, self.offset)
        else:
            ret_vals = (self.param, self.value, self.fem, self.chip) 
            
        return ret_vals

     
class ExcaliburClient(object):
        
    def __init__(self, address='localhost', port=8888, log_level=logging.INFO):
    
        self.url = 'http://{}:{}/api/0.1/excalibur/'.format(address, port)
        
        self.error_code = 0
        self.error_msg = ''
        
        self.cmd_completion_poll_interval = 0.2
        
        self.request_headers = {'Content-Type': 'application/json'}
        
        self.logger = logging.getLogger('ExcaliburClient')
        self.logger.setLevel(log_level)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        self._pp = pprint.PrettyPrinter()

    
    def json_print(self, response, log_level=logging.DEBUG):
        
        if isinstance(response, requests.models.Response):
            json_data = response.json()
        else:
            json_data = response
            
        self.logger.log(log_level, self._pp.pformat(json_data))
    
    def print_all(self, log_level=logging.DEBUG):
        
        response = requests.get(self.url, headers=self.request_headers)
        self.json_print(response, log_level)
            
    def exec_command(self, cmd, params=None):
        
        self.logger.debug('Executing command: {}'.format(cmd))

        payload = {cmd: params}
        response = requests.put(self.url + 'command', data=json.dumps(payload), headers=self.request_headers)
        
        succeeded = False
        
        if response.status_code == requests.codes.ok:
            
            while True:
                time.sleep(self.cmd_completion_poll_interval)
                response = requests.get(self.url + 'status')
                state = response.json()['status']

                if not state['command_pending']:
                    succeeded = state['command_succeeded']
                    if succeeded:
                        response = requests.get(self.url + 'command/' + cmd )
                    else:
                        self.logger.error('Command {} failed on following FEMS:'.format(cmd))
                        fem_error_count = 0
                        for (idx, fem_id, error_code, error_msg) in self.get_fem_error_state():
                            if error_code != 0:
                                self.logger.error('  FEM idx {} id {} : {} : {}'.format(idx, fem_id, error_code, error_msg))
                                fem_error_count += 1
                        self.error_code = ExcaliburDefinitions.ERROR_FEM
                        self.error_msg = 'Command {} failed on {} FEMs'.format(cmd, fem_error_count)
                    break
                
        else:
            self.error_code = ExcaliburDefinitions.ERROR_REQUEST
            if 'error' in response.json():
                self.error_msg = response.json()['error']
            else:
                self.error_msg = 'unknown error'
            
            self.error_msg = 'Command {} request failed with code {}: {}'.format(
                cmd, response.status_code, self.error_msg)
            
            self.logger.error(self.error_msg)
        
        return (succeeded, response.json())

    def get_param(self, path):
        
        param = path.split('/')[-1]
        response = requests.get(self.url + path)
        
        value = response.json()[param]
        
        return value

    def get_fem_chip_ids(self):
        
        status_fems = self.get_param('status/fem')
        
        fem_ids = [status_fem['id'] for status_fem in status_fems]
        chip_ids = [status_fem['chips_enabled'] for status_fem in status_fems]
        return (fem_ids, chip_ids)
        
    def get_fem_error_state(self):
        
        fem_state = self.get_param('status/fem')
        for (idx, state) in enumerate(fem_state):
            yield (idx, state['id'], state['error_code'], state['error_msg'])

    def get_powercard_fem_idx(self):

        powercard_fem_idx = self.get_param('status/powercard_fem_idx')
        return powercard_fem_idx

    def connect(self):
        
        connected = self.get_param('status/connected')
        if not connected:
            self.logger.info('Detector not connected, sending connect command')
            self.exec_command('connect', {'state': True})
        else:
            self.logger.info('Detector already connected')
            
    def disconnect(self):
        
        self.exec_command('connect', {'state': False})
        self.logger.info('Disconnected from detector')
        
    
    def set_api_trace(self, enabled):
        
        cmd = 'api_trace'
        cmd_params = {
            'enabled': enabled 
        }
        (succeeded, _) = self.exec_command(cmd, cmd_params)
        return succeeded
            
    def fe_init(self):
             
        self.logger.info('Initialising front-end')
        (init_ok, _) = self.exec_command('fe_init')
        if init_ok:
            self.logger.info('Front-end init completed OK')
        else:
            self.logger.error('Front-end init failed')

        return init_ok
    
    def fe_param_read(self, param, fem=ExcaliburDefinitions.ALL_FEMS, chip=ExcaliburDefinitions.ALL_CHIPS):
        
        cmd = 'fe_param_read'
            
        cmd_params = {
            'param': param,
            'fem': fem,
            'chip': chip
        }
        (succeeded, response) = self.exec_command(cmd, cmd_params)
        
        if succeeded:
            values = response[cmd]['value']
        else:
            values = []
            self.logger.error('Read of frontend parameter {} failed'.format(param))
            #self.json_print(response, logging.ERROR)
        
        return (succeeded, values)
    
    def fe_param_write(self, params):
           
        cmd = 'fe_param_write'
          
        if not isinstance(params, list):
            params = [params]
            
        (succeeded, _) = self.exec_command(cmd, params)
        
        if not succeeded:
            self.logger.error('Write of frontend parameter failed: {}'.format(self.error_msg))
            #self.json_print(response, logging.ERROR)
            
        return succeeded
    
    def do_command(self, cmd, fem=[ExcaliburDefinitions.ALL_FEMS], chip=[ExcaliburDefinitions.ALL_CHIPS]):
        
        cmd_params = {
            'fem': fem,
            'chip': chip
        }
        (succeeded, _) = self.exec_command(cmd, cmd_params) 
        return succeeded
