"""EXCALIBUR detector implementation for the ODIN EXCALIBUR plugin.

Tim Nicholls, STFC Application Engineering
"""

import logging
import threading
from functools import partial
from tornado.concurrent import run_on_executor
from concurrent import futures

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from excalibur.fem import ExcaliburFem, ExcaliburFemError
from excalibur.parameter import *

class ExcaliburDetectorError(Exception):
    """Simple exception class for ExcaliburDetector."""

    pass
        
class ExcaliburDetectorFemConnection(object):
    """Internally used container class describing FEM connection."""

    STATE_DISCONNECTED = 0
    STATE_CONNECTED = 1
    STATE_ERROR = 2

    DEFAULT_DATA_ADDR = '10.0.2.1'
    DEFAULT_CHIP_ENABLE_MASK = 0xFF
    
    def __init__(self, fem_id, host_addr, port, data_addr=None, fem=None, state=STATE_DISCONNECTED):

        self.fem_id = fem_id
        self.host_addr = host_addr
        self.port = port
        self.data_addr = data_addr if data_addr is not None else self.DEFAULT_DATA_ADDR
        self.fem = fem
        self.chip_enable_mask = self.DEFAULT_CHIP_ENABLE_MASK
        self.chips_enabled = []
        
        self.state = self.STATE_DISCONNECTED
        self.error_code = FEM_RTN_OK
        self.error_msg = ""
        
        self.param_tree = ParameterTree({
            'id': (self._get('fem_id'), None),
            'address': (self._get('host_addr'), None),
            'port': (self._get('port'), None),
            'data_address': (self._get('data_addr'), None),
            'chip_enable_mask': (self._get('chip_enable_mask'), None),
            'chips_enabled': (self._get('chips_enabled'), None),
            'state': (self._get('state'), None),
            'error_code': (self._get('error_code'), None),
            'error_msg': (self._get("error_msg"), None),
        })

    def _get(self, attr):
        return lambda : getattr(self, attr)
    
class ExcaliburDetector(object):
    """EXCALIBUR detector class.

    This class implements the representation of an EXCALIBUR detector, providing the composition
    of one or more ExcaliburFem instances into a complete detector.
    """

    ALL_FEMS = 0
    ALL_CHIPS = 0
    def __init__(self, fem_connections):
        """Initialise the ExcaliburDetector object.

        :param fem_connections: list of (address, port) FEM connections to make
        """

        self.connected = False
        self.num_pending = 0   
        self.command_succeeded = True
        
        self.api_trace = False
        self.state_lock = threading.Lock()
        
        self.powercard_fem_idx = None
        self.chip_enable_mask = None
        
        self.fe_param_map = ExcaliburFrontEndParameterMap()
            
        self.fe_param_read = {
            'param': ['none'],
            'fem': -1,
            'chip': -1,
            'value': {},
        }
        self.fe_param_write = [{
            'param': 'none',
            'fem': -1,
            'chip': -1,
            'offset': 0,
            'value': [],
        }]
        
        self.fems = []
        if not isinstance(fem_connections, (list, tuple)):
            fem_connections = [fem_connections]
        if isinstance(fem_connections, tuple) and len(fem_connections) >= 2:
            fem_connections = [fem_connections]

        try:
            fem_id = 1
            for connection in fem_connections:
                (host_addr, port) = connection[:2]
                data_addr = connection[2] if len(connection) > 2 else None
                   
                self.fems.append(ExcaliburDetectorFemConnection(fem_id, host_addr, int(port), data_addr))
                fem_id += 1
        except Exception as e:
            raise ExcaliburDetectorError('Failed to initialise detector FEM list: {}'.format(e))

        self._fem_thread_pool = futures.ThreadPoolExecutor(max_workers = len(self.fems))
        
        self.fe_cmd_map = ExcaliburFrontEndCommandMap()
            
        cmd_tree = OrderedDict()
        cmd_tree['api_trace'] = (self._get('api_trace'), self.set_api_trace)
        cmd_tree['connect'] = (None, self.connect)
        cmd_tree.update(self.fe_cmd_map)
        for cmd in self.fe_cmd_map:
            cmd_tree[cmd] = (None, partial(self.do_command, cmd))
        cmd_tree['fe_param_read'] = (self._get('fe_param_read'), self.read_fe_param)
        cmd_tree['fe_param_write'] = (self._get('fe_param_write'), self.write_fe_param)

        self.param_tree = ParameterTree({
            'status' : {
                'connected': (self._get('connected'), None),
                'command_pending': (self.command_pending, None),
                'command_succeeded': (self._get('command_succeeded'), None),
                'num_pending': (self._get('num_pending'), None),
                'fem': [fem.param_tree for fem in self.fems],
                'powercard_fem_idx': (self._get('powercard_fem_idx'), None),
            },
            'command': cmd_tree, 
        })
    
    def set_powercard_fem_idx(self, idx):
        
        if idx < -1 or idx > len(self.fems):
            raise ExcaliburDetectorError('Illegal FEM index {} specified for power card'.format(idx))
        
        self.powercard_fem_idx = idx
    
    def set_chip_enable_mask(self, chip_enable_mask):
        
        if not isinstance(chip_enable_mask, (list, tuple)):
            chip_enable_mask = [chip_enable_mask]
            
        if len(chip_enable_mask) != len(self.fems):
            raise ExcaliburDetectorError('Mismatch in length of asic enable mask ({}) versus number of FEMS ({})'.format(
                len(chip_enable_mask), len(self.fems)
            ))
            
        for (fem_idx, mask) in enumerate(chip_enable_mask):
            self.fems[fem_idx].chip_enable_mask = mask
            for chip_idx in range(CHIPS_PER_FEM):
                if mask & (1<<(7 - chip_idx)):
                    self.fems[fem_idx].chips_enabled.append(chip_idx + 1)
                    
        self.chip_enable_mask = chip_enable_mask
                                                            
    def get(self, path):
        
        try:
            return self.param_tree.get(path)
        except ParameterTreeError as e:
            raise ExcaliburDetectorError(e)
    
    def set(self, path, data):
        
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise ExcaliburDetectorError(e)
        
    def _get(self, attr):
        
        return lambda : getattr(self, attr)
                             
    def _increment_pending(self):
        
        with self.state_lock:
            self.num_pending += 1

    def _decrement_pending(self, success):
        
        with self.state_lock:
            self.num_pending -= 1
            if not success:
                self.command_succeeded = False
        
    def _set_fem_error_state(self, fem_idx, error_code, error_msg):
        
        with self.state_lock:
            self.fems[fem_idx].error_code = error_code
            self.fems[fem_idx].error_msg = error_msg
            
    def command_pending(self):
        
        with self.state_lock:    
            command_pending = self.num_pending > 0
        
        return command_pending
    
    def set_api_trace(self, params):
        
        trace = False
        if 'enabled' in params:
            trace = params['enabled']

        self.command_succeeded = True        
        if not isinstance(trace, bool):
            raise ExcaliburDetectorError('api_trace requires a bool enabled parameter')
        
        if trace != self.api_trace:
            self.api_trace = bool(trace)
            for idx in range(len(self.fems)):
                self.fems[idx].fem.set_api_trace(trace)
                
    def connect(self, params):
        
        state = True
        if 'state' in params:
            state = params['state']
        
        self.command_succeeded = True
        self.connected = state

        """Establish connection to the detectors FEMs."""
        for idx in range(len(self.fems)):
            self._increment_pending()
            if state:
                self._connect_fem(idx)
            else:
                self._disconnect_fem(idx)


    @run_on_executor(executor='_fem_thread_pool')
    def _connect_fem(self, idx):
        
        connect_ok = True
        
        logging.debug('Connecting FEM {} at {}:{}, data_addr {}'.format(
            self.fems[idx].fem_id, self.fems[idx].host_addr, self.fems[idx].port, self.fems[idx].data_addr
        ))
        
        try:
            self.fems[idx].fem = ExcaliburFem(self.fems[idx].fem_id, self.fems[idx].host_addr, self.fems[idx].port, self.fems[idx].data_addr)
            self.fems[idx].state = ExcaliburDetectorFemConnection.STATE_CONNECTED
            logging.debug('Connected FEM {}'.format(self.fems[idx].fem_id))
        except ExcaliburFemError as e:
            self.fems[idx].state = ExcaliburDetectorFemConnection.STATE_ERROR
            logging.error('Failed to connect to FEM {} at {}:{}: {}'.format(
                self.fems[idx].fem_id, self.fems[idx].host_addr, self.fems[idx].port, str(e)
            ))
            connect_ok = False

        # Set up chip enables according to asic enable mask
        try:
            (param_id, _, _, _, _) = self.fe_param_map['medipix_chip_disable']
            for chip_idx in range(CHIPS_PER_FEM):
                chip_disable = 0 if chip_idx+1 in self.fems[idx].chips_enabled else 1
                rc = self.fems[idx].fem.set_int(chip_idx+1, param_id, chip_disable)
                if rc != FEM_RTN_OK:
                    self.fems[idx].error_msg = self.fems[idx].fem.get_error_msg()
                    logging.error('FEM {}: chip {} enable set returned error {}: {}'.format(
                        self.fems[idx].fem_id, rc, self.fems[idx].error_msg   
                    ))
        except Exception as e:
            self.fems[idx].error_code = FEM_RTN_INTERNALERROR
            self.fems[idx].error_msg = 'Unable to build chip enable list for FEM {}: {}'.format(idx, e)                                                                                    
            
        self._decrement_pending(connect_ok)
        
    @run_on_executor(executor='_fem_thread_pool')
    def _disconnect_fem(self, idx):
        
        disconnect_ok = True
        
        logging.debug("Disconnecting from FEM {}".format(
            self.fems[idx].fem_id
        ))
        
        try:
            self.fems[idx].fem.close()
        except ExcaliburFemError as e:
            logging.error("Failed to disconnect from FEM {}: {}".format(
              self.fems[idx].fem_id, str(e)  
            ))
            disconnect_ok = False
            
        self._decrement_pending(disconnect_ok)
 
    def _cmd(self, cmd_name):
        
        return partial(self.do_command, cmd_name)
    
    def _build_fem_idx_list(self, fem_ids):
        
        if not isinstance(fem_ids, list):
            fem_ids = [fem_ids]
        
        if fem_ids == [ExcaliburDetector.ALL_FEMS]:
            fem_idx_list = range(len(self.fems))
        else:
            fem_idx_list = [fem_id - 1 for fem_id in fem_ids]
        
        return fem_idx_list
            
    def do_command(self, cmd_name, params):

        logging.debug('{} called with params {}'.format(cmd_name, params))
        
        fem_idx_list = range(len(self.fems))
        chip_ids = [self.ALL_CHIPS]
        
        if params is not None:

            if 'fem' in params:
                fem_idx_list = self._build_fem_idx_list(params['fem'])

            if 'chip' in params:
                chip_ids = params['chip']
        
        self.command_succeeded = True
        
        for idx in fem_idx_list:
            self._increment_pending()
            self._do_command(idx, chip_ids, *self.fe_cmd_map[cmd_name])
        
    @run_on_executor(executor='_fem_thread_pool')
    def _do_command(self, fem_idx, chip_ids, cmd_id, cmd_text, param_err):
        
        logging.debug("FEM {} chip {}: {} command (id={}) in thread {:x}".format(
            self.fems[fem_idx].fem_id, chip_ids, cmd_text, cmd_id, threading.current_thread().ident
        ))

        self._set_fem_error_state(fem_idx, FEM_RTN_OK, '')
        cmd_ok =True
  
        for chip_id in chip_ids:
            try:
                rc = self.fems[fem_idx].fem.cmd(chip_id, cmd_id)
                if rc != FEM_RTN_OK:
                    self._set_fem_error_state(fem_idx, rc, self.fems[fem_idx].fem.get_error_msg())
                    logging.error("FEM {}: {} command returned error {}: {}".format(
                        self.fems[fem_idx].fem_id, cmd_text, rc, self.fems[fem_idx].error_msg
                    ))
                    cmd_ok = False
            except ExcaliburFemError as e:
                self._set_fem_error_state(fem_idx, param_err, str(e))
                logging.error("FEM {}: {} command raised exception: {}".format(
                    self.fems[fem_idx].fem_id, cmd_text, str(e)
                ))
                cmd_ok = False
  
        self._decrement_pending(cmd_ok)
                    
    def read_fe_param(self, attrs):

        logging.debug("In read_fe_param with attrs {} thread id {}".format(attrs, threading.current_thread().ident))

        self.command_succeeded = True        
        required_attrs = ('param', 'fem', 'chip')
        for attr in required_attrs:
            try:
                self.fe_param_read[attr] = attrs[attr]
            except KeyError:
                self.command_succeeded = False 
                raise ExcaliburDetectorError(
                    'Frontend parameter read command is missing {} attribute'.format(attr)
                )
     
        if isinstance(attrs['param'], list):
            params = attrs['param']
        else:
            params = [attrs['param']] 

        for param in params:
                        
            if param not in self.fe_param_map:
                self.command_succeeded = False 
                raise ExcaliburDetectorError(
                    'Frontend parameter read - illegal parameter name {}'.format(param))
        
        fem_idx_list = self._build_fem_idx_list(attrs['fem'])

        for param in params:
            self.fe_param_read['value'][param] = [[] for fem_idx in fem_idx_list]
        
        for (res_idx, fem_idx) in enumerate(fem_idx_list):
            self._increment_pending()
            self._read_fe_param(fem_idx, attrs['chip'], params, res_idx)
        
        logging.debug('read_fe_param returning')
        
    @run_on_executor(executor='_fem_thread_pool')
    def _read_fe_param(self, fem_idx, chips, params, res_idx):
        
        logging.debug("FEM {}: _read_fe_param in thread {:x}".format(self.fems[fem_idx].fem_id, threading.current_thread().ident))
        
        self._set_fem_error_state(fem_idx, FEM_RTN_OK, '')
        read_ok = True
        
        try:
            for param in params:
    
                (param_id, param_type, param_read_len, param_mode, param_access) = self.fe_param_map[param]
                
                try:
                    fem_get_method = getattr(self.fems[fem_idx].fem, 'get_' + param_type)
                    
                except AttributeError:
                    self._set_fem_error_state(fem_idx, FEM_RTN_INTERNALERROR,
                        'Read of frontend parameter {} failed: cannot resolve read method'.format(param))
                    read_ok = False
                    
                else:
                    if param_mode == ParamPerChip:
                        if chips == ExcaliburDetector.ALL_CHIPS:
                            chip_list = self.fems[fem_idx].chips_enabled
                        else:
                            chip_list = [chips]
                    else:
                        chip_list = [0]
    
                    values = []
                    for chip in chip_list:
                        (rc, value) = fem_get_method(chip, param_id, param_read_len)
                        if rc != FEM_RTN_OK:
                            self._set_fem_error_state(fem_idx, rc, self.fems[fem_idx].fem.get_error_msg())
        
                            value = [-1]
                            read_ok = False
                        
                        values.extend(value)
                        if not read_ok:
                            break
            
                    values = values[0] if len(values) == 1 else values
                    with self.state_lock:
                        self.fe_param_read['value'][param][res_idx] = values
        
        except Exception as e:
            self._set_fem_error_state(fem_idx, FEM_RTN_INTERNALERROR,
                'Read of frontend parameter {} failed: {}'.format(param, e))
            read_ok = False
                        
        if not read_ok:
                logging.error('FEM {}: {}'.format(
                    self.fems[fem_idx].fem_id, self.fems[fem_idx].error_msg
                ))
            
        self._decrement_pending(read_ok)
        
    def write_fe_param(self, params):
        
        logging.debug("In write_fe_param with params {:50.50} thread id {}".format(params, threading.current_thread().ident))

        self.command_succeeded = True        
        self.fe_param_write = []
        
        params_by_fem = []
            
        for fem_idx in range(len(self.fems)):
            params_by_fem.append([])
                       
        for idx in range(len(params)):

            param = params[idx]

            self.fe_param_write.append({})
                        
            required_attrs = ('param', 'fem', 'chip', 'value')
            for attr in required_attrs:
                try:
                    self.fe_param_write[idx][attr] = param[attr]
                except KeyError:
                    self.command_succeeded = False 
                    raise ExcaliburDetectorError(
                        'Frontend parameter write command is missing {} attribute'.format(attr)
                    )
            self.fe_param_write[idx]['offset'] = param['offset'] if 'offset' in param else 0
                
            if param['param'] not in self.fe_param_map:
                self.command_succeeded = False 
                raise ExcaliburDetectorError('Illegal parameter name {}'.format(param['param']))
        
            fem_idx_list = self._build_fem_idx_list(param['fem'])
            num_fems = len(fem_idx_list)     
            
            values = param['value']
            
            # If single-valued, expand outer level of values list to match length of number of FEMs
            if len(values) == 1:
                values = [values[0]] * num_fems 
            
            if len(values) != num_fems:
                self.command_succeeded = False 
                raise ExcaliburDetectorError(
                    'Mismatch in shape of frontend parameter {} values list of FEMs'.format(
                        param['param']
                    )
                )
            
            # Remap onto per-FEM list of expanded parameters
            for (idx, fem_idx) in enumerate(fem_idx_list):
            
                params_by_fem[fem_idx].append({
                    'param': param['param'],
                    'chip': param['chip'],
                    'offset': param['offset'] if 'offset' in param else 0,
                    'value': values[idx]
                })
                                
        # Execute write params for all specified FEMs (launched in threads)
        for fem_idx in fem_idx_list:
            self._increment_pending()
            self._write_fe_param(fem_idx, params_by_fem[fem_idx])
            
        logging.debug("write_fe_param returning")
        
    @run_on_executor(executor='_fem_thread_pool')
    def _write_fe_param(self, fem_idx, params):
        
        logging.debug("FEM {}: _write_fe_param in thread {:x}".format(self.fems[fem_idx].fem_id, threading.current_thread().ident))
        
        self._set_fem_error_state(fem_idx, FEM_RTN_OK, '')
        write_ok = True
        
        try:
            
            for param in params:
                
                param_name = param['param']
                (param_id, param_type, param_write_len, param_mode, param_access) = self.fe_param_map[param_name]
                
                try:
                    fem_set_method = getattr(self.fems[fem_idx].fem, "set_" + param_type)
                
                except AttributeError:
                    self._set_fem_error_state(fem_idx, FEM_RTN_INTERNALERROR, 
                        'Write of frontend parameter {} failed: cannot resolve write method {}'.format(param_name, 'set_' + param_type))
                    write_ok = False
                else:
                    
                    values = param['value']
                    
                    if param_mode == ParamPerFemRandomAccess and 'offset' in param:
                        offset = param['offset']
                    else:
                        offset = 0
                    
                    if param_mode == ParamPerChip:
                        chip_list = param['chip']
                        if not isinstance(chip_list, list):
                            chip_list = [chip_list]
                        if chip_list == [ExcaliburDetector.ALL_CHIPS]:
                            chip_list = self.fems[fem_idx].chips_enabled
                            
                        # If single-valued for a per-chip parameter, expand to match number of chips
                        if len(values) == 1:
                            values = [values[0]] * len(chip_list)

                        if len(values) != len(chip_list):
                            self._set_fem_error_state(fem_idx, FEM_RTN_INTERNALERROR,
                                'Write of frontend parameter {} failed: ' \
                                'mismatch between number of chips and values'.format(param_name))
                            write_ok = False
                            break

                    else:
                        chip_list = [0]
                    
                    for (idx, chip) in enumerate(chip_list):
                       
                        if isinstance(values[idx], list):
                            values_len = len(values[idx])
                        else:
                            values_len = 1
                        
                        if param_mode == ParamPerFemRandomAccess:
                            # TODO validate random access offset and size don't exceed param_write_len
                            pass
                        else:    
                            if values_len != param_write_len:
                                self._set_fem_error_state(fem_idx, FEM_RTN_INTERNALERROR, 
                                    'Write of frontend parameter {} failed: ' \
                                    'mismatch in number of values specified (got {} expected {})'.format(
                                        param_name, values_len, param_write_len
                                    ))
                                write_ok = False
                                break
                        
                        try:
                            rc = fem_set_method(chip, param_id, offset, values[idx])
                            if rc != FEM_RTN_OK:
                                self._set_fem_error_state(fem_idx, rc,self.fems[fem_idx].fem.get_error_msg())
                                write_ok = False
                                break

                        except ExcaliburFemError as e:
                            self._set_fem_error_state(fem_idx, FEM_RTN_INTERNALERROR, str(e))
                            write_ok = False
                            break
                 
                if not write_ok:
                    break
                    
        except Exception as e:
            self._set_fem_error_state(fem_idx, FEM_RTN_INTERNALERROR,
                'Write of frontend parameter {} failed: {}'.format(param, e))
            write_ok = False
        
        if not write_ok:
            logging.error(self.fems[fem_idx].error_msg)
              
        self._decrement_pending(write_ok)
        