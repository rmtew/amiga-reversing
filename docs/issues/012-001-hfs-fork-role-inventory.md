Status: implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Classify MPW-GM HFS files and forks into roles that the Mac platform importer
and UI can use without flattening everything into a generic binary.

This issue covers both starter tracks:

- `Sample` source view: `TEXT/MPS ` data forks are source text, while small
  `MPSR` resource forks are editor metadata.
- `Asm` binary view: `MPST/MPS ` resource fork contains executable `CODE`
  resources, while the data fork is data/string payload.

Out of scope:
Do not parse MPW object format, perform CODE disassembly, or build the web UI.

Files likely touched:
- `src/scripts/extract_classic_hfs.py`
- new reusable Mac/HFS inventory module, if promoted from script
- `ext/macos_tools/mpw_gm/`
- tests under `tests/`

Acceptance criteria:
- Inventory records each selected HFS item path, CNID, type, creator, data fork
  size, resource fork size, and inferred fork role.
- `AExamples` files are classified as source data forks plus editor metadata
  resource forks.
- `MPW/Tools/Asm` is classified as executable resource fork plus data/string
  data fork.
- Role decisions are deterministic and cite local evidence from
  `docs/macos-initial-analysis-research.md`.
- Unknown file/fork roles are represented explicitly, not guessed.

Required tests:
- AExamples fork role check.
- `Asm` fork role check.
- Inventory drift check against `ext/macos_includes/mpw_gm/inventory.json`.

Cleanup / deletion:
Delete after fork role support is implemented and durable notes are promoted
into Proposal 012 or runtime docs.

Notes for agents:
Keep role classification separate from parsing. A source fork role does not
mean the parser can fully understand MPW assembly yet.

Implementation notes:
- Added `amiga_reversing.disasm.macos_fork_roles` as a deterministic enrichment
  layer over the committed MPW-GM inventory.
- Added `--fork-roles` to `src/scripts/extract_classic_hfs.py`; the default
  inventory output stays unchanged.
- Focused roles implemented now: `source_text`, `editor_metadata`,
  `executable_resource_fork`, `data_string_payload`, `object_payload`,
  `unknown`, and `absent`.

Review notes:
- Role evidence cites `docs/macos-initial-analysis-research.md` plus committed
  inventory metadata; `Asm` CODE count is attached only when the inspected
  resource summary is supplied.
- Unknown nonzero forks remain explicit `unknown`; no broad TEXT/MPS guessing.
- Full-tree mypy currently reports unrelated existing failures. The new module
  passes direct mypy.

Verification:
- `uv run python -m pytest tests\test_mac_fork_roles.py tests\test_mac_resource_fork.py -q`
- `uv run ruff check amiga_reversing\disasm\macos_fork_roles.py src\scripts\extract_classic_hfs.py tests\test_mac_fork_roles.py`
- `uv run mypy amiga_reversing\disasm\macos_fork_roles.py`
