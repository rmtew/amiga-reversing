from src.scripts.target_usage_manifest import (
    CODE_START_REASON_CONTROL_TARGET,
    CODE_START_REASON_PLATFORM_LOADSEG_ENTRY,
    ORPHAN_CODE_SIGNAL_STATUS_UNRESOLVED,
    XREF_KIND_ABSOLUTE_ADDRESS_RANGE,
    XREF_KIND_ACCEPTED_CODE_RUN,
    XREF_KIND_ADDRESS_IDENTITY,
    XREF_KIND_ADDRESS_OBSERVATION,
    XREF_KIND_CODE_ORIGIN,
    XREF_KIND_CODE_START_REF,
    XREF_KIND_DATA_REFERENCE,
    XREF_KIND_PLATFORM_ADDRESS_USE,
    XREF_KIND_RANGE_OWNERSHIP,
    XREF_KIND_RUNTIME_ADDRESS_REF,
    XREF_KIND_SOURCE_QUALITY_DIAGNOSTIC,
    XREF_KIND_TABLE_CONSUMER,
    XREF_KIND_TABLE_DESCRIPTOR,
    XREF_KIND_TABLE_ENTRY,
    FeatureBag,
    _add_analysis_features,
    _add_listing_features,
    _analysis_xrefs,
    _listing_xrefs,
)


def test_runtime_copied_entry_stub_feature_and_xref() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "runtime_views": [
                    {
                        "storage_address": 0x52,
                        "storage_offset": 0x52,
                        "runtime_address": 0x100,
                        "kind": 2,
                    },
                    {
                        "storage_address": 0x5C,
                        "storage_offset": 0x5C,
                        "runtime_address": 0x5BFF0,
                        "kind": 2,
                    },
                ],
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, _examples, tags = bag.row_features()

    assert counts["runtime:copied_code"] == 2
    assert counts["runtime:copied_entry_stub"] == 1
    assert "runtime:copied_entry_stub" in tags

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {(0, 0x52): (7, "s0:00000052:instruction:7", "subq.l #1,d7")}
    xrefs = _analysis_xrefs(row, analysis, row_locations)

    copied_entry_xrefs = [xref for xref in xrefs if xref["feature"] == "runtime:copied_entry_stub"]
    assert len(copied_entry_xrefs) == 1
    assert copied_entry_xrefs[0]["offset"] == 0x52
    assert copied_entry_xrefs[0]["value"] == 0x100


def test_decompression_payload_role_features() -> None:
    analysis = {
        "derived_target_suggestions": [
            {
                "kind_id": 1,
                "kind": "decompressed_payload",
                "status_id": 2,
                "status": "materializable",
                "reason_id": 3,
                "reason": "initial_control_target_validated_runtime_copy",
                "source_section": 0,
                "source_section_offset": 0x4C40,
                "packed_size": 168391,
                "decompressed_size": 359600,
                "load_address": 0x4000,
                "entrypoint": 0x4000,
                "runtime_copy_address": 0x4000,
                "runtime_copy_size": 168396,
                "runtime_copy_kind": 3,
            }
        ],
        "decompression_events": [
            {
                "event_kind_id": 1,
                "event_kind": "decompression",
                "event_id": "decompression:section:0:00004C40:rnc1-old",
                "status_id": 2,
                "status": "materializable",
                "reason_id": 3,
                "reason": "initial_control_target_validated_runtime_copy",
                "codec_id": "rnc1-old",
                "codec_support_id": 1,
                "codec_support": "external_provider",
                "payload_role_id": 2,
                "payload_role": "primary_program",
                "parent_remains_active_id": 0,
                "parent_remains_active": "unknown",
                "source_kind_id": 1,
                "source_kind": "stale_display_name",
                "provider_id": "ancient",
                "simulated_output_size": 128,
                "simulated_output_sha256": "d37ec7db83012eba179956026b0677cfd46763d585722154f761bd6f6d2b5748",
                "source_section": 0,
                "source_section_offset": 0x4C40,
                "packed_size": 168391,
                "decompressed_size": 359600,
                "load_address": 0x4000,
                "entrypoint": 0x4000,
            }
        ],
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["decompression:payload_role:primary_program"] == 1
    assert counts["decompression:parent_remains_active:unknown"] == 1
    assert counts["decompression:event:decompression"] == 1
    assert counts["decompression:has_event_id"] == 1
    assert counts["decompression:codec_support:external_provider"] == 1
    assert counts["decompression:source_kind:section_range"] == 1
    assert counts["decompression:provider:ancient"] == 1
    assert counts["decompression:codec:rnc1-old"] == 1
    assert counts["decompression:simulated_output"] == 1
    assert counts["decompression:simulated_output_hash"] == 1
    assert counts["decompression:source_section"] == 2
    assert counts["decompression:source_section:0"] == 2
    assert counts["decompression:source_offset"] == 2
    assert counts["decompression:source_offset:0:00004C40"] == 2
    assert counts["decompression:source_range"] == 2
    assert counts["decompression:source_range:0:00004C40-0002DE07"] == 2
    assert counts["decompression:packed_size"] == 2
    assert counts["decompression:output_load_address"] == 2
    assert counts["decompression:output_load_address:00004000"] == 2
    assert counts["decompression:entrypoint"] == 2
    assert counts["decompression:entrypoint:00004000"] == 2
    assert counts["decompression:pattern:runtime_copy_to_absolute"] == 1
    assert "decompression:payload_role:primary_program" in tags
    assert examples["decompression:payload_role:primary_program"][0]["payload_role"] == "primary_program"
    assert examples["decompression:source_kind:section_range"][0]["source_kind"] == "section_range"
    assert examples["decompression:provider:ancient"][0]["provider_id"] == "ancient"
    assert examples["decompression:has_event_id"][0]["event_id"] == "decompression:section:0:00004C40:rnc1-old"
    assert examples["decompression:source_range"][0]["source_section_end_offset"] == 0x2DE07


def test_recognized_unpacker_target_start_indexes_absolute_depack_destination() -> None:
    analysis = {
        "decompression_events": [
            {
                "event_kind_id": 1,
                "event_kind": "decompression",
                "event_id": "decompression:recognized_unpacker:section:1:000000C4:tetragon",
                "status_id": 2,
                "status": "materializable",
                "reason_id": 9,
                "reason": "native_tetragon_unpack_validated",
                "codec_id": "tetragon",
                "codec_support_id": 2,
                "codec_support": "native_decompressor",
                "payload_role_id": 2,
                "payload_role": "primary_program",
                "parent_remains_active_id": 1,
                "parent_remains_active": "false",
                "source_kind_id": 2,
                "source_kind": "recognized_unpacker",
                "provider_id": "c-tetragon-signature",
                "source_section": 1,
                "source_section_offset": 0x100,
                "compressed_source_section_offset": 0x100,
                "compressed_source_section_end_offset": 0x428,
                "unpacker_marker_offset": 0xC4,
                "target_start_address": 0x40000,
                "target_end_address": 0x50000,
                "entrypoint": 0x40000,
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, _examples, tags = bag.row_features()

    assert counts["absolute-depack-dest"] == 1
    assert counts["decompressed-entrypoint"] == 1
    assert counts["decompression:output_load_address:00040000"] == 1
    assert counts["decompression:entrypoint:00040000"] == 1
    assert counts["decompression:pattern:recognized_unpacker"] == 1
    assert counts["decompression:pattern:recognized_unpacker:tetragon"] == 1
    assert counts["decompression:codec:tetragon"] == 1
    assert counts["decompression:source_range:1:00000100-00000428"] == 1
    assert counts["decompression:compressed_source_range:1:00000100-00000428"] == 1
    assert counts["decompression:unpacker_marker:1:000000C4"] == 1
    assert "absolute-depack-dest" in tags

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {(1, 0x100): (12, "s1:00000100:data:12", "dc.b $00")}
    xrefs = _analysis_xrefs(row, analysis, row_locations)
    assert any(xref["feature"] == "absolute-depack-dest" and xref["row_index"] == 12 for xref in xrefs)
    assert any(xref["feature"] == "decompression:codec:tetragon" and xref["row_index"] == 12 for xref in xrefs)
    assert any(xref["feature"] == "decompression:source_range:1:00000100-00000428" for xref in xrefs)
    assert any(xref["feature"] == "decompression:unpacker_marker:1:000000C4" for xref in xrefs)


def test_self_decrunch_event_indexes_output_and_pattern_work_item() -> None:
    analysis = {
        "decompression_events": [
            {
                "event_kind_id": 1,
                "event_kind": "decompression",
                "event_id": "decompression:self_decrunch:section:0:00000000:00020000",
                "status_id": 4,
                "status": "needs_simulated_decrunch",
                "reason_id": 14,
                "reason": "simulated_instruction_limit",
                "codec_id": "unknown-self-decrunch",
                "codec_support_id": 3,
                "codec_support": "simulator_required",
                "payload_role_id": 1,
                "payload_role": "unknown_runtime_payload",
                "parent_remains_active_id": 1,
                "parent_remains_active": "false",
                "source_kind_id": 3,
                "source_kind": "self_decruncher",
                "provider_id": "m68k-sim-decrunch",
                "decompressor_code_section": 0,
                "decompressor_entry_offset": 0,
                "load_address": 0x20000,
                "entrypoint": 0x20000,
                "simulated_output_size": 44220,
                "simulated_output_sha256": "21ea11a46f008c69cca2795347eca093967191bf535b33c5ff3777619161999d",
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["decompression:pattern:absolute_self_decrunch_transfer"] == 1
    assert counts["decompression:pattern:simulated_self_decrunch_output"] == 1
    assert counts["decompression:output_load_address:00020000"] == 1
    assert counts["decompression:entrypoint:00020000"] == 1
    assert counts["decompression:decompressor_code"] == 1
    assert counts["decompression:decompressor_entry:0:00000000"] == 1
    assert counts["decompression:unmaterialized_work_item"] == 1
    assert counts["decompression:work_item_reason:simulated_instruction_limit"] == 1
    assert "decompression:pattern:absolute_self_decrunch_transfer" in tags
    assert examples["decompression:output_load_address:00020000"][0]["load_address"] == 0x20000
    assert examples["decompression:decompressor_code"][0]["decompressor_entry_offset"] == 0

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {(0, 0): (2, "s0:00000000:instruction:2", "lea.l $20000,a0")}
    xrefs = _analysis_xrefs(row, analysis, row_locations)
    assert any(
        xref["feature"] == "decompression:pattern:absolute_self_decrunch_transfer" and xref["row_index"] == 2
        for xref in xrefs
    )
    assert any(xref["feature"] == "decompression:output_load_address:00020000" for xref in xrefs)
    assert any(xref["feature"] == "decompression:decompressor_entry:0:00000000" for xref in xrefs)


def test_labelized_table_shape_features_and_xrefs() -> None:
    listing = {
        "rows": [
            {
                "kind": "data",
                "kind_id": 4,
                "section_index": 0,
                "start_offset": 0x3526,
                "stable_key": "s0:00003526:data:1",
                "text": "\tdc.w abs_0_0000355C-abs_0_0000355C,abs_0_0000356A-abs_0_0000355C\t; lookup_table\n",
                "data_class": "lookup_table",
                "data_class_flags": 8,
            },
            {
                "kind": "data",
                "kind_id": 4,
                "section_index": 0,
                "start_offset": 0x7D44,
                "stable_key": "s0:00007D44:data:1",
                "text": "\tdc.l abs_0_00007CA0,abs_0_00007CA6,$00000000,abs_0_00007CD6\t; lookup_table\n",
                "data_class": "lookup_table",
                "data_class_flags": 8,
            },
            {
                "kind": "data",
                "kind_id": 4,
                "section_index": 0,
                "start_offset": 0xC266,
                "stable_key": "s0:0000C266:data:1",
                "text": "\tdc.l abs_0_0000C53C\t; pointer_table\n",
                "data_class": "pointer_table",
                "data_class_flags": 4,
            },
            {
                "kind": "label",
                "kind_id": 2,
                "section_index": 0,
                "start_offset": 0xDDBA,
                "stable_key": "s0:0000DDBA:label:1",
                "text": "loc_0_0000DDBA:",
                "data_class": "string",
                "data_class_flags": 128,
            },
        ]
    }
    bag = FeatureBag()
    _add_listing_features(listing, bag)
    counts, _examples, tags = bag.row_features()

    assert counts["analysis:lookup_table:word_relative_labels"] == 1
    assert counts["analysis:lookup_table:long_label_entries"] == 1
    assert counts["analysis:pointer_table:long_label_entries"] == 1
    assert "data:string" not in counts
    assert "analysis:lookup_table:word_relative_labels" in tags

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    xrefs = _listing_xrefs(row, listing, feature_bag=FeatureBag())
    features = {xref["feature"] for xref in xrefs}

    assert "analysis:lookup_table:word_relative_labels" in features
    assert "analysis:lookup_table:long_label_entries" in features
    assert "analysis:pointer_table:long_label_entries" in features
    assert "data:string" not in features


def test_orphan_missing_inbound_uses_status_id_for_actionable_queue() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "orphan_code_signals": [
                    {
                        "offset": 0x40,
                        "size": 6,
                        "reason_id": 1,
                        "status_id": ORPHAN_CODE_SIGNAL_STATUS_UNRESOLVED,
                        "missing_inbound_id": 6,
                        "terminal_flow_kind": 5,
                    },
                    {
                        "offset": 0x80,
                        "size": 6,
                        "reason_id": 1,
                        "status_id": 3,
                        "status": "unresolved",
                        "missing_inbound_id": 6,
                        "terminal_flow_kind": 5,
                    },
                    {
                        "offset": 0xC0,
                        "size": 6,
                        "reason_id": 1,
                        "status_id": ORPHAN_CODE_SIGNAL_STATUS_UNRESOLVED,
                        "missing_inbound_id": 1,
                        "terminal_flow_kind": 5,
                    },
                    {
                        "offset": 0x100,
                        "size": 6,
                        "reason_id": 1,
                        "status_id": ORPHAN_CODE_SIGNAL_STATUS_UNRESOLVED,
                        "missing_inbound_id": 8,
                        "terminal_flow_kind": 5,
                    },
                ],
            }
        ],
        "orphan_code_signal_count": 4,
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, _examples, tags = bag.row_features()

    assert counts["orphan-code:missing_inbound:api"] == 1
    assert "orphan-code:missing_inbound:unknown" not in counts
    assert "orphan-code:missing_inbound:policy_seed" not in counts
    assert "target-pattern:orphan_missing_api" in tags
    assert "target-pattern:orphan_missing_unknown" not in tags
    assert "target-pattern:orphan_missing_policy_seed" not in tags

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    features = {xref["feature"] for xref in _analysis_xrefs(row, analysis, {})}
    assert "orphan-code:missing_inbound:api" in features
    assert "orphan-code:missing_inbound:unknown" not in features
    assert "orphan-code:missing_inbound:policy_seed" not in features


def test_source_quality_diagnostics_feature_and_xref() -> None:
    analysis = {
        "source_quality_diagnostics": [
            {
                "section_index": 0,
                "offset": 0x42C00,
                "kind": "unterminated_or_invalid_code_range",
                "origin": "auto_analysis",
                "length": 12,
                "summary": "accepted code has no terminal proof",
            }
        ],
        "sections": [
            {
                "section_index": 0,
                "source_quality_diagnostics": [
                    {
                        "offset": 0x74,
                        "kind": "platform_name_without_use_shape",
                        "platform_use_shape": "low_memory_base",
                        "owner_kind": "low_ram",
                        "related_address": 0x74,
                    }
                ],
            }
        ],
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["diagnostic:source_quality"] == 2
    assert counts["source-quality:diagnostic"] == 2
    assert counts["source-quality:kind:unterminated_or_invalid_code_range"] == 1
    assert counts["source-quality:kind:platform_name_without_use_shape"] == 1
    assert counts["source-quality:origin:auto_analysis"] == 1
    assert counts["source-quality:owner:low_ram"] == 1
    assert counts["source-quality:platform_use:low_memory_base"] == 1
    assert "source-quality:diagnostic" in tags
    assert "target-pattern:source_quality_false_code" in tags
    assert "target-pattern:source_quality_platform_semantics" in tags
    assert examples["source-quality:kind:unterminated_or_invalid_code_range"][0]["length"] == 12

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {
        (0, 0x42C00): (10, "s0:00042C00:instruction:10", "\tori.b #0,d0"),
        (0, 0x74): (11, "s0:00000074:instruction:11", "\tlea.l $74.w,a2"),
    }
    xrefs = _analysis_xrefs(row, analysis, row_locations)

    accepted_xrefs = [
        xref for xref in xrefs if xref["feature"] == "source-quality:kind:unterminated_or_invalid_code_range"
    ]
    assert len(accepted_xrefs) == 1
    assert accepted_xrefs[0]["kind_id"] == XREF_KIND_SOURCE_QUALITY_DIAGNOSTIC
    assert accepted_xrefs[0]["row_index"] == 10
    assert accepted_xrefs[0]["value"] == 12
    assert accepted_xrefs[0]["text"] == "\tori.b #0,d0"

    base_xrefs = [xref for xref in xrefs if xref["feature"] == "source-quality:platform_use:low_memory_base"]
    assert len(base_xrefs) == 1
    assert base_xrefs[0]["offset"] == 0x74
    assert base_xrefs[0]["value"] == 0x74


def test_source_quality_precursor_target_patterns_are_derived_from_existing_features() -> None:
    bag = FeatureBag()
    bag.add("orphan-code:context:accepted_code_boundary", example={"offset": 0x100})
    bag.add("orphan-code:context:renderable_label", example={"offset": 0x200})
    bag.add("label:definition_without_reference", example={"offset": 0x220})
    bag.add("memory-layout-view:absolute_owner:cpu_vector", example={"address": 0x74})
    bag.add("memory-layout-view:absolute_unowned_one_off", example={"address": 0x70000})
    bag.add("runtime:copied_code", example={"offset": 0x300})
    bag.add("table:source_pattern:indexed_local_pointer_read", example={"offset": 0x400})
    counts, examples, tags = bag.row_features()

    assert counts["target-pattern:source_quality_precursor_false_code"] == 1
    assert counts["target-pattern:source_quality_precursor_label_consistency"] == 1
    assert counts["target-pattern:source_quality_precursor_platform_semantics"] == 1
    assert counts["target-pattern:source_quality_precursor_unowned_range"] == 1
    assert counts["target-pattern:source_quality_precursor_runtime_identity"] == 1
    assert counts["target-pattern:source_quality_precursor_table_range"] == 1
    assert "target-pattern:source_quality_precursor_false_code" in tags
    assert (
        examples["target-pattern:source_quality_precursor_platform_semantics"][0]["evidence_feature"]
        == "memory-layout-view:absolute_owner:cpu_vector"
    )
    assert (
        examples["target-pattern:source_quality_precursor_unowned_range"][0]["evidence_feature"]
        == "memory-layout-view:absolute_unowned_one_off"
    )


def test_memory_layout_sparse_unowned_absolute_refs_are_indexed_as_precursors() -> None:
    analysis = {
        "memory_layout_records": [
            {
                "section_index": 0,
                "record_kind_id": 8,
                "owner_kind_id": 7,
                "address": 0x5FFFC,
                "access_width": 0,
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["memory-layout-view:absolute_unowned_refs"] == 1
    assert counts["memory-layout-view:absolute_unowned_one_off"] == 1
    assert "memory-layout-view:absolute_unowned_sparse" not in counts
    assert "target-pattern:source_quality_precursor_unowned_range" in tags
    assert examples["memory-layout-view:absolute_unowned_one_off"][0]["absolute_ref_count"] == 1


def test_memory_layout_absolute_owner_access_shape_is_indexed() -> None:
    analysis = {
        "memory_layout_records": [
            {
                "section_index": 0,
                "source_offset": 0x100,
                "record_kind_id": 8,
                "owner_kind_id": 2,
                "owner_kind": "cpu_vector",
                "address": 0x6C,
                "access": "memory_write",
                "access_width": 4,
            },
            {
                "section_index": 0,
                "source_offset": 0x120,
                "record_kind_id": 8,
                "owner_kind_id": 2,
                "owner_kind": "cpu_vector",
                "address": 0x74,
                "access": "address",
                "access_width": 0,
            },
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["memory-layout:access:memory_write"] == 1
    assert counts["memory-layout:access:address"] == 1
    assert counts["memory-layout:owner_access:cpu_vector:memory_write"] == 1
    assert counts["memory-layout:owner_access:cpu_vector:address"] == 1
    assert counts["memory-layout-view:absolute_owner_access:cpu_vector:memory_write"] == 1
    assert counts["memory-layout-view:absolute_owner_access:cpu_vector:address"] == 1
    assert examples["memory-layout:owner_access:cpu_vector:address"][0]["address"] == 0x74
    assert "memory-layout:owner_access:cpu_vector:address" in tags


def test_listing_navigation_labels_without_references_are_indexed_as_precursors() -> None:
    listing = {
        "labels": [
            {
                "addr": 0x42C00,
                "section_index": 0,
                "row_index": 10,
                "stable_key": "s0:00042C00:label:10",
                "symbol": "abs_0_00042C00",
                "access_counts": {"definition": 1},
            },
            {
                "addr": 0x43080,
                "section_index": 0,
                "row_index": 11,
                "symbol": "abs_0_00043080",
                "access_counts": {"definition": 1, "reference": 4},
            },
        ],
        "rows": [],
    }
    bag = FeatureBag()
    _add_listing_features(listing, bag)
    counts, examples, tags = bag.row_features()

    assert counts["label:definition_without_reference"] == 1
    assert examples["label:definition_without_reference"][0]["symbol"] == "abs_0_00042C00"
    assert "target-pattern:source_quality_precursor_label_consistency" in tags


def test_analysis_code_start_refs_are_indexed_for_origin_search() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 2,
                "code_start_refs": [
                    {
                        "offset": 0x42C00,
                        "reason": CODE_START_REASON_CONTROL_TARGET,
                        "reason_name": "control_target",
                        "confidence": 3,
                        "source_section_index": 2,
                        "source_offset": 0x41000,
                        "runtime_address": 0x43C00,
                        "size": 12,
                    }
                ],
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["analysis:code_start_ref"] == 1
    assert counts["analysis:code_start_reason:control_target"] == 1
    assert counts["analysis:code_start_runtime_address"] == 1
    assert counts["analysis:code_start_confidence:3"] == 1
    assert examples["analysis:code_start_reason:control_target"][0]["runtime_address"] == 0x43C00
    assert "analysis:code_start_ref" in tags

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    xrefs = _analysis_xrefs(row, analysis, {})
    code_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:code_start_reason:control_target"]
    assert len(code_xrefs) == 1
    assert code_xrefs[0]["kind_id"] == XREF_KIND_CODE_START_REF
    assert code_xrefs[0]["section"] == 2
    assert code_xrefs[0]["offset"] == 0x42C00


def test_analysis_accepted_code_runs_are_indexed_for_false_code_search() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "accepted_code_runs": [
                    {
                        "start_offset": 0x42C00,
                        "end_offset": 0x42C74,
                        "terminal_offset": 0x42C70,
                        "end_kind": "data_span",
                        "weakest_origin_class": "weak_shape_only",
                        "instruction_count": 29,
                        "detail": "falls through into data",
                    }
                ],
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["analysis:accepted_code_run"] == 1
    assert counts["analysis:accepted_code_run_end:data_span"] == 1
    assert counts["analysis:accepted_code_run_origin:weak_shape_only"] == 1
    assert counts["analysis:accepted_code_run:suspicious_end"] == 1
    assert "target-pattern:source_quality_false_code" in tags
    assert examples["analysis:accepted_code_run:suspicious_end"][0]["end_offset"] == 0x42C74

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {(0, 0x42C00): (10, "s0:00042C00:instruction:10", "\tori.b #0,d0")}
    xrefs = _analysis_xrefs(row, analysis, row_locations)
    accepted_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:accepted_code_run:suspicious_end"]
    assert len(accepted_xrefs) == 1
    assert accepted_xrefs[0]["kind_id"] == XREF_KIND_ACCEPTED_CODE_RUN
    assert accepted_xrefs[0]["row_index"] == 10
    assert accepted_xrefs[0]["symbol"] == "data_span"
    assert accepted_xrefs[0]["value"] == 0x42C74


def test_analysis_code_origins_are_indexed_for_false_code_search() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "code_origins": [
                    {
                        "offset": 0x6098,
                        "length": 8,
                        "origin_class": "weak_shape_only",
                        "evidence_kind": "table_value_only",
                        "reason_name": "control_target",
                        "detail": "address-like table value is not executable proof",
                    }
                ],
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["analysis:code_origin"] == 1
    assert counts["analysis:code_origin_class:weak_shape_only"] == 1
    assert counts["analysis:code_origin_evidence:table_value_only"] == 1
    assert counts["analysis:code_origin:weak"] == 1
    assert "target-pattern:source_quality_false_code" in tags
    assert examples["analysis:code_origin:weak"][0]["length"] == 8

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {(0, 0x6098): (11, "s0:00006098:instruction:11", "\tori.w #112,$0(a0,d0.w)")}
    xrefs = _analysis_xrefs(row, analysis, row_locations)
    origin_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:code_origin:weak"]
    assert len(origin_xrefs) == 1
    assert origin_xrefs[0]["kind_id"] == XREF_KIND_CODE_ORIGIN
    assert origin_xrefs[0]["section"] == 0
    assert origin_xrefs[0]["offset"] == 0x6098
    assert origin_xrefs[0]["row_index"] == 11
    assert origin_xrefs[0]["symbol"] == "weak_shape_only"
    assert origin_xrefs[0]["value"] == 8


def test_analysis_address_identities_are_indexed_for_identity_search() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "address_identities": [
                    {
                        "identity_id": 3,
                        "source_offset": 0x42C6C,
                        "absolute_address": 0x42C6C,
                        "runtime_address": 0x42C6C,
                        "owner_kind": "runtime_range",
                        "role_kind": "storage",
                        "conflict_state": "code_data",
                        "conflict_count": 1,
                        "detail": "absolute storage overlaps accepted code",
                    }
                ],
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["analysis:address_identity"] == 1
    assert counts["analysis:address_identity_owner:runtime_range"] == 1
    assert counts["analysis:address_identity_role:storage"] == 1
    assert counts["analysis:address_identity_conflict:code_data"] == 1
    assert counts["analysis:address_identity:runtime"] == 1
    assert counts["analysis:address_identity:conflict"] == 1
    assert "target-pattern:source_quality_address_identity" in tags
    assert examples["analysis:address_identity:conflict"][0]["absolute_address"] == 0x42C6C

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {(0, 0x42C6C): (14, "s0:00042C6C:data:14", "\tdc.w $0000")}
    xrefs = _analysis_xrefs(row, analysis, row_locations)
    identity_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:address_identity:conflict"]
    assert len(identity_xrefs) == 1
    assert identity_xrefs[0]["kind_id"] == XREF_KIND_ADDRESS_IDENTITY
    assert identity_xrefs[0]["section"] == 0
    assert identity_xrefs[0]["offset"] == 0x42C6C
    assert identity_xrefs[0]["row_index"] == 14
    assert identity_xrefs[0]["symbol"] == "runtime_range"
    assert identity_xrefs[0]["value"] == 0x42C6C


def test_analysis_range_facts_are_indexed_for_range_search() -> None:
    analysis = {
        "absolute_address_ranges": [
            {
                "start_address": 0x459BA,
                "range_size": 4,
                "owner_kind": "absolute_memory",
                "status": "unowned_sparse",
                "access": "memory_write",
                "observation_count": 2,
                "source_section_index": 0,
                "source_offset": 0x43000,
            }
        ],
        "sections": [
            {
                "section_index": 0,
                "range_ownerships": [
                    {
                        "start_offset": 0x6098,
                        "end_offset": 0x60A0,
                        "kind_name": "conflict",
                        "status_name": "conflict",
                        "source_pattern": "pc_relative_indexed_read",
                        "table_kind": "pointer_table",
                        "negative_evidence_flags": 1,
                        "conflict_state_name": "code_overlap",
                    }
                ],
            }
        ],
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["analysis:range_ownership"] == 1
    assert counts["analysis:range_ownership_kind:conflict"] == 1
    assert counts["analysis:range_ownership_status:conflict"] == 1
    assert counts["analysis:range_ownership_source_pattern:pc_relative_indexed_read"] == 1
    assert counts["analysis:range_ownership_table_kind:pointer_table"] == 1
    assert counts["analysis:range_ownership:negative_evidence"] == 1
    assert counts["analysis:absolute_address_range"] == 1
    assert counts["analysis:absolute_address_range_owner:absolute_memory"] == 1
    assert counts["analysis:absolute_address_range_status:unowned_sparse"] == 1
    assert counts["analysis:absolute_address_range_access:memory_write"] == 1
    assert counts["analysis:absolute_address_range:unowned_sparse"] == 1
    assert "target-pattern:source_quality_unowned_range" in tags
    assert examples["analysis:range_ownership:negative_evidence"][0]["end_offset"] == 0x60A0

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {
        (0, 0x6098): (30, "s0:00006098:data:30", "\tdc.l loc_0_00006098"),
        (0, 0x43000): (31, "s0:00043000:instruction:31", "\tmove.l d0,$000459BA.l"),
    }
    xrefs = _analysis_xrefs(row, analysis, row_locations)
    range_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:range_ownership:negative_evidence"]
    absolute_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:absolute_address_range:unowned_sparse"]
    assert len(range_xrefs) == 1
    assert range_xrefs[0]["kind_id"] == XREF_KIND_RANGE_OWNERSHIP
    assert range_xrefs[0]["row_index"] == 30
    assert range_xrefs[0]["value"] == 0x60A0
    assert len(absolute_xrefs) == 1
    assert absolute_xrefs[0]["kind_id"] == XREF_KIND_ABSOLUTE_ADDRESS_RANGE
    assert absolute_xrefs[0]["row_index"] == 31
    assert absolute_xrefs[0]["symbol"] == "absolute_memory"
    assert absolute_xrefs[0]["value"] == 0x459BA


def test_analysis_table_facts_are_indexed_for_table_search() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "table_descriptors": [
                    {
                        "start_offset": 0x6090,
                        "end_offset": 0x60A0,
                        "entry_size": 4,
                        "entry_count": 4,
                        "entry_count_proof": "consumer_structural_scan",
                        "stop_reason": "range_end",
                        "table_kind": "pointer_table",
                        "base_expression": "table_label",
                        "source_pattern": "pc_relative_indexed_read",
                        "status_name": "accepted",
                        "consumer_offset": 0x7000,
                        "target_offset": 0x8000,
                    }
                ],
                "table_consumers": [
                    {
                        "consumer_offset": 0x7000,
                        "table_start_offset": 0x6090,
                        "table_end_offset": 0x60A0,
                        "entry_count": 4,
                        "entry_count_proof": "consumer_structural_scan",
                        "stop_reason": "range_end",
                        "table_kind": "pointer_table",
                        "source_pattern": "pc_relative_indexed_read",
                        "index_register": 0,
                    }
                ],
                "table_entries": [
                    {
                        "table_start_offset": 0x6090,
                        "entry_index": 0,
                        "entry_offset": 0x6090,
                        "entry_size": 4,
                        "raw_value": 0x8000,
                        "table_kind": "pointer_table",
                        "source_pattern": "pc_relative_indexed_read",
                        "target_status_name": "accepted_target",
                        "target_offset": 0x8000,
                    }
                ],
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["analysis:table_descriptor"] == 1
    assert counts["analysis:table_descriptor_kind:pointer_table"] == 1
    assert counts["analysis:table_descriptor_entry_count_proof:consumer_structural_scan"] == 1
    assert counts["analysis:table_descriptor_source_pattern:pc_relative_indexed_read"] == 1
    assert counts["analysis:table_descriptor:consumer"] == 1
    assert counts["analysis:table_descriptor:target"] == 1
    assert counts["analysis:table_consumer"] == 1
    assert counts["analysis:table_consumer_source_pattern:pc_relative_indexed_read"] == 1
    assert counts["analysis:table_consumer:indexed"] == 1
    assert counts["analysis:table_entry"] == 1
    assert counts["analysis:table_entry_target_status:accepted_target"] == 1
    assert counts["analysis:table_entry:target"] == 1
    assert examples["analysis:table_entry:target"][0]["target_offset"] == 0x8000

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {
        (0, 0x6090): (40, "s0:00006090:data:40", "\tdc.l abs_0_00008000"),
        (0, 0x7000): (41, "s0:00007000:instruction:41", "\tmove.l $0(a0,d0.w),a1"),
    }
    xrefs = _analysis_xrefs(row, analysis, row_locations)
    descriptor_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:table_descriptor:consumer"]
    consumer_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:table_consumer:indexed"]
    entry_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:table_entry:target"]
    assert len(descriptor_xrefs) == 1
    assert descriptor_xrefs[0]["kind_id"] == XREF_KIND_TABLE_DESCRIPTOR
    assert descriptor_xrefs[0]["row_index"] == 40
    assert descriptor_xrefs[0]["value"] == 4
    assert len(consumer_xrefs) == 1
    assert consumer_xrefs[0]["kind_id"] == XREF_KIND_TABLE_CONSUMER
    assert consumer_xrefs[0]["row_index"] == 41
    assert consumer_xrefs[0]["value"] == 0x6090
    assert len(entry_xrefs) == 1
    assert entry_xrefs[0]["kind_id"] == XREF_KIND_TABLE_ENTRY
    assert entry_xrefs[0]["row_index"] == 40
    assert entry_xrefs[0]["value"] == 0x8000


def test_analysis_reference_facts_are_indexed_for_observation_search() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "runtime_address_refs": [
                    {
                        "offset": 0x43000,
                        "operand_index": 1,
                        "runtime_address": 0x42C00,
                        "target_offset": 0x42C00,
                        "data_class": "pointer_table",
                        "owner_kind": "runtime_range",
                    }
                ],
                "data_references": [
                    {
                        "source_offset": 0x6090,
                        "source_kind_name": "table_entry",
                        "table_kind": "pointer_table",
                        "source_pattern": "pc_relative_indexed_read",
                        "target_status_name": "accepted_target",
                        "target_offset": 0x8000,
                        "evidence_flags": 3,
                    }
                ],
                "address_observations": [
                    {
                        "offset": 0x43004,
                        "operand_index": 1,
                        "address": 0x42C6C,
                        "access_kind_name": "memory_read",
                        "source_name": "absolute_operand",
                        "identity_id": 9,
                    }
                ],
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["analysis:runtime_address_ref"] == 1
    assert counts["analysis:runtime_address_ref_data_class:pointer_table"] == 1
    assert counts["analysis:runtime_address_ref_owner:runtime_range"] == 1
    assert counts["analysis:runtime_address_ref:runtime"] == 1
    assert counts["analysis:runtime_address_ref:target"] == 1
    assert counts["analysis:data_reference"] == 1
    assert counts["analysis:data_reference_source:table_entry"] == 1
    assert counts["analysis:data_reference_source_pattern:pc_relative_indexed_read"] == 1
    assert counts["analysis:data_reference:target"] == 1
    assert counts["analysis:address_observation"] == 1
    assert counts["analysis:address_observation_access:memory_read"] == 1
    assert counts["analysis:address_observation_source:absolute_operand"] == 1
    assert counts["analysis:address_observation:identity"] == 1
    assert examples["analysis:address_observation:identity"][0]["address"] == 0x42C6C

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {
        (0, 0x43000): (50, "s0:00043000:instruction:50", "\tmovea.l runtime_address_00042C00.l,a3"),
        (0, 0x6090): (51, "s0:00006090:data:51", "\tdc.l abs_0_00008000"),
        (0, 0x43004): (52, "s0:00043004:instruction:52", "\tmove.w $00042C6C.l,d0"),
    }
    xrefs = _analysis_xrefs(row, analysis, row_locations)
    runtime_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:runtime_address_ref:runtime"]
    data_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:data_reference:target"]
    observation_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:address_observation:identity"]
    assert runtime_xrefs[0]["kind_id"] == XREF_KIND_RUNTIME_ADDRESS_REF
    assert runtime_xrefs[0]["row_index"] == 50
    assert runtime_xrefs[0]["value"] == 0x42C00
    assert data_xrefs[0]["kind_id"] == XREF_KIND_DATA_REFERENCE
    assert data_xrefs[0]["row_index"] == 51
    assert data_xrefs[0]["value"] == 0x8000
    assert observation_xrefs[0]["kind_id"] == XREF_KIND_ADDRESS_OBSERVATION
    assert observation_xrefs[0]["row_index"] == 52
    assert observation_xrefs[0]["value"] == 0x42C6C


def test_analysis_platform_address_uses_are_indexed_for_semantic_search() -> None:
    analysis = {
        "platform_address_uses": [
            {
                "section_index": 0,
                "offset": 0x400,
                "address": 0x64,
                "effective_address": 0x64,
                "use_shape": "vector_fill_loop",
                "access": "memory_write",
                "handler_target": 0x41A,
                "detail": "fills exception vectors",
            }
        ],
        "sections": [
            {
                "section_index": 1,
                "platform_address_uses": [
                    {
                        "offset": 0x59484,
                        "address": 0x74,
                        "effective_address": 0x63A8 + 0x74,
                        "use_shape": "low_memory_base",
                        "access_kind": "compute_address",
                        "detail": "vector-range address used as low-memory base",
                    }
                ],
            }
        ],
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, examples, tags = bag.row_features()

    assert counts["analysis:platform_address_use"] == 2
    assert counts["analysis:platform_address_use_shape:vector_fill_loop"] == 1
    assert counts["analysis:platform_address_use_shape:low_memory_base"] == 1
    assert counts["analysis:platform_address_use_access:memory_write"] == 1
    assert counts["analysis:platform_address_use_access:compute_address"] == 1
    assert counts["analysis:platform_address_use:handler_target"] == 1
    assert counts["analysis:platform_address_use:vector_semantic"] == 1
    assert counts["analysis:platform_address_use:low_memory"] == 1
    assert "target-pattern:source_quality_platform_semantics" in tags
    assert examples["analysis:platform_address_use_shape:low_memory_base"][0]["effective_address"] == 0x641C

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {(1, 0x59484): (12, "s1:00059484:instruction:12", "\tlea.l $74.w,a2")}
    xrefs = _analysis_xrefs(row, analysis, row_locations)
    use_xrefs = [
        xref
        for xref in xrefs
        if xref["feature"] == "analysis:platform_address_use_shape:low_memory_base"
    ]
    assert len(use_xrefs) == 1
    assert use_xrefs[0]["kind_id"] == XREF_KIND_PLATFORM_ADDRESS_USE
    assert use_xrefs[0]["section"] == 1
    assert use_xrefs[0]["offset"] == 0x59484
    assert use_xrefs[0]["row_index"] == 12
    assert use_xrefs[0]["symbol"] == "low_memory_base"
    assert use_xrefs[0]["value"] == 0x641C


def test_direct_control_stub_table_feature_and_xref() -> None:
    listing = {
        "rows": [
            {"kind": "label", "kind_id": 2, "section_index": 0, "start_offset": 0x16A, "end_offset": 0x16A, "text": "loc:\n"},
            {
                "kind": "instruction",
                "kind_id": 3,
                "section_index": 0,
                "start_offset": 0x16A,
                "end_offset": 0x16E,
                "stable_key": "stub-a",
                "text": "\tbra.w loc_0_0000021E\n",
                "opcode_or_directive": "bra.w",
                "operand_accesses": ["branch_target"],
                "operand_parts": [{"kind": "symbol", "text": "loc_0_0000021E"}],
                "code_start_refs": [{"reason": CODE_START_REASON_CONTROL_TARGET}],
            },
            {"kind": "label", "kind_id": 2, "section_index": 0, "start_offset": 0x16E, "end_offset": 0x16E, "text": "loc:\n"},
            {
                "kind": "instruction",
                "kind_id": 3,
                "section_index": 0,
                "start_offset": 0x16E,
                "end_offset": 0x172,
                "stable_key": "stub-b",
                "text": "\tbra.w loc_0_00000254\n",
                "opcode_or_directive": "bra.w",
                "operand_accesses": ["branch_target"],
                "operand_parts": [{"kind": "symbol", "text": "loc_0_00000254"}],
                "code_start_refs": [{"reason": CODE_START_REASON_CONTROL_TARGET}],
            },
        ]
    }
    bag = FeatureBag()
    _add_listing_features(listing, bag)
    counts, _examples, tags = bag.row_features()

    assert counts["analysis:direct_control_stub_table"] == 2
    assert "analysis:direct_control_stub_table" in tags

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    xrefs = _listing_xrefs(row, listing, feature_bag=FeatureBag())
    direct_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:direct_control_stub_table"]
    assert [xref["stable_key"] for xref in direct_xrefs] == ["stub-a", "stub-b"]


def test_platform_loadseg_code_start_feature_and_xref() -> None:
    listing = {
        "rows": [
            {
                "kind": "instruction",
                "kind_id": 3,
                "section_index": 3,
                "start_offset": 0,
                "end_offset": 2,
                "stable_key": "loadseg-entry",
                "text": "\tmoveq.l #0,d5\n",
                "code_start_refs": [{"reason": CODE_START_REASON_PLATFORM_LOADSEG_ENTRY}],
            }
        ]
    }
    bag = FeatureBag()
    _add_listing_features(listing, bag)
    counts, _examples, tags = bag.row_features()

    assert counts["analysis:platform_loadseg_entry"] == 1
    assert counts["target-pattern:platform_loadseg_entry"] == 1
    assert "target-pattern:platform_loadseg_entry" in tags

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    xrefs = _listing_xrefs(row, listing, feature_bag=FeatureBag())
    features = {xref["feature"] for xref in xrefs}
    assert "analysis:platform_loadseg_entry" in features
    assert "target-pattern:platform_loadseg_entry" in features


def test_relocated_absolute_jmp_stub_table_feature_and_xref() -> None:
    listing = {
        "rows": [
            {"kind": "label", "kind_id": 2, "section_index": 1, "start_offset": 0x1FE8, "end_offset": 0x1FE8, "text": "loc:\n"},
            {
                "kind": "instruction",
                "kind_id": 3,
                "section_index": 1,
                "start_offset": 0x1FE8,
                "end_offset": 0x1FEE,
                "stable_key": "stub-a",
                "text": "\tjmp loc_4_0000002C.l\n",
                "opcode_or_directive": "jmp",
                "operand_accesses": ["branch_target"],
                "operand_parts": [{"kind": "symbol", "text": "loc_4_0000002C"}],
                "code_start_refs": [{"reason": CODE_START_REASON_CONTROL_TARGET}],
            },
            {"kind": "label", "kind_id": 2, "section_index": 1, "start_offset": 0x1FEE, "end_offset": 0x1FEE, "text": "loc:\n"},
            {
                "kind": "instruction",
                "kind_id": 3,
                "section_index": 1,
                "start_offset": 0x1FEE,
                "end_offset": 0x1FF4,
                "stable_key": "stub-b",
                "text": "\tjmp loc_4_00000058.l\n",
                "opcode_or_directive": "jmp",
                "operand_accesses": ["branch_target"],
                "operand_parts": [{"kind": "symbol", "text": "loc_4_00000058"}],
                "code_start_refs": [{"reason": CODE_START_REASON_CONTROL_TARGET}],
            },
        ]
    }
    bag = FeatureBag()
    _add_listing_features(listing, bag)
    counts, _examples, tags = bag.row_features()

    assert counts["analysis:direct_control_stub_table"] == 2
    assert counts["analysis:relocated_absolute_jmp_stub_table"] == 2
    assert "analysis:relocated_absolute_jmp_stub_table" in tags

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    xrefs = _listing_xrefs(row, listing, feature_bag=FeatureBag())
    jmp_xrefs = [xref for xref in xrefs if xref["feature"] == "analysis:relocated_absolute_jmp_stub_table"]
    assert [xref["stable_key"] for xref in jmp_xrefs] == ["stub-a", "stub-b"]
