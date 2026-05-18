Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add or specify missing Manual Action Log actions for source-converging edits
identified by the capability matrix.

Out of scope:
Do not expose commands before the durable manual action and replay semantics are
clear. Do not write retired state models.

Files likely touched:
- `amiga_reversing/disasm/manual_actions.py`
- `amiga_reversing/disasm/target_metadata.py`
- source rendering/projection code
- focused tests

Acceptance criteria:
- Required manual actions exist for each supported source-converging edit
  family.
- Replay produces deterministic effective metadata/projection state.
- Existing manual state remains append-only and undo uses corrective actions.
- Gaps such as app-slot add/edit/rename, equate add/edit/rename, data roles,
  structure fields, API/register semantics, correction/suppression, and
  immediate representation are either implemented or split into child issues.

Current progress:
- `remove_manual_seed` replay exists and is now reachable from
  `manual_seed_conflict` review items through the command catalog, using the
  conflict item's durable `seed_ids`.
- Existing `create_manual_register_seed` replay now has explicit coverage for
  both `library_base` and `struct_ptr` semantic helper payloads.

Child issues:
- `014-007-data-role-command-coverage.md`
- `014-008-immediate-representation-verification.md`
- `014-009-equate-constant-editing.md`
- `014-010-api-register-semantic-actions.md`
- `014-011-app-slot-rsset-editing.md`
- `014-012-structure-field-editing.md`
- `014-013-correction-and-view-actions.md`
- `014-014-data-global-symbol-naming.md`

Required tests:
Manual action append/replay/projection tests for each added action family.

Cleanup / deletion:
Delete after manual-action coverage is complete or all remaining gaps have
specific child issues.
