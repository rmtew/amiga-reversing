Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Prevent heuristic-only executable parsing from being marked implemented.

Acceptance criteria:
- Tests distinguish candidate heuristics from accepted parser facts.
- Accepted platform parsing rules require citations or parser assertions.
- Candidate facts may drive reports and candidate ranges, but not accepted
  parser output.
- Proposal/issue closeout templates require unresolved executable-format gaps
  to be deferred explicitly.
- The Mac `movea.l (a7)+,a0` entry heuristic is documented as candidate
  evidence until 018-002 validates or replaces it.
- Renderer output must not label heuristic-only ranges as confirmed code or
  accepted entrypoints.

Blocked by:
- 018-001.
