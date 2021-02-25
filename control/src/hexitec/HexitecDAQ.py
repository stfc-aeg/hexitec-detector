"""
HexitecDAQ for Hexitec ODIN control.

Christian Angelsen, STFC Detector Systems Software Group
"""

import logging
from functools import partial

from tornado.ioloop import IOLoop
from odin.adapters.adapter import ApiAdapterRequest
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from hexitec.GenerateConfigFiles import GenerateConfigFiles

import h5py
from datetime import datetime
import collections.abc
import time
import os


class HexitecDAQ():
    """
    Encapsulates all the functionaility to initiate the DAQ.

    Configures the Frame Receiver and Frame Processor plugins
    Configures the HDF File Writer Plugin
    Configures the Live View Plugin
    """

    THRESHOLDOPTIONS = ["value", "filename", "none"]

    # Define timestamp format
    DATE_FORMAT = '%Y%m%d_%H%M%S.%f'

    def __init__(self, parent, save_file_dir="", save_file_name=""):
        """
        Initialize the HexitecDAQ object.

        This constructor initializes the HexitecDAQ object.
        :param parent: Reference to adapter object
        :param save_file_dir: save processed file to directory
        :param save_file_name: save processed file name as
        """
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

        # Construct path to hexitec source code
        cwd = os.getcwd()
        index = cwd.find("control")
        self.base_path = cwd[:index]

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
        self.number_histograms = int((self.bin_end - self.bin_start) / self.bin_width)

        self.max_frames_received = 10
        self.pass_processed = False
        self.raw_data = False
        # Look at histogram/hdf to determine when processing finished:
        self.plugin = "histogram"
        self.master_dataset = "spectra_bins"
        self.extra_datasets = []
        # Processing timeout variables, support adapter's watchdog
        self.processed_timestamp = 0
        self.frames_processed = 0
        self.shutdown_processing = False

        self.threshold_filename = ""
        self.threshold_mode = "value"
        self.threshold_value = 120

        self.rows, self.columns = 160, 160
        self.pixels = self.rows * self.columns
        self.number_frames = 10
        # Diagnostics
        self.daq_start_time = 0
        self.fem_not_busy = 0
        self.daq_stop_time = 0

        self.param_tree = ParameterTree({
            "diagnostics": {
                "daq_start_time": (lambda: self.daq_start_time, None),
                "daq_stop_time": (lambda: self.daq_stop_time, None),
                "fem_not_busy": (lambda: self.fem_not_busy, None),
            },
            "receiver": {
                "connected": (partial(self._is_od_connected, adapter="fr"), None),
                "configured": (self._is_fr_configured, None),
                "config_file": (partial(self.get_config_file, "fr"), None)
            },
            "processor": {
                "connected": (partial(self._is_od_connected, adapter="fp"), None),
                "configured": (self._is_fp_configured, None),
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
                    "gradients_filename": (lambda: self.gradients_filename,
                                           self._set_gradients_filename),
                    "intercepts_filename": (lambda: self.intercepts_filename,
                                            self._set_intercepts_filename)
                },
                "discrimination": {
                    "enable": (lambda: self.discrimination_enable, self._set_discrimination_enable),
                    "pixel_grid_size": (lambda: self.pixel_grid_size, self._set_pixel_grid_size)
                },
                "histogram": {
                    "bin_end": (lambda: self.bin_end, self._set_bin_end),
                    "bin_start": (lambda: self.bin_start, self._set_bin_start),
                    "bin_width": (lambda: self.bin_width, self._set_bin_width),
                    "max_frames_received": (lambda: self.max_frames_received,
                                            self._set_max_frames_received),
                    "pass_processed": (lambda: self.pass_processed, self._set_pass_processed)
                },
                "reorder": {
                    "raw_data": (lambda: self.raw_data, self._set_raw_data)
                },
                "next_frame": {
                    "enable": (lambda: self.next_frame_enable, self._set_next_frame_enable)
                },
                "threshold": {
                    "threshold_filename": (lambda: self.threshold_filename,
                                           self._set_threshold_filename),
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
        """Initialise adapters and related parameter tree entries."""
        self.adapters["fp"] = adapters['fp']
        self.adapters["fr"] = adapters['fr']
        self.adapters["file_interface"] = adapters['file_interface']
        self.get_config_file("fp")
        self.get_config_file("fr")
        self.is_initialised = True

    def start_acquisition(self, number_frames):
        """Ensure the odin data FP and FR are configured, and turn on File Writing."""
        logging.debug("Setting up Acquisition")

        fr_status = self.get_od_status("fr")
        fp_status = self.get_od_status("fp")
        if self._is_od_connected(fr_status) is False:
            logging.error("Cannot start Acquisition: Frame Receiver not found")
            return
        elif self._is_fr_configured(fr_status) is False:
            self._config_odin_data("fr")
        else:
            logging.debug("Frame Receiver Already connected/configured")

        if self._is_od_connected(fp_status) is False:
            logging.error("Cannot Start Acquisition: Frame Processor not found")
            return
        elif self._is_fp_configured(fp_status) is False:
            self._config_odin_data("fp")
        else:
            logging.debug("Frame Processor Already connected/configured")

        hdf_status = fp_status.get('hdf', None)
        if hdf_status is None:
            fp_status = self.get_od_status('fp')
            # Get current frame written number. If not found, assume FR
            # just started up and it will be 0
            hdf_status = fp_status.get('hdf', {"frames_processed": 0})
        self.frame_start_acquisition = hdf_status['frames_processed']
        self.frame_end_acquisition = number_frames
        logging.info("FRAME START ACQ: %d END ACQ: %d",
                     self.frame_start_acquisition,
                     self.frame_start_acquisition + number_frames)
        self.in_progress = True
        # Reset timeout watchdog
        self.processed_timestamp = time.time()
        logging.debug("Starting File Writer")
        if self.first_initialisation:
            # First initialisation captures data without writing to disk
            #   therefore don't enable file writing here
            pass  # pragma: no cover
        else:
            self.set_file_writing(True)
        # Diagnostics:
        self.daq_start_time = '%s' % (datetime.now().strftime(HexitecDAQ.DATE_FORMAT))

        # Wait while fem(s) finish sending data
        IOLoop.instance().call_later(1.3, self.acquisition_check_loop)

    def acquisition_check_loop(self):
        """Wait for acquisition to complete without blocking current thread."""
        bBusy = self.parent.fems[0].hardware_busy
        if bBusy:
            IOLoop.instance().call_later(0.5, self.acquisition_check_loop)
        else:
            self.fem_not_busy = '%s' % (datetime.now().strftime(HexitecDAQ.DATE_FORMAT))
            # Reset timeout watchdog
            self.processed_timestamp = time.time()
            self.frames_processed = 0
            IOLoop.instance().call_later(0.5, self.processing_check_loop)

    def processing_check_loop(self):
        """Check that the processing has completed."""
        if self.first_initialisation:
            # First initialisation runs without file writing; Stop acquisition
            #   without reopening (non-existent) file to add meta data
            self.first_initialisation = False
            self.in_progress = False
            # Delay calling stop_acquisition, otherwise software may beat fem to it
            IOLoop.instance().call_later(2.0, self.stop_acquisition)
            return
        # Not fudge initialisation; Check HDF/histogram processing progress
        processing_status = self.get_od_status('fp').get(self.plugin, {'frames_processed': 0})

        # # Debugging information:
        # hdf_status = self.get_od_status('fp').get('hdf', {"frames_processed": 0})
        # his_status = self.get_od_status('fp').get('histogram', {'frames_processed': 0})
        # print("")
        # logging.debug("      proc'g_chek_loop, hdf (%s) v his (%s) v frm_end_acq (%s) PLUG = %s" %
        #              (hdf_status['frames_processed'], his_status['frames_processed'],
        #               self.frame_end_acquisition, self.plugin))
        # print("")

        if processing_status['frames_processed'] == self.frame_end_acquisition:
            delay = 1.0
            IOLoop.instance().call_later(delay, self.stop_acquisition)
            logging.debug("Acquisition Complete")
            # All required frames acquired; if either of frames based datasets
            #   selected, wait for hdf file to close
            IOLoop.instance().call_later(delay, self.hdf_closing_loop)
        else:
            # Not all frames processed yet; Check data still in flow
            if processing_status['frames_processed'] == self.frames_processed:
                # No frames processed in at least 0.5 sec, did processing time out?
                if self.shutdown_processing:
                    self.shutdown_processing = False
                    self.in_progress = False
                    IOLoop.instance().add_callback(self.stop_acquisition)
                    return
            else:
                # Data still bein' processed
                self.processed_timestamp = time.time()
                self.frames_processed = processing_status['frames_processed']
            # Wait 0.5 seconds and check again
            IOLoop.instance().call_later(.5, self.processing_check_loop)

    def stop_acquisition(self):
        """Disable file writing so processing can access the saved data to add Meta data."""
        self.daq_stop_time = '%s' % (datetime.now().strftime(HexitecDAQ.DATE_FORMAT))
        self.set_file_writing(False)

    def hdf_closing_loop(self):
        """Wait for processing to complete but don't block, before prep to write meta data."""
        hdf_status = self.get_od_status('fp').get('hdf', {"writing": True})
        if hdf_status['writing']:
            IOLoop.instance().call_later(0.5, self.hdf_closing_loop)
        else:
            self.hdf_file_location = self.file_dir + self.file_name + '_000001.h5'
            # Check file exists before reopening to add metadata
            if os.path.exists(self.hdf_file_location):
                self.prepare_hdf_file()
            else:
                self.parent.fems[0]._set_status_error("No file to add meta: %s" %
                                                      self.hdf_file_location)
                self.in_progress = False

    def prepare_hdf_file(self):
        """Re-open HDF5 file, prepare meta data."""
        try:
            hdf_file = h5py.File(self.hdf_file_location, 'r+')
            for fem in self.parent.fems:
                fem._set_status_message("Reopening file to add meta data..")
            self.hdf_retry = 0
        except IOError as e:
            # Let's retry a couple of times in case file temporary busy
            if self.hdf_retry < 6:
                self.hdf_retry += 1
                logging.warning(" Re-try attempt: %s Reopen file, because: %s" %
                                (self.hdf_retry, e))
                IOLoop.instance().call_later(0.5, self.hdf_closing_loop)
                return
            logging.error("Failed to open '%s' with error: %s" % (self.hdf_file_location, e))
            self.in_progress = False
            for fem in self.parent.fems:
                fem._set_status_error("Error reopening HDF file: %s" % e)
            return

        error_code = 0
        # Create metadata group, add dataset to it and pass to write function
        parent_metadata_group = hdf_file.create_group("hexitec")
        parent_tree_dict = self.parent.param_tree.get('')
        error_code = self.write_metadata(parent_metadata_group, parent_tree_dict)

        # TODO: returns < 0 if XML issues, 0 if fine
        # if (error_code == 0)
        #    # ..
        # TODO: Hacked until frame_process_adapter updated to use parameter tree
        hdf_metadata_group = hdf_file.create_group("hdf")
        hdf_tree_dict = self.adapters['fp']._param
        self.write_metadata(hdf_metadata_group, hdf_tree_dict)

        for fem in self.parent.fems:
            fem._set_status_message("Meta data added")
        hdf_file.close()
        self.in_progress = False

    def write_metadata(self, metadata_group, param_tree_dict):
        """Write parameter tree(s) and config files as meta data."""
        param_tree_dict = self._flatten_dict(param_tree_dict)

        # Build metadata attributes from dictionary
        for param, val in param_tree_dict.items():
            if val is None:
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

            # Write contents of config file, and selected coefficients file(s)
            file_name = ['detector/fems/fem_0/hexitec_config']
            if self.calibration_enable:
                file_name.append('detector/daq/config/calibration/gradients_filename')
                file_name.append('detector/daq/config/calibration/intercepts_filename')
            if self.threshold_mode == self.THRESHOLDOPTIONS[1]:  # = "filename"
                file_name.append('detector/daq/config/threshold/threshold_filename')

            for param_file in file_name:
                # Only attempt to open file if it exists
                file_name = param_tree_dict[param_file]
                if os.path.isfile(file_name):
                    self.config_ds[param_file] = \
                        metadata_group.create_dataset(param_file, shape=(1,), dtype=str_type)
                    try:
                        with open(file_name, 'r') as xml_file:
                            self.config_ds[param_file][:] = xml_file.read()
                    except IOError as e:
                        logging.error("Failed to read %s XML file %s : %s " %
                                      (param_file, file_name, e))
                        return -1
                    except Exception as e:
                        logging.error("Exception creating metadata for %s XML file %s : %s" %
                                      (param_file, param_file, e))
                        return -2
                    logging.debug("Key '%s'; Successfully read file '%s'" % (param_file, file_name))
                else:
                    logging.error("Key: %s's file: %s. Doesn't exist!" % (param_file, file_name))
        return 0

    def _flatten_dict(self, d, parent_key='', sep='/'):
        """Flatten a dictionary of nested dictionary into single dictionary of key-value pairs."""
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.abc.MutableMapping):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _is_od_connected(self, status=None, adapter=""):
        if status is None:
            status = self.get_od_status(adapter)
        return status.get("connected", False)

    def _is_fr_configured(self, status={}):
        if status.get('status') is None:
            status = self.get_od_status("fr")
        config_status = status.get("status", {}).get("configuration_complete", False)
        return config_status

    def _is_fp_configured(self, status=None):
        status = self.get_od_status("fp")
        config_status = status.get("plugins")  # if plugins key exists, it has been configured
        return config_status is not None

    def get_od_status(self, adapter):
        """Get status from adapter."""
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
        """Get config file from adapter."""
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
        """Set directory of processed file."""
        self.file_dir = directory

    def set_number_frames(self, number_frames):
        """Set number of frames to be acquired."""
        self.number_frames = number_frames

    def set_file_name(self, name):
        """Set processed file name."""
        self.file_name = name

    def set_file_writing(self, writing):
        """Update processed file details, file writing and histogram setting."""
        command = "config/hdf/frames"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        # request.body = "{}".format(self.number_frames)
        request.body = "{}".format(0)
        self.adapters["fp"].put(command, request)

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

        # Finally, update self_writing so FEM(s) can safely begin sending data
        self.file_writing = writing

    def _config_odin_data(self, adapter):
        config = os.path.join(self.config_dir, self.config_files[adapter])
        config = os.path.expanduser(config)
        if not config.startswith('/'):
            config = '/' + config
        logging.debug(config)
        request = ApiAdapterRequest(config, content_type="application/json")
        command = "config/config_file"
        _ = self.adapters[adapter].put(command, request)

    def update_rows_columns_pixels(self):
        """Update rows, columns and pixels from selected sensors_layout value.

        e.g. sensors_layout = "3x2" => 3 rows of sensors by 2 columns of sensors
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
        if (size in [3, 5]):
            self.pixel_grid_size = size
        else:
            raise ParameterTreeError("Must be either 3 or 5")

    def _set_gradients_filename(self, gradients_filename):
        gradients_filename = self.base_path + gradients_filename
        if (os.path.isfile(gradients_filename) is False):
            raise ParameterTreeError("Gradients file doesn't exist")
        self.gradients_filename = gradients_filename

    def _set_intercepts_filename(self, intercepts_filename):
        intercepts_filename = self.base_path + intercepts_filename
        if (os.path.isfile(intercepts_filename) is False):
            raise ParameterTreeError("Intercepts file doesn't exist")
        self.intercepts_filename = intercepts_filename

    def _set_bin_end(self, bin_end):
        """Update bin_end and datasets' histograms' dimensions."""
        self.bin_end = bin_end
        self.update_histogram_dimensions()

    def _set_bin_start(self, bin_start):
        """Update bin_start and datasets' histograms' dimensions."""
        self.bin_start = bin_start
        self.update_histogram_dimensions()

    def _set_bin_width(self, bin_width):
        """Update bin_width and datasets' histograms' dimensions."""
        self.bin_width = bin_width
        self.update_histogram_dimensions()

    def update_datasets_frame_dimensions(self):
        """Update frames' datasets' dimensions."""
        for dataset in ["processed_frames", "raw_frames"]:
            payload = '{"dims": [%s, %s]}' % (self.rows, self.columns)
            command = "config/hdf/dataset/" + dataset
            request = ApiAdapterRequest(str(payload), content_type="application/json")
            self.adapters["fp"].put(command, request)

    def update_histogram_dimensions(self):
        """Update histograms' dimensions in the relevant datasets."""
        self.number_histograms = int((self.bin_end - self.bin_start) / self.bin_width)
        # spectra_bins dataset
        payload = '{"dims": [%s], "chunks": [1, %s]}' % \
            (self.number_histograms, self.number_histograms)
        command = "config/hdf/dataset/" + "spectra_bins"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

        # pixel_spectra dataset
        payload = '{"dims": [%s, %s], "chunks": [1, %s, %s]}' % \
            (self.pixels, self.number_histograms, self.pixels, self.number_histograms)
        command = "config/hdf/dataset/" + "pixel_spectra"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

        # summed_spectra dataset
        payload = '{"dims": [%s], "chunks": [1, %s]}' % \
            (self.number_histograms, self.number_histograms)
        command = "config/hdf/dataset/" + "summed_spectra"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

    def _set_max_frames_received(self, max_frames_received):
        self.max_frames_received = max_frames_received

    def _set_pass_processed(self, pass_processed):
        self.pass_processed = pass_processed

    def _set_raw_data(self, raw_data):
        self.raw_data = raw_data

    def _set_threshold_filename(self, threshold_filename):
        threshold_filename = self.base_path + threshold_filename
        if (os.path.isfile(threshold_filename) is False):
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
        """Set sensors_layout in all FP's plugins and FR; Recalculates rows, columns and pixels."""
        self.sensors_layout = layout

        # send command to all FP plugins, then FR
        plugins = ['addition', 'calibration', 'discrimination', 'histogram', 'reorder',
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
        """Generate and sends the FP config files."""
        # Generate JSON config file determining which plugins, the order to chain them, etc
        parameter_tree = self.param_tree.get('')

        self.extra_datasets = []
        self.master_dataset = "spectra_bins"

        if self.raw_data:
            self.master_dataset = "raw_frames"
            self.extra_datasets.append(self.master_dataset)
        if self.pass_processed:
            self.master_dataset = "processed_frames"
            self.extra_datasets.append(self.master_dataset)

        self.gcf = GenerateConfigFiles(parameter_tree, self.number_histograms,
                                       master_dataset=self.master_dataset,
                                       extra_datasets=self.extra_datasets)

        store_config, execute_config = self.gcf.generate_config_files()
        command = "config/config_file/"
        request = ApiAdapterRequest(store_config, content_type="application/json")

        response = self.adapters["fp"].put(command, request)
        status_code = response.status_code
        if (status_code != 200):
            error = "Error {} parsing store json config file in fp adapter".format(status_code)
            logging.error(error)
            self.parent.fems[0]._set_status_error(error)

        request = ApiAdapterRequest(execute_config, content_type="application/json")
        response = self.adapters["fp"].put(command, request)
        status_code = response.status_code
        if (status_code != 200):
            error = "Error {} parsing execute json config file in fp adapter".format(status_code)
            logging.error(error)
            self.parent.fems[0]._set_status_error(error)

        # Allow FP time to process above PUT requests before configuring plugin settings
        IOLoop.instance().call_later(0.4, self.submit_configuration)

    def submit_configuration(self):
        """Send each ParameterTree value to the corresponding FP plugin."""
        # Loop overall plugins in ParameterTree, updating fp's settings except reorder
        # TODO: Include reorder when odin control supports raw_data (i.e. bool)

        for plugin in self.param_tree.tree.get("config"):

            if plugin != "reorder":

                for param_key in self.param_tree.tree['config'].get(plugin):

                    # print "config/%s/%s" % (plugin, param_key), " -> ", \
                    #         self.param_tree.tree['config'][plugin][param_key].get("")

                    # Don't send histograms' pass_processed, since Odin Control do not support bool
                    if param_key != "pass_processed":

                        command = "config/%s/%s" % (plugin, param_key)

                        payload = self.param_tree.tree['config'][plugin][param_key].get()
                        request = ApiAdapterRequest(str(payload), content_type="application/json")
                        self.adapters["fp"].put(command, request)

        # Which plugin determines when processing finished?
        if (self.raw_data or self.pass_processed):
            self.plugin = "hdf"
        else:
            self.plugin = "histogram"
