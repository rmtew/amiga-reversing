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

## Keyboard-region baseline and derived layout contract

`runtime/scenarios/pandora-keyboard-state.json` observes reset, title/UI entry and
normal gameplay reads, then holds/releases raw Amiga keys 11 and 12. Phase-bound
`key N` controls use `input.key` with bounded press/release and cleanup. Capture
reads can use `region_id`, nonnegative `offset` and `size` (1..64); compilation
resolves the native original extent, or the validated derived manifest placement.
Absolute reads remain available as independent old-address guards.

In this saved cloud environment, reproduce the original-layout baseline:

```sh
cd /workspace/amiga-reversing
.venv/bin/python -m amiga_reversing.tools.copperline_session \
  --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 \
  --rom /workspace/attachments/30c1a24c-f353-4e4e-9dc0-36ce5cee8932/kick13.rom \
  --copperline /workspace/copperline-assessment/squashfs-root/usr/bin/copperline \
  --direct-payload-contract pandora \
  --scenario runtime/scenarios/pandora-keyboard-state.json \
  --state-directory .runtime-state/pandora-analysis/keyboard-relocation/reproduce --run
```

A closed `memory_build` manifest can be passed as `--derived-artifact`. Binding
recomputes the native proof and checks the exact rewrite ledger and both payload
hashes. The shim reserves marker storage first, then the entire input and declared
destinations **before CMD_READ**. Overlapping input/destination leases are merged;
there are no allocator calls or frees after loading. Marker-allocation failure
holds without writing; later failures publish FAIL without payload release.

Mapped-source initialization requires a hash-bound `materialization` contract:
source offset/size, copied runtime address, exact entry source offset and explicit
`source_consumed_at_entry: true`. Binding checks the native materialized view and
entry instruction. The runtime verifies all loaded input at HAND, stops before
the declared game entry, verifies the entire copied image, then writes/reads back
only the logical region bytes and anchors reverse history. This runs before every
scenario, single breakpoint or free-run path. It is one cold-bootstrap operation,
not repeated on warm restart. An input-overlapping destination must fit wholly
inside the consumed source interval and outside copied game storage and markers.
The contract asserts no later reads of that consumed input; full-copy equality
does not prove this lifetime assertion for arbitrary loaders.

Pandora declares its native `$55370`-byte copy to `$10000`, ending before entry
`$1046A`; initialization must not occur while the input at `$20000` is still live.
The volume's logical two bytes use an eight-byte lease. Accepted native owner
regions, runtime equates and materialized views reject conflicting destinations.
Keyboard's five pointer/frame obligations remain open. No original-disk-loader
parity is implied. `capture.custom_registers` accepts at most sixteen names or even numeric offsets
below `$200` and uses Copperline's read-only `custom.read`, including the stored values of
write-only Paula registers; CPU memory reads of those addresses are insufficient.

For the volume comparison, use the command above with
`--scenario runtime/scenarios/pandora-audio-volume-relocation.json` and a distinct
state directory. Add `--derived-artifact <manifest.json>` for the changed layout.
The current saved-environment manifest is
`.runtime-state/restoration/derived/e449f89c0ec6e432b070bdf0809c405958be12a2119909c502f3d135561f666c/manifest.json`.
To rebuild it, run a fresh `verify`, then revision-checked `memory_build` for
`region_id: "audio_master_volume"`, `destination: 414720`, `memory_class: "chip"`
with that verification receipt. This initial scenario intentionally finishes
`incomplete` at its short writer watch; its eight prior hits establish read/output
parity. The follow-up `runtime/scenarios/pandora-volume-proximity-writers.json`
uses ordinary joystick input and completes 21 canonical phases in both layouts,
covering the D0 WORD volume writer, immediate WORD reset and sampled AUD3VOL=2
at volume 6. The old-address guard remains `0040` in the derived run. Use the same
command/manifest with that scenario and separate `--state-directory` values.
[Compact writer observations](../runtime/observations/pandora-volume-proximity-writers.json)
record the comparison. The original eight-phase
[observations/ledger](../runtime/observations/pandora-audio-volume-relocation.json)
remain historical receipts.

`runtime/scenarios/pandora-volume-feed-combat-probe.json` uses the same command,
with a separate state directory. It reaches the Feed, opens inventory using
`key 64` (Space), swaps the selected officer ID for an empty carried slot and uses
six charged fire presses to defeat it. Both layouts hit all 46 canonical phases.
The final capture establishes defeated flag bit 1 set and shared audio flag bit 0
clear: combat already reset that flag and restored volume `0040`. The BYTE writer
therefore remains uncovered; both flags must be set to enter it. The next work is
a normal flag-setting route after defeat or a static reachability assessment,
not a forced game-state write. Keyboard-buffer relocation remains deferred.

Canonical copied-view PC samples near the view end include preceding bytes so the
whole minimum 16-byte sample stays materialized. Offset/base validation and full
input/copied-image identity checks remain unchanged. Declarative scenarios permit
2..64 phases including handoff, producing at most 63 executable phases within the
runner's existing cap of 64; input-event holds remain capped at 32 in the compiler.


## Pandora's bounded world model

The remaining BYTE volume path is a static candidate: a direct rifle kill can
preserve the armed shared flag until the same-frame proximity update. Full combat
clears it first. Weapon acquisition/aim and nearby-event predicates remain
unvalidated, so this is not all-writer completion.

The read-only model uses native symbol coordinates/opcode values, effective
record schemas and the exact original payload. It reconstructs terrain, movement
poses, bounded original script patrols and the scenario dependency chain. The
provided checkpoint predicts the pianist encounter and validates the next UI/
movement transition. It does not treat a timeout's last successful capture as the
state at timeout or assign a register role before the relevant binding executes.

With the existing listing server running, regenerate the offline model **without
launching Copperline**:

```sh
.venv/bin/python -m amiga_reversing.tools.pandora_world_model \
  --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 \
  --observation runtime/observations/pandora-world-model-checkpoint.json \
  --output /tmp/pandora-world-model.json
```

[Saved model](../runtime/observations/pandora-world-model.json) includes a compact
excluded-tile grid, native source bindings, 35 original object identities/script profiles, the
validated pianist encounter and explicit unknowns. Only that observed actor's
patrol is currently enforced by the route search. Its whole swept envelope leaves
no admitted rifle route under this model; that is not a real-game impossibility
proof. The model derives a conditional staging goal `(780,794)` with eight-move
checks and refuses to assume a safe crossing without timing/interaction evidence.

`runtime/scenarios/pandora-world-model-transition.json` is the existing bounded
normal-input diagnostic that captures canonical combat entry `$7792` and subsequent
movement rejection `$9984` (ten source phases). It validates the model's specific
counterexample, not a weapon acquisition or BYTE write. Use the normal public
Copperline CLI, legal ROM, original direct contract and a separate state directory
if reproducing it; no repeat is needed merely to inspect the saved receipts.
`pandora-volume-byte-route-blocker.json` preserves the earlier rejection-only
observation. All owned emulator processes have exited after capture.

Alternative canonical stop outcomes remain a framework gap. Memory captures now
support `expect_hex` and optional `expect_mask_hex`, each exactly `size` bytes
encoded as hex. They are checked after canonical PC/payload verification at every
counted visit. A mismatch records `capture_expectation_mismatch`, ends the
scenario and releases held input. A transition that never reaches the requested
PC still stops at the phase deadline; assertions do not provide an alternative
early breakpoint. Verified local checkpoints are described below; older raw `state.save/load`
transport snapshots do not establish that provenance contract. The previous successful WORD/Paula comparison remains unchanged.


## Pianist timing and guarded crossing

The original-layout timing diagnostic reaches `(780,794)` in the predicted 95
accepted moves. Five subsequent source `$5CA` observations validate one pianist
script update per gameplay loop: Y=834,832,830,828,826, with matching script PC,
delay and all six mutable repeat counters. The outer source `$253C` loop skips
flags `&$42` before decrementing delay; source `$13F4` dispatches on the call that
reaches zero. Delay 1 therefore advances next call, delay 2 every second call.
The original admitted script has a 377-call cycle, including its 30-call rest.
These are gameplay-loop calls, not assumed PAL frames or accepted player moves.

Camera scrolling inserts movement pauses. Known camera profile writers select
0/1, with reloads 4/6. The bounded crossing model checks every possible elapsed
actor call for each pose under 1..6 calls per accepted move, including initial
input latency and the waiting interval before the following move. It rejects the
immediate crossing and instead waits 249 calls from `timing_loop_4` to the start
of the rest at `(816,974)`, script `$1F2C`, delay 30. The gate's exact player/actor
state is checked before pressing right.

The model-derived corridor route is right 6, down 1 (lateral drift), up 14, right
7. Every accepted position is asserted, rather than assuming counted movement
remains on course. All 28 moves passed in real Copperline, ending `(864,738)` with
UI mask 6 clear. Captured actor states match 49 eligible calls, with each
inter-move delta within 1..6. Proximity flag bits 4/5 change separately and are
not mistaken for interpreter timing state.

The pure model is `amiga_reversing.tools.pandora_patrol_timing`; evidence is in
`runtime/observations/pandora-pianist-{timing,crossing}.json`. Reproduce with the
normal CLI command above, replacing `--scenario` with
`runtime/scenarios/pandora-pianist-timing.json` or
`runtime/scenarios/pandora-pianist-crossing.json` and using a fresh state directory.
This earlier diagnostic starts from boot; the new segments below use verified
local checkpoints. These are original-only
observations: the rifle pickup, direct hit, BYTE writer and relocated comparison
remain separate gates. The next corridor contains the flight controller's patrol
at X=1104; its live state must be admitted before that crossing.

The follow-up `pandora-corridor-actors.json` scenario repeats the qualified prefix
and stops at the same player coordinate. Its 61 canonical phases pass (62 total
including handoff). It samples all 35 object records over three successive loop
visits, then takes three consecutive flight-controller captures. The same
interpreter predicts `(1104,746),delay1` → `(1104,748),delay2` →
`(1104,748),delay1`, including all six live repeat counters. These snapshots are
not atomic global state or bounds for every unknown callback.

The next unexecuted staging candidate is right 30 to `(1074,738)`, west of the
flight-controller interaction envelope. A reliable rifle route still needs its
timed crossing composed with camera pauses and normal pickup prerequisites. The
security officer at `(1234,840)` is another nearby interaction predicate; its
original script holds XY and toggles animation, which does not by itself prove
that interaction harmless. Empty-slot selection and a fresh proximity latch must
be admitted before pickup. The return path, accepted aim and direct ray hit are
subsequent model gaps. This checkpoint stops before those assumptions.

Focused verification for this checkpoint:

```sh
.venv/bin/python -m pytest -q \
  tests/test_pandora_patrol_timing.py tests/test_pandora_world_model.py \
  tests/test_copperline_runtime.py tests/test_copperline_session.py
```

Result: **112 passed**. Native/control suites and full source round-trip were not
repeated: no target facts or generated source changed, and the original
binary/source hashes and prior WORD receipt are checked unchanged. No owned
Copperline process remains running. The existing listing server remains on
loopback port 8123. Native canonical scenario compilation remains the dominant
probe cost (roughly a minute or two here); the timing model itself runs offline.


## Verified checkpoints and normal rifle pickup

`--checkpoint-save <fresh-name.json>` saves a local `.clstate` plus receipt after
a complete canonical scenario, after acknowledged input cleanup. `--checkpoint-load` requires
a scenario beginning with `verified_checkpoint`, then a single-visit canonical
anchor at the saved source PC. Before loading, the runner checks the snapshot
hash, target/payload, ROM, emulator, fixed profile, media, derived-manifest and
runtime-view binding. After loading, every saved CPU register and the canonical
PC payload sample must match before execution/input. Reverse history is anchored
after load; replay across it is not evidence. Existing destinations are refused.

Root receipts preserve the full input/copied-image verification from boot. Resume
reports explicitly mark that root verification as inherited, rather than claiming
a new handoff. Each successor records its parent snapshot hash. These are local runtime artifacts with content/context checks; cross-machine
portability has not been validated. Snapshots contain private guest
machine state and stay in ignored `.runtime-state`; none are committed. Each
original/relocated layout needs a separate root and chain. An original checkpoint
cannot be loaded with the relocated payload/manifest.

A real fresh-process chain now passes:

| Segment | Canonical phases | Result |
|---|---:|---|
| Existing corridor prefix | 61 | Fresh verified root at `(864,738)` |
| `pandora-rifle-west-staging.json` | 32 | 30 exact moves to `(1074,738)` |
| `pandora-flight-model-crossing.json` | 30 | 28 exact moves to `(1130,810)`; admitted live patrol gate |
| `pandora-rifle-approach.json` | 38 | 30 exact moves to `(1214,874)`, normal empty-slot selection |
| `pandora-rifle-pickup.json` | 5 | Two moves enter pickup radius; source `$811E` confirms item 18 |
| `pandora-rifle-checkpoint-audit.json` | 2 | Fresh-process restore and one idle loop; cached movement/fire remain zero |

At the approach, Space opens inventory, fire swaps selected card 54 into the first
empty carried slot, fire is released, and Space closes the panel. The final gate
checks selected item 0, UI mask 6 clear, fire 0 and a clear receptacle latch.
Movement changes pickup distance 37→30→23; the strict `<28` test and fresh latch
then copy rifle ID 18. Final state is `(1228,874)`, selected 18, HP 95, ammo `05,01`,
carried bytes `36000000`, receptacle `00058a481201`, volume `0040`, shared audio
byte `00`. The rifle-bearing snapshot is saved. No guest predicate was edited;
subsequent segments resumed exact saved execution instead of replaying the prefix.

For this environment, use the existing legal ROM path and pinned Copperline.
Create a fresh root once (choose a new local directory if these files exist):

```sh
pandora_target=amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8
pandora_run=.runtime-state/pandora-rifle-reproduction
pandora_rom=/workspace/attachments/30c1a24c-f353-4e4e-9dc0-36ce5cee8932/kick13.rom
pandora_emulator=/workspace/copperline-assessment/squashfs-root/usr/bin/copperline
.venv/bin/python -m amiga_reversing.tools.copperline_session \
  --target "$pandora_target" --rom "$pandora_rom" --copperline "$pandora_emulator" \
  --direct-payload-contract pandora --state-directory "$pandora_run/root" \
  --scenario runtime/scenarios/pandora-corridor-actors.json \
  --checkpoint-save "$pandora_run/corridor.json" --run

.venv/bin/python -m amiga_reversing.tools.copperline_session \
  --target "$pandora_target" --rom "$pandora_rom" --copperline "$pandora_emulator" \
  --direct-payload-contract pandora --state-directory "$pandora_run/west" \
  --scenario runtime/scenarios/pandora-rifle-west-staging.json \
  --checkpoint-load "$pandora_run/corridor.json" \
  --checkpoint-save "$pandora_run/west.json" --run
```

Repeat the second command with these arguments, retaining the same media/payload:

| Scenario | Load receipt | Save receipt | State subdirectory |
|---|---|---|---|
| `pandora-flight-model-crossing.json` | `west.json` | `east.json` | `east` |
| `pandora-rifle-approach.json` | `east.json` | `ready.json` | `ready` |
| `pandora-rifle-pickup.json` | `ready.json` | `rifle.json` | `rifle` |
| `pandora-rifle-checkpoint-audit.json` | `rifle.json` | `rifle-clean.json` | `audit` |

[Compact receipt](../runtime/observations/pandora-rifle-composition.json) contains
all phase outcomes, snapshot-parent hashes, inventory/pickup captures, the flight
patrol comparisons and the unexecuted return/aim assessments. Native scenario
compilation took about 95–98 seconds per new segment here; saved-state reuse
removes repeated gameplay prefixes, not that separate compilation cost.

**Earlier BYTE gap (superseded by the camera/clearance assessment below):** the terrain model finds a conditional 382-move return to
`(808,154)`, but it crosses both patrol corridors in reverse. For the 45-move
reverse flight corridor, none of 377 original patrol-cycle gates is admitted by
the conservative 1..6-call-per-move windows. This is a model limitation, not an
impossibility claim. Before running the return, derive tighter cumulative camera
pause bounds (or a different admitted reverse route), validate them against the
saved crossing receipts, and resume from the rifle checkpoint. The forward
crossing proof does not qualify its reverse.

A read-only restore of the rifle state captures the live Feed descriptor at
`(840,168)`, geometry `$5C264`, zero state offsets, alive HP 29 and bounds
`[847,872)×[168,195)`. All six original animated frames share those bounds. The
provisional upward ray X=843 would miss them, and aligning that column encounters
a solid tile before the body. The revised terrain candidate finishes at
`(808,154)` after an accepted right move, safely outside the strict encounter box.
Decoded ray arithmetic gives first point `(850,168)`, inside the captured body.
Its tile 450 is clear; the nearby live cells match the original map. This remains
a conditional aim: future active-list membership, live geometry/flags, fire edge,
ammo, prior alive proximity arming and callback preservation need validation at
the firing point. No return, aim, hit, BYTE write or relocated weapon comparison
was executed.

The first read-only map capture stopped on an incorrect `$8880` base assumption;
that was an earlier sampled-cell address. The corrected capture verifies the live
base `$4000` before interpreting cells. It reused the unchanged compiled canonical
row/mapping and revalidated only the revised bounded capture, taking 0.2 seconds
without a native rebuild or gameplay advance. Both the stopped guard and corrected
receipt are retained. `pandora-feed-ray-state.json` reproduces the read-only
inspection from the rifle checkpoint; omit `--checkpoint-save` for that command.

Focused checkpoint/runtime/session/patrol/model/transaction suite: **134 passed**.
Original binary/source and prior WORD receipts remain unchanged. Native/control
suites and full reassembly were not repeated because target output is unchanged.

## Camera timing resolved; return blocked by ID clearance

Continue from the verified rifle checkpoint above, without replaying acquisition.
`pandora_camera_timing` models the mutable movement-script delay: horizontal
requests write two at source `$9680`, vertical requests write one at `$96AA`,
and idle dispatch writes one at `$999C`. Camera service `$7D48..$7DA4`
decrements its countdown before movement; expiry clears the active bit/deltas.
Profile 1 has reload six and margins 32/16. Its interior burst shifts 80 pixels
and adds at most five calls. These are gameplay-loop bounds, not wall-clock rates.
The bound requires a fixed profile, accepted axis moves and no modal encounter,
wrapping or external script change.

Seven real neutral transitions agree exactly, including scroll, countdown
`5,4,3,2,1,0,255,254`, and delay two becoming one. The previously qualified
forward flight crossing takes 41 eligible calls within the new cumulative bound
45. A reverse diagnostic reaches all 45 predicted positions in 64 calls within
bound 68, with two vertical bursts. This validates timing only: the first
diagnostic checked health at its end and found 44 rather than 95. The stronger
published recipe guards HP at every wait/movement visit and stops at
`reverse_34_up`; subsequent phases and snapshot save do not run.

A separate bounded prefix stops at canonical source `$887C`, before the health
store: HP is still 95, D0 contains 44, A5 identifies the player and the nearest
NPC is the flight controller. The decoded security response subtracts 51 when
the held ID fails clearance. Zone is zero; accepted item IDs are 48 through 53
with tiers `[4,3,1,3,0,2]`, requiring tier greater than zone. Selected rifle 18
fails, and carried Amy ID 54 is outside that range. Swapping back to Amy is
therefore insufficient. A stationary ten-second probe did not hit the response;
that negative result applies only to its parked window.

The intact rifle checkpoint remains at `(1228,874)`, HP95, rifle18, ammo `05,01`.
A separately verified staging checkpoint is at `(1137,874)`. No successful return
checkpoint, firing-point qualification, hit, normal BYTE execution or relocated
weapon comparison is claimed. Acquiring another valid ID/trade would expand
this two-byte relocation test into another game quest, so gameplay work stops
at this explicit boundary.

[Bounded camera/clearance evidence](../runtime/observations/pandora-camera-return-boundary.json)
records successful timing observations separately from the failed health guard.
From the existing rifle receipt, use the same public checkpoint CLI above with:

| Scenario | Load checkpoint | Save checkpoint |
|---|---|---|
| `pandora-camera-idle-observation.json` | rifle-clean | fresh neutral receipt |
| `pandora-reverse-flight-staging.json` | neutral receipt | fresh reverse-stage receipt |
| `pandora-reverse-flight-crossing.json` | reverse-stage receipt | omit (expected HP refusal) |
| `pandora-reverse-security-damage.json` | reverse-stage receipt | omit (before-store inspection) |
| `pandora-rifle-security-response.json` | rifle-clean | omit (parked timeout) |
| `pandora-volume-routine-context.json` | rifle-clean | omit (read-only CPU donor) |

Each command still needs a fresh isolated `--state-directory`; checkpoints and
guest snapshots remain ignored local inputs. The camera probe's neutral successor
is the staging donor; do not silently substitute a state with different timing.

## Cheaper local BYTE contract and simulator boundary

The provenance-preserving CPU-only tool validates the original payload, closed
two-byte relocation manifest and a read-only canonical `$5CA` donor. Live routine
bytes match the original. Original/derived code and bounded captured cells are
projected into separate local memories; unobserved cells use the original image
or zero. Synthetic call frames and modeled guard inputs never enter Copperline.

The actual manifest BYTE instruction at source `$552F0` passes **all 65,536
initial 16-bit words**: exactly one byte write at the respective volume address,
output `0x4000 | (input & 0xff)`, equal registers/CCR/PC, preserved low byte and
adjacent guards. This explicitly enters at the writer, excluding its guards,
reset helper, Paula and normal gameplay reachability.

Full-routine comparison is **refused**, including the captured natural guard:
the generated concrete simulator treats an unsized memory bit operand as a
longword despite the KB's existing EA-category byte rule. The BCLR flag write
spans four bytes rather than one. Equality under that defect is not a routine
proof. No routine case is accepted; no CPU semantics or generated backend was
changed. Proposal 044 records the required upstream binding fix and oracle
coverage. `machine68k` is not installed, so this is not independent CPU proof.

```sh
.venv/bin/python -m amiga_reversing.tools.pandora_volume_local_compare \
  --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 \
  --context runtime/observations/pandora-volume-local-context.json \
  --manifest .runtime-state/restoration/derived/e449f89c0ec6e432b070bdf0809c405958be12a2119909c502f3d135561f666c/manifest.json \
  --output /tmp/pandora-local-comparison.json
```

Expected exit **2** writes the partial result, not a successful routine verdict.
The manifest is the existing local derived-build output, not a published guest
snapshot. [Comparison receipt](../runtime/observations/pandora-volume-local-comparison.json)
and [bounded donor](../runtime/observations/pandora-volume-local-context.json)
retain hashes and explicit scope. Normal game writer coverage remains **two of
three**. No interrupts, hardware/DMA timing, storage ownership or allocation
claims follow from local CPU execution. Focused regression results and unchanged
target hashes are recorded with this slice in the restoration status.

## Generated EA-category width binding fixed

The initial four-byte bit-memory refusal above is retained as historical
negative evidence. The next framework slice fixes its source: execution metadata
now binds an EA operand with the existing `size_by_ea_category` rule to
`ea_category`, and generated simulator form metadata carries both byte widths.
The native width selector uses the decoded operand category even without a size
suffix. Reads, writes and EA updates consume that selector. Bit masks/flags use
the same generated category widths, replacing the old separate register/memory
width assumptions. The bit path also invokes the existing predecrement helper
before access; the new predecrement regression exposed that missing call.

Only the four affected execution bindings (BCHG/BCLR/BSET/BTST, including both
forms) were regenerated from preserved PDF-backed KB fields through the parser's
normal execution-metadata builder. No new instruction facts or Pandora-specific
CPU semantics were introduced. The simulator tables were regenerated, all native
consumers rebuilt, and the listing service restarted for the changed backend.

The [new comparison receipt](../runtime/observations/pandora-volume-local-comparison-width-fixed.json)
uses the same donor and full relocation manifest. Eight bounded local cases pass
normalized CPU state, writes and control-flow comparison. Five explicitly
modeled dead/armed calls enter the routine's real guard, execute the BYTE writer,
run the reset helper and return, 26 instructions per layout, for initial words
`0040,0006,01ff,aa55,ffff`. Outputs are `4040,4006,40ff,4055,40ff`.
These are complete guarded local calls, not observed game calls. The unchanged
65,536-word direct-store result is preserved exactly in both receipts.

The ninth case, alive/near/armed at `(808,154)`, remains **refused** on a separate
concrete ADD/SUB defect. At source `$55310`, `subi.w #840,d0` with D0 `$00070328`
and SR `$2000` should produce D0 `$0007ffe0` and SR `$2019`; the concrete direct
register branch instead produces `$0006ffe0` and leaves SR `$2000`. It operates
on the full register and omits data-arithmetic flags, causing BPL to skip NEG.
The local near case consequently gives volume 64 rather than 53. Even equal
original/derived results cannot satisfy the independent routine contract. The
runner records this as `refused_local_routine_contract`, continues independent
cases, writes the partial report and exits 2. Fixing general arithmetic semantics
is a separate framework slice; this width fix does not hide or bypass that gap.

Repeat the local comparison command above with
`--output /tmp/pandora-width-fixed-comparison.json`. It still exits **2**, now for
the arithmetic contract rather than bit-memory width. Build/check commands:

```sh
.venv/bin/python src/scripts/generate_c99_simulator_subset.py
make -j4 all
.venv/bin/python -m pytest -q src/tests/test_generate_c99_simulator_subset.py \
  src/tests/test_m68k_simulator_abstract.py tests/test_pandora_camera_and_local_compare.py
src/build/m68k_c_unit_tests.exe
```

The local ignored Linux Makefile supplies `make`; tracked Linux setup instructions
remain in `docs/linux-baseline-2026-10.md`. The metadata regeneration recipe/test
is recorded in Proposal 044. Native simulator tests pass all 29 cases, including a
64-combination concrete bit matrix; abstract tests add 32 bit-operation subtests.
The broader focused run passes176 tests plus32 subtests. Full native tests retain
the two independently documented baseline failures in pointer-table pointee
propagation and unknown decompression identification. The changed C/header/table
files pass style checks; the repository-wide style test still reports violations
in 24 unchanged files. Full-image rendered-source roundtrip remains exact with no
differing ranges. No independent machine68k CPU oracle is installed.

Clearance-ID route expansion stays paused. Normal gameplay BYTE coverage remains
unobserved, and normal game writer coverage stays two of three. The intact rifle
checkpoint, source/binary bytes and earlier WORD evidence are unchanged. The UI
continues on loopback `http://127.0.0.1:8123/`; no emulator is running.

After restart, Pandora's native listing reload completed with 42,219 rows and a
successful three-row listing API read (web app contract header 2). The global
project index retains its independently documented local baseline 404:
`Missing .project.json for project: amiga_hunk_large`. No unrelated target
metadata was changed to repair that selector; direct Pandora project/listing
requests succeed. See the existing server baseline classification under local
`.runtime-state/pandora-analysis/performance-c8f6/`.

## Concrete arithmetic corrected; nine bounded routine cases pass

This supersedes the arithmetic refusal above. A minimal native regression first
reproduced `SUBI.W #840,D0` (`04400348`) with D0 `$00070328` and SR `$2000`:
the old concrete path produced `$0006ffe0`, corrupting the upper word, and left
CCR unchanged. It now produces `$0007ffe0` and SR `$2019`. The shared concrete
ADD/SUB path uses existing generated operand-width/CCR metadata, the existing
source-extension arithmetic helper and sized destination writer. Data-register
upper bits and memory neighbours are preserved; address-register destinations
retain full-width arithmetic and unchanged SR. Immediate, register, quick and EA
forms share the correction, including existing pre/post access update helpers.
No Pandora-specific instruction branch or new CPU fact is introduced.

The boundary matrix exposed an adjacent upstream form-binding error: reversing
`<ea>,Dn` into `Dn,<ea>` retained a register-only destination access. The parser
now normalizes register-to-EA accesses as well as EA-to-register accesses. Seven
stale access bindings were regenerated from preserved extracted KB fields:
ADD/AND/OR/SUB destinations and three PMOVE source forms. Generated simulator
tables were regenerated too. PMOVE execution support is not added by correcting
its metadata. Generator tests verify reproducibility and category normalization;
concrete AND/OR memory checks cover the shared reversed-form correction.

[Arithmetic-fixed comparison](../runtime/observations/pandora-volume-local-comparison-arithmetic-fixed.json)
uses the same verified donor and complete relocation manifest. All nine bounded
calls now satisfy their independent contracts and original/derived normalized
CPU state, control-flow and write comparisons. The near-player case at `(808,154)`
executes both required NEG instructions, returns in 21 instructions and writes
volume `$0035` (53). The five modeled dead/armed BYTE calls still return in 26
instructions each. The exhaustive 65,536-word direct-store result is identical to
both historical receipts, which remain unmodified. The CLI now exits **0** with
`bounded_local_routine_and_BYTE_equivalence`; this is a bounded CPU verdict, not
normal game reachability or unrestricted routine equivalence.

Run the local-comparison command above with
`--output /tmp/pandora-arithmetic-fixed-comparison.json` (expected exit 0).
Focused arithmetic tests use generated assembly and explicit boundary vectors:

```sh
.venv/bin/python -m pytest -q src/tests/test_m68k_simulator_arithmetic.py \
  src/tests/test_generate_c99_simulator_subset.py \
  src/tests/test_m68k_simulator_abstract.py tests/test_pandora_camera_and_local_compare.py
.venv/bin/python src/scripts/check_c_style.py src/m68k_simulator.c \
  src/test_m68k_simulator.c src/generated/m68k_simulator_tables.h
src/build/m68k_c_unit_tests.exe
```

The full focused run passes 190 tests plus 1,004 subtests. The new arithmetic tests
cover byte/word/long signed overflow, zero/negative results, carry/borrow/extend,
non-CCR SR preservation, Dn upper-bit and memory-neighbour preservation,
immediate/register/quick forms, EA pre/post updates, address-source extension
and 32-bit address wrapping. End-of-memory byte access succeeds; invalid word
access/predecrement stops without a completed instruction or memory write.
Refused execution may retain prepared EA register updates; no rollback guarantee
is assumed. Native simulator 30/30 passes; the full native suite still fails only
the two documented pointer-table-pointee and unknown-decompression baseline
cases. Changed C/header/table style and full-image exact roundtrip pass, with no
differing source ranges. The independent machine68k oracle remains unavailable.

The service is restarted for the rebuilt backend and Pandora's listing reloaded.
Original binary/source, relocation manifest, WORD evidence, historical local
receipts and rifle checkpoint are preserved. No emulator/gameplay run was added.
Clearance gameplay stays paused, and normal game BYTE execution remains unobserved.

Final reload check: 42,219 Pandora rows, successful three-row listing API read.
All 121 preserved-KB execution entries reproduce through the normal builder;
only the seven documented access kinds differ from the previous commit. The
previous global-project-index orphan-metadata error remains unrelated.

### Snapshot lifecycle observation

`runtime/scenarios/pandora-overlay-clear-order.json` stops around the initial
panel clear and CPU border/text work. `custom_registers` numeric offsets `$002`,
`$01C` and `$01E` obtain live DMACONR/INTENAR/INTREQR through `custom.read`.
The pinned runtime refused the named DMACONR query, while debugger `memory_reads`
of custom-register addresses returned `FFFF`; those memory values were discarded
as hardware-status evidence. The narrow adapter addition accepts only names or
even offsets below `$200`, with the existing sixteen-register limit.

The initial clear run reaches every canonical stop and then gameplay with the
original payload identity verified. BBUSY is clear and BLIT request set at the
first stop after BLTSIZE, border entry/exit and READY marking. BLITHOG remains
set. This observes completion in this initial panel case; it does not establish
all geometry, gameplay-display contention or arbitrary CPU/DMA ordering.
See `runtime/observations/pandora-snapshot-lifecycle.json` for the compact receipt
and `docs/validation/pandora-snapshot-lifecycle.json` for conditional contracts.

The connected gameplay probe composes snapshot stops into the existing successful
Feed input route, without duplicating its full scenario or editing guest state:

```sh
.venv/bin/python -m amiga_reversing.tools.pandora_snapshot_lifecycle_scenario /tmp/pandora-snapshot.json
.venv/bin/python -m amiga_reversing.tools.copperline_session \
  --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 \
  --rom /workspace/attachments/30c1a24c-f353-4e4e-9dc0-36ce5cee8932/kick13.rom \
  --copperline /workspace/copperline-assessment/squashfs-root/usr/bin/copperline \
  --direct-payload-contract pandora \
  --state-directory .runtime-state/pandora-snapshot-reproduction \
  --scenario /tmp/pandora-snapshot.json --run > /tmp/pandora-snapshot-result.json
```

Use a fresh state directory. The recorded run is **partial**, not an all-phases
success: hit capture, six Feed hits, combat-exit restore and return to gameplay
are observed. Correction: the subsequent timeout watches `$27E0`, a trade
announcement, rather than body entry `$27EA`; it is not negative body-entry
evidence. Later scripted body phases do not run. Next capture nearest-object pointer, collision
carry and object bit1 at inventory guards `$2736/$2748/$274A`; a timeout does not
identify which guard failed. Second combat recapture and hit-tail palette reuse
remain unobserved. Snapshot sample hashes and hardware values in the compact
receipt are observations, not complete lifetime/alias guarantees.

### Body inventory guard and recapture stages

The snapshot scenario composer also supports `--stage root`, `--stage guards`
and `--stage body`. Root replays the established Feed encounter and ends at
post-combat `$5CA`; save it with `--checkpoint-save`. Guards resumes that root,
uses key64, and stops after resolving the original descriptor/state/geometry
pointers at `$26A4`; optionally save that diagnostic checkpoint separately.
Body resumes the **root**, not the partly opened guard checkpoint. Direct up
movement is terrain-blocked; the stage checks an 18-move local route to
`(822,146)`, then probes canonical body entry `$27EA`, capture, restore and
recapture. The route derives from the existing terrain model and is checked at
each commit. The previous `$27E0` probe was a trade-announcement instruction.

Generate each stage with the public composer:

```sh
.venv/bin/python -m amiga_reversing.tools.pandora_snapshot_lifecycle_scenario --stage root /tmp/pandora-body-root.json
.venv/bin/python -m amiga_reversing.tools.pandora_snapshot_lifecycle_scenario --stage guards /tmp/pandora-body-guards.json
.venv/bin/python -m amiga_reversing.tools.pandora_snapshot_lifecycle_scenario --stage body /tmp/pandora-body-cycle.json
```

Use the same target/ROM/Copperline/direct-contract CLI arguments as above, with
fresh state directories and these checkpoint arguments:

| Scenario | Load receipt | Save receipt |
| --- | --- | --- |
| `/tmp/pandora-body-root.json` | none | a fresh local `post-combat.json` |
| `/tmp/pandora-body-guards.json` | `post-combat.json` | optional fresh `geometry.json` |
| `/tmp/pandora-body-cycle.json` | `post-combat.json` | a fresh local `body-recaptured.json` |

Checkpoint hashes, guard inputs, phase outcomes and remaining limits are recorded
in `runtime/observations/pandora-snapshot-body-guards.json`; no guest snapshots are
published. The palette-stack witnesses are modeled original-CPU calls, separate
from the normal Copperline gameplay observations.


The corrected body stage completes all 37 source-row phases in the recorded run,
including 18 coordinate-checked moves to `(822,146)`, body open at canonical
`$27EA`, first capture, direct close restore and reopen/second capture. A verified
successor is saved. Flags cycle `$40,$60,$E0,$40,$60,$E0`; before each capture
BLIT request is clear and the first post-start stop shows completion and no
BBUSY. Six sampled body chunks retain identical hashes through restore and
second capture (384 of 2,304 bytes). These are bounded observations, not all-path
allocation, alias exclusion or bus arbitration guarantees. Hit-family second
capture and palette-tail entry/exclusion remain unresolved.

### Version check, 2026-10-15

The selected executable remains
`/workspace/copperline-assessment/squashfs-root/usr/bin/copperline`.
`--version` reports `copperline 1.0.0`; executable SHA256 is
`e92e5d527369ae7565e8d8b16f978da7c6868f41aa4b0d8e01a9e7f4956eea3c`.
The retained official AppImage still hashes to
`9ab3e2ecc89beb25344bd1b0d8aa3dcf9370ade8f3b08fdec2fb37e59461f55d`,
matching the release checksum recorded above. The official
[latest stable release](https://github.com/CopperlineHQ/Copperline/releases/tag/v1.0.0)
is v1.0.0, published October 10 at commit `1a284cd`. Newer main commits are not
evidence that a particular observed behavior is fixed; no upgrade was performed.

The MOVEQ sign-extension defect was in this project's generated simulator and
is fixed there. The CLR.W predecrement defect was also in that simulator; concrete execution
is now fixed and the strict expected failure is a passing regression. Neither
test executes Copperline. The subsequent five-defect follow-up also fixes
abstract scalar EA updates and shared-register operand scheduling; see
`docs/validation/framework-defects-2026-10-15.md`. The earlier
negative body-open inference used the wrong source entry (`$27E0`); the corrected
`$27EA` route completed body capture/restore/recapture in Copperline. The palette
return issue is currently supported by modeled original-game stack/control-flow
witnesses, separately from those runtime observations. It is not an observed
Copperline CPU failure, nor is ordinary gameplay reachability of that spliced
palette path established. Do not attribute it to emulator version without an
isolated architectural discrepancy or a relevant upstream fix.

## Replacement-worker checkpoint recreation and combat defeat

On October 16 the pinned official Copperline 1.0.0 AppImage was downloaded again
and verified against its published checksum. The existing legal ROM was reused;
`ctennis` was not changed. The original corridor, west staging, flight crossing,
rifle approach, pickup and fresh-process audit all passed, followed by the
neutral observation, reverse staging and first-security-damage route. Local
receipts and snapshots are in `.runtime-state/pandora-takeover`; guest snapshots
are not committed. This recreation no longer depends on transferring the old
worker's checkpoint archive.

The original `pandora-security-null-node.json` again times out awaiting a second
security hit. The new `pandora-security-eligibility-window.json` instead counts
160 service entries after the first hit, retaining the first and last capture
of each 32-call group. Combat flag bit 1 becomes set, the security countdown
pauses at 33, and HP drops to 0. This contradicts the provisional lost-proximity
explanation for that observed window: the sampled nearest object remains the
flight controller.

`pandora-combat-null-node.json`, loaded from the saved first-damage receipt,
passes all seven canonical stops. It observes combat defeat `$79A8`, call site
`$7A06`, A0=0 before the node writes at `$868A`, word `$10` changed from `$00FC`
to zero after them at `$8694`, and the return at `$7A0A`. Byte `$A` remains `$08`
because its cleared bit was already zero. No HP, pointer, predicate, or gameplay
register was injected. The direct-payload boot contract remains the explicit
original-loader limitation.

Use the existing public checkpoint command with scenario
`runtime/scenarios/pandora-combat-null-node.json`, load receipt
`.runtime-state/pandora-takeover/damage.json`, and a fresh state directory.
The damage receipt is recreated by the documented chain above; save it after
`pandora-reverse-security-damage.json` completes at the pre-store stop.
[Compact evidence](../runtime/observations/pandora-combat-null-node.json) records
the chain, input cleanup, payload identity, captures and raw report hashes.
[Optional correction](optional-patches.md) remains separate from default source.

## Corrected-build combat comparison

The opt-in NULL-node guard now completes a fresh corrected boot, the same
corridor/rifle/return route, and combat defeat using only corrected-build
checkpoints. All ten segments pass. Each snapshot binds the corrected payload
`ee345a4a502415dd717509f834a05db5039fbcc0acc4e28b6f3b14c813a78535`,
its artifact receipt, media, ROM and emulator. An original checkpoint is refused
against that context. No guest HP, pointer or predicate was forced.

All captured values in the eight shared west-through-first-damage segments
match the original. Common combat registers, PC/SP and memory also match except
for the intended vector preservation after exchange. Original `$10..$13`
changes `$00FC081C`→`$0000081C`; corrected remains `$00FC081C`. The bus-error
vector `$8..$B` remains `$00FC0818` in both: bit 0 of byte `$A` was already clear.
These are exception vectors, not overwritten handler code.

Eight following main-loop visits retain HP 0, the defeated flag, static defeat
state and cleared combat mode, with vectors intact. The exit counter remains 70
in this short window. No complete exit/title transition, visual comparison,
exception-consequence test or player-visible improvement is claimed. This is a
low-impact original bug used to prove explicit optional correction.

The non-NULL entry-officer exchange matches original captured registers and
object/state/node/vector bytes; only the declared four-byte extra stack scratch
differs. Runtime admission rejects original instruction anchors inside replaced
ranges and omits overlapping function symbols. One immutable canonical analysis
snapshot is reused within each CLI invocation and closed on all exits; payload
and checkpoint identity checks are unchanged. **127 focused framework tests pass.**
The default binary and rendered-source hashes still match the prior C/vasm exact
receipt `95a4fdbeb207af048a0afd556358d3a7e87f26a5f881d9cc6c4f7e4ec7b3f836`.

[Evidence](../runtime/observations/pandora-corrected-combat-defeat.json) and
[reproduction](optional-patches.md#reproduce-the-corrected-route) record the build,
checkpoint lineage, captures and comparison limits. No guest snapshots are
published. The corrected local chain is under `.runtime-state/pandora-corrected`.

### Original rifle descriptor and retained-aim audit

The [descriptor and shot receipt](../runtime/observations/pandora-rifle-descriptor-admission.json)
uses the original `pandora` contract and verified original
`.runtime-state/pandora-takeover/audit.json` checkpoint, with inherited full payload
and copied-image verification. The pinned emulator/ROM and snapshot hashes are
recorded there. No guest snapshots are published. Reproduce with the usual CLI,
`--checkpoint-load` that receipt, and either
[`pandora-rifle-descriptor-audit.json`](../runtime/scenarios/pandora-rifle-descriptor-audit.json)
or [`pandora-rifle-simultaneous-left-fire.json`](../runtime/scenarios/pandora-rifle-simultaneous-left-fire.json),
using a fresh isolated `--state-directory`. Inputs release at the first sampled
ray point and on runner cleanup. The shot's historical execution identifier says
`west-wall-shot`; “west” describes requested input, not the resulting aim.

The live table contains 67 distinct descriptors and NULL: 29 fixed prefix entries,
32 reordered entries, and six fixed tail entries. The flight controller's root
has ray-state skip bit3, but its linked attachment does not. That root flag alone
therefore does not establish immunity. Feed has cached geometry even with its
outside-view flag set. These are table/state observations, not successful hits.

Pressing left and fire together leaves player XY at (1228,874) and uses retained
rightward request (7,0). The first sample, (1270,888), reaches the blocked-tile
handler, then execution returns to the canonical main-loop anchor. Original tile
306 is blocking there. Player HP remains 95, controller HP 55. The four-byte capture
at `$1924C` changes from `05010501` to `05010401`: initial ammunition 5/1 remains,
while mutable ammunition falls to 4/1. Earlier audits read the initial pair at
`$1924C`; the audit scenario now reads mutable ammunition at `$1924E`. It also
separates cached neutral input at A6+$1C6 from retained aim at A6+$31C. No general
ray termination, ordinary NPC hit, Feed return, BYTE write, DMA/pixels or audible
output is established. Changing aim requires a separately accepted movement request
before the fresh fire press.

The [separated left-aim scenario](../runtime/scenarios/pandora-rifle-separated-left-aim.json)
uses the same original checkpoint. A two-visit direction window did not admit a
movement request; this is a bounded negative observation. An eight-visit window
records accepted request (-7,0); two neutral visits settle player XY at (1207,874)
with cached input zero. A fresh fire press then samples (1193,888), clear original
tile 92, and (1179,888), blocking tile 64. Mutable ammo 5/1 becomes 4/1; initial ammo
and both measured HP values stay unchanged, then the canonical main loop is hit.
Only these two ray samples are bounded. The native instruction anchors from the
preceding CLI compilation were reused unchanged; captures and inputs pass normal
runner validation. This adds no successful NPC hit or global ray bound.
