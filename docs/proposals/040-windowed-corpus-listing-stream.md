# Proposal 040: Native Streaming Listing Render for Corpus Collection

Status: In progress — 2026-08-01.

The builder/final-plan lifetime correction, semantic-only layout product, and
bounded transient-row visitor are implemented and covered by C tests. They are
foundations only: corpus production still uses the random-access listing
artifact. This proposal is not accepted and makes no RSS or corpus-output
claim yet.

## Decision

The next corpus-memory fix belongs in the native listing renderer, not in the
Python collector and not in worker scheduling.  The corpus must receive the
same authoritative listing rows through a native, sequential stream whose
maximum live row state is bounded.  This requires separating source analysis
and render planning from per-row text/materialisation in the C listing
artifact.

Python paging alone was implemented and measured as an experiment, then
removed.  It is explicitly not the solution proposed here.

## Evidence

A clean 8-worker baseline build completed 428 entries in 708.07 seconds:

| Phase | Time | Peak process memory |
| --- | ---: | ---: |
| File analysis (319 entries) | 286.07 s | 12.51 GiB |
| Project analysis (59 entries) | 309.87 s | 16.85 GiB |
| Total | 708.07 s | 16.85 GiB |

Completed analysis payloads are released at phase boundaries, so this is not a
stale-output leak or an unbounded Python staging queue.

The rejected Python-window experiment used 512-row `window_payload` calls
instead of requesting a whole listing.  Its full 8-worker build completed all
428 entries, but took 883.37 seconds: file analysis rose to 360.66 seconds and
project analysis to 405.42 seconds.  Its peak was 16.86 GiB, statistically the
same as the baseline.  Although manifest, snippets, variants, unresolved
fields, and coverage matched byte-for-byte, xrefs and the derived type-flow
report did not.  The production experiment was removed rather than retained as
a fallback or a partially correct optimisation.

The native ownership boundary explains the result.  A
`PlatformFileListingArtifact` owns the complete `M68kSourceAnalysisIR`,
`M68kRenderPlan`, render evidence, and a complete listing row index before its
first window is served.  `listing_artifact_build_analysis` calls
`m68k_facts_v2_render_asm_source_plan_analysis_profile_evidence_alloc`, then
constructs the row index from that full render plan.  Paging changes only the
JSON response after the expensive complete native representation already
exists; repeated page requests additionally repeat projection work.

There was a second, independent native retention fault in the previous
`M68kRenderPlan` implementation. Its growable contiguous arrays retained
superseded `arena_realloc_copy` allocations until artifact destruction. This
was an ownership mismatch between monotonic allocation and replaceable,
growable buffers, not an arena defect. It is corrected by separate
temporary-builder and final exact-size plan lifetimes; that correction does not
remove the complete row plan and index retained by the interactive artifact.

## Current Implementation State

Completed:

- `M68kRenderPlan` finalisation publishes exact-size arrays and destroys the
  builder arena; its regression test proves the builder is released.
- A semantic-only facts-v2 entry point finalises declarations, labels, and
  expressions without rendered rows, listing indexes, or source text.
- A facts-v2 transient-row visitor emits completed rows through a reusable
  native buffer without retaining an emitted-row plan. Its C test proves rows
  are emitted and `asm_source_plan_rows` remains zero.
- The native forward-only stream now creates its own object/policy state,
  invokes the transient visitor once, and serializes each row through the
  canonical listing serializer. Its analysis payload is delivered before the
  first row callback; it retains neither a complete rendered plan nor a
  listing-row index. Direct regression comparisons against the interactive
  artifact cover raw code, a branch target, and mixed code/data fixtures.

Completed since the initial stream implementation:

- `target_usage_manifest.py` now consumes the native typed stream through one
  shared ordered projector. It retains only location obligations, direct-control
  confirmation state, and a 20-row snippet buffer; production staging adopts
  target-local streamed snippet shards rather than materialising snippets.
- The trial stream ABI has been replaced by a typed-event contract: analysis,
  bounded canonical row batches, navigation, then summary. Obsolete stream
  summary/navigation/`next` entry points and their Python wrappers are gone.
- Native stream allocation counters are aggregated by the build monitor outside
  semantic corpus artifacts.
- **D. Plan-owned rendered-symbol evidence is implemented.** The
  rejected implementation derived rendered-symbol evidence in a second
  traversal of the completed semantic plan before it emitted rows. That
  preserved analysis/row equivalence, but diagnostic eight-worker runs
  regressed the file-analysis rate and therefore failed the timing criterion.
  The replacement now records canonical evidence as each instruction,
  label/storage label, runtime alias, and symbolic data or equate expression
  is planned. It finalises that evidence in source order before source-quality
  analysis and the analysis event; row rendering only consumes it. Native
  ordering and pre-row event tests pass, including a direct native comparison
  of streamed rows and analysis JSON against the interactive artifact for a
  branch-plus-relocated-data fixture and a runtime-alias fixture. Python-level
  Python-level direct equivalence is covered by the native-listing-stream test;
  corpus timing/RSS/identity acceptance evidence remains outstanding.
- The first failed normal acceptance attempt exposed a separate typed-access
  record-lifetime defect: arena-grown recovered-platform-access slots did not
  initialise their optional table-origin fields when no origin was present.
  Stale bytes then produced history-dependent platform-typed facts, first
  visible in the Pandora decompressed target.  The append boundary now
  initialises every new record; consecutive native stream analyses of that
  target produce identical semantic analysis JSON.
- A fresh normal eight-worker run after that repair completed all 319 file
  entries and 59 project targets with real concurrent analysis.  File/project
  phases took 284.18/306.81 seconds, under the 286.07/309.87-second baselines,
  but peak process memory remained 15.61 GiB, above the 11.80 GiB limit.  Its
  high-water mark occurred during concurrent project-target analysis rather
  than report publication.  The remaining work was therefore to locate and
  remove that concurrent native allocation or retention, not to weaken worker
  concurrency or comparison.
- That allocation was the Amiga typed-reference flow graph: it reserved a
  full typed/platform in/out state for every decoded candidate while creating
  nodes only for accepted starts.  The graph now counts accepted starts first
  and allocates its nodes exactly once at that count; no queue chunking,
  worker reduction, or target exception is retained.  A normal eight-worker
  rerun completed all 428 entries with a 10.46 GB (9.74 GiB) peak, clearing
  the RSS gate and retaining a maximum of eight active analysis workers.
  It took 354.31 s for file analysis and 440.93 s for project analysis, so it
  failed the timing gate. The current typed-flow lifecycle worktree has since
  repeated the isolated comparison: its one-worker build completed all 428
  entries in 1,537.97 s and is byte-identical to its eight-worker manifest,
  xrefs, snippet index/blob, variants, type-flow, unresolved-field, and
  coverage artifacts. This proves concurrency determinism for the current
  code, not acceptance; a non-regressing timing run remains required.
- The queue's trace-state storage now has its own reachability-only arena and
  is released before source analysis and rendering.  That is a correct
  lifetime boundary, but it was not the material RSS reduction: a queue
  chunking experiment did not lower the peak and was removed.  The exact-size
  typed-flow allocation is the retained memory correction.
- A later typed-reference fixed-point lifecycle improvement avoids recording a
  typed-access final pass that is necessarily discarded before the required
  post-callback pass.  On the large Pandora stream target it reduced the
  typed-reference phase from 24.88 s to 20.83 s (45.83 s to 41.89 s total).
  The latest normal eight-worker run kept the memory result (9.39 GiB peak)
  but took 440.42 s for file analysis and 560.55 s for project analysis, so it
  also failed the timing gate.  Its output counts matched the prior run, but
  the matching current one-worker run took 643.75 s for file analysis and
  665.71 s for project analysis; all normal artifacts were byte-identical to
  the eight-worker run.
- Reusing the immutable typed-flow topology across the adjacent direct and
  post-callback solves removes a second graph construction without extending
  its lifetime beyond typed-reference analysis. A normal eight-worker run
  after that change completed all 428 entries with byte-identical normal
  artifacts and a 10.09 GB (9.39 GiB) peak. File/project analysis improved to
  334.45/486.71 s, but remains above the 286.07/309.87-second baselines.
- When callback-summary discovery adds no new summary, the already-converged
  typed-flow graph now performs only the required final access-recording walk;
  a full second solve remains mandatory when callback facts change. On the
  King project target, typed-reference time fell from 46.36 s to 16.82 s and
  total stream time from 200.86 s to 115.18 s. The ensuing normal eight-worker
  run kept every normal artifact byte-identical, reduced peak RSS to 8.47 GiB,
  and passed file analysis at 256.62 s. Project analysis improved to 367.19 s
  but still exceeds its 309.87-second baseline, so acceptance remains open.
- One/eight-worker identity, full-suite, timing, and RSS acceptance evidence
  is therefore still not satisfied for the production stream path.

## Blocked-Path Investigation and Decision

This is an in-repository implementation gap, not a harness bug, worker-loop
problem, external dependency, or request for user intervention. The previous
workflow-level `blocked` status does not describe a technical impasse and must
not be read as evidence that the proposal is complete or unable to progress.

The native transient visitor is adapted into canonical order before
publication: the adapter retains only preamble lines needed for the existing
diagnostic, include, and equate ordering, and delegates every emitted line to
the existing canonical row serializer. It preserves stable row IDs and row
metadata without creating a render plan or index. That solves row authority,
but not the collector's whole-list contract.

The audit found four exact dependencies on the complete list:

- analysis-derived xrefs resolve `(section_index, offset)` to the highest-rank
  listing row (instruction, data, directive, then label);
- listing xrefs and features need the canonical row and a contiguous
  direct-control-stub run, ignoring zero-width labels;
- snippets select the union of all `row_index +/- 20` windows; and
- navigation labels supply definition/reference counts and stable locations.

None requires retaining all rendered rows. They do require an ordered protocol
with explicit non-row events, a deterministic location-resolution rule, and a
bounded finalisation rule. The sole accepted design is therefore a single
native forward stream with typed events and one shared Python ordered
projector. The stream emits `analysis` before rows, bounded canonical `rows`
batches in order, then `navigation` and `summary` after the last row. The
native serializer owns canonical row and navigation meaning; Python only
projects those authoritative values into existing corpus features, xrefs, and
snippets.

The following paths were explored and rejected:

| Path | Rejection reason |
| --- | --- |
| Python `start,count` paging over the artifact | Already measured: it leaves the native complete plan/index live, regresses time, and did not preserve xrefs/type-flow. |
| Keep the current mixed analysis/row callback and error-returning legacy calls | Ambiguous event schema and incomplete payload contract; it would institutionalise transitional API surface. |
| Rebuild navigation or row meaning in Python | Creates a second renderer/semantic authority and risks divergence. |
| Stage all rows in a temporary file or database | Moves the forbidden full-list retention to another owner and adds I/O churn. |
| Re-run native analysis for relation or snippet passes | Repeats the dominant work and violates the single-pass performance requirement. |
| Reduce workers, retry, cache, or retain the old collector as a fallback | Contradicts the goal and masks rather than removes the native ownership problem. |

The recommended path has no compatibility layer: replace the trial stream ABI
before production migration, remove its obsolete summary/navigation/`next`
functions and their Python wrapper methods, and retain the interactive artifact
only as its separate random-access product and migration oracle.

## Current Block and Exit Criteria

Typed events, canonical row/navigation serialization, and the shared ordered
projector are implemented. D's planner-owned evidence implementation is in
place; its remaining block is direct stream/artifact equivalence and corpus
acceptance evidence.

### D. Produce canonical rendered-symbol evidence during semantic planning

The planner must own one canonical rendered-symbol-evidence product and append
each identity at the same point it accepts the corresponding semantic decision:

- an instruction's planned symbol accesses;
- a planned label or storage-label declaration; and
- a planned runtime alias; and
- a symbolic data, relocation, relative-table, or equate expression that the
  renderer will emit.

The resulting evidence must be complete as soon as semantic planning finishes.
Source-quality analysis and the `analysis` event consume it before any row
event. The subsequent row walk renders each source row once and only consumes
the planned evidence; it must not perform a second plan-wide evidence pass,
append evidence, or retain completed row text/index state. The interactive
artifact must consume the same canonical evidence representation, so its
semantic analysis content and the stream's semantic analysis content remain
identical.

Focused source-order and pre-row tests now cover instructions, labels, and a
relocated data expression; a native direct fixture also compares streamed rows
and analysis JSON with the interactive artifact, including a runtime alias.
The focused Python stream/projector suite, full C unit suite, and full Python
suite (1,375 passed, 58 skipped) pass. Python also directly compares the
native stream with the interactive artifact for rows, analysis, navigation,
and zero stream-owned complete-plan/index bytes. The C fixtures add
branch/relocated-data and runtime-alias coverage. The current-worktree
one/eight artifact comparison also passes. D's semantic, direct-equivalence,
and identity requirements are therefore met; the proposal remains in progress
solely because no normal eight-worker run has met the analysis-time criterion.
The 11.80 GiB peak-RSS gate has passed at normal eight-worker concurrency, but
must accompany the eventual passing timing acceptance run.

Until D and these acceptance checks pass, the proposal remains in progress and
corpus production must continue using the existing random-access artifact.

## Goal

Provide an authoritative corpus-listing stream that preserves exactly the
existing source rows, row indices, source/runtime addresses, stable keys,
xrefs, features, snippets, and ordering, while avoiding a complete rendered
row/text plan for a corpus target.  Correct the random-access plan's separate
growth-retention fault by giving temporary construction and final published
storage explicit lifetimes with no retained overlap after finalisation.  Eight workers remain real
concurrent analysis workers; no reduced-worker mode, retry, cache, target
exclusion, or reduced-fidelity corpus mode is permitted.  The normal
eight-worker peak must fall by at least 30% from the 16.85 GiB baseline
(at most 11.80 GiB under the same measurement method).

## Design

### Separate temporary construction from published plan storage

Published `M68kRenderPlan` arrays no longer grow with `arena_realloc_copy`.
Do not add an arena per capacity generation or make a
general-purpose arena free individual allocations; both obscure ownership and
would be unsafe for unrelated arena users.

Instead introduce explicit lifetimes:

1. The plan builder owns temporary append-only storage in one builder arena.
   It is the only object allowed to grow while planning.
2. `m68k_render_plan_finalize` determines exact counts and allocates
   each published plan array once in a dedicated final-plan arena, then copies
   the completed values.
3. The builder arena is destroyed immediately after finalisation.  The final
   plan owns no temporary chunk and never grows.

Rows, expressions, declarations, instructions, labels, runtime aliases, and
row text follow this rule.  The builder must expose lookup operations needed
during planning without materialising a prematurely published contiguous
array.  This ownership correction applies to every `M68kRenderPlan` producer,
not merely the corpus path, so the core plan model has one lifetime rule.  The
existing random-access artifact may retain this final exact-size plan and its
index because that is its explicit contract.

### Split semantic planning from corpus row ownership

Refactor the native renderer into two explicit products:

1. A compact, immutable semantic render layout containing only the facts
   needed to make rendering decisions: analysis facts, symbol/declaration
   decisions, section/range order, and the deterministic header layout.
2. A sequential row emitter that traverses that layout once and writes each
   authoritative row to a sink.  It must not allocate or retain the complete
   `M68kRenderPlan` row text or complete listing row index.

The corpus stream uses the semantic layout directly and never finalises a
random-access plan or row index.  The existing random-access artifact remains
supported for interactive uses that genuinely require it.  Both paths share
the same renderer and row-serialization primitive; there must not be a second
Python renderer or corpus-specific interpretation of source facts.

### Native stream ABI

Add a C-owned corpus stream handle with these operations:

- create from the same source, metadata, and policy inputs as the existing
  listing artifact;
- visit typed events: exactly one analysis event before any rows, bounded
  canonical row-batch events in row-index order, exactly one navigation event
  after rows, then exactly one summary/profile event;
- destroy the handle.

The stream is forward-only and single-use. It has no `start,count`, `next`, or
post-hoc summary/navigation contract, because each either implies random
access or an ambiguous partial lifecycle. A typed event discriminator is part
of the C ABI, not inferred from JSON keys. Batch JSON is the initial payload
encoding; its builder is scoped to one bounded batch and freed before the next
batch. The navigation event is generated by the native canonical serializer's
navigation context while rows are emitted, not reconstructed in Python.

### Exact corpus projection

Replace the current all-list projection with a single ordered collector that
consumes the native stream once.  It maintains only:

- the bounded current batch, direct-control confirmation state, and a 20-row
  rolling buffer;
- a scalar end index for the merged active `row_index +/- 20` snippet interval
  and the last compact row appended to target-local snippet staging;
- target-local xrefs and compact snippet rows already owned by existing
  staging.

Before row delivery, the projector turns analysis relationships into pending
obligations keyed by `(section_index, offset)`. At each equal-location row
group it applies the existing rank rule (instruction, data, directive, label),
then resolves and emits those obligations. This retains relation obligations,
not unrelated rendered rows. It consumes analysis features and builds those
obligations before the first batch, then releases the decoded analysis payload.
The first possible direct-control row is deferred only until the next non-label
row confirms or rejects a two-row run; confirmed subsequent rows are emitted
immediately, so run detection is constant-space.
When an xref opens or extends a snippet interval, the projector appends the
needed rows from its 20-row rolling buffer, then appends each newly eligible
compact row directly to target-local staging. A scalar interval end and last
appended index prevent duplicates even when xrefs make one interval span a
whole target. The navigation event is applied after row completion for
label-count features. Location resolution is supplied by durable row metadata,
never reconstructed from text.

### Allocation evidence

Add native allocation/ownership counters to the stream profile, reported per
target and aggregated by the build monitor:

- builder-arena bytes, final-plan-arena bytes, and the momentary finalisation
  overlap, each separately;
- semantic layout bytes;
- source-analysis bytes where measurable;
- live row batch bytes and maximum rows;
- transient JSON bytes;
- complete render-plan/index bytes (zero for the corpus stream).

These fields are observability only.  They must never alter scheduling or
corpus content.  They are required before claiming a memory improvement, so
the next build can distinguish source-analysis pressure from rendering
materialisation rather than infer it from process RSS alone.

## Invariants

- Analyse all 319 file entries and 59 project targets.
- Preserve manifest, xref, snippet index/blob, variant, type-flow,
  unresolved-field, and coverage schemas and byte identity across one and
  eight workers.
- Preserve byte-identical rendered source and random-access listing output.
  Profile payloads may differ only in timing and allocation-observability
  fields; they are not semantic corpus output.
- Preserve current stable xref IDs, snippet IDs, ordering, compression inputs,
  and row-index semantics.
- Keep C source analysis and rendering authoritative.
- Publish artifacts atomically only after successful completion.
- Treat stream failure as an explicit target analysis failure with coverage
  evidence; never silently omit or retry a target.

## Implementation Plan

1. Add allocation counters around artifact construction, builder growth,
   final-plan creation, row indexing, and window JSON construction.  Profile
   known large targets to establish the exact native owners.
2. Introduce the builder/final-plan split.  Add direct C tests that force
   repeated growth and prove that final-plan capacity is exact, builder storage
   is released at finalisation, and the existing random-access listing is
   byte-identical.
3. Extract the renderer's semantic-layout pass from final row/text storage,
   with direct C tests proving emitted rows are identical to the existing
   render plan for representative code, data, labels, late declarations, and
   runtime aliases.
4. Complete D acceptance: verify the planner-owned rendered-symbol evidence,
   emitted before the analysis event and consumed without a second plan-wide
   pass or row-walk mutation, against the interactive artifact. Verify terminal
   payloads, allocation bounds, and batch-boundary invariance at direct-control
   runs, labels, runtime aliases, and overlapping snippet contexts.
5. Refactor file and project collection to one shared ordered projector. Feed
   analysis relations into its pending-location scheduler, stream rows through
   row feature/xref reducers, append merged snippet intervals incrementally to
   target-local staging, and release the decoded analysis payload before row
   delivery. Use the former all-list collector only as a migration test oracle,
   then remove it from production.
6. Run isolated one-worker and eight-worker builds and compare every normal
   corpus artifact and random-access rendered-source/listing fixture
   byte-for-byte.  Record phase timings, allocation counters, and peak process
   memory separately from semantic-output comparison.

## Acceptance Criteria

- Published random-access plans retain no superseded growth allocations;
  temporary builder storage is destroyed immediately after finalisation.
- Corpus stream creation retains no complete render plan, complete listing row
  index, or complete rendered source text.
- One and eight worker outputs are byte-identical to the pre-change corpus for
  all normal artifacts.
- Existing random-access rendered-source and listing fixtures are
  byte-identical.  A discovered semantic defect is not repaired incidentally:
  it requires a separate proposal, acceptance case, and regression coverage.
- The normal eight-worker build completes all 428 entries with no new coverage
  failures and real concurrent analysis.
- Measured peak memory is materially below the 16.85 GiB baseline, with
  counters attributing the reduction to removed native render materialisation;
  the normal eight-worker peak is at most 11.80 GiB under the baseline method.
- Analysis time does not regress; the stream renders each source row once per
  target rather than once per Python page.
- C unit tests and the full Python suite pass.  No canonical corpus output is
  replaced until isolated artifacts validate.

## Non-Goals

- Lowering worker count, skipping targets, changing snippet radius, dropping
  xrefs, caching stale listings, retries, or target-specific exceptions.
- Changing M68K analysis, pointer propagation, rendering meaning, or corpus
  feature semantics.
- Maintaining the rejected Python paging collector as a fallback.
