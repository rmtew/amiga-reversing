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

- [ ] Add, edit, and clear review-note actions append log entries rather than mutating prior history.
- [ ] Notes support `note_only` and `needs_review` tracking mode.
- [ ] Only open `needs_review` notes project into **Manual Review Items**.
- [ ] `note_only` notes do not affect **Review State**.
- [ ] Cleared notes no longer appear in current projected note surfaces.
- [ ] Optional title/body supports bookmark use.
- [ ] Unresolved note locations remain visible in projected navigation data.
- [ ] Backend tests cover log replay and projection.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [006-002: Catalog Action Execution](006-002-catalog-action-execution.md)
