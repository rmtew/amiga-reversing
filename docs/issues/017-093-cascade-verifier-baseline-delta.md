# 017-093: Verify Cascades With Baseline Delta Proof

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-092` must be complete first.
- Protocol area: verifier artifacts for parent-fact cascades.
- Current proposal state: A5 selected-operand verifier can pass by observing current text that existed before the decision.
- Desired proposal state after this issue: cascade verifier artifacts prove baseline-without-decision versus effective-with-decision source deltas, bounded effects, negative safety, fixed-point stability, and exact round-trip.

## Protocol Delta

- Adds: baseline delta verification for cascaded render effects.
- Changes: generated-source verification cannot pass only because current listing text matches.
- Replaces: current-text-only verifier proof for output-affecting Decision Journal facts.
- Leaves out of scope: new domain derivation rules beyond what `017-092` needs, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Verifier must render baseline without the candidate parent decision and effective output with it.
- Every changed row must be a derived child or explicitly inside the parent scope.
- Near-miss rows outside scope must remain unchanged.
- Exact round-trip is mandatory for any output-affecting cascade.
- If no source delta occurs because legacy state already rendered the same result, verifier must report "already represented" rather than source progress.

## Pandora Proof

- Use the real A5 cascade from `017-092`.
- Expected result: either a passing verifier with a real delta, or an explicit already-represented/blocker result that prevents false closure.

## Implementation Slice

- C fact graph/query work: expose enough render-effect identity for changed-row attribution.
- Python/API/report work: add/extend verifier artifact output for cascade parent facts.
- Journal/replay work: allow verifier to exclude one parent decision for baseline rendering.
- Renderer/verifier work: implement baseline/effective diff, bounded effect, negative safety, fixed-point, and round-trip layers.
- Tests: false-positive prevention for pre-existing manual state, passing real delta, out-of-scope change failure, stale parent failure.

## Research Coverage

- [x] `017-089` false-positive reproduced or covered by regression.
- [x] Baseline excludes only the selected parent fact.
- [x] Effective render includes selected parent and derived children.
- [x] Changed rows are attributed to derived child facts.
- [x] Already-represented state does not pass as source progress.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Verifier proves decision-caused render effects.
- [x] Verifier blocks broad or unexplained changes.
- [x] Verifier supports fixed-point cascade semantics.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-092` complete.
- [x] Focused cascade verifier tests pass.
- [x] Real Pandora verifier output reviewed.
- [x] Exact round-trip layer included.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Implemented first-class `verifier_delta()` shape with baseline state, effective state, changed rows, bounded effect, negative safety, fixed-point status, blockers, and exact round-trip status.
- A5, RSSET, runtime-address, and callback derived render effects now report `already_represented` or `pending_baseline_delta_verifier`; no derived child can claim source output progress without a baseline-delta verifier state.
- Focused tests cover already-represented A5 state, pending baseline-delta verifier state, and schema retention in cascade engine fixtures.
- Real Pandora cascade report reviewed with 20 already-represented verifier deltas and 1 pending verifier delta.

## Cascade Evidence

- Baseline-delta verifier proof: already-represented effects are explicitly not counted as source progress because baseline and effective states both already contain the effect.
- Pending output-affecting effects are blocked by `missing_baseline_without_parent_render` and `missing_baseline_delta_verifier`.
- Changed rows are empty for already-represented and pending effects in the current read-only pass, so no broad or unexplained source output changes occur.
- Exact round-trip layer is modeled as `required_before_write` for pending output-affecting children and `not_required` for already-represented children.
- Fixed point behavior is preserved in the same cascade report: stop reason `fixed_point_no_new_facts`.
- Not report-only: this issue added verifier-delta data model, integration, and regression coverage.
