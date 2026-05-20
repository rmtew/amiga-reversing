Status: implemented
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

Implementation notes:
- Current Pandora dry run selected `representation.character`, not an
  RSSET/app-slot action.
- `inspect` returned no candidate work, and the dry-run ranked/selected work
  exposed no `target.rsset_region.*` or `rsset.binding.*` candidate.
- Existing RSSET command and verifier support is present, but there is no
  accepted source evidence for a new app-slot field, binding, alias, or typed
  region in the current target state.
- No generic A6 adjacency naming was performed.

Verification:
- `reversing_loop inspect --target ...`
- `reversing_loop run-one --target ... --dry-run`
