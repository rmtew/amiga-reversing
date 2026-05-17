Status: Blocked
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Add a test-only browser debug hook that returns a copied JSON-safe snapshot of current browser state for CDP semantic assertions and LLM-driven browser verification.

## Acceptance criteria

- [ ] Browser debug state exposes project id, projection hash, request sequence, visible locators, selected/focused locators, and pending mutation id.
- [ ] The hook returns copied JSON-safe data and does not expose live mutable internal objects.
- [ ] CDP can compare browser debug state with server debug state for the same target/projection.
- [ ] The hook is dev/test instrumentation and not used as a user workflow API.
- [ ] Debug state names the client model layer that owns each field so failures do not require DOM scraping to diagnose.
- [ ] Debug state is concise and stable enough for an LLM agent to verify initial state, selected/focused locators, pending mutation state, and projection match without reading live internals.
- [ ] The browser hook has one explicit test/dev-only name, such as `window.__amigaDebugState()`, and returns a stable schema version.
- [ ] The browser hook returns a deterministic machine-readable summary of project/projection/selection state; explanatory prose is not the test oracle.

## Files likely touched

- `amiga_reversing/web/app.js`
- CDP helper/tests

## Blocked by

- docs/issues/028-009-refactor-app-js-listing-state-into-internal-models.md
- docs/issues/028-010-persist-and-repair-locator-view-navigation-state.md

## Required tests

- Source/debug-state tests proving copied JSON-safe output.
- CDP smoke assertion comparing browser and server debug state.
- Deterministic browser-debug assertion covering schema version, copied JSON-safe values, server/browser projection match, visible locators, and selected/focused locators without DOM scraping.
