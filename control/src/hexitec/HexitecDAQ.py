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
from ast import literal_eval
import collections.abc
import numpy as np
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
    COMPRESSIONOPTIONS = ["none", "blosc"]

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
        index = cwd.rfind("control")
        self.base_path = cwd[:index]

        # ParameterTree variables

        self.sensors_layout = "2x6"
        self.compression_type = "none"

        # Note that these four enable(s) are cosmetic only - written as meta data
        #   actual control is exercised by odin_server.js via sequence config files
        #   loading select(ed) plugins
        self.addition_enable = False
        self.discrimination_enable = False
        self.calibration_enable = False
        self.next_frame_enable = False

        self.pixel_grid_size = 3
        self.gradients_filename = self.base_path + "data/config/m_2x6.txt"
        self.intercepts_filename = self.base_path + "data/config/c_2x6.txt"
        self.bin_end = 8000
        self.bin_start = 0
        self.bin_width = 10.0
        self.number_histograms = int((self.bin_end - self.bin_start) / self.bin_width)

        self.max_frames_received = 10
        self.pass_processed = False
        self.pass_raw = False

        # Look at histogram/hdf to determine when processing finished:
        self.plugin = "histogram"
        self.master_dataset = "spectra_bins"
        self.extra_datasets = []
        # Processing timeout variables, support adapter's watchdog
        self.processed_timestamp = 0
        self.frames_processed = 0
        self.shutdown_processing = False

        self.lvframes_dataset_name = "raw_frames"
        self.lvframes_socket_addr = "tcp://192.168.0.52:5020"
        self.lvframes_frequency = 0
        self.lvframes_per_second = 2

        self.lvspectra_dataset_name = "summed_spectra"
        self.lvspectra_socket_addr = "tcp://192.168.0.52:5021"
        self.lvspectra_frequency = 0
        self.lvspectra_per_second = 1

        self.threshold_lower = 0
        self.threshold_upper = 4400
        self.image_frequency = 1

        self.threshold_filename = self.base_path + "data/config/thresh_2x6.txt"
        self.threshold_mode = "value"
        self.threshold_value = 120

        self.rows, self.columns = 160, 160
        self.pixels = self.rows * self.columns
        self.number_frames = 10
        self.number_nodes = 2   # 1
        # Status variables
        self.in_error = False
        self.daq_ready = False
        self.frames_received = 0
        self.processed_remaining = self.number_frames - self.frames_processed
        self.received_remaining = self.number_frames - self.frames_received

        # Diagnostics
        self.daq_start_time = 0
        self.fem_not_busy = 0
        self.daq_stop_time = 0

        self.param_tree = ParameterTree({
            "diagnostics": {
                "daq_start_time": (lambda: self.daq_start_time, None),
                "daq_stop_time": (lambda: self.daq_stop_time, None),
                "fem_not_busy": (lambda: self.fem_not_busy, None)
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
            "status": {
                "in_progress": (lambda: self.in_progress, None),
                "daq_ready": (lambda: self.daq_ready, None),
                "frames_expected": (lambda: self.number_frames, None),
                "frames_received": (lambda: self.frames_received, None),
                "frames_processed": (lambda: self.frames_processed, None),
                "processed_remaining": (lambda: self.processed_remaining, None),
                "received_remaining": (lambda: self.received_remaining, None)
            },
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
                    "pass_processed": (lambda: self.pass_processed, self._set_pass_processed),
                    "pass_raw": (lambda: self.pass_raw, self._set_pass_raw)
                },
                "lvframes": {
                    "dataset_name": (lambda: self.lvframes_dataset_name,
                                     self._set_lvframes_dataset_name),
                    "frame_frequency": (lambda: self.lvframes_frequency,
                                        self._set_lvframes_frequency),
                    "live_view_socket_addr": (lambda: self.lvframes_socket_addr,
                                              self._set_lvframes_socket_addr),
                    "per_second": (lambda: self.lvframes_per_second,
                                   self._set_lvframes_per_second)
                },
                "lvspectra": {
                    "dataset_name": (lambda: self.lvspectra_dataset_name,
                                     self._set_lvspectra_dataset_name),
                    "frame_frequency": (lambda: self.lvspectra_frequency,
                                        self._set_lvspectra_frequency),
                    "live_view_socket_addr": (lambda: self.lvspectra_socket_addr,
                                              self._set_lvspectra_socket_addr),
                    "per_second": (lambda: self.lvspectra_per_second,
                                   self._set_lvspectra_per_second)
                },
                "next_frame": {
                    "enable": (lambda: self.next_frame_enable, self._set_next_frame_enable)
                },
                "summed_image": {
                    "threshold_lower": (lambda: self.threshold_lower,
                                        self._set_threshold_lower),
                    "threshold_upper": (lambda: self.threshold_upper,
                                        self._set_threshold_upper),
                    "image_frequency": (lambda: self.image_frequency,
                                        self._set_image_frequency)
                },
                "threshold": {
                    "threshold_filename": (lambda: self.threshold_filename,
                                           self._set_threshold_filename),
                    "threshold_mode": (lambda: self.threshold_mode, self._set_threshold_mode),
                    "threshold_value": (lambda: self.threshold_value, self._set_threshold_value)
                }
            },
            "compression_type": (self._get_compression_type, self._set_compression_type),
            "sensors_layout": (self._get_sensors_layout, self._set_sensors_layout)
        })
        self.update_rows_columns_pixels()
        # Placeholder for GenerateConfigFiles instance generating json files
        self.gcf = None

    def initialize(self, adapters):
        """Initialise adapters and related parameter tree entries."""
        try:
            self.adapters["fp"] = adapters['fp']
            self.adapters["fr"] = adapters['fr']
            self.adapters["file_interface"] = adapters['file_interface']
        except KeyError as e:
            logging.error("The odin_server config file missing %s entry" % e)
        self.get_config_file("fp")
        self.get_config_file("fr")
        self.is_initialised = True

    def prepare_odin(self):
        """Ensure the odin data FP and FR are configured."""
        logging.debug("Setting up Acquisition")
        fr_status = self.get_adapter_status("fr")
        fp_status = self.get_adapter_status("fp")
        if self.are_processes_connected(fr_status) is False:
            self.parent.fem.flag_error("Frame Receiver(s) not connected!")
            self.in_error = True
            return False
        elif self.are_processes_configured(fr_status, "fr") is False:
            self.parent.fem.flag_error("Frame Receiver(s) not configured!")
            self.in_error = True
            return False
        elif self.are_buffers_available(fr_status) is False:
            self.parent.fem.flag_error("FR buffers not empty!")
            self.in_error = True
            return False
        else:
            logging.debug("Frame Receiver(s) connected and configured")

        if self.are_processes_connected(fp_status) is False:
            self.parent.fem.flag_error("Frame Processor(s) not connected!")
            self.in_error = True
            return False
        elif self.are_processes_configured(fp_status, "fp") is False:
            self.parent.fem.flag_error("Frame Processor(s) not configured!")
            self.in_error = True
            return False
        else:
            logging.debug("Frame Processor(s) connected and configured")
        # DAQ ready only if no data collection in progress
        if not self.in_progress:
            self.daq_ready = True
        return True

    def are_buffers_available(self, fr_status):
        """Determine whether all frameReceiver(s)' buffers are empty."""
        all_buffers_empty = True
        for node in fr_status:
            if (node['buffers']['empty'] == 0):
                all_buffers_empty = False
        return all_buffers_empty

    def prepare_daq(self, number_frames):
        """Turn on File Writing."""
        self.frames_processed = 0
        self.frames_received = 0
        # Count hdf's frames_processed across node(s)
        self.frame_start_acquisition = self.get_total_frames_processed('hdf')
        self.number_frames = number_frames
        logging.info("FRAME START ACQ: %d END ACQ: %d",
                     self.frame_start_acquisition,
                     self.frame_start_acquisition + number_frames)
        self.in_progress = True
        # Reset timeout watchdog
        self.processed_timestamp = time.time()
        logging.debug("Starting File Writer")
        self.set_file_writing(True)
        # Diagnostics:
        self.daq_start_time = '%s' % (datetime.now().strftime(HexitecDAQ.DATE_FORMAT))
        # About to receive fem data, daq therefore now busy
        self.daq_ready = False
        # Wait while fem finish sending data
        IOLoop.instance().call_later(1.3, self.acquisition_check_loop)

    def acquisition_check_loop(self):
        """Wait for acquisition to complete without blocking current thread."""
        bBusy = self.parent.fem.hardware_busy
        if bBusy:
            self.frames_received = self.get_total_frames_received()
            self.frames_processed = self.get_total_frames_processed(self.plugin)
            self.processed_remaining = self.number_frames - self.frames_processed
            self.received_remaining = self.number_frames - self.frames_received
            # print("\n0\t rxd {} left: {} proc'd {} left: {}\n".format(
            #     self.frames_received, self.received_remaining, self.frames_processed,
            #     self.processed_remaining))
            IOLoop.instance().call_later(0.5, self.acquisition_check_loop)
        else:
            self.fem_not_busy = '%s' % (datetime.now().strftime(HexitecDAQ.DATE_FORMAT))
            # Reset timeout watchdog
            self.processed_timestamp = time.time()
            IOLoop.instance().call_later(0.5, self.processing_check_loop)

    def processing_check_loop(self):
        """Check that the processing has completed."""
        # Check HDF/histogram processing progress
        total_frames_processed = self.get_total_frames_processed(self.plugin)
        self.frames_received = self.get_total_frames_received()
        self.received_remaining = self.number_frames - self.frames_received
        # print("\nX\t rxd {} left: {} proc'd {} left: {}\n".format(
        #     self.frames_received, self.received_remaining, self.frames_processed,
        #     self.processed_remaining))
        if total_frames_processed == self.number_frames:
            IOLoop.instance().add_callback(self.flush_data)
            logging.debug("Acquisition Complete")
            # All required frames acquired; if either of frames based datasets
            #   selected, wait for hdf file to close
            IOLoop.instance().call_later(0.1, self.hdf_closing_loop)
        else:
            # Not all frames processed yet; Check data still in flow
            if total_frames_processed == self.frames_processed:
                # No frames processed in at least 0.5 sec, did processing time out?
                if self.shutdown_processing:
                    self.shutdown_processing = False
                    self.in_progress = False
                    self.daq_ready = True
                    # Don't turn off FileWriterPlugin; EndOfAcquisition to flush out histograms
                    self.daq_stop_time = '%s' % (datetime.now().strftime(HexitecDAQ.DATE_FORMAT))
                    self.file_writing = False
                    return
            else:
                # Data still bein' processed
                self.processed_timestamp = time.time()
                self.frames_processed = total_frames_processed
                self.processed_remaining = self.number_frames - self.frames_processed
                # print("\n1\t rxd {} (left: {}) proc'd {} left: {}\n".format(
                #     self.frames_received, self.received_remaining, self.frames_processed,
                #     self.processed_remaining))
            # Wait 0.5 seconds and check again
            IOLoop.instance().call_later(.5, self.processing_check_loop)

    def flush_data(self):
        """Flush out histograms, ensure complete datasets included."""
        # Inject End of Acquisition Frame
        command = "config/inject_eoa"
        request = ApiAdapterRequest("", content_type="application/json")
        self.adapters["fp"].put(command, request)
        IOLoop.instance().call_later(0.02, self.monitor_eoa_progress)

    def monitor_eoa_progress(self):
        """Check whether End of Acquisition completed."""
        if self.get_eoa_processed_status():
            self.stop_acquisition()
        else:
            IOLoop.instance().call_later(0.25, self.monitor_eoa_progress)

    def stop_acquisition(self):
        """Disable file writing so processing can add local Meta data to file."""
        if self.check_hdf_write_statuses():
            # hdf file still open
            if self.hdf_retry < 5:
                IOLoop.instance().call_later(1.0, self.stop_acquisition)
                self.hdf_retry += 1
                return
            else:
                self.parent.fem.flag_error("DAQ timed out, file didn't close")
        self.hdf_retry = 0
        self.daq_stop_time = '%s' % (datetime.now().strftime(HexitecDAQ.DATE_FORMAT))
        self.set_file_writing(False)
        self.frames_processed = self.get_total_frames_processed(self.plugin)
        self.processed_remaining = self.number_frames - self.frames_processed
        # print("\n2\t rxd {} (left: {}) proc'd {} left: {}\n".format(
        #     self.frames_received, self.received_remaining, self.frames_processed,
        #     self.processed_remaining))

    def check_hdf_write_statuses(self):
        """Check hdf node(s) statuses, return True until all finished writing."""
        fp_statuses = self.get_adapter_status("fp")
        hdf_status = False
        for status in fp_statuses:
            writing = status.get('hdf').get("writing")
            # print("Rank: ", status.get('hdf', None).get('rank'), " hdf writing: ", writing)
            if writing:
                hdf_status = True
        return hdf_status

    def hdf_closing_loop(self):
        """Wait for processing to complete but don't block, before prep to write meta data."""
        if self.check_hdf_write_statuses():
            IOLoop.instance().call_later(0.5, self.hdf_closing_loop)
        else:
            self.hdf_file_location = self.file_dir + self.file_name + '.h5'
            self.prepare_hdf_file()

    def prepare_hdf_file(self):
        """Re-open HDF5 file, prepare meta data."""
        try:
            hdf_file = h5py.File(self.hdf_file_location, 'w')
            self.parent.fem._set_status_message("Reopening file to add meta data..")
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
            self.hdf_retry = 0
            self.in_progress = False
            self.daq_ready = True
            self.parent.fem.flag_error("Error reopening HDF file: %s" % e)
            return

        error_code = 0
        # Create metadata group, add dataset to it and pass to write function
        parent_metadata_group = hdf_file.create_group("hexitec")
        parent_tree_dict = self.parent.param_tree.get('')
        error_code = self.write_metadata(parent_metadata_group, parent_tree_dict, hdf_file)

        # TODO: Hacked until frame_process_adapter updated to use ParameterTree
        hdf_metadata_group = hdf_file.create_group("hdf")
        hdf_tree_dict = self.adapters['fp']._param
        # Only "hexitec" group contain filename entries, ignore return value of write_metadata
        self.write_metadata(hdf_metadata_group, hdf_tree_dict, hdf_file)

        if (error_code == 0):
            self.parent.fem._set_status_message("Meta data added to {}".format(
                self.hdf_file_location))
        else:
            self.parent.fem.flag_error("Meta data writer unable to access file(s)!")

        hdf_file.close()
        self.in_progress = False
        self.daq_ready = True

    def save_dict_contents_to_file(self, hdf_file, path, param_tree_dict):
        """Traverse dictionary, write each key as native type to h5file."""
        for key, item in param_tree_dict.items():
            item = self._convert_values(item)
            if isinstance(item, list):
                if isinstance(item[0], dict):
                    newdict = {}
                    for i in range(len(item)):
                        newdict[key + str(i)] = item[i]
                    item = newdict
                    self.save_dict_contents_to_file(hdf_file, path, {})
                else:
                    if not isinstance(item[0], str):
                        item = np.array(item)
            if isinstance(item, dict):
                self.save_dict_contents_to_file(hdf_file, path + key + '/', item)
            else:
                try:
                    # Do not include errors, log messages (see error log for such details)
                    if key == "errors_history" or key == "log_messages":
                        continue
                    hdf_file[path + key] = item
                except TypeError as e:
                    logging.error("Error: {} Parsing key: {}{} value: {}".format(
                        e, path, key, item))
                    self.parent.fem.flag_error("Parsing key: {}{} value: {}".format(
                        path, key, item), str(e))

    def _convert_values(self, value):
        """Convert values to correct Python types."""
        if isinstance(value, list):
            if len(value) == 0:
                value = ["(empty)"]
            else:
                value = [self._convert_values(v) for v in value]
        elif isinstance(value, dict):
            for key, entry in value.items():
                value[key] = self._convert_values(entry)
        try:
            val = literal_eval(value)
        except Exception:
            val = value
        return str(val) if isinstance(val, type(None)) else val

    def write_metadata(self, metadata_group, param_tree_dict, hdf_file):
        """Write parameter tree(s) and config files as meta data."""
        self.save_dict_contents_to_file(hdf_file, '/', param_tree_dict)

        # Flatten dictionary, before checking whether any config/xml files selected
        param_tree_dict = self._flatten_dict(param_tree_dict)

        # Only write parent's (Hexitec class) parameter tree's config files once
        if metadata_group.name == u'/hexitec':
            # Add additional attribute to record current date
            metadata_group.attrs['runDate'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            # Write the configuration files into the metadata group
            self.config_ds = {}
            str_type = h5py.special_dtype(vlen=str)

            # Write contents of config file, and selected coefficients file(s)
            file_name = ['detector/fem/hexitec_config']
            if self.calibration_enable:
                file_name.append('detector/daq/config/calibration/gradients_filename')
                file_name.append('detector/daq/config/calibration/intercepts_filename')
            if self.threshold_mode == self.THRESHOLDOPTIONS[1]:  # = "filename"
                file_name.append('detector/daq/config/threshold/threshold_filename')

            for param_file in file_name:
                if param_file not in param_tree_dict:
                    print(" *** {} not in parameter tree: {}".format(param_file, param_tree_dict))
                    continue
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
                    return -3
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

    def are_processes_connected(self, status):
        """Check all node(s) connected from 'status' (list of dictionary)."""
        fr_connections = self._is_od_connected(status)
        fr_connected = True
        # Check list of fr connections, any not connected?
        for connection in fr_connections:
            if not connection:
                fr_connected = False
        return fr_connected  # True if all node(s) connected, else False

    def are_processes_configured(self, status, adapter):
        """Check all node(s) configured from 'status' (list of dictionary)."""
        if adapter == "fr":
            configurations = self._is_fr_configured(status)
        elif adapter == "fp":
            configurations = self._is_fp_configured(status)
        else:
            logging.error("'{}' unknown adapter, unknown configuration state".format(adapter))
            return False
        is_configured = True
        # Check list of configurations, any not configured?
        for config in configurations:
            if not config:
                is_configured = False
        return is_configured  # True if all node(s) connected, else False

    def get_total_frames_processed(self, plugin):
        """Count frames_processed across all of 'plugin' process(es)."""
        fp_statuses = self.get_adapter_status("fp")
        # print("get_adapter_status", self.get_adapter_status("fp"))
        frames_processed = 0
        for fp_status in fp_statuses:
            fw_status = fp_status.get(plugin, None).get('frames_processed')
            # print("Rank:", fp_status.get('hdf', None).get('rank'), " frames_proc'd: ", fw_status)
            if fw_status > 0:   # TODO: Sort out this better
                frames_processed = frames_processed + fw_status
        return frames_processed

    def get_eoa_processed_status(self):
        """Check whether End Of Acquisition (eoa) propogated through node(s)' histogram plugin."""
        fp_statuses = self.get_adapter_status("fp")
        eoa_processed = True
        for fp_status in fp_statuses:
            eoa_status = fp_status.get("histogram", None).get('eoa_processed')
            # print("Rank:", fp_status.get('hdf', None).get('rank'), " eoa_processed: ", eoa_status)
            if eoa_status is False:
                eoa_processed = eoa_status
        return eoa_processed

    def get_total_frames_received(self):
        """Count frames received across all frameReceiver(s)."""
        fr_statuses = self.get_adapter_status("fr")
        total_received = 0
        for fr_status in fr_statuses:
            received = fr_status.get("frames", None).get("received", None)
            if received > 0:
                total_received = total_received + received
        # print(" *** FR total received frames: {}".format(total_received))
        return total_received

    def _is_od_connected(self, status=None, adapter=""):
        if status is None:
            # Called from ParameterTree init, build list of node(s)
            status = self.get_connection_status(adapter)
        else:
            # Called by are_processes_connected()
            status_list = []
            for index in status:
                status_list.append(index.get('connected'))
            status = status_list
        return status

    def get_connection_status(self, adapter):
        """Get connection status from adapter."""
        if not self.is_initialised:
            return [{"Error": "Adapter not initialised with references yet"}]
        try:
            return_value = []
            request = ApiAdapterRequest(None, content_type="application/json")
            response = self.adapters[adapter].get("status", request)
            response = response.data["value"]
            for node in response:
                return_value.append(node["connected"])
        except KeyError:
            logging.warning("%s Adapter Not Found" % adapter)
            return_value = [{"Error": "Adapter {} not found".format(adapter)}]
        finally:
            return return_value

    def _is_fr_configured(self, status=None):
        if status is None:
            status = self.get_adapter_status("fr")
        configured = []
        for index in status:
            config_status = index.get("status", {}).get("configuration_complete", False)
            configured.append(config_status)
        return configured

    def _is_fp_configured(self, status=None):
        if status is None:
            status = self.get_adapter_status("fp")
        configured = []
        for index in status:
            config_status = index.get("plugins")  # if plugins key exists, it has been configured
            configured.append(config_status is not None)
        return configured

    def get_adapter_status(self, adapter):
        """Get status from adapter.

        To replace get_od_status()?
        """
        if not self.is_initialised:
            return [{"Error": "Adapter {} not initialised with references yet".format(adapter)}]
        try:
            request = ApiAdapterRequest(None, content_type="application/json")
            response = self.adapters[adapter].get("status", request)
            response = response.data["value"]
        except KeyError:
            logging.warning("%s Adapter Not Found" % adapter)
            response = [{"Error": "Adapter {} not found".format(adapter)}]
        finally:
            return response

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
            return []
        try:
            return_val = []
            request = ApiAdapterRequest(None)
            response = self.adapters['file_interface'].get('', request).data
            self.config_dir = response['config_dir']
            # print("\n get_config_file(), response: {}\n\t ({})".format(response, type(response)))
            for config_file in response["{}_config_files".format(adapter)]:
                if "hexitec" in config_file.lower():
                    return_val.append(config_file)
        except KeyError as key_error:
            logging.warning("KeyError when trying to get config file: %s" % key_error)
            return_val = []
        finally:
            self.config_files[adapter] = return_val
            return return_val

    def set_data_dir(self, directory):
        """Set directory of processed file."""
        self.file_dir = directory

    def set_number_frames(self, number_frames):
        """Set number of frames to be acquired."""
        self.number_frames = number_frames
        self.processed_remaining = self.number_frames - self.frames_processed
        self.received_remaining = self.number_frames - self.frames_received

    def set_number_nodes(self, nodes):
        """Set number of nodes."""
        self.number_nodes = nodes

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
        frame_rate = self.parent.fem.frame_rate
        max_frames_received = round(frame_rate // self.number_nodes)
        self._set_max_frames_received(max_frames_received)
        command = "config/histogram/max_frames_received"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(max_frames_received)
        self.adapters["fp"].put(command, request)

        # Finally, update own file_writing so FEM(s) know the status
        self.file_writing = writing

        # TODO: Implement if each node should accumulate summed images data as a single image
        # # Determine each node(s)' rank, Tell which node's
        # # summed images plugin what frame number it should use
        # fp_statuses = self.get_adapter_status("fp")
        # rank = []
        # node = 0
        # for status in fp_statuses:
        #     current_rank = status.get('hdf', None).get('rank')
        #     # print("Rank: ", current_rank, " hdf writing: ", writing)
        #     rank.append(current_rank)
        #     command = "config/summed_image/" + str(node)
        #     # request = ApiAdapterRequest(current_rank, content_type="application/json")
        #     request.body = "{}".format(current_rank)
        #     self.adapters["fp"].put(command, request)
        # print(" Node(s) rank: {}".format(rank))

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

    def _set_lvframes_dataset_name(self, lvframes_dataset_name):
        self.lvframes_dataset_name = lvframes_dataset_name

    def _set_lvframes_frequency(self, lvframes_frequency):
        if lvframes_frequency < 0:
            raise ParameterTreeError("lvframes_frequency must be positive!")
        self.lvframes_frequency = lvframes_frequency

    def _set_lvframes_socket_addr(self, socket_addr):
        self.lvframes_socket_addr = socket_addr

    def _set_lvframes_per_second(self, lvframes_per_second):
        if lvframes_per_second < 0:
            raise ParameterTreeError("lvframes_per_second must be positive!")
        self.lvframes_per_second = lvframes_per_second

    def _set_lvspectra_dataset_name(self, lvspectra_dataset_name):
        self.lvspectra_dataset_name = lvspectra_dataset_name

    def _set_lvspectra_frequency(self, lvspectra_frequency):
        if lvspectra_frequency < 0:
            raise ParameterTreeError("lvspectra_frequency must be positive!")
        self.lvspectra_frequency = lvspectra_frequency

    def _set_lvspectra_socket_addr(self, socket_addr):
        self.lvspectra_socket_addr = socket_addr

    def _set_lvspectra_per_second(self, lvspectra_per_second):
        if lvspectra_per_second < 0:
            raise ParameterTreeError("lvspectra_per_second must be positive!")
        self.lvspectra_per_second = lvspectra_per_second

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
        if bin_end < 1:
            raise ParameterTreeError("bin_end must be positive!")
        self.bin_end = bin_end
        self.update_histogram_dimensions()

    def _set_bin_start(self, bin_start):
        """Update bin_start and datasets' histograms' dimensions."""
        if bin_start < 0:
            raise ParameterTreeError("bin_start must be positive!")
        self.bin_start = bin_start
        self.update_histogram_dimensions()

    def _set_bin_width(self, bin_width):
        """Update bin_width and datasets' histograms' dimensions."""
        if bin_width <= 0:
            raise ParameterTreeError("bin_width must be positive!")
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

    def _set_pass_raw(self, pass_raw):
        self.pass_raw = pass_raw

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
        if threshold_value < 0:
            raise ParameterTreeError("threshold_value must be positive!")
        self.threshold_value = threshold_value

    def _set_threshold_lower(self, threshold_lower):
        if threshold_lower < 0:
            raise ParameterTreeError("threshold_lower must be positive!")
        self.threshold_lower = threshold_lower

    def _set_threshold_upper(self, threshold_upper):
        if threshold_upper < 0:
            raise ParameterTreeError("threshold_upper must be positive!")
        self.threshold_upper = threshold_upper

    def _set_image_frequency(self, image_frequency):
        if image_frequency < 0:
            raise ParameterTreeError("image_frequency must be positive!")
        self.image_frequency = image_frequency

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

    def _get_compression_type(self):
        return self.compression_type

    def _set_compression_type(self, compression_type):
        if compression_type in self.COMPRESSIONOPTIONS:
            self.compression_type = compression_type
        else:
            error = "Invalid compression type; Valid options: {}".format(self.COMPRESSIONOPTIONS)
            raise ParameterTreeError(error)

    def commit_configuration(self):
        """Generate and sends the FP config files."""
        # Generate JSON config file determining which plugins, the order to chain them, etc
        parameter_tree = self.param_tree.get('')

        # Delete any existing datasets
        command = "config/hdf/delete_datasets"
        request = ApiAdapterRequest("", content_type="application/json")

        response = self.adapters["fp"].put(command, request)
        status_code = response.status_code
        if (status_code != 200):
            error = "Error {} deleting existing datasets in fp adapter".format(status_code)
            self.parent.fem.flag_error(error)

        # Delete any existing datasets
        command = "config/plugin"
        request = ApiAdapterRequest('{"disconnect": "all"}', content_type="application/json")

        response = self.adapters["fp"].put(command, request)
        status_code = response.status_code
        if (status_code != 200):
            error = "Error {} disconnecting plugins from fp adapter".format(status_code)
            self.parent.fem.flag_error(error)

        self.extra_datasets = []
        self.master_dataset = "spectra_bins"

        if self.pass_processed:
            self.master_dataset = "processed_frames"
            self.extra_datasets.append(self.master_dataset)
        if self.pass_raw:
            self.master_dataset = "raw_frames"
            self.extra_datasets.append(self.master_dataset)

        # Enable live view for first node only
        live_view_selected = True

        # Loop over node(s)
        for index in range(self.number_nodes):
            self.gcf = GenerateConfigFiles(parameter_tree, self.number_histograms,
                                           compression_type=self.compression_type,
                                           master_dataset=self.master_dataset,
                                           extra_datasets=self.extra_datasets,
                                           selected_os="CentOS",
                                           live_view_selected=live_view_selected)
            store_config, execute_config, store_string, execute_string = \
                self.gcf.generate_config_files(index)
            live_view_selected = False

            command = "config/store/" + str(index)    # Configure using strings
            request = ApiAdapterRequest(store_string, content_type="application/json")

            response = self.adapters["fp"].put(command, request)
            status_code = response.status_code
            if (status_code != 200):
                error = "Error {} storing plugins config in fp adapter".format(status_code)
                self.parent.fem.flag_error(error)

            command = "config/execute/" + str(index)  # Configure using strings
            request = ApiAdapterRequest(execute_string, content_type="application/json")

            response = self.adapters["fp"].put(command, request)
            status_code = response.status_code
            if (status_code != 200):
                error = "Error {} loading plugins config in fp adapter".format(status_code)
                self.parent.fem.flag_error(error)

        # Allow FP time to process above PUT requests before configuring plugin settings
        IOLoop.instance().call_later(0.4, self.submit_configuration)

    def submit_configuration(self):
        """Send each ParameterTree value to the corresponding FP plugin."""
        # Loop overall plugins in ParameterTree, updating fp's settings except reorder
        for plugin in self.param_tree.tree.get("config"):

            for param_key in self.param_tree.tree['config'].get(plugin):

                # print("                   config/%s/%s" % (plugin, param_key), " -> ",
                #       self.param_tree.tree['config'][plugin][param_key].get(""))

                # Don't send histogram's pass_raw, pass_processed,
                #   since Odin Control do not support bool
                if param_key not in ["pass_processed", "pass_raw"]:

                    command = "config/%s/%s" % (plugin, param_key)

                    payload = self.param_tree.tree['config'][plugin][param_key].get()
                    request = ApiAdapterRequest(str(payload), content_type="application/json")
                    self.adapters["fp"].put(command, request)

        # Which plugin determines when processing finished?
        if (self.pass_raw or self.pass_processed):
            self.plugin = "hdf"
        else:
            self.plugin = "histogram"

        # # Temporary fix: hard code Extended packet headers OFF
        # command = "config/decoder_config/extended_packet_header"
        # request = ApiAdapterRequest("0", content_type="application/json")
        # self.adapters["fr"].put(command, request)
