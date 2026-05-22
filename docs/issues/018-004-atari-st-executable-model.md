Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Capture cited Atari ST PRG/TOS/TTP/GEMDOS executable knowledge.

Acceptance criteria:
- Text/data/bss layout, relocation table, symbols, basepage/entrypoint, and
  trap ABI context are represented with citations.
- Existing Atari ST parser assumptions can be checked against the KB.
- Parser assertions are explicit where sources are indirect.
- Existing parser assumptions may be adopted incrementally, but known gaps must
  be visible as backfill-required/deferred records.
- Producer/toolchain variants are represented when they affect symbols,
  relocation streams, or runtime entry assumptions.

Blocked by:
- 018-001 for final schema shape.
