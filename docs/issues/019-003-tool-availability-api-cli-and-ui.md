# 019-003: Tool Availability API CLI and UI

## Parent

[PRD 019: Tool Registry and Oracle Availability](../prd/019-tool-registry-and-oracle-availability.md)

## Type

AFK

## Labels

done

## What to build

Expose **Tool Availability Records** through API, CLI, and Web UI surfaces.

## Acceptance criteria

- [x] API returns availability for requested profile/oracle context.
- [x] CLI can list detected tools and missing reasons.
- [x] UI surfaces unavailable required tools instead of hiding options.
- [x] Missing `vamos` makes built-in GenAm oracle unavailable with a clear reason.
- [x] Tests cover API, CLI, and UI payload rendering.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [019-002: Oracle Tool Availability Detector](019-002-oracle-tool-availability-detector.md)
