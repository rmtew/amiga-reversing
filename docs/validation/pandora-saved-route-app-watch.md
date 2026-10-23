# Pandora saved-route app access evidence

The successful route at [`666b373c`](https://github.com/rmtew/amiga-reversing/commit/666b373ca9b612e0f4ad8eb92bd0a797d9389a89)
was replayed with simultaneous CPU data-access subscriptions over the remaining
14 declaration gaps (750 bytes) and declared slots `+$2D4..+$2D8` and
`+$368..+$36C` (8 bytes). The target binary, source, authored/compiled route and
normal controller inputs were unchanged. This publication adds only independent
observation tools, tests and evidence to master; it does **not** merge PR5 or its
148 held commits, or publish any paused B07 work.

[Machine-readable receipt](../../runtime/observations/pandora-saved-route-app-watch.json)
binds the original/ROM/emulator/native-fact identities, private reports and
executed observer/bridge code. It contains no proprietary media, raw checkpoints
or raw register/stack captures. The qualified route and its runtime support are
still dependencies at the linked commit; master alone is not claimed to contain
that held route. The observer and reporter import no held implementation.

## Completed window and findings

Watches start at source `$83AE`, **frame463 after initial proximity setup**, and
end at the original movement-inhibition instruction, **frame14,332**. Initial
clearing/copying and the previously observed initial overlay read at frame462
are excluded. Existing startup/early/inventory/deposit evidence was reconciled,
not rerun. All 576 canonical stop frames **and colour-clock positions**, plus
the complete input acknowledgement trace, equal the unwatched cold baseline.
The selected outcome remains saved Earth plus player escaped: A0 `$5CAE5`,
state `$FF`, event flags `$5C`, Earth deadline `$8258`, HP49.

| Actual event | Accessing original instruction | Interpretation and remaining question |
| --- | --- | --- |
| 29 WORD reads, physical `$3B8C`, app`+$190`; first frame1218, last14262 | source`$6130`, runtime`$16130`: `move.w APP_RASTER_ROW_OFFSETS_OFFSET(a6,d1.w),d1` | Repeats the already established indexed text-row lookup alias into the startup pointer's high WORD. Source masks the Y cell, then shifts its row index. It does **not** demonstrate a callback consumer or explain why that pointer was initialized there. |
| 84 WORD writes to `$3CD0` (`+$2D4`) and84 to `$3CD2` (`+$2D6`); first frame543, last14211 | source`$8366`, runtime`$18366`: `move.l a5,app_02D4(a6)` | Semantic gameplay production: the NULL-terminated object-table scan puts the current object in A5; when a candidate changes, it writes `app_nearest_object_ptr` at`$8362` and then this shadow. Reset clearing at`$9FB2` is a separate producer outside the window. This confirms the existing producer contract; the shadow's downstream purpose remains unresolved. |

These are **197 bus events, three address/direction signatures, two already-known
instruction sites**. The backend reports each WORD bus access of the LONG store;
168 events must not be reported as168 separate LONG instructions. Counts84/84
and first/last bus positions are retained; this bounded signature summary is not
an ordered value trace proving every individual pair.

All accesses were counted rather than retiring a watch on first hit. No event
was received in the other13 whole gaps (745 bytes), the other3 bytes of the
`+$190` gap, or slot`+$368`. There were no reported outbound notification or MMIO-queue drops and no
local signature overflow. These are completed-window observations, **not unused
or dead-storage proofs**. Instruction fetches, DMA and accesses starting outside
a filter but extending into it are excluded.

## Before/after accounting

| Obligation | Before | After |
| --- | ---: | ---: |
| Declaration gaps / gap bytes | 14 /750 | 14 /750 |
| Unexplained declared slots (`+$2D4`, `+$368`) | 2 | 2 |
| Conditional A6 sites without established original entry | 4 | 4 |
| Register-alias sites in the dated inventory | 662 | 662; this pass does not re-enumerate or close them |
| New original instruction sites / newly classified bytes | — | 0 /0 |

The older inventory has a different rendered-source hash. Its extents were
therefore checked against the **current** generated numeric RS block: all14 gap
intervals and the2032-byte envelope match. This is not a fresh whole native
analysis. Native instruction identity, original binary and current source hashes
are separately bound. No source generation or redundant byte-exact rebuild was
needed because neither target source nor bytes changed.

The old source already documents the producer/reset at`+$2D4` and the unchecked
row alias, so a cosmetic rename is not justified by this pass. A consumer or an
owner/lifetime meaning requires new evidence. Likewise `+$190` still needs its
initialization intent explained, and `+$368` needs an actual original blitter
callback producer/call context. The four unestablished A6 sites are source`$6DBA`, `$6DBE`, `$6DD6` and
`$6F22`; they require original
entry evidence; physical gap watches cannot establish that all other code paths
or computed pointers are covered.

## Backend and context limits

The initial attempt to register32 separate stopping traps failed with RPC
`-32602` before gameplay. Cleanup also errored; the owned process exited, and
that attempt is retained as failed infrastructure with no coverage claimed.
The error does not establish a precise universal backend trap-count limit.

A first completed subscription replay recorded197 positive events but retained
only `dropped_notifications`. A two-frame, known frame-counter control exposed
the separate `dropped_events` field. That replay is retained as provisional:
its positive observations stand, but its quiet windows are not qualified. The
final replay repeats the route with **both** loss counters checked.

The working implementation uses Copperline's documented
[`events.subscribe` / `event.mmio`](https://copperline.dev/docs/control/#streaming-observability)
with16 simultaneous read/write ranges. It verifies `events.list` readback,
counts received accesses before the client's small notification deque evicts old
items, and retains at most256 signatures. Missing either loss counter (`dropped_notifications` or `dropped_events`), reported loss
or signature overflow cannot qualify complete coverage. The collector injects
no guest writes, inputs, run or step commands. Filter registration and cleanup
operate only on debugger subscriptions.

Each signature retains actual PC, address, bus width, direction and precise
first/last frame/CCK. The reporter assigns those positions to canonical route
phase intervals. A6=`$39FC` and code-address candidates on the stack are retained
from a **later canonical boundary**. They are not access-time register snapshots
or a validated access-time call stack. Source `$6130` also overwrites D1 with the
loaded WORD, so a later D1 must not be presented as its original index. Existing
static caller/reference evidence and the prior stopped alias probe support the
interpretations above; no new all-path base-register proof is claimed.

## Reproduction and validation

Use the qualified checkout at`666b373c` and its legal local assets and baseline
artifacts. Generate/replay its `pandora_finale.complete` route with the existing
owned `copperline_session` runner. Import `RouteAppWatch` from this independent
publication; it needs only the client's existing `events`, `request`,
`registers` and `read_memory` interfaces. The thin phase observer wiring is:

```python
watcher.phase = phase['name']
result = original_run_scenario_phase(client, phase, *args, **kwargs)
if result['status'] == 'hit' and phase['source_offset'] == 0x83AE:
    watcher.arm(client, result['stop_event'])
if watcher.client is not None:
    watcher.boundary(client, result)
if result['status'] != 'hit':
    watcher.close(None)  # incomplete; never qualify as a successful window
elif phase['source_offset'] == 0x4C99C:
    watcher.close(result['stop_event'])
# Persist watcher.report() to the fresh private run directory as watch.json.
```

Preserve the existing phase/input sequence. Bind the observer and bridge hashes
at run start and verify they remain unchanged at completion, as in the recorded
execution-identities receipt. Raw reports, media and snapshots stay local.
The baseline hashes in the public receipt allow refusal of substitute artifacts;
without those local prerequisites, replay is missing evidence, not a pass.

Rebuild the sanitized accounting from retained private evidence:

```sh
python -m amiga_reversing.tools.pandora_route_app_watch_report \
  --qualified-checkout /path/to/qualified-checkout \
  --run ending-app-watch-c \
  --output /tmp/pandora-saved-route-app-watch.json
```

Actual checks: nine focused adapter tests pass on the isolated master worktree;
the full197-event replay preserves outcome and exact input/timing; the reporter
reproduces the accounting and refuses a controlled reported-loss variant. The
failed stopping-trap attempt remains explicitly non-passing. PR5 stays unmerged;
all nine paused B07 files are unchanged.

## Targeted static follow-up (2026-10-23)

[Reproducible static findings](../../runtime/observations/pandora-app-static-followup.json)
reconcile the remaining questions against all7,059 accepted instructions,
3,500 native CFG edges and40 published reviewed original-data edges. No ending
replay or new gameplay capture was run for this follow-up. The older private
edge cache has obsolete `$A9E` store provenance; the report consumes the canonical
published `$A9C` reference instead, and checks the retained reachability topology.

Two newly generated leads were adjudicated, without counting them as semantic
unknowns closed:

- The only indexed address-producing instruction is `$A15E`, the camera-profile
  data lookup. All three direct scalar writers of the profile index are the
  reset/shortcut sites `$6AE`, `$6C6`, `$9EEC`, assigning0 or1. The original domain
  selects six-byte records at`$A146/$A14C`, followed by three WORD data loads.
  This supplies no original entry to the missing background helpers. Corrupted
  indices and indirect alias writes remain outside that qualified domain.
- An all-byte-alignment raw DWORD search finds one outside coincidence into
  the background component: bytes at`$44BEF` resemble runtime address`$16F00`.
  That odd-offset location belongs to the classified `scene_pixel_cells_for_mask_bank_47`
  bitmap, not a canonical pointer field; there is no incoming code reference or
  stored pointer seed. It is not admitted as a control-flow edge.

The background component has201 accepted instructions outside the established
original-entry graph; it contains`$6DBA`, `$6DBE`, `$6F22`. The standalone helper
at`$6DCA` has8 such instructions and contains`$6DD6`. Neither component has an
external resolved edge, concrete address producer or typed original pointer
seed after this bulk search. Absolute/immediate operands and native
PC-displacement LEA/PEA producers were included. This does not exclude split,
computed, opaque or unaccepted-code targets.

The register-copy audit adds a distinct check to the earlier cursor list:
**all** direct A6 reads are the two stack saves at`$102A/$97BE`; all9 group saves
containing A6 also go to A7 and belong to the14 reviewed save/restore pairs.
Register populations match, under the existing normal-return/valid-stack
assumption. There is no accepted direct A6-to-another-register copy producer.
This does not resolve all662 generic register aliases or prove pointer exclusivity.

The remaining slots have the following exact evidence boundaries:

| Question | Supported result | Missing evidence / next justified action |
| --- | --- | --- |
| `+$190` initialization intent | Original noop pointer store and indexed text-row read are both established. They describe different operations. | A typo/old callback-layout explanation needs another original source/build or a demonstrated pointer consumer. More repetitions of the row read cannot establish intent. |
| `+$2D4` shadow purpose | `$8362/$8366` mirror the changed candidate pointer; `$9FB2` clears it. Existing source already says this. | Need an original semantic reader/owner or bounds for the remaining cursor/lifetime aliases. No dead-storage claim or cosmetic rename. |
| `+$368` legitimate callback producer | Known scalar consumer is the raw BLIT callback dispatch at`$92E/$932`; A6 is explicitly rebound in the ISR. | An original installer/target is still absent. Known INTENA writes do not enable BLIT, but this alone is **not** proof the branch is unreachable: `$8F4` reads raw INTREQR. The exact selection condition is BLIT set with COPER/VBL clear at that sample; a natural entry reaching that combination needs evidence before a scenario is justified. |
| Four conditional A6 sites | Helper roles and conditional base use are understood; no new original entry was established. | Need an original caller/stored or computed target producer. Calling the helpers artificially would not establish original-game use. |

A proposed capacity experiment was rejected before execution: all six original
receptacle primary states have non-NULL attachments and NULL saved-attachment
pointers. The documented NULL-attachment pickup behavior therefore supplies no
**initial** repeatable source for a terminal-deposit overflow route. This does
not prove a lifetime stock bound; a later reachable detach that leaves the saved
pointer NULL would be the concrete missing producer needed to revisit that
hypothesis. No speculative farming route was run.

**Before/after:** two unexplained slots, four conditional entry sites, and14 gaps
/750 bytes remain unchanged; zero new semantic classifications. The benefit is
closing the two generated static leads and bounding which evidence could
actually settle each question. None currently supplies a concrete new normal-input
scenario. Do not repeat the saved-Earth route or reinterpret no-hits as unused.

Reproduce from the retained qualified evidence without importing held code:

```sh
python -m amiga_reversing.tools.pandora_app_static_followup \
  --qualified-checkout /path/to/qualified-checkout \
  --output /tmp/pandora-app-static-followup.json
```

The auditor binds every consumed artifact and checks the original binary,
instruction bytes/population, canonical edge/metadata identities, reachability,
register-save population, profile writers and original receptacle seeds. Focused
validation uses this real retained dataset and controlled inconsistent-input
refusals; no target source generation, byte-exact rebuild, generic behaviour
programme, PR5 merge or B07 work is added.

## Initial alternate-execution feasibility halt (2026-10-23)

Historical result at `61bc75f3`; superseded by the explicitly authorized minimal
build experiment below. General derived-artifact admission remains unsupported.

**HALTED before artifact construction or emulator execution.** The requested
experiment was a moved execution layout, with startup prevented from restoring
it to`$10000`, old-address observations, and the qualified ending route. Merely
rerunning the original layout or moving the already supported two-byte volume
field would not answer that question.

Minimal inspection established these boundaries:

- The [Pandora direct contract](../../runtime/direct_payload_contracts/pandora.json)
  loads the376,832-byte file at`$20000`, but its native bootstrap copies
  source`0..$55370` to`$10000..$65370` and enters`$1046A`. Changing the load address
  alone does not move gameplay execution.
- [Derived artifact admission](../../amiga_reversing/disasm/derived_artifact.py)
  explicitly rewrites fixed-width references **without moving code**. Its
  mapped-region initialization must equal the original source bytes. The
  single-region planner/build path in
  [memory_regions.py](../../amiga_reversing/disasm/memory_regions.py) is not a
  whole-image rebase/copy-bypass emitter. Existing volume relocation at`$65400`
  is a data-only example; it is not an alternate code-layout result.
- [Direct runtime binding](../../amiga_reversing/tools/direct_payload_adapter.py)
  retains the original load/entry/materialization contract, requires a unique
  native copied-source view, and rejects mapped-region destinations overlapping
  the materialized game storage.
  No inspected canonical operation emits a moved-code manifest plus its new
  copy/entry mapping. Hand-editing ORG or suppressing these checks would not
  supply that missing capability.
- A legal placement cannot assume the entire image can move to slow RAM: its
  DMA-used data and fixed chip buffers need compatible placements. The current
  native planner also refuses overlapping semantic source identities rather
  than implementing coordinated moves. No new candidate allocation was claimed
  safe or attempted.
- The completed MMIO subscription observes CPU **data** accesses, not instruction
  fetches or DMA. It must not be advertised as a fetch trap for this experiment.
  Fetch/data/DMA observation design is deferred until an admitted alternate
  image exists; no unsupported watch claim is made.

**Actual moved PC/data addresses: none.** No alternate configuration/patch facts,
derived binary, allocation, reference repair, old-address watch or gameplay run
was produced. No original-layout substitute test, broad semantic audit or new
framework work was started. Original source/binary and all nine B07 files remain
unchanged; PR5 is unmerged and native-C work remains paused.

The precise unsupported action is constructing/admitting a rebased executable
image for this target using existing capabilities. It was **not attempted beyond
read-only feasibility inspection**, not denied by permissions, and has no pending
or uncertain execution outcome. Next decision: separately authorize a bounded
executable-rebase/copy-bypass and runtime-mapping capability, or explicitly narrow
the experiment to an existing supported data-region relocation. Neither is
silently substituted for the requested experiment.


## Minimal alternate-execution experiment (2026-10-23)

**Moved execution confirmed; stopped at the first stale original-image pointer.**
Following explicit authorization to use a separate assembly/startup experiment,
[the small runner](../../amiga_reversing/tools/pandora_minimal_rebase_experiment.py)
changes only `ORG $10000` to `ORG $80000` and replaces the bootstrap's first
copy-helper LEA with `bra.w initialize_runtime_workspace`. Hardware interrupt/DMA
clearing and the workspace/supervisor initialization remain. The original source,
binary, native contract and nine paused B07 files are unchanged. This is an
explicit experimental boot contract, not general native-plan admission.

The original 512 KiB Chip RAM profile cannot hold the disjoint image here. This
experiment uses a separate A500/ECS/PAL/68000, **1 MiB Chip RAM**, 512 KiB slow RAM
profile. The **entire 376,832-byte file** occupies `$80000..$DC000` (end exclusive),
inside Chip RAM, above the original image, fixed low workspace/tile grid,
framebuffers and `$7FFF8` boot marker. No original-profile equivalence is claimed.
The original DMA-used data therefore remains Chip-addressable; that placement
alone does not prove relocated DMA references correct.

`vasm -Fbin -m68000 -no-opt` built the image; all **7,059** retained instruction
extents keep their original size. Two cold runs (prototype and published script)
produced the same payload and first failure. The boot handoff verified the full
loaded payload. Actual PC stops were `$80000`, `$8046A` and `$8048C`, all at frame
386: execution did not copy back to `$10000`.

The existing saved-Earth scenario was reused with source-offset PC observations
projected to the new base. Fixed workspace observations stay fixed. Only three
explicit pointer-field expectations are projected; scalar bytes are not scanned
for address-looking values. No gameplay condition/assertion is relaxed. A verified
CPU data watch covers `$10000..$65370`; PC sentinels cover only `$10000` and
`$1046A`, **not every instruction fetch**. DMA is not watched.

At frame **398**, before the title phase or any normal route input, the guard
stopped a LONG read:

| Evidence | Observed value |
| --- | --- |
| Access PC / source offset | `$89F70` / `$9F70` |
| Instruction | `movea.l world_position_state_record_interaction_data_ptr(a1),a2` |
| A1 / displacement / effective address | `$588C2` / `$1A` / `$588DC` |
| Read value / post-access PC | `0` / `$89F74` |
| Pointer table source / moved address | `$488AA` / `$C88AA` |
| Retained first pointer / required moved target | `$588C2` / `$C88C2` |
| Caller return at SP+4 | `$804DC`, after source `$4D6` JSR |

`scene_restart_receptacle_state_ptrs` moved, but its first entry is the literal
`$000588C2`; the other five entries use fixed original-runtime EQU aliases.
The original and experimental table bytes match. Its first target is the existing
`item_receptacle_lifecycle_records` label at source `$488C2`. A0=`$C88AE` after
reading that first entry and A1+`$1A` exactly matches the watched address. This is
an evidenced missing symbolic relocation, not an inference from a crash alone.
The next bounded repair is to symbolize the evidenced table reference and review
its connected entries, then rerun to the next concrete failure. **No reference
repair was applied in this batch.**

### What moved, including display and DMA references

This changed the **whole assembled image and execution**, not every address in
the machine. Source labels resolve at the new ORG; fixed EQU constants and raw
numeric pointers retain their values. Source/listing cross-checks establish:

| Area | Experimental scope |
| --- | --- |
| App/workspaces | `APP_STATE_BASE=$39FC` and other explicit fixed workspaces stay fixed. |
| Gameplay Copper list | Source `$9EA` now at `$809EA`; PC-relative LEA installs this moved address into COP1LC. |
| Main bitplanes | Banks remain `$70000/$78000`. VBL reads the selected app display pointer and writes four BPL pointers at 40-byte spacing. These are intentionally fixed buffers. |
| Copper split bitplanes | High/low words retain `$75000/$75028/$75050/$75078`, also fixed framebuffer addresses. |
| Sprite image vs Copper words | `blank_sprite_data` moved `$5D5DE` → `$CD5DE`; symbolic CPU LEAs and `#blank_sprite_data` blitter source resolve to `$CD5DE`. Copper sprite words still use the fixed `sprite_0005D5DE` EQU, retaining `$5D5DE`: a static stale-reference lead, not yet a live DMA result. |
| Cursor sprites | Separately initialized DMA buffers remain fixed at `$65370/$653B4`; app slots select their hardware pointers. |
| Audio assets | Record stream is now `$CEAD8`, sample 0 `$CEADE`, silence `$D500A`. The PC-relative initializer derives payload pointers into metadata; service later writes them to AUDxLC. Actual relocated audio/DMA execution has not been qualified. |

The Copper and audio examples are static assembled results. The live run stops
before their setup completes, so they are not evidence that all DMA references
are repaired. Hardware register addresses stay fixed throughout. There was no
blanket replacement of address-looking words, and the stale receptacle pointer
shows exactly why moving ORG alone is incomplete.

[Sanitized evidence and artifact identities](../../runtime/observations/pandora-minimal-rebase-experiment.json)
bind the build, two-run result and first-access attribution. Original-layout
semantic unknown accounting is unchanged. The relocated completion route has
**not** run: this result establishes moved execution and the first missed
reference only. Proprietary source/assets, binaries, ADF, ROM and raw captures
remain private.

Reproduce with the retained qualified checkout at `666b373c`, including its
identity-matched source package, instruction inventory and qualified compiled
ending scenario. The command deliberately refuses changed source/binary identities
and requires a fresh private output directory. `--run` requires local legal media
and Copperline; omit it for build/extent validation only:

```sh
/path/to/qualified-checkout/.venv/bin/python \
  amiga_reversing/tools/pandora_minimal_rebase_experiment.py \
  --qualified-checkout /path/to/qualified-checkout \
  --output /private/pandora-rebase-run \
  --run --rom /private/kick13.rom --copperline /path/to/copperline
```

The script uses the explicitly qualified checkout's existing runtime by pathname;
it does not import held B07 changes into master or publish their files. The
qualified runtime and private prerequisites are required, not a standalone public
reproduction bundle. PR5 was unmerged at the experiment milestone; the later
master consolidation is recorded in the target status.


## Relocated saved-Earth completion (2026-10-23)

The explicit `$80000` experiment now completes the existing normal-input route
from cold boot, twice: **576 phases**, HP49, ending frame14,278. Moved PC
`$CC9DC` selects message `$CCAE5`; state is FF and flags5C. A 30-frame
postlude visibly displays “PANDORA IS DESTROYED. EARTH IS SAVED.” The repeat's
phase frame/CCK positions and all509 acknowledged controller calls (including
cleanup) match the first relocated success. The375 authored input events and
actual controller actions match the original route; no goal assertion was relaxed.

The retained failures identified three connected fixes: six receptacle restart
pointers and six interaction-data fields; the player's absolute callback/self
jump; eight combat geometry pointers and two related descriptors. Blank sprite/
mask aliases also now use the existing moved data label, including Copper high/
low words. The21 symbolic edit groups are experiment-only. They assemble to the
**exact original full file at the original ORG** under vasm; canonical source is
unchanged and still passes the C full-file exact check. All7,059 instruction
extents remain unchanged. No byte-looking constants were scanned/replaced.

The old-image synchronous CPU guard reported no access after repair. Both loss
counters were zero across262 live heartbeat notifications. Separate DMA profiles
cover six complete frames:411–412,3953–3954 and14280–14281, with no old-image
transfer. Audio/Copper and sprite accesses include moved-image data; bitplanes
retain fixed buffers. Partial first frames are excluded, not treated as complete.
These are representative DMA observations, not whole-route DMA coverage. Native
[screen captures](https://github.com/CopperlineHQ/Copperline/blob/v1.0.0/docs/debugger/control.md#framebuffer-capture)
were visually inspected; image files remain private.

Asset comparison verifies **126 exported files /295,492 bytes**, including seven
sound assets,118 bitmap assets and the opaque tail: each manifest hash and each
original/relocated image slice match. Inline records, pointer tables, instruction
operands and runtime-mutated data are outside that raw-asset check; changed
symbolic source groups are enumerated separately in the receipt.

[Completion evidence](../../runtime/observations/pandora-relocated-completion.json)
retains failures, identities, asset extents/hashes and sampled DMA counts. The
profile remains separate1MiB Chip/ECS. **Gameplay completion and asset integrity
are established; matched original-versus-relocated graphics/PCM comparison is
still required and in progress.** Screenshot coherence and sampled valid DMA
addresses do not establish pixel or audio equivalence. No original-profile or
all-optional-path certification is claimed.

Use the existing experiment command with `--inspect-output` for private PNGs and
three bounded DMA captures. Original source/binary and nine unfinished B07 files
remain unchanged. No new PR is used.


## Final scoped graphics/audio comparison (2026-10-23)

**Completed**, with original NULL-sprite bounds findings retained.
[Final receipt](../../runtime/observations/pandora-relocated-output-validation.json)
and [offline comparator](../../amiga_reversing/tools/pandora_rebase_output_compare.py)
separate gameplay, assets, device bounds and actual output. This supersedes the
earlier “output comparison pending” milestone; no universal relocation or
original packed-loader equivalence is claimed.

Two fresh cold original/relocated runs on the **same A500/ECS/PAL/68000,1MiB
Chip +512KiB slow** profile passed all576 phases and509 acknowledged controller
calls (including releases/cleanup). The authored plan has375 input events:
these are different denominators. Every phase's actual CCK and every controller
call's arguments/clock matched; captured main-image PCs differ by exactly
`$70000`. Both selected saved-Earth at frame14,464 and committed at14,465, HP49.
A separate cold relocated run with **no clock hold** also passed all576 phases,
ending frame14,351, HP49, with the identical final payload.

All **eight RGBA captures** match without masks: initial star-helper/title
transition, UI overlay initialization, initial proximity, Engineer card transfer,
first sonicdriver hit, console ready, post-ending, and settled title after180
normal no-input frames. The settled capture includes the full PANDORA logo,
credits and starfield; the ending visibly says Earth is saved. These are eight
selection points, not a comparison of every video frame.

Mixed **44,100Hz, stereo,32-bit IEEE float PCM** is byte-identical from sample
441,704 through12,804,988 (end exclusive): **12,363,284 stereo frames /24,726,568
float samples**, about280.35 seconds, through the recorded post-ending EOF.
SHA-256 of both compared intervals is
`3067ef3704857f099506c14bee458610c8b9e61ad1eb737f2b9c52f4bfc5690f`.
The predeclared interval through20 post-ending frames also matches. There is
**no fitted shift, resampling, gain adjustment, tolerance or omitted interior
window**. Pre-game ROM/disk sound before the common handoff is explicitly outside
the interval. The full-file pre-game difference is retained, not described as
equal. Per-source prefix captures also showed identical Paula WAV bytes.

### Startup fixture and actual relocation boundary

The earlier fast copy-bypass builds changed the raster phase of initialization.
Four stable scene pictures matched, but audio did not: per-source capture showed
drive noise plus a real Paula difference; initial AUD1PER was1988 versus1970.
Keeping copy duration alone did not settle that offset. Those failures remain
recorded; they were not accepted using a correlation or an audio tolerance.

The final variant keeps the original **temporary load at `$20000`** and native
forward copy operation count. ORG changes to `$80000`; the helper's destination
label and entry label therefore move. Its CMPA operand order is swapped to take
the forward path for the **disjoint** source/destination intervals, rather than
the generic backwards path for a higher destination. No calibrated delay loop
or gameplay-state patch was added. The low helper at `$300` is intentional.

For differential comparison, both guests naturally spin in the unchanged
pre-game HAND loop until target CCK35,525,500 (frame500); both actually stop at
35,525,509 with identical PC/registers. Frame500 is a shared settling fixture,
not a delay fitted to the waveform. It lets ordinary OS/drive activity continue
before the game starts. The only host memory write is the existing provisioning
marker at `$7FFF8`: `HAND` (`$48414E44`) → `GO!!` (`$474F2121`), followed by a
reverse-history anchor. There are **zero host register writes, checkpoint loads,
artificial game routine calls or gameplay RAM edits**. Guest loader code supplies
the existing A1=`$20000` entry context. Same pre-GO PC/registers are expected
because the same loader is executing; relocated game code has not run yet. This
does not imply all RAM/chip state was identical or that native disk boot is
reproduced. Actual moved body entry and all576 main-image PC stops are verified.

The full376,832-byte input is staged at `$20000..$7C000`; the349,040-byte prefix
is copied and verified at `$80000..$D5370`. **All125 exported graphics/audio
assets and all11 primary sample payloads are inside that prefix**. The opaque
file suffix remains loader-only at `$75370..$7C000`, preserving the original
short-copy contract; the known title clear later overwrites this backing. It is
not claimed mapped at `$D5370`, classified unused, or used as an asset fallback.
Old-range reads during the native loader copy are expected before the consumed
boundary; the `$10000..$65370` CPU guard is then armed at moved source `$48C`.
It stays active through gameplay and post-ending observation. Fixed workspaces
remain fixed, so this is not a watch of every overlapping temporary-loader byte.

### Asset and DMA checks, including the original exception

126 exported files /295,492 bytes match their manifest hashes and original and
relocated image slices. Independently parsed11 primary audio payloads (including
small inline samples), their length/divisor headers,64-byte silence,640-byte
secondary bank and512-byte blank sprite are unchanged. Pointer tables and
instruction operands are excluded from raw-asset identity and listed explicitly
in the source-edit ledger. Runtime mutation is covered by measured output, not
by pretending seed bytes never change.

Six complete DMA frames **per layout** have identical normalized audio, sprite
and bitplane data/ordering. Audio targets fit the actual eleven sample extents,
silence or secondary bank; Copper fetches fit the verified copied image; display
reads fit the established fixed banks; blitter targets were checked for physical
Chip-RAM legality, **not** every object's logical extent. Partial first frames
are discarded explicitly. Both streaming loss counters are zero.

The bounds check also preserves **eight original zero-valued SPR0/1 control
reads at addresses0/2**, across the first two sampled gameplay frames, before
cursor installation. They occur at the same beam positions in both layouts;
source pointers are NULL and the control words are zero. These remain **outside
certified sprite-asset bounds**. The report's verdict is
`pass_with_original_bounds_findings`: exact output/stream equivalence, no new
bounds finding, and no claim of complete original memory safety. Arbitrary
invalid pointers are not admitted. This is not whole-route DMA coverage.

### Reproduction

Use the qualified local checkout/media prerequisites described above. For each
control/candidate capture, append `--run --inspect-output --capture-pcm
--phase-locked-boot`; use `--original-control` for the canonical original and
`--matched-startup` for the relocated candidate. For settled-title captures add
`--stop-after title_menu_loop --title-frames 180`. For the independent cold
completion omit `--phase-locked-boot`. The original source/binary remain intact.

Run the offline comparator with Python containing Pillow (no NumPy required):

```sh
python amiga_reversing/tools/pandora_rebase_output_compare.py \
  --original /private/original --candidate /private/relocated \
  --title-original /private/title-original --title-candidate /private/title-relocated \
  --target /qualified/targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 \
  --output /private/comparison.json
```

Seventeen focused positive/refusal/corruption tests pass. Canonical C full-file
exactness and original-ORG vasm pointer-repair exactness are retained. No new
ROM, media, WAV, PNG, raw slot or checkpoint payload is published. The nine
unfinished B07 files remain unchanged. Other profiles, original packed-disk
boot, every frame/optional path and universal DMA/lifetime safety remain outside
this completed bounded validation.
