"""Adapter for Hexitec ODIN control

This class implements an  adapter used for Hexitec

Christian Angelsen, STFC Application Engineering
"""
import logging
import tornado
import time
from concurrent import futures

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

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin._version import get_versions


class HexitecAdapter(ApiAdapter):
    """System info adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the server and the system that it is
    running on.
    """

    def __init__(self, **kwargs):
        """Initialize the HexitecAdapter object.

        This constructor initializes the HexitecAdapter object.

        :param kwargs: keyword arguments specifying options
        """
        # Intialise superclass
        super(HexitecAdapter, self).__init__(**kwargs)

        # Parse options
        background_task_enable = bool(self.options.get('background_task_enable', False))
        background_task_interval = float(self.options.get('background_task_interval', 5.0))
        
        self.hexitec = Hexitec(background_task_enable, background_task_interval)

        logging.debug('HexitecAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.hexitec.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        content_type = 'application/json'

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
        try:
            data = json_decode(request.body)
            data = self.convert_to_string(data)
            self.hexitec.set(path, data)
            response = self.hexitec.get(path)
            status_code = 200
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

class HexitecError(Exception):
    """Simple exception class for Hexitec to wrap lower-level exceptions."""

    pass


class Hexitec():
    """Hexitec - class that extracts and stores information about system-level parameters."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, background_task_enable, background_task_interval):
        """Initialise the Hexitec object.

        This constructor initlialises the Hexitec object, building a parameter tree and
        launching a background task if enabled
        """
        # Save arguments
        self.background_task_enable = background_task_enable
        self.background_task_interval = background_task_interval

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        # Build a parameter tree for the background task
        bg_task = ParameterTree({
            'count': (lambda: self.background_task_counter, None),
            'enable': (lambda: self.background_task_enable, self.set_task_enable),
            'interval': (lambda: self.background_task_interval, self.set_task_interval),
        })

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
            'enable': False
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
        # Charged Sharing
        charged_sharing = ParameterTree({
            'addition': False,
            'discrimination': False,
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

        # Build odin_data (vars) area here
        odin_data = ParameterTree({
            'reorder': reorder,
            'threshold': threshold,
            'next_frame': False,
            'calibration': calibration,
            'charged_sharing': charged_sharing,
            'histogram': histogram
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'odin_version': version_info['version'],
            'tornado_version': tornado.version,
            'server_uptime': (self.get_server_uptime, None),
            'background_task': bg_task,
            'test_area': test_area,
            'odin_data': odin_data
        })

        # Set the background task counter to zero
        self.background_task_counter = 0

        # Launch the background task if enabled in options
        if self.background_task_enable:
            logging.debug(
                "Launching background task with interval %.2f secs", background_task_interval
            )
            self.background_task()

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

    def set_task_interval(self, interval):

        logging.debug("Setting background task interval to %f", interval)
        self.background_task_interval = float(interval)
        
    def set_task_enable(self, enable):

        logging.debug("Setting background task enable to %s", enable)

        current_enable = self.background_task_enable
        self.background_task_enable = bool(enable)

        if not current_enable:
            logging.debug("Restarting background task")
            self.background_task()


    @run_on_executor
    def background_task(self):
        """Run the adapter background task.

        This simply increments the background counter and sleeps for the specified interval,
        before adding itself as a callback to the IOLoop instance to be called again.

        """
        if self.background_task_counter < 10 or self.background_task_counter % 20 == 0:
            logging.debug("Background task running, count = %d", self.background_task_counter)

        self.background_task_counter += 1
        time.sleep(self.background_task_interval)

        if self.background_task_enable:
            IOLoop.instance().add_callback(self.background_task)
        else:
            logging.debug("Background task no longer enabled, stopping")
