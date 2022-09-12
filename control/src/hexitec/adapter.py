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

        # Bias (clock) tracking variables #
        self.bias_clock_running = False
        self.bias_init_time = 0         # Placeholder
        self.bias_blocking_acquisition = False
        self.extended_acquisition = False       # Track acquisition spanning bias window(s)
        self.frames_already_acquired = 0        # Track frames acquired across collection windows

        self.collect_and_bias_time = self.fem.bias_refresh_interval + \
            self.fem.bias_voltage_settle_time + self.fem.time_refresh_voltage_held

        # Tracks whether first acquisition of multiple, bias-window(s), collection
        self.initial_acquisition = True
        # Tracks whether 2 frame fudge collection: (during cold initialisation)
        self.first_initialisation = True

        self.acquisition_in_progress = False

        # Watchdog variables
        self.error_margin = 400                               # TODO: Revisit timeouts
        self.fem_tx_timeout = 5000
        self.daq_rx_timeout = self.collect_and_bias_time + self.error_margin
        self.fem_start_timestamp = 0
        self.time_waiting_for_data_arrival = 0

        # Store initialisation time
        self.init_time = time.time()

        self.system_health = True
        self.status_message = ""
        self.status_error = ""
        self.elog = ""
        self.number_nodes = 1
        # Software states:
        #   Cold, Disconnected, Idle, Acquiring
        self.software_state = "Cold"
        self.cold_initialisation = True

        detector = ParameterTree({
            "fem": self.fem.param_tree,
            "daq": self.daq.param_tree,
            "connect_hardware": (None, self.connect_hardware),
            "initialise_hardware": (None, self.initialise_hardware),
            "disconnect_hardware": (None, self.disconnect_hardware),
            "collect_offsets": (None, self._collect_offsets),
            "commit_configuration": (None, self.commit_configuration),
            "software_state": (lambda: self.software_state, None),
            "cold_initialisation": (lambda: self.cold_initialisation, None),
            "hv_on": (None, self.hv_on),
            "hv_off": (None, self.hv_off),
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

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            "system_info": self.system_info.param_tree,
            "detector": detector
        })

        self._start_polling()

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
            # Either cold initialisation (first_initialisation is True, therefore only 2 frames
            # expected) or, ordinary collection (self.number_frames frames expected)
            if ((self.first_initialisation and (frames_processed == 2))
                    or (frames_processed == self.number_frames)):  # noqa: W503

                if self.first_initialisation:
                    self.first_initialisation = False
                    self.number_frames = self.backed_up_number_frames  # TODO: redundant

                # Reset FEM's acquisiton status ahead of future acquisitions
                self.fem.acquisition_completed = False
        # TODO: Also check sensor values?
        # ..
        fem_health = self.fem.get_health()
        self.fem_health = fem_health
        if self.system_health:
            self.status_error = self.fem._get_status_error()
            self.status_message = self.fem._get_status_message()
            self.system_health = self.system_health and self.fem_health

    def check_fem_watchdog(self):
        """Check data sent when FEM acquiring data."""
        if self.acquisition_in_progress:
            # TODO: Monitor FEM in case no data following fem.acquire_data() call
            if (self.fem.hardware_busy):
                fem_begun = self.fem.acquire_timestamp
                delta_time = time.time() - fem_begun
                logging.debug("    FEM w-dog: {0:.2f} < {1:.2f}".format(delta_time,
                                                                        self.fem_tx_timeout))
                if (delta_time > self.fem_tx_timeout):
                    self.fem.stop_acquisition = True
                    self.shutdown_processing()
                    logging.error("FEM data transmission timed out")
                    error = "Timed out waiting ({0:.2f} seconds) for FEM data".format(delta_time)
                    self.fem._set_status_message(error)

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
        """Set up watchdog timeout, start bias clock and connect with hardware."""
        # TODO: Must recalculate collect and bias time both here and in initialise()
        #   Logically, commit_configuration() is the best place but it updates variables before
        #   reading .ini file
        self.collect_and_bias_time = self.fem.bias_refresh_interval + \
            self.fem.bias_voltage_settle_time + self.fem.time_refresh_voltage_held

        self.daq_rx_timeout = self.collect_and_bias_time + self.error_margin
        # Start bias clock if not running
        if not self.bias_clock_running:
            IOLoop.instance().add_callback(self.start_bias_clock)
        self.fem.connect_hardware(msg)
        self.software_state = "Idle"

    def start_bias_clock(self):
        """Set up bias 'clock'."""
        if not self.bias_clock_running:
            self.bias_init_time = time.time()
            self.bias_clock_running = True
        self.poll_bias_clock()

    def poll_bias_clock(self):
        """Call periodically (0.1 seconds often enough??) to bias window status.

        Are we in bias refresh intv /  refresh volt held / Settle time ?
        Example: 60000 / 3000 / 2000: Collect for 60s, pause for 3+2 secs
        """
        current_time = time.time()
        time_elapsed = current_time - self.bias_init_time
        if (time_elapsed < self.fem.bias_refresh_interval):
            # Still within collection window - acquiring data is allowed
            pass
        else:
            if (time_elapsed < self.collect_and_bias_time):
                # Blackout period - Wait for electrons to replenish/voltage to stabilise
                self.bias_blocking_acquisition = True
            else:
                # Beyond blackout period - Back within bias
                # Reset bias clock
                self.bias_init_time = current_time
                self.bias_blocking_acquisition = False

        IOLoop.instance().call_later(0.1, self.poll_bias_clock)

    def initialise_hardware(self, msg):
        """Initialise hardware.

        Recalculate collect and bias timing, update watchdog timeout.
        """
        # TODO: Must recalculate collect and bias time both here and in initialise();
        #   Logically, commit_configuration() is the best place but it updates variables before
        #   values read from .ini file
        self.collect_and_bias_time = self.fem.bias_refresh_interval + \
            self.fem.bias_voltage_settle_time + self.fem.time_refresh_voltage_held

        self.daq_rx_timeout = self.collect_and_bias_time + self.error_margin
        # If first initialisation, ie fudge, temporarily change number_frames to 2
        # Adapter also controls this change in FEM
        if self.first_initialisation:
            self.backed_up_number_frames = self.number_frames
            self.number_frames = 2
            # TODO: Fix this fudge?
            self.fem.acquire_timestamp = time.time()
            self.acquisition_in_progress = True
        self.fem.initialise_hardware(msg)
        # Wait for fem initialisation/fudge frames
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
        self.software_state = "Disconnected"
        # Reset system status
        self.status_error = ""
        self.status_message = ""
        self.system_health = True
        # Stop bias clock
        if self.bias_clock_running:
            self.bias_clock_running = False

    def set_duration_enable(self, duration_enable):
        """Set duration enable, calculating number of frames accordingly."""
        self.duration_enable = duration_enable
        self.fem.set_duration_enable(duration_enable)
        # Ensure DAQ, FEM have correct duration/number of frames configured
        if duration_enable:
            self.set_duration(self.duration)
        else:
            # print("\n\tadp.set_duration_enable({}) number_frames: {}\n".format(duration_enable, self.number_frames))
            self.set_number_frames(self.number_frames)

    def set_number_frames(self, frames):
        """Set number of frames in DAQ, FEM."""
        # print("\n\tadp.set_number_frames({}) -> number_frames: {}\n".format(frames, self.number_frames))
        self.number_frames = frames
        # Update number of frames in Hardware, and (via DAQ) in histogram and hdf plugins
        self.fem.set_number_frames(self.number_frames)
        self.daq.set_number_frames(self.number_frames)

    def set_duration(self, duration):
        """Set duration, calculate frames from frame rate and update DAQ, FEM."""
        self.duration = duration
        self.fem.set_duration(self.duration)
        # print("\n\tadp.set_duration({}) number_frames {} -> {}\n".format(duration, self.fem.get_number_frames(), self.number_frames))
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
        # Synchronise first_initialisation status (i.e. collect 2 fudge frames) with FEM
        if self.first_initialisation:
            self.first_initialisation = self.fem.first_initialisation
        else:
            # Clear (any previous) daq error
            self.daq.in_error = False

        if self.extended_acquisition is False:
            if self.daq.in_progress:
                logging.warning("Cannot Start Acquistion: Already in progress")
                self.fem._set_status_error("Cannot Start Acquistion: Already in progress")
                return

        self.total_delay = 0
        self.number_frames_to_request = self.number_frames

        if self.fem.bias_voltage_refresh:
            # Did the acquisition coincide with bias dead time?
            if self.bias_blocking_acquisition:
                IOLoop.instance().call_later(0.1, self.acquisition)
                return

            # Work out how many frames can be acquired before next bias refresh
            time_into_window = time.time() - self.bias_init_time
            time_available = self.fem.bias_refresh_interval - time_into_window

            if time_available < 0:
                IOLoop.instance().call_later(0.09, self.acquisition)
                return

            frames_before_bias = self.fem.frame_rate * time_available
            number_frames_before_bias = int(round(frames_before_bias))

            self.number_frames_to_request = self.number_frames - self.frames_already_acquired

            # Can we obtain all required frames within current bias window?
            if (number_frames_before_bias < self.number_frames_to_request):
                # Need >1 bias window to fulfil acquisition
                self.extended_acquisition = True
                self.number_frames_to_request = number_frames_before_bias

            self.total_delay = time_available + self.fem.bias_voltage_settle_time + \
                self.fem.time_refresh_voltage_held

        # # TODO: Remove once Firmware made to reset on each new acquisition
        # # TODO: WILL BE NON 0 VALUE IN THE FUTURE - TO SUPPORT BIAS REFRESH INTV
        # #       BUT, if nonzero then won't FP's Acquisition time out before processing done?????
        # #
        # Reset Reorder plugin's frame_number (to current frame number, for multi-window acquire)
        command = "config/reorder/frame_number"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(self.frames_already_acquired)
        self.adapters["fp"].put(command, request)
        # TODO: To be removed once firmware updated? FP may be slow to process frame_number reset
        time.sleep(0.5)

        # Reset histograms, call DAQ's prepare_daq() once per acquisition
        if self.initial_acquisition:
            # Issue reset to histogram
            command = "config/histogram/reset_histograms"
            request = ApiAdapterRequest(self.file_dir, content_type="application/json")
            request.body = "{}".format(1)
            self.adapters["fp"].put(command, request)

            self.daq_target = time.time()
            self.daq.prepare_daq(self.number_frames)
            self.initial_acquisition = False
            # Acquisition (whether single/multi-run) starts here
            self.acquisition_in_progress = True

        # Wait for DAQ (i.e. file writer) to be enabled before FEM told to collect data
        # IOLoop.instance().call_later(0.1, self.await_daq_ready)
        IOLoop.instance().add_callback(self.await_daq_ready)

    def await_daq_ready(self):
        """Wait until DAQ has configured, enabled file writer."""
        if (self.daq.in_error):
            # Reset state variables
            self.reset_state_variables()
        elif (self.daq.file_writing is False):
            IOLoop.instance().call_later(0.05, self.await_daq_ready)
        else:
            self.software_state = "Acquiring"
            # Add additional 8 ms delay to ensure file writer's file open before first frame arrives
            IOLoop.instance().call_later(0.08, self.trigger_fem_acquisition)

    def trigger_fem_acquisition(self):
        """Trigger data acquisition in fem."""
        # TODO: Temp hack: Prevent frames being 1 (continuous readout) by setting to 2 if it is
        self.number_frames_to_request = 2 if (self.number_frames_to_request == 1) else \
            self.number_frames_to_request
        self.fem.set_number_frames(self.number_frames_to_request)
        self.fem.collect_data()

        self.frames_already_acquired += self.number_frames_to_request
        # Note when FEM told to begin collecting data
        self.fem_start_timestamp = time.time()
        IOLoop.instance().call_later(self.total_delay, self.monitor_fem_progress)

    def monitor_fem_progress(self):
        """Check fem hardware progress.

        Busy either:
        -Initialising from cold (2 fudge frames)
        -Normal initialisation
        -Waiting for data collection to complete, either single/multi run
        """
        if (self.fem.hardware_busy):
            # Still sending data
            IOLoop.instance().call_later(0.5, self.monitor_fem_progress)
            return
        else:
            # Current collection completed; Do we have all the requested frames?
            if self.extended_acquisition:
                if (self.frames_already_acquired < self.number_frames):
                    # Need further bias window(s)
                    IOLoop.instance().add_callback(self.acquisition)
                    return

        # Issue reset to summed_image
        command = "config/summed_image/reset_image"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(1)
        self.adapters["fp"].put(command, request)

        rc = self.daq.prepare_odin()
        if not rc:
            logging.error("Odin's frameReceiver/frameProcessor not ready")

        self.reset_state_variables()

    def reset_state_variables(self):
        """Reset state variables.

        Utilised by await_daq_ready(), monitor_fem_progress()
        """
        self.initial_acquisition = True
        self.extended_acquisition = False
        self.acquisition_in_progress = False
        self.frames_already_acquired = 0
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
        # TODO: Complete placeholder
        self.fem.hv_bias_enabled = True

    def hv_off(self, msg):
        """Switch HV off."""
        # TODO: Complete placeholder
        self.fem.hv_bias_enabled = False

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
        self.save_file = "default_file"
        self.number_frames = 10
        self.fem = {
            "id": 0,
            "server_ctrl_ip": "10.0.2.2",
            "camera_ctrl_ip": "10.0.2.1",
            "server_data_ip": "10.0.4.2",
            "camera_data_ip": "10.0.4.1"
        }
