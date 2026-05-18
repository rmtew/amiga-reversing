Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add manual editing for custom structs, fields, typed accesses, and unresolved
typed gaps.

Current evidence:
- Target metadata supports `custom_structs`.
- Manual Action Log now supports `create_manual_custom_struct`,
  `rename_manual_custom_struct`, and `remove_manual_custom_struct`, and
  effective metadata projects/renames/removes manual struct definitions in
  `custom_structs`.
- Manual Action Log also supports `create_manual_custom_struct_field` and
  `rename_manual_custom_struct_field` and `remove_manual_custom_struct_field`,
  and effective metadata projects/renames/removes fields by
  `(struct_name, offset)`.
- Target command catalog exposes `target.custom_struct.add/edit/rename/remove`
  and `target.custom_struct_field.add/edit/rename/remove`, which emit
  name-keyed custom struct payloads and offset-keyed field payloads.
- Listing/navigation exposes typed accesses, unresolved typed accesses, type
  flow analysis, app-slot field gaps, and field paths.
- Listing element commands now expose `typed_gap.field.add/edit` and
  `typed_access.field.edit/rename/remove`, using typed context struct names and
  offsets.
- `/commands/execute` now has route-level coverage proving selected typed-gap
  and typed-access element commands append the expected custom-struct-field
  Manual Action Log entries and return `custom_struct_field` local effects.
- The loop planner builds explicit `target.custom_struct.*`,
  `target.custom_struct_field.*`, `typed_gap.field.*`, and
  `typed_access.field.*` command candidates and routes typed field commands
  through selected listing element context. It skips already-projected
  struct/field candidates, but blocks unproven changes as missing an
  action-specific verifier until rendered custom-field paths are proven.
- No verifier proves rendered typed field paths from custom struct metadata yet.

Acceptance criteria:
- Struct and field identities are stable by namespace/name/offset and survive
  projection rebuilds.
- Manual actions replay into effective metadata and rendered field references.
- Commands cover typed-access and field-gap contexts.
- Loop planner support covers explicit target custom-struct and typed-field
  command candidates with source element context where applicable.
- Verifiers prove rendered field paths, semantic reload, and round-trip.

Required tests:
Manual replay, command catalog, typed rendering, and verifier tests.
