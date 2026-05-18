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
- Ranked candidate command summaries now report the candidate-specific verifier
  that selection uses, not only the static command default.
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
- Planner now recognizes explicit `data_symbol.rename` and `data_symbol.remove`
  candidates, ranks them above fallback comments, and skips already-satisfied
  data-symbol rename/remove candidates from projected metadata.
- Planner now mines internal listing `data_ref` elements backed by
  `runtime_address_refs` into autonomous `data_symbol.rename` candidates and
  routes those commands through element context, skipping candidates already
  satisfied by projected manual data-symbol seeds.
- Planner now mines null-terminated printable ASCII data rows into autonomous
  `row.seed.data.string` candidates, skipping rows already covered by projected
  manual string seeds.
- Planner now accepts explicit `range.seed.code` and `range.seed.data.*`
  candidates, routes them through durable range locators, and requires
  round-trip verification.
- Planner now accepts explicit review-item candidates for named/data-role seeds,
  seed removal, and label rename/scope/removal commands, routes them through
  durable review item ids, and uses manual-label state verification for label
  edits.
- Planner now skips already-satisfied target-local equate candidates from
  projected target-equate metadata.
- Planner already-satisfied checks now treat rename candidates with
  `previous_name` as satisfied when projected metadata has the requested new
  name.
- Generic `run-one` now retries listing-derived candidate mining when inspect
  returns candidates but every candidate is skipped, so stale/projected review
  work no longer prevents available source-converging listing edits.
- Generic `run-one` also treats an inspect-selected `comment.edit` as
  provisional until listing-derived candidates have been mined once, keeping
  comments as fallback-only work.
- Planner candidate selection now evaluates alternate command options for a
  candidate, so an unverified higher-ranked command does not hide a supported
  lower option from the same evidence.
- Non-dry execution now checks catalog availability across alternate command
  options before stopping, so a missing higher-ranked command does not hide an
  available lower-ranked action from the same candidate.
- Planner verifier summaries now report the action-specific verifier for
  data-symbol rename/remove candidates rather than a generic round-trip label.
- Planner verifier summaries now report `target_equate_state` for
  target-equate commands rather than a generic round-trip label.
- Planner verifier summaries now report `rsset_region_state` for target RSSET
  and selected app-slot commands rather than a generic round-trip label.
- Planner verifier summaries now report `manual_seed_state` for row/range/review
  seed creation and review seed removal rather than a generic round-trip label.
- Planner verifier summaries now report `manual_label_state` for review label
  rename/scope/removal commands rather than a generic round-trip label.
- Autonomous listing feeds now skip data names and data roles already present
  in effective target metadata, not only Manual Action Log projections.
- Generic `run-one` now mines source descriptor entrypoint evidence into an
  autonomous `label.rename` candidate when the listing still has the generated
  source label at that address.
- Autonomous entrypoint label candidates now skip labels already present in
  effective target metadata or Manual Action Log projections.
- Generic `run-one` now mines `data_class` listing rows into row-level
  `data_symbol.rename` candidates, beyond referenced data use-sites.
- Generic `run-one` now mines listing LVO API-call rows into autonomous
  `semantic.library_base.*` candidates.
- Autonomous referenced-data rename candidates now also use stable runtime
  addresses when `runtime_address_refs` have no data class.

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
  representations, internal referenced data names, and obvious ASCII strings.
- Extend autonomous planner feeds for label and broader data/global symbol
  candidates.

Cleanup / deletion:
Delete after implementation, verification, and proposal notes are complete.
