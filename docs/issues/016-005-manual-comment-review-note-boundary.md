# 016-005: Manual Comment Review Note Boundary

## Parent

[PRD 016: Review Notes](../prd/016-review-notes.md)

## Related PRDs

- [PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Keep **Manual Comment** and **Review Note** behavior distinct across action eligibility, projection, listing display, and review surfaces.

## Acceptance criteria

- [x] Manual comments remain source/rendering annotation.
- [x] Review notes remain review workflow state.
- [x] `note_only` Review Notes do not appear as source comments or **Manual Review Items**.
- [x] `needs_review` Review Notes appear as **Manual Review Items** without becoming source comments.
- [x] Catalog entries and labels make the distinction clear.
- [x] Tests prove notes and comments project into distinct surfaces.
- [x] Existing manual comment behavior does not regress.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Review notes are separate `review_notes` projection state, not manual comments.
- Listing note badges are rendered from review-note annotations, not source comments.

## Blocked by

- [016-003: Review Note Web Surfaces](016-003-review-note-web-surfaces.md)
