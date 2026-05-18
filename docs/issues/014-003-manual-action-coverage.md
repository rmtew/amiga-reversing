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
- Gaps such as app-slot add/edit/rename, equate add/edit/rename, and immediate
  representation are either implemented or split into child issues.

Required tests:
Manual action append/replay/projection tests for each added action family.

Cleanup / deletion:
Delete after manual-action coverage is complete or all remaining gaps have
specific child issues.

