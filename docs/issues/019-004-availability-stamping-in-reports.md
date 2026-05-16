# 019-004: Availability Stamping in Reports

## Parent

[PRD 019: Tool Registry and Oracle Availability](../prd/019-tool-registry-and-oracle-availability.md)

## Type

AFK

## Labels

done

## What to build

Stamp requested oracle **Tool Availability Records** into reproduction/oracle reports.

## Acceptance criteria

- [x] Reports include availability only for requested oracle checks.
- [x] Stamps include tool id, resolved path, version, discovery source, required flag, and executable stamp when available.
- [x] Missing optional oracle tools do not fail the exactness gate.
- [x] Tests prove unrequested tools are not stamped.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [019-002: Oracle Tool Availability Detector](019-002-oracle-tool-availability-detector.md)
