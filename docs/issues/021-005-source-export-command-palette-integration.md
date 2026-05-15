# 021-005: Source Export Command Palette Integration

## Parent

[PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Related PRDs

- [PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

List and run Source Export from the centralized command palette as a **Target Tooling Command**.

## Acceptance criteria

- [ ] Export command appears in palette/global command search.
- [ ] Command is not represented as a **Manual Action Catalog** entry.
- [ ] Executing export does not append the **Manual Action Log**.
- [ ] Export parameter flow can choose assembler profile.
- [ ] Web tests cover palette launch and browser export request.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [021-001: Source Export Route and Browser Save](021-001-source-export-route-and-browser-save.md)
- [008-002: Contextual Command Palette](008-002-contextual-command-palette.md)

