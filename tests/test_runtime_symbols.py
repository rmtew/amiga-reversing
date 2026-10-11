from __future__ import annotations

import json

import pytest

from amiga_reversing.tools import runtime_symbols


class _Artifact:
    _runtime_observation_views = ({"base_addr": 0x10000, "source_start": 0x200, "source_end": 0x400},)

    def analysis_payload(self):
        return ({"sections": [{
            "accepted_code_runs": [
                {"start_offset": 0x220, "end_offset": 0x230},
                {"start_offset": 0x240, "end_offset": 0x250},
            ],
            "symbol_origins": [
                {"origin_kind": "manual_label", "symbol_name": "accepted", "offset": 0x220},
                {"origin_kind": "manual_label", "symbol_name": "not_a_range", "offset": 0x222},
                {"origin_kind": "manual_label", "symbol_name": "ambiguous", "offset": 0x240},
                {"origin_kind": "manual_label", "symbol_name": "ambiguous", "offset": 0x220},
            ],
        }]}, {})


def test_eligible_functions_use_only_canonical_named_accepted_run_starts(monkeypatch) -> None:
    monkeypatch.setattr(runtime_symbols, "canonical_function_facts", lambda *_: {"functions": [
        {"name": "accepted", "entry_offset": 0x220, "status": "accepted", "ranges": [{"start_offset": 0x220, "end_offset": 0x230}]},
        {"name": "not_a_range", "entry_offset": 0x222, "status": "rejected", "reason": "entry_not_accepted_block"},
        {"name": "ambiguous", "entry_offset": 0x240, "status": "rejected", "reason": "overlapping_cfg_ownership"},
    ]})
    view, functions = runtime_symbols._eligible_functions("unused", _Artifact())

    assert view == {"base_addr": 0x10000, "source_start": 0x200, "source_end": 0x400}
    assert [(item.name, item.source_start, item.source_end) for item in functions] == [("accepted", 0x220, 0x230)]


def test_runtime_metadata_maps_nonzero_source_start_without_elf(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(runtime_symbols, "canonical_function_facts", lambda *_: {"functions": [
        {"name": "accepted", "entry_offset": 0x220, "status": "accepted", "ranges": [{"start_offset": 0x220, "end_offset": 0x230}]},
    ]})
    payload = runtime_symbols.generate_runtime_symbol_artifact("unused", tmp_path, artifact=_Artifact())

    assert payload["runtime_view"]["runtime_base"] == 0xFE00
    assert payload["functions"] == [{
        "name": "accepted", "source_start": 0x220, "source_end": 0x230,
        "runtime_start": 0x10020, "runtime_end": 0x10030,
    }]
    assert json.loads((tmp_path / "canonical-runtime-symbols.json").read_text()) == payload
    assert sorted(path.suffix for path in tmp_path.iterdir()) == [".json"]


def test_coverage_report_lists_only_symbol_decisions(monkeypatch) -> None:
    artifact = _Artifact()
    artifact.close = lambda: None
    monkeypatch.setattr(runtime_symbols, "build_project_listing_artifact_profile", lambda _: (0, {}, artifact))
    monkeypatch.setattr(runtime_symbols, "canonical_function_facts", lambda *_: {"functions": [
        {
            "name": "accepted",
            "entry_offset": 0x220,
            "status": "accepted",
            "ranges": [{"start_offset": 0x220, "end_offset": 0x230}],
        },
        {"name": "ambiguous", "entry_offset": 0x240, "status": "rejected", "reason": "overlapping_cfg_ownership"},
    ]})

    report = runtime_symbols.symbol_coverage_report("unused")

    assert report["counts"] == {"emitted": 1, "omitted": 1}
    assert report["emitted"] == [{"name": "accepted", "source_start": 0x220, "source_end": 0x230, "range_count": 1}]
    assert report["omitted"] == [{"name": "ambiguous", "entry_offset": 0x240, "reason": "overlapping_cfg_ownership"}]


def test_eligible_functions_reject_noncontiguous_ranges() -> None:
    functions, omitted = runtime_symbols._runtime_eligible_facts([
        {
            "name": "split_function",
            "entry_offset": 0x220,
            "status": "accepted",
            "ranges": [
                {"start_offset": 0x220, "end_offset": 0x230},
                {"start_offset": 0x240, "end_offset": 0x250},
            ],
        },
    ])

    assert functions == []
    assert omitted == [{"name": "split_function", "entry_offset": 0x220, "reason": "noncontiguous_function_ranges"}]


@pytest.mark.parametrize("views", [
    (),
    ({"base_addr": 0x10000, "source_start": 0, "source_end": 0x400},) * 2,
    ({"base_addr": 0x10000, "source_start": 0x400, "source_end": 0x200},),
    ({"base_addr": 0xFFFFFF, "source_start": 0, "source_end": 4},),
])
def test_runtime_view_rejects_missing_ambiguous_and_invalid_mapping(views) -> None:
    artifact = _Artifact()
    artifact._runtime_observation_views = views
    with pytest.raises(ValueError, match="[Rr]untime"):
        runtime_symbols._single_runtime_view(artifact)


@pytest.mark.parametrize("facts", [
    [{"name": "outside", "entry_offset": 0x100, "status": "accepted", "ranges": [{"start_offset": 0x100, "end_offset": 0x110}]}],
    [
        {"name": "duplicate", "entry_offset": 0x220, "status": "accepted", "ranges": [{"start_offset": 0x220, "end_offset": 0x230}]},
        {"name": "duplicate", "entry_offset": 0x240, "status": "accepted", "ranges": [{"start_offset": 0x240, "end_offset": 0x250}]},
    ],
])
def test_metadata_rejects_out_of_view_or_ambiguous_functions(monkeypatch, facts, tmp_path) -> None:
    monkeypatch.setattr(runtime_symbols, "canonical_function_facts", lambda *_: {"functions": facts})
    with pytest.raises(ValueError, match="Accepted"):
        runtime_symbols.generate_runtime_symbol_artifact("unused", tmp_path, artifact=_Artifact())
    assert not list(tmp_path.iterdir())


def test_owned_artifact_closes_on_invalid_facts(monkeypatch, tmp_path) -> None:
    artifact = _Artifact()
    closed = []
    artifact.close = lambda: closed.append(True)
    monkeypatch.setattr(runtime_symbols, "build_project_listing_artifact_profile", lambda _: (0, {}, artifact))
    monkeypatch.setattr(runtime_symbols, "canonical_function_facts", lambda *_: {"functions": [None]})
    with pytest.raises(ValueError, match="malformed entry"):
        runtime_symbols.generate_runtime_symbol_artifact("unused", tmp_path)
    assert closed == [True]


def test_empty_function_metadata_supports_source_row_scenarios(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(runtime_symbols, "canonical_function_facts", lambda *_: {"functions": []})
    payload = runtime_symbols.generate_runtime_symbol_artifact("unused", tmp_path, artifact=_Artifact())
    assert payload["functions"] == []
    assert payload["runtime_view"]["runtime_base"] == 0xFE00
    assert [path.name for path in tmp_path.iterdir()] == ["canonical-runtime-symbols.json"]
