# 017-036: Decision Replay Projection Model

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: replayable Decision Journal semantics
- Blocked by: `017-034`, `017-035`
- Current proposal state: Decision Journal records are durable, inspectable,
  and dry-run-validatable through `decision-journal-report`, but not projected
  into active decision state.
- Desired proposal state after this issue: accepted, deferred, rejected, and
  superseded decisions can be replayed into an in-memory projection with clear
  active/inactive outcomes and no C fact mutation yet.

## Protocol Delta

- Adds: deterministic replay projection for journal decisions.
- Changes: journal records gain protocol meaning as active/deferred/rejected
  evidence state, while still not mutating C facts.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: C fact graph insertion, command-gate activation,
  rendering, Manual Action Log replacement.

## Default Behavior

- Existing default analysis and reports remain unchanged unless an explicit
  validation/replay helper is invoked.
- Replay projection must be deterministic from current journal contents and must
  not write target state.
- Projection helper name: add `project_decision_journal(records)` in the
  Decision Journal module, or update this issue before implementation if a
  better local name is required by code evidence.
- CLI/API exposure: extend explicit `decision-journal-report` output with a
  `projection` object. Do not add a second command unless implementation
  evidence proves that is cleaner and the proposal is updated.

## Projection Contract

The projection is an in-memory summary derived only from a valid current
journal. Invalid records and invalid journals must not produce active accepted
facts. The output should include:

- `valid`: whether projection was produced from a valid journal.
- `diagnostics`: projection-specific diagnostics, plus journal validation
  blockers when projection cannot be produced.
- `accepted_facts`: active `accept_fact` decisions that are not superseded.
- `deferred_facts`: active `defer_fact` decisions that are not superseded.
- `rejected_facts`: active `reject_fact` decisions that are not superseded.
- `superseded_decision_ids`: decision ids hidden by supersession.
- `active_decision_ids`: non-superseded decision ids considered by projection.
- `by_candidate_id`: grouped active accepted/deferred/rejected decisions by
  `candidate_id`.
- `by_selected_identity`: grouped active accepted/deferred/rejected decisions by
  a stable selected-identity key.

Projection rules:

- The input journal must be valid under `validate_decision_journal_records`.
- `supersede_decision` removes the superseded decision id from active
  accepted/deferred/rejected buckets.
- `replacement_decision_id`, when present, is informational only in this issue;
  it does not make a forward reference active.
- `accept_fact` entries become active accepted facts only when their own record
  validates and they are not superseded.
- `defer_fact` and `reject_fact` entries remain active blockers/negative
  decisions only when their own record validates and they are not superseded.
- Unknown or malformed records remain diagnostics only and cannot affect active
  projection.
- Projection never calls C analysis, Manual Action Log projection, command
  catalog, renderer, verifier, or append helpers.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: `decision-journal-report` can show whether a selected-use
  RSSET app-base decision is accepted, deferred, rejected, or superseded in the
  projection.
- Decision behavior: accepted facts become active only in the replay
  projection; deferred/rejected decisions remain inspectable blockers.
- Command gate behavior: gate remains blocked because the projection is not yet
  consumed by RSSET mutation.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required.

## Implementation Slice

- C fact graph/query work: none unless implementation evidence proves a small
  read-only type boundary is needed and the proposal is updated first.
- Python/API/report work: expose replay projection through
  `decision-journal-report` only.
- Journal/replay work: active decision selection, supersession handling,
  conflict preservation, candidate/selected-identity grouping, and
  invalid-record exclusion.
- Renderer/verifier work: none.
- Tests: active accept projection, defer/reject projection, supersession,
  duplicate/invalid exclusion, malformed journal projection block,
  deterministic ordering/grouping, CLI projection JSON output, and no target
  mutation.

## Research Completion Standard

Record trace blocks for journal validation, packet identity, current report
accepted-evidence logic, existing Manual Action Log projection, command-gate
inputs, and any existing projection/state model that could conflict with
replay.

## Research Coverage

- [x] Decision Journal IO and validation surfaces checked.
- [x] Current RSSET accepted-evidence classification checked.
- [x] Existing Manual Action Log projection checked for replacement boundary.
- [x] Current command-gate inputs checked to prove projection is not consumed
  yet.
- [x] Active/inactive/superseded projection rules defined.
- [x] Side-effect boundary checked so replay projection cannot mutate C facts
  or target state.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed hooks.
- [x] Findings checked against current RSSET packet shape.
- [x] Proposal updated if replay rules change the protocol.
- [x] Next issue scope follows from the replay projection.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Replay projection tested.
- [x] `decision-journal-report` projection output tested.
- [x] C fact mutation explicitly absent or deferred.
- [x] Command gate refuses unsafe mutation.
- [x] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Implementation Trace

### Journal Validation And Projection

- Files and functions inspected:
  - `amiga_reversing/disasm/decision_journal.py`
  - `read_decision_journal`
  - `validate_decision_journal_records`
  - `decision_journal_report`
  - `project_decision_journal`
- Call/data flow summary: `decision_journal_report` reads the target-local
  `decision_journal.jsonl`, validates the current chain, then adds a
  `projection` object. `project_decision_journal(records)` revalidates the
  supplied in-memory sequence before producing active accepted/deferred/rejected
  buckets. Invalid validation blocks projection and returns empty active
  buckets with diagnostics.
- Projection rules implemented: active `accept_fact`, `defer_fact`, and
  `reject_fact` records are copied into action buckets only when their journal
  is valid and their `decision_id` is not superseded. `supersede_decision`
  removes the target id from action buckets. `replacement_decision_id` remains
  informational and does not activate forward references.
- Grouping shape: projection includes `by_candidate_id` and
  `by_selected_identity` maps. Selected identity keys prefer
  `<target_id>:<selected_use_id>`, then fall back to
  `<target_id>:<segment_id>:<addr>:op<operand_index>`, then stable sorted JSON.
- Searches/commands used:
  - `Get-Content amiga_reversing\disasm\decision_journal.py`
  - `Select-String -Path tests\test_decision_journal.py,tests\test_reversing_loop.py -Pattern "decision_journal_report|dry_run|decision-journal-report|default_inspect|malformed"`
- Open questions: none.

### RSSET Packet And Gate Boundary

- Files and functions inspected:
  - `amiga_reversing/reversing_loop.py`
  - `inspect_decision_journal`
  - `inspect_rsset_candidates`
  - `_rsset_evidence_packet_from_candidate`
  - `_rsset_candidate_evidence_search`
  - `_rsset_candidate_accepted_base_evidence_ref`
- Call/data flow summary: `decision-journal-report` is the only
  reversing-loop command that imports and calls the Decision Journal report.
  RSSET candidate reporting still derives accepted base evidence from selected
  use, same-displacement app-slot context, and Manual Action Log projection via
  `manual_state`; it does not consult Decision Journal projection.
- Command gate result: `rsset.binding.bind` remains blocked until a later issue
  explicitly wires replayed accepted evidence into RSSET mutation gates.
- Searches/commands used:
  - `Select-String -Path amiga_reversing\reversing_loop.py -Pattern "decision_journal|decision-journal|Decision Journal"`
  - `Select-String -Path amiga_reversing\reversing_loop.py -Pattern "selected_identity|selected_use_id|packet_id|rsset-packet|by_candidate|accepted_base"`
- Open questions: none.

### Manual Action Boundary

- Files and functions inspected:
  - `amiga_reversing/disasm/effective_metadata.py`
  - `_apply_manual_seed_projection`
  - `amiga_reversing/disasm/manual_actions.py`
- Call/data flow summary: existing Manual Action Log projection remains the
  legacy target-state path consumed by metadata/listing reload. Decision Journal
  projection is read-only protocol state and is not passed into manual
  projection, effective metadata, C analysis, renderer, verifier, or command
  catalog code.
- Replacement boundary: no old code was deleted because this issue only makes
  replay state observable; replacement/cutover is deferred to later replay and
  gate issues.
- Searches/commands used:
  - `Get-ChildItem -Path amiga_reversing -Recurse -File | Select-String -Pattern "manual_state|manual_actions|projection" -CaseSensitive`
- Open questions: none.

## Pandora Proof

Temporary-project projection proof used the Pandora target id and RSSET packet
`rsset-raw-a6:022E` at `s0:000006E4:op1`, with a temporary
`decision_journal.jsonl` containing accept, defer, reject, and supersede
records. The supersede record targeted the defer decision and included an
informational forward `replacement_decision_id`.

Key output:

```text
projection_valid=True
accepted_ids=decision-accept
deferred_ids=
rejected_ids=decision-reject
superseded_ids=decision-defer
active_ids=decision-accept,decision-reject,decision-supersede
candidate_keys=rsset-raw-a6:022E
selected_keys=amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8:s0:000006E4:op1
```

Real-target RSSET gate proof remains unchanged:

```text
rsset safe_to_mutate=False
top_id=rsset-raw-a6:022E
top_status=blocked
top_selected_addr=000006E4
top_missing_gates=missing_accepted_base_evidence
top_accepted_base_evidence_count=0
```

Real-target dry-run planner proof remains unchanged:

```text
dry_action=
dry_action_result_status=not_run
dry_planner_status=no_candidate
dry_next_reason=no locator-backed command candidate
```

Validation:

```text
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m pytest tests\test_decision_journal.py tests\test_reversing_loop.py -q -k "decision_journal or inspect_cli_reports_json"
23 passed, 323 deselected

$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run ruff check amiga_reversing\disasm\decision_journal.py amiga_reversing\reversing_loop.py tests\test_decision_journal.py tests\test_reversing_loop.py
All checks passed!
```

## Review Notes

- C fact mutation: absent by construction; projection code lives only in
  `decision_journal.py` and report wiring.
- Render/verifier/round-trip: not applicable because no output-affecting source
  path changed.
- Next issue scope: wire the replayed projection into one selected read-only
  consumer or gate query without enabling mutation until verifier and render
  gates are present.
