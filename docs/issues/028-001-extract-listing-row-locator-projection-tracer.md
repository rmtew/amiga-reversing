Status: Ready
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Introduce the first working `ListingProjectionService` skeleton and `ListingRowLocator` path through it. A listing request should return rows with the new locator contract, backed by authoritative row identity from the C listing payload, and no web-facing dual contract for `stable_key` or `row_id`.

This is a tracer slice, not a compatibility wrapper. It should establish the service interface that later owns cache/job lifecycle, even if this issue only routes the minimal listing-window path through it.

## Acceptance criteria

- [ ] `amiga_reversing/disasm/listing_projection.py` exists and owns `ListingRowLocator` creation, locator validation, locator recovery, and projected listing-window normalization for the tracer path.
- [ ] Listing rows exposed to the web state contract include `target_id`, `projection_hash`, `row_key`, section/start/end offsets, kind, and optional storage/runtime addresses.
- [ ] The C listing payload emits the authoritative row identity needed to construct `row_key`; Python does not paper over missing identity with row text or row indexes.
- [ ] Web-facing listing/debug/preference payloads do not expose both old identity names and `row_key`.
- [ ] Locator resolution tests cover exact match, stale hash with unique recovery, target mismatch, missing locator, and ambiguous locator.
- [ ] Generated listing JSON consumed by the web UI uses `row_key`/`ListingRowLocator` fields, not `stable_key` or `row_id`.
- [ ] Existing route code may still own most cache/job lifecycle in this tracer, but new locator-aware code does not patch or extend those globals directly.

## Files likely touched

- `amiga_reversing/disasm/listing_projection.py`
- `amiga_reversing/disasm/api.py`
- `amiga_reversing/disasm/c_backend.py`
- C listing payload emitter under `src/`
- `amiga_reversing/disasm/server.py`
- listing row fixtures/tests

## Blocked by

None - can start immediately.

## Required tests

- Focused `ListingProjectionService` locator tests.
- Focused listing route tests proving web-facing rows expose only the new locator contract.
