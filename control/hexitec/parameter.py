'''
Created on Mar 21, 2017

@author: tcn45
'''

from collections import OrderedDict

from .fem_api_parameters import *
from fem_api_parameters import FEM_OP_DAC_SCAN_STEPS_COMPLETE

FEM_RTN_INTERNALERROR = -1
CHIPS_PER_FEM = FEM_CHIPS_PER_STRIPE_X
FEM_PIXELS_PER_CHIP = FEM_PIXELS_PER_CHIP_X * FEM_PIXELS_PER_CHIP_Y

ParamPerFem = 1
ParamPerFemRandomAccess = 2
ParamPerChip = 3

ParamReadOnly = 1
ParamReadWrite = 2

class ParameterSpec(object):
    
    def __init__(self, param_id, param_type, param_len, param_mode, param_access=ParamReadOnly):
        
        self.param_id = param_id
        self.param_type = param_type
        self.param_len = param_len
        self.param_mode = param_mode
        self.param_access = param_access
        
    def get(self):
        
        return (self.param_id, self.param_type, self.param_len, self.param_mode, self.param_access)
        
class ParameterMap(OrderedDict):
        
    def __init__(self, *args, **kwargs):
        
        super(ParameterMap, self).__init__()
        self.update(*args, **kwargs)
        
    def __getitem__(self, key):
        
        param_container = OrderedDict.__getitem__(self, key)
        return param_container.get()
    
    def __setitem__(self, key, arg): 
        
        if isinstance(arg, ParameterSpec):
            param_container = arg
        elif isinstance(arg, tuple):
            param_container = ParameterSpec(*arg)
        else:
            raise TypeError("Unable to set parameter map item with {}".format(type(arg)))
            
        OrderedDict.__setitem__(self, key, param_container)
    
class ExcaliburFrontEndParameterMap(ParameterMap):
     
    def __init__(self):

        super(ExcaliburFrontEndParameterMap, self).__init__()
        
        self['mpx3_colourmode'] = ParameterSpec(FEM_OP_MPXIII_COLOURMODE, 'int', 1, ParamPerFem)
        self['mpx3_counterdepth'] = ParameterSpec(FEM_OP_MPXIII_COUNTERDEPTH, 'int', 1, ParamPerFem)
        self['mpx3_externaltrigger'] = ParameterSpec(FEM_OP_MPXIII_EXTERNALTRIGGER, 'int', 1, ParamPerFem)
        self['mpx3_operationmode'] = ParameterSpec(FEM_OP_MPXIII_OPERATIONMODE, 'int', 1, ParamPerFem)
        self['mpx3_counterselect'] = ParameterSpec(FEM_OP_MPXIII_COUNTERSELECT, 'int', 1, ParamPerFem)
        self['mpx3_numtestpulses'] = ParameterSpec(FEM_OP_MPXIII_NUMTESTPULSES, 'int', 1, ParamPerFem)
        self['mpx3_readwritemode'] = ParameterSpec(FEM_OP_MPXIII_READWRITEMODE, 'int', 1, ParamPerFem)
        self['mpx3_disccsmspm'] = ParameterSpec(FEM_OP_MPXIII_DISCCSMSPM, 'int', 1, ParamPerFem)
        self['mpx3_equalizationmode'] = ParameterSpec(FEM_OP_MPXIII_EQUALIZATIONMODE, 'int', 1, ParamPerFem)
        self['mpx3_csmspmmode'] = ParameterSpec(FEM_OP_MPXIII_CSMSPMMODE, 'int', 1, ParamPerFem)
        self['mpx3_gainmode'] = ParameterSpec(FEM_OP_MPXIII_GAINMODE, 'int', 1, ParamPerFem)
        self['mpx3_triggerpolarity'] = ParameterSpec(FEM_OP_MPXIII_TRIGGERPOLARITY, 'int', 1, ParamPerFem)
        self['mpx3_lfsrbypass'] = ParameterSpec(FEM_OP_MPXIII_LFSRBYPASS, 'int', 1, ParamPerFem)
        
        self['mpx3_dacsense'] = ParameterSpec(FEM_OP_MPXIII_DACSENSE, 'int', 1, ParamPerChip)
        self['mpx3_dacexternal'] = ParameterSpec(FEM_OP_MPXIII_DACEXTERNAL, 'int', 1, ParamPerChip)
        self['mpx3_threshold0dac'] = ParameterSpec(FEM_OP_MPXIII_THRESHOLD0DAC, 'int', 1, ParamPerChip)
        self['mpx3_threshold1dac'] = ParameterSpec(FEM_OP_MPXIII_THRESHOLD1DAC, 'int', 1, ParamPerChip)
        self['mpx3_threshold2dac'] = ParameterSpec(FEM_OP_MPXIII_THRESHOLD2DAC, 'int', 1, ParamPerChip)
        self['mpx3_threshold3dac'] = ParameterSpec(FEM_OP_MPXIII_THRESHOLD3DAC, 'int', 1, ParamPerChip)
        self['mpx3_threshold4dac'] = ParameterSpec(FEM_OP_MPXIII_THRESHOLD4DAC, 'int', 1, ParamPerChip)
        self['mpx3_threshold5dac'] = ParameterSpec(FEM_OP_MPXIII_THRESHOLD5DAC, 'int', 1, ParamPerChip)
        self['mpx3_threshold6dac'] = ParameterSpec(FEM_OP_MPXIII_THRESHOLD6DAC, 'int', 1, ParamPerChip)
        self['mpx3_threshold7dac'] = ParameterSpec(FEM_OP_MPXIII_THRESHOLD7DAC, 'int', 1, ParamPerChip)
        self['mpx3_preampdac'] = ParameterSpec(FEM_OP_MPXIII_PREAMPDAC, 'int', 1, ParamPerChip)
        self['mpx3_ikrumdac'] = ParameterSpec(FEM_OP_MPXIII_IKRUMDAC, 'int', 1, ParamPerChip)
        self['mpx3_shaperdac'] = ParameterSpec(FEM_OP_MPXIII_SHAPERDAC, 'int', 1, ParamPerChip)
        self['mpx3_discdac'] = ParameterSpec(FEM_OP_MPXIII_DISCDAC, 'int', 1, ParamPerChip)
        self['mpx3_disclsdac'] = ParameterSpec(FEM_OP_MPXIII_DISCLSDAC, 'int', 1, ParamPerChip)
        self['mpx3_shapertestdac'] = ParameterSpec(FEM_OP_MPXIII_SHAPERTESTDAC, 'int', 1, ParamPerChip) 
        self['mpx3_discldac'] = ParameterSpec(FEM_OP_MPXIII_DISCLDAC, 'int', 1, ParamPerChip) 
        self['mpx3_delaydac'] = ParameterSpec(FEM_OP_MPXIII_DELAYDAC, 'int', 1, ParamPerChip)
        self['mpx3_tpbufferindac'] = ParameterSpec(FEM_OP_MPXIII_TPBUFFERINDAC, 'int', 1, ParamPerChip)
        self['mpx3_tpbufferoutdac'] = ParameterSpec(FEM_OP_MPXIII_TPBUFFEROUTDAC, 'int', 1, ParamPerChip)
        self['mpx3_rpzdac'] = ParameterSpec(FEM_OP_MPXIII_RPZDAC, 'int', 1, ParamPerChip)
        self['mpx3_gnddac'] = ParameterSpec(FEM_OP_MPXIII_GNDDAC, 'int', 1, ParamPerChip)
        self['mpx3_tprefdac'] = ParameterSpec(FEM_OP_MPXIII_TPREFDAC, 'int', 1, ParamPerChip)
        self['mpx3_fbkdac'] = ParameterSpec(FEM_OP_MPXIII_FBKDAC, 'int', 1, ParamPerChip)
        self['mpx3_casdac'] = ParameterSpec(FEM_OP_MPXIII_CASDAC, 'int', 1, ParamPerChip)
        self['mpx3_tprefadac'] = ParameterSpec(FEM_OP_MPXIII_TPREFADAC, 'int', 1, ParamPerChip)
        self['mpx3_tprefbdac'] = ParameterSpec(FEM_OP_MPXIII_TPREFBDAC, 'int', 1, ParamPerChip)
        self['mpx3_testdac'] = ParameterSpec(FEM_OP_MPXIII_TESTDAC, 'int', 1, ParamPerChip)
        self['mpx3_dischdac'] = ParameterSpec(FEM_OP_MPXIII_DISCHDAC, 'int', 1, ParamPerChip) 
        self['efuseid'] = ParameterSpec(FEM_OP_MPXIII_EFUSEID, 'int', 1, ParamPerChip)
        self['testpulse_enable'] = ParameterSpec(FEM_OP_MPXIII_TESTPULSE_ENABLE, 'int', 1, ParamPerChip)
        
        self['mpx3_pixel_mask'] = ParameterSpec(FEM_OP_MPXIII_PIXELMASK, 'short', FEM_PIXELS_PER_CHIP, ParamPerChip)
        self['mpx3_pixel_discl'] = ParameterSpec(FEM_OP_MPXIII_PIXELDISCL, 'short', FEM_PIXELS_PER_CHIP, ParamPerChip)
        self['mpx3_pixel_disch'] = ParameterSpec(FEM_OP_MPXIII_PIXELDISCH, 'short', FEM_PIXELS_PER_CHIP, ParamPerChip)
        self['mpx3_pixel_test'] = ParameterSpec(FEM_OP_MPXIII_PIXELTEST, 'short', FEM_PIXELS_PER_CHIP, ParamPerChip)
        
        self['num_frames_to_acquire'] = ParameterSpec(FEM_OP_NUMFRAMESTOACQUIRE, 'int', 1, ParamPerFem)
        self['acquisition_time'] = ParameterSpec(FEM_OP_ACQUISITIONTIME, 'int', 1, ParamPerFem)

        self['pwr_p5va_vmon'] = ParameterSpec(FEM_OP_P5V_A_VMON, 'float', 1, ParamPerFem) 
        self['pwr_p5vb_vmon'] = ParameterSpec(FEM_OP_P5V_B_VMON, 'float', 1, ParamPerFem) 
        self['pwr_p5v_fem00_imon'] = ParameterSpec(FEM_OP_P5V_FEMO0_IMON, 'float', 1, ParamPerFem) 
        self['pwr_p5v_fem01_imon'] = ParameterSpec(FEM_OP_P5V_FEMO1_IMON, 'float', 1, ParamPerFem) 
        self['pwr_p5v_fem02_imon'] = ParameterSpec(FEM_OP_P5V_FEMO2_IMON, 'float', 1, ParamPerFem) 
        self['pwr_p5v_fem03_imon'] = ParameterSpec(FEM_OP_P5V_FEMO3_IMON, 'float', 1, ParamPerFem) 
        self['pwr_p5v_fem04_imon'] = ParameterSpec(FEM_OP_P5V_FEMO4_IMON, 'float', 1, ParamPerFem) 
        self['pwr_p5v_fem05_imon'] = ParameterSpec(FEM_OP_P5V_FEMO5_IMON, 'float', 1, ParamPerFem) 
        self['pwr_p48v_vmon'] = ParameterSpec(FEM_OP_P48V_VMON, 'float', 1, ParamPerFem) 
        self['pwr_p48v_imon'] = ParameterSpec(FEM_OP_P48V_IMON, 'float', 1, ParamPerFem) 
        self['pwr_p5vsup_vmon'] = ParameterSpec(FEM_OP_P5VSUP_VMON, 'float', 1, ParamPerFem) 
        self['pwr_p5vsup_imon'] = ParameterSpec(FEM_OP_P5VSUP_IMON, 'float', 1, ParamPerFem) 
        self['pwr_humidity_mon'] = ParameterSpec(FEM_OP_HUMIDITY_MON, 'float', 1, ParamPerFem) 
        self['pwr_air_temp_mon'] = ParameterSpec(FEM_OP_AIR_TEMP_MON, 'float', 1, ParamPerFem) 
        self['pwr_coolant_temp_mon'] = ParameterSpec(FEM_OP_COOLANT_TEMP_MON, 'float', 1, ParamPerFem) 
        self['pwr_coolant_flow_mon'] = ParameterSpec(FEM_OP_COOLANT_FLOW_MON, 'float', 1, ParamPerFem) 
        self['pwr_p3v3_imon'] = ParameterSpec(FEM_OP_P3V3_IMON, 'float', 1, ParamPerFem) 
        self['pwr_p1v8_imonA'] = ParameterSpec(FEM_OP_P1V8_IMON_A, 'float', 1, ParamPerFem) 
        self['pwr_bias_imon'] = ParameterSpec(FEM_OP_BIAS_IMON, 'float', 1, ParamPerFem) 
        self['pwr_p3v3_vmon'] = ParameterSpec(FEM_OP_P3V3_VMON, 'float', 1, ParamPerFem) 
        self['pwr_p1v8_vmon'] = ParameterSpec(FEM_OP_P1V8_VMON_A, 'float', 1, ParamPerFem) 
        self['pwr_bias_vmon'] = ParameterSpec(FEM_OP_BIAS_VMON, 'float', 1, ParamPerFem) 
        self['pwr_p1v8_imonB'] = ParameterSpec(FEM_OP_P1V8_IMON_B, 'float', 1, ParamPerFem) 
        self['pwr_p1v8_vmonB'] = ParameterSpec(FEM_OP_P1V8_VMON_B, 'float', 1, ParamPerFem) 
        
        self['pwr_coolant_temp_status'] = ParameterSpec(FEM_OP_COOLANT_TEMP_STATUS, 'int', 1, ParamPerFem) 
        self['pwr_humidity_status'] = ParameterSpec(FEM_OP_HUMIDITY_STATUS, 'int', 1, ParamPerFem) 
        self['pwr_coolant_flow_status'] = ParameterSpec(FEM_OP_COOLANT_FLOW_STATUS, 'int', 1, ParamPerFem) 
        self['pwr_air_temp_status'] = ParameterSpec(FEM_OP_AIR_TEMP_STATUS, 'int', 1, ParamPerFem) 
        self['pwr_fan_fault'] = ParameterSpec(FEM_OP_FAN_FAULT, 'int', 1, ParamPerFem) 

        self['supply_p1v5_avdd1'] = ParameterSpec(FEM_OP_P1V5_AVDD_1_POK, 'int', 1, ParamPerFem)
        self['supply_p1v5_avdd2'] = ParameterSpec(FEM_OP_P1V5_AVDD_2_POK, 'int', 1, ParamPerFem)
        self['supply_p1v5_avdd3'] = ParameterSpec(FEM_OP_P1V5_AVDD_3_POK, 'int', 1, ParamPerFem)
        self['supply_p1v5_avdd4'] = ParameterSpec(FEM_OP_P1V5_AVDD_4_POK, 'int', 1, ParamPerFem)
        self['supply_p1v5_vdd1'] = ParameterSpec(FEM_OP_P1V5_VDD_1_POK, 'int', 1, ParamPerFem)
        self['supply_p2v5_dvdd1'] = ParameterSpec(FEM_OP_P2V5_DVDD_1_POK, 'int', 1, ParamPerFem)
        
        self['mpx3_dac_out'] = ParameterSpec(FEM_OP_DAC_OUT_FROM_MEDIPIX, 'float', 1, ParamPerChip)
        self['moly_temp'] = ParameterSpec(FEM_OP_MOLY_TEMPERATURE, 'float', 1, ParamPerFem)
        self['fem_local_temp'] = ParameterSpec(FEM_OP_LOCAL_TEMP, 'float', 1, ParamPerFem)
        self['fem_remote_temp'] = ParameterSpec(FEM_OP_REMOTE_DIODE_TEMP, 'float', 1, ParamPerFem)
        self['moly_humidity'] = ParameterSpec(FEM_OP_MOLY_HUMIDITY, 'float', 1, ParamPerFem)
        self['medipix_chip_disable'] = ParameterSpec(FEM_OP_MEDIPIX_CHIP_DISABLE, 'int', 1, ParamPerChip)
        
        self['dac_scan_dac'] = ParameterSpec(FEM_OP_SCAN_DAC, 'int', 1, ParamPerFem)
        self['dac_scan_start'] = ParameterSpec(FEM_OP_SCAN_START, 'int', 1, ParamPerFem)
        self['dac_scan_stop'] = ParameterSpec(FEM_OP_SCAN_STOP, 'int', 1, ParamPerFem)
        self['dac_scan_step'] = ParameterSpec(FEM_OP_SCAN_STEP, 'int', 1, ParamPerFem)
        
        self['dac_scan_steps_complete'] = ParameterSpec(FEM_OP_DAC_SCAN_STEPS_COMPLETE, 'int', 1, ParamPerFem)
        self['dac_scan_state'] = ParameterSpec(FEM_OP_DAC_SCAN_STATE, 'int', 1, ParamPerFem)
        
        self['fe_lv_enable'] = ParameterSpec(FEM_OP_LV_ON_OFF, 'int', 1, ParamPerFem)
        self['fe_hv_enable'] = ParameterSpec(FEM_OP_BIAS_ON_OFF, 'int', 1, ParamPerFem)
        self['fe_hv_bias'] = ParameterSpec(FEM_OP_BIAS_LEVEL, 'float', 1, ParamPerFem)
        self['fe_vdd_enable'] = ParameterSpec(FEM_OP_VDD_ON_OFF, 'int', 1, ParamPerFem)
               
        self['datareceiver_enable'] = ParameterSpec(FEM_OP_DATA_RECEIVER_ENABLE, 'int', 1 , ParamPerFem)
        self['frames_acquired'] = ParameterSpec(FEM_OP_FRAMES_ACQUIRED, 'int', 1 , ParamPerFem)
        self['control_state'] = ParameterSpec(FEM_OP_CONTROL_STATE, 'int', 1 , ParamPerFem)
        
        self['source_data_addr'] = ParameterSpec(FEM_OP_SOURCE_DATA_ADDR, 'string', FEM_FARM_MODE_LUT_SIZE, ParamPerFemRandomAccess)
        self['source_data_mac'] = ParameterSpec(FEM_OP_SOURCE_DATA_MAC, 'string', FEM_FARM_MODE_LUT_SIZE, ParamPerFemRandomAccess)
        self['source_data_port'] = ParameterSpec(FEM_OP_SOURCE_DATA_PORT, 'int', FEM_FARM_MODE_LUT_SIZE, ParamPerFemRandomAccess)
        self['dest_data_addr'] = ParameterSpec(FEM_OP_DEST_DATA_ADDR, 'string', FEM_FARM_MODE_LUT_SIZE, ParamPerFemRandomAccess)
        self['dest_data_mac'] = ParameterSpec(FEM_OP_DEST_DATA_MAC, 'string', FEM_FARM_MODE_LUT_SIZE, ParamPerFemRandomAccess)
        self['dest_data_port'] = ParameterSpec(FEM_OP_DEST_DATA_PORT, 'int', FEM_FARM_MODE_LUT_SIZE, ParamPerFemRandomAccess)
        self['dest_data_port_offset'] = ParameterSpec(FEM_OP_DEST_DATA_PORT_OFFSET, 'int', 1, ParamPerFem)
        self['farm_mode_num_dests'] = ParameterSpec(FEM_OP_FARM_MODE_NUM_DESTS, 'int', 1, ParamPerFem)
        self['farm_mode_enable'] = ParameterSpec(FEM_OP_FARM_MODE_ENABLE, 'int', 1, ParamPerFem)
        self['firmware_version'] = ParameterSpec(FEM_OP_FIRMWARE_VERSION, 'int', 4, ParamPerFem)
        
        
class ExcaliburFrontEndCommandMap(OrderedDict):
    
    def __init__(self):
        
        super(ExcaliburFrontEndCommandMap, self).__init__()
        
        self['fe_init'] = (FEM_OP_FEINIT, 'frontend initialisation', FEM_RTN_INITFAILED)
        self['start_acquisition'] = (FEM_OP_STARTACQUISITION, 'start acquisition', FEM_RTN_INTERNALERROR)
        self['stop_acquisition'] = (FEM_OP_STOPACQUISITION, 'stop acquisition', FEM_RTN_INTERNALERROR)
        self['load_pixelconfig'] = (FEM_OP_LOADPIXELCONFIG, 'pixel config load', FEM_RTN_INTERNALERROR)
        self['load_dacconfig'] = (FEM_OP_LOADDACCONFIG, 'DAC config load', FEM_RTN_INTERNALERROR)
        self['fem_reboot'] = (FEM_OP_REBOOT, 'FEM reboot', FEM_RTN_INTERNALERROR)
        self['reset_udp_counter'] = (FEM_OP_RESET_UDP_COUNTER, 'reset udp counter', FEM_RTN_INTERNALERROR)
