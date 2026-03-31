from __future__ import annotations

"""Disassembly emit and session build tests."""

import struct

from disasm import operands as operands_mod
from tests.disasm_pipeline_support import (
    BasicBlock,
    BootBlockTargetMetadata,
    CustomStructFieldMetadata,
    CustomStructMetadata,
    DisassemblySession,
    EntryRegisterSeedMetadata,
    ExecutionViewMetadata,
    Hunk,
    HunkDisassemblySession,
    HunkType,
    Instruction,
    LibraryBaseTag,
    LibraryTargetMetadata,
    ListingRow,
    MemoryRegionAddressSpace,
    MemoryRegionProvenance,
    MemType,
    MonkeyPatch,
    Path,
    RawBinarySource,
    RelocatedSegment,
    RelocLike,
    ResidentAutoinitMetadata,
    ResidentTargetMetadata,
    SemanticOperand,
    SimpleNamespace,
    StructFieldOperandMetadata,
    StructuredFieldSpec,
    StructuredRegionSpec,
    TargetMetadata,
    TypedMemoryRegion,
    _FakeBlock,
    _instruction,
    asdict,
    build_disassembly_session,
    build_entry_seed_config,
    build_target_local_os_kb,
    cast,
    disassemble,
    effective_entry_register_seeds,
    emit_session_rows,
    emitter_mod,
    gen_disasm_mod,
    json,
    make_empty_os_kb,
    make_platform,
    provenance_named_base,
    render_instruction_text,
    render_rows,
    render_session_text,
    replace,
    runtime_os,
    session_mod,
    target_structure_spec,
)


def test_gen_disasm_uses_shared_session_row_pipeline(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    calls: list[str] = []
    output_path = tmp_path / "out.s"
    entities_path = tmp_path / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=entities_path,
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=output_path,
        entities=[],
        hunk_sessions=[],
    )
    rows: list[ListingRow] = [ListingRow(row_id="row0", kind="instruction", text="moveq #0,d0\n")]

    def fake_build_session(
        binary_path: str,
        entities_path: str,
        session_output_path: str | None,
        base_addr: int = 0,
        code_start: int = 0,
        assembler_profile_name: str = "vasm",
        profile_stages: bool = False,
    ) -> DisassemblySession:
        calls.append("build_session")
        assert binary_path == "bin/test"
        assert entities_path == str(entities_path_obj)
        assert session_output_path == str(output_path)
        assert base_addr == 0x400
        assert code_start == 2
        assert assembler_profile_name == "vasm"
        assert profile_stages is True
        return session

    def fake_emit_rows(seen_session: DisassemblySession) -> list[ListingRow]:
        calls.append("emit_rows")
        assert seen_session is session
        return rows

    def fake_render_rows(seen_rows: list[ListingRow]) -> str:
        calls.append("render_rows")
        assert seen_rows == rows
        return "; rendered\n"

    def fake_refresh_needed(binary_path: str, seen_entities_path: str) -> bool:
        assert binary_path == "bin/test"
        assert seen_entities_path == str(entities_path_obj)
        return False

    entities_path_obj = entities_path
    monkeypatch.setattr(gen_disasm_mod, "build_disassembly_session",
                        fake_build_session)
    monkeypatch.setattr(gen_disasm_mod, "emit_session_rows", fake_emit_rows)
    monkeypatch.setattr(gen_disasm_mod, "render_rows", fake_render_rows)
    monkeypatch.setattr(gen_disasm_mod, "_entities_need_refresh", fake_refresh_needed)

    gen_disasm_mod.gen_disasm(
        "bin/test",
        str(entities_path),
        str(output_path),
        base_addr=0x400,
        code_start=2,
        profile_stages=True,
    )

    assert calls == ["build_session", "emit_rows", "render_rows"]
    assert output_path.read_text() == "; rendered\n"

def test_gen_disasm_refreshes_entities_when_needed(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[object, ...]] = []
    output_path = tmp_path / "out.s"
    entities_path = tmp_path / "entities.jsonl"
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=entities_path,
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=output_path,
        entities=[],
        hunk_sessions=[],
    )

    def fake_refresh_needed(binary_path: str, seen_entities_path: str) -> bool:
        calls.append(("refresh_check", binary_path, seen_entities_path))
        return True

    def fake_build_entities(
        binary_path: str,
        seen_entities_path: str,
        base_addr: int,
        code_start: int,
    ) -> int:
        calls.append(("build_entities", binary_path, seen_entities_path, base_addr, code_start))
        Path(seen_entities_path).write_text("", encoding="utf-8")
        return 0

    def fake_build_session(
        binary_path: str,
        seen_entities_path: str,
        session_output_path: str | None,
        base_addr: int = 0,
        code_start: int = 0,
        assembler_profile_name: str = "vasm",
        profile_stages: bool = False,
    ) -> DisassemblySession:
        calls.append(("build_session", binary_path, seen_entities_path))
        assert assembler_profile_name == "vasm"
        return session

    def fake_emit_session_rows(seen_session: DisassemblySession) -> list[ListingRow]:
        return []

    def fake_render_rows(seen_rows: list[ListingRow]) -> str:
        return ""

    monkeypatch.setattr(gen_disasm_mod, "_entities_need_refresh", fake_refresh_needed)
    monkeypatch.setattr(gen_disasm_mod, "build_entities", fake_build_entities)
    monkeypatch.setattr(gen_disasm_mod, "build_disassembly_session", fake_build_session)
    monkeypatch.setattr(gen_disasm_mod, "emit_session_rows", fake_emit_session_rows)
    monkeypatch.setattr(gen_disasm_mod, "render_rows", fake_render_rows)

    gen_disasm_mod.gen_disasm(
        "bin/test",
        str(entities_path),
        str(output_path),
        base_addr=0x400,
        code_start=2,
    )

    assert calls[:3] == [
        ("refresh_check", "bin/test", str(entities_path)),
        ("build_entities", "bin/test", str(entities_path), 0x400, 2),
        ("build_session", "bin/test", str(entities_path)),
    ]

def test_gen_disasm_passes_selected_assembler_profile(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    output_path = tmp_path / "out.s"
    entities_path = tmp_path / "entities.jsonl"
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=entities_path,
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=output_path,
        entities=[],
        hunk_sessions=[],
        assembler_profile_name="devpac",
    )

    monkeypatch.setattr(gen_disasm_mod, "_entities_need_refresh", lambda *_args: False)
    monkeypatch.setattr(gen_disasm_mod, "emit_session_rows", lambda _session: [])
    monkeypatch.setattr(gen_disasm_mod, "render_rows", lambda _rows: "")

    def fake_build_session(
        binary_path: str,
        seen_entities_path: str,
        session_output_path: str | None,
        base_addr: int = 0,
        code_start: int = 0,
        assembler_profile_name: str = "vasm",
        profile_stages: bool = False,
    ) -> DisassemblySession:
        assert binary_path == "bin/test"
        assert seen_entities_path == str(entities_path)
        assert session_output_path == str(output_path)
        assert assembler_profile_name == "devpac"
        return session

    monkeypatch.setattr(gen_disasm_mod, "build_disassembly_session", fake_build_session)

    gen_disasm_mod.gen_disasm(
        "bin/test",
        str(entities_path),
        str(output_path),
        assembler_profile_name="devpac",
    )

def test_emit_session_rows_smoke_for_empty_hunk_session() -> None:
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
                labels={},
                jump_table_regions={},
                jump_table_target_sources={},
                region_map={},
                lvo_equs={},
                lvo_substitutions={},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                data_access_sizes={},
                platform=make_platform(),
        os_kb=make_empty_os_kb(),
                base_addr=0,
                code_start=0,
                relocated_segments=[],
            )
        ],
    )

    rows = emit_session_rows(session)

    assert rows
    assert rows[0].kind == "comment"


def test_emit_session_rows_renders_execution_view_comments() -> None:
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
                code=b"\x4E\x75",
                code_size=2,
                entities=[],
                blocks={},
                hint_blocks={},
                code_addrs=set(),
                hint_addrs=set(),
                reloc_map={},
                reloc_target_set=set(),
                pc_targets={},
                string_addrs=set(),
                labels={},
                jump_table_regions={},
                jump_table_target_sources={},
                region_map={},
                lvo_equs={},
                lvo_substitutions={},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                data_access_sizes={},
                platform=make_platform(),
                os_kb=make_empty_os_kb(),
                base_addr=0,
                code_start=0,
                relocated_segments=[],
                execution_views=(
                    ExecutionViewMetadata(
                        source_start=0x5C,
                        source_end=0x590B8,
                        base_addr=0x400,
                        name="relocated_code_1",
                        seed_origin="autodoc",
                        review_status="seeded",
                        citation="container:relocated_segment",
                        comment="Relocated code executes from $00000400",
                    ),
                ),
            )
        ],
    )

    rendered = render_rows(emit_session_rows(session))

    assert "; Execution views" in rendered
    assert ";   relocated_code_1: source 0x5C..0x590B8 -> runtime 0x400" in rendered
    assert ";   Relocated code executes from $00000400" in rendered


def test_emit_hunk_rows_keeps_relocated_hunks_source_first() -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=b"\x11\x22\x00\x00\x00\x00\x33\x44",
        code_size=8,
        stored_size=8,
        alloc_size=8,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={2: "loc_0002"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[RelocatedSegment(file_offset=2, base_addr=6)],
    )

    rows, _compat_floor, _preamble = emitter_mod._emit_hunk_rows(
        hunk_session,
        include_header=False,
    )
    rendered = "".join(row.text for row in rows)

    assert "loc_0002:\n" in rendered
    assert "org $" not in rendered
    assert rendered.count("dc.b") >= 1


def test_absolute_target_outside_execution_context_stays_literal() -> None:
    inst = disassemble(b"\x4e\xb9\x00\x00\x04\x20", base_offset=0)[0]
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={0: _FakeBlock(0, len(inst.raw), (), [inst])},
        hint_blocks={},
        code_addrs=set(range(len(inst.raw))),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x20: "bootstrapped_sub"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        execution_views=(
            ExecutionViewMetadata(
                source_start=0x20,
                source_end=0x60,
                base_addr=0x420,
                name="bootstrapped_code",
                seed_origin="autodoc",
                review_status="seeded",
                citation="test",
            ),
        ),
    )

    text, _comment, _comment_parts = render_instruction_text(inst, hunk_session, set())

    assert text == "jsr $420"


def test_execution_view_pc_relative_target_stays_source_relative() -> None:
    inst = disassemble(bytes.fromhex("41fa0038"), base_offset=0x22)[0]
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={0x22: _FakeBlock(0x22, 0x26, (), [inst])},
        hint_blocks={},
        code_addrs=set(range(0x22, 0x26)),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x5C: "pcref_005c"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        execution_views=(
            ExecutionViewMetadata(
                source_start=0x5C,
                source_end=0x100,
                base_addr=0x400,
                name="relocated_code_1",
                seed_origin="autodoc",
                review_status="seeded",
                citation="container:relocated_segment",
            ),
        ),
    )

    text, _comment, _comment_parts = render_instruction_text(inst, hunk_session, set())

    assert "pcref_005c" in text


def test_execution_view_absolute_target_uses_available_source_label() -> None:
    inst = disassemble(bytes.fromhex("41f8005c"), base_offset=0x32)[0]
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={0x32: _FakeBlock(0x32, 0x36, (), [inst])},
        hint_blocks={},
        code_addrs=set(range(0x32, 0x36)),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x5C: "pcref_005c"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        execution_views=(
            ExecutionViewMetadata(
                source_start=0x32,
                source_end=0x5C,
                base_addr=0x90,
                name="trap_0_stub",
                seed_origin="autodoc",
                review_status="seeded",
                citation="analysis:trap_bootstrap",
            ),
            ExecutionViewMetadata(
                source_start=0x5C,
                source_end=0x100,
                base_addr=0x400,
                name="relocated_code_1",
                seed_origin="autodoc",
                review_status="seeded",
                citation="container:relocated_segment",
            ),
        ),
    )

    text, _comment, _comment_parts = render_instruction_text(inst, hunk_session, set())

    assert text == "lea pcref_005c,a0"


def test_execution_view_entry_absolute_target_preserves_runtime_base() -> None:
    inst = disassemble(bytes.fromhex("41f900000400"), base_offset=0x40)[0]
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={0x40: _FakeBlock(0x40, 0x44, (), [inst])},
        hint_blocks={},
        code_addrs=set(range(0x40, 0x44)),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x5C: "loc_005c"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        execution_views=(
            ExecutionViewMetadata(
                source_start=0x32,
                source_end=0x5C,
                base_addr=0x90,
                name="trap_0_stub",
                seed_origin="autodoc",
                review_status="seeded",
                citation="analysis:trap_bootstrap",
            ),
            ExecutionViewMetadata(
                source_start=0x5C,
                source_end=0x100,
                base_addr=0x400,
                name="relocated_code_1",
                seed_origin="autodoc",
                review_status="seeded",
                citation="container:relocated_segment",
            ),
        ),
    )

    text, _comment, _comment_parts = render_instruction_text(inst, hunk_session, set())

    assert text == "lea $400,a0"


def test_unlabeled_low_absolute_operands_render_compact() -> None:
    lea_inst = disassemble(bytes.fromhex("43f900000090"), base_offset=0)[0]
    move_inst = disassemble(bytes.fromhex("23fc0000009000000080"), base_offset=0)[0]
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=lea_inst.raw + move_inst.raw,
        code_size=len(lea_inst.raw) + len(move_inst.raw),
        entities=[],
        blocks={
            0: _FakeBlock(0, len(lea_inst.raw), (), [lea_inst]),
            len(lea_inst.raw): _FakeBlock(
                len(lea_inst.raw),
                len(lea_inst.raw) + len(move_inst.raw),
                (),
                [move_inst],
            ),
        },
        hint_blocks={},
        code_addrs=set(range(len(lea_inst.raw) + len(move_inst.raw))),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )

    lea_text, _comment, _comment_parts = render_instruction_text(lea_inst, hunk_session, set())
    move_text, _comment, _comment_parts = render_instruction_text(move_inst, hunk_session, set())

    assert lea_text == "lea $90,a1"
    assert move_text == "move.l #$90,$80"


def test_absolute_label_or_text_uses_remapped_numeric_target_not_stale_token() -> None:
    inst = disassemble(bytes.fromhex("4238005c"), base_offset=0)[0]
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={0: _FakeBlock(0, len(inst.raw), (), [inst])},
        hint_blocks={},
        code_addrs=set(range(len(inst.raw))),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x887B: "dat_887b"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )

    text = operands_mod._absolute_label_or_text(0x887B, hunk_session, "$00008c1f", inst)

    assert text == "$0000887b"


def test_absolute_label_or_text_uses_generic_source_label_inside_execution_view() -> None:
    inst = disassemble(bytes.fromhex("4238005c"), base_offset=0)[0]
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={0: _FakeBlock(0, len(inst.raw), (), [inst])},
        hint_blocks={},
        code_addrs=set(range(len(inst.raw))),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x887B: "dat_887b"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        execution_views=(
            ExecutionViewMetadata(
                source_start=0x5C,
                source_end=0x9000,
                base_addr=0x400,
                name="relocated_code_1",
                seed_origin="autodoc",
                review_status="seeded",
                citation="test",
            ),
        ),
    )

    text = operands_mod._absolute_label_or_text(0x887B, hunk_session, "$00008c1f", inst)

    assert text == "dat_887b"


def test_execution_view_helper_discovers_nested_bootstrap_views() -> None:
    code = b""
    code += struct.pack(">HH", 0x41FA, 0x001E)
    code += struct.pack(">HHH", 0x43F9, 0x0000, 0x0090)
    code += struct.pack(">H", 0x7013)
    code += struct.pack(">H", 0x12D8)
    code += struct.pack(">HH", 0x51C8, 0xFFFC)
    code += struct.pack(">HH", 0x4DFA, 0x0020)
    code += struct.pack(">HHHH", 0x4E71, 0x4E71, 0x4E71, 0x4E71)
    code += struct.pack(">H", 0x4E40)
    code += struct.pack(">HHH", 0x41F9, 0x0000, 0x0400)
    code += struct.pack(">H", 0x7003)
    code += struct.pack(">H", 0x10DE)
    code += struct.pack(">HH", 0x51C8, 0xFFFC)
    code += struct.pack(">HHH", 0x4EF9, 0x0000, 0x0400)
    code += struct.pack(">H", 0x702A)
    code += struct.pack(">H", 0x4E75)

    views = session_mod._execution_views_for_session(
        code=code,
        blocks={},
        target_metadata=TargetMetadata(
            target_type="raw_binary",
            entry_register_seeds=(),
            execution_views=(
                ExecutionViewMetadata(
                    source_start=0x20,
                    source_end=len(code),
                    base_addr=0x90,
                    name="bootstrapped_code",
                    seed_origin="autodoc",
                    review_status="seeded",
                    citation="test",
                ),
            ),
        ),
        relocated_segments=[],
        physical_stored_size=len(code),
    )

    assert any(
        view.source_start == 0x34
        and view.source_end == len(code)
        and view.base_addr == 0x400
        for view in views
    )

def test_execution_view_helper_discovers_trap_bootstrap_stub() -> None:
    code = b""
    code += struct.pack(">HH", 0x41FA, 0x001E)
    code += struct.pack(">HHH", 0x43F9, 0x0000, 0x0090)
    code += struct.pack(">H", 0x7003)
    code += struct.pack(">H", 0x12D8)
    code += struct.pack(">HH", 0x51C8, 0xFFFC)
    code += struct.pack(">H", 0x23FC)
    code += struct.pack(">I", 0x00000090)
    code += struct.pack(">I", 0x00000080)
    code += struct.pack(">H", 0x4E40)
    code += struct.pack(">HH", 0x4E71, 0x4E71)
    code += struct.pack(">HH", 0x4E71, 0x4E71)
    code += struct.pack(">H", 0x4E75)

    analysis = session_mod.analyze_hunk(code, [], 0)
    views = session_mod._execution_views_for_session(
        code=code,
        blocks=analysis.blocks,
        target_metadata=None,
        relocated_segments=analysis.relocated_segments,
        physical_stored_size=len(code),
    )

    assert any(
        view.source_start == 0x20
        and view.source_end == 0x24
        and view.base_addr == 0x90
        for view in views
    )


def test_execution_view_source_start_gets_code_label() -> None:
    labels = {0x5C: "pcref_005c"}
    session_mod._apply_execution_view_source_labels(
        labels=labels,
        execution_views=(
            ExecutionViewMetadata(
                source_start=0x5C,
                source_end=0x100,
                base_addr=0x400,
                name="relocated_code_1",
                seed_origin="autodoc",
                review_status="seeded",
                citation="test",
            ),
        ),
    )

    assert labels[0x5C] == "loc_005c"

def test_emit_session_rows_emits_file_header_once_for_multi_hunk_session() -> None:
    def empty_hunk(index: int, size: int) -> HunkDisassemblySession:
        return HunkDisassemblySession(
            hunk_index=index,
            code=b"\x00" * size,
            code_size=size,
            entities=[],
            blocks={},
            hint_blocks={},
            code_addrs=set(),
            hint_addrs=set(),
            reloc_map={},
            reloc_target_set=set(),
            pc_targets={},
            string_addrs=set(),
            labels={},
            jump_table_regions={},
            jump_table_target_sources={},
            region_map={},
            lvo_equs={},
            lvo_substitutions={},
            arg_substitutions={},
            app_offsets={},
            arg_annotations={},
            data_access_sizes={},
            platform=make_platform(),
            os_kb=make_empty_os_kb(),
            base_addr=0,
            code_start=0,
            relocated_segments=[],
        )

    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[empty_hunk(0, 316), empty_hunk(1, 504)],
    )

    rows = emit_session_rows(session)
    comments = [row.text for row in rows if row.kind == "comment"]

    assert comments.count("; Generated disassembly -- vasm Motorola syntax\n") == 1
    assert comments.count("; Source: bin\\demo\n") == 1
    assert "; 820 bytes, 0 entities, 0 blocks\n" in comments
    assert "; Hunk 0: 316 bytes, 0 entities, 0 blocks\n" in comments
    assert "; Hunk 1: 504 bytes, 0 entities, 0 blocks\n" in comments

def test_emit_hunk_rows_uses_real_section_kind_and_bss_space() -> None:
    data_hunk = HunkDisassemblySession(
        hunk_index=0,
        hunk_type=int(HunkType.HUNK_DATA),
        mem_type=int(MemType.FAST),
        section_name="assets",
        code=b"\x11\x22\x33\x44",
        code_size=4,
        alloc_size=4,
        entities=[],
        blocks={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )
    bss_hunk = replace(
        data_hunk,
        hunk_index=1,
        hunk_type=int(HunkType.HUNK_BSS),
        mem_type=int(MemType.CHIP),
        section_name="work",
        code=b"",
        code_size=0,
        alloc_size=12,
        stored_size=0,
        labels={0: "work_area"},
    )

    data_rows, _data_floor, _data_preamble = emitter_mod._emit_hunk_rows(
        data_hunk,
        include_header=False,
    )
    bss_rows, _bss_floor, _bss_preamble = emitter_mod._emit_hunk_rows(
        bss_hunk,
        include_header=False,
    )

    assert data_rows[0].text == "    section assets,data,fast\n"
    assert any(row.kind == "data" for row in data_rows)
    assert bss_rows[0].text == "    section work,bss,chip\n"
    assert any(row.text == "work_area:\n" for row in bss_rows)
    assert any(row.text == "    ds.b 12\n" for row in bss_rows)

def test_emit_hunk_rows_splits_bss_space_at_interior_labels() -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        hunk_type=int(HunkType.HUNK_BSS),
        mem_type=int(MemType.ANY),
        section_name="bss",
        code=b"",
        code_size=0,
        alloc_size=12,
        stored_size=0,
        entities=[],
        blocks={},
        labels={0: "bss_start", 4: "bss_mid", 8: "bss_end"},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )

    rows, _compat_floor, _preamble = emitter_mod._emit_hunk_rows(
        hunk_session,
        include_header=False,
    )

    assert rows[0].text == "    section bss,bss\n"
    assert [row.text for row in rows if row.kind == "label"] == [
        "bss_start:\n",
        "bss_mid:\n",
        "bss_end:\n",
    ]
    assert [row.text for row in rows if row.kind == "directive"] == [
        "    ds.b 4\n",
        "    ds.b 4\n",
        "    ds.b 4\n",
    ]

def test_emit_hunk_rows_emits_databss_tail_for_shortened_data_hunk() -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        hunk_type=int(HunkType.HUNK_DATA),
        mem_type=int(MemType.ANY),
        section_name="data",
        code=b"\x11\x22\x33\x44",
        code_size=4,
        alloc_size=8,
        stored_size=4,
        entities=[],
        blocks={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )

    rows, _floor, _preamble = emitter_mod._emit_hunk_rows(
        hunk_session,
        include_header=False,
    )

    assert [row.text for row in rows] == [
        "    section data,data\n",
        "\n",
        "    dc.b    $11,$22,$33,$44\n",
        "    ds.b 4\n",
    ]

def test_emit_hunk_rows_splits_databss_tail_at_interior_labels() -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        hunk_type=int(HunkType.HUNK_DATA),
        mem_type=int(MemType.ANY),
        section_name="data",
        code=b"\x11\x22\x33\x44",
        code_size=4,
        alloc_size=12,
        stored_size=4,
        entities=[],
        blocks={},
        labels={8: "tail_mid"},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )

    rows, _floor, _preamble = emitter_mod._emit_hunk_rows(
        hunk_session,
        include_header=False,
    )

    assert [row.text for row in rows] == [
        "    section data,data\n",
        "\n",
        "    dc.b    $11,$22,$33,$44\n",
        "    ds.b 4\n",
        "tail_mid:\n",
        "    ds.b 4\n",
    ]

def test_emit_session_rows_includes_bootblock_structure_section() -> None:
    session = DisassemblySession(
        target_name="demo_bootblock",
        binary_path=Path("targets/demo_bootblock/binary.bin"),
        entities_path=Path("targets/demo_bootblock/entities.jsonl"),
        analysis_cache_path=Path("targets/demo_bootblock/binary.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[
                HunkDisassemblySession(
                    hunk_index=0,
                    code=b"DOS\x00" + b"\x00\x00\x00\x00" + b"\x00\x00\x03\x70" + b"\x4e\x75",
                    code_size=14,
                    entities=[],
                    blocks={
                        0x0C: _FakeBlock(
                            start=0x0C,
                            end=0x0E,
                            successors=(),
                            instructions=[
                                _instruction(
                                    offset=0x0C,
                                    raw=b"\x4e\x75",
                                    mnemonic="rts",
                                    operand_size="w",
                                    operand_texts=(),
                                )
                            ],
                        )
                    },
                    hint_blocks={},
                    code_addrs={0x0C, 0x0D},
                    hint_addrs=set(),
                    reloc_map={},
                    reloc_target_set=set(),
                    pc_targets={},
                    string_addrs={0},
                    labels={
                        0: "boot_magic",
                        4: "boot_checksum",
                        8: "boot_root_block",
                        0x0C: "boot_entry",
                    },
                jump_table_regions={},
                jump_table_target_sources={},
                region_map={},
                lvo_equs={"exec.library": {-456: "_LVODoIO"}},
                lvo_substitutions={0: ("rts", "_LVODoIO(a6)")},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                    data_access_sizes={4: 4, 8: 4},
                    platform=make_platform(),
                    os_kb=make_empty_os_kb(),
                    base_addr=0,
                    code_start=0x0C,
                relocated_segments=[],
            )
        ],
        target_metadata=TargetMetadata(
            target_type="bootblock",
            entry_register_seeds=(
                EntryRegisterSeedMetadata(
                    entry_offset=None,
                    register="A6",
                    kind="library_base",
                    note="ExecBase",
                    library_name="exec.library",
                    struct_name="LIB",
                    context_name=None,
                ),
                EntryRegisterSeedMetadata(
                    entry_offset=None,
                    register="A1",
                    kind="struct_ptr",
                    note="IOStdReq (open trackdisk.device)",
                    library_name=None,
                    struct_name="IO",
                    context_name="trackdisk.device",
                ),
            ),
            bootblock=BootBlockTargetMetadata(
                magic_ascii="DOS",
                flags_byte=0,
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=880,
                bootcode_offset=0x0C,
                bootcode_size=1012,
                load_address=0x70000,
                entrypoint=0x7000C,
            ),
        ),
    )

    rows = emit_session_rows(session)
    rendered = "".join(row.text for row in rows)

    assert "; Boot block structure\n" in rendered
    assert "; OS compatibility floor: 1.3\n" in rendered
    assert ";   boot code: offset 0xC, size 1012 bytes\n" in rendered
    assert ";   execution context:" not in rendered
    assert 'INCLUDE "exec/exec_lib.i"\n' in rendered
    assert "_LVODoIO\tEQU\t-456\n" not in rendered
    assert "boot_entry:\n" in rendered

def test_build_disassembly_session_for_local_offset_raw_bootblock_renders_local_labels(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "bootblock"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(
        (b"DOS\x00" + b"\x00\x00\x00\x00" + b"\x00\x00\x03\x70")
        + bytes.fromhex("43FA00184EAEFFA04A80670A20402068001670004E7570FF60FA")
        + b"dos.library\x00",
    )
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="bootblock",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        bootblock=BootBlockTargetMetadata(
            magic_ascii="DOS",
            flags_byte=0,
            fs_description="DOS\\0 - OFS",
            checksum="0x00000000",
            checksum_valid=True,
            rootblock_ptr=880,
            bootcode_offset=0x0C,
            bootcode_size=1012,
            load_address=0x70000,
            entrypoint=0x7000C,
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )

    rendered = render_session_text(build_disassembly_session(source, str(entities_path)))

    assert "boot_magic:\n" in rendered
    assert "; OS compatibility floor: 1.3\n" in rendered
    assert 'dc.b    "DOS",0\n' in rendered
    assert "boot_checksum:\n" in rendered
    assert "dc.l    $00000000\n" in rendered
    assert "boot_root_block:\n" in rendered
    assert "dc.l    $00000370\n" in rendered
    assert "boot_entry:\n" in rendered
    assert "dc.b    $43,$fa,$00,$18,$4e,$ae,$ff,$a0" not in rendered
    assert "jsr _LVOFindResident(a6)" in rendered
    assert "movea.l RT_INIT(a0),a0" in rendered
    assert "movea.l d0,a0" in rendered
    assert "moveq #0,d0" in rendered
    assert ";   boot code: offset 0xC, size 1012 bytes\n" in rendered
    assert ";   execution context:" not in rendered
    assert "$70022" not in rendered
    assert "$70020" not in rendered

def test_build_disassembly_session_leaves_out_of_segment_absolute_jump_unlabeled(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "bootblock_abs_jump"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(
        b"DOS\x00"
        + bytes.fromhex("A382070F")
        + bytes.fromhex("00000370")
        + bytes.fromhex(
            "48E7FFFE337C0002001C237C000400000028237C000054000024"
            "237C00000400002C4EAEFE384EF900040000"
        )
        + b"\x00" * (1024 - 12 - 38)
    )
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="bootblock",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A1",
                kind="struct_ptr",
                note="IOStdReq (open trackdisk.device)",
                library_name=None,
                struct_name="IO",
                context_name="trackdisk.device",
            ),
        ),
        bootblock=BootBlockTargetMetadata(
            magic_ascii="DOS",
            flags_byte=0,
            fs_description="DOS\\0 - OFS",
            checksum="0xA382070F",
            checksum_valid=True,
            rootblock_ptr=880,
            bootcode_offset=0x0C,
            bootcode_size=1012,
            load_address=0x70000,
            entrypoint=0x7000C,
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )

    rendered = render_session_text(build_disassembly_session(source, str(entities_path)))

    assert "move.w #CMD_READ,IO_COMMAND(a1)" in rendered
    assert "move.l #$40000,IO_DATA(a1)" in rendered
    assert "move.l #$5400,IO_LENGTH(a1)" in rendered
    assert "move.l #$400,IO_OFFSET(a1)" in rendered
    assert "jsr _LVODoIO(a6)" in rendered
    assert "jmp $00040000" in rendered
    assert "loc_40000" not in rendered

def test_build_disassembly_session_for_runtime_absolute_raw_keeps_absolute_label_space(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "absolute_boot"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(
        (b"DOS\x00" + b"\x00\x00\x00\x00" + b"\x00\x00\x03\x70")
        + bytes.fromhex("43FA00184EAEFFA04A80670A20402068001670004E7570FF60FA")
        + b"dos.library\x00",
    )
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="bootblock",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A1",
                kind="struct_ptr",
                note="IOStdReq (open trackdisk.device)",
                library_name=None,
                struct_name="IO",
                context_name="trackdisk.device",
            ),
        ),
        bootblock=BootBlockTargetMetadata(
            magic_ascii="DOS",
            flags_byte=0,
            fs_description="DOS\\0 - OFS",
            checksum="0x00000000",
            checksum_valid=True,
            rootblock_ptr=880,
            bootcode_offset=0x0C,
            bootcode_size=1012,
            load_address=0x70000,
            entrypoint=0x7000C,
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="runtime_absolute",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )

    rendered = render_session_text(build_disassembly_session(source, str(entities_path)))

    assert "boot_magic:\n" in rendered
    assert "boot_entry:\n" in rendered
    assert "dc.b    $43,$fa,$00,$18,$4e,$ae,$ff,$a0" not in rendered
    assert "movea.l d0,a0" in rendered
    assert "moveq #0,d0" in rendered
    assert ";   boot code: offset 0xC, size 1012 bytes\n" in rendered
    assert ";   execution context: load 0x70000, entry 0x7000C\n" in rendered
    assert "$70022" not in rendered
    assert "$70020" not in rendered


def test_build_disassembly_session_for_runtime_absolute_raw_discovers_local_pc_data_labels(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "absolute_pcdata"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(bytes.fromhex("41FA00044E75") + b"\x00\x00\x12\x34")
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(TargetMetadata(target_type="program", entry_register_seeds=())), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="runtime_absolute",
        load_address=0x40000,
        entrypoint=0x40000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )

    rendered = render_session_text(build_disassembly_session(source, str(entities_path)))

    assert "lea pcref_0006(pc),a0" in rendered


def test_build_disassembly_session_for_runtime_absolute_raw_keeps_external_absolute_data_accesses(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "absolute_extdata"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(bytes.fromhex("423800644E75"))  # clr.b $64 ; rts
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(TargetMetadata(target_type="program", entry_register_seeds=())), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="runtime_absolute",
        load_address=0x40000,
        entrypoint=0x40000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )

    rendered = render_session_text(build_disassembly_session(source, str(entities_path)))

    assert "clr.b $64" in rendered


def test_build_disassembly_session_preserves_absolute_short_memory_syntax_details(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "absolute_short_mem"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(bytes.fromhex("20B8006421C800644E75"))
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(TargetMetadata(target_type="program", entry_register_seeds=())), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="runtime_absolute",
        load_address=0x40000,
        entrypoint=0x40000,
        code_start_offset=0,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )

    rendered = render_session_text(build_disassembly_session(source, str(entities_path)))

    assert "move.l ($0064).w,(a0)" in rendered
    assert "move.l a0,($0064).w" in rendered

def test_build_entry_seed_config_scopes_autoinit_library_a6_by_entrypoint() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x88,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=4,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x44,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x44,
                base_size=0x24,
                vectors_offset=0x54,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x88,
            ),
        ),
    )

    seed_config = build_entry_seed_config(metadata)

    assert seed_config.initial_state is None
    assert seed_config.initial_register_regions == {}
    assert seed_config.entry_initial_states.keys() == {0x88, 0x90}
    assert seed_config.entry_register_regions[0x88]["a6"].context_name is None
    assert seed_config.entry_register_regions[0x90]["a6"].provenance.derivation is not None
    assert seed_config.entry_register_regions[0x90]["a6"].provenance.derivation.named_base == "icon.library"
    assert seed_config.entry_initial_states[0x88].a[6].tag == LibraryBaseTag(
        library_base="exec.library",
        struct_name="LIB",
    )
    assert seed_config.entry_initial_states[0x90].a[6].tag == LibraryBaseTag(
        library_base="icon.library",
        struct_name="LIB",
    )

def test_build_entry_seed_config_synthesizes_autoinit_library_a6_by_entrypoint() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        resident=ResidentTargetMetadata(
            offset=4,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x44,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x44,
                base_size=0x24,
                vectors_offset=0x54,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x88,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 37.1",
            version=37,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    seed_config = build_entry_seed_config(metadata)

    assert seed_config.initial_state is None
    assert seed_config.initial_register_regions == {}
    assert seed_config.entry_initial_states.keys() == {0x88, 0x90}
    assert seed_config.entry_register_regions[0x88]["a6"].context_name is None
    assert seed_config.entry_register_regions[0x90]["a6"].provenance.derivation is not None
    assert seed_config.entry_register_regions[0x90]["a6"].provenance.derivation.named_base == "icon.library"
    assert seed_config.entry_initial_states[0x88].a[6].tag == LibraryBaseTag(
        library_base="exec.library",
        struct_name="LIB",
    )
    assert seed_config.entry_initial_states[0x90].a[6].tag == LibraryBaseTag(
        library_base="icon.library",
        struct_name="LIB",
    )

def test_emit_target_structure_rows_filters_library_exports_by_library_version() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2",
            version=34,
            public_function_count=8,
            total_lvo_count=18,
        ),
    )
    session = DisassemblySession(
        target_name="icon34",
        binary_path=Path("icon.library"),
        entities_path=Path("entities.jsonl"),
        analysis_cache_path=Path("binary.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[],
        target_metadata=metadata,
        source_kind="hunk_file",
    )

    rendered = render_rows(emitter_mod._emit_target_structure_rows(session))

    assert (
        ";   exports: BumpRevision, MatchToolValue, FindToolType, FreeDiskObject, "
        "PutDiskObject, GetDiskObject, AddFreeList, FreeFreeList\n"
    ) in rendered
    assert "GetDiskObjectNew" not in rendered
    assert "DeleteDiskObject" not in rendered

def test_emit_target_structure_rows_dedupes_library_entry_register_notes() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x148,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x0DC,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x0EA,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    session = DisassemblySession(
        target_name="icon.library",
        binary_path=Path("bin/icon.library"),
        entities_path=Path("targets/icon/entities.jsonl"),
        analysis_cache_path=Path("targets/icon/binary.analysis"),
        output_path=None,
        hunk_sessions=[],
        entities=[],
        target_metadata=metadata,
    )

    rendered = "".join(row.text for row in emitter_mod._emit_target_structure_rows(session))

    assert ";   entry registers:" not in rendered
    assert "GetDefDiskObject" not in rendered
    assert "PutDefDiskObject" not in rendered

def test_emit_target_structure_rows_shows_synthesized_library_entry_register_notes() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=34,
            node_type_name="NT_LIBRARY",
            priority=70,
            name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            init_offset=0x48,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x48,
                base_size=0x24,
                vectors_offset=0x58,
                vector_format="offset32",
                vector_offsets=(0xDC, 0xEA, 0x100, 0x144),
                init_struct_offset=0,
                init_func_offset=0x148,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    session = DisassemblySession(
        target_name="icon.library",
        binary_path=Path("bin/icon.library"),
        entities_path=Path("targets/icon/entities.jsonl"),
        analysis_cache_path=Path("targets/icon/binary.analysis"),
        output_path=None,
        hunk_sessions=[],
        entities=[],
        target_metadata=metadata,
    )

    rendered = "".join(row.text for row in emitter_mod._emit_target_structure_rows(session))

    assert ";   entry registers:" not in rendered

def test_emit_session_rows_emits_entry_register_notes_at_entry_labels() -> None:
    inst = Instruction(
        offset=0x0,
        size=2,
        opcode=0x4E75,
        text="rts",
        raw=b"\x4e\x75",
        opcode_text="rts",
        kb_mnemonic="rts",
        operand_size="l",
        operand_texts=(),
    )
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x0,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x0,
                register="D0",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
    )
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={0x0: _FakeBlock(0x0, 0x2, (), [inst])},
        code_addrs={0x0, 0x1},
        labels={0x0: "library_init"},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )
    session = DisassemblySession(
        target_name="icon.library",
        binary_path=Path("bin/icon.library"),
        entities_path=Path("targets/icon/entities.jsonl"),
        analysis_cache_path=Path("targets/icon/binary.analysis"),
        output_path=None,
        hunk_sessions=[hunk_session],
        entities=[],
        target_metadata=metadata,
    )

    rendered = emitter_mod.render_session_text(session)

    assert "; entry registers: A6=ExecBase, D0=icon.library base\nlibrary_init:\n" in rendered

def test_target_structure_spec_filters_resident_library_vector_names_by_library_version() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=34,
            node_type_name="NT_LIBRARY",
            priority=70,
            name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            init_offset=0x48,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x48,
                base_size=0x24,
                vectors_offset=0x58,
                vector_format="offset32",
                vector_offsets=tuple(0x100 + (index * 2) for index in range(23)),
                init_struct_offset=0,
                init_func_offset=0x148,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    structure = target_structure_spec(metadata)

    assert structure is not None
    labels = [entry.label for entry in structure.entrypoints]
    assert "put_disk_object" in labels
    assert "bump_revision" in labels
    assert "get_def_disk_object" not in labels
    assert "put_def_disk_object" not in labels
    assert "get_disk_object_new" not in labels
    assert "delete_disk_object" not in labels
    assert "icon_private_8" in labels
    assert "icon_private_9" in labels
    assert "icon_private_10" in labels
    assert "icon_private_11" in labels

def test_effective_entry_register_seeds_include_kb_typed_vector_inputs() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=34,
            node_type_name="NT_LIBRARY",
            priority=70,
            name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            init_offset=0x48,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x48,
                base_size=0x24,
                vectors_offset=0x58,
                vector_format="offset32",
                vector_offsets=(
                    0x74, 0x78, 0x7C, 0x80, 0x84, 0x88, 0x8C, 0x90, 0x94,
                    0x98, 0x9C, 0xA0, 0xA4, 0xA8, 0xAC, 0xB0, 0xB4, 0xB8, 0xBC,
                ),
                init_struct_offset=0,
                init_func_offset=0xDC,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    seeds = effective_entry_register_seeds(metadata)

    assert any(
        seed.entry_offset == 0xDC
        and seed.register == "D0"
        and seed.kind == "library_base"
        and seed.library_name == "icon.library"
        and seed.struct_name == "LIB"
        for seed in seeds
    )
    assert any(
        seed.entry_offset == 0xA8
        and seed.register == "A1"
        and seed.kind == "struct_ptr"
        and seed.struct_name == "DiskObject"
        for seed in seeds
    )
    assert not any(
        seed.entry_offset == 0x74
        and seed.register == "D0"
        and seed.kind == "struct_ptr"
        for seed in seeds
    )

def test_effective_entry_register_seeds_merges_explicit_and_synthesized_resident_inputs() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0xDC,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x74,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=34,
            node_type_name="NT_LIBRARY",
            priority=70,
            name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            init_offset=0x48,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x48,
                base_size=0x24,
                vectors_offset=0x58,
                vector_format="offset32",
                vector_offsets=(0x74,),
                init_struct_offset=0,
                init_func_offset=0xDC,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    seeds = effective_entry_register_seeds(metadata)

    assert any(
        seed.entry_offset == 0xDC
        and seed.register == "A6"
        and seed.library_name == "exec.library"
        for seed in seeds
    )
    assert any(
        seed.entry_offset == 0x74
        and seed.register == "A6"
        and seed.library_name == "icon.library"
        for seed in seeds
    )
    assert any(
        seed.entry_offset == 0xDC
        and seed.register == "D0"
        and seed.kind == "library_base"
        and seed.library_name == "icon.library"
        and seed.struct_name == "LIB"
        for seed in seeds
    )

def test_apply_named_base_struct_overrides_rewrites_seeded_register_regions() -> None:
    platform = make_platform()
    icon_region = TypedMemoryRegion(
        struct="LIB",
        size=runtime_os.STRUCTS["LIB"].size,
        provenance=provenance_named_base("icon.library"),
    )
    platform.entry_register_regions = {
        0x148: {
            "d0": icon_region,
            "a2": TypedMemoryRegion(
                struct="LIB",
                size=runtime_os.STRUCTS["LIB"].size,
                provenance=MemoryRegionProvenance(
                    address_space=MemoryRegionAddressSpace.REGISTER,
                ),
            ),
        }
    }
    platform.initial_register_regions = {"d0": icon_region}
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        custom_structs=(
            CustomStructMetadata(
                name="InferredIconLibraryBase",
                size=46,
                fields=(
                    CustomStructFieldMetadata(
                        name="exec_library_base",
                        type="APTR",
                        offset=34,
                        size=4,
                        pointer_struct="LIB",
                    ),
                ),
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="test",
                base_struct="LIB",
                base_offset=runtime_os.STRUCTS["LIB"].size,
            ),
        ),
    )
    os_kb = build_target_local_os_kb(
        runtime_os,
        target_metadata,
        named_base_struct_overrides={"icon.library": "InferredIconLibraryBase"},
    )
    session_mod._apply_named_base_struct_overrides(platform, os_kb)

    assert platform.initial_register_regions["d0"].struct == "InferredIconLibraryBase"
    assert platform.entry_register_regions[0x148]["d0"].struct == "InferredIconLibraryBase"
    assert platform.entry_register_regions[0x148]["a2"].struct == "LIB"

def test_emit_session_rows_emits_initstruct_macros() -> None:
    code = bytes.fromhex(
        "e0 00 00 08 09 00"
        "c0 00 00 0a 00 00 00 18"
        "00"
    ) + b"dos.library\x00"
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=code,
        code_size=len(code),
        entities=[],
        blocks={},
        reloc_map={10: 0x18},
        reloc_target_set={0x18},
        string_addrs={0x18},
        labels={0: "resident_initstruct", 0x18: "dos_name"},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        typed_data_sizes={},
        typed_data_fields={},
        addr_comments={},
        string_ranges={0x18: 0x24},
        dynamic_structured_regions=(
            StructuredRegionSpec(
                start=0,
                end=15,
                subtype="typed_data_stream",
                struct_name="LIB",
                stream_format="exec.InitStruct",
            ),
        ),
        absolute_labels={},
        reserved_absolute_addrs=set(),
        app_struct_regions={},
        hardware_base_regs={},
        unresolved_indirects={},
        lib_calls=(),
    )
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("targets/demo/binary.analysis"),
        output_path=None,
        hunk_sessions=[hunk_session],
        entities=[],
        target_metadata=None,
    )

    rendered = render_rows(emit_session_rows(session))

    assert '    INCLUDE "exec/initializers.i"\n' in rendered
    assert "    INITBYTE LN_TYPE,$09\n" in rendered
    assert "    INITLONG LN_NAME,dos_name\n" in rendered
    assert "    dc.b    $00\n" in rendered
    assert "resident_initstruct:\n" in rendered

def test_emit_hunk_rows_rewrites_struct_field_names_for_compatibility_floor() -> None:
    custom_struct = SimpleNamespace(
        source="exec/libraries.i",
        base_offset=0,
        base_offset_symbol=None,
        size=34,
        fields=(
            SimpleNamespace(
                name="LIB_OPENCOUNT",
                type="UWORD",
                offset=32,
                size=2,
                available_since="1.3",
                names_by_version={"1.3": "LIB_OPENCNT", "3.1": "LIB_OPENCOUNT"},
            ),
        ),
        available_since="1.3",
    )
    row = ListingRow(
        row_id="instruction:000000",
        kind="instruction",
        text="    move.w LIB_OPENCOUNT(a6),d0\n",
        addr=0,
        opcode_or_directive="move.w",
        operand_parts=(
            SemanticOperand(
                kind="struct_field",
                text="LIB_OPENCOUNT(a6)",
                base_register="a6",
                displacement=32,
                metadata=StructFieldOperandMetadata(
                    symbol="LIB_OPENCOUNT",
                    owner_struct="LIB",
                    field_symbol="LIB_OPENCOUNT",
                ),
            ),
            SemanticOperand(kind="register", text="d0", register="d0"),
        ),
        operand_text="LIB_OPENCOUNT(a6),d0",
    )

    rewritten = emitter_mod._apply_compatibility_field_names(
        [row],
        cast(HunkDisassemblySession, SimpleNamespace(
            os_kb=SimpleNamespace(STRUCTS={"LIB": custom_struct}),
        )),
        "1.3",
    )

    assert rewritten[0].text == "    move.w LIB_OPENCNT(a6),d0\n"
    assert rewritten[0].operand_text == "LIB_OPENCNT(a6),d0"

def test_build_disassembly_session_for_resident_library_uses_resident_init_entry(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "library"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "library.bin"
    binary_path.write_bytes(b"fake")
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0xA0,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x40,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x40,
                base_size=0x24,
                vectors_offset=0x50,
                vector_format="offset32",
                vector_offsets=(0xA0,),
                init_struct_offset=None,
                init_func_offset=0x90,
            ),
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    code = bytearray(0xA2)
    code[0:2] = bytes.fromhex("4afc")
    code[2:6] = (0).to_bytes(4, byteorder="big")
    code[6:10] = (0x42).to_bytes(4, byteorder="big")
    code[10] = 0x80
    code[11] = 37
    code[12] = 9
    code[14:18] = (0x20).to_bytes(4, byteorder="big")
    code[18:22] = (0x30).to_bytes(4, byteorder="big")
    code[22:26] = (0x40).to_bytes(4, byteorder="big")
    code[0x20:0x2D] = b"icon.library\x00"
    code[0x30:0x3A] = b"icon 37.1\x00"
    code[0x40:0x44] = (0x24).to_bytes(4, byteorder="big")
    code[0x44:0x48] = (0x50).to_bytes(4, byteorder="big")
    code[0x48:0x4C] = (0).to_bytes(4, byteorder="big")
    code[0x4C:0x50] = (0x90).to_bytes(4, byteorder="big")
    code[0x50:0x54] = (0xA0).to_bytes(4, byteorder="big")
    code[0x54:0x58] = (0xFFFFFFFF).to_bytes(4, byteorder="big", signed=False)
    code[0x90:0x92] = b"\x4e\x75"
    code[0xA0:0xA2] = b"\x4e\x75"

    def fake_parse(_data: bytes) -> SimpleNamespace:
        return SimpleNamespace(
            hunks=[
                Hunk(
                    index=0,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=len(code),
                    data=bytes(code),
                )
            ]
        )

    def fake_load_hunk_analysis(
        *,
        analysis_cache_path: Path,
        code: bytes,
        relocs: list[RelocLike],
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...],
        extra_entry_points: tuple[int, ...],
        seed_key: str,
        initial_state: object,
        entry_initial_states: object | None = None,
    ) -> SimpleNamespace:
        assert entry_points == (0x90, 0xA0)
        assert extra_entry_points == ()
        assert isinstance(entry_initial_states, dict)
        assert set(entry_initial_states) == {0x90, 0xA0}
        inst = disassemble(b"\x4e\x75")[0]
        inst.offset = 0x90
        block = BasicBlock(
            start=0x90,
            end=0x92,
            instructions=[inst],
            is_entry=True,
        )
        return SimpleNamespace(
            blocks={0x90: block},
            hint_blocks={},
            jump_tables=[],
            call_targets=set(),
            branch_targets=set(),
            lib_calls=[],
            os_kb=runtime_os,
            platform=make_platform(),
            exit_states={},
            relocated_segments=[],
            indirect_sites=[],
            xrefs=[],
        )

    monkeypatch.setattr("disasm.session.parse", fake_parse)
    monkeypatch.setattr("disasm.session.load_hunk_analysis", fake_load_hunk_analysis)

    rendered = render_session_text(build_disassembly_session(str(binary_path), str(entities_path)))

    assert "resident_matchword:\n" in rendered
    assert "resident_init_ptr:\n" in rendered
    assert "library_init:\n" in rendered
    assert "lib_open:\n" in rendered

def test_build_disassembly_session_keeps_resident_vector_blocks_before_init_entry(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "library"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "library.bin"
    binary_path.write_bytes(b"fake")
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x120,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x40,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x40,
                base_size=0x24,
                vectors_offset=0x50,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x120,
            ),
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    code = bytearray(0x122)
    code[0:2] = bytes.fromhex("4afc")
    code[2:6] = (0).to_bytes(4, byteorder="big")
    code[6:10] = (0x42).to_bytes(4, byteorder="big")
    code[10] = 0x80
    code[11] = 37
    code[12] = 9
    code[14:18] = (0x20).to_bytes(4, byteorder="big")
    code[18:22] = (0x30).to_bytes(4, byteorder="big")
    code[22:26] = (0x40).to_bytes(4, byteorder="big")
    code[0x20:0x2D] = b"icon.library\x00"
    code[0x30:0x3A] = b"icon 37.1\x00"
    code[0x40:0x44] = (0x24).to_bytes(4, byteorder="big")
    code[0x44:0x48] = (0x50).to_bytes(4, byteorder="big")
    code[0x48:0x4C] = (0).to_bytes(4, byteorder="big")
    code[0x4C:0x50] = (0x120).to_bytes(4, byteorder="big")
    code[0x50:0x54] = (0x90).to_bytes(4, byteorder="big")
    code[0x54:0x58] = (0xFFFFFFFF).to_bytes(4, byteorder="big", signed=False)
    code[0x90:0x92] = b"\x4e\x75"
    code[0x120:0x122] = b"\x4e\x75"

    def fake_parse(_data: bytes) -> SimpleNamespace:
        return SimpleNamespace(
            hunks=[
                Hunk(
                    index=0,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=len(code),
                    data=bytes(code),
                )
            ]
        )

    def fake_load_hunk_analysis(
        *,
        analysis_cache_path: Path,
        code: bytes,
        relocs: list[RelocLike],
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...],
        extra_entry_points: tuple[int, ...],
        seed_key: str,
        initial_state: object,
        entry_initial_states: object | None = None,
    ) -> SimpleNamespace:
        assert entry_points == (0x120, 0x90)
        vector_inst = disassemble(b"\x4e\x75")[0]
        vector_inst.offset = 0x90
        init_inst = disassemble(b"\x4e\x75")[0]
        init_inst.offset = 0x120
        vector_block = BasicBlock(
            start=0x90,
            end=0x92,
            instructions=[vector_inst],
            is_entry=True,
        )
        init_block = BasicBlock(
            start=0x120,
            end=0x122,
            instructions=[init_inst],
            is_entry=True,
        )
        return SimpleNamespace(
            blocks={0x90: vector_block, 0x120: init_block},
            hint_blocks={},
            jump_tables=[],
            call_targets={0x90, 0x120},
            branch_targets=set(),
            lib_calls=[],
            os_kb=runtime_os,
            platform=make_platform(),
            exit_states={},
            relocated_segments=[],
            indirect_sites=[],
            xrefs=[],
        )

    monkeypatch.setattr("disasm.session.parse", fake_parse)
    monkeypatch.setattr("disasm.session.load_hunk_analysis", fake_load_hunk_analysis)

    session = build_disassembly_session(str(binary_path), str(entities_path))
    rendered = render_session_text(session)

    assert 0x90 in session.hunk_sessions[0].blocks
    assert 0x120 in session.hunk_sessions[0].blocks
    assert "lib_open:\n" in rendered
    assert "library_init:\n" in rendered

def test_target_structure_spec_for_resident_library_starts_at_earliest_vector_entry() -> None:
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x120,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x40,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x40,
                base_size=0x24,
                vectors_offset=0x50,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x120,
            ),
        ),
    )
    structure = target_structure_spec(target_metadata)

    assert structure is not None
    assert structure.analysis_start_offset == 0x90
    assert tuple(entry.offset for entry in structure.entrypoints) == (0x120, 0x90)

def test_build_disassembly_session_applies_resident_structure_only_to_first_code_hunk(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "library"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "library.bin"
    binary_path.write_bytes(b"fake")
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x88,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=4,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x44,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x44,
                base_size=0x24,
                vectors_offset=0x54,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x88,
            ),
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    first_code = bytearray(0x92)
    first_code[4:6] = bytes.fromhex("4afc")
    first_code[6:10] = (4).to_bytes(4, byteorder="big")
    first_code[10:14] = (0x4A).to_bytes(4, byteorder="big")
    first_code[14] = 0x80
    first_code[15] = 37
    first_code[16] = 9
    first_code[18:22] = (0x20).to_bytes(4, byteorder="big")
    first_code[22:26] = (0x30).to_bytes(4, byteorder="big")
    first_code[26:30] = (0x44).to_bytes(4, byteorder="big")
    first_code[0x20:0x2D] = b"icon.library\x00"
    first_code[0x30:0x3A] = b"icon 37.1\x00"
    first_code[0x44:0x48] = (0x24).to_bytes(4, byteorder="big")
    first_code[0x48:0x4C] = (0x54).to_bytes(4, byteorder="big")
    first_code[0x4C:0x50] = (0).to_bytes(4, byteorder="big")
    first_code[0x50:0x54] = (0x88).to_bytes(4, byteorder="big")
    first_code[0x54:0x58] = (0x90).to_bytes(4, byteorder="big")
    first_code[0x58:0x5C] = (0xFFFFFFFF).to_bytes(4, byteorder="big", signed=False)
    first_code[0x88:0x8A] = b"\x4e\x75"
    first_code[0x90:0x92] = b"\x4e\x75"
    second_code = b"\x4e\x75" * 10

    def fake_parse(_data: bytes) -> SimpleNamespace:
        return SimpleNamespace(
            hunks=[
                Hunk(
                    index=0,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=len(first_code),
                    data=bytes(first_code),
                ),
                Hunk(
                    index=1,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=len(second_code),
                    data=second_code,
                ),
            ]
        )

    def fake_load_hunk_analysis(
        *,
        analysis_cache_path: Path,
        code: bytes,
        relocs: list[RelocLike],
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...],
        extra_entry_points: tuple[int, ...],
        seed_key: str,
        initial_state: object,
        entry_initial_states: object | None = None,
    ) -> SimpleNamespace:
        if hunk_index == 0:
                assert entry_points == (0x88, 0x90)
                assert extra_entry_points == ()
                assert isinstance(entry_initial_states, dict)
                assert set(entry_initial_states) == {0x88, 0x90}
                inst = disassemble(b"\x4e\x75")[0]
                inst.offset = 0x88
                block = BasicBlock(
                    start=0x88,
                    end=0x8A,
                    instructions=[inst],
                    is_entry=True,
                )
                return SimpleNamespace(
                    blocks={0x88: block},
                hint_blocks={},
                jump_tables=[],
                call_targets=set(),
                branch_targets=set(),
                lib_calls=[],
                os_kb=runtime_os,
                platform=make_platform(),
                exit_states={},
                relocated_segments=[],
                indirect_sites=[],
                xrefs=[],
            )
        assert hunk_index == 1
        assert entry_points == ()
        assert extra_entry_points == ()
        assert entry_initial_states == {}
        inst = disassemble(b"\x4e\x75")[0]
        inst.offset = 0
        block = BasicBlock(
            start=0,
            end=2,
            instructions=[inst],
            is_entry=True,
        )
        return SimpleNamespace(
            blocks={0: block},
            hint_blocks={},
            jump_tables=[],
            call_targets=set(),
            branch_targets=set(),
            lib_calls=[],
            os_kb=runtime_os,
            platform=make_platform(),
            exit_states={},
            relocated_segments=[],
            indirect_sites=[],
            xrefs=[],
        )

    monkeypatch.setattr("disasm.session.parse", fake_parse)
    monkeypatch.setattr("disasm.session.load_hunk_analysis", fake_load_hunk_analysis)

    session = build_disassembly_session(str(binary_path), str(entities_path))
    rendered = render_session_text(session)

    assert rendered.count("resident_matchword:\n") == 1
    assert "resident_matchword" not in session.hunk_sessions[1].labels.values()
    assert "resident_init" not in session.hunk_sessions[1].labels.values()

def test_emit_session_rows_emits_fd_only_lvo_equates() -> None:
    session = DisassemblySession(
        target_name="demo_graphics",
        binary_path=Path("targets/demo_graphics/binary.bin"),
        entities_path=Path("targets/demo_graphics/entities.jsonl"),
        analysis_cache_path=Path("targets/demo_graphics/binary.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[
            HunkDisassemblySession(
                hunk_index=0,
                code=b"\x4e\x75",
                code_size=2,
                entities=[],
                blocks={
                    0: _FakeBlock(
                        start=0,
                        end=2,
                        successors=(),
                        instructions=[
                            _instruction(
                                offset=0,
                                raw=b"\x4e\x75",
                                mnemonic="rts",
                                operand_size="w",
                                operand_texts=(),
                            )
                        ],
                    )
                },
                hint_blocks={},
                code_addrs={0, 1},
                hint_addrs=set(),
                reloc_map={},
                reloc_target_set=set(),
                pc_targets={},
                string_addrs=set(),
                labels={0: "loc_0000"},
                jump_table_regions={},
                jump_table_target_sources={},
                region_map={},
                lvo_equs={"graphics.library": {-30: "_LVOBltBitMap"}},
                lvo_substitutions={},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                data_access_sizes={},
                platform=make_platform(),
                os_kb=make_empty_os_kb(),
                base_addr=0,
                code_start=0,
                relocated_segments=[],
            )
        ],
        target_metadata=None,
    )

    rendered = "".join(row.text for row in emit_session_rows(session))

    assert "; LVO offsets: graphics.library (FD-derived)\n" in rendered
    assert "_LVOBltBitMap\tEQU\t-30\n" in rendered

def test_absolute_symbol_rows_emit_only_used_external_equ_and_hardware_includes() -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        absolute_labels={
            0x00000004: "AbsExecBase",
        },
    )
    rows = [
        ListingRow(
            row_id="instruction:000000",
            kind="instruction",
            text="",
            operand_parts=(
                SemanticOperand(
                    kind="absolute_target",
                    text="_custom+intena",
                    segment_addr=0x00DFF09A,
                ),
                SemanticOperand(kind="absolute_target", text="AbsExecBase", segment_addr=0x00000004),
                SemanticOperand(kind="absolute_target", text="_ciaa+ciapra", segment_addr=0x00BFE001),
                SemanticOperand(kind="absolute_target", text="$1234", segment_addr=0x00001234),
            ),
        )
    ]

    used = emitter_mod._collect_used_absolute_addrs(rows, hunk_session)
    equ_defs, includes = emitter_mod._absolute_symbol_defs(used, hunk_session)

    assert used == {0x00000004, 0x00DFF09A, 0x00BFE001}
    assert includes == {"hardware/cia.i", "hardware/custom.i"}
    assert equ_defs == {"AbsExecBase": 0x00000004}

def test_collect_used_absolute_addrs_accepts_sized_absolute_symbol_operands() -> None:
    hunk_session = cast(
        HunkDisassemblySession,
        SimpleNamespace(absolute_labels={0x00000004: "AbsExecBase"}),
    )
    rows = [
        ListingRow(
            row_id="row0",
            kind="instruction",
            text="    movea.l AbsExecBase.w,a6\n",
            addr=0x10,
            operand_parts=(
                SemanticOperand(kind="absolute_target", text="AbsExecBase.w", segment_addr=0x00000004),
            ),
        ),
        ListingRow(
            row_id="row1",
            kind="instruction",
            text="    movea.l (AbsExecBase).l,a6\n",
            addr=0x12,
            operand_parts=(
                SemanticOperand(kind="absolute_target", text="(AbsExecBase).l", segment_addr=0x00000004),
            ),
        ),
    ]

    assert emitter_mod._collect_used_absolute_addrs(rows, hunk_session) == {0x00000004}

def test_emit_hunk_rows_emits_fd_derived_lvo_equates(monkeypatch: MonkeyPatch) -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        lvo_equs={"graphics.library": {-36: "_LVOText", -30: "_LVOBltBitMap"}},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )
    monkeypatch.setattr(
        emitter_mod,
        "_OS_INCLUDE_KB",
        SimpleNamespace(
            library_lvo_owners={
                "graphics.library": SimpleNamespace(
                    kind="fd_only",
                    canonical_include_path=None,
                    assembler_include_path="graphics/graphics_lib.i",
                    source_file="FD/GRAPHICS_LIB.FD",
                )
            }
        ),
    )

    rows, _compat_floor, preamble = emitter_mod._emit_hunk_rows(hunk_session, include_header=False)

    assert [row.text for row in rows[:2]] == [
        "    section code,code\n",
        "\n",
    ]
    assert preamble["fd_only_lvo_equs"] == {
        "graphics.library": {
            -36: "_LVOText",
            -30: "_LVOBltBitMap",
        }
    }

def test_emit_session_rows_dedupes_preamble_before_first_hunk() -> None:
    hunk0 = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        reloc_target_hunks={},
        platform=make_platform(),
        os_kb=build_target_local_os_kb(
            runtime_os,
            extra_custom_structs=(
                CustomStructMetadata(
                    name="InferredIconLibraryBase",
                    size=46,
                    fields=(
                        CustomStructFieldMetadata(
                            name="exec_library_base",
                            type="APTR",
                            offset=34,
                            size=4,
                            pointer_struct="ExecBase",
                            named_base="exec.library",
                        ),
                    ),
                    seed_origin="manual_analysis",
                    review_status="seeded",
                    citation="test",
                    base_struct="LIB",
                    base_offset=runtime_os.STRUCTS["LIB"].size,
                ),
            ),
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        lvo_equs={"exec.library": {-198: "_LVOAllocMem"}},
        region_map={
            0x100: {
                "a2": TypedMemoryRegion(
                    struct="InferredIconLibraryBase",
                    size=46,
                    provenance=provenance_named_base("icon.library"),
                )
            }
        },
    )
    hunk1 = replace(
        hunk0,
        hunk_index=1,
    )
    rendered = emitter_mod.render_session_text(
        DisassemblySession(
            target_name="demo",
            binary_path=Path("demo.bin"),
            entities_path=Path("entities.jsonl"),
            analysis_cache_path=Path("analysis"),
            output_path=None,
            entities=[],
            hunk_sessions=[hunk0, hunk1],
        )
    )

    assert rendered.count('    INCLUDE "exec/exec_lib.i"\n') == 1
    assert rendered.count("exec_library_base\tEQU\t34\n") == 1
    first_section = rendered.index("    section code,code\n")
    assert rendered.index('    INCLUDE "exec/exec_lib.i"\n') < first_section
    assert rendered.index("exec_library_base\tEQU\t34\n") < first_section

def test_emit_session_rows_uses_selected_assembler_profile() -> None:
    hunk = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )
    rendered = emitter_mod.render_session_text(
        DisassemblySession(
            target_name="demo",
            binary_path=Path("demo.bin"),
            entities_path=Path("entities.jsonl"),
            analysis_cache_path=Path("analysis"),
            output_path=None,
            entities=[],
            hunk_sessions=[hunk],
            assembler_profile_name="devpac",
        )
    )

    assert rendered.startswith("; Generated disassembly -- GenAm Motorola syntax\n")
    assert "\n    SECTION code,code\n" in rendered

def test_emit_session_rows_emits_orphan_hint_bytes_as_data() -> None:
    hunk = HunkDisassemblySession(
        hunk_index=0,
        code=b"\x11\x22\x33\x44",
        code_size=4,
        entities=[],
        blocks={},
        hint_addrs={0, 1, 2, 3},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )
    rendered = emitter_mod.render_session_text(
        DisassemblySession(
            target_name="demo",
            binary_path=Path("demo.bin"),
            entities_path=Path("entities.jsonl"),
            analysis_cache_path=Path("analysis"),
            output_path=None,
            entities=[],
            hunk_sessions=[hunk],
        )
    )

    assert "    dc.b    $11,$22,$33,$44\n" in rendered

def test_emit_session_rows_does_not_emit_hint_code_inside_unknown_entity() -> None:
    hint_inst = Instruction(
        offset=2,
        size=2,
        opcode=0x4E75,
        text="rts",
        raw=b"\x4E\x75",
        kb_mnemonic="RTS",
        operand_size="w",
    )
    hunk = HunkDisassemblySession(
        hunk_index=0,
        code=b"\x11\x22\x4E\x75",
        code_size=4,
        entities=[{"addr": "0000", "end": "0004", "type": "unknown"}],
        blocks={},
        hint_blocks={2: _FakeBlock(start=2, end=4, successors=(), instructions=[hint_inst])},
        hint_addrs={2, 3},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )
    rendered = emitter_mod.render_session_text(
        DisassemblySession(
            target_name="demo",
            binary_path=Path("demo.bin"),
            entities_path=Path("entities.jsonl"),
            analysis_cache_path=Path("analysis"),
            output_path=None,
            entities=[],
            hunk_sessions=[hunk],
        )
    )

    assert "; --- unverified ---\n" not in rendered
    assert "    rts\n" not in rendered
    assert "    dc.b    $11,$22\n" in rendered
    assert "    dc.b    $4e,$75\n" in rendered

def test_emit_session_rows_does_not_emit_hint_code_inside_code_entity() -> None:
    hint_inst = Instruction(
        offset=0,
        size=2,
        opcode=0x4E75,
        text="rts",
        raw=b"\x4E\x75",
        kb_mnemonic="RTS",
        operand_size="w",
    )
    hunk = HunkDisassemblySession(
        hunk_index=0,
        code=b"\x4E\x75",
        code_size=2,
        entities=[{"addr": "0000", "end": "0002", "type": "code", "confidence": "hint"}],
        blocks={},
        hint_blocks={0: _FakeBlock(start=0, end=2, successors=(), instructions=[hint_inst])},
        hint_addrs={0, 1},
        labels={0: "hint_0000"},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )
    rendered = emitter_mod.render_session_text(
        DisassemblySession(
            target_name="demo",
            binary_path=Path("demo.bin"),
            entities_path=Path("entities.jsonl"),
            analysis_cache_path=Path("analysis"),
            output_path=None,
            entities=[],
            hunk_sessions=[hunk],
        )
    )

    assert "; --- unverified ---\n" not in rendered
    assert "    rts\n" not in rendered
    assert "hint_0000:\n" in rendered
    assert "    dc.b    $4e,$75\n" in rendered

def test_build_listing_rows_delegates_to_session_builder(monkeypatch: MonkeyPatch) -> None:
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[],
    )
    rows: list[ListingRow] = [ListingRow(row_id="r0", kind="instruction", text="nop\n", addr=0)]
    calls: list[str] = []

    def fake_build(
        binary_path: str,
        entities_path: str,
        output_path: str | None,
        base_addr: int = 0,
        code_start: int = 0,
        assembler_profile_name: str = "vasm",
        profile_stages: bool = False,
    ) -> DisassemblySession:
        calls.append("build")
        assert binary_path == "bin/demo"
        assert entities_path == "targets/demo/entities.jsonl"
        assert output_path is None
        assert base_addr == 0x400
        assert code_start == 2
        assert assembler_profile_name == "vasm"
        return session

    def fake_emit(seen_session: DisassemblySession) -> list[ListingRow]:
        calls.append("emit")
        assert seen_session is session
        return rows

    monkeypatch.setattr(emitter_mod, "build_disassembly_session", fake_build)
    monkeypatch.setattr(emitter_mod, "emit_session_rows", fake_emit)

    result = emitter_mod.build_listing_rows("bin/demo", "targets/demo/entities.jsonl",
                                            base_addr=0x400, code_start=2)

    assert calls == ["build", "emit"]
    assert result == rows

def test_emit_hunk_rows_renders_structured_string_with_embedded_quotes() -> None:
    data = b'Say "it\'s ok"\x00'
    hunk = HunkDisassemblySession(
        hunk_index=0,
        code=data,
        code_size=len(data),
        entities=[],
        blocks={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
    )

    rows, _compat, _preamble = emitter_mod._emit_hunk_rows(
        hunk,
        include_header=False,
        structured_regions=(
            StructuredRegionSpec(
                start=0,
                end=len(data),
                subtype="structured_data",
                fields=(
                    StructuredFieldSpec(offset=0, label="quoted_string", is_string=True),
                ),
            ),
        ),
    )

    rendered = "".join(row.text for row in rows)
    assert 'DC.B    "Say ",' in rendered or 'dc.b    "Say ",' in rendered
    assert '"it"' in rendered
    assert '"\'"' in rendered

