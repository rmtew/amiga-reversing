# 017-067: Callback Code Verifier Gates

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

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

- [ ] Required verifier layers mapped.
- [ ] Command readiness wired to verifier layers.
- [ ] Stale/missing verifier state fails closed.
- [ ] Negative safety checks neighboring ranges.
- [ ] Exact round-trip required for output-affecting change.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] No command can bypass verifier gates.
- [ ] Failure reasons are explicit.
- [ ] Existing verifier surfaces are reused where appropriate.
- [ ] Tests cover pass and fail-closed cases.
- [ ] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Code implemented, not only documentation.
- [ ] Verifier gates are command-enforced.
- [ ] Tests cover stale/missing/failing verifier states.
- [ ] Exact round-trip passes where output changes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
