Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add first-class data/global symbol naming actions for source-converging names
that are not function or code labels.

Accepted review state:
Data/global naming remains source-identity work by default. Reference reports
may rank or verify naming candidates, but names do not create provenance or
type-flow descendants unless a separate semantic action owns them.

Current evidence:
- `SeededEntityMetadata.name` can name data definitions.
- Manual data seeds can carry a name.
- The command catalog now exposes named row, data-literal element, range, and
  unreconciled data review seed commands that write `name` into the seed
  payload.
- Manual Action Log `rename_data_symbol` now projects a manual seeded-entity
  name override by durable hunk/address/range identity, preserving generated
  seeded-entity metadata during effective metadata merge.
- Rows backed by `target_seeded_metadata.json` seeded entities expose
  `data_symbol.rename`, and `/commands/execute` appends `rename_data_symbol`.
- Seeded-entity rename now has rendered-source and exact direct-rebuild verifier
  coverage for the definition name path.
- Seeded-entity rows now expose `data_symbol.remove`, mapped to durable
  `suppress_seeded_item`, with command execution plus rendered-source/exact
  direct-rebuild coverage.
- Ordinary data rows now expose `data_symbol.rename`, projecting a manual named
  data seed by hunk/source range with rendered-source/exact direct-rebuild
  coverage.
- Listing elements backed by internal `runtime_address_refs` now expose
  `data_symbol.rename` for referenced data use-sites, projecting the referenced
  target hunk/offset/size into the same durable data-symbol identity.
- Referenced data use-site commands now preserve existing `data_ref` symbols as
  `previous_name`, and autonomous referenced-data candidates skip symbols that
  already match the generated data name.
- Manual data-symbol rename now has rendered-source and exact direct-rebuild
  verifier coverage for an instruction use-site reference to the renamed data
  definition.
- Loop planner recognizes explicit data-symbol add/edit/rename/remove
  candidates and skips already-satisfied projected names/removals. It also
  mines internal `data_ref` listing elements into autonomous referenced-data
  rename candidates.
- Autonomous referenced-data rename candidates now skip names already present in
  effective target metadata as well as Manual Action Log projections.
- Autonomous data-symbol rename candidates now include row-level `data_class`
  evidence for data definitions, not only referenced data use-sites.
- Autonomous data-symbol already-satisfied checks now match existing names by
  data-symbol kind plus hunk/address/end identity, so a non-data seeded entity
  or different-sized data seed at the same address does not hide a distinct
  naming candidate.
- Effective metadata projection now merges seeded data-symbol entities by
  hunk/address/end/type identity, preventing a same-address manual rename from
  replacing a distinct generated data range.
- Target metadata merge now uses the same hunk/address/end/type identity for
  seeded entities, preserving same-address generated ranges and typed metadata
  during manual-over-seeded overrides.
- Exact-identity data-symbol rename projection now preserves existing typed
  entity fields such as struct/field/c-type/value-domain metadata instead of
  turning a naming override into semantic metadata loss.
- Autonomous referenced-data rename candidates now generate
  `runtime_address_XXXXXXXX` names from stable runtime-address references when
  no data class is available.
- Generic `run-one` now verifies `data_symbol.remove` by checking either the
  reloaded suppressed seeded item state or the removed manual data-symbol seed,
  rather than affected row metadata.
- `data_symbol.rename_existing` now exposes first-class rename-existing-symbol
  workflows for seeded data entities, ordinary named data rows, and referenced
  data use-sites with a preserved `previous_name`; it reuses the durable
  `rename_data_symbol` Manual Action Log projection and rendered-name verifier.
- `data_symbol.add` and `data_symbol.edit` now expose explicit first-name and
  existing-name edit workflows in the catalog while reusing the same durable
  `rename_data_symbol` Manual Action Log projection and rendered-name verifier.
- Planner command normalization strips report/provenance fields from
  data-symbol rename/remove parameter payloads; rename parameters carry the
  requested name plus selected hunk/address/end source identity, and remove
  parameters carry only selected seeded-item or manual-seed identity.
- Embedded data-symbol command normalization also strips report/provenance
  fields from command context; selected row or element locator remains the
  rendered source location, while hunk/address/end disambiguates the durable
  data-symbol source identity.
- `data_symbol.remove` now preserves the source-identity boundary for
  Manual Action Log owned data symbols: rows whose effective symbol comes from
  `ManualSeed:*` remove that manual seed, while generated seeded entities still
  use seeded-item suppression.
- Route-level coverage now proves the same boundary at command catalog and
  execution time: `ManualSeed:*` data-symbol rows emit `remove_manual_seed`,
  not generated seeded-item suppression.
- Planner command availability for `data_symbol.remove` now matches the cleanup
  identity shape before execution: manual data-symbol removals require the
  selected `seed_id`, while generated seeded-entity removals require the selected
  suppression identity, including `end` when the catalog row has a ranged seeded
  entity.
- Planner already-satisfied checks for `data_symbol.remove` now use the same
  cleanup identity shape: selected manual `seed_id` for Manual Action Log owned
  data symbols, or generated seeded-item `(kind, hunk, addr[, end])`
  suppression identity.
- Data-symbol rename command execution now honors the selected seeded-entity
  `end` when building the durable payload, so a same-address generated range
  cannot be renamed by accident when the operator selected a different range.
- Planner-built data-symbol add/edit/rename/rename-existing commands now
  preserve selected hunk/address/end source identity while still stripping
  provenance/report fields, and availability rejects stale ranged catalog
  entries before execution.
- Data-symbol seed ids now include `end` when present and Manual Action Log
  projection derives that ranged id from the payload, so same-address range
  renames cannot collide before effective metadata merge.
- Seeded-entity suppression projection now carries optional `end` and effective
  metadata applies ranged suppressions exactly, so suppressing one generated
  seeded data range does not remove a same-address range with a different end.
- Real GenAm listing rows with render-plan `data_class` evidence now have a
  smoke test proving they feed autonomous `data_symbol.rename` or
  `data_symbol.rename_existing` candidates with projected-name verification and
  exact round-trip status.
- Data-symbol add/edit/rename verification now derives expected state from the
  executed durable `data_symbol` payload before checking semantic reload and
  rendered text. A matching rendered row alone cannot hide a missing or
  mismatched hunk/address/range/name payload.
- Broader global data-symbol workflows and expanded autonomous candidate
  workflows remain open beyond seeded data-entity rename/remove,
  add/edit/rename-existing-symbol, and internal referenced data use-sites.
- Data symbols created or consumed by manual interpretation of values inside
  opaque data blocks are tracked by the data-block investigation in `014-015`,
  with interpreted-reference facts in `014-018` and type/domain binding in
  `014-019`.
- The proposal goal includes clearer global and data names.
- Post-`014-022` split: data/global naming remains source-identity work, not
  semantic/type propagation by default. Reference queries for labels/data
  symbols are evidence-bearing def-use/xref views and may support provenance
  exploration, but a rename does not itself create provenance/type-flow
  descendants unless a separate semantic action owns them.

Acceptance criteria:
- Data/global symbol identities are stable by hunk, source/runtime address
  range, and symbol kind, not row index or rendered text.
- Manual actions cover add, edit, rename, remove, and rename-existing-symbol
  workflows for data definitions and referenced global data names.
- Command catalog exposes row, element, range, and review-item actions where
  evidence identifies a data/global symbol.
- Verifiers prove semantic reload, rendered definition names, rendered use-site
  references where applicable, and round-trip exactness.
- The loop can rank a non-comment data/global naming candidate and skip
  already-satisfied names from projected semantic state.
- Naming workflows preserve the boundary between source identity and
  provenance/type-flow facts; any semantic descendants are owned by a separate
  action.
- Source identity boundary:
  data/global names and label names may consume xref/reference reports for
  candidate ranking and rendered-use verification, but the name itself is not a
  provenance source-family classification. A separate semantic action must
  consume a reference as provenance before it can generate type-flow, field
  bindings, or propagated descendants.
- Remove workflows must preserve their source identity boundary at availability
  time as well as verification time: command id `data_symbol.remove` is shared,
  but manual-seed cleanup and generated seeded-item suppression are different
  durable actions.

Required tests:
Identity tests, manual replay tests, command catalog execution tests,
rendered-source/use-site tests, loop verifier tests, and a GenAm-style smoke
when a target exposes a high-confidence data/global naming candidate.
