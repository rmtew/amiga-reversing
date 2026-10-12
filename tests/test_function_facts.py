from __future__ import annotations

from amiga_reversing.disasm import function_facts


class _Projection:
    labels = (
        {"name": "first", "addr": 0x10200, "address_domain": "runtime"},
        {"name": "second", "addr": 0x10220, "address_domain": "runtime"},
    )


def test_function_facts_own_multiple_blocks_and_reject_overlap(monkeypatch) -> None:
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: _Projection())
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [
        {"start_offset": 0x200, "end_offset": 0x204},
        {"start_offset": 0x204, "end_offset": 0x208},
        {"start_offset": 0x220, "end_offset": 0x224},
    ], "edges": [
        {"source_block_index": 0, "target_block_index": 1, "kind": 1},
        {"source_block_index": 2, "target_block_index": 1, "kind": 1},
    ]}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert [(item["name"], item["status"], item.get("reason")) for item in result["functions"]] == [
        ("first", "rejected", "overlapping_cfg_ownership"),
        ("second", "rejected", "overlapping_cfg_ownership"),
    ]


def test_function_facts_keep_shared_return_block(monkeypatch) -> None:
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: _Projection())
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [
        {"start_offset": 0x200, "end_offset": 0x204},
        {"start_offset": 0x204, "end_offset": 0x208},
        {"start_offset": 0x220, "end_offset": 0x224},
    ], "edges": [
        {"source_block_index": 0, "target_block_index": 1, "kind": 1},
        {"source_block_index": 2, "target_block_index": 1, "kind": 1},
        {"source_block_index": 1, "target_block_index": 0xFFFFFFFF, "kind": 5},
    ]}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert [item["status"] for item in result["functions"]] == ["accepted", "accepted"]
    assert result["functions"][0]["shared_terminal_blocks"] == [{"start_offset": 0x204, "end_offset": 0x208}]


def test_function_facts_record_all_cfg_owned_blocks(monkeypatch) -> None:
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: _Projection())
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [
        {"start_offset": 0x200, "end_offset": 0x204},
        {"start_offset": 0x204, "end_offset": 0x208},
        {"start_offset": 0x220, "end_offset": 0x224},
    ], "edges": [
        {"source_block_index": 0, "target_block_index": 1, "kind": 1},
    ]}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    first, second = result["functions"]
    assert first["status"] == "accepted"
    assert first["ranges"] == [{"start_offset": 0x200, "end_offset": 0x208}]
    assert first["owned_blocks"] == [
        {"start_offset": 0x200, "end_offset": 0x204},
        {"start_offset": 0x204, "end_offset": 0x208},
    ]
    assert second["status"] == "accepted"
    assert second["ranges"] == [{"start_offset": 0x220, "end_offset": 0x224}]


def test_function_facts_reject_unresolved_flow_target(monkeypatch) -> None:
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: _Projection())
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [{"start_offset": 0x200, "end_offset": 0x204}], "edges": [
        {"source_block_index": 0, "target_block_index": 0xFFFFFFFF, "kind": 4},
    ]}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert result["functions"][0]["reason"] == "unresolved_cfg_flow_target"
    assert result["functions"][0]["evidence"] == {"entry": "manual_label", "ownership": "rejected_cfg_flow"}


def test_function_facts_reject_multiple_names_for_one_entry(monkeypatch) -> None:
    projection = type("Projection", (), {"labels": (
        {"name": "first_name", "addr": 0x10200, "address_domain": "runtime"},
        {"name": "second_name", "addr": 0x10200, "address_domain": "runtime"},
    )})()
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: projection)
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [{"start_offset": 0x200, "end_offset": 0x204}], "edges": []}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert [(item["name"], item["reason"]) for item in result["functions"]] == [
        ("first_name", "ambiguous_entry_names"),
        ("second_name", "ambiguous_entry_names"),
    ]


def test_function_facts_reject_named_entry_inside_owned_block(monkeypatch) -> None:
    projection = type("Projection", (), {"labels": (
        {"name": "outer", "addr": 0x10200, "address_domain": "runtime"},
        {"name": "interior", "addr": 0x10202, "address_domain": "runtime"},
    )})()
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: projection)
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [{"start_offset": 0x200, "end_offset": 0x204}], "edges": []}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert [(item["name"], item["reason"]) for item in result["functions"]] == [
        ("outer", "named_entry_inside_owned_block"),
        ("interior", "entry_not_accepted_block"),
    ]


def test_analysis_functions_use_entries_not_labels_and_cover_sections() -> None:
    analysis = {"sections": [
        {"section_index": 0, "blocks": [
            {"start_offset": 0, "end_offset": 4, "certainty": 1},
            {"start_offset": 4, "end_offset": 8, "certainty": 1},
            {"start_offset": 16, "end_offset": 20, "certainty": 1},
        ], "code_start_refs": [{"offset": 0, "reason_name": "section_entry"}],
         "symbol_origins": [{"offset": 4, "symbol_name": "interior_label"},
                            {"offset": 16, "symbol_name": "manual_callee", "origin_kind": "manual_label"}],
         "edges": [
             {"source_block_index": 0, "target_block_index": 2, "source_offset": 0, "target_offset": 16, "kind": 3},
             {"source_block_index": 0, "target_block_index": 1, "source_offset": 0, "target_offset": 4, "kind": 1},
             {"source_block_index": 1, "target_block_index": 0xFFFFFFFF, "source_offset": 4, "target_offset": 0xFFFFFFFF, "kind": 4},
             {"source_block_index": 2, "target_block_index": 0xFFFFFFFF, "source_offset": 16, "target_offset": 0xFFFFFFFF, "kind": 5},
         ]},
        {"section_index": 2, "blocks": [{"start_offset": 0, "end_offset": 2}], "edges": [],
         "code_start_refs": [{"offset": 0, "reason_name": "policy_entry_point"}]},
    ]}
    result = function_facts.analysis_function_facts("test", analysis)
    first, callee, other = result["functions"]
    assert [(f["section_index"], f["entry_offset"]) for f in result["functions"]] == [(0, 0), (0, 16), (2, 0)]
    assert first["ranges"] == [{"start_offset": 0, "end_offset": 8}]
    assert first["ownership_status"] == "partial"
    assert first["callees"][0]["target_offset"] == 16
    assert first["unresolved_transfers"][0]["kind"] == "jump"
    assert callee["name"] == "manual_callee"
    assert callee["callers"][0]["source_entries"] == [0]
    assert callee["unresolved_transfers"] == []  # Dynamic returns are expected.
    assert other["name"] is None
    assert "native_cfg_is_section_local" in result["unknowns"]


def test_analysis_functions_retain_unsupported_and_shared_candidates() -> None:
    result = function_facts.analysis_function_facts("test", {"sections": [{
        "section_index": 0,
        "blocks": [{"start_offset": 0, "end_offset": 2}, {"start_offset": 4, "end_offset": 6},
                   {"start_offset": 8, "end_offset": 10}],
        "code_start_refs": [{"offset": x, "reason_name": "policy_entry_offset"} for x in (0, 4, 12)],
        "edges": [{"source_block_index": i, "target_block_index": 2, "source_offset": x,
                   "target_offset": 8, "kind": 4} for i, x in enumerate((0, 4))],
    }]})
    first, second, unavailable = result["functions"]
    assert first["ownership_status"] == second["ownership_status"] == "ambiguous"
    assert first["shared_block_starts"] == [8]
    assert unavailable["ownership_status"] == "unavailable"
    assert unavailable["ranges"] == []
    assert "entry_not_accepted_block" in unavailable["unknowns"]


def test_analysis_function_resolved_offset_without_block_is_partial() -> None:
    result = function_facts.analysis_function_facts("test", {"sections": [{
        "section_index": 0,
        "blocks": [{"start_offset": 0, "end_offset": 2}],
        "code_start_refs": [{"offset": 0, "reason_name": "section_entry"}],
        "edges": [{"source_block_index": 0, "target_block_index": 0xFFFFFFFF,
                   "source_offset": 0, "target_offset": 8, "kind": 4}],
    }]})
    fact = result["functions"][0]
    assert fact["ownership_status"] == "partial"
    assert "flow_target_not_accepted_block" in fact["unknowns"]
