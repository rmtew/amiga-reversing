Status: Implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Define and implement focused render smoke tests proving that Mac source and
platform facts are displayed usefully for porting/reference work.

Required render targets:

```text
Sample.a -> Initialize
SampleMisc.a -> GoGetRect
MemorySrc.a -> PBHGetVInfoSync call site
Count -> tool/runtime summary
```

Out of scope:
Do not require full source rendering, full trap coverage, or byte-for-byte
round-trip.

Files likely touched:
- source/project renderer
- Mac platform annotation code
- generated Mac OS metadata consumers
- tests under `tests/`

Acceptance criteria:
- `Initialize` render shows file, segment, routine, imports, selected globals,
  stack frame facts, resource-related calls, and Mac API annotations.
- `GoGetRect` render shows `_GetResource('RECT', id)`, handle use, Rect field
  copy, and resource xrefs for `rStopRect`/`rGoRect`.
- `Memory` render shows `_PBHGetVInfoSync`, A0 parameter block, relevant
  `HVolumeParam` fields, and computed free-space intent.
- `Count` render shows MPW tool kind, `cmdo` resource, linked runtime/library
  provenance, and runtime calls.

Required tests:
- Snapshot or structured render tests for all four targets.
- Test that annotations come from generated/structured Mac facts.
- Test that missing facts are shown as unsupported/unknown, not guessed.

Cleanup / deletion:
Delete after smoke tests are implemented and stable.

Notes for agents:
These tests define "useful source view." Keep expected output compact and
structural, not prose-heavy.

Implementation notes:
- Added `amiga_reversing.disasm.macos_source_render` to render compact
  structured routine/product views from the source-first Mac project model.
- Smoke tests cover `Sample.a` `Initialize`, `SampleMisc.a` `GoGetRect`,
  `MemorySrc.a` `_PBHGetVInfoSync`, and `Count` tool/runtime/resource
  provenance.
- Rendered facts come from parsed source/resources/build metadata plus
  generated/structured Mac OS facts supplied to the source project model.
- Unsupported areas remain explicit: executable `CODE` import and byte-for-byte
  MPW Link/Rez roundtrip are not guessed.

Verification:
- `pytest tests/test_macos_source_render.py -q`
- `pytest tests/test_macos_source_project.py tests/test_macos_source_render.py tests/test_macos_source_structure.py tests/test_macos_resource_model.py tests/test_macos_build_provenance.py tests/test_macos_runtime_generation.py -q`
