# 017-093: Verify Cascades With Baseline Delta Proof

Status: active
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

- [ ] `017-089` false-positive reproduced or covered by regression.
- [ ] Baseline excludes only the selected parent fact.
- [ ] Effective render includes selected parent and derived children.
- [ ] Changed rows are attributed to derived child facts.
- [ ] Already-represented state does not pass as source progress.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Verifier proves decision-caused render effects.
- [ ] Verifier blocks broad or unexplained changes.
- [ ] Verifier supports fixed-point cascade semantics.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-092` complete.
- [ ] Focused cascade verifier tests pass.
- [ ] Real Pandora verifier output reviewed.
- [ ] Exact round-trip layer included.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

