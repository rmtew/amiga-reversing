Status: Blocked
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Finish the proposal implementation by auditing historical bugs, retired terminology, and stale implementation names so the codebase no longer preserves obsolete UI state paths.

## Acceptance criteria

- [ ] Known refresh/restart/cache UI bugs touched during implementation have named regression fixtures attached to the subsystem that owns the state contract.
- [ ] `CONTEXT.md` and relevant docs use the new command catalog, authoritative mutation result, and locator-based selection terminology.
- [ ] Final audit searches cover retired names such as `target_ui_edits`, `stable_key`, `row_id`, row-code identity, `manual-action-catalog`, presentation-dirty concepts, `_PROJECT_LISTING_*`, and row index in mutation/preference contexts.
- [ ] Remaining production references to retired names are removed or explicitly justified as private implementation details that do not leak into the web-state contract.
- [ ] `src/precommit.bat` and relevant focused API/source/CDP tests pass before the proposal work is considered complete.
- [ ] The audit distinguishes allowed viewport/debug uses of `row_index` from forbidden mutation/preference/identity uses.
- [ ] The audit records any deliberately retained internal names with owner, reason, and follow-up issue if removal is not in scope.

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
