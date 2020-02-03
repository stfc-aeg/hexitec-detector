"""
temp_file.py - Testing creating a temporary file to replace 12 Configuration files
"""

import tempfile

def main():


    # ---------------- Section for the store sequence ---------------- #

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
    sample_plugins = ["reorder", "threshold", "histogram", "live_view", "hdf"]
    # print(sample_plugins)
    
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
    for plugin in sample_plugins:
        if plugin not in ["live_view", "hdf"]:
            store_plugin_config = ''',
                {
                    "%s": {
            			"sensors_layout": "2x2"
                    }
                }''' % plugin

    # hdf  template can be hardcoded:
#     hdf_template = ''',
#                 {
#                     "hdf": 
#                     {
#                         "master": "data",
#                         "dataset": 
#                         {
#                             "data" : 
#                             {
#                                 "cmd": "create",
#                                 "datatype": "float",
#                                 "dims": [160, 160],
#                                 "chunks": [1, 160, 160],
#                                 "compression": "none"
#                             },
#                             "raw_frames" : 
#                             {
#                                 "cmd": "create",
#                                 "datatype": "float",
#                                 "dims": [160, 160],
#                                 "chunks": [1, 160, 160],
#                                 "compression": "none"
#                             },
#                             "energy_bins" :
#                             {
#                                 "cmd": "create",
#                                 "datatype": "float",
#                                 "dims": [800],
#                                 "chunks": [1, 800],
#                                 "compression": "none"
#                             },
#                             "pixel_histograms" :
#                             {
#                                 "cmd": "create",
#                                 "datatype": "float",
#                                 "dims": [25600, 800],
#                                 "chunks": [1, 25600, 800],
#                                 "compression": "none"
#                             },
#                             "summed_histograms" :
#                             {
#                                 "cmd": "create",
#                                 "datatype": "uint64",
#                                 "dims": [800],
#                                 "chunks": [1, 800],
#                                 "compression": "none"
#                             }
#                         }
#                     }
#                 },                
# '''
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
#             "index": "config"
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
    main()
