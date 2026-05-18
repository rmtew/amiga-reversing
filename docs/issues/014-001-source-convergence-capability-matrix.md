Status: Complete
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Build the complete source-convergence capability matrix for editable facts,
rendered-source constructs, manual actions, command catalog exposure, loop
support, and verifiers.

Completion:
The proposal now contains an evidence-backed matrix covering current target
metadata, Manual Action Log projection, command catalog exposure, source
rendering support, reversing-loop support, verifier state, and known gaps.
Concrete child issues were added for the missing fact families discovered by
the audit:

- `014-007-data-role-command-coverage.md`
- `014-008-immediate-representation-verification.md`
- `014-009-equate-constant-editing.md`
- `014-010-api-register-semantic-actions.md`
- `014-011-app-slot-rsset-editing.md`
- `014-012-structure-field-editing.md`
- `014-013-correction-and-view-actions.md`
- `014-014-data-global-symbol-naming.md`

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
- Unsupported required capabilities are linked to specific 014 issues,
  including data/global symbol naming.
- Agent instructions say missing matrix/command coverage is a blocker, not a
  reason to script around normal paths.

Required tests:
Docs-only unless helper tooling is added.

Cleanup / deletion:
Can be deleted after this completion note and the proposal matrix are accepted.
