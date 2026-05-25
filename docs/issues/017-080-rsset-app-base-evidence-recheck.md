# 017-080: RSSET App-Base Evidence Recheck

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: start after `017-079` callback lane closeout.
- Protocol area: refreshing the RSSET/app-base lane after callback tooling exhausted current Pandora evidence.
- Current proposal state: earlier 017 passes left RSSET groups, especially `$022E`, blocked by missing accepted base evidence.
- Desired proposal state after this issue: current RSSET blockers are rechecked against present tooling and classified into command-ready evidence, missing-evidence shapes, or no-longer-promising candidates.

## Protocol Delta

- Adds: current RSSET/app-base report refresh and blocker classification.
- Changes: old RSSET conclusions must be revalidated from current reports, not copied forward.
- Replaces: relying on stale `$022E` blocker notes.
- Leaves out of scope: speculative RSSET mutation, callback work, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- This issue is report/classification work unless a small report bug blocks correct classification.
- If a fixable report bug is found, implement the minimal code path with focused tests.
- No RSSET source mutation is allowed in this issue.
- If command-ready accepted base evidence exists, create a dependent implementation issue rather than mutating here.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird`
- Historical candidate: `rsset-raw-a6:022E` at `s0:000006E4`
- Expected report: current RSSET candidate report with grouped displacements, top blockers, accepted base evidence counts, and command readiness.
- Evidence packet expected: strongest active RSSET group with selected identity and exact blocker reason.

## Implementation Slice

- C fact graph/query work: only if current RSSET report lacks required C-owned facts to classify base evidence.
- Python/API/report work: rerun and summarize current RSSET reports; patch report output only if it cannot express the required blocker state.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests: focused tests for any report-code change; otherwise issue validator and whitespace check.

## Research Coverage

- [ ] `017-079` closeout checked before work.
- [ ] Current RSSET report rerun.
- [ ] Top RSSET groups listed with blockers and accepted base evidence counts.
- [ ] Historical `$022E` state rechecked.
- [ ] Missing evidence shape recorded precisely if still blocked.
- [ ] Any report-code change covered by focused tests.
- [ ] No callback, 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Conclusions are based on current report output.
- [ ] Strongest RSSET candidate is selected or explicitly rejected.
- [ ] Any command-ready result is deferred to a dependent implementation issue.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-079` checked before work.
- [ ] Real Pandora RSSET report rerun.
- [ ] No source or journal writes performed.
- [ ] Focused tests pass if code changed.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

