"""Range annotations share a revision snapshot without caching future requests."""

import pytest

from amiga_reversing.disasm import server
from amiga_reversing.disasm.listing_projection import ListingProjectionService


def setup_range(monkeypatch, count=3, native=True):
    service = ListingProjectionService()
    rows = [dict(row_key=f"row-{i}", kind="data", section_index=0,
                 start_offset=2*i, end_offset=2*i+2) for i in range(count)]
    monkeypatch.setattr(server, "_LISTING_PROJECTION_SERVICE", service)
    monkeypatch.setattr(server, "_project_listing_cache_key", lambda _: "revision")
    monkeypatch.setattr(service, "projection_hash", lambda **_: "revision")
    class Artifact:
        calls = 0

        def row_for_source_offset(self, *, section_index, offset):
            self.calls += 1
            if section_index == 0 and 0 <= offset < count*2:
                return dict(rows[offset//2])
            return None

    artifact = Artifact()
    monkeypatch.setattr(server, "_valid_c_listing_artifact", lambda _: artifact if native else None)

    def all_rows(_):
        assert not native, "native ranges must not materialize the complete listing"
        return rows

    monkeypatch.setattr(server, "_all_listing_rows", all_rows)
    calls = []

    def metadata(project):
        calls.append(project)
        return [dict(hunk=0, addr=0, end=2*count, seed_id=f"seed-{len(calls)}")]

    monkeypatch.setattr(server, "_target_suppressible_seeded_items", metadata)
    locators = [service.locator_for_row(target_id="demo", projection_hash="revision",
                                      row=row).to_dict() for row in rows]
    return rows, locators, calls, artifact


def test_large_range_uses_one_annotation_snapshot_and_refreshes_next_request(monkeypatch):
    # The current Starglider sample selection contains 1,180 listing rows.
    original, locators, calls, artifact = setup_range(monkeypatch, 1180)
    for request in (1, 2):
        rows, revision = server._resolve_command_range_locators("demo", locators)
        assert revision == "revision"
        assert len(rows) == 1180
        assert {row["suppressible_seeded_items"][0]["seed_id"] for row in rows} == {f"seed-{request}"}
        assert len(calls) == request
        assert artifact.calls == request * 1180
    assert all("suppressible_seeded_items" not in row for row in original)


@pytest.mark.parametrize("native", [True, False])
@pytest.mark.parametrize("failure", ["stale", "duplicate"])
def test_range_snapshot_preserves_locator_refusals(monkeypatch, failure, native):
    _, locators, _, _ = setup_range(monkeypatch, native=native)
    if failure == "stale":
        locators[1] = {**locators[1], "projection_hash": "old-revision", "start_offset": 99999}
    else:
        locators[1] = dict(locators[0])
    with pytest.raises(server.CommandContractError) as exc:
        server._resolve_command_range_locators("demo", locators)
    assert exc.value.code == ("stale_locator" if failure == "stale" else "ambiguous_locator")


@pytest.mark.parametrize("native", [True, False])
def test_unique_stale_identity_recovery_is_preserved(monkeypatch, native):
    _, locators, calls, _ = setup_range(monkeypatch, native=native)
    locators[1] = {**locators[1], "projection_hash": "old-revision", "row_key": "old-row"}
    rows, _ = server._resolve_command_range_locators("demo", locators)
    assert [row["row_key"] for row in rows] == ["row-0", "row-1", "row-2"]
    assert len(calls) == 1
