"""Adapter for ODIN control archiver

This class implements an adapter used for archiving Odin-data HDF5 files

Christian Angelsen, STFC Application Engineering
"""
import logging
import tornado
import time
from concurrent import futures
from datetime import datetime
import subprocess
import sysrsync

from tornado.concurrent import run_on_executor
from tornado.escape import json_decode

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin._version import get_versions


class ArchiverAdapter(ApiAdapter):
    """System info adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the server and the system that it is
    running on.
    """

    def __init__(self, **kwargs):
        """Initialize the ArchiverAdapter object.

        This constructor initializes the ArchiverAdapter object.

        :param kwargs: keyword arguments specifying options
        """
        # Intialise superclass
        super(ArchiverAdapter, self).__init__(**kwargs)

        # Parse options
        local_dir = self.options.get('local_dir', "/")

        self.archiver = Archiver(local_dir)

        logging.debug('ArchiverAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.archiver.get(path)
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
            self.archiver.set(path, data)
            response = self.archiver.get(path)
            status_code = 200
        except ArchiverError as e:
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
        response = 'ArchiverAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    def cleanup(self):
        """Clean up adapter state at shutdown.

        This method cleans up the adapter state when called by the server at e.g. shutdown.
        It simplied calls the cleanup function of the archiver instance.
        """
        self.archiver.cleanup()


class ArchiverError(Exception):
    """Simple exception class to wrap lower-level exceptions."""

    pass


class Archiver():
    """Archiver - class that extracts and stores information about system-level parameters."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, local_dir):
        """Initialise the Archiver object.

        This constructor initlialises the Archiver object, building a parameter tree and
        launching a background task if enabled
        """
        # Save arguments
        self.local_dir = local_dir

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        self.files_to_archive = {}
        self.number_files_archived = 0
        self.number_files_failed = 0

        # Track history of errors
        self.errors_history = []
        timestamp = self.create_timestamp()
        self.last_message_timestamp = ''
        self.log_messages = [timestamp, "initialised OK"]

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'odin_version': version_info['version'],
            'tornado_version': tornado.version,
            'server_uptime': (self.get_server_uptime, None),
            'files_to_archive': (self.get_files_to_archive, self.set_files_to_archive),
            'local_dir': (lambda: self.local_dir, self.set_local_dir),
            'archive_files': (None, self.archive_files),
            "errors_history": (lambda: self.errors_history, None),
            'log_messages': (lambda: self.log_messages, None),
            'last_message_timestamp': (lambda: self.last_message_timestamp, self.get_log_messages)
        })

    def set_local_dir(self, dir):
        """Set directory to receive HDF5 files."""
        self.local_dir = dir

    def set_files_to_archive(self, full_path):
        """Syntax of 'server:/path/to.h5' describing server and file to be archived."""
        server, file = full_path.split(":")
        logging.debug(f"Received server {server} file {file} to be archived")
        if server in self.files_to_archive:
            # PC already listed with file(s)
            self.files_to_archive[server].append(file)
        else:
            # PC not listed, add
            self.files_to_archive[server] = [file]

    def get_files_to_archive(self):
        """Return number of files to be archived."""
        return str(self.files_to_archive)

    @run_on_executor(executor='executor')
    def archive_files(self, msg):
        """Execute archiving of files onto local dir."""
        if len(self.files_to_archive) == 0:
            logging.warning("No files in queue, archiving skipped")
            return 0
        logging.debug("Pulling selected file(s)..")
        local_dir = self.local_dir
        files_failed_this_time = 0
        files_archived_this_time = 0
        for remote_server in self.files_to_archive:
            for remote_source in self.files_to_archive[remote_server]:
                r_cmd = sysrsync.get_rsync_command(source=remote_source,
                                                   destination=local_dir,
                                                   source_ssh=remote_server,
                                                   options=['-a'],
                                                   sync_source_contents=False)
                sp = subprocess.run(r_cmd, capture_output=True, text=True)
                if sp.returncode == 0:
                    self.flag_ok(f"Copied {remote_server}:{remote_source} to {local_dir}")
                    files_archived_this_time += 1
                else:
                    self.flag_error(f"Failed to copy {remote_server}:{remote_source}", sp.stderr)
                    files_failed_this_time += 1
        logging.debug(f"Archiving completed, {files_archived_this_time} file(s) archived.")
        self.files_to_archive = {}
        if files_failed_this_time:
            logging.warning(f"{files_failed_this_time} file(s) failed to be archived.")
        # Total up number of successes, failures over multiple transfers:
        self.number_files_failed += files_failed_this_time
        self.number_files_archived += files_archived_this_time

    def flag_error(self, message, e=None):
        """Log error message to parameter tree."""
        error_message = "{}".format(message)
        if e:
            error_message += ": {}".format(e)
        logging.error(error_message)
        timestamp = self.create_timestamp()
        # Append to errors_history list, nested list of timestamp, error message
        self.errors_history.append([timestamp, error_message])

    def flag_ok(self, message):
        """Log message to parameter tree."""
        ok_message = "{}".format(message)
        logging.debug(ok_message)
        timestamp = self.create_timestamp()
        # Append to log_messages list, nested list of timestamp, log message
        self.log_messages.append([timestamp, ok_message])

    def create_timestamp(self):
        """Returns timestamp of now."""
        return '{}'.format(datetime.now().strftime('%Y%m%d_%H%M%S.%f'))

    def get_log_messages(self, last_message_timestamp):
        """This method gets the log messages that are appended to the log message deque by the
        log function, and adds them to the log_messages variable. If a last message timestamp is
        provided, it will only get the subsequent log messages if there are any, otherwise it will
        get all of the messages from the deque.
        """
        logs = []
        if self.last_message_timestamp != "":
            # Display any new message
            for index, (timestamp, log_message) in enumerate(self.errors_history):
                if timestamp > last_message_timestamp:
                    logs = self.errors_history[index:]
                    break
        else:
            logs = self.errors_history
            self.last_message_timestamp = self.create_timestamp()

        self.log_messages = [(str(timestamp), log_message) for timestamp, log_message in logs]

    def get_server_uptime(self):
        """Get the uptime for the ODIN server.

        This method returns the current uptime for the ODIN server.
        """
        return time.time() - self.init_time

    def get(self, path):
        """Get the parameter tree.

        This method returns the parameter tree for use by clients via the Archiver adapter.

        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree.

        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate ArchiverError.

        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise ArchiverError(e)

    def cleanup(self):
        """Clean up the Archiver instance.

        This method stops the background tasks, allowing the adapter state to be cleaned up
        correctly.
        """
        pass
