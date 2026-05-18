Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add target-local equate/constant add, edit, rename, remove, and use commands.

Current evidence:
- The source model supports constants/EQU.
- The command catalog can suggest `semantic.equate.*` from NDK constants.
- `create_manual_semantic_hint` is currently only projected in
  `ManualActionLogProjection`; effective metadata and rendering do not consume
  it, so equate hints are not yet source-converging.

Acceptance criteria:
- Equates have durable target-local identities.
- Manual actions replay into effective metadata and rendered source.
- Command catalog exposes add/edit/rename/remove/use operations.
- Verifier proves rendered EQU/use sites and round-trip exactness.

Required tests:
Manual action replay, command execution, source rendering, and verifier tests.
