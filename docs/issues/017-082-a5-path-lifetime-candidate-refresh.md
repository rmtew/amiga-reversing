# 017-082: A5 Path/Lifetime Candidate Refresh

Status: complete
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

- [x] `017-079` closeout checked before work.
- [x] Current A5 path/lifetime report rerun.
- [x] Already accepted refs separated from fresh candidates.
- [x] Render-safe and render-unsafe candidates separated.
- [x] Lifetime blockers classified precisely.
- [x] Any safe candidate processed through existing gates or deferred to a new implementation issue.
- [x] No callback, 012/018/Mac/platform-format files touched.

## Research Review

- [x] Work does not count duplicate accepted A5 refs as progress.
- [x] Any new source mutation is command-backed and verifier-backed.
- [x] If no mutation occurs, blockers are structured and current.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-079` checked before work.
- [x] Real Pandora A5 report rerun.
- [x] Focused tests pass if code changed.
- [x] Exact round-trip passes for any source change.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Current report was rerun against the resolved Pandora listing target
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`;
  the disk/container target alone still has no listing.
- The resolved listing opened successfully. The A5 path/lifetime report found
  `use_count=525`, `accepted_custom_base_evidence_count=20`,
  `command_candidate_count=0`, `safe_to_mutate=false`, and
  `rendering_gate.status=blocked` with missing gate `command_candidate`.
- Current status split is `accepted_custom_base=20` and `unknown=505`.
  Accepted refs are not counted as fresh progress.
- Render split is `symbol_operand=19`, `entry_comment=1`, and `505` without
  render mode because they remain unknown/unaccepted.
- Unknown-use blocker counts are:
  `branch before selected use requires full CFG path proof=494`,
  `call before selected use may clobber A5=288`,
  `return before selected use breaks local path proof=286`,
  `A5 save/restore boundary requires interprocedural lifetime proof=218`, and
  `A5 is redefined before selected use=201`.
- Representative fresh unknowns from the earliest base setup
  `s0:00000498` remain blocked by `call before selected use may clobber A5`
  at uses `s0:000004E6`, `s0:000004EA`, `s0:000004EE`,
  `s0:000004F4`, and `s0:000004FA`.
- No A5 command candidate is currently exposed, so no source mutation or exact
  round-trip action is authorized by this issue.
