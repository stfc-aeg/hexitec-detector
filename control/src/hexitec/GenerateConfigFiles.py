"""
GenerateConfigFiles.py - Creates a temporary file according to user UI selections 
                        (to replace 12 Configuration files)
"""

import tempfile
import logging
from collections import OrderedDict

class GenerateConfigFiles():
    """
    Accepts Parameter tree from hexitecDAQ's "/config" branch to generate json file
    """

    def __init__(self, param_tree, number_histograms, 
                bDeleteFileOnClose=False, master_dataset="data", extra_datasets=[]):

        self.param_tree = param_tree
        self.number_histograms = number_histograms
        self.delete_file_on_close = bDeleteFileOnClose
        self.master_dataset = master_dataset
        self.extra_datasets = extra_datasets

    def boolean_to_string(self, bBool):
        string = "false"
        if bBool:
            string = "true"
        return string

    def threshold_settings(self, threshold):
        try:
            threshold_config = '''
                        "threshold_file": "%s",
                        "threshold_value": %s,
                        "threshold_mode": "%s",''' % (threshold['threshold_filename'], 
                                threshold['threshold_value'], threshold['threshold_mode'])
        except KeyError:
            logging.error("Error extracting threshold_settings!")
            print("Error extracting threshold_settings!")
            raise KeyError("Couldn't locate threshold setting(s)!")
        return threshold_config

    def calibration_settings(self, calibration):
        try:
            calibration_config = '''
                        "gradients_file": "%s",
                        "intercepts_file": "%s",''' % (calibration['gradients_filename'], 
                                                    calibration['intercepts_filename'])
        except KeyError:
            logging.error("Error extracting calibration_settings!")
            print("Error extracting calibration_settings!")
            raise KeyError("Couldn't locate calibration setting(s)!")
        return calibration_config

    def histogram_settings(self, histogram):
        try:
            histogram_config = '''
                        "bin_start": %s,
                        "bin_end": %s,
                        "bin_width": %s,''' % (histogram['bin_start'],
                        histogram['bin_end'], histogram['bin_width'])
        except KeyError:
            logging.error("Error extracting histogram_settings!")
            print("Error extracting histogram_settings!")
            raise KeyError("Couldn't locate histogram setting(s)!")
        return histogram_config


    def generate_config_files(self):

        # ---------------- Section for the store sequence ---------------- #

        # Preamble includes name of sequence, fr setup (unlikely to change)
        store_sequence_preamble = '''[
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

        sensors_layout = self.param_tree['sensors_layout']
        rows_of_sensors, columns_of_sensors = int(sensors_layout[0]), int(sensors_layout[2])
        rows = rows_of_sensors * 80
        columns = columns_of_sensors * 80
        pixels = rows * columns
        d = self.param_tree['config']

        # Sort parameter tree dict into R, T, N, C, A, D, H plugin order
        keyorder = ['reorder', 'threshold',  'next_frame', 'calibration', 'addition', 
                    'discrimination', 'histogram']
        config = OrderedDict(sorted(d.items(), key=lambda i:keyorder.index(i[0])))

        # Check parameter tree if next/calib/CS (i.e. optional) plugins to be added:

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
                # print("%s has 'enable' %s" % (key, enabled))
            except KeyError as e:
                # KeyError thrown if plugin doesn't have "enable" key
                print("Plugin %s missing 'enable' setting!")
                logging.debug("Plugin %s missing 'enable' setting!")
                raise Exception("Plugin %s missing 'enable' setting!")

        sample_plugins += ["histogram", "live_view", "hdf"]
        
        odin_path = "/u/ckd27546/develop/projects/odin-demo"
        store_plugin_paths = ""

        # Build config for standard paths
        for plugin in sample_plugins:
            if plugin in standard_path:
                store_plugin_paths += ''',
                {
                    "plugin": {
                        "load": {
                            "index": "%s",
                            "name": "Hexitec%sPlugin",
                            "library": "%s/install/lib/libHexitec%sPlugin.so"
                        }
                    }
                }''' % (standard_path[plugin][0], standard_path[plugin][1], 
                        odin_path, standard_path[plugin][2])

        # Build config for Non-standard paths
        for plugin in sample_plugins:
            if plugin in nonstandard_path:
                store_plugin_paths += ''',
                {
                    "plugin": {
                        "load": {
                            "index": "%s",
                            "name": "%sPlugin",
                            "library": "%s/install/lib/lib%sPlugin.so"
                        }
                    }
                }''' % (nonstandard_path[plugin][0], nonstandard_path[plugin][1],
                        odin_path, nonstandard_path[plugin][2])


        store_plugin_connect = ""
        previous_plugin = "frame_receiver"
        # Chain together plugins starting with frame receiver
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
    
        # Set plugins' settings
        store_plugin_config = ""
        unique_setting = ""
        for plugin in sample_plugins:
            # rinse and repeat for all except final two plugins of any chain
            if plugin not in ["live_view", "hdf"]:

                # Get unique_setting(s) according to plugin
                if plugin == "reorder":
                    unique_setting = '''\n                        "raw_data": %s,''' % \
                                        self.boolean_to_string(config[plugin]['raw_data'])
                if plugin == "threshold":
                    unique_setting = self.threshold_settings(config[plugin])
                if plugin == "next_frame":
                    pass # Nowt extra
                if plugin == "calibration":
                    unique_setting = self.calibration_settings(config[plugin])
                if plugin == "discrimination" or plugin == "addition":
                    unique_setting = '''\n                        "pixel_grid_size": %s,''' % \
                                                                config[plugin]['pixel_grid_size']
                if plugin == "histogram":
                    unique_setting = self.histogram_settings(config[plugin])

                store_plugin_config += ''',
                {
                    "%s": {%s
            		"sensors_layout": "%s"
                    }
                }''' % (plugin, unique_setting, sensors_layout)
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
                        "master": "%s",''' % self.master_dataset + '''
                        "dataset": 
                        {'''

        for dataset in self.extra_datasets:
            store_plugin_config += '''
                            "%s":''' % dataset + '''
                            {
                                "cmd": "create",
                                "datatype": "float",
                                "dims": [%s, %s],''' % (rows, columns) + '''
                                "chunks": [1, %s, %s],''' % (rows, columns) + '''
                                "compression": "none"
                            },'''

        store_plugin_config += '''
                            "spectra_bins":
                            {
                                "cmd": "create",
                                "datatype": "float",
                                "dims": [%s],''' % (self.number_histograms) + '''
                                "chunks": [1, %s],''' % (self.number_histograms) + '''
                                "compression": "none"
                            },
                            "pixel_spectra":
                            {
                                "cmd": "create",
                                "datatype": "float",
                                "dims": [%s, %s],''' % (pixels, self.number_histograms) + '''
                                "chunks": [1, %s, %s],''' % (pixels, self.number_histograms) + '''
                                "compression": "none"
                            },
                            "summed_spectra":
                            {
                                "cmd": "create",
                                "datatype": "uint64",
                                "dims": [%s],''' % (self.number_histograms) + '''
                                "chunks": [1, %s],''' % (self.number_histograms) + '''
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
                            "path": "/tmp/"
                        }
                    }
                }
            ]
        }
    }
]'''

        self.store_temp = tempfile.NamedTemporaryFile(mode='w+t')
        self.store_temp.delete = self.delete_file_on_close

        # Put together the store sequence file
        try:
            self.store_temp.writelines(store_sequence_preamble)
            self.store_temp.writelines(store_plugin_paths)
            self.store_temp.writelines(store_plugin_connect)
            self.store_temp.writelines(store_plugin_config)
        finally:
            self.store_temp.close()


        # The execute_config file is used to wipe any existing config, then load user config
        execute_config = '''
[
    {
        "plugin": 
        {
            "disconnect": "all"
        }
    },
    {
        "execute": 
        {
            "index": "temp"
        }
    }
]'''

        self.execute_temp = tempfile.NamedTemporaryFile(mode='w+t')
        self.execute_temp.delete = self.delete_file_on_close

        # Put together the execute sequence file 
        try:
            self.execute_temp.writelines(execute_config)
        finally:
            self.execute_temp.close()

        return self.store_temp.name, self.execute_temp.name

    # Redundant, couldn't get delete on file closing (delay closing file) to work
    # def close_files(self):
    #     self.store_temp.close()
    #     self.execute_temp.close()


if __name__ == '__main__':
    param_tree = {'file_info': {'file_name': 'default_file', 'enabled': False, 'file_dir': '/tmp/'}, 
        'sensors_layout': '2x2',  'receiver': {'config_file': '', 'configured': False, 'connected': 
        False}, 'in_progress': False, 
        # The 'config' nested dictionary control which plugin(s) are loaded:
        'config': 
        {'calibration': {'enable': False, 'intercepts_filename': '', 'gradients_filename': ''}, 
            'addition': {'enable': False, 'pixel_grid_size': 3}, 'discrimination': {'enable': 
            False, 'pixel_grid_size': 5}, 'histogram': {'max_frames_received': 10, 'bin_end': 
            8000, 'bin_width': 10.0, 'bin_start': 0}, 'next_frame': {'enable': True}, 
            'threshold': {'threshold_value': 99, 'threshold_filename': '', 'threshold_mode': 
            'none'}, 'reorder': {'raw_data': True}
        }, 
        'processor': {'config_file': '', 'configured': False, 'connected': False}}

    bin_end = param_tree['config']['histogram']['bin_end']
    bin_start = param_tree['config']['histogram']['bin_start']
    bin_width = param_tree['config']['histogram']['bin_width']
    number_histograms = int((bin_end - bin_start) / bin_width)
    master_dataset = "raw_frames"
    # extra_datasets = [master_dataset, "raw_frames"]
    extra_datasets = [master_dataset]

    gcf = GenerateConfigFiles(param_tree, number_histograms, bDeleteFileOnClose=False, 
                                master_dataset=master_dataset, extra_datasets=extra_datasets)
    s, e = gcf.generate_config_files()

    print("GFC returned config files\n Store:   %s\n Execute: %s\n" % (s, e))
