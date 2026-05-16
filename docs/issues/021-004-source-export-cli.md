# 021-004: Source Export CLI

## Parent

[PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Type

AFK

## Labels

done

## What to build

Expose **Source Export** through CLI with selected assembler profile.

## Acceptance criteria

- [x] CLI command exports `.s` source for a target.
- [x] CLI accepts assembler profile selection.
- [x] CLI reports refusal diagnostics clearly.
- [x] CLI does not imply export is verification.
- [x] Tests cover success, profile selection, and refusal.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [021-001: Source Export Route and Browser Save](021-001-source-export-route-and-browser-save.md)
