Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add manual editing for custom structs, fields, typed accesses, and unresolved
typed gaps.

Current evidence:
- Target metadata supports `custom_structs`.
- Manual Action Log now supports `create_manual_custom_struct`, and effective
  metadata projects manual struct definitions into `custom_structs`.
- Listing/navigation exposes typed accesses, unresolved typed accesses, type
  flow analysis, app-slot field gaps, and field paths.
- No command catalog action exists for struct/field add, edit, rename, remove,
  or typed-gap resolution.
- No field-level edit/remove/rename Manual Action Log actions exist yet.

Acceptance criteria:
- Struct and field identities are stable by namespace/name/offset and survive
  projection rebuilds.
- Manual actions replay into effective metadata and rendered field references.
- Commands cover typed-access and field-gap contexts.
- Verifiers prove rendered field paths, semantic reload, and round-trip.

Required tests:
Manual replay, command catalog, typed rendering, and verifier tests.
