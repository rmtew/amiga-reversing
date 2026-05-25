# 021-006: Closeout Proof

Status: active
Type: AFK
Source proposal: docs/proposals/021-native-macos-code-source-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`
- Blocked by: 021-001 through 021-005.
- Current state: final closeout must prove Mac CODE is native through the
  pipeline and that 018/020 evidence authority still holds.
- Desired state after this issue: Proposal 021 is complete.

## What To Build

Run and record the closeout proof. Fix small closeout failures only if they are
clearly inside 021 scope. Serious gaps should become the smallest follow-up
issue, not hidden in closeout.

Required proof:

- native Mac CODE source descriptor is active;
- listing/analysis/artifact/web paths report native Mac CODE identity;
- raw bridge and wrapped raw backend are deleted from active behavior;
- shared executable ranges remain present;
- candidate/deferred/unsupported facts remain non-accepted;
- 020 cross-platform coverage remains green.

## Acceptance Criteria

- [ ] Native Mac CODE source descriptor is active in project resolution.
- [ ] Mac listing/analysis no longer reports wrapped `amiga-raw`.
- [ ] Mac project/artifact/web payloads retain user-visible Mac evidence.
- [ ] Raw bridge is deleted or has an exact out-of-scope blocker.
- [ ] Candidate/deferred/unsupported facts remain non-accepted.
- [ ] Proposal 021 records final state and future work.
- [ ] Completed 021 issue files are deleted after conclusions move to the
  proposal.

## Blocked By

- 021-001
- 021-002
- 021-003
- 021-004
- 021-005

## Required Sign-Off

- [ ] KB validate passes.
- [ ] Combined 020 coverage passes.
- [ ] Focused Mac backend/project/artifact/web tests pass.
- [ ] Focused C/listing tests pass.
- [ ] Repository precommit passes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record exact commands, summaries, remaining future work, deleted issue files,
and final proposal status.
