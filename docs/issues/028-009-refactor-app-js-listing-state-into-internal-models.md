Status: Blocked
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Refactor browser listing state inside the existing `app.js` file into explicit internal models that consume the locator and mutation contracts without making DOM state authoritative.

## Acceptance criteria

- [ ] `ListingSession`, `SelectionModel`, `PreferenceSync`, and `NavigationSession` or equivalent internal models own listing window, selection, preferences, and navigation transitions.
- [ ] Selection and focus store locators, not DOM rows, row text, or durable row indexes.
- [ ] Request sequence rejects stale browser responses without replacing newer projection state.
- [ ] Command context sends locators and element ids, not full row snapshots as authority.
- [ ] Existing user behavior for selection, first-open entrypoint selection, virtual scrolling, and navigation remains covered.
- [ ] Tests stop reaching into broad `state.listingRows`, `state.listingSelection`, or `state.virtualListing` when a model/debug-state assertion is available.

## Files likely touched

- `amiga_reversing/web/app.js`
- `tests/test_web_app_source.py`
- focused CDP tests for listing behavior

## Blocked by

- docs/issues/028-006-delete-target-ui-edits-and-unify-mutation-execution.md

## Required tests

- Client source/model checks for locator selection and stale response rejection.
- Existing selection, first-open, virtual scrolling, and navigation CDP/source tests.
