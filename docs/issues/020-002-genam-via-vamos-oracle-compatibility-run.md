# 020-002: GenAm Via Vamos Oracle Compatibility Run

## Parent

[PRD 020: Oracle Compatibility Reports](../prd/020-oracle-compatibility-reports.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Run the GenAm/DevPac-compatible oracle through `vamos` and produce a scoped oracle compatibility result.

## Acceptance criteria

- [ ] Source is rendered with the DevPac-compatible assembler profile.
- [ ] `genam` and `vamos` availability are required for the built-in GenAm oracle.
- [ ] Missing `vamos` reports `oracle.missing`, not gate failure.
- [ ] Output is compared where comparable.
- [ ] Reports name the concrete GenAm/vamos tool chain used.
- [ ] Tests cover fake success, missing tool, and rejected source cases.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [019-002: Oracle Tool Availability Detector](019-002-oracle-tool-availability-detector.md)

