Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Teach the reversing loop to select source-converging actions from analysis,
listing/navigation facts, and command catalog capabilities.

Accepted review state:
Planner provenance support starts read-only. Non-dry semantic/type writes must
wait for accepted evidence, resolved path/lifetime scope, supported catalog
command, action-specific verifier, and already-satisfied checks against
effective metadata/provenance state.

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
- Planner verifier summaries now distinguish `data_symbol.remove` cleanup
  shapes: seeded-item removals report `suppressed_seeded_item`, while
  `ManualSeed:*` data-symbol removals report `manual_seed_state` and keep only
  the `seed_id` command parameter.
- Planner verifier summaries now report `target_equate_state` for
  target-equate commands rather than a generic round-trip label.
- Planner verifier summaries now report `rsset_region_state` for target RSSET
  and selected app-slot commands rather than a generic round-trip label.
- Planner verifier summaries now report `manual_seed_state` for row/range/review
  seed creation and review seed removal rather than a generic round-trip label.
- Planner verifier summaries now report `manual_label_state` for review label
  rename/scope/removal commands rather than a generic round-trip label.
- Planner verifier summaries now let a command-specific verifier override a
  candidate's generic `round_trip` fallback, so stale explicit candidates do
  not hide stricter state verifiers.
- Non-dry execution now blocks selected commands with no action-specific
  verifier before catalog availability or command execution, so bypassed or
  stale selections cannot execute unverified source changes.
- Non-dry execution now queries range command availability with
  `context=range` and serialized range locators instead of falling through to
  target context, so explicit `range.seed.*` candidates can reach the range
  command catalog.
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
- Listing-derived candidates are now mined from bounded paged listing windows
  instead of the first 2048 rows only; this is required for real GenAm direct
  LVO calls, which first appear around row 8030.
- GenAm real-target smoke now proves the autonomous API/register feed can mine
  a direct `_LVOAllocMem(a6)` row, select
  `semantic.library_base.exec.library`, execute through the command catalog,
  append Manual Action Log state, reload the library-base register seed, and
  retain exact round-trip status.
- Autonomous referenced-data rename candidates now also use stable runtime
  addresses when `runtime_address_refs` have no data class.
- GenAm real-target smoke now proves the autonomous RSSET feed can mine an
  `app-slot-suggestions` candidate, select `target.rsset_region.add`, execute
  through the command catalog, append Manual Action Log state, reload RSSET
  metadata, render an `RS.*` definition, and retain exact round-trip status.
- Planner now treats report/inspection commands as planner-visible evidence,
  not executable edits. Report-only options are summarized with
  `execution_policy=report_only`, skipped before selection, and blocked again
  if a stale selected command or catalog entry reaches non-dry execution.
- Provenance-backed planner gates now read only the command's direct consumed
  evidence fields. Nested cleanup-scope evidence ids cannot satisfy typed-field
  or data-block type write prerequisites.
- Command availability for `rsset.binding.bind`/`unbind` now requires and
  matches the complete
  selected binding identity, including layout/base, base register,
  `base_evidence_id`, displacement, and operand index. A row that exposes a
  different RSSET binding action no longer authorizes a stale candidate with a
  mismatched base evidence id.
- Catalog availability for provenance-bearing typed-field and data-block type
  writes now matches the consumed provenance boundary, not only command id and
  layout/field coordinates. Stale candidates with a different
  `source_evidence_id`, path/lifetime scope, conflict state, override reason, or
  cleanup scope no longer pass the availability gate.
- Planner command-availability refresh now serializes provenance context for row
  and element command queries, matching the server-side contract. Accepted
  `source_evidence_id`, source family/status, path/lifetime scope, conflicts,
  parent ids, cleanup scope, and override fields survive the refreshed catalog
  lookup instead of being lost between candidate selection and availability
  matching.
- Planner report-only recognition now uses the supported catalog command shape
  `*.report` only. Legacy `provenance.explore_*` ids are not normalized into
  planner commands, so stale candidate feeds cannot bypass the current command
  catalog contract.
- Semantic hint candidates for LVO, struct-offset, and equate commands now skip
  when projected semantic state already carries the same selected hint identity,
  so verified hint writes are not repeated just because listing text still
  exposes the same numeric operand.
- Planner alternate-command selection now uses command-specific source,
  provenance, and cleanup identity parameters instead of only command id plus
  context, so one stale same-context command cannot hide another valid
  ranged/provenance-backed command. Planner-to-planner comparison uses the
  union of identity parameters present on either command, so a candidate that
  lacks accepted evidence cannot exclude one that carries it.

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

Working goal:
- Treat Proposal 014 and this issue as live implementation state. Planner work
  is not complete until the matrix and issue evidence/remaining-work lists match
  the code behavior.
- Keep comments as fallback-only. If structured command support or verification
  is missing, stop with a precise capability blocker instead of selecting a
  note/comment path.
- Prefer real target convergence evidence before widening autonomous feeds:
  candidate mined, command catalog selected, Manual Action Log appended,
  rendered source improved, exact round-trip passed.

Remaining work:
- Extend autonomous listing candidate feeds beyond byte immediate
  representations, internal referenced data names, and obvious ASCII strings.
- Extend autonomous planner feeds for label and broader data/global symbol
  candidates.
- Do not broaden custom-struct or typed-field semantic feeds past explicit
  candidates until their rendered-source verifiers are proven in `014-005`,
  `014-010`, and `014-012`. API/register has first real GenAm evidence for
  library-base register seeds, but broader API argument/return semantics remain
  open.
- Add real-target smoke coverage for each new autonomous feed before considering
  the feed mature; app-slot/RSSET and API/register library-base seeds have first
  GenAm coverage, while structures, correction/view actions, broader
  data/global symbols, data-block layouts/interpreted references, and richer
  API semantics still need family-specific evidence (`014-010`, `014-012`,
  `014-013`, `014-014`, `014-017`, `014-018`, `014-019`, `014-020`).
- Do not mine raw numeric RSSET binding candidates broadly until `014-011`
  implements the `014-021` report/bind/refine/unbind model and its verifiers.
  First feed should use a real target like GenAm `$0102(a6)` with one selected
  use-site, clear base evidence, linked gap state, and owned cleanup.
- Explicit RSSET binding candidates must carry the chosen layout/base and
  `base_evidence_id`; raw displacement element availability alone is only
  enough for `rsset.binding.report`, not mutation.
- Post-`014-022` split: planner feeds may run generic provenance/def-use
  exploration as read-only evidence gathering. They must not execute semantic
  or type writes from exploratory provenance alone. Write candidates require a
  supported command, durable provenance/classification evidence, resolved
  path/lifetime scope when definitions differ, action-specific verifier support,
  and already-satisfied checks against effective metadata.
- Raw or unsupported semantic/type candidates, including raw RSSET
  displacement candidates, should remain report-only until those gates exist.
- Planner read/write rules:
  read-only provenance reports may be mined freely for candidate explanation,
  duplicate detection, and missing-capability reports. The planner may suggest
  a write when a supported catalog command exists and the report names an
  accepted `source_evidence_id`, compatible source family, resolved
  path/lifetime scope, and action-specific verifier. The planner may execute a
  write only when the same checks pass at execution time against refreshed
  effective metadata.
- Already-satisfied checks must compare against effective metadata and
  provenance state, not just current listing text. For semantic/type work this
  includes existing register seeds, semantic hints, RSSET bindings/regions,
  custom fields, data-block layouts/bindings, suppressed/removed facts, and
  accepted provenance classifications or overrides.
- Exploratory evidence alone may produce `suggested_only` or report-only
  planner output. It must not become a non-dry write candidate until accepted
  classification/link/apply state exists.
- Catalog availability is not sufficient write authority: if the available
  entry has `effect=inspection` or `appends_to_manual_action_log=false`, the
  loop must stop at `command_execution_policy` instead of POSTing it.
- Catalog command id availability is not sufficient identity authority for
  evidence-bearing writes. Any command family whose parameters select consumed
  provenance or cleanup identity must compare those parameters against the
  refreshed catalog entry before execution.
Cleanup / deletion:
Delete after implementation, verification, and proposal notes are complete.
