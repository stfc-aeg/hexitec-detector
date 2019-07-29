"""Adapter for Hexitec ODIN control

This class implements an adapter used for Hexitec

Christian Angelsen, STFC Application Engineering
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

from tornado.escape import json_decode
from concurrent import futures

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
                
        self.hexitec = Hexitec(self.options)

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

        # self.adapters["liveview"] = adapter

class HexitecError(Exception):
    """Simple exception class for Hexitec to wrap lower-level exceptions."""

    pass


class Hexitec():
    """Hexitec - class that extracts and stores information about system-level parameters."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, options):
        """Initialise the Hexitec object.

        This constructor initlialises the Hexitec object, building a parameter tree and
        launching a background task if enabled
        """
        # Save arguments
        # self.background_task_enable = background_task_enable
        # self.background_task_interval = background_task_interval

        # Begin implementing DAQ code..
        defaults = HexitecDetectorDefaults()
        self.file_dir = options.get("save_dir", defaults.save_dir)
        self.file_name = options.get("save_file", defaults.save_file)
        # self.vector_file_dir = options.get("vector_file_dir", defaults.vector_file_dir)
        # self.vector_file = options.get("vector_file_name", defaults.vector_file)
        # self.acq_num = options.get("acquisition_num_frames", defaults.acq_num)
        # self.acq_gap = options.get("acquisition_frame_gap", defaults.acq_gap)
        odin_data_dir = options.get("odin_data_dir", defaults.odin_data_dir)
        odin_data_dir = os.path.expanduser(odin_data_dir)

        self.daq = HexitecDAQ(self.file_dir, self.file_name, odin_data_dir=odin_data_dir)

        # -------

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

        # Calibration
        calibration = ParameterTree({
            'gradients_filename': "",
            'intercepts_filename': "",
            'enable': False
        })

        ### POPULATE REPLACEMENT parameter tree ###
        self.sensors_layout = "2x2"
        odin_control = ParameterTree({
            'hexitec_fem': self.fem.param_tree,
            # sensors_layout belong to Odin Data..
            'sensors_layout': (self._get_sensors_layout, self._set_sensors_layout),
            'daq': self.daq.param_tree
        })

        # Build odin_data (vars) area here
        odin_data = ParameterTree({
            'next_frame': False,
            'calibration': calibration,
            'odin_control': odin_control
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'odin_version': version_info['version'],
            'tornado_version': tornado.version,
            'server_uptime': (self.get_server_uptime, None),
            # 'background_task': bg_task,
            'odin_data': odin_data
        })

        # # Set the background task counter to zero
        # self.background_task_counter = 0

        # # Launch the background task if enabled in options
        # if self.background_task_enable:
        #     logging.debug(
        #         "Launching background task with interval %.2f secs", background_task_interval
        #     )
        #     self.background_task()

    def initialize(self, adapters):
        """Get references to required adapters and pass those references to the classes that need
            to use them
        """
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)

        self.daq.initialize(self.adapters)

    def cleanup(self):
        self.daq.cleanup()

    def _get_sensors_layout(self):

        return self.sensors_layout

    def _set_sensors_layout(self, layout):

        self.sensors_layout = layout

        # send command to all FP plugins, then FR
        plugins =  ['addition', 'calibration', 'discrimination', 'histogram', 'reorder', 'next_frame', 'threshold']

        for plugin in plugins:
            command = "config/" + plugin + "/sensors_layout"
            request = ApiAdapterRequest(self.sensors_layout, content_type="application/json")
            self.adapters["fp"].put(command, request)

        command = "config/decoder_config/sensors_layout"
        request = ApiAdapterRequest(self.sensors_layout, content_type="application/json")
        self.adapters["fr"].put(command, request)

# curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fp/config/reorder/ -d '{"sensors_layout": "5x8"}'
# curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fr/config/decoder_config -d '{"sensors_layout": "500x895"}'

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

class HexitecDetectorDefaults():

    def __init__(self):
        self.save_dir = "/tmp/"
        self.save_file = "default_file"
        # self.vector_file_dir = "/aeg_sw/work/projects/qem/python/03052018/"
        # self.vector_file = "QEM_D4_198_ADC_10_icbias30_ifbias24.txt"
        self.odin_data_dir = "~/develop/projects/odin-demo/install/"
        self.acq_num = 4096
        self.acq_gap = 1
        self.fem = {
            "ip_addr": "192.168.0.122",
            "port": "8070",
            "id": 0,
            "server_ctrl_ip": "10.0.1.2",
            "camera_ctrl_ip": "10.0.1.102",
            "server_data_ip": "10.0.2.2",
            "camera_data_ip": "10.0.2.102"
        }