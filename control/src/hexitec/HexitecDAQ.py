""" 
HexitecDAQ for Hexitec ODIN control

Christian Angelsen, STFC Detector Systems Software Group
"""
import logging

from os import path
from functools import partial

from odin.adapters.adapter import ApiAdapterRequest
from odin.adapters.parameter_tree import ParameterTree

# from concurrent import futures
from tornado.ioloop import IOLoop
# from tornado.concurrent import run_on_executor

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from hexitec.GenerateConfigFiles import GenerateConfigFiles

import h5py
from datetime import datetime
import collections
import os.path
import time

class HexitecDAQ():
    """
    Encapsulates all the functionaility to initiate the DAQ.
    
    Configures the Frame Receiver and Frame Processor plugins
    Configures the HDF File Writer Plugin
    Configures the Live View Plugin
    """
    # thread_executor = futures.ThreadPoolExecutor(max_workers=1)

    THRESHOLDOPTIONS = ["value", "filename", "none"]

    def __init__(self, parent, save_file_dir="", save_file_name=""):

        self.parent = parent
        self.adapters = {}

        self.file_dir = save_file_dir
        self.file_name = save_file_name

        self.in_progress = False
        self.is_initialised = False

        # these varables used to tell when an acquisiton is completed
        self.frame_start_acquisition = 0  # number of frames received at start of acq
        self.frame_end_acquisition = 0  # number of frames at end of acq (acq number)

        # First initialisation fudges data acquisition (but without writing to disk)
        self.first_initialisation = True

        self.file_writing = False
        self.config_dir = ""
        self.config_files = {
            "fp": "",
            "fr": ""
        }

        self.hdf_file_location = ""
        self.hdf_retry = 0

        # ParameterTree variables

        self.sensors_layout = "2x2"

        # Note that these four enable(s) are cosmetic only - written as meta data
        #   actual control is exercised by odin_server.js via sequence config files
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
        self.number_of_histograms = int((self.bin_end - self.bin_start) / self.bin_width)

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
        # Placeholder for GenerateConfigFiles instance generating json files
        self.gcf = None

    def initialize(self, adapters):
        self.adapters["fp"] = adapters['fp']
        self.adapters["fr"] = adapters['fr']
        self.adapters["file_interface"] = adapters['file_interface']
        self.get_config_file("fp")
        self.get_config_file("fr")
        self.is_initialised = True

    def start_acquisition(self, number_frames):
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
        self.frame_end_acquisition = number_frames
        logging.info("FRAME START ACQ: %d END ACQ: %d",
                     self.frame_start_acquisition,
                     self.frame_start_acquisition+number_frames)
        self.in_progress = True
        logging.debug("Starting File Writer")
        if self.first_initialisation:
            # First initialisation captures data without writing to disk
            #   therefore don't enable file writing here
            pass
        else:
            # print("   ***   start_acquisition - not first initialisation, let's set that File writing to TRUE !")
            self.set_file_writing(True)
        # Wait while fem(s) finish sending data
        IOLoop.instance().call_later(0.5, self.acquisition_check_loop)

    def acquisition_check_loop(self):
        """
        Waits for acquisition to complete without blocking current thread
        """
        logging.debug("      acq_chek_loop")
        #TODO: Handle multiple fems more gracefully ?
        bBusy = True
        for fem in self.parent.fems:
            bBusy = fem.hardware_busy
        if bBusy:
            IOLoop.instance().call_later(0.5, self.acquisition_check_loop)
        else:
            IOLoop.instance().call_later(0.5, self.processing_check_loop)

    def processing_check_loop(self):
        """
        Checks that the processing has completed
        """
        hdf_status = self.get_od_status('fp').get('hdf', {"frames_processed": 0})
        logging.debug("      process_chek_loop, hdf stat vs frm_end_acq %s v %s" % (hdf_status['frames_processed'], self.frame_end_acquisition))
        if hdf_status['frames_processed'] == self.frame_end_acquisition:
            self.stop_acquisition()
            logging.debug("Acquisition Complete")
            # All required frames acquired, wait for hdf file to close
            self.hdf_closing_loop()
        else:
            if self.first_initialisation:
                # First initialisation runs without file writing, stopping acquisition 
                #   without reopening (non-existent) file to add meta data
                self.first_initialisation = False
                # Delay calling stop_acquisition, otherwise software may beat fem to it
                IOLoop.instance().call_later(2.0, self.stop_acquisition)
                return
            IOLoop.instance().call_later(.5, self.processing_check_loop)

    def check_file_exists(self):
        # DEBUGGING
        full_path = self.file_dir + self.file_name + '_000001.h5'
        existence = os.path.exists(full_path)
        print(" *** Exist? %s file: %s " % (existence, full_path))
        IOLoop.instance().call_later(.5, self.check_file_exists)

    def stop_acquisition(self):
        """ Disables file writing so the processes can access the saved data """
        logging.debug("      stop_acq()")
        self.in_progress = False
        self.set_file_writing(False)

    def hdf_closing_loop(self):
        """
        Waits for processing to complete without blocking thread,
        before preparing to write meta data
        """
        hdf_status = self.get_od_status('fp').get('hdf', {"writing": True})
        logging.debug("      hdf_clos_loop, hdf stat: %s" % hdf_status)
        if hdf_status['writing']:
            # print("   hdf_clo_loo, writ still TRUE")
            IOLoop.instance().call_later(0.5, self.hdf_closing_loop)
        else:
            # print("   hdf_clo_loo, writ FALSE so LET's GOGOGO")
            self.hdf_file_location = self.file_dir + self.file_name + '_000001.h5'
            # Check file exists before reopening to add metadata
            if os.path.exists(self.hdf_file_location):
                self.prepare_hdf_file()
            else:
                for fem in self.parent.fems:
                    fem._set_status_error("Cannot add meta data; No such File: %s" % \
                                                                self.hdf_file_location)

    def prepare_hdf_file(self):
        """
        Re-open HDF5 file, prepare meta data
        """
        logging.debug("      prep_hdf_file")
        try:
            hdf_file = h5py.File(self.hdf_file_location, 'r+')
            for fem in self.parent.fems:
                fem._set_status_message("Reopening file to add meta data..")
            self.hdf_retry= 0
        except IOError as e:
            # Let's retry a couple of times in case file just temporary busy
            if self.hdf_retry < 3:
                self.hdf_retry += 1
                # print("   *** Re-trying: %s because: %s" % (self.hdf_retry, e))
                IOLoop.instance().call_later(1.0, self.hdf_closing_loop)
                return
            #....?
            logging.error("Failed to open '%s' with error: %s" % (hdf_file_location, e))
            for fem in self.parent.fems:
                fem._set_status_error("Error reopening HDF file: %s" % e)
            return

        # Create metadata group, add dataset to it and pass to write function

        parent_metadata_group = hdf_file.create_group("hexitec")
        parent_tree_dict = self.parent.param_tree.get('')
        # fem_tree_dict = self.parent.fem.param_tree.get('')
        self.write_metadata(parent_metadata_group, parent_tree_dict)

        #TODO: Hacked until frame_process_adapter updated to use parameter tree
        hdf_metadata_group = hdf_file.create_group("hdf")
        hdf_tree_dict = self.adapters['fp']._param
        self.write_metadata(hdf_metadata_group, hdf_tree_dict)

        for fem in self.parent.fems:
            fem._set_status_message("Meta data added")
        hdf_file.close()

    def write_metadata(self, metadata_group, param_tree_dict):
        """
        Write parameter tree(s) and config files as meta data
        """
        param_tree_dict = self.flatten_dict(param_tree_dict)

        # Build metadata attributes from dictionary
        for param, val in param_tree_dict.items():
            if val == None:
                # Replace None or TypeError will be thrown as:
                #   ("Object dtype dtype('O') has no native HDF5 equivalent")
                val = "N/A"
            metadata_group.attrs[param] = val

        # Only write parent's (Hexitec class) parameter tree's config files once
        if metadata_group.name == u'/hexitec':
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

                    self.config_ds[param_file] = metadata_group.create_dataset(param_file, 
                                                                            shape=(1,),
                                                                            dtype=str_type)
                    try:
                        with open(file_name, 'r') as xml_file:
                            self.config_ds[param_file][:] = xml_file.read()

                    except IOError as e:
                        logging.error("Failed to read %s XML file %s : %s " % (param_file, 
                                                                    file_name, e))
                        raise(e)
                    except Exception as e:
                        logging.error("Exception creating metadata for %s XML file %s : %s " %
                            (param_file, param_file, e))
                        raise(e)
                    logging.debug("Key '%s'; Successfully read file '%s'" % (param_file, file_name))
                else:
                    logging.debug("\n\n Key: %s's file: %s\n Doesn't exist!\n\n\n" % (param_file, file_name))

    def flatten_dict(self, d, parent_key='', sep='/'):
        """
        Flattens a dictionary with nested dictionary into single dictionary of key-value pairs
        """
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
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
            else:  # else of for loop: calls if loop finished without hitting break
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
        # print("\n\n")
        # logging.debug("hexitecDAQ set_number_frames(%s)" % self.number_frames)
        # print("\n\n")

    def set_file_name(self, name):
        self.file_name = name

    def set_file_writing(self, writing):
        # print("\n\n")
        # logging.debug("hexitecDAQ set_number_frames(%s) number_frames: %s" % (writing, self.number_frames))
        # print("\n\n")
        
        command = "config/hdf/frames"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(self.number_frames)
        self.adapters["fp"].put(command, request)

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

        # Target both config/histogram/max_frames_received and own ParameterTree
        self._set_max_frames_received(self.number_frames)
        command = "config/histogram/max_frames_received"
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
        Updates rows, columns and pixels from selected sensors_layout value
        If sensors_layout = "3x2" => 3 rows of sensors by 2 columns of sensors
        """
        self.sensors_rows, self.sensors_columns = self.sensors_layout.split("x")
        self.rows = int(self.sensors_rows) * 80
        self.columns = int(self.sensors_columns) * 80
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
        Updates bin_end and datasets' histograms' dimensions
        """
        self.bin_end = bin_end
        self.update_histogram_dimensions()
    
    def _set_bin_start(self, bin_start):
        """
        Updates bin_start and datasets' histograms' dimensions
        """
        self.bin_start = bin_start
        self.update_histogram_dimensions()
    
    def _set_bin_width(self, bin_width):
        """
        Updates bin_width and datasets' histograms' dimensions
        """
        self.bin_width = bin_width
        self.update_histogram_dimensions()

    def update_datasets_frame_dimensions(self):
        """
        Updates frames' datasets' dimensions
        """
        for dataset in ["data", "raw_frames"]:
            payload = '{"dims": [%s, %s]}' % (self.rows, self.columns)
            command = "config/hdf/dataset/" + dataset
            request = ApiAdapterRequest(str(payload), content_type="application/json")
            self.adapters["fp"].put(command, request)

    def update_histogram_dimensions(self):
        """
        Updates histograms' dimensions in the relevant datasets
        """
        self.number_of_histograms = int((self.bin_end - self.bin_start) / self.bin_width)
        # energy_bins dataset
        payload = '{"dims": [%s], "chunks": [1, %s]}' % \
            (self.number_of_histograms, self.number_of_histograms)
        command = "config/hdf/dataset/" + "energy_bins"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

        # pixel_histograms dataset
        payload = '{"dims": [%s, %s], "chunks": [1, %s, %s]}' % \
            (self.pixels, self.number_of_histograms, self.pixels, self.number_of_histograms)
        command = "config/hdf/dataset/" + "pixel_histograms"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

        # summed_histograms dataset
        payload = '{"dims": [%s], "chunks": [1, %s]}' % \
            (self.number_of_histograms, self.number_of_histograms)
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
        self.update_histogram_dimensions()

    def commit_configuration(self):
        """
        Sends each ParameterTree value to it's counterpart in the FP
        """
        # Generate JSON config file from parameter tree's settings
        parameter_tree = self.param_tree.get('')
        
        self.gcf = GenerateConfigFiles(parameter_tree, self.number_of_histograms, 
                                        bDeleteFileOnClose=False)

        store_config, execute_config = self.gcf.generate_config_files()

        command = "config/config_file/"
        request = ApiAdapterRequest(store_config, content_type="application/json")
        self.adapters["fp"].put(command, request)

        request = ApiAdapterRequest(execute_config, content_type="application/json")
        self.adapters["fp"].put(command, request)

        # Loop overall plugins in ParameterTree, updating fp's settings except reorder
        #TODO: Include reorder when odin control supports raw_data (i.e. bool)
        for plugin in self.param_tree.tree.get("config"):

            if plugin != "reorder":

                for param_key in self.param_tree.tree['config'].get(plugin):

                    # print "\nconfig/%s/%s" % (plugin, param_key), " -> ", \
                    #         self.param_tree.tree['detector']['config'][plugin][param_key].get(), "\n"

                    command = "config/%s/%s" % (plugin, param_key)
                    payload = self.param_tree.tree['config'][plugin][param_key].get()
                    request = ApiAdapterRequest(str(payload), content_type="application/json")
                    self.adapters["fp"].put(command, request)

        #TODO: Cannot implement delayed file deletion, forced to keep them alive past closure..!
    #     logging.debug("\n\n\tWaiting three seconds before closing temporary files..\n\n")
    #     IOLoop.instance().call_later(3.0, self.close_temporary_files)

    # @run_on_executor(executor='thread_executor')
    # def close_temporary_files(self):
    #     logging.debug("\n\n\tI ain't waiting no more, close them files!!!!!\n\n")
    #     # Cleanup by closing temporary files
    #     self.gcf.close_files()

