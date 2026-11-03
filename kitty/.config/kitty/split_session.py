"""Split immediately locally, or choose Local/Remote for a kitten ssh session."""

import os

from kittens.tui.handler import result_handler
from kitty.child import cwd_of_process


def main(args):
    # no_ui dispatches directly to handle_result inside Kitty.
    pass


@result_handler(no_ui=True)
def handle_result(args, result, target_window_id, boss):
    window = boss.window_id_map.get(target_window_id)
    if window is None:
        return

    # Keep the same split geometry for either choice. No arbitrary command is
    # accepted: launching a shell lets Kitty reconnect through its SSH kitten.
    location = args[1] if len(args) > 1 else 'hsplit'
    if location not in ('hsplit', 'vsplit'):
        raise ValueError('split_session.py expects hsplit or vsplit')

    ssh_pid, ssh_cmdline = window.ssh_kitten_cmdline_with_pid()
    local_cwd = None
    if ssh_cmdline:
        try:
            # The local SSH process inherits the cwd where SSH was invoked.
            # Resolve it before opening the chooser, not from remote OSC 7 data.
            local_cwd = cwd_of_process(ssh_pid)
        except (OSError, ValueError):
            pass

    def split(choice):
        # The source may have closed while the chooser was visible.
        if target_window_id not in boss.window_id_map:
            return
        if choice == 'r':
            cwd = 'current'
        elif choice == 'l':
            # An explicit local path bypasses Kitty's SSH-aware --cwd=current.
            cwd = (
                local_cwd
                or window.get_cwd_of_root_child()
                or os.path.expanduser('~')
            )
        else:
            return  # Escape or cancellation.
        boss.launch(
            f'--source-window=id:{target_window_id}',
            f'--next-to=id:{target_window_id}',
            f'--cwd={cwd}',
            f'--location={location}',
            '--bias=50',
        )

    if not ssh_cmdline:
        # Preserve the original mapping's local cwd behavior without a popup.
        split('r')
        return

    boss.choose(
        'Open the split locally or on the remote host?',
        split,
        'l:Local',
        'r:Remote',
        window=window,
        default='r',
        title='Split session',
    )
