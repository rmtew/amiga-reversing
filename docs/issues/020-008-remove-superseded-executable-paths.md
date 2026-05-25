# 020-008: Remove Superseded Executable Paths

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: completed/reviewed 020-006 and 020-007.
- Current state: once parser, rendering, and analysis all consume shared ranges,
  old platform-specific executable summary/range/import/rendering paths may
  remain as dead or default-adjacent code.
- Desired state after this issue: replaced paths are deleted, not preserved as
  compatibility or legacy alternatives.

## Start-Of-Issue Refresh

Before deleting anything, build a deletion table from Proposal 020 completion
evidence for 020-001 through 020-007. Each row must name the old path, the
replacement proof, and whether deletion is authorized now. Update the checklist
if prior issues discovered additional old paths.

## What To Build

Delete superseded executable import/listing/range paths identified by 020-001
and proven replaceable by 020-002 through 020-007. Update callers/tests to use
the shared path only.

Likely deletion candidates include:

- inspect-only Amiga/Atari fact or section-derived compatibility surfaces that
  are no longer needed after shared model consumers prove equivalent refs;
- Python coverage or current-output assumptions that could synthesize or accept
  old section-derived behavior;
- Mac raw-binary wrapper/post-filter code that is replaced by shared CODE range
  rendering;
- Mac payload/artifact/web projection helpers whose only job was to compensate
  for missing shared executable ranges;
- platform-specific analysis import range derivation replaced by 020-007.

Do not delete code whose replacement was not proven. If a path cannot be safely
deleted, record the exact blocker in Proposal 020 and leave it for a later
issue. Do not keep a compatibility branch for an old behavior that was proven
replaced.

## Acceptance Criteria

- [ ] Deletion table is recorded in Proposal 020 before code deletion.
- [ ] Superseded Amiga executable path code is deleted or explicitly blocked.
- [ ] Superseded Atari executable path code is deleted or explicitly blocked.
- [ ] Superseded Mac executable path code is deleted or explicitly blocked.
- [ ] No compatibility branch keeps old behavior active for migrated paths.
- [ ] Tests fail if callers use a deleted old path.
- [ ] Parser coverage, analysis import, listing/rendering, and artifact tests
  still pass after deletion.
- [ ] Proposal 020 records what was removed and what remains blocked.

## Blocked By

- 020-006
- 020-007

## Required Sign-Off

- [ ] Every deletion is tied to proven replacement behavior.
- [ ] No user or other-agent unrelated changes reverted.
- [ ] No old/default dual path remains for migrated behavior.
- [ ] Focused platform/import/listing/artifact tests pass.
- [ ] Combined current coverage passes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record deleted paths, retained blocked paths, replacement proof links, and
validation output.
