# 017-038: RSSET Journal Mutation Gate Readiness

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: safe mutation gate contract before source output changes
- Blocked by: `017-037`
- Current proposal state: `017-037` exposes matching journal decisions in a
  read-only `journal_decision_evidence` lane. Even a matching accept leaves
  `rsset.binding.bind` blocked.
- Desired proposal state after this issue: the selected RSSET candidate has a
  complete, explicit gate report showing every condition required before a
  journal-backed mutation can run, with render/verifier readiness checked but
  mutation still disabled.

## Protocol Delta

- Adds: journal-backed RSSET mutation gate contract and readiness report.
- Changes: the RSSET packet/report can explain why a matching journal accept is
  not yet executable, including render and verifier readiness.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: applying the mutation, writing Manual Action Log state,
  changing rendered source, broad RSSET migration, UI.

## Default Behavior

- Existing planner/default mutation behavior must remain unchanged.
- `rsset.binding.bind` must remain disabled in this issue even when all
  non-mutation evidence gates pass.
- The gate may report `ready_for_039=true` only when the selected candidate has
  all evidence/render/verifier prerequisites required for `017-039`; it must
  still report `mutation_enabled=false`.

## Gate Contract

Add a read-only gate object for journal-backed RSSET binding. The exact field
placement may follow existing packet/report structure, but it must expose:

- `command_id`: `rsset.binding.bind`.
- `mutation_enabled`: always `false` in this issue.
- `ready_for_039`: true only when every pre-mutation gate below is satisfied.
- `status`: `blocked` or `ready_for_mutation_issue`.
- `satisfied_gates`: ordered list of passed gate ids.
- `missing_gates`: ordered list of failed gate ids.
- `journal_evidence`: summary or pointer to the matching
  `journal_decision_evidence` lane.
- `render_intent`: exact source effect expected by the later mutation.
- `verifier_plan`: generated-source and exact round-trip verification plan.

Required gate ids:

- `journal_accept`: one exact matching active `accept_fact`.
- `candidate_identity`: candidate id equals `rsset-raw-a6:022E`.
- `selected_identity`: target, segment, address, operand index, and optional
  selected-use id match the selected use.
- `fact_type`: accepted fact type is `rsset_app_base`.
- `selected_use_scope`: accepted scope is exact selected-use hunk/address/operand.
- `empty_conflicts`: accepted fact conflicts are explicit empty list.
- `field_or_layout_refinement`: target layout/field context exists for the
  selected displacement.
- `render_support`: renderer can express the selected RSSET binding without
  changing unrelated operands.
- `generated_source_verifier`: verifier can prove the selected source effect.
- `exact_round_trip`: exact binary round-trip verifier is available.

## Render/Verifier Readiness Contract

This issue must not invent a desired source edit. It must inspect existing
RSSET bind render/verifier support and report one of:

- `ready`: existing render/verifier support can prove the selected mutation.
- `blocked`: name the missing render or verifier capability.
- `not_applicable_yet`: no exact journal accept or layout field is present, so
  render readiness cannot be evaluated.

The readiness report must identify the expected selected source effect for the
Pandora `rsset-raw-a6:022E` use without changing output. If implementation
evidence shows the expected effect cannot be expressed safely, update the
proposal and leave `017-039` blocked.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: report shows journal evidence lane plus mutation gate
  readiness with missing gates.
- Decision behavior: accepted journal evidence may satisfy evidence gates but
  cannot enable mutation in this issue.
- Command gate behavior: `rsset.binding.bind` remains blocked/disabled.
- Render effect: none.
- Verifier/round-trip: readiness is reported; no output-affecting verification
  is required unless the implementation accidentally changes output, which must
  be treated as a bug.

## Implementation Slice

- C fact graph/query work: none unless implementation evidence proves a
  read-only query is necessary and the proposal is updated first.
- Python/API/report work: add the gate/readiness object to the selected RSSET
  packet/report.
- Journal/replay work: consume the read-only `journal_decision_evidence` lane.
- Renderer/verifier work: inspect and report readiness only; do not render.
- Tests: blocked without journal accept, blocked with wrong identity, blocked
  with conflicts, blocked without selected-use scope, blocked without layout
  field, render/verifier readiness reporting, exact round-trip availability
  reporting, `mutation_enabled=false`, no write to source/MAL/journal.

## Research Completion Standard

Record trace blocks for RSSET journal evidence flow, command catalog,
RSSET bind render/verifier support, round-trip availability, C/Python
ownership, and any legacy path that would be replaced by `017-039`.

## Research Coverage

- [x] RSSET journal evidence lane checked.
- [x] Command catalog and planner hooks checked.
- [x] Existing RSSET bind render support checked.
- [x] Generated-source verifier support checked.
- [x] Exact round-trip availability path checked.
- [x] Legacy/current RSSET bind mutation path identified for later cutover or
  blocker.
- [x] Pandora selected-use expected source effect recorded.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed hooks.
- [x] Proposal updated if gate/readiness rules change the protocol.
- [x] `017-039` refreshed or marked blocked if readiness is incomplete.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Gate/readiness object tested.
- [x] `mutation_enabled=false` tested for every path.
- [x] Render/verifier readiness tested without changing output.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

Trace blocks:

- RSSET journal evidence lane:
  `amiga_reversing/reversing_loop.py::_rsset_journal_decision_evidence`
  still owns read-only accepted/deferred/rejected/mismatched journal projection
  consumption. Journal evidence remains excluded from legacy
  `accepted_base_evidence_count`.
- Gate/readiness object:
  `amiga_reversing/reversing_loop.py::_rsset_journal_mutation_gate` now emits
  `command_id`, `mutation_enabled=false`, `ready_for_039`, `status`,
  ordered `satisfied_gates`/`missing_gates`, `journal_evidence`,
  `render_intent`, `verifier_plan`, and render/verifier readiness.
- Command catalog/planner:
  `rsset.binding.bind` remains the existing command id, but 017-038 does not
  make the planner actionable. Candidate `command_support.bind` and evidence
  packet `command_gate.enabled` remain blocked/false.
- Render/verifier support:
  readiness points at existing
  `_verify_projected_rsset_binding_rendered_source` and `_verify_round_trip_exact`
  support without invoking mutation or changing rendered source.
- Exact round-trip availability:
  `inspect_rsset_candidates` feeds the gate from the target
  `reproduction.json` availability path. The Pandora raw subtarget has
  `reproduction.json` with `status: exact`.
- Legacy/current mutation path:
  current `rsset.binding.bind` manual-state mutation and verifier code remains
  legacy command support for 017-039 cutover; 017-038 deliberately does not
  delete or enable it.
- Pandora selected-use effect:
  selected use remains `rsset-raw-a6:022E` at `s0:000006E4:op1`; later mutation
  intent is one selected use-site binding rendering `app_022E(a6)` only.

Verification:

- Focused RSSET tests:
  `uv run python -m pytest tests\test_reversing_loop.py -q -k "rsset_journal_mutation_gate or rsset_candidate_report or rsset_evidence_packet or query_rsset_evidence_packet or inspect_rsset_candidates"`
  passed with `23 passed, 315 deselected`.
- Lint:
  `uv run ruff check amiga_reversing\reversing_loop.py tests\test_reversing_loop.py`
  passed.
