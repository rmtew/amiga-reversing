Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Build the cited Mac OS executable/CODE model needed by Proposal 012.

Acceptance criteria:
- Local MD/docs/KB are mined for Segment Loader, resource fork, CODE resources,
  A5 world, jump table, relocation/fixup, entrypoint, and MPW Link output facts.
- Facts are recorded in the executable-format KB with citations.
- Existing CODE entry heuristics are downgraded to candidate evidence unless
  backed by cited rules.
- Proposal 012 names this issue as its blocking dependency.

Blocked by:
- 018-001 for final schema shape.
