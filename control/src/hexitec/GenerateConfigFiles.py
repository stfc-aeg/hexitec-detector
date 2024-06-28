"""
GenerateConfigFiles: Creates a temporary file according to user UI selections.

Christian Angelsen, STFC Detector Systems Software Group
"""

import logging
import os
from collections import OrderedDict


class GenerateConfigFiles():
    """Accepts Parameter tree from hexitecDAQ's "/config" branch to generate json file."""

    def __init__(self, param_tree, number_histograms, compression_type="none",
                 master_dataset="processed_frames", extra_datasets=[], selected_os="CentOS",
                 live_view_selected=True, odin_path=None):
        """
        Initialize the GenerateConfigFiles object.

        This constructor initializes the GenerateConfigFiles object.
        :param param_tree: dictionary of parameter_tree configuration
        :param number_histograms: number of histogram bins
        :param master_dataset: set master dataset
        :param extra_datasets: include optional dataset(s)
        :param selected_os: which OS (ie path) to generate config for
        :param live_view_selected: should live view be configured
        :param odin_path: path to configuration files
        """
        self.param_tree = param_tree
        self.number_histograms = number_histograms
        # Compression Options are ["none", "blosc"]
        self.compression_type = compression_type
        self.master_dataset = master_dataset
        self.extra_datasets = extra_datasets
        # Each OS needs its own install, build paths
        self.selected_os = selected_os
        self.live_view_selected = live_view_selected
        self.odin_path = odin_path

    def boolean_to_string(self, bBool):
        """Convert bool to string."""
        string = "false"
        if bBool:
            string = "true"
        return string

    def threshold_settings(self, threshold):
        """Add threshold plugin section to configuration."""
        try:
            threshold_config = '''
                        "threshold_file": "%s",
                        "threshold_value": %s,
                        "threshold_mode": "%s",''' % \
                (threshold['threshold_filename'], threshold['threshold_value'],
                 threshold['threshold_mode'])
        except KeyError:
            logging.error("Error extracting threshold_settings!")
            print("Error extracting threshold_settings!")
            raise KeyError("Couldn't locate threshold setting(s)!")
        return threshold_config

    def calibration_settings(self, calibration):
        """Add calibration plugin section to configuration."""
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
        """Add histogram plugin section to configuration."""
        try:
            histogram_config = '''
                        "bin_start": %s,
                        "bin_end": %s,
                        "bin_width": %s,
                        "max_frames_received": %s,
                        "pass_processed": %s,
                        "pass_raw": %s,''' % \
                (histogram['bin_start'], histogram['bin_end'], histogram['bin_width'],
                 histogram['max_frames_received'],
                 self.boolean_to_string(histogram['pass_processed']),
                 self.boolean_to_string(histogram['pass_raw']))
        except KeyError:
            logging.error("Error extracting histogram_settings!")
            print("Error extracting histogram_settings!")
            raise KeyError("Couldn't locate histogram setting(s)!")
        return histogram_config

    def summed_image_settings(self, summed_image):
        """Add summed_image plugin section to configuration."""
        try:
            summed_image_config = '''
                        "threshold_lower": %s,
                        "threshold_upper": %s,''' % \
                (summed_image['threshold_lower'], summed_image['threshold_upper'])
        except KeyError:
            logging.error("Error extracting summed_image_settings!")
            print("Error extracting summed_image_settings!")
            raise KeyError("Couldn't locate summed_image setting(s)!")
        return summed_image_config

    def live_view_settings(self, plugin_name, live_view):
        """Add plugin_name (a live_view plugin) section to configuration."""
        try:
            frame_frequency = live_view["frame_frequency"]
            per_second = live_view["per_second"]
            socket_addr = live_view["live_view_socket_addr"]
            dataset_name = live_view["dataset_name"]
            live_view_config = ''',
                {
                    "%s":
                    {
                        "frame_frequency": %s,
                        "per_second": %s,
                        "live_view_socket_addr": "%s",
                        "dataset_name": "%s"
                    }
                }''' % (plugin_name, frame_frequency, per_second, socket_addr, dataset_name)
        except KeyError:
            logging.error("Error extracting live_view settings!")
            print("Error extracting live_view_settings!")
            raise KeyError("Couldn't locate live_view setting(s)!")
        return live_view_config

    def generate_config_files(self, id=""):  # noqa: C901
        """Generate the two configuration files, and configuration strings.

        The store config file contains the actual configuration.
        The execute config file is used to execute the configuration of the store file.
        """
        store_temp_name = "/tmp/_tmp_store{}.json".format(id)
        self.store_temp = open(store_temp_name, mode='w+t')

        # Generate a unique index name
        (blank, folder, filename) = store_temp_name.split("/")
        self.index_name = filename

        # ---------------- Section for the store sequence ---------------- #

        # Preamble includes name of sequence, fr setup (unlikely to change)
        store_sequence_preamble = '''[
    {
        "store":
        {
            "index": "%s",
            "value":
            [''' % self.index_name

        # plugin path that follows the same format i.e. ("reorder", "Reorder", "Reorder")
        # "index": "reorder",
        # "name": "HexitecReorderPlugin",
        # "library": "~/develop/projects/odin-demo/install/lib/libHexitecReorderPlugin.so"

        # Hexitec plugins (These also follow a uniform naming convention)
        hexitec_plugins = {}
        hexitec_plugins['reorder'] = ["reorder", "Reorder", "Reorder"]
        hexitec_plugins['threshold'] = ["threshold", "Threshold", "Threshold"]
        hexitec_plugins["calibration"] = ["calibration", "Calibration", "Calibration"]
        hexitec_plugins["addition"] = ["addition", "Addition", "Addition"]
        hexitec_plugins["discrimination"] = ["discrimination", "Discrimination", "Discrimination"]
        hexitec_plugins["histogram"] = ["histogram", "Histogram", "Histogram"]
        hexitec_plugins["summed_image"] = ["summed_image", "SummedImage", "SummedImage"]

        # Plugin path that doesn't follow the same format (as the others)
        # "live_view", "LiveViewPlugin      "install/lib/libLiveViewPlugin.so"
        # "hdf",       "FileWriterPlugin",  "install/lib/libHdf5Plugin.so"
        # "blosc",     "BloscPlugin",       "install/lib/libBloscPlugin.so"

        # Odin plugins
        odin_plugins = {}
        odin_plugins["lvframes"] = ["lvframes", "LiveView", "LiveView"]
        odin_plugins["lvspectra"] = ["lvspectra", "LiveView", "LiveView"]
        odin_plugins['hdf'] = ["hdf", "FileWriter", "Hdf5"]
        odin_plugins['blosc'] = ["blosc", "Blosc", "Blosc"]

        # Work out pixel dimensions
        sensors_layout = self.param_tree['sensors_layout']
        rows_of_sensors, columns_of_sensors = int(sensors_layout[0]), int(sensors_layout[2])
        rows = rows_of_sensors * 80
        columns = columns_of_sensors * 80
        pixels = rows * columns

        # Extract configuration from HexitecDAQ config
        d = self.param_tree['config']

        # Sort parameter tree dict into R, T, C, A, D, SI, H, LV plugin order
        keyorder = ['reorder', 'threshold', 'calibration', 'addition', 'discrimination',
                    'summed_image', 'histogram', 'lvframes', 'lvspectra']
        config = OrderedDict(sorted(d.items(), key=lambda i: keyorder.index(i[0])))

        # Determine plugin chain (to configure frameProcessor)

        # Reorder, threshold always mandatory
        plugin_chain = ["reorder", "threshold"]

        # User selectable plugins
        optional_plugins = ["calibration", "addition", "discrimination"]

        # Any optional plugin(s) to be added?
        for key in config:
            if key not in optional_plugins:
                continue
            try:
                if config[key]['enable']:
                    plugin_chain.append(key)
            except KeyError:
                # KeyError thrown if plugin doesn't have "enable" key
                print("Plugin %s missing 'enable' setting!" % key)
                logging.debug("Plugin %s missing 'enable' setting!" % key)
                raise Exception("Plugin %s missing 'enable' setting!" % key)

        plugin_chain += ["summed_image", "histogram"]
        if self.live_view_selected:
            plugin_chain += ["lvframes"]
            plugin_chain += ["lvspectra"]

        # Add blosc if compression selected
        if self.compression_type == "blosc":
            plugin_chain.append("blosc")
        plugin_chain += ["hdf"]

        store_plugin_paths = ""
        # Ubuntu and CentOS require different paths, builds, json files
        os_path = ""
        if self.selected_os == "CentOS":
            os_path = ""
        elif self.selected_os == "Ubuntu":
            os_path = "_ubuntu"

        comma_or_blank = ""
        # DEBUGGING:
        # avoid = ['threshold', 'calibration', 'addition', 'summed_image', 'histogram']
        avoid = []
        # Build config for Hexitec plugins (uniform naming)
        for plugin in plugin_chain:
            if plugin in avoid:     # pragma: no coverage
                continue
            if plugin in hexitec_plugins:
                store_plugin_paths += '''%s
                {
                    "plugin": {
                        "load": {
                            "index": "%s",
                            "name": "Hexitec%sPlugin",
                            "library": "%s/install%s/lib/libHexitec%sPlugin.so"
                        }
                    }
                }''' % (comma_or_blank,
                        hexitec_plugins[plugin][0],
                        hexitec_plugins[plugin][1],
                        self.odin_path,
                        os_path,
                        hexitec_plugins[plugin][2])
                comma_or_blank = ","

        # Build config for Odin plugins (differing names)
        for plugin in plugin_chain:
            if plugin in avoid:     # pragma: no coverage
                continue
            if plugin in odin_plugins:
                store_plugin_paths += ''',
                {
                    "plugin": {
                        "load": {
                            "index": "%s",
                            "name": "%sPlugin",
                            "library": "%s/install%s/lib/lib%sPlugin.so"
                        }
                    }
                }''' % (odin_plugins[plugin][0],
                        odin_plugins[plugin][1],
                        self.odin_path,
                        os_path,
                        odin_plugins[plugin][2])

        if self.live_view_selected:
            # Chain plugins together, with live view plugins branched off histogram
            # so it can support the following datasets, plugins:
            # * raw_frames/processed_frames (from reorder)
            # * summed_spectra (from histogram)
            # * summed_images (from summed_image)
            store_plugin_connect = ''',
                {
                    "plugin": {
                        "connect": {
                            "index": "lvframes",
                            "connection": "histogram"
                        }
                    }
                }'''
            # Remove lvframes from main plugin chain
            plugin_chain.remove("lvframes")

            store_plugin_connect += ''',
                {
                    "plugin": {
                        "connect": {
                            "index": "lvspectra",
                            "connection": "histogram"
                        }
                    }
                }'''
            # Remove lvspectra from main plugin chain
            plugin_chain.remove("lvspectra")
        else:
            store_plugin_connect = ""

        previous_plugin = "frame_receiver"
        # Chain together all other selected plugins, from frame receiver until hdf
        for plugin in plugin_chain:
            if plugin in avoid:     # pragma: no coverage
                continue
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

        # Configure plugins' settings

        store_plugin_config = ""
        unique_setting = ""
        for plugin in plugin_chain:
            if plugin in avoid:     # pragma: no coverage
                continue
            # rinse and repeat for all (except live view, hdf, and blosc if selected)
            if plugin not in ["lvframes", "lvspectra", "hdf"]:

                # Get unique_setting(s) according to plugin
                if plugin == "threshold":
                    unique_setting = self.threshold_settings(config[plugin])
                if plugin == "calibration":
                    unique_setting = self.calibration_settings(config[plugin])
                if plugin == "discrimination" or plugin == "addition":
                    unique_setting = '''\n                        "pixel_grid_size": %s,''' % \
                        config[plugin]['pixel_grid_size']
                if plugin == "histogram":
                    unique_setting = self.histogram_settings(config[plugin])
                if plugin == "summed_image":
                    unique_setting = self.summed_image_settings(config[plugin])

                store_plugin_config += ''',
                {
                    "%s": {%s
                        "sensors_layout": "%s"
                    }
                }''' % (plugin, unique_setting, sensors_layout)
                unique_setting = ""
        # Live view, hdf have different settings (e.g. no sensors_layout)

        if self.live_view_selected:
            # Add frames, spectra live view settings
            store_plugin_config += \
                self.live_view_settings("lvframes", self.param_tree["config"]["lvframes"])
            store_plugin_config += \
                self.live_view_settings("lvspectra", self.param_tree["config"]["lvspectra"])

        # Configure blosc (common settings) if selected
        if self.compression_type == "blosc":
            store_plugin_config += ''',
                {
                    "blosc": {
                        "compressor": 1,
                        "shuffle": 0,
                        "level": 4,
                        "threads": 1
                    }
                }'''

        store_plugin_config += ''',
                {
                    "hdf":
                    {
                        "master": "%s",''' % self.master_dataset + '''
                        "dataset":
                        {'''

        # Datasets' individual Blosc settings will be defined once only,
        #  applied to all datasets:
        blosc_settings = '''
                                "compression": "%s",
                                "blosc_compressor": 1,
                                "blosc_shuffle": 0,
                                "blosc_level": 4''' % self.compression_type

        # extra_datasets contained 0 or more of: [processed_frames, raw_frames]
        for dataset in self.extra_datasets:
            # datatype is float for processed_frames, uint16 for raw_frames
            datatype = "float"
            if dataset == "raw_frames":
                datatype = "uint16"
            store_plugin_config += '''
                            "%s":''' % dataset + '''
                            {
                                "datatype": "%s",''' % (datatype) + '''
                                "dims": [%s, %s],''' % (rows, columns) + '''
                                "chunks": [1, %s, %s],%s''' % (rows, columns, blosc_settings) + '''
                            },'''

        store_plugin_config += '''
                            "summed_images":
                            {
                                "datatype": "uint32",
                                "dims": [%s, %s],''' % (rows, columns) + '''
                                "chunks": [1, %s, %s],%s''' % (rows, columns, blosc_settings) + '''
                            },
                            "spectra_bins":
                            {
                                "datatype": "float",
                                "dims": [%s],''' % (self.number_histograms) + '''
                                "chunks": [1, %s],%s''' % (self.number_histograms,
                                                           blosc_settings) + '''
                            },
                            "pixel_spectra":
                            {
                                "datatype": "float",
                                "dims": [%s, %s],''' % (pixels, self.number_histograms) + '''
                                "chunks": [1, %s, %s],%s''' % (pixels, self.number_histograms,
                                                               blosc_settings) + '''
                            },
                            "summed_spectra":
                            {
                                "datatype": "uint64",
                                "dims": [%s],''' % (self.number_histograms) + '''
                                "chunks": [1, %s],%s''' % (self.number_histograms,
                                                           blosc_settings) + '''
                            }
                        }
                    }
                }'''

        file_path = self.param_tree["file_info"]["file_dir"]
        store_plugin_config += ''',
                {
                    "hdf":
                    {
                        "file":
                        {
                            "path": "%s"
                        }
                    }
                }
            ]
        }
    }
]''' % file_path

        # Put together the store sequence file
        try:
            self.store_temp.writelines(store_sequence_preamble)
            self.store_temp.writelines(store_plugin_paths)
            self.store_temp.writelines(store_plugin_connect)
            self.store_temp.writelines(store_plugin_config)
        finally:
            self.store_temp.close()

        # The execute_string file is used to wipe any existing config, then load user config
        execute_string = '''[
    {
        "plugin":
        {
            "disconnect": "all"
        }
    },
    {
        "execute":
        {
            "index": "%s"
        }
    }
]''' % self.index_name

        execute_temp_name = "/tmp/_tmp_execute.json"
        self.execute_temp = open(execute_temp_name, mode='w+t')

        # Put together the execute sequence file
        try:
            self.execute_temp.writelines(execute_string)
        finally:
            self.execute_temp.close()

        store_string = store_sequence_preamble + store_plugin_paths + store_plugin_connect + \
            store_plugin_config

        # Remove "execute" key (but keep its contents) from .json file contents:
        execute_preamble = execute_string.find("execute")
        string_without_execute_key = execute_string[execute_preamble+9: -3]
        execute_string_without_cr = "".join(string_without_execute_key.split())
        # Configuring FP using strings require removal of "store" key (but keeping its contents)
        # from .json equivalent, and removing the final two brackets:
        preamble = store_string.find("store")
        store_string = store_string[preamble+9: -4]
        store_string_without_cr = "".join(store_string.split())

        return store_temp_name, execute_temp_name, store_string_without_cr, \
            execute_string_without_cr


if __name__ == '__main__':  # pragma: no cover
    param_tree = {'file_info':
                  {'file_name': 'default_file', 'enabled': False, 'file_dir': '/tmp/'},
                  'sensors_layout': '2x6',
                  'receiver':
                  {'config_file': '', 'configured': False, 'connected': False},
                  'status': {'in_progress': False, 'daq_ready': False},
                  # The 'config' nested dictionary control which plugin(s) are loaded:
                  'config':
                  {'calibration': {'enable': True, 'intercepts_filename': '',
                                   'gradients_filename': ''},
                   'addition': {'enable': True, 'pixel_grid_size': 3},
                   'discrimination': {'enable': False, 'pixel_grid_size': 5},
                   'histogram': {'bin_end': 8000, 'bin_start': 0, 'bin_width': 10.0,
                                 'max_frames_received': 10, 'pass_processed': True,
                                 'pass_raw': True},
                   'lvframes': {'dataset_name': 'raw_frames', 'frame_frequency': 0,
                                'live_view_socket_addr': 'tcp://127.0.0.1:5020', 'per_second': 2},
                   'lvspectra': {'dataset_name': 'summed_spectra', 'frame_frequency': 0,
                                 'live_view_socket_addr': 'tcp://127.0.0.1:5021', 'per_second': 1},
                   'threshold': {'threshold_value': 99, 'threshold_filename': '',
                                 'threshold_mode': 'none'},
                   'summed_image': {'threshold_lower': 120, 'threshold_upper': 4800,
                                    'image_frequency': 1}},
                  'processor': {'config_file': '', 'configured': False, 'connected': False}}

    bin_end = param_tree['config']['histogram']['bin_end']
    bin_start = param_tree['config']['histogram']['bin_start']
    bin_width = param_tree['config']['histogram']['bin_width']
    number_histograms = int((bin_end - bin_start) / bin_width)
    master_dataset = "raw_frames"
    extra_datasets = [master_dataset, "processed_frames"]
    # extra_datasets = [master_dataset]
    selected_os = "CentOS"
    # Construct path relative to current working directory
    # -- Must execute from source code directory if run outside of Odin!
    cwd = os.getcwd()
    base_path_index = cwd.rfind("hexitec-detector")
    odin_path = cwd[:base_path_index - 1]
    gcf = GenerateConfigFiles(param_tree, number_histograms, compression_type="none",
                              master_dataset=master_dataset, extra_datasets=extra_datasets,
                              selected_os=selected_os, odin_path=odin_path)
    s, e, ss, se = gcf.generate_config_files(0)
    # print(type(s), type(e), type(ss), type(se))
    print("GFC (os:%s) returned config files\n Store:   %s\n Execute: %s\n" % (selected_os, s, e))
