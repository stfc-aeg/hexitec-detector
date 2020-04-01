"""Adapter for Hexitec ODIN control

This class implements an adapter used for Hexitec

Christian Angelsen, STFC Detector Systems Software Group
"""
import logging
import tornado
import time
import os

# Making checking for integer type Python2/3 independent
import sys
if sys.version_info < (3, ):
    integer_types = (int, long,)
    float_types = (float, long,)
else:
    integer_types = (int,)
    float_types = (float,)

from odin.util import convert_unicode_to_string, decode_request_body

from tornado.escape import json_decode
from concurrent import futures
from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor

from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types, response_types)
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin_data.live_view_adapter import LiveViewAdapter
from odin_data.frame_processor_adapter import FrameProcessorAdapter
from odin_data.frame_receiver_adapter import FrameReceiverAdapter
from odin.adapters.proxy import ProxyAdapter
from odin._version import get_versions

from .HexitecFem import HexitecFem
from .HexitecDAQ import HexitecDAQ

class HexitecAdapter(ApiAdapter):
    """
    Hexitec adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the Hexitec system.
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
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        content_type = "application/json"
        status_code = 200
        response = {}
        request = ApiAdapterRequest(None, accept="application/json")
        # Check adapters if path isn't empty
        #   e.g. If asking for /api/0.1/hexitec/fp/, path = "fp/"
        #        Compare:      /api/0.1/hexitec/, path = ""
        checkAdapters = True if len(path) > 0 else False
        try:
            if checkAdapters:
                for name, adapter in self.adapters.items():
                    if path.startswith(name):
                        relative_path = path.split(name)
                        path = relative_path[1]
                        response = adapter.get(path=path, request=request).data
                        logging.debug(response)
                        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

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
        :return: an ApiAdapterResponse object containing the appropriate response
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
            if requestSent == False:
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
        """
        Get references to required adapters and pass those references to the classes that need
        to use them
        """
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        # Pass adapter list to Hexitec class:
        self.hexitec.initialize(self.adapters)
        # Display all loaded adapters:
        #logging.debug("\n\n" + "".join(['   {0:16} = {1}\n'.format(k, v) for k, v in self.adapters.iteritems()]))

class HexitecError(Exception):
    """
    Simple Exception class for Hexitec to wrap lower-level exceptions.
    """

    pass


class Hexitec():
    """
    Hexitec - class that extracts and stores information about system-level parameters.
    """

    # Thread executor used for background tasks
    thread_executor = futures.ThreadPoolExecutor(max_workers=3)

    def __init__(self, options):
        """
        Initialise the Hexitec object.

        This constructor initialises the Hexitec object, building a parameter tree and
        launching a background task if enabled
        """
        defaults = HexitecDetectorDefaults()
        self.file_dir = options.get("save_dir", defaults.save_dir)
        self.file_name = options.get("save_file", defaults.save_file)
        self.number_frames = options.get("acquisition_num_frames", defaults.number_frames)
        self.duration = 1

        self.daq = HexitecDAQ(self, self.file_dir, self.file_name)

        self.adapters = {}

        self.fems = []
        for key, value in options.items():
            logging.debug("%s: %s", key, value)
            if "fem" in key:
                fem_info = value.split(',')
                fem_info = [(i.split('=')[0], i.split('=')[1]) for i in fem_info]
                fem_dict = {fem_key.strip(): fem_value.strip() for (fem_key, fem_value) in fem_info}
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

        ## bias (clock) tracking variables ##
        self.bias_clock_running = False
        self.bias_init_time = 0         # Placeholder
        self.bias_blocking_acquisition = False
        self.extended_acquisition = False       # Track acquisition spanning bias window(s)
        self.frames_already_acquired = 0        # If > 1 bias window needed, how many collected during previous window(s)?

        self.collect_and_bias_time = self.fems[0].bias_refresh_interval + \
            self.fems[0].bias_voltage_settle_time + self.fems[0].time_refresh_voltage_held

        print("\n\n %s %s %s \n\n" % (self.fems[0].bias_refresh_interval, self.fems[0].bias_voltage_settle_time, self.fems[0].time_refresh_voltage_held))

        self.data_collection_begun = 0
        self.initial_acquisition = True

        ## ##

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        self.vcal = 3               # 0-2: Calibrated Image 0-2; 3: Normal data
        
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
            "check_file": (None, self.check_file),  # DEBUGGING
            "collect_offsets": (None, self._collect_offsets),
            "commit_configuration": (None, self.commit_configuration),
            "vcal": (self._get_vcal, self._set_vcal),
            "debug_count": (self._get_debug_count, self._set_debug_count),
            "acquisition": {
                "number_frames": (lambda: self.number_frames, self.set_number_frames),
                "duration": (lambda: self.duration, self.set_duration),
                "start_acq": (None, self.acquisition)
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

        self.start_polling()

    @run_on_executor(executor='thread_executor')
    def start_polling(self):
        IOLoop.instance().add_callback(self.poll_fem)

    def poll_fem(self):
        start = time.time()
        #TODO: Needs reworking, reset must be issued to all fem(s) once triggered
        for fem in self.fems:
            if fem.acquisition_completed:
                timeout = time.time() - fem.acquisition_timestamp
                if (timeout > 1.0):
                    # Issue reset to histogram
                    command = "config/histogram/flush_histograms"
                    request = ApiAdapterRequest(self.file_dir, content_type="application/json")
                    request.body = "{}".format(1)
                    self.adapters["fp"].put(command, request)

                    # Reset fem's acquisiton status ahead of future acquisition
                    fem.acquisition_completed = False
            #TODO: Also check sensor values?
            # ..
            health = fem.get_health()
            # Only note current id if system is in health
            if self.health:
                self.fem_id = fem.get_id()
                self.status_error = fem._get_status_error()
                self.status_message = fem._get_status_message()
                self.health = self.health and health

        IOLoop.instance().call_later(1.0, self.poll_fem)

    def connect_hardware(self, msg):
        #TODO: Must recalculate collect and bias time both here and in initialise();
        #   Logically, commit_configuration() is the best place but it updates variables before 
        #   values read from .ini file
        self.collect_and_bias_time = self.fems[0].bias_refresh_interval + \
            self.fems[0].bias_voltage_settle_time + self.fems[0].time_refresh_voltage_held

        print("\n\n Bias Interval: %s Settle: %s Held: %s bias_and_deadtime: %s\n\n" % \
            (self.fems[0].bias_refresh_interval, self.fems[0].bias_voltage_settle_time, self.fems[0].time_refresh_voltage_held, self.collect_and_bias_time))

        # Start bias clock if not running
        if not self.bias_clock_running:

            IOLoop.instance().add_callback(self.start_bias_clock)

        for fem in self.fems:
            fem.connect_hardware(msg)

    #TODO: Rename this func... :-p
    @run_on_executor(executor='thread_executor')
    def start_bias_clock(self):
        """ Sets up bias "clock" """
        if not self.bias_clock_running:
            self.bias_init_time = time.time()
            self.bias_clock_running = True
        
        self.poll_bias_clock()
        
    def poll_bias_clock(self):
        """ Called periodically (0.1 seconds often enough??) to check
            if we're in bias refresh intv /  refresh volt held / Settle time
            Example: 60000 / 3000 / 2000: Collect for 60s, pause for 3+2 secs """
        #
        current_time = time.time()
        time_elapsed = current_time - self.bias_init_time
        # print(time_enlapsed < self.fems[0].bias_refresh_interval)
        if (time_elapsed < self.fems[0].bias_refresh_interval):
            # Still within collection window - acquiring data is allowed
            pass    #TODO: Need not change anything here?
            # print("!\n Within bias ; lapsed: %s v interval: %s\n!" % (time_elapsed, self.fems[0].bias_refresh_interval))
        else:
            if (time_elapsed < self.collect_and_bias_time):
                # Blackout period - Await for electrons to replenish/voltage to stabilise
                self.bias_blocking_acquisition = True
                # print("!\n Blackout Period ; lapsed: %s v interval: %s\n!" % (time_elapsed, (self.fems[0].bias_refresh_interval +
                #                 self.fems[0].bias_voltage_refresh + 
                #                 self.fems[0].time_refresh_voltage_held)))
            else:
                # Beyond blackout period - Back within bias
                # Reset bias clock
                self.bias_init_time = current_time
                self.bias_blocking_acquisition = False
                # print("!\n BEYOND THE BLACKOUT PERIODIC, RESETTING THE BIAS TO GO BACK TO BIAS (say what?)\n!")

        IOLoop.instance().call_later(0.1, self.poll_bias_clock)

    def initialise_hardware(self, msg):
        #TODO: Must recalculate collect and bias time both here and in initialise();
        #   Logically, commit_configuration() is the best place but it updates variables before 
        #   values read from .ini file
        self.collect_and_bias_time = self.fems[0].bias_refresh_interval + \
            self.fems[0].bias_voltage_settle_time + self.fems[0].time_refresh_voltage_held

        print("\n\n Bias Interval: %s Settle: %s Held: %s bias_and_deadtime: %s\n\n" % \
            (self.fems[0].bias_refresh_interval, self.fems[0].bias_voltage_settle_time, self.fems[0].time_refresh_voltage_held, self.collect_and_bias_time))

        for fem in self.fems:
            fem.initialise_hardware(msg)

    def disconnect_hardware(self, msg):
        for fem in self.fems:
            fem.disconnect_hardware(msg)
        # With all FEM(s) disconnected, reset system status
        self.status_error = ""
        self.status_message = ""
        self.health = True
        # Stop bias clock
        if self.bias_clock_running:
            self.bias_clock_running = False

    def check_file(self, msg):
        # DEBUGGING
        self.daq.check_file_exists()

    def set_number_frames(self, frames):
        self.number_frames = frames
        # Update number of frames in Hardware, and (via DAQ) in histogram and hdf plugins
        for fem in self.fems:
            fem.set_number_frames(self.number_frames)

        self._update_daq()

    def _update_daq(self):

        self.daq.set_number_frames(self.number_frames)

        #TODO: Redundant??
        # Toggle file writing off/on if already on
        if self.daq.file_writing:
            self.daq.set_file_writing(False)
            self.daq.set_file_writing(True)

    def set_duration(self, duration):
        self.duration = duration

        number_frames = 0
        for fem in self.fems:
            fem.set_duration(self.duration)
            number_frames = fem.get_number_frames()
        
        self.number_frames = number_frames
        self._update_daq()
        
    def _get_debug_count(self):
        return self.dbgCount

    def _set_debug_count(self, count):
        self.dbgCount = count

    def initialize(self, adapters):
        """
        Get references to required adapters and pass those references to the classes that need
        to use them
        """
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)

        self.daq.initialize(self.adapters)

    def cleanup(self):
        self.daq.cleanup()

    @run_on_executor(executor='thread_executor')
    def acquisition(self, put_data=None):
        
        # print(" ?")
        if self.extended_acquisition == False:
            if self.daq.in_progress:
                logging.warning("Cannot Start Acquistion: Already in progress")
                return

        # Did the acquisition coincide with bias dead time?
        if self.bias_blocking_acquisition:
            IOLoop.instance().call_later(0.1, self.acquisition)
            return

        # Only call daq's start_acquisition() once per acquisition
        if self.initial_acquisition:
            self.daq.start_acquisition(self.number_frames)
            self.initial_acquisition = False
        
        # #TODO: Remove once Firmware made to reset on each new acquisition
        # #TODO: WILL BE NON 0 VALUE IN THE FUTURE - TO SUPPORT BIAS REFRESH INTV
        # #       BUT, if nonzero then won't FP's Acquisition time out before processing completed?????
        # #
        # Issue reset frame_number (to current frame number, for multi-window acquisition) to reorder plugin
        command = "config/reorder/frame_number"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(self.frames_already_acquired)
        self.adapters["fp"].put(command, request)

        # Work out how many frames can be acquired before next bias refresh #
        time_into_window = time.time() - self.bias_init_time
        time_available = self.fems[0].bias_refresh_interval - time_into_window

        # If we (already) exceeded bias window, stop here without acquiring any frames
        if time_available < 0:
            print("    ?")
            IOLoop.instance().add_callback(self.acquisition)

        frames_before_bias = self.fems[0].frame_rate * time_available
        number_frames_before_bias = int(round(frames_before_bias))

        number_frames_to_request = self.number_frames - self.frames_already_acquired

        print("\n\n frames_before_bias: %s number_frames: %s frames_already_acquired: %s number_frames_to_request: %s time left: %s\n\n" \
            % (number_frames_before_bias, self.number_frames, self.frames_already_acquired, number_frames_to_request, time_available))

        # Can we obtain frames within current bias window?
        if (number_frames_before_bias < number_frames_to_request):
            # No - Need >1 bias window(s) fulfil acquisition?
            self.extended_acquisition = True

            number_frames_to_request = number_frames_before_bias
        #

        self.data_collection_begun = time.time()
        for fem in self.fems:
            #TODO: Dirty hack: Prevent frames being 1 (= continuous readout) by setting it to 2 if it is 1
            number_frames_to_request = 2 if (number_frames_to_request == 1) else number_frames_to_request
            fem.set_number_frames(number_frames_to_request)
            fem.collect_data()

        # Fem(s) are now busy acquiring data; If remainder of Bias window is enough to accommodate 
        #  number_frames_to_request then we're done here. Otherwise..
        #  ..Wait for Fem(s) to finish plus delay of dead time and for voltage to settle, before calling same function again
        if (self.frames_already_acquired < self.number_frames):
            total_delay = time_available + self.fems[0].bias_voltage_settle_time + self.fems[0].time_refresh_voltage_held
            self.frames_already_acquired += number_frames_to_request
            print("    total_delay: %s" % (total_delay))

            #TODO: Test whether asking fem when it finished collecting data, well does that work better?
            IOLoop.instance().call_later(0.1, self.check_fem_finished_collecting_data)
            # IOLoop.instance().call_later(total_delay, self.acquisition)

    def check_fem_finished_collecting_data(self):
        ''' Wait until fem has finished collecting data, then go back to acquisition()
        '''
        if (self.fems[0].hardware_busy):
            # fem still collecting data
            IOLoop.instance().call_later(0.1, self.check_fem_finished_collecting_data)
        else:
            print("\n\n  Adapter detected fem data collected in: %s seconds \n\n" % (time.time() - self.data_collection_begun))
            # Current collection completed; But do we have all the frames user requested?
            if (self.frames_already_acquired < self.number_frames):
                print("\n     MORE bias window(s)")
                # Need further bias window(s)
                IOLoop.instance().add_callback(self.acquisition)
            else:
                print("\n     WE DO NOT NEED bias window(s)                   RESETTING bool!!!!!")
                # Reset initial acquisition bool
                self.initial_acquisition = True
                # We've acquired all the frames we need, reset frames_already_acquired
                self.frames_already_acquired = 0

    def _get_vcal(self):
        return self.vcal

    def _set_vcal(self, vcal):
        """
        Sets vcal in Fem(s)
        """
        self.vcal = vcal
        for fem in self.fems:
            fem._set_test_mode_image(vcal)

    def _collect_offsets(self, msg):
        """
        Instructs fem(s) to collect offsets
        """
        for fem in self.fems:
            fem.collect_offsets()        

    def commit_configuration(self, msg):
        """
        Pushes HexitecDAQ's 'config/' ParameterTree settings into FP's plugins
        """
        self.daq.commit_configuration()

    def _get_status_message(self):
        return self.status_message

    def _get_status_error(self):
        return self.status_error

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

    def __init__(self):
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
