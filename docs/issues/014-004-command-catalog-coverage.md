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

Required tests:
Command catalog availability and execution tests for each supported action
family.

Cleanup / deletion:
Delete after command exposure matches the supported manual-action matrix.
