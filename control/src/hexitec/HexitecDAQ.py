import logging

from os import path
from functools import partial

from odin.adapters.adapter import ApiAdapterRequest
from odin.adapters.parameter_tree import ParameterTree
from tornado.ioloop import IOLoop

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

import h5py
from datetime import datetime
import collections
# Check whether file exists:
import os.path

class HexitecDAQ():
    """
    Encapsulates all the functionaility to initiate the DAQ.
    
    TODO: Configures the Frame Receiver and Frame Processor plugins
    TODO: Configures the HDF File Writer Plugin
    TODO: Configures the Live View Plugin
    """

    THRESHOLDOPTIONS = ["value", "filename", "none"]

    def __init__(self, parent, save_file_dir="", save_file_name=""):

        self.parent = parent
        self.adapters = {}

        self.file_dir = save_file_dir
        self.file_name = save_file_name     # Unused, but may use in future..?

        self.in_progress = False
        self.is_initialised = False

        # these varables used to tell when an acquisiton is completed
        self.frame_start_acquisition = 0  # number of frames received at start of acq
        self.frame_end_acquisition = 0  # number of frames at end of acq (start + acq number)

        self.file_writing = False
        self.config_dir = ""
        self.config_files = {
            "fp": "",
            "fr": ""
        }

        # ParameterTree variables

        self.sensors_layout = "2x2"

        # Note that these four enable(s) are cosmetic only - written as meta data
        #   actual control is exercises from odin_server.js via sequence config files
        #   loading select(ed) plugins
        self.addition_enable = False
        self.discrimination_enable = False
        self.calibration_enable = False
        self.next_frame_enable = False

        self.pixel_grid_size = 3
        self.gradients_filename = ""
        self.intercepts_filename = ""
        self.bin_end = 8000
        self.bin_start = 0
        self.bin_width = 10.0
        self.max_frames_received = 10
        self.raw_data = False
        self.threshold_filename = ""
        self.threshold_mode = "value"
        self.threshold_value = 100

        self.rows, self.columns = 80, 80
        self.pixels = self.rows * self.columns
        self.number_frames = 10

        self.param_tree = ParameterTree({
            "receiver": {
                "connected": (partial(self.is_od_connected, adapter="fr"), None),
                "configured": (self.is_fr_configured, None),
                "config_file": (partial(self.get_config_file, "fr"), None)
            },
            "processor": {
                "connected": (partial(self.is_od_connected, adapter="fp"), None),
                "configured": (self.is_fp_configured, None),
                "config_file": (partial(self.get_config_file, "fp"), None)
            },
            "file_info": {
                "enabled": (lambda: self.file_writing, self.set_file_writing),
                "file_name": (lambda: self.file_name, self.set_file_name),
                "file_dir": (lambda: self.file_dir, self.set_data_dir)
            },
            "in_progress": (lambda: self.in_progress, None),
            "config": {
                "addition": {
                    "enable": (lambda: self.addition_enable, self._set_addition_enable),
                    "pixel_grid_size": (lambda: self.pixel_grid_size, self._set_pixel_grid_size)
                },
                "calibration": {
                    "enable": (lambda: self.calibration_enable, self._set_calibration_enable),
                    "gradients_filename": (lambda: self.gradients_filename, self._set_gradients_filename),
                    "intercepts_filename": (lambda: self.intercepts_filename, self._set_intercepts_filename)
                },
                "discrimination": {
                    "enable": (lambda: self.discrimination_enable, self._set_discrimination_enable),
                    "pixel_grid_size": (lambda: self.pixel_grid_size, self._set_pixel_grid_size)
                },
                "histogram": {
                    "bin_end": (lambda: self.bin_end, self._set_bin_end),
                    "bin_start": (lambda: self.bin_start, self._set_bin_start),
                    "bin_width": (lambda: self.bin_width, self._set_bin_width),
                    "max_frames_received": (lambda: self.max_frames_received, self._set_max_frames_received)
                },
                "reorder": {
                    "raw_data": (lambda: self.raw_data, self._set_raw_data)
                },
                "next_frame": {
                    "enable": (lambda: self.next_frame_enable, self._set_next_frame_enable)
                },
                "threshold": {
                    "threshold_filename": (lambda: self.threshold_filename, self._set_threshold_filename),
                    "threshold_mode": (lambda: self.threshold_mode, self._set_threshold_mode),
                    "threshold_value": (lambda: self.threshold_value, self._set_threshold_value)
                }
            },
            "sensors_layout": (self._get_sensors_layout, self._set_sensors_layout)
        })
        self.update_rows_columns_pixels()

    def initialize(self, adapters):
        self.adapters["fp"] = adapters['fp']
        self.adapters["fr"] = adapters['fr']
        self.adapters["file_interface"] = adapters['file_interface']
        self.get_config_file("fp")
        self.get_config_file("fr")
        self.is_initialised = True

    def start_acquisition(self, num_frames):
        """
        Ensures the odin data FP and FR are configured, and turn on File Writing
        """
        logging.debug("Setting up Acquisition")
        fr_status = self.get_od_status("fr")
        fp_status = self.get_od_status("fp")

        if self.is_od_connected(fr_status) is False:
            logging.error("Cannot start Acquisition: Frame Receiver not found")
            return
        elif self.is_fr_configured(fr_status) is False:
            self.config_odin_data("fr")
        else:
            logging.debug("Frame Receiver Already connected/configured")

        if self.is_od_connected(fp_status) is False:
            logging.error("Cannot Start Acquisition: Frame Processor not found")
            return
        elif self.is_fp_configured(fp_status) is False:
            self.config_odin_data("fp")
        else:
            logging.debug("Frame Processor Already connected/configured")

        hdf_status = fp_status.get('hdf', None)
        if hdf_status is None:
            fp_status = self.get_od_status('fp')
            # get current frame written number. if not found, assume FR
            # just started up and it will be 0
            hdf_status = fp_status.get('hdf', {"frames_processed": 0})
        self.frame_start_acquisition = hdf_status['frames_processed']
        self.frame_end_acquisition = self.frame_start_acquisition + num_frames
        logging.info("FRAME START ACQ: %d END ACQ: %d",
                     self.frame_start_acquisition,
                     self.frame_end_acquisition)
        self.in_progress = True
        IOLoop.instance().add_callback(self.acquisition_check_loop)
        logging.debug("Starting File Writer")
        self.set_file_writing(True)

    def acquisition_check_loop(self):
        hdf_status = self.get_od_status('fp').get('hdf', {"frames_processed": 0})
        if hdf_status['frames_processed'] == self.frame_end_acquisition:
            self.stop_acquisition()
            logging.debug("Acquisition Complete")
            # All required frames processed, wait for hdf file to close
            self.hdf_closing_loop()
        else:
            IOLoop.instance().call_later(.5, self.acquisition_check_loop)

    def stop_acquisition(self):
        """ Disable file writing so the processes can access the save data """
        self.in_progress = False
        self.set_file_writing(False)

    def hdf_closing_loop(self):
        hdf_status = self.get_od_status('fp').get('hdf', {"writing": True})
        if hdf_status['writing']:
            IOLoop.instance().call_later(0.5, self.hdf_closing_loop)
        else:
            full_path = self.file_dir + self.file_name + '_000001.h5'
            self.prepare_hdf_file(full_path)

    def prepare_hdf_file(self, filename):
        hdf_file_location = filename
        try:
            hdf_file = h5py.File(hdf_file_location, 'r+')
        except IOError as e:
            print("Failed to open HDF file with error: %s" % e)
            raise(e)
        # Create metadata group, add datasets to it and pass to write function
        # daq_metadata_group = hdf_file.create_group("daq")
        # daq_tree_dict = self.param_tree.get('')
        # self.write_metadata(daq_metadata_group, daq_tree_dict)

        parent_metadata_group = hdf_file.create_group("hexitec")
        parent_tree_dict = self.parent.param_tree.get('')
        # fem_tree_dict = self.parent.fem.param_tree.get('')
        self.write_metadata(parent_metadata_group, parent_tree_dict)
        hdf_file.close()

    def write_metadata(self, metadata_group, param_tree_dict):
        param_tree_dict = self.flatten(param_tree_dict)
        # logging.debug(" param_tree_dict:\n\n%s\n\n\n" % param_tree_dict)
        # Build metadata attributes from cached parameters
        for param, val in param_tree_dict.items():
            if val == None:
                # Replace None or TypeError will be thrown here
                #   ("Object dtype dtype('O') has no native HDF5 equivalent")
                val = "N/A"
            # print("  Adding key %s (%s), value %s (%s)" % (param, type(param), val, type(val)))
            metadata_group.attrs[param] = val
        # Add additional attribute to record current date
        metadata_group.attrs['runDate'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        # Write the configuration files into the metadata group
        self.config_ds = {}
        str_type = h5py.special_dtype(vlen=str)

        # Write contents of config files
        for param_file in ('detector/fems/fem_0/aspect_config',
                            'detector/daq/config/calibration/gradients_filename',
                            'detector/daq/config/calibration/intercepts_filename'):
            # Only attempt to open file if it exists
            file_name = param_tree_dict[param_file]
            if os.path.isfile(file_name):

                self.config_ds[param_file] = metadata_group.create_dataset(param_file, shape=(1,),
                                                                        dtype=str_type)
                try:
                    with open(file_name, 'r') as xml_file:
                        self.config_ds[param_file][:] = xml_file.read()

                except IOError as e:
                    print("Failed to read %s XML file %s : %s " % (param_file, 
                                                                file_name, e))
                    raise(e)
                except Exception as e:
                    print("Got exception trying to create metadata for %s XML file %s : %s " %
                        (param_file, param_file, e))
                    raise(e)
                logging.debug("Key '%s'; Successfully read file '%s'" % (param_file, file_name))
            else:
                logging.debug("\n\n Key: %s says file: %s\n Doesn't exist!\n\n\n" % (param_file, file_name))

    def flatten(self, d, parent_key='', sep='/'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def is_od_connected(self, status=None, adapter=""):
        if status is None:
            status = self.get_od_status(adapter)
        return status.get("connected", False)

    def is_fr_configured(self, status={}):
        if status.get('status') is None:
            status = self.get_od_status("fr")
        config_status = status.get("status", {}).get("configuration_complete", False)
        return config_status

    def is_fp_configured(self, status=None):
        status = self.get_od_status("fp")
        config_status = status.get("plugins")  # if plugins key exists, it has been configured
        return config_status is not None

    def get_od_status(self, adapter):
        if not self.is_initialised:
            return {"Error": "Adapter not initialised with references yet"}
        try:
            request = ApiAdapterRequest(None, content_type="application/json")
            response = self.adapters[adapter].get("status", request)
            response = response.data["value"][0]
        except KeyError:
            logging.warning("%s Adapter Not Found" % adapter)
            response = {"Error": "Adapter {} not found".format(adapter)}
        finally:
            return response

    def get_config_file(self, adapter):
        if not self.is_initialised:
            # IAC not setup yet
            return ""
        try:
            return_val = ""
            request = ApiAdapterRequest(None)
            response = self.adapters['file_interface'].get('', request).data
            self.config_dir = response['config_dir']
            for config_file in response["{}_config_files".format(adapter)]:
                if "hexitec" in config_file.lower():
                    return_val = config_file
                    break
            else:  # else of for loop: calls if finished loop without hitting break
                # just return the first config file found
                return_val = response["{}_config_files".format(adapter)][0]
        except KeyError as key_error:
            logging.warning("KeyError when trying to get config file: %s" % key_error)
            return_val = ""
        finally:
            self.config_files[adapter] = return_val
            return return_val

    def set_data_dir(self, directory):
        self.file_dir = directory

    def set_number_frames(self, number_frames):
        self.number_frames = number_frames

    def set_file_name(self, name):
        self.file_name = name

    def set_file_writing(self, writing):
        self.file_writing = writing
        # send command to Odin Data
        command = "config/hdf/file/path"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        self.adapters["fp"].put(command, request)

        command = "config/hdf/file/name"
        request.body = self.file_name
        self.adapters["fp"].put(command, request)

        command = "config/hdf/write"
        request.body = "{}".format(writing)
        self.adapters["fp"].put(command, request)

        # Avoid config/histogram/max_frames_received - use own paramTree instead
        self._set_max_frames_received(self.number_frames)

        command = "config/hdf/frames"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(self.number_frames)
        self.adapters["fp"].put(command, request)

    def config_odin_data(self, adapter):
        config = path.join(self.config_dir, self.config_files[adapter])
        config = path.expanduser(config)
        if not config.startswith('/'):
            config = '/' + config
        logging.debug(config)
        request = ApiAdapterRequest(config, content_type="application/json")
        command = "config/config_file"
        _ = self.adapters[adapter].put(command, request)

    def update_rows_columns_pixels(self):
        """
        Updates rows, columns and pixels from new sensors_layout value
        """
        self.rows, self.columns = self.sensors_layout.split("x")
        self.rows = int(self.rows) * 80
        self.columns = int(self.columns) * 80
        self.pixels = self.rows * self.columns

    def _set_addition_enable(self, addition_enable):
        self.addition_enable = addition_enable

    def _set_calibration_enable(self, calibration_enable):
        self.calibration_enable = calibration_enable

    def _set_discrimination_enable(self, discrimination_enable):
        self.discrimination_enable = discrimination_enable

    def _set_next_frame_enable(self, next_frame_enable):
        self.next_frame_enable = next_frame_enable

    def _set_pixel_grid_size(self, size):
        if (self.pixel_grid_size in [3, 5]):
            self.pixel_grid_size = size
        else:
            raise ParameterTreeError("Must be either 3 or 5")

    def _set_gradients_filename(self, gradients_filename):
        if (path.isfile(gradients_filename) == False):
            raise ParameterTreeError("Gradients file doesn't exist")
        self.gradients_filename = gradients_filename

    def _set_intercepts_filename(self, intercepts_filename):
        if (path.isfile(intercepts_filename) == False):
            raise ParameterTreeError("Intercepts file doesn't exist")
        self.intercepts_filename = intercepts_filename

    def _set_bin_end(self, bin_end):
        """
        Updates bin_end, datasets' histograms' dimensions
        """
        self.bin_end = bin_end
        self.update_histogram_dimensions()
    
    def _set_bin_start(self, bin_start):
        """
        Updates bin_start, datasets' histograms' dimensions
        """
        self.bin_start = bin_start
        self.update_histogram_dimensions()
    
    def _set_bin_width(self, bin_width):
        """
        Updates bin_width, datasets' histograms' dimensions
        """
        self.bin_width = bin_width
        self.update_histogram_dimensions()

    def update_datasets_frame_dimensions(self):
        """
        Updates frames datasets' dimensions
        """
        # Update data, raw_data datasets
        for dataset in ["data", "raw_frames"]:
            payload = '{"dims": [%s, %s]}' % (self.rows, self.columns)
            command = "config/hdf/dataset/" + dataset
            request = ApiAdapterRequest(str(payload), content_type="application/json")
            self.adapters["fp"].put(command, request)

    def update_histogram_dimensions(self):
        """
        Updates histograms' dimensions in the relevant datasets
        """
        number_of_histograms = int((self.bin_end - self.bin_start) / self.bin_width)
        # energy_bins dataset
        payload = '{"dims": [%s]}' % (number_of_histograms)
        command = "config/hdf/dataset/" + "energy_bins"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

        # pixel_histograms dataset
        payload = '{"dims": [%s, %s]}' % (self.pixels, number_of_histograms)
        command = "config/hdf/dataset/" + "pixel_histograms"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

        # summed_histograms dataset
        payload = '{"dims": [%s]}' % (number_of_histograms)
        command = "config/hdf/dataset/" + "summed_histograms"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

    def _set_max_frames_received(self, max_frames_received):
        self.max_frames_received = max_frames_received

    def _set_raw_data(self, raw_data):
        self.raw_data = raw_data

    def _set_threshold_filename(self, threshold_filename):
        if (path.isfile(threshold_filename) == False):
            raise ParameterTreeError("Threshold file doesn't exist")
        self.threshold_filename = threshold_filename

    def _set_threshold_mode(self, threshold_mode):
        threshold_mode = threshold_mode.lower()
        if (threshold_mode in self.THRESHOLDOPTIONS):
            self.threshold_mode = threshold_mode
        else:
            raise ParameterTreeError("Must be one of: value, filename or none")

    def _set_threshold_value(self, threshold_value):
        self.threshold_value = threshold_value

    def _get_sensors_layout(self):
        return self.sensors_layout

    def _set_sensors_layout(self, layout):
        """
        Sets sensors_layout in all FP's plugins and FR; Recalculates rows, columns and pixels
        """
        self.sensors_layout = layout

        # send command to all FP plugins, then FR
        plugins =  ['addition', 'calibration', 'discrimination', 'histogram', 'reorder', 
                    'next_frame', 'threshold']

        for plugin in plugins:
            command = "config/" + plugin + "/sensors_layout"
            request = ApiAdapterRequest(self.sensors_layout, content_type="application/json")
            self.adapters["fp"].put(command, request)

        command = "config/decoder_config/sensors_layout"
        request = ApiAdapterRequest(self.sensors_layout, content_type="application/json")
        self.adapters["fr"].put(command, request)

        self.update_rows_columns_pixels()
        self.update_datasets_frame_dimensions()

    def commit_configuration(self):

        # Loop overall plugins in ParameterTree, updating fp's settings
        #   Except reorder, until raw_data (i.e. bool) supported
        for plugin in self.param_tree.tree.get("config"):

            if plugin != "reorder":

                for param_key in self.param_tree.tree['config'].get(plugin):

                    # print "\nconfig/%s/%s" % (plugin, param_key), " -> ", \
                    #         self.param_tree.tree['detector']['config'][plugin][param_key].get(), "\n"

                    command = "config/%s/%s" % (plugin, param_key)
                    payload = self.param_tree.tree['config'][plugin][param_key].get()
                    request = ApiAdapterRequest(str(payload), content_type="application/json")
                    self.adapters["fp"].put(command, request)

        # Effin' works:
        # command = "config/threshold/threshold_value"
        # payload = str(121)
        # request = ApiAdapterRequest(payload, content_type="application/json")
        # self.adapters["fp"].put(command, request)

        # What does work:
        #curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fp/config/threshold -d 
        #   '{"threshold_value": 7, "threshold_mode": "none"}' | python -m json.tool