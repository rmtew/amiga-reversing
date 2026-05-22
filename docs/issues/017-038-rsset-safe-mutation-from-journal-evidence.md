# 017-038: RSSET Safe Mutation From Journal Evidence

Status: planned

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: first verifier-backed mutation from Decision Journal evidence
- Blocked by: `017-037`
- Current proposal state: RSSET packets can be backed by replayed Decision
  Journal evidence, but mutation remains blocked unless all safe gates are
  implemented and proven.
- Desired proposal state after this issue: `rsset.binding.bind` can perform the
  selected Pandora mutation only when replayed journal evidence satisfies every
  identity, scope, conflict, render, and verifier gate.

## Protocol Delta

- Adds: safe RSSET mutation gate from replayed Decision Journal evidence.
- Changes: a journal-backed accepted fact may become actionable source progress
  after verifier support proves the render is exact and scoped.
- Replaces: selected-slice report-private RSSET mutation gating if v2 fully
  owns the path.
- Deletes: replaced selected-slice legacy gate code when cutover is complete.
- Leaves out of scope: broad RSSET migration, broad Pandora mutation run,
  speculative labels, UI.

## Default Behavior

- There must be exactly one default implementation for the selected mutation
  path after cutover.
- Do not leave two competing active paths. If v2 cannot fully own the selected
  path, keep mutation blocked and record the blocker.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: durable journal accept with exact selected-use identity,
  accepted app-base evidence, selected-use path/lifetime scope, explicit empty
  conflicts, render intent, command support, verifier support, and exact
  round-trip.
- Decision behavior: accepted decision enables mutation only through replayed
  projection and only for the selected scope.
- Command gate behavior: `rsset.binding.bind` reports enabled only when every
  gate is satisfied; otherwise it names the remaining blocker.
- Render effect: source-quality improvement in the selected RSSET use only.
- Verifier/round-trip: generated source verifier and exact binary round-trip
  are mandatory before commit.

## Implementation Slice

- C fact graph/query work: implement the minimum authoritative query/fact path
  needed so the mutation is replayable and not report-private.
- Python/API/report work: expose the command only through the v2 gate result.
- Journal/replay work: consume active accepted decision state as durable
  evidence.
- Renderer/verifier work: implement and test exact selected-scope render and
  verifier support before enabling mutation.
- Tests: blocked without journal evidence, blocked with wrong identity, blocked
  with conflicts, blocked without path/lifetime scope, enabled with complete
  evidence, exact source diff scope, generated-source verifier, exact
  round-trip, and no duplicate legacy path.

## Research Completion Standard

Record trace blocks for command catalog, RSSET evidence flow, renderer,
verifier, round-trip path, C/Python ownership, and any old code deleted or
deferred.

## Research Coverage

- [ ] RSSET decision evidence flow checked.
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
