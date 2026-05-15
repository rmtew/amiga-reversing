# 008-001: Key Binding Registry

## Parent

[PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## What to build

Add a centralized default key-binding registry for catalog commands, including unbound commands and visible binding metadata.

## Acceptance criteria

- [ ] Registry exposes default bindings for palette, review, navigate, history, and row navigation commands.
- [ ] Registry can represent unbound commands.
- [ ] Catalog/palette data can show binding badges from the registry.
- [ ] Existing keyboard behavior is routed through the registry where practical.
- [ ] Web tests cover bound and unbound command display metadata.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [006-003: Target and Listing Action Contexts](006-003-target-and-listing-action-contexts.md)
- [007-001: Listing Row Selection](007-001-listing-row-selection.md)
