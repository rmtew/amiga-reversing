# 004-010 Clean Proposal 004 Tracking Docs

Status: Done
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

Proposal 004 follow-up tracking is stale:

- `TODO.md` still lists old legacy issue paths and marks implemented slices as
  open.
- Proposal 004's deletion checklist still refers to the old issue lifecycle.
- Implemented issue files remain as live issue files even though their durable
  reasoning has been promoted into the proposal.

This creates false work and makes the active proposal state harder to trust.

## Scope

- Update `TODO.md` so completed Proposal 004 slices are not listed as open work.
- Replace stale legacy issue references with current Proposal 004 tracking.
- Keep only real follow-up work visible.
- Decide whether implemented `004-001` through `004-006` issue files should be
  deleted or moved to an archive.
- Preserve any durable implementation notes in the proposal before deletion or
  archival.

## Acceptance Criteria

- No stale legacy issue references remain in Proposal 004 tracking docs.
- `TODO.md` only lists active Proposal 004 follow-up work.
- Implemented issue files are either removed after promotion or clearly archived.
- Proposal 004 remains the durable spec.

## Verification

```text
search docs/TODO for stale legacy issue references
review docs/issues/004-* active/open state
docs-only diff review
```

## Implementation Notes

- `TODO.md` now records Proposal 004 as complete instead of listing completed
  slices as open work.
- Proposal 004 status, checkpoint index, source-inventory notes, follow-up
  hardening list, acceptance criteria, and issue archive convention were
  updated.
- Completed issue files remain in `docs/issues/004-*` as an implementation
  archive.

## Verified

```text
stale legacy issue prefix search: no matches
Select-String -Path docs\issues\004-*.md -Pattern '^Status: Proposed'
git diff --check
```
