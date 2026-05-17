# 009-003 Add Indexed Normal Locator Resolution

Status: Done
Source proposal: `docs/proposals/009-workflow-profiling-and-system-encapsulation.md`
Created: 2026-05-17

## What to build

Make normal row and element command locator resolution avoid materializing the
whole listing.

The common manual-edit path should resolve the selected `ListingRowLocator`
through `ListingProjectionService` locality. Range commands may still use a
bounded range resolver when their interface makes that cost explicit.

## Scope

- Add a projection-service-owned locator resolution path that can find a normal
  row/element subject without `window_payload(start=0, count=total_rows)`.
- Preserve stale locator recovery using section/start/end/kind identity.
- Keep route-level command execution using `ListingRowLocator` as authority.
- Add tests that fail if normal locator resolution calls the all-row path.

## Out of scope

- Full range-selection optimization.
- Browser UI changes.
- Manual Action Log semantics.
- Source Rendering or Round-Trip Verification refactors.

## Files likely touched

- `amiga_reversing/disasm/listing_projection.py`
- `amiga_reversing/disasm/server.py`
- `tests/test_listing_projection.py`
- `tests/test_disasm_server.py`

## Acceptance criteria

- Normal row command locator resolution does not call
  `artifact.window_payload(start=0, count=total_rows)`.
- Normal element command locator resolution uses the same indexed row path.
- Stale locator recovery still rejects ambiguous or missing recovery.
- Range command behavior remains explicit and covered.
- Manual command tests still pass through the normal command route.

## Required tests

```powershell
uv run python -m pytest tests\test_listing_projection.py tests\test_disasm_server.py -q
```

## Cleanup / deletion

- Delete or narrow `_all_listing_rows()` use for normal row/element command
  execution.
- Keep any remaining all-row path named and scoped to the commands that truly
  need it.

## Notes for agents

- This issue should improve locality, not introduce a second locator identity.
  `ListingRowLocator` remains the contract.

## Implementation notes

- `ListingProjectionService` now owns a row-key and recovery-identity index
  populated from normalized listing windows.
- Normal row/element command locator resolution uses the indexed/artifact-local
  resolver instead of `_all_listing_rows()`.
- Range command resolution remains explicitly on the all-row path through
  `_resolve_command_range_locator()`.
- Focused tests prove normal row and element command resolution do not call the
  all-row `window_payload(start=0, count=total_rows)` path.
- Focused verification passed:
  `uv run python -m pytest tests\test_listing_projection.py tests\test_disasm_server.py -q`.
- Lint passed:
  `uv run ruff check amiga_reversing\disasm\listing_projection.py amiga_reversing\disasm\server.py tests\test_listing_projection.py tests\test_disasm_server.py`.
