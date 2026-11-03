# TODO: PiG-aware Nixant split chooser

Status: initial implementation completed, with updated requirements below.
Live guest acceptance remains pending. The original checklist below is retained
as design history, not current implementation status.

Implemented changes:
- Inspect the source **tab** title as requested (rather than pane title).
- Recognize case-sensitive `pig -` / `kmet -` prefixes, or `Claude Code` anywhere.
- Offer a single **A: Agent** shortcut for the identified pig/kmet/claude binary.
- Retain Container as default and preserve local/SSH behavior.
- Add Nixant `shell --startup-app pig|kmet|claude` (also its ssh alias), with an
  interactive login environment and a fresh login shell after application exit.
- Add kitten and Nixant CLI regression coverage. See `nixant-compat.md` for
  deployment requirements and title-detection limitations.

## Objective

When splitting a recognized local Nixant session whose source pane title suggests
PiG is active (for example, `pig - workspace`), offer an explicit option to open
a fresh guest shell and start PiG there. Preserve current local, SSH, and Nixant
shell behavior.

Relevant files:

- `kitty/.config/kitty/split_session.py`
- `kitty/.config/kitty/nixant-compat.md`
- `kitty/tests/test_split_session.py`
- Nixant implementation: `/home/user/dev/jail/nixant`

## Design decisions

- Detect PiG heuristically from the **source window/pane title**, not the tab
  title. Tabs can contain multiple panes or have manually assigned titles.
- Apply title detection only after validating a local Nixant session through the
  existing process metadata contract.
- Treat the title as an untrusted UI hint, never as authoritative process state.
- Keep Container shell as the default. PiG launch always requires an explicit
  choice, so a stale or forged title cannot automatically start an application.
- Launch a new PiG session. Do not automatically resume, attach to, or clone the
  original agent session, arguments, credentials, model, or prompt.
- Do not infer the guest directory from the title. Continue using validated
  session-specific OSC 7 reports.
- No PiG core changes, guest application marker, or Kitty remote-control access
  are required for title detection.

## 1. Snapshot and classify the source pane title

- [ ] Capture `window.title` at invocation, before opening the choice overlay.
- [ ] Add a small pure helper for title classification.
- [ ] Initially recognize an anchored, case-insensitive prefix such as:

  ```python
  re.match(r"^pig\s*[-–—]\s*\S", title, re.IGNORECASE)
  ```

- [ ] Match titles such as `pig - workspace`, `PiG – workspace`, and
  `pig — workspace`.
- [ ] Do not use broad substring matching: `editing pig - notes` should not match.
- [ ] Do not display or execute text extracted from the title.
- [ ] Add other title formats only after observing actual PiG titles; do not
  assume an undocumented format or inspect PiG internals unnecessarily.

Known limitations:

- PiG may leave a stale title after exiting.
- User title overrides or intermediaries may hide the PiG title.
- Any guest application can set a matching title.
- Titles do not establish whether PiG is the current foreground process.

These limitations are acceptable for an optional, explicitly confirmed action.

## 2. Extend the Nixant chooser

For a validated Nixant session with a matching title:

```text
Open split in:
[L] Local
[C] Container shell
[P] Container shell + PiG
```

- [ ] Keep `c` as the default and Escape as cancellation.
- [ ] Preserve instance identification in the container choices.
- [ ] If no valid guest CWD report is available, label both guest choices as
  using the normal starting directory.
- [ ] Preserve the existing Local/Container menu when the title does not match.
- [ ] Preserve SSH Local/Remote behavior, even if the SSH pane title mentions PiG.
- [ ] Preserve immediate local splitting without a chooser.
- [ ] Preserve source-window ID, adjacency, direction, and 50 percent split bias.
- [ ] Recheck source-window existence before acting on a choice.

## 3. Add a reliable Nixant startup-app interface

The current shell interface does not provide the required startup application
contract. Implement and document this on the Nixant side before wiring the
kitten's PiG action.

Proposed CLI (not an existing option):

```sh
nixant shell TARGET --cwd GUEST_DIRECTORY --startup-app pig
```

Without a valid guest directory report:

```sh
nixant shell TARGET --startup-app pig
```

Requirements:

- [ ] Reuse normal Nixant project/target discovery, ownership validation,
  instance startup, guest user selection, and login environment initialization.
- [ ] Support only an explicit allowlisted startup application, initially `pig`.
  Reject unknown values clearly.
- [ ] Start PiG in the chosen guest directory after the guest login environment
  has initialized, with the terminal and stdin attached normally.
- [ ] Define and test startup sequencing for supported Bash, Zsh, and Fish shells.
  Do not assume `shell -lc` reproduces interactive initialization for every shell.
- [ ] Leave an interactive guest shell available after PiG exits.
- [ ] If PiG is missing or exits unsuccessfully, show a useful error/status and
  leave the guest shell usable. Never silently run a host-side PiG instead.
- [ ] Ensure startup happens once per new entry, not on every prompt or in
  subsequently opened nested shells.
- [ ] Emit fresh `NIXANT_KITTY_SESSION` metadata and preserve the session-specific
  OSC 7 reporting contract for subsequent splits.
- [ ] Preserve existing `nixant shell` behavior when the option is omitted.
- [ ] Decide and document whether the existing `nixant ssh` alias exposes the
  same option for consistency.

Do not implement startup by blindly sending `pig\n` to the new terminal. Startup
latency, instance-start confirmation, authentication, or errors can cause input
to reach the wrong program. Do not solve this with a fixed delay.

## 4. Wire the kitten launch action

- [ ] Add a distinct PiG choice that constructs a fixed argument vector:

  ```text
  HOST_NIXANT_EXECUTABLE shell TARGET [--cwd GUEST_DIRECTORY] --startup-app pig
  ```

- [ ] Continue launching from the recorded **local project root**; guest CWD
  remains a Nixant argument, not Kitty's local `--cwd`.
- [ ] Use the existing locally configured `NIXANT_EXECUTABLE` resolution.
- [ ] Pass each argument individually, with Kitty's option/command separator.
- [ ] Never construct a shell command from the title or metadata.
- [ ] Retain missing executable/project-root checks and visible launch errors.
- [ ] Keep CLI failures visible with the existing held-pane behavior, including
  use of an older Nixant that does not support `--startup-app`.
- [ ] Do not silently downgrade a failed PiG request to another action.

## 5. Automated tests

### Kitten

- [ ] Matching titles: case variants, hyphen/en dash/em dash, Unicode workspace
  names, and spaces.
- [ ] Nonmatches: empty titles, unrelated titles, embedded `pig` text, and a
  different pane/tab title.
- [ ] Matching title without valid Nixant metadata does not add the PiG option.
- [ ] Matching SSH/local titles retain existing behavior.
- [ ] Container shell remains default when PiG is offered.
- [ ] PiG choice emits the exact fixed argument vector in both split directions.
- [ ] Title contents cannot introduce arguments or commands.
- [ ] Missing/stale CWD reports omit `--cwd` and label the fallback.
- [ ] Snapshot isolation across panes, instances, and title changes while the
  chooser is open.
- [ ] Escape, closed source window, missing executable/project root, and launch
  exceptions behave safely.
- [ ] Existing local, SSH, and Nixant tests remain green.

### Nixant

- [ ] Allowlisted startup-app validation and unchanged default shell entry.
- [ ] User/login environment and explicit/default CWD are preserved.
- [ ] PiG launches once, interactively, inside the guest, never on the host.
- [ ] Shell remains usable after PiG exits or cannot be found.
- [ ] Fresh session metadata and authority reach the appropriate processes.
- [ ] Supported shell startup strategies do not replace user prompt hooks or
  accidentally trigger application startup in nested shells.

## 6. Live acceptance

- [ ] Enter a local Nixant session and launch PiG; verify the pane title matches.
- [ ] Split and select PiG; confirm a new PiG session starts in the same guest CWD.
- [ ] Repeat from a guest-only directory and a path containing spaces/Unicode.
- [ ] Exit PiG in the new pane; confirm a usable guest shell remains.
- [ ] Select Container shell instead; verify PiG does not start.
- [ ] Exercise a stale PiG title; ensure startup still requires explicit `P`.
- [ ] Test multiple panes/containers to ensure titles and directories never leak
  between source contexts.
- [ ] Verify ordinary local and SSH panes behave as before.
- [ ] Test missing guest PiG and an older host Nixant; errors must remain visible.

## Delivery and scope

1. Implement/test the Nixant startup-app contract.
2. Implement title classification and the conditional kitten choice.
3. Update compatibility documentation with CLI version requirements, heuristic
   limitations, executable resolution, and held-pane behavior.
4. Run unit tests and record live acceptance separately.

Deferred: authoritative foreground-process detection, application markers,
automatic PiG session continuation, arbitrary application replay, Incus behind
SSH, nested environments, and new tab/OS-window bindings.

Completion requires both automated coverage and live validation; title matching
unit tests alone do not establish reliable guest startup sequencing.
