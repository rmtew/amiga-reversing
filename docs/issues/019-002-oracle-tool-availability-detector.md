# 019-002: Oracle Tool Availability Detector

## Parent

[PRD 019: Tool Registry and Oracle Availability](../prd/019-tool-registry-and-oracle-availability.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Detect availability for `vasm`, `genam`, and `vamos` from configured paths and PATH lookup.

## Acceptance criteria

- [ ] Detector returns **Tool Availability Records** with required fields.
- [ ] Configured paths take precedence over PATH lookup.
- [ ] Cheap version and executable stamps are included when possible.
- [ ] Status values are `available`, `missing`, `unsupported`, or `error`.
- [ ] Tests cover fake available tools, missing tools, bad paths, and probe errors.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [019-001: Tool Registry Storage](019-001-tool-registry-storage.md)

