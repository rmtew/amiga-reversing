Status: in progress; C resource-fork/CODE, HFS metadata, fork materialization, C-backed Python summary, and selected CODE byte extraction slices implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Make Classic Mac OS platform parsing/import a first-class extension of the core
C-backed platform framework.

Problem:
The current Mac starter slice proves behavior with Python helpers for HFS,
resource forks, CODE inventory, and project payload assembly. That is useful
for research, but it is not complete platform support. In this codebase Python
should generally wrap the C API, prepare fixtures, generate reports, and provide
editing/workflow layers. Durable import/listing/runtime behavior belongs in C
when Amiga or Atari ST already implement that class of behavior in C.

This is not a request to preserve backwards compatibility with the prototype
Python path. Replace it where the core framework has the right abstraction. If
the framework does not have the right abstraction, extend the framework or raise
the blocker; do not keep a Mac-only workaround.

Required C-backed areas:

```text
HFS catalog/file/fork access
Classic Mac resource fork parsing
CODE 0 metadata and nonzero CODE segment inventory
selected CODE segment byte extraction for listing
Finder type/creator and fork-role platform metadata
Mac project metadata serialized for API/web consumers
```

Out of scope:
Do not implement full Segment Loader relocation/fixups or byte-for-byte MPW
roundtrip in this issue.

Acceptance criteria:
- C code owns the durable parser/import path for the required areas above.
- The implementation uses shared platform abstractions where possible and
  extends them cleanly where Mac exposes missing concepts.
- Python Mac helpers call, wrap, generate fixtures for, or report on that C path
  instead of being the only implementation.
- No duplicate Mac-only metadata model or compatibility shim remains as the
  accepted durable path.
- Existing Python tests either exercise the C-backed path or are clearly
  labelled as parser research/unit fixtures.
- The C path preserves the same metadata currently proven by the Python starter:
  HFS path/CNID, Finder type/creator, fork sizes, resource types, `CODE 0`,
  nonzero `CODE` resources, and selected `CODE 1 Main` bytes.
- Amiga and Atari ST platform tests continue to pass.

Required tests:
- C unit tests for Mac HFS/resource/CODE parsing.
- Python integration test proving the Python wrapper uses the C path.
- Drift test against committed MPW `Asm` metadata when the real fixture is
  available.
- `cmd /c src\precommit.bat`.

Blocker recorded:
- 012-015 removed handcrafted Mac runtime metadata from the render path, but the
  durable Mac container/import path is still Python-only research code.
- `src/` now has a C-backed Classic Mac resource fork parser for resource-map
  inventory, `CODE 0` metadata, nonzero `CODE` segment metadata, and selected
  resource payload bounds.
- `src/` now has a read-only C-backed HFS catalog metadata parser for MDB
  volume fields, catalog directory/file records, Finder type/creator,
  data/resource fork sizes, first-extent fork bounds, catalog-extent fork
  materialization, and CNID-backed path reconstruction.
- `platform_file_lib` now exposes a C-backed Mac HFS/CODE summary API that
  finds an HFS file path, materializes catalog extents, parses its resource
  fork, inventories `CODE` resources, and reports selected `CODE 1` bytes.
- `platform_file_lib` also exposes selected nonzero `CODE` resource byte
  extraction for listing/import consumers; `CODE 0` stays metadata-only.
- `amiga_reversing.disasm.c_backend` now wraps that C API, with Python
  integration coverage using a synthetic HFS/resource-fork fixture.
- `src/` still has no C-backed overflow-extent fork materializer, real MPW
  fixture drift gate through this API, Mac project metadata serializer, or
  normal API/web project payload equivalent to the Amiga/Atari platform
  backends.
- Do not promote the Python helper path as the accepted durable implementation.
  The next viable 012 slice is a C platform-file backend extension that owns HFS
  file lookup and Finder/fork metadata, then routes resource/CODE inspection
  through the new C resource parser.

Implemented slice:
- Added `src/platform_macos_resource.c` and
  `src/platform_macos_resource.h` as the durable C parser surface for Classic
  Mac resource forks.
- Added native C unit coverage for synthetic `CODE 0` jump-table metadata,
  nonzero `CODE` segment metadata, selected payload bounds, and malformed
  payload bounds rejection.
- Added `src/platform_macos_hfs.c` and `src/platform_macos_hfs.h` for the
  first HFS C path slice: MDB/catalog parsing, file type/creator metadata,
  fork size/extent metadata, and CNID-derived file paths.
- Added native C unit coverage for synthetic HFS catalog/file/fork metadata and
  missing MDB signature rejection.
- Added catalog-extent fork materialization in C, with native tests for a
  resource fork spread across multiple catalog extents and explicit overflow
  extent-needed reporting.
- Added `platform_file_macos_hfs_code_summary_json_alloc` as the first exported
  C platform-file Mac container summary API, plus a Python wrapper test proving
  Python consumes that C path for HFS file metadata, Finder type/creator, fork
  sizes, resource/CODE inventory, and selected `CODE 1` bytes.
- Added `platform_file_macos_hfs_code_resource_bytes_alloc` for actual selected
  nonzero `CODE` segment byte extraction, with the same Python integration test
  asserting `CODE 1` bytes come from the C path.
- Routed the existing MPW `Asm` nonzero `CODE` byte extraction helper through
  the C-backed byte API so the listing smoke path no longer depends on the
  Python resource parser for selected segment bytes. `CODE 0` remains metadata
  handled by the existing parser path.
