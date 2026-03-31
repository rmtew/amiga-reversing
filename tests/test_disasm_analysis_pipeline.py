from __future__ import annotations

"""Disassembly analysis and substitution tests."""

from tests.disasm_pipeline_support import (
    _OS_INCLUDE_KB,
    AppBaseInfo,
    AppBaseKind,
    CallArgumentAnnotation,
    Instruction,
    LibraryBaseTag,
    LibraryCall,
    Path,
    SeededCodeEntrypointMetadata,
    SeededCodeLabelMetadata,
    SimpleNamespace,
    TargetMetadata,
    _apply_seeded_code_annotations,
    _instruction,
    _refresh_library_call_signatures,
    _test_constant,
    _test_library,
    analyze_call_setups,
    build_app_slot_symbols,
    build_arg_substitutions,
    build_lvo_substitutions,
    infer_target_name,
    load_canonical_os_kb,
    load_entities,
    make_empty_os_kb,
    make_platform,
    pytest,
    replace,
    runtime_os,
)


def test_os_include_kb_contains_device_include_mappings() -> None:
    assert _OS_INCLUDE_KB.library_lvo_owners["timer.device"].canonical_include_path == "devices/timer.i"
    assert _OS_INCLUDE_KB.library_lvo_owners["timer.device"].assembler_include_path == "devices/timer_lib.i"
    assert _OS_INCLUDE_KB.library_lvo_owners["console.device"].canonical_include_path == "devices/console.i"
    assert _OS_INCLUDE_KB.library_lvo_owners["console.device"].assembler_include_path == "devices/console_lib.i"

def test_os_include_kb_loads_from_main_os_reference() -> None:
    payload = load_canonical_os_kb()
    assert "library_lvo_owners" not in payload["_meta"]
    assert payload["libraries"]["exec.library"]["owner"]["canonical_include_path"] == "exec/exec_lib.i"

def test_load_entities_reads_jsonl(tmp_path: Path) -> None:
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

def test_infer_target_name_prefers_target_dir(tmp_path: Path) -> None:
    target_dir = tmp_path / "demo"
    entities_path = target_dir / "entities.jsonl"

    assert infer_target_name(target_dir, entities_path) == "demo"

def test_infer_target_name_falls_back_to_entities_parent(tmp_path: Path) -> None:
    entities_path = tmp_path / "demo" / "entities.jsonl"

    assert infer_target_name(None, entities_path) == "demo"

def test_apply_seeded_code_annotations_adds_labels_and_notes() -> None:
    labels: dict[int, str] = {}
    comments: dict[int, str] = {}
    metadata = TargetMetadata(
        target_type="program",
        entry_register_seeds=(),
        seeded_code_labels=(
            SeededCodeLabelMetadata(
                addr=0x10,
                name="named_label",
                hunk=0,
                comment="seeded note",
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="demo",
            ),
        ),
        seeded_code_entrypoints=(
            SeededCodeEntrypointMetadata(
                addr=0x20,
                name="entry_name",
                hunk=0,
                role="input routine",
                comment="seeded comment",
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="demo",
            ),
        ),
    )

    _apply_seeded_code_annotations(
        target_metadata=metadata,
        hunk_index=0,
        code_size=0x40,
        labels=labels,
        addr_comments=comments,
    )

    assert labels == {0x10: "named_label", 0x20: "entry_name"}
    assert comments == {0x10: "seeded note", 0x20: "input routine: seeded comment"}

def test_apply_seeded_code_annotations_rejects_out_of_bounds_label() -> None:
    metadata = TargetMetadata(
        target_type="program",
        entry_register_seeds=(),
        seeded_code_labels=(
            SeededCodeLabelMetadata(
                addr=0x40,
                name="named_label",
                hunk=0,
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="demo",
            ),
        ),
    )

    with pytest.raises(ValueError, match="Seeded code label 0x40 lies outside code size 0x40"):
        _apply_seeded_code_annotations(
            target_metadata=metadata,
            hunk_index=0,
            code_size=0x40,
            labels={},
            addr_comments={},
        )

def test_build_lvo_substitutions_collects_direct_jsr_substitution() -> None:
    call = LibraryCall(
        addr=0x20,
        block=0x20,
        library="dos.library",
        function="OpenLibrary",
        lvo=-552,
    )

    lvo_equs, lvo_substitutions = build_lvo_substitutions(
        blocks={},
        lib_calls=[call],
        hunk_entities=[],
    )

    assert lvo_equs == {"dos.library": {-552: "_LVOOpenLibrary"}}
    assert lvo_substitutions == {0x20: ("-552(", "_LVOOpenLibrary(")}

def test_build_lvo_substitutions_collects_dispatch_call_lvo_from_call_site() -> None:
    setter = Instruction(
        offset=0x12,
        size=2,
        opcode=0x70E2,
        text="corrupted",
        raw=b"\x70\xe2",
        kb_mnemonic="moveq",
        operand_size="l",
        operand_texts=("#-30", "d0"),
    )
    call_inst = Instruction(
        offset=0x14,
        size=4,
        opcode=0x6100,
        text="corrupted",
        raw=b"\x61\x00\x00\x2a",
        kb_mnemonic="bsr",
        operand_size="w",
        operand_texts=("$0040",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()

    lvo_equs, lvo_substitutions = build_lvo_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x14,
            block=0x10,
            library="dos.library",
            function="Open",
            lvo=-30,
            dispatch=0x42,
        )],
        hunk_entities=[{"addr": "0040", "end": "0050", "type": "code"}],
    )

    assert lvo_equs == {"dos.library": {-30: "_LVOOpen"}}
    assert lvo_substitutions == {0x12: ("#-30", "#_LVOOpen")}

def test_build_arg_substitutions_collects_immediate_constant() -> None:
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
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},

        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"OpenLibrary": {"name": "test.openlibrary.name"}}},
        VALUE_DOMAINS={"test.openlibrary.name": runtime_os.OsValueDomain(kind="enum", members=("OL_TAG",), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={"OL_TAG": _test_constant(raw="1", value=1)},
        LIBRARIES={
            "dos.library": _test_library(
                {
                    "OpenLibrary": runtime_os.OsFunction(
                        lvo=-552,
                        inputs=(runtime_os.OsInput(name="name", regs=("d0",)),),
                    )
                },
            )
        },
    )

    arg_constants, arg_substitutions = build_arg_substitutions(
        blocks={0x20: block},
        hunk_entities=[],
        lib_calls=[LibraryCall(
            addr=0x20,
            block=0x20,
            library="dos.library",
            function="OpenLibrary",
            lvo=-552,
        )],
        os_kb=os_kb,
    )

    assert arg_constants == {"OL_TAG"}
    assert arg_substitutions == {0x10: ("#1", "#OL_TAG")}

def test_build_arg_substitutions_collects_dispatch_call_constant() -> None:
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
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},

        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"Seek": {"mode": "test.seek.mode"}}},
        VALUE_DOMAINS={"test.seek.mode": runtime_os.OsValueDomain(kind="enum", members=("OFFSET_BEGINNING", "OFFSET_CURRENT"), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={
            "OFFSET_BEGINNING": _test_constant(raw="-1", value=-1),
            "OFFSET_CURRENT": _test_constant(raw="0", value=0),
        },
        LIBRARIES={
            "dos.library": _test_library(
                {
                    "Seek": runtime_os.OsFunction(
                        lvo=-66,
                        inputs=(
                            runtime_os.OsInput(name="arg1", regs=("d1",)),
                            runtime_os.OsInput(name="arg2", regs=("d2",)),
                            runtime_os.OsInput(name="mode", regs=("d3",)),
                        ),
                    )
                },
            )
        },
    )

    arg_constants, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x10,
            block=0x10,
            library="dos.library",
            function="Seek",
            lvo=-66,
            dispatch=0x42,
        )],
        hunk_entities=[{"addr": "0040", "end": "0050", "type": "code"}],
        os_kb=os_kb,
    )

    assert arg_constants == {"OFFSET_BEGINNING"}
    assert arg_substitutions == {0x12: ("#-1", "#OFFSET_BEGINNING")}

def test_build_arg_substitutions_collects_long_immediate_constant() -> None:
    setter = _instruction(
        offset=0x10,
        raw=b"\x22\x3c\x00\x00\x10\x00",
        mnemonic="move",
        operand_size="l",
        operand_texts=("#$1000", "d1"),
    )
    call_inst = _instruction(
        offset=0x16,
        raw=b"\x4e\x75",
        mnemonic="jsr",
        operand_size="w",
        operand_texts=("_LVOSetSignal(a6)",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},

        ),
        API_INPUT_VALUE_DOMAINS={"exec.library": {"SetSignal": {"signalMask": "test.exec.signal_mask"}}},
        VALUE_DOMAINS={"test.exec.signal_mask": runtime_os.OsValueDomain(kind="flags", members=("SIGBREAKF_CTRL_C",), zero_name=None, exact_match_policy="error", composition="bit_or", remainder_policy="error")},
        CONSTANTS={
            "SIGBREAKF_CTRL_C": _test_constant(raw="(1<<12)", value=0x1000),
        },
        LIBRARIES={
            "exec.library": _test_library(
                {
                    "SetSignal": runtime_os.OsFunction(
                        lvo=-306,
                        inputs=(
                            runtime_os.OsInput(name="newSignals", regs=("d0",)),
                            runtime_os.OsInput(name="signalMask", regs=("d1",)),
                        ),
                    )
                },
            )
        },
    )

    arg_constants, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x16,
            block=0x10,
            library="exec.library",
            function="SetSignal",
            lvo=-306,
            dispatch=None,
        )],
        hunk_entities=[],
        os_kb=os_kb,
    )

    assert arg_constants == {"SIGBREAKF_CTRL_C"}
    assert arg_substitutions == {0x10: ("#$1000", "#SIGBREAKF_CTRL_C")}

def test_build_arg_substitutions_collects_open_mode_constant() -> None:
    setter = _instruction(
        offset=0x10,
        raw=b"\x24\x3c\x00\x00\x03\xed",
        mnemonic="move",
        operand_size="l",
        operand_texts=("#$3ed", "d2"),
    )
    call_inst = _instruction(
        offset=0x12,
        raw=b"\x4e\x75",
        mnemonic="jsr",
        operand_size="w",
        operand_texts=("_LVOOpen(a6)",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},

        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"Open": {"accessMode": "test.open.access_mode"}}},
        VALUE_DOMAINS={"test.open.access_mode": runtime_os.OsValueDomain(kind="enum", members=("MODE_OLDFILE", "MODE_NEWFILE", "MODE_READWRITE"), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={
            "MODE_OLDFILE": _test_constant(raw="1005", value=0x3ED),
            "MODE_NEWFILE": _test_constant(raw="1006", value=0x3EE),
            "MODE_READWRITE": _test_constant(raw="1004", value=0x3EC),
        },
        LIBRARIES={
            "dos.library": _test_library(
                {
                    "Open": runtime_os.OsFunction(
                        lvo=-30,
                        inputs=(
                            runtime_os.OsInput(name="name", regs=("d1",)),
                            runtime_os.OsInput(name="accessMode", regs=("d2",)),
                        ),
                    )
                },
            )
        },
    )

    arg_constants, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x12,
            block=0x10,
            library="dos.library",
            function="Open",
            lvo=-30,
            dispatch=None,
        )],
        hunk_entities=[],
        os_kb=os_kb,
    )

    assert arg_constants == {"MODE_OLDFILE"}
    assert arg_substitutions == {0x10: ("#$3ed", "#MODE_OLDFILE")}

def test_build_arg_substitutions_collects_composed_flag_constants() -> None:
    setter = _instruction(
        offset=0x10,
        raw=b"\x22\x3c\x00\x00\x00\x03",
        mnemonic="move",
        operand_size="l",
        operand_texts=("#3", "d1"),
    )
    call_inst = _instruction(
        offset=0x16,
        raw=b"\x4e\x75",
        mnemonic="jsr",
        operand_size="w",
        operand_texts=("_LVOAllocMem(a6)",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},

        ),
        API_INPUT_VALUE_DOMAINS={"exec.library": {"AllocMem": {"attributes": "test.alloc.attributes"}}},
        VALUE_DOMAINS={
            "test.alloc.attributes": runtime_os.OsValueDomain(
                kind="flags",
                members=("MEMF_PUBLIC", "MEMF_CHIP", "MEMF_FAST"),
                zero_name=None,
                exact_match_policy="error",
                composition="bit_or",
                remainder_policy="error",
            )
        },
        CONSTANTS={
            "MEMF_PUBLIC": _test_constant(raw="(1<<0)", value=0x1),
            "MEMF_CHIP": _test_constant(raw="(1<<1)", value=0x2),
            "MEMF_FAST": _test_constant(raw="(1<<2)", value=0x4),
        },
        LIBRARIES={
            "exec.library": _test_library(
                {
                    "AllocMem": runtime_os.OsFunction(
                        lvo=-198,
                        inputs=(
                            runtime_os.OsInput(name="byteSize", regs=("d0",)),
                            runtime_os.OsInput(name="attributes", regs=("d1",)),
                        ),
                    )
                },
            )
        },
    )

    arg_constants, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x16,
            block=0x10,
            library="exec.library",
            function="AllocMem",
            lvo=-198,
            dispatch=None,
        )],
        hunk_entities=[],
        os_kb=os_kb,
    )

    assert arg_constants == {"MEMF_PUBLIC", "MEMF_CHIP"}
    assert arg_substitutions == {0x10: ("#3", "#MEMF_PUBLIC|MEMF_CHIP")}

def test_build_arg_substitutions_collects_availmem_flag_constants() -> None:
    setter = _instruction(
        offset=0x10,
        raw=b"\x22\x3c\x00\x02\x00\x01",
        mnemonic="move",
        operand_size="l",
        operand_texts=("#$20001", "d1"),
    )
    call_inst = _instruction(
        offset=0x16,
        raw=b"\x4e\x75",
        mnemonic="jsr",
        operand_size="w",
        operand_texts=("_LVOAvailMem(a6)",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},

        ),
        API_INPUT_VALUE_DOMAINS={"exec.library": {"AvailMem": {"attributes": "test.alloc.attributes"}}},
        VALUE_DOMAINS={
            "test.alloc.attributes": runtime_os.OsValueDomain(
                kind="flags",
                members=("MEMF_PUBLIC", "MEMF_LARGEST"),
                zero_name=None,
                exact_match_policy="error",
                composition="bit_or",
                remainder_policy="error",
            )
        },
        CONSTANTS={
            "MEMF_PUBLIC": _test_constant(raw="(1<<0)", value=0x1),
            "MEMF_LARGEST": _test_constant(raw="(1<<17)", value=0x20000),
        },
        LIBRARIES={
            "exec.library": _test_library(
                {
                    "AvailMem": runtime_os.OsFunction(
                        lvo=-216,
                        inputs=(runtime_os.OsInput(name="attributes", regs=("d1",)),),
                    )
                },
            )
        },
    )

    arg_constants, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x16,
            block=0x10,
            library="exec.library",
            function="AvailMem",
            lvo=-216,
            dispatch=None,
        )],
        hunk_entities=[],
        os_kb=os_kb,
    )

    assert arg_constants == {"MEMF_PUBLIC", "MEMF_LARGEST"}
    assert arg_substitutions == {0x10: ("#$20001", "#MEMF_PUBLIC|MEMF_LARGEST")}

def test_build_arg_substitutions_requires_declared_constant() -> None:
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},

        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"OpenLibrary": {"name": "test.openlibrary.name"}}},
        VALUE_DOMAINS={"test.openlibrary.name": runtime_os.OsValueDomain(kind="enum", members=("OL_TAG",), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={},
        LIBRARIES={},
    )

    with pytest.raises(KeyError, match="Missing constant OL_TAG"):
        build_arg_substitutions(
            blocks={},
            hunk_entities=[],
            lib_calls=[],
            os_kb=os_kb,
        )

def test_build_arg_substitutions_requires_concrete_constant_value() -> None:
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},

        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"OpenLibrary": {"name": "test.openlibrary.name"}}},
        VALUE_DOMAINS={"test.openlibrary.name": runtime_os.OsValueDomain(kind="enum", members=("OL_TAG",), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={"OL_TAG": _test_constant(raw="TAG_USER+1", value=None)},
        LIBRARIES={},
    )

    with pytest.raises(ValueError, match="Non-concrete constant OL_TAG"):
        build_arg_substitutions(
            blocks={},
            hunk_entities=[],
            lib_calls=[],
            os_kb=os_kb,
        )

def test_build_arg_substitutions_rejects_ambiguous_matched_function_domain_value() -> None:
    setter = Instruction(
        offset=0x10,
        size=2,
        opcode=0x76FF,
        text="corrupted",
        raw=b"\x76\xff",
        kb_mnemonic="moveq",
        operand_size="l",
        operand_texts=("#-1", "d3"),
    )
    block = type("Block", (), {
        "instructions": [
            setter,
            Instruction(
                offset=0x20,
                size=2,
                opcode=0x4E75,
                text="jsr     _LVOSeek(a6)",
                raw=b"\x4E\x75",
                kb_mnemonic="jsr",
                operand_size="w",
                operand_texts=("_LVOSeek(a6)",),
            ),
        ]
    })()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},

        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"Seek": {"mode": "test.seek.mode"}}},
        VALUE_DOMAINS={"test.seek.mode": runtime_os.OsValueDomain(kind="enum", members=("OFFSET_BEGINNING", "OFFSET_ALIAS"), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={
            "OFFSET_BEGINNING": _test_constant(raw="-1", value=-1),
            "OFFSET_ALIAS": _test_constant(raw="-1", value=-1),
        },
        LIBRARIES={
            "dos.library": _test_library(
                {
                    "Seek": runtime_os.OsFunction(
                        lvo=-66,
                        inputs=(runtime_os.OsInput(name="mode", regs=("d3",)),),
                    )
                },
            )
        },
    )

    with pytest.raises(ValueError, match="Input domain resolution failed for Seek.mode"):
        build_arg_substitutions(
            blocks={0x20: block},
            hunk_entities=[],
            lib_calls=[LibraryCall(
                addr=0x20,
                block=0x20,
                library="dos.library",
                function="Seek",
                lvo=-66,
            )],
            os_kb=os_kb,
        )

def test_build_lvo_substitutions_collects_dispatch_call_lvo_constant() -> None:
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
        lib_calls=[LibraryCall(
            addr=0x10,
            block=0x10,
            library="dos.library",
            function="Seek",
            lvo=-66,
            dispatch=0x42,
        )],
        hunk_entities=[{"addr": "0040", "end": "0050", "type": "code"}],
    )

    assert lvo_equs == {"dos.library": {-66: "_LVOSeek"}}
    assert lvo_substitutions == {0x12: ("#-66", "#_LVOSeek")}

def test_build_app_slot_symbols_prefers_initial_mem_and_typed_slots() -> None:
    class FakeInitMem:
        _tags = {
            (0x1020, 4): LibraryBaseTag(library_base="dos.library"),
        }

        def iter_tags(self) -> tuple[tuple[tuple[int, int], object], ...]:
            return tuple(self._tags.items())

    app_offsets = build_app_slot_symbols(
        blocks={},
        lib_calls=[],
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0x1000), initial_mem=FakeInitMem()),
    )

    assert app_offsets == {0x20: "app_dos_base"}

def test_build_app_slot_symbols_ignores_non_app_relative_library_tags_for_dynamic_base() -> None:
    class FakeInitMem:
        _tags = {
            (0x02C00CD8, 4): LibraryBaseTag(library_base="dos.library"),
            (0x03700CD8, 4): LibraryBaseTag(library_base="dos.library"),
            (0x04200CD8, 4): LibraryBaseTag(library_base="dos.library"),
            (0x80300CD8, 4): LibraryBaseTag(library_base="dos.library"),
        }

        def iter_tags(self) -> tuple[tuple[tuple[int, int], object], ...]:
            return tuple(self._tags.items())

    app_offsets = build_app_slot_symbols(
        blocks={},
        lib_calls=[],
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0x80300002), initial_mem=FakeInitMem()),
    )

    assert app_offsets == {0x0CD6: "app_dos_base"}

def test_build_app_slot_symbols_accepts_only_signed_word_slots_for_absolute_base() -> None:
    class FakeInitMem:
        _tags = {
            (0x00007FFC, 4): LibraryBaseTag(library_base="dos.library"),
            (0x00010000, 4): LibraryBaseTag(library_base="dos.library"),
        }

        def iter_tags(self) -> tuple[tuple[tuple[int, int], object], ...]:
            return tuple(self._tags.items())

    app_offsets = build_app_slot_symbols(
        blocks={},
        lib_calls=[],
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=AppBaseInfo(
            kind=AppBaseKind.ABSOLUTE,
            reg_num=6,
            concrete=0x00008000,
        ), initial_mem=FakeInitMem()),
    )

    assert app_offsets == {-4: "app_dos_base"}

def test_build_app_slot_symbols_disambiguates_duplicate_typed_slot_names() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="timer.device",
            function="GetSysTime",
            lvo=-66,
            inputs=(runtime_os.OsInput(name="dest", regs=("A0",), type="struct timeval *", i_struct="TIMEVAL"),),
        ),
        LibraryCall(
            addr=12,
            block=8,
            library="timer.device",
            function="GetSysTime",
            lvo=-66,
            inputs=(runtime_os.OsInput(name="dest", regs=("A0",), type="struct timeval *", i_struct="TIMEVAL"),),
        ),
        LibraryCall(
            addr=22,
            block=16,
            library="timer.device",
            function="SubTime",
            lvo=-48,
            inputs=(
                runtime_os.OsInput(name="dest", regs=("A0",), type="struct timeval *", i_struct="TIMEVAL"),
                runtime_os.OsInput(name="src", regs=("A1",), type="struct timeval *", i_struct="TIMEVAL"),
            ),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41EE, text="lea 4264(a6),a0", raw=b"\x41\xEE\x10\xA8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
        8: type("Block", (), {"instructions": [
            Instruction(offset=8, size=4, opcode=0x41EE, text="lea 4272(a6),a0", raw=b"\x41\xEE\x10\xB0",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=12, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
        16: type("Block", (), {"instructions": [
            Instruction(offset=16, size=4, opcode=0x41EE, text="lea 4272(a6),a0", raw=b"\x41\xEE\x10\xB0",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=20, size=4, opcode=0x43EE, text="lea 4264(a6),a1", raw=b"\x43\xEE\x10\xA8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=22, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0)),
    )

    assert app_offsets == {
        0x10A8: "app_subtime_src",
        0x10B0: "app_subtime_dest",
    }

def test_build_app_slot_symbols_prefers_backward_usage_name_for_single_slot() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="dos.library",
            function="Output",
            lvo=-60,
            output=runtime_os.OsOutput(name="file", reg="D0", type="BPTR"),
        ),
        LibraryCall(
            addr=12,
            block=8,
            library="dos.library",
            function="Write",
            lvo=-48,
            inputs=(runtime_os.OsInput(name="file", regs=("D1",), type="BPTR"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
            Instruction(offset=6, size=4, opcode=0x2D40, text="move.l d0,4264(a6)", raw=b"\x2D\x40\x10\xA8",
                        kb_mnemonic="MOVE", operand_size="l"),
        ]})(),
        8: type("Block", (), {"instructions": [
            Instruction(offset=8, size=4, opcode=0x222E, text="move.l 4264(a6),d1", raw=b"\x22\x2E\x10\xA8",
                        kb_mnemonic="MOVE", operand_size="l"),
            Instruction(offset=12, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }
    blocks[0].xrefs = []
    blocks[8].xrefs = []

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0)),
    )

    assert app_offsets == {
        0x10A8: "app_write_file",
    }

def test_build_app_slot_symbols_preserves_first_equal_priority_usage() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="exec.library",
            function="OpenDevice",
            lvo=-444,
            inputs=(runtime_os.OsInput(name="ioRequest", regs=("A1",), type="struct IORequest *", i_struct="IO"),),
        ),
        LibraryCall(
            addr=12,
            block=8,
            library="exec.library",
            function="CloseDevice",
            lvo=-450,
            inputs=(runtime_os.OsInput(name="ioRequest", regs=("A1",), type="struct IORequest *", i_struct="IO"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x43EE, text="lea 4280(a6),a1", raw=b"\x43\xEE\x10\xB8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
        8: type("Block", (), {"instructions": [
            Instruction(offset=8, size=4, opcode=0x43EE, text="lea 4280(a6),a1", raw=b"\x43\xEE\x10\xB8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=12, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0)),
    )

    assert app_offsets == {
        0x10B8: "app_opendevice_iorequest",
    }

def test_build_app_slot_symbols_prefers_named_base_identity_for_struct_slot() -> None:
    code = (
        b"\x41\xFA\x00\x08"
        + b"\x43\xEE\x10\xB8"
        + b"\x4E\x75"
        + b"timer.device\x00"
    )
    lib_calls = [
        LibraryCall(
            addr=8,
            block=0,
            library="exec.library",
            function="OpenDevice",
            lvo=-444,
            inputs=(
                runtime_os.OsInput(name="devName", regs=("A0",), type="STRPTR"),
                runtime_os.OsInput(name="ioRequest", regs=("A1",), type="struct IORequest *", i_struct="IO"),
            ),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41FA, text="lea 8(pc),a0", raw=b"\x41\xFA\x00\x08",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=4, opcode=0x43EE, text="lea 4280(a6),a1", raw=b"\x43\xEE\x10\xB8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=8, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=code,
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0)),
    )

    assert app_offsets == {
        0x10B8: "app_timer_device_iorequest",
    }

def test_build_app_slot_symbols_for_absolute_app_base_disambiguates_by_absolute_address() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="exec.library",
            function="OpenLibrary",
            lvo=-552,
            output=runtime_os.OsOutput(name="library", reg="D0", type="struct Library *", i_struct="LIBRARY"),
        ),
        LibraryCall(
            addr=12,
            block=8,
            library="exec.library",
            function="OpenLibrary",
            lvo=-552,
            output=runtime_os.OsOutput(name="library", reg="D0", type="struct Library *", i_struct="LIBRARY"),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
            Instruction(offset=6, size=4, opcode=0x2D40, text="move.l d0,-32768(a6)", raw=b"\x2D\x40\x80\x00",
                        kb_mnemonic="MOVE", operand_size="l"),
        ]})(),
        8: type("Block", (), {"instructions": [
            Instruction(offset=12, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
            Instruction(offset=14, size=4, opcode=0x2D40, text="move.l d0,-32764(a6)", raw=b"\x2D\x40\x80\x04",
                        kb_mnemonic="MOVE", operand_size="l"),
        ]})(),
    }
    blocks[0].xrefs = []
    blocks[8].xrefs = []

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=AppBaseInfo(
            kind=AppBaseKind.ABSOLUTE,
            reg_num=6,
            concrete=0x8000,
        )),
    )

    assert app_offsets == {
        -32768: "app_openlibrary_library_0000",
        -32764: "app_openlibrary_library_0004",
    }

def test_analyze_call_setups_names_pc_relative_struct_argument_targets() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="intuition.library",
            function="OpenScreen",
            lvo=-198,
            inputs=(runtime_os.OsInput(name="newScreen", regs=("A0",),
                                       type="struct NewScreen *", i_struct="NewScreen"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41FA, text="lea 8(pc),a0", raw=b"\x41\xFA\x00\x08",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    result = analyze_call_setups(
        blocks=blocks,
        lib_calls=lib_calls,
        os_kb=runtime_os,
        code=b"\x00" * 16,
        platform=make_platform(),
    )

    assert result.arg_annotations == {
        0: CallArgumentAnnotation("newScreen", "A0", "OpenScreen", "intuition.library")
    }
    assert result.segment_data_symbols == {0x000A: "openscreen_newscreen"}
    assert result.segment_struct_regions == {0x000A: "NewScreen"}
    assert result.segment_code_symbols == {}
    assert result.code_entry_points == ()
    assert result.string_ranges == {}
    assert result.typed_data_fields[0x000A] == ("NewScreen", "ns_LeftEdge", None)
    assert result.typed_data_sizes[0x000A] == 2
    assert result.typed_data_sizes[0x000C] == 2
    assert result.typed_data_sizes[0x001A] == 4
    assert result.typed_data_comments[0x000A] == "NewScreen.ns_LeftEdge"
    assert result.typed_data_comments[0x000C] == "NewScreen.ns_TopEdge"
    assert result.typed_data_comments[0x001A] == "NewScreen.ns_Font"

def test_refresh_library_call_signatures_uses_current_os_kb_inputs() -> None:
    call = LibraryCall(
        addr=0x12,
        block=0x10,
        library="intuition.library",
        function="SetPointer",
        lvo=-270,
        inputs=(runtime_os.OsInput(name="pointer", regs=("A1",), type="UWORD *", i_struct=None),),
    )
    updated_input = runtime_os.OsInput(
        name="pointer",
        regs=("A1",),
        type="struct SimpleSprite *",
        i_struct="SimpleSprite",
    )
    updated_function = replace(
        runtime_os.LIBRARIES["intuition.library"].functions["SetPointer"],
        inputs=(updated_input,),
    )
    updated_library = replace(
        runtime_os.LIBRARIES["intuition.library"],
        functions={
            **runtime_os.LIBRARIES["intuition.library"].functions,
            "SetPointer": updated_function,
        },
    )
    updated_os_kb = make_empty_os_kb()
    updated_os_kb = SimpleNamespace(
        META=updated_os_kb.META,
        VALUE_DOMAINS=updated_os_kb.VALUE_DOMAINS,
        API_INPUT_VALUE_DOMAINS=updated_os_kb.API_INPUT_VALUE_DOMAINS,
        STRUCT_FIELD_VALUE_DOMAINS=updated_os_kb.STRUCT_FIELD_VALUE_DOMAINS,
        STRUCTS=updated_os_kb.STRUCTS,
        CONSTANTS=updated_os_kb.CONSTANTS,
        LIBRARIES={
            **runtime_os.LIBRARIES,
            "intuition.library": updated_library,
        },
    )

    refreshed = _refresh_library_call_signatures([call], updated_os_kb)

    assert refreshed[0].inputs[0].type == "struct SimpleSprite *"
    assert refreshed[0].inputs[0].i_struct == "SimpleSprite"

def test_analyze_call_setups_extnewscreen_includes_inherited_fields() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="intuition.library",
            function="OpenScreen",
            lvo=-198,
            inputs=(runtime_os.OsInput(name="newScreen", regs=("A0",),
                                       type="struct ExtNewScreen *", i_struct="ExtNewScreen"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41FA, text="lea 8(pc),a0", raw=b"\x41\xFA\x00\x08",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    result = analyze_call_setups(
        blocks=blocks,
        lib_calls=lib_calls,
        os_kb=runtime_os,
        code=b"\x00" * 64,
        platform=make_platform(),
    )

    assert result.segment_struct_regions == {0x000A: "ExtNewScreen"}
    assert result.typed_data_sizes[0x000A] == 2
    assert result.typed_data_comments[0x000A] == "NewScreen.ns_LeftEdge"
    assert result.typed_data_comments[0x002A] == "ExtNewScreen.ens_Extension"

def test_analyze_call_setups_errors_on_conflicting_typed_names_for_same_segment_address() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="intuition.library",
            function="OpenScreen",
            lvo=-198,
            inputs=(runtime_os.OsInput(name="newScreen", regs=("A0",),
                                       type="struct NewScreen *", i_struct="NewScreen"),),
        ),
        LibraryCall(
            addr=10,
            block=0,
            library="intuition.library",
            function="OpenWindow",
            lvo=-204,
            inputs=(runtime_os.OsInput(name="newWindow", regs=("A0",),
                                       type="struct NewWindow *", i_struct="NewWindow"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41FA, text="lea 8(pc),a0", raw=b"\x41\xFA\x00\x08",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
            Instruction(offset=6, size=4, opcode=0x41FA, text="lea 2(pc),a0", raw=b"\x41\xFA\x00\x02",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=10, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    with pytest.raises(ValueError, match="Conflicting typed segment names"):
        analyze_call_setups(
            blocks=blocks,
            lib_calls=lib_calls,
            os_kb=runtime_os,
            code=b"\x00" * 16,
            platform=make_platform(),
        )
