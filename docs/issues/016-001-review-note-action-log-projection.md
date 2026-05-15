# 016-001: Review Note Action Log Projection

## Parent

[PRD 016: Review Notes](../prd/016-review-notes.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Add **Review Note** records to the **Manual Action Log** and project only review-tracking notes into **Manual Review Items**.

## Acceptance criteria

- [x] Add, edit, and clear review-note actions append log entries rather than mutating prior history.
- [x] Notes support `note_only` and `needs_review` tracking mode.
- [x] Only open `needs_review` notes project into **Manual Review Items**.
- [x] `note_only` notes do not affect **Review State**.
- [x] Cleared notes no longer appear in current projected note surfaces.
- [x] Optional title/body supports bookmark use.
- [x] Unresolved note locations remain visible in projected navigation data.
- [x] Backend tests cover log replay and projection.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Review notes replay into `manual_state.review_notes`.
- `needs_review` notes project into non-blocking `review_note` Manual Review Items.
- `note_only` and cleared notes stay out of Review State and Review dialog projection.

## Blocked by

- [006-002: Catalog Action Execution](006-002-catalog-action-execution.md)
