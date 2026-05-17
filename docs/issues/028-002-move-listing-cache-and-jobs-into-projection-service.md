Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Move listing artifact cache ownership, artifact lifecycle, listing job lifecycle, projection hashing, and server debug state behind a `ListingProjectionService` instance. Server routes should become thin adapters over the service.

## Acceptance criteria

- [x] Server listing routes call a `ListingProjectionService` instance for windows, locator context, cache state, job state, and debug state.
- [x] The service owns artifact cache keys, cached artifact disposal, reset/close hooks, listing job start/reuse/cancel, and artifact-ready event state.
- [x] `projection_hash` is computed lazily from explicit projected-row inputs and remains separate from `effective_metadata_hash`.
- [x] Tests can instantiate isolated service instances without patching private server `_PROJECT_*` globals.
- [x] Existing listing, navigation, review, and listing-job API tests pass through the new service without compatibility wrappers around the old globals.
- [x] Tests that currently seed `_PROJECT_C_LISTING_ARTIFACT_CACHE`, `_PROJECT_LISTING_CACHE_KEY`, `_PROJECT_LISTING_PRESENTATION_DIRTY`, or `_PROJECT_ANALYSIS_REVIEW_ITEMS_CACHE` move to public service helpers for touched behavior.

## Implementation notes

- Removed the server-owned `_PROJECT_*` listing cache globals. `ListingProjectionService` now owns artifact/cache-key state, presentation-dirty state, review-item cache state, cache reset/close, cached artifact replacement, and debug snapshots.
- Moved listing job start/reuse/cancel and artifact-ready event payload construction into `ListingProjectionService`; `server.py` now supplies only generic async-job storage, thread startup, and C artifact build callbacks.
- Kept `effective_metadata_hash` inside the server-side cache-key builder, but route row payloads ask the service for the projection hash from the current projected-row cache key.
- Updated browser helpers to seed listing state through service helpers. The client normalizes fetched `row_key` to its existing internal `stable_key` fields after the wire payload is received, without re-exposing legacy row identity names from `/listing`.

## Files likely touched

- `amiga_reversing/disasm/listing_projection.py`
- `amiga_reversing/disasm/server.py`
- `tests/test_disasm_server.py`
- `tests/test_web_e2e_cdp.py`

## Blocked by

- docs/issues/028-001-extract-listing-row-locator-projection-tracer.md

## Required tests

- Listing, navigation, review, and listing-job route tests.
- Focused service cache/job lifecycle tests.
