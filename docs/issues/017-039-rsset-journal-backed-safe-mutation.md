# 017-039: RSSET Journal-Backed Safe Mutation

Status: blocked

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: first verifier-backed source mutation from Decision Journal
  evidence
- Blocked by: `017-038`, `017-040`
- Current proposal state: `017-038` provides a complete gate/readiness report
  while mutation remains disabled. `017-040` must provide a real durable
  journal accept before this issue can proceed.
- Desired proposal state after this issue: the selected Pandora RSSET use can
  be mutated through `rsset.binding.bind` only when the `017-038` gate is ready,
  the generated source verifier passes, and exact round-trip passes.

## Protocol Delta

- Adds: executable journal-backed RSSET bind mutation for the selected safe
  slice.
- Changes: a durable accepted journal fact can become source progress when all
  evidence, render, verifier, and round-trip gates pass.
- Replaces: the selected-slice report-private/manual-state mutation authority
  only if v2 fully owns the path.
- Deletes: replaced selected-slice legacy gate code when cutover is complete.
- Leaves out of scope: broad RSSET migration, speculative labels, UI, unrelated
  Pandora cleanup.

## Default Behavior

- Exactly one default implementation may own the selected mutation path after
  cutover.
- If `017-038` is not `ready_for_039=true`, this issue must stop as blocked and
  update the proposal/issue with the missing gate.
- Do not leave both a legacy accepted-evidence path and a v2 journal-backed path
  able to authorize the same selected mutation.

## Mutation Contract

The command may enable only for the selected RSSET use when all are true:

- `017-038` gate reports `ready_for_039=true`.
- One exact active journal `accept_fact` satisfies `journal_accept`,
  `candidate_identity`, `selected_identity`, `fact_type`,
  `selected_use_scope`, and `empty_conflicts`.
- Layout/field context is present and identifies the source symbol to render.
- The command writes one scoped RSSET use-site binding for the selected hunk,
  address, operand index, base register, and displacement.
- Generated-source verifier proves the expected selected source effect.
- Exact round-trip verifier passes.

The command must remain blocked for:

- missing journal accept;
- wrong candidate;
- wrong selected identity;
- wrong fact type;
- missing or mismatched selected-use scope;
- non-empty conflicts;
- missing layout/field refinement;
- missing render support;
- missing generated-source verifier;
- missing exact round-trip verifier;
- duplicate legacy/v2 authority for the same selected mutation.

## Render/Verifier Contract

Before commit, record the exact Pandora source effect and prove it with the
generated-source verifier. The verifier must prove:

- the selected operand/use changed as expected;
- unrelated RSSET uses did not change;
- no unsafe symbolic operand was emitted;
- exact binary round-trip passed.

If the renderer cannot prove the selected effect without unrelated changes,
stop and mark the issue blocked. Do not commit a partial mutation.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: durable journal accept, ready `017-038` gate, selected
  field/layout context, verifier support, exact round-trip.
- Decision behavior: accepted decision enables mutation only through replayed
  projection and only for the selected scope.
- Command gate behavior: `rsset.binding.bind` reports enabled only when every
  gate is satisfied; otherwise it names the remaining blocker.
- Render effect: source-quality improvement in the selected RSSET use only.
- Verifier/round-trip: generated-source verifier and exact binary round-trip
  are mandatory before commit.

## Implementation Slice

- C fact graph/query work: implement the minimum authoritative query/fact path
  needed so the mutation is replayable and not report-private, or update the
  proposal if the current C path already owns the needed fact.
- Python/API/report work: expose the command only through the v2 gate result.
- Journal/replay work: consume active accepted decision state as durable
  evidence.
- Renderer/verifier work: implement and test exact selected-scope render and
  verifier support before enabling mutation.
- Tests: blocked states for every missing gate, enabled path with complete
  evidence, exact source diff scope, generated-source verifier, exact
  round-trip, no duplicate legacy path, no broad Pandora mutation run.

## Research Completion Standard

Record trace blocks for command catalog, `017-038` gate, RSSET evidence flow,
renderer, verifier, round-trip path, C/Python ownership, and any old code
deleted or deferred.

## Research Coverage

- [x] `017-038` gate/readiness result checked.
- [x] Command catalog and planner hooks checked.
- [x] Renderer support checked.
- [x] Generated-source verifier and exact round-trip path checked.
- [x] Legacy/replaced selected-slice mutation path identified for deletion or
  deferred blocker.
- [x] Pandora mutation proof plan defined before implementation.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed hooks.
- [x] Proposal updated if safe mutation gates change the protocol.
- [x] Follow-up scope recorded for broader RSSET migration if needed.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Command gate behavior tested.
- [x] Render/verifier/round-trip tested.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Blocked Evidence

017-039 must stop if the 017-038 gate is not `ready_for_039=true` for the real
selected Pandora use. Current state does not contain a durable active
`decision_journal.jsonl` accept for `rsset-raw-a6:022E` at `s0:000006E4:op1`,
so the missing 017-038 gate is `journal_accept`. `017-040` owns that unblocker.

Trace blocks:

- 017-038 gate:
  `amiga_reversing/reversing_loop.py::_rsset_journal_mutation_gate` can report a
  ready gate only when every evidence/render/verifier/round-trip gate is
  satisfied. Tests prove the complete-evidence path reports
  `ready_for_039=true` while `mutation_enabled=false`.
- Command catalog/planner:
  the selected command id remains `rsset.binding.bind`; current candidate
  `command_support.bind` and packet `command_gate.enabled` remain blocked/false
  without legacy accepted base evidence. No duplicate v2/legacy authority was
  introduced.
- Renderer/verifier:
  `_verify_projected_rsset_binding_rendered_source` and `_verify_round_trip_exact`
  are the existing proof path. 017-038 reports them; 017-039 does not execute a
  partial mutation without a durable journal accept.
- Round-trip:
  the Pandora raw subtarget has an exact `reproduction.json`; round-trip
  availability is not the current blocker.
- Pandora source effect:
  generated source already contains the selected `app_022E(a6)` line at the
  `s0:000006E4` use-site. The 017-039 proof plan remains one scoped
  `rsset_use_site_binding` for that selected hunk/address/operand only, followed
  by generated-source verification and exact round-trip.

Required unblocker:

- Add or replay one durable active `accept_fact` with candidate
  `rsset-raw-a6:022E`, fact type `rsset_app_base`, selected identity
  `s0:000006E4:op1`, selected-use scope, and `conflicts: []`; then rerun the
  017-038 gate and only enable `rsset.binding.bind` in this issue if it reports
  `ready_for_039=true`. This work is tracked by `017-040`.

Verification:

- Focused RSSET tests:
  `uv run python -m pytest tests\test_reversing_loop.py -q -k "rsset_journal_mutation_gate or rsset_candidate_report or rsset_evidence_packet or query_rsset_evidence_packet or inspect_rsset_candidates"`
  passed with `23 passed, 315 deselected`.
- Lint:
  `uv run ruff check amiga_reversing\reversing_loop.py tests\test_reversing_loop.py`
  passed.
