# Copperline native runtime

The active runtime uses Copperline 1.0.0's native JSON-RPC control protocol.
Patched WinUAE, Windows PowerShell, GDB/MI and generated ELF symbols are retired.
The UI remains the static-analysis/reassembly workspace; runtime sessions run
through the restricted target-aware CLI and return JSON observations. There is
no new public debugger endpoint or browser emulator console.

## Reproduce in this cloud environment

```sh
cd /workspace/amiga-reversing
export COPPERLINE_BINARY=/workspace/copperline-assessment/squashfs-root/usr/bin/copperline
export COPPERLINE_ROM=/workspace/attachments/30c1a24c-f353-4e4e-9dc0-36ce5cee8932/kick13.rom
TARGET=amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8
.venv/bin/python -m amiga_reversing.tools.copperline_session \
  --target "$TARGET" --rom "$COPPERLINE_ROM" \
  --direct-payload-contract pandora \
  --scenario runtime/scenarios/pandora-relocation-entry.json \
  --state-directory .runtime-state/copperline/relocation \
  --continue-seconds 30 --run
```

Repeat with `pandora-gameplay-entry.json` or
`pandora-world-object-callback-queue.json` and a distinct state directory.
`pandora-nearby-interaction-callback.json` waits for the entry officer's card
transfer, counts nineteen downward and twenty rightward movement commits, then
captures A5 and SR at the indirect interaction call and its return. Fire is
released at UI initialization; movement starts only after the card store.
Omit `--run` to inspect the resolved launch/scenario plan. Each runtime owns an
isolated temporary configuration, dynamic loopback endpoint and token; it exits
on completion or exception. No fixed port, shared config, Wine or GUI is used.
Canonical target analysis can take around a minute before/after a run; each
emulator run phase has its own wall deadline.

Source-row phases may specify `occurrences` from 1 to 64. One `wait_seconds`
budget covers all visits. A single instruction executes when departure from the
already-paused PC is needed, preventing an immediate same-PC match from being
counted again. Every visit must match original payload bytes and the canonical
source mapping. The report retains the last accepted capture on an incomplete
phase; `capture_first: true` also retains the first capture. Input remains held
through the counted visits and is released at the named phase boundary or on
failure. Visit counts alone do not establish a gameplay effect; this route also
checks observed coordinates at its completed-move checkpoint `0x9844`.

`--copperline` takes precedence over `COPPERLINE_BINARY`, the configured runtime
path and PATH. The tool registry now exposes `copperline`; legacy `winuae` paths
are ignored with a warning and never reused for a different executable.

## Dependency and input provenance

The official [Copperline 1.0.0 release](https://github.com/CopperlineHQ/Copperline/releases/tag/v1.0.0)
AppImage was verified against its published SHA256SUMS before extraction:
`9ab3e2ecc89beb25344bd1b0d8aa3dcf9370ade8f3b08fdec2fb37e59461f55d`.
The extracted executable is selected explicitly; binaries are not vendored.
Startup requires authenticated protocol 1 and emulator version `copperline 1.0.0`.
See the release's `docs/control.md` for protocol details. Future versions require
explicit compatibility verification before changing the version check.

The existing user-supplied Kickstart attachment is readable: 524288 bytes,
version 34.5, identical 256 KiB halves, SHA256
`1d68ba18412501d2a4b307a0a632b94a50b839c2c7c5ff2df6de2c38b99a921f`.
No ROM was downloaded or copied into this repository. Its prior omission from
the initial environment inventory was an inspection error, not a missing input.

The existing decoded Pandora target contains 376832 bytes, SHA256
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`,
matching the existing contract. It is loaded at `0x20000`; the runtime verifies
the entire loaded payload before releasing `HAND` at `0x7fff8` with `GO!!`.
Pandora then relocates to the previously observed `0x10000` view. No target
facts or source files are edited by the session.

The original Pandora ADF remains absent: `Pandora (1988)(Firebird).adf`, 901120
bytes, SHA256 `7f225192a177d9c06c54a99210de801ab0c840d4773bd99031aed5c7741a1c95`.
Original disk-image and loader parity are explicitly excluded by the user from
this task. The absent image is historical input context, not a blocker or a
required next step; direct-payload scenarios do not require it.

## Preserved contracts and deliberate changes

- Canonical stable keys resolve to reviewed observation views. Unique bytes and
  expected source offsets must agree at a hit; stale/ambiguous mappings fail.
- `enter_function` requires an exact accepted named contiguous function entry.
  Host-side JSON metadata replaces disposable ELF/DWARF; no GDB backend remains.
- Input port0/port1 maps to Copperline physical port1/port2; fire maps to red.
  Full held state is sent, overlapping holds remain active, and cleanup releases
  both ports even after failures.
- The gameplay scenario now releases fire at UI initialization, using the
  already established queue scenario's phase boundary. Removed obsolete timed
  event fields. This is an explicit scenario correction, not timing equivalence.
- The old duplicate continuation on `enter_function` is removed.
- Register and bounded absolute/register-relative memory capture, stack return
  address, NDK Exec/task/process inspection and optional DOS LoadSeg observation
  remain host-side reads. Invalid OS structures are reported as unavailable.
  Scenario register capture accepts D0-D7, A0-A7 and SR (at most seventeen names).
  SR exposes the observed carry bit; register-relative memory still requires an
  address register. This adds no debugger write or execution-control capability.
- Injected handoff writes create a new reverse-history anchor. Snapshot/reverse
  controls are internally available; host filesystem effects are not rolled back.
- Timeout handling pauses and drains the same control stream. Unexpected stops
  and identity mismatches cannot become successful phase results. Owned emulator
  processes are shut down, then terminated/killed with bounded waits if needed.

## Validation

Focused and real-run results are recorded in the final validation section below.
Transport synthetic tests cover memory/register writes, stepping, repeated
lifecycle, breakpoints, snapshot restore, input, deadline recovery, malformed
responses, auth redaction and cleanup. They are distinct from target scenarios.

```sh
COPPERLINE_BINARY="$COPPERLINE_BINARY" COPPERLINE_ROM="$COPPERLINE_ROM" \
  .venv/bin/python -m pytest tests/test_copperline_control.py \
  tests/test_copperline_runtime.py tests/test_copperline_session.py \
  tests/test_runtime_symbols.py tests/test_direct_payload_adapter.py \
  tests/test_tool_graph.py tests/test_tool_registry_cli.py -q
```

The baseline native/UI architecture, build instructions and broader pre-existing
test failures are in [the initial Linux assessment](linux-baseline-2026-10.md).

### Cloud results, 2026-10-11

- Relocation: handoff observed in about 6 seconds; all 376832 loaded bytes
  verified; breakpoint `0x1046a` uniquely maps to source `0x46a` and base
  `0x10000`. Public PC resolution reports `mapped`.
- Gameplay: title `0x10ba8`, UI initialization `0x1079e`, gameplay `0x105d6`,
  and `handle_inventory_panel_input` at `0x128d4` all hit with unique payload
  identities. Named function acceptance and register-relative capture worked.
- Single public stable-key breakpoint: `hit` at `0x1046a`. Standalone direct
  observation releases the handoff, re-anchors history and observes unique
  payload execution (`0x10c84` in this run).
- Queue scenario: title, initialization and enqueue `0x166a0` hit. The requested
  queue-processing entry `0x16676` did not hit in either a 20-second window or
  a separate 60-second diagnostic window. The latter returned `incomplete`,
  paused at `0x16854`, released inputs and exited its emulator. Historical
  WinUAE documentation establishes enqueue reachability but does not establish
  a complete queue-processing run. This result is a remaining behavioral
  question, not evidence of a proven emulator regression or complete parity.
- Independent review exercised actual Copperline/Kickstart transport and
  identified eight mapping/lifecycle integration issues; all were corrected
  and re-reviewed. No blocking findings remained for validated scenarios.
- Final focused suite: **85 passed**, including real Copperline/Kickstart
  lifecycle/control probes. The transport suite also passed with bundled AROS.
- Default pytest: **1426 passed, 64 skipped, 355 deselected, 1 failed**. Failure
  remains the absent Mac fixture `resources/platform_macos/MPW-GM.img.bin`.
  Skips/deselections are not untested-pass claims. The initial native C and
  integration failures remain as documented in the baseline assessment.
- Real browser smoke after server restart: imported a synthetic HUNK, rendered
  native rows, reproduced exact bytes with both C and external vasm, and checked
  Chromium DOM/page errors. Screenshot: `.runtime-state/linux-smoke/ui.png`.
  Local URL: `http://127.0.0.1:8123/amiga_hunk_cloud-smoke-7`.
- Pandora exact source roundtrip was attempted. The raw output path incorrectly
  passed HUNK-only `-kick1hunks`; that invocation is now scoped to HUNK output
  and covered for both formats. At the migration baseline, freshly rendered Pandora source assembled,
  but yielded **376846 versus 376832 bytes**, first difference **0x497**. Renderer
  and target sources/facts were not changed in this migration. That historical mismatch was resolved by the
  [zero-field renderer fix](validation/zero-field-renderer-fix-2026-10-12.md):
  fresh source now reproduces all 376832 bytes exactly and the rebuilt payload
  passes the gameplay scenario.

Runtime result files are local `.runtime-state/copperline-*.json`; logs remain
small and no instruction trace was retained. All owned emulator processes were
closed after testing, including the initial assessment process. The web service
continues on loopback port 8123; it is not publicly hosted or forwarded.

Queue-processing reachability remains a separate investigation; no queue
correction is included in the renderer fix. Original-loader comparison is outside
the current scope. Windows execution of the replacement has not been tested here.

The [shared restoration validation](validation/restoration-framework-2026-10-12.md)
now also proves full-target C and vasm exactness after a real evidence-bearing
Pandora source change, with rebuilt-file gameplay checkpoints and review receipts.
