# 012-003: Keyboard Focus For Parameter Editing

## Parent

[PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)
- [PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Make palette-hosted editable parameter controls capture text-editing keys while preserving palette and listing keyboard behavior outside the editor.

## Acceptance criteria

- [ ] Arrow keys and text-editing keys inside parameter fields do not move **Listing Selection**.
- [ ] Enter submits only when the field state is valid for submission.
- [ ] Escape cancels the parameter editor and returns predictably to the command palette.
- [ ] Focus returns predictably to the command palette after submit/cancel.
- [ ] Web tests cover focus isolation for parameter controls.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [012-001: Text Parameter Editor Rename Label](012-001-text-parameter-editor-rename-label.md)
