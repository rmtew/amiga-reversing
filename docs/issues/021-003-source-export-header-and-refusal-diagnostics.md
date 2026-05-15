# 021-003: Source Export Header and Refusal Diagnostics

## Parent

[PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Add a generated source header and structured refusal diagnostics for export.

## Acceptance criteria

- [ ] Header includes target name, assembler profile, metadata or target identity hash, timestamp, and non-verification note.
- [ ] Refusal diagnostics expose source-rendering refusal reason and profile counters.
- [ ] Header does not make source unassemblable for supported profiles.
- [ ] Tests cover header content and refusal payloads.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [021-001: Source Export Route and Browser Save](021-001-source-export-route-and-browser-save.md)

