# Proposal 016: Pandora Reversing Loop Hardening

Status: proposed follow-up to closed Proposal 015.

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
3. `016-003`: A5 hardware-base lifetime provenance.
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
