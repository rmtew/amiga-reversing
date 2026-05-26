# 017-094: Cascade RSSET/App-Base Facts Into Field Analysis

Status: completed
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

- [x] Current RSSET report and Decision Journal state checked.
- [x] Parent scope/lifetime is explicit.
- [x] Derived children carry parent/rule provenance.
- [x] Downstream candidates are emitted without unsafe mutation.
- [x] Baseline delta verifier used for any source change.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This makes RSSET a cascade lane, not a selected operand lane.
- [x] Existing accepted state is not counted as new progress unless it causes new derived output.
- [x] Blocked candidates remain explainable.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-093` complete.
- [x] Focused RSSET cascade tests pass.
- [x] Real Pandora RSSET cascade report produced.
- [x] Exact round-trip passes for any source output change.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Implemented `rsset_app_base` parent fact construction for accepted RSSET/app-base candidates.
- Implemented `rsset.app_base.field_refs.v1` derivation into `rsset_app_field_ref` and `rsset_downstream_candidate` children with parent/rule provenance.
- Blocked RSSET candidates remain structured blocked children and review packets, preserving blockers such as `missing_accepted_base_evidence` and `missing_field_or_layout_refinement`.
- Focused test: `test_cascade_report_derives_rsset_address_and_callback_lanes`.
- Real Pandora cascade report produced by the full `cascade-report` command.

## Cascade Evidence

- Parent scope includes target id, candidate id, and selected identity for accepted RSSET facts.
- Derived field/downstream children carry `parent_fact_ids` and rule id `rsset.app_base.field_refs.v1`.
- Real Pandora blocker summary includes 123 `missing_accepted_base_evidence`, 6 `missing_field_or_layout_refinement`, and 1 `missing_accepted_rsset_app_base_parent`.
- Baseline-delta verifier proof: RSSET output-affecting children remain pending until baseline/effective rendering proves a bounded delta.
- Exact round-trip: no RSSET source output change was applied by this issue.
- Not report-only: this issue added RSSET cascade lane implementation and focused tests.
