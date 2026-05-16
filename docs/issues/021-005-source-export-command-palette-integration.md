# 021-005: Source Export Command Palette Integration

## Parent

[PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Related PRDs

- [PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## Labels

done

## What to build

List and run Source Export from the centralized command palette as a **Target Tooling Command**.

## Acceptance criteria

- [x] Export command appears in palette/global command search.
- [x] Command is not represented as a **Manual Action Catalog** entry.
- [x] Executing export does not append the **Manual Action Log**.
- [x] Export parameter flow can choose assembler profile.
- [x] Web tests cover palette launch and browser export request.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [021-001: Source Export Route and Browser Save](021-001-source-export-route-and-browser-save.md)
- [008-002: Contextual Command Palette](008-002-contextual-command-palette.md)
