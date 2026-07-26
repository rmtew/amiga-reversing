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
