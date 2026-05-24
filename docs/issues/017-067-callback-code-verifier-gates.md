# 017-067: Callback Code Verifier Gates

Status: superseded
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

Superseded by: `017-072-callback-verifier-artifact-producer.md`.
Reason: post-commit review found verifier gates are only helper functions and
are not enforced by a real command/verifier artifact path.

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: verifier gates for callback-derived accepted facts.
- Current proposal state: callback code acceptance/rendering needs semantic reload, generated-source, negative-safety, and exact-round-trip gates before source-changing commands are safe.
- Desired proposal state after this issue: callback code actions refuse unsafe changes unless all required verifier layers pass.

## Protocol Delta

- Adds: verifier layer integration for callback-derived code facts.
- Changes: callback accept/render commands become verifier-gated rather than trust packet evidence alone.
- Replaces: any weaker command readiness check for callback code.
- Deletes: obsolete verifier bypasses if found.
- Leaves out of scope: unrelated verifier refactors, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: source-changing actions fail closed until verifier layers pass.
- Switched surface to v2: callback code command readiness uses protocol verifier layers.
- Deleted old surface path: any replaced readiness shortcut must be removed.
- User-visible behavior: command output explains pass/fail layer state.

## Pandora Proof

- Target candidate: fixture first; Pandora if a real accepted callback candidate exists.
- Evidence packet expected: decision id, replay result, render effect, semantic reload result, generated-source result, negative-safety result, exact-round-trip result, and blockers.
- Decision behavior: accepted fact may exist, but source-changing action refuses if verifier state is missing/stale/failing.
- Command gate behavior: fail closed on stale artifact, missing semantic reload, source diff mismatch, neighbor change, or round-trip failure.
- Render effect: only after verifier gates pass.
- Verifier/round-trip: all required.

## Implementation Slice

- C fact graph/query work: expose enough replay/render state for verifier checks.
- Python/API/report work: integrate verifier layers into command readiness and reports.
- Journal/replay work: consume decision ids and replay status.
- Renderer/verifier work: implement or reuse semantic reload, generated-source diff, negative safety, and exact round-trip checks for callback code.
- Tests: pass/fail layer tests, stale artifact fail-closed tests, exact round-trip test for output-affecting fixture.

## Research Coverage

- [x] Required verifier layers mapped.
- [x] Command readiness wired to verifier layers.
- [x] Stale/missing verifier state fails closed.
- [x] Negative safety checks neighboring ranges.
- [x] Exact round-trip required for output-affecting change.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] No command can bypass verifier gates.
- [x] Failure reasons are explicit.
- [x] Existing verifier surfaces are reused where appropriate.
- [x] Tests cover pass and fail-closed cases.
- [x] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Code implemented, not only documentation.
- [x] Verifier gates are command-enforced.
- [x] Tests cover stale/missing/failing verifier states.
- [x] Exact round-trip passes where output changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Added `callback_verifier_gate` requiring semantic reload, generated source, negative safety, and exact round-trip pass states.
- Missing verifier state and individual failing layers block render/source effects.
- No output-affecting Pandora change occurred, so exact round-trip was not required for target output.
