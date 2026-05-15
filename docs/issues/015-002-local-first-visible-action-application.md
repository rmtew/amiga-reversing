# 015-002: Local-First Visible Action Application

## Parent

[PRD 015: Local-First Manual Edit Application](../prd/015-local-first-manual-edit-application.md)

## Related PRDs

- [PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Apply known visible effects from the manual edit application contract in the current listing and review UI immediately after durable action append, without special-casing label rename as the only local-first path.

## Acceptance criteria

- [ ] The UI applies known local effects from action results through one generic path.
- [ ] Label rename is covered as the first concrete behavior through that generic path.
- [ ] Failed append leaves visible rows unchanged.
- [ ] The viewport is not covered by a listing or reanalysis loading overlay for known local effects.
- [ ] CDP coverage proves label rename updates visibly through the generic local-first path.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [015-001: Manual Edit Application Contract](015-001-manual-edit-application-contract.md)
- [012-001: Text Parameter Editor Rename Label](012-001-text-parameter-editor-rename-label.md)
