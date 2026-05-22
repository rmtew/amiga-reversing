Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md
Promoted from: 017-018 follow-up mutation

Scope:
Record the remaining render-safe Pandora A5 hardware references from accepted
path/lifetime evidence.

Problem:
After 017-018, the A5 report still exposed command-backed non-zero displacement
hardware references with durable path/lifetime evidence, command support,
verifier support, and exact round-trip gates. These were the same focused A5
family and did not need new tooling or policy.

Required work:
- Execute the remaining unrecorded command-backed A5 candidates.
- Stop on the first verifier failure or report-only/tooling-needed candidate.
- Verify manual-log, provenance, semantic-reload, rendered-source, and exact
  round-trip layers for every executed mutation.

Acceptance:
- All remaining command-backed A5 candidates pass the full verifier stack.
- `a5-hardware-report` has zero remaining command-backed A5 candidates after
  existing manual A5 refs are excluded.
- Exact round-trip remains passed.

Result:
- Recorded 15 additional A5 hardware refs:
  - `s0:000004C4` -> `move.w d0,bltalwm(a5)`
  - `s0:000004C8` -> `clr.w bltcon1(a5)`
  - `s0:000004CC` -> `move.w #DMAF_SETCLR|DMAF_BLITHOG|DMAF_MASTER|DMAF_BLITTER,dmacon(a5)`
  - `s0:0000059A` -> `move.w #DMAF_SETCLR|DMAF_RASTER|DMAF_SPRITE,dmacon(a5)`
  - `s0:00000800` -> `move.w joy1dat(a5),d1`
  - `s0:000008F4` -> `move.w intreqr(a5),d0`
  - `s0:00006366` -> `move.w intreqr(a5),d0`
  - `s0:000063CE` -> `move.w intreqr(a5),d0`
  - `s0:00006478` -> `move.w intreqr(a5),d0`
  - `s0:000066E6` -> `move.w intreqr(a5),d0`
  - `s0:00006732` -> `move.w #$FFFF,bltalwm(a5)`
  - `s0:00006738` -> `clr.w bltamod(a5)`
  - `s0:0000673C` -> `move.w #$26,bltdmod(a5)`
  - `s0:00006742` -> `move.w #BC0F_SRCA|BC0F_DEST|ABC|ABNC|ANBC|ANBNC,bltcon0(a5)`
  - `s0:0000677E` -> `move.w intreqr(a5),d0`
- Every mutation passed manual-log, provenance, semantic-reload,
  rendered-source, and exact round-trip verification.
- The A5 report now has no remaining unrecorded command-backed candidates.
