# 0001-010 Keep Live Blockers Blocked

## Parent

PRD 0001: Manual Review Workflow

## What to build

Make hard-blocking Manual Review Items stay blocking while the underlying contradiction is still present. A user may acknowledge that a conflict was seen, but an unchanged live blocker must not be projected as resolved or allow the target to become `clear`.

This should cover the end-to-end path from regenerated review items through manual resolution actions and the checklist UI, so the visible Review State matches the actual blocker state.

## Acceptance criteria

- [ ] A Manual Resolution for a non-blocking item can still mark the matching Evidence Fingerprint as resolved.
- [ ] A Manual Resolution for a hard-blocking item records the acknowledgement but leaves the item open while the same blocker evidence is still present.
- [ ] When the underlying blocker evidence changes or disappears, prior acknowledgement does not hide the new state.
- [ ] Checklist UI actions for conflicts make clear that acknowledgement does not clear a live blocker.
- [ ] A target with any live hard-blocking Manual Review Item cannot be rated `clear`.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-004 Manual Review Item Generation
- 0001-006 Checklist Review UI And Suggested Actions
- 0001-007 Review State Rendering Export Warnings

