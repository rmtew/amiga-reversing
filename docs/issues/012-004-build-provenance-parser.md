Status: implemented
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

Implementation notes:
- Added `amiga_reversing.disasm.macos_build_provenance`, a source-level MPW
  recipe parser for variables, target dependencies, and `Asm`/`Link`/`SetFile`/
  `Rez` commands.
- The parser records `AOptions`, `AObjs`, object recipes, primary assembly
  source inputs, link object/library inputs, link output, type/creator,
  driver/tool/application program kind, SetFile metadata, and Rez append inputs.
- Source recipe provenance is explicitly separated from executable binary
  import provenance. Parsed build recipes do not claim byte-for-byte roundtrip
  support and do not map source recipes to observed `Asm` `CODE` resources.
- Real MPW make files decode dependency and continuation glyphs as U+0192 and
  U+2202 under MacRoman; tests cover those forms and PowerShell display
  equivalents.

Validation notes:
- Local ignored AExamples validation parsed `Sample.make` into one `Sample`
  product with Link/SetFile/Rez commands.
- Local ignored AExamples validation parsed `MakeFile` into `Count` and
  `Memory` products, including Count Rez/link/library inputs and Memory driver
  link metadata.

Verification:
- `uv run python -m pytest tests\test_macos_build_provenance.py -q`
- `uv run ruff check amiga_reversing\disasm\macos_build_provenance.py tests\test_macos_build_provenance.py`
- `uv run mypy amiga_reversing\disasm\macos_build_provenance.py`
