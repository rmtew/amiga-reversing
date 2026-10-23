"""Purpose is explicit scoped evidence, independent of labels, source and acceptance counts."""

import json

import pytest

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.decision_journal import (
    project_decision_journal,
    read_decision_journal,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_text
from amiga_reversing.disasm.manual_action_catalog import (
    target_action_catalog,
    target_catalog_manual_payload,
)
from amiga_reversing.disasm.manual_actions import ManualActionKind as K
from amiga_reversing.disasm.manual_actions import (
    append_manual_actions,
    load_manual_projection,
)
from amiga_reversing.disasm.purpose_assessments import (
    purpose_intervals,
    purpose_summary,
    reviewed_assessments,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_restoration_accounting import analysis, ownership, report
from tests.test_restoration_operations import target as target


def definition(**changes):
    return {
        "coordinate_space": "source",
        "start": 0,
        "end": 4,
        "section_index": 0,
        "category": "graphics",
        "purpose": "Four planar bytes copied as one UI border row.",
        "confidence": "high",
        "coverage": "whole_scope",
        "limits": "CPU byte-copy evidence only; DMA timing and display pixels are not assessed.",
    } | changes


def claim(**changes):
    return (
        dict(
            assessment_id="purpose-one",
            action_id="action-one",
            **definition(),
            interpretation={
                "source_evidence_status": "analysis_proven",
                "evidence_refs": ["s0:00000000:data"],
                "reason": "Original CPU copy reads these four bytes.",
            },
            review_status="accepted",
            evidence_available=True,
        )
        | changes
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"confidence": "automatic"},
        {"confidence": None},
        {"category": "bitmap_by_name"},
        {"start": 4},
        {"end": True},
        {"coverage": "all_understood"},
        {"purpose": ""},
        {"limits": ""},
        {"layout_name": "app"},
        {"section_index": None},
        {"coordinate_space": "guessed"},
        {"evidence_count": 999},
    ],
)
def test_invalid_assessment_refused_by_normal_catalog(changes):
    with pytest.raises(ValueError, match="purpose|assessment"):
        target_catalog_manual_payload(
            "target.purpose.assess", parameters=definition(**changes)
        )


def fixture(tmp_path):
    b = tmp_path / "binary.bin"
    b.write_bytes(bytes.fromhex("4e750000"))
    (tmp_path / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": str(b),
                "load_address": 0,
                "entrypoint": 0,
                "code_start_offset": 0,
            }
        )
    )
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
    write_target_metadata(
        tmp_path, TargetMetadata(target_type="program", entry_register_seeds=())
    )
    return source


def test_catalog_replay_remove_undo_redo_preserve_identity_and_native_policy(tmp_path):
    source = fixture(tmp_path)
    before = effective_metadata_text(tmp_path)
    commands = {a["action_id"]: a for a in target_action_catalog()}
    assert (
        commands["target.purpose.assess"]["enabled"]
        and commands["target.purpose.remove"]["enabled"]
    )
    kind, payload = target_catalog_manual_payload(
        "target.purpose.assess", parameters=definition()
    )
    payload["interpretation"] = claim()["interpretation"]
    action = append_manual_actions(
        tmp_path, binary_source=source, actions=[(K(kind), payload)]
    )[0]
    projected = load_manual_projection(tmp_path).purpose_assessments
    assert len(projected) == 1 and projected[0]["action_id"] == action["action_id"]
    assert (
        projected[0]["confidence"] == "high"
        and projected[0]["interpretation"]["evidence_refs"]
    )
    assert (
        effective_metadata_text(tmp_path) == before
    )  # No source-policy hash, C classification or ASM comment change.
    append_manual_actions(
        tmp_path,
        binary_source=source,
        actions=[(K.UNDO_ACTION, {"undoes_action_id": action["action_id"]})],
    )
    assert not load_manual_projection(tmp_path).purpose_assessments
    append_manual_actions(
        tmp_path,
        binary_source=source,
        actions=[(K.REDO_ACTION, {"redoes_action_id": action["action_id"]})],
    )
    assert load_manual_projection(tmp_path).purpose_assessments == projected
    kind, payload = target_catalog_manual_payload(
        "target.purpose.remove",
        parameters={"assessment_id": projected[0]["assessment_id"]},
    )
    append_manual_actions(tmp_path, binary_source=source, actions=[(K(kind), payload)])
    assert not load_manual_projection(tmp_path).purpose_assessments
    assert effective_metadata_text(tmp_path) == before


def test_unreviewed_evidence_and_rejected_deferred_partial_claims_remain_unassessed():
    for status in ["unassessed", "rejected", "deferred", "conflicting_reviews"]:
        s = purpose_summary(purpose_intervals(0, 8, [claim(review_status=status)]))
        assert not s["bytes_by_status"].get("supported", 0)
    partial = purpose_summary(
        purpose_intervals(0, 8, [claim(coverage="partial_scope")])
    )
    assert partial["bytes_by_status"] == {"partial_claim": 4, "unassessed": 4}
    missing = purpose_summary(
        purpose_intervals(0, 8, [claim(evidence_available=False)])
    )
    assert missing["bytes_by_status"] == {"provisional": 4, "unassessed": 4}


def test_accepted_low_confidence_is_not_promoted_and_overlaps_do_not_double_count():
    cells = purpose_intervals(
        0,
        12,
        [
            claim(confidence="low", end=8),
            claim(assessment_id="purpose-two", start=4, end=12),
        ],
    )
    s = purpose_summary(cells)
    assert s["bytes_by_status"] == {"overlapping_assessments": 4, "supported": 8}
    assert s["supported_bytes_by_category_confidence"] == {
        "graphics:high": 4,
        "graphics:low": 4,
    }
    assert sum(s["bytes_by_status"].values()) == 12


def test_journal_join_is_action_specific_and_requires_no_new_review_tracker():
    a = claim()
    a.pop("review_status")
    a.pop("evidence_available")
    assert reviewed_assessments([a], {})[0]["review_status"] == "unassessed"
    d = {
        "fact_type": "restoration_interpretation",
        "decision_id": "accepted-one",
        "selected_identity": {"subject_id": "action-one"},
    }
    result = reviewed_assessments([a], {"accepted_facts": [d]})[0]
    assert result["review_status"] == "accepted" and result["evidence_available"]
    result = reviewed_assessments(
        [a],
        {
            "accepted_facts": [d],
            "rejected_facts": [d | {"decision_id": "rejected-two"}],
        },
    )[0]
    assert result["review_status"] == "conflicting_reviews"


def test_report_maps_only_explicit_claims_and_retains_structural_and_readiness_limits():
    r = report(
        analysis(ownership(0, 20, "structured_data")), purpose_assessments=[claim()]
    )
    assert r["payload_sections"][0]["classification_bytes"] == {"structured_data": 20}
    assert r["payload_sections"][0]["purpose"]["bytes_by_status"] == {
        "supported": 4,
        "unassessed": 16,
    }
    assert r["purpose"]["status"] == "partially_assessed"
    assert r["structure"]["closure_status"] == "not_established"
    assert (
        r["final_review"]["status"]
        == r["relocation_readiness"]["status"]
        == "not_assessed"
    )
    bad = report(purpose_assessments=[claim(end=24)])
    assert bad["purpose"]["assessments"][0]["scope_status"] == "outside_known_extent"
    assert bad["payload_sections"][0]["purpose"]["bytes_by_status"] == {
        "unassessed": 20
    }


def test_rsset_identity_and_gap_neighbor_links_do_not_invent_unused_storage():
    a = analysis(
        base_layout_fields=[
            {
                "layout_kind": 1,
                "layout_name": "app",
                "base_symbol": "APP",
                "offset": 0,
                "size": 2,
                "symbol": "left",
            },
            {
                "layout_kind": 1,
                "layout_name": "app",
                "base_symbol": "APP",
                "offset": 6,
                "size": 2,
                "symbol": "right",
            },
        ]
    )
    a["sections"][0]["app_slot_refs"] = [{"offset": 4, "symbol_name": "right"}]
    workspace = claim(
        coordinate_space="base_relative",
        section_index=None,
        layout_name="app",
        base_symbol="APP",
        start=0,
        end=2,
        category="workspace",
    )
    r = report(a, purpose_assessments=[workspace])
    w = r["workspace"]["base_layouts"][0]
    assert w["purpose"]["bytes_by_status"] == {"supported": 2, "unassessed": 6}
    gap = next(c for c in w["intervals"] if c["classification"] == "unknown")
    assert gap["gap_intent"] == "unknown" and gap["boundary_use_links"] == [
        {"symbol": "right", "listing_url": "/fixture?section_index=0&source_offset=4"}
    ]
    other = report(a, purpose_assessments=[workspace | {"base_symbol": "OTHER"}])
    assert other["workspace"]["base_layouts"][0]["purpose"]["bytes_by_status"] == {
        "unassessed": 8
    }


@pytest.mark.c_backend
def test_purpose_claim_never_leaks_into_native_source_or_changes_exact_output(tmp_path):
    from amiga_reversing.disasm import c_backend
    from amiga_reversing.disasm.effective_metadata import effective_metadata_file

    source = fixture(tmp_path)
    kind, payload = target_catalog_manual_payload(
        "target.purpose.assess", parameters=definition()
    )
    payload["interpretation"] = claim()["interpretation"]
    append_manual_actions(tmp_path, binary_source=source, actions=[(K(kind), payload)])
    with effective_metadata_file(tmp_path) as m:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=m
        )[2]
    try:
        text = artifact.source_text_with_profile()[0]
        assert (
            definition()["purpose"] not in text
            and "confidence" not in text
            and "assessment" not in text
        )
        assert (
            c_backend.assemble_platform_source_text_with_c_backend("amiga-raw", text)[0]
            == source.path.read_bytes()
        )
    finally:
        artifact.close()


def test_normal_review_accepts_scoped_fact_without_promoting_declared_confidence(
    target, monkeypatch
):
    from amiga_reversing.disasm import restoration, restoration_verification
    from tests.test_restoration_operations import current, invoke

    kind, payload = target_catalog_manual_payload(
        "target.purpose.assess", parameters=definition(confidence="low")
    )
    payload["interpretation"] = claim()["interpretation"]
    action = append_manual_actions(
        target.directory, binary_source=target.source, actions=[(K(kind), payload)]
    )[0]
    subject = restoration.revisions("test")["subject_revision"]
    monkeypatch.setattr(
        restoration_verification,
        "load_receipt",
        lambda *_: {"kind": "verification", "subject_revision": subject, "exact": True},
    )
    invoke(
        "review",
        expected_revision=current(),
        action_id=action["action_id"],
        decision="accept",
        reason="Bounded purpose; confidence remains low.",
        verification_id="fixture-proof",
    )
    journal = read_decision_journal(target.directory)
    assert journal["valid"]
    assessments = reviewed_assessments(
        load_manual_projection(target.directory).purpose_assessments,
        project_decision_journal(journal["records"]),
    )
    assert (
        assessments[0]["review_status"] == "accepted"
        and assessments[0]["confidence"] == "low"
    )
    assert purpose_summary(purpose_intervals(0, 4, assessments))[
        "supported_bytes_by_category_confidence"
    ] == {"graphics:low": 4}


def test_absolute_purpose_stays_in_observed_external_domain_not_payload_or_address_gaps():
    a = analysis(
        absolute_address_ranges=[
            {
                "start_address": 100,
                "range_end": 104,
                "owner_kind_name": "hardware_register",
                "status_name": "accepted",
                "source_section_index": 0,
                "source_offset": 2,
            }
        ]
    )
    external = claim(
        coordinate_space="absolute",
        section_index=None,
        start=100,
        end=108,
        category="platform",
    )
    r = report(a, purpose_assessments=[external])
    assert r["purpose"]["status"] == "partially_assessed"
    assert r["hardware_external"]["purpose"]["bytes_by_status"] == {"supported": 4}
    assert r["hardware_external"]["denominator_bytes"] is None
    assert r["payload_sections"][0]["purpose"]["bytes_by_status"] == {"unassessed": 20}


def test_encoding_inventory_exposes_finer_evidence_without_promoting_it_to_purpose():
    a = analysis(ownership(0, 20, "structured_data"))
    m = {
        "files": [
            {
                "kind": "asset",
                "asset_id": "bitmap",
                "source_section_index": 0,
                "source_offset": 0,
                "size": 8,
                "classification": "bitmap",
            },
            {
                "kind": "asset",
                "asset_id": "sample",
                "source_section_index": 0,
                "source_offset": 8,
                "size": 4,
                "classification": "sound_sample",
            },
        ]
    }
    r = report(a, manifest=m)
    classes = r["structure"]["data_evidence_inventory"]["native_asset_encoding_classes"]
    assert classes["bitmap"]["within_structured_data_bytes_by_section"] == {"0": 8}
    assert classes["sound_sample"]["within_structured_data_bytes_by_section"] == {
        "0": 4
    }
    assert r["payload_sections"][0]["purpose"]["bytes_by_status"] == {"unassessed": 20}
    assert r["units"]["assets"]["chunks"][0]["purpose"]["status"] == "not_assessed"


def test_gap_links_normalize_native_app_alias_by_qualified_offset_not_spelling():
    fields = [
        {
            "layout_kind": 1,
            "layout_name": "app",
            "base_symbol": "APP",
            "offset": 0,
            "size": 2,
            "symbol": "left",
            "source_kind_name": "app_slot_access",
        },
        {
            "layout_kind": 1,
            "layout_name": "app",
            "base_symbol": "APP",
            "offset": 6,
            "size": 2,
            "symbol": "right",
            "source_kind_name": "app_slot_access",
        },
    ]
    a = analysis(base_layout_fields=fields)
    a["sections"][0]["app_slot_refs"] = [
        {"offset": 4, "displacement": 6, "symbol_name": "app_0006"}
    ]
    r = report(a)
    gap = next(
        c
        for c in r["workspace"]["base_layouts"][0]["intervals"]
        if c["classification"] == "unknown"
    )
    assert gap["gap_intent"] == "unknown"
    assert gap["boundary_use_links"] == [
        {
            "symbol": "right",
            "native_symbol": "app_0006",
            "match_basis": "qualified_native_app_slot_offset",
            "listing_url": "/fixture?section_index=0&source_offset=4",
        }
    ]
    # Equal displacements in multiple possible bases remain ambiguous.
    a["base_layout_fields"] = fields + [
        fields[-1] | {"layout_name": "other", "base_symbol": "OTHER"}
    ]
    r = report(a)
    assert all(
        not c.get("boundary_use_links")
        for w in r["workspace"]["base_layouts"]
        for c in w["intervals"]
        if c["classification"] == "unknown"
    )
