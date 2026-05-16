# 020-003: Oracle Report Schema and Labels

## Parent

[PRD 020: Oracle Compatibility Reports](../prd/020-oracle-compatibility-reports.md)

## Type

AFK

## Labels

done

## What to build

Add report schema fields and scoped labels for **Oracle Compatibility Reports**.

## Acceptance criteria

- [x] Primary oracle result is comparison level.
- [x] Supported labels include `oracle.full_file_match`, `oracle.content_match`, `oracle.mismatch`, `oracle.not_comparable`, `oracle.missing`, and `oracle.not_run`.
- [x] Assembler acceptance and diagnostics are supporting fields.
- [x] Bare `exact` is not used for oracle results.
- [x] Schema tests cover all labels.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- None
