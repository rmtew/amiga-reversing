# 017-031: Evidence-Driven Analysis Architecture Inventory

Status: implemented

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: evidence-driven analysis architecture inventory
- Current proposal state: 017 defines the Evidence-Driven Analysis Protocol as
  the master working specification, but the concrete rewrite scope is not fixed
  until current analysis architecture is researched.
- Desired proposal state after this issue: 017 includes a checked architecture
  map, reuse/replace findings, rewrite-scope boundaries, and a recommended
  first implementation slice.

## Protocol Delta

- Adds: verified current-architecture inventory for target load,
  auto-analysis, fact/state ownership, reports, commands, rendering,
  verification, and Pandora-specific surfaces.
- Changes: proposal rewrite scope from preliminary direction to research-backed
  plan.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: v2 implementation, default behavior changes,
  opportunistic refactors, old-code deletion, broad Pandora mutation runs.

## Default Behavior

- Unchanged, v2 internal only: no v2 implementation in this issue.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: none, except updated proposal/issue documentation.

## Pandora Proof

- Target candidate: current Pandora RSSET/A5/immediate report surfaces,
  especially `rsset-raw-a6:022E`, source-offset immediate `s0:000009A6`, and
  A5 hardware/base evidence surfaces.
- Evidence packet expected: not implemented here; research must define what the
  first packet slice should cover.
- Decision behavior: not implemented here; research must map current
  Manual Action Log behavior and recommend Decision Journal replacement scope.
- Command gate behavior: not implemented here; research must map current
  command catalog/planner/verifier flow.
- Render effect: not implemented here; research must map current source
  export/render projection flow.
- Verifier/round-trip: not implemented here; research must map current verifier
  and round-trip layers.

## Implementation Slice

- C fact graph/query work: research current C analysis ownership and query
  shape only.
- Python/API/report work: research current orchestration, reports, APIs,
  command catalog, and planner only.
- Journal/replay work: research current Manual Action Log and replay behavior
  only.
- Renderer/verifier work: research current render/export and verifier paths
  only.
- Tests: no implementation tests required unless narrow inspection tooling is
  added to answer the research.

## Research Completion Standard

Checking a research box requires evidence, not just a summary sentence. Each
completed coverage item must include a trace block with:

- files and functions inspected;
- call/data flow summary;
- current ownership boundary;
- protocol/v2 implication;
- reuse/replace classification where relevant;
- commands or searches used to check for missed hooks;
- open questions, or `none`.

`Mapped` means the relevant code path is traceable from entrypoint to output or
explicitly marked out of scope with reason. `Inventoried` means the durable,
derived, cached, and generated state involved in that subsystem is named and
classified. `Traced` means the issue records the caller, callee, inputs,
outputs, and invalidation/replay behavior where applicable.

Pandora report or verifier claims require reproducible evidence:

```text
Command:
Commit:
Target:
Key output:
Validation artifact path, or inline result block:
```

The first implementation slice recommendation must include a comparison matrix
for RSSET, A5, and immediate-reference candidates:

- current evidence available;
- missing protocol primitives;
- C work required;
- Python/API work required;
- render/verifier involvement;
- risk/blast radius;
- expected source-quality payoff;
- reason selected or rejected.

The proposal update must carry concrete architecture findings and rewrite-scope
corrections, not only say that research completed.

## Architecture Inventory

### Target Load Lifecycle

Trace block:

- Files/functions inspected:
  `amiga_reversing/disasm/binary_source.py::resolve_target_binary_source`,
  `_load_raw_binary_source`, `_load_hunk_file_source`,
  `_load_disk_entry_source`;
  `amiga_reversing/disasm/projects.py::_binary_project_record`,
  `_load_project_record`, `get_project`; `amiga_reversing/disasm/server.py`
  `_require_ready_binary_project`; `amiga_reversing/disasm/c_backend.py`
  `_source_file_for_c_backend`, `CListingArtifact`.
- Call/data flow: project id resolves to `targets/...`; `.project.json` gives
  project record metadata; `source_binary.json` selects raw/hunk/disk-entry
  source; target metadata and Manual Action Log projection are loaded into the
  project record; C listing/source paths receive the binary source plus an
  effective metadata JSON path.
- Current ownership boundary: Python owns project path resolution, binary
  source descriptors, target readiness, and C DLL calls. C owns binary decode,
  analysis, listing rows, source text, and fact-derived JSON.
- Protocol/v2 implication: v2 should reuse binary source descriptors and path
  resolution. Selected identity must be anchored in C listing locators, not
  Python row indexes alone.
- Reuse/replace: reuse `source_binary.json`, project ids, target path helpers,
  and C listing artifact construction; replace report-private identity
  interpretation.
- Commands/searches used: `git grep -n "resolve_target_binary_source"`,
  `Select-String ... binary_source.py,projects.py,c_backend.py`.
- Open questions: none.

### Post-Load Auto-Analysis Hooks

Trace block:

- Files/functions inspected:
  `src/m68k_analysis_facts_v2.c::facts_v2_collect_profile_internal`,
  `m68k_facts_v2_collect_profile`,
  `m68k_facts_v2_render_asm_source_profile_alloc`;
  `src/platform_file_lib.c` facts-v2 JSON/listing/source entrypoints;
  `amiga_reversing/disasm/c_backend.py::CListingArtifact`.
- Call/data flow: Python asks the C backend for listing/analysis/source
  payloads; C decodes object sections, seeds policy/metadata, propagates facts,
  builds render lookup/preview, then emits JSON/source/profile data.
- Current ownership boundary: C owns deterministic analysis and generated
  facts. Python owns invocation, caching, JSON parsing, and presentation.
- Protocol/v2 implication: the fact graph/query API belongs in C. Python should
  ask typed questions for packets/gates/effects instead of recomputing semantic
  truth from rendered rows.
- Reuse/replace: reuse facts-v2 decode/fixed-point/render primitives; replace
  report-specific Python candidate semantics where they duplicate C facts.
- Commands/searches used: `git grep -n "facts_v2" -- src`, `Select-String ...
  m68k_analysis_facts_v2.c platform_file_lib.c c_backend.py`.
- Open questions: none.

### C Analysis Ownership

Trace block:

- Files/functions inspected:
  `src/m68k_analysis_facts_v2.c`, `src/m68k_analysis_facts_v2.h`,
  `src/m68k_analysis_render_lookup.c`, `src/m68k_fact_ir.c`,
  `src/m68k_render_ir.c`, `src/m68k_render_plan.c`.
- Call/data flow: facts-v2 constructs `M68kFactIR`, accepted candidate indexes,
  relocation/runtime-address state, source-analysis IR, render lookup, and
  source render plan/profile counters.
- Current ownership boundary: C state is authoritative while a listing/source
  artifact is being built, but Python receives JSON snapshots rather than a
  durable typed query interface.
- Protocol/v2 implication: add C-owned packet/gate/replay/effect queries over
  analysis state. Avoid making Python reports the schema of record.
- Reuse/replace: reuse `M68kFactIR`, decode IR, render lookup, source analysis,
  and exact render profile counters; replace JSON snapshot scraping as the
  durable protocol interface.
- Commands/searches used: `git grep -n "m68k_facts_v2_" -- src`,
  `Select-String ... m68k_analysis_facts_v2.c`.
- Open questions: none.

### Python Orchestration Ownership

Trace block:

- Files/functions inspected:
  `amiga_reversing/reversing_loop.py::main`, `inspect_target`,
  `run_one_iteration`, `inspect_immediate_runtime_refs`,
  `inspect_a5_hardware_lifetimes`, `inspect_rsset_candidates`,
  `_select_command_action`, `_command_availability`,
  `_verify_manual_mutation`; `amiga_reversing/disasm/server.py` command and
  listing handlers.
- Call/data flow: CLI/report commands open or reuse listing artifacts, assemble
  report JSON from listing rows plus manual state, choose a candidate, query
  the command catalog, execute `/commands/execute` when allowed, then run
  command-specific verifier layers.
- Current ownership boundary: Python owns orchestration, report formatting,
  planner ranking, command catalog mediation, and verifier composition. Some
  semantic candidate checks are currently Python-local.
- Protocol/v2 implication: keep Python as orchestration/presentation, but move
  shared packet truth and command gates behind typed C or protocol adapters.
- Reuse/replace: reuse CLI/server harness, planner shell, and verifier runner;
  replace report-specific candidate schema and gate duplication.
- Commands/searches used: `Select-String ... reversing_loop.py`, `git grep -n
  "commands/execute" -- amiga_reversing`.
- Open questions: none.

### Platform-Specific Extension Points

Trace block:

- Files/functions inspected:
  `src/platform_facts_v2.c`, `src/platform_common.c`,
  `src/platform_amiga_hunk.c`, `src/platform_amiga_disk.c`,
  `amiga_reversing/disasm/target_metadata.py`, `knowledge/amiga-hardware.md`,
  `knowledge/amiga-os.md`.
- Call/data flow: C platform helpers classify relocation anchors, runtime
  sinks, callback slots, absolute memory owners, and LoadSeg segment chains.
  Python target metadata supplies platform/target seeds such as RSSET regions,
  entry register seeds, custom structs, and reproduction policy.
- Current ownership boundary: platform facts are split between C platform
  helpers, Python metadata, and Markdown knowledge used by agents.
- Protocol/v2 implication: v2 evidence packets need explicit platform evidence
  lanes and source references so hardware/app-base decisions are not inferred
  from listing style alone.
- Reuse/replace: reuse platform helper functions and target metadata schema;
  replace implicit report-only platform assumptions with packet fields.
- Commands/searches used: `git grep -n "platform_facts_v2" -- src`,
  `Select-String ... target_metadata.py`.
- Open questions: none.

### Fact And State Sources

Trace block:

- Files/functions inspected: `source_binary.json`, `target_metadata.json`,
  `target_seeded_metadata.json`, `target_corrections.json`,
  `manual_actions.jsonl`, `reproduction.json`, generated `.s`,
  `amiga_reversing/disasm/effective_metadata.py::effective_target_metadata`,
  `effective_metadata_file`, `effective_metadata_hash`.
- Call/data flow: source/import facts and metadata are preserved; Manual Action
  Log projection overlays target metadata into an effective metadata file; C
  consumes effective metadata to emit listing/source; reproduction output and
  generated source are derived.
- Current ownership boundary: durable inputs are target files and Manual Action
  Log; derived files are listing caches, source export, and reproduction
  reports.
- Protocol/v2 implication: Decision Journal should store accepted actor
  decisions only. Derived facts must be regenerated from binary, metadata,
  platform knowledge, C analysis code, and journal replay.
- Reuse/replace: reuse durable source descriptors and metadata; replace Manual
  Action Log semantics for evidence decisions.
- Commands/searches used: `reversing_loop inspect` hygiene output; `git grep
  -n "effective_metadata" -- amiga_reversing`.
- Open questions: none.

### Derived-State And Replay Assumptions

Trace block:

- Files/functions inspected:
  `amiga_reversing/disasm/manual_actions.py::append_manual_action`,
  `load_manual_projection`, `_project_actions`; `server.py`
  `_manual_action_affects_listing_artifact`; `listing_projection.py`.
- Call/data flow: append validates payload and target identity, writes JSONL,
  projection replays active records with undo/redo filtering, and server/cache
  invalidation decides whether listing artifacts must be regenerated.
- Current ownership boundary: replay is Python-only and projects to typed
  Python metadata before C sees it.
- Protocol/v2 implication: Decision Journal replay must be validated and then
  applied into C analysis state, with stale/invalid decisions surfaced as
  packets rather than hidden projection failures.
- Reuse/replace: reuse append-only discipline, target identity pinning, and
  projection invalidation concepts; replace action-kind-specific projection as
  the protocol source of truth.
- Commands/searches used: `git grep -n "ManualActionLogProjection"`,
  `Select-String ... manual_actions.py server.py`.
- Open questions: none.

### Reports And Candidate Generation

Trace block:

- Files/functions inspected:
  `reversing_loop.py::inspect_immediate_runtime_refs`,
  `_listing_immediate_runtime_reference_report`;
  `inspect_a5_hardware_lifetimes`, `_listing_a5_cfg_path_lifetime_report`;
  `inspect_rsset_candidates`, `_listing_rsset_candidate_report`.
- Call/data flow: reports require a listing artifact, scan listing row contexts,
  join existing manual state, emit candidates, mutation policy, blockers, and
  command hints.
- Current ownership boundary: report semantics are Python-local,
  listing-backed, and not durable truth.
- Protocol/v2 implication: reports should become discovery and packet
  presentation surfaces over common protocol packets.
- Reuse/replace: reuse scans as regression references and candidate finders;
  replace their schemas as durable packet schemas.
- Commands/searches used: reproduced Pandora report commands below; `git grep
  -n "immediate-ref-report|a5-hardware-report|rsset-candidate-report"`.
- Open questions: none.

### Command Catalog And Planner Flow

Trace block:

- Files/functions inspected:
  `manual_action_catalog.py::listing_row_action_catalog`,
  `_rsset_binding_actions`, `_a5_hardware_ref_actions`,
  `_immediate_ref_payload`; `server.py` `/commands/available` and
  `/commands/execute` handlers; `reversing_loop.py::_command_availability`,
  `_available_catalog_command`, `_command_execution_policy_blocker`,
  `_select_command_action`.
- Call/data flow: candidate context becomes a command query; catalog returns
  report-only or available actions; execution converts command parameters to a
  Manual Action Log payload; planner rejects unavailable/report-only/low-value
  candidates.
- Current ownership boundary: catalog is Python and writes Manual Action Log;
  planner is Python and depends on catalog identity matching.
- Protocol/v2 implication: command gates should be query results from protocol
  evidence, not report/catalog agreement by convention.
- Reuse/replace: reuse catalog transport and execution harness; replace
  report-specific gate checks and Manual Action Log write targets for v2
  decisions.
- Commands/searches used: `run-one --dry-run`; `git grep -n
  "rsset.binding.bind|a5_hardware_ref.interpret|immediate_ref.interpret"`.
- Open questions: none.

### Legacy Manual Action Log Flow

Trace block:

- Files/functions inspected:
  `manual_actions.py::ManualActionKind`, `append_manual_action`,
  `validate_manual_action_payload`, `_project_actions`,
  `_validated_immediate_interpreted_ref`, `_validated_a5_hardware_ref`,
  `_rsset_use_site_binding_key`; `effective_metadata.py` manual projection
  conversion functions.
- Call/data flow: UI/CLI command appends action; projection replays active
  actions into seeds, labels, comments, representations, RSSET bindings,
  interpreted immediates, A5 refs, review notes/items; effective metadata
  converts projection records to target metadata for C.
- Current ownership boundary: Python owns durable review/mutation state and
  semantic reload; C only sees projected metadata.
- Protocol/v2 implication: Decision Journal must keep append-only audit value
  but avoid storing derived render metadata as the decision model.
- Reuse/replace: reuse JSONL append, target identity, count/head-hash audit,
  and focused validators as migration references; replace Manual Action Log as
  architecture for accepted evidence.
- Commands/searches used: `git grep -n "manual_actions.jsonl"`,
  `Select-String ... manual_actions.py effective_metadata.py`.
- Open questions: none.

### Render And Export Flow

Trace block:

- Files/functions inspected:
  `source_export.py::render_source_export`,
  `source_rendering.py::render_source_from_binary_source`,
  `c_backend.py::listing_artifact_source_text_with_c_backend_profile`,
  `src/m68k_analysis_facts_v2.c::m68k_facts_v2_render_asm_source_profile_alloc`,
  `src/m68k_render_ir.c`, `src/m68k_source_file_emit.c`.
- Call/data flow: Python builds effective metadata and calls C to render
  assembler source/profile; source export wraps the text with metadata hash and
  target identity; generated `.s` is output, not proof.
- Current ownership boundary: C owns render plan/source text; Python owns file
  export and refusal presentation.
- Protocol/v2 implication: accepted facts need an explicit render-effect query
  before mutation, then generated-source verification after replay.
- Reuse/replace: reuse C render plan/source emit and export wrapper; replace
  post-hoc report-specific render checks with shared render-effect model.
- Commands/searches used: `Select-String ... source_export.py
  source_rendering.py`, `git grep -n "render_asm_source" -- src`.
- Open questions: none.

### Verifier And Round-Trip Flow

Trace block:

- Files/functions inspected:
  `reversing_loop.py::_verify_manual_mutation`,
  `_verify_immediate_interpreted_ref_mutation`,
  `_verify_a5_hardware_ref_mutation`, `_verify_rsset_binding_mutation`,
  `_verify_round_trip_exact`; `reproduction.py::load_reproduction_report`,
  `run_target_reproduction`; `src/m68k_reproduction_compare.c`.
- Call/data flow: after command execution, Python verifier checks Manual Action
  Log append, semantic reload/projection, rendered source or xrefs, negative
  safety for specific actions, then exact round-trip via `reproduction.json`.
- Current ownership boundary: verifier composition is Python-specific, while
  binary/source comparison is C/reproduction-backed.
- Protocol/v2 implication: verifier layers should become common protocol
  requirements: journal state, semantic replay, render effect, negative safety,
  exact round-trip.
- Reuse/replace: reuse reproduction/round-trip and focused action verifier
  checks; replace scattered verifier dispatch with a shared verifier result
  model.
- Commands/searches used: `reversing_loop inspect`, `run-one --dry-run`, `git
  grep -n "_verify_.*mutation" -- amiga_reversing/reversing_loop.py`.
- Open questions: none.

### Pandora Surface Evidence

Trace block:

- Files/functions inspected:
  `reversing_loop.py::inspect_immediate_runtime_refs`,
  `inspect_a5_hardware_lifetimes`, `inspect_rsset_candidates`,
  `inspect_target`, `run_one_iteration`; `manual_actions.py::_project_actions`.
- Call/data flow: Pandora reports open a listing artifact, scan current rows,
  join Manual Action Log projection, emit report-only or already-recorded
  states, then the dry-run planner skips low-value or unsupported candidates.
- Current ownership boundary: Pandora proof is produced by Python reports over
  C listing rows and Manual Action Log projection, with exact round-trip status
  read from `reproduction.json`.
- Protocol/v2 implication: RSSET/A5/immediate must share one packet shape even
  though current reports expose different JSON shapes.
- Reuse/replace: reuse these reports as regression inputs; replace their
  report-private schemas as protocol truth.
- Commands/searches used: the five commands below plus `git grep -n
  "immediate-ref-report|a5-hardware-report|rsset-candidate-report"`.
- Open questions: none.

Command:

```text
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m amiga_reversing.reversing_loop immediate-ref-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8
```

Commit: `2569c047ab0ad381c6322a012e729c2d3509b304`
Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Key output:

```text
candidate_count=9
safe_to_mutate=false
top_id=immediate-runtime-ref:s0:000009A6:instruction:664:0:00001080
current_render_state="\taddi.w #4224,d1\n"
source_family=source_offset
write_policy.status=report_only
reason=source-offset immediate matches are report-only until accepted runtime-address provenance exists
```

Command:

```text
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m amiga_reversing.reversing_loop a5-hardware-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8
```

Commit: `2569c047ab0ad381c6322a012e729c2d3509b304`
Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Key output:

```text
path_model=conservative_straight_line_cfg
use_count=525
accepted_custom_base_evidence_count=20
command_candidate_count=0
rendering_gate.status=blocked
missing_gates=command_candidate
top_source_evidence_id=a5-custom-cfg:h0:00000456->0000045C:op0:b0002+d0000
top_render_mode=entry_comment
```

Command:

```text
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m amiga_reversing.reversing_loop rsset-candidate-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8
```

Commit: `2569c047ab0ad381c6322a012e729c2d3509b304`
Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Key output:

```text
candidate_count=125
use_count=994
blocked=124
already_recorded=1
top_id=rsset-raw-a6:022E
top_selected_use=bclr.b #1,app_022E(a6)
top_use_addr=000006E4
top_missing_gates=missing_accepted_base_evidence
top_accepted_base_evidence_count=0
safe_to_mutate=false
```

Command:

```text
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m amiga_reversing.reversing_loop inspect --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8
```

Commit: `2569c047ab0ad381c6322a012e729c2d3509b304`
Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Key output:

```text
candidate_work=[]
safe_to_mutate=true
manual_action_log.count=58
manual_action_log.head_hash=3cbe93c200fd62d091b67c5b096c7b2221e3b57bf30f222272633a4342deed35
round_trip.status=exact
verification_paths=semantic_reload,projection_check,round_trip
```

Command:

```text
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m amiga_reversing.reversing_loop run-one --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 --dry-run
```

Commit: `2569c047ab0ad381c6322a012e729c2d3509b304`
Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Key output:

```text
action=null
action_result.status=not_run
candidate_work_count=225
planner.status=no_candidate
skipped_count=225
next.recommendation=stop
next.reason=no locator-backed command candidate
round_trip.status=exact
```

Validation artifact path, or inline result block: inline result blocks above.

### Hidden Couplings And Risks

Trace block:

- Files/functions inspected:
  `reversing_loop.py` report/planner/verifier paths,
  `manual_action_catalog.py`, `manual_actions.py`, `effective_metadata.py`,
  `server.py`, `listing_projection.py`, `source_rendering.py`.
- Call/data flow: candidate reports, command catalog availability, Manual
  Action Log projection, effective metadata generation, listing cache
  invalidation, render verification, and round-trip checks are coupled through
  Python data shapes and cache keys.
- Current ownership boundary: Python currently coordinates and partially owns
  semantic evidence that v2 wants C/protocol state to own.
- Protocol/v2 implication: hidden couplings define the rewrite boundary and
  prevent report-specific schemas from becoming v2 interfaces.
- Reuse/replace: reuse cache invalidation, projection hashing, and verifier
  checks; replace implicit coupling with explicit packet/gate/effect fields.
- Commands/searches used: `git grep -n "manual_actions.jsonl"`, `git grep -n
  "commands/execute"`, `git grep -n "_verify_.*mutation"`.
- Open questions: none.

- Report schemas are currently executable policy: RSSET, A5, and immediate
  reports each encode blockers, status, command hints, and verifier names in
  different shapes.
- Command availability depends on catalog/query identity matching, not a shared
  protocol gate object.
- Manual Action Log projection stores accepted facts, render metadata, and
  review state in one replay path.
- Effective metadata is the C/Python bridge; stale or partially projected
  metadata can make semantic reload look correct while packet evidence remains
  report-local.
- Listing cache keys include binary descriptor, file stamps, and effective
  metadata hash; command execution must invalidate or reopen listing artifacts
  before render verification.
- A5 and RSSET evidence use Python listing contexts for selected-use identity;
  v2 needs C-owned identity normalization to avoid row-shape drift.
- Generated `.s` and `reproduction.json` are derived artifacts. They prove
  verification only when tied to command output and current Manual Action Log
  count/head hash.

### Reuse/Replace Classification

Trace block:

- Files/functions inspected: all trace blocks above, especially
  `binary_source.py`, `projects.py`, `c_backend.py`,
  `m68k_analysis_facts_v2.c`, `manual_actions.py`,
  `manual_action_catalog.py`, `reversing_loop.py`, `source_rendering.py`,
  `reproduction.py`.
- Call/data flow: durable target inputs flow through Python orchestration into C
  facts/rendering, then back through Python reports, commands, manual replay,
  render/export, and verification.
- Current ownership boundary: reuse surfaces are stable input/C/render/verifier
  foundations; replace surfaces are workflow/state semantics and duplicated
  report gates.
- Protocol/v2 implication: the clean v2 stack can be built beside current code
  only if reuse surfaces remain stable and replace surfaces are not deepened.
- Reuse/replace: table below.
- Commands/searches used: all search commands recorded in preceding trace
  blocks.
- Open questions: none.

| Surface | Reuse | Replace |
| --- | --- | --- |
| Target load | project ids, `source_binary.json`, path helpers | none for v2 slice |
| C analysis | decode IR, facts-v2, FactIR, render lookup | JSON snapshot scraping as protocol truth |
| Python orchestration | CLI/server command harness, listing cache, planner shell | report-private packet/gate semantics |
| Platform facts | C platform helpers, target metadata, knowledge docs | implicit listing-style platform assumptions |
| Manual state | append-only JSONL audit ideas, target identity, head hash | Manual Action Log as accepted evidence architecture |
| Reports | candidate finders and regression references | report schemas as durable protocol schema |
| Commands | catalog transport and execution endpoint | Manual Action Log write target for v2 decisions |
| Render | C render plan/source emit, source export wrapper | post-hoc report-specific render proof |
| Verification | round-trip/reproduction, semantic reload checks | scattered action-specific verifier result shape |

### First Implementation Slice Matrix

Trace block:

- Files/functions inspected:
  `reversing_loop.py` RSSET/A5/immediate report functions, command catalog
  helpers in `manual_action_catalog.py`, focused verifier functions in
  `reversing_loop.py`, Manual Action Log projection in `manual_actions.py`.
- Call/data flow: RSSET is blocked but has high-payoff selected-use evidence;
  A5 has accepted and verifier-rich existing facts but no fresh command
  candidates; immediate source-offset has selected operand evidence but no
  command/verifier policy.
- Current ownership boundary: first slice should be read-only packet/API work,
  not mutation, because accepted evidence still lives in current report/manual
  shapes.
- Protocol/v2 implication: implement packet identity/blocker/conflict/journal
  result schema first, then gate mutation only after packet evidence proves the
  RSSET selected use.
- Reuse/replace: reuse report finders and verifier references; replace
  candidate-specific schemas with the packet schema chosen by the next issue.
- Commands/searches used: Pandora report commands and dry-run planner command
  recorded above.
- Open questions: none.

| Candidate | Current evidence available | Missing protocol primitives | C work required | Python/API work required | Render/verifier involvement | Risk/blast radius | Source-quality payoff | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RSSET `rsset-raw-a6:022E` | 125 RSSET groups; top selected use `s0:000006E4`; same-displacement context; command/report surface exists | accepted app-base evidence packet; selected-use path/lifetime scope; explicit empty conflicts; Decision Journal action | selected-use identity query, A6 base/lifetime evidence lanes, conflict query | packet API, journal accept/defer/reject, command gate from accepted packet | one selected operand render, negative same-displacement safety, exact round-trip | medium: currently blocked, so first slice can be read-only before mutation | high: unlocks app-slot naming family | Selected first slice as read-only packet + blocked decision path, then accept/mutate only if evidence is proven |
| A5 hardware | 20 accepted manual refs, 525 uses, verifier/render path exists, no fresh command candidates | common packet schema and journal replay; non-duplicate decision handling | C identity/evidence packet normalization for existing A5 facts | adapt existing report to packet shape; expose no-op/already-accepted state | verifier already rich; render already has symbol/comment modes | low for read-only, low payoff for new mutation because queue exhausted | medium but already harvested | Rejected as first slice; use as regression/control surface |
| Immediate `s0:000009A6` | 9 candidates; top source-offset immediate has selected operand and empty conflicts | source-offset acceptance policy, runtime provenance, command support, render intent | possible source-offset/dataflow evidence query | packet API can show blocked state; mutation path deferred | no command/verifier support for source-offset promotion | medium/high policy risk | medium if policy is solved | Rejected as first mutation slice; include as packet blocker example |

Recommended next issue: define the shared read-only evidence packet, selected
identity, blockers/conflicts, and decision result schema using RSSET
`rsset-raw-a6:022E` as the primary packet and A5/immediate as regression packet
shapes. Do not add mutation until accepted app-base evidence and conflict proof
exist.

## Research Coverage

- [x] Target load lifecycle traced, or marked out of scope with reason.
- [x] Post-load auto-analysis hooks traced, or marked out of scope with reason.
- [x] C analysis ownership mapped, or marked out of scope with reason.
- [x] Python orchestration ownership mapped, or marked out of scope with reason.
- [x] Platform-specific extension points mapped, or marked out of scope with reason.
- [x] Fact/state sources inventoried, or marked out of scope with reason.
- [x] Derived-state/replay assumptions inventoried, or marked out of scope with reason.
- [x] Reports/candidate generation traced, or marked out of scope with reason.
- [x] Command catalog/planner flow traced, or marked out of scope with reason.
- [x] Legacy Manual Action Log flow traced, or marked out of scope with reason.
- [x] Render/export flow traced, or marked out of scope with reason.
- [x] Verifier/round-trip flow traced, or marked out of scope with reason.
- [x] Pandora RSSET/A5/immediate surfaces mapped, or marked out of scope with reason.
- [x] Hidden couplings/risks listed, or marked out of scope with reason.
- [x] Reuse/replace candidates classified, or marked out of scope with reason.
- [x] First implementation slice recommended, or blocker recorded.

If research discovers another relevant subsystem, add it to this checklist
before continuing. The issue is not complete until the expanded checklist is
signed off or explicitly marked out of scope with reason.

## Research Review

- [x] Second pass checked every completed trace block against the named
  files/functions.
- [x] Cross-references searched for missed hooks, with search terms or commands
  recorded.
- [x] Findings were checked against Pandora current surfaces with command output
  or validation artifact references.
- [x] Proposal updated with concrete model corrections and rewrite-scope
  findings.
- [x] First-slice comparison matrix justifies the recommended next issue.
- [x] Next issue scope follows from the inventory.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Every checked research item has a trace block satisfying the Research
  Completion Standard.
- [x] Pandora report/verifier claims include reproducible command evidence.
- [x] Evidence packet shape tested, or explicitly deferred because this remains
  research-only.
- [x] Decision/replay behavior tested where applicable.
- [x] Command gate refuses unsafe mutation.
- [x] Render/verifier/round-trip checked where output-affecting.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

Sign-off notes:

- Old code deletion is deferred because this is research-only and no v2 cutover
  was implemented.
- Evidence packet shape implementation/testing is deferred to the recommended
  next issue; this issue defines the required first slice and validates current
  report blockers.
- Default behavior impact is none: docs-only inventory work plus read-only
  report/inspect/dry-run commands.
- Post-commit review completed after the issue/proposal commit; no unresolved
  worthwhile findings remain.
