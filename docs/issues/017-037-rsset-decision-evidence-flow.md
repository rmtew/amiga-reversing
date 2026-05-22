# 017-037: RSSET Decision Evidence Flow

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: first packet-to-decision-to-gate evidence flow
- Blocked by: `017-036`
- Current proposal state: RSSET evidence packets and Decision Journal replay
  exist separately. `017-036` exposes accepted/deferred/rejected journal
  projection through `decision-journal-report`, but RSSET reports do not consume
  it.
- Desired proposal state after this issue: the RSSET packet/gate can consult a
  replayed Decision Journal projection as accepted/deferred/rejected evidence
  without enabling mutation until all safe gates are satisfied.

## Protocol Delta

- Adds: RSSET evidence packet integration with replayed Decision Journal
  decisions.
- Changes: accepted RSSET app-base evidence can come from the replay
  projection as a separate read-only lane.
- Replaces: none by default. Report-private/manual-state RSSET evidence remains
  visible until a later cutover issue explicitly deletes it.
- Deletes: none unless implementation evidence proves a selected-slice helper
  is pure duplication and the proposal is updated first.
- Leaves out of scope: broad RSSET migration, broad Pandora mutation run,
  rendering, UI, enabling `rsset.binding.bind`.

## Default Behavior

- Existing RSSET report/default planner behavior must remain non-mutating.
- The selected RSSET report/packet may gain a read-only
  `journal_decision_evidence` lane, but `rsset.binding.bind` must remain
  blocked until a later safe-mutation issue wires verifier/render gates.
- Do not count journal accepted evidence as command-enabled mutation evidence
  unless every non-render gate is also explicit and render/verifier gates still
  block mutation.

## Evidence Matching Contract

Journal decisions may be associated with an RSSET selected use only when all
required identity and safety fields match:

- `action` is one of `accept_fact`, `defer_fact`, or `reject_fact`.
- `candidate_id` equals the RSSET candidate id, for Pandora
  `rsset-raw-a6:022E`.
- `selected_identity.target_id`, `segment_id`, `addr`, and `operand_index`
  match the selected use.
- If `selected_identity.selected_use_id` exists, it must match the packet
  selected-use id.
- `fact_type` for accepted facts is `rsset_app_base`.
- `scope.kind` for accepted facts is `selected_use`.
- `scope.hunk`, `scope.addr`, and `scope.operand_index` match the selected
  use.
- `conflicts` for accepted facts is explicit empty list.

Mismatches remain visible as rejected journal evidence, not accepted evidence.
Deferred/rejected records for the selected identity should be surfaced as
blockers/negative evidence, not silently ignored.

## Output Contract

Add a read-only journal evidence lane to the selected RSSET packet/report. The
shape may be adjusted to fit existing packet structure, but must expose:

- `status`: `accepted`, `blocked`, `rejected`, or `unavailable`.
- `accepted_count`: exact accepted journal decisions usable as RSSET app-base
  evidence.
- `accepted`: accepted matching decisions.
- `deferred_count` / `deferred`: selected matching defer decisions.
- `rejected_count` / `rejected`: selected matching reject decisions.
- `mismatched_count` / `mismatched`: journal decisions with same candidate or
  nearby selected identity that failed exact matching, including reason codes.
- `missing_gates`: remaining gates after journal evidence is considered.
- `mutation_enabled`: always `false` in this issue.

Reason codes should distinguish wrong candidate, wrong selected identity, wrong
fact type, missing selected-use scope, scope mismatch, and non-empty conflicts.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: packet/report output shows whether accepted/deferred/
  rejected journal decisions satisfy or block the journal app-base evidence lane.
- Decision behavior: journal accept can satisfy the accepted-base-evidence lane
  only when selected-use identity, path/lifetime scope, and empty conflicts are
  exact.
- Command gate behavior: mutation remains blocked unless all gates are present;
  render/verifier gates must remain blockers in this issue.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required.

## Implementation Slice

- C fact graph/query work: none unless implementation evidence proves a small
  read-only query is required and the proposal is updated first.
- Python/API/report work: connect RSSET packet/report evidence to replay
  projection for the selected RSSET candidate as a read-only lane.
- Journal/replay work: consume accepted/deferred/rejected projection state.
- Renderer/verifier work: none.
- Tests: accepted exact selected-use decision, rejected/deferred blockers,
  mismatched identity rejection, non-empty conflicts rejection, missing
  selected-use scope rejection, wrong candidate/fact-type rejection, malformed
  journal blocking active evidence, and no unsafe mutation.

## Research Completion Standard

Record trace blocks for RSSET packet generation, replay projection, command
catalog gates, current report-private accepted-evidence paths, Manual Action
Log accepted evidence, and the selected Pandora candidate.

## Research Coverage

- [x] RSSET packet and gate code checked.
- [x] Decision replay projection checked.
- [x] Command catalog gate logic checked.
- [x] Report-private accepted-evidence logic checked for replacement boundary.
- [x] Manual Action Log accepted-evidence path checked for replacement
  boundary.
- [x] Journal matching and mismatch reason codes defined.
- [x] Pandora selected-use identity and blocker evidence checked.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed hooks.
- [x] Proposal updated if RSSET evidence flow changes the protocol.
- [x] Next issue scope follows from the RSSET decision flow.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] RSSET decision evidence flow tested.
- [x] Command gate refuses unsafe mutation unless all gates are present.
- [x] Journal accepted/deferred/rejected/mismatched evidence lanes tested.
- [x] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Implementation Trace

### RSSET Report And Packet Flow

- Files and functions inspected:
  - `amiga_reversing/reversing_loop.py`
  - `inspect_rsset_candidates`
  - `_listing_rsset_candidate_report`
  - `_rsset_candidate_group_summary`
  - `_rsset_evidence_packet_from_candidate`
  - `_rsset_evidence_packet_lanes`
- Call/data flow summary: `inspect_rsset_candidates` now reads the explicit
  Decision Journal report for the target, extracts its replay `projection`, and
  passes that read-only projection into RSSET candidate construction. Each RSSET
  candidate gets a `journal_decision_evidence` lane, and selected packets expose
  the same lane under `evidence_lanes`.
- Gate boundary: `has_base_evidence`, `accepted_base_evidence_count`, candidate
  status, and `command_support.bind` still use the existing report/private and
  Manual Action Log accepted-base evidence path. Journal evidence is visible
  protocol evidence only; it does not make `rsset.binding.bind` available.
- Searches/commands used:
  - `Get-Content amiga_reversing\reversing_loop.py | Select-Object -Skip 3740 -First 330`
  - `Get-Content amiga_reversing\reversing_loop.py | Select-Object -Skip 4060 -First 150`
- Open questions: none.

### Journal Matching Rules

- Files and functions inspected:
  - `amiga_reversing/disasm/decision_journal.py`
  - `project_decision_journal`
  - `amiga_reversing/reversing_loop.py`
  - `_rsset_journal_decision_evidence`
  - `_rsset_journal_decision_mismatch_reasons`
  - `_rsset_journal_decision_selected_identity_matches`
  - `_rsset_journal_decision_scope_matches`
- Matching summary: active journal `accept_fact`, `defer_fact`, and
  `reject_fact` records are considered only from a valid replay projection.
  Accepted RSSET evidence requires exact `candidate_id`, selected identity
  target/segment/address/operand match, optional `selected_use_id` match,
  `fact_type=rsset_app_base`, `scope.kind=selected_use`, matching
  hunk/address/operand scope, and explicit empty conflicts.
- Mismatch reason codes: `wrong_candidate`, `wrong_selected_identity`,
  `wrong_fact_type`, `missing_selected_use_scope`, `scope_mismatch`, and
  `non_empty_conflicts`.
- Invalid journal behavior: invalid or malformed journals surface diagnostics
  on the lane with `status=unavailable` and no active accepted evidence.
- Open questions: none.

### Replacement Boundary

- Files and functions inspected:
  - `inspect_rsset_candidates`
  - `_rsset_candidate_evidence_search`
  - `_rsset_candidate_search_sources`
  - `_rsset_candidate_accepted_base_evidence_ref`
  - command normalization and RSSET bind command handling in
    `amiga_reversing/reversing_loop.py`
- Boundary summary: report-private selected-use evidence and legacy Manual
  Action Log evidence remain visible and authoritative for current command
  availability. Decision Journal projection is not passed into C analysis,
  effective metadata, renderer, verifier, command catalog execution, or planner
  selection.
- Deletion decision: no old code deleted; this issue adds a read-only lane and
  defers cutover/deletion until later verifier/render-gated mutation work.
- Open questions: none.

## Pandora Proof

Synthetic selected-use proof used the Pandora RSSET packet
`rsset-raw-a6:022E` at `s0:000006E4:op1` through the same RSSET report and
packet helpers used by tests. A matching journal accept produced:

```text
journal_status=accepted
journal_accepted_count=1
journal_missing_gates=missing_render_gate,missing_verifier_gate,mutation_disabled_in_017_037
journal_mutation_enabled=False
accepted_base_evidence_count=0
bind_state=blocked
safe_to_mutate=False
```

Deferred and rejected matching journal decisions remain negative evidence:

```text
journal_status=rejected
deferred_ids=decision-defer
rejected_ids=decision-reject
journal_missing_gates=missing_accepted_base_evidence
```

Mismatch coverage distinguishes wrong candidate, wrong selected identity, wrong
fact type, missing selected-use scope, scope mismatch, and non-empty conflicts.

Real-target Pandora report remains blocked:

```text
rsset safe_to_mutate=False
top_id=rsset-raw-a6:022E
top_status=blocked
top_selected_addr=000006E4
top_missing_gates=missing_accepted_base_evidence
top_accepted_base_evidence_count=0
journal_status=unavailable
journal_accepted_count=0
journal_mutation_enabled=False
bind_state=blocked
```

Real-target dry-run planner remains unchanged:

```text
dry_action=
dry_action_result_status=not_run
dry_planner_status=no_candidate
dry_next_reason=no locator-backed command candidate
```

Validation:

```text
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m pytest tests\test_reversing_loop.py -q -k "rsset_candidate_report or rsset_evidence_packet or query_rsset_evidence_packet or inspect_rsset_candidates"
18 passed, 315 deselected

$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run ruff check amiga_reversing\reversing_loop.py tests\test_reversing_loop.py
All checks passed!

$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m pytest tests\test_reversing_loop.py -q
333 passed
```

## Review Notes

- C fact mutation: absent; this issue only reads replay projection and annotates
  RSSET report/packet output.
- Render/verifier/round-trip: not applicable because no output-affecting source
  path changed.
- Next issue scope: decide the next explicit gate contract for using accepted
  journal evidence without enabling mutation before render/verifier gates exist.
