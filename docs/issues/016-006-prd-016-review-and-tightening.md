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

- [x] Review notes are stored through the **Manual Action Log**.
- [x] `note_only` notes appear in listing and Navigate but not the Review dialog.
- [x] `needs_review` notes appear as **Manual Review Items** and affect **Review State**.
- [x] Review notes do not create `blocked` state in the first implementation.
- [x] Row and range note behavior is covered where implemented.
- [x] Ctrl-click and Navigate behavior matches standard symbolic navigation interaction.
- [x] Manual comment behavior remains distinct.
- [x] PRD 016 issue links are accurate.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- PRD 016 behavior is covered by projection, route/CLI, source, and CDP tests.
- Review-note changes do not invalidate listing analysis caches because they do not change analysis metadata.

## Blocked by

- [016-001: Review Note Action Log Projection](016-001-review-note-action-log-projection.md)
- [016-002: Review Note Catalog API CLI](016-002-review-note-catalog-api-cli.md)
- [016-003: Review Note Web Surfaces](016-003-review-note-web-surfaces.md)
- [016-004: Range Targeted Review Notes](016-004-range-targeted-review-notes.md)
- [016-005: Manual Comment Review Note Boundary](016-005-manual-comment-review-note-boundary.md)
