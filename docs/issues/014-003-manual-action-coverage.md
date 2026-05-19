Status: Implementation complete for supported 014 surface; future variants deferred
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
- Actions that generate derived analysis facts have paired corrective actions
  that retract or recompute only the derived facts owned by the original action.
- Gaps such as app-slot add/edit/rename, equate add/edit/rename, data roles,
  data-block layouts, structure fields, API/register semantics,
  correction/suppression, and immediate representation are either implemented
  or split into child issues.

Current progress:
- `remove_manual_seed` replay exists and is now reachable from
  `manual_seed_conflict` review items through the command catalog, using the
  conflict item's durable `seed_ids`.
- Existing `create_manual_register_seed` replay now has explicit coverage for
  both `library_base` and `struct_ptr` semantic helper payloads.
- `suppress_seeded_item` replay projects append-only target-specific seeded
  item suppressions into effective metadata.
- `create_manual_execution_view` replay projects append-only target runtime
  views into effective metadata by `(source_start, source_end, base_addr)`.
- `remove_manual_execution_view` replay removes target runtime views by that
  same durable identity.
- `rename_data_symbol` replay projects a manual seeded-entity name override by
  durable `(hunk, addr)` identity.
- Seeded data symbol removal uses existing durable `suppress_seeded_item`
  replay.
- Manual Action Log owned data-symbol removal uses existing durable
  `remove_manual_seed` replay with the `ManualSeed:*` seed id, so cleanup
  retracts only the source-owned manual symbol projection.
- Data-block layout and scalar element replay is implemented in `014-016`
  through `create/edit/remove_manual_data_block_layout`,
  `set/remove/represent_manual_data_block_element`, deterministic effective
  metadata projection, overlap replacement, stale range blocking, and owned
  element/reference cleanup on layout or element removal.
- Supported absolute byte/word/long interpreted-reference replay is implemented
  in `014-018` through `interpret_manual_data_block_element_ref` and
  `remove_manual_data_block_element_ref`, including owned source-ref cleanup.
- Data-block type/domain binding replay for the active row bind/clear slice is
  implemented in `014-019` through data-block element `type_binding` and
  `previous_type_binding` payloads carrying owner/cleanup and consumed
  provenance lineage.

Child / related implementation issues:
- `014-007-data-role-command-coverage.md`
- `014-008-immediate-representation-verification.md`
- `014-009-equate-constant-editing.md`
- `014-010-api-register-semantic-actions.md`
- `014-011-app-slot-rsset-editing.md`
- `014-012-structure-field-editing.md`
- `014-013-correction-and-view-actions.md`
- `014-014-data-global-symbol-naming.md`
- `014-015-data-block-layout-and-reference-interpretation.md`
- `014-016-data-block-layout-core-metadata.md`
- `014-017-data-block-layout-command-render-verifier.md`
- `014-018-interpreted-data-reference-facts.md`
- `014-019-data-block-type-binding-and-platform-structs.md`
- `014-020-target-equate-value-representation.md`

Note: `014-015` is the data-block investigation parent. Its scalar layout,
supported interpreted-reference, and active type/domain binding Manual Action
Log replay work is implemented in `014-016` through `014-019`. Remaining
data-block Manual Action Log gaps are limited to unsupported reference/type
variants and future generated type-flow/review descendants until their owning
issues define identity, replay, cleanup, and verifier semantics.

Required tests:
Manual action append/replay/projection tests for each added action family.

Cleanup / deletion:
Delete after manual-action coverage is complete or all remaining gaps have
specific child issues.
