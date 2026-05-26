# 017-095: Add Address And Callback Cascade Lanes

Status: completed
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

- [x] Current immediate and callback reports checked.
- [x] Address-space identity is stable.
- [x] Callback store/use path identity is stable.
- [x] Derived children can feed further review packets.
- [x] Already represented targets are exhausted cleanly.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This adds general cascade lanes, not callback-only special cases.
- [x] Ambiguous code/data promotion fails closed.
- [x] Derived facts feed chained analysis where safe.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-094` complete.
- [x] Focused address/callback cascade tests pass.
- [x] Real Pandora reports demonstrate derived children or precise blockers.
- [x] Exact round-trip passes for any source output change.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Implemented `runtime_address` parent facts and `address.runtime.labels.v1` derivation into `address_label` and `address_xref` children.
- Implemented `callback_pointer_path` parent facts and `callback.pointer.callable_targets.v1` derivation into `callback_callable_target` children.
- Source-offset immediates remain candidate-only and emit blockers/review packets instead of accepted parser facts.
- Callback already-code/data outcomes are emitted as exhausted facts rather than repeated proposals.
- Focused tests: `test_cascade_report_keeps_source_offset_immediate_candidate_only` and `test_cascade_report_derives_rsset_address_and_callback_lanes`.

## Cascade Evidence

- Address-space identity is explicit in runtime-address parent scope; source-offset candidates are blocked by `source_offset_candidate_only`.
- Callback path identity is carried through the callback packet selected identity and candidate id.
- Real Pandora blocker summary includes 9 source-offset candidate-only blockers and 179 missing callback consumer blockers.
- Real Pandora exhausted facts: 12 already-represented callback facts.
- Baseline-delta verifier proof: address/callback output-affecting children remain pending until baseline/effective rendering proves a bounded delta and exact round-trip.
- Not report-only: this issue added address and callback cascade lane implementation plus focused tests.
