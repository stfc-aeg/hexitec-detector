"""
Test Cases for the archiver in hexitec.archiver.

Christian Angelsen, STFC Detector Systems Software Group
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

from hexitec.archiver import ArchiverAdapter, Archiver, ArchiverError
from odin.adapters.parameter_tree import ParameterTreeError
import numpy as np


class TestArchiverAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = ArchiverAdapter(local_dir='/tmp')
        self.put_data = 1024
        self.request = Mock()
        self.request.configure_mock(
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            body=self.put_data
        )

    def tearDown(self):
        """Tear down test fixture after each unit test."""
        self.adapter.archiver.stop_background_tasks()
        del self.adapter

    def test_get_success(self):
        self.adapter.archiver.get = MagicMock(return_value={'status': 'ok'})
        response = self.adapter.get('/some/path', self.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'ok'})

    def test_get_failure(self):
        self.adapter.archiver.get = MagicMock(side_effect=ParameterTreeError('Error'))
        response = self.adapter.get('/some/path', self.request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'Error'})

    @patch('hexitec.archiver.json_decode')
    def test_put_success(self, mock_json_decode):
        mock_json_decode.return_value = {'key': 'value'}
        self.adapter.archiver.set = MagicMock()
        self.adapter.archiver.get = MagicMock(return_value={'status': 'ok'})
        request = MagicMock()
        request.body = '{"key": "value"}'
        response = self.adapter.put('/some/path', request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'ok'})

    @patch('hexitec.archiver.json_decode')
    def test_put_failure_archiver_error(self, mock_json_decode):
        mock_json_decode.return_value = {'key': 'value'}
        self.adapter.archiver.set = MagicMock(side_effect=ArchiverError('Error'))
        request = MagicMock()
        request.body = '{"key": "value"}'
        response = self.adapter.put('/some/path', request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'Error'})

    @patch('hexitec.archiver.json_decode')
    def test_put_failure_decode_error(self, mock_json_decode):
        mock_json_decode.side_effect = ValueError('Decode Error')
        request = MagicMock()
        request.body = '{"key": "value"}'
        response = self.adapter.put('/some/path', request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': 'Failed to decode PUT request body: Decode Error'})

    def test_delete(self):
        response = self.adapter.delete('/some/path', None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'ArchiverAdapter: DELETE on path /some/path')

    def test_cleanup(self):
        self.adapter.archiver.cleanup = MagicMock()
        self.adapter.cleanup()
        self.adapter.archiver.cleanup.assert_called_once()


class TestArchiver(unittest.TestCase):

    def setUp(self):
        options = {'local_dir': '/tmp'}
        self.archiver = Archiver(options)

    def tearDown(self):
        self.archiver.stop_background_tasks()
        del self.archiver

    def test_set_local_dir(self):
        self.archiver.set_local_dir('/new_dir')
        self.assertEqual(self.archiver.local_dir, '/new_dir')

    def test_set_files_to_archive(self):
        self.archiver.queue = MagicMock()
        self.archiver.set_files_to_archive('server:/path/to/file.h5')
        self.archiver.queue.put.assert_called_once_with('server:/path/to/file.h5')

    def test_set_files_to_archive_invalid(self):
        with self.assertRaises(ValueError):
            self.archiver.set_files_to_archive('invalid_path')

    def test_is_server_accessible(self):
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.return_value.poll.return_value = 0
            self.assertEqual(self.archiver.is_server_accessible('server'), 0)

    def test_execute_rsync_command(self):
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.side_effect = [None, None, 0]
            mock_proc.stdout.readline.side_effect = [b'output_line', b'']
            mock_proc.stderr.readline.side_effect = [b'error_line', b'']
            mock_proc.returncode = 0
            mock_popen.return_value = mock_proc

            bOK, errors, rc = self.archiver.execute_rsync_command(['rsync', 'cmd'])
            self.assertFalse(bOK)
            self.assertEqual(errors, ['error_line'])
            self.assertEqual(rc, 0)

    def test_execute_rsync_command_with_errors(self):
        """Test execute_rsync_command captures stderr errors."""
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.side_effect = [None, 0]
            mock_proc.stdout.readline.return_value = b''
            mock_proc.stderr.readline.side_effect = [b'error message', b'']
            mock_proc.returncode = 1
            mock_popen.return_value = mock_proc

            bOK, errors, rc = self.archiver.execute_rsync_command(['rsync', 'cmd'])
            self.assertFalse(bOK)
            self.assertEqual(errors, ['error message'])
            self.assertEqual(rc, 1)

    def test_execute_rsync_command_exception_handling(self):
        """Test execute_rsync_command handles exceptions gracefully."""
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.side_effect = Exception("Process error")
            mock_proc.returncode = None
            mock_popen.return_value = mock_proc

            with patch('hexitec.archiver.logging.error') as mock_logging:
                bOK, errors, rc = self.archiver.execute_rsync_command(['rsync', 'cmd'])
                mock_logging.assert_called_once()

    def test_parse_rsync_output_sets_filename_transferring(self):
        self.archiver.parse_rsync_output(b'08-11-002_000000.h5')
        self.assertEqual(self.archiver.filename_transferring, '08-11-002_000000.h5')

    def test_parse_rsync_output_with_completion_status(self):
        """Test parse_rsync_output sets status when transfer completes."""
        self.archiver.parse_rsync_output(b'246,080,238 100%  112.76MB/s    0:00:02 (xfr#1, to-chk=0/1)')
        self.assertEqual(self.archiver.status, "File transferred")
        self.assertEqual(self.archiver.transfer_progress, 100)
        self.assertEqual(self.archiver.filename_transferring, "")

    def test_parse_rsync_output_hundred_percent_progress(self):
        """Test parse_rsync_output extracts 100 percent correctly."""
        self.archiver.parse_rsync_output(b'246,080,238 100%  112.76MB/s    0:00:02')
        self.assertEqual(self.archiver.transfer_progress, '100')

    def test_flag_error(self):
        self.archiver.flag_error('Test error')
        self.assertIn('Test error', self.archiver.errors_history[-1][-1])

    def test_flag_ok(self):
        # Example log messages:
        # ["2025-02-12T11:10:39.140740+00:00", "initialised OK",
        # ["2025-02-12T11:31:25.208396+00:00", "Copied pc:/path/to/12-02-000_000000.h5 to /tmp"],
        # ["2025-02-12T11:31:28.366037+00:00", "Copied pc:/path/to/12-02-000_000001.h5 to /tmp"],
        # ["2025-02-12T11:31:29.093050+00:00", "Copied pc:/path/to/12-02-000.h5 to /tmp"]]
        self.archiver.limit_number_log_messages = Mock()
        self.archiver.flag_ok('Test ok')
        self.assertIn('Test ok', self.archiver.log_messages[-1][-1])
        self.archiver.limit_number_log_messages.assert_called_once()

    def test_limit_number_log_messages_leaves_40_messages(self):
        self.archiver.log_messages = [
            ['2025-02-12T11:10:39.140740+00:00', 'initialised OK'],
            ['1', 'tmp'], ['2', 'tmp'], ['3', 'tmp'], ['4', 'tmp'],
            ['5', 'tmp'], ['6', 'tmp'], ['7', 'tmp'], ['8', 'tmp'],
            ['9', 'tmp'], ['10', 'tmp'], ['11', 'tmp'], ['12', 'tmp'],
            ['13', 'tmp'], ['14', 'tmp'], ['15', 'tmp'],
            ['16', 'tmp'], ['17', 'tmp'], ['18', 'tmp'], ['19', 'tmp'],
            ['20', 'tmp'], ['21', 'tmp'], ['22', 'tmp'], ['23', 'tmp'],
            ['24', 'tmp'], ['25', 'tmp'], ['26', 'tmp'], ['27', 'tmp'],
            ['28', 'tmp'], ['29', 'tmp'], ['30', 'tmp'],
            ['31', 'tmp'], ['32', 'tmp'], ['33', 'tmp'], ['34', 'tmp'],
            ['35', 'tmp'], ['36', 'tmp'], ['37', 'tmp'], ['38', 'tmp'],
            ['39', 'tmp'], ['40', 'tmp'], ['41', 'tmp'], ['42', 'tmp']]
        self.archiver.limit_number_log_messages()
        # Check that the log messages are limited to 40
        assert 40 == len(self.archiver.log_messages)

    def test_get_server_uptime(self):
        uptime = self.archiver.get_server_uptime()
        self.assertGreaterEqual(uptime, 0)

    def test_get(self):
        self.archiver.param_tree.get = MagicMock(return_value={'status': 'ok'})
        response = self.archiver.get('/some/path')
        self.assertEqual(response, {'status': 'ok'})

    def test_set(self):
        self.archiver.param_tree.set = MagicMock()
        self.archiver.set('/some/path', {'key': 'value'})
        self.archiver.param_tree.set.assert_called_once_with('/some/path', {'key': 'value'})

    def test_set_raises_archiver_error(self):
        self.archiver.param_tree.set = MagicMock(side_effect=ParameterTreeError('Error'))
        with self.assertRaises(ArchiverError):
            self.archiver.set('/some/path', {'key': 'value'})

    def test_cleanup(self):
        self.archiver.proc = MagicMock()
        self.archiver.cleanup()
        assert self.archiver.background_task_enable is False
        self.archiver.proc.kill.assert_called_once()

    @patch('hexitec.archiver.Archiver.execute_rsync_command')
    @patch('hexitec.archiver.Archiver.is_server_accessible')
    def test_archive_files_success(self, mock_is_server_accessible, mock_execute_rsync_command):
        mock_is_server_accessible.return_value = 0
        mock_execute_rsync_command.return_value = (True, [], 0)
        self.archiver.bandwidth_limit = 1000
        self.archiver.queue.put('server:/path/to/file.h5')
        self.archiver.archive_files()
        self.assertEqual(self.archiver.number_files_archived, 1)
        self.assertEqual(self.archiver.number_files_failed, 0)
        self.assertFalse(self.archiver.archiving_in_progress)
        self.assertEqual(self.archiver.status, "Idle")

    @patch('hexitec.archiver.Archiver.is_server_accessible')
    def test_archive_files_server_malformatted_h5_file(self, mock_is_server_accessible):
        mock_is_server_accessible.return_value = 1
        self.archiver.queue.put('server_file_messed_up.h5')
        self.archiver.archive_files()
        self.assertEqual(self.archiver.number_files_archived, 0)
        self.assertEqual(self.archiver.number_files_failed, 0)
        self.assertFalse(self.archiver.archiving_in_progress)
        self.assertEqual(self.archiver.status, "Idle")

    @patch('hexitec.archiver.Archiver.execute_rsync_command')
    @patch('hexitec.archiver.Archiver.is_server_accessible')
    def test_archive_files_rsync_failure(self, mock_is_server_accessible,
                                         mock_execute_rsync_command):
        mock_is_server_accessible.return_value = 1
        mock_execute_rsync_command.return_value = (False, ['error'], 0)
        self.archiver.queue = MagicMock()
        self.archiver.queue.get.return_value = 'server:/path/to/file.h5'
        self.archiver.queue.qsize.side_effect = [1, 0]
        self.archiver.queue.empty.side_effect = [False, True]
        self.archiver.archive_files()
        self.assertEqual(self.archiver.number_files_archived, 0)
        self.assertEqual(self.archiver.number_files_failed, 1)
        self.assertFalse(self.archiver.archiving_in_progress)
        self.assertEqual(self.archiver.status, "Idle")

    @patch('hexitec.archiver.Archiver.execute_rsync_command')
    @patch('hexitec.archiver.Archiver.is_server_accessible')
    def test_archive_files_fails_copy_file(self, mock_is_server_accessible,
                                           mock_execute_rsync_command):
        mock_is_server_accessible.return_value = 0
        mock_execute_rsync_command.return_value = (False, [], 0)
        self.archiver.queue = MagicMock()
        self.archiver.queue.get.return_value = 'server:/path/to/file.h5'
        self.archiver.queue.qsize.side_effect = [1, 0]
        self.archiver.queue.empty.side_effect = [False, True]
        self.archiver.archive_files()
        self.assertEqual(self.archiver.number_files_failed, 1)
        self.assertFalse(self.archiver.archiving_in_progress)
        self.assertEqual(self.archiver.status, "Idle")

    @patch('hexitec.archiver.Archiver.execute_rsync_command')
    @patch('hexitec.archiver.Archiver.is_server_accessible')
    def test_archive_files_rsync_interrupted_negative_rc(self, mock_is_server_accessible,
                                                         mock_execute_rsync_command):
        mock_is_server_accessible.return_value = 0
        mock_execute_rsync_command.return_value = (False, ['error'], -9)
        self.archiver.queue = MagicMock()
        full_path = 'server:/path/to/file.h5'
        self.archiver.queue.get.return_value = full_path
        self.archiver.queue.qsize.side_effect = [1, 0]
        self.archiver.queue.empty.side_effect = [False, True]
        self.archiver.archive_files()
        # interrupted transfer should put the item back on the queue and stop background tasks
        self.archiver.queue.put.assert_called_once_with(full_path)
        self.assertFalse(self.archiver.background_task_enable)
        self.assertFalse(self.archiver.archiving_in_progress)

    def test_get_log_messages_with_last_message_timestamp(self):
        # Prepare errors_history with timestamps
        self.archiver.errors_history = [
            ['2025-02-12T11:10:39.140740+00:00', 'error1'],
            ['2025-02-12T11:11:39.140740+00:00', 'error2'],
            ['2025-02-12T11:12:39.140740+00:00', 'error3'],
        ]
        self.archiver.last_message_timestamp = "2025-02-12T11:11:00.000000+00:00"
        self.archiver.limit_number_log_messages = MagicMock()
        self.archiver.get_log_messages("2025-02-12T11:11:00.000000+00:00")
        # Should only include errors after the given timestamp
        assert self.archiver.log_messages == [
            ('2025-02-12T11:11:39.140740+00:00', 'error2'),
            ('2025-02-12T11:12:39.140740+00:00', 'error3'),
        ]
        self.archiver.limit_number_log_messages.assert_called_once()

    def test_get_log_messages_without_last_message_timestamp(self):
        self.archiver.errors_history = [
            ['2025-02-12T11:10:39.140740+00:00', 'error1'],
            ['2025-02-12T11:11:39.140740+00:00', 'error2'],
        ]
        self.archiver.last_message_timestamp = ""
        self.archiver.create_timestamp = MagicMock(return_value="2025-02-12T12:00:00.000000+00:00")
        self.archiver.limit_number_log_messages = MagicMock()
        self.archiver.get_log_messages("")
        # Should include all errors
        assert self.archiver.log_messages == [
            ('2025-02-12T11:10:39.140740+00:00', 'error1'),
            ('2025-02-12T11:11:39.140740+00:00', 'error2'),
        ]
        assert self.archiver.last_message_timestamp == "2025-02-12T12:00:00.000000+00:00"
        self.archiver.limit_number_log_messages.assert_called_once()

    @patch('hexitec.archiver.time.sleep')
    def test_background_worker_exits_when_disabled(self, mock_sleep):
        """Test that background_worker exits when background_task_enable is set to False."""
        self.archiver.background_task_enable = False
        self.archiver.background_worker()
        self.assertEqual(self.archiver.status, "Halted")
        mock_sleep.assert_not_called()

    @patch('hexitec.archiver.Archiver.archive_files')
    @patch('hexitec.archiver.time.sleep')
    def test_background_worker_sleeps_when_queue_empty(self, mock_sleep, mock_archive_files):
        """Test that background_worker sleeps when queue is empty."""
        self.archiver.queue = MagicMock()
        self.archiver.queue.qsize.return_value = 0
        call_count = [0]

        def side_effect_enable(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 2:
                self.archiver.background_task_enable = False

        mock_sleep.side_effect = side_effect_enable
        self.archiver.background_worker()

        mock_sleep.assert_called_with(0.1)
        mock_archive_files.assert_not_called()
        self.assertEqual(self.archiver.status, "Halted")

    @patch('hexitec.archiver.Archiver.archive_files')
    def test_background_worker_calls_archive_files_when_queue_not_empty(self, mock_archive_files):
        """Test that background_worker calls archive_files when queue is not empty."""
        self.archiver.queue = MagicMock()
        self.archiver.queue.qsize.return_value = 1
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 1:
                self.archiver.background_task_enable = False

        mock_archive_files.side_effect = side_effect
        self.archiver.background_worker()

        mock_archive_files.assert_called_once()
        self.assertEqual(self.archiver.status, "Halted")

    @patch('hexitec.archiver.Archiver.archive_files')
    @patch('hexitec.archiver.time.sleep')
    def test_background_worker_loops_correctly(self, mock_sleep, mock_archive_files):
        """Test that background_worker loops between sleeping and archiving."""
        self.archiver.queue = MagicMock()
        self.archiver.queue.qsize.side_effect = [0, 1, 0]
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 3:
                self.archiver.background_task_enable = False

        mock_sleep.side_effect = side_effect
        mock_archive_files.side_effect = side_effect
        self.archiver.background_worker()

        self.assertEqual(mock_sleep.call_count, 2)
        mock_archive_files.assert_called_once()
        self.assertEqual(self.archiver.status, "Halted")

    @patch('hexitec.archiver.glob.glob')
    @patch('hexitec.archiver.Archiver.extract_meta_data')
    @patch('hexitec.archiver.Archiver.aggregate_data_across_files')
    @patch('hexitec.archiver.Archiver.build_virtual_layout')
    @patch('hexitec.archiver.Archiver.map_sources_to_layout')
    @patch('hexitec.archiver.Archiver.write_datasets_to_file')
    def test_map_virtual_datasets_success(self, mock_write, mock_map_sources, mock_build_layout,
                                          mock_aggregate, mock_extract_meta, mock_glob):
        """Test map_virtual_datasets successfully processes files."""

        mock_glob.return_value = ['/tmp/test_000.h5', '/tmp/test_001.h5']

        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32

        si_dset = MagicMock()
        si_dset.shape = (10, 8, 80)
        si_dset.dtype = np.uint32

        ss_dset = MagicMock()
        ss_dset.shape = (10, 2048)
        ss_dset.dtype = np.uint32

        mock_extract_meta.return_value = (['pixel_spectra', 'summed_images', 'summed_spectra'],
                                          ps_dset, si_dset, ss_dset, 3)

        mock_aggregate.return_value = ([], np.zeros((80, 8, 2)), np.zeros((80, 80)),
                                       np.zeros(2048), [10, 10, 10], [np.uint32, np.uint32, np.uint32],
                                       [(10, 8, 8, 2), (10, 8, 80), (10, 2048)])

        mock_build_layout.return_value = MagicMock()

        result = self.archiver.map_virtual_datasets('test.h5')
        self.assertEqual(result, 0)
        self.assertEqual(mock_build_layout.call_count, 3)
        self.assertEqual(mock_map_sources.call_count, 3)
        self.assertEqual(mock_write.call_count, 3)

    @patch('hexitec.archiver.glob.glob')
    def test_map_virtual_datasets_no_source_files(self, mock_glob):
        """Test map_virtual_datasets returns -1 when no source files found."""
        mock_glob.return_value = []

        result = self.archiver.map_virtual_datasets('test.h5')
        self.assertEqual(result, -1)

    @patch('hexitec.archiver.glob.glob')
    @patch('hexitec.archiver.Archiver.extract_meta_data')
    def test_map_virtual_datasets_missing_pixel_spectra(self, mock_extract_meta, mock_glob):
        """Test map_virtual_datasets returns -1 when pixel_spectra dataset missing."""
        mock_glob.return_value = ['/tmp/test_000.h5']
        mock_extract_meta.return_value = (['summed_images'], None, MagicMock(), MagicMock(), 1)

        result = self.archiver.map_virtual_datasets('test.h5')
        self.assertEqual(result, -1)

    @patch('hexitec.archiver.glob.glob')
    @patch('hexitec.archiver.Archiver.extract_meta_data')
    def test_map_virtual_datasets_missing_summed_images(self, mock_extract_meta, mock_glob):
        """Test map_virtual_datasets returns -1 when summed_images dataset missing."""
        mock_glob.return_value = ['/tmp/test_000.h5']
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32
        mock_extract_meta.return_value = (['pixel_spectra'], ps_dset, None, MagicMock(), 1)

        result = self.archiver.map_virtual_datasets('test.h5')
        self.assertEqual(result, -1)

    @patch('hexitec.archiver.glob.glob')
    @patch('hexitec.archiver.Archiver.extract_meta_data')
    def test_map_virtual_datasets_missing_summed_spectra(self, mock_extract_meta, mock_glob):
        """Test map_virtual_datasets returns -1 when summed_spectra dataset missing."""
        mock_glob.return_value = ['/tmp/test_000.h5']
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32
        si_dset = MagicMock()
        si_dset.shape = (10, 8, 80)
        si_dset.dtype = np.uint32
        mock_extract_meta.return_value = (['pixel_spectra', 'summed_images'], ps_dset, si_dset, None, 2)

        result = self.archiver.map_virtual_datasets('test.h5')
        self.assertEqual(result, -1)

    @patch('hexitec.archiver.glob.glob')
    @patch('hexitec.archiver.Archiver.extract_meta_data')
    @patch('hexitec.archiver.Archiver.aggregate_data_across_files')
    @patch('hexitec.archiver.Archiver.build_virtual_layout')
    def test_map_virtual_datasets_build_layout_index_error(self, mock_build_layout, mock_aggregate,
                                                           mock_extract_meta, mock_glob):
        """Test map_virtual_datasets returns -2 when build_virtual_layout raises IndexError."""

        mock_glob.return_value = ['/tmp/test_000.h5']
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32
        si_dset = MagicMock()
        si_dset.shape = (10, 8, 80)
        si_dset.dtype = np.uint32
        ss_dset = MagicMock()
        ss_dset.shape = (10, 2048)
        ss_dset.dtype = np.uint32

        mock_aggregate.return_value = ([], np.zeros((80, 8, 2)), np.zeros((80, 80)),
                                       np.zeros(2048), [10], [np.uint32], [(10, 8, 8, 2)])

        mock_extract_meta.return_value = (['pixel_spectra'], ps_dset, si_dset, ss_dset, 1)
        mock_build_layout.side_effect = IndexError("Shape mismatch")

        result = self.archiver.map_virtual_datasets('test.h5')
        self.assertEqual(result, -2)

    @patch('hexitec.archiver.glob.glob')
    @patch('hexitec.archiver.Archiver.extract_meta_data')
    @patch('hexitec.archiver.Archiver.aggregate_data_across_files')
    @patch('hexitec.archiver.Archiver.build_virtual_layout')
    @patch('hexitec.archiver.Archiver.map_sources_to_layout')
    def test_map_virtual_datasets_map_sources_value_error(self, mock_map_sources, mock_build_layout,
                                                          mock_aggregate, mock_extract_meta, mock_glob):
        """Test map_virtual_datasets returns -3 when map_sources_to_layout raises ValueError."""

        mock_glob.return_value = ['/tmp/test_000.h5']
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32
        si_dset = MagicMock()
        si_dset.shape = (10, 8, 80)
        si_dset.dtype = np.uint32
        ss_dset = MagicMock()
        ss_dset.shape = (10, 2048)
        ss_dset.dtype = np.uint32

        mock_extract_meta.return_value = (['pixel_spectra'], ps_dset, si_dset, ss_dset, 1)
        mock_aggregate.return_value = ([], np.zeros((80, 8, 2)), np.zeros((80, 80)),
                                       np.zeros(2048), [10], [np.uint32], [(10, 8, 8, 2)])
        mock_build_layout.return_value = MagicMock()
        mock_map_sources.side_effect = ValueError("Invalid layout")

        result = self.archiver.map_virtual_datasets('test.h5')
        self.assertEqual(result, -3)

    @patch('hexitec.archiver.glob.glob')
    @patch('hexitec.archiver.Archiver.extract_meta_data')
    @patch('hexitec.archiver.Archiver.aggregate_data_across_files')
    @patch('hexitec.archiver.Archiver.build_virtual_layout')
    @patch('hexitec.archiver.Archiver.map_sources_to_layout')
    @patch('hexitec.archiver.Archiver.write_datasets_to_file')
    def test_map_virtual_datasets_write_datasets_blocking_error(self, mock_write, mock_map_sources,
                                                                mock_build_layout, mock_aggregate,
                                                                mock_extract_meta, mock_glob):
        """Test map_virtual_datasets returns -4 when write_datasets_to_file raises BlockingIOError."""

        mock_glob.return_value = ['/tmp/test_000.h5']
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32
        si_dset = MagicMock()
        si_dset.shape = (10, 8, 80)
        si_dset.dtype = np.uint32
        ss_dset = MagicMock()
        ss_dset.shape = (10, 2048)
        ss_dset.dtype = np.uint32

        mock_extract_meta.return_value = (['pixel_spectra'], ps_dset, si_dset, ss_dset, 1)
        mock_aggregate.return_value = ([], np.zeros((80, 8, 2)), np.zeros((80, 80)),
                                       np.zeros(2048), [10], [np.uint32], [(10, 8, 8, 2)])
        mock_build_layout.return_value = MagicMock()
        mock_write.side_effect = BlockingIOError("File locked")

        result = self.archiver.map_virtual_datasets('test.h5')
        self.assertEqual(result, -4)

    @patch('hexitec.archiver.h5py.File')
    def test_extract_meta_data_success(self, mock_h5py_file):
        """Test extract_meta_data successfully extracts metadata from HDF5 file."""
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32

        si_dset = MagicMock()
        si_dset.shape = (10, 8, 80)
        si_dset.dtype = np.uint32

        ss_dset = MagicMock()
        ss_dset.shape = (10, 2048)
        ss_dset.dtype = np.uint32

        mock_file = MagicMock()
        mock_file.keys.return_value = ['pixel_spectra', 'summed_images', 'summed_spectra']
        mock_file.__iter__.return_value = iter(['pixel_spectra', 'summed_images', 'summed_spectra'])
        mock_file.__getitem__.side_effect = lambda x: {'pixel_spectra': ps_dset,
                                                       'summed_images': si_dset,
                                                       'summed_spectra': ss_dset}[x]
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        dataset_names, ps, si, ss, num_datasets = self.archiver.extract_meta_data('/tmp/test.h5')

        self.assertEqual(dataset_names, ['pixel_spectra', 'summed_images', 'summed_spectra'])
        self.assertEqual(ps, ps_dset)
        self.assertEqual(si, si_dset)
        self.assertEqual(ss, ss_dset)
        self.assertEqual(num_datasets, 3)

    @patch('hexitec.archiver.h5py.File')
    def test_extract_meta_data_partial_datasets(self, mock_h5py_file):
        """Test extract_meta_data when only some expected datasets are present."""
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32

        mock_file = MagicMock()
        mock_file.keys.return_value = ['pixel_spectra', 'other_dataset']
        mock_file.__iter__.return_value = iter(['pixel_spectra', 'other_dataset'])
        mock_file.__getitem__.side_effect = lambda x: {'pixel_spectra': ps_dset,
                                                       'other_dataset': MagicMock()}[x]
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        dataset_names, ps, si, ss, num_datasets = self.archiver.extract_meta_data('/tmp/test.h5')

        self.assertEqual(dataset_names, ['pixel_spectra', 'other_dataset'])
        self.assertEqual(ps, ps_dset)
        self.assertIsNone(si)
        self.assertIsNone(ss)
        self.assertEqual(num_datasets, 2)

    @patch('hexitec.archiver.h5py.File')
    def test_extract_meta_data_file_not_found(self, mock_h5py_file):
        """Test extract_meta_data returns -1 when file cannot be opened."""
        mock_h5py_file.return_value.__enter__.side_effect = OSError("File not found")

        with patch('hexitec.archiver.logging.error') as mock_logging:
            result = self.archiver.extract_meta_data('/tmp/nonexistent.h5')
            self.assertEqual(result, -1)
            mock_logging.assert_called_once()

    @patch('hexitec.archiver.h5py.File')
    def test_extract_meta_data_empty_file(self, mock_h5py_file):
        """Test extract_meta_data with empty HDF5 file."""
        mock_file = MagicMock()
        mock_file.keys.return_value = []
        mock_file.__iter__.return_value = iter([])
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        dataset_names, ps, si, ss, num_datasets = self.archiver.extract_meta_data('/tmp/empty.h5')

        self.assertEqual(dataset_names, [])
        self.assertIsNone(ps)
        self.assertIsNone(si)
        self.assertIsNone(ss)
        self.assertEqual(num_datasets, 0)

    @patch('hexitec.archiver.h5py.File')
    def test_extract_meta_data_accesses_shape_and_dtype(self, mock_h5py_file):
        """Test extract_meta_data accesses shape and dtype to prevent later issues."""
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32

        mock_file = MagicMock()
        mock_file.keys.return_value = ['pixel_spectra']
        mock_file.__iter__.return_value = iter(['pixel_spectra'])
        mock_file.__getitem__.return_value = ps_dset
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        self.archiver.extract_meta_data('/tmp/test.h5')

        # Verify that shape and dtype were accessed
        self.assertTrue(ps_dset.shape)
        self.assertTrue(ps_dset.dtype)

    @patch('hexitec.archiver.h5py.VirtualLayout')
    def test_build_virtual_layout_spectra_bins_2d(self, mock_virtual_layout):
        """Test build_virtual_layout for spectra_bins dataset with 2D input shape."""
        inshape = [(10, 2048)]
        num_frames = [10]
        dtype = [np.uint32]

        self.archiver.build_virtual_layout('spectra_bins', inshape, 0, num_frames, dtype)

        mock_virtual_layout.assert_called_once_with(shape=(inshape[0][0], inshape[0][1]), dtype=np.uint32)

    @patch('hexitec.archiver.h5py.VirtualLayout')
    def test_build_virtual_layout_spectra_bins_3d(self, mock_virtual_layout):
        """Test build_virtual_layout for spectra_bins dataset with 3D input shape."""
        inshape = [(10, 8, 2)]
        num_frames = [10]
        dtype = [np.uint32]

        self.archiver.build_virtual_layout('spectra_bins', inshape, 0, num_frames, dtype)

        mock_virtual_layout.assert_called_once_with(shape=(inshape[0][1], inshape[0][2]), dtype=np.uint32)

    @patch('hexitec.archiver.h5py.VirtualLayout')
    def test_build_virtual_layout_pixel_spectra(self, mock_virtual_layout):
        """Test build_virtual_layout for pixel_spectra dataset."""
        inshape = [(10, 8, 8, 2)]
        num_frames = [20]
        dtype = [np.uint32]

        self.archiver.build_virtual_layout('pixel_spectra', inshape, 0, num_frames, dtype)

        mock_virtual_layout.assert_called_once_with(
            shape=(20, 8, 8, 2),
            dtype=np.uint32
        )

    @patch('hexitec.archiver.h5py.VirtualLayout')
    def test_build_virtual_layout_summed_images_2d(self, mock_virtual_layout):
        """Test build_virtual_layout for summed_images dataset with 2D input shape."""
        inshape = [(10, 8, 80)]
        num_frames = [15]
        dtype = [np.uint32]

        self.archiver.build_virtual_layout('summed_images', inshape, 0, num_frames, dtype)

        mock_virtual_layout.assert_called_once_with(shape=(15, 8, 80), dtype=np.uint32)

    @patch('hexitec.archiver.h5py.VirtualLayout')
    def test_build_virtual_layout_summed_images_3d(self, mock_virtual_layout):
        """Test build_virtual_layout for summed_images with 3D input shape."""
        inshape = [(10, 8, 80)]
        num_frames = [15]
        dtype = [np.uint32]

        self.archiver.build_virtual_layout('summed_images', inshape, 0, num_frames, dtype)

        mock_virtual_layout.assert_called_once_with(shape=(15, 8, 80), dtype=np.uint32)

    @patch('hexitec.archiver.h5py.VirtualLayout')
    def test_build_virtual_layout_summed_spectra_2d(self, mock_virtual_layout):
        """Test build_virtual_layout for summed_spectra dataset with 2D input shape."""
        inshape = [(10, 2048)]
        num_frames = [10]
        dtype = [np.uint32]

        self.archiver.build_virtual_layout('summed_spectra', inshape, 0, num_frames, dtype)

        mock_virtual_layout.assert_called_once_with(shape=(10, 10, 2048), dtype=np.uint32)

    @patch('hexitec.archiver.h5py.VirtualLayout')
    def test_build_virtual_layout_multiple_datasets(self, mock_virtual_layout):
        """Test build_virtual_layout with multiple datasets at different indices."""
        inshape = [(10, 8, 8, 2), (10, 8, 80), (10, 2048)]
        num_frames = [20, 20, 20]
        dtype = [np.uint32, np.uint32, np.uint32]

        self.archiver.build_virtual_layout('pixel_spectra', inshape, 0, num_frames, dtype)
        self.archiver.build_virtual_layout('summed_images', inshape, 1, num_frames, dtype)
        self.archiver.build_virtual_layout('summed_spectra', inshape, 2, num_frames, dtype)

        self.assertEqual(mock_virtual_layout.call_count, 3)

    @patch('hexitec.archiver.h5py.VirtualLayout')
    def test_build_virtual_layout_different_dtypes(self, mock_virtual_layout):
        """Test build_virtual_layout with different data types."""
        inshape = [(10, 8, 8, 2)]
        num_frames = [20]

        for dtype_val in [np.uint16, np.uint32, np.uint64, np.float32, np.float64]:
            mock_virtual_layout.reset_mock()
            self.archiver.build_virtual_layout('pixel_spectra', inshape, 0, num_frames, [dtype_val])
            mock_virtual_layout.assert_called_once_with(shape=(20, 8, 8, 2), dtype=dtype_val)

    @patch('hexitec.archiver.h5py.VirtualLayout')
    def test_build_virtual_layout_various_frame_counts(self, mock_virtual_layout):
        """Test build_virtual_layout with various frame counts."""
        inshape = [(10, 8, 8, 2)]
        dtype = [np.uint32]

        for num_frames_val in [1, 5, 10, 100, 1000]:
            mock_virtual_layout.reset_mock()
            self.archiver.build_virtual_layout('pixel_spectra', inshape, 0, [num_frames_val], dtype)
            mock_virtual_layout.assert_called_once_with(
                shape=(num_frames_val, 8, 8, 2),
                dtype=np.uint32
            )

    def test_map_sources_to_layout_spectra_bins(self):
        """Test map_sources_to_layout for spectra_bins dataset."""
        layout = np.zeros((8, 2), dtype=np.uint32)
        vsources = [np.ones((8, 2), dtype=np.uint32)]
        dataset_index = [0]

        self.archiver.map_sources_to_layout('spectra_bins', 0, [10], 1, 1, vsources, layout, dataset_index)

        np.testing.assert_array_equal(layout, vsources[0])
        self.assertEqual(dataset_index[0], 1)

    def test_map_sources_to_layout_pixel_spectra_single_source(self):
        """Test map_sources_to_layout for pixel_spectra with single source."""
        layout = np.zeros((20, 8, 8, 2), dtype=np.uint32)
        vsource = np.ones((20, 8, 8, 2), dtype=np.uint32)
        vsources = [vsource]
        dataset_index = [0]

        self.archiver.map_sources_to_layout('pixel_spectra', 0, [20], 1, 1, vsources, layout, dataset_index)

        np.testing.assert_array_equal(layout[0:20:1, :, :, :], vsource)
        self.assertEqual(dataset_index[0], 1)

    def test_map_sources_to_layout_summed_images_single_source(self):
        """Test map_sources_to_layout for summed_images with single source."""
        layout = np.zeros((20, 8, 80), dtype=np.uint32)
        vsource = np.ones((8, 80), dtype=np.uint32)
        vsources = [vsource]
        dataset_index = [0]

        self.archiver.map_sources_to_layout('summed_images', 0, [20], 1, 1, vsources, layout, dataset_index)
        layout = layout[0]
        np.testing.assert_array_equal(layout[0:20:1, :], vsource)
        self.assertEqual(dataset_index[0], 1)

    @patch('hexitec.archiver.h5py.File')
    def test_write_datasets_to_file_new_dataset(self, mock_h5py_file):
        """Test write_datasets_to_file creates new virtual dataset when it doesn't exist."""
        mock_outfile = MagicMock()
        mock_outfile.keys.return_value = []
        mock_h5py_file.return_value.__enter__.return_value = mock_outfile

        layout = MagicMock()
        pixel_spectra_summed = np.zeros((80, 8, 2))
        summed_images_summed = np.zeros((80, 80))
        summed_spectra_summed = np.zeros(2048)

        self.archiver.write_datasets_to_file(
            '/tmp/test.h5', 'other_dataset', ['other_dataset'], 0, layout,
            pixel_spectra_summed, summed_images_summed, summed_spectra_summed
        )

        mock_outfile.create_virtual_dataset.assert_called_once_with('other_dataset', layout)

    @patch('hexitec.archiver.h5py.File')
    def test_write_datasets_to_file_existing_dataset_amended(self, mock_h5py_file):
        """Test write_datasets_to_file amends dataset name when it already exists."""
        mock_outfile = MagicMock()
        mock_outfile.keys.return_value = ['pixel_spectra']
        mock_h5py_file.return_value.__enter__.return_value = mock_outfile

        layout = MagicMock()
        pixel_spectra_summed = np.zeros((80, 8, 2))
        summed_images_summed = np.zeros((80, 80))
        summed_spectra_summed = np.zeros(2048)

        with patch('hexitec.archiver.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.hour = 14
            mock_now.minute = 30
            mock_now.second = 45
            mock_datetime.now.return_value = mock_now

            self.archiver.write_datasets_to_file(
                '/tmp/test.h5', 'other_dataset', ['pixel_spectra'], 0, layout,
                pixel_spectra_summed, summed_images_summed, summed_spectra_summed
            )

            mock_outfile.create_virtual_dataset.assert_called_once()
            call_args = mock_outfile.create_virtual_dataset.call_args
            self.assertIn('14:30:45/', call_args[0][0])

    @patch('hexitec.archiver.h5py.File')
    def test_write_datasets_to_file_pixel_spectra_dataset(self, mock_h5py_file):
        """Test write_datasets_to_file replaces pixel_spectra with real dataset."""
        mock_outfile = MagicMock()
        mock_outfile.keys.return_value = []
        mock_h5py_file.return_value.__enter__.return_value = mock_outfile

        layout = MagicMock()
        pixel_spectra_summed = np.ones((80, 8, 2))
        summed_images_summed = np.zeros((80, 80))
        summed_spectra_summed = np.zeros(2048)

        self.archiver.write_datasets_to_file(
            '/tmp/test.h5', 'pixel_spectra', ['pixel_spectra'], 0, layout,
            pixel_spectra_summed, summed_images_summed, summed_spectra_summed
        )

        mock_outfile.create_virtual_dataset.assert_called_once()
        mock_outfile.__delitem__.assert_called_once_with('pixel_spectra')
        mock_outfile.create_dataset.assert_called_once_with('pixel_spectra', data=pixel_spectra_summed)

    @patch('hexitec.archiver.h5py.File')
    def test_write_datasets_to_file_summed_images_dataset(self, mock_h5py_file):
        """Test write_datasets_to_file replaces summed_images with real dataset."""
        mock_outfile = MagicMock()
        mock_outfile.keys.return_value = []
        mock_h5py_file.return_value.__enter__.return_value = mock_outfile

        layout = MagicMock()
        pixel_spectra_summed = np.zeros((80, 8, 2))
        summed_images_summed = np.ones((80, 80))
        summed_spectra_summed = np.zeros(2048)

        self.archiver.write_datasets_to_file(
            '/tmp/test.h5', 'summed_images', ['summed_images'], 0, layout,
            pixel_spectra_summed, summed_images_summed, summed_spectra_summed
        )

        mock_outfile.create_virtual_dataset.assert_called_once()
        mock_outfile.__delitem__.assert_called_once_with('summed_images')
        mock_outfile.create_dataset.assert_called_once_with('summed_images', data=summed_images_summed)

    @patch('hexitec.archiver.h5py.File')
    def test_write_datasets_to_file_summed_spectra_dataset(self, mock_h5py_file):
        """Test write_datasets_to_file replaces summed_spectra with real dataset."""
        mock_outfile = MagicMock()
        mock_outfile.keys.return_value = []
        mock_h5py_file.return_value.__enter__.return_value = mock_outfile

        layout = MagicMock()
        pixel_spectra_summed = np.zeros((80, 8, 2))
        summed_images_summed = np.zeros((80, 80))
        summed_spectra_summed = np.ones(2048)

        self.archiver.write_datasets_to_file(
            '/tmp/test.h5', 'summed_spectra', ['summed_spectra'], 0, layout,
            pixel_spectra_summed, summed_images_summed, summed_spectra_summed
        )

        mock_outfile.create_virtual_dataset.assert_called_once()
        mock_outfile.__delitem__.assert_called_once_with('summed_spectra')
        mock_outfile.create_dataset.assert_called_once_with('summed_spectra', data=summed_spectra_summed)

    @patch('hexitec.archiver.h5py.File')
    def test_write_datasets_to_file_uses_correct_index(self, mock_h5py_file):
        """Test write_datasets_to_file uses correct index into dataset_names."""
        mock_outfile = MagicMock()
        mock_outfile.keys.return_value = []
        mock_h5py_file.return_value.__enter__.return_value = mock_outfile

        layout = MagicMock()
        dataset_names = ['dataset1', 'dataset2', 'dataset3']
        pixel_spectra_summed = np.zeros((80, 8, 2))
        summed_images_summed = np.zeros((80, 80))
        summed_spectra_summed = np.zeros(2048)

        self.archiver.write_datasets_to_file(
            '/tmp/test.h5', 'other', dataset_names, 1, layout,
            pixel_spectra_summed, summed_images_summed, summed_spectra_summed
        )

        mock_outfile.create_virtual_dataset.assert_called_once_with('dataset2', layout)

    @patch('hexitec.archiver.h5py.File')
    def test_write_datasets_to_file_file_opened_with_append_mode(self, mock_h5py_file):
        """Test write_datasets_to_file opens file in append mode with latest libver."""
        mock_outfile = MagicMock()
        mock_outfile.keys.return_value = []
        mock_h5py_file.return_value.__enter__.return_value = mock_outfile

        layout = MagicMock()
        pixel_spectra_summed = np.zeros((80, 8, 2))
        summed_images_summed = np.zeros((80, 80))
        summed_spectra_summed = np.zeros(2048)

        self.archiver.write_datasets_to_file(
            '/tmp/test.h5', 'other', ['dataset'], 0, layout,
            pixel_spectra_summed, summed_images_summed, summed_spectra_summed
        )

        mock_h5py_file.assert_called_once_with('/tmp/test.h5', 'a', libver='latest')

    @patch('hexitec.archiver.logging.warning')
    @patch('hexitec.archiver.h5py.File')
    def test_write_datasets_to_file_logs_warning_for_existing_dataset(self, mock_h5py_file, mock_warning):
        """Test write_datasets_to_file logs warning when dataset already exists."""
        mock_outfile = MagicMock()
        mock_outfile.keys.return_value = ['pixel_spectra']
        mock_h5py_file.return_value.__enter__.return_value = mock_outfile

        layout = MagicMock()
        pixel_spectra_summed = np.zeros((80, 8, 2))
        summed_images_summed = np.zeros((80, 80))
        summed_spectra_summed = np.zeros(2048)

        self.archiver.write_datasets_to_file(
            '/tmp/test.h5', 'other', ['pixel_spectra'], 0, layout,
            pixel_spectra_summed, summed_images_summed, summed_spectra_summed
        )

        mock_warning.assert_called_once()
        warning_msg = mock_warning.call_args[0][0]
        self.assertIn("already exist", warning_msg)
        self.assertIn("pixel_spectra", warning_msg)

    @patch('hexitec.archiver.h5py.File')
    def test_write_datasets_to_file_no_delete_for_non_special_datasets(self, mock_h5py_file):
        """Test write_datasets_to_file does not delete datasets for non-special types."""
        mock_outfile = MagicMock()
        mock_outfile.keys.return_value = []
        mock_h5py_file.return_value.__enter__.return_value = mock_outfile

        layout = MagicMock()
        pixel_spectra_summed = np.zeros((80, 8, 2))
        summed_images_summed = np.zeros((80, 80))
        summed_spectra_summed = np.zeros(2048)

        self.archiver.write_datasets_to_file(
            '/tmp/test.h5', 'other_dataset', ['other_dataset'], 0, layout,
            pixel_spectra_summed, summed_images_summed, summed_spectra_summed
        )

        mock_outfile.__delitem__.assert_not_called()
        mock_outfile.create_dataset.assert_not_called()

    @patch('hexitec.archiver.h5py.File')
    def test_aggregate_data_across_files_multiple_files(self, mock_h5py_file):
        """Test aggregate_data_across_files with multiple HDF5 files."""
        ps_dset1 = MagicMock()
        ps_dset1.shape = (10, 8, 8, 2)
        ps_dset1.dtype = np.uint32
        ps_dset1.__getitem__.return_value = np.ones((8, 8, 2))

        si_dset1 = MagicMock()
        si_dset1.shape = (10, 8, 80)
        si_dset1.dtype = np.uint32
        si_dset1.__getitem__.return_value = np.ones((8, 80))

        ss_dset1 = MagicMock()
        ss_dset1.shape = (10, 2048)
        ss_dset1.dtype = np.uint32
        ss_dset1.__getitem__.return_value = np.ones(2048)

        ps_dset2 = MagicMock()
        ps_dset2.shape = (10, 8, 8, 2)
        ps_dset2.dtype = np.uint32
        ps_dset2.__getitem__.return_value = np.ones((8, 8, 2))

        si_dset2 = MagicMock()
        si_dset2.shape = (10, 8, 80)
        si_dset2.dtype = np.uint32
        si_dset2.__getitem__.return_value = np.ones((8, 80))

        ss_dset2 = MagicMock()
        ss_dset2.shape = (10, 2048)
        ss_dset2.dtype = np.uint32
        ss_dset2.__getitem__.return_value = np.ones(2048)

        def mock_file_factory(filename):
            mock = MagicMock()
            mock.keys.return_value = ['pixel_spectra', 'summed_images', 'summed_spectra']
            if 'test_000.h5' in filename:
                mock.__iter__.return_value = iter(['pixel_spectra', 'summed_images', 'summed_spectra'])
                mock.__getitem__.side_effect = lambda x: {
                    'pixel_spectra': ps_dset1,
                    'summed_images': si_dset1,
                    'summed_spectra': ss_dset1
                }[x]
            else:
                mock.__iter__.return_value = iter(['pixel_spectra', 'summed_images', 'summed_spectra'])
                mock.__getitem__.side_effect = lambda x: {
                    'pixel_spectra': ps_dset2,
                    'summed_images': si_dset2,
                    'summed_spectra': ss_dset2
                }[x]
            return mock

        mock_h5py_file.side_effect = lambda f: MagicMock(__enter__=lambda s: mock_file_factory(f), __exit__=lambda s, *args: None)

        pixel_spectra_summed = np.zeros((8, 8, 2))
        summed_images_summed = np.zeros((8, 80))
        summed_spectra_summed = np.zeros(2048)

        vsources, ps_sum, si_sum, ss_sum, num_frames, dtype, inshape = \
            self.archiver.aggregate_data_across_files(
                ['/tmp/test_000.h5', '/tmp/test_001.h5'], 3, pixel_spectra_summed,
                summed_images_summed, summed_spectra_summed
            )

        self.assertEqual(len(vsources), 6)
        self.assertEqual(num_frames, [20, 20, 20])

    @patch('hexitec.archiver.h5py.File')
    def test_aggregate_data_across_files_dataset_count_mismatch(self, mock_h5py_file):
        """Test aggregate_data_across_files returns -2 when dataset count mismatches."""
        mock_file = MagicMock()
        mock_file.keys.return_value = ['pixel_spectra', 'summed_images']
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        pixel_spectra_summed = np.zeros((8, 8, 2))
        summed_images_summed = np.zeros((8, 80))
        summed_spectra_summed = np.zeros(2048)

        with patch('hexitec.archiver.logging.error'):
            result = self.archiver.aggregate_data_across_files(
                ['/tmp/test_000.h5'], 3, pixel_spectra_summed,
                summed_images_summed, summed_spectra_summed
            )

        self.assertEqual(result, -2)

    @patch('hexitec.archiver.h5py.File')
    def test_aggregate_data_across_files_spectra_bins_dataset(self, mock_h5py_file):
        """Test aggregate_data_across_files correctly handles spectra_bins dataset."""
        sb_dset = MagicMock()
        sb_dset.shape = (2048,)
        sb_dset.dtype = np.uint32

        mock_file = MagicMock()
        mock_file.keys.return_value = ['spectra_bins']
        mock_file.__iter__.return_value = iter(['spectra_bins'])
        mock_file.__getitem__.return_value = sb_dset
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        pixel_spectra_summed = np.zeros((8, 8, 2))
        summed_images_summed = np.zeros((8, 80))
        summed_spectra_summed = np.zeros(2048)

        vsources, ps_sum, si_sum, ss_sum, num_frames, dtype, inshape = \
            self.archiver.aggregate_data_across_files(
                ['/tmp/test_000.h5'], 1, pixel_spectra_summed,
                summed_images_summed, summed_spectra_summed
            )

        self.assertEqual(num_frames[0], 1)

    @patch('hexitec.archiver.h5py.File')
    def test_aggregate_data_across_files_accumulates_data(self, mock_h5py_file):
        """Test aggregate_data_across_files correctly accumulates pixel_spectra data."""
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32
        ps_dset.__getitem__.return_value = np.ones((8, 8, 2))

        mock_file = MagicMock()
        mock_file.keys.return_value = ['pixel_spectra']
        mock_file.__iter__.return_value = iter(['pixel_spectra'])
        mock_file.__getitem__.return_value = ps_dset
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        initial_ps_summed = np.ones((8, 8, 2))
        summed_images_summed = np.zeros((8, 80))
        summed_spectra_summed = np.zeros(2048)

        vsources, ps_sum, si_sum, ss_sum, num_frames, dtype, inshape = \
            self.archiver.aggregate_data_across_files(
                ['/tmp/test_000.h5'], 1, initial_ps_summed,
                summed_images_summed, summed_spectra_summed
            )

        np.testing.assert_array_equal(ps_sum, np.ones((8, 8, 2)) * 2)

    @patch('hexitec.archiver.h5py.File')
    def test_aggregate_data_across_files_dtype_validation(self, mock_h5py_file):
        """Test aggregate_data_across_files validates dtype consistency across files."""
        ps_dset1 = MagicMock()
        ps_dset1.shape = (10, 8, 8, 2)
        ps_dset1.dtype = np.uint32
        ps_dset1.__getitem__.return_value = np.ones((8, 8, 2))

        ps_dset2 = MagicMock()
        ps_dset2.shape = (10, 8, 8, 2)
        ps_dset2.dtype = np.uint32
        ps_dset2.__getitem__.return_value = np.ones((8, 8, 2))

        def mock_file_factory(filename):
            mock = MagicMock()
            mock.keys.return_value = ['pixel_spectra']
            mock.__iter__.return_value = iter(['pixel_spectra'])
            mock.__getitem__.return_value = ps_dset1 if 'test_000.h5' in filename else ps_dset2
            return mock

        mock_h5py_file.side_effect = lambda f: MagicMock(__enter__=lambda s: mock_file_factory(f), __exit__=lambda s, *args: None)

        pixel_spectra_summed = np.zeros((8, 8, 2))
        summed_images_summed = np.zeros((8, 80))
        summed_spectra_summed = np.zeros(2048)

        vsources, ps_sum, si_sum, ss_sum, num_frames, dtype, inshape = \
            self.archiver.aggregate_data_across_files(
                ['/tmp/test_000.h5', '/tmp/test_001.h5'], 1, pixel_spectra_summed,
                summed_images_summed, summed_spectra_summed
            )

        self.assertEqual(dtype[0], np.uint32)

    @patch('hexitec.archiver.h5py.VirtualSource')
    @patch('hexitec.archiver.h5py.File')
    def test_aggregate_data_across_files_creates_virtual_sources(self, mock_h5py_file, mock_virtual_source):
        """Test aggregate_data_across_files creates VirtualSource objects for each dataset."""
        ps_dset = MagicMock()
        ps_dset.shape = (10, 8, 8, 2)
        ps_dset.dtype = np.uint32
        ps_dset.__getitem__.return_value = np.ones((8, 8, 2))

        mock_file = MagicMock()
        mock_file.keys.return_value = ['pixel_spectra']
        mock_file.__iter__.return_value = iter(['pixel_spectra'])
        mock_file.__getitem__.return_value = ps_dset
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        pixel_spectra_summed = np.zeros((8, 8, 2))
        summed_images_summed = np.zeros((8, 80))
        summed_spectra_summed = np.zeros(2048)

        vsources, ps_sum, si_sum, ss_sum, num_frames, dtype, inshape = \
            self.archiver.aggregate_data_across_files(
                ['/tmp/test_000.h5'], 1, pixel_spectra_summed,
                summed_images_summed, summed_spectra_summed
            )

        mock_virtual_source.assert_called_once_with('/tmp/test_000.h5', 'pixel_spectra', shape=(10, 8, 8, 2))
        self.assertEqual(len(vsources), 1)

    @patch('hexitec.archiver.h5py.File')
    def test_aggregate_data_across_files_initializes_inshape(self, mock_h5py_file):
        """Test aggregate_data_across_files initializes inshape only once."""
        ps_dset1 = MagicMock()
        ps_dset1.shape = (10, 8, 8, 2)
        ps_dset1.dtype = np.uint32
        ps_dset1.__getitem__.return_value = np.ones((8, 8, 2))

        ps_dset2 = MagicMock()
        ps_dset2.shape = (10, 8, 8, 2)
        ps_dset2.dtype = np.uint32
        ps_dset2.__getitem__.return_value = np.ones((8, 8, 2))

        def mock_file_factory(filename):
            mock = MagicMock()
            mock.keys.return_value = ['pixel_spectra']
            mock.__iter__.return_value = iter(['pixel_spectra'])
            mock.__getitem__.return_value = ps_dset1 if 'test_000.h5' in filename else ps_dset2
            return mock

        mock_h5py_file.side_effect = lambda f: MagicMock(__enter__=lambda s: mock_file_factory(f), __exit__=lambda s, *args: None)

        pixel_spectra_summed = np.zeros((8, 8, 2))
        summed_images_summed = np.zeros((8, 80))
        summed_spectra_summed = np.zeros(2048)

        vsources, ps_sum, si_sum, ss_sum, num_frames, dtype, inshape = \
            self.archiver.aggregate_data_across_files(
                ['/tmp/test_000.h5', '/tmp/test_001.h5'], 1, pixel_spectra_summed,
                summed_images_summed, summed_spectra_summed
            )

        self.assertEqual(inshape[0], (10, 8, 8, 2))

    @patch('hexitec.archiver.h5py.File')
    def test_aggregate_data_across_files_summed_images_accumulation(self, mock_h5py_file):
        """Test aggregate_data_across_files correctly accumulates summed_images data."""
        si_dset = MagicMock()
        si_dset.shape = (10, 8, 80)
        si_dset.dtype = np.uint32
        si_dset.__getitem__.return_value = np.ones((8, 80))

        mock_file = MagicMock()
        mock_file.keys.return_value = ['summed_images']
        mock_file.__iter__.return_value = iter(['summed_images'])
        mock_file.__getitem__.return_value = si_dset
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        pixel_spectra_summed = np.zeros((8, 8, 2))
        initial_si_summed = np.ones((8, 80))
        summed_spectra_summed = np.zeros(2048)

        vsources, ps_sum, si_sum, ss_sum, num_frames, dtype, inshape = \
            self.archiver.aggregate_data_across_files(
                ['/tmp/test_000.h5'], 1, pixel_spectra_summed,
                initial_si_summed, summed_spectra_summed
            )

        np.testing.assert_array_equal(si_sum, np.ones((8, 80)) * 2)

    @patch('hexitec.archiver.h5py.File')
    def test_aggregate_data_across_files_summed_spectra_accumulation(self, mock_h5py_file):
        """Test aggregate_data_across_files correctly accumulates summed_spectra data."""
        ss_dset = MagicMock()
        ss_dset.shape = (10, 2048)
        ss_dset.dtype = np.uint32
        ss_dset.__getitem__.return_value = np.ones(2048)

        mock_file = MagicMock()
        mock_file.keys.return_value = ['summed_spectra']
        mock_file.__iter__.return_value = iter(['summed_spectra'])
        mock_file.__getitem__.return_value = ss_dset
        mock_h5py_file.return_value.__enter__.return_value = mock_file

        pixel_spectra_summed = np.zeros((8, 8, 2))
        summed_images_summed = np.zeros((8, 80))
        initial_ss_summed = np.ones(2048)

        vsources, ps_sum, si_sum, ss_sum, num_frames, dtype, inshape = \
            self.archiver.aggregate_data_across_files(
                ['/tmp/test_000.h5'], 1, pixel_spectra_summed,
                summed_images_summed, initial_ss_summed
            )

        np.testing.assert_array_equal(ss_sum, np.ones(2048) * 2)

    def test_flag_error_with_exception(self):
        """Test flag_error appends error message with exception info."""
        self.archiver.create_timestamp = MagicMock(return_value="2025-02-12T12:00:00.000000+00:00")
        with patch('hexitec.archiver.logging.error') as mock_logging:
            self.archiver.flag_error('Test error', e=ValueError('fail'))
            mock_logging.assert_called_once_with('Test error: fail')
        timestamp, error_message = self.archiver.errors_history[-1]
        self.assertEqual(error_message, 'Test error: fail')

    def test_flag_error_multiple_calls(self):
        """Test flag_error appends multiple error messages."""
        self.archiver.create_timestamp = MagicMock(side_effect=[
            "2025-02-12T12:00:00.000000+00:00",
            "2025-02-12T12:01:00.000000+00:00"
        ])
        with patch('hexitec.archiver.logging.error'):
            self.archiver.flag_error('First error')
            self.archiver.flag_error('Second error')
        self.assertEqual(self.archiver.errors_history[-2][1], 'First error')
        self.assertEqual(self.archiver.errors_history[-1][1], 'Second error')

    @patch('hexitec.archiver.logging.error')
    def test_parse_rsync_output_malformed_percentage_line_logs_error(self, mock_logging):
        """Test parse_rsync_output logs error on malformed percentage line"""
        error = "Error parsing invalid % % % format: too many values to unpack (expected 2)"
        self.archiver.parse_rsync_output(b'invalid % % % format')
        mock_logging.assert_called_once_with(error)
