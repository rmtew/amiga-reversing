Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Define the shared schema for platform executable/container format knowledge.

Acceptance criteria:
- Records can describe signatures, containers, sections, relocations, symbols,
  BSS, entrypoints, loader metadata, runtime conventions, citations, and parser
  assertions.
- Schema supports Amiga, Atari ST, and Mac OS without platform-specific hacks.
- Parser assertions require reason, citation context, and standard
  interpretation.
- Tests validate representative records.

Blocked by:
None.
