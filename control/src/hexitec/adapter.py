"""Adapter for Hexitec ODIN control

This class implements an adapter used for Hexitec

Christian Angelsen, STFC Detector Systems Software Group
"""
import logging
import tornado
import time
import os
#
import threading

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

    def __init__(self, options):
        """
        Initialise the Hexitec object.

        This constructor initialises the Hexitec object, building a parameter tree and
        launching a background task if enabled
        """
        # Begin implementing DAQ code..
        defaults = HexitecDetectorDefaults()
        self.file_dir = options.get("save_dir", defaults.save_dir)
        self.file_name = options.get("save_file", defaults.save_file)
        self.number_frames = options.get("acquisition_num_frames", defaults.number_frames)

        self.daq = HexitecDAQ(self.file_dir, self.file_name)

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
                    fem_dict.get("ip_addr", defaults.fem["ip_addr"]),
                    fem_dict.get("port", defaults.fem["port"]),
                    fem_dict.get("id", defaults.fem["id"]),
                    fem_dict.get("server_ctrl_ip_addr", defaults.fem["server_ctrl_ip"]),
                    fem_dict.get("camera_ctrl_ip_addr", defaults.fem["camera_ctrl_ip"]),
                    fem_dict.get("server_data_ip_addr", defaults.fem["server_data_ip"]),
                    fem_dict.get("camera_data_ip_addr", defaults.fem["camera_data_ip"])
                ))

        if not self.fems:  # if self.fems is empty
            self.fems.append(HexitecFem(
                ip_address=defaults.fem["ip_addr"],
                port=defaults.fem["port"],
                fem_id=defaults.fem["id"],
                server_ctrl_ip_addr=defaults.fem["server_ctrl_ip"],
                camera_ctrl_ip_addr=defaults.fem["camera_ctrl_ip"],
                server_data_ip_addr=defaults.fem["server_data_ip"],
                camera_data_ip_addr=defaults.fem["camera_data_ip"]
            ))

        fem_tree = {}
        for fem in self.fems:
            fem_tree["fem_{}".format(fem.id)] = fem.param_tree

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
            "collect_data": (None, self.collect_data),
            "disconnect_hardware": (None, self.disconnect_hardware),
            "collect_offsets": (None, self._collect_offsets),
            "commit_configuration": (None, self.commit_configuration),
            # "stop_acquisition": (None, self._set_stop_acquisition),
            "vcal": (self._get_vcal, self._set_vcal),
            "debug_count": (self._get_debug_count, self._set_debug_count),
            # Implement acquisition through daq class:
            "acquisition": {
                "num_frames": (lambda: self.number_frames, self.set_number_frames),
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
        IOLoop.instance().add_callback(self.poll_histograms)  # Polling Histogram status

    def poll_histograms(self):
        # for t in threading.enumerate():
        #     logging.debug(" *** thread: %s" % t.getName())
        # logging.debug("tick-tock!? \n")
        start = time.time()
        for fem in self.fems:
            if fem.acquisition_completed:
                timeout = time.time() - fem.acquisition_timestamp
                if (timeout > 1.0):
                    # Issue reset to histogram
                    command = "config/histogram/flush_histograms"
                    request = ApiAdapterRequest(self.file_dir, content_type="application/json")
                    request.body = "{}".format(1)
                    self.adapters["fp"].put(command, request)
                    # Clear fem's Boolean
                    fem.acquisition_completed = False
            #TODO: Also check sensor values?
            # ..
            health = fem.get_health()
            # Don't note current id if error already found in another fem
            if self.health:
                self.fem_id = fem.get_id()
                self.status_error = fem._get_status_error()
                self.status_message = fem._get_status_message()
                self.health = self.health and health
                # print(" Health report; fem id (%s)" % fem.get_id(), "    err: ", self.status_error,"    msg: ", self.status_message)
            else:
                pass
                # print(" ALERT: Don't note fem's id (%s). Existing info:" % fem.get_id(), "    err: ", self.status_error, "    msg: ", self.status_message)

        IOLoop.instance().call_later(1.0, self.poll_histograms)

    def connect_hardware(self, msg):
        for fem in self.fems:
            fem.connect_hardware(msg)

    def initialise_hardware(self, msg):
        for fem in self.fems:
            fem.initialise_hardware(msg)

    def collect_data(self, msg):
        for fem in self.fems:
            fem.collect_data(msg)

    def disconnect_hardware(self, msg):
        for fem in self.fems:
            fem.disconnect_hardware(msg)
        # With all FEM(s) disconnected, reset system status
        self.status_error = ""
        self.status_message = ""
        self.health = True

    def set_number_frames(self, frames):
        self.number_frames = frames
        # Update number of frames in Hardware, and (via DAQ) histogram and hdf plugins
        for fem in self.fems:
            fem._set_number_frames(self.number_frames)

        self.daq.set_number_frames(self.number_frames)

        # Toggle file writing off/on if current on
        if self.daq.file_writing:
            self.daq.set_file_writing(False)
            self.daq.set_file_writing(True)
        
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
        for fem in self.fems:
            fem.collect_data()

    # def _set_stop_acquisition(self, stop):
    #     self.fems._set_stop_acquisition = stop


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
        self.number_frames = 10
        self.acq_gap = 1
        self.fem = {
            "ip_addr": "192.168.0.122",
            "port": "8070",
            "id": 0,
            "server_ctrl_ip": "10.0.2.2",
            "camera_ctrl_ip": "10.0.2.1",
            "server_data_ip": "10.0.4.2",
            "camera_data_ip": "10.0.4.1"
        }
