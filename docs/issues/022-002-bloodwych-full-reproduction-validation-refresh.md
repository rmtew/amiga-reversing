# 022-002: Bloodwych Full Reproduction Validation Refresh

## Parent

[PRD 022: Full Reproduction Validation Sweep](../prd/022-full-reproduction-validation-sweep.md)

## Type

AFK

## Labels

done

## What to build

Re-run and record full reproduction validation for Bloodwych with current gate and oracle reporting.

## Acceptance criteria

- [x] Fresh Bloodwych reproduction report is produced or archived as agreed by project conventions.
- [x] Gate result is classified separately from oracle results.
- [x] Content/container differences use current vocabulary.
- [x] Classification is recorded in report or follow-up notes.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [020-003: Oracle Report Schema and Labels](020-003-oracle-report-schema-and-labels.md)
