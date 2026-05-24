# 020-008: Remove Superseded Executable Paths

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-006 and 020-007.
- Current state: after migration, old platform-specific executable summary,
  range, import, or rendering paths may remain as dead/default-adjacent code.
- Desired state after this issue: replaced paths are deleted, not preserved as
  compatibility or legacy alternatives.

## What To Build

Delete superseded executable import/listing/range paths identified by 020-001
and proven replaceable by 020-002 through 020-007. Update callers/tests to use
the shared path only.

Do not delete code whose replacement was not proven. If a path cannot be safely
deleted, record the exact blocker in Proposal 020 and leave it for a later
issue.

## Acceptance Criteria

- [ ] Superseded Amiga executable path code is deleted or explicitly blocked.
- [ ] Superseded Atari executable path code is deleted or explicitly blocked.
- [ ] Superseded Mac executable path code is deleted or explicitly blocked.
- [ ] No compatibility branch keeps old behavior active for migrated paths.
- [ ] Tests fail if callers use the deleted old path.
- [ ] Proposal 020 records what was removed and what remains blocked.

## Blocked By

- 020-006
- 020-007

## Required Sign-Off

- [ ] Deletions are tied to proven replacement behavior.
- [ ] No user or other-agent unrelated changes reverted.
- [ ] Focused platform/import/listing tests pass.
- [ ] `git diff --check` passes.

## Completion Evidence

Record deleted paths, retained blocked paths, and validation output.
