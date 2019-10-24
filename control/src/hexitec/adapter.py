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
        # Intialise superclass
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

        # self.adapters["liveview"] = adapter

class HexitecError(Exception):
    """
    Simple exception class for Hexitec to wrap lower-level exceptions.
    """

    pass


class Hexitec():
    """
    Hexitec - class that extracts and stores information about system-level parameters.
    """

    # Thread executor used for background tasks
    # executor = futures.ThreadPoolExecutor(max_workers=1)
    thread_executor = futures.ThreadPoolExecutor(max_workers=1)

    THRESHOLDOPTIONS = ["value", "filename", "none"]

    def __init__(self, options):
        """
        Initialise the Hexitec object.

        This constructor initlialises the Hexitec object, building a parameter tree and
        launching a background task if enabled
        """
        # Begin implementing DAQ code..
        defaults = HexitecDetectorDefaults()
        self.file_dir = options.get("save_dir", defaults.save_dir)
        self.file_name = options.get("save_file", defaults.save_file)
        # self.vector_file_dir = options.get("vector_file_dir", defaults.vector_file_dir)
        # self.vector_file = options.get("vector_file_name", defaults.vector_file)
        self.number_frames = options.get("acquisition_num_frames", defaults.number_frames)
        # self.acq_gap = options.get("acquisition_frame_gap", defaults.acq_gap)
        # odin_data_dir = options.get("odin_data_dir", defaults.odin_data_dir)
        # odin_data_dir = os.path.expanduser(odin_data_dir)

        self.daq = HexitecDAQ(self.file_dir, self.file_name)

        # -------

        self.adapters = {}

        self.fem = HexitecFem()

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        self.dbgCount = 0

        # ParameterTree variables
        self.sensors_layout = "2x2"
        self.vcal = 3               # 0-2: Calibrated Image 0-2; 3: Normal data

        self.pixel_grid_size = 3
        self.gradients_filename = ""
        self.intercepts_filename = ""
        self.bin_end = 8000
        self.bin_start = 0
        self.bin_width = 10.0
        self.max_frames_received = 10
        self.raw_data = False
        self.threshold_filename = ""
        self.threshold_mode = "value"
        self.threshold_value = 100

        detector = ParameterTree({
            "fem": self.fem.param_tree,
            "daq": self.daq.param_tree,
            "connect_hardware": (None, self.connect_hardware),
            "initialise_hardware": (None, self.initialise_hardware),
            "collect_data": (None, self.collect_data),
            "disconnect_hardware": (None, self.disconnect_hardware),
            "collect_offsets": (None, self._collect_offsets),
            "commit_configuration": (None, self.commit_configuration),
            # "stop_acquisition": (None, self._set_stop_acquisition),
            # Move sensors_layout into own subtree?
            "sensors_layout": (self._get_sensors_layout, self._set_sensors_layout),
            "vcal": (self._get_vcal, self._set_vcal),
            "debug_count": (self._get_debug_count, self._set_debug_count),
            "config": {
                "addition": {
                    "pixel_grid_size": (lambda: self.pixel_grid_size, self._set_pixel_grid_size)#,
                },
                "calibration": {
                    "gradients_filename": (lambda: self.gradients_filename, self._set_gradients_filename),
                    "intercepts_filename": (lambda: self.intercepts_filename, self._set_intercepts_filename)#,
                },
                "discrimination": {
                    "pixel_grid_size": (lambda: self.pixel_grid_size, self._set_pixel_grid_size)#,
                },
                "histogram": {
                    "bin_end": (lambda: self.bin_end, self._set_bin_end),
                    "bin_start": (lambda: self.bin_start, self._set_bin_start),
                    "bin_width": (lambda: self.bin_width, self._set_bin_width),
                    "max_frames_received": (lambda: self.max_frames_received, self._set_max_frames_received)#,
                },
                "reorder": {
                    "raw_data": (lambda: self.raw_data, self._set_raw_data)#,
                },
                "threshold": {
                    "threshold_filename": (lambda: self.threshold_filename, self._set_threshold_filename),
                    "threshold_mode": (lambda: self.threshold_mode, self._set_threshold_mode),
                    "threshold_value": (lambda: self.threshold_value, self._set_threshold_value)
                }
            },
            # Implement acquisition through daq class:
            "acquisition": {
                "num_frames": (lambda: self.number_frames, self.set_number_frames),
                "start_acq": (None, self.acquisition)
            }
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            "odin_version": version_info['version'],
            "tornado_version": tornado.version,
            "server_uptime": (self.get_server_uptime, None),
            "detector": detector
        })
        self.update_rows_columns_pixels()

        self.start_polling()

    @run_on_executor(executor='thread_executor')
    def start_polling(self):
        IOLoop.instance().add_callback(self.poll_histograms)  # Polling Histogram status

    def poll_histograms(self):
        if (self.fem.acquisition_completed):
            timeout = time.time() - self.fem.acquisition_timestamp
            if (timeout > 1.0):
                # Issue reset to histogram
                command = "config/histogram/flush_histograms"
                request = ApiAdapterRequest(self.file_dir, content_type="application/json")
                request.body = "{}".format(1)
                self.adapters["fp"].put(command, request)
                # Clear fem's Boolean
                self.fem.acquisition_completed = False

        time.sleep(0.5)
        IOLoop.instance().call_later(0.5, self.poll_histograms)

    def connect_hardware(self, msg):
        self.fem.connect_hardware(msg)
      
    def initialise_hardware(self, msg):
        self.fem.initialise_hardware(msg)

    def collect_data(self, msg):
        self.fem.collect_data(msg)

    def disconnect_hardware(self, msg):
        self.fem.disconnect_hardware(msg)

    def set_number_frames(self, frames):
        self.number_frames = frames
        # Update number of frames in Hardware, and histogram and hdf plugins
        self.fem._set_number_frames(self.number_frames)

        # Avoid config/histogram/max_frames_received - use own paramTree instead
        self._set_max_frames_received(self.number_frames)

        command = "config/hdf/frames"
        request = ApiAdapterRequest(self.file_dir, content_type="application/json")
        request.body = "{}".format(self.number_frames)
        self.adapters["fp"].put(command, request)

        self.daq.set_file_writing(False)
        self.daq.set_file_writing(True)
        
    def update_rows_columns_pixels(self):
        """
        Updates rows, columns and pixels from new sensors_layout value
        """
        self.rows, self.columns = self.sensors_layout.split("x")
        self.rows = int(self.rows) * 80
        self.columns = int(self.columns) * 80
        self.pixels = self.rows * self.columns

    def _set_pixel_grid_size(self, size):
        if (self.pixel_grid_size in [3, 5]):
            self.pixel_grid_size = size
        else:
            raise ParameterTreeError("Must be either 3 or 5")

    def _set_gradients_filename(self, gradients_filename):
        if (os.path.isfile(gradients_filename) == False):
            raise ParameterTreeError("Gradients file doesn't exist")
        self.gradients_filename = gradients_filename

    def _set_intercepts_filename(self, intercepts_filename):
        if (os.path.isfile(intercepts_filename) == False):
            raise ParameterTreeError("Intercepts file doesn't exist")
        self.intercepts_filename = intercepts_filename

    def _set_bin_end(self, bin_end):
        """
        Updates bin_end, datasets' histograms' dimensions
        """
        self.bin_end = bin_end
        self.update_histogram_dimensions()
    
    def _set_bin_start(self, bin_start):
        """
        Updates bin_start, datasets' histograms' dimensions
        """
        self.bin_start = bin_start
        self.update_histogram_dimensions()
    
    def _set_bin_width(self, bin_width):
        """
        Updates bin_width, datasets' histograms' dimensions
        """
        self.bin_width = bin_width
        self.update_histogram_dimensions()

    def update_datasets_frame_dimensions(self):
        """
        Updates frames datasets' dimensions
        """
        # Update data, raw_data datasets
        for dataset in ["data", "raw_frames"]:
            payload = '{"dims": [%s, %s]}' % (self.rows, self.columns)
            command = "config/hdf/dataset/" + dataset
            request = ApiAdapterRequest(str(payload), content_type="application/json")
            self.adapters["fp"].put(command, request)

    def update_histogram_dimensions(self):
        """
        Updates histograms' dimensions in the relevant datasets
        """
        number_of_histograms = int((self.bin_end - self.bin_start) / self.bin_width)
        # energy_bins dataset
        payload = '{"dims": [%s]}' % (number_of_histograms)
        command = "config/hdf/dataset/" + "energy_bins"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

        # pixel_histograms dataset
        payload = '{"dims": [%s, %s]}' % (self.pixels, number_of_histograms)
        command = "config/hdf/dataset/" + "pixel_histograms"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

        # summed_histograms dataset
        payload = '{"dims": [%s]}' % (number_of_histograms)
        command = "config/hdf/dataset/" + "summed_histograms"
        request = ApiAdapterRequest(str(payload), content_type="application/json")
        self.adapters["fp"].put(command, request)

    def _set_max_frames_received(self, max_frames_received):
        self.max_frames_received = max_frames_received

    def _set_raw_data(self, raw_data):
        self.raw_data = raw_data

    def _set_threshold_filename(self, threshold_filename):
        if (os.path.isfile(threshold_filename) == False):
            raise ParameterTreeError("Threshold file doesn't exist")
        self.threshold_filename = threshold_filename

    def _set_threshold_mode(self, threshold_mode):
        threshold_mode = threshold_mode.lower()
        if (threshold_mode in self.THRESHOLDOPTIONS):
            self.threshold_mode = threshold_mode
        else:
            raise ParameterTreeError("Must be one of: value, filename or none")

    def _set_threshold_value(self, threshold_value):
        self.threshold_value = threshold_value

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

    def acquisition(self, put_data):
        if self.daq.in_progress:
            logging.warning("Cannot Start Acquistion: Already in progress")
            return
        self.daq.start_acquisition(self.number_frames)
        # for fem in self.fems:
        self.fem.setup_camera()
            # fem.get_aligner_status()  # TODO: is this required?
            # locked = fem.get_idelay_lock_status()
            # if not locked:
            #     fem.load_vectors_from_file()
        self.fem.collect_data()
        # self.fems[0].frame_gate_settings(self.number_frames - 1, self.acq_gap)
        # self.fems[0].frame_gate_trigger()

    # def _set_stop_acquisition(self, stop):
    #     self.fem._set_stop_acquisition = stop

    def _get_sensors_layout(self):
        return self.sensors_layout

    def _set_sensors_layout(self, layout):
        """
        Sets sensors_layout in all FP's plugins and FR; Recalculates rows, columns and pixels
        """
        self.sensors_layout = layout

        # send command to all FP plugins, then FR
        plugins =  ['addition', 'calibration', 'discrimination', 'histogram', 'reorder', 
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

    def _get_vcal(self):
        return self.vcal

    def _set_vcal(self, vcal):
        """
        Sets vcal in Fem(s)
        """
        self.vcal = vcal
        self.fem._set_test_mode_image(vcal)

    def _collect_offsets(self, msg):
        """
        Instructs fem(s) to collect offsets
        """
        self.fem.collect_offsets()        
        
    def commit_configuration(self, msg):
        """
        Pushes settings in 'config/' ParameterTree into FP's plugins
        """
        # Loop overall plugins in ParameterTree, updating fp's settings
        #   Except reorder, until raw_data (i.e. bool) supported
        for plugin in self.param_tree.tree['detector'].get("config"):

            if plugin != "reorder":

                for param_key in self.param_tree.tree['detector']['config'].get(plugin):

                    # print "\nconfig/%s/%s" % (plugin, param_key), " -> ", \
                    #         self.param_tree.tree['detector']['config'][plugin][param_key].get(), "\n"

                    command = "config/%s/%s" % (plugin, param_key)
                    payload = self.param_tree.tree['detector']['config'][plugin][param_key].get()
                    request = ApiAdapterRequest(str(payload), content_type="application/json")
                    self.adapters["fp"].put(command, request)

        # Effin' works:
        # command = "config/threshold/threshold_value"
        # payload = str(121)
        # request = ApiAdapterRequest(payload, content_type="application/json")
        # self.adapters["fp"].put(command, request)

        # What does work:
        #curl -s -H 'Content-type:application/json' -X PUT http://localhost:8888/api/0.1/hexitec/fp/config/threshold -d 
        #   '{"threshold_value": 7, "threshold_mode": "none"}' | python -m json.tool
        # (But not {"threshold": {"threshold_value": 7, ...}} !)

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

        This method simply wraps underlying ParameterTree method so that an exceptions can be
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
        # self.vector_file_dir = "/aeg_sw/work/projects/qem/python/03052018/"
        # self.vector_file = "QEM_D4_198_ADC_10_icbias30_ifbias24.txt"
        # self.odin_data_dir = "~/develop/projects/odin-demo/install/"
        self.number_frames = 20
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
