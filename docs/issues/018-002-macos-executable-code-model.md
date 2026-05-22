Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Build the cited Mac OS executable/CODE model needed by Proposal 012.

Acceptance criteria:
- Local MD/docs/KB are mined for Segment Loader, resource fork, CODE resources,
  A5 world, jump table, relocation/fixup, entrypoint, and MPW Link output facts.
- Facts are recorded in the executable-format KB with citations.
- The first scope focuses on MPW `Asm` / application-style CODE resources,
  while leaving desk accessories, INITs, cdevs, and drivers as later archetypes
  unless required facts are shared.
- Mac facts distinguish file entrypoint, segment entrypoint, runtime
  entrypoint, exported entrypoint, callback entrypoint, and analysis seed
  entrypoint.
- `producer` / `variant` records capture MPW Link/Rez scope rather than
  assuming all Classic Mac OS toolchains produce identical executable layout.
- Observed fixture bytes can support candidate facts and parser assertions but
  cannot by themselves validate general CODE entry rules.
- Existing CODE entry heuristics are downgraded to candidate evidence unless
  backed by cited rules.
- The current `movea.l (a7)+,a0` boundary is either validated by cited
  Segment Loader/MPW output facts or replaced by a documented rule.
- Proposal 012 names this issue as its blocking dependency.

Blocked by:
- 018-001 for final schema shape.
