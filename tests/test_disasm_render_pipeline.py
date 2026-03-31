from __future__ import annotations

"""Disassembly rendering and listing tests."""

from tests.disasm_pipeline_support import (
    AddressRowContext,
    DisassemblySession,
    HunkDisassemblySession,
    IndirectSite,
    IndirectSiteRegion,
    IndirectSiteStatus,
    Instruction,
    JumpTableEntryRef,
    JumpTableRegion,
    LibraryCall,
    ListingRow,
    MemoryRegionAddressSpace,
    MemoryRegionProvenance,
    MonkeyPatch,
    Path,
    SemanticOperand,
    TypedMemoryRegion,
    _block,
    build_instruction_comment_parts,
    data_render_mod,
    decode_stream_by_name,
    emit_jump_table_rows,
    emitter_mod,
    format_typed_data_stream_command,
    get_instruction_processor_min,
    has_valid_branch_target,
    hint_block_has_supported_terminal_flow,
    io,
    is_valid_hint_block,
    listing_window,
    listing_window_payload,
    load_assembler_profile,
    make_empty_os_kb,
    make_platform,
    pytest,
    render_comment_parts,
    render_instruction_text,
    render_rows,
    runtime_m68k_analysis,
    runtime_os,
    serialize_row,
    session_metadata,
)


def test_render_rows_concatenates_listing_text() -> None:
    rows = [
        ListingRow(row_id="a", kind="comment", text="; one\n"),
        ListingRow(row_id="b", kind="instruction", text="moveq #0,d0\n"),
    ]

    assert render_rows(rows) == "; one\nmoveq #0,d0\n"

def test_render_comment_parts_joins_non_empty_parts() -> None:
    assert render_comment_parts(("68020+", "", "note")) == "68020+; note"

def test_build_instruction_comment_parts_prefers_app_offset_before_ascii() -> None:
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
        lvo_equs={"exec.library": {-456: "_LVODoIO"}},
        lvo_substitutions={0: ("rts", "_LVODoIO(a6)")},
        platform=make_platform(app_base=(6, 0)),
        os_kb=make_empty_os_kb(),
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
            SemanticOperand(kind="immediate", value=0x4C494E45,
                            base_register=None, displacement=None,
                            text="#$4C494E45"),
            SemanticOperand(kind="base_displacement", value=568,
                            base_register="a6", displacement=568,
                            text="568(a6)"),
        ))

    assert parts == ("app+$238",)

def test_build_instruction_comment_parts_uses_instruction_processor_min_not_text() -> None:
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
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
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
            SemanticOperand(kind="register", value=None,
                            base_register=None, displacement=None,
                            text="d0"),
        ))
    assert parts == ("68020+",)

def test_render_instruction_text_requires_opcode_text() -> None:
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
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    from disasm.instruction_rows import render_instruction_text

    with pytest.raises(AssertionError, match="missing opcode_text"):
        render_instruction_text(inst, session, set())

def test_build_instruction_comment_parts_uses_decoded_immediate_not_rendered_text() -> None:
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
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
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
            SemanticOperand(kind="immediate", value=0x4C494E45,
                            base_register=None, displacement=None,
                            text="#$4C494E45"),
            SemanticOperand(kind="register", value=None,
                            base_register=None, displacement=None,
                            text="d0"),
        ))

    assert parts == ("'LINE'",)

def test_build_instruction_comment_parts_appends_unresolved_indirect_marker() -> None:
    session = HunkDisassemblySession(
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
        reloc_file_offset=0,
        reloc_base_addr=0,
        unresolved_indirects={0x20: IndirectSite(
            addr=0x20,
            mnemonic="JSR",
            flow_type=runtime_m68k_analysis.FlowType.CALL,
            shape="pcindex.brief",
            status=IndirectSiteStatus.UNRESOLVED,
            target=None,
            region=IndirectSiteRegion.CORE,
        )},
    )
    inst = Instruction(
        offset=0x20,
        size=2,
        opcode=0x4E90,
        text="corrupted",
        raw=b"\x4E\x90",
        kb_mnemonic="jsr",
    )

    parts = build_instruction_comment_parts(inst, session, ())

    assert parts == ("unresolved_indirect_core:pcindex.brief",)

def test_build_instruction_comment_parts_suppresses_unresolved_marker_for_refined_lib_call() -> None:
    inst = Instruction(
        offset=0x20,
        size=4,
        opcode=0x4EAE,
        text="jsr -210(a6)",
        raw=b"\x4e\xae\xff\x2e",
        kb_mnemonic="jsr",
        operand_size="l",
        operand_texts=("-210(a6)",),
    )
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={},
        code_addrs={0x20},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        unresolved_indirects={
            0x20: IndirectSite(
                addr=0x20,
                mnemonic="JSR",
                flow_type=runtime_m68k_analysis.FlowType.CALL,
                shape="disp",
                target=None,
                region=IndirectSiteRegion.CORE,
                status=IndirectSiteStatus.UNRESOLVED,
            )
        },
        lib_calls=(
            LibraryCall(
                addr=0x20,
                block=0x20,
                library="exec.library",
                function="FreeMem",
                lvo=-210,
            ),
        ),
    )

    parts = build_instruction_comment_parts(inst, hunk_session, operand_parts=())

    assert parts == ()

def test_get_instruction_processor_min_reports_base_68000_instruction() -> None:
    inst = Instruction(
        offset=0x10,
        size=2,
        opcode=0x7000,
        text="moveq   #0,d0",
        raw=b"\x70\x00",
        kb_mnemonic="moveq",
        operand_size="l",
    )
    assert get_instruction_processor_min(inst) == "68000"

def test_get_instruction_processor_min_respects_68000_size_constraints() -> None:
    inst = Instruction(
        offset=0x10,
        size=2,
        opcode=0x4380,
        text="chk.l   d0,d1",
        raw=b"\x43\x80",
        kb_mnemonic="chk",
        operand_size="l",
    )
    assert get_instruction_processor_min(inst) == "68020"

def test_has_valid_branch_target_rejects_odd_branch_target() -> None:
    inst = Instruction(
        offset=0x40,
        size=2,
        opcode=0x6605,
        text="bne.s   $000047",
        raw=b"\x66\x05",
        kb_mnemonic="bcc",
    )

    assert has_valid_branch_target(inst) is False

def test_hint_block_has_supported_terminal_flow_for_return() -> None:
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

    assert hint_block_has_supported_terminal_flow(block) is True

def test_is_valid_hint_block_rejects_non_68000_instruction() -> None:
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

    assert is_valid_hint_block(block) is False

def test_is_valid_hint_block_rejects_profile_unsupported_hint_operand_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    hunk_session = type("HunkSession", (), {"assembler_profile_name": "devpac"})()

    monkeypatch.setattr(
        "disasm.hint_validation.instruction_operands_render_completely",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "disasm.hint_validation.build_instruction_semantic_operands",
        lambda *args, **kwargs: (
            SemanticOperand(
                kind="memory_indirect_indexed",
                text="([1234,a0],d0.w,8)",
            ),
        ),
    )

    assert is_valid_hint_block(block, hunk_session) is False

def test_emit_jump_table_rows_emits_data_entries() -> None:
    rows: list[ListingRow] = []
    labels_seen = []

    def emit_label(addr: int) -> None:
        labels_seen.append(addr)

    hunk_session = type("HunkSession", (), {
        "jump_table_regions": {
            0x20: JumpTableRegion(
                pattern="word_table",
                entries=(JumpTableEntryRef(0x20, 0x80), JumpTableEntryRef(0x22, 0x90)),
                base_label="ignored",
                table_end=0x24,
            )
        },
        "labels": {0x80: "loc_0080", 0x90: "loc_0090"},
    })()

    end = emit_jump_table_rows(
        rows, hunk_session, 0x20, 0x20, set(), emit_label)

    assert end == 0x24
    assert labels_seen == []
    assert len(rows) == 2
    assert rows[0].text == "    dc.w    loc_0080-*\n"

def test_emit_jump_table_rows_anchors_self_relative_data_for_devpac() -> None:
    rows: list[ListingRow] = []
    labels_seen: list[int] = []

    def emit_label(addr: int) -> None:
        labels_seen.append(addr)

    hunk_session = type("HunkSession", (), {
        "hunk_index": 0,
        "code": b"",
        "reloc_map": {},
        "string_addrs": set(),
        "reloc_labels": {},
        "data_access_sizes": {},
        "typed_data_sizes": {},
        "typed_data_fields": {},
        "os_kb": make_empty_os_kb(),
        "addr_comments": {},
        "jump_table_regions": {
            0x20: JumpTableRegion(
                pattern="word_table",
                entries=(JumpTableEntryRef(0x20, 0x80), JumpTableEntryRef(0x22, 0x90)),
                base_label="ignored",
                table_end=0x24,
            )
        },
        "labels": {
            0x20: "jtent_0020",
            0x22: "jtent_0022",
            0x80: "loc_0080",
            0x90: "loc_0090",
        },
        "entities": [],
        "blocks": {0x80: object(), 0x90: object()},
        "hint_blocks": {},
        "generic_data_label_addrs": set(),
    })()

    end = emit_jump_table_rows(
        rows, hunk_session, 0x20, 0x20, set(), emit_label, load_assembler_profile("devpac"))

    assert end == 0x24
    assert labels_seen == [0x22]
    assert rows[0].text == "    DC.W    loc_0080-jtent_0020\n"

def test_emit_jump_table_rows_uses_bytes_for_unaligned_devpac_word_entry() -> None:
    rows: list[ListingRow] = []

    def emit_label(_addr: int) -> None:
        raise AssertionError("Unexpected label emission")

    hunk_session = type("HunkSession", (), {
        "hunk_index": 0,
        "code": b"",
        "reloc_map": {},
        "string_addrs": set(),
        "reloc_labels": {},
        "data_access_sizes": {},
        "typed_data_sizes": {},
        "typed_data_fields": {},
        "os_kb": make_empty_os_kb(),
        "addr_comments": {},
        "jump_table_regions": {
            0x21: JumpTableRegion(
                pattern="word_table",
                entries=(JumpTableEntryRef(0x21, 0x80),),
                base_label="ignored",
                table_end=0x23,
            )
        },
        "labels": {
            0x21: "jtent_0021",
            0x80: "loc_0080",
        },
        "entities": [],
        "blocks": {},
        "hint_blocks": {},
        "generic_data_label_addrs": set(),
    })()

    end = emit_jump_table_rows(
        rows, hunk_session, 0x21, 0x21, set(), emit_label, load_assembler_profile("devpac"))

    assert end == 0x23
    assert rows[0].text == "    DC.B    $00,$5f\n"

def test_emit_jump_table_rows_emits_inline_dispatch_rows() -> None:
    rows: list[ListingRow] = []
    labels_seen = []

    def emit_label(addr: int) -> None:
        labels_seen.append(addr)

    code = b"\x70\x00\x4E\x75"
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=code,
        code_size=len(code),
        entities=[],
        blocks={},
        labels={0x02: "loc_0002"},
        jump_table_regions={
            0x00: JumpTableRegion(pattern="pc_inline_dispatch", table_end=0x04)
        },
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
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

def test_emit_jump_table_rows_emits_string_dispatch_rows() -> None:
    rows: list[ListingRow] = []

    def emit_label(addr: int) -> None:
        raise AssertionError(f"Unexpected label emission at ${addr:04x}")

    code = bytes([1, 1, 0, 6, 1, 2, 0, 8, 0, 0x4E, 0x75, 0x4E, 0x75])
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=code,
        code_size=len(code),
        entities=[],
        blocks={},
        labels={0x08: "loc_0008", 0x0A: "loc_000a"},
        jump_table_regions={
            0x00: JumpTableRegion(
                pattern="string_dispatch_self_relative",
                entries=(JumpTableEntryRef(0x02, 0x08), JumpTableEntryRef(0x06, 0x0A)),
                table_end=0x08,
            )
        },
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    end = emit_jump_table_rows(
        rows, hunk_session, 0x00, 0x00, set(), emit_label)

    assert end == 0x08
    assert [row.text for row in rows] == [
        "    dc.b    $01,$01\n",
        "    dc.w    loc_0008-*\n",
        "    dc.b    $01,$02\n",
        "    dc.w    loc_000a-*\n",
    ]

def test_emit_jump_table_rows_preserves_sparse_word_gaps() -> None:
    rows: list[ListingRow] = []

    def emit_label(addr: int) -> None:
        raise AssertionError(f"Unexpected label emission at ${addr:04x}")

    code = bytes.fromhex("0000000400000008")
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=code,
        code_size=len(code),
        entities=[],
        blocks={},
        labels={0x20: "loc_0020", 0x24: "loc_0024"},
        jump_table_regions={
            0x00: JumpTableRegion(
                pattern="pc_sparse_word_offset",
                entries=(JumpTableEntryRef(0x02, 0x20), JumpTableEntryRef(0x06, 0x24)),
                base_addr=0x00,
                base_label="jt_0000",
                table_end=0x08,
            )
        },
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    end = emit_jump_table_rows(
        rows, hunk_session, 0x00, 0x00, set(), emit_label)

    assert end == 0x08
    assert [row.text for row in rows] == [
        "    dc.b    $00,$00\n",
        "    dc.w    loc_0020-jt_0000\n",
        "    dc.b    $00,$00\n",
        "    dc.w    loc_0024-jt_0000\n",
    ]

def test_listing_window_anchors_to_matching_addr() -> None:
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="", addr=0x10),
        ListingRow(row_id="r1", kind="instruction", text="", addr=0x20),
        ListingRow(row_id="r2", kind="instruction", text="", addr=0x30),
    ]

    window = listing_window(rows, 0x20, before=1, after=1)

    assert [row.row_id for row in window["rows"]] == ["r0", "r1", "r2"]
    assert window["start"] == 0
    assert window["end"] == 3

def test_listing_window_anchors_to_last_row_past_end() -> None:
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="", addr=0x10),
        ListingRow(row_id="r1", kind="instruction", text="", addr=0x20),
        ListingRow(row_id="r2", kind="instruction", text="", addr=0x30),
    ]

    window = listing_window(rows, 0x40, before=1, after=0)

    assert [row.row_id for row in window["rows"]] == ["r1", "r2"]
    assert window["has_more_before"] is True
    assert window["has_more_after"] is False

def test_decode_stream_by_name_decodes_autoinit_commands() -> None:
    code = bytes.fromhex(
        "e0 00 00 08 09 00"
        "c0 00 00 0a 00 00 00 18"
        "00"
    ) + b"dos.library\x00"

    spec = runtime_os.META.typed_data_stream_formats["exec.InitStruct"]
    stream = decode_stream_by_name(code, 0, runtime_os, "exec.InitStruct")

    assert stream is not None
    assert stream.end == 15
    assert len(stream.commands) == 2
    assert format_typed_data_stream_command(
        stream.commands[0],
        spec=spec,
        code=code,
        labels={0x18: "dos_name"},
        reloc_map={},
        reloc_labels={},
        structs=runtime_os.STRUCTS,
        struct_name="LIB",
    ) == "INITBYTE LN_TYPE,$09"
    assert format_typed_data_stream_command(
        stream.commands[1],
        spec=spec,
        code=code,
        labels={0x18: "dos_name"},
        reloc_map={10: 0x18},
        reloc_labels={10: "dos_name"},
        structs=runtime_os.STRUCTS,
        struct_name="LIB",
    ) == "INITLONG LN_NAME,dos_name"

def test_render_instruction_text_substitutes_field_domain_constant_for_trackdisk_io_command() -> None:
    inst = Instruction(
        offset=0x22,
        size=6,
        opcode=0x337C,
        text="move.w",
        raw=b"\x33\x7c\x00\x02\x00\x1c",
        opcode_text="move.w",
        kb_mnemonic="move",
        operand_size="w",
        operand_texts=("#$2", "$1c(a1)"),
    )
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={},
        code_addrs={inst.offset},
        region_map={
            inst.offset: {
                "a1": TypedMemoryRegion(
                    struct="IO",
                    size=runtime_os.STRUCTS["IO"].size,
                    provenance=MemoryRegionProvenance(
                        address_space=MemoryRegionAddressSpace.REGISTER,
                    ),
                    context_name="trackdisk.device",
                )
            }
        },
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    text, _comment, _parts = render_instruction_text(inst, hunk_session, set())

    assert text == "move.w #CMD_READ,IO_COMMAND(a1)"

def test_serialize_row_preserves_structured_fields() -> None:
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
        source_context=AddressRowContext(block=0x20),
    )

    payload = serialize_row(row)

    assert payload["row_id"] == "row0"
    assert payload["bytes"] == "7000"
    assert payload["operand_parts"][0]["kind"] == "immediate"
    assert payload["source_context"] == {"block": 0x20}

def test_session_metadata_summarizes_hunks() -> None:
    block = _block(0, 2)
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=Path("targets/test/entities.jsonl"),
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=Path("targets/test/out.s"),
        entities=[{"addr": "0000", "type": "code"}],
        hunk_sessions=[
            HunkDisassemblySession(
                hunk_index=0,
                code=b"\x4e\x75",
                code_size=2,
                entities=[{"addr": "0000", "type": "code"}],
                blocks={0: block},
                hint_blocks={},
                code_addrs={0, 1},
                hint_addrs=set(),
                reloc_map={},
                reloc_target_set=set(),
                pc_targets={},
                string_addrs=set(),
                labels={0: "entry_point"},
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

def test_listing_window_payload_serializes_rows() -> None:
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

def test_render_session_text_renders_emitted_rows(monkeypatch: MonkeyPatch) -> None:
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[],
    )
    rows: list[ListingRow] = [ListingRow(row_id="r0", kind="instruction", text="moveq #0,d0\n", addr=0)]
    calls: list[str] = []

    def fake_emit(seen_session: DisassemblySession) -> list[ListingRow]:
        calls.append("emit")
        assert seen_session is session
        return rows

    def fake_render(seen_rows: list[ListingRow]) -> str:
        calls.append("render")
        assert seen_rows == rows
        return "; rendered\n"

    monkeypatch.setattr(emitter_mod, "emit_session_rows", fake_emit)
    monkeypatch.setattr(emitter_mod, "render_rows", fake_render)

    assert emitter_mod.render_session_text(session) == "; rendered\n"
    assert calls == ["emit", "render"]

def test_emit_data_region_renders_relocated_longword_label() -> None:
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

def test_emit_data_region_renders_cross_hunk_relocated_longword_label() -> None:
    output = io.StringIO()

    data_render_mod.emit_data_region(
        output,
        code=b"\x00\x00\x00\x20",
        start=0,
        end=4,
        labels={},
        reloc_map={0: 0x20},
        string_addrs=set(),
        reloc_labels={0: "hunk_3_sub_0020"},
    )

    assert output.getvalue() == "    dc.l    hunk_3_sub_0020\n"

def test_emit_data_region_renders_zero_fill_run() -> None:
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

def test_emit_data_region_renders_ascii_string() -> None:
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
