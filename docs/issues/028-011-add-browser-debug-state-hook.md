Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Add a test-only browser debug hook that returns a copied JSON-safe snapshot of current browser state for CDP semantic assertions and LLM-driven browser verification.

## Acceptance criteria

- [x] Browser debug state exposes project id, projection hash, request sequence, visible locators, selected/focused locators, and pending mutation id.
- [x] The hook returns copied JSON-safe data and does not expose live mutable internal objects.
- [x] CDP can compare browser debug state with server debug state for the same target/projection.
- [x] The hook is dev/test instrumentation and not used as a user workflow API.
- [x] Debug state names the client model layer that owns each field so failures do not require DOM scraping to diagnose.
- [x] Debug state is concise and stable enough for an LLM agent to verify initial state, selected/focused locators, pending mutation state, and projection match without reading live internals.
- [x] The browser hook has one explicit test/dev-only name, such as `window.__amigaDebugState()`, and returns a stable schema version.
- [x] The browser hook returns a deterministic machine-readable summary of project/projection/selection state; explanatory prose is not the test oracle.

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

## Implementation

- Added `window.__amigaDebugState()` returning schema version 1 with copied JSON-safe project, listing session, selection, and mutation-layer summaries.
- The snapshot includes top-level `project_id`, `listing_projection_hash`, request sequence, selected row key, visible locators, selected/focused locators, and pending mutation id.
- CDP coverage compares browser projection state with the server projection service debug state and verifies returned snapshots are copies.
