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
- `tests/test_c_backend.py::test_full_listing_runtime_copy_storage_alias_precedes_runtime_org`
- `tests/test_c_backend.py::test_full_listing_contained_runtime_view_does_not_emit_second_org`
- `tests/test_c_backend.py::test_real_dll_runtime_absolute_raw_binary_materializes_runtime_load_range`
- `tests/test_c_backend.py::test_listing_artifact_runtime_observation_view_maps_pc_without_source_view`
- `tests/test_c_backend.py::test_real_dll_epic_runtime_absolute_raw_source_keeps_single_load_org`
- `tests/test_c_backend.py::test_real_dll_ice_bootloader_stage_recovers_copied_runtime_payload_without_bad_addend`
- `tests/test_c_backend.py::test_real_dll_runtime_ref_to_copied_range_start_seeds_org_entry_code`
- `tests/test_c_backend.py::test_real_dll_magicland_org_bootstrap_decodes_copied_runtime_entry`

On Pandora, the corrected core projection removes the orphan without changing
manual facts or original bytes. Full C/vasm receipt:
`50771b9f5546592e67e62ce92efa5fbd16d2dc3868e6ec05e3177b2261567630`;
rendered-source SHA256 `a1f139cd5c237514d5dc116155a108c21cac8bb4e808779d288b0a725a19be48`.
It also removes false call-target boundaries inside seven already classified
bitmap banks, enabling their existing asset policy to export contiguous named
assets. The prior 78 asset/include files remain byte-identical and retained;
these seven assets are additional native exports of original bytes. Tail
classification is a separate subsequent action slice.

A subsequent fresh tail query exposed two value-only EQU uses whose numeric
addresses had inherited source offsets from a suppressed load view:
`UI_HIT_BACKGROUND_STORAGE` at `$77D00` and `WORK_BUFFER_PALETTE_INPUT_BASE` at
`$77FE0`. The planner now retains the named value references with NULL source
targets. A value equate does not itself assert a source-byte identity. Two new
cases cover plain and explicitly runtime-only equates coinciding with real file
bytes. This keeps the distinction between address reuse and consumption of
original unpacked contents; it does not erase the runtime references.

These scratch addresses lie within the original unpacked tail's RAM window
`$75370..$7C000`. Their known later workspace roles do not establish preservation
or consumption of its initial bytes. The fixed-copy destination's tail spelling
`$65370..$6C000` is a rendered view, not the original unpack storage location.
All 812 native checks and 100 affected representation/asset Python checks pass
after this extension; the earlier 306-case run remains the broader baseline.

Reproduce focused checks from the repository root:

```sh
make -j4
.venv/bin/python -m pytest -q tests/test_canonical_source_symbol.py tests/test_absolute_operand_symbol_catalog.py tests/test_manual_representation_storage.py tests/test_source_package.py tests/test_source_package_publish.py -m 'not real_integration'
src/build/m68k_c_unit_tests.exe
```

Final preflight hardening also passes every new symbol presentation through the
native policy codec before atomic append. A non-source generated EQU declaration
must not be assumed to belong to the native platform-symbol registry. The
additional conservative fixture verifies that an unsupported generated EQU
refuses without changing history. The final focused run passes **309 Python
checks**, including **17 new cases**, with **812 native checks** passing.

The full tail audit exposed the remaining presentation mismatch: source analysis
retains labels at `$57D00`, `$57FDE` and `$57FE0`, while the final source plan emits
none of them. Those analysis-only boundaries still rejected the opaque owner
and caused unclassified raw fallback rows, preventing export. The final render
now uses planned declaration boundaries; the earlier pointer-planning pass
remains conservative. Accepted code, relocations, anchors, structured owners and
actual emitted labels remain guards. No analysis label or legacy annotation was
removed. A copied bootstrap feeding a runtime-only blitter-source address
reproduces the failure before this correction and exports the exact opaque
bytes afterwards. Both small and full-tail-size raw ranges are covered.

The completed slice passes **311 focused Python checks**, including 19 new
cases, and **812 native checks**. The final copied-bootstrap case also asserts
that the analysis label remains recorded after its presentation stops blocking
asset export. Full Pandora C/vasm reconstruction is exact under receipt
`0c11b57ba11fc0b92b6f84e360120cd3463aac16b314fef724d9b3b832bdd0b2`.
Changed C lines have no new style findings. The generated source and artifact
sizes are audited in `pandora-tail-asset.json`; no PR metadata was updated.
