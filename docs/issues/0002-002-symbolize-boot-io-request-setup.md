# 0002-002 Symbolize Boot IO Request Setup

## Parent

[PRD 0002: Bootblock Runtime Address Model](../prd/0002-bootblock-runtime-address-model.md)

## What to build

Carry boot entry IO request type knowledge far enough through simple local save/load patterns that `DoIO` setup renders with IO field names instead of raw offsets. A bootblock that saves the entry `A1` pointer to local storage, reloads it, writes command, offset, length, and data fields, then calls `DoIO` should produce readable IO request field references.

This slice is complete when the Epic bootblock's `DoIO` setup is symbolized without target-specific special cases.

## Acceptance criteria

- [x] Entry `A1` boot IO request seed is available at boot entry for local-offset bootblocks.
- [x] Type propagation survives a proven local storage save and reload of the boot IO request pointer.
- [x] IO request field writes render with symbolic field names for command, offset, length, and data destination.
- [x] Exec `DoIO` calls remain named through the existing platform call path.
- [x] Ambiguous or overwritten local storage does not propagate stale IO request type facts.
- [x] A focused fixture covers save, reload, IO field writes, and `DoIO`.
- [x] The Epic bootblock no longer shows the relevant IO request setup as raw `$001C/$0024/$0028/$002C(a1)` offsets.
- [x] Relevant Python and C backend tests pass.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Implementation notes

- Added policy register seeds to typed render-flow state so boot entry `A1:IO` propagates through existing typed storage save/reload handling.
- Added `policy_seed` typed provenance to facts JSON.
- Added `test_real_dll_bootblock_policy_io_seed_symbolizes_saved_request_setup`, covering the happy path, exact reassembly, and an overwritten-storage stale-type guard.

## Verification

- `cmd /c src\build.bat`
- `uv run python -m pytest tests\test_c_backend.py -q -k "bootblock_policy_io_seed_symbolizes_saved_request_setup or epic_bootblock_does_not_materialize_load_address_org or facts_v2_propagates_opendevice_instance_to_io_calls"`
- Epic bootblock generated source reassembled exact: 1024/1024 bytes, with `IO_OFFSET(a1)`, `IO_LENGTH(a1)`, `IO_DATA(a1)`, `IO_COMMAND(a1)`, and `_LVODoIO(a6)`.
- `$env:M68K_RUN_BRAVE_CDP='1'; uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- [0002-001 Stop Bootblock Load Address From Emitting ORG](0002-001-stop-bootblock-load-org.md)
