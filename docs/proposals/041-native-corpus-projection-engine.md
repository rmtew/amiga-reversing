# Proposal 041: Native Corpus Projection Engine

Status: Research proposed -- 2026-08-04.

## Decision

Replace the corpus collector's JSON-and-dictionary hot path with one native,
forward-only projection engine. The engine consumes authoritative C analysis
and canonical rendered rows once, produces compact target-local corpus records,
and publishes the existing artifacts through deterministic bounded writers.
Python remains build orchestration, merging, reports, and query support; it is
not a per-row transport, parsing, or feature-reduction runtime.

This is a replacement architecture. During migration the current
stream/projector is a test oracle only. Once the replacement proves byte
identity and acceptance performance, delete the old production path: no
fallback collector, compatibility mode, or hidden runtime switch remains.

This repository is used only on its local development system. There are no
external API or ABI consumers to preserve. Private C interfaces, ctypes
bindings, Python orchestration APIs, CLI plumbing, the web/LLM integration
points that consume shared foundations, and agent-facing commands may therefore
be upgraded together when the new design is cleaner. Compatibility is required
only for durable semantic outcomes and published corpus artifacts until this
proposal explicitly changes their contract; it is not required for an
in-repository call shape.

Proposal 040's timing gates are migration safety ceilings, not the performance
ambition. R0 must establish the irreducible analysis/render cost and set a
stronger measured local-machine target. Native projection overhead must be
measured separately and made negligible compared with decoding, semantic
analysis, and canonical rendering.

## Evidence and Goal

Proposal 040 has established artifact identity, 8.47 GiB peak RSS, and a
passing 256.62-second file phase. Its project phase remains 367.19 seconds
against a 309.87-second gate. The current path converts one representation too
many times:

```text
C facts / canonical rows -> JSON batches -> Python dictionaries
  -> Python ordered projection -> JSONL/blob staging
```

Those conversions allocate, copy, parse strings, chase pointers, and weaken
cache locality. The objective is a simple modern pipeline: one native ordered
pass, compact contiguous records, bounded output buffers, and no complete row
list or index for a corpus target.

The web/LLM/manual-action workflow retains its random-access listing artifact:
it needs stable random access while a user changes analysis facts and unlocks
new work. It is a separate consumer of the upgraded C semantic and
canonical-row foundations, not a corpus compatibility path or second semantic
authority.

## Current-System Map and Migration Boundary

The current production route has three exact ownership boundaries:

1. `platform_file_lib.c` receives transient `M68kRenderPlanRow` values from
   facts-v2 and passes them to `PlatformListingCanonicalStream`.
2. `platform_file_json.c` converts each canonical row into JSON batches. The
   public stream callback transports `(event_kind, json_bytes)`.
3. `CListingStream.visit` decodes every event with `json.loads`; Python's
   `_OrderedListingProjector` constructs dictionaries, resolves locations,
   derives xrefs/features/snippets, serializes target-local JSONL shards, then
   reparses those shards for sorting, merging, reports, and publication.

`_OrderedListingProjector` contains the semantic migration surface: pending
analysis xrefs keyed by source location, location rank resolution,
direct-control confirmation, merged snippet windows, listing features, and
navigation features. The new engine must preserve those rules exactly, but it
must not port Python's object model into C.

The first replacement seam is below JSON: split
`PlatformListingCanonicalStream` into a canonical typed-row emitter and two
consumers. The existing JSON serializer remains an oracle/test consumer while
the native corpus projection consumer is introduced. It must not be retained
on the production route after migration.

The second replacement seam is target staging. Current xref staging writes
chronological JSONL, parses it to make sorted chunks, writes those chunks,
then parses them again for merge. The new engine writes compact deterministic
records directly; final JSONL/blob encoding occurs once at publication. This
also removes the current disk-entry temporary-file copy from the hot path by
accepting the already extracted source bytes/buffer in the native entry API
where a disk source cannot otherwise be passed directly.

## Proposed Private C Interfaces

These interfaces are private C implementation interfaces, not an external ABI
and not Python transport. They may replace the current stream interfaces and
their bindings outright:

```text
PlatformCanonicalRowEmitter
  create(object, policy, source_analysis, row_sink)
  accept_transient_row(M68kRenderPlanRow)
  finish(navigation)

PlatformCorpusProjection
  begin(typed_source_analysis, target_identity, bounded_target_writer)
  accept_batch(PlatformCanonicalRowBatch)
  accept_navigation(PlatformNavigationFacts)
  finish(PlatformCorpusTargetSummary)
```

`PlatformCanonicalRowBatch` is a borrowed bounded structure. It has parallel
arrays for fixed-width fields (`row_kind`, section, offsets, addresses, line
metadata, symbolic-part ranges) plus append-only byte spans for text and
symbols. It is valid only for `accept_batch`; batch storage is reset/reused
afterward. The projection copies only selected compact row text into a snippet
writer and only final xref/string values needed by output records.

`PlatformCorpusProjection` owns one target-scoped reducer state and shard
writer. It exports an error and coverage result equivalent to the current
collector. It does not own decoding, source rendering, random-access listing,
or report-wide aggregation.

## Execution Plan and Decision Gates

Each phase has a stop/go comparison. Do not start a lower-level optimization
until the preceding phase proves semantic parity and identifies a real cost.

| Gate | Change | Required proof before proceeding |
| --- | --- | --- |
| R0 | Add stage timers/copy/allocation counters around current JSON encoding, ctypes decoding, Python reduction, JSONL shard sort/merge, and source-byte staging. Use Windows Performance Recorder's CPU Usage profile, analysed in Windows Performance Analyzer, for thread/stack attribution. | Per-target attribution for King and other project tails; counters do not change artifacts. Establish the irreducible native analysis/render baseline, a stronger local-machine end-to-end target, and a numerical projection budget before R1. |
| R1 | Introduce typed canonical row batches beneath the current JSON serializer. | Typed batches serialize to byte-identical current row JSON across fixtures and corpus samples. |
| R2 | Move location resolution and direct-control reduction to C. | Native reducer and Python oracle emit identical xrefs and row-index selections at every batch boundary. |
| R3 | Move snippet interval merging and compact shard writing to C. | Identical snippet index/blob and xref shards; bounded live rows/bytes proven. |
| R4 | Move listing/navigation feature reduction and target manifest contribution to C. | Identical target manifest rows, variants, type-flow inputs, unresolved-field inputs, and coverage. |
| R5 | Replace JSONL intermediate sort/reparse with compact sorted shard records and one final encoder. Upgrade the corpus CLI and only the call sites that consume the shared native semantic/canonical foundations; retain the web/LLM/manual-action random-access artifact as its own consumer. | Byte-identical final artifacts, fewer copies/allocations measured, and all updated in-repository integrations pass. |
| R6 | Profile carefully selected bulk kernels and add CPU dispatch only when justified. | Scalar/SIMD equivalence, supported-host dispatch tests, and material end-to-end gain. |
| R7 | Run end-to-end conformance against the temporary oracle at normal one-worker and eight-worker concurrency. | All normal artifacts and coverage byte-identical, full C/Python suites pass, proposal 040 safety gates clear, and the stronger R0 target and projection budget pass. |
| R8 | Delete the old collector, ctypes/JSON stream bindings, and the temporary oracle. Update proposal 040 only after its separate acceptance evidence passes. | No production reference, compatibility mode, or stale interface remains; the replacement architecture is the sole route. |

R0 must separately time semantic planning, canonical typed-row production,
JSON construction, FFI callback time, Python decode, Python projection, shard
writing, and sorting. It is not enough to report a single `source_seconds`
value. Before R1, record the exact budget in this proposal: for targets with
at least one second of unavoidable native semantic work, total projection,
staging, and final encoding overhead must be at most five percent of that
target's end-to-end time. R0 must also set a separately measured fixed-cost
budget for smaller targets. These budgets may be tightened by evidence, but
not relaxed without an explicit proposal update. This determines whether
R1--R5 are sufficient before SIMD work begins.

## Required Worklog

Maintain [`docs/worklogs/041-native-corpus-projection-engine.md`](../worklogs/041-native-corpus-projection-engine.md)
throughout R0--R8. It is the mandatory resume ledger for this migration, not a
second design specification or source of semantic truth. Before beginning or
resuming work, record the active gate, next bounded action, relevant invariants,
and unresolved questions. At every meaningful boundary, record the commands
run, result, artifact/benchmark evidence, failures, decisions, and the next
action. Remove or mark resolved checklist items so the next worker does not
treat historical work as pending.

No gate may be claimed complete from conversation memory or a focused test
alone: its required evidence must be linked in the worklog and remain
reproducible from the code, tests, and recorded command. Update the proposal
when a durable architecture or contract decision changes; update the worklog
for progress, observations, and resume context.

## Target Architecture

```text
authoritative C analysis + canonical row serializer
                    |
                    v
       NativeCorpusProjectionEngine (one ordered pass)
       - pending-location relation merge
       - direct-control state machine
       - rolling snippet window / interval merger
       - compact target-local xref and snippet writers
                    |
                    v
       deterministic normal artifact writers
                    |
                    v
       Python orchestration, merge, reports, query APIs
```

C remains authoritative for decoding, analysis, canonical rows, navigation,
and source text. The engine derives corpus records only from those typed facts
and rows, preserving location rank rules, stable IDs, direct-control semantics,
snippet intervals, feature ordering, and artifact sort keys.

### Internal ABI and ownership

Use C-owned typed bounded spans, not JSON, between native row production and
projection. A batch contains fixed-width metadata plus offsets into one bounded
text/operand blob. The producer owns it until the callback returns; no consumer
may retain raw pointers. Numeric IDs already generated for row kinds, xref
kinds, features, and platforms are used in hot records. Strings are copied
only when the final artifact needs them.

Use parallel/structure-of-arrays storage for scans over offsets, section IDs,
kinds, feature IDs, and pending keys; use small structures only when all fields
are consumed together. Keep hot fields contiguous and cache-line aligned; keep
cold diagnostics and strings out of the hot record. Use clear batch and target
arena lifetimes, exact finalized storage, and no retained superseded builders.

## Modern CPU and Memory Design

The goal is measured efficiency, not decorative intrinsics.

- Prefer contiguous sequential scans, sorted fixed-width keys, linear merges,
  and small branch-friendly state machines over pointer-rich maps and callback
  chains in the row loop.
- Pre-size from durable counts where possible; otherwise use amortized builders
  and exact final storage. Never retain prior capacities after finalization.
- Make the bounded batch and rolling snippet state cache-resident where
  practical; reserve separate streaming buffers for output blobs.
- Use `memcpy`/`memmove` and toolchain bulk routines first. Profile before
  introducing explicit vector code.
- Candidate SIMD kernels are byte classification, newline/delimiter detection,
  UTF-8-safe ASCII fast paths, hashing/checksum preprocessing, and fixed-width
  record filtering. Every kernel needs scalar-equivalent tails, safe alignment,
  and exact tests.
- Do not attempt SIMD for graph solving, source semantics, ordering decisions,
  or irregular lookup-heavy control flow. Improve their data layout and
  allocation behavior first.
- Put CPU-feature dispatch behind one small capability layer. Provide a scalar
  kernel baseline and dispatch AVX2/AVX-512 only when runtime CPU/OS support
  and measured evidence justify it. This is implementation dispatch, not a
  collector fallback; outputs must be identical.

## Required Research Evidence

Instrument current and candidate paths with the same per-target values:

1. semantic planning, typed flow, row walk, source-quality, and native shard
   writing time;
2. batch encoding/decoding, projection reduction, report derivation, and
   publishing time;
3. row/byte/operand/xref/snippet counts, allocation count/bytes, copied bytes,
   and peak live bytes; and
4. cycles, instructions, cache misses, branch misses, and per-target tail
   latency where an optional Intel VTune hardware-counter capture is available
   on this machine and agrees with the WPR/WPA timing attribution.

WPR/WPA is the required profiler for scheduler and stack attribution. VTune is
an optional hardware-counter diagnostic, never a gate and never a condition of
correctness. Neither profiler may affect content or scheduling. Research must
identify dominant costs before changing record layout or adding SIMD.

## Transition and Shared Tests

Build a shared corpus-projection conformance suite that runs the current oracle
and candidate against the same fixture input. Compare analysis lifecycle,
canonical rows/metadata/navigation, xref identity and ordering, feature counts
and examples, direct-control runs, snippet index/blob bytes, all normal
artifacts, and explicit analysis-failure coverage.

Fixtures must cover shared-location labels, code/data rank rules, batch-boundary
branches, runtime aliases, relocated expressions, large rows, overlapping
snippet windows, empty targets, refusal paths, and platform facts. Add
batch-boundary property tests varying batch capacities without retaining a full
row list.

At corpus scale run clean one-worker and eight-worker builds for both paths
while the oracle exists, comparing manifest, xrefs, both snippet files,
variants, type-flow, unresolved fields, and coverage byte-for-byte. Profile
payloads may differ; semantic artifacts may not.

Byte identity is the migration oracle, not an eternal local-artifact
constraint. After replacement parity is proven, a later explicit proposal may
make a cleaner corpus-schema change. It must version the contract, update every
in-repository producer and consumer, provide regeneration for checked
artifacts, and land atomically with complete tests. Incidental artifact drift
is never an acceptable schema upgrade.

### Verification discipline

Focused reducer and batch tests are fast feedback only. They must never be
used as evidence that an architectural phase is complete. Each phase must add
its focused regression coverage and then run the broad tests covering every
layer it touches:

- C unit tests after C model, serializer, renderer, projection, or ABI work;
- both Python test roots separately after collector, staging, command, web, or
  agent-facing integration work (their duplicate module names make a combined
  pytest invocation invalid);
- existing source/rendering, random-access artifact, and corpus fixture tests
  whenever canonical rows, navigation, or artifact encoding changes; and
- clean one-worker and eight-worker corpus comparisons at each migration gate,
  not only at the final cutover.

Do not deselect, skip, quarantine, weaken, or rewrite a failing broad test to
advance the migration. Classify each failure against the old and new paths,
add a minimal reproducer where coverage is missing, and repair the design or
implementation before proceeding. The performance counters and oracle may help
diagnose a failure, but neither replaces end-to-end semantic verification.

### Required commands and build modes

Run these from the repository root, with the local uv cache set so the normal
Windows environment is used:

```powershell
$env:UV_CACHE_DIR = 'C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'
cmd /c src\build.bat --lock-held
.\src\build\m68k_c_unit_tests.exe
uv run pytest tests -q
uv run pytest src/tests -q
```

Run the corpus-manifest build command with fully clean, distinct output and
temporary directories once with `--workers 1` and once with `--workers 8`.
For each R1--R7 comparison, invoke it once through the temporary oracle and
once through the candidate, then byte-compare every declared normal artifact
and coverage output. The implementation must add a checked test helper or
script that supplies those isolated paths and comparison inputs; handwritten
ad-hoc invocations are not acceptance evidence.

Capture R0 and R6 scheduler/stack profiles with Windows Performance Recorder's
CPU Usage profile and inspect them in Windows Performance Analyzer. If Intel
VTune is installed and supports this host, capture its hardware counters for
the same clean corpus build and retain the capture command and summary with the
benchmark record.

## Acceptance Criteria

- One native ordered projection pass; no JSON row-batch/Python-dictionary hot
  path and no complete rendered row list, listing index, or source text held
  for a corpus target.
- Exact normal artifact identity across one/eight workers and preserved
  random-access source/listing fixtures.
- C and Python conformance coverage throughout migration; full suites pass.
- No phase advances on a focused subset alone: all relevant broad suites,
  random-access fixture coverage, and corpus-scale comparisons pass.
- Every new test failure is diagnosed and repaired or accompanied by an
  explicit, separately approved contract change; no quarantine or silent
  suppression is permitted.
- No worker reduction, retry, cache, target exclusion, degraded output,
  compatibility mode, or fallback collector.
- All in-repository callers use the new architecture; obsolete private API/ABI
  surfaces and bindings are removed rather than preserved for compatibility.
- SIMD is used only for measured exact bulk kernels.
- A normal eight-worker build completes all 378 currently scoped targets (319
  file entries and 59 project targets), clears proposal 040's
  memory and timing gates, and publishes atomically.
- The stronger R0-derived local performance target passes, with projection
  overhead within the recorded per-target budget: at most five percent of
  end-to-end time for targets with at least one second of native semantic work,
  plus R0's explicit fixed-cost budget for smaller targets.
- The required C build/unit command and both isolated Python test-root commands
  pass at each applicable gate; corpus acceptance uses clean one-worker and
  eight-worker output directories and the checked comparison helper.

## Non-Goals

- A second semantic renderer or reimplementation of C analysis in Python.
- Changing artifact schemas, feature meanings, IDs, snippet radius, or target
  coverage for a benchmark result.
- Keeping a second production collector after the transition.
