# 020-002: GenAm Via Vamos Oracle Compatibility Run

## Parent

[PRD 020: Oracle Compatibility Reports](../prd/020-oracle-compatibility-reports.md)

## Type

AFK

## Labels

done

## What to build

Run the GenAm/DevPac-compatible oracle through `vamos` and produce a scoped oracle compatibility result.

## Acceptance criteria

- [x] Source is rendered with the DevPac-compatible assembler profile.
- [x] `genam` and `vamos` availability are required for the built-in GenAm oracle.
- [x] Missing `vamos` reports `oracle.missing`, not gate failure.
- [x] Output is compared where comparable.
- [x] Reports name the concrete GenAm/vamos tool chain used.
- [x] Tests cover fake success, missing tool, and rejected source cases.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [019-002: Oracle Tool Availability Detector](019-002-oracle-tool-availability-detector.md)
