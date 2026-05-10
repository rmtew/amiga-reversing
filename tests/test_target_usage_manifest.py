from src.scripts.target_usage_manifest import (
    CODE_START_REASON_CONTROL_TARGET,
    CODE_START_REASON_PLATFORM_LOADSEG_ENTRY,
    FeatureBag,
    ORPHAN_CODE_SIGNAL_STATUS_UNRESOLVED,
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
                ],
            }
        ],
        "orphan_code_signal_count": 2,
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, _examples, tags = bag.row_features()

    assert counts["orphan-code:missing_inbound:api"] == 1
    assert "target-pattern:orphan_missing_api" in tags


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
