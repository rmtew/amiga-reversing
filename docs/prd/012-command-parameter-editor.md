# PRD 012: Command Parameter Editor

## Status

Complete as of 2026-05-16.

## Purpose

Replace browser-native prompts with a basic palette-hosted **Command Parameter Editor** that renders **Manual Action Catalog** parameter schemas and submits catalog-backed actions without web-only command behavior.

## Dependencies

- PRD 006: Manual Action Catalog, API, and CLI.
- PRD 008: Command Palette and Default Key Bindings.

## Scope

- Render action parameters from catalog `parameter_schema`.
- Support command palette execution for actions that require parameters, starting with label rename.
- Preserve keyboard flow: open palette, choose command, edit value, Enter submits, Escape cancels.
- Keep execution catalog-backed and server-validated.
- Keep this as the minimal prompt-replacement path that PRD 017 can later generalize.

## Requirements

- `window.prompt` is not used for command palette action execution.
- Parameter controls are derived from schema fields, required flags, defaults, and current selected context.
- Validation errors are shown in the editor without closing the palette.
- Submitting an action uses the same catalog execution endpoint as Review dialog, CLI, and API callers.
- The editor appears inside the command palette; inline listing hosts and row-anchored overlays are PRD 017 scope.
- Editable controls do not leak keyboard events into listing navigation or palette navigation.
- Cancel leaves **Listing Selection**, scroll position, and catalog state unchanged.

## Non-Goals

- A custom form system for non-catalog web features.
- User-defined command schemas.
- One-off rename dialogs outside the catalog path.
- Inline listing editors, palette session back stacks, choice grids, filtered choosers, and rich interaction metadata; covered by PRD 017.

## Verification

- Web source tests for schema rendering, required-field validation, Enter submit, and Escape cancel.
- Web source test proving catalog action execution no longer calls `window.prompt`.
- CDP test for renaming a label through the in-app parameter editor.
- Route/backend tests continue to validate parameters before appending **Manual Action Log** entries.

Verified:

- `uv run pytest tests\test_web_app_source.py -q`
- `uv run pytest tests\test_web_e2e_cdp.py -q -k command_palette_offers_rename_for_selected_label_row`

## Issues

- [012-001: Text Parameter Editor Rename Label](../issues/012-001-text-parameter-editor-rename-label.md)
- [012-002: Parameter Validation Feedback](../issues/012-002-parameter-validation-feedback.md)
- [012-003: Keyboard Focus For Parameter Editing](../issues/012-003-keyboard-focus-for-parameter-editing.md)
- [012-004: Schema Field Coverage](../issues/012-004-schema-field-coverage.md)
- [012-005: PRD 012 Review and Tightening](../issues/012-005-prd-012-review-and-tightening.md)

## Follow-On PRDs

- PRD 017 generalizes the basic command parameter editor into reusable inline and palette-hosted parameter sessions.
