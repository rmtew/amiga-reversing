# 021-005: Delete Raw Bridge

Status: active
Type: AFK
Source proposal: docs/proposals/021-native-macos-code-source-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`
- Blocked by: 021-004.
- Current state: the raw bridge should be replaceable after native source,
  backend, listing/analysis, and payload migration.
- Desired state after this issue: active Mac CODE behavior has no
  `RawBinarySource` bridge or `amiga-raw` wrapper dependency.

## Start-Of-Issue Refresh

Build a deletion table from 021-001 through 021-004 completion evidence. Each
row must name the old path, replacement proof, and deletion/block decision.

## What To Build

Delete `_temporary_code_binary_source` and superseded raw-wrapper code paths.
Update callers and tests to use the native Mac CODE path only.

Do not delete a public compatibility field unless replacement consumers are
proven. Do delete active default paths that only preserve the old raw bridge.

## Acceptance Criteria

- [ ] Deletion table is recorded in Proposal 021.
- [ ] Active `RawBinarySource` bridge behavior for Mac CODE is deleted.
- [ ] Active `wrapped_backend: amiga-raw` behavior for Mac CODE is deleted.
- [ ] Tests fail if Mac CODE listing/analysis tries to use the old raw bridge.
- [ ] Retained compatibility fields have exact blockers.
- [ ] Proposal 021 records removed paths and retained blockers.

## Blocked By

- 021-004

## Required Sign-Off

- [ ] Every deletion has replacement proof.
- [ ] No unrelated 017 or target changes are touched.
- [ ] Focused Mac tests pass.
- [ ] Cross-platform 020 coverage still passes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record deleted paths, blockers, and validation output.
