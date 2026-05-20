Status: blocked
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
- `src/` has no C-backed HFS catalog/file/fork parser, Classic Mac resource
  fork parser, CODE inventory/extraction path, or Mac project metadata serializer
  equivalent to the Amiga/Atari platform backends.
- Do not promote the Python helper path as the accepted durable implementation.
  The next viable 012 slice is a C platform-file backend extension that owns HFS
  file lookup, fork/resource metadata, CODE 0/nonzero CODE inventory, and
  selected CODE byte extraction.
