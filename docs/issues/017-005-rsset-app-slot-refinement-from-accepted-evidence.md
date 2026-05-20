Status: proposed
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md

Scope:
Continue Pandora RSSET/app-slot improvement only where accepted evidence
supports a specific binding, field, alias, or refinement.

Problem:
Proposal 015 improved many A6 app-state fields, but remaining raw A6 operands
should not be named by adjacency or generic class/address policy. 016 improved
planner/report trust but did not make every RSSET report actionable.

Required work:
- Inspect remaining raw or weak A6-relative operands through listing,
  provenance, RSSET reports, xrefs, and command catalog availability.
- Prefer same-flow/same-displacement groups only when base evidence and
  path/lifetime scope are accepted.
- Bind/refine fields, aliases, arrays, or typed regions only with verifier
  coverage and cleanup ownership.
- Avoid generic names that do not add Pandora semantics.
- Record gaps where `rsset.binding.report` remains report-only because base
  evidence, source family, or ownership is missing.

Acceptance:
- At least one app-slot/RSSET source improvement is verified, or the proposal
  records a precise blocker for the best remaining candidate.
- Generated descendants have owning action identity and cleanup semantics.
- Exact round-trip passes for output-affecting changes.

Blocked by:
- 017-001.
