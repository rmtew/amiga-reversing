# 017-081: RSSET Base Provenance Command Path

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: start after `017-080` identifies a concrete RSSET base-evidence shape.
- Protocol area: implementing command/report/verifier support for RSSET base provenance if current evidence can justify it.
- Current proposal state: RSSET mutation is blocked until accepted app-base evidence can be represented and verified.
- Desired proposal state after this issue: the selected RSSET base-evidence shape either has a command-backed verifier path or is blocked with fixture proof explaining why it cannot be safely accepted.

## Protocol Delta

- Adds: RSSET base provenance command path, if justified by `017-080`.
- Changes: accepted base evidence must be durable, replayable, verifier-backed, and source-effective before it can affect rendering.
- Replaces: manual or report-only RSSET base assumptions.
- Leaves out of scope: broad RSSET refactors, callback work, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unsafe base provenance must fail closed.
- Accepted evidence must use the Decision Journal or existing durable manual-state mechanism, whichever is already standard for this lane.
- A source-changing RSSET mutation requires generated-source effect and exact round-trip.
- If `017-080` finds no implementable evidence shape, this issue must be marked blocked or superseded with that reason instead of inventing one.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird`
- Selected candidate: from `017-080`, likely the strongest active RSSET group.
- Evidence packet expected: selected RSSET use path, base provenance, conflicts, command dry-run, durable decision/state replay, generated-source diff, verifier artifact, and exact round-trip if source changes.

## Implementation Slice

- C fact graph/query work: expose base provenance facts through normal analysis/export paths if Python cannot safely infer them.
- Python/API/report work: add or complete command dry-run/write path for accepted RSSET base evidence.
- Journal/replay work: accepted base evidence must replay into effective analysis state.
- Renderer/verifier work: add verifier artifact layers for semantic reload, generated-source effect, negative safety, and exact round-trip.
- Tests: fixture command tests, replay tests, verifier tests, and real Pandora dry-run/rerun.

## Research Coverage

- [ ] `017-080` completion evidence checked before work.
- [ ] Selected RSSET candidate and evidence shape named.
- [ ] Command dry-run implemented or existing command verified.
- [ ] Accepted state replays into report/effective analysis.
- [ ] Generated-source effect tested when source change is expected.
- [ ] Negative safety and exact round-trip gates enforced.
- [ ] No callback, 012/018/Mac/platform-format files touched.

## Research Review

- [ ] No helper-only path is closed as complete.
- [ ] Any source effect comes through normal render/effective metadata paths.
- [ ] If no source change occurs, the blocker is implemented and precise.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-080` checked before work.
- [ ] Focused command/replay/verifier tests pass.
- [ ] Real Pandora RSSET rerun performed.
- [ ] Exact round-trip passes for any source change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

