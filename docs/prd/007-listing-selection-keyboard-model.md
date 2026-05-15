# PRD 007: Listing Selection and Keyboard Model

## Purpose

Add a durable **Listing Selection** model so keyboard, command palette, context menu, review navigation, and API-driven workflows have a precise current target in the rendered analysis listing.

## Scope

- Track selected listing row independently from temporary jump highlights.
- Support optional **Listing Element** selection for operands, symbols, immediate values, equates, comments, and data literals.
- Define keyboard movement for row selection and viewport movement.
- Preserve selection across listing window reloads when stable row identity still exists.

## Requirements

- Review and Navigate dialog jumps set **Listing Selection** and visually distinguish it from temporary focus/highlight.
- Up/Down moves selected row by one listing row.
- Home, End, PageUp, and PageDown move the viewport while preserving **Listing Selection**.
- Selection survives virtual listing fetches using stable row keys, section offsets, runtime addresses, and row indexes as available.
- Element selection is optional but required for actions where row-level targeting is ambiguous.
- If an element target disappears after reanalysis, selection falls back to the containing row and the UI reports the loss of precision.
- Keyboard handling avoids stealing input from dialogs, search fields, and editable controls.

## Non-Goals

- User-defined key bindings.
- Multi-row or range selection.
- Text-editor-style caret editing.

## Verification

- Web source tests for selection state transitions.
- CDP/e2e tests for arrow-key movement, paging behavior, dialog jump selection, and selection preservation after listing reload.
- Backend tests only where stable row/element identity needs new payload fields.

## Issues

- [007-001: Listing Row Selection](../issues/007-001-listing-row-selection.md)
- [007-002: Selection Keyboard Navigation](../issues/007-002-selection-keyboard-navigation.md)
- [007-003: Selection Preserved Across Reloads](../issues/007-003-selection-preserved-across-reloads.md)
- [007-004: Listing Element Selection](../issues/007-004-listing-element-selection.md)
- [007-005: PRD 007 Review and Tightening](../issues/007-005-prd-007-review-and-tightening.md)

## Open Questions

- Whether the first element in a row should be auto-selected when an action needs element precision.
- Visual styling for selected row versus transient focused row.
