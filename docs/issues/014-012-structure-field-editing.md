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
- Non-dry execution now rechecks the selected command's action-specific
  verifier before catalog availability or execution, so forced or stale
  selections cannot bypass the custom-struct missing-verifier block through
  generic target local-effect projection.
- That pre-execution block is covered for target custom-struct commands,
  target custom-struct-field commands, typed-gap field commands, and typed-access
  field commands.
- The C analysis policy currently imports target metadata for register seeds,
  seeded entities, target equates, manual representations, execution views,
  absolute labels, and Amiga RSSET layout regions, but has no `custom_structs`
  import into the typed-reference resolver.
- No verifier proves rendered typed field paths from custom struct metadata yet.
- Applying custom or platform structs inside arbitrary data blocks, and mixing
  those fields with ad hoc layout elements or interpreted references, is tracked
  by the `014-015-data-block-layout-and-reference-interpretation.md`
  investigation and the concrete `014-019-data-block-type-binding-and-platform-structs.md`
  implementation issue.
- Struct fields need representation and type metadata rich enough for agentic
  reversing work: per-field display style, enum/equate domain, nested
  custom/platform struct type, array count/stride, generated field names that
  can be renamed durably, and enough source identity to propagate typed access
  improvements through `014-010`.
- Platform struct reuse should be based on parsed/static platform data such as
  NDK include output, not copied ad hoc strings in individual actions.
- RSSET binding type refinement from `014-021` depends on this issue for
  custom/platform type compatibility. A `rsset.binding.type_refine` command must
  block until rendered typed-field paths are proven and the chosen type shape
  reconciles with the bound field size and observed accesses.

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
