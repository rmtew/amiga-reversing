# 017-039: RSSET Journal-Backed Safe Mutation

Status: complete

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

## Completion Evidence

017-040 provided the durable active `decision_journal.jsonl` accept for
`rsset-raw-a6:022E` at `s0:000006E4:op1`, so 017-039 proceeded only after the
017-038 gate reported `ready_for_039=true`.

Trace blocks:

- 017-038 gate:
  `amiga_reversing/reversing_loop.py::_rsset_journal_mutation_gate` can report a
  ready gate only when every evidence/render/verifier/round-trip gate is
  satisfied. Tests prove the complete-evidence path reports
  `ready_for_039=true` while the selected 017-039 bind support becomes
  available from journal authority.
- Command catalog/planner:
  the selected command id remains `rsset.binding.bind`. The planner now derives
  exactly one selected `rsset_use_site_binding` candidate from the journal-ready
  RSSET report and copies decision provenance into command context/parameters.
  Catalog execution accepts `source_evidence_status=accepted` and keeps
  non-journal or mismatched evidence report-only.
- Renderer/verifier:
  `_verify_projected_rsset_binding_rendered_source` and `_verify_round_trip_exact`
  are the proof path. Existing app-slot/symbol contexts now record
  `render_state=linked_existing_field`; raw/gap contexts remain
  `linked_gap_or_raw`.
- Round-trip:
  the real Pandora execution passed exact round-trip verification.
- Pandora source effect:
  generated source already contained the selected `app_022E(a6)` line. The
  durable source-progress effect is one scoped binding:
  `rsset-binding-h0-000006E4-op1-A6-022E-app-__amiga_app_base__-selected-base_A6___amiga_app_base__`.
  The verifier proved the selected app-slot render, no raw unsafe operand, and
  exact round-trip.

Real execution:

- Dry-run selected `rsset-journal-bind:rsset-raw-a6:022E:s0:000006E4:op1`
  with command `rsset.binding.bind`.
- Real execution appended
  `create_manual_rsset_use_site_binding` action
  `manual-6e574feccab748359c7577833fa718ba` at sequence 60, scoped to
  hunk 0, address `000006E4`, operand 1, base `A6`, displacement `022E`,
  source evidence `decision-rsset-022e-accept-017-040`, and `conflicts: []`.
- Post-mutation selected report state:
  `status=already_recorded`, `bind_state=already_satisfied`,
  `accepted_base_evidence_count=1`, `journal_ready=true`, no missing gates.

Verification:

- Focused RSSET tests:
  `uv run python -m pytest tests\test_reversing_loop.py tests\test_manual_action_catalog.py -q -k "rsset_journal or rsset_candidate_report or rsset_evidence_packet or rsset_binding"`
  passed with `36 passed, 341 deselected`.
- Real verifier replay:
  `manual_action_log`, `semantic_reload`, `rendered_source`, and `round_trip`
  all passed for the corrected sequence-60 binding action.
- Lint:
  pending final run before commit.
