Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Finish the proposal implementation by auditing historical bugs, retired terminology, and stale implementation names so the codebase no longer preserves obsolete UI state paths.

## Acceptance criteria

- [x] Known refresh/restart/cache UI bugs touched during implementation have named regression fixtures attached to the subsystem that owns the state contract.
- [x] `CONTEXT.md` and relevant docs use the new command catalog, authoritative mutation result, and locator-based selection terminology.
- [x] Final audit searches cover retired names such as `target_ui_edits`, `stable_key`, `row_id`, row-code identity, `manual-action-catalog`, presentation-dirty concepts, `_PROJECT_LISTING_*`, and row index in mutation/preference contexts.
- [x] Remaining production references to retired names are removed or explicitly justified as private implementation details that do not leak into the web-state contract.
- [x] `src/precommit.bat` and relevant focused API/source/CDP tests pass before the proposal work is considered complete.
- [x] The audit distinguishes allowed viewport/debug uses of `row_index` from forbidden mutation/preference/identity uses.
- [x] The audit records any deliberately retained internal names with owner, reason, and follow-up issue if removal is not in scope.

## Audit

Searches covered `target_ui_edits`, `stable_key`, `row_id`, row-code identity,
`manual-action-catalog`, presentation-dirty state, `_PROJECT_LISTING_*`, and
`row_index` mutation/preference contexts.

Retired route terminology no longer appears in production or CLI code. The only
source reference to `manual-action-catalog` is the negative web source test that
asserts it is absent from `app.js`; historical docs retain the removed route
only to describe the migration.

The only production `target_ui_edits.json` reference is
`OBSOLETE_TARGET_UI_EDITS_FILE_NAME` in `target_local_state.py`. Owner:
target-local-state cleanup. Reason: import/reimport/profile-set cleanup must
delete obsolete local state instead of preserving or reading it. No follow-up is
needed unless the cleanup list is retired entirely.

`stable_key` and `row_id` remain in private C/listing internals, legacy manual
action payload matching, reproduction diagnostics, and test fixtures. Owner:
listing projection and manual action payload builders. Reason: these are input
compatibility and diagnostics fields; `ListingProjectionService` normalizes web
listing payloads to `row_key`/`ListingRowLocator` and strips `stable_key` and
`row_id` before browser consumption. No web-state contract depends on them.

`row_code` remains only in test fixture helpers and historical audit wording.
It is not used as durable web identity.

`row_index` remains valid for viewport windows, virtualized rendering, corpus
snippets, reproduction diagnostics, and tests that verify stale row-index
preferences are rejected. It is no longer accepted as mutation/preference,
URL/deep-link, or Manual Action Log subject identity.

`presentation_dirty` remains an internal `ListingProjectionService` invalidation
set and debug-state field. Owner: listing projection service. Reason: it marks
cached presentation artifacts stale without exposing a browser contract beyond
test/debug inspection.

No production `_PROJECT_LISTING_*` globals remain. Historical proposal and
issue docs mention them only as removed state.

## Checks

```text
uv run ruff check amiga_reversing/tools/manual_actions.py tests/test_manual_actions_cli.py
uv run python -m pytest tests/test_manual_actions_cli.py tests/test_api_workflow_harness.py tests/test_web_app_source.py -q
M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests/test_web_e2e_cdp.py -q -k "llm_operable_command_smoke or first_open_selects_source_entrypoint"
cmd /c src/precommit.bat
```

## Files likely touched

- `CONTEXT.md`
- relevant proposal/issue docs
- regression fixtures created during implementation
- source and tests containing retired names

## Blocked by

- docs/issues/028-001-extract-listing-row-locator-projection-tracer.md
- docs/issues/028-002-move-listing-cache-and-jobs-into-projection-service.md
- docs/issues/028-003-inventory-workflow-contracts-against-real-locators.md
- docs/issues/028-004-replace-command-palette-catalog-routes-with-command-routes.md
- docs/issues/028-005-tighten-reimport-cleanup-for-target-local-state.md
- docs/issues/028-006-delete-target-ui-edits-and-unify-mutation-execution.md
- docs/issues/028-007-add-api-workflow-harness.md
- docs/issues/028-008-add-durability-matrix-runner.md
- docs/issues/028-009-refactor-app-js-listing-state-into-internal-models.md
- docs/issues/028-010-persist-and-repair-locator-view-navigation-state.md
- docs/issues/028-011-add-browser-debug-state-hook.md
- docs/issues/028-012-convert-cdp-tests-to-semantic-durability-assertions.md

## Required tests

- `src/precommit.bat`
- Focused API workflow tests changed by implementation.
- Focused source/model tests changed by implementation.
- Focused CDP durability tests changed by implementation.
