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
    PROCESSING_NODES = 'processing_nodes'
    ODIN_CONTROL_NODE = "odin_control_node"

    def __init__(self, options):
        """Initialise the Hexitec object.

        This constructor initialises the Hexitec object, building a
        parameter tree and launching a background task if enabled
        """
        defaults = HexitecDetectorDefaults()
        self.file_dir = options.get("save_dir", defaults.save_dir)
        self.file_name = options.get("save_file", defaults.save_file)
        processing_nodes = options.get(self.PROCESSING_NODES, "")
        self.processing_nodes = processing_nodes.replace(" ", "").split(",")
        self.odin_control_node = options.get(self.ODIN_CONTROL_NODE, "")

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

        self.leak_fault = 0
        self.leak_warning = 0
        self.leak_health = True
        self.leak_error = ""
        self.system_health = True
        self.status_message = ""
        self.status_error = ""
        self.leak_fault_counter = 0
        self.elog = ""
        self.number_nodes = 1
        self.archiver_configured = False
        self.archiver_status = 200
        # Software states in alphabetical order:
        #  Acquiring, Cleared, Cold, Connecting, Disconnected, Environs,
        #  Error, Idle, Initialising, Interlocked, Offsets, Ready
        self.software_state = "Cold"
        self.cold_start = True

        detector = ParameterTree({
            "fem": self.fem.param_tree,
            "daq": self.daq.param_tree,
            "connect_hardware": (None, self.connect_hardware),
            "initialise_hardware": (None, self.initialise_hardware),
            "disconnect_hardware": (None, self.disconnect_hardware),
            "save_odin": (None, self.save_odin),
            "load_odin": (None, self.load_odin),
            "collect_offsets": (None, self.collect_offsets),
            "prepare_fem_farm_mode": (None, self.prepare_fem_farm_mode),
            "apply_config": (None, self.apply_config),
            "software_state": (lambda: self.software_state, None),
            "hv_on": (None, self.hv_on),
            "hv_off": (None, self.hv_off),
            "environs": (None, self.environs),
            "reset_error": (None, self.reset_error),
            "acquisition": {
                "number_frames": (lambda: self.number_frames, self.set_number_frames),
                "duration": (lambda: self.duration, self.set_duration),
                "duration_enable": (lambda: self.duration_enable, self.set_duration_enable),
                "start_acq": (None, self.start_acquisition),
                "stop_acq": (None, self.stop_acquisition)
            },
            "status": {
                "system_health": (lambda: self.system_health, None),
                "status_message": (lambda: self.status_message, None),
                "status_error": (lambda: self.status_error, None),
                "elog": (lambda: self.elog, self.set_elog),
                "fem_health": (lambda: self.fem_health, None),
                "number_nodes": (lambda: self.number_nodes, self.set_number_nodes),
                "leak": {
                    "fault": (lambda: bool(self.leak_fault), None),
                    "warning": (lambda: bool(self.leak_warning), None),
                    "leak_error": (self._get_leak_error, None)
                }
            },
            "triggering_frames": (lambda: self.fem.triggering_frames, self.set_triggering_frames),
            "triggering_mode": (lambda: self.fem.triggering_mode, self.set_triggering_mode)
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

        self.start_polling()

    def initialize(self, adapters):
        """Get references to adapters, and pass these to the classes that need to use them."""
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        self.daq.initialize(self.adapters)
        if "archiver" in self.adapters:
            self.archiver_configured = True
        else:
            self.archiver_configured = False

    def update_meta(self, meta):
        """Save to parameter tree meta data PUT by Manchester."""
        self.xtek_meta = meta

    def start_polling(self):
        # Load default Odin values
        IOLoop.instance().call_later(1.0, self.load_odin)
        # Then commence polling
        IOLoop.instance().call_later(2.0, self.polling)

    def polling(self):  # pragma: no cover
        """Poll FEM for status.

        Check if acquisition completed (if initiated), for error(s) and
        whether DAQ watchdog timed out.
        """
        # Poll FEM acquisition & health status
        self.poll_fem()

        if self.archiver_configured:
            # Check archiver running?
            self.check_archiver_running()

        IOLoop.instance().call_later(1.0, self.polling)

    def check_archiver_running(self):
        """Check that archiver is running."""
        archiver_response = self.get_proxy_adapter_data("archiver")
        archiver_status = archiver_response['status']['archiver']['status_code']
        if (archiver_status != 200) and (archiver_status != self.archiver_status):
            self.fem.flag_error(f"Archiver not responding, HTTP code: {archiver_status}")
        self.archiver_status = archiver_status

    def report_leak_detector_error(self, error_message):
        """Report leak detector error.

        Report leak detector error without overwriting any fem error(s).
        """
        logging.error(error_message)
        # Pass error to logging but bypass fem's error reporting
        timestamp = self.fem.create_iso_timestamp()
        self.fem.errors_history.append([timestamp, error_message])
        # Report leak fault to GUI
        self.status_error = error_message
        self._set_leak_error(error_message)
        self.leak_fault_counter += 1

    def get_frames_processed(self):
        """Get number of frames processed across node(s)."""
        status = self._get_od_status("fp")
        frames_processed = 0
        for index in status:
            # rank = index.get('hdf', None).get('rank')
            # frames = index.get('histogram').get('frames_processed')
            # print("    g_f_p(), rank: {} frames_processed: {}".format(rank, frames))
            histogram = index.get('histogram')
            if histogram is not None:
                frames_processed += histogram.get('frames_processed', 0)
        return frames_processed

    def get_proxy_adapter_data(self, adapter):
        """Get leak detector data."""
        response = {"Error": f"Adapter {adapter} not found"}
        try:
            request = ApiAdapterRequest(None, content_type="application/json")
            response = self.adapters[adapter].get("", request)
            response = response.data
        except KeyError:
            logging.warning(f"{adapter} Adapter Not Found")
        finally:
            return response

    def parse_leak_detector_response(self, response):
        """Parse leak detector response."""
        status_code = response['status']['leak']['status_code']
        leak_fault = True
        leak_warning = True
        if status_code == 200:
            leak_fault = response["leak"]["system"]["fault"]
            leak_warning = response["leak"]["system"]["warning"]
        else:
            pass    # Cannot reach leak detector unit
        # print(f"[E SC {status_code} LF {leak_fault} lw {leak_warning}")
        return leak_fault, leak_warning

    def poll_fem(self):
        """Poll FEM for acquisition and health statuses."""
        if self.fem.acquisition_completed:
            frames_processed = self.get_frames_processed()
            # Check all frames finished processed
            if (frames_processed == self.number_frames):
                # Reset FEM's acquisiton status ahead of future acquisitions
                self.fem.acquisition_completed = False
        fem_health = self.fem.get_health()
        self.fem_health = fem_health

        # Any leak detector error?
        try:
            response = self.get_proxy_adapter_data("proxy")
            self.leak_fault, self.leak_warning = self.parse_leak_detector_response(response)

            # If leak detector fault, display in GUI (overrides any fem faults)
            if self.leak_fault:
                self.leak_health = not self.leak_fault
                # print(f"\n [E  IF* LH: {self.leak_health} LF: {self.leak_fault} LW: {self.leak_warning} state: {self.software_state} leak_err: '{self.leak_error}' cond {self.leak_error != ''}")
                # Log leak detector fault only once
                if self.leak_error == "":
                    self.software_state = "Interlocked"
                    # TODO Obtain actual error message from leak detector

                    self.report_leak_detector_error("Leak Detector fault!")
                    self.status_message = "Check leak detector unit!"
            else:
                # print(f"\n [E  ELS LH: {self.leak_health} LF: {self.leak_fault} LW: {self.leak_warning} state: {self.software_state} leak_err: {self.leak_error} cond {self.leak_error != ''}")

                # No leak fault(s), set to Fem's instead (or blank if none)
                self.status_error = self.fem._get_status_error()
                self.status_message = self.fem._get_status_message()
                if (self.leak_fault is False) and (self.leak_health is False):
                    # Leak fault cleared, leak health not yet toggled
                    self.leak_health = not self.leak_fault
                    self._set_leak_error("")
                # Is there a fem error?
                if self.status_error != "":
                    self.software_state = "Error"
                elif (self.status_error == ""):
                    if (self.software_state == "Error") or (self.software_state == "Interlocked"):
                        # Neither of Fem error or leak fault just cleared, update software state
                        self.software_state = "Cleared"
        except KeyError:
            # Log leak detector fault only once
            if self.leak_error == "":
                self.software_state = "Interlocked"
                self.report_leak_detector_error("Leak Detector unreachable!")
                self.status_message = "Check leak detector unit!"

        # Determine system health
        self.system_health = self.fem_health and self.leak_health

    def _set_leak_error(self, error):
        self.leak_error = str(error)

    def _get_leak_error(self):
        return self.leak_error

    def shutdown_processing(self):
        """Stop processing in DAQ."""
        self.daq.shutdown_processing = True
        self.acquisition_in_progress = False

    def _get_od_status(self, adapter):
        """Get status from adapter."""
        response = [{"Error": "Adapter {} not found".format(adapter)}]
        try:
            request = ApiAdapterRequest(None, content_type="application/json")
            response = self.adapters[adapter].get("status", request)
            response = response.data["value"]
        except KeyError:
            logging.warning("%s Adapter Not Found" % adapter)
        finally:
            return response

    def connect_hardware(self, msg=None):
        """Connect with hardware."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't connect with camera")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            # Reset leak fault counter
            self.leak_fault_counter = 0
            # Must ensure Odin data configured before connecting
            if self.cold_start:
                self.prepare_fem_farm_mode()
                self.fem.set_hexitec_config("")
            self.software_state = "Connecting"
            self.fem.connect_hardware(msg)

    def apply_config(self, msg=None):
        """Apply configuration to Odin and VSR Hardware."""
        self.prepare_fem_farm_mode()
        self.fem.set_hexitec_config("")
        self.daq.commit_configuration()
        self.daq.update_fp_configuration = False

    def initialise_hardware(self, msg=None):
        """Initialise hardware."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't initialise Hardware")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            self.fem.initialise_hardware(msg)
            # Wait for fem initialisation
            IOLoop.instance().call_later(0.5, self.monitor_fem_progress)

    def disconnect_hardware(self, msg=None):
        """Disconnect FEM's hardware connection."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't disconnect Hardware")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            # Prevent disconnect if system busy
            if self.fem.hardware_busy:
                error = f"Cannot Disconnect while: {self.software_state}"
                self.fem.flag_error(error)
                raise ParameterTreeError(error)
            else:
                if self.fem.hardware_connected:
                    self.fem.disconnect_hardware(msg)
                else:
                    error = "No connection to disconnect"
                    self.fem.flag_error(error)
                    raise ParameterTreeError(error)

    def strip_base_path(self, path, keyword):
        """Remove base path from path.

        Removes everything up to but not including 'keyword' from path.
        i.e. if keyword="data/" and path='/hxt_sw/install/config/data/m_2x6.txt'
        then function returns 'm_2x6.txt'
        """
        return path.split(keyword)[-1]

    def save_odin(self, msg=None):
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
        config["daq/gradients_filename"] = self.strip_base_path(self.daq.gradients_filename,
                                                                "data/")
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
        config["daq/threshold_filename"] = self.strip_base_path(self.daq.threshold_filename,
                                                                "data/")
        config["daq/threshold_lower"] = self.daq.threshold_lower
        config["daq/threshold_mode"] = self.daq.threshold_mode
        config["daq/threshold_upper"] = self.daq.threshold_upper
        config["daq/threshold_value"] = self.daq.threshold_value
        config["duration"] = self.duration
        config["duration_enable"] = self.duration_enable
        config["fem/hexitec_config"] = self.strip_base_path(self.fem.hexitec_config, "control/")
        config["fem/triggering_mode"] = self.fem.triggering_mode
        config["fem/triggering_frames"] = self.fem.triggering_frames
        config["number_frames"] = self.number_frames
        try:
            with open(self.odin_config_file, "w") as f:
                json.dump(config, f, indent=2, separators=(",", ": "))
        except Exception as e:
            self.fem.flag_error("Saving Odin config", str(e))

    def load_odin(self, msg=None):
        """Load Odin's settings from file."""
        self.daq.check_daq_acquiring_data("odin settings")
        try:
            with open(self.odin_config_file, "r") as f:
                config = json.load(f)
                self.fem.set_hexitec_config(config["fem/hexitec_config"])
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
                self.fem.set_triggering_frames(config["fem/triggering_frames"])
                self.fem.set_triggering_mode(config["fem/triggering_mode"])
                # Set file directory, then filename
                self.daq.set_data_dir(config["daq/file_dir"])
                self.daq.set_file_name(config["daq/file_name"], skip_hw_check=True)
        except FileNotFoundError as e:
            self.fem.flag_error("Loading Odin config - file missing", str(e))
        except JSONDecodeError as e:
            self.fem.flag_error("Loading Odin config - Bad json?", str(e))
        except Exception as e:
            self.fem.flag_error("Loading Odin values", str(e))

    def set_duration_enable(self, duration_enable):
        """Set duration enable, calculating number of frames accordingly."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't update duration enable")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        # Prevent if system busy
        if self.fem.hardware_busy:
            error = f"Cannot update duration enable while: {self.software_state}"
            self.fem.flag_error(error)
            raise ParameterTreeError(error)
        if self.fem.triggering_mode == "triggered":
            error = "Cannot set duration enable in triggered mode"
            self.fem.flag_error(error)
            raise ParameterTreeError(error)
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
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't update number frames")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        # Prevent if system busy
        if self.fem.hardware_busy:
            error = f"Cannot update number of frames while: {self.software_state}"
            self.fem.flag_error(error)
            raise ParameterTreeError(error)
        if self.fem.triggering_mode == "triggered":
            error = "Cannot set number of frames in triggered mode"
            self.fem.flag_error(error)
            raise ParameterTreeError(error)
        # Ensure even number of frames
        if frames % 2:
            frames = self.round_to_even(frames)
        if frames <= 0:
            raise ParameterTreeError("frames must be above 0!")
        self.number_frames = frames
        # Update number of frames in Hardware, and (via DAQ) in histogram and hdf plugins
        self.fem.set_number_frames(self.number_frames)
        self.daq.set_number_frames(self.number_frames)

    def set_triggering_mode(self, triggering_mode):
        """Set triggering mode in FEM."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't update triggering mode")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        # Prevent if system busy
        if self.fem.hardware_busy:
            error = f"Cannot update triggering mode while: {self.software_state}"
            self.fem.flag_error(error)
            raise ParameterTreeError(error)
        self.fem.set_triggering_mode(triggering_mode)

    def set_triggering_frames(self, triggering_frames):
        """Set triggering frames in FEM."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't update triggering frames")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        # Prevent if system busy
        if self.fem.hardware_busy:
            error = f"Cannot update triggering frames while: {self.software_state}"
            self.fem.flag_error(error)
            raise ParameterTreeError(error)
        self.fem.set_triggering_frames(triggering_frames)

    def set_duration(self, duration):
        """Set duration, calculate frames from frame rate and update DAQ, FEM."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't update duration")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        # Prevent if system busy
        if self.fem.hardware_busy:
            error = f"Cannot update duration while: {self.software_state}"
            self.fem.flag_error(error)
            raise ParameterTreeError(error)
        if self.fem.triggering_mode == "triggered":
            error = "Cannot set duration in triggered mode"
            self.fem.flag_error(error)
            raise ParameterTreeError(error)
        if duration <= 0:
            raise ParameterTreeError("duration must be above 0!")
        self.duration = duration
        self.fem.set_duration(self.duration)
        self.number_frames = self.fem.get_number_frames()
        self.daq.set_number_frames(self.number_frames)

    def set_elog(self, entry):
        """Set the elog entry provided by the user through the UI."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't update eLog message")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        # Prevent if system busy
        if self.fem.hardware_busy:
            error = f"Cannot update eLog message while: {self.software_state}"
            self.fem.flag_error(error)
            raise ParameterTreeError(error)
        self.elog = entry

    def set_number_nodes(self, number_nodes):
        """Set number of nodes."""
        # Function called by fem.verify_farm_mode_parameters(), which determines how many nodes
        self.number_nodes = number_nodes
        self.daq.set_number_nodes(self.number_nodes)

    def start_acquisition(self, put_data=None):
        """Instruct DAQ and FEM to acquire data."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't acquire data")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            # Check hardware ready, system initialised before acquisition
            self.fem.check_hardware_ready("acquire data")
            self.fem.check_system_initialised("acquire data")

            if self.daq.update_fp_configuration:
                self.daq.commit_configuration()

            # Clear (any previous) daq error
            self.daq.in_error = False
            self.fem.cancel_acquisition = False

            if self.daq.in_progress:
                error = "Acquistion already in progress"
                self.fem._set_status_error(error)
                raise ParameterTreeError(error)

            # Check Odin data ready, following configuration committed above
            self.daq.prepare_odin()

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

            # Issue reset to threshold plugin, to clear occupancy data
            command = "config/threshold/reset_occupancy"
            request = ApiAdapterRequest(self.file_dir, content_type="application/json")
            request.body = "{}".format(1)
            self.adapters["fp"].put(command, request)

            # Reset FR(s) statistics
            command = "command/reset_statistics"
            request = ApiAdapterRequest("", content_type="application/json")
            self.adapters["fr"].put(command, request)

            IOLoop.instance().add_callback(self.await_daq_configuring_fps)

    def await_daq_configuring_fps(self):
        """Wait until DAQ configured frameProcessor plugin chain(s)."""
        if (self.daq.busy_configuring_fps):
            IOLoop.instance().call_later(0.05, self.await_daq_configuring_fps)
        else:
            self.daq.prepare_daq(self.number_frames)
            # Acquisition starts here
            self.acquisition_in_progress = True
            self.software_state = "Acquiring"
            # Wait for DAQ (i.e. file writer) to be enabled before FEM told to acquire data
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
        if (self.fem.hardware_busy):
            # Still sending data
            IOLoop.instance().call_later(0.5, self.monitor_fem_progress)
            return

        self.reset_state_variables()

    def reset_state_variables(self):
        """Reset state variables.

        Utilised by await_daq_ready(), monitor_fem_progress()
        """
        self.acquisition_in_progress = False

    def stop_acquisition(self, put_data=None):
        """Cancel ongoing acquisition in Software.

        Not yet possible to stop FEM, mid-acquisition
        """
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't cancel acquisition")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            if self.software_state != "Acquiring":
                error = "No acquisition in progress"
                self.fem.flag_error(error)
                raise ParameterTreeError(error)
            else:
                self.fem.cancel_acquisition = True
                # Inject End of Acquisition Frame
                command = "config/inject_eoa"
                request = ApiAdapterRequest("", content_type="application/json")
                self.adapters["fp"].put(command, request)
                self.shutdown_processing()
                self.software_state = "Idle"

    def collect_offsets(self, msg=None):
        """Instruct FEM to collect offsets."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't collect offsets")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            self.fem.run_collect_offsets()

    def prepare_fem_farm_mode(self, msg=None):
        """Instruct fem to load farm mode parameters."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't load fem farm mode")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            try:
                self.fem.prepare_farm_mode()
            except Exception as e:
                error = f"Prepare fem farm mode: {str(e)}"
                self.fem.flag_error(error)
                raise ParameterTreeError(error)

    def hv_on(self, msg=None):
        """Switch HV on."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't switch on HV")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            try:
                self.fem.hv_on()
            except Exception as e:
                error = f"Switching on HV: {str(e)}"
                self.fem.flag_error(error)
                raise ParameterTreeError(error)

    def hv_off(self, msg=None):
        """Switch HV off."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't switch off HV")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            try:
                self.fem.hv_off()
            except Exception as e:
                error = f"Switching off HV: {str(e)}"
                self.fem.flag_error(error)
                raise ParameterTreeError(error)

    def environs(self, msg=None):
        """Readout environmental data."""
        if self.software_state == "Interlocked":
            error_message = "{}".format("Interlocked: Can't read environs")
            self.report_leak_detector_error(error_message)
            raise ParameterTreeError(error_message)
        else:
            self.fem.environs()

    def reset_error(self, msg=None):
        """Reset fem error.

        Note that any leak unit error will remain.
        """
        self.fem.reset_error()
        # Reset system status
        self.status_error = self.leak_error
        self.status_message = ""
        # Determine system health
        self.system_health = self.fem_health and self.leak_health
        # print(f"\n [E IF* FH: {self.fem_health} LH: {self.leak_health} ");time.sleep(0.2)
        if not self.leak_health:
            self.software_state = "Interlocked"
        elif not self.fem_health:
            self.software_state = "Error"
        else:
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
