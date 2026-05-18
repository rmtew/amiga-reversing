Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add Manual Action Log support for auto-analysis corrections, suppressions, and
execution/runtime view edits that a reverser needs to fix wrong target state.

Current evidence:
- Target metadata supports `execution_views`, `absolute_code_labels`, and
  `suppressed_seeded_items`.
- `target_corrections.json` can suppress seeded items, but there is no append-only
  manual action or command for this capability.
- Label commands cover some absolute labels, but not execution view add/edit or
  correction/suppression workflows.

Acceptance criteria:
- Corrections and execution views have durable identities.
- Manual actions replay deterministically into effective metadata.
- Review/catalog commands can suppress wrong auto/imported facts and add/edit
  execution views.
- Verifiers prove source rendering, reproduction, and round-trip where
  applicable.

Required tests:
Manual replay, command execution, source rendering, and reproduction/round-trip
tests.
