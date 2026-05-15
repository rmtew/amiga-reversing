# 014-001: Focus Anchor Range Selection

## Parent

[PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Extend **Listing Selection** with focus row, anchor row, and contiguous selected row range controlled by Arrow and Shift+Arrow keyboard behavior.

## Acceptance criteria

- [x] Plain ArrowUp and ArrowDown move focus and collapse selection to one row.
- [x] Shift+ArrowUp and Shift+ArrowDown extend or shrink range from the anchor row.
- [x] Focus row and selected rows render distinctly.
- [x] Keyboard handling does not steal input from editable controls.
- [x] Web tests cover focus, anchor, extension, shrink, and collapse.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion

Implemented in `amiga_reversing/web/app.js` with CDP coverage in
`test_brave_cdp_listing_range_selection_and_palette_reasons`.

## Blocked by

- [007-002: Selection Keyboard Navigation](007-002-selection-keyboard-navigation.md)
