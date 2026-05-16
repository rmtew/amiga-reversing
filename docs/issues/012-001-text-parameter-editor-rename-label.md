# 012-001: Text Parameter Editor Rename Label

## Parent

[PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)
- [PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)
- [PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Type

AFK

## Labels

done

## What to build

Render a palette-hosted text **Command Parameter Editor** for a selected catalog action and use it to rename a selected **Manual Label** through the catalog execution path.

This is the basic prompt replacement slice. PRD 017 later turns the same behavior into reusable palette-hosted and inline **Parameter Sessions**.

## Acceptance criteria

- [x] A command palette action with a required text parameter opens a palette-hosted editor instead of `window.prompt`.
- [x] Rename label pre-fills the current label name when available.
- [x] Enter submits the catalog action with the edited parameter.
- [x] Escape cancels the editor and returns to the command palette state required by PRD 012.
- [x] Web/CDP coverage proves label rename works through the editor.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Progress

Completed 2026-05-16. Verified by focused web source and CDP command-palette rename tests.

## Blocked by

- [006-002: Catalog Action Execution](006-002-catalog-action-execution.md)
- [008-002: Contextual Command Palette](008-002-contextual-command-palette.md)
