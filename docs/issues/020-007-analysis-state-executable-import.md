# 020-007: Analysis-State Executable Import

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: completed/reviewed 020-003, 020-004, and 020-005.
- Current state: parser summaries and listing output expose executable
  structure, but analysis state can still re-derive executable range roles from
  platform-specific JSON or C internals.
- Desired state after this issue: analysis import consumes shared executable
  ranges through one durable path.

## Start-Of-Issue Refresh

Before coding, read 020-003 through 020-006 completion evidence. If 020-006
changed the shared rendering contract, align analysis import with that contract
instead of duplicating older parser-specific assumptions.

## What To Build

Feed shared executable ranges into analysis state through one import path. The
analysis state should receive durable range roles, source/stored byte spans,
load offsets, provenance, KB fact refs, candidate/deferred/unsupported markers,
and stable identity.

Required behavior:

- Amiga HUNK shared ranges enter analysis state without re-deriving role from
  old `sections` JSON.
- Atari PRG shared ranges enter analysis state without promoting BSS or
  relocation breadth.
- Mac CODE shared ranges enter analysis state without promoting byte-entry,
  relocation/fixup, or candidate code facts.
- Analysis state must preserve fact authority and parser-use information needed
  for later review/verifier reporting.
- The import path must be shared; platform-specific adapters may normalize raw
  parser inputs into the shared model, but analysis must not have separate
  active role-classification logic per platform.
- Do not perform broad target regeneration. Use fixtures/current-output proof
  unless a focused target artifact is required to prove the path.

## Acceptance Criteria

- [ ] A shared parser-summary-to-analysis import path exists.
- [ ] Amiga migrated ranges enter analysis state through that path.
- [ ] Atari migrated ranges enter analysis state through that path.
- [ ] Mac migrated ranges enter analysis state through that path.
- [ ] Analysis facts preserve KB fact refs, statuses, and parser-use authority.
- [ ] Candidate/deferred/unsupported facts remain non-accepted in analysis.
- [ ] Tests fail if analysis import falls back to old platform-specific range
  derivation for migrated behavior.
- [ ] Proposal 020 records the analysis fact shape and any retained blockers.

## Blocked By

- 020-003
- 020-004
- 020-005
- Review 020-006 completion before finalizing import assumptions

## Required Sign-Off

- [ ] No platform-specific analysis side route remains active for migrated
  behavior.
- [ ] No broad target regeneration unless required by focused tests.
- [ ] Parser coverage still passes.
- [ ] Focused analysis/import tests pass.
- [ ] Focused listing/rendering tests still pass if shared contract is touched.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the analysis-state fact shape, a small proof for each platform, and the
old analysis/import paths ready for 020-008 deletion.
