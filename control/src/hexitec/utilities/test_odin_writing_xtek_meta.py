"""
Test writing xtek Meta data to h5

Christian Angelsen, STFC Detector Systems Software Group
"""

from datetime import datetime
from ast import literal_eval

import numpy as np
import h5py


def build_metadata_attributes(param_tree_dict):
    """Build metadata attributes from parameter tree."""
    error_code = 0
    save_dict_contents_to_group('/', param_tree_dict)
    return error_code


DATE_FORMAT = '%Y%m%d_%H%M%S'
fname = "/tmp/test_odin_{}.h5".format(datetime.now().strftime(DATE_FORMAT))
print("Going to write meta data to file: {}".format(fname))
hdf_file = h5py.File(fname, "w")


def save_dict_contents_to_group(path, dic):
    for key, item in dic.items():
        item = _convert_values(item)
        if isinstance(item, list):
            if isinstance(item[0], dict):
                newdict = {}
                for i in range(len(item)):
                    newdict[key + str(i)] = item[i]
                item = newdict
                save_dict_contents_to_group(path, {})
            else:
                # print(" D: {} => {}".format(key, item))
                if isinstance(item[0], str):
                    # Don't modify list of string(s)
                    pass
                else:
                    item = np.array(item)
        if isinstance(item, dict):
            save_dict_contents_to_group(path + key + '/', item)
        else:
            try:
                hdf_file[path + key] = item
            except (TypeError, ValueError) as e:
                print("  ***  (path + key] = item) => [{} + {}] = {}. Error: {}".format(path, key, item, e))

def _convert_values(value):
    # convert values to correct Python types
    if isinstance(value, list):
        value = [_convert_values(v) for v in value]
    elif isinstance(value, dict):
        for key, entry in value.items():
            value[key] = _convert_values(entry)
    try:
        val = literal_eval(value)
    except:
        val = value
    return str(val) if isinstance(val, type(None)) else val


if __name__ == "__main__":

    parent_tree_dict = {'xtek_meta': {'CTProfile': {'@xmlns:xsi': 'none', 'ManipulatorPosition': {'@Version': '2'}, 'CTAxisOffset': '0', 'XraySettings': {'kV': '140', 'uA': '70', 'FocusMode': 'autoDefocus'}, 'requiresPreprocessing': 'false', 'preprocessingType': '-1', 'XrayHead': 'Reflection 225', 'XrayHeadNumber': '0', 'ShadingCorrectionProfile': {'StandardCorrection': 'false', 'Frames': '60', 'PanelScan': 'false', 'PanelScanNumberImages': '1', 'ImagingConditions': {'@exposure': '354', '@accumulation': '0', '@binning': '1', '@gain': '1', '@brightness': '0', '@digitalGain': '0', '@WhiteToBlackLatency': '16000', '@BlackToWhiteLatency': '0', '@WhiteToWhiteLatency': '3000', '@lines': '1', 'transform': '1', 'imageOffsetX': '24', 'imageOffsetY': '24', 'imageSizeX': '4048', 'imageSizeY': '4048'}, 'IntensifierField': '0', 'GreyLevelTargets': {'Target': [{'kV': '0', 'uA': '0', 'XrayFilterMaterial': None, 'XrayFilterThickness': '0', 'GreyLevel': '165', 'PercentageWhiteLevel': '0'}, {'kV': '140', 'uA': '70', 'XrayFilterMaterial': 'Copper', 'XrayFilterThickness': '0.1', 'GreyLevel': '627', 'PercentageWhiteLevel': '100'}]}, 'WhiteTargetLevel': '60000', 'UsesMultipleXrayFilters': 'false', 'Mode': 'CT3D', 'TiltDegrees': '0'}}, 'Information': {'@xmlns:xsi': 'none', 'JobGuid': '392c51f4-48c1-49ae-a1a6-2998093e7bc1', 'Identifier': 'spl_1', 'Elements': {'Element': {'tag': 'Dataset name', 'value': 'spl_1'}}}, 'XTekCT': {'Name': 'spl_1', 'OperatorID': '', 'InputSeparator': '_', 'InputFolderName': '', 'OutputSeparator': '_', 'OutputFolderName': 'spl_1', 'VoxelsX': '2024', 'VoxelSizeX': '0.00494929', 'OffsetX': '0.00000006', 'VoxelsY': '2024', 'VoxelSizeY': '0.00494929', 'OffsetY': '0.0', 'VoxelsZ': '1660', 'VoxelSizeZ': '0.00494929', 'OffsetZ': '-0.16346376', 'SrcToObject': '24.918', 'SrcToDetector': '1006.932', 'MaskRadius': '4.78752535', 'DetectorPixelsX': '2024', 'DetectorPixelSizeX': '0.2', 'DetectorOffsetX': '0.0', 'DetectorPixelsY': '2024', 'DetectorPixelSizeY': '0.2', 'DetectorOffsetY': '0.0', 'RegionStartX': '0', 'RegionPixelsX': '2024', 'RegionStartY': '0', 'RegionPixelsY': '2024', 'Units': 'mm', 'Scaling': '1000.0', 'OutputUnits': '/m', 'OutputType': '3', 'ImportConversion': '1', 'AutoScalingType': '0', 'ScalingMinimum': '0.0', 'ScalingMaximum': '1000.0', 'LowPercentile': '0.2', 'HighPercentile': '99.8', 'Projections': '3179', 'InitialAngle': '0.0', 'AngularStep': '0.1132432', 'WhiteLevel': '60000', 'InterpolationType': '1', 'BeamHardeningLUTFile': '', 'CoefX4': '0.0', 'CoefX3': '0.0', 'CoefX2': '0.0', 'CoefX1': '1.0', 'CoefX0': '0.0', 'Scale': '1.0', 'FilterType': '0', 'CutOffFrequency': '2.5', 'Exponent': '1.0', 'Normalisation': '1.0', 'Scattering': '0.0', 'MedianFilterKernelSize': '1', 'ConvolutionKernelSize': '0', 'Increment': '1', 'ModifierID': '', 'InputName': 'spl_1', 'InputDigits': '4', 'OutputName': 'spl_1', 'OutputDigits': '4', 'VirtualDetectorPixelsX': '2024', 'VirtualDetectorPixelsY': '2024', 'VirtualDetectorPixelSizeX': '0.2', 'VirtualDetectorPixelSizeY': '0.2', 'VirtualDetectorOffsetX': '0.0', 'VirtualDetectorOffsetY': '0.0', 'SrcToVirtualDetector': '1006.932', 'AutomaticCentreOfRotation': '0', 'ObjectOffsetX': '-0.12539856', 'ObjectOffsetY': '0.0', 'ObjectTilt': '0.0', 'ObjectRoll': '0.0', 'Blanking': '0', 'OrderFFT': '13'}, 'Xrays': {'XraykV': '140', 'XrayuA': '70'}, 'DICOM': {'DICOMTags': '<?xml version="1.0" encoding="utf-16"?><ArrayOfMetaDataSchema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><MetaDataSchema xsi:type="MetaDataStringSchema"><Tag>Dataset name</Tag><Description>Dataset name</Description><Identifier>true</Identifier><DataValue>spl_1</DataValue><DicomTagGroup>0</DicomTagGroup><DicomTagElement>0</DicomTagElement></MetaDataSchema></ArrayOfMetaDataSchema>'}, 'CTPro': {'Version': 'V5.4.7289.18310 (Date:2019-12-16)', 'Product': '[XT 5.4][Copyright (c) 2004-2019 Nikon Metrology NV]', 'Filter_ThicknessMM': '0.1', 'Filter_Material': 'Copper', 'Shuttling': 'True', 'AutoCOR_NumBands': '1', 'CorAutoAccuracy': '2', 'SliceHeightMMSingle': '5.00868301', 'SliceHeightMMDualTop': '7.51302451', 'SliceHeightMMDualBottom': '2.5043415', 'AngleFile_Use': 'False', 'AngleFile_IgnoreErrors': 'True'}}, 'system_info': {'odin_version': '1.0.0', 'tornado_version': '6.1', 'python_version': '3.8.3', 'platform': {'system': 'Linux', 'node': 'te7aegdev07.te.rl.ac.uk', 'release': '3.10.0-1160.71.1.el7.x86_64', 'version': '#1 SMP Tue Jun 28 15:37:28 UTC 2022', 'processor': 'x86_64'}, 'server_uptime': 63.327951431274414}, 'detector': {'fem': {'diagnostics': {'acquire_start_time': '20220818_112417.742050', 'acquire_stop_time': '20220818_112417.843345', 'acquire_time': 0.101295}, 'offsets_timestamp': '20220818_112414.487694', 'hv_bias_enabled': False, 'debug': False, 'frame_rate': 7154.079227920547, 'health': True, 'status_message': 'Reopening file to add meta data..', 'status_error': '', 'number_frames': 10, 'duration': 1, 'duration_remaining': 0, 'hexitec_config': '/aeg_sw/work/users/ckd27546/develop/projects/hexitec/hexitec-detector/control/config/hexitec_unified_CSD__performance.ini', 'read_sensors': None, 'hardware_connected': True, 'hardware_busy': False, 'firmware_date': 'N/A', 'firmware_time': 'N/A', 'vsr1_sync': 15, 'vsr2_sync': 12, 'vsr1_sensors': {'ambient': 0, 'humidity': 0, 'asic1': 0, 'asic2': 0, 'adc': 0, 'hv': 0}, 'vsr2_sensors': {'ambient': 0, 'humidity': 0, 'asic1': 0, 'asic2': 0, 'adc': 0, 'hv': 0}}, 'daq': {'diagnostics': {'daq_start_time': '20220818_112417.658370', 'daq_stop_time': '20220818_112420.460854', 'fem_not_busy': '20220818_112418.958658'}, 'receiver': {'connected': [True], 'configured': [True], 'config_file': ['fr_hexitec_config_0.json', 'fr_hexitec_config_1.json', 'fr_hexitec_config_2.json']}, 'processor': {'connected': [True], 'configured': [True], 'config_file': ['fp_hexitec_config_0.json', 'fp_hexitec_config_1.json', 'fp_hexitec_config_2.json']}, 'file_info': {'enabled': False, 'file_name': 'reverted_conv_val_f', 'file_dir': '/tmp/'}, 'status': {'in_progress': True, 'daq_ready': False, 'frames_expected': 10, 'frames_received': 12, 'frames_processed': 10, 'processed_remaining': 0, 'received_remaining': -2}, 'config': {'addition': {'enable': False, 'pixel_grid_size': 3}, 'calibration': {'enable': False, 'gradients_filename': '/aeg_sw/work/users/ckd27546/develop/projects/hexitec/hexitec-detector/data/config/m_2018_01_001_400V_20C.txt', 'intercepts_filename': '/aeg_sw/work/users/ckd27546/develop/projects/hexitec/hexitec-detector/data/config/c_2018_01_001_400V_20C.txt'}, 'discrimination': {'enable': False, 'pixel_grid_size': 3}, 'histogram': {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10, 'max_frames_received': 10, 'pass_processed': True, 'pass_raw': True}, 'live_view': {'dataset_name': 'raw_frames', 'frame_frequency': 50, 'per_second': 0}, 'summed_image': {'threshold_lower': 0, 'threshold_upper': 4400, 'image_frequency': 1}, 'threshold': {'threshold_filename': '/aeg_sw/work/users/ckd27546/develop/projects/hexitec/hexitec-detector/data/config/thresh_2018_01_001_400V_20C.txt', 'threshold_mode': 'value', 'threshold_value': 120}}, 'compression_type': 'none', 'sensors_layout': '2x2'}, 'connect_hardware': None, 'initialise_hardware': None, 'disconnect_hardware': None, 'collect_offsets': None, 'commit_configuration': None, 'software_state': 'Idle', 'cold_initialisation': False, 'hv_on': None, 'hv_off': None, 'acquisition': {'number_frames': 10, 'duration': 1, 'duration_enable': False, 'start_acq': None, 'stop_acq': None}, 'status': {'system_health': True, 'status_message': 'Requested 10 frame(s), took 0.1 seconds', 'status_error': '', 'elog': '', 'fem_health': True, 'number_odin_instances': 1}}}

    # Build metadata attributes from dictionary
    rc = build_metadata_attributes(parent_tree_dict)
    print("rc: ", rc)
    hdf_file.close()
