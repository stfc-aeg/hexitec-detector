"""Adapter for Hexitec ODIN control.

This class implements an adapter used for Hexitec

Christian Angelsen, STFC Detector Systems Software Group
"""
import logging
import tornado
import time

from concurrent import futures
from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor

from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types,
                                   response_types)
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.util import convert_unicode_to_string, decode_request_body
from odin._version import get_versions

from .HexitecFem import HexitecFem
from .HexitecDAQ import HexitecDAQ

# Making checking for integer type Python2/3 independent
import sys
if sys.version_info < (3, ):  # pragma: no cover
    integer_types = (int, long,)
    float_types = (float, long,)
else:
    integer_types = (int,)
    float_types = (float,)


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
        # # Display all loaded adapters:
        # logging.debug(self.adapters.items())


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
        # Backup number_frames as first initialisation temporary sets number_frames = 2
        self.backed_up_number_frames = self.number_frames

        self.duration = 1
        self.duration_enable = False

        self.daq = HexitecDAQ(self, self.file_dir, self.file_name)

        self.adapters = {}

        self.fems = []
        for key, value in options.items():
            logging.debug("%s: %s", key, value)
            if "fem" in key:
                fem_info = value.split(',')
                fem_info = [(i.split('=')[0], i.split('=')[1])
                            for i in fem_info]
                fem_dict = {fem_key.strip(): fem_value.strip()
                            for (fem_key, fem_value) in fem_info}
                logging.debug(fem_dict)

                self.fems.append(HexitecFem(
                    self,
                    fem_dict.get("id", defaults.fem["id"]),
                    fem_dict.get("server_ctrl_ip_addr", defaults.fem["server_ctrl_ip"]),
                    fem_dict.get("camera_ctrl_ip_addr", defaults.fem["camera_ctrl_ip"]),
                    fem_dict.get("server_data_ip_addr", defaults.fem["server_data_ip"]),
                    fem_dict.get("camera_data_ip_addr", defaults.fem["camera_data_ip"])
                ))

        if not self.fems:  # if self.fems is empty
            self.fems.append(HexitecFem(
                parent=self,
                fem_id=defaults.fem["id"],
                server_ctrl_ip_addr=defaults.fem["server_ctrl_ip"],
                camera_ctrl_ip_addr=defaults.fem["camera_ctrl_ip"],
                server_data_ip_addr=defaults.fem["server_data_ip"],
                camera_data_ip_addr=defaults.fem["camera_data_ip"]
            ))

        fem_tree = {}
        for fem in self.fems:
            fem_tree["fem_{}".format(fem.id)] = fem.param_tree

        # Bias (clock) tracking variables #
        self.bias_clock_running = False
        self.bias_init_time = 0         # Placeholder
        self.bias_blocking_acquisition = False
        self.extended_acquisition = False       # Track acquisition spanning bias window(s)
        self.frames_already_acquired = 0        # Track frames acquired across collection windows

        self.collect_and_bias_time = self.fems[0].bias_refresh_interval + \
            self.fems[0].bias_voltage_settle_time + self.fems[0].time_refresh_voltage_held

        # Tracks whether first acquisition of multi-bias window collection
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

        # Get package version information
        version_info = get_versions()

        self.fem_id = 101
        self.health = True
        self.status_message = ""
        self.status_error = ""

        self.dbgCount = 0

        detector = ParameterTree({
            "fems": fem_tree,
            "daq": self.daq.param_tree,
            "connect_hardware": (None, self.connect_hardware),
            "initialise_hardware": (None, self.initialise_hardware),
            "disconnect_hardware": (None, self.disconnect_hardware),
            "collect_offsets": (None, self._collect_offsets),
            "commit_configuration": (None, self.commit_configuration),
            "debug_count": (self._get_debug_count, self._set_debug_count),
            "acquisition": {
                "number_frames": (lambda: self.number_frames, self.set_number_frames),
                "duration": (lambda: self.duration, self.set_duration),
                "duration_enable": (lambda: self.duration_enable, self.set_duration_enable),
                "start_acq": (None, self.acquisition),
                "stop_acq": (None, self.cancel_acquisition),
                "in_progress": (lambda: self.acquisition_in_progress, None)
            },
            "status": {
                "fem_id": (lambda: self.fem_id, None),
                "system_health": (lambda: self.health, None),
                "status_message": (lambda: self.status_message, None),
                "status_error": (lambda: self.status_error, None)
            }
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            "odin_version": version_info['version'],
            "tornado_version": tornado.version,
            "server_uptime": (self.get_server_uptime, None),
            "detector": detector
        })

        self._start_polling()

    @run_on_executor(executor='thread_executor')
    def _start_polling(self):
        IOLoop.instance().add_callback(self.polling)

    def polling(self):  # noqa: C901
        """Poll fem(s) for status.

        Check if acquire completed (if initiated), for error(s) and
        whether daq/fem watchdogs timed out
        """
        for fem in self.fems:
            if fem.acquisition_completed:
                histogram_status = self._get_od_status('fp').get('histogram',
                                                                 {'frames_processed': 0})

                # Either cold initialisation (first_initialisation is True, therefore only 2 frames
                # expected) or, ordinary collection (self.number_frames frames expected)
                if ((self.first_initialisation and (histogram_status['frames_processed'] == 2))
                   or (histogram_status['frames_processed'] == self.number_frames)):  # noqa: W503

                    if self.first_initialisation:
                        self.number_frames = fem.get_number_frames()

                    # Reset fem's acquisiton status ahead of future acquisition
                    fem.acquisition_completed = False
            # TODO: Also check sensor values?
            # ..
            health = fem.get_health()
            # Only note current id if system is in health
            if self.health:
                self.fem_id = fem.get_id()
                self.status_error = fem._get_status_error()
                self.status_message = fem._get_status_message()
                self.health = self.health and health

        # Watchdogs
        if self.acquisition_in_progress:
            # print("")
            # logging.debug(" (%s) v (%s) => acq_in_prog, hw_busy" % (self.acquisition_in_progress,
            #                                                         self.fems[0].hardware_busy))
            # logging.debug("   {0:.6f}  acquire_timestamp".format(self.fems[0].acquire_timestamp))
            # logging.debug("   {0:.6f} processed_timestamp".format(self.daq.processed_timestamp))
            # differ = self.daq.processed_timestamp - self.fems[0].acquire_timestamp
            # compare = self.daq.processed_timestamp == self.fems[0].acquire_timestamp
            # logging.debug("   {0:.6f} processed - acquire".format(differ))
            # logging.debug("   {} cmp proc'd v acquir".format(compare))
            # TODO: Monitor Fem in case no data from following fem.acquire_data()
            if (self.fems[0].hardware_busy):
                # #
                # waiting_time = self.daq.processed_timestamp - self.fems[0].acquire_timestamp
                # if (waiting_time < 0):
                #     # No data yet from the fem
                #     self.time_waiting_for_data_arrival += 1
                # #
                fem_begun = self.fems[0].acquire_timestamp
                delta_time = time.time() - fem_begun
                logging.debug("    FEM w-dog: {0:.2f} < {1:.2f}".format(delta_time,
                                                                        self.fem_tx_timeout))
                if (delta_time > self.fem_tx_timeout):
                    self.fems[0].stop_acquisition = True
                    self.shutdown_processing()
                    logging.error("FEM data transmission timed out")
                    error = "Timed out waiting ({0:.2f} seconds) for FEM data".format(delta_time)
                    self.fems[0]._set_status_message(error)
        # else:
        #     # No acquisition in progress, reset watchdog variable
        #     print("\n\n   ABOUT to reset Time_waiting_for_data_arrival(%s)\n\n" %
        #           self.time_waiting_for_data_arrival)
        #     self.time_waiting_for_data_arrival = 0
        # # logging.debug("      (%s)          ==>>           daq_in_prog" % self.daq.in_progress)

        # TODO: WATCHDOG, monitor HexitecDAQ rate of frames_processed updated.. (Break if stalled)
        if self.daq.in_progress:
            processed_timestamp = self.daq.processed_timestamp
            delta_time = time.time() - processed_timestamp
            # logging.debug("    DAQ w-dog: {0:.2f} < {1:.2f}".format(delta_time,
            #                                                         self.daq_rx_timeout))
            if (delta_time > self.daq_rx_timeout):
                logging.error("    DAQ -- PROCESSING TIMED OUT")
                # daq: Timed out waiting for next frame to process
                self.shutdown_processing()
                logging.error("DAQ processing timed out; Saw %s expected %s frames" %
                              (self.daq.frames_processed, self.daq.frame_end_acquisition))
                self.fems[0]._set_status_error("Processing timed out: {0:.2f} seconds \
                    (exceeded {1:.2f}); Expected {2} got {3} frames\
                        ".format(delta_time, self.daq_rx_timeout,
                                 self.daq.frame_end_acquisition, self.daq.frames_processed))
                self.fems[0]._set_status_message("Processing interrupted")
        # print("")

        IOLoop.instance().call_later(1.0, self.polling)

    def shutdown_processing(self):
        """Stop processing in daq."""
        self.daq.shutdown_processing = True
        self.acquisition_in_progress = False

    def _get_od_status(self, adapter):
        try:
            request = ApiAdapterRequest(None, content_type="application/json")
            response = self.adapters[adapter].get("status", request)
            response = response.data["value"][0]
        except KeyError:
            logging.warning("%s Adapter Not Found" % adapter)
            response = {"Error": "Adapter {} not found".format(adapter)}
        finally:
            return response

    def connect_hardware(self, msg):
        """Set up watchdog timeout, start bias clock and connect with hardware."""
        # TODO: Must recalculate collect and bias time both here and in initialise()
        #   Logically, commit_configuration() is the best place but it updates variables before
        #   values read from .ini file
        self.collect_and_bias_time = self.fems[0].bias_refresh_interval + \
            self.fems[0].bias_voltage_settle_time + self.fems[0].time_refresh_voltage_held

        # print("\n\n  ADP Bias Interval: %s Settle: %s Held: %s bias_and_deadtime: %s\n\n" %
        #       (self.fems[0].bias_refresh_interval, self.fems[0].bias_voltage_settle_time,
        #        self.fems[0].time_refresh_voltage_held, self.collect_and_bias_time))

        self.daq_rx_timeout = self.collect_and_bias_time + self.error_margin

        # Start bias clock if not running
        if not self.bias_clock_running:
            IOLoop.instance().add_callback(self.start_bias_clock)

        for fem in self.fems:
            fem.connect_hardware(msg)

    @run_on_executor(executor='thread_executor')
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
        if (time_elapsed < self.fems[0].bias_refresh_interval):
            # Still within collection window - acquiring data is allowed
            pass
        else:
            if (time_elapsed < self.collect_and_bias_time):
                # Blackout period - Await for electrons to replenish/voltage to stabilise
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
        self.collect_and_bias_time = self.fems[0].bias_refresh_interval + \
            self.fems[0].bias_voltage_settle_time + self.fems[0].time_refresh_voltage_held

        # print("\n\n  ADP Bias Interval: %s Settle: %s Held: %s bias_and_deadtime: %s\n\n" %
        #       (self.fems[0].bias_refresh_interval, self.fems[0].bias_voltage_settle_time,
        #        self.fems[0].time_refresh_voltage_held, self.collect_and_bias_time))

        self.daq_rx_timeout = self.collect_and_bias_time + self.error_margin

        # If first initialisation, ie fudge, temporarily change number_frames to 2
        # Adapter also controls this change in fem(s)
        if self.first_initialisation:
            self.backed_up_number_frames = self.number_frames
            self.number_frames = 2
            # TODO: Fix this fudge?
            self.fems[0].acquire_timestamp = time.time()
            self.acquisition_in_progress = True

        for fem in self.fems:
            fem.initialise_hardware(msg)

        # Wait for fudge frames to come through
        IOLoop.instance().call_later(0.5, self.check_fem_finished_sending_data)

    def disconnect_hardware(self, msg):
        """Disconnect fem(s)' hardware connection."""
        for fem in self.fems:
            fem.disconnect_hardware(msg)
        # With all FEM(s) disconnected, reset system status
        self.status_error = ""
        self.status_message = ""
        self.health = True
        # Stop bias clock
        if self.bias_clock_running:
            self.bias_clock_running = False

    def set_duration_enable(self, duration_enable):
        """Set duration enable, calculating number of frames accordingly."""
        self.duration_enable = duration_enable
        for fem in self.fems:
            fem.set_duration_enable(duration_enable)
        # Ensure daq, fem(s) have correct duration/number of frames configured
        if duration_enable:
            self.set_duration(self.duration)
        else:
            self.set_number_frames(self.number_frames)

    def set_number_frames(self, frames):
        """Set number of frames in daq, fem(s)."""
        self.number_frames = frames
        # Update number of frames in Hardware, and (via DAQ) in histogram and hdf plugins
        for fem in self.fems:
            fem.set_number_frames(self.number_frames)
        self.daq.set_number_frames(self.number_frames)

    def set_duration(self, duration):
        """Set duration, calculate frames from frame rate and update daq, fem(s)."""
        self.duration = duration

        number_frames = 0
        for fem in self.fems:
            fem.set_duration(self.duration)
            number_frames = fem.get_number_frames()

        self.number_frames = number_frames

        self.daq.set_number_frames(self.number_frames)

    def _get_debug_count(self):
        return self.dbgCount

    def _set_debug_count(self, count):
        self.dbgCount = count

    def initialize(self, adapters):
        """Get references to adapters, and pass these to the classes that need to use them."""
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        self.daq.initialize(self.adapters)

    @run_on_executor(executor='thread_executor')  # noqa: C901
    def acquisition(self, put_data=None):
        """Instruct daq and fem(s) to acquire data."""
        # Synchronise first_initialisation status with fem
        if self.first_initialisation:
            for fem in self.fems:
                # Only need to check first fem's value
                self.first_initialisation = fem.first_initialisation
                break

        if self.extended_acquisition is False:
            if self.daq.in_progress:
                logging.warning("Cannot Start Acquistion: Already in progress")
                return

        total_delay = 0
        number_frames_to_request = self.number_frames

        if self.fems[0].bias_voltage_refresh:
            # Did the acquisition coincide with bias dead time?
            if self.bias_blocking_acquisition:
                IOLoop.instance().call_later(0.1, self.acquisition)
                return

            # Work out how many frames can be acquired before next bias refresh
            time_into_window = time.time() - self.bias_init_time
            time_available = self.fems[0].bias_refresh_interval - time_into_window

            if time_available < 0:
                IOLoop.instance().call_later(0.09, self.acquisition)
                return

            frames_before_bias = self.fems[0].frame_rate * time_available
            number_frames_before_bias = int(round(frames_before_bias))

            number_frames_to_request = self.number_frames - self.frames_already_acquired

            # Can we obtain all required frames within current bias window?
            if (number_frames_before_bias < number_frames_to_request):
                # Need >1 bias window fulfil acquisition
                self.extended_acquisition = True
                number_frames_to_request = number_frames_before_bias

            total_delay = time_available + self.fems[0].bias_voltage_settle_time + \
                self.fems[0].time_refresh_voltage_held

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

        # Reset histograms, call daq's start_acquisition() once per acquisition
        if self.initial_acquisition:
            # Issue reset to histogram
            command = "config/histogram/reset_histograms"
            request = ApiAdapterRequest(self.file_dir, content_type="application/json")
            request.body = "{}".format(1)
            self.adapters["fp"].put(command, request)

            self.daq.start_acquisition(self.number_frames)
            self.initial_acquisition = False
            # Acquisition (whether single/multi-run) starts here
            self.acquisition_in_progress = True
            # Give daq (enabling file writing) 50 ms head start before fem sends data
            time.sleep(0.05)

        for fem in self.fems:
            # TODO: Temp hack: Prevent frames being 1 (continuous readout) by setting to 2 if it is
            number_frames_to_request = 2 if (number_frames_to_request == 1) else \
                number_frames_to_request

            fem.set_number_frames(number_frames_to_request)
            fem.collect_data()

        self.frames_already_acquired += number_frames_to_request

        # Note when fem told to begun collecting data
        self.fem_start_timestamp = time.time()
        IOLoop.instance().call_later(total_delay, self.check_fem_finished_sending_data)

    def check_fem_finished_sending_data(self):
        """Check whether fem stopped transmitting data.

        Wait until fem has finished sending data, then either finish
        acquisition (single run) or request more frames (multi run)
        """
        if (self.fems[0].hardware_busy):
            # Still sending data
            IOLoop.instance().call_later(0.5, self.check_fem_finished_sending_data)
            return
        else:
            # Current collection completed; Do we have all the frames that user requested?
            if self.extended_acquisition:
                if (self.frames_already_acquired < self.number_frames):
                    # Need further bias window(s)
                    IOLoop.instance().add_callback(self.acquisition)
                    return
        # If first initialisation, reset associated variables
        if self.first_initialisation:
            self.first_initialisation = False
            self.number_frames = self.backed_up_number_frames
        # Reset initial acquisition, extended acquisition bools
        self.initial_acquisition = True
        self.extended_acquisition = False
        self.acquisition_in_progress = False
        # We've acquired all the frames we need, reset frames_already_acquired
        self.frames_already_acquired = 0

    def cancel_acquisition(self, put_data=None):
        """Cancel ongoing acquisition in Software.

        Not yet possible to stop Hardware.
        """
        for fem in self.fems:
            fem.stop_acquisition = True
        self.shutdown_processing()

    def _collect_offsets(self, msg):
        """Instruct fem(s) to collect offsets."""
        for fem in self.fems:
            fem.collect_offsets()

    def commit_configuration(self, msg):
        """Push HexitecDAQ's 'config/' ParameterTree settings into FP's plugins."""
        self.daq.commit_configuration()
        # # DEBUGGING ONLY: Ensure fudge for everyone(!)
        # self.first_initialisation  = True
        # self.fems[0].first_initialisation  = True
        # self.daq.first_initialisation = True

    def get_server_uptime(self):
        """
        Get the uptime for the ODIN server.

        This method returns the current uptime for the ODIN server.
        """
        return time.time() - self.init_time

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
