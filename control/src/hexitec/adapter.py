"""
Adapter for Hexitec ODIN control.

This class implements an adapter used for Hexitec

Christian Angelsen, STFC Detector Systems Software Group
"""
import logging
import time

from concurrent import futures
from tornado.ioloop import IOLoop

from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types,
                                   response_types)
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.util import convert_unicode_to_string, decode_request_body
from odin.adapters.system_info import SystemInfo
from json.decoder import JSONDecodeError
import json

from .HexitecFem import HexitecFem
from .HexitecDAQ import HexitecDAQ


class HexitecAdapter(ApiAdapter):
    """
    Hexitec adapter class for the ODIN server.

    Adapter provides ODIN clients with information about the Hexitec system.
    """

    def __init__(self, **kwargs):
        """
        Initialize the HexitecAdapter object.

        This constructor initializes the HexitecAdapter object.

        :param kwargs: keyword arguments specifying options
        """
        # Initialise superclass
        super(HexitecAdapter, self).__init__(**kwargs)

        self.hexitec = Hexitec(self.options)

        self.adapters = {}

        logging.debug('HexitecAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """
        Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object with the appropriate response
        """
        content_type = "application/json"
        status_code = 200
        response = {}
        request = ApiAdapterRequest(None, accept="application/json")
        # Check adapters if path isn't empty
        #   e.g. If asking for /api/0.1/hexitec/fr/status/frames,
        #                   path = "fr/status/frames"
        #        Compare:      /api/0.1/hexitec/, path = ""
        checkAdapters = True if len(path) > 0 else False
        try:
            if checkAdapters:
                for name, adapter in self.adapters.items():
                    if path.startswith(name):
                        tokens = path.split("/")
                        path = "/".join(tokens[1:])
                        response = adapter.get(path=path, request=request).data
                        logging.debug(response)
                        return ApiAdapterResponse(response, content_type=content_type,
                                                  status_code=status_code)

            # No matching adapter found, try Hexitec member:
            response = self.hexitec.get(path)
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """
        Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object with the appropriate response
        """
        content_type = 'application/json'
        status_code = 200
        response = {}
        checkAdapters = True if len(path) > 0 else False
        requestSent = False
        # print("   put, Path: {}".format(path))
        # print("     request: {}".format(request))
        try:
            if checkAdapters:
                for name, adapter in self.adapters.items():
                    if path.startswith(name):

                        relative_path = path.split(name + '/')
                        reply = adapter.put(path=relative_path[1], request=request)
                        requestSent = True
                        if reply.status_code != 200:
                            status_code = reply.status_code
                            response = reply.data
                            logging.debug(response)
                            return ApiAdapterResponse(response, content_type=content_type,
                                                      status_code=status_code)

            # Only pass request to Hexitec member if no matching adapter found
            if requestSent is False:
                data = convert_unicode_to_string(decode_request_body(request))
                self.hexitec.set(path, data)
                response = self.hexitec.get(path)
        except HexitecError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):
        """
        Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'HexitecAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    def initialize(self, adapters):
        """Get references to required adapters and pass these to classes needing them."""
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        # Pass adapter list to Hexitec class:
        self.hexitec.initialize(self.adapters)


class HexitecError(Exception):
    """Simple Exception class for Hexitec to wrap lower-level exceptions."""

    pass


class Hexitec():
    """Hexitec: Class that extracts and stores information about system-level parameters."""

    # Thread executor used for background tasks
    thread_executor = futures.ThreadPoolExecutor(max_workers=3)

    CONTROL_DIR_NAME = 'control_config'
    DEFAULT_CONTROL_DIR = '/hxt_sw/install/config/control/'
    DATA_DIR_NAME = 'data_config'
    DEFAULT_DATA_DIR = '/hxt_sw/install/config/data/'

    def __init__(self, options):
        """Initialise the Hexitec object.

        This constructor initialises the Hexitec object, building a
        parameter tree and launching a background task if enabled
        """
        defaults = HexitecDetectorDefaults()
        self.file_dir = options.get("save_dir", defaults.save_dir)
        self.file_name = options.get("save_file", defaults.save_file)
        self.number_frames = options.get("acquisition_num_frames", defaults.number_frames)
        self.number_frames_to_request = self.number_frames
        self.total_delay = 0.0
        # Backup number_frames as first initialisation temporary sets number_frames = 2
        self.backed_up_number_frames = self.number_frames

        self.duration = 1
        self.duration_enable = False

        if options.get(self.CONTROL_DIR_NAME, False):
            self.control_config_path = options.get(self.CONTROL_DIR_NAME, "")
        else:
            logging.debug("Setting default control directory: '%s'", self.DEFAULT_CONTROL_DIR)
            self.control_config_path = self.DEFAULT_CONTROL_DIR

        if options.get(self.DATA_DIR_NAME, False):
            self.data_config_path = options.get(self.DATA_DIR_NAME, "")
        else:
            logging.debug("Setting default data directory: '%s'", self.DEFAULT_DATA_DIR)
            self.data_config_path = self.DEFAULT_DATA_DIR

        self.daq = HexitecDAQ(self, self.file_dir, self.file_name)

        self.adapters = {}

        self.fem = None
        for key, value in options.items():
            if "fem" in key:
                fem_info = value.split(',')
                fem_info = [(i.split('=')[0], i.split('=')[1])
                            for i in fem_info]
                fem_dict = {fem_key.strip(): fem_value.strip()
                            for (fem_key, fem_value) in fem_info}
                logging.debug("From options: {}".format(fem_dict))
                self.fem = HexitecFem(
                    self,
                    fem_dict
                )
        if not self.fem:
            logging.error("Using default HexitecFem values!")
            fem_dict = {
                "control_interface": defaults.fem["control_interface"],
                "camera_ctrl_ip": defaults.fem["camera_ctrl_ip"]
            }
            self.fem = HexitecFem(
                parent=self,
                config=fem_dict
            )
        self.fem_health = True

        self.acquisition_in_progress = False

        # Watchdog variables
        self.daq_idle_timeout = 6

        # Store initialisation time
        self.init_time = time.time()

        self.system_health = True
        self.status_message = ""
        self.status_error = ""
        self.elog = ""
        self.number_nodes = 1
        # Software states:
        #   Cold, Environs, Initialising, Offsets, Disconnected,
        #   Idle, Ready, Acquiring, Error, Cleared
        self.software_state = "Cold"
        self.cold_initialisation = True

        detector = ParameterTree({
            "fem": self.fem.param_tree,
            "daq": self.daq.param_tree,
            "connect_hardware": (None, self.connect_hardware),
            "initialise_hardware": (None, self.initialise_hardware),
            "disconnect_hardware": (None, self.disconnect_hardware),
            "save_odin": (None, self.save_odin),
            "load_odin": (None, self.load_odin),
            "collect_offsets": (None, self._collect_offsets),
            "commit_configuration": (None, self.commit_configuration),
            "software_state": (lambda: self.software_state, None),
            "cold_initialisation": (lambda: self.cold_initialisation, None),
            "hv_on": (None, self.hv_on),
            "hv_off": (None, self.hv_off),
            "environs": (None, self.environs),
            "reset_error": (None, self.reset_error),
            "acquisition": {
                "number_frames": (lambda: self.number_frames, self.set_number_frames),
                "duration": (lambda: self.duration, self.set_duration),
                "duration_enable": (lambda: self.duration_enable, self.set_duration_enable),
                "start_acq": (None, self.acquisition),
                "stop_acq": (None, self.cancel_acquisition)
            },
            "status": {
                "system_health": (lambda: self.system_health, None),
                "status_message": (lambda: self.status_message, None),
                "status_error": (lambda: self.status_error, None),
                "elog": (lambda: self.elog, self.set_elog),
                "fem_health": (lambda: self.fem_health, None),
                "number_nodes": (lambda: self.number_nodes, self.set_number_nodes)
            }
        })

        self.system_info = SystemInfo()

        # Store xtek metadata
        self.xtek_meta = {}

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            "xtek_meta": (lambda: self.xtek_meta, self.update_meta),
            "system_info": self.system_info.param_tree,
            "detector": detector
        })

        self.odin_config_file = self.control_config_path + "odin_config.json"

        self._start_polling()

    def update_meta(self, meta):
        """Save to parameter tree meta data PUT by Manchester."""
        self.xtek_meta = meta

    def _start_polling(self):
        IOLoop.instance().add_callback(self.polling)

    def polling(self):  # pragma: no cover
        """Poll FEM for status.

        Check if acquisition completed (if initiated), for error(s) and
        whether DAQ watchdog timed out.
        """
        # Poll FEM acquisition & health status
        self.poll_fem()

        # Monitor HexitecDAQ rate of frames_processed updated.. (Break if stalled)
        if self.daq.processing_interruptable:
            self.check_daq_watchdog()

        IOLoop.instance().call_later(1.0, self.polling)

    def get_frames_processed(self):
        """Get number of frames processed across node(s)."""
        status = self._get_od_status("fp")
        frames_processed = 0
        for index in status:
            # rank = index.get('hdf', None).get('rank')
            # frames = index.get('histogram').get('frames_processed')
            # print("    g_f_p(), rank: {} frames_processed: {}".format(rank, frames))
            frames_processed = frames_processed + index.get('histogram').get('frames_processed')
        return frames_processed

    def poll_fem(self):
        """Poll FEM for acquisition and health status."""
        if self.fem.acquisition_completed:
            frames_processed = self.get_frames_processed()
            # Check all frames finished processed
            if (frames_processed == self.number_frames):
                # Reset FEM's acquisiton status ahead of future acquisitions
                self.fem.acquisition_completed = False
        fem_health = self.fem.get_health()
        self.fem_health = fem_health
        self.status_error = self.fem._get_status_error()
        self.status_message = self.fem._get_status_message()
        self.system_health = self.system_health and self.fem_health

    def check_daq_watchdog(self):
        """Monitor DAQ's frames_processed while data processed.

        Ensure frames_processed increments, completes within reasonable time of acquisition.
        Failure to do so indicate missing/dropped packet(s), stop processing if stalled.
        """
        if self.daq.in_progress:
            idle_time = time.time() - self.daq.processing_timestamp
            # print("  {} -> check_daq_watchdog() checking.. delta: {}".format(
            #      self.daq.debug_timestamp(), idle_time))
            if (idle_time > self.daq_idle_timeout):
                # DAQ: Timed out waiting for next frame to process
                self.shutdown_processing()
                logging.warning("DAQ processing timed out; Saw %s expected %s frames" %
                                (self.daq.frames_processed, self.daq.number_frames))
                self.fem._set_status_error("Processing timed out: {0:.2f} seconds \
                    (exceeded {1:.2f}); Expected {2} got {3} frames\
                        ".format(idle_time, self.daq_idle_timeout,
                                 self.daq.number_frames, self.daq.frames_processed))
                self.fem._set_status_message("Processed frames, some packet(s) loss")

    def shutdown_processing(self):
        """Stop processing in DAQ."""
        self.daq.shutdown_processing = True
        self.acquisition_in_progress = False

    def _get_od_status(self, adapter):
        """Get status from adapter."""
        try:
            request = ApiAdapterRequest(None, content_type="application/json")
            response = self.adapters[adapter].get("status", request)
            response = response.data["value"]
        except KeyError:
            logging.warning("%s Adapter Not Found" % adapter)
            response = [{"Error": "Adapter {} not found".format(adapter)}]
        finally:
            return response

    def connect_hardware(self, msg):
        """Connect with hardware."""
        self.software_state = "Connecting"
        self.fem.connect_hardware(msg)

    def initialise_hardware(self, msg):
        """Initialise hardware."""
        self.fem.initialise_hardware(msg)
        # Wait for fem initialisation
        IOLoop.instance().call_later(0.5, self.monitor_fem_progress)

    def disconnect_hardware(self, msg):
        """Disconnect FEM's hardware connection."""
        if self.daq.in_progress:
            # Stop hardware if still in acquisition
            if self.fem.hardware_busy:
                self.cancel_acquisition()
            # Reset daq
            self.shutdown_processing()
            # Allow processing to shutdown before disconnecting hardware
            IOLoop.instance().call_later(0.2, self.fem.disconnect_hardware)
        else:
            # Nothing in progress, disconnect hardware
            self.fem.disconnect_hardware(msg)

    def strip_base_path(self, path, keyword):
        """Remove base path from path.

        Removes everything up to but not including 'keyword' from path.
        i.e. if keyword="data/" and path='/hxt_sw/install/config/data/m_2x6.txt'
        then function returns 'm_2x6.txt'
        """
        return path.split(keyword)[-1]

    def save_odin(self, msg):
        """Save Odin's settings to file."""
        config = {}
        config["daq/addition_enable"] = self.daq.addition_enable
        config["daq/bin_end"] = self.daq.bin_end
        config["daq/bin_start"] = self.daq.bin_start
        config["daq/bin_width"] = self.daq.bin_width
        config["daq/calibration_enable"] = self.daq.calibration_enable
        config["daq/compression_type"] = self.daq.compression_type
        config["daq/discrimination_enable"] = self.daq.discrimination_enable
        config["daq/file_dir"] = self.daq.file_dir
        config["daq/file_name"] = self.daq.file_name
        config["daq/gradients_filename"] = self.strip_base_path(self.daq.gradients_filename, "data/")
        config["daq/image_frequency"] = self.daq.image_frequency
        config["daq/intercepts_filename"] = self.strip_base_path(self.daq.intercepts_filename,
                                                                 "data/")
        config["daq/lvframes_dataset_name"] = self.daq.lvframes_dataset_name
        config["daq/lvframes_frequency"] = self.daq.lvframes_frequency
        config["daq/lvframes_per_second"] = self.daq.lvframes_per_second
        config["daq/lvspectra_frequency"] = self.daq.lvspectra_frequency
        config["daq/lvspectra_per_second"] = self.daq.lvspectra_per_second
        config["daq/max_frames_received"] = self.daq.max_frames_received
        config["daq/pass_processed"] = self.daq.pass_processed
        config["daq/pass_raw"] = self.daq.pass_raw
        config["daq/pixel_grid_size"] = self.daq.pixel_grid_size
        config["daq/threshold_filename"] = self.strip_base_path(self.daq.threshold_filename, "data/")
        config["daq/threshold_lower"] = self.daq.threshold_lower
        config["daq/threshold_mode"] = self.daq.threshold_mode
        config["daq/threshold_upper"] = self.daq.threshold_upper
        config["daq/threshold_value"] = self.daq.threshold_value
        config["duration"] = self.duration
        config["duration_enable"] = self.duration_enable
        config["fem/hexitec_config"] = self.strip_base_path(self.fem.hexitec_config, "control/")
        config["number_frames"] = self.number_frames
        try:
            with open(self.odin_config_file, "w") as f:
                json.dump(config, f, indent=2, separators=(",", ": "))
        except Exception as e:
            self.fem.flag_error("Saving Odin config", str(e))

    def load_odin(self, msg):
        """Load Odin's settings from file."""
        try:
            with open(self.odin_config_file, "r") as f:
                config = json.load(f)
                self.fem.set_hexitec_config(config["fem/hexitec_config"])
                self.daq.set_file_name(config["daq/file_name"])
                self.daq.set_data_dir(config["daq/file_dir"])
                self.daq._set_addition_enable(config["daq/addition_enable"])
                self.daq._set_pixel_grid_size(config["daq/pixel_grid_size"])
                self.daq._set_calibration_enable(config["daq/calibration_enable"])
                self.daq._set_gradients_filename(config["daq/gradients_filename"])
                self.daq._set_intercepts_filename(config["daq/intercepts_filename"])
                self.daq._set_discrimination_enable(config["daq/discrimination_enable"])
                self.daq._set_bin_end(config["daq/bin_end"])
                self.daq._set_bin_start(config["daq/bin_start"])
                self.daq._set_bin_width(config["daq/bin_width"])
                self.daq._set_max_frames_received(config["daq/max_frames_received"])
                self.daq._set_pass_processed(config["daq/pass_processed"])
                self.daq._set_pass_raw(config["daq/pass_raw"])
                self.daq._set_lvframes_dataset_name(config["daq/lvframes_dataset_name"])
                self.daq._set_lvframes_frequency(config["daq/lvframes_frequency"])
                self.daq._set_lvframes_per_second(config["daq/lvframes_per_second"])
                self.daq._set_lvspectra_frequency(config["daq/lvspectra_frequency"])
                self.daq._set_lvspectra_per_second(config["daq/lvspectra_per_second"])
                self.daq._set_threshold_lower(config["daq/threshold_lower"])
                self.daq._set_threshold_upper(config["daq/threshold_upper"])
                self.daq._set_image_frequency(config["daq/image_frequency"])
                self.daq._set_threshold_filename(config["daq/threshold_filename"])
                self.daq._set_threshold_mode(config["daq/threshold_mode"])
                self.daq._set_threshold_value(config["daq/threshold_value"])
                self.daq._set_compression_type(config["daq/compression_type"])
                if config["duration_enable"]:
                    self.set_duration(config["duration"])
                    self.set_duration_enable(config["duration_enable"])
                else:
                    self.set_number_frames(config["number_frames"])
                    self.set_duration_enable(config["duration_enable"])
        except FileNotFoundError as e:
            self.fem.flag_error("Loading Odin config - file missing", str(e))
        except JSONDecodeError as e:
            self.fem.flag_error("Loading Odin config - Bad json?", str(e))
        except Exception as e:
            self.fem.flag_error("Loading default Odin values", str(e))

    def set_duration_enable(self, duration_enable):
        """Set duration enable, calculating number of frames accordingly."""
        self.duration_enable = duration_enable
        self.fem.set_duration_enable(duration_enable)
        # Ensure DAQ, FEM have correct duration/number of frames configured
        if duration_enable:
            self.set_duration(self.duration)
        else:
            self.set_number_frames(self.number_frames)

    def round_to_even(self, n):
        """Round (upwards) integer to even integer."""
        return (2 * round(0.4+n/2))

    def set_number_frames(self, frames):
        """Set number of frames in DAQ, FEM."""
        # Ensure even number of frames
        if frames % 2:
            frames = self.round_to_even(frames)
        if frames <= 0:
            raise ParameterTreeError("frames must be above 0!")
        self.number_frames = frames
        # Update number of frames in Hardware, and (via DAQ) in histogram and hdf plugins
        self.fem.set_number_frames(self.number_frames)
        self.daq.set_number_frames(self.number_frames)

    def set_duration(self, duration):
        """Set duration, calculate frames from frame rate and update DAQ, FEM."""
        if duration <= 0:
            raise ParameterTreeError("duration must be above 0!")
        self.duration = duration
        self.fem.set_duration(self.duration)
        self.number_frames = self.fem.get_number_frames()
        self.daq.set_number_frames(self.number_frames)

    def set_elog(self, entry):
        """Set the elog entry provided by the user through the UI."""
        self.elog = entry

    def set_number_nodes(self, number_nodes):
        """Set number of nodes."""
        self.number_nodes = number_nodes
        self.daq.set_number_nodes(self.number_nodes)

    def initialize(self, adapters):
        """Get references to adapters, and pass these to the classes that need to use them."""
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        self.daq.initialize(self.adapters)

    def acquisition(self, put_data=None):
        """Instruct DAQ and FEM to acquire data."""
        # Clear (any previous) daq error
        self.daq.in_error = False

        if self.daq.in_progress:
            logging.warning("Cannot Start Acquistion: Already in progress")
            self.fem._set_status_error("Cannot Start Acquistion: Already in progress")
            return

        if not self.daq.prepare_odin():
            logging.error("Odin's frameReceiver/frameProcessor not ready")
            return

        self.total_delay = 0
        self.number_frames_to_request = self.number_frames

        # Issue reset to histogram
        command = "config/histogram/reset_histograms"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(1)
        self.adapters["fp"].put(command, request)

        # Issue reset to summed_image
        command = "config/summed_image/reset_image"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(1)
        self.adapters["fp"].put(command, request)

        # Reset FR(s) statistics
        command = "command/reset_statistics"
        request = ApiAdapterRequest("", content_type="application/json")
        self.adapters["fr"].put(command, request)

        self.daq.prepare_daq(self.number_frames)
        # Acquisition starts here
        self.acquisition_in_progress = True
        self.software_state = "Acquiring"
        # Wait for DAQ (i.e. file writer) to be enabled before FEM told to collect data
        IOLoop.instance().add_callback(self.await_daq_ready)

    def await_daq_ready(self):
        """Wait until DAQ has configured, enabled file writer."""
        if (self.daq.in_error):
            # Reset state variables
            self.reset_state_variables()
        elif (self.daq.hdf_is_reset is False):
            IOLoop.instance().call_later(0.03, self.await_daq_ready)
        else:
            # Add additional 8 ms delay to ensure file writer's file open before first frame arrives
            IOLoop.instance().call_later(0.08, self.trigger_fem_acquisition)

    def trigger_fem_acquisition(self):
        """Trigger data acquisition in fem."""
        # print(" \n trigger_fem_acquisition() executing")
        # TODO: Temp hack: Prevent frames being 1 (continuous readout) by setting to 2 if it is
        self.number_frames_to_request = 2 if (self.number_frames_to_request == 1) else \
            self.number_frames_to_request
        self.fem.set_number_frames(self.number_frames_to_request)
        self.fem.collect_data()
        IOLoop.instance().call_later(self.total_delay, self.monitor_fem_progress)

    def monitor_fem_progress(self):
        """Check fem hardware progress.

        Busy either:
        -Initialising
        -Waiting for data collection to complete
        """
        # print("\n adpt.monitor_fem_progress() called")
        if (self.fem.hardware_busy):
            # Still sending data
            IOLoop.instance().call_later(0.5, self.monitor_fem_progress)
            return
        # print("\n adpt.monitor_fem_progress() fem done")

        self.reset_state_variables()

    def reset_state_variables(self):
        """Reset state variables.

        Utilised by await_daq_ready(), monitor_fem_progress()
        """
        self.acquisition_in_progress = False

    def cancel_acquisition(self, put_data=None):
        """Cancel ongoing acquisition in Software.

        Not yet possible to stop FEM, mid-acquisition
        """
        self.fem.stop_acquisition = True
        # Inject End of Acquisition Frame
        command = "config/inject_eoa"
        request = ApiAdapterRequest("", content_type="application/json")
        self.adapters["fp"].put(command, request)
        self.shutdown_processing()
        self.software_state = "Idle"
        # print("  {} -> adp.cancel_acq() SW_date = Idle".format(self.daq.debug_timestamp()))

    def _collect_offsets(self, msg):
        """Instruct FEM to collect offsets."""
        self.fem.collect_offsets()

    def commit_configuration(self, msg):
        """Push HexitecDAQ's 'config/' ParameterTree settings into FP's plugins."""
        try:
            if self.fem.prepare_hardware():
                self.daq.commit_configuration()
                # Clear cold initialisation if first config commit
                if self.cold_initialisation:
                    self.cold_initialisation = False
        except Exception as e:
            self.fem.flag_error(str(e))

    def hv_on(self, msg):
        """Switch HV on."""
        try:
            self.fem.hv_on()
        except Exception as e:
            self.fem.flag_error(str(e))

    def hv_off(self, msg):
        """Switch HV off."""
        try:
            self.fem.hv_off()
        except Exception as e:
            self.fem.flag_error(str(e))

    def environs(self, msg):
        """Readout environmental data."""
        self.fem.environs()

    def reset_error(self, msg):
        """Reset error."""
        self.fem.reset_error()
        # Reset system status
        self.status_error = ""
        self.status_message = ""
        self.system_health = True
        self.software_state = "Cleared"

    def get(self, path):
        """
        Get the parameter tree.

        This method returns the parameter tree for use by clients via the Hexitec adapter.

        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path)

    def set(self, path, data):
        """
        Set parameters in the parameter tree.

        This method simply wraps underlying ParameterTree method so that an exception can be
        re-raised with an appropriate HexitecError.

        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise HexitecError(e)


class HexitecDetectorDefaults():
    """Class defining Hexitec class default values."""

    def __init__(self):
        """Initialise member variables."""
        self.save_dir = "/tmp/"
        self.save_file = "a"
        self.number_frames = 10
        self.fem = {
            "control_interface": "enp94s0f2",
            "camera_ctrl_ip": "10.0.3.1"
        }
