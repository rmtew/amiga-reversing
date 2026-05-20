Status: Open
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Parse MPW build recipes from `Sample.make` and `MakeFile` into provenance
metadata that explains how source, object, resource, file metadata, and linked
libraries contribute to outputs.

Out of scope:
Do not execute MPW, emulate MPW Shell, parse MPW object files, or produce a
byte-for-byte rebuild.

Files likely touched:
- new build recipe parser under `src/scripts/` or reusable platform module
- tests under `tests/`
- docs if output schema needs documenting

Acceptance criteria:
- `Sample.make` parses `AOptions`, `AObjs`, `Link`, `SetFile`, and `Rez` lines.
- `MakeFile` parses `Count` and `Memory` recipes.
- Parsed metadata records:
  - Asm source inputs and `.a.o` object outputs
  - Link object/library inputs
  - Link output file
  - output type/creator or program kind where specified
  - SetFile type/creator attributes
  - Rez append inputs
- Metadata distinguishes source-view provenance from executable `Asm` binary
  import provenance.

Required tests:
- `Sample.make` parser test.
- `MakeFile` `Count` parser test.
- `MakeFile` `Memory` parser test.
- Schema/drift test for generated build provenance.

Cleanup / deletion:
Delete after build provenance parsing is implemented and tested.

Notes for agents:
The value here is explanatory provenance for rendered source and future
round-trip research. It is not a commitment to rebuilding MPW outputs.
