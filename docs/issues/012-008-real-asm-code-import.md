Status: implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Import `MPW-GM/MPW/Tools/Asm` as the real Classic Mac OS executable/container
fixture.

This covers the binary side of Proposal 012.

Out of scope:
Do not infer source mapping to `Sample`, complete Segment Loader relocation,
or implement byte-for-byte round-trip.

Files likely touched:
- resource fork parser/importer
- target/project import code
- disassembly/listing code
- `ext/macos_tools/mpw_gm/`
- tests under `tests/`

Acceptance criteria:
- Importer recognizes `MPW/Tools/Asm` as Classic Mac OS `MPST/MPS ` input.
- Data fork is represented as data/string payload.
- Resource fork is parsed and preserved as platform structure.
- `CODE 0` is represented as jump-table/application metadata.
- `CODE 1 Main` is importable/listable as m68k code bytes.
- Other named `CODE` resources are visible in inventory.
- Unsupported areas are explicit: relocation/fixups, complete Segment Loader
  behavior, source mapping, and round-trip.

Required tests:
- `Asm` HFS item recognition test.
- `Asm` data-fork role test.
- `Asm` resource-fork/CODE inventory drift test.
- `CODE 0` metadata parser test.
- `CODE 1 Main` listing smoke test.

Cleanup / deletion:
Delete after real `Asm` import is implemented and covered.

Notes for agents:
Keep committed binary content policy in mind. Prefer committed metadata and
hashes over committing extracted executable forks unless explicitly approved.

Implementation notes:
- Added reusable read-only HFS catalog/fork access for the MPW image and a
  reusable Classic Mac OS resource-fork parser.
- Refactored `inspect_mac_resource_fork.py` into a thin CLI over the reusable
  parser.
- Added an MPW `Asm` container importer that reads the committed MacBinary
  NDIF image through the committed `ndif2raw` provider, extracts the real HFS
  file forks in temp space, preserves `MPST`/`MPS ` metadata, classifies the
  data fork as `data_string_payload`, parses the resource fork, represents
  `CODE 0` as jump-table/application metadata, exposes all 28 `CODE`
  resources, and selects `CODE 1 Main` as the starter code segment.
- `CODE 1 Main` now has a code-byte listing preview and a smoke test through
  the existing raw m68k listing backend, but relocation/fixups, complete
  Segment Loader behavior, source mapping, and byte-for-byte round-trip remain
  explicitly unsupported.

Verification:
- `uv run python -m pytest tests\test_macos_asm_container.py -q`
- `uv run python -m pytest tests\test_macos_asm_container.py tests\test_mac_resource_fork.py tests\test_mac_fork_roles.py tests\test_macos_resource_model.py tests\test_macos_build_provenance.py tests\test_macos_source_structure.py tests\test_macos_source_project.py tests\test_macos_source_render.py tests\test_macos_runtime_generation.py -q`
- `uv run ruff check amiga_reversing\disasm\macos_hfs.py amiga_reversing\disasm\macos_resource_fork.py amiga_reversing\disasm\macos_asm_container.py src\scripts\inspect_mac_resource_fork.py tests\test_macos_asm_container.py`
- `uv run mypy amiga_reversing\disasm\macos_hfs.py amiga_reversing\disasm\macos_resource_fork.py amiga_reversing\disasm\macos_asm_container.py tests\test_macos_asm_container.py`
