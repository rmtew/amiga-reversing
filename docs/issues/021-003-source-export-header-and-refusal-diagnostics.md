# 021-003: Source Export Header and Refusal Diagnostics

## Parent

[PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Type

AFK

## Labels

done

## What to build

Add a generated source header and structured refusal diagnostics for export.

## Acceptance criteria

- [x] Header includes target name, assembler profile, metadata or target identity hash, timestamp, and non-verification note.
- [x] Refusal diagnostics expose source-rendering refusal reason and profile counters.
- [x] Header does not make source unassemblable for supported profiles.
- [x] Tests cover header content and refusal payloads.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [021-001: Source Export Route and Browser Save](021-001-source-export-route-and-browser-save.md)
