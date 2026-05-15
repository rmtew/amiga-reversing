# 021-004: Source Export CLI

## Parent

[PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Expose **Source Export** through CLI with selected assembler profile.

## Acceptance criteria

- [ ] CLI command exports `.s` source for a target.
- [ ] CLI accepts assembler profile selection.
- [ ] CLI reports refusal diagnostics clearly.
- [ ] CLI does not imply export is verification.
- [ ] Tests cover success, profile selection, and refusal.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [021-001: Source Export Route and Browser Save](021-001-source-export-route-and-browser-save.md)

