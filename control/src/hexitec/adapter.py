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

        self.daq = HexitecDAQ(self, self.file_dir, self.file_name)

        self.adapters = {}

        self.fem = None
        for key, value in options.items():
            if "fem" in key:
                fem_info = value.split(',')
                print("fem_info: {}".format(fem_info))
                fem_info = [(i.split('=')[0], i.split('=')[1])
                            for i in fem_info]
                fem_dict = {fem_key.strip(): fem_value.strip()
                            for (fem_key, fem_value) in fem_info}
                logging.debug("From options: {}".format(fem_dict))
                self.fem = HexitecFem(
                    self,
                    fem_dict.get("server_ctrl_ip", defaults.fem["server_ctrl_ip"]),
                    fem_dict.get("camera_ctrl_ip", defaults.fem["camera_ctrl_ip"]),
                    fem_dict.get("server_data_ip", defaults.fem["server_data_ip"]),
                    fem_dict.get("camera_data_ip", defaults.fem["camera_data_ip"])
                )

        if not self.fem:
            logging.error("Using default HexitecFem values!")
            self.fem = HexitecFem(
                parent=self,
                server_ctrl_ip_addr=defaults.fem["server_ctrl_ip"],
                camera_ctrl_ip_addr=defaults.fem["camera_ctrl_ip"],
                server_data_ip_addr=defaults.fem["server_data_ip"],
                camera_data_ip_addr=defaults.fem["camera_data_ip"]
            )

        self.fem_health = True

        self.acquisition_in_progress = False

        # Watchdog variables
        self.error_margin = 400     # TODO: Revisit timeouts
        self.fem_tx_timeout = 5000
        self.daq_rx_timeout = self.error_margin

        # Store initialisation time
        self.init_time = time.time()

        self.system_health = True
        self.status_message = ""
        self.status_error = ""
        self.elog = ""
        self.number_nodes = 1   # 3
        # Software states:
        #   Cold, Environs, Initialising, Offsets, Disconnected, Idle, Acquiring, Error, Cleared
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

        self.odin_config_file = "odin_config.json"

        self._start_polling()

    def update_meta(self, meta):
        """Save to parameter tree meta data PUT by Manchester."""
        self.xtek_meta = meta

    def _start_polling(self):
        IOLoop.instance().add_callback(self.polling)

    def polling(self):  # pragma: no cover
        """Poll FEM for status.

        Check if acquisition completed (if initiated), for error(s) and
        whether DAQ/FEM watchdogs timed out.
        """
        # Poll FEM acquisition & health status
        self.poll_fem()

        # Watchdog: Watch FEM in case no data from hardware triggered by fem.acquire_data()
        self.check_fem_watchdog()

        # TODO: WATCHDOG, monitor HexitecDAQ rate of frames_processed updated.. (Break if stalled)
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

    # TODO: Revisit and update once firmware data readout available
    def check_fem_watchdog(self):
        """Check data sent when FEM acquiring data."""
        if self.acquisition_in_progress:
            # TODO: Monitor FEM in case no data following fem.acquire_data() call
            if (self.fem.hardware_busy):
                fem_begun = self.fem.acquire_timestamp
                delta_time = time.time() - fem_begun
                logging.debug("    FEM w-dog: {0:.2f} < {1:.2f}".format(delta_time,
                                                                        self.fem_tx_timeout))
                # if (delta_time > self.fem_tx_timeout):
                #     self.fem.stop_acquisition = True
                #     self.shutdown_processing()
                #     logging.error("FEM data transmission timed out")
                #     error = "Timed out waiting ({0:.2f} seconds) for FEM data".format(delta_time)
                #     self.fem._set_status_message(error)

    def check_daq_watchdog(self):
        """Monitor DAQ's frames_processed while data processed.

        Ensure frames_processed increments, completes within reasonable time of acquisition.
        Failure to do so indicate missing/dropped packet(s), stop processing if stalled.
        """
        if self.daq.in_progress:
            processed_timestamp = self.daq.processed_timestamp
            delta_time = time.time() - processed_timestamp
            if (delta_time > self.daq_rx_timeout):
                logging.error("    DAQ -- PROCESSING TIMED OUT")
                # DAQ: Timed out waiting for next frame to process
                self.shutdown_processing()
                logging.error("DAQ processing timed out; Saw %s expected %s frames" %
                              (self.daq.frames_processed, self.daq.frame_end_acquisition))
                self.fem._set_status_error("Processing timed out: {0:.2f} seconds \
                    (exceeded {1:.2f}); Expected {2} got {3} frames\
                        ".format(delta_time, self.daq_rx_timeout,
                                 self.daq.frame_end_acquisition, self.daq.frames_processed))
                self.fem._set_status_message("Processing abandoned")

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
        # TODO: Do not reset status; See reset_error()
        # # Reset system status
        # self.status_error = ""
        # self.status_message = ""
        # self.system_health = True

    def save_odin(self, msg):
        """Save Odin's settings to file."""
        config = {}
        config["fem/hexitec_config"] = self.fem.hexitec_config
        config["daq/file_name"] = self.daq.file_name
        config["daq/file_dir"] = self.daq.file_dir
        config["daq/addition_enable"] = self.daq.addition_enable
        config["daq/pixel_grid_size"] = self.daq.pixel_grid_size
        config["daq/calibration_enable"] = self.daq.calibration_enable
        config["daq/gradients_filename"] = self.daq.gradients_filename
        config["daq/intercepts_filename"] = self.daq.intercepts_filename
        config["daq/discrimination_enable"] = self.daq.discrimination_enable
        config["daq/bin_end"] = self.daq.bin_end
        config["daq/bin_start"] = self.daq.bin_start
        config["daq/bin_width"] = self.daq.bin_width
        config["daq/max_frames_received"] = self.daq.max_frames_received
        config["daq/pass_processed"] = self.daq.pass_processed
        config["daq/pass_raw"] = self.daq.pass_raw
        config["daq/lvframes_dataset_name"] = self.daq.lvframes_dataset_name
        config["daq/lvframes_frequency"] = self.daq.lvframes_frequency
        config["daq/lvframes_per_second"] = self.daq.lvframes_per_second
        config["daq/lvspectra_frequency"] = self.daq.lvspectra_frequency
        config["daq/lvspectra_per_second"] = self.daq.lvspectra_per_second
        config["daq/next_frame_enable"] = self.daq.next_frame_enable
        config["daq/threshold_lower"] = self.daq.threshold_lower
        config["daq/threshold_upper"] = self.daq.threshold_upper
        config["daq/image_frequency"] = self.daq.image_frequency
        config["daq/threshold_filename"] = self.daq.threshold_filename
        config["daq/threshold_mode"] = self.daq.threshold_mode
        config["daq/threshold_value"] = self.daq.threshold_value
        config["number_frames"] = self.number_frames
        config["duration"] = self.duration
        config["duration_enable"] = self.duration_enable
        try:
            with open(self.odin_config_file, "w") as f:
                json.dump(config, f)
        except Exception as e:
            self.fem.flag_error("Saving Odin config", str(e))

    def load_odin(self, msg):
        """Load Odin's settings from file."""
        try:
            with open(self.odin_config_file, "r") as f:
                print("\n adp.load_Odin()")
                # print(" exists? {}".format(os.stat(self.odin_config_file)))
                config = json.load(f)
                print(" ({}) config = {}".format(type(config), config))
                self.fem.hexitec_config = config["fem/hexitec_config"]
                self.daq.file_name = config["daq/file_name"]
                self.daq.file_dir = config["daq/file_dir"]
                self.daq.addition_enable = config["daq/addition_enable"]
                self.daq.pixel_grid_size = config["daq/pixel_grid_size"]
                self.daq.calibration_enable = config["daq/calibration_enable"]
                self.daq.gradients_filename = config["daq/gradients_filename"]
                self.daq.intercepts_filename = config["daq/intercepts_filename"]
                self.daq.discrimination_enable = config["daq/discrimination_enable"]
                self.daq.bin_end = config["daq/bin_end"]
                self.daq.bin_start = config["daq/bin_start"]
                self.daq.bin_width = config["daq/bin_width"]
                self.daq.max_frames_received = config["daq/max_frames_received"]
                self.daq.pass_processed = config["daq/pass_processed"]
                self.daq.pass_raw = config["daq/pass_raw"]
                self.daq.lvframes_dataset_name = config["daq/lvframes_dataset_name"]
                self.daq.lvframes_frequency = config["daq/lvframes_frequency"]
                self.daq.lvframes_per_second = config["daq/lvframes_per_second"]
                self.daq.lvspectra_frequency = config["daq/lvspectra_frequency"]
                self.daq.lvspectra_per_second = config["daq/lvspectra_per_second"]
                self.daq.next_frame_enable = config["daq/next_frame_enable"]
                self.daq.threshold_lower = config["daq/threshold_lower"]
                self.daq.threshold_upper = config["daq/threshold_upper"]
                self.daq.image_frequency = config["daq/image_frequency"]
                self.daq.threshold_filename = config["daq/threshold_filename"]
                self.daq.threshold_mode = config["daq/threshold_mode"]
                self.daq.threshold_value = config["daq/threshold_value"]
                self.number_frames = config["number_frames"]
                self.duration = config["duration"]
                self.duration_enable = config["duration_enable"]
        except FileNotFoundError as e:
            self.fem.flag_error("Loading Odin config - file missing", str(e))
        except JSONDecodeError as e:
            self.fem.flag_error("Loading Odin config - Bad json?", str(e))

    def set_duration_enable(self, duration_enable):
        """Set duration enable, calculating number of frames accordingly."""
        self.duration_enable = duration_enable
        self.fem.set_duration_enable(duration_enable)
        # Ensure DAQ, FEM have correct duration/number of frames configured
        if duration_enable:
            self.set_duration(self.duration)
        else:
            # print("\n\tadp.set_duration_enable({}) number_frames: {}\n".format(
            #     duration_enable, self.number_frames))
            self.set_number_frames(self.number_frames)

    def set_number_frames(self, frames):
        """Set number of frames in DAQ, FEM."""
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
        # print("\n\tadp.set_duration({}) number_frames {} -> {}\n".format(
        #     duration, self.fem.get_number_frames(), self.number_frames))
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

        self.daq_target = time.time()
        self.daq.prepare_daq(self.number_frames)
        # Acquisition starts here
        self.acquisition_in_progress = True
        # Wait for DAQ (i.e. file writer) to be enabled before FEM told to collect data
        IOLoop.instance().add_callback(self.await_daq_ready)

    def await_daq_ready(self):
        """Wait until DAQ has configured, enabled file writer."""
        if (self.daq.in_error):
            # print(" \n daq is in error")
            # Reset state variables
            self.reset_state_variables()
        elif (self.daq.file_writing is False):
            # print(" \n DAC acquisition file writing still false")
            # IOLoop.instance().call_later(0.05, self.await_daq_ready)
            IOLoop.instance().call_later(0.5, self.await_daq_ready)
        else:
            # self.software_state = "Acquiring"
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
        -Waiting for data collection to complete, either single/multi run
        """
        # print("\n adpt.monitor_fem_progress() called")
        if (self.fem.hardware_busy):
            # Still sending data
            IOLoop.instance().call_later(0.5, self.monitor_fem_progress)
            return
        # print("\n adpt.monitor_fem_progress() fem done")
        # Issue reset to summed_image
        command = "config/summed_image/reset_image"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(1)
        self.adapters["fp"].put(command, request)

        self.reset_state_variables()

    def reset_state_variables(self):
        """Reset state variables.

        Utilised by await_daq_ready(), monitor_fem_progress()
        """
        self.acquisition_in_progress = False
        self.software_state = "Idle"

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

    def _collect_offsets(self, msg):
        """Instruct FEM to collect offsets."""
        self.fem.collect_offsets()

    def commit_configuration(self, msg):
        """Push HexitecDAQ's 'config/' ParameterTree settings into FP's plugins."""
        self.daq.commit_configuration()
        # Clear cold initialisation if first config commit
        if self.cold_initialisation:
            self.cold_initialisation = False

    def hv_on(self, msg):
        """Switch HV on."""
        self.fem.hv_on(msg)

    def hv_off(self, msg):
        """Switch HV off."""
        self.fem.hv_off(msg)

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
            "id": 0,
            "server_ctrl_ip": "10.0.2.2",
            "camera_ctrl_ip": "10.0.2.1",
            "server_data_ip": "10.0.4.2",
            "camera_data_ip": "10.0.4.1"
        }
