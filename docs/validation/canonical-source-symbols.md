# Canonical operand identities and copied-call projection

The two defects exposed by the Pandora tail investigation have separate causes.

The renderer attached a correct copied-view target to a control operand, but
its subsequent symbol-access planner preferred the original decode candidate's
target. In Pandora, source `$576` encodes JSR `$5AFFA`, resolves to source
`$4AFFA`, and names `initialize_player_and_fixed_animation_nodes`. Planning a
second declaration from raw source `$5AFFA` instead created orphan `$6AFFA`.
The planner now uses the attached operand's resolved section/offset before the
raw decode target. Original decode evidence is retained. A synthetic copied
bootstrap with a valid numeric address also inside the file demonstrates the
old renderer creates the phantom declaration; the corrected renderer agrees
with its call xref and emits none. This is a projection fix, not deletion of
an unexplained manual fact.

Operand representations previously persisted an unchecked name, while native
policy could encode only platform symbols and target equates. New source-label
selections resolve one native render-plan declaration during the locked append
preflight and store section, source offset, rendered address view and value.
The current native operand must agree in value and width; missing, ambiguous,
stale or mismatched choices fail before append. The native renderer checks the
coordinate/view/value again and resolves the current name by coordinate, so a
rename updates rendering and xrefs without rewriting historical actions. Python
neither parses generated names nor translates load addresses. Existing legacy
metadata serialization remains unchanged when no source identity is present.

The asset planner also needed a small general extension: explicit `opaque_data`
classification. Previously only bitmap and sound ranges could become assets.
This new role travels from the normal data layout/element commands through
native metadata and source packaging; unclassified bytes are still excluded.
The same fixup, label, expression, ORG, overlap and numeric-data guards apply.
No media purpose or unused-memory claim is attached to an opaque asset.

Validation: 306 focused Python checks pass across catalog/history, metadata,
representation, source-package and callable-summary paths; all 812 native checks
pass. The 14 new end-to-end cases cover canonical identities in local/runtime
views, exact C/vasm reconstruction, xrefs after rename, invalid selection refusal
with unchanged history, native rejection of invalid identities, the copied-call
regression and opaque layout-to-asset publication.

A broader runtime/backend selection has 16 passes, two skips and eight failures.
All eight failures reproduce with the previous renderer linked against the same
native objects; no new failures appeared. These existing tests remain open:
FAILED tests/test_c_backend.py::test_full_listing_runtime_copy_storage_alias_precedes_runtime_org
FAILED tests/test_c_backend.py::test_full_listing_contained_runtime_view_does_not_emit_second_org
FAILED tests/test_c_backend.py::test_real_dll_runtime_absolute_raw_binary_materializes_runtime_load_range
FAILED tests/test_c_backend.py::test_listing_artifact_runtime_observation_view_maps_pc_without_source_view
FAILED tests/test_c_backend.py::test_real_dll_epic_runtime_absolute_raw_source_keeps_single_load_org
FAILED tests/test_c_backend.py::test_real_dll_ice_bootloader_stage_recovers_copied_runtime_payload_without_bad_addend
FAILED tests/test_c_backend.py::test_real_dll_runtime_ref_to_copied_range_start_seeds_org_entry_code
FAILED tests/test_c_backend.py::test_real_dll_magicland_org_bootstrap_decodes_copied_runtime_entry

On Pandora, the corrected core projection removes the orphan without changing
manual facts or original bytes. Full C/vasm receipt:
`50771b9f5546592e67e62ce92efa5fbd16d2dc3868e6ec05e3177b2261567630`;
rendered-source SHA256 `a1f139cd5c237514d5dc116155a108c21cac8bb4e808779d288b0a725a19be48`.
It also removes false call-target boundaries inside seven already classified
bitmap banks, enabling their existing asset policy to export contiguous named
assets. The prior 78 asset/include files remain byte-identical and retained;
these seven assets are additional native exports of original bytes. Tail
classification is a separate subsequent action slice.
