"""Run with: python3 -B -m unittest discover -s kitty/tests -v"""
import io
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
from urllib.parse import unquote, urlsplit

# The custom kitten normally imports these inside Kitty's embedded Python.
for name in ('kittens', 'kittens.tui', 'kitty'):
    sys.modules[name] = types.ModuleType(name)
handler = types.ModuleType('kittens.tui.handler')
handler.result_handler = lambda **kw: lambda function: function
sys.modules[handler.__name__] = handler
child = types.ModuleType('kitty.child')
child.cwd_of_process = Mock(return_value='/host/entry')
sys.modules[child.__name__] = child
utils = types.ModuleType('kitty.utils')
utils.path_from_osc7_url = lambda url: unquote(urlsplit(url).path)
sys.modules[utils.__name__] = utils
spec = importlib.util.spec_from_file_location(
    'split_session', Path(__file__).parents[1] / '.config/kitty/split_session.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

RECORD = dict(version=1, project_root='/host/project space', target='dev',
              instance='local:project-dev', host_cwd='/host/original',
              cwd_authority='nixant-' + 'a' * 32)
ARGV = ['incus', 'exec', RECORD['instance'], '--cwd', '/workspace', '--', '/bin/bash']


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.window = Mock()
        self.window.child.foreground_processes = []
        self.window.screen.last_reported_cwd = ''
        self.window.ssh_kitten_cmdline_with_pid.return_value = (-1, [])
        self.window.get_cwd_of_root_child.return_value = '/host/root'
        self.boss = Mock()
        self.boss.window_id_map = {7: self.window}
        child.cwd_of_process.reset_mock(side_effect=True, return_value=True)
        child.cwd_of_process.return_value = '/host/entry'

    def invoke(self, direction='hsplit'):
        m.handle_result(['split_session.py', direction], None, 7, self.boss)

    def choose(self, choice):
        self.boss.choose.call_args.args[1](choice)

    def container(self, record=None, report=None):
        record = record or RECORD
        self.window.child.foreground_processes = [{'pid': 123, 'cmdline': ARGV}]
        self.window.screen.last_reported_cwd = report or f"file://{record['cwd_authority']}/etc"
        return patch.object(m, 'read_session', return_value=(record, '/host/entry'))

    def test_local_and_ssh(self):
        self.invoke()
        self.boss.choose.assert_not_called()
        self.assertIn('--cwd=current', self.boss.launch.call_args.args)
        for choice, cwd in [('l', '/host/entry'), ('r', 'current'), ('', None)]:
            self.boss.reset_mock()
            self.window.ssh_kitten_cmdline_with_pid.return_value = (5, ['kitten', 'ssh', 'host'])
            self.invoke()
            self.assertEqual(self.boss.choose.call_args.kwargs['default'], 'r')
            self.choose(choice)
            if cwd:
                self.assertIn('--cwd=' + cwd, self.boss.launch.call_args.args)
            else:
                self.boss.launch.assert_not_called()

    @patch.object(m, 'usable_directory', return_value=True)
    @patch.object(m.shutil, 'which', return_value='/bin/nixant')
    def test_container_vectors_and_snapshot(self, *_):
        for direction in ('hsplit', 'vsplit'):
            with self.container(report=f"file://{RECORD['cwd_authority']}/guest%20space/%E9%9B%AA"):
                self.invoke(direction)
            self.assertEqual(self.boss.choose.call_args.kwargs['default'], 'c')
            self.window.screen.last_reported_cwd = 'file://host/stale'
            self.choose('c')
            self.assertEqual(self.boss.launch.call_args.args, (
                '--source-window=id:7', '--next-to=id:7', '--cwd=/host/project space',
                f'--location={direction}', '--bias=50', '--hold', '--', '/bin/nixant',
                'shell', 'dev', '--cwd', '/guest space/雪'))

    @patch.object(m, 'usable_directory', return_value=True)
    def test_local_cancel_closed_window(self, *_):
        with self.container():
            self.invoke()
        self.choose('l')
        self.assertIn('--cwd=/host/entry', self.boss.launch.call_args.args)
        self.boss.launch.reset_mock()
        self.choose('')
        self.boss.window_id_map.clear()
        self.choose('c')
        self.boss.launch.assert_not_called()

    @patch.object(m.shutil, 'which', return_value='/bin/nixant')
    @patch.object(m, 'usable_directory', return_value=True)
    def test_missing_stale_report_and_concurrent_sessions(self, *_):
        for target, instance, token, path in [('dev', 'local:a', 'a', '/etc'),
                                              ('test', 'local:b', 'b', '/root'),
                                              ('dev', 'local:a', 'c', '/tmp')]:
            record = dict(RECORD, target=target, instance=instance,
                          cwd_authority='nixant-' + token * 32)
            for report, expected in [(f"file://{record['cwd_authority']}{path}", path),
                                      ('file://host/local', None),
                                      ('file://nixant-' + 'd' * 32 + '/old', None)]:
                with self.container(record, report):
                    self.invoke()
                self.choose('c')
                args = self.boss.launch.call_args.args
                self.assertIn(target, args)
                self.assertEqual('--cwd' in args, expected is not None)
                if expected:
                    self.assertEqual(args[-1], expected)
                else:
                    self.assertIn('normal starting directory', self.boss.choose.call_args.args[3])

    @patch.object(m, 'usable_directory', return_value=True)
    @patch.object(m.shutil, 'which', return_value='/bin/nixant')
    def test_agent_titles_and_launch(self, *_):
        for title, agent in [('pig - workspace', 'pig'), ('kmet - workspace', 'kmet'),
                             ('project | Claude Code | active', 'claude')]:
            for direction in ('hsplit', 'vsplit'):
                self.window.tabref.return_value.title = title
                with self.container():
                    self.invoke(direction)
                self.assertEqual(self.boss.choose.call_args.kwargs['default'], 'c')
                self.assertIn(f'a:Agent — {agent}', self.boss.choose.call_args.args)
                # Choice uses the captured source tab, not a later overlay title.
                self.window.tabref.return_value.title = 'unrelated'
                self.choose('a')
                self.assertEqual(self.boss.launch.call_args.args[-2:], ('--startup-app', agent))
                self.choose('c')
                self.assertNotIn('--startup-app', self.boss.launch.call_args.args)
        for title in ['', 'editing pig - notes', ' kmet - space', 'claude code', None]:
            self.assertIsNone(m.agent_from_title(title))
        self.assertEqual(m.agent_from_title('pig - $(evil); Claude Code'), 'pig')

    def test_agent_requires_container_and_matching_tab(self):
        self.window.title = 'pig - pane'
        self.window.tabref.return_value.title = 'unrelated tab'
        with self.container(), patch.object(m, 'usable_directory', return_value=True):
            self.invoke()
        self.assertEqual(len(self.boss.choose.call_args.args), 4)
        self.choose('a')
        self.boss.launch.assert_not_called()
        self.window.tabref.return_value.title = 'pig - workspace'
        self.window.child.foreground_processes = []
        self.boss.reset_mock()
        self.invoke()
        self.boss.choose.assert_not_called()

    def test_guest_path_validation(self):
        authority = RECORD['cwd_authority']
        for report in ['', 'file://host/etc', f'file://{authority}',
                       f'file://{authority}/bad%00path', f'file://{authority}/bad%zz',
                       f'file://{authority}/etc?query', f'file://{authority}/etc#fragment',
                       f'file://{authority}/\npath', 'file://[broken/path']:
            self.assertIsNone(m.guest_directory(report, authority), report)
        self.assertEqual(m.guest_directory(f'file://{authority}/guest-only', authority), '/guest-only')

    def read_record(self, record, env=None):
        command = b'\0'.join(x.encode() for x in ARGV) + b'\0'
        environment = env if env is not None else b'NIXANT_KITTY_SESSION=' + json.dumps(record).encode() + b'\0'
        def read(pid, name, limit):
            return command if name == 'cmdline' else environment
        with patch.object(m, 'process_identity', return_value=b'123'), patch.object(m, 'read_proc', side_effect=read):
            return m.read_session(123, ARGV)

    def test_metadata_validation(self):
        self.assertEqual(self.read_record(RECORD), (RECORD, '/host/entry'))
        for key, values in {
            'version': [True, 2, '1', None], 'target': ['-x', 'dev;evil', 4, None],
            'instance': ['local:wrong', 'remote:project-dev', '\x1b[31m', None],
            'project_root': ['relative', '/bad\0path', None],
            'host_cwd': ['relative', [], None],
            'cwd_authority': ['nixant-old', None, 123],
        }.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    self.assertIsNone(self.read_record(dict(RECORD, **{key: value})))
        self.assertIsNone(self.read_record([]))
        self.assertIsNone(self.read_record(RECORD, b'OTHER=value\0'))
        self.assertIsNone(self.read_record(RECORD, b'NIXANT_KITTY_SESSION=' + b'x' * (m.MAX_SESSION_BYTES + 1)))
        # Additional record fields never become commands.
        self.assertIsNotNone(self.read_record(dict(RECORD, command='evil', executable='/evil')))

    def test_bounded_reads_and_malformed_environment(self):
        with patch('builtins.open', return_value=io.BytesIO(b'12345')):
            with self.assertRaises(ValueError):
                m.read_proc(123, 'environ', 4)
        with patch('builtins.open', return_value=io.BytesIO(b'1234')):
            self.assertEqual(m.read_proc(123, 'environ', 4), b'1234')
        with self.assertRaises(ValueError):
            self.read_record(RECORD, b'NIXANT_KITTY_SESSION={broken\0')
        self.assertIsNone(self.read_record(RECORD, b'NIXANT_KITTY_SESSION={}\0NIXANT_KITTY_SESSION={}\0'))
        with patch.object(m, 'read_proc', return_value=b'1 (name with ) parentheses) S ' + b'0 ' * 18 + b'987 0'):
            self.assertEqual(m.process_identity(1), b'987')

    def test_process_failures_and_ambiguity(self):
        self.window.child.foreground_processes = [{'pid': 123, 'cmdline': ARGV}]
        for error in (PermissionError(), ProcessLookupError(), ValueError(), UnicodeError()):
            with patch.object(m, 'read_session', side_effect=error):
                self.assertIsNone(m.nixant_session(self.window))
        with patch.object(m, 'read_session') as read:
            self.window.child.foreground_processes *= 2
            self.assertIsNone(m.nixant_session(self.window))
            read.assert_not_called()
        with patch.object(m, 'process_identity', return_value=b'123'), patch.object(m, 'read_proc', return_value=b'other\0'):
            self.assertIsNone(m.read_session(123, ARGV))
        command = b'\0'.join(x.encode() for x in ARGV) + b'\0'
        env = b'NIXANT_KITTY_SESSION=' + json.dumps(RECORD).encode()
        with patch.object(m, 'process_identity', side_effect=[b'1', b'2']), patch.object(m, 'read_proc', side_effect=[command, env]):
            self.assertIsNone(m.read_session(123, ARGV))

    @patch.object(m, 'usable_directory', return_value=True)
    def test_detection_failure_passthrough_and_ssh_precedence(self, *_):
        with self.container(), patch.object(m, 'read_session', return_value=None):
            self.invoke()
        self.boss.choose.assert_not_called()
        self.window.ssh_kitten_cmdline_with_pid.return_value = (5, ['kitten', 'ssh', 'host'])
        with self.container():
            self.invoke()
        self.assertEqual(self.boss.choose.call_args.kwargs['default'], 'c')

    def test_local_fallbacks(self):
        for usable in ('/host/original', '/host/root', '/home/fallback'):
            with self.container(), patch.object(m, 'read_session', return_value=(RECORD, None)), \
                    patch.object(m.os.path, 'expanduser', return_value='/home/fallback'), \
                    patch.object(m, 'usable_directory', side_effect=lambda path: path == usable):
                self.invoke()
            self.choose('l')
            self.assertIn('--cwd=' + usable, self.boss.launch.call_args.args)

    def test_launch_errors(self):
        with self.container(), patch.object(m, 'usable_directory', return_value=True):
            self.invoke()
        with patch.object(m, 'usable_directory', return_value=False):
            self.choose('c')
        self.boss.launch.assert_not_called()
        self.boss.show_error.assert_called()
        with patch.object(m, 'usable_directory', return_value=True), patch.object(m.shutil, 'which', return_value=None):
            self.choose('c')
        self.boss.launch.assert_not_called()
        with patch.object(m, 'usable_directory', return_value=True), patch.object(m.shutil, 'which', return_value='/bin/nixant'):
            self.boss.launch.side_effect = OSError('failed')
            self.choose('c')
        self.assertIn('Launch failed', self.boss.show_error.call_args.args[1])

    def test_invalid_direction_and_missing_source(self):
        with self.assertRaises(ValueError):
            self.invoke('invalid')
        self.boss.window_id_map.clear()
        self.invoke()
        self.boss.launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
