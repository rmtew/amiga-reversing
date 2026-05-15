# 020-004: Oracle Results in Reproduction UI

## Parent

[PRD 020: Oracle Compatibility Reports](../prd/020-oracle-compatibility-reports.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Display oracle compatibility sections in the reproduction panel without confusing them with the exactness gate.

## Acceptance criteria

- [ ] UI shows the gate result separately from oracle results.
- [ ] Oracle sections lead with comparison level.
- [ ] Tool missing and not-comparable cases are clear.
- [ ] Diagnostics are available without overwhelming the main summary.
- [ ] Web tests cover exact gate plus oracle content match and missing cases.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [020-003: Oracle Report Schema and Labels](020-003-oracle-report-schema-and-labels.md)

