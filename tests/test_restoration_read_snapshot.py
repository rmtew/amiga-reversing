"""Operation-local reuse keeps full content hashing at each read boundary."""

import hashlib
import os
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import restoration, server
from tests.test_restoration_operations import target as target


def test_cache_key_snapshot_ends_at_request_and_rechecks_same_stat_edit(tmp_path, monkeypatch):
    history = tmp_path / "manual_actions.jsonl"
    history.write_bytes(b"first")
    calls = []

    def compute(project):
        calls.append(project)
        return hashlib.sha256(history.read_bytes()).hexdigest()

    monkeypatch.setattr(server, "_compute_project_listing_cache_key", compute)
    with server._listing_read_snapshot():
        original = server._project_listing_cache_key("target")
        with server._listing_read_snapshot():
            assert server._project_listing_cache_key("target") == original
        assert server._project_listing_cache_key("target") == original
    assert calls == ["target"]
    assert server._LISTING_CACHE_KEY_SNAPSHOT.get() is None

    stamp = history.stat()
    history.write_bytes(b"later")
    os.utime(history, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    with server._listing_read_snapshot():
        assert server._project_listing_cache_key("target") != original
    assert calls == ["target", "target"]


def test_discard_before_mutation_forces_fresh_hash_within_operation(tmp_path, monkeypatch):
    history = tmp_path / "manual_actions.jsonl"
    history.write_bytes(b"before")
    monkeypatch.setattr(server, "_compute_project_listing_cache_key",
                        lambda _: hashlib.sha256(history.read_bytes()).hexdigest())
    with server._listing_read_snapshot():
        original = server._project_listing_cache_key("target")
        server._discard_listing_read_snapshot("target")
        assert "target" not in server._LISTING_CACHE_KEY_SNAPSHOT.get()
        history.write_bytes(b"after")
        assert server._project_listing_cache_key("target") != original


def test_snapshot_exception_does_not_leak_into_next_operation(monkeypatch):
    calls = []
    monkeypatch.setattr(server, "_compute_project_listing_cache_key",
                        lambda project: calls.append(project) or str(len(calls)))
    def fail_inside_snapshot():
        with server._listing_read_snapshot():
            assert server._project_listing_cache_key("target") == "1"
            raise RuntimeError("invalid final batch entry")
    with pytest.raises(RuntimeError, match="invalid final batch entry"):
        fail_inside_snapshot()
    assert server._LISTING_CACHE_KEY_SNAPSHOT.get() is None
    with server._listing_read_snapshot():
        assert server._project_listing_cache_key("target") == "2"


def test_expected_revision_read_hashes_subject_once(target, monkeypatch):
    expected = restoration.revisions("test")["revision"]
    original = restoration.revisions
    calls = []

    def counted(project):
        calls.append(project)
        return original(project)

    monkeypatch.setattr(restoration, "revisions", counted)
    result = restoration.execute("test", {"operation": "query", "kind": "symbols",
                                          "expected_revision": expected})
    assert result["revision"] == expected
    assert calls == ["test"]


def test_http_and_restoration_share_one_full_hash_under_target_lease(target, monkeypatch):
    from amiga_reversing.disasm.listing_projection import ListingProjectionService
    artifact = target.backend._LISTING_PROJECTION_SERVICE.valid_artifact("test", "native")
    service = ListingProjectionService()
    service.set_artifact(project_id="test", cache_key="native", artifact=artifact)
    paths = SimpleNamespace(target_dir=target.directory, binary_source=target.source)
    calls = []
    monkeypatch.setattr(restoration, "_server", lambda: server)
    monkeypatch.setattr(server, "get_project", lambda _: SimpleNamespace(target_dir=str(target.directory)))
    monkeypatch.setattr(server, "resolve_project_paths", lambda *a, **k: paths)
    monkeypatch.setattr(server, "_LISTING_PROJECTION_SERVICE", service)
    monkeypatch.setattr(server, "_compute_project_listing_cache_key", lambda project: calls.append(project) or "native")
    expected = restoration.revisions("test")["revision"]
    calls.clear()
    result = server.route_request("POST", "/api/projects/test/restoration", {},
                                  {"operation": "query", "kind": "symbols", "expected_revision": expected})
    assert result["data"]["revision"] == expected
    assert calls == ["test"]
    assert server._LISTING_CACHE_KEY_SNAPSHOT.get() is None


def test_same_stat_binary_change_still_refuses_stale_read(target):
    expected = restoration.revisions("test")["revision"]
    binary = target.directory / "binary.bin"
    stamp = binary.stat()
    binary.write_bytes(bytes.fromhex("4e754e75"))
    os.utime(binary, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    with pytest.raises(ValueError, match="stale_revision"):
        restoration.execute("test", {"operation": "query", "kind": "symbols",
                                     "expected_revision": expected})
    assert not target.calls


def test_cached_native_navigation_keeps_live_overlays_and_response_mutations_separate(monkeypatch):
    from amiga_reversing.disasm.listing_projection import ListingProjectionService

    class Artifact:
        def __init__(self):
            self.calls = 0

        def navigation_payload(self):
            self.calls += 1
            return {"groups": {"labels": [{"name": "native_label"}]}}, {}

        def close(self):
            pass

    artifact = Artifact()
    service = ListingProjectionService()
    service.set_artifact(project_id="demo", cache_key="a", artifact=artifact)
    note = {"body": "first review note"}
    monkeypatch.setattr(server, "_LISTING_PROJECTION_SERVICE", service)
    monkeypatch.setattr(server, "get_project", lambda _: SimpleNamespace(kind=server.ProjectKind.BINARY))
    monkeypatch.setattr(server, "_listing_read_artifact", lambda _: artifact)
    monkeypatch.setattr(server, "_project_listing_cache_key", lambda _: "a")
    monkeypatch.setattr(server, "_project_listing_generation", lambda _: "full")
    monkeypatch.setattr(server, "_active_reproduction_report", lambda _: None)
    monkeypatch.setattr(server, "_project_review_notes", lambda _: [note])

    first = server._route_request_unlocked("GET", "/api/projects/demo/listing/navigation", {})["data"]
    first["groups"]["labels"][0]["name"] = "response-only change"
    note["body"] = "updated review note"
    second = server._route_request_unlocked("GET", "/api/projects/demo/listing/navigation", {})["data"]
    assert artifact.calls == 1
    assert second["groups"]["labels"][0]["name"] == "native_label"
    assert second["groups"]["review-notes"][0]["match_text"] == "updated review note"
    native, _ = service.cached_native_navigation_payload(project_id="demo", artifact=artifact, current_cache_key="a")
    assert "review-notes" not in native["groups"]
