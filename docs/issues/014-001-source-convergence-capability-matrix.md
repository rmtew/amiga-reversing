Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Build the complete source-convergence capability matrix for editable facts,
rendered-source constructs, manual actions, command catalog exposure, loop
support, and verifiers.

Out of scope:
Do not implement missing commands in this slice except tiny inspection helpers
needed to complete the matrix. Do not keep the matrix limited to GenAm.

Files likely touched:
- `docs/proposals/014-source-converging-manual-action-surface.md`
- `docs/agents/reversing-loop.md`
- command/manual-action/source-rendering docs or tests if needed for discovery

Acceptance criteria:
- Matrix includes auto-analysis source, rendered-source effect, human edit need,
  durable identity, Manual Action Log support, command support, loop support,
  verifier, and gap issue for every fact family.
- Fact families include labels/functions, app/base slots, globals, equates,
  immediate representation, code/data seeds, strings/tables, structures/types,
  API semantics, register/base facts, review items, and semantic comments.
- Unsupported required capabilities are linked to specific 014 issues.
- Agent instructions say missing matrix/command coverage is a blocker, not a
  reason to script around normal paths.

Required tests:
Docs-only unless helper tooling is added.

Cleanup / deletion:
Delete after the matrix and derived issues are complete and durable notes are in
the proposal.

