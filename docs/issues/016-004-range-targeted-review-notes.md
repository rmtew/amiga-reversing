# 016-004: Range Targeted Review Notes

## Parent

[PRD 016: Review Notes](../prd/016-review-notes.md)

## Related PRDs

- [PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Type

AFK

## Labels

done

## What to build

Support **Review Notes** attached to selected row ranges once range **Listing Selection** context is available.

## Acceptance criteria

- [x] Add review note accepts explicit range context from **Listing Selection**.
- [x] Range notes appear as range-bound listing and Navigate annotations.
- [x] Range notes project into range-bound **Manual Review Items** only when tracking mode is `needs_review`.
- [x] Range note actions do not infer hidden rows outside the selected visible range.
- [x] Web and backend tests cover row-range note creation and clearing.
- [x] Row-level note behavior remains unchanged.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- `range.review_note.add` consumes explicit selected rows and records row indexes.
- Range notes use selected visible rows only; no hidden-row inference is added.

## Blocked by

- [016-003: Review Note Web Surfaces](016-003-review-note-web-surfaces.md)
- [014-003: Range Catalog Context Query](014-003-range-catalog-context-query.md)
