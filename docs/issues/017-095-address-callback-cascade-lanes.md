# 017-095: Add Address And Callback Cascade Lanes

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-094` must be complete first.
- Protocol area: runtime/source address facts and callback pointer facts as cascade parents.
- Current proposal state: immediates and callbacks expose evidence packets but do not drive general cascaded analysis.
- Desired proposal state after this issue: accepted address and callback facts derive xrefs, labels, code/data candidates, and downstream analysis children where safe.

## Protocol Delta

- Adds: address-space and callback-pointer parent fact cascade rules.
- Changes: immediates/callbacks can trigger chained analysis instead of stopping at report-only packets.
- Replaces: callback-specific helper thinking as the only code-entry path.
- Leaves out of scope: speculative code promotion without verifier, bulk mutation, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Accepted address facts derive labels/xrefs/range classifications only inside known address spaces.
- Accepted callback pointer facts derive callable targets only when store/use/dataflow proof is stable.
- Derived code/data candidates may become review packets if they are ambiguous.
- Already-code/already-data outcomes are recorded as exhausted, not repeatedly proposed.

## Pandora Proof

- Use current source-offset immediate and callback reports.
- Expected result: at least one lane emits useful derived children or precise blockers that show what is missing.
- Do not claim source progress without baseline delta verifier proof.

## Implementation Slice

- C fact graph/query work: model address and callback derived facts in cascade state.
- Python/API/report work: expose derived children and blockers in existing report/CLI surfaces.
- Journal/replay work: accept/defer/reject parent facts where command support exists.
- Renderer/verifier work: use cascade verifier for any rendered labels/code/data changes.
- Tests: address label/xref derivation, callback callable target derivation, already-represented exhaustion, ambiguous blocker.

## Research Coverage

- [ ] Current immediate and callback reports checked.
- [ ] Address-space identity is stable.
- [ ] Callback store/use path identity is stable.
- [ ] Derived children can feed further review packets.
- [ ] Already represented targets are exhausted cleanly.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] This adds general cascade lanes, not callback-only special cases.
- [ ] Ambiguous code/data promotion fails closed.
- [ ] Derived facts feed chained analysis where safe.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-094` complete.
- [ ] Focused address/callback cascade tests pass.
- [ ] Real Pandora reports demonstrate derived children or precise blockers.
- [ ] Exact round-trip passes for any source output change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

