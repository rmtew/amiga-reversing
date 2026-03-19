from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import build_runtime_kb
from m68k import m68k_asm
from m68k.runtime_kb import (
    KNOWLEDGE,
    load_canonical_hunk_kb,
    load_canonical_m68k_kb,
    load_canonical_naming_rules,
    load_canonical_os_kb,
    load_hunk_runtime_kb,
    load_m68k_runtime_kb,
    load_naming_runtime_kb,
    load_os_runtime_kb,
)


def test_runtime_kb_generation_is_deterministic():
    script = Path(__file__).resolve().parent.parent / "scripts" / "build_runtime_kb.py"
    targets = [
        KNOWLEDGE / "runtime_m68k.py",
        KNOWLEDGE / "runtime_os.py",
        KNOWLEDGE / "runtime_hunk.py",
        KNOWLEDGE / "runtime_naming.py",
    ]
    before = {path: path.read_bytes() for path in targets}
    subprocess.run([sys.executable, str(script)], check=True)
    middle = {path: path.read_bytes() for path in targets}
    subprocess.run([sys.executable, str(script)], check=True)
    after = {path: path.read_bytes() for path in targets}
    assert before == middle == after


def test_runtime_size_encodings_match_canonical_structured_size_encoding():
    runtime = load_m68k_runtime_kb()["runtime"]["tables"]["size_encodings_asm"]
    expected = {}
    for inst in load_canonical_m68k_kb()["instructions"]:
        if "size_encoding" in inst:
            mapping = {
                entry["size"]: entry["bits"]
                for entry in inst["size_encoding"]["values"]
            }
            expected[inst["mnemonic"]] = mapping
    assert runtime == expected


def test_runtime_special_case_tables_match_canonical_data():
    payload = load_m68k_runtime_kb()
    runtime = payload["runtime"]["tables"]
    canonical = load_canonical_m68k_kb()
    by_name = {inst["mnemonic"]: inst for inst in canonical["instructions"]}

    expected_structured = {}
    for key, kb_mnemonic in canonical["_meta"]["asm_syntax_index"].items():
        mnemonic, _, raw_operand_types = key.partition(":")
        operand_types = tuple(raw_operand_types.split(",")) if raw_operand_types else ()
        expected_structured[(mnemonic, operand_types)] = kb_mnemonic
    assert runtime["asm_syntax_index"] == expected_structured

    assert runtime["addq_zero_means"] == by_name["ADDQ"]["constraints"]["immediate_range"]["zero_means"]

    expected_control = {}
    for entry in by_name["MOVEC"]["constraints"]["control_registers"]:
        expected_control.setdefault(int(entry["hex"], 16), entry["abbrev"])
    assert runtime["control_registers"] == expected_control

    assert payload["meta"]["_sp_reg_num"] == 7
    assert payload["meta"]["_num_data_regs"] == 8
    assert payload["meta"]["_num_addr_regs"] == 8
    assert runtime["asm_syntax_index"][("move", ("ea", "sr"))] == "MOVE to SR"
    expected_families = tuple(
        {
            "prefix": entry["prefix"],
            "canonical": entry["canonical"],
            "codes": tuple(entry["codes"]),
            "match_numeric_suffix": entry["match_numeric_suffix"],
            "exclude_from_family": tuple(entry["exclude_from_family"]),
        }
        for entry in canonical["_meta"]["condition_families"]
    )
    assert tuple(runtime["condition_families"]) == expected_families


def test_canonical_m68k_runtime_fields_are_structured():
    canonical = load_canonical_m68k_kb()
    assert canonical["_meta"]["condition_families"]
    for inst in canonical["instructions"]:
        if "size_encoding" in inst:
            assert inst["size_encoding"]["field"] == "SIZE"
            assert inst["size_encoding"]["values"]
    for mnemonic in ("DIVS, DIVSL", "DIVU, DIVUL", "MULS", "MULU"):
        inst = next(item for item in canonical["instructions"] if item["mnemonic"] == mnemonic)
        assert {
            entry["size"]: entry["bits"]
            for entry in inst["size_encoding"]["values"]
        } == {"w": 0, "l": 1}


def test_runtime_builder_requires_structured_size_encoding(monkeypatch):
    broken = copy.deepcopy(load_canonical_m68k_kb())
    target = next(inst for inst in broken["instructions"] if "size_encoding" in inst)
    del target["size_encoding"]

    def fake_load_json(name: str):
        if name == "m68k_instructions.json":
            return broken
        raise AssertionError(f"unexpected load for {name}")

    monkeypatch.setattr(build_runtime_kb, "_load_json", fake_load_json)
    with pytest.raises(KeyError, match="size_encoding"):
        build_runtime_kb._build_m68k_runtime()


def test_runtime_builder_requires_condition_families(monkeypatch):
    broken = copy.deepcopy(load_canonical_m68k_kb())
    del broken["_meta"]["condition_families"]

    def fake_load_json(name: str):
        if name == "m68k_instructions.json":
            return broken
        raise AssertionError(f"unexpected load for {name}")

    monkeypatch.setattr(build_runtime_kb, "_load_json", fake_load_json)
    with pytest.raises(KeyError, match="condition_families"):
        build_runtime_kb._build_m68k_runtime()


def test_runtime_loader_does_not_fallback_to_canonical_m68k(monkeypatch):
    load_m68k_runtime_kb.cache_clear()
    monkeypatch.setattr(
        "m68k.runtime_kb.load_canonical_m68k_kb",
        lambda: pytest.fail("canonical KB should not be loaded by runtime loader"),
    )
    try:
        payload = load_m68k_runtime_kb()
        assert payload["instructions"]
        assert payload["meta"]["condition_codes"]
    finally:
        load_m68k_runtime_kb.cache_clear()


def test_runtime_loader_requires_runtime_instructions(monkeypatch):
    load_m68k_runtime_kb.cache_clear()

    class FakeModule:
        RUNTIME = {"meta": {}, "tables": {}}

    monkeypatch.setattr("m68k.runtime_kb._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="instructions"):
            load_m68k_runtime_kb()
    finally:
        load_m68k_runtime_kb.cache_clear()


def test_runtime_loader_requires_runtime_meta(monkeypatch):
    load_m68k_runtime_kb.cache_clear()

    class FakeModule:
        RUNTIME = {"instructions": [], "tables": {}}

    monkeypatch.setattr("m68k.runtime_kb._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="meta"):
            load_m68k_runtime_kb()
    finally:
        load_m68k_runtime_kb.cache_clear()


def test_assembler_requires_kb_size_encoding(monkeypatch):
    move_inst = next(
        inst for inst in load_canonical_m68k_kb()["instructions"]
        if inst["mnemonic"] == "MOVE"
    )
    monkeypatch.setattr(m68k_asm, "_kb_size_encodings", lambda: {})
    with pytest.raises(KeyError, match="size encoding"):
        m68k_asm._get_size_encoding(move_inst, "w")


def test_runtime_os_is_compact_subset_of_canonical_os_kb():
    runtime = load_os_runtime_kb()
    canonical = load_canonical_os_kb()
    assert runtime["_meta"]["calling_convention"] == canonical["_meta"]["calling_convention"]
    assert runtime["_meta"]["exec_base_addr"] == canonical["_meta"]["exec_base_addr"]
    assert runtime["_meta"]["constant_domains"] == canonical["_meta"]["constant_domains"]
    assert runtime["structs"] == canonical["structs"]
    assert runtime["constants"] == canonical["constants"]
    for library, library_data in runtime["libraries"].items():
        source_library = canonical["libraries"][library]
        assert library_data["lvo_index"] == source_library["lvo_index"]
        for func_name, func_data in library_data["functions"].items():
            source_func = source_library["functions"][func_name]
            for key, value in func_data.items():
                assert source_func[key] == value


def test_runtime_hunk_and_naming_match_canonical_payloads():
    assert load_hunk_runtime_kb() == load_canonical_hunk_kb()
    assert load_naming_runtime_kb() == load_canonical_naming_rules()
