# 016-002: Review Note Catalog API CLI

## Parent

[PRD 016: Review Notes](../prd/016-review-notes.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)

## Type

AFK

## Labels

done

## What to build

Expose add, edit, and clear **Review Note** actions through the **Manual Action Catalog**, HTTP API, and CLI.

## Acceptance criteria

- [x] Catalog entries exist for add, edit, and clear review note.
- [x] Add and edit actions expose title, body, and tracking mode parameters.
- [x] Row-level note actions are available without range selection.
- [x] HTTP routes validate note parameters and target context.
- [x] CLI can list and invoke note actions.
- [x] CLI/API output distinguishes `note_only`, `needs_review`, cleared, and unresolved-location notes.
- [x] Route and CLI tests cover add, edit, and clear flows.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Row and range catalog actions expose schema-backed add note parameters.
- Review-note review items expose edit and clear actions through the same catalog/API/CLI path.
- CLI range contexts are supported with `--row-indexes`.

## Blocked by

- [016-001: Review Note Action Log Projection](016-001-review-note-action-log-projection.md)
