from src.scripts.target_usage_manifest import (
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
                "kind": "decompressed_payload",
                "status": "materializable",
                "reason": "initial_control_target_validated_runtime_copy",
                "source_section": 0,
                "source_section_offset": 0x4C40,
                "packed_size": 168391,
                "decompressed_size": 359600,
                "load_address": 0x4000,
                "entrypoint": 0x4000,
            }
        ],
        "decompression_events": [
            {
                "event_kind": "decompression",
                "event_id": "decompression:section:0:00004C40:rnc1-old",
                "status": "materializable",
                "reason": "initial_control_target_validated_runtime_copy",
                "codec_support": "external_provider",
                "payload_role": "primary_program",
                "parent_remains_active": "unknown",
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
    assert "decompression:payload_role:primary_program" in tags
    assert examples["decompression:payload_role:primary_program"][0]["payload_role"] == "primary_program"
    assert examples["decompression:has_event_id"][0]["event_id"] == "decompression:section:0:00004C40:rnc1-old"


def test_labelized_table_shape_features_and_xrefs() -> None:
    listing = {
        "rows": [
            {
                "kind": "data",
                "section_index": 0,
                "start_offset": 0x3526,
                "stable_key": "s0:00003526:data:1",
                "text": "\tdc.w abs_0_0000355C-abs_0_0000355C,abs_0_0000356A-abs_0_0000355C\t; lookup_table\n",
            },
            {
                "kind": "data",
                "section_index": 0,
                "start_offset": 0x7D44,
                "stable_key": "s0:00007D44:data:1",
                "text": "\tdc.l abs_0_00007CA0,abs_0_00007CA6,$00000000,abs_0_00007CD6\t; lookup_table\n",
                "data_class": "lookup_table",
            },
            {
                "kind": "data",
                "section_index": 0,
                "start_offset": 0xC266,
                "stable_key": "s0:0000C266:data:1",
                "text": "\tdc.l abs_0_0000C53C\t; pointer_table\n",
                "data_class": "pointer_table",
            },
            {
                "kind": "label",
                "section_index": 0,
                "start_offset": 0xDDBA,
                "stable_key": "s0:0000DDBA:label:1",
                "text": "loc_0_0000DDBA:",
                "data_class": "string",
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


def test_direct_control_stub_table_feature_and_xref() -> None:
    listing = {
        "rows": [
            {"kind": "label", "section_index": 0, "start_offset": 0x16A, "end_offset": 0x16A, "text": "loc:\n"},
            {
                "kind": "instruction",
                "section_index": 0,
                "start_offset": 0x16A,
                "end_offset": 0x16E,
                "stable_key": "stub-a",
                "text": "\tbra.w loc_0_0000021E\n",
                "opcode_or_directive": "bra.w",
                "operand_accesses": ["branch_target"],
                "operand_parts": [{"kind": "symbol", "text": "loc_0_0000021E"}],
                "code_start_refs": [{"reason_name": "control_target"}],
            },
            {"kind": "label", "section_index": 0, "start_offset": 0x16E, "end_offset": 0x16E, "text": "loc:\n"},
            {
                "kind": "instruction",
                "section_index": 0,
                "start_offset": 0x16E,
                "end_offset": 0x172,
                "stable_key": "stub-b",
                "text": "\tbra.w loc_0_00000254\n",
                "opcode_or_directive": "bra.w",
                "operand_accesses": ["branch_target"],
                "operand_parts": [{"kind": "symbol", "text": "loc_0_00000254"}],
                "code_start_refs": [{"reason_name": "control_target"}],
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


def test_relocated_absolute_jmp_stub_table_feature_and_xref() -> None:
    listing = {
        "rows": [
            {"kind": "label", "section_index": 1, "start_offset": 0x1FE8, "end_offset": 0x1FE8, "text": "loc:\n"},
            {
                "kind": "instruction",
                "section_index": 1,
                "start_offset": 0x1FE8,
                "end_offset": 0x1FEE,
                "stable_key": "stub-a",
                "text": "\tjmp loc_4_0000002C.l\n",
                "opcode_or_directive": "jmp",
                "operand_accesses": ["branch_target"],
                "operand_parts": [{"kind": "symbol", "text": "loc_4_0000002C"}],
                "code_start_refs": [{"reason_name": "control_target"}],
            },
            {"kind": "label", "section_index": 1, "start_offset": 0x1FEE, "end_offset": 0x1FEE, "text": "loc:\n"},
            {
                "kind": "instruction",
                "section_index": 1,
                "start_offset": 0x1FEE,
                "end_offset": 0x1FF4,
                "stable_key": "stub-b",
                "text": "\tjmp loc_4_00000058.l\n",
                "opcode_or_directive": "jmp",
                "operand_accesses": ["branch_target"],
                "operand_parts": [{"kind": "symbol", "text": "loc_4_00000058"}],
                "code_start_refs": [{"reason_name": "control_target"}],
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
