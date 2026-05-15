# PRD 008: Command Palette and Default Key Bindings

## Purpose

Add a command palette that exposes **Manual Action Catalog** entries for the current **Listing Selection**, with default key bindings and visible key-binding badges.

## Scope

- Add an initial command palette bound to `p`.
- Open context-filtered by default from the current **Listing Selection**.
- Allow broadening from contextual actions to all currently valid target actions.
- Display assigned key bindings beside matching commands.
- Use an internal binding registry so defaults are centralized and future user rebinding is possible.

## Requirements

- Palette search filters by label, action id, target kind, symbol/equate/struct text, and command category.
- The initial view shows context-valid actions first.
- Backspace from an empty contextual search, or an equivalent visible toggle, broadens to all valid actions.
- Palette entries execute the same backend catalog actions used by review buttons and CLI/API callers.
- Navigation commands appear in the same global palette list, are filterable, and show key-binding badges even when they do not append to the **Manual Action Log**.
- Default key bindings include command palette open, review open, navigate open, history back/forward, and core row navigation.
- The registry can represent unbound commands.

## Non-Goals

- User-defined key binding persistence or preferences UI.
- Chorded shortcut editor.
- Replacing existing Review and Navigate dialogs.

## Verification

- Web source tests for palette rendering from catalog entries and key-binding badge display.
- CDP/e2e tests for opening the palette, contextual filtering, broadening to all valid actions, executing a log action, and executing a transient navigation action.
- Regression test that existing Review dialog actions still execute through catalog-backed behavior.

## Issues

- [008-001: Key Binding Registry](../issues/008-001-key-binding-registry.md)
- [008-002: Contextual Command Palette](../issues/008-002-contextual-command-palette.md)
- [008-003: Palette Global Mode](../issues/008-003-palette-global-mode.md)
- [008-004: Review Actions Through Catalog](../issues/008-004-review-actions-through-catalog.md)
- [008-005: PRD 008 Review and Tightening](../issues/008-005-prd-008-review-and-tightening.md)

## Open Questions

- Whether `p` remains the final default after broader keyboard review.
- Exact category names used in palette filtering.
