Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add manual editing for custom structs, fields, typed accesses, and unresolved
typed gaps.

Post-`014-022` split:
This issue consumes generic provenance from `014-010` when typed access or gap
edits depend on where a base/register value came from. It owns custom
struct/field resolver and rendered typed-field proof, not the generic
provenance model itself.

Accepted review state:
Typed-field writes consume accepted `struct_pointer` provenance and must not
execute from exploratory reports alone. This issue owns C resolver/render
support, type-shape checks, rendered-field verification, and cleanup of owned
propagated typed accesses.

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
- The C analysis policy imports target metadata `custom_structs`, deep-copies
  heap-owned custom-struct policy state, and emits custom structs in effective
  policy JSON.
- Register-seed-backed custom struct fields now resolve through the C typed
  resolver and render field paths such as `player_score(a0)` in source/listing
  output.
- Target custom structs now shadow same-named platform structs in the typed
  resolver, so a target-local `InputEvent` seed renders target fields instead
  of silently falling back to NDK `InputEvent`.
- Selected `typed_gap.field.*` and `typed_access.field.*` commands now require
  accepted `struct_pointer` provenance before execution, persist the consumed
  `source_evidence_id` in the Manual Action Log payload, and verify manual-log
  replay, projected custom-field state, rendered typed access, provenance
  evidence, and exact round-trip.
- Selected typed-field execution now rejects a known selected access
  width/field size mismatch before command availability or mutation.
- Selected typed-field execution now also rejects a payload struct name that
  differs from the selected typed access/gap owner or refined struct before
  command availability or mutation.
- Selected typed-field execution now rejects a field shape whose offset/size
  runs past the selected struct size when that struct size is known.
- Projected custom-field state now stamps `owner_action_id` for create/rename
  and `cleanup_action_id` for remove, and the semantic reload verifier requires
  consumed provenance and owner fields to match the reloaded projection.
- Selected typed-field rename verification now proves the selected row renders
  the new field and no longer exposes the previous field name/access; rename
  proof fails when the command does not carry the previous field name.
- Planner command availability for `typed_gap.field.*` and
  `typed_access.field.*` now requires the refreshed catalog entry to match the
  selected struct, offset, and consumed `struct_pointer` provenance identity.
  A stale typed-field candidate can no longer borrow availability from a
  same-command action exposed by a different typed access/gap.
- Typed-field payloads, candidate commands, catalog availability checks, and
  custom-field semantic reload verification now preserve and compare
  `parent_evidence_ids`, so derived struct-pointer authority cannot silently
  lose the dependency set it consumed.
- Typed-field execution now preserves accepted provenance carried on selected
  element context, including manual-classified evidence, path/lifetime scope,
  conflicts, and parent evidence ids, instead of regenerating row-local
  `struct_pointer` evidence during catalog re-selection.
- Typed-field add/edit/rename parameter schemas now advertise the full accepted
  provenance boundary, including source evidence id, family/status,
  path/lifetime scope, conflicts, parent ids, manual override reason, and
  cleanup scope. This keeps the public command contract aligned with the
  verifier and availability gates.
- Target-wide `target.custom_struct*` metadata commands remain blocked by the
  missing action-specific verifier when selected autonomously; they do not prove
  a selected rendered field path.
- Owned cleanup of propagated typed-access descendants after remove/rename is
  still missing beyond selected-row rendered-source proof.
- Custom target struct names still share the resolver namespace with platform
  structs. Target-local names now win on collision; explicit namespace identity
  remains future work for choosing an NDK/platform struct when a target custom
  struct intentionally uses the same display name.
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
- Post-`014-022` provenance decisions require typed-field descendants to record
  both consumed provenance `source_evidence_id` and field/edit `owner_action_id`
  when they differ. Path-specific or conflicting provenance must block broad
  typed-field propagation until a path/lifetime scope or manual classification
  is selected.

Acceptance criteria:
- Struct and field identities are stable by namespace/name/offset and survive
  projection rebuilds.
- Typed field application can consume accepted provenance evidence for
  `struct_pointer` sources without re-solving provenance locally.
- Typed field edits consume `struct_pointer` provenance by requiring the
  selected typed access/gap or candidate to name an accepted
  `source_evidence_id`, owner struct/type identity, path/lifetime scope, field
  offset, observed access width, and existing field/gap state. Exploratory
  provenance reports can suggest a field edit but cannot execute it.
- C resolver/render path to prove before unblocking loop execution: import
  `custom_structs` into the analysis policy, resolve custom fields alongside
  platform/NDK fields, render selected and propagated custom field paths, and
  expose unresolved/conflicting typed accesses when shape reconciliation fails.
- Type-shape compatibility checks must compare selected field offset, access
  width, storage kind, nested struct/array shape, platform/custom namespace,
  and existing field overlap. Mismatches block propagation or create review
  feedback; they must not silently emit typed facts.
- Rendered-field verifier must prove Manual Action Log replay, effective
  custom struct/field metadata, C semantic reload, rendered field path at the
  selected access, exact round-trip, and cleanup of propagated typed accesses
  by `owner_action_id` on remove/rename/clear. Selected-row typed-field proof
  now includes stale previous-name/access rejection for rename; propagated
  descendant cleanup remains open.
- Availability checks already enforce selected struct/offset/provenance
  identity for typed-field writes. Future propagated typed-access feeds must
  preserve that invariant and add explicit owner-scoped cleanup proof before
  widening beyond selected rows.
- Manual actions replay into effective metadata and rendered field references.
- Commands cover typed-access and field-gap contexts.
- Loop planner support covers explicit target custom-struct and typed-field
  command candidates with source element context where applicable.
- Verifiers prove rendered field paths, semantic reload, and round-trip.

Required tests:
Manual replay, command catalog, typed rendering, and verifier tests.
