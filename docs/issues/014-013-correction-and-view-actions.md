Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add Manual Action Log support for target-specific auto-analysis suppressions and
execution/runtime view edits that a reverser needs to fix wrong target state.
Do not use manual corrections as a substitute for fixing importer or analyzer
bugs that affect a whole class of targets.

Current evidence:
- Target metadata supports `execution_views`, `absolute_code_labels`, and
  `suppressed_seeded_items`.
- `target_corrections.json` can suppress seeded items.
- Manual Action Log `suppress_seeded_item` now projects append-only
  target-specific suppressions into effective metadata for seeded entities,
  seeded code labels, and seeded code entrypoints.
- Listing rows are annotated with suppressible `target_seeded_metadata.json`
  source identities, and row command catalogs expose
  `correction.suppress_seeded_item.<kind>` for those rows.
- Manual Action Log `create_manual_execution_view` now projects target runtime
  views into effective metadata, and `target.execution_view.add` appends it
  from target command context.
- Manual Action Log `remove_manual_execution_view` now removes target runtime
  views by `(source_start, source_end, base_addr)`, and
  `target.execution_view.remove` appends it from target command context.
- Label commands cover some absolute labels, but not execution view inline edit
  or broader correction workflows.
- High-level bootblock, resident, library/device, autoinit, and import
  relationship errors are usually importer/analyzer defects when they are
  objectively wrong for a class of targets. Those must stop as implementation
  bugs with regression tests, not become per-target Manual Action Log edits.

Acceptance criteria:
- Target-specific suppressions/corrections and execution views have durable
  identities.
- Manual actions replay deterministically into effective metadata.
- Review/catalog commands can suppress wrong imported seeded facts and add/edit
  execution views. Seeded-item row suppression and execution-view add are
  exposed; execution-view removal is exposed by identity, while inline edit and
  broader reproduction/view correction commands remain open.
- Verifiers prove source rendering, reproduction, and round-trip where
  applicable.
- The loop distinguishes importer/analyzer defects from target-specific manual
  suppressions and reports the former as upstream implementation blockers.

Required tests:
Manual replay, command execution, source rendering, and reproduction/round-trip
tests.
