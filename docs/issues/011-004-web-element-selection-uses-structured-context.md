# 011-004: Web Element Selection Uses Structured Context

## Parent

[PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Related PRDs

- [PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Type

AFK

## Labels

done

## What to build

Update web listing selection and command palette catalog requests so selected elements use structured context identifiers from listing metadata rather than inferred element kind and rendered text.

PRD 017 consumes this structured element context for inline editors, representation choices, semantic choosers, and the edit-selected command.

## Acceptance criteria

- [x] Clicked/selectable listing elements carry structured element ids or stable fallback context.
- [x] Command palette element catalog requests include structured element context, not just row index and a guessed element kind.
- [x] If a selected element disappears after listing refresh, the UI falls back to row precision and reports precision loss.
- [x] Enter in the command palette executes the selected visible action and preserves input focus while moving selection with arrow keys.
- [x] CDP tests cover operand/literal selection, symbol/equate-style selection, precision loss, and no-command/backend-error regression for numeric-looking labels.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [011-002: Structured Catalog Context Model](011-002-structured-catalog-context-model.md)
