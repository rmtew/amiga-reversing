# 020-003: Oracle Report Schema and Labels

## Parent

[PRD 020: Oracle Compatibility Reports](../prd/020-oracle-compatibility-reports.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Add report schema fields and scoped labels for **Oracle Compatibility Reports**.

## Acceptance criteria

- [ ] Primary oracle result is comparison level.
- [ ] Supported labels include `oracle.full_file_match`, `oracle.content_match`, `oracle.mismatch`, `oracle.not_comparable`, `oracle.missing`, and `oracle.not_run`.
- [ ] Assembler acceptance and diagnostics are supporting fields.
- [ ] Bare `exact` is not used for oracle results.
- [ ] Schema tests cover all labels.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- None

