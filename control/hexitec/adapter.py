"""Adapter for Hexitec ODIN control

This class implements an adapter used for Hexitec

Christian Angelsen, STFC Application Engineering
"""
import logging
import tornado
import time
from concurrent import futures
from .HexitecFem import HexitecFem

# Making checking for integer type Python2/3 independent
import sys
if sys.version_info < (3, ):
    integer_types = (int, long,)
    float_types = (float, long,)
else:
    integer_types = (int,)
    float_types = (float,)

from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor
from tornado.escape import json_decode

from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types, response_types)
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin_data.live_view_adapter import LiveViewAdapter
from odin_data.frame_processor_adapter import FrameProcessorAdapter
from odin_data.frame_receiver_adapter import FrameReceiverAdapter
from odin.adapters.proxy import ProxyAdapter
from odin._version import get_versions


class HexitecAdapter(ApiAdapter):
    """Hexitec adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the Hexitec system.
    """

    def __init__(self, **kwargs):
        """Initialize the HexitecAdapter object.

        This constructor initializes the HexitecAdapter object.

        :param kwargs: keyword arguments specifying options
        """
        # Intialise superclass
        super(HexitecAdapter, self).__init__(**kwargs)

        # Parse options
        # background_task_enable = bool(self.options.get('background_task_enable', False))
                
        self.hexitec = Hexitec()

        self.adapters = {}

        logging.debug('HexitecAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

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
        print "get? my arse; path: ", path, "checkAdapters: ", checkAdapters
        try:
            if checkAdapters:
                for name, adapter in self.adapters.items():
                    if path.startswith(name):
                        # print "Adapter: ", name, " Let's ask it"
                        relative_path = path.split(name)
                        path = relative_path[1]
                        response = adapter.get(path=path, request=request).data
                        # print name, " => ", response
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
        """Handle an HTTP PUT request.

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
                data = json_decode(request.body)
                data = self.convert_to_string(data)
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
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'HexitecAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)
    
    """ ADDED TO PREVENT unicode / string mismatch type error """
    def convert_to_string(self, obj):
        """
        Convert all unicode parts of a dictionary or list to standard strings.
        This method may not handle special characters well!
        :param obj: the dictionary, list, or unicode string
        :return: the same data type as obj, but with unicode strings converted to python strings.
        """
        if isinstance(obj, dict):
            return {self.convert_to_string(key): self.convert_to_string(value)
                    for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_string(element) for element in obj]
        elif isinstance(obj, unicode):
            return obj.encode('utf-8')

        return obj

    def initialize(self, adapters):
        """Get references to required adapters and pass those references to the classes that need
            to use them
        """
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        # Pass adapter list to Hexitec class:
        self.hexitec.initialize(self.adapters)

        # for name, adapter in adapters.items():
        #     if isinstance(adapter, ProxyAdapter):
        #         logging.debug("%s is Proxy Adapter", name)
        #         self.adapters["proxy"] = adapter
        #         print "adding: ", adapter

        #     elif isinstance(adapter, FrameProcessorAdapter):
        #         logging.debug("%s is FP Adapter", name)
        #         self.adapters["fp"] = adapter
        #         print "adding: ", adapter

        #     elif isinstance(adapter, FrameReceiverAdapter):
        #         logging.debug("%s is FR Adapter", name)
        #         self.adapters["fr"] = adapter
        #         print "adding: ", adapter

        #     elif isinstance(adapter, LiveViewAdapter):
        #         logging.debug("%s is Live View Adapter", name)

        #     else:
        #         logging.debug("%s: Wat dis?", name)
        #         print adapter, " adapter is not self: ", adapter is not self

        #         if adapter is not self:
        #             print name, adapter, "   ", type(name)
        #             self.adapters[name] = adapter
        #             print "adding: ", adapter

            #     if isinstance(adapter, HexitecAdapter):
            #         print name, "It's me"
            #     else:
            #         print name, "it's not me"

        # print "How many loaded adapters?", len(self.adapters)
        # print self.adapters

        # self.adapters["liveview"] = adapter

class HexitecError(Exception):
    """Simple exception class for Hexitec to wrap lower-level exceptions."""

    pass


class Hexitec():
    """Hexitec - class that extracts and stores information about system-level parameters."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self):
        """Initialise the Hexitec object.

        This constructor initlialises the Hexitec object, building a parameter tree and
        launching a background task if enabled
        """
        # Save arguments
        # self.background_task_enable = background_task_enable
        # self.background_task_interval = background_task_interval

        self.adapters = {}

        self.fem = HexitecFem()

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        # Build a parameter tree for the background task
        # bg_task = ParameterTree({
        #     'count': (lambda: self.background_task_counter, None),
        #     'enable': (lambda: self.background_task_enable, self.set_task_enable),
        #     'interval': (lambda: self.background_task_interval, self.set_task_interval),
        # })

        # Test area for checking things in the UI
        test_area = ParameterTree({
            'target_text': "(blank)"
        })

        self.height = 80
        self.width = 80
        # Reorder
        reorder = ParameterTree({
            'height': (self._get_height, self._set_height),   # UI's rows = .config's height
            'width': (self._get_width, self._set_width),    # columns = width
            'reorder': False,
            'raw_data': False
        })

        self.threshold_value = 100
        self.threshold_mode = "None"
        # Threshold
        threshold = ParameterTree({
            'threshold_filename': "",
            'threshold_value': (self._get_threshold_value, self._set_threshold_value),
            'threshold_mode': (self._get_threshold_mode, self._set_threshold_mode),
            'enable': False
        })

        # Calibration
        calibration = ParameterTree({
            'gradients_filename': "",
            'intercepts_filename': "",
            'enable': False
        })

        self.pixel_grid_size = 3
        # Addition (Charged Sharing)
        addition = ParameterTree({
            'enable': False,
            'pixel_grid_size': (self._get_pixel_grid_size, self._set_pixel_grid_size)
        })
        # Discrimination (Charged Sharing)
        discrimination = ParameterTree({
            'enable': False,
            'pixel_grid_size': (self._get_pixel_grid_size, self._set_pixel_grid_size)
        })

        self.max_frames_received = 540
        self.bin_start = 0
        self.bin_end = 8000
        self.bin_width = 10.0
        # Histogram
        histogram = ParameterTree({
            'enable': False,
            'max_frames_received': (self._get_max_frames_received, self._set_max_frames_received),
            'bin_start': (self._get_bin_start, self._set_bin_start),
            'bin_end': (self._get_bin_end, self._set_bin_end),
            'bin_width': (self._get_bin_width, self._set_bin_width)
        })

        ### POPULATE REPLACEMENT parameter tree ###
        self.sensors_layout = "1x1"
        adapter_settings = ParameterTree({
            'hexitec_fem': self.fem.param_tree,
            'sensors_layout': (self._get_sensors_layout, self._set_sensors_layout),
            'enable': False
        })

        # Build odin_data (vars) area here
        odin_data = ParameterTree({
            'reorder': reorder,
            'threshold': threshold,
            'next_frame': False,
            'calibration': calibration,
            'addition': addition,
            'discrimination': discrimination,
            'histogram': histogram,
            'adapter_settings': adapter_settings
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'odin_version': version_info['version'],
            'tornado_version': tornado.version,
            'server_uptime': (self.get_server_uptime, None),
            # 'background_task': bg_task,
            'test_area': test_area,
            'odin_data': odin_data#,
            # This is the future:
            # 'adapter_settings': adapter_settings
        })

        # # Set the background task counter to zero
        # self.background_task_counter = 0

        # # Launch the background task if enabled in options
        # if self.background_task_enable:
        #     logging.debug(
        #         "Launching background task with interval %.2f secs", background_task_interval
        #     )
        #     self.background_task()

    def _get_sensors_layout(self):

        return self.sensors_layout

    def _set_sensors_layout(self, layout):

        self.sensors_layout = layout

        # send command to FP,FR adapters 

        command = "config/reorder/sensors_layout"
        request = ApiAdapterRequest(self.sensors_layout, content_type="application/json")
        self.adapters["fp"].put(command, request)

        command = "config/decoder_config/sensors_layout"
        request = ApiAdapterRequest(self.sensors_layout, content_type="application/json")
        self.adapters["fr"].put(command, request)

# curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fp/config/reorder/ -d '{"sensors_layout": "5x8"}'
# curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fr/config/decoder_config -d '{"sensors_layout": "500x895"}'

    def _get_height(self):

        return self.height
        
    def _set_height(self, rows):
        """Check that rows is an integer, above zero
        """
        if (isinstance(rows, integer_types)):
            if (rows > 0):
                self.height = rows
            else:
                raise HexitecError("Must be > 0")
        else:
            raise HexitecError("Must be an integer")

    def _get_width(self):

        return self.width
        
    def _set_width(self, columns):
        """Check that columns is an integer, above zero
        """
        if (isinstance(columns, integer_types)):
            if (columns > 0):
                self.width = columns
            else:
                raise HexitecError("Must be > 0")
        else:
            raise HexitecError("Must be an integer")

    def _get_threshold_value(self):

        return self.threshold_value
        
    def _set_threshold_value(self, value):
        """Check that (threshold) value is an integer, zero or above
        """
        if (isinstance(value, integer_types)):
            if (value >= 0):
                self.threshold_value = value
            else:
                raise HexitecError("Must be >= 0")
        else:
            raise HexitecError("Must be an integer")

    def _get_pixel_grid_size(self):

        return self.pixel_grid_size

    def _set_pixel_grid_size(self, pixel_grid_size):
        """Check that pixel grid size is an integer, either 3 or 5
        """
        if (isinstance(pixel_grid_size, integer_types)):
            if (pixel_grid_size == 3 or pixel_grid_size == 5):
                self.pixel_grid_size = pixel_grid_size
            else:
                raise HexitecError("Must be 3 or 5")
        else:
            raise HexitecError("Must be an integer")

    def _get_max_frames_received(self):

        return self.max_frames_received

    def _set_max_frames_received(self, max_frames_received):
        """Check that max_frames_received is an integer, above zero
        """
        if (isinstance(max_frames_received, integer_types)):
            if (max_frames_received > 0):
                self.max_frames_received = max_frames_received
            else:
                raise HexitecError("Must be above zero")
        else:
            raise HexitecError("Must be an integer")

    def _get_bin_start(self):

        return self.bin_start

    def _set_bin_start(self, bin_start):
        """Check that bin_start is an integer, zero or above
        """
        if (isinstance(bin_start, integer_types)):
            if (bin_start >= 0):
                self.bin_start = bin_start
            else:
                raise HexitecError("Must be zero or above")
        else:
            raise HexitecError("Must be an integer")

    def _get_bin_end(self):

        return self.bin_end

    def _set_bin_end(self, bin_end):
        """Check that bin_end is an integer, above zero
        """
        if (isinstance(bin_end, integer_types)):
            if (bin_end > 0):
                self.bin_end = bin_end
            else:
                raise HexitecError("Must be above zero")
        else:
            raise HexitecError("Must be an integer")

    def _get_bin_width(self):

        return self.bin_width

    def _set_bin_width(self, bin_width):
        """Check that bin_width is a float, above zero
        """
        # JavaScript converts zero fractionals into integers
        #   (I.e. 10.0 -> 10); Force integers to be floats:
        if (isinstance(bin_width, integer_types)):
            bin_width = float(bin_width)

        if (isinstance(bin_width, float_types)):
            if (bin_width >= 0):
                self.bin_width = bin_width
            else:
                raise HexitecError("Must be above zero")
        else:
            raise HexitecError("Must be a float")

    def _get_threshold_mode(self):

        return self.threshold_mode

    def _set_threshold_mode(self, mode):
        """Check that the threshold mode is either of
            none, value or filename
            """
        validChoices = ("none", "value", "filename")
        if (mode in validChoices):
            self.threshold_mode = mode
        else:
            raise HexitecError("Must be either of: none, value or filename")

    def get_server_uptime(self):
        """Get the uptime for the ODIN server.

        This method returns the current uptime for the ODIN server.
        """
        return time.time() - self.init_time

    def get(self, path):
        """Get the parameter tree.

        This method returns the parameter tree for use by clients via the Hexitec adapter.

        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree.

        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate HexitecError.

        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise HexitecError(e)

    def initialize(self, adapters):
        """Get references to required adapters and pass those references to the classes that need
            to use them
        """
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)

    # def set_task_interval(self, interval):

    #     logging.debug("Setting background task interval to %f", interval)
    #     self.background_task_interval = float(interval)
        
    # def set_task_enable(self, enable):

    #     logging.debug("Setting background task enable to %s", enable)

    #     current_enable = self.background_task_enable
    #     self.background_task_enable = bool(enable)

    #     if not current_enable:
    #         logging.debug("Restarting background task")
    #         self.background_task()


    # @run_on_executor
    # def background_task(self):
    #     """Run the adapter background task.

    #     This simply increments the background counter and sleeps for the specified interval,
    #     before adding itself as a callback to the IOLoop instance to be called again.

    #     """
    #     if self.background_task_counter < 10 or self.background_task_counter % 20 == 0:
    #         logging.debug("Background task running, count = %d", self.background_task_counter)

    #     self.background_task_counter += 1
    #     time.sleep(self.background_task_interval)

    #     if self.background_task_enable:
    #         IOLoop.instance().add_callback(self.background_task)
    #     else:
    #         logging.debug("Background task no longer enabled, stopping")
