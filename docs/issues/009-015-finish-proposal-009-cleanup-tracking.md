# 009-015 Finish Proposal 009 Cleanup Tracking

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## Problem

Proposal 009 still reads as ready for implementation while its original issue
set is marked done. It also contains stale current-code evidence that no longer
matches implemented source-export behavior. This makes the proposal unreliable
as the durable implementation record.

## Scope

- Update Proposal 009 status to reflect completed, remaining, and deferred work.
- Move durable implementation notes from completed 009 issues into the proposal.
- Mark the new cleanup follow-up issues as the remaining work.
- Remove stale current-code evidence that contradicts the codebase.
- Keep completed issue files only if the project keeps them as an explicit
  archive.

## Acceptance Criteria

- Proposal 009 clearly distinguishes completed implementation from remaining
  cleanup.
- Stale evidence about source export and reproduction ownership is corrected or
  removed.
- The deletion checklist points to live follow-up issues for any unfinished
  cleanup.
- Issue status and proposal status no longer contradict each other.

## Blocked by

- `docs/issues/009-010-route-all-production-source-rendering-through-source-rendering-module.md`
- `docs/issues/009-011-finish-c-profiled-operation-adapter-for-touched-c-calls.md`
- `docs/issues/009-012-collapse-round-trip-profile-timings-into-workflow-profile.md`
- `docs/issues/009-013-finish-round-trip-verification-phase-encapsulation.md`
- `docs/issues/009-014-delete-dead-phase-timer.md`

## Required tests

```text
docs-only review
search docs for stale 009 implementation/current-code evidence
search docs/issues for completed active 009 issues
```

## Implementation notes

- Marked Proposal 009 implemented.
- Replaced stale current-code evidence with a current implementation summary.
- Recorded the remaining separate-module move as future work only, not active
  required cleanup.
- Kept completed 009 issue files as the project-local issue archive.

## Verification

Passed:

```text
docs-only review
search docs/proposals/009 for stale source-export/current-code evidence
search docs/issues for remaining Proposed 009 issues
```
