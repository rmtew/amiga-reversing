# 017-039: RSSET Journal-Backed Safe Mutation

Status: planned

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: first verifier-backed source mutation from Decision Journal
  evidence
- Blocked by: `017-038`
- Current proposal state: `017-038` must provide a complete gate/readiness
  report while mutation remains disabled.
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

- [ ] `017-038` gate/readiness result checked.
- [ ] Command catalog and planner hooks checked.
- [ ] Renderer support checked.
- [ ] Generated-source verifier and exact round-trip path checked.
- [ ] Legacy/replaced selected-slice mutation path identified for deletion or
  deferred blocker.
- [ ] Pandora mutation proof plan defined before implementation.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed hooks.
- [ ] Proposal updated if safe mutation gates change the protocol.
- [ ] Follow-up scope recorded for broader RSSET migration if needed.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Command gate behavior tested.
- [ ] Render/verifier/round-trip tested.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
