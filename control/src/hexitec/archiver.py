"""Adapter for ODIN control archiver

This class implements an adapter used for archiving Odin-data HDF5 files

Christian Angelsen, STFC Application Engineering
"""
import logging
import time
from persistqueue import Queue
from concurrent import futures
from datetime import datetime
import subprocess
import h5py
import glob
import os

from threading import Thread
# from tornado.ioloop import IOLoop
# from tornado.concurrent import run_on_executor
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

        self.archiver = Archiver(self.options)

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
    """Archiver - class that archives data files from remote servers to local directory."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, options):
        """Initialise the Archiver object.

        This constructor initlialises the Archiver object, building a parameter tree and
        resumes archiving data file(s) if previously interrupted
        """
        # Parse options
        self.local_dir = options.get('local_dir', "/")
        self.bandwidth_limit = options.get('bandwidth_limit', None)

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        self.number_files_archived = 0
        self.number_files_failed = 0
        self.persistent_file_path = "/tmp/"

        # Track history of errors, messages
        self.errors_history = []
        timestamp = self.create_timestamp()
        self.last_message_timestamp = ''
        self.log_messages = [timestamp, "initialised OK"]
        # File transfer information
        self.transfer_status = "Initialised"
        self.filename_transferring = ""
        self.transfer_progress = ""
        self.archiving_in_progress = False
        # Persistent Queue
        self.queue = Queue(self.persistent_file_path)
        self.qsize = self.queue.qsize

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'bandwidth_limit': (lambda: self.bandwidth_limit, None),
            'errors_history': (lambda: self.errors_history, None),
            'filename_transferring': (lambda: self.filename_transferring, None),
            'files_to_archive': (None, self.set_files_to_archive),
            'last_message_timestamp': (lambda: self.last_message_timestamp, self.get_log_messages),
            'local_dir': (lambda: self.local_dir, self.set_local_dir),
            'log_messages': (lambda: self.log_messages, None),
            'odin_version': version_info['version'],
            'server_uptime': (self.get_server_uptime, None),
            'transfer_progress': (lambda: self.transfer_progress, None),
            'transfer_status': (lambda: self.transfer_status, None),
            'queue_length': (self.queue.qsize, None)
        })

        # self.ioloop = None
        self.proc = None
        self.background_task_enable = True
        self.start_background_tasks()

    def start_background_tasks(self):
        """Start the background worker thread."""
        logging.debug("Launching worker thread")

        self.background_task_enable = True

        # Implementation using threading.Thread class
        self.background_ioloop_task = Thread(target=self.background_worker, args=(None,))
        self.background_ioloop_task.start()

        # Using tornado ioloop
        # self.background_worker()

    def stop_background_tasks(self):
        """Stop the background tasks."""
        self.background_task_enable = False
        if self.proc is not None:
            self.proc.kill()
            # self.ioloop.stop()
            # self.proc.join()
            # self.proc.stop()
        else:
            logging.debug("Work thread idle")

    # @run_on_executor
    def background_worker(self, msg=None):
        """Run the adapter worker thread.

        This simply wait until the queue has any file(s) to transfer. It will shutdown gracefully
        when the cleanup function boggles the background_task_enable to False.
        """
        # self.ioloop = IOLoop.current(instance=True)
        # This is the worker running in its own thread
        while self.background_task_enable:
            if self.queue.qsize() == 0:
                time.sleep(0.1)
            else:
                # logging.debug(f" DEBUG: File(s) in Q = ({self.queue.qsize()})")
                self.archive_files()
        logging.debug(" DEBUG: Worker thread stopping")

    def archive_files(self, msg=None):
        """Execute archiving of files onto local dir."""
        # 3 different possible rsync errors when archiver shutting down:
        # rsync error: received SIGINT, SIGTERM, or SIGHUP (code 20)
        # rsync error: unexplained error (code 255)
        # rsync error: <No description>  (code -9)

        self.archiving_in_progress = True
        logging.debug("Pulling selected file(s)..")
        local_dir = self.local_dir
        files_failed_this_time = 0
        files_archived_this_time = 0
        options = '-aP'
        resume = '--append'
        while not self.queue.empty():
            full_path = self.queue.get()
            try:
                server, file = full_path.split(":")
            except AttributeError:
                logging.error(f"Unexpected Queue item: {full_path}")
                self.queue.task_done()
                continue

            r_cmd = ['rsync', options, resume, f'{server}:{file}', local_dir]
            if self.bandwidth_limit:
                bwlimit = f"--bwlimit={self.bandwidth_limit}"
                r_cmd.append(bwlimit)
            # logging.debug(f" DEBUG: (task_enable) {self.background_task_enable} Built rsync r_cmd: {r_cmd}. ")
            logging.debug(f"Transferring from {server} file {file} [self.proc: {self.proc}]")
            bOK, errors, rc = self.execute_rsync_command(r_cmd)
            # logging.debug(f" DEBUG rsync completed; bOK: {bOK} errors: {errors} rc: {rc}")
            if (rc == 255) or (rc == -9) or (rc == 20):
                # logging.debug(f" DEBUG after archive_file() (task_enable={self.background_task_enable})")
                self.background_task_enable = False
                self.archiving_in_progress = False
                return
            if bOK:
                self.flag_ok(f"Copied {server}:{file} to {local_dir}")
                files_archived_this_time += 1
                # File safely transferred, persist queue change:
                if self.check_run_data_completed(file):
                    if self.map_virtual_datasets(file) != 0:
                        logging.warning("VDS failed to map Virtual datasets")
            else:
                self.flag_error(f"Failed to copy {server}:{file} error: {errors}")
                files_failed_this_time += 1
            # Once rsync transfer completed, persist the change in the queue (item dequeued):
            self.queue.task_done()
        logging.debug(f"Archiving completed, {files_archived_this_time} file(s) archived.")
        if files_failed_this_time:
            logging.warning(f"{files_failed_this_time} file(s) failed to be archived.")
        # Total up number of successes, failures over multiple transfers:
        self.number_files_failed += files_failed_this_time
        self.number_files_archived += files_archived_this_time
        self.archiving_in_progress = False
        self.transfer_status = "Idle"

    def parse_rsync_output(self, bytes_object):
        """Parse output from rsync command execution.

        Typically output look like this:
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
        # logging.debug(f" DEBUG (enable: {self.background_task_enable}) transfer: {string_object}")
        # Check string contains '%' otherwise no transfer data in string
        if "%" not in string_object:
            return
        if "chk" in string_object:
            self.transfer_status = "File transferred"
            self.transfer_progress = 100
            return
        size_and_percentage, datarate_remaining = string_object.split("%")
        size_and_percentage = size_and_percentage.split(" ")
        # size = size_and_percentage[0]
        percentage = size_and_percentage[-1]
        self.transfer_progress = percentage
        # # For future development, useful for UI?
        # datarate_remaining = datarate_remaining.strip()
        # datarate_blank_remaining = datarate_remaining.split(" ")
        # datarate, remaining = datarate_blank_remaining[0], datarate_blank_remaining[-1]
        # print(f" -> size= {size}, percent= {percentage}, rate= {datarate}, remain= {remaining}")
        # return size, percentage, datarate, remaining

    def execute_rsync_command(self, cmd):
        """Execute rsync command through subprocess."""
        errors = []
        bOK = True
        rc = 0
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.set_blocking(self.proc.stdout.fileno(), False)
            os.set_blocking(self.proc.stderr.fileno(), False)
            while self.proc.poll() is None:
                error_line = self.proc.stderr.readline()
                if len(error_line) > 0:
                    bOK = False
                    errors.append(self.parse_error_bytes(error_line))
                    # print(f" Error? {error_line}")
                output_line = self.proc.stdout.readline()
                if len(output_line) > 0:
                    # print(f"poll: {self.proc.poll()} len {len(output_line)} ln {output_line}")
                    self.parse_rsync_output(output_line)
        except Exception as e:
            logging.error(f"rsync error, subprocess returned: {e.returncode}")
        rc = self.proc.returncode
        # Delete subprocess handle after file(s) transfered
        del self.proc
        self.proc = None
        return bOK, errors, rc

    def parse_error_bytes(self, bytes_object):
        """Parse bytes object into string."""
        string_object = bytes_object.decode("utf-8")
        return string_object.strip()

    def set_local_dir(self, dir):
        """Set directory to receive HDF5 files."""
        self.local_dir = dir

    def set_files_to_archive(self, full_path):
        """Syntax of 'server:/path/to.h5' describing server and file to be queued."""
        try:
            server, file = full_path.split(":")
            self.queue.put(full_path)
            self.q_size = self.queue.qsize()
            logging.debug(f"Received server {server} file {file}. Queue is {self.q_size} file(s)")
        except ValueError:
            error = f"Cannot parse '{full_path}', syntax should be 'server:/path/to.h5'"
            logging.error(error)
            raise ValueError(error)

    def map_virtual_datasets(self, filename):
        """Maps actual datasets into set of virtual datasets."""
        file_tokenised = filename.split(".h5")
        file_without_extension = file_tokenised[0]
        data_files = f"{file_without_extension}_*.h5"
        files_found = glob.glob(data_files)
        source_files = (sorted(files_found))
        num_sources = len(source_files)
        logging.debug(f"VDS found {num_sources} file(s), namely: {source_files}")
        if num_sources == 0:
            logging.error("Received meta data but no files containing real data")
            return -1
        dest_file = f'{filename}'
        dataset_names = []
        dtype = None
        inshape = None

        # Open first file to check how many datasets
        try:
            with h5py.File(source_files[0]) as file:
                num_datasets = len(file.keys())
                for dataset in file:  # Each dataset in current file
                    dataset_names.append(dataset)
        except OSError as e:
            logging.error(f"Error opening data file {source_files[0]}: {e}")
            return -1
        # print(f"first file contains: {dataset_names} dataset_names")

        vsources = []
        num_frames = [0 for idx in range(num_datasets)]
        dtype = [0 for idx in range(num_datasets)]
        inshape = [0 for idx in range(num_datasets)]
        # print(f"Number of files: {num_sources}, source files: {source_files}")
        # Loop over all source files, datasets
        for source in source_files:     # Go through all .h5 files
            with h5py.File(source) as file:     # Go through each file
                if num_datasets != len(file.keys()):
                    e = f"Expected {num_datasets} but {source} has {len(file.keys())} datasets"
                    logging.error(e)
                    return -2

                index = 0
                for dataset in file:  # Each dataset in current file
                    dset = file[dataset]

                    # 'spectra_bins' identical across files, need only one instance
                    if dataset == "spectra_bins":
                        num_frames[index] = 1
                    else:
                        num_frames[index] += dset.shape[0]

                    if not inshape[index]:
                        inshape[index] = dset.shape
                    if not dtype[index]:
                        dtype[index] = dset.dtype
                    else:
                        assert dset.dtype == dtype[index]

                    # print(f" {dataset}, shape={dset.shape}")
                    vsources.append(h5py.VirtualSource(source, dataset, shape=dset.shape))
                    index += 1
        layout = []
        dataset_index = [0 for idx in range(num_datasets)]
        index = -1
        for dataset in dataset_names:  # Iterate through all datasets
            index += 1

            if len(inshape[index]) == 2:
                n = 1
            else:
                n = 0
            # print(f"*** dataset: '{dataset}' Shape: {inshape[index]} n: {n}")
            if dataset == "spectra_bins":
                outshape = (inshape[index][1-n], inshape[index][2-n])
            elif dataset == "pixel_spectra":
                outshape = (num_frames[index], inshape[index][1],
                            inshape[index][2], inshape[index][3])
            else:
                outshape = (num_frames[index], inshape[index][1-n], inshape[index][2-n])
            # print(f" outshape = {outshape}")

            layout = h5py.VirtualLayout(shape=outshape, dtype=dtype[index])

            for (idx, vsource) in enumerate(vsources):
                current_index = idx % num_datasets
                if current_index == index:
                    temp_idx = dataset_index[current_index]

                    if dataset == "spectra_bins":
                        # print(f" spectra_bins, layout[, ] = layout[, ]")
                        layout[:, :] = vsource
                    elif dataset == "pixel_spectra":
                        # print(f" layout: [{temp_idx}:{num_frames[index]}:{num_sources}, :, :, :]")
                        layout[temp_idx:num_frames[index]:num_sources, :, :, :] = vsource
                    else:
                        # print(f" layout: [{temp_idx}:{num_frames[index]}:{num_sources}, :, :]")
                        layout[temp_idx:num_frames[index]:num_sources, :, :] = vsource
                    dataset_index[current_index] += 1
            try:
                with h5py.File(dest_file, 'a', libver='latest') as outfile:
                    outfile.create_virtual_dataset(dataset_names[index], layout)
            except ValueError as e:
                logging.error(f"Couldn't map virtual dataset into {dest_file}: {e}")
                return -3
        logging.debug(f"VDS finished mapping virtual datasets into file {dest_file}")
        return 0

    def check_run_data_completed(self, file):
        """Checks whether all data files of current run archived."""
        # All data files are of the format <prefix>_00000N.h5
        # The user can only change <prefix>
        # The Meta data is of the format <prefix>.h5
        bRunCompleted = False
        if "_00000" not in file:
            bRunCompleted = True
        return bRunCompleted

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
        logging.debug("SHUTTING DOWN, cleanup called")
        self.stop_background_tasks()
