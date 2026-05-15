# PRD 016: Review Notes

## Purpose

Add **Review Note** actions so user-authored notes and bookmarks become durable target annotations, with optional review-tracking mode for notes that should appear as **Manual Review Items**.

## Dependencies

- PRD 006: Manual Action Catalog, API, and CLI.
- PRD 014: Range Listing Selection and Catalog Context, for range-targeted notes.
- PRD 017: Inline and Palette Parameter Sessions, for reusable note text editing hosts once note actions exist.

## Scope

- Add catalog actions for `add_review_note`, `edit_review_note`, and `clear_review_note`.
- Store notes in the **Manual Action Log**.
- Project review-tracking notes into **Manual Review Items** with open/resolved state.
- Display notes consistently in the listing, Navigate dialog, command palette, HTTP API, and CLI.
- Reuse PRD 017 parameter sessions for note body add/edit when available; otherwise keep note editing catalog-backed through the basic command parameter editor.

## Requirements

- A **Review Note** targets a location or range and may have an optional title plus optional body.
- A bookmark is a note with minimal title/body.
- First implementation targets rows and ranges; target-level and section-level notes are later work.
- Review notes are distinct from **Manual Comments**; they are review workflow state, not source/rendering annotation.
- Review notes have explicit tracking mode: `note_only` or `needs_review`.
- Adding or editing a note appends a **Manual Action Log** entry.
- Clearing a note appends a compensating action rather than deleting prior history.
- `note_only` notes appear in listing and Navigate surfaces but do not appear in the Review dialog and do not affect **Review State**.
- `needs_review` notes project into **Manual Review Items**, appear in the Review dialog, and contribute to `needs_review` **Review State** while open.
- Review notes do not create `blocked` **Review State** in the first implementation.
- All review notes appear in the Navigate dialog under a dedicated Review Notes class with type/status badges.
- Listing annotations show compact badges first; icons are later optional polish.
- Click selects or focuses the note target; Ctrl-click opens Navigate focused on that note, matching standard symbolic navigation behavior.
- Duplicate notes on the same target are allowed.
- If a note target cannot be resolved after analysis changes, keep the note in Navigate under unresolved location; `needs_review` notes remain open with a stale-location reason.
- Catalog eligibility is backend-owned; there are no web-only note actions.
- Row-level note actions work without range selection; range-targeted notes use PRD 014 context when available.
- Review-note inline editing is owned here, not by PRD 017; PRD 017 provides reusable hosts.

## Non-Goals

- Freeform project documentation.
- Source-rendered comments.
- Replacing **Manual Resolution** for generated review items.

## Verification

- Backend tests for review-note Manual Action Log records and projection rules.
- Route tests for add, edit, and clear note actions.
- CLI tests for listing and invoking note actions.
- Web/CDP tests for adding a row note through the command palette and seeing it in listing and Navigate.
- Web/CDP tests proving only `needs_review` notes appear in the Review dialog.
- Tests proving notes and **Manual Comments** render through distinct surfaces.

## Issues

- [016-001: Review Note Action Log Projection](../issues/016-001-review-note-action-log-projection.md)
- [016-002: Review Note Catalog API CLI](../issues/016-002-review-note-catalog-api-cli.md)
- [016-003: Review Note Web Surfaces](../issues/016-003-review-note-web-surfaces.md)
- [016-004: Range Targeted Review Notes](../issues/016-004-range-targeted-review-notes.md)
- [016-005: Manual Comment Review Note Boundary](../issues/016-005-manual-comment-review-note-boundary.md)
- [016-006: PRD 016 Review and Tightening](../issues/016-006-prd-016-review-and-tightening.md)

## Open Questions

- Resolved: first implementation stores note bodies as plain text. Markdown
  rendering is later polish.

## Completion Notes

- Added durable `add_review_note`, `edit_review_note`, and `clear_review_note`
  Manual Action Log actions.
- `note_only` notes stay in listing/Navigate surfaces only.
- `needs_review` notes project into non-blocking Manual Review Items and update
  Review State.
- Row and range note creation use catalog/API/CLI paths and schema-backed web
  parameter entry.
