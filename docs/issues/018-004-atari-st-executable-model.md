Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Capture cited Atari ST PRG/TOS/TTP/GEMDOS executable knowledge.

Acceptance criteria:
- Text/data/bss layout, relocation table, symbols, basepage/entrypoint, and
  trap ABI context are represented with citations.
- Existing Atari ST parser assumptions can be checked against the KB.
- Parser assertions are explicit where sources are indirect.

Blocked by:
- 018-001 for final schema shape.
