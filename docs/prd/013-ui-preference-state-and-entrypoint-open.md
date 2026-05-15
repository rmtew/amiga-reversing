# PRD 013: UI Preference State and Entrypoint Open

## Status

Complete as of 2026-05-16.

## Purpose

Persist project-local **UI Preference State** for listing location and use the source entrypoint as the first-open fallback when no explicit or persisted location exists.

## Dependencies

- PRD 007: Listing Selection and Keyboard Model.
- PRD 009: Symbol, Equate, and Struct Navigation.
- PRD 018: Reproduction Profiles and Policy Summary.
- PRD 021: Source Export Workflow.

## Scope

- Add project-local storage for non-domain UI workflow state.
- Restore last listing selection and scroll anchor when opening a project target.
- Select and center the source entrypoint row on first open when no URL/navigation anchor or stored UI location exists.
- Keep UI preferences out of the **Manual Action Log**.

## Requirements

- **UI Preference State** may store selected row, scroll anchor, last target location, key-binding overrides, render profile choice, reproduction profile view choice, and last source-export assembler choice.
- Target-affecting **Reproduction Policy** remains target configuration, not UI preference state.
- First-open logic reads the target `source_binary.json` entrypoint or equivalent source descriptor.
- If a matching listing row is visible or fetchable, the UI selects it and centers it in the virtual listing viewport.
- Explicit URL anchors, navigation commands, and restored UI preference locations take precedence over entrypoint fallback.
- Missing or stale preference state falls back safely to entrypoint selection.
- Browser storage may cache UI state, but project-local preference state is the source of truth.
- Preference writes do not append **Manual Action Log** entries and do not affect review state.

## Non-Goals

- Storing reverse-engineering facts.
- Replacing target metadata or source descriptors.
- Full preference UI for every stored field.
- Persisting target-affecting reproduction policy.

## Verification

- Web source tests for precedence: explicit anchor, restored preference, then entrypoint fallback.
- CDP test for first-open entrypoint row selection and centered viewport.
- Tests proving preference writes do not touch the **Manual Action Log**.
- Regression test for stale row identity falling back without breaking listing load.

Verified:

- `uv run pytest tests\test_ui_preferences.py tests\test_disasm_server.py -q -k "ui_preferences"`
- `uv run pytest tests\test_web_app_source.py -q`
- `uv run pytest tests\test_web_e2e_cdp.py -q -k first_open_selects_source_entrypoint`

## Issues

- [013-001: UI Preference State Storage](../issues/013-001-ui-preference-state-storage.md)
- [013-002: Restore Listing Location](../issues/013-002-restore-listing-location.md)
- [013-003: First Open Entrypoint Selection](../issues/013-003-first-open-entrypoint-selection.md)
- [013-004: Location Precedence Rules](../issues/013-004-location-precedence-rules.md)
- [013-005: PRD 013 Review and Tightening](../issues/013-005-prd-013-review-and-tightening.md)

## Decisions

- Project-local UI preference state is stored as `ui_preferences.json` in the binary target directory.
