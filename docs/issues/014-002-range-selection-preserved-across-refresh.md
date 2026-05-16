# 014-002: Range Selection Preserved Across Refresh

## Parent

[PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)
- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

done

## What to build

Preserve range **Listing Selection** across virtual listing refreshes using stable row metadata before falling back to row indexes.

## Acceptance criteria

- [x] Focus, anchor, and range endpoints survive listing window refresh when stable rows still exist.
- [x] Row index fallback is used only when stable row identity is unavailable.
- [x] Lost range precision is reported instead of silently retargeting actions.
- [x] Tests cover stable identity preservation and fallback behavior.
- [x] Existing single-row selection preservation remains intact.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion

Range state stores stable keys for focus, anchor, and range endpoints and
resolves them against rendered rows before falling back to row indexes.

## Blocked by

- [014-001: Focus Anchor Range Selection](014-001-focus-anchor-range-selection.md)
- [011-001: C Listing Element Metadata](011-001-c-listing-element-metadata.md)
