Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Capture cited Amiga executable/object/library/resident/device/HUNK knowledge.

Acceptance criteria:
- HUNK, LoadSeg, resident, library/device, code/data/bss, relocations, symbols,
  and entry conventions are represented with citations.
- Sources are old/out-of-print platform manuals/books, compatible modern
  sources, project-observed facts, or parser assertions. Modern incompatible
  sources are not KB inputs.
- Version scope is recorded when a source describes a specific OS/toolchain
  version.
- Existing Amiga parser assumptions can be checked against the KB.
- Existing parser assumptions may be adopted incrementally, but known gaps must
  be visible as backfill-required/deferred records.

Blocked by:
- 018-001 for final schema shape.
