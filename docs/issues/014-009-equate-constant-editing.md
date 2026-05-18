Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add target-local equate/constant add, edit, rename, remove, and use commands.

Current evidence:
- The source model supports constants/EQU.
- The command catalog can suggest `semantic.equate.*` from NDK constants.
- `create_manual_semantic_hint` now projects NDK `domain="equate"` hints with
  a known `symbol` into manual symbol representations, and rendering consumes
  them as symbolic immediates with include coverage.

Progress:
- Known NDK equate use sites are source-converging: Manual Action Log hint ->
  effective metadata -> rendered symbol -> exact direct rebuild.
- Target-local equate identities and add/edit/rename/remove commands remain
  open.

Acceptance criteria:
- Equates have durable target-local identities.
- Manual actions replay into effective metadata and rendered source.
- Command catalog exposes add/edit/rename/remove/use operations.
- Verifier proves rendered EQU/use sites and round-trip exactness.

Required tests:
Manual action replay, command execution, source rendering, and verifier tests.
