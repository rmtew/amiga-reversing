Status: Implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Define and implement the project model needed to represent `Sample` as a
Classic Mac OS source project.

The project model must cover:

```text
source files
segments
routines
imports/exports
records/globals
resources
build recipe
generated Mac OS facts
```

Out of scope:
Do not import `Asm` CODE bytes in this issue, and do not build a full web UI.

Files likely touched:
- target/project metadata model
- Mac platform project/importer code
- tests under `tests/`
- docs if metadata schema is public

Acceptance criteria:
- `Sample` can be represented as a source-first project without requiring a
  built binary.
- Source segments and routines are navigable project entities.
- Resource declarations and build recipe metadata attach to the same project.
- Generated Mac facts can annotate project entities.
- The model explicitly distinguishes source project facts from `Asm` executable
  container facts.

Required tests:
- Source project creation smoke test for `Sample`.
- Metadata schema test for source files, segments, routines, resources, and
  build provenance.
- Regression test that source project import does not require ROMs, emulator,
  or built output.

Cleanup / deletion:
Delete after the source project model is implemented and accepted.

Notes for agents:
This issue makes the source view real. It should not be reduced to a text file
browser.

Implementation notes:
- Added `amiga_reversing.disasm.macos_source_project` to compose MPW source
  structure, Rez resources, build provenance, resource xrefs, and generated Mac
  OS facts into a source-first project model.
- The model records navigable source files, segments, routines, records,
  imports/exports, resource declarations, build products, object recipes, and
  Mac OS fact annotations.
- The project model explicitly requires no built binary, ROM, or emulator, and
  does not import executable `CODE` resources or map source `SEG` facts to
  observed `Asm` `CODE` resources.

Verification:
- `pytest tests/test_macos_source_project.py -q`
- `pytest tests/test_macos_source_project.py tests/test_macos_source_structure.py tests/test_macos_resource_model.py tests/test_macos_build_provenance.py tests/test_macos_runtime_generation.py -q`
