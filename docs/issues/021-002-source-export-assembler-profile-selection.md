# 021-002: Source Export Assembler Profile Selection

## Parent

[PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Related PRDs

- [PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Let users choose the **Assembler Profile** for source export.

## Acceptance criteria

- [ ] Supported profiles include `vasm` and `devpac`.
- [ ] Invalid assembler profile names are rejected.
- [ ] UI can collect the profile choice using reusable parameter-session controls where practical.
- [ ] Last selected export assembler may be stored in **UI Preference State**.
- [ ] Tests cover selected profile propagation.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [021-001: Source Export Route and Browser Save](021-001-source-export-route-and-browser-save.md)

