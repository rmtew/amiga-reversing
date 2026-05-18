Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add first-class data/global symbol naming actions for source-converging names
that are not function or code labels.

Current evidence:
- `SeededEntityMetadata.name` can name data definitions.
- Manual data seeds can carry a name.
- The command catalog now exposes named row, data-literal element, range, and
  unreconciled data review seed commands that write `name` into the seed
  payload.
- Manual Action Log `rename_data_symbol` now projects a manual seeded-entity
  name override by durable `(hunk, addr)` identity, preserving generated
  seeded-entity metadata during effective metadata merge.
- Rows backed by `target_seeded_metadata.json` seeded entities expose
  `data_symbol.rename`, and `/commands/execute` appends `rename_data_symbol`.
- Seeded-entity rename now has rendered-source and exact direct-rebuild verifier
  coverage for the definition name path.
- Durable data/global symbol edit, rename, remove, rename-existing-symbol,
  referenced-use-site, and loop-planner workflows remain open beyond seeded
  data-entity rename.
- The proposal goal includes clearer global and data names.

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

Required tests:
Identity tests, manual replay tests, command catalog execution tests,
rendered-source/use-site tests, loop verifier tests, and a GenAm-style smoke
when a target exposes a high-confidence data/global naming candidate.
