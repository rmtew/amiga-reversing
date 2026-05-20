Status: Open
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
