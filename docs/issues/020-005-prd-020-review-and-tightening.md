# 020-005: PRD 020 Review and Tightening

## Parent

[PRD 020: Oracle Compatibility Reports](../prd/020-oracle-compatibility-reports.md)

## Type

AFK

## Labels

done

## What to build

Review oracle compatibility implementation and docs against PRD 020.

## Acceptance criteria

- [x] Oracle results are scoped and never reported as gate exactness.
- [x] vasm and GenAm/vamos reports include concrete tool evidence.
- [x] Missing tools are explicit.
- [x] PRD and issue links are accurate.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [020-001: Vasm Oracle Compatibility Run](020-001-vasm-oracle-compatibility-run.md)
- [020-002: GenAm Via Vamos Oracle Compatibility Run](020-002-genam-via-vamos-oracle-compatibility-run.md)
- [020-003: Oracle Report Schema and Labels](020-003-oracle-report-schema-and-labels.md)
- [020-004: Oracle Results in Reproduction UI](020-004-oracle-results-in-reproduction-ui.md)
