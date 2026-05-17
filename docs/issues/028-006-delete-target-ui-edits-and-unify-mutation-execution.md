Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Delete `target_ui_edits` as a durable UI mutation source and route supported browser mutations through command execution and Manual Action Log mutation results.

## Acceptance criteria

- [x] `/target-edits` and `target_ui_edits.py` are removed after supported flows are replaced.
- [x] Inline comment edits, label/comment/representation/review workflows, and command palette mutation flows use the same mutation result shape.
- [x] Mutation responses return durable action id, manual log count/head hash, projection hash, effective metadata hash, affected locators, and optional authoritative refreshed window.
- [x] Browser workflows do not bypass locator/context validation through direct append routes.
- [x] No production workflow reads `target_ui_edits.json`.
- [x] `effective_metadata.py`, reproduction stamping, profile-set copying, source tests, and server route tests no longer depend on `target_ui_edits`.
- [x] Local listing effects in `app.js` are deleted or narrowed to presentation-only pending/flash state followed by authoritative projection refresh.

## Files likely touched

- `amiga_reversing/disasm/target_ui_edits.py`
- `amiga_reversing/disasm/effective_metadata.py`
- `amiga_reversing/disasm/listing_context.py`
- `amiga_reversing/disasm/manual_action_catalog.py`
- `amiga_reversing/disasm/reproduction.py`
- `amiga_reversing/disasm/server.py`
- `amiga_reversing/web/app.js`
- tests covering target edits, manual actions, source checks, and reproduction stamps

## Blocked by

- docs/issues/028-002-move-listing-cache-and-jobs-into-projection-service.md
- docs/issues/028-003-inventory-workflow-contracts-against-real-locators.md
- docs/issues/028-004-replace-command-palette-catalog-routes-with-command-routes.md
- docs/issues/028-005-tighten-reimport-cleanup-for-target-local-state.md

## Required tests

- Manual label/comment/representation/review mutation route tests.
- Effective metadata/reproduction stamp tests proving `target_ui_edits` is gone.
- Client source tests proving `/target-edits` and local durable effects are gone.
