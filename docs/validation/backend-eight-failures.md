# Optional backend failures: complete pre-change comparison

These eight cases were exposed by expanding into `tests/test_c_backend.py` with
`-m ''`. They were outside the earlier green focused selections. The default
configuration excludes `integration` and `real_integration`; this file is marked
`c_backend`/`integration`, and `test_real_dll_` cases are also real integration.
A green applicable selection did not assert that this optional file was green.

The initial comparison replaced only the renderer while retaining other current
objects. That isolated renderer effects but was not a complete baseline. A
stronger follow-up archived **all tracked native sources at `ffae9904`**, compiled
them in an isolated directory using the same installed Linux toolchain, and ran
exactly these eight unchanged test bodies through the existing DLL-root override.
All eight fail at the same assertions/errors as the current backend. Source
identity, complete baseline commit, library hash and exact selection are in
`backend-eight-baseline.json`. The earlier mixed-object result is superseded as
the basis for the pre-change claim. No changed-code regression among these eight
was found. No production code or test expectations were changed by this audit.

All names below have the exact prefix `tests/test_c_backend.py::`.

| Test | Actual failure and practical impact |
|---|---|
| `test_full_listing_runtime_copy_storage_alias_precedes_runtime_org` | Expects `lea.l loc_0_00000020-(*+2)(pc),a0`; actual is `lea.l loc_0_00000020(pc),a0`. Its two policy views are suppressed and the absolute JMP remains numeric. This is a code-promotion/old presentation-expectation case: a source-only entry outside either nonidentity policy view does not establish runtime entry lineage. The test cannot currently exercise its intended storage-alias-before-ORG behavior. |
| `test_full_listing_contained_runtime_view_does_not_emit_second_org` | ORG deduplication and both symbolic JMP assertions pass; the test then expects NOP/RTS at runtime `$84`, while the body remains `dc.b $4E,$71,$4E,$75`. Address mapping does not itself establish accepted execution. The source-only seeds lack established runtime entry lineage under the earlier conservative promotion gate. Mapping presentation works; code promotion is withheld. |
| `test_real_dll_runtime_absolute_raw_binary_materializes_runtime_load_range` | Exact dictionary equality rejects the additional native `provenance: 0` and `use_mask: 0` fields. Section, offset, length, runtime address and name match. This is a stale expected wire shape, not evidence of an incorrect load address or failed materialization. |
| `test_listing_artifact_runtime_observation_view_maps_pc_without_source_view` | Runtime PC lookup returns a row, but expects obsolete stable key `s0:00000000:instruction:0`; the canonical key is `s0:00000000:instruction`. Mapping succeeded; the identifier-format assertion is stale. `platform_file_json.c` constructs the key without the display ordinal. |
| `test_real_dll_epic_runtime_absolute_raw_source_keeps_single_load_org` | Missing `targets/amiga_disk_epic-1992-ocean-disk-1/targets/amiga_raw_bootloader_stage_1/binary.bin`. The test stops before native analysis; Epic's load/ORG behavior is untested in this environment. |
| `test_real_dll_ice_bootloader_stage_recovers_copied_runtime_payload_without_bad_addend` | Missing `targets/amiga_disk_ice-1991-06-28-the-silents/targets/amiga_raw_bootloader_stage_1/binary.bin`. It stops before native analysis; ICE copy/addend recovery is untested here. |
| `test_real_dll_runtime_ref_to_copied_range_start_seeds_org_entry_code` | Expects RTS code at source `$10`; actual bytes remain data and the discovered `$400` copy is suppressed. The fixture copies a WORD and returns; it never branches/calls into the copied payload. `facts_runtime_ref_targets_range_start` requires branch-target/control-target evidence; a LEA destination pointer does not qualify. The old automatic code-seeding expectation conflicts with that conservative rule. |
| `test_real_dll_magicland_org_bootstrap_decodes_copied_runtime_entry` | Missing `resources/platform_amiga/Magicland Dizzy (1991)(Codemasters)[cr TRSI][t +2 LSD].zip`. It stops during input resolution, so Magicland bootstrap recovery is untested here. |

The conservative source-only entry gate predates this task: commit `cd00a27b`,
recorded in `pandora-entry-lineage-refusal.md`. Relevant implementation paths are
`runtime_unphased_absolute_control`, `seed_facts_from_object`, and
`facts_runtime_ref_targets_range_start` in `m68k_analysis_facts_v2.c`. Source-only
entry points in nonidentity executable policy domains must not silently become
proof of runtime execution. Whether the first two older tests should declare a
proved runtime entry or explicitly assert refusal is a separate test-contract
reconciliation, not a reason to weaken the gate. The third copy test needs actual
control evidence if its intended claim is code seeding. The two wire-shape
expectations can be refreshed separately. No missing proprietary inputs were
retrieved or copied to make corpus tests appear green.

## Copied-call defect fixed in the published task

For Pandora source `$576`, the encoded JSR address is `$5AFFA`. Native CFG
resolution already maps it to source `$4AFFA` in the copied `$10000` view.
`attach_runtime_address_ref_symbols` also attaches that canonical coordinate to
the operand. The bug came later: `plan_rendered_instruction_symbol_accesses`
preferred `candidate_control_target_for_operand`, whose original decode target
was source `$5AFFA`, over the resolved operand identity. That mismatched access
fed `append_rendered_instruction_expression`; `derive_rendered_pointer_declarations`
formatted the wrong source target under the `$10000` rendering view, requiring
phantom declaration `$6AFFA`. The actual call operand and CFG were already right;
the reference/declaration planner was wrong.

The fix prioritizes the attached operand's section/offset. Thus the operand,
public reference query, required declaration and existing CFG agree on source
`$4AFFA`, named `initialize_player_and_fixed_animation_nodes`. It does not retarget
the CFG to match a string or erase raw decode evidence. Value-only EQU references
also no longer inherit coincident source targets. Retained analysis-only labels
remain evidence but do not split rendering unless present in the final source
plan; real emitted labels, code, relocations and ownership boundaries still guard
extraction. New synthetic regressions demonstrate the old phantom declaration
and hidden-boundary asset failure, then the corrected behavior with retained
analysis evidence. Pandora still reconstructs every original byte exactly.
