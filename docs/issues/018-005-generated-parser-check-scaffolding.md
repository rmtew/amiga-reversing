Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Generate or validate parser/check scaffolding from executable-format KB records.

Acceptance criteria:
- C parser output can be checked against KB-defined regions and metadata.
- Standard code/data/bss/reloc/symbol enumeration is tested per platform.
- Generated checks fail when parser output contradicts cited platform facts.
- Checks are blocking for new or explicitly `kb_backed` parser slices.
- Legacy Amiga/Atari areas can start with optional reports until the relevant
  parser area is migrated.
- Generated runtime/check outputs use `src/generated/platform_executable_formats.c`
  and `.h` unless an implementation review chooses a better existing local
  generator pattern.

Blocked by:
- 018-001.
- At least one platform record from 018-002, 018-003, or 018-004.
