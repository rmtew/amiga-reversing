Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-003 blocker

Scope:
Upgrade A5 hardware-base reporting from linear listing-state candidates to
CFG-backed path/lifetime proof.

Problem:
`a5-hardware-report` can identify probable `_custom` candidates and linear
scopes such as `linear_listing_between_a5_writes`, but that is not accepted
path/lifetime evidence. Hardware register rendering is still blocked because
no proof shows A5 remains `_custom` on every relevant path to a selected use.

Required work:
- Build or extend a read-only report that follows control flow for a selected
  A5 definition/use family.
- Account for A5 definitions, clobbers, save/restore boundaries, calls/returns,
  fallthrough, branches, and conflicting paths.
- Produce a durable path/lifetime scope identity suitable for later accepted
  evidence.
- Classify selected uses as accepted custom-base, unknown, or conflicting.
- Keep hardware register rendering blocked unless accepted path/lifetime
  evidence and verifier support are present.

Acceptance:
- The selected Pandora A5 use at `s0:000004A6` is either proven for a concrete
  path/lifetime scope or remains blocked with explicit conflicting/unknown
  paths.
- No hardware register rendering executes from linear listing-state evidence.
- The report output is stable enough for a later verifier to consume by
  source evidence id and path/lifetime scope.

Blocked by:
- 017-003.

Result:
- `a5-hardware-report` now includes a read-only
  `cfg_path_lifetime_report` with stable `source_evidence_id` and
  `path_lifetime_scope` payloads for conservative straight-line CFG slices.
- Straight-line `_custom` definition-to-use paths are classified as
  `accepted_custom_base`; branches, calls, save/restore boundaries, missing
  definitions, and out-of-range displacements remain unknown/conflicting with
  explicit blockers.
- Pandora validation classified the selected `s0:000004A6` use as
  `accepted_custom_base` with source evidence
  `a5-custom-cfg:h0:00000498->000004A6:op1:d0096` and scope kind
  `straight_line_cfg_between_definition_and_use`.
- Hardware register rendering remains blocked: the report is read-only and
  `rendering_allowed=false`.
