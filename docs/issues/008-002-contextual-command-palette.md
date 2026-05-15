# 008-002: Contextual Command Palette

## Parent

[PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## What to build

Add the initial command palette opened by `p`, context-filtered from the current **Listing Selection**, and capable of executing catalog actions.

## Acceptance criteria

- [ ] `p` opens the command palette when focus is not in an editable control.
- [ ] Initial palette contents are filtered by current **Listing Selection**.
- [ ] Search matches label, action id, target kind, and relevant symbol/equate/struct text.
- [ ] Executing a log action uses the catalog action execution path.
- [ ] Executing a transient action performs the expected UI/navigation behavior.
- [ ] CDP/e2e tests cover opening, filtering, and executing one log action.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [008-001: Key Binding Registry](008-001-key-binding-registry.md)
- [007-002: Selection Keyboard Navigation](007-002-selection-keyboard-navigation.md)
