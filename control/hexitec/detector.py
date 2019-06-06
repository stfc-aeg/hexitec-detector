""" Hexitec Detector adapter class for the ODIN server.

The IacDetectorAdapter class implements an adapter for the ODIN server that handle
inter adapter communication.

Christian Angelsen, STFC Application Engineering
"""
import logging
from concurrent import futures
import time
from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor

from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types, response_types)
from odin.util import decode_request_body


class IacDetectorAdapter(ApiAdapter):
    """Detector adapter class for Inter Adapter Communications.

    This adapter implements the basic operations of GET and PUT,
    and allows another adapter to interact with it via these methods.
    """

    def __init__(self, **kwargs):
        """Initialize the Detector adapter.

        Create the adapter using the base adapter class.
        Create an empty dictionary to store the references to other loaded adapters.
        """

        super(IacDetectorAdapter, self).__init__(**kwargs)
        self.adapters = {}

        logging.debug("IAC Detector Adapter Loaded")

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
        """Initialize the adapter after it has been loaded.

        Receive a dictionary of all loaded adapters so that they may be accessed by this adapter.
        Remove itself from the dictionary so that it does not reference itself, as doing so
        could end with an endless recursive loop.
        """

        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)

        for k, v in adapters.items():
            logging.debug("Adapter loaded: %s", k)
        #logging.debug("Received following dict of Adapters: %s", self.adapters)
