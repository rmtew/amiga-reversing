Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Teach the reversing loop to select source-converging actions from analysis,
listing/navigation facts, and command catalog capabilities.

Progress:
- Generic `run-one` now ranks known source-converging command candidates
  (`label.rename`, row data/code seeds, representation commands, and fallback
  comments) instead of selecting only `comment.edit`.
- Iteration reports include planner state with ranked candidates, selected
  command, and skipped-candidate reasons.
- Planner skips candidates already satisfied by projected semantic/current
  metadata, including already-selected literal representations.
- Command availability failures now name the selected missing catalog command.
- Generic inspect review candidates with `create_manual_seed` suggestions now
  map to review-item catalog commands such as `review.seed.code` and
  `review.seed.data.raw`, using the durable review item id.
- Generic `run-one` now opens listing projection when inspect has no candidates
  and emits conservative representation candidates for byte-sized printable
  immediates in byte instructions.
- GenAm smoke performed a non-comment source-converging action through the
  command catalog: `representation.character` rendered `subi.b #48,d1` as
  `subi.b #'0',d1`, verified Manual Action Log, semantic reload, rendered
  listing text, and exact round-trip in iteration `000022`.
- Representation verification now refreshes listing projection after command
  cache invalidation before checking rendered text; this was required by the
  first GenAm smoke attempt.

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

Remaining work:
- Extend autonomous listing candidate feeds beyond byte immediate
  representations.
- Extend planner tests across listing row seed and label paths.

Cleanup / deletion:
Delete after implementation, verification, and proposal notes are complete.
