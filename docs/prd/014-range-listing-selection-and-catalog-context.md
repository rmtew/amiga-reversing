# PRD 014: Range Listing Selection and Catalog Context

## Purpose

Extend **Listing Selection** with focus, anchor, and selected row range so users can apply catalog actions to explicit listing ranges without inferring hidden rows or scraping rendered text.

## Dependencies

- PRD 006: Manual Action Catalog, API, and CLI.
- PRD 007: Listing Selection and Keyboard Model.
- PRD 011: Structured Contextual Action Metadata.

## Scope

- Add focus row, anchor row, and contiguous selected row range to **Listing Selection**.
- Add range-selection catalog contexts using stable row metadata.
- Return applicable, partially applicable, and unavailable actions with concise reasons.
- Support explicit subrange execution where catalog semantics define it.

## Requirements

- Plain ArrowUp and ArrowDown move focus and collapse selection to the focus row.
- Shift+ArrowUp and Shift+ArrowDown keep the anchor row and extend or shrink the selected row range.
- Focus and selected rows render distinctly.
- Range selection survives virtual listing refresh using stable row ids when available, then row index fallback.
- Catalog range requests include selected row ids/indexes and visible structured row metadata.
- Multi-row actions do not infer hidden rows outside the selected visible range.
- Partial applicability is allowed only when the catalog returns explicit applicable subranges and row-specific reasons.
- Actions that cannot state safe subrange semantics are unavailable with a reason.

## Non-Goals

- Text-editor-style arbitrary text selection.
- Inferring action targets from rendered source strings.
- Multi-range or discontiguous selection.

## Verification

- Web source tests for focus/anchor/range transitions.
- Web source tests for collapse on plain Arrow movement.
- Backend/catalog tests for applicable, partial, and unavailable range actions.
- CDP test for selecting a block of data rows and seeing mixed-eligibility actions ordered with reasons.
- Regression tests that range actions use structured row metadata, not rendered text.

## Issues

- [014-001: Focus Anchor Range Selection](../issues/014-001-focus-anchor-range-selection.md)
- [014-002: Range Selection Preserved Across Refresh](../issues/014-002-range-selection-preserved-across-refresh.md)
- [014-003: Range Catalog Context Query](../issues/014-003-range-catalog-context-query.md)
- [014-004: Mixed Range Action Eligibility](../issues/014-004-mixed-range-action-eligibility.md)
- [014-005: Command Palette Range Actions](../issues/014-005-command-palette-range-actions.md)
- [014-006: PRD 014 Review and Tightening](../issues/014-006-prd-014-review-and-tightening.md)

## Open Questions

- Resolved: mouse Shift-click remains out of scope for PRD 014. Keyboard range
  selection is the implemented slice.

## Completion Notes

- Implemented focus/anchor/range keyboard selection with Shift+Arrow extension
  and plain Arrow collapse.
- Range catalog requests send explicit selected row indexes and visible row
  metadata; hidden rows are not inferred.
- Range catalog responses distinguish applicable, partial, and unavailable
  actions with reasons and explicit applicable subranges.
- Partial range execution appends actions only for explicit applicable subranges.
