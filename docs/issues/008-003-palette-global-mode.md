# 008-003: Palette Global Mode

## Parent

[PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## What to build

Let the command palette broaden from contextual actions to all currently valid target actions, with useful category filtering.

## Acceptance criteria

- [ ] Palette can switch from contextual mode to all-valid-actions mode.
- [ ] Backspace from empty contextual search or an equivalent visible control performs the broadening.
- [ ] Global mode still hides invalid actions for the current project/target.
- [ ] Category filtering includes navigation and manual-editing commands.
- [ ] Tests cover broadening and category filtering.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [008-002: Contextual Command Palette](008-002-contextual-command-palette.md)
