# PRD 007: Listing Selection and Keyboard Model

## Status

Complete as of 2026-05-16.

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
- Multi-row or range selection in this PRD; focus/anchor/range behavior is covered by PRD 014.
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

- Resolved: row selection remains the default; element precision is selected
  explicitly or inferred only for unambiguous element-only bindings.
- Resolved: selected rows use distinct styling from transient focused rows.

## Completion Notes

- Listing selection now tracks row and optional element context, drives catalog
  queries, and survives listing refresh by stable row identity with explicit
  precision-loss fallback.
- Focused PRD007 verification passed on 2026-05-16:
  `uv run python -m pytest tests\test_web_e2e_cdp.py tests\test_web_app_source.py -q -k "listing_selection_keyboard_navigation or listing_selection_survives_refresh_by_stable_key or manual_review_panel_filters_and_navigates or command_palette_sends_structured_symbol_context or command_palette_applies_manual_representation or page_level_listing_keys_route_to_listing_viewport or command_palette_and_selection_model"`.

## Follow-On PRDs

- PRD 013 persists listing location as **UI Preference State** and defines first-open entrypoint selection.
- PRD 014 extends **Listing Selection** with focus, anchor, and selected row range.
- PRD 015 preserves **Listing Selection** during immediate projection and background refresh.
