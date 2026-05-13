# 0001-007 Review State Rendering Export Warnings

## Parent

PRD 0001: Manual Review Workflow

## What to build

Carry Review State through listing, rendering, reproduction, and export workflows. `blocked` prevents the target from being rated `clear`, but it is not a generic UI or export lock. Viewing, analysis, rendering, and export remain available when meaningful, with warnings explaining live blockers.

## Acceptance criteria

- [ ] Listing and project views show Review State consistently.
- [ ] Blocked targets can still be viewed and rendered when target identity is valid.
- [ ] Exports and reports include warnings for blocked or needs-review targets.
- [ ] Target identity mismatch remains fatal for that project target and prevents applying manual state.
- [ ] Round-trip verification output feeds reproduction mismatch review state.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-004 Manual Review Item Generation
- 0001-006 Checklist Review UI And Suggested Actions
