# 016-004: Range Targeted Review Notes

## Parent

[PRD 016: Review Notes](../prd/016-review-notes.md)

## Related PRDs

- [PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Support **Review Notes** attached to selected row ranges once range **Listing Selection** context is available.

## Acceptance criteria

- [ ] Add review note accepts explicit range context from **Listing Selection**.
- [ ] Range notes appear as range-bound listing and Navigate annotations.
- [ ] Range notes project into range-bound **Manual Review Items** only when tracking mode is `needs_review`.
- [ ] Range note actions do not infer hidden rows outside the selected visible range.
- [ ] Web and backend tests cover row-range note creation and clearing.
- [ ] Row-level note behavior remains unchanged.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [016-003: Review Note Web Surfaces](016-003-review-note-web-surfaces.md)
- [014-003: Range Catalog Context Query](014-003-range-catalog-context-query.md)
