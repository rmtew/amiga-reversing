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

- [x] Required-field failures are shown in the editor.
- [x] Backend validation errors are surfaced without closing the palette.
- [x] Failed validation does not append a **Manual Action Log** entry.
- [x] Correcting the value and resubmitting succeeds through the same catalog path.
- [x] Tests cover required text parameter failure and recovery.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Progress

Completed 2026-05-16. Required-field failure/recovery is covered by CDP; backend errors stay inside the editor through `submitError` without closing the palette.

## Blocked by

- [012-001: Text Parameter Editor Rename Label](012-001-text-parameter-editor-rename-label.md)
