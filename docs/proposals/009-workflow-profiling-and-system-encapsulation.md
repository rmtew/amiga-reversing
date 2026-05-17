# Proposal 009: Workflow Profiling And System Encapsulation

Status: Ready for implementation after current-state review.

Status changed: 2026-05-17.

## Contents

- Why This Exists
- Goals
- Mental Model
- Current State Read
- Integration Findings
- Chosen Path
- Implementation Guidance
- Forward Implementation Model
- Artifact Ownership
- Non-Goals
- Proposed Rewrite
- Acceptance Criteria
- Deletion Checklist
- Rewrite Acceptance Tests
- Verification
- Implementation Evidence

## Why This Exists

The web UI now brings together several framework paths:

```text
manual action
  -> Manual Action Log
  -> effective metadata
  -> C analysis / listing projection
  -> Source Rendering
  -> Project Rebuild
  -> Reproduction Comparison
  -> browser state update
```

Users may also use narrower paths:

```text
Source Export:
  Source Rendering -> browser-delivered source text

source assembly comparison:
  Source Rendering -> Assembly -> Reproduction Comparison

normal exactness gate:
  Project Rebuild -> Reproduction Comparison
```

These paths work, but they are not yet encapsulated in a way that makes
performance and cleanup straightforward. The UI can feel slow during manual
editing, and the current answer to "what was slow?" depends on which layer the
developer inspects.

The goal is not to add many timers. The goal is to make workflow state and timing
first-class enough that each system can be improved independently.

## Goals

Make these workflows measurable and easier to refactor:

```text
manual edit application
listing projection and locator resolution
Source Rendering
Source Export
Project Rebuild
Assembly
Reproduction Comparison
Round-Trip Verification
oracle/tool capability workflows
browser fetch/render/update work
LLM-driven API and browser verification workflows
```

The proposal should support two kinds of work:

```text
diagnosis:
  where did time go for this user-visible action?

cleanup:
  which module owns this phase and what can be deleted or deepened?

LLM iteration:
  can an agent inspect state, run the same command path as the UI, read profile
  spans, and decide the next focused change without scraping incidental DOM text?
```

## Mental Model

Think of the system as nested workflows with correlated spans:

```text
browser interaction span
  -> API route span
  -> workflow span
  -> C API span
  -> C internal phase spans
  -> report/debug payload
```

Proposal 007 already made the Web UI stack more LLM-operable by standardizing
locators, command routes, semantic assertions, server debug state, and browser
debug state. This proposal should extend that same surface with workflow spans:

```text
LLM agent
  -> read server/browser debug state
  -> choose locator or command context
  -> execute API/browser command
  -> read workflow profile
  -> inspect affected durable/projection state
  -> decide whether slowness belongs to UI, Python, C API, or C internals
```

The key questions are:

```text
For a user-visible workflow:
  Which durable inputs define the work?
  Which generated or cached artifacts did it use?
  Which module owns each phase?
  Which spans explain elapsed time?
  Which result payload carries the profile?
```

This makes profiling a state contract, not ad hoc debug output.

## Current State Read

The system already records useful local timings, but there is no shared profile
contract. Round-Trip Verification writes `profile_timings`, C backend calls
return profile JSON, target benchmark reports capture C phase timings, and the
browser stores listing fetch/render samples.

Those pieces are enough to start, but they are not correlated. A developer can
see that something was slow only after choosing the right layer to inspect.

The code also has three clear maintainability pressure points:

```text
Round-Trip Verification:
  one large orchestration body owns phase selection, timing, report shaping, and
  error exits

Source Rendering:
  Source Export and source-gate reproduction call the renderer directly and each
  owns pieces of refusal/profile handling

Manual command execution:
  normal locator resolution can still materialize all listing rows
```

The direction matches the existing ADRs: C owns Reproduction Comparison, Python
owns Round-Trip Verification orchestration and UI row mapping, Manual Action Log
remains the durable manual-review state, and local C interfaces can change
without compatibility bridges because this repository is the only consumer.

Proposal 007 has already moved the web UI toward durable state contracts.
Proposal 008 already tracks the separate tool graph work.

## Integration Findings

### 1. Profiling Exists But Has No Shared Contract

Profiling data is spread across:

```text
PhaseTimer
reproduction profile dicts
C backend profile JSON
target benchmark reports
browser fetch stats
test integration timing summaries
```

Each shape is reasonable locally. Together, they make correlation hard. The fix
is one shared workflow profile envelope, not more unrelated timing dicts.

Target shape:

```json
{
  "workflow_id": "round_trip_verification",
  "target_id": "amiga_hunk_bloodwych",
  "input_stamp": "hash-or-stamp-summary",
  "spans": [
    {"name": "direct_rebuild", "seconds": 0.18, "module": "c_backend"},
    {"name": "reproduction_compare", "seconds": 0.02, "module": "c_backend"}
  ]
}
```

This does not replace detailed C profiles. It gives them one envelope.

### 2. Round-Trip Verification Is Too Broad Internally

`run_reproduction()` owns:

```text
input stamp resolution
output directory setup
direct rebuild
optional source compare
source render fallback
assembly
diffing
Reproduction Comparison
row issue mapping
report writing
profile merging
```

The external workflow can remain one call, but the implementation is a shallow
module internally: too many phases share one local dictionary and one
control-flow body.

Target shape:

```text
RoundTripWorkflow.run()
  prepare()
  run_project_rebuild()
  maybe_run_source_rendering_gate()
  maybe_run_source_assembly_debug_path()
  compare()
  write_report()
```

The interface stays small. The implementation gets locality. This must respect
ADR-0001: direct Project Rebuild plus Reproduction Comparison stays the normal
path; source assembly remains a source gate or debug/comparison path.

### 3. Source Rendering Is Reused Without A Deep Module

Source Export and source-assembly reproduction both call into Source Rendering,
but refusal handling, profile handling, headers, and workflow result shape are
owned by callers.

Target shape:

```text
SourceRenderingWorkflow.render(target, assembler_profile)
  -> source_text
  -> listing_profile
  -> refusal payload
  -> spans
```

Then Source Export and Round-Trip Verification become callers. They should not
decode renderer refusal, C profile JSON, or source-rendering headers themselves.

### 4. Manual Editing Can Resolve Too Much Listing State

Command context resolution uses locators, but server command execution can still
load every listing row to resolve one locator:

```text
_resolve_command_locator()
  -> _all_listing_rows()
  -> artifact.window_payload(start=0, count=total_rows)
```

For large listings, this is a likely latency source for manual editing.

Target shape:

```text
ListingProjectionService.resolve_locator(locator)
  uses row_key index or recovery index
  does not materialize the whole listing for normal row/element commands
```

Range commands may need more rows, but the interface should make that cost
explicit.

### 5. Local C API Adapters Repeat Ownership And Profile Handling

`c_backend.py` has repeated patterns:

```text
call C function
collect output pointer
collect profile JSON pointer
collect error pointer
decode JSON
raise refusal or operation failure
free C buffers
```

This is a good candidate for a deep Local C API adapter module. The interface
should express operation kind and result shape; the implementation should own
ctypes pointer cleanup and profile parsing. This is internal cleanup only, not a
compatibility layer.

### 6. Browser Timing Is Useful But Not Connected To Backend Spans

The browser stats panel can show listing fetch latency, and
`window.__amigaDebugState()` exposes browser debug state, but backend job spans
and route spans are not correlated with the browser sample that caused them.

Target shape:

```text
browser request id
  -> API response profile id
  -> backend workflow spans
  -> browser fetch/render sample
```

This is especially useful for manual editing, where perceived slowness may be:

```text
locator resolution
Manual Action Log append
effective metadata projection
C analysis
listing projection
network fetch
DOM render
```

### 7. Tool Capability Work Is Related But Separately Tracked

Proposal 008 already specifies the Tool Registry replacement with a runtime-aware
tool graph. This proposal should not reopen that design. It should consume tool
capability spans later, after the tool graph exists.

### 8. Proposal 007 Created An LLM-Operable Surface

Proposal 007 includes an LLM verification surface: server debug state, browser
debug state, locators, command availability, command execution, and semantic
assertion helpers.

That surface is currently strongest for correctness and durability. Proposal 009
should use it for performance and workflow cleanup too.

Target shape:

```text
same workflow harness:
  assert semantic state
  collect workflow spans
  record cache/projection stamps
  report frontend/backend split
```

This avoids a separate "LLM automation interface". LLM operability is just
another consumer of the same module interfaces and debug contracts.

## Chosen Path

Start with the shared workflow profile contract, then apply it to the manual-edit
path before refactoring the larger workflows. This gives immediate visibility
into the slow interactive path while keeping the first implementation slice
small.

Recommended order:

```text
1. Shared workflow spans and browser/backend correlation
2. Manual edit latency trace and indexed locator resolution
3. Source Rendering module
4. Round-Trip Verification phase module
5. Local C API adapter cleanup
6. LLM-operable profiling harness coverage
7. Optional tool graph integration after Proposal 008 is ready
```

Do not start with speculative caching or broad rewrites. Measurement and module
ownership should move together: each slice should either add a shared span
contract, remove duplicated ownership, or make a caller depend on a deeper
module.

## Implementation Guidance

### Workflow Span Contract

The first step is a small shared contract. Do not start by rewriting every
workflow.

#### Step 1: Define Shared Span Records

Create a Python module such as:

```text
amiga_reversing/disasm/workflow_profile.py
```

Illustrative types:

```python
WorkflowSpan:
  name: str
  seconds: float
  module: str
  detail: dict[str, object]

WorkflowProfile:
  workflow_id: str
  target_id: str | None
  input_stamp: dict[str, object] | None
  spans: list[WorkflowSpan]
  counters: dict[str, int | float | str | bool]
```

`PhaseTimer` can become an adapter or internal helper.

#### Step 2: Attach Spans To Existing Reports

Add a shared profile envelope to report and API payloads:

```json
{
  "profile": {
    "elapsed_seconds": 0.2,
    "direct_rebuild_seconds": 0.17
  },
  "workflow_profile": {
    "workflow_id": "round_trip_verification",
    "spans": []
  }
}
```

Do not create a long-lived compatibility bridge. Where existing in-repo tests or
UI code still read old `profile` fields, update them in the same implementation
slice or keep the old fields only as canonical report fields with a deletion
date in the slice notes.

#### Step 3: Expose Spans In Browser Debug State

For browser workflows, expose through `window.__amigaDebugState()` and the
server debug-state helper or route:

```text
last_api_request_id
last_workflow_profile
last_listing_fetch_sample
last_manual_mutation_profile
```

This belongs in debug state, not visible feature text.

#### Step 4: Add Regression Budgets Without Hard Timing Gates

Timing is noisy. Initial tests should assert shape and relative attribution, not
wall-clock thresholds.

Good tests:

```text
manual edit result includes locator_resolution span
reproduction report includes direct_rebuild span for direct path
source export includes source_rendering span
browser debug state records fetch/render split
```

Avoid:

```text
test fails if manual edit takes more than 100ms
test fails if Bloodwych render is slower than last run
```

### Manual Edit Latency Trace

Start with the user-visible slow path:

```text
row/element command
  -> locator resolution
  -> command catalog
  -> Manual Action Log append
  -> cache invalidation or presentation dirty mark
  -> mutation result
  -> optional listing refresh
  -> browser render
```

Add spans around:

```text
command_context
locator_resolution
command_catalog
manual_action_append
manual_action_application
listing_cache_invalidation
response_build
```

Then replace all-row locator resolution where measured:

```text
row_key index
recovery identity index
range resolver for bounded row ranges
```

### LLM-Operable Profiling Harness

Build on Proposal 007's API/CDP workflow harness rather than creating a parallel
agent-only path.

An LLM-operable profiling workflow should be able to:

```text
open or select a target
read server debug state
read browser debug state when a browser is involved
resolve or reuse a ListingRowLocator
query command availability
execute the command through the normal API route
read the Authoritative Mutation Result
read workflow_profile spans
assert semantic state after refresh/reopen when needed
produce a concise diagnosis
```

Example manual edit loop:

```text
1. GET /api/debug/state or equivalent server debug route
2. GET /api/projects/{target}/listing
3. select row by locator, not row text
4. GET /api/projects/{target}/commands?context=row&locator=...
5. POST /api/projects/{target}/commands/execute
6. inspect mutation, projection hash, manual action log count/head hash
7. inspect workflow_profile spans
8. decide whether to optimize locator resolution, projection, C analysis, or DOM render
```

The harness should report missing observability as a workflow defect. If an LLM
has to infer state by scraping DOM text or private globals, the interface is not
deep enough.

### Source Rendering Module

Source Rendering should be callable by:

```text
Source Export
Round-Trip Verification source gate
benchmark target
future UI preview or renderer comparison
```

Module interface:

```text
render_source(target, assembler_profile, metadata_path, project_root)
  -> SourceRenderingResult
```

Result fields:

```text
status: ok | refused | error
source_text
listing_profile
workflow_profile
metadata_hash
target_identity_sha256
refusal_message
```

The C implementation remains behind the module. Callers should not own C profile
decoding or refusal interpretation. Source Export may still own export headers
and filenames because those are Source Export result concerns, not rendering
concerns.

### Round-Trip Verification Phase Module

Round-Trip Verification should remain the user-facing workflow:

```text
Project Rebuild
Reproduction Comparison
optional Source Rendering source gate
optional Assembly source debug path
```

The implementation should make phase ownership explicit:

```text
RoundTripWorkflow
  prepare_inputs
  run_project_rebuild
  run_source_gate_when_requested
  run_assembly_path_when_needed
  run_reproduction_comparison
  build_report
```

The report remains understandable at the browser edge, but phase internals become
testable through the workflow interface. Since there are no external consumers,
update in-repo callers and tests directly instead of adding adapter layers.

### Local C API Adapter

Create one internal adapter for C profiled operations:

```text
CProfiledOperation.call_bytes_result()
CProfiledOperation.call_text_result()
CProfiledOperation.call_compare_result()
```

It owns:

```text
ctypes argument conversion
output buffer lifetime
error text lifetime
profile JSON parsing
FactsV2SourceRefused mapping
FactsV2DirectRebuildRefused mapping
FactsV2ProfiledOperationFailed mapping
span creation
```

This is a Local C API cleanup, not a public compatibility layer. It should
delete repeated pointer/profile ownership in touched operations rather than wrap
it with another pass-through function.

## Larger Architecture Observations

### 1. Workflow Profiling Should Be A Deep Module

The deletion test says the module earns its place. Without it, every workflow
has to rediscover:

```text
span naming
elapsed time collection
profile merging
input stamp attachment
debug payload shape
test assertions
```

### 2. Workflow Modules Should Hide Phase Complexity

Callers should ask for:

```text
run Round-Trip Verification
render source
execute manual mutation
resolve tool capability
```

They should not know every internal phase unless they are reading the returned
profile. The profile is observability, not a second control interface.

### 3. Fast UI Editing Requires Indexed Projection Locality

If a single manual action needs the whole listing, the module interface is not
deep enough. The common path should resolve the selected locator without
materializing unrelated rows.

### 4. Timing Data Must Be Correlated With Inputs

Timing without input stamps is weak evidence. Profiles should record enough
context to compare:

```text
target id
binary hash or input stamp summary
effective metadata hash
projection hash
reproduction policy
tool stamps
browser request id
```

### 5. LLM Operability Is A Consumer Of The Same Interface

An LLM should not get privileged hidden behavior. It should use the same command
routes, locators, reports, and debug state that tests and the browser use.

The extra requirement is explainability:

```text
what command ran
what durable state changed
what projection changed
what spans consumed time
what next action is justified
```

That explainability is also useful to human developers.

## Forward Implementation Model

### Workflow Span Model

One Python-owned profile contract shared by reports, tests, and browser debug
state.

### Source Rendering Workflow

One module owns source text rendering, listing profile interpretation, refusal
payloads, and source-rendering spans.

### Round-Trip Verification Workflow

One module owns phase orchestration while preserving current report behavior.

### Manual Mutation Trace

Server command execution emits spans for locator resolution, catalog generation,
manual action append, invalidation, and response construction.

### LLM Operation Harness

Shared API/CDP helpers run representative workflows and return:

```text
semantic state assertions
workflow profiles
debug-state snapshots
durable state stamps
frontend/backend timing split when browser-driven
```

### Local C API Adapter

One adapter owns ctypes buffer/error/profile patterns.

### Browser Debug Integration

Browser fetch/render timing and backend workflow profiles share a request or
workflow id.

## Artifact Ownership

Durable reports:

```text
targets/<name>/reproduction.json
targets/<name>/benchmark.json
```

Debug-only browser state:

```text
window.__amigaDebugState()
```

Transient workflow profile data may appear in API responses, but should not
become reverse-engineering facts.

Benchmark history or performance snapshots should live under docs or generated
report paths only when explicitly captured for review.

## Non-Goals

- Do not make timing thresholds exactness gates.
- Do not change Reproduction Exactness semantics.
- Do not make external tools part of the exactness gate.
- Do not add a public C ABI compatibility layer.
- Do not migrate Proposal 008 into this proposal.
- Do not preserve old internal call shapes for compatibility.
- Do not add speculative caching before profiling shows the cost.

## Proposed Rewrite

### Slice 1: Shared Workflow Span Records

Add `workflow_profile.py` and adapt one small path first.

Exit condition:

```text
Round-Trip Verification and Source Export can attach a workflow_profile payload
and in-repo consumers assert the shared shape.
```

### Slice 2: Manual Edit Latency Trace

Add backend spans for command execution and browser correlation for the matching
manual mutation.

Exit condition:

```text
a manual label/comment/representation edit reports where backend time went
```

### Slice 3: Source Rendering Module

Move Source Rendering result/refusal/profile logic behind a module consumed by
Source Export and source-gate reproduction paths.

Exit condition:

```text
source_export.py no longer calls C backend rendering directly
reproduction.py source gate no longer calls C backend rendering directly
renderer refusal/profile parsing has one owner
```

### Slice 4: Round-Trip Verification Phase Module

Refactor `run_reproduction()` internals into explicit phase functions or a
workflow object.

Exit condition:

```text
tests can exercise direct rebuild, source gate, assembly fallback, and
comparison phases through named workflow seams
```

### Slice 5: Local C API Adapter Cleanup

Centralize ctypes result/error/profile ownership for profiled C calls.

Exit condition:

```text
c_backend.py no longer repeats output/error/profile pointer cleanup blocks for
the touched operations
tests cover success, C error, refused source, and profile JSON cleanup
```

### Slice 6: Browser/Profile Correlation

Add request/workflow ids that connect browser fetch/render samples to backend
workflow profiles.

Exit condition:

```text
browser debug state can show the last manual mutation or listing fetch with
backend and frontend timing split
```

### Slice 7: LLM-Operable Profiling Harness

Extend the Proposal 007 workflow harness to collect and assert workflow profiles.

Exit condition:

```text
one representative manual edit workflow can be driven through API and CDP
helpers, then reported with semantic state, durable stamps, and workflow spans
without scraping DOM text as authority
```

### Slice 8: Optional Tool Graph Integration

After Proposal 008 Slice 1, attach workflow spans to capability resolution and
oracle invocation chains.

Exit condition:

```text
oracle reports show tool capability resolution and invocation timing through the
same workflow profile contract
```

## Acceptance Criteria

- Manual edit API results can include backend workflow spans.
- Browser debug state can correlate one user-visible action with backend spans.
- LLM workflow helpers can drive at least one representative command through the
  same API/browser stack and read semantic state plus workflow spans.
- Source Export and the Round-Trip Verification source gate share Source
  Rendering behavior.
- Round-Trip Verification phase timing is expressed through shared span records.
- C backend profiled operations use one adapter for touched pointer/profile
  ownership.
- Locator resolution for normal row/element manual commands does not require
  materializing the whole listing.
- In-repo report consumers are updated with the workflow profile contract; no
  compatibility bridge is added for external consumers.
- Timing tests assert profile shape and attribution, not fragile thresholds.
- The implementation preserves ADR-0001 ownership: C owns Reproduction
  Comparison; Python owns Round-Trip Verification orchestration and row mapping.
- The implementation preserves ADR-0004 ownership: Manual Action Log remains the
  durable source for manual review state.

## Deletion Checklist

Delete or replace:

```text
ad hoc profile merging helpers made obsolete by workflow_profile.py
unused PhaseTimer or duplicate timer helpers after workflow_profile.py lands
duplicate Source Rendering refusal/profile handling
duplicate ctypes output/error/profile cleanup blocks for touched C calls
all-row locator resolution for normal row/element command execution
browser-only timing samples that cannot be correlated with backend work
```

Do not delete:

```text
canonical report fields still displayed by the browser until the slice updates
that browser/report contract
target benchmark reports
Proposal 008 tool graph issue work
```

## Rewrite Acceptance Tests

Required focused tests:

```text
workflow profile serializes stable span records
Source Export includes source_rendering span
Round-Trip Verification direct path includes direct_rebuild and comparison spans
manual row command includes locator_resolution and manual_action_append spans
normal row locator resolution avoids all-row materialization
C adapter frees output/error/profile buffers on success and failure
browser debug state exposes last correlated workflow profile
LLM-operable workflow harness reports semantic state, durable stamps, and spans
```

Regression tests:

```text
existing source export tests
existing reproduction tests
existing server command tests
existing web app source tests
focused CDP test for manual edit debug/profile state
```

## Verification

Minimum focused verification for implementation slices:

```powershell
uv run python -m pytest tests\test_source_export.py tests\test_reproduction.py tests\test_disasm_server.py -q
uv run python -m pytest tests\test_web_app_source.py -q
```

For C backend adapter changes:

```powershell
uv run python -m pytest tests\test_c_backend.py -q
```

For browser correlation:

```powershell
$env:M68K_RUN_BRAVE_CDP='1'
uv run python -m pytest tests\test_web_e2e_cdp.py -q
```

For final proposal slices:

```powershell
cmd /c src\precommit.bat
```

If a timing-related command is skipped because it is noisy or requires local
tools, record the skipped command and the reason in the implementation issue or
proposal follow-up notes.

## Implementation Evidence

Implemented slice evidence:

```text
009-001:
  Added shared WorkflowProfile/WorkflowSpan records.
  Source Export returns a source_rendering workflow span.
  Round-Trip Verification direct rebuild reports return direct_rebuild and
  reproduction_compare workflow spans.
  Focused tests passed:
    uv run python -m pytest tests\test_workflow_profile.py tests\test_source_export.py tests\test_reproduction.py -q

009-002:
  Manual command execution responses return workflow_profile.
  The normal command route records command_context, locator_resolution,
  command_catalog, manual_action_append, manual_action_application,
  listing_cache_invalidation, and response_build spans.
  The API workflow harness can require manual mutation workflow spans.
  Focused tests passed:
    uv run python -m pytest tests\test_api_workflow_harness.py tests\test_disasm_server.py -q

009-003:
  ListingProjectionService owns row-key and recovery-identity indexes populated
  from normalized windows.
  Normal row/element command locator resolution uses the indexed/artifact-local
  resolver instead of materializing all listing rows.
  Range command resolution remains explicitly on the all-row path.
  Focused tests passed:
    uv run python -m pytest tests\test_listing_projection.py tests\test_disasm_server.py -q
  Lint passed:
    uv run ruff check amiga_reversing\disasm\listing_projection.py amiga_reversing\disasm\server.py tests\test_listing_projection.py tests\test_disasm_server.py

009-004:
  Source Rendering is now a dedicated module owning the C renderer call,
  listing profile, refusal interpretation, metadata hash, target identity hash,
  and source_rendering workflow span.
  Source Export and Round-Trip Verification source rendering paths consume the
  module instead of calling the C backend renderer directly.
  Focused tests passed:
    uv run python -m pytest tests\test_source_rendering.py tests\test_source_export.py tests\test_reproduction.py -q
  Lint passed:
    uv run ruff check amiga_reversing\disasm\source_rendering.py amiga_reversing\disasm\source_export.py amiga_reversing\disasm\reproduction.py tests\test_source_rendering.py tests\test_source_export.py tests\test_reproduction.py

009-005:
  Round-Trip Verification now has named phase seams for direct rebuild, source
  rendering, source assembly, and Reproduction Comparison.
  run_reproduction() calls those seams while preserving the direct rebuild plus
  Reproduction Comparison normal path.
  Focused tests passed:
    uv run python -m pytest tests\test_reproduction.py tests\test_disasm_server.py -q
  Lint passed:
    uv run ruff check amiga_reversing\disasm\reproduction.py tests\test_reproduction.py
```

Observed during implementation:

```text
Direct Project Rebuild can already perform the Reproduction Comparison inside
the C direct rebuild operation. The workflow profile represents this as a
reproduction_compare span with mode=direct_rebuild_compare and zero extra
Python elapsed time, so the report still shows the user-visible phase without
pretending a second backend call happened.

Manual command execution still resolves locators through the existing
all-listing materialization path. 009-002 intentionally exposes that cost before
009-003 replaces the common row/element path with indexed projection locality.

The test suite includes simple one-row artifacts that do not expose the C
artifact's source-offset row lookup. The indexed resolver keeps a bounded
single-row fallback for that shape; production C artifacts use
row_for_source_offset and normal browser-origin commands use the row index built
when the listing window is normalized.

Source Rendering needed two consumer shapes: Source Export wants a refusal
payload, while Round-Trip Verification wants the existing
FactsV2SourceRefused exception path. The module owns refusal detection and
offers both result and raise-on-refusal helpers so callers do not decode the C
profile themselves.

The first Round-Trip Verification extraction deliberately stopped at phase
functions rather than a full workflow object. That made direct rebuild, source
rendering, source assembly, and Reproduction Comparison directly testable
without rewriting report construction in the same slice.
```

Current code evidence:

```text
amiga_reversing/disasm/reproduction.py
  run_reproduction() owns source rendering, direct rebuild, assembly,
  comparison, report construction, profile merging, and row issue mapping.

amiga_reversing/disasm/source_export.py
  Source Export calls listing_artifact_source_text_with_c_backend_profile()
  directly.

amiga_reversing/disasm/server.py
  _resolve_command_locator()
    -> ListingProjectionService.resolve_locator(rows=_all_listing_rows(...))
    -> _all_listing_rows()
    -> artifact.window_payload(start=0, count=total_rows)

amiga_reversing/disasm/listing_projection.py
  resolve_locator() normalizes and scans caller-provided rows.

amiga_reversing/disasm/c_backend.py
  profiled operations repeat output pointer, error pointer, profile JSON, and
  free-buffer handling.

amiga_reversing/web/app.js
  recordListingFetchSample() stores queue/fetch/render timings.
  window.__amigaDebugState() exposes browser debug state.

tests/workflow_harness.py
  already asserts semantic state, server debug-shaped state, and browser
  debug-shaped state for representative workflows.
```

Current benchmark reports already show useful backend attribution. Examples:

```text
amiga_hunk_bloodwych:
  total=2.212s analysis=0.586s render_ir=1.607s

amiga_hunk_genam:
  total=0.607s analysis=0.138s render_ir=0.461s

amiga_hunk_monam302:
  total=0.724s analysis=0.132s render_ir=0.572s
```

Relevant ADR constraints:

```text
ADR-0001:
  C owns Reproduction Comparison; Python owns Round-Trip Verification
  orchestration, reporting, and UI row mapping.

ADR-0002:
  Local C interfaces may change because this repository is the only consumer.
  Avoid compatibility layers that preserve old lifetime complexity.

ADR-0004:
  Manual review state is the Manual Action Log plus projection.
```
