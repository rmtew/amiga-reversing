from __future__ import annotations

import pytest

from amiga_reversing.disasm.listing_projection import (
    ListingLocatorError,
    ListingProjectionService,
)


def test_listing_projection_normalizes_rows_to_locator_contract() -> None:
    service = ListingProjectionService()
    payload = {
        "anchor_addr": 0,
        "start": 0,
        "end": 1,
        "has_more_before": False,
        "has_more_after": False,
        "total_rows": 1,
        "analysis_generation": "full",
        "rows": [
            {
                "row_id": "c:1",
                "stable_key": "s0:00000004:instruction:1",
                "kind": "instruction",
                "section_index": 0,
                "start_offset": 4,
                "end_offset": 6,
                "addr": 4,
                "runtime_address": 0x6004,
                "text": "rts\n",
            }
        ],
    }

    normalized = service.normalize_window(target_id="demo", projection_hash="hash-a", payload=payload)
    row = normalized["rows"][0]

    assert normalized["target_id"] == "demo"
    assert normalized["projection_hash"] == "hash-a"
    assert row["target_id"] == "demo"
    assert row["projection_hash"] == "hash-a"
    assert row["row_key"] == "s0:00000004:instruction:1"
    assert row["section_index"] == 0
    assert row["start_offset"] == 4
    assert row["end_offset"] == 6
    assert row["kind"] == "instruction"
    assert row["storage_address"] == 4
    assert row["runtime_address"] == 0x6004
    assert row["locator"] == {
        "target_id": "demo",
        "projection_hash": "hash-a",
        "row_key": "s0:00000004:instruction:1",
        "section_index": 0,
        "start_offset": 4,
        "end_offset": 6,
        "kind": "instruction",
        "storage_address": 4,
        "runtime_address": 0x6004,
    }
    assert "row_id" not in row
    assert "stable_key" not in row


def test_listing_projection_resolves_exact_locator() -> None:
    service = ListingProjectionService()
    rows = [
        {"row_key": "row-a", "kind": "instruction", "section_index": 0, "start_offset": 0, "end_offset": 2},
    ]

    resolved = service.resolve_locator(
        target_id="demo",
        projection_hash="hash-a",
        rows=rows,
        locator_payload={
            "target_id": "demo",
            "projection_hash": "hash-a",
            "row_key": "row-a",
            "kind": "instruction",
        },
    )

    assert resolved["row_key"] == "row-a"


def test_listing_projection_recovers_stale_locator_by_unique_recovery_identity() -> None:
    service = ListingProjectionService()
    rows = [
        {"row_key": "row-new", "kind": "instruction", "section_index": 0, "start_offset": 4, "end_offset": 6},
    ]

    resolved = service.resolve_locator(
        target_id="demo",
        projection_hash="hash-b",
        rows=rows,
        locator_payload={
            "target_id": "demo",
            "projection_hash": "hash-a",
            "row_key": "row-old",
            "section_index": 0,
            "start_offset": 4,
            "end_offset": 6,
            "kind": "instruction",
        },
    )

    assert resolved["row_key"] == "row-new"
    assert resolved["projection_hash"] == "hash-b"


def test_listing_projection_rejects_target_mismatch() -> None:
    service = ListingProjectionService()

    with pytest.raises(ListingLocatorError, match="target_id") as exc:
        service.resolve_locator(
            target_id="demo",
            projection_hash="hash-a",
            rows=[],
            locator_payload={
                "target_id": "other",
                "projection_hash": "hash-a",
                "row_key": "row-a",
                "kind": "instruction",
            },
        )

    assert exc.value.code == "target_mismatch"


def test_listing_projection_rejects_missing_locator() -> None:
    service = ListingProjectionService()

    with pytest.raises(ListingLocatorError) as exc:
        service.resolve_locator(
            target_id="demo",
            projection_hash="hash-a",
            rows=[],
            locator_payload={
                "target_id": "demo",
                "projection_hash": "hash-a",
                "row_key": "missing",
                "kind": "instruction",
            },
        )

    assert exc.value.code == "missing_locator"


def test_listing_projection_rejects_ambiguous_stale_locator() -> None:
    service = ListingProjectionService()
    rows = [
        {"row_key": "row-a", "kind": "instruction", "section_index": 0, "start_offset": 4, "end_offset": 6},
        {"row_key": "row-b", "kind": "instruction", "section_index": 0, "start_offset": 4, "end_offset": 6},
    ]

    with pytest.raises(ListingLocatorError) as exc:
        service.resolve_locator(
            target_id="demo",
            projection_hash="hash-b",
            rows=rows,
            locator_payload={
                "target_id": "demo",
                "projection_hash": "hash-a",
                "row_key": "row-old",
                "section_index": 0,
                "start_offset": 4,
                "end_offset": 6,
                "kind": "instruction",
            },
        )

    assert exc.value.code == "ambiguous_locator"
