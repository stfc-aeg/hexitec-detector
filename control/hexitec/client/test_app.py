from excalibur.client import *
import logging
import argparse
import os
import time
import json
import sys

class ExcaliburTestAppDefaults(object):
    
    def __init__(self):
        
        self.ip_addr = 'localhost'
        self.port = 8888
        self.log_level = 'info'

        self.source_data_addr = ['10.1.0.100']
        self.source_data_mac = ['62:00:00:00:00:01']
        self.source_data_port = [8]
        self.dest_data_addr = ['10.1.0.1']
        self.dest_data_mac = ['00:07:43:10:63:00']
        self.dest_data_port = [61649]
        self.dest_data_port_offset = [0]
        self.farm_mode_enable = 0
        self.farm_mode_num_dests = 1
        
        self.log_levels = {
            'error': logging.ERROR,
            'warning': logging.WARNING,
            'info': logging.INFO,
            'debug': logging.DEBUG,
        }
             
        self.asic_readout_mode = 0
        self.asic_counter_select = 0
        self.asic_counter_depth = 2
        
        self.num_frames = 1
        self.acquisition_time = 100
        self.tp_count = 0
        self.trigger_mode = ExcaliburDefinitions.FEM_TRIGMODE_INTERNAL
        self.readout_mode = ExcaliburDefinitions.FEM_READOUT_MODE_SEQUENTIAL
        self.colour_mode = ExcaliburDefinitions.FEM_COLOUR_MODE_FINEPITCH
        self.csmspm_mode = ExcaliburDefinitions.FEM_CSMSPM_MODE_SINGLE
        self.disccsmspm = ExcaliburDefinitions.FEM_DISCCSMSPM_DISCL
        self.equalization_mode = ExcaliburDefinitions.FEM_EQUALIZATION_MODE_OFF
        self.gain_mode = ExcaliburDefinitions.FEM_GAIN_MODE_SLGM
        self.counter_select = 0
        self.counter_depth = 12
        self.operation_mode = ExcaliburDefinitions.FEM_OPERATION_MODE_NORMAL
        
        self.sense_dac = 0
        self.powercard_fem_id = 0
        
class CsvArgparseAction(argparse.Action):
    """
    Comma separated list of values action for argument parser.
    """
    def __init__(self, val_type=None, *args, **kwargs):
        self.val_type =val_type
        super(CsvArgparseAction, self).__init__(*args, **kwargs)
        
    def __call__(self, parser, namespace, value, option_string=None):
        item_list=[]
        try:
            for item_str in value.split(','):
                item_list.append(self.val_type(item_str))
        except ValueError as e:
            raise argparse.ArgumentError(self, e)
        setattr(namespace, self.dest, item_list)
        
class ExcaliburTestApp(object):
    
    def __init__(self):
        
        self.defaults = ExcaliburTestAppDefaults()
        
        try:
            term_columns = int(os.environ['COLUMNS']) - 2
        except:
            term_columns = 100
        
        parser = argparse.ArgumentParser(
            prog= os.path.basename(sys.argv[0]), description='EXCALIBUR test application',
            formatter_class=lambda prog : argparse.ArgumentDefaultsHelpFormatter(
                prog, max_help_position=40, width=term_columns)
        )
        
        config_group = parser.add_argument_group('Configuration')
        config_group.add_argument('--ipaddress', '-i', type=str, dest='ip_addr', 
            default=self.defaults.ip_addr, metavar='ADDR',
            help='Hostname or IP address of EXCALIBUR control server to connect to')
        config_group.add_argument('--port', '-p', type=int, dest='port',
            default=self.defaults.port, 
            help='Port number of EXCALIBUR control server to connect to')
        config_group.add_argument('--logging', type=str, dest='log_level',
            default=self.defaults.log_level,
            choices=['error', 'warning', 'info', 'debug'],
            help='Setting logging output level')
        config_group.add_argument('--trace', type=str, dest='api_trace',
            choices=['off', 'on'],
            help='Toggle API trace output (requires debug logging to be enabled on server)')
        
        cmd_group = parser.add_argument_group('Commands')
        cmd_group.add_argument('--dump', action='store_true',
            help='Dump the state of the control server')
        cmd_group.add_argument('--reset', '-r', action='store_true', 
            help='Issue front-end reset/init')
        cmd_group.add_argument('--lvenable', type=int, dest='lv_enable',
            choices=[0, 1], 
            help='Set power card LV enable: 0=off (default), 1=on')
        cmd_group.add_argument('--hvenable', type=int, dest='hv_enable',
            choices=[0, 1], 
            help='Set power card HV enable: 0=off (default), 1=on')
        cmd_group.add_argument('--hvbias', type=float, dest='hv_bias', metavar='VOLTS',
            help='Set power card HV bias in volts')
        cmd_group.add_argument('--efuse', '-e', action='store_true',
            help='Read and diplay MPX3 eFuse IDs')
        cmd_group.add_argument('--slow', '-s', action='store_true',
            help='Display front-end slow control parameters')
        cmd_group.add_argument('--pwrcard', action='store_true',
            help='Display power card status')
        cmd_group.add_argument('--acquire', '-a', action='store_true',
            help='Execute image acquisition sequence')
        cmd_group.add_argument('--dacscan', type=str, val_type=int, dest='dac_scan', 
           action=CsvArgparseAction, metavar='DAC,START,STOP_STEP',
           help='Execute DAC scan, params format is comma separated DAC,START,STOP,STEP')
        cmd_group.add_argument('--stop', action='store_true',
            help='Stop acquisition execution')
        cmd_group.add_argument('--disconnect', action='store_true',
            help='Disconnect server from detector system')
        cmd_group.add_argument('--dacs', nargs='*', metavar='FILE',
            help='Load MPX3 DAC values from a filename if given, otherwise use default values')
        cmd_group.add_argument('--config', action='store_true',
            help='Load MPX3 pixel configuration')
        cmd_group.add_argument('--udpconfig', nargs='?', metavar='FILE',
            default=None, const='-',
            help='Load 10GigE UDP data interface parameters from file, otherwise use default values')
        cmd_group.add_argument('--fwversion', action='store_true',
            help='Display firmware version information for connected FEMs')
        
        dataif_group = parser.add_argument_group('10GigE UDP data interface parameters')
        dataif_group.add_argument('--sourceaddr', metavar='IP', dest='source_data_addr',
            nargs='+', type=str, default=self.defaults.source_data_addr,
            help='Set the data source IP address(es)')
        dataif_group.add_argument('--sourcemac', metavar='MAC', dest='source_data_mac',
            nargs='+', type=str, default=self.defaults.source_data_mac,
            help='Set the data source MAC address(es)')
        dataif_group.add_argument('--sourceport', metavar='PORT', dest='source_data_port',
            nargs='+', type=int, default=self.defaults.source_data_port,
            help='Set the data source port(s)')
        dataif_group.add_argument('--destaddr', metavar='IP', dest='dest_data_addr',
            nargs='+', type=str, default=self.defaults.dest_data_addr,
            help='Set the data destination IP address(es)')
        dataif_group.add_argument('--destmac', metavar='MAC', dest='dest_data_mac',
            nargs='+', type=str, default=self.defaults.dest_data_mac,
            help='Set the data destination MAC address(es)')
        dataif_group.add_argument('--destport', metavar='PORT', dest='dest_data_port',
            nargs='+', type=int, default=self.defaults.dest_data_port,
            help='Set the data destination port(s)')
        dataif_group.add_argument('--destportoffset', metavar='OFFSET', dest='dest_data_port_offset',
            nargs='+', type=int, default=self.defaults.dest_data_port_offset,
            help='Set the FEM data destination port offset')
        dataif_group.add_argument('--farmenable', metavar='ENABLE', dest='farm_mode_enable',
            type=int, default=self.defaults.farm_mode_enable,
            help='Enable UDP farm mode')
        dataif_group.add_argument('--farmdests', metavar='NUM_DESTS', dest='farm_mode_num_dests',
            type=int, default=self.defaults.farm_mode_num_dests,
            help='Set the number of destination nodes in UDP farm mode')
        
        config_group = parser.add_argument_group('DAC and pixel configuration mode parameters')
        config_group.add_argument('--fem', metavar='FEM', dest='config_fem',
            nargs='+', type=int, default=[ExcaliburDefinitions.ALL_FEMS],
            help='Specify FEM(s) for configuration loading (0=all)')
        config_group.add_argument('--chip', metavar='CHIP', dest='config_chip',
            nargs='+', type=int, default=[ExcaliburDefinitions.ALL_CHIPS],
            help='Specified chip(s) for configuration loading (0=all)')
        config_group.add_argument('--sensedac', metavar='DAC', dest='sense_dac',
            type=int, default=self.defaults.sense_dac,
            help='Set MPX3 sense DAC id. NB Requires DAC load command to take effect')
        config_group.add_argument('--tpmask', type=str, 
            dest='pixel_test_file',  metavar='FILE',
            help='Specify MPX3 pixel test pulse mask configuration filename to load')
        config_group.add_argument('--pixelmask', type=str, 
            dest='pixel_mask_file', metavar='FILE',
            help='Specify MPX3 pixel test pulse mask configuration filename to load')
        config_group.add_argument('--discl', type=str, 
            dest='pixel_discl_file', metavar='FILE',
            help='Specify MPX3 pixel DiscL configuration filename to load')
        config_group.add_argument('--disch', type=str, 
            dest='pixel_disch_file', metavar='FILE',
            help='Specify MPX3 pixel DiscH configuration filename to load')
       
        acq_group = parser.add_argument_group('Acquisition parameters')
        acq_group.add_argument('--nowait', action='store_true', dest='no_wait',
            help='Do not wait for acqusition to complete before returning')
        acq_group.add_argument('--burst', action='store_true', dest='burst_mode',
            help='Select burst mode for image acquisition')
        acq_group.add_argument('--matrixread', action='store_true',
            help='During acquisition, perform matrix read only (i.e. no shutter for config read or digital test')
        acq_group.add_argument('--frames', '-n', type=int, dest='num_frames',
            default=self.defaults.num_frames, metavar='FRAMES',
            help='Set number of frames to acquire')
        acq_group.add_argument('--acqtime', '-t', type=int, dest='acquisition_time',
            default=self.defaults.acquisition_time, metavar='TIME',
            help='Set acquisition time (shutter duration) in ms')
        acq_group.add_argument('--readmode', type=int, dest='readout_mode',
            choices=[0,1],
            default=self.defaults.readout_mode,
            help='Set readout mode: 0=sequential, 1=continuous')
        acq_group.add_argument('--trigmode', type=int, dest='trigger_mode',
           choices = [0, 1, 2],
           default=self.defaults.trigger_mode,
           help='Set trigger mode: 0=internal, 1=external shutter, 2=external sync')
        acq_group.add_argument('--colourmode', type=int, dest='colour_mode',
            choices=[0, 1],
            default=self.defaults.colour_mode,
            help='Set MPX3 colour mode: 0=finepitch, 1=spectroscopic')
        acq_group.add_argument('--csmspm', type=int, dest='csmspm_mode',
            choices=[0, 1],
            default=self.defaults.csmspm_mode,
            help='Set MPX3 pixel mode: 0=single pixel, 1=charge summing')
        acq_group.add_argument('--disccsmspm', type=int, dest='disccsmspm',
            choices=[0, 1],
            default=self.defaults.disccsmspm,
            help='Set MPX3 discriminator output mode: 0=DiscL, 1=DiscH')
        acq_group.add_argument('--equalization', type=int, dest='equalization_mode',
            choices=[0, 1],
            default=self.defaults.equalization_mode,
            help='Set MPX3 equalization mode: 0=off, 1=on')
        acq_group.add_argument('--gainmode', type=int, dest='gain_mode',
            choices=[0, 1, 2, 3],
            default=self.defaults.gain_mode,
            help='Set MPX3 gain mode: 0=SHGM, 1=HGM, 2=LGM, 3=SLGM')
        acq_group.add_argument('--counter', type=int, dest='counter_select',
            choices=[0, 1],
            default=self.defaults.counter_select,
            help='Set MPX counter to read: 0 or 1')
        acq_group.add_argument('--depth', type=int, dest='counter_depth',
            choices=[1, 6, 12, 24],
            default=self.defaults.counter_depth,
            help='Set MPX counter bit depth: 1, 6, 12, or 24')
        acq_group.add_argument('--tpcount', type=int, dest='tp_count',
            default=self.defaults.tp_count, metavar='COUNT',
            help='Set MPX3 test pulse count')
        
        self.args = parser.parse_args()
        if self.args.log_level in self.defaults.log_levels:
            log_level = self.defaults.log_levels[self.args.log_level]
        else:
            log_level = self.defaults.log_levels[self.defaults.log_level]
            
        logging.basicConfig(level=log_level, format='%(levelname)1.1s %(asctime)s.%(msecs)03d %(message)s', datefmt='%y%m%d %H:%M:%S')
        self.client = ExcaliburClient(address=self.args.ip_addr, port=self.args.port, log_level=log_level)
        
    def run(self):
        
        if self.args.dump:
            logging.info('Dumping state of control server:')
            self.client.print_all(logging.INFO)
            return
        
        self.powercard_fem_id = self.client.get_powercard_fem_idx() + 1
        if self.powercard_fem_id > 0:
            logging.debug("Server reports power card is on FEM {}".format(self.powercard_fem_id))
        else:
            logging.debug("Server reports no power card present in system")

        self.client.connect()

        if self.args.api_trace:
            logging.debug('Setting API trace mode to {}'.format(self.args.api_trace))
            trace_enable = (self.args.api_trace == 'on')
            self.client.set_api_trace(trace_enable)
            

        (self.fem_ids, self.chip_ids) = self.client.get_fem_chip_ids()
        self.num_fems = len(self.fem_ids)
        logging.info('Detector has {} FEM{} with ID {}'.format(
            self.num_fems, ('' if self.num_fems == 1 else 's'), 
            ','.join([str(fem_id) for fem_id in self.fem_ids])
        ))
        
        if self.args.fwversion:
            self.do_fw_version_read()
                      
        if self.args.lv_enable is not None:
            self.do_lv_enable()

        if self.args.hv_enable:
            self.do_hv_enable()

        if self.args.hv_bias:
            self.do_hv_bias_set()

        if self.args.reset:
            self.do_frontend_init()
            
        if self.args.efuse:
            self.do_efuseid_read()
            
        if self.args.slow:
            self.do_slow_control_read()
        
        if self.args.pwrcard:
            self.do_powercard_read()
            
        if self.args.dacs is not None:
            self.do_dac_load()
         
        if self.args.config:
            self.do_pixel_config_load()
        
        if self.args.udpconfig:
            self.do_udp_config()

        if self.args.dac_scan:
            self.do_dac_scan()
            
        if self.args.acquire:
            self.do_acquisition()
            
        if self.args.stop:
            self.do_stop()
        
        if self.args.disconnect:    
            self.client.disconnect()
    
    def do_fw_version_read(self):
        
        (read_ok, response) = self.client.fe_param_read('firmware_version')
        if read_ok:
            firmware_versions = response['firmware_version']
            for fem_idx in range(len(firmware_versions)):
                logging.info('FEM {} firmware versions:'.format(fem_idx+1))
                logging.info('  Config SP3 : 0x{:08x}'.format(firmware_versions[fem_idx][0]))
                logging.info('  Top IO SP3 : 0x{:08x}'.format(firmware_versions[fem_idx][1]))
                logging.info('  Bot IO SP3 : 0x{:08x}'.format(firmware_versions[fem_idx][2]))
                logging.info('  Virtex5    : 0x{:08x}'.format(firmware_versions[fem_idx][3]))
                
        else:
            logging.error('Firmware version read failed')
       
       
    def do_lv_enable(self):

        if self.powercard_fem_id <= 0:
            logging.warning("Unable to set LV enable as server reports no power card")
            return
        
        params = []
        params.append(ExcaliburParameter('fe_lv_enable', [[self.args.lv_enable]], 
                      fem=self.powercard_fem_id))
                
        write_ok = self.client.fe_param_write(params)
        if not write_ok:
            logging.error('Failed to write LV enable parameter to system: {}'.format(self.client.error_msg))

    def do_hv_enable(self):

        if self.powercard_fem_id <= 0:
            logging.warning("Unable to set HV enable as server reports no power card")
            return
        
        params = []
        params.append(ExcaliburParameter('fe_hv_enable', [[self.args.hv_enable]], 
                      fem=self.powercard_fem_id))
                
        write_ok = self.client.fe_param_write(params)
        if not write_ok:
            logging.error('Failed to write HV enable parameter to system: {}'.format(self.client.error_msg))

    def do_hv_bias_set(self):

        if self.powercard_fem_id <= 0:
            logging.warning("Unable to set HV bias as server reports no power card")
            return
        
        params = []
        params.append(ExcaliburParameter('fe_hv_bias', [[self.args.hv_bias]], 
                      fem=self.powercard_fem_id))
                
        write_ok = self.client.fe_param_write(params)
        if not write_ok:
            logging.error('Failed to write HV bias parameter to system: {}'.format(self.client.error_msg))

    def do_frontend_init(self):
        
        params = []
        params.append(ExcaliburParameter('fe_vdd_enable', [[1]]))
        
        write_ok = self.client.fe_param_write(params)
        if not write_ok:
            logging.error('Failed to enable FE VDD on system: {}'.format(self.client.error_msg))
            
        self.client.fe_init()
        
    def do_efuseid_read(self):
        
        (read_ok, response) = self.client.fe_param_read('efuseid')
        if read_ok:
            efuse_ids = response['efuseid']          
            for fem_idx in range(len(efuse_ids)):
                fem_efuse_ids = efuse_ids[fem_idx]
                if not isinstance(fem_efuse_ids, list):
                    fem_efuse_ids = [fem_efuse_ids]
                logging.info('FEM {} : efuse IDs: {}'.format(fem_idx+1, ' '.join([hex(efuse_id) for efuse_id in fem_efuse_ids])))
        else:
            logging.error('eFuse ID read command failed')
    
    def do_slow_control_read(self):

        fem_params = ['fem_local_temp','fem_remote_temp', 'moly_temp', 'moly_humidity']
        supply_params = ['supply_p1v5_avdd1', 'supply_p1v5_avdd2', 'supply_p1v5_avdd3', 'supply_p1v5_avdd4', 
                     'supply_p1v5_vdd1', 'supply_p2v5_dvdd1']
      
        fe_params = fem_params + supply_params + ['mpx3_dac_out']
         
        (read_ok, param_vals) = self.client.fe_param_read(fe_params)

        if read_ok:
            for fem_idx in range(self.num_fems):
                logging.info('FEM {} : FPGA temp: {:.1f}C PCB temp: {:.1f}C FE temp: {:.1f}C FE humidity: {:.1f}%'.format(
                    fem_idx, param_vals['fem_remote_temp'][fem_idx], param_vals['fem_local_temp'][fem_idx],
                    param_vals['moly_temp'][fem_idx], param_vals['moly_humidity'][fem_idx]
                ))
                 
                supply_vals = ['ON' if val == 1 else 'OFF' for val in [param_vals[key][fem_idx] for key in supply_params]]
                 
                logging.info('FEM {} : Supply status: P1V5_AVDD: {}/{}/{}/{} P1V5_VDD1: {} P2V5_DVDD1: {}'.format(
                    fem_idx, *supply_vals
                ))
                 
                fe_dacs = ' '.join(['{}: {:.3f}V'.format(idx, val) for (idx, val) in enumerate(param_vals['mpx3_dac_out'][fem_idx])])
                 
                logging.info('FEM {} : Front-end DAC channels: {}'.format(fem_idx, fe_dacs))
        else:
            logging.error('Slow control read command failed')
    
    def do_powercard_read(self):
        
        if self.powercard_fem_id <= 0:
            logging.warning("Unable to set LV enable as server reports no power card")
            return
        
        status_params = [
            'pwr_coolant_temp_status', 'pwr_humidity_status',
            'pwr_coolant_flow_status', 'pwr_air_temp_status',
            'pwr_fan_fault'
        ]
        
        supply_params = [
            'pwr_p5va_vmon', 'pwr_p5vb_vmon', 
            'pwr_p5v_fem00_imon', 'pwr_p5v_fem01_imon', 'pwr_p5v_fem02_imon', 
            'pwr_p5v_fem03_imon', 'pwr_p5v_fem04_imon', 'pwr_p5v_fem05_imon',
            'pwr_p48v_vmon', 'pwr_p48v_imon', 
            'pwr_p5vsup_vmon', 'pwr_p5vsup_imon',
            'pwr_humidity_mon', 'pwr_air_temp_mon', 
            'pwr_coolant_temp_mon', 'pwr_coolant_flow_mon',
            'pwr_p3v3_imon', 'pwr_p1v8_imonA', 'pwr_bias_imon', 'pwr_p3v3_vmon',
            'pwr_p1v8_vmon', 'pwr_bias_vmon', 'pwr_p1v8_imonB', 'pwr_p1v8_vmonB'
        ]
        
        power_params = status_params + supply_params
        
        (read_ok, param_vals) = self.client.fe_param_read(
            power_params, fem=self.powercard_fem_id
        )
        
        if read_ok:
            logging.info("Power card parameters read OK:")
            for param in sorted(param_vals.iterkeys()):
                logging.info("   {} : {}".format(param, param_vals[param][0]))
        else:
            logging.error("Power card read command failed")
        
    def do_dac_load(self):

        try:
            fem_ids = self.args.config_fem
            if fem_ids == [ExcaliburDefinitions.ALL_FEMS]:
                fem_ids = self.fem_ids
            fem_idxs = [self.fem_ids.index(fem_id) for fem_id in fem_ids]
        except ValueError as e:
            logging.error('Error in FEM IDs specified for DAC loading: {}'.format(e))
            return
        
        self.dac_config = ExcaliburDacConfigParser(
            self.args.dacs, fem_ids, self.args.config_chip)
 
        dac_params = []
        
        for (dac_name, dac_param) in self.dac_config.dac_api_params():

            dac_vals = []
            for (fem_id, fem_idx) in zip(fem_ids, fem_idxs):
    
                chip_ids = self.args.config_chip
                if chip_ids == [ExcaliburDefinitions.ALL_CHIPS]:
                    chip_ids = self.chip_ids[fem_idx]
                try:                        
                    [self.chip_ids[fem_idx].index(chip_id) for chip_id in chip_ids]
                except ValueError as e:
                    logging.error('Error in FEM {} chip IDs specified for DAC loading: {}'.format(fem_id, e))
                    return
                
                fem_vals = [self.dac_config.dacs(fem_id, chip_id)[dac_name] for chip_id in chip_ids]
                dac_vals.append(fem_vals)
            
            dac_params.append(ExcaliburParameter(dac_param, dac_vals, 
                              fem=fem_ids, chip=chip_ids))
        
        dac_params.append(ExcaliburParameter('mpx3_dacsense', [[self.args.sense_dac]],
                          fem=fem_ids, chip=chip_ids))
        
        write_ok = self.client.fe_param_write(dac_params)
        if not write_ok:
            logging.error('Failed to write DAC parameters for FEM ID {}, chip ID {}'.format(fem_id, chip_id))
            return
        
        load_ok = self.client.do_command('load_dacconfig', fem=fem_ids, chip=chip_ids)
        if load_ok:
            logging.info('DAC load completed OK')
        else:
            logging.error('Failed to execute DAC load command: {}'.format(self.client.error_msg))
    
    def do_pixel_config_load(self):
        
        logging.info('Loading pixel configuration')
        
        mpx3_pixel_mask = [0] * ExcaliburDefinitions.FEM_PIXELS_PER_CHIP
        mpx3_pixel_discl = [0] * ExcaliburDefinitions.FEM_PIXELS_PER_CHIP
        mpx3_pixel_disch = [0] * ExcaliburDefinitions.FEM_PIXELS_PER_CHIP
        mpx3_pixel_test = [0] * ExcaliburDefinitions.FEM_PIXELS_PER_CHIP
        
        if self.args.pixel_mask_file:
            logging.info('  Loading pixel mask configuration from {}'.format(self.args.pixel_disch_file))
            mpx3_pixel_mask = ExcaliburPixelConfigParser(self.args.pixel_mask_file).pixels
        if self.args.pixel_discl_file:
            logging.info('  Loading pixel DiscL configuration from {}'.format(self.args.pixel_discl_file))
            mpx3_pixel_discl = ExcaliburPixelConfigParser(self.args.pixel_discl_file).pixels
        if self.args.pixel_disch_file:
            logging.info('  Loading pixel DiscH configuration from {}'.format(self.args.pixel_disch_file))
            mpx3_pixel_disch = ExcaliburPixelConfigParser(self.args.pixel_disch_file).pixels
        if self.args.pixel_test_file:
            logging.info('  Loading pixel test configuration from {}'.format(self.args.pixel_test_file))
            mpx3_pixel_test = ExcaliburPixelConfigParser(self.args.pixel_test_file).pixels
        
        pixel_params = []
        pixel_params.append(ExcaliburParameter('mpx3_pixel_mask', [[mpx3_pixel_mask]], 
                            fem=self.args.config_fem, chip=self.args.config_chip))
        pixel_params.append(ExcaliburParameter('mpx3_pixel_discl', [[mpx3_pixel_discl]], 
                            fem=self.args.config_fem, chip=self.args.config_chip))
        pixel_params.append(ExcaliburParameter('mpx3_pixel_disch', [[mpx3_pixel_disch]], 
                            fem=self.args.config_fem, chip=self.args.config_chip))
        pixel_params.append(ExcaliburParameter('mpx3_pixel_test', [[mpx3_pixel_test]], 
                            fem=self.args.config_fem, chip=self.args.config_chip))
        
        logging.info('  Writing pixel configuration to system')
        write_ok = self.client.fe_param_write(pixel_params)
        if not write_ok:
            logging.error('Failed to write pixel config parameters')
            return
        
        logging.info(('  Sending configuration load command to system'))
        load_ok = self.client.do_command('load_pixelconfig', self.args.config_fem, self.args.config_chip)
        if load_ok:
            logging.info('Pixel configuration load completed OK')
        else:
            logging.error('Failed to execute pixel config load command: {}'.format(self.client.error_msg))

    def do_udp_config(self):
        
        if self.args.udpconfig != '-':
            logging.info("Loading UDP configuration from file {}".format(self.args.udpconfig))
            
            try:
                with open(self.args.udpconfig) as config_file:
                    udp_config = json.load(config_file)
            except IOError as io_error:
                logging.error("Failed to open UDP configuration file: {}".format(io_error))
                return
            except ValueError as value_error:
                logging.error("Failed to parse UDP json config: {}".format(value_error))
                return
    
            source_data_addr = []
            source_data_mac = []
            source_data_port = []
            dest_data_port_offset = []
            
            for idx, fem in enumerate(udp_config['fems']):
                
                source_data_addr.append(fem['ipaddr'])
                source_data_mac.append(fem['mac'])
                source_data_port.append(fem['port'])
                dest_data_port_offset.append(fem['dest_port_offset']
                                                       )
                logging.debug('    FEM  {:d} : ip {:16s} mac: {:s} port: {:5d} offset: {:d}'.format(
                    idx, source_data_addr[-1], source_data_mac[-1], 
                    source_data_port[-1], dest_data_port_offset[-1]
                ))
                
            dest_data_addr = []
            dest_data_mac = []
            dest_data_port = []
            
            for idx, node in enumerate(udp_config['nodes']):
                
                dest_data_addr.append(node['ipaddr'])
                dest_data_mac.append(node['mac'])
                dest_data_port.append(int(node['port']))
                    
                logging.debug('    Node {:d} : ip {:16s} mac: {:s} port: {:5d}'.format(
                    idx, dest_data_addr[-1], dest_data_mac[-1],
                    dest_data_port[-1]
                ))
    
            farm_mode_enable = udp_config['farm_mode']['enable']
            farm_mode_num_dests = udp_config['farm_mode']['num_dests']
        
        else:
            
            logging.info("Using default UDP configuration")
            
            source_data_addr = self.args.source_data_addr
            source_data_mac = self.args.source_data_mac
            source_data_port = self.args.source_data_port
            dest_data_port_offset = self.args.dest_data_port_offset

            dest_data_addr = self.args.dest_data_addr
            dest_data_mac = self.args.dest_data_mac
            dest_data_port = self.args.dest_data_port
            
            farm_mode_enable = self.args.farm_mode_enable
            farm_mode_num_dests  = self.args.farm_mode_num_dests
            
        udp_params = []
        
        # Append per-FEM UDP source parameters, truncating to number of FEMs present in system
        udp_params.append(ExcaliburParameter(
            'source_data_addr', [[addr] for addr in source_data_addr[:self.num_fems]],
        ))
        udp_params.append(ExcaliburParameter(
            'source_data_mac', [[mac] for mac in source_data_mac[:self.num_fems]],
        ))
        udp_params.append(ExcaliburParameter(
            'source_data_port', [[port] for port in source_data_port[:self.num_fems]]
        ))
        udp_params.append(ExcaliburParameter(
            'dest_data_port_offset', 
            [[offset] for offset in dest_data_port_offset[:self.num_fems]]
        ))
          
        # Append the UDP destination parameters, noting [[[ ]]] indexing as they are common for
        # all FEMs and chips - there must be a better way to do this 
        udp_params.append(ExcaliburParameter(
            'dest_data_addr', [[[addr for addr in dest_data_addr]]]
        ))
        udp_params.append(ExcaliburParameter(
            'dest_data_mac', [[[mac for mac in dest_data_mac]]]
        ))
        udp_params.append(ExcaliburParameter(
            'dest_data_port', [[[port for port in dest_data_port]]]
        ))
          
        # Append the farm mode configuration parameters
        udp_params.append(ExcaliburParameter('farm_mode_enable', [[farm_mode_enable]]))
        udp_params.append(ExcaliburParameter('farm_mode_num_dests', [[farm_mode_num_dests]]))
  
        # Write all the parameters to system
        logging.info('Writing UDP configuration parameters to system')
        write_ok = self.client.fe_param_write(udp_params)
        if not write_ok:
            logging.error('Failed to write UDP configuration parameters to system: {}'.format(self.client.error_msg))
        
    def do_dac_scan(self):
        
        try:
            (scan_dac, scan_start, scan_stop, scan_step) = self.args.dac_scan
        except ValueError:
            logging.error("DAC scan requires four parameters (dac, start, stop, step)")
            return
        
        logging.info("Executing DAC scan ...")

        # Build a list of parameters to be written toset up the DAC scan
        scan_params = []
        
        logging.info('  Setting scan DAC to {}'.format(scan_dac))
        scan_params.append(ExcaliburParameter('dac_scan_dac', [[scan_dac]]))
        
        logging.info('  Setting scan start value to {}'.format(scan_start))
        scan_params.append(ExcaliburParameter('dac_scan_start', [[scan_start]]))
        
        logging.info('  Setting scan stop value to {}'.format(scan_stop))
        scan_params.append(ExcaliburParameter('dac_scan_stop', [[scan_stop]]))
        
        logging.info('  Setting scan step size to {}'.format(scan_step))
        scan_params.append(ExcaliburParameter('dac_scan_step', [[scan_step]]))
        
        logging.info('  Setting acquisition time to {} ms'.format(self.args.acquisition_time))
        scan_params.append(ExcaliburParameter('acquisition_time', [[self.args.acquisition_time]]))
        
        readout_mode = ExcaliburDefinitions.FEM_READOUT_MODE_SEQUENTIAL
        logging.info('  Setting ASIC readout mode to {}'.format(
            ExcaliburDefinitions.readout_mode_name(readout_mode)
        ))
        scan_params.append(ExcaliburParameter('mpx3_readwritemode', [[readout_mode]]))
        
        logging.info('  Setting ASIC colour mode to {} '.format(
            ExcaliburDefinitions.colour_mode_name(self.args.colour_mode)
        ))
        scan_params.append(ExcaliburParameter('mpx3_colourmode', [[self.args.colour_mode]]))

        logging.info('  Setting ASIC pixel mode to {} '.format(
            ExcaliburDefinitions.csmspm_mode_name(self.args.csmspm_mode)
        ))
        scan_params.append(ExcaliburParameter('mpx3_csmspmmode', [[self.args.csmspm_mode]]))

        logging.info('  Setting ASIC discriminator output mode to {} '.format(
            ExcaliburDefinitions.disccsmspm_name(self.args.disccsmspm)
        ))
        scan_params.append(ExcaliburParameter('mpx3_disccsmspm', [[self.args.disccsmspm]]))

        logging.info('  Setting ASIC equalization mode to {} '.format(
            ExcaliburDefinitions.equalisation_mode_name(self.args.equalization_mode)
        ))
        scan_params.append(ExcaliburParameter('mpx3_equalizationmode', [[self.args.equalization_mode]]))
        
        logging.info('  Setting ASIC gain mode to {} '.format(
            ExcaliburDefinitions.gain_mode_name(self.args.gain_mode)
        ))
        scan_params.append(ExcaliburParameter('mpx3_gainmode', [[self.args.gain_mode]]))

        logging.info('  Setting ASIC counter select to {} '.format(self.args.counter_select))
        scan_params.append(ExcaliburParameter('mpx3_counterselect', [[self.args.counter_select]]))
        
        counter_depth=12
        logging.info('  Setting ASIC counter depth to {} bits'.format(counter_depth))
        counter_depth_val = ExcaliburDefinitions.counter_depth(counter_depth)
        scan_params.append(ExcaliburParameter('mpx3_counterdepth', [[counter_depth_val]]))
        
        operation_mode = ExcaliburDefinitions.FEM_OPERATION_MODE_DACSCAN
        logging.info('  Setting operation mode to {}'.format(
            ExcaliburDefinitions.operation_mode_name(operation_mode)
        ))
        scan_params.append(ExcaliburParameter('mpx3_operationmode', [[operation_mode]]))

        lfsr_bypass_mode = ExcaliburDefinitions.FEM_LFSR_BYPASS_MODE_DISABLED
        logging.info('  Setting LFSR bypass mode to {}'.format(
            ExcaliburDefinitions.lfsr_bypass_mode_name(lfsr_bypass_mode)
        ))
        scan_params.append(ExcaliburParameter('mpx3_lfsrbypass', [[lfsr_bypass_mode]]))

        logging.info('  Disabling local data receiver thread')
        scan_params.append(ExcaliburParameter('datareceiver_enable', [[0]]))

        # Write all the parameters to system
        logging.info('Writing configuration parameters to system')
        write_ok = self.client.fe_param_write(scan_params)
        if not write_ok:
            logging.error('Failed to write configuration parameters to system: {}'.format(self.client.error_msg))
            return
        
        # Send start acquisition command
        logging.info('Sending start acquisition command')
        cmd_ok = self.client.do_command('start_acquisition')
        if not cmd_ok:
            logging.error('start_acquisition command failed: {}'.format(self.client.error_msg))
            return

        # If the nowait arguments wasn't given, monitor the scan state until all requested steps
        # have been completed
        if not self.args.no_wait:

            wait_count = 0
            scan_steps_completed = 0
            
            while True:

                (_, vals) = self.client.fe_param_read(['dac_scan_steps_complete', 'dac_scan_state'])
                scan_steps_completed = min(vals['dac_scan_steps_complete'])                
                scan_completed = all(
                    [(scan_state == 0) for scan_state in vals['dac_scan_state']]
                )
                
                if scan_completed:
                    break
                
                wait_count += 1
                if wait_count % 5 == 0:
                    logging.info('  {:d} scan steps completed  ...'.format(scan_steps_completed))


            (_, vals) = self.client.fe_param_read(['dac_scan_steps_complete'])
            scan_steps_completed = min(vals['dac_scan_steps_complete'])
                            
            self.do_stop()

            logging.info('DAC scan with {} steps completed'.format(scan_steps_completed))
        else:
            logging.info('Acquisition of DAC scan started, not waiting for completion, will not send stop command')


    def do_acquisition(self):
        
        # Resolve the acquisition operating mode appropriately, handling burst and matrix read if necessary
        operation_mode = self.defaults.operation_mode
        
        if self.args.burst_mode:
            operation_mode = ExcaliburDefinitions.FEM_OPERATION_MODE_BURST
        
        if self.args.matrixread:
            if self.args.burst_mode:
                logging.warning('Cannot select burst mode and matrix read simultaneously, ignoring burst option')
            operation_mode =  ExcaliburDefinitions.FEM_OPERATION_MODE_MAXTRIXREAD

        acq_loops = 1
        num_frames = self.args.num_frames
           
        # 24-bit reads are a special case, so set things up appropriately in this mode    
        if self.args.counter_depth == 24:

            # Force counter select to C1, C0 is read manually afterwards
            self.args.counter_select = 1 
        
            # For acquisitions with > 1 frame, run multiple acquisition loops instea
            acq_loops = num_frames
            num_frames = 1
            if acq_loops > 1:
                logging.info("Configuring 24-bit acquisition with {} 1-frame loops".format(acq_loops))
            
            # Disable no_wait mode if requested
            if self.args.no_wait:
                logging.info("Disabling no-wait mode for 24-bit acquisition")
                self.args.no_wait = False
                
            # In 24-bit mode, force a reset of the UDP frame counter before first acquisition loop
            logging.info('Resetting UDP frame counter for 24 bit mode')
            cmd_ok = self.client.do_command('reset_udp_counter')
            if not cmd_ok:
                logging.error("UDP counter reset failed: {}".format(self.client.error_msg))
                return

        # Build a list of parameters to be written to the system to set up acquisition
        write_params = []
                
        logging.info('  Setting test pulse count to {}'.format(self.args.tp_count))
        write_params.append(ExcaliburParameter('mpx3_numtestpulses', [[self.args.tp_count]]))
        tp_enable = 1 if self.args.tp_count != 0 else 0
        write_params.append(ExcaliburParameter('testpulse_enable', [[tp_enable]]))
        
        logging.info('  Setting number of frames to {}'.format(num_frames))
        write_params.append(ExcaliburParameter('num_frames_to_acquire', [[num_frames]]))
        
        logging.info('  Setting acquisition time to {} ms'.format(self.args.acquisition_time))
        write_params.append(ExcaliburParameter('acquisition_time', [[self.args.acquisition_time]]))
        
        logging.info('  Setting trigger mode to {}'.format(
            ExcaliburDefinitions.trigmode_name(self.args.trigger_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_externaltrigger', [[self.args.trigger_mode]]))
        
        logging.info('  Setting ASIC readout mode to {}'.format(
            ExcaliburDefinitions.readout_mode_name(self.args.readout_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_readwritemode', [[self.args.readout_mode]]))

        logging.info('  Setting ASIC colour mode to {} '.format(
            ExcaliburDefinitions.colour_mode_name(self.args.colour_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_colourmode', [[self.args.colour_mode]]))

        logging.info('  Setting ASIC pixel mode to {} '.format(
            ExcaliburDefinitions.csmspm_mode_name(self.args.csmspm_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_csmspmmode', [[self.args.csmspm_mode]]))

        logging.info('  Setting ASIC discriminator output mode to {} '.format(
            ExcaliburDefinitions.disccsmspm_name(self.args.disccsmspm)
        ))
        write_params.append(ExcaliburParameter('mpx3_disccsmspm', [[self.args.disccsmspm]]))

        logging.info('  Setting ASIC equalization mode to {} '.format(
            ExcaliburDefinitions.equalisation_mode_name(self.args.equalization_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_equalizationmode', [[self.args.equalization_mode]]))
        
        logging.info('  Setting ASIC gain mode to {} '.format(
            ExcaliburDefinitions.gain_mode_name(self.args.gain_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_gainmode', [[self.args.gain_mode]]))

        logging.info('  Setting ASIC counter select to {} '.format(self.args.counter_select))
        write_params.append(ExcaliburParameter('mpx3_counterselect', [[self.args.counter_select]]))
        
        logging.info('  Setting ASIC counter depth to {} bits'.format(self.args.counter_depth))
        counter_depth_val = ExcaliburDefinitions.counter_depth(self.args.counter_depth)
        write_params.append(ExcaliburParameter('mpx3_counterdepth', [[counter_depth_val]]))
        
        logging.info('  Setting operation mode to {}'.format(
            ExcaliburDefinitions.operation_mode_name(operation_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_operationmode', [[operation_mode]]))
        
        if self.args.matrixread:
            lfsr_bypass_mode = ExcaliburDefinitions.FEM_LFSR_BYPASS_MODE_ENABLED
        else:
            lfsr_bypass_mode = ExcaliburDefinitions.FEM_LFSR_BYPASS_MODE_DISABLED
        logging.info('  Setting LFSR bypass mode to {}'.format(
            ExcaliburDefinitions.lfsr_bypass_mode_name(lfsr_bypass_mode)
        ))
        write_params.append(ExcaliburParameter('mpx3_lfsrbypass', [[lfsr_bypass_mode]]))

        # Disable local receiver thread
        logging.info('  Disabling local data receiver thread')
        write_params.append(ExcaliburParameter('datareceiver_enable', [[0]]))
    
        for acq_loop in range(acq_loops):
        
            logging.info(
                'Executing acquisition loop {} of {}...'.format(acq_loop+1, acq_loops)
            )
            
            # Write all the parameters to system
            logging.info('Writing configuration parameters to system')
            write_ok = self.client.fe_param_write(write_params)
            if not write_ok:
                logging.error('Failed to write configuration parameters to system: {}'.format(self.client.error_msg))
                return

            # Send start acquisition command
            logging.info('Sending start acquisition command')
            cmd_ok = self.client.do_command('start_acquisition')
            if not cmd_ok:
                logging.error('start_acquisition command failed: {}'.format(self.client.error_msg))
                return
            
            # If the nowait arguments wasn't given, monitor the acquisition state until all requested frames
            # have been read out by the system
            if not self.args.no_wait:
    
                frames_acquired = self.await_acquistion_completion(0x40000000)
                
                if self.args.counter_depth == 24:
                    self.client.do_command('stop_acquisition')
                    self.do_c0_matrix_read()
                
                self.do_stop()
    
                logging.info('Acquistion of {} frame{} completed'.format(
                    frames_acquired, "s" if frames_acquired > 1 else ""
                ))
            else:
                logging.info('Acquisition started, not waiting for completion, will not send stop command')
        
        if acq_loops > 1:
            logging.info("Completed {} acquisition loops".format(acq_loops))
                
    def do_c0_matrix_read(self):

        logging.info('Performing a C0 matrix read for 24 bit mode')

        c0_read_params = []
        c0_read_params.append(ExcaliburParameter(
            'mpx3_operationmode', [[ExcaliburDefinitions.FEM_OPERATION_MODE_MAXTRIXREAD]]
        ))
        c0_read_params.append(ExcaliburParameter('mpx3_counterselect', [[0]]))
        c0_read_params.append(ExcaliburParameter('num_frames_to_acquire', [[1]]))
        c0_read_params.append(ExcaliburParameter('mpx3_lfsrbypass', [[0]]))
        
        logging.info("Sending configuration parameters for C0 matrix read")
        write_ok = self.client.fe_param_write(c0_read_params)
        if not write_ok:
            logging.error("Failed to write C0 matix read configuration parameters: {}".format(
                self.client.error_msg)
            )
            return
        
        logging.info("Sending matrix read acquisition command")
        cmd_ok = self.client.do_command('start_acquisition')
        if not cmd_ok:
            logging.error("start_acqusition command failed: {}".format(self.client.error_msg))
            return

        self.await_acquistion_completion(0x1f)
        # self.client.do_command('stop_acquisition')
    
    def await_acquistion_completion(self, acq_completion_state_mask):
        
        wait_count = 0
        frames_acquired = 0
                
        while True:
            
            (_, vals) = self.client.fe_param_read(['frames_acquired','control_state'])
            frames_acquired = min(vals['frames_acquired'])
            acq_completed = all(
                [((state & acq_completion_state_mask) == acq_completion_state_mask) for state in vals['control_state']]
            )
            if acq_completed:
                break
            
            wait_count += 1
            if wait_count % 5 == 0:
                logging.info('  {:d} frames read out  ...'.format(frames_acquired))
        
        return frames_acquired        

    def do_stop(self):
        
        logging.info('Sending stop acquisition command')
        self.client.do_command('stop_acquisition')
        
        
def main():
    
    ExcaliburTestApp().run()

if __name__ == '__main__':
    
    main()