# 017-094: Cascade RSSET/App-Base Facts Into Field Analysis

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-093` must be complete first.
- Protocol area: RSSET/app-base parent facts and derived app-slot field references.
- Current proposal state: RSSET can accept selected app-base evidence, but new candidates remain blocked and propagation is not cascade-first.
- Desired proposal state after this issue: accepted app-base/layout/lifetime facts derive all safe field refs, xrefs, and downstream candidate facts within scope.

## Protocol Delta

- Adds: RSSET/app-base parent fact cascade.
- Changes: app-slot interpretation is derived over scope rather than per selected operand only.
- Replaces: one-off RSSET binding as the only useful output.
- Leaves out of scope: speculative field naming without evidence, A5 implementation changes, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Accepted app-base facts must define base register, layout, lifetime/scope, and conflicts.
- Safe same-scope app-slot operands become derived children.
- Children may produce further candidates: xrefs, field names, struct layout hints, callback-slot links, and data classifications.
- Out-of-scope or conflicting operands remain blocked.

## Pandora Proof

- Use current Pandora RSSET/app-base evidence, including accepted `$022E` as existing state and one non-accepted blocked candidate as a negative case.
- Do not claim new source progress unless verifier proves baseline delta.

## Implementation Slice

- C fact graph/query work: model app-base parent and derived field refs in cascade state.
- Python/API/report work: expose parent/child/blocker summaries.
- Journal/replay work: accept/defer/reject app-base parent facts as needed.
- Renderer/verifier work: render derived app-slot effects only through cascade verifier.
- Tests: scoped derivation, out-of-scope blocker, existing accepted fact replay, downstream candidate emission.

## Research Coverage

- [ ] Current RSSET report and Decision Journal state checked.
- [ ] Parent scope/lifetime is explicit.
- [ ] Derived children carry parent/rule provenance.
- [ ] Downstream candidates are emitted without unsafe mutation.
- [ ] Baseline delta verifier used for any source change.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] This makes RSSET a cascade lane, not a selected operand lane.
- [ ] Existing accepted state is not counted as new progress unless it causes new derived output.
- [ ] Blocked candidates remain explainable.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-093` complete.
- [ ] Focused RSSET cascade tests pass.
- [ ] Real Pandora RSSET cascade report produced.
- [ ] Exact round-trip passes for any source output change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

