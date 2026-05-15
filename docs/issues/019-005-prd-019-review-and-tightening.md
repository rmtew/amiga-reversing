# 019-005: PRD 019 Review and Tightening

## Parent

[PRD 019: Tool Registry and Oracle Availability](../prd/019-tool-registry-and-oracle-availability.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Review tool-registry implementation and docs against PRD 019.

## Acceptance criteria

- [ ] Tool ids remain limited to `vasm`, `genam`, and `vamos` for this PRD slice.
- [ ] Tool paths are not stored in target metadata.
- [ ] Availability payloads are structured and tested.
- [ ] PRD and issue links are accurate.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [019-001: Tool Registry Storage](019-001-tool-registry-storage.md)
- [019-002: Oracle Tool Availability Detector](019-002-oracle-tool-availability-detector.md)
- [019-003: Tool Availability API CLI and UI](019-003-tool-availability-api-cli-and-ui.md)
- [019-004: Availability Stamping in Reports](019-004-availability-stamping-in-reports.md)

