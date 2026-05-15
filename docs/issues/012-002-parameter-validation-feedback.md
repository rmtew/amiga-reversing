# 012-002: Parameter Validation Feedback

## Parent

[PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Keep the **Command Parameter Editor** open when catalog parameter validation fails and show actionable field-level feedback without appending a **Manual Action Log** entry.

## Acceptance criteria

- [ ] Required-field failures are shown in the editor.
- [ ] Backend validation errors are surfaced without closing the palette.
- [ ] Failed validation does not append a **Manual Action Log** entry.
- [ ] Correcting the value and resubmitting succeeds through the same catalog path.
- [ ] Tests cover required text parameter failure and recovery.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [012-001: Text Parameter Editor Rename Label](012-001-text-parameter-editor-rename-label.md)
