# 017-070: Callback Accepted Fact Replay Into Analysis

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: callback-derived code replay into analysis state.
- Current proposal state: accepted callback facts can be projected by helper functions only; normal analysis/reload/report paths do not consume them.
- Desired proposal state after this issue: accepted callback facts replay into the normal analysis state used by reports and render planning.

## Protocol Delta

- Adds: normal replay consumption of accepted `callback_derived_code` facts.
- Changes: accepted callback decisions become analysis facts, not side dictionaries.
- Replaces: helper-only `analysis_with_accepted_callback_code` usage if it is not part of the normal pipeline.
- Deletes: unused helper path or marks it private.
- Leaves out of scope: final rendering, verifier artifact production, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: no source output change yet unless existing render paths already consume the fact safely.
- Switched surface to v2: semantic reload/report analysis sees accepted callback code facts.
- Deleted old surface path: helper-only replay bypasses removed or made test-only.
- User-visible behavior: reports show replayed accepted callback fact state.

## Pandora Proof

- Target candidate: fixture accepted callback decision; Pandora only if a real accepted decision exists.
- Evidence packet expected: Decision Journal record, replay projection, semantic reload state, analysis fact state, and report visibility.
- Decision behavior: accepted facts replay deterministically; deferred/rejected records do not create accepted analysis facts.
- Command gate behavior: no render/source command enabled by this issue.
- Render effect: may be reported as pending render support.
- Verifier/round-trip: no output-affecting round-trip required.

## Implementation Slice

- C fact graph/query work: use C/core analysis fact path where accepted code classification belongs; avoid Python-only semantic ownership.
- Python/API/report work: wire replayed callback facts into target load/semantic reload/report surfaces.
- Journal/replay work: consume Decision Journal projection from normal target state.
- Renderer/verifier work: none.
- Tests: semantic reload/report tests for accepted/deferred/rejected callback decisions; C/core tests where applicable.

## Research Coverage

- [ ] Existing analysis reload/replay path traced.
- [ ] Accepted callback fact model wired into normal analysis state.
- [ ] Deferred/rejected records confirmed non-effecting.
- [ ] Report visibility added or verified.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Replay is not test-only helper projection.
- [ ] Core fact ownership is appropriate.
- [ ] No source output changes occur unless already safely supported.
- [ ] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-065` supersession addressed.
- [ ] Code implemented in normal replay/analysis path.
- [ ] Tests cover accepted/deferred/rejected behavior.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
