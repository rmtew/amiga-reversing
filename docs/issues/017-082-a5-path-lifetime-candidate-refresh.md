# 017-082: A5 Path/Lifetime Candidate Refresh

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: start after `017-079` callback lane closeout.
- Protocol area: refreshing A5 custom-base/path-lifetime candidates for source-quality progress.
- Current proposal state: previous A5 work accepted some safe refs and left others blocked by lifetime, render safety, or existing accepted state.
- Desired proposal state after this issue: current A5 candidates are reclassified from fresh reports into source-safe command candidates or precise blocker categories.

## Protocol Delta

- Adds: current A5 report refresh after callback-lane closeout.
- Changes: stale A5 blockers must be rechecked against present analysis and render behavior.
- Replaces: assuming the old A5 queue is still exhausted without rerunning it.
- Leaves out of scope: broad A5 model rewrite, callback work, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Already accepted A5 refs are not progress.
- Unsafe symbolic rendering must fail closed.
- If a fresh A5 candidate is safe, it must go through the existing command/verifier/round-trip path.
- If no candidate is safe, report the exact current blocker categories.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird`
- Candidate source: current A5 path/lifetime report.
- Evidence packet expected: selected A5 use or group with lifetime proof, source evidence status, render-safety status, command readiness, and exact blocker reason.

## Implementation Slice

- C fact graph/query work: only if lifetime/path facts are missing from current exported analysis.
- Python/API/report work: rerun and classify current A5 path/lifetime report; improve report output if blocker states are too flat to act on.
- Journal/replay work: use existing A5 command path only if a candidate becomes safe.
- Renderer/verifier work: use existing generated-source and round-trip gates for any source effect.
- Tests: focused tests for any report or command change; otherwise current-report validation and issue validator.

## Research Coverage

- [ ] `017-079` closeout checked before work.
- [ ] Current A5 path/lifetime report rerun.
- [ ] Already accepted refs separated from fresh candidates.
- [ ] Render-safe and render-unsafe candidates separated.
- [ ] Lifetime blockers classified precisely.
- [ ] Any safe candidate processed through existing gates or deferred to a new implementation issue.
- [ ] No callback, 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Work does not count duplicate accepted A5 refs as progress.
- [ ] Any new source mutation is command-backed and verifier-backed.
- [ ] If no mutation occurs, blockers are structured and current.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-079` checked before work.
- [ ] Real Pandora A5 report rerun.
- [ ] Focused tests pass if code changed.
- [ ] Exact round-trip passes for any source change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

