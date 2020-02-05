"""
temp_file.py - Testing creating a temporary file to replace 12 Configuration files
"""

import tempfile
from collections import OrderedDict

def boolean_to_string(bBool):
	string = "false"
	if bBool:
		string = "true"
	return string

def threshold_settings(threshold):
    try:
        threshold_config = '''
                            "threshold_file": "%s",
                            "threshold_value": %s,
                            "threshold_mode": "%s",''' % (threshold['threshold_filename'], 
                                    threshold['threshold_value'], threshold['threshold_mode'])
    except KeyError:
        # logging.error("Error extracting threshold_settings!")
        print("Error extracting threshold_settings!")
        raise KeyError("Couldn't locate threshold setting(s)!")
    return threshold_config

def calibration_settings(calibration):
    try:
        calibration_config = '''
                            "gradients_file": "%s",
                            "intercepts_file": "%s",''' % (calibration['gradients_file'], 
                                                            calibration['intercepts_file'])
    except KeyError:
        # logging.error("Error extracting calibration_settings!")
        print("Error extracting calibration_settings!")
        raise KeyError("Couldn't locate calibration setting(s)!")
    return calibration_config

def histogram_settings(histogram):
    try:
        histogram_config = '''
                            "bin_start": %s,
                            "bin_end": %s,
                            "bin_width": %s,''' % (histogram['bin_start'],
                            histogram['bin_end'], histogram['bin_width'])
    except KeyError:
        # logging.error("Error extracting histogram_settings!")
        print("Error extracting histogram_settings!")
        raise KeyError("Couldn't locate histogram setting(s)!")
    return histogram_config


def main(param_tree):

    # ---------------- Section for the store sequence ---------------- #

    # Example 
    # param_tree = {'config': {'calibration': {'enable': False, 'intercepts_filename': '', 'gradients_filename': ''}, 'addition': {'enable': False, 'pixel_grid_size': 3}, 'discrimination': {'enable': False, 'pixel_grid_size': 3}, 'histogram': {'max_frames_received': 10, 'bin_end': 8000, 'bin_width': 10.0, 'bin_start': 0}, 'next_frame': {'enable': False}, 'threshold': {'threshold_value': 100, 'threshold_filename': '', 'threshold_mode': 'value'}, 'reorder': {'raw_data': False}}}



    store_sequence_preamble = '''
[
    {
        "store": 
        {
            "index": "temp", 
            "value":
            [
                {
                    "fr_setup": {
                        "fr_ready_cnxn": "tcp://127.0.0.1:5001",
                        "fr_release_cnxn": "tcp://127.0.0.1:5002"
                    }
                }'''

    plugin_template = '''
    '''

    # plugin path that follows the same format i.e. ("reorder", "Reorder", "Reorder")
    # "index": "reorder",
    # "name": "HexitecReorderPlugin",
    # "library": "/u/ckd27546/develop/projects/odin-demo/install/lib/libHexitecReorderPlugin.so"

    standard_path = {}
    standard_path['reorder']        = ["reorder", "Reorder", "Reorder"]
    standard_path['threshold']      = ["threshold", "Threshold", "Threshold"]
    standard_path['next_frame']     = ["next_frame", "NextFrame", "NextFrame"]
    standard_path["calibration"]    = ["calibration", "Calibration", "Calibration"]
    standard_path["addition"]       = ["addition", "Addition", "Addition"]
    standard_path["discrimination"] = ["discrimination", "Discrimination", "Discrimination"]
    standard_path["histogram"]      = ["histogram", "Histogram", "Histogram"]

    # Plugin path that doesn't follow the same format (as the others)
    # "index": "live_view",
    # "name": "LiveViewPlugin",
    # "library": "/u/ckd27546/develop/projects/odin-demo/install/lib/libLiveViewPlugin.so"
    # "index": "hdf",
    # "name": "FileWriterPlugin",
    # "library": "/u/ckd27546/develop/projects/odin-demo/install/lib/libHdf5Plugin.so"

    nonstandard_path = {}
    nonstandard_path["live_view"] = ["live_view", "LiveView", "LiveView"]
    nonstandard_path['hdf']       = ["hdf", "FileWriter", "Hdf5"]

    # Let's put together a sample chain of plugin paths

    # Sort parameter tree dict into R, T, N, C, A, D, H plugin order
    d = param_tree['config']
    keyorder = ['reorder', 'threshold',  'next_frame', 'calibration', 'addition', 'discrimination', 'histogram']
    od = OrderedDict(sorted(d.items(), key=lambda i:keyorder.index(i[0])))
    
    # config = dict(od)
    # USE ORDEREDDICT INSTEAD OF (BUILT-IN) DICT ! ??
    config = od


    # print("od.keys() ", od.keys())
    # for key in od.keys():
    #     # print("key, val: %s => %s" % (key, od[key]))
    #     config[key] = od[key]

    # config is now parameter
    print("od.keys() ", od.keys())
    print("config    ", config.keys())                  # wong too

    # Check parameter tree if next/calib/CS plugins to be added:

    list_optional_plugins = ["next_frame", "calibration", "addition", "discrimination"]
    sample_plugins = ["reorder", "threshold"]

    for key in config:
        if key not in list_optional_plugins:
            continue
        try:
            enabled = ""
            if config[key]['enable']:
                enabled = True
                sample_plugins.append(key)
            print("%s has 'enable' %s" % (key, enabled))
        except KeyError:
            # KeyError thrown if plugin doesn't have "enable" key
            pass #print("%s doesn't 'enable' ANYTHING" % key)

    sample_plugins += ["histogram", "live_view", "hdf"]
    
    # print(sample_plugins) # DEBUGGING INFO
    
    store_plugin_paths = ""
    for plugin in sample_plugins:
        # Build config for standard paths
        if plugin in standard_path:
            # print("Plug in: %s Exists!" % plugin)
            store_plugin_paths += ''',
                {
                    "plugin": {
                        "load": {
                            "index": "%s",
                            "name": "Hexitec%sPlugin",
                            "library": "/u/ckd27546/develop/projects/odin-demo/install/lib/libHexitec%sPlugin.so"
                        }
                    }
                }''' % (standard_path[plugin][0], standard_path[plugin][1], standard_path[plugin][2])

    for plugin in sample_plugins:
        # Build config for Non-standard paths
        if plugin in nonstandard_path:
            # print("Plug in: %s Exists!" % plugin)
            store_plugin_paths += ''',
                {
                    "plugin": {
                        "load": {
                            "index": "%s",
                            "name": "%sPlugin",
                            "library": "/u/ckd27546/develop/projects/odin-demo/install/lib/lib%sPlugin.so"
                        }
                    }
                }''' % (nonstandard_path[plugin][0], nonstandard_path[plugin][1], nonstandard_path[plugin][2])

    store_plugin_connect = ""
    previous_plugin = "frame_receiver"
    for plugin in sample_plugins:
        store_plugin_connect += ''',
                {
                    "plugin": {
                        "connect": {
                            "index": "%s",
                            "connection": "%s"
                        }
                    }
                }''' % (plugin, previous_plugin)
        previous_plugin = plugin
    
    # Setup plugin settings - only need to set up sensors_layout for each?
    store_plugin_config = ""
    unique_setting = ""
    for plugin in sample_plugins:
        # rinse and repeat for all except final two, unique plugins
        if plugin not in ["live_view", "hdf"]:

            # Get unique_setting(s) according to plugin
            if plugin == "reorder":
                unique_setting = '''\n                        "raw_data": %s,''' % \
                                                            config[plugin]['raw_data']
            if plugin == "threshold":
                unique_setting = threshold_settings(config[plugin])
            if plugin == "next_frame":
                pass # Nowt extra
            if plugin == "calibration":
                unique_setting = calibration_settings(config[plugin])
            if plugin == "discrimination" or plugin == "addition":
                unique_setting = '''\n                        "pixel_grid_size": %s,''' % \
                                                            config[plugin]['pixel_grid_size']
            if plugin == "histogram":
                unique_setting = histogram_settings(config[plugin])

            store_plugin_config += ''',
                {
                    "%s": {%s
            			"sensors_layout": "2x2"
                    }
                }''' % (plugin, unique_setting)
            unique_setting = ""

    # live_view, hdf have different settings (no sensors_layout..)
    store_plugin_config += ''',
                {
                    "live_view": 
                    {
                        "frame_frequency": 50,
                        "per_second": 0,
                        "live_view_socket_addr": "tcp://127.0.0.1:5020",
                        "dataset_name": "raw_frames"
                    }
                }'''

    store_plugin_config += ''',
                {
                    "hdf": 
                    {
                        "master": "data",
                        "dataset": 
                        {
                            "data" : 
                            {
                                "cmd": "create",
                                "datatype": "float",
                                "dims": [160, 160],
                                "chunks": [1, 160, 160],
                                "compression": "none"
                            },
                            "raw_frames" : 
                            {
                                "cmd": "create",
                                "datatype": "float",
                                "dims": [160, 160],
                                "chunks": [1, 160, 160],
                                "compression": "none"
                            },
                            "energy_bins" :
                            {
                                "cmd": "create",
                                "datatype": "float",
                                "dims": [800],
                                "chunks": [1, 800],
                                "compression": "none"
                            },
                            "pixel_histograms" :
                            {
                                "cmd": "create",
                                "datatype": "float",
                                "dims": [25600, 800],
                                "chunks": [1, 25600, 800],
                                "compression": "none"
                            },
                            "summed_histograms" :
                            {
                                "cmd": "create",
                                "datatype": "uint64",
                                "dims": [800],
                                "chunks": [1, 800],
                                "compression": "none"
                            }
                        }
                    }
                }'''
    store_plugin_config += ''',
                {
                    "hdf":
                    {
                        "file":
                        {
                            "path": "/data/hexitec/"
                        }
                    }
                }
            ]
        }
    }
]'''

    store_temp = tempfile.NamedTemporaryFile(mode='w+t')
    store_temp.delete = False

    # Put together the store sequence file
    try:
        print("Created file is:", store_temp)
        print("Name of the file is:", store_temp.name)
        # store_temp.writelines("[\n")
        # store_temp.writelines("   Hello?\n")
        # store_temp.writelines("]\n")


        store_temp.writelines(store_sequence_preamble)
        store_temp.writelines(store_plugin_paths)
        store_temp.writelines(store_plugin_connect)
        store_temp.writelines(store_plugin_config)
    finally:
        print("Closing store's temp file")
        store_temp.close()


#     # The execute_config file is used to wipe any existing config, then load user config
#     execute_config = '''
# [
#     {
#         "plugin": 
#         {
#             "disconnect": "all"
#         }
#     },
#     {
#         "execute": 
#         {
#             "index": "temp"
#         }
#     }
# ]'''

#     print("Creating execute config sequence, temporary file...")

#     execute_temp = tempfile.NamedTemporaryFile(mode='w+t')
#     execute_temp.delete = False


#     # Put together the execute sequence file 
#     try:
#         print("Execute config file:", execute_temp)
#         print("Name of the file is:", execute_temp.name)
#         execute_temp.writelines(execute_config)
#     finally:
#         print("Closing execute's temp file")
#         execute_temp.close()

if __name__ == '__main__':
    param_tree = {'config': {'calibration': {'enable': False, 
        'intercepts_filename': '/u/ckd27546/data/frameProcessor/c_2018_01_001_400V_20C.txt', 
        'gradients_filename': '/u/ckd27546/data/frameProcessor/m_2018_01_001_400V_20C.txt'}, 
        'addition': {'enable': True, 'pixel_grid_size': 5}, 'discrimination': {'enable': True, 'pixel_grid_size': 3}, 
        'histogram': {'max_frames_received': 109, 'bin_end': 8100, 'bin_width': 8, 'bin_start': 100}, 'next_frame': {'enable': True}, 
        'threshold': {'threshold_value': 7, 'threshold_filename': '/what/ever/', 'threshold_mode': 'filename'}, 'reorder': {'raw_data': True}}}

    main(param_tree)
