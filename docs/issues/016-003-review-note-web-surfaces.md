# 016-003: Review Note Web Surfaces

## Parent

[PRD 016: Review Notes](../prd/016-review-notes.md)

## Related PRDs

- [PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)
- [PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)
- [PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Let users add, edit, clear, and view **Review Notes** from the web command palette, listing annotations, Navigate dialog, and Review dialog where applicable.

## Acceptance criteria

- [x] The command palette exposes review-note actions for the current row.
- [x] Adding a note uses schema-backed parameter entry for title, body, and tracking mode.
- [x] If PRD 017 parameter sessions are available, note add/edit uses the shared palette or inline text host rather than a note-specific editor.
- [x] Listing annotations show compact badges that distinguish `note_only` and `needs_review`.
- [x] All current notes appear in Navigate under a Review Notes class.
- [x] Ctrl-click on a note annotation opens Navigate focused on that note.
- [x] Only `needs_review` notes appear in the Review dialog as **Manual Review Items**.
- [x] Clearing a note updates listing, Navigate, and Review dialog surfaces as applicable.
- [x] CDP coverage adds a row note and sees it in listing and Navigate.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Review notes use the existing command parameter editor.
- Listing badges render as Note/Review chips and locally update after append.
- Navigate has a Review Notes class; note navigation refreshes cached entries before focusing.

## Blocked by

- [016-002: Review Note Catalog API CLI](016-002-review-note-catalog-api-cli.md)
- [012-001: Text Parameter Editor Rename Label](012-001-text-parameter-editor-rename-label.md)
