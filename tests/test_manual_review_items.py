from __future__ import annotations

from amiga_reversing.disasm.manual_review_items import analysis_review_items


def test_analysis_review_items_emit_orphan_unreconciled_and_suspicious_items() -> None:
    items = analysis_review_items(
        {
            "analysis_policy": {
                "structured_data_items": [
                    {"section_index": 0, "offset": 6, "size": 2},
                ],
            },
            "sections": [
                {
                    "section_index": 0,
                    "section_size": 12,
                    "blocks": [{"start_offset": 0, "end_offset": 2}],
                    "entity_hints": [{"offset": 4, "size": 2}],
                    "orphan_code_signals": [
                        {
                            "offset": 8,
                            "size": 2,
                            "reason_name": "callback",
                            "status_name": "unresolved",
                        },
                    ],
                    "violations": [
                        {
                            "offset": 10,
                            "size": 2,
                            "kind_name": "cpu_requirement",
                            "required_cpu_name": "68020",
                        },
                    ],
                }
            ],
        }
    )

    unreconciled_ranges = {
        (item["start"], item["end"])
        for item in items
        if item["kind"] == "unreconciled_data_range"
    }
    by_kind = {item["kind"]: item for item in items if item["kind"] != "unreconciled_data_range"}
    assert (2, 4) in unreconciled_ranges
    assert (8, 12) in unreconciled_ranges
    assert by_kind["orphan_code_candidate"]["start"] == 8
    assert by_kind["orphan_code_candidate"]["reason"] == "callback"
    assert by_kind["suspicious_instruction_decode"]["start"] == 10
    assert by_kind["suspicious_instruction_decode"]["required_cpu"] == "68020"
    for item in items:
        assert isinstance(item["item_id"], str)
        assert isinstance(item["evidence_fingerprint"], str)
        assert item["state"] == "open"
        assert isinstance(item["suggested_actions"], list)


def test_analysis_review_item_fingerprint_changes_with_supporting_facts() -> None:
    base = {
        "sections": [
            {
                "section_index": 0,
                "section_size": 4,
                "blocks": [{"start_offset": 0, "end_offset": 2}],
                "orphan_code_signals": [{"offset": 2, "size": 2, "reason_name": "callback"}],
            }
        ]
    }
    changed = {
        "sections": [
            {
                "section_index": 0,
                "section_size": 4,
                "blocks": [{"start_offset": 0, "end_offset": 2}],
                "orphan_code_signals": [{"offset": 2, "size": 2, "reason_name": "vector"}],
            }
        ]
    }

    base_item = next(item for item in analysis_review_items(base) if item["kind"] == "orphan_code_candidate")
    changed_item = next(item for item in analysis_review_items(changed) if item["kind"] == "orphan_code_candidate")

    assert base_item["item_id"] == changed_item["item_id"]
    assert base_item["evidence_fingerprint"] != changed_item["evidence_fingerprint"]


def test_analysis_review_resolution_closes_matching_fingerprint_and_reopens_changed_evidence() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "section_size": 4,
                "blocks": [{"start_offset": 0, "end_offset": 2}],
            }
        ]
    }
    open_item = analysis_review_items(analysis)[0]
    resolution = {
        "resolution_id": "r1",
        "item_id": open_item["item_id"],
        "evidence_fingerprint": open_item["evidence_fingerprint"],
    }

    resolved_item = analysis_review_items(analysis, resolutions=(resolution,))[0]
    changed_item = analysis_review_items(
        {
            "sections": [
                {
                    "section_index": 0,
                    "section_size": 5,
                    "blocks": [{"start_offset": 0, "end_offset": 2}],
                }
            ]
        },
        resolutions=(resolution,),
    )[0]

    assert resolved_item["state"] == "resolved"
    assert changed_item["state"] == "open"


def test_manual_label_and_comment_on_unreconciled_ranges_create_review_work() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "section_size": 8,
                "blocks": [{"start_offset": 0, "end_offset": 2}],
            }
        ]
    }

    items = analysis_review_items(
        analysis,
        manual_labels=(
            {"label_id": "l1", "name": "maybe_table", "hunk": 0, "addr": 4},
        ),
        manual_comments=(
            {"comment_id": "c1", "text": "looks like data", "range": "h0:$00000006..$00000008"},
        ),
    )

    by_kind = {item["kind"]: item for item in items if item["kind"].startswith("manual_")}
    assert by_kind["manual_label_unreconciled"]["label_id"] == "l1"
    assert by_kind["manual_label_unreconciled"]["start"] == 4
    assert by_kind["manual_comment_unreconciled"]["comment_id"] == "c1"
    assert by_kind["manual_comment_unreconciled"]["start"] == 6
