# 020-009: Cross-Platform Closeout Proof

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-001 through 020-008.
- Current state: final closeout must prove the shared executable import
  pipeline is the active cross-platform path.
- Desired state after this issue: Proposal 020 is complete, with durable
  evidence that Amiga, Atari, and Mac flow through the shared model.

## What To Build

Run and record the full cross-platform closeout proof. Fix any small issues
found during closeout. If a serious gap remains, reopen or create the smallest
follow-up issue instead of marking the proposal complete.

## Acceptance Criteria

- [ ] Amiga HUNK current parser path uses shared executable ranges.
- [ ] Atari PRG current parser path uses shared executable ranges.
- [ ] Mac CODE current parser/listing path uses shared executable ranges.
- [ ] Analysis import consumes shared ranges.
- [ ] Listing/rendering consumes shared ranges.
- [ ] Parser fact coverage passes with `invalid: 0`.
- [ ] Candidate/deferred/unsupported facts remain non-accepted.
- [ ] Superseded paths are deleted or have explicit follow-up blockers.
- [ ] Proposal 020 records closeout state and future work.
- [ ] Completed 020 issue files are deleted after durable conclusions are in
  the proposal.

## Blocked By

- 020-001
- 020-002
- 020-003
- 020-004
- 020-005
- 020-006
- 020-007
- 020-008

## Required Sign-Off

- [ ] `platform_executable_formats validate` passes.
- [ ] Combined current coverage passes.
- [ ] Focused Amiga, Atari, Mac, analysis, listing, and artifact tests pass.
- [ ] Repository precommit gate passes.
- [ ] `git diff --check` passes.
- [ ] Worktree contains no unrelated 020 output churn.

## Completion Evidence

Record exact commands, summaries, remaining future work, and the final proposal
closeout decision.
