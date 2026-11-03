# Kitty kitten implementation plan: Nixant compatibility

Status: implemented in `split_session.py` with mocked unit coverage. Live Kitty/Incus acceptance remains to be performed.

Companion implementation inspected at [`nixant-py`](https://github.com/jasalt/nixant-py) (`src/nixant/cli.py` and `nix/modules/shell-integration/osc7.py`). Its design document is `nixant-py/todo-kitten-compat.md`.

## Implemented contract and installation

The version-1 JSON includes the five fields below **plus the required**
`cwd_authority`, matching `nixant-[0-9a-f]{32}`. Nixant generates a fresh authority
for every shell entry. Guest prompts emit `file://AUTHORITY/URL_ENCODED_PATH`
through OSC 7. The kitten accepts a directory only when its authority exactly
matches the inspected local Incus process's record. Even a previous session into
the same instance cannot supply the current session's directory.

Detection currently supports the generated local invocation
`incus exec local:INSTANCE --cwd PATH -- COMMAND...`. Unknown Incus argument
layouts, non-local instances, ambiguous foreground Incus processes, and invalid
metadata are not replayed. Environment reads are Linux-only, capped at 1 MiB;
the JSON record is capped at 16 KiB. Process start time and command-line checks
reduce process-exit/PID-reuse races. Metadata is correlation data, not authentication.

Deploy `split_session.py` beside the local `kitty.conf` using this repository's
normal Stow setup (`stow -S kitty` from the repository root, after resolving any
existing destination conflicts). The existing hsplit/vsplit bindings are
unchanged. Reload changed mappings with Ctrl+Shift+F5.

If GUI Kitty cannot find the host-installed `nixant`, set `NIXANT_EXECUTABLE` at
the top of `split_session.py` to its absolute executable path. This setting is
local configuration, never taken from process metadata. Missing executable or
project directory errors appear in Kitty. Container launches use `--hold` so CLI
errors, including an older Nixant without `--cwd`, remain visible; this also means
successful container shells leave their pane held open after exit (close it with
Kitty's normal close-window shortcut).

Local uses the usable Incus process CWD, recorded `host_cwd`, root-process CWD,
then home. Container runs `nixant shell TARGET [--cwd GUEST_PATH]` from the local
project root. Missing/stale reports visibly select the normal starting directory.
SSH and ordinary local behavior remain unchanged. Incus entered after SSH and
unmanaged Incus sessions are not supported.

Run unit tests from the dotfiles repository:

```sh
python3 -B -m unittest discover -s kitty/tests -v
```

The remaining sections preserve the design requirements and live acceptance
checklist. They are not a claim that live acceptance has been completed.

## Objective

Extend the current Local/Remote SSH split chooser with Local/Container choices for locally launched interactive Nixant sessions. Preserve immediate splitting for ordinary local panes and the existing SSH behavior.

The existing kitten lives in the Kitty dotfiles configuration as `kitty/.config/kitty/split_session.py`. Locate that configuration repository before editing; this plan's directory is the workspace root, not necessarily the dotfiles repository.

Existing bindings:

```conf
map ctrl+shift+o kitten split_session.py hsplit
map ctrl+shift+alt+o kitten split_session.py vsplit
```

Both directions retain a 50 percent split. No tab or OS-window binding changes are required.

## Required Nixant interface

Nixant provides:

1. `nixant shell TARGET --cwd ABSOLUTE_GUEST_PATH`.
2. `NIXANT_KITTY_SESSION` on the local interactive Incus process, containing version-1 JSON with `project_root`, `target`, `instance`, and `host_cwd`.
3. Prompt-time guest CWD reporting with an agreed method to distinguish valid guest reports from stale host/previous-session reports.

Example record:

```json
{
  "version": 1,
  "project_root": "/home/user/projects/myapp",
  "target": "dev",
  "instance": "local:myapp-dev",
  "host_cwd": "/home/user/projects/myapp/src",
  "cwd_authority": "nixant-0123456789abcdef0123456789abcdef"
}
```

Optional guest `NIXANT_*` variables are not used as authoritative detection. No global registry, guest-to-host control socket, or arbitrary replay command is needed.

## 1. Detect the selected pane's session

At invocation:

- Resolve the source window by its ID and validate `hsplit`/`vsplit`.
- Inspect that window's foreground processes using Kitty's available process APIs.
- Recognize an actual local `incus exec` invocation and obtain its PID and arguments.
- Read that PID's environment, preferably through a suitable Kitty API if available; otherwise use bounded Linux `/proc/PID/environ` reads.
- Decode and validate `NIXANT_KITTY_SESSION` from that process, never from the kitten's own environment.
- Match the recorded qualified instance to the Incus invocation. Reject ambiguity instead of selecting an unrelated process.
- Handle exited processes, permission failures, malformed/oversized data, unsupported versions, and missing fields without crashing.

Validate field types, absolute host paths, Nixant target syntax, and instance identity. Treat metadata as context rather than proof of trust: the local process user can modify it. Do not execute commands supplied in the record.

Suggested precedence:

1. Valid local Nixant/Incus session.
2. Existing recognized `kitten ssh` session.
3. Ordinary local passthrough.

Do not classify arbitrary `incus exec` commands as Nixant sessions without valid metadata. When detection fails, preserve ordinary splitting and do not replay an unknown container command.

## 2. Capture local and guest directories before the popup

Local directory priority:

1. Actual local Incus process CWD.
2. Recorded `host_cwd`, if usable.
3. Existing local root-process CWD/home fallback.

Use an explicit local path for Local launches. Do not use SSH-aware `--cwd=current` for that choice.

Guest directory:

- Read the source pane's reported directory using Kitty's directory-report parsing facilities.
- Decode URI encoding and require an absolute path without NUL characters.
- Associate the report with this guest session according to the reporting contract agreed with Nixant.
- Do not accept the last local OSC 7 report as a guest directory.
- Do not check guest paths with local filesystem APIs.
- If the report is missing or cannot be associated reliably, omit Nixant's `--cwd` and label the choice as using the normal starting directory.

Snapshot context before opening the overlay, so the chooser cannot become the source process/window accidentally. Recheck source-window existence before launching.

## 3. Show the chooser only for recognized sessions

For Nixant:

```text
Open split in:
[L] Local
[C] Container — myapp-dev
```

Use Kitty's built-in choice UI through the same custom-kitten pattern as the current SSH chooser. Container is the default; Escape cancels. Sanitize instance names before including them in terminal UI text.

For SSH, retain Local/Remote and its current default. For ordinary local panes, perform the original split immediately, without a popup.

## 4. Launch through Nixant

Local selection:

- Open the configured local shell in the explicit resolved local directory.
- Preserve source-window ID, adjacency, split direction, and bias.

Container selection:

- Set Kitty's local launch CWD to the recorded project root.
- Execute a fixed argument vector:

```text
nixant shell TARGET --cwd GUEST_DIRECTORY
```

If no trustworthy guest directory is available:

```text
nixant shell TARGET
```

Pass arguments individually via Kitty's launch API, using its option/command separator as needed. Do not construct a shell string. The guest path belongs to Nixant's `--cwd`, not Kitty's local `--cwd`.

Use the host-installed Nixant executable, with a documented configuration override if required for GUI PATH differences; do not accept an executable path or command from terminal-provided metadata. Surface missing Nixant, missing project roots, unsupported CLI versions, and launch errors clearly. Never silently reinterpret a failed container choice as a local command.

Fresh Nixant entry preserves ownership validation, configured user/login shell, target selection, and startup handling. It also creates fresh session metadata for subsequent splits.

## 5. Process and lifecycle safety

- Keep reads bounded and fast; do not run Nix evaluation or slow Incus inspection on Kitty's UI thread.
- Catch expected process/environment access errors.
- Where practical, confirm process identity has not changed during inspection to reduce PID-reuse races.
- Keep source-window targeting explicit after the popup closes.
- Cancel cleanly if the source pane closes.
- Avoid shared mutable session state: every invocation uses its own pane, process, metadata, and reported directory.
- Do not expose host metadata in the guest or grant the guest Kitty remote-control access.

## Tests

Unit tests with mocked Kitty/process interfaces:

- Local passthrough and existing SSH Local/Remote behavior.
- Nixant detection and both split directions.
- Two instances, multiple targets, and two sessions into one instance with different guest CWDs.
- Container default, Local choice, Escape, and closed source pane.
- Exact argument vectors and explicit local project-root CWD.
- Local process CWD and metadata/root/home fallbacks.
- Paths with spaces and Unicode; URI decoding and NUL/relative-path rejection.
- Missing/stale directory reports omit guest `--cwd`.
- Malformed JSON, unsupported schema, wrong field types, instance mismatch, oversized metadata, unreadable environment, and process exit.
- No arbitrary command execution from metadata or interpolated shell strings.

Live validation after deploying both sides:

1. Start Nixant from a host subdirectory; Local returns there.
2. Change the guest directory and split; Container opens there.
3. Repeat from `/etc` or another guest-only directory.
4. Use several containers and sessions without mixing contexts.
5. Confirm ordinary local and SSH panes behave as before.
6. Verify failure behavior with missing reports, stopped/deleted instances, and unavailable Nixant.

## Deferred work

- Nixant entered after SSH: local process inspection cannot see remote Incus metadata; requires a separate validated metadata channel and SSH-host reconnect path.
- Nested sessions and a Local/SSH host/Container three-way menu.
- Arbitrary unmanaged Incus sessions.
- Non-Linux process-environment inspection.
- Extending the chooser to tabs and OS windows.

## Completion criteria

The two implementations share a documented versioned contract; local and guest-only directory preservation work; concurrent sessions stay independent; local/SSH behavior is unchanged; malformed or stale context fails safely; installation and local-only limitations are documented. Unit tests alone do not establish live Kitty UI or guest prompt integration correctness.
