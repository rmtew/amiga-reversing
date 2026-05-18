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
- Label commands cover some absolute labels, but not execution view add/edit or
  correction/suppression workflows.
- High-level bootblock, resident, library/device, autoinit, and import
  relationship errors are usually importer/analyzer defects when they are
  objectively wrong for a class of targets. Those must stop as implementation
  bugs with regression tests, not become per-target Manual Action Log edits.

Acceptance criteria:
- Target-specific suppressions/corrections and execution views have durable
  identities.
- Manual actions replay deterministically into effective metadata.
- Review/catalog commands can suppress wrong auto/imported facts and add/edit
  execution views. Command exposure remains open pending listing/review identity
  sources for suppressible auto facts.
- Verifiers prove source rendering, reproduction, and round-trip where
  applicable.
- The loop distinguishes importer/analyzer defects from target-specific manual
  suppressions and reports the former as upstream implementation blockers.

Required tests:
Manual replay, command execution, source rendering, and reproduction/round-trip
tests.
