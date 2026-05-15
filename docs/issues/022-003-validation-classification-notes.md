# 022-003: Validation Classification Notes

## Parent

[PRD 022: Full Reproduction Validation Sweep](../prd/022-full-reproduction-validation-sweep.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Record validation sweep classifications using gate/oracle language rather than console-only notes.

## Acceptance criteria

- [ ] Classification notes distinguish gate exactness from oracle comparison levels.
- [ ] Notes include target, profile, tool availability, and report path.
- [ ] Notes avoid bare `exact` for oracle results.
- [ ] Tests or docs show how future agents should update classifications.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [022-001: GenAm Full Reproduction Validation Refresh](022-001-genam-full-reproduction-validation-refresh.md)
- [022-002: Bloodwych Full Reproduction Validation Refresh](022-002-bloodwych-full-reproduction-validation-refresh.md)

