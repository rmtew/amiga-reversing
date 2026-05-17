Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Replace fallback-heavy persisted view state with locator-based preferences, URL state, and navigation history that repair stale projection hashes deterministically.

## Acceptance criteria

- [x] `ui_preferences.json` stores locator-compatible fields, projection hash, viewport anchor, and useful selection/focus locators.
- [x] URL/deep-link state uses precise locator-compatible fields and does not use row index, row text/code, legacy stable key, or legacy row id.
- [x] Back/forward navigation entries store locator plus viewport anchor and skip/drop unrecoverable entries.
- [x] Stale projection hash restore repairs by unique recovery identity and persists/replaces repaired locators when appropriate.
- [x] Failed repair falls back deterministically to entrypoint or first row.
- [x] `ui_preferences.py` sanitizer rejects legacy identity fields for new payloads and has explicit stale/repair behavior tests.

## Files likely touched

- `amiga_reversing/disasm/ui_preferences.py`
- `amiga_reversing/web/app.js`
- preference and navigation tests

## Blocked by

- docs/issues/028-009-refactor-app-js-listing-state-into-internal-models.md

## Required tests

- Preference sanitizer/load/save tests.
- Locator restore/repair tests through service and client model paths.

## Implementation

- `ui_preferences.py` now persists only locator-shaped listing state plus viewport anchor, selection locator, and focus locator; legacy row index/stable key/row code payloads sanitize to no listing location.
- `app.js` restores URL/preference/navigation locations through `ListingRowLocator`, repairs stale projection hashes from the rendered row, persists repaired locators, and falls back to entrypoint or the first rendered row.
- Navigation history entries now require recoverable targets and carry locator plus viewport anchor for back/forward recovery.
