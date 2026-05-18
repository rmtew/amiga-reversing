Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Expose supported source-converging manual actions through command discovery and
`/commands/execute`.

Out of scope:
Do not add private loop-only routes. Do not expose commands whose durable
identity or verifier is not defined.

Files likely touched:
- `amiga_reversing/disasm/manual_action_catalog.py`
- `amiga_reversing/disasm/server.py`
- command catalog tests
- workflow harness tests

Acceptance criteria:
- Command catalog lists available source-converging actions for row, element,
  range, review item, target, and any new identity contexts.
- Each command declares required parameters and effect kind.
- Execution returns authoritative mutation details and workflow profile.
- Missing command support is visible as a precise blocker to the loop.

Current progress:
- `manual_seed_conflict` review items expose `review.seed.remove`, parameterized
  by durable Manual Action Log `seed_id`, and `/commands/execute` appends
  `remove_manual_seed`.
- A6 LVO element contexts expose `semantic.library_base.<library>` commands
  from row API metadata or NDK lookup, and register elements expose
  `semantic.register.struct_ptr` with required `struct_name`.
- Rows backed by suppressible `target_seeded_metadata.json` items expose
  `correction.suppress_seeded_item.<kind>` commands that append
  `suppress_seeded_item` using durable `(kind, hunk, addr)` identity.
- Target context exposes `target.execution_view.add`, with required
  `source_start`, `source_end`, `base_addr`, and `name`, and `/commands/execute`
  appends `create_manual_execution_view`.
- Target context exposes `target.execution_view.remove`, with required
  `source_start`, `source_end`, and `base_addr`, and `/commands/execute`
  appends `remove_manual_execution_view`.
- Rows backed by `target_seeded_metadata.json` seeded entities expose
  `data_symbol.rename`, with required `name`, and `/commands/execute` appends
  `rename_data_symbol`.
- Ordinary data rows expose `data_symbol.rename`, with required `name`, and
  `/commands/execute` appends `rename_data_symbol` as a manual named data seed.
- Rows backed by `target_seeded_metadata.json` seeded entities expose
  `data_symbol.remove`, and `/commands/execute` appends `suppress_seeded_item`.
- Target context exposes `target.equate.add/edit/rename/remove`;
  `/commands/execute` appends the matching Manual Action Log entry and returns
  distinct local mutation details for remove.
- Target context exposes `target.custom_struct.*` and
  `target.custom_struct_field.*`; `/commands/execute` appends the matching
  custom struct/field Manual Action Log entry and returns local mutation
  details for create/edit/rename/remove operations.
- Command execution tests now cover edit-variant local effects for target
  equates, RSSET regions, custom structs, and custom struct fields, not only
  add/remove/rename paths.
- Data-block layout and interpreted-reference command exposure is not covered
  by the existing data-role, representation, symbol, or struct commands; track
  that surface in `014-017` through `014-019`. `014-016` owns metadata and
  Manual Action Log replay only, not command exposure.
- Target-equate definition value representation command exposure is tracked in
  `014-020-target-equate-value-representation.md`.
- RSSET numeric use-site binding command exposure is defined by `014-021` and
  implemented in `014-011`: `rsset.binding.report`, `rsset.binding.bind`,
  `rsset.binding.bind_refine`, `rsset.binding.unbind`,
  `rsset.binding.type_refine`, and `rsset.binding.clear_type`.

Required tests:
Command catalog availability and execution tests for each supported action
family.

Cleanup / deletion:
Delete after command exposure matches the supported manual-action matrix.
