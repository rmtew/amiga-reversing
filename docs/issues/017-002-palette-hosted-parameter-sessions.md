# 017-002: Palette Hosted Parameter Sessions

## Parent

[PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Related PRDs

- [PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)
- [PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)

## Type

AFK

## Labels

done

## What to build

Render a selected catalog action's **Parameter Session** inside the command palette, preserving command-list state behind an Escape-driven back stack.

## Acceptance criteria

- [x] Selecting a parameterized palette action opens its session inside the palette.
- [x] Escape returns from the session to the previous palette search/selection state.
- [x] Escape from the restored command list closes the palette.
- [x] Enter commits through the catalog execution path.
- [x] Server validation errors keep the session open.
- [x] Web/CDP tests cover submit, cancel, back-stack, and validation-error behavior.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Palette-hosted sessions now render from the shared parameter-session components used by inline sessions.
- Existing command-parameter validation and back-stack behavior remain the palette host contract.

## Blocked by

- [017-001: Interaction Schema Contract](017-001-interaction-schema-contract.md)
- [012-001: Text Parameter Editor Rename Label](012-001-text-parameter-editor-rename-label.md)
