from __future__ import annotations

import threading

import pytest

from amiga_reversing.disasm.listing_projection import (
    ListingLocatorError,
    ListingProjectionService,
)


class _Artifact:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_listing_projection_service_owns_artifact_cache_lifecycle() -> None:
    service = ListingProjectionService()
    old_artifact = _Artifact()
    new_artifact = _Artifact()

    service.set_artifact(project_id="demo", cache_key="cache-a", artifact=old_artifact)
    assert service.valid_artifact("demo", "cache-a") is old_artifact

    service.set_artifact(project_id="demo", cache_key="cache-b", artifact=new_artifact)
    assert old_artifact.closed is True
    assert service.valid_artifact("demo", "cache-b") is new_artifact

    service.reset()
    assert new_artifact.closed is True
    assert service.debug_state()["artifact_projects"] == []


def test_listing_projection_service_allows_dirty_presentation_reads() -> None:
    service = ListingProjectionService()
    artifact = _Artifact()
    service.set_artifact(project_id="demo", cache_key="old-cache", artifact=artifact)
    service.mark_presentation_dirty("demo")

    assert service.valid_artifact("demo", "new-cache") is None
    assert service.read_artifact("demo", "new-cache") is artifact


def test_listing_projection_service_starts_reuses_and_cancels_listing_jobs() -> None:
    service = ListingProjectionService()
    jobs: dict[str, dict[str, object]] = {}
    lock = threading.Lock()
    started: list[tuple[str, str]] = []

    payload = service.start_listing_job(
        project_id="demo",
        cache_key="cache-a",
        jobs=jobs,
        lock=lock,
        job_kind="listing_artifact",
        phase_count=2,
        now=lambda: 1.0,
        make_job_id=lambda: "job-1",
        total_rows=lambda: 3,
        prewarm=lambda: None,
        on_ready=lambda: None,
        start_worker=lambda job_id, project_id: started.append((job_id, project_id)),
    )
    reused = service.start_listing_job(
        project_id="demo",
        cache_key="cache-a",
        jobs=jobs,
        lock=lock,
        job_kind="listing_artifact",
        phase_count=2,
        now=lambda: 2.0,
        make_job_id=lambda: "job-2",
        total_rows=lambda: 3,
        prewarm=lambda: None,
        on_ready=lambda: None,
        start_worker=lambda job_id, project_id: started.append((job_id, project_id)),
    )

    assert payload["job_id"] == "job-1"
    assert reused["job_id"] == "job-1"
    assert started == [("job-1", "demo")]

    canceled = service.cancel_listing_jobs(
        jobs=jobs,
        lock=lock,
        job_kind="listing_artifact",
        now=lambda: 3.0,
        project_id="demo",
    )

    assert canceled[0][1]["status"] == "failed"
    assert jobs == {}


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


def test_listing_projection_resolves_indexed_locator_from_normalized_window() -> None:
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
            {"row_key": "row-a", "kind": "instruction", "section_index": 0, "start_offset": 4, "end_offset": 6}
        ],
    }
    normalized = service.normalize_window(target_id="demo", projection_hash="hash-a", payload=payload)
    locator = normalized["rows"][0]["locator"]

    resolved = service.resolve_locator_from_artifact(
        target_id="demo",
        projection_hash="hash-a",
        artifact=object(),
        locator_payload=locator,
    )

    assert resolved["row_key"] == "row-a"


def test_listing_projection_index_rejects_ambiguous_stale_locator() -> None:
    service = ListingProjectionService()
    payload = {
        "anchor_addr": 0,
        "start": 0,
        "end": 2,
        "has_more_before": False,
        "has_more_after": False,
        "total_rows": 2,
        "analysis_generation": "full",
        "rows": [
            {"row_key": "row-a", "kind": "instruction", "section_index": 0, "start_offset": 4, "end_offset": 6},
            {"row_key": "row-b", "kind": "instruction", "section_index": 0, "start_offset": 4, "end_offset": 6},
        ],
    }
    service.normalize_window(target_id="demo", projection_hash="hash-b", payload=payload)

    with pytest.raises(ListingLocatorError) as exc:
        service.resolve_locator_from_artifact(
            target_id="demo",
            projection_hash="hash-b",
            artifact=object(),
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
