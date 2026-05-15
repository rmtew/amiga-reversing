# 017-003: Inline Text Editors For Labels And Comments

## Parent

[PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Related PRDs

- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)
- [PRD 015: Local-First Manual Edit Application](../prd/015-local-first-manual-edit-application.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Render inline text editors for selected **Manual Label** and **Manual Comment** targets, submitting catalog actions and applying results through local-first manual edit application.

Review Note text editing is integrated by PRD 016 after note actions exist; this issue only builds the reusable label/comment text host.

## Acceptance criteria

- [ ] Selected label can become an inline text editor with the current label prefilled.
- [ ] Selected comment/comment slot can become an inline text editor with current text prefilled when available.
- [ ] Enter commits through the catalog action; Escape cancels and restores rendered text.
- [ ] Inline editing does not mutate rendered source text directly.
- [ ] Local validation state and server validation errors are visible in the editor.
- [ ] CDP tests cover inline label edit and inline comment edit.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [017-001: Interaction Schema Contract](017-001-interaction-schema-contract.md)
- [015-002: Local-First Visible Action Application](015-002-local-first-visible-action-application.md)
