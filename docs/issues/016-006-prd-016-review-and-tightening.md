# 016-006: PRD 016 Review and Tightening

## Parent

[PRD 016: Review Notes](../prd/016-review-notes.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)
- [PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Review **Review Note** behavior against PRD 016 and confirm notes are durable target annotations with optional review-tracking mode, not UI-only bookmarks or source comments.

## Acceptance criteria

- [ ] Review notes are stored through the **Manual Action Log**.
- [ ] `note_only` notes appear in listing and Navigate but not the Review dialog.
- [ ] `needs_review` notes appear as **Manual Review Items** and affect **Review State**.
- [ ] Review notes do not create `blocked` state in the first implementation.
- [ ] Row and range note behavior is covered where implemented.
- [ ] Ctrl-click and Navigate behavior matches standard symbolic navigation interaction.
- [ ] Manual comment behavior remains distinct.
- [ ] PRD 016 issue links are accurate.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [016-001: Review Note Action Log Projection](016-001-review-note-action-log-projection.md)
- [016-002: Review Note Catalog API CLI](016-002-review-note-catalog-api-cli.md)
- [016-003: Review Note Web Surfaces](016-003-review-note-web-surfaces.md)
- [016-004: Range Targeted Review Notes](016-004-range-targeted-review-notes.md)
- [016-005: Manual Comment Review Note Boundary](016-005-manual-comment-review-note-boundary.md)
