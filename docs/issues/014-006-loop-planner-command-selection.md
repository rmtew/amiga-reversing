Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Teach the reversing loop to select source-converging actions from analysis,
listing/navigation facts, and command catalog capabilities.

Out of scope:
Do not implement a speculative decompiler or private planner API. Do not fall
back to comments or scripts when a structured action is missing.

Files likely touched:
- `amiga_reversing/reversing_loop.py`
- command/catalog metadata if ranking needs more shape
- focused reversing-loop tests
- `docs/agents/reversing-loop.md`

Acceptance criteria:
- Loop ranks candidates by source-convergence value and command availability.
- Reports include evidence, expected rendered-source improvement, command,
  verifier, and skipped-candidate reasons.
- Already-satisfied candidates are skipped using projected semantic state.
- Missing command/verifier support stops with a precise capability blocker.
- A GenAm smoke performs one non-comment source-converging action through the
  command catalog and verifies it.

Required tests:
Planner ranking, already-satisfied skipping, command-catalog selection, verifier
failure, and GenAm-style non-comment smoke.

Cleanup / deletion:
Delete after implementation, verification, and proposal notes are complete.

