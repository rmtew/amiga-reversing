# 017-038: RSSET Journal Mutation Gate Readiness

Status: active

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

- [ ] RSSET journal evidence lane checked.
- [ ] Command catalog and planner hooks checked.
- [ ] Existing RSSET bind render support checked.
- [ ] Generated-source verifier support checked.
- [ ] Exact round-trip availability path checked.
- [ ] Legacy/current RSSET bind mutation path identified for later cutover or
  blocker.
- [ ] Pandora selected-use expected source effect recorded.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed hooks.
- [ ] Proposal updated if gate/readiness rules change the protocol.
- [ ] `017-039` refreshed or marked blocked if readiness is incomplete.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Gate/readiness object tested.
- [ ] `mutation_enabled=false` tested for every path.
- [ ] Render/verifier readiness tested without changing output.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
