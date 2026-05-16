# 020-004: Oracle Results in Reproduction UI

## Parent

[PRD 020: Oracle Compatibility Reports](../prd/020-oracle-compatibility-reports.md)

## Type

AFK

## Labels

done

## What to build

Display oracle compatibility sections in the reproduction panel without confusing them with the exactness gate.

## Acceptance criteria

- [x] UI shows the gate result separately from oracle results.
- [x] Oracle sections lead with comparison level.
- [x] Tool missing and not-comparable cases are clear.
- [x] Diagnostics are available without overwhelming the main summary.
- [x] Web tests cover exact gate plus oracle content match and missing cases.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [020-003: Oracle Report Schema and Labels](020-003-oracle-report-schema-and-labels.md)
