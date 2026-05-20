# Proposal 016: Pandora Reversing Loop Hardening

Status: Complete.

Proposal 015 is the closed Pandora trial archive. This proposal owns the
remaining actionable tooling work that came out of that trial before another
Pandora reversing pass starts.

## Purpose

Harden the reversing loop surfaces that affected trust, evidence quality, and
review cost during the first Pandora pass.

This is not another broad Pandora mutation run. Pandora remains the repro and
validation target, but target mutations should happen only when a focused issue
needs them for proof.

## Carried-Forward Decisions

- Do not resume open-ended 015 iteration.
- Treat generic class/address labels in the tracked Pandora `.s` as historical
  trial artifacts, not cleanup blockers.
- Do not spend target-iteration budget on generic names such as
  `string_XXXXXXXX`; framework policy may handle that separately.
- Review Items are an evidence-backed work queue, not a count-reduction list.
- Exact round-trip remains mandatory for output-affecting changes.
- Full `src\precommit.bat` currently passes after the native C unit-test stack
  and diagnostic fix.

## Issues

1. `016-001`: dry-run/execute selected-action traceability.
2. `016-002`: manual-seed verifier output dedupe.
3. `016-003`: A5 hardware-base listing-state candidate report.
4. `016-004`: immediate runtime-reference detection.
5. `016-005`: evidence-led orphan-code candidate scoring.

## Recommended Order

Start with `016-001`, because every later autonomous action benefits from
stable selected-action reporting. Then do `016-002` if Review Items or manual
seeds are active. Choose either `016-003` for a hardware/custom-register pass
or `016-004` for a data/reference pass. Do `016-005` only after stronger
evidence sources exist.

## Source

Moved from remaining Proposal 015 deferred work:

- D008 -> `016-001`
- D011 -> `016-002`
- D007 -> `016-003`
- D006 -> `016-004`
- D002 -> `016-005`

No `docs\issues\015-*` files were present in the tree at creation time, so
there were no old issue files to delete.

## Implementation Notes

- 016-001 hardened `run-one` selection traceability. Dry-run now performs the
  same command-catalog availability resolution as execute, planner reports show
  selected-before-availability and selected-after-availability, availability
  checks include stale locator/catalog errors, and fallback selection drift is
  explicit. No Pandora target mutation was needed.
- 016-002 deduped manual-seed verifier payloads when command execution exposes
  the same seed through both `action` and `actions`. Exact duplicate seed
  payloads and duplicate removal ids are collapsed before reporting, while
  distinct seed payloads remain visible.
- 016-004 added a read-only `immediate-ref-report` for immediate constants that
  fall inside known source/runtime ranges. The first Pandora validation was too
  noisy because small immediates such as `#1` matched early source offsets, so
  the report now ignores small constants and remains report-only until a
  verifier-backed interpretation path exists. Pandora validation found 10
  candidates after filtering, including one runtime-address family candidate.
- 016-005 made orphan-code review scoring evidence-led. Review items now expose
  durable evidence, decode plausibility, false-positive checks, category, and
  score. Terminal-decode-only or false-positive-risk items stay report-only, and
  the planner requires evidence-led orphan-code scoring before selecting a
  code-seed action.
- 016-003 added a read-only `a5-hardware-report` for A5 `_custom` listing-state
  candidates. The report records definitions, uses, clobbers, save/restore
  boundaries, probable-candidate/unknown/conflicting status, and the verifier
  gate that keeps raw A5 displacement rendering blocked until real
  path/lifetime scope verification exists. Pandora validation reported 114 A5
  definitions, 525 uses, 98 clobbers, and 26 save/restore boundaries, with 324
  probable custom candidates and 201 still unknown.

## Final Verification

`cmd /c src\precommit.bat` passed after all 016 issue commits. The generated
`src/benchmark.json` timing-only diff from that run was discarded as pure churn.
