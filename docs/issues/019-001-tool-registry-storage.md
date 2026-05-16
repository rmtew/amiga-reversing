# 019-001: Tool Registry Storage

## Parent

[PRD 019: Tool Registry and Oracle Availability](../prd/019-tool-registry-and-oracle-availability.md)

## Type

AFK

## Labels

done

## What to build

Add project/workspace **Tool Registry** storage for external oracle tool paths and discovery hints.

## Acceptance criteria

- [x] Tool Registry is separate from target metadata and **Manual Action Log**.
- [x] Registry supports `vasm`, `genam`, and `vamos` tool ids.
- [x] Invalid registry payloads fail with clear errors.
- [x] Tests cover missing, empty, and populated registry files.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- None
