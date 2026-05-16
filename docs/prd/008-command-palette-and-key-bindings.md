# PRD 008: Command Palette and Default Key Bindings

## Status

Complete as of 2026-05-16.

## Purpose

Add a command palette that centralizes **Manual Action Catalog** entries, navigation commands, and **Target Tooling Commands** with default key bindings and visible key-binding badges.

## Scope

- Add an initial command palette bound to `p`.
- Open context-filtered by default from the current **Listing Selection**.
- Allow broadening from contextual actions to all currently valid target actions.
- Include non-manual target tooling commands such as reproduction profile selection and source export when applicable.
- Display assigned key bindings beside matching commands.
- Use an internal binding registry so defaults are centralized and future user rebinding is possible.

## Requirements

- Palette search filters by label, action id, target kind, symbol/equate/struct text, and command category.
- The initial view shows context-valid actions first.
- Backspace from an empty contextual search, or an equivalent visible toggle, broadens to all valid actions.
- Manual palette entries execute the same backend catalog actions used by review buttons and CLI/API callers.
- Navigation commands appear in the same global palette list, are filterable, and show key-binding badges even when they do not append to the **Manual Action Log**.
- **Target Tooling Commands** appear in the same global palette list, are filterable, and preserve their non-log persistence semantics.
- Default key bindings include command palette open, review open, navigate open, history back/forward, and core row navigation.
- The registry can represent unbound commands.

## Non-Goals

- User-defined key binding persistence or preferences UI.
- Chorded shortcut editor.
- Replacing existing Review and Navigate dialogs.
- Defining reproduction profile or source export semantics; covered by PRDs 018 and 021.
- Parameter entry UI for actions requiring values; covered by PRD 012.

## Verification

- Web source tests for palette rendering from catalog entries and key-binding badge display.
- CDP/e2e tests for opening the palette, contextual filtering, broadening to all valid actions, executing a log action, executing a transient navigation action, and displaying a target tooling command.
- Regression test that existing Review dialog actions still execute through catalog-backed behavior.

## Issues

- [008-001: Key Binding Registry](../issues/008-001-key-binding-registry.md)
- [008-002: Contextual Command Palette](../issues/008-002-contextual-command-palette.md)
- [008-003: Palette Global Mode](../issues/008-003-palette-global-mode.md)
- [008-004: Review Actions Through Catalog](../issues/008-004-review-actions-through-catalog.md)
- [008-005: PRD 008 Review and Tightening](../issues/008-005-prd-008-review-and-tightening.md)

## Open Questions

- Resolved: `p` is the default command palette binding.
- Resolved: palette entries use manual, navigation, and target-tooling
  categories from catalog metadata.

## Completion Notes

- Command palette opens context-filtered, broadens to global mode, displays
  key-binding badges, and executes manual, navigation, and target-tooling
  commands without changing Manual Action Log semantics for non-log commands.
- Focused PRD008 verification passed on 2026-05-16:
  `uv run python -m pytest tests\test_web_e2e_cdp.py tests\test_web_app_source.py tests\test_disasm_server.py -q -k "command_palette_opens_and_executes_catalog_command or command_palette_arrow_keys_select_entry or command_palette_offers_rename_for_selected_label_row or command_palette_and_selection_model or manual_action_catalog_returns_target_commands or manual_review_panel_filters_and_navigates or reproduction_profile_command_updates_summary or source_export_palette_uses_browser_save"`.

## Follow-On PRDs

- PRD 012 adds the **Command Parameter Editor** for schema-backed action parameters.
- PRD 015 keeps command palette state stable during immediate manual projection and refresh.
- PRD 017 adds palette-hosted parameter sessions and default edit-selected key bindings.
- PRD 018 adds reproduction profile target tooling commands.
- PRD 021 adds source export target tooling commands.
