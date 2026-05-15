# 020-001: Vasm Oracle Compatibility Run

## Parent

[PRD 020: Oracle Compatibility Reports](../prd/020-oracle-compatibility-reports.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Run the vasm source oracle and produce a scoped oracle compatibility result.

## Acceptance criteria

- [ ] Source is rendered with the vasm assembler profile.
- [ ] `vasm` availability is required for the vasm oracle run.
- [ ] Accepted, rejected, missing, and tool-error cases are classified.
- [ ] Output is compared where comparable.
- [ ] Tests cover fake vasm success and failure cases.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [019-002: Oracle Tool Availability Detector](019-002-oracle-tool-availability-detector.md)

