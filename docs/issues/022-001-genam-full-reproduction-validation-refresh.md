# 022-001: GenAm Full Reproduction Validation Refresh

## Parent

[PRD 022: Full Reproduction Validation Sweep](../prd/022-full-reproduction-validation-sweep.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Re-run and record full reproduction validation for the GenAm target with current gate and oracle reporting.

## Acceptance criteria

- [ ] Fresh GenAm reproduction report is produced or archived as agreed by project conventions.
- [ ] Gate result is classified separately from oracle results.
- [ ] Missing tools are recorded explicitly.
- [ ] Classification is recorded in report or follow-up notes.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [020-003: Oracle Report Schema and Labels](020-003-oracle-report-schema-and-labels.md)

