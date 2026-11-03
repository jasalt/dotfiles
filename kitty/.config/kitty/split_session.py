"""Local/SSH/Nixant split chooser. See nixant-compat.md for the contract."""

import json
import os
import re
import shutil
from urllib.parse import urlsplit

from kittens.tui.handler import result_handler
from kitty.child import cwd_of_process
from kitty.utils import path_from_osc7_url

# Local configuration only: set an absolute executable path for GUI PATH issues.
# Never read an executable or command from session metadata.
NIXANT_EXECUTABLE = 'nixant'
MAX_ENV_BYTES = 1024 * 1024
MAX_SESSION_BYTES = 16 * 1024


def absolute_path(value):
    return isinstance(value, str) and value.startswith('/') and '\0' not in value


def usable_directory(value):
    try:
        return absolute_path(value) and os.path.isdir(value) and os.access(value, os.X_OK)
    except (OSError, ValueError):
        return False


def process_cwd(pid):
    try:
        return cwd_of_process(pid)
    except (OSError, ValueError):
        return None


def read_proc(pid, name, limit):
    with open(f'/proc/{pid}/{name}', 'rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('process data exceeds limit')
    return data


def process_identity(pid):
    # starttime (field 22); comm can itself contain spaces and parentheses.
    stat = read_proc(pid, 'stat', 8192)
    return stat[stat.rindex(b')') + 2:].split()[19]


def read_session(pid, argv):
    """Read only the selected Incus process, rejecting exit/exec/PID reuse races."""
    before = process_identity(pid)
    command = read_proc(pid, 'cmdline', MAX_ENV_BYTES)
    if [os.fsdecode(x) for x in command.rstrip(b'\0').split(b'\0')] != argv:
        return None
    environment = read_proc(pid, 'environ', MAX_ENV_BYTES)
    records = [x.split(b'=', 1)[1] for x in environment.split(b'\0')
               if x.startswith(b'NIXANT_KITTY_SESSION=')]
    if len(records) != 1 or len(records[0]) > MAX_SESSION_BYTES:
        return None
    local_cwd = process_cwd(pid)
    if (before != process_identity(pid)
            or command != read_proc(pid, 'cmdline', MAX_ENV_BYTES)):
        return None
    record = json.loads(records[0])
    if not isinstance(record, dict) or type(record.get('version')) is not int or record['version'] != 1:
        return None
    if not all(absolute_path(record.get(key)) for key in ('project_root', 'host_cwd')):
        return None
    for key, pattern in (
        ('target', r'[A-Za-z_][A-Za-z0-9_-]*'),
        ('instance', r'local:[A-Za-z0-9][A-Za-z0-9_.-]*'),
        ('cwd_authority', r'nixant-[0-9a-f]{32}'),
    ):
        if not isinstance(record.get(key), str) or not re.fullmatch(pattern, record[key]):
            return None
    if record['instance'] != argv[2]:
        return None
    return record, local_cwd


def guest_directory(report, authority):
    """Only accept OSC 7 reports carrying this entry's random authority."""
    try:
        if isinstance(report, bytes):
            report = report.decode('utf-8')
        if not report or any(ord(c) < 32 for c in report):
            return None
        uri = urlsplit(report)
        if (uri.scheme != 'file' or uri.netloc != authority
                or uri.query or uri.fragment
                or re.search(r'%(?![0-9a-fA-F]{2})', uri.path)):
            return None
        path = path_from_osc7_url(report)
        return path if absolute_path(path) else None
    except (ValueError, UnicodeError):
        return None


def nixant_session(window):
    # Recognize the exact locally generated Nixant exec prefix, not arbitrary
    # Incus options, remote hosts, wrappers, or commands copied from metadata.
    candidates = []
    for process in window.child.foreground_processes:
        argv = list(process.get('cmdline') or ())
        if (len(argv) >= 6 and os.path.basename(argv[0]) == 'incus'
                and argv[1] == 'exec' and argv[3] == '--cwd'
                and argv[5] == '--'):
            candidates.append((process['pid'], argv))
    if len(candidates) != 1:
        return None
    try:
        session = read_session(*candidates[0])
    except (OSError, ValueError, IndexError, UnicodeError, RecursionError):
        return None
    if session is None:
        return None
    record, local_cwd = session
    return record, local_cwd, guest_directory(
        window.screen.last_reported_cwd, record['cwd_authority'])


def main(args):
    # no_ui dispatches directly to handle_result inside Kitty.
    pass


@result_handler(no_ui=True)
def handle_result(args, result, target_window_id, boss):
    window = boss.window_id_map.get(target_window_id)
    if window is None:
        return
    location = args[1] if len(args) > 1 else 'hsplit'
    if location not in ('hsplit', 'vsplit'):
        raise ValueError('split_session.py expects hsplit or vsplit')

    # Snapshot before the popup changes foreground processes / active window.
    container = nixant_session(window)
    ssh_pid, ssh_cmdline = window.ssh_kitten_cmdline_with_pid()
    if container:
        record, entry_cwd, guest_cwd = container
        local_cwd = next((path for path in (entry_cwd, record['host_cwd'],
                          window.get_cwd_of_root_child(), os.path.expanduser('~'))
                          if usable_directory(path)), os.path.expanduser('~'))
    else:
        local_cwd = (process_cwd(ssh_pid) if ssh_cmdline else None)
        local_cwd = local_cwd or window.get_cwd_of_root_child() or os.path.expanduser('~')

    def split(choice):
        if target_window_id not in boss.window_id_map:
            return
        command = []
        if choice == 'c' and container:
            cwd = record['project_root']
            if not usable_directory(cwd):
                boss.show_error('Cannot split Nixant session',
                                'The recorded local project directory is missing or inaccessible.')
                return
            executable = shutil.which(NIXANT_EXECUTABLE)
            if not executable:
                boss.show_error('Cannot split Nixant session',
                                'Nixant is not executable on Kitty\'s PATH. Set '
                                'NIXANT_EXECUTABLE in split_session.py to its absolute path.')
                return
            # --hold keeps CLI errors (including unsupported --cwd) visible.
            command = ['--hold', '--', executable, 'shell', record['target']]
            if guest_cwd is not None:
                command.extend(['--cwd', guest_cwd])
        elif choice == 'r' and not container:
            cwd = 'current'
        elif choice == 'l':
            cwd = local_cwd
        else:
            return
        try:
            boss.launch(
                f'--source-window=id:{target_window_id}',
                f'--next-to=id:{target_window_id}',
                f'--cwd={cwd}',
                f'--location={location}',
                '--bias=50',
                *command,
            )
        except Exception as exc:
            boss.show_error('Cannot split session', f'Launch failed: {type(exc).__name__}')

    if container:
        label = f"c:Container — {record['instance']}"
        if guest_cwd is None:
            label += ' (normal starting directory)'
        boss.choose('Open split in:', split, 'l:Local', label,
                    window=window, default='c', title='Split session')
    elif ssh_cmdline:
        boss.choose('Open the split locally or on the remote host?', split,
                    'l:Local', 'r:Remote', window=window, default='r', title='Split session')
    else:
        split('r')
