# 020-009: Cross-Platform Closeout Proof

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: completed/reviewed 020-001 through 020-008.
- Current state: final closeout must prove the shared executable import
  pipeline is the active cross-platform path.
- Desired state after this issue: Proposal 020 is complete, with durable
  evidence that Amiga, Atari, and Mac flow through the shared model from parser
  output to analysis/listing/rendering proof.

## Start-Of-Issue Refresh

Before running closeout, verify that issue docs 020-001 through 020-008 have
their durable conclusions copied into Proposal 020. If a completed issue file
still exists, either delete it after copying conclusions or explain why it must
remain active.

## What To Build

Run and record the full cross-platform closeout proof. Fix small closeout
failures only when the fix is clearly inside 020 scope. If a serious gap
remains, reopen or create the smallest follow-up issue instead of marking the
proposal complete.

Required proof:

- current parser coverage for Mac, Amiga, and Atari;
- shared executable range paths visible in coverage;
- analysis import uses shared ranges;
- listing/rendering uses shared ranges;
- candidate/deferred/unsupported states remain non-accepted;
- removed paths stay removed and no old default path remains;
- exact artifact/round-trip behavior stays exact where expected.

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

Record exact commands, summaries, remaining future work, deleted issue files,
and the final proposal closeout decision.
