# 008-003: Palette Global Mode

## Parent

[PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## Labels

done

## What to build

Let the command palette broaden from contextual actions to all currently valid target actions, with useful category filtering.

## Acceptance criteria

- [x] Palette can switch from contextual mode to all-valid-actions mode.
- [x] Backspace from empty contextual search or an equivalent visible control performs the broadening.
- [x] Global mode still hides invalid actions for the current project/target.
- [x] Category filtering includes navigation and manual-editing commands.
- [x] Tests cover broadening and category filtering.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [008-002: Contextual Command Palette](008-002-contextual-command-palette.md)
