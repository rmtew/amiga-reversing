Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

Scope:
Use evidence-led Review Items as a focused work queue for real Pandora
source-quality blockers.

Problem:
Review Items are useful only when they resolve underlying source issues, not
when they are cleared mechanically. 016 made orphan-code scoring evidence-led;
the next pass should consume Review Items through durable ids and verifiers.

Required work:
- Inspect current Review Items from the same source surfaced by the Review
  dialog.
- Select items with durable ids, evidence fingerprints, source-quality value,
  command availability, verifier coverage, and round-trip availability.
- For orphan code, seed only evidence-led candidates without false-positive
  risk.
- For data/range/conflict items, use structured commands that fix the source
  issue rather than placeholder comments.
- Record skipped items when they expose missing support or ambiguous evidence.

Acceptance:
- At least one Review Item is resolved through a verified structured fact, or
  the proposal records the precise blocker that prevents safe resolution.
- Review-count reduction is not counted as progress unless rendered source or
  durable metadata improves.
- Output-affecting actions pass exact round-trip.

Blocked by:
- 017-001.

Implementation notes:
- Current `reversing_loop inspect` for the Pandora sub-target reports zero
  Review Items and zero candidate work.
- No structured source fact was applied, because there is no durable Review
  Item id/evidence fingerprint to resolve.
- Review-count reduction is not counted as progress; this issue closes as a
  no-op until new evidence-led Review Items appear.

Verification:
- `reversing_loop inspect --target ...`
