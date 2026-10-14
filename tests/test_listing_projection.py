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


class _NavigationArtifact(_Artifact):
    def __init__(self):
        super().__init__()
        self.navigation_calls = 0
        self.fail_next_navigation = False

    def navigation_payload(self):
        self.navigation_calls += 1
        if self.fail_next_navigation:
            self.fail_next_navigation = False
            raise RuntimeError("native navigation serialization failed")
        return {"groups": {"labels": [{"name": "native_label"}]}}, {"native": True}


def test_native_navigation_reused_only_for_owned_current_artifact():
    service = ListingProjectionService()
    artifact = _NavigationArtifact()
    service.set_artifact(project_id="demo", cache_key="a", artifact=artifact)
    first = service.cached_native_navigation_payload(project_id="demo", artifact=artifact, current_cache_key="a")
    assert service.cached_native_navigation_payload(project_id="demo", artifact=artifact, current_cache_key="a") == first
    assert artifact.navigation_calls == 1
    service.cached_native_navigation_payload(project_id="demo", artifact=artifact, current_cache_key="b")
    assert artifact.navigation_calls == 2
    assert service.debug_state()["native_navigation_cache_projects"] == []
    replacement = _NavigationArtifact()
    service.set_artifact(project_id="demo", cache_key="a", artifact=replacement)
    service.cached_native_navigation_payload(project_id="demo", artifact=replacement, current_cache_key="a")
    assert artifact.closed and replacement.navigation_calls == 1


@pytest.mark.parametrize("operation", ["clear", "reset", "invalidate", "dirty", "global"])
def test_native_navigation_released_at_artifact_invalidation(operation):
    service = ListingProjectionService()
    artifact = _NavigationArtifact()
    service.set_artifact(project_id="demo", cache_key="a", artifact=artifact)
    service.cached_native_navigation_payload(project_id="demo", artifact=artifact, current_cache_key="a")
    if operation == "clear":
        service.clear_project("demo")
    elif operation == "reset":
        service.reset()
    elif operation == "invalidate":
        service.invalidate_project_keep_artifact("demo")
    elif operation == "dirty":
        service.mark_presentation_dirty("demo")
    else:
        service.invalidate_all_lazy()
    assert service.debug_state()["native_navigation_cache_projects"] == []


def test_native_navigation_failure_can_retry_without_partial_cache():
    service = ListingProjectionService()
    artifact = _NavigationArtifact()
    artifact.fail_next_navigation = True
    service.set_artifact(project_id="demo", cache_key="a", artifact=artifact)
    with pytest.raises(RuntimeError, match="serialization failed"):
        service.cached_native_navigation_payload(project_id="demo", artifact=artifact, current_cache_key="a")
    assert service.debug_state()["native_navigation_cache_projects"] == []
    service.cached_native_navigation_payload(project_id="demo", artifact=artifact, current_cache_key="a")
    assert artifact.navigation_calls == 2


def test_native_navigation_shared_under_target_lease(tmp_path):
    from amiga_reversing.disasm.target_history import target_lock
    service = ListingProjectionService()
    artifact = _NavigationArtifact()
    service.set_artifact(project_id="demo", cache_key="a", artifact=artifact)
    barrier = threading.Barrier(2)
    results = []

    def read():
        barrier.wait()
        with target_lock(tmp_path):
            results.append(service.cached_native_navigation_payload(project_id="demo", artifact=artifact, current_cache_key="a"))

    threads = [threading.Thread(target=read) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
    assert all(not thread.is_alive() for thread in threads)
    assert len(results) == 2 and artifact.navigation_calls == 1


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


def test_listing_projection_recovers_projected_label_when_offset_lookup_returns_backing_data() -> None:
    class Artifact:
        def row_for_source_offset(self, *, section_index: int, offset: int) -> dict[str, object]:
            assert (section_index, offset) == (0, 4)
            return {
                "row_key": "data-row",
                "row_index": 11,
                "kind": "data",
                "section_index": 0,
                "start_offset": 4,
                "end_offset": 6,
            }

        def window_payload(self, *, start: int, count: int) -> tuple[dict[str, object], dict[str, object]]:
            assert start == 0
            assert count == 129
            return (
                {
                    "rows": [
                        {
                            "row_key": "label-row",
                            "row_index": 10,
                            "kind": "label",
                            "section_index": 0,
                            "start_offset": 4,
                            "end_offset": 4,
                        },
                        {
                            "row_key": "data-row",
                            "row_index": 11,
                            "kind": "data",
                            "section_index": 0,
                            "start_offset": 4,
                            "end_offset": 6,
                        },
                    ]
                },
                {},
            )

    service = ListingProjectionService()
    resolved = service.resolve_locator_from_artifact(
        target_id="demo",
        projection_hash="hash-a",
        artifact=Artifact(),
        locator_payload={
            "target_id": "demo",
            "projection_hash": "hash-a",
            "row_key": "label-row",
            "kind": "label",
            "section_index": 0,
            "start_offset": 4,
            "end_offset": 4,
        },
    )

    assert resolved["row_key"] == "label-row"


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


def test_failed_listing_poll_preserves_error_until_retry_or_revision_change() -> None:
    service = ListingProjectionService()
    jobs: dict[str, dict[str, object]] = {}
    started: list[tuple[str, str]] = []
    lock = threading.Lock()

    def start(cache_key: str, *, retry_failed: bool = False) -> dict[str, object]:
        return service.start_listing_job(
            project_id="demo", cache_key=cache_key, jobs=jobs, lock=lock,
            job_kind="listing_artifact", phase_count=2, now=lambda: 1.0,
            make_job_id=lambda: f"job-{len(started)}", total_rows=lambda: None,
            prewarm=lambda: None, on_ready=lambda: None,
            start_worker=lambda job_id, project: started.append((job_id, project)),
            retry_failed=retry_failed,
        )

    first = start("revision-a")
    jobs[str(first["job_id"])].update(status="failed", error="native parser rejected input")
    for _ in range(3):
        polled = start("revision-a")
        assert polled["status"] == "failed"
        assert polled["error"] == "native parser rejected input"
    assert len(started) == 1
    assert start("revision-a", retry_failed=True)["status"] == "queued"
    assert len(started) == 2
    assert start("revision-a")["status"] == "queued"
    assert len(started) == 2
    assert start("revision-b")["status"] == "queued"
    assert len(started) == 3
