""" Qem Detector Adapter for QEM Detector System.

Main control layer for the entire qem detector system.
Intelligent adapter that can communicate to all other loaded adapters lower down in the heirarchy.
Bridges the gap between generic UI commands and detector specific business logic.

Christian Angelsen, Detector Systems Software  Group, STFC. 2019
"""

import logging
import tornado
import time
from concurrent import futures
import os

from tornado.ioloop import IOLoop
from odin.util import decode_request_body, convert_unicode_to_string

from odin.adapters.adapter import ApiAdapter, ApiAdapterRequest, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

#from odin.adapters.proxy import ProxyAdapter
from odin_data.live_view_adapter import LiveViewAdapter
from odin_data.frame_processor_adapter import FrameProcessorAdapter
from odin_data.frame_receiver_adapter import FrameReceiverAdapter

from odin._version import get_versions

class HexitecDetectorAdapter(ApiAdapter):
    """Top Level Adapter for the Hexitec system

    """

    def __init__(self, **kwargs):
        """Initialize the HexitecDetectorAdapter object.

        This constructor initializes the HexitecDetector object.
        
        :param kwargs: keyword arguments specifying options
        """
        # Intialise superclass
        super(HexitecDetectorAdapter, self).__init__(**kwargs)
        self.hexitec = HexitecDetector()
        self.adapters = {}
        logging.debug('HexitecDetector Adapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.hexitec.get(path, request)
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
            data = convert_unicode_to_string(decode_request_body(request))
            self.hexitec.set(path, data)
            response = self.hexitec.get(path)
            status_code = 200
        except HexitecDetectorError as e:
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
        response = 'HexitecDetectorAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    def initialize(self, adapters):
        self.hexitec.initialize(adapters)

class HexitecDetectorError(Exception):
    """ Simple Exception class for Hexitec to wrap lower-level Exceptions."""

    pass

class HexitecDetector():
    """ HexitecDetector object representing the Hexitec Detector System.

    """

    def __init__(self, **kwargs):
        """Initialize the HexitecDetector adapter.

        Create the adapter using the base adapter class.
        Create an empty dictionary to store the references to other loaded adapters.
        """

        # super(HexitecDetector, self).__init__(**kwargs)
        self.adapters = {}

        logging.debug("HexitecDetector Loaded")

    @request_types("application/json", "application/vnd.odin-native")
    @response_types("application/json", default="application/json")
    def get(self, path, request):
        """Handle a HTTP GET Request

        Call the get method of each other adapter that is loaded and return the responses
        in a dictionary.
        """
        logging.debug("IAC Hexitec Get")
        response = {}
        request = ApiAdapterRequest(None, accept="application/json")
        for key, value in self.adapters.items():
            if path.startswith(key):
                # Lose 'key/' from the start of the path
                # (E.g. 'fp/' from 'fp/config/reorder/width')
                relative_path = path.split(key)
                path = relative_path[1]
                response[key] = value.get(path=path, request=request).data
                print key, " => ", response[key]
        logging.debug("Full response: %s", response)
        content_type = "application/json"
        status_code = 200

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types("application/json", "application/vnd.odin-native")
    @response_types("application/json", default="application/json")
    def put(self, path, request):
        """Handle a HTTP PUT request.

        Calls the put method of each, other adapter that has been loaded, and returns the responses
        in a dictionary.
        """
        logging.debug("IAC Hexitec PUT")
        response = {}
        status_code = 200

        for key, value in self.adapters.items():
            if path.startswith(key):
                # Lose 'key/' from start of path
                relative_path = path.split(key + '/')
                # response[key] = value.put(path=relative_path[1], request=request).data
                reply = value.put(path=relative_path[1], request=request)
                if reply.status_code != 200:
                    status_code = reply.status_code
                    response = reply.data
                # print " ! ", reply.data, reply.status_code, reply
        content_type = "application/json"
        # status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def initialize(self, adapters):
        """Get references to required adapters and pass those references to the classes that need
            to use them
        """
        for name, adapter in adapters.items():
            if isinstance(adapter, FrameProcessorAdapter):
                logging.debug("%s is FP Adapter", name)
                self.adapters["fp"] = adapter
            elif isinstance(adapter, FrameReceiverAdapter):
                logging.debug("%s is FR Adapter", name)
                self.adapters["fr"] = adapter
            elif isinstance(adapter, LiveViewAdapter):
                logging.debug("%s is Live View Adapter", name)
                self.adapters["liveview"] = adapter

