# 019-001: Tool Registry Storage

## Parent

[PRD 019: Tool Registry and Oracle Availability](../prd/019-tool-registry-and-oracle-availability.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Add project/workspace **Tool Registry** storage for external oracle tool paths and discovery hints.

## Acceptance criteria

- [ ] Tool Registry is separate from target metadata and **Manual Action Log**.
- [ ] Registry supports `vasm`, `genam`, and `vamos` tool ids.
- [ ] Invalid registry payloads fail with clear errors.
- [ ] Tests cover missing, empty, and populated registry files.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- None

