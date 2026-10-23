"""Independent accounting cases: unknowns must survive successful rendering."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm.completeness import (
    build_accounting,
    format_accounting,
    partition,
    union_size,
)
from amiga_reversing.disasm.target_metadata import (
    DataBlockElementKind,
    DataBlockElementMetadata,
    DataBlockLayoutMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    write_target_metadata,
)
from amiga_reversing.tools.restoration_accounting import verification_evidence

REVIEW = {
    "seed_origin": TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
    "review_status": TargetMetadataReviewStatus.SEEDED,
    "citation": "manual_action_log:fixture",
}


def metadata(**kwargs):
    return TargetMetadata(target_type="program", entry_register_seeds=(), **kwargs)


def ownership(lo, hi, kind="code", status="accepted"):
    return {
        "start_offset": lo,
        "end_offset": hi,
        "kind_name": kind,
        "status_name": status,
    }


def analysis(*ranges, **kwargs):
    return dict(
        sections=[
            {"section_index": 0, "section_size": 20, "range_ownerships": list(ranges)}
        ],
        **kwargs,
    )


def report(a=None, m=None, **kwargs):
    a = a or analysis()
    plan = kwargs.setdefault("source_plan", {"rows": [], "labels": []})
    plan.setdefault(
        "sections",
        [
            {
                "section_index": s["section_index"],
                "stored_size": s["section_size"],
                "allocation_size": s["section_size"],
                "kind": "code",
            }
            for s in a["sections"]
        ],
    )
    return build_accounting(
        target_id="fixture", analysis=a, metadata=m or metadata(), **kwargs
    )


def test_unclassified_payload_gaps_are_retained_not_called_padding_or_unused():
    r = report(analysis(ownership(2, 6), ownership(10, 12, "text")))
    s = r["payload_sections"][0]
    assert s["classification_bytes"] == {"code": 4, "text": 2, "unknown": 14}
    assert sum(s["classification_bytes"].values()) == 20
    assert [i["start"] for i in s["intervals"] if i["classification"] == "unknown"] == [
        0,
        6,
        12,
    ]
    assert all(i["id"].startswith("payload:s0:") for i in s["intervals"])
    assert r["purpose"]["assessed_unit_denominator"] is None


def test_alias_and_overlapping_classifications_union_without_double_counting():
    r = report(analysis(ownership(0, 8), ownership(4, 12), ownership(10, 15, "table")))
    assert r["payload_sections"][0]["classification_bytes"] == {
        "code": 10,
        "conflict": 2,
        "table": 3,
        "unknown": 5,
    }
    assert union_size([(0, 8), (0, 8), (4, 12), (13, 15)]) == 14


def test_provisional_and_blocked_facts_do_not_fill_classification_gaps():
    r = report(
        analysis(
            ownership(0, 20, "table", "candidate"), ownership(5, 10, "text", "blocked")
        )
    )
    s = r["payload_sections"][0]
    assert s["classification_bytes"] == {"unknown": 20}
    assert any("table" in i["provisional_classes"] for i in s["intervals"])
    assert r["purpose"]["confidence"] == "unknown"


def test_known_classification_authored_name_and_comment_do_not_prove_purpose():
    e = SeededEntityMetadata(
        addr=0,
        end=20,
        hunk=0,
        name="decoded_enemy_behavior",
        type="data",
        subtype="string",
        comment="Fully understood.",
        **REVIEW,
    )
    r = report(analysis(ownership(0, 20, "text")), metadata(seeded_entities=(e,)))
    assert r["payload_sections"][0]["classification_bytes"] == {"text": 20}
    assert r["payload_sections"][0]["purpose"]["status"] == "not_assessed"
    assert r["purpose"]["status"] == "not_assessed"
    assert r["units"]["data"]["string_seed_count"] == 1
    assert r["final_review"]["status"] == "not_assessed"


def test_partial_rsset_aliases_gaps_conflicts_and_unrelated_equal_offsets():
    fields = [
        {
            "layout_kind": 1,
            "layout_name": "app",
            "base_symbol": "APP",
            "offset": 0,
            "size": 4,
            "symbol": "ptr",
        },
        {
            "layout_kind": 1,
            "layout_name": "app",
            "base_symbol": "APP",
            "offset": 0,
            "size": 4,
            "symbol": "ptr_alias",
            "alias": True,
        },
        {
            "layout_kind": 1,
            "layout_name": "app",
            "base_symbol": "APP",
            "offset": 8,
            "size": 2,
            "symbol": "unused_by_name",
            "conflicted": True,
        },
        {
            "layout_kind": 1,
            "layout_name": "other",
            "base_symbol": "OTHER",
            "offset": 0,
            "size": 4,
            "symbol": "other",
        },
    ]
    r = report(analysis(base_layout_fields=fields))
    app = next(
        w for w in r["workspace"]["base_layouts"] if w["layout_identity"][1] == "app"
    )
    assert app["declared_union_bytes"] == 6 and app["field_declarations"] == 3
    assert app["classification_bytes"] == {"conflict": 2, "field": 4, "unknown": 4}
    gap = next(c for c in app["intervals"] if c["classification"] == "unknown")
    assert (gap["start"], gap["end"], gap["gap_intent"]) == (4, 8, "unknown")
    assert app["denominator_bytes"] is None
    assert app["intent_counts"] == {
        "unknown_gaps": 1,
        "reserved": None,
        "padding": None,
        "unused": None,
    }
    assert len(r["workspace"]["base_layouts"]) == 2
    assert r["workspace"]["coordinate_spaces_must_not_be_added"] is True


def test_partial_data_layout_explicit_padding_and_array_counts_stay_separate():
    elements = (
        DataBlockElementMetadata(
            layout_id="owner",
            offset=0,
            width=4,
            kind=DataBlockElementKind.ARRAY,
            array_count=2,
            array_stride=2,
            **REVIEW,
        ),
        DataBlockElementMetadata(
            layout_id="owner",
            offset=4,
            width=2,
            kind=DataBlockElementKind.PADDING,
            **REVIEW,
        ),
    )
    owner = DataBlockLayoutMetadata(
        layout_id="owner",
        hunk=0,
        source_start=0,
        source_end=12,
        elements=elements,
        **REVIEW,
    )
    r = report(m=metadata(data_block_layouts=(owner,)))
    d = r["units"]["data"]["owners"][0]
    assert d["layout_bytes"] == {"element": 4, "padding": 2, "unknown": 6}
    assert d["array_record_count"] == 2 and d["purpose"]["status"] == "not_assessed"
    assert r["units"]["data"]["complete_object_denominator"] is None


def test_incbin_chunks_alias_union_is_presentation_not_semantic_resource_count():
    assets = [
        {
            "kind": "asset",
            "asset_id": "one",
            "source_section_index": 0,
            "source_offset": 4,
            "size": 8,
            "classification": "bitmap",
        },
        {
            "kind": "asset",
            "asset_id": "alias",
            "source_section_index": 0,
            "source_offset": 4,
            "size": 8,
            "classification": "bitmap",
        },
    ]
    r = report(manifest={"files": assets})
    assert r["units"]["assets"]["emission_chunk_count"] == 2
    assert r["units"]["assets"]["union_bytes_by_section"] == {"0": 8}
    assert r["units"]["assets"]["semantic_resource_denominator"] is None
    assert r["payload_sections"][0]["classification_bytes"] == {"unknown": 20}
    assert r["presentation"]["purpose_inferred"] is False


def test_function_candidates_share_bytes_and_do_not_claim_complete_boundaries():
    fs = {
        "functions": [
            {
                "section_index": 0,
                "entry_offset": i,
                "names": ["sub_0" if i == 0 else "understood_name"],
                "ranges": [{"start_offset": 0, "end_offset": 8}],
                "entry_evidence": [{"reason_name": "native_call_target"}],
                "unknowns": ["shared_cfg_blocks"],
            }
            for i in [0, 4]
        ],
        "unknowns": ["candidate_ranges_are_not_proven_function_boundaries"],
    }
    r = report(analysis(ownership(0, 8)), functions=fs)
    assert r["units"]["code"]["candidate_count"] == 2
    assert r["units"]["code"]["complete_boundary_denominator"] is None
    assert r["payload_sections"][0]["classification_bytes"] == {
        "code": 8,
        "unknown": 12,
    }
    assert all(
        c["purpose"]["status"] == "not_assessed"
        for c in r["units"]["code"]["candidates"]
    )


def test_runtime_regions_and_external_hardware_do_not_change_payload_denominator():
    absolute = [
        {
            "start_address": 100,
            "range_end": 104,
            "owner_kind_name": "hardware_register",
            "status_name": "accepted",
            "source_section_index": 0,
            "source_offset": 0,
        },
        {
            "start_address": 102,
            "range_end": 106,
            "owner_kind_name": "hardware_register_range",
            "status_name": "accepted",
            "source_section_index": 0,
            "source_offset": 4,
        },
        {
            "start_address": 300,
            "range_end": 304,
            "owner_kind_name": "runtime_range",
            "status_name": "unknown",
            "source_section_index": 0,
            "source_offset": 8,
        },
    ]
    r = report(
        analysis(absolute_address_ranges=absolute),
        memory_regions={
            "items": [
                {
                    "region_id": "ram",
                    "runtime_address": 300,
                    "size": 64,
                    "source_domain": "runtime_only",
                },
                {
                    "region_id": "alias",
                    "runtime_address": 500,
                    "size": 20,
                    "source_domain": "mapped_source",
                },
            ]
        },
    )
    assert r["hardware_external"]["observed_union_bytes"] == 6
    assert r["hardware_external"]["denominator_bytes"] is None
    assert len(r["workspace"]["absolute_observations"]) == 1
    assert r["payload_sections"][0]["denominator_bytes"] == 20


def test_presentation_coverage_and_generic_labels_are_only_review_signals():
    r = report(
        source_plan={
            "rows": [
                {
                    "has_source_range": 1,
                    "source_size": 20,
                    "source_section_index": 0,
                    "source_offset": 0,
                },
                {
                    "has_source_range": 1,
                    "source_size": 4,
                    "source_section_index": 0,
                    "source_offset": 4,
                },
            ],
            "labels": [
                {"source_section_index": 0, "source_offset": 0, "name": "sub_0000"},
                {
                    "source_section_index": 0,
                    "source_offset": 4,
                    "name": "important_purpose",
                },
            ],
        }
    )
    assert r["presentation"]["source_union_bytes_by_section"] == {"0": 20}
    assert len(r["presentation"]["generic_label_signals"]) == 1
    assert r["payload_sections"][0]["classification_bytes"] == {"unknown": 20}


def test_deterministic_partition_evidence_order_and_boundary_validation():
    a = [(0, 8, "code", "accepted", "a"), (4, 12, "code", "accepted", "b")]
    assert partition(0, 20, a) == partition(0, 20, list(reversed(a)))
    with pytest.raises(ValueError, match="outside"):
        partition(0, 20, [(18, 21, "code", "accepted", "bad")])
    with pytest.raises(ValueError, match="Invalid accounting interval"):
        union_size([(2, 1)])
    r = report(analysis(ownership(0, 8)))
    assert json.dumps(r, sort_keys=True) == json.dumps(
        report(analysis(ownership(0, 8))), sort_keys=True
    )
    assert "score" not in r and "overall_percentage" not in r
    assert "unknown" in format_accounting(r)


def exact_receipt():
    h = lambda x: hashlib.sha256(x).hexdigest()
    return {
        "target_id": "fixture",
        "original_sha256": h(b"original"),
        "original_size": 8,
        "source_sha256": h(b"source"),
        "source_package_sha256": "package",
        "output_sha256": h(b"original"),
        "exact": True,
        "framework_exact": True,
        "oracle": {
            "comparison_level": "oracle.full_file_match",
            "output_sha256": h(b"original"),
        },
    }


def test_byte_exact_receipt_does_not_resolve_semantic_gaps_and_stale_binding_refuses():
    receipt = exact_receipt()
    args = {
        "target_id": "fixture",
        "original": b"original",
        "source": b"source",
        "package_sha256": "package",
    }
    verified = verification_evidence(receipt, **args)
    assert (
        verified["status"] == "exact_original_layout" and not verified["semantic_proof"]
    )
    r = report(verification=verified)
    assert r["payload_sections"][0]["classification_bytes"] == {"unknown": 20}
    assert r["purpose"]["confidence"] == "unknown"
    for field, value in [
        ("original", b"changed!"),
        ("source", b"changed"),
        ("package_sha256", "other"),
    ]:
        assert (
            verification_evidence(receipt, **{**args, field: value})["status"]
            == "stale_or_failed_receipt"
        )


@pytest.mark.c_backend
def test_real_native_report_is_read_only_and_uses_current_ownership(
    tmp_path, monkeypatch
):
    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        RawAddressModel,
        RawBinarySource,
    )
    from amiga_reversing.tools import restoration_accounting as tool

    b = tmp_path / "binary.bin"
    b.write_bytes(bytes.fromhex("4e75000001020304"))
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=b,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(b),
        analysis_cache_path=tmp_path / "analysis",
    )
    write_target_metadata(tmp_path, metadata())
    paths = SimpleNamespace(target_dir=tmp_path, binary_source=source, output_path=None)
    monkeypatch.setattr(tool, "resolve_project_paths", lambda _: paths)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    r = tool.account_target("fixture")
    assert r["payload_sections"][0]["classification_bytes"]["code"] == 2
    assert sum(r["payload_sections"][0]["classification_bytes"].values()) == 8
    assert r["verification"]["status"] == "not_supplied"
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()} == before


def test_stored_payload_allocation_tail_and_bss_are_separate_domains():
    a = {
        "sections": [
            {
                "section_index": 0,
                "section_size": 20,
                "range_ownerships": [ownership(0, 20)],
            },
            {"section_index": 1, "section_size": 12, "range_ownerships": []},
        ]
    }
    plan = {
        "sections": [
            {
                "section_index": 0,
                "stored_size": 8,
                "allocation_size": 20,
                "kind": "code",
            },
            {
                "section_index": 1,
                "stored_size": 0,
                "allocation_size": 12,
                "kind": "bss",
            },
        ]
    }
    r = report(a, source_plan=plan)
    assert len(r["payload_sections"]) == 1
    assert r["payload_sections"][0]["denominator_bytes"] == 8
    assert r["payload_sections"][0]["classification_bytes"] == {"code": 8}
    tails = r["workspace"]["section_allocations"]
    assert [w["denominator_bytes"] for w in tails] == [12, 12]
    assert all(w["purpose"]["status"] == "not_assessed" for w in tails)
    missing = build_accounting(target_id="fixture", analysis=a, metadata=metadata())
    assert missing["payload_sections"] == [] and len(missing["unbounded_sections"]) == 2
    assert all(s["stored_bytes"] is None for s in missing["unbounded_sections"])


def test_unresolved_references_have_source_stable_evidence_identities():
    a = analysis()
    a["sections"][0]["data_references"] = [
        {
            "source_offset": 4,
            "target_status_name": "unresolved_target",
            "table_entry_index": 2,
        },
        {
            "source_offset": 8,
            "target_status_name": "accepted_target",
            "table_entry_index": 3,
        },
    ]
    r = report(a)
    assert r["structure"]["data_reference_target_status"] == {
        "accepted_target": 1,
        "unresolved_target": 1,
    }
    unresolved = r["structure"]["unresolved"]
    assert len(unresolved) == 1 and unresolved[0]["kind"] == "data_reference"
    assert unresolved[0]["id"].startswith("reference:")
    assert unresolved[0]["evidence"]["source_offset"] == 4


@pytest.mark.c_backend
def test_native_hunk_storage_export_keeps_bss_out_of_payload(tmp_path):
    from amiga_reversing.disasm import c_backend
    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        HunkFileBinarySource,
    )

    blob, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        "    SECTION code,code\n    rts\n    dc.w 0\n    SECTION workspace,bss\n    dcb.b 12,0\n",
    )
    b = tmp_path / "program"
    b.write_bytes(blob)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=b,
        display_path=str(b),
        analysis_cache_path=tmp_path / "analysis",
    )
    artifact = c_backend.build_listing_artifact_profile_from_binary_source(source)[2]
    try:
        native = artifact.analysis_payload()[0]
        plan = artifact.source_plan_payload()
        assert plan["sections"] == [
            {
                "section_index": 0,
                "kind": "code",
                "stored_size": 4,
                "allocation_size": 4,
            },
            {
                "section_index": 1,
                "kind": "bss",
                "stored_size": 0,
                "allocation_size": 12,
            },
        ]
        r = build_accounting(
            target_id="fixture", analysis=native, metadata=metadata(), source_plan=plan
        )
        assert [s["denominator_bytes"] for s in r["payload_sections"]] == [4]
        assert [
            s["denominator_bytes"] for s in r["workspace"]["section_allocations"]
        ] == [12]
        # The added DTO does not alter source generation or its exact encoding.
        text = artifact.source_text_with_profile()[0]
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
            "amiga-hunk", text
        )
        assert rebuilt == blob
    finally:
        artifact.close()


def test_point_hardware_observation_with_unknown_width_is_not_fabricated_byte():
    point = {
        "start_address": 100,
        "range_end": 100,
        "owner_kind_name": "hardware_register",
        "status_name": "unknown",
        "source_section_index": 0,
        "source_offset": 2,
    }
    r = report(analysis(absolute_address_ranges=[point]))
    assert r["hardware_external"]["observed_union_bytes"] == 0
    assert r["hardware_external"]["unknown_extent_observations"] == 1
    assert len(r["hardware_external"]["observed_ranges"]) == 1


def test_disagreeing_native_storage_bounds_refuse_instead_of_mixing_domains():
    with pytest.raises(ValueError, match="extents disagree"):
        report(
            source_plan={
                "sections": [
                    {"section_index": 0, "stored_size": 24, "allocation_size": 20}
                ]
            }
        )


def test_indirect_review_identity_survives_evidence_changes_and_keeps_native_status():
    a = analysis()
    a["sections"][0]["recovered_indirect_sites"] = [
        {"offset": 4, "operand_index": 0, "status": "unresolved", "detail": "first"},
        {"offset": 8, "operand_index": 0, "status": "resolved_runtime"},
    ]
    r = report(a)
    assert r["structure"]["indirect_site_status"] == {
        "resolved_runtime": 1,
        "unresolved": 1,
    }
    item = r["structure"]["unresolved"][0]
    assert item["id"] == "indirect:s0:4:0"
    a["sections"][0]["recovered_indirect_sites"][0]["detail"] = "new evidence"
    assert report(a)["structure"]["unresolved"][0]["id"] == item["id"]


def test_read_only_cli_rejects_canonical_output_before_collecting(
    tmp_path, monkeypatch
):
    import sys

    from amiga_reversing.tools import restoration_accounting as tool

    target = tmp_path / "target"
    target.mkdir()
    canonical = target / "manual_actions.jsonl"
    canonical.write_text("original history\n")
    monkeypatch.setattr(
        tool, "resolve_project_paths", lambda _: SimpleNamespace(target_dir=target)
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["accounting", "--target", "fixture", "--json-output", str(canonical)],
    )
    with pytest.raises(ValueError, match="outside the canonical target"):
        tool.main()
    assert canonical.read_text() == "original history\n"


def test_broad_data_owner_is_compatible_with_native_leaf_classification():
    r = report(
        analysis(
            ownership(0, 20, "structured_data"),
            ownership(0, 8, "table"),
            ownership(8, 12, "text"),
        )
    )
    assert r["payload_sections"][0]["classification_bytes"] == {
        "structured_data": 8,
        "table": 8,
        "text": 4,
    }


def test_explicit_native_conflict_status_remains_conflict_without_accepted_claim():
    r = report(analysis(ownership(2, 6, "conflict", "conflict")))
    assert r["payload_sections"][0]["classification_bytes"] == {
        "conflict": 4,
        "unknown": 16,
    }


def test_known_payload_spans_compact_but_keep_native_count_and_unknown_evidence():
    r = report(
        analysis(
            ownership(0, 4),
            ownership(4, 8),
            ownership(8, 12),
            ownership(12, 16, "table", "candidate"),
        )
    )
    cells = r["payload_sections"][0]["intervals"]
    assert len(cells) == 3
    assert cells[0]["evidence"]["native_claim_count"] == 3
    assert (cells[0]["start"], cells[0]["end"]) == (0, 12)
    assert cells[1]["classification"] == "unknown" and cells[1]["evidence"]
    assert cells[1]["id"] == "payload:s0:c:10"


def test_unresolved_operand_forms_keep_status_with_assessed_routine_context():
    from tests.test_purpose_assessments import claim

    a = analysis(ownership(0, 10))
    a['sections'][0]['recovered_platform_unresolved_typed_accesses'] = [
        {"offset": 2, "operand_index": 0, "root_struct_name": 'records', "classification": 'indexed_dynamic'},
        {"offset": 12, "operand_index": 1, "root_struct_name": 'records', "classification": 'field_gap'},
    ]
    r = report(a, purpose_assessments=[claim(end=10, category='code')])
    structure = r['structure']
    assert structure['field_access_records']['unresolved_native_access_records'] == 2
    assert structure['unresolved_access_forms'] == {'field_gap': 1, 'indexed_dynamic': 1}
    assert structure['unresolved_access_layouts'] == {'records': {'field_gap': 1, 'indexed_dynamic': 1}}
    first, second = [i for i in structure['unresolved'] if i['kind'] == 'field_access']
    # Stable identities sort lexically; select the actual instruction coordinates.
    first, second = sorted((first, second), key=lambda i: i['evidence']['offset'])
    assert first['instruction_purpose_context']['status'] == 'supported_scope'
    assert second['instruction_purpose_context']['status'] == 'not_assessed'
    assert first['listing_url'] == '/fixture?section_index=0&source_offset=2'
    assert first['evidence']['classification'] == 'indexed_dynamic'
