"""Tests for the shared disassembly session/row pipeline."""

import io
from pathlib import Path
from types import SimpleNamespace

import pytest

from disasm import cli as gen_disasm_mod
from disasm.comments import build_instruction_comment_parts, render_comment_parts
from disasm import data_render as data_render_mod
from disasm.analysis_loader import load_hunk_analysis
from disasm.entities import infer_target_name, load_entities
from disasm.hunks import (build_hunk_session, build_session_object,
                          prepare_hunk_code)
from disasm.metadata import build_hunk_metadata
from disasm.hint_validation import (hint_block_has_supported_terminal_flow,
                                    is_valid_hint_block)
from disasm.jump_tables import emit_jump_table_rows
from disasm.substitutions import (build_app_offset_symbols,
                                  build_arg_substitutions,
                                  build_lvo_substitutions)
from disasm.api import listing_window_payload, serialize_row, session_metadata
from disasm import emitter as emitter_mod
from disasm.emitter import emit_session_rows
from disasm.text import listing_window, render_rows
from disasm.types import (DisassemblySession, HunkDisassemblySession,
                          ListingRow, SemanticOperand)
from m68k.m68k_executor import Instruction
from m68k.kb_util import KB
from disasm.validation import get_instruction_processor_min, has_valid_branch_target
from disasm.validation import get_instruction_processor_min


def test_load_entities_reads_jsonl(tmp_path):
    entities_path = tmp_path / "entities.jsonl"
    entities_path.write_text(
        '{"addr":"0000","type":"code"}\n'
        '\n'
        '{"addr":"0010","type":"data"}\n',
        encoding="utf-8",
    )

    assert load_entities(entities_path) == [
        {"addr": "0000", "type": "code"},
        {"addr": "0010", "type": "data"},
    ]


def test_infer_target_name_prefers_target_dir(tmp_path):
    target_dir = tmp_path / "demo"
    entities_path = target_dir / "entities.jsonl"

    assert infer_target_name(target_dir, entities_path) == "demo"


def test_infer_target_name_falls_back_to_entities_parent(tmp_path):
    entities_path = tmp_path / "demo" / "entities.jsonl"

    assert infer_target_name(None, entities_path) == "demo"


def test_build_lvo_substitutions_collects_direct_jsr_substitution():
    call = {"library": "dos.library", "function": "OpenLibrary", "lvo": -552, "addr": 0x20}

    lvo_equs, lvo_substitutions = build_lvo_substitutions(
        blocks={},
        lib_calls=[call],
        hunk_entities=[],
        kb=KB(),
    )

    assert lvo_equs == {"dos.library": {-552: "_LVOOpenLibrary"}}
    assert lvo_substitutions == {0x20: ("-552(", "_LVOOpenLibrary(")}


def test_build_arg_substitutions_collects_immediate_constant():
    setter = Instruction(
        offset=0x10,
        size=4,
        opcode=0x7001,
        text="corrupted",
        raw=b"\x70\x01",
        kb_mnemonic="moveq",
        operand_size="l",
        operand_texts=("#1", "d0"),
    )
    block = type("Block", (), {
        "instructions": [
            setter,
            Instruction(
                offset=0x20,
                size=2,
                opcode=0x4E75,
                text="jsr     _LVOOpenLibrary(a6)",
                raw=b"\x4E\x75",
                kb_mnemonic="jsr",
                operand_size="w",
                operand_texts=("_LVOOpenLibrary(a6)",),
            ),
        ]
    })()
    os_kb = {
        "_meta": {"constant_domains": {"OpenLibrary": ["OL_TAG"]}},
        "constants": {"OL_TAG": {"value": 1}},
        "libraries": {
            "dos.library": {
                "functions": {
                    "OpenLibrary": {"inputs": [{"reg": "d0"}]}
                }
            }
        },
    }

    arg_equs, arg_substitutions = build_arg_substitutions(
        blocks={0x20: block},
        hunk_entities=[],
        lib_calls=[{"library": "dos.library", "function": "OpenLibrary", "block": 0x20, "addr": 0x20}],
        os_kb=os_kb,
        kb=KB(),
    )

    assert arg_equs == {"OL_TAG": 1}
    assert arg_substitutions == {0x10: ("#1", "#OL_TAG")}


def test_build_arg_substitutions_collects_dispatch_call_constant():
    setter = Instruction(
        offset=0x12,
        size=2,
        opcode=0x76FF,
        text="corrupted",
        raw=b"\x76\xff",
        kb_mnemonic="moveq",
        operand_size="l",
        operand_texts=("#-1", "d3"),
    )
    branch = Instruction(
        offset=0x16,
        size=4,
        opcode=0x6100,
        text="bsr.w   $40",
        raw=b"\x61\x00\x00\x28",
        kb_mnemonic="bsr",
        operand_size="w",
        operand_texts=("$40",),
    )
    block = type("Block", (), {
        "instructions": [
            Instruction(
                offset=0x10,
                size=2,
                opcode=0x2F03,
                text="move.l  d3,-(sp)",
                raw=b"\x2f\x03",
                kb_mnemonic="move",
                operand_size="l",
                operand_texts=("d3", "-(sp)"),
            ),
            setter,
            Instruction(
                offset=0x14,
                size=2,
                opcode=0x70BE,
                text="moveq   #-66,d0",
                raw=b"\x70\xbe",
                kb_mnemonic="moveq",
                operand_size="l",
                operand_texts=("#-66", "d0"),
            ),
            branch,
        ]
    })()
    os_kb = {
        "_meta": {"constant_domains": {"Seek": ["OFFSET_BEGINNING", "OFFSET_CURRENT"]}},
        "constants": {
            "OFFSET_BEGINNING": {"value": -1},
            "OFFSET_CURRENT": {"value": 0},
        },
        "libraries": {
            "dos.library": {
                "functions": {
                    "Seek": {
                        "inputs": [
                            {"reg": "d1"},
                            {"reg": "d2"},
                            {"reg": "d3"},
                        ]
                    }
                }
            }
        },
    }

    arg_equs, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[{
            "library": "dos.library",
            "function": "Seek",
            "block": 0x10,
            "addr": 0x10,
            "dispatch": 0x42,
        }],
        hunk_entities=[{"addr": "0040", "end": "0050", "type": "code"}],
        os_kb=os_kb,
        kb=KB(),
    )

    assert arg_equs == {"OFFSET_BEGINNING": -1}
    assert arg_substitutions == {0x12: ("#-1", "#OFFSET_BEGINNING")}


def test_build_lvo_substitutions_collects_dispatch_call_lvo_constant():
    branch = Instruction(
        offset=0x16,
        size=4,
        opcode=0x6100,
        text="bsr.w   $40",
        raw=b"\x61\x00\x00\x28",
        kb_mnemonic="bsr",
        operand_size="w",
        operand_texts=("$40",),
    )
    block = type("Block", (), {
        "instructions": [
            Instruction(
                offset=0x12,
                size=2,
                opcode=0x70BE,
                text="moveq   #-66,d0",
                raw=b"\x70\xbe",
                kb_mnemonic="moveq",
                operand_size="l",
                operand_texts=("#-66", "d0"),
            ),
            branch,
        ]
    })()

    lvo_equs, lvo_substitutions = build_lvo_substitutions(
        blocks={0x10: block},
        lib_calls=[{
            "library": "dos.library",
            "function": "Seek",
            "lvo": -66,
            "addr": 0x10,
            "dispatch": 0x42,
        }],
        hunk_entities=[{"addr": "0040", "end": "0050", "type": "code"}],
        kb=KB(),
    )

    assert lvo_equs == {"dos.library": {-66: "_LVOSeek"}}
    assert lvo_substitutions == {0x12: ("#-66", "#_LVOSeek")}


def test_build_app_offset_symbols_prefers_initial_mem_and_typed_slots():
    class FakeInitMem:
        _tags = {
            (0x1020, 4): {"library_base": "dos.library"},
        }

    app_offsets = build_app_offset_symbols(
        blocks={},
        lib_calls=[],
        platform={"initial_base_reg": (6, 0x1000), "_initial_mem": FakeInitMem()},
    )

    assert app_offsets == {0x20: "app_dos_base"}


def test_prepare_hunk_code_relocates_payload_segment():
    code, code_size, relocated_segments, reloc_file_offset, reloc_base_addr = prepare_hunk_code(
        b"\xAA\xBB\x11\x22",
        [{"file_offset": 2, "base_addr": 6}],
    )

    assert code == b"\xAA\xBB\x00\x00\x00\x00\x11\x22"
    assert code_size == 8
    assert relocated_segments == [{"file_offset": 2, "base_addr": 6}]
    assert reloc_file_offset == 2
    assert reloc_base_addr == 6


def test_build_session_object_uses_binary_analysis_suffix(tmp_path):
    binary_path = tmp_path / "demo.bin"
    entities_path = tmp_path / "entities.jsonl"
    output_path = tmp_path / "demo.s"

    session = build_session_object(
        target_name="demo",
        binary_path=binary_path,
        entities_path=entities_path,
        output_path=output_path,
        entities=[],
        hunk_sessions=[],
        profile_stages=True,
    )

    assert session.target_name == "demo"
    assert session.analysis_cache_path == binary_path.with_suffix(".analysis")
    assert session.output_path == output_path
    assert session.profile_stages is True


def test_build_hunk_session_preserves_metadata_and_analysis_fields():
    session = build_hunk_session(
        hunk_index=1,
        code=b"\x00\x01",
        code_size=2,
        entities=[{"addr": "0000", "type": "code"}],
        blocks={"b": 1},
        hint_blocks={"h": 2},
        code_addrs={0, 1},
        hint_addrs={2},
        reloc_map={0: 0x40},
        reloc_target_set={0x40},
        pc_targets={0x20: "pcref_0020"},
        string_addrs={0x20},
        core_absolute_targets={0x40},
        labels={0x40: "loc_0040"},
        jump_table_regions={0x10: {"pattern": "word_table"}},
        jump_table_target_sources={0x80: ["loc_0040"]},
        struct_map={0x00: {"a0": {"struct": "Foo", "fields": {}}}},
        lvo_equs={"dos.library": {-552: "_LVOOpenLibrary"}},
        lvo_substitutions={0x10: ("-552(", "_LVOOpenLibrary(")},
        arg_equs={"OL_TAG": 1},
        arg_substitutions={0x12: ("#1", "#OL_TAG")},
        app_offsets={0x20: "app_dos_base"},
        arg_annotations={0x30: {"d0": "name"}},
        data_access_sizes={0x40: 2},
        platform={"initial_base_reg": (6, 0x1000)},
        os_kb={"structs": {}},
        kb=KB(),
        fixed_abs_addrs={0x0004},
        base_addr=0x400,
        code_start=2,
        relocated_segments=[{"file_offset": 0, "base_addr": 0}],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    assert session.hunk_index == 1
    assert session.code == b"\x00\x01"
    assert session.jump_table_target_sources == {0x80: ["loc_0040"]}
    assert session.lvo_substitutions == {0x10: ("-552(", "_LVOOpenLibrary(")}
    assert session.app_offsets == {0x20: "app_dos_base"}


def test_build_hunk_metadata_collects_code_and_hint_addresses():
    block = type("Block", (), {"start": 0x10, "end": 0x14, "successors": [], "instructions": []})()
    hint_block = type("Block", (), {"start": 0x20, "end": 0x22, "successors": [], "instructions": []})()
    ha = type("Analysis", (), {
        "blocks": {0x10: block},
        "hint_blocks": {0x20: hint_block},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [],
    })()

    metadata = build_hunk_metadata(
        code=b"\x00" * 0x40,
        code_size=0x40,
        hunk_index=0,
        hunk_entities=[],
        ha=ha,
        hf_hunks=[],
        kb=KB(),
        fixed_abs_addrs=set(),
    )

    assert metadata["code_addrs"] == {0x10, 0x11, 0x12, 0x13}
    assert metadata["hint_addrs"] == {0x20, 0x21}


def test_build_hunk_metadata_builds_word_table_regions_and_sources():
    block = type("Block", (), {"start": 0x10, "end": 0x14, "successors": [], "instructions": []})()
    ha = type("Analysis", (), {
        "blocks": {0x10: block},
        "hint_blocks": {},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [{
            "addr": 0x30,
            "pattern": "word_table",
            "base_addr": 0x50,
            "targets": [0x80, 0x90],
            "table_end": 0x34,
        }],
    })()

    metadata = build_hunk_metadata(
        code=b"\x00" * 0x100,
        code_size=0x100,
        hunk_index=0,
        hunk_entities=[],
        ha=ha,
        hf_hunks=[],
        kb=KB(),
        fixed_abs_addrs=set(),
    )

    assert metadata["jump_table_regions"][0x30]["entries"] == [(0x30, 0x80), (0x32, 0x90)]
    assert metadata["jump_table_regions"][0x30]["base_label"] == "loc_0050"
    assert metadata["jump_table_target_sources"] == {
        0x80: ["loc_0050"],
        0x90: ["loc_0050"],
    }


def test_load_hunk_analysis_uses_cache_when_present(tmp_path, monkeypatch):
    binary_path = tmp_path / "demo.bin"
    cache_path = binary_path.with_suffix(".analysis")
    cache_path.write_text("cache", encoding="utf-8")
    sentinel = object()
    seen = {}

    def fake_load(path, os_kb):
        seen["path"] = path
        seen["os_kb"] = os_kb
        return sentinel

    monkeypatch.setattr("disasm.analysis_loader.HunkAnalysis.load", fake_load)
    monkeypatch.setattr("disasm.analysis_loader.load_os_kb", lambda: {"ok": True})

    result = load_hunk_analysis(
        binary_path=binary_path,
        code=b"\x00\x00",
        relocs=[],
        hunk_index=0,
        base_addr=0,
        code_start=0,
    )

    assert result is sentinel
    assert seen == {"path": cache_path, "os_kb": {"ok": True}}


def test_load_hunk_analysis_runs_analysis_without_cache(tmp_path, monkeypatch):
    binary_path = tmp_path / "demo.bin"
    seen = {}

    class FakeAnalysis:
        def save(self, path):
            seen["saved_path"] = path

    sentinel = FakeAnalysis()

    def fake_analyze_hunk(code, relocs, hunk_index, base_addr, code_start):
        seen["args"] = (code, relocs, hunk_index, base_addr, code_start)
        return sentinel

    monkeypatch.setattr("disasm.analysis_loader.analyze_hunk", fake_analyze_hunk)

    result = load_hunk_analysis(
        binary_path=binary_path,
        code=b"\x01\x02",
        relocs=[("r", 1)],
        hunk_index=3,
        base_addr=0x400,
        code_start=2,
    )

    assert result is sentinel
    assert seen["args"] == (b"\x01\x02", [("r", 1)], 3, 0x400, 2)
    assert seen["saved_path"] == binary_path.with_suffix(".analysis")


def test_load_hunk_analysis_rebuilds_stale_cache(tmp_path, monkeypatch):
    binary_path = tmp_path / "demo.bin"
    cache_path = binary_path.with_suffix(".analysis")
    cache_path.write_text("stale", encoding="utf-8")
    seen = {}

    class FakeAnalysis:
        def save(self, path):
            seen["saved_path"] = path

    sentinel = FakeAnalysis()

    def fake_load(path, os_kb):
        seen["load"] = (path, os_kb)
        from m68k.analysis import AnalysisCacheError
        raise AnalysisCacheError("Cache version mismatch")

    def fake_analyze_hunk(code, relocs, hunk_index, base_addr, code_start):
        seen["analyze"] = (code, relocs, hunk_index, base_addr, code_start)
        return sentinel

    monkeypatch.setattr("disasm.analysis_loader.HunkAnalysis.load", fake_load)
    monkeypatch.setattr("disasm.analysis_loader.analyze_hunk", fake_analyze_hunk)
    monkeypatch.setattr("disasm.analysis_loader.load_os_kb", lambda: {"ok": True})

    result = load_hunk_analysis(
        binary_path=binary_path,
        code=b"\x01\x02",
        relocs=[("r", 1)],
        hunk_index=3,
        base_addr=0x400,
        code_start=2,
    )

    assert result is sentinel
    assert seen["load"] == (cache_path, {"ok": True})
    assert seen["analyze"] == (b"\x01\x02", [("r", 1)], 3, 0x400, 2)
    assert seen["saved_path"] == cache_path


def test_load_hunk_analysis_does_not_hide_non_cache_value_errors(tmp_path, monkeypatch):
    binary_path = tmp_path / "demo.bin"
    cache_path = binary_path.with_suffix(".analysis")
    cache_path.write_text("broken", encoding="utf-8")

    def fake_load(path, os_kb):
        raise ValueError("unexpected parse bug")

    monkeypatch.setattr("disasm.analysis_loader.HunkAnalysis.load", fake_load)
    monkeypatch.setattr("disasm.analysis_loader.load_os_kb", lambda: {"ok": True})

    with pytest.raises(ValueError, match="unexpected parse bug"):
        load_hunk_analysis(
            binary_path=binary_path,
            code=b"\x01\x02",
            relocs=[],
            hunk_index=0,
            base_addr=0,
            code_start=0,
        )


def test_render_rows_concatenates_listing_text():
    rows = [
        ListingRow(row_id="a", kind="comment", text="; one\n"),
        ListingRow(row_id="b", kind="instruction", text="moveq #0,d0\n"),
    ]

    assert render_rows(rows) == "; one\nmoveq #0,d0\n"


def test_render_comment_parts_joins_non_empty_parts():
    assert render_comment_parts(("68020+", "", "note")) == "68020+; note"


def test_build_instruction_comment_parts_prefers_app_offset_before_ascii():
    inst = Instruction(
        offset=0x10,
        size=6,
        opcode=0x203C,
        text="corrupted",
        raw=b"\x20\x3C\x4C\x49\x4E\x45",
        kb_mnemonic="move",
        operand_size="l",
        operand_texts=("#$4C494E45", "568(a6)"),
    )
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        core_absolute_targets=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        struct_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform={"initial_base_reg": (6, "a6")},
        os_kb={"structs": {}},
        kb=KB(),
        fixed_abs_addrs=set(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    parts = build_instruction_comment_parts(
        inst,
        session,
        operand_parts=(
            SimpleNamespace(kind="immediate", value=0x4C494E45,
                            base_register=None, displacement=None,
                            text="#$4C494E45"),
            SimpleNamespace(kind="base_displacement", value=568,
                            base_register="a6", displacement=568,
                            text="568(a6)"),
        ))

    assert parts == ("app+$238",)


def test_build_instruction_comment_parts_uses_instruction_processor_min_not_text():
    inst = Instruction(
        offset=0x10,
        size=2,
        opcode=0x49C0,
        text="corrupted",
        raw=b"\x49\xC0",
        kb_mnemonic="extb",
        operand_size="l",
    )
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        core_absolute_targets=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        struct_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform={},
        os_kb={"structs": {}},
        kb=KB(),
        fixed_abs_addrs=set(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    parts = build_instruction_comment_parts(
        inst,
        session,
        operand_parts=(
            SimpleNamespace(kind="register", value=None,
                            base_register=None, displacement=None,
                            text="d0"),
        ))
    assert parts == ("68020+",)


def test_render_instruction_text_requires_opcode_text():
    inst = Instruction(
        offset=0x10,
        size=2,
        opcode=0x49C0,
        text="corrupted",
        raw=b"\x49\xC0",
        kb_mnemonic="extb",
        operand_size="l",
        operand_texts=("d0",),
    )
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        core_absolute_targets=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        struct_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform={},
        os_kb={"structs": {}},
        kb=KB(),
        fixed_abs_addrs=set(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    from disasm.instruction_rows import render_instruction_text

    try:
        render_instruction_text(inst, session, set())
    except ValueError as exc:
        assert "missing opcode_text" in str(exc)
    else:
        raise AssertionError("expected missing opcode_text")


def test_build_instruction_comment_parts_uses_decoded_immediate_not_rendered_text():
    inst = Instruction(
        offset=0x38,
        size=6,
        opcode=0x203C,
        text="corrupted",
        raw=b"\x20\x3C\x4C\x49\x4E\x45",
        kb_mnemonic="move",
        operand_size="l",
        operand_texts=("#$4C494E45", "d0"),
    )
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        core_absolute_targets=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        struct_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform={},
        os_kb={"structs": {}},
        kb=KB(),
        fixed_abs_addrs=set(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    parts = build_instruction_comment_parts(
        inst,
        session,
        operand_parts=(
            SimpleNamespace(kind="immediate", value=0x4C494E45,
                            base_register=None, displacement=None,
                            text="#$4C494E45"),
            SimpleNamespace(kind="register", value=None,
                            base_register=None, displacement=None,
                            text="d0"),
        ))

    assert parts == ("'LINE'",)


def test_get_instruction_processor_min_reports_base_68000_instruction():
    inst = Instruction(
        offset=0x10,
        size=2,
        opcode=0x7000,
        text="moveq   #0,d0",
        raw=b"\x70\x00",
        kb_mnemonic="moveq",
        operand_size="l",
    )
    assert get_instruction_processor_min(inst, KB()) == "68000"


def test_has_valid_branch_target_rejects_odd_branch_target():
    inst = Instruction(
        offset=0x40,
        size=2,
        opcode=0x6605,
        text="bne.s   $000047",
        raw=b"\x66\x05",
        kb_mnemonic="bcc",
    )

    assert has_valid_branch_target(inst, KB()) is False


def test_hint_block_has_supported_terminal_flow_for_return():
    block = type("Block", (), {
        "instructions": [
            Instruction(
                offset=0x10,
                size=2,
                opcode=0x4E75,
                text="rts",
                raw=b"\x4E\x75",
                kb_mnemonic="rts",
                operand_size="w",
            )
        ]
    })()

    assert hint_block_has_supported_terminal_flow(block, KB()) is True


def test_is_valid_hint_block_rejects_non_68000_instruction():
    block = type("Block", (), {
        "instructions": [
            Instruction(
                offset=0x10,
                size=2,
                opcode=0x49C0,
                text="corrupted",
                raw=b"\x49\xC0",
                kb_mnemonic="extb",
                operand_size="l",
            )
        ]
    })()

    assert is_valid_hint_block(block, KB()) is False


def test_emit_jump_table_rows_emits_data_entries():
    rows = []
    labels_seen = []

    def emit_label(addr: int):
        labels_seen.append(addr)

    hunk_session = type("HunkSession", (), {
        "jump_table_regions": {
            0x20: {
                "pattern": "word_table",
                "entries": [(0x20, 0x80), (0x22, 0x90)],
                "base_addr": None,
                "base_label": "ignored",
                "table_end": 0x24,
            }
        },
        "labels": {0x80: "loc_0080", 0x90: "loc_0090"},
    })()

    end = emit_jump_table_rows(
        rows, hunk_session, 0x20, 0x20, set(), emit_label)

    assert end == 0x24
    assert labels_seen == []
    assert len(rows) == 2
    assert rows[0].text == "    dc.w    loc_0080-*\n"


def test_emit_jump_table_rows_emits_inline_dispatch_rows():
    rows = []
    labels_seen = []

    def emit_label(addr: int):
        labels_seen.append(addr)

    code = b"\x70\x00\x4E\x75"
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=code,
        code_size=len(code),
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        core_absolute_targets=set(),
        labels={0x02: "loc_0002"},
        jump_table_regions={
            0x00: {
                "pattern": "pc_inline_dispatch",
                "table_end": 0x04,
            }
        },
        jump_table_target_sources={},
        struct_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform={},
        os_kb={"structs": {}},
        kb=KB(),
        fixed_abs_addrs=set(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    end = emit_jump_table_rows(
        rows, hunk_session, 0x00, 0x00, set(), emit_label)

    assert end == 0x04
    assert labels_seen == [0x02]
    assert len(rows) == 2
    assert rows[0].kind == "instruction"


def test_listing_window_anchors_to_matching_addr():
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="", addr=0x10),
        ListingRow(row_id="r1", kind="instruction", text="", addr=0x20),
        ListingRow(row_id="r2", kind="instruction", text="", addr=0x30),
    ]

    window = listing_window(rows, 0x20, before=1, after=1)

    assert [row.row_id for row in window["rows"]] == ["r0", "r1", "r2"]
    assert window["start"] == 0
    assert window["end"] == 3


def test_listing_window_anchors_to_last_row_past_end():
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="", addr=0x10),
        ListingRow(row_id="r1", kind="instruction", text="", addr=0x20),
        ListingRow(row_id="r2", kind="instruction", text="", addr=0x30),
    ]

    window = listing_window(rows, 0x40, before=1, after=0)

    assert [row.row_id for row in window["rows"]] == ["r1", "r2"]
    assert window["has_more_before"] is True
    assert window["has_more_after"] is False


def test_gen_disasm_uses_shared_session_row_pipeline(monkeypatch, tmp_path):
    calls: list[str] = []
    output_path = tmp_path / "out.s"
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=Path("targets/test/entities.jsonl"),
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=output_path,
        entities=[],
        hunk_sessions=[],
    )
    rows = [ListingRow(row_id="row0", kind="instruction", text="moveq #0,d0\n")]

    def fake_build_session(binary_path, entities_path, session_output_path,
                           base_addr=0, code_start=0, profile_stages=False):
        calls.append("build_session")
        assert binary_path == "bin/test"
        assert entities_path == "targets/test/entities.jsonl"
        assert session_output_path == str(output_path)
        assert base_addr == 0x400
        assert code_start == 2
        assert profile_stages is True
        return session

    def fake_emit_rows(seen_session):
        calls.append("emit_rows")
        assert seen_session is session
        return rows

    def fake_render_rows(seen_rows):
        calls.append("render_rows")
        assert seen_rows == rows
        return "; rendered\n"

    monkeypatch.setattr(gen_disasm_mod, "build_disassembly_session",
                        fake_build_session)
    monkeypatch.setattr(gen_disasm_mod, "emit_session_rows", fake_emit_rows)
    monkeypatch.setattr(gen_disasm_mod, "render_rows", fake_render_rows)

    gen_disasm_mod.gen_disasm(
        "bin/test",
        "targets/test/entities.jsonl",
        str(output_path),
        base_addr=0x400,
        code_start=2,
        profile_stages=True,
    )

    assert calls == ["build_session", "emit_rows", "render_rows"]
    assert output_path.read_text() == "; rendered\n"


def test_emit_session_rows_smoke_for_empty_hunk_session():
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[
            HunkDisassemblySession(
                hunk_index=0,
                code=b"",
                code_size=0,
                entities=[],
                blocks={},
                hint_blocks={},
                code_addrs=set(),
                hint_addrs=set(),
                reloc_map={},
                reloc_target_set=set(),
                pc_targets={},
                string_addrs=set(),
                core_absolute_targets=set(),
                labels={},
                jump_table_regions={},
                jump_table_target_sources={},
                struct_map={},
                lvo_equs={},
                lvo_substitutions={},
                arg_equs={},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                data_access_sizes={},
                platform={},
                os_kb={"structs": {}},
                kb=KB(),
                fixed_abs_addrs=set(),
                base_addr=0,
                code_start=0,
                relocated_segments=[],
                reloc_file_offset=0,
                reloc_base_addr=0,
            )
        ],
    )

    rows = emit_session_rows(session)

    assert rows
    assert rows[0].kind == "comment"


def test_serialize_row_preserves_structured_fields():
    row = ListingRow(
        row_id="row0",
        kind="instruction",
        text="    moveq #0,d0\n",
        addr=0x20,
        entity_addr=0x20,
        verified_state="verified",
        bytes=b"\x70\x00",
        label="entry_point",
        opcode_or_directive="moveq",
        operand_parts=(
            SemanticOperand(kind="immediate", text="#0", value=0),
            SemanticOperand(kind="register", text="d0", register="d0"),
        ),
        operand_text="#0,d0",
        comment_parts=("note",),
        comment_text="note",
        source_context={"block": 0x20},
    )

    payload = serialize_row(row)

    assert payload["row_id"] == "row0"
    assert payload["bytes"] == "7000"
    assert payload["operand_parts"][0]["kind"] == "immediate"
    assert payload["source_context"] == {"block": 0x20}


def test_session_metadata_summarizes_hunks():
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=Path("targets/test/entities.jsonl"),
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=Path("targets/test/out.s"),
        entities=[{"addr": "0x0000"}],
        hunk_sessions=[
            HunkDisassemblySession(
                hunk_index=0,
                code=b"\x4e\x75",
                code_size=2,
                entities=[{"addr": "0x0000"}],
                blocks={0: object()},
                hint_blocks={},
                code_addrs={0, 1},
                hint_addrs=set(),
                reloc_map={},
                reloc_target_set=set(),
                pc_targets={},
                string_addrs=set(),
                core_absolute_targets=set(),
                labels={0: "entry_point"},
                jump_table_regions={},
                jump_table_target_sources={},
                struct_map={},
                lvo_equs={},
                lvo_substitutions={},
                arg_equs={},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                data_access_sizes={},
                platform={},
                os_kb={"structs": {}},
                kb=None,
                fixed_abs_addrs=set(),
                base_addr=0,
                code_start=0,
                relocated_segments=[],
                reloc_file_offset=0,
                reloc_base_addr=0,
            )
        ],
    )

    payload = session_metadata(session)

    assert payload["target_name"] == "test"
    assert payload["entity_count"] == 1
    assert payload["hunk_count"] == 1
    assert payload["hunks"][0]["label_count"] == 1
    assert payload["hunks"][0]["relocated"] is False


def test_listing_window_payload_serializes_rows():
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="a\n", addr=0x10),
        ListingRow(row_id="r1", kind="instruction", text="b\n", addr=0x20),
        ListingRow(row_id="r2", kind="instruction", text="c\n", addr=0x30),
    ]

    payload = listing_window_payload(rows, 0x20, before=0, after=1)

    assert payload["anchor_addr"] == 0x20
    assert [row["row_id"] for row in payload["rows"]] == ["r1", "r2"]
    assert payload["has_more_before"] is True
    assert payload["has_more_after"] is False


def test_build_listing_rows_delegates_to_session_builder(monkeypatch):
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[],
    )
    rows = [ListingRow(row_id="r0", kind="instruction", text="nop\n", addr=0)]
    calls: list[str] = []

    def fake_build(binary_path, entities_path, output_path, base_addr=0, code_start=0, profile_stages=False):
        calls.append("build")
        assert binary_path == "bin/demo"
        assert entities_path == "targets/demo/entities.jsonl"
        assert output_path is None
        assert base_addr == 0x400
        assert code_start == 2
        return session

    def fake_emit(seen_session):
        calls.append("emit")
        assert seen_session is session
        return rows

    monkeypatch.setattr(emitter_mod, "build_disassembly_session", fake_build)
    monkeypatch.setattr(emitter_mod, "emit_session_rows", fake_emit)

    result = emitter_mod.build_listing_rows("bin/demo", "targets/demo/entities.jsonl",
                                            base_addr=0x400, code_start=2)

    assert calls == ["build", "emit"]
    assert result == rows


def test_render_session_text_renders_emitted_rows(monkeypatch):
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[],
    )
    rows = [ListingRow(row_id="r0", kind="instruction", text="moveq #0,d0\n", addr=0)]
    calls: list[str] = []

    def fake_emit(seen_session):
        calls.append("emit")
        assert seen_session is session
        return rows

    def fake_render(seen_rows):
        calls.append("render")
        assert seen_rows == rows
        return "; rendered\n"

    monkeypatch.setattr(emitter_mod, "emit_session_rows", fake_emit)
    monkeypatch.setattr(emitter_mod, "render_rows", fake_render)

    assert emitter_mod.render_session_text(session) == "; rendered\n"
    assert calls == ["emit", "render"]


def test_emit_data_region_renders_relocated_longword_label():
    output = io.StringIO()

    data_render_mod.emit_data_region(
        output,
        code=b"\x00\x00\x00\x20",
        start=0,
        end=4,
        labels={0x20: "target_label"},
        reloc_map={0: 0x20},
        string_addrs=set(),
    )

    assert output.getvalue() == "    dc.l    target_label\n"


def test_emit_data_region_renders_zero_fill_run():
    output = io.StringIO()

    data_render_mod.emit_data_region(
        output,
        code=b"\x00\x00\x00\x00\x00",
        start=0,
        end=5,
        labels={},
        reloc_map={},
        string_addrs=set(),
    )

    assert output.getvalue() == "    dcb.b   5,0\n"


def test_emit_data_region_renders_ascii_string():
    output = io.StringIO()

    data_render_mod.emit_data_region(
        output,
        code=b"TEST\x00",
        start=0,
        end=5,
        labels={},
        reloc_map={},
        string_addrs={0},
    )

    assert output.getvalue() == '    dc.b    "TEST",0\n'
