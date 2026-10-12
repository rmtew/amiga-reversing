"""Concurrent API readers retain their native artifact until their target lease ends."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import server
from amiga_reversing.disasm.listing_projection import ListingProjectionService


@pytest.mark.parametrize("mutation", ["clear", "publish"])
def test_reader_lease_blocks_native_artifact_close(tmp_path, monkeypatch, mutation):
    service = ListingProjectionService()
    closed = Event()
    reading = Event()
    release = Event()
    mutation_started = Event()

    class Artifact:
        def close(self):
            closed.set()

    original = Artifact()
    replacement = Artifact()
    service.set_artifact(project_id="demo", cache_key="revision", artifact=original)
    project = SimpleNamespace(target_dir=tmp_path)
    monkeypatch.setattr(server, "_LISTING_PROJECTION_SERVICE", service)
    monkeypatch.setattr(server, "get_project", lambda _: project)
    monkeypatch.setattr(server, "resolve_project_paths", lambda *a, **kw: project)
    monkeypatch.setattr(server, "_COMMAND_AVAILABILITY_CACHE", {})
    monkeypatch.setattr(server, "_project_listing_cache_key", lambda _: "revision")

    def read(*args):
        assert service.valid_artifact("demo", "revision") is original
        reading.set()
        assert release.wait(3)
        assert not closed.is_set(), "native artifact closed during a leased read"
        return {"ok": True}

    monkeypatch.setattr(server, "_route_request_unlocked", read)
    if mutation == "publish":
        monkeypatch.setattr(server, "_ASYNC_JOBS", {"job": {"cache_key": "revision"}})
        monkeypatch.setattr(server, "_set_job_state", lambda *a, **kw: True)
        monkeypatch.setattr(server, "_set_job_phase", lambda *a, **kw: True)
        monkeypatch.setattr(server, "_is_macos_listing_project", lambda _: False)
        monkeypatch.setattr(
            server,
            "build_project_listing_artifact_profile",
            lambda _: (1, {}, replacement),
        )
        for name in (
            "_prewarm_analysis_review_items",
            "_publish_listing_artifact_ready_event",
            "_start_reproduction_job_if_needed",
            "_log_event",
        ):
            monkeypatch.setattr(server, name, lambda *a, **kw: None)

    def mutate():
        mutation_started.set()
        if mutation == "clear":
            server._clear_project_listing_cache("demo")
        else:
            server._build_rows_job("job", "demo")

    with ThreadPoolExecutor(max_workers=2) as pool:
        reader = pool.submit(
            server.route_request, "GET", "/api/projects/demo/listing", {}
        )
        try:
            assert reading.wait(3)
            writer = pool.submit(mutate)
            assert mutation_started.wait(3)
            assert not closed.wait(0.05)
        finally:
            release.set()
        assert reader.result(timeout=3) == {"ok": True}
        writer.result(timeout=3)
    assert closed.is_set()
    if mutation == "publish":
        assert service.valid_artifact("demo", "revision") is replacement
