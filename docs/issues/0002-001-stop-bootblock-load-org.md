# 0002-001 Stop Bootblock Load Address From Emitting ORG

## Parent

[PRD 0002: Bootblock Runtime Address Model](../prd/0002-bootblock-runtime-address-model.md)

## What to build

Make local-offset bootblock targets render as local source bytes, not as an automatic `$70000` source-level runtime view. Bootblock metadata should still seed boot entry analysis, boot header structured data, and entry register context. Runtime-absolute raw targets must keep their existing loaded-image ORG behavior.

This slice is complete when the Epic bootblock no longer emits `ORG $70000`, while its boot entry and boot header remain readable and the rebuilt bytes remain exact.

## Acceptance criteria

- [x] A local-offset bootblock with load metadata does not create a full-source materialized runtime range.
- [x] Rendered local-offset bootblock source does not emit `ORG $70000` solely from bootblock metadata.
- [x] Boot magic, checksum, root block, boot entry label, and boot entry register context still render from bootblock metadata.
- [x] Runtime-absolute raw targets still emit their single loaded-image ORG and runtime entrypoint.
- [x] The Epic bootblock regression test asserts no false `$70000` ORG.
- [x] Round-trip reproduction remains exact for affected regenerated source.
- [x] Relevant Python and C backend tests pass.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Implementation evidence

- Bootblock metadata now seeds only local bootblock structure and boot entry facts; it no longer adds a full-source `$70000` runtime range or runtime entrypoint.
- Covered by focused C backend regressions for the Epic bootblock, local-offset bootblock metadata, local-offset raw binaries, and runtime-absolute raw binaries.
- Verified Epic bootblock rendered source has no `ORG $70000`, keeps `boot_entry` and boot magic, and reassembles byte-exact against the original 1024-byte bootblock.
- Verified with `uv run python -m pytest tests\test_c_backend.py -q -k "epic_bootblock_does_not_materialize_load_address_org or facts_v2_bootblock_metadata_recovers_entry_context_and_pc_data_label or runtime_absolute_raw_binary_materializes_runtime_load_range or local_offset_raw_binary_does_not_invent_runtime_load_range"`.
- Full `tests\test_c_backend.py` result: 142 passed; 16 existing corpus-fixture availability failures for missing checked-in targets.
- Verified with `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- Verified with `cmd /c src\precommit.bat`.

## Blocked by

None - can start immediately
