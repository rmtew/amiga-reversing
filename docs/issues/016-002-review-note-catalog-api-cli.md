# 016-002: Review Note Catalog API CLI

## Parent

[PRD 016: Review Notes](../prd/016-review-notes.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Expose add, edit, and clear **Review Note** actions through the **Manual Action Catalog**, HTTP API, and CLI.

## Acceptance criteria

- [ ] Catalog entries exist for add, edit, and clear review note.
- [ ] Add and edit actions expose title, body, and tracking mode parameters.
- [ ] Row-level note actions are available without range selection.
- [ ] HTTP routes validate note parameters and target context.
- [ ] CLI can list and invoke note actions.
- [ ] CLI/API output distinguishes `note_only`, `needs_review`, cleared, and unresolved-location notes.
- [ ] Route and CLI tests cover add, edit, and clear flows.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [016-001: Review Note Action Log Projection](016-001-review-note-action-log-projection.md)
