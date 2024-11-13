"""Adapter for ODIN control archiver

This class implements an adapter used for archiving Odin-data HDF5 files

Christian Angelsen, STFC Application Engineering
"""
import logging
import tornado
import time
from persistqueue import Queue
from concurrent import futures
from datetime import datetime
import subprocess
import os

from tornado.concurrent import run_on_executor
from tornado.escape import json_decode

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin._version import get_versions


class ArchiverAdapter(ApiAdapter):
    """Archiver adapter class for the ODIN server.

    This adapter provides the functionality to archive data files from
    remote PCs into a local directory.
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

        self.archiver.check_queue_not_empty()

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
    """Archiver - class that archives data files from remote servers to local directory."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, local_dir):
        """Initialise the Archiver object.

        This constructor initlialises the Archiver object, building a parameter tree and
        resumes archiving data file(s) if previously interrupted
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
        self.persistent_file_path = "/tmp/"

        # Track history of errors, messages
        self.errors_history = []
        timestamp = self.create_timestamp()
        self.last_message_timestamp = ''
        self.log_messages = [timestamp, "initialised OK"]
        # File transfer information
        self.transfer_status = ""
        self.filename_transferring = ""
        self.transfer_progress = ""

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
            'transfer_status': (lambda: self.transfer_status, None),
            'filename_transferring': (lambda: self.filename_transferring, None),
            'transfer_progress': (lambda: self.transfer_progress, None),
            'last_message_timestamp': (lambda: self.last_message_timestamp, self.get_log_messages)
        })

    def __del__(self):
        print("\n *** DTOR ***\n")

    def check_queue_not_empty(self):
        """ Check whether persistent queue already have file(s) to transfer."""
        q = Queue(self.persistent_file_path)
        q_size = q.info['size']
        print(f" *** {q_size} file(s) on start-up ***")
        if q_size > 0:
            logging.debug(f"Queue contain {q_size} file(s), resuming..")
            self.archive_files()
        else:
            logging.debug("Queue empty")
        del q

    def set_local_dir(self, dir):
        """Set directory to receive HDF5 files."""
        self.local_dir = dir

    def set_files_to_archive(self, full_path):
        """Syntax of 'server:/path/to.h5' describing server and file to be queued."""
        try:
            server, file = full_path.split(":")
            q = Queue(self.persistent_file_path)
            q.put(full_path)
            q_size = q.info['size']
            logging.debug(f"Received server {server} file {file} joining queue of {q_size} file(s)")
            del q
        except ValueError:
            error = f"Cannot parse '{full_path}', syntax should be 'server:/path/to.h5'"
            logging.error(error)
            raise ValueError(error)

    def get_files_to_archive(self):
        """Return number of files to be archived."""
        return str(self.files_to_archive)

    @run_on_executor(executor='executor')
    def archive_files(self, msg=None):
        """Execute archiving of files onto local dir."""
        q = Queue(self.persistent_file_path)
        if q.info['size'] == 0:
            logging.warning("No files in queue, archiving skipped")
            del q
            return 0
        logging.debug("Pulling selected file(s)..")
        local_dir = self.local_dir
        files_failed_this_time = 0
        files_archived_this_time = 0
        options = '-aP'
        while not q.empty():
            full_path = q.get()
            server, file = full_path.split(":")
            r_cmd = ['rsync', options, f'{server}:{file}', local_dir]
            print(f"2. r_cmd: {r_cmd}. ")
            bOK, errors = self.execute_rsync_command(r_cmd)
            if bOK:
                self.flag_ok(f"Copied {server}:{file} to {local_dir}")
                files_archived_this_time += 1
            else:
                self.flag_error(f"Failed to copy {server}:{file}", errors)
                files_failed_this_time += 1
            # Once rsync transfer completed, persist the change in the queue (item dequeued):
            q.task_done()
        logging.debug(f"Archiving completed, {files_archived_this_time} file(s) archived.")
        self.files_to_archive = {}
        if files_failed_this_time:
            logging.warning(f"{files_failed_this_time} file(s) failed to be archived.")
        # Total up number of successes, failures over multiple transfers:
        self.number_files_failed += files_failed_this_time
        self.number_files_archived += files_archived_this_time

    def execute_rsync_command(self, cmd):
        """Execute rsync command through subprocess."""
        errors = []
        bOK = True
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.set_blocking(p.stdout.fileno(), False)
            os.set_blocking(p.stderr.fileno(), False)
            while p.poll() is None:
                error_line = p.stderr.readline()
                if len(error_line) > 0:
                    bOK = False
                    errors.append(self.parse_error_bytes(error_line))
                    # print(f" Error? {error_line}")
                output_line = p.stdout.readline()
                if len(output_line) > 0:
                    # print("poll: ", p.poll(), " length? ", len(output_line), "ln: ", output_line)
                    self.parse_rsync_output(output_line)
        except Exception as e:
            print(f"Error return call: {e.returncode}")
        return bOK, errors

    def parse_error_bytes(self, bytes_object):
        """Parse bytes object into string."""
        string_object = bytes_object.decode("utf-8")
        return string_object.strip()

    def parse_rsync_output(self, bytes_object):
        """Parse output from rsync command execution.

        Typically output may look like this:
        sending incremental file list
        08-11-002_000000.h5
                32,768   0%    0.00kB/s    0:00:00
            108,592,900  44%  103.35MB/s    0:00:01
            246,080,238 100%  112.76MB/s    0:00:02 (xfr#1, to-chk=0/1)
        """
        bytes_stripped = bytes_object.strip()
        string_object = bytes_stripped.decode("utf-8")
        if string_object.endswith(".h5"):
            self.filename_transferring = string_object
            self.transfer_status = "Transferring file.."
            return
        # logging.debug(f" DEBUG transfer: {string_object}")
        # Check string contains '%' otherwise no transfer data in string
        if "%" not in string_object:
            return
        if "chk" in string_object:
            self.transfer_status = "File transferred"
            self.transfer_progress = 100
            return
        size_and_percentage, datarate_remaining = string_object.split("%")
        # print("1. size_and_percentage, datarate_remaining = ",
        #       size_and_percentage, datarate_remaining)
        size_and_percentage = size_and_percentage.split(" ")
        size = size_and_percentage[0]
        percentage = size_and_percentage[-1]
        self.transfer_progress = percentage
        # print("2. size, percentage = ", size_and_percentage[0], size_and_percentage[-1])
        datarate_remaining = datarate_remaining.strip()
        # print("3. datarate_remaining = ", datarate_remaining)
        # print("4. datarate_blank_remaining = ", datarate_remaining.split(" "))
        datarate_blank_remaining = datarate_remaining.split(" ")
        datarate, remaining = datarate_blank_remaining[0], datarate_blank_remaining[-1]
        # print("5. datarate, remaining = ", datarate, remaining)
        # print(f" -> size= {size}, percent= {percentage}, rate= {datarate}, remain= {remaining}")
        return size, percentage, datarate, remaining

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
