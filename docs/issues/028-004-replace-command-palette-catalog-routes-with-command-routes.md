Status: Blocked
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Replace manual-action-catalog web routes with command-oriented routes. Command context should be locator-based, action availability should be effect-classified, and row snapshots should no longer be accepted as authoritative context.

## Acceptance criteria

- [ ] Web/API command routes expose command availability and command execution with the shared web-state contract marker.
- [ ] Row commands send a `ListingRowLocator`, range commands send ordered locators, and element commands send locator plus `element_id`.
- [ ] Command availability is cached only by projection hash, selected locators, element id, and context kind.
- [ ] Mutation commands delegate to Manual Action Log payload construction; navigation, clipboard, and inspection commands are effect-classified separately.
- [ ] Stale/missing/ambiguous/non-mutable locator failures return typed contract errors.
- [ ] Command context resolution goes through `ListingProjectionService`; command routes do not accept row snapshots or row indexes as authoritative context.
- [ ] Legacy `/manual-action-catalog` callers are updated or deleted in the same slice; no compatibility bridge remains after callers move.
- [ ] Command entries are machine-operable: stable command id, effect, target context, required parameter descriptions, and typed result/error shape are exposed clearly enough for CDP and LLM-driven verification to choose and execute commands without DOM scraping.

## Files likely touched

- `amiga_reversing/disasm/server.py`
- `amiga_reversing/disasm/listing_context.py`
- `amiga_reversing/disasm/manual_action_catalog.py`
- `amiga_reversing/web/app.js`
- command/catalog route tests

## Blocked by

- docs/issues/028-001-extract-listing-row-locator-projection-tracer.md
- docs/issues/028-002-move-listing-cache-and-jobs-into-projection-service.md

## Required tests

- Command availability and execution route tests for row, range, element, and target contexts.
- Client source tests proving command context sends locators, not row snapshots.
- Command catalog response test proving machine-operable command metadata is present.
