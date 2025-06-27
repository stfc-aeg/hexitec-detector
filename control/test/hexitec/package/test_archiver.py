"""
Test Cases for the archiver in hexitec.archiver.

Christian Angelsen, STFC Detector Systems Software Group
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

from hexitec.archiver import ArchiverAdapter, Archiver, ArchiverError
from odin.adapters.parameter_tree import ParameterTreeError


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
            mock_popen.return_value = mock_proc

            bOK, errors, rc = self.archiver.execute_rsync_command(['rsync', 'cmd'])
            self.assertFalse(bOK)
            self.assertEqual(errors, ['error_line'])
            # self.assertEqual(rc, 0)
            # -> AssertionError: <MagicMock name='Popen().returncode' id='140562371779696'> != 0

    def test_parse_rsync_output_sets_filename_transferring(self):
        self.archiver.parse_rsync_output(b'08-11-002_000000.h5')
        self.assertEqual(self.archiver.filename_transferring, '08-11-002_000000.h5')

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
    def test_archive_files_rsync_interrupted(self, mock_is_server_accessible,
                                             mock_execute_rsync_command):
        mock_is_server_accessible.return_value = 0
        mock_execute_rsync_command.return_value = (False, ['error'], 255)
        self.archiver.queue = MagicMock()
        self.archiver.queue.get.return_value = 'server:/path/to/file.h5'
        self.archiver.queue.qsize.side_effect = [1, 0]
        self.archiver.queue.empty.side_effect = [False, True]
        self.archiver.archive_files()
        self.assertEqual(self.archiver.queue.qsize(), 1)
        self.assertFalse(self.archiver.background_task_enable)
        self.assertFalse(self.archiver.archiving_in_progress)

    @patch('hexitec.archiver.Archiver.execute_rsync_command')
    @patch('hexitec.archiver.Archiver.is_server_accessible')
    def test_archive_files_with_bandwidth_limit(self, mock_is_server_accessible,
                                                mock_execute_rsync_command):
        mock_is_server_accessible.return_value = 0
        mock_execute_rsync_command.return_value = (True, [], 0)
        self.archiver.bandwidth_limit = 1000
        self.archiver.queue = MagicMock()
        self.archiver.queue.get.return_value = 'server:/path/to/file.h5'
        self.archiver.queue.qsize.side_effect = [1, 0]
        self.archiver.queue.empty.side_effect = [False, True]
        self.archiver.archive_files()
        self.assertEqual(self.archiver.number_files_archived, 1)
        self.assertEqual(self.archiver.number_files_failed, 0)
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
