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
