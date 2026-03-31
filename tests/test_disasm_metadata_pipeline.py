from __future__ import annotations

"""Disassembly metadata and session state tests."""

from tests.disasm_pipeline_support import (
    CallArgumentAnnotation,
    CustomStructFieldMetadata,
    CustomStructMetadata,
    DisasmBlockLike,
    DisassemblySession,
    Hunk,
    HunkDisassemblySession,
    HunkType,
    JumpTable,
    JumpTableEntry,
    JumpTableEntryRef,
    JumpTablePattern,
    JumpTableRegion,
    LibraryCall,
    MemoryRegionAddressSpace,
    MemoryRegionProvenance,
    MemType,
    MonkeyPatch,
    Path,
    Reloc,
    RelocatedSegment,
    RelocLike,
    SimpleNamespace,
    TypedDataFieldInfo,
    TypedMemoryRegion,
    _block,
    _FakeBlock,
    _FakeReloc,
    _prepare_hunk_code,
    _prepare_hunk_sizes,
    analysis_cache_root,
    assemble_instruction,
    build_hunk_metadata,
    build_target_local_os_kb,
    cast,
    disassemble,
    emitter_mod,
    hunk_analysis_cache_path,
    load_hunk_analysis,
    make_empty_os_kb,
    make_platform,
    provenance_named_base,
    pytest,
    replace,
    runtime_os,
    session_mod,
)


def test_build_hunk_metadata_masks_hints_inside_typed_string_ranges() -> None:
    core_block = type("Block", (), {"start": 0x00, "end": 0x04, "successors": [], "instructions": []})()
    hint_block = type("Block", (), {"start": 0x20, "end": 0x24, "successors": [], "instructions": []})()
    ha = type("HA", (), {
        "blocks": {0x00: core_block},
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
        typed_string_ranges={0x20: 0x24},
    )

    assert metadata.hint_addrs == set()
    assert metadata.string_addrs == {0x20}
    assert metadata.string_ranges == {0x20: 0x24}
    assert 0x20 not in metadata.labels

def test_prepare_hunk_code_relocates_payload_segment() -> None:
    code, code_size, relocated_segments, reloc_file_offset, reloc_base_addr = _prepare_hunk_code(
        b"\xAA\xBB\x11\x22",
        [RelocatedSegment(file_offset=2, base_addr=6)],
    )

    assert code == b"\xAA\xBB\x00\x00\x00\x00\x11\x22"
    assert code_size == 8
    assert relocated_segments == [RelocatedSegment(file_offset=2, base_addr=6)]
    assert reloc_file_offset == 2
    assert reloc_base_addr == 6

def test_prepare_hunk_sizes_rebases_relocated_runtime_window() -> None:
    stored_size, alloc_size = _prepare_hunk_sizes(
        stored_size=9968,
        alloc_size=9968,
        reloc_file_offset=490,
        reloc_base_addr=0,
    )

    assert stored_size == 9478
    assert alloc_size == 9478

def test_disassembly_session_uses_binary_analysis_suffix(tmp_path: Path) -> None:
    binary_path = tmp_path / "demo.bin"
    entities_path = tmp_path / "entities.jsonl"
    output_path = tmp_path / "demo.s"

    session = DisassemblySession(
        target_name="demo",
        binary_path=binary_path,
        analysis_cache_path=binary_path.with_suffix(".analysis"),
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

def test_hunk_disassembly_session_preserves_metadata_and_analysis_fields() -> None:
    block = _block()
    hint_block = _block(2, 3)
    session = HunkDisassemblySession(
        hunk_index=1,
        code=b"\x00\x01",
        code_size=2,
        entities=[{"addr": "0000", "type": "code"}],
        blocks={0: block},
        hint_blocks={2: hint_block},
        code_addrs={0, 1},
        hint_addrs={2},
        reloc_map={0: 0x40},
        reloc_target_set={0x40},
        pc_targets={0x20: "pcref_0020"},
        string_addrs={0x20},
        labels={0x40: "loc_0040"},
        jump_table_regions={0x10: JumpTableRegion(pattern="word_table", table_end=0)},
        jump_table_target_sources={0x80: ("loc_0040",)},
        region_map={0x00: {"a0": TypedMemoryRegion(
            struct="Foo",
            size=4,
                provenance=MemoryRegionProvenance(
                    address_space=MemoryRegionAddressSpace.ABSOLUTE,
                    absolute_addr=0,
                ),
        )}},
        lvo_equs={"dos.library": {-552: "_LVOOpenLibrary"}},
        lvo_substitutions={0x10: ("-552(", "_LVOOpenLibrary(")},
        arg_constants={"OL_TAG"},
        arg_substitutions={0x12: ("#1", "#OL_TAG")},
        app_offsets={0x20: "app_dos_base"},
        arg_annotations={0x30: CallArgumentAnnotation("name", "D0", "OpenLibrary", "dos.library")},
        data_access_sizes={0x40: 2},
        typed_data_sizes={},
        typed_data_fields={},
        platform=make_platform(app_base=(6, 0x1000)),
        os_kb=make_empty_os_kb(),
        base_addr=0x400,
        code_start=2,
        relocated_segments=[RelocatedSegment(file_offset=0, base_addr=0)],
        reloc_file_offset=0,
        reloc_base_addr=0,
        string_ranges={},
        dynamic_structured_regions=(),
        absolute_labels={},
        reserved_absolute_addrs=set(),
        app_struct_regions={},
        hardware_base_regs={},
        unresolved_indirects={},
    )

    assert session.hunk_index == 1
    assert session.code == b"\x00\x01"
    assert session.jump_table_target_sources == {0x80: ("loc_0040",)}
    assert session.lvo_substitutions == {0x10: ("-552(", "_LVOOpenLibrary(")}
    assert session.app_offsets == {0x20: "app_dos_base"}

def test_build_hunk_metadata_collects_code_and_hint_addresses() -> None:
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
        reserved_absolute_addrs=set(),
    )

    assert metadata.code_addrs == {0x10, 0x11, 0x12, 0x13}
    assert metadata.hint_addrs == {0x20, 0x21}

def test_build_hunk_metadata_builds_word_table_regions_and_sources() -> None:
    block = type("Block", (), {"start": 0x10, "end": 0x14, "successors": [], "instructions": []})()
    ha = type("Analysis", (), {
        "blocks": {0x10: block},
        "hint_blocks": {},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [JumpTable(
            addr=0x30,
            pattern=JumpTablePattern.WORD_OFFSET,
            targets=(0x80, 0x90),
            dispatch_sites=(0x10,),
            dispatch_block=0x10,
            base_addr=0x50,
            table_end=0x34,
        )],
    })()

    metadata = build_hunk_metadata(
        code=b"\x00" * 0x100,
        code_size=0x100,
        hunk_index=0,
        hunk_entities=[],
        ha=ha,
        hf_hunks=[],
        reserved_absolute_addrs=set(),
    )

    assert metadata.jump_table_regions[0x30].entries == (
        JumpTableEntryRef(0x30, 0x80), JumpTableEntryRef(0x32, 0x90))
    assert metadata.jump_table_regions[0x30].base_label == "loc_0050"
    assert metadata.jump_table_target_sources == {
        0x80: ("loc_0050",),
        0x90: ("loc_0050",),
    }

def test_build_hunk_metadata_preserves_string_dispatch_entry_offsets() -> None:
    block = type("Block", (), {"start": 0x10, "end": 0x14, "successors": [], "instructions": []})()
    ha = type("Analysis", (), {
        "blocks": {0x10: block},
        "hint_blocks": {},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [JumpTable(
            addr=0x30,
            pattern=JumpTablePattern.STRING_DISPATCH_SELF_RELATIVE,
            entries=(
                JumpTableEntry(offset_addr=0x32, target=0x80),
                JumpTableEntry(offset_addr=0x37, target=0x90),
            ),
            targets=(0x80, 0x90),
            dispatch_sites=(0x10,),
            dispatch_block=0x10,
            table_end=0x39,
        )],
    })()

    metadata = build_hunk_metadata(
        code=b"\x00" * 0x100,
        code_size=0x100,
        hunk_index=0,
        hunk_entities=[],
        ha=ha,
        hf_hunks=[],
        reserved_absolute_addrs=set(),
    )

    assert metadata.jump_table_regions[0x30].entries == (
        JumpTableEntryRef(0x32, 0x80), JumpTableEntryRef(0x37, 0x90))

def test_build_hunk_metadata_rejects_out_of_segment_jump_table_targets() -> None:
    block = type("Block", (), {"start": 0x10, "end": 0x14, "successors": [], "instructions": []})()
    ha = type("Analysis", (), {
        "blocks": {0x10: block},
        "hint_blocks": {},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [JumpTable(
            addr=0x30,
            pattern=JumpTablePattern.WORD_OFFSET,
            targets=(0x80, 0x40000),
            dispatch_sites=(0x10,),
            dispatch_block=0x10,
            base_addr=0x50,
            table_end=0x34,
        )],
    })()

    with pytest.raises(ValueError, match="out-of-segment targets"):
        build_hunk_metadata(
            code=b"\x00" * 0x100,
            code_size=0x100,
            hunk_index=0,
            hunk_entities=[],
            ha=ha,
            hf_hunks=[],
            reserved_absolute_addrs=set(),
        )

def test_load_hunk_analysis_uses_cache_when_present(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    cache_path = hunk_analysis_cache_path(
        analysis_cache_root(
            tmp_path / "demo.analysis",
            seed_key="default",
            base_addr=0,
            code_start=0,
            entry_points=(),
        ),
        0,
    )
    cache_path.write_text("cache", encoding="utf-8")
    sentinel = object()
    seen: dict[str, object] = {}

    def fake_load(path: Path, os_kb: object) -> object:
        seen["path"] = path
        seen["os_kb"] = os_kb
        return sentinel

    monkeypatch.setattr("disasm.analysis_loader.HunkAnalysis.load", fake_load)
    fake_os_kb = make_empty_os_kb()
    monkeypatch.setattr("disasm.analysis_loader.m68k_analysis.RUNTIME_OS_KB", fake_os_kb)

    result = load_hunk_analysis(
        analysis_cache_path=tmp_path / "demo.analysis",
        code=b"\x00\x00",
        relocs=[],
        hunk_index=0,
        base_addr=0,
        code_start=0,
    )

    assert result is sentinel
    assert seen == {"path": cache_path, "os_kb": fake_os_kb}

def test_load_hunk_analysis_runs_analysis_without_cache(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    class FakeAnalysis:
        def save(self, path: Path) -> None:
            seen["saved_path"] = path

    sentinel = FakeAnalysis()
    relocs: list[RelocLike] = [_FakeReloc(reloc_type=HunkType.HUNK_RELOC32, offsets=(1,))]

    def fake_analyze_hunk(
        code: bytes,
        relocs: object,
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...] = (),
        extra_entry_points: tuple[int, ...] = (),
        entry_initial_states: object | None = None,
    ) -> FakeAnalysis:
        seen["args"] = (code, relocs, hunk_index, base_addr, code_start, entry_points)
        seen["extra_entry_points"] = extra_entry_points
        return sentinel

    monkeypatch.setattr("disasm.analysis_loader.analyze_hunk", fake_analyze_hunk)

    result = load_hunk_analysis(
        analysis_cache_path=tmp_path / "demo.analysis",
        code=b"\x01\x02",
        relocs=relocs,
        hunk_index=3,
        base_addr=0x400,
        code_start=2,
    )

    assert cast(object, result) is sentinel
    assert seen["args"] == (b"\x01\x02", relocs, 3, 0x400, 2, ())
    assert seen["extra_entry_points"] == ()
    assert seen["saved_path"] == hunk_analysis_cache_path(
        analysis_cache_root(
            tmp_path / "demo.analysis",
            seed_key="default",
            base_addr=0x400,
            code_start=2,
            entry_points=(),
            extra_entry_points=(),
        ),
        3,
    )

def test_load_hunk_analysis_rebuilds_stale_cache(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    cache_path = hunk_analysis_cache_path(
        analysis_cache_root(
            tmp_path / "demo.analysis",
            seed_key="default",
            base_addr=0x400,
            code_start=2,
            entry_points=(),
        ),
        3,
    )
    cache_path.write_text("stale", encoding="utf-8")
    seen: dict[str, object] = {}

    class FakeAnalysis:
        def save(self, path: Path) -> None:
            seen["saved_path"] = path

    sentinel = FakeAnalysis()
    relocs: list[RelocLike] = [_FakeReloc(reloc_type=HunkType.HUNK_RELOC32, offsets=(1,))]

    def fake_load(path: Path, os_kb: object) -> object:
        seen["load"] = (path, os_kb)
        from m68k.analysis import AnalysisCacheError
        raise AnalysisCacheError("Cache version mismatch")

    def fake_analyze_hunk(
        code: bytes,
        relocs: object,
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...] = (),
        extra_entry_points: tuple[int, ...] = (),
        entry_initial_states: object | None = None,
    ) -> FakeAnalysis:
        seen["analyze"] = (code, relocs, hunk_index, base_addr, code_start, entry_points)
        seen["extra_entry_points"] = extra_entry_points
        return sentinel

    monkeypatch.setattr("disasm.analysis_loader.HunkAnalysis.load", fake_load)
    monkeypatch.setattr("disasm.analysis_loader.analyze_hunk", fake_analyze_hunk)
    fake_os_kb = make_empty_os_kb()
    monkeypatch.setattr("disasm.analysis_loader.m68k_analysis.RUNTIME_OS_KB", fake_os_kb)

    result = load_hunk_analysis(
        analysis_cache_path=tmp_path / "demo.analysis",
        code=b"\x01\x02",
        relocs=relocs,
        hunk_index=3,
        base_addr=0x400,
        code_start=2,
    )

    assert cast(object, result) is sentinel
    assert seen["load"] == (cache_path, fake_os_kb)
    assert seen["analyze"] == (b"\x01\x02", relocs, 3, 0x400, 2, ())
    assert seen["extra_entry_points"] == ()
    assert seen["saved_path"] == cache_path

def test_load_hunk_analysis_does_not_hide_non_cache_value_errors(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    cache_path = hunk_analysis_cache_path(
        analysis_cache_root(
            tmp_path / "demo.analysis",
            seed_key="default",
            base_addr=0,
            code_start=0,
            entry_points=(),
            extra_entry_points=(),
        ),
        0,
    )
    cache_path.write_text("broken", encoding="utf-8")

    def fake_load(path: Path, os_kb: object) -> object:
        raise ValueError("unexpected parse bug")

    monkeypatch.setattr("disasm.analysis_loader.HunkAnalysis.load", fake_load)
    monkeypatch.setattr("disasm.analysis_loader.m68k_analysis.RUNTIME_OS_KB", make_empty_os_kb())

    with pytest.raises(ValueError, match="unexpected parse bug"):
        load_hunk_analysis(
            analysis_cache_path=tmp_path / "demo.analysis",
            code=b"\x01\x02",
            relocs=[],
            hunk_index=0,
            base_addr=0,
            code_start=0,
        )

def test_load_hunk_analysis_uses_distinct_cache_files_per_hunk(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    cache_root = tmp_path / "demo.analysis"
    seen_paths: list[Path] = []

    class FakeAnalysis:
        def save(self, path: Path) -> None:
            seen_paths.append(path)

    monkeypatch.setattr("disasm.analysis_loader.analyze_hunk", lambda *args, **kwargs: FakeAnalysis())

    load_hunk_analysis(
        analysis_cache_path=cache_root,
        code=b"\x00",
        relocs=[],
        hunk_index=0,
        base_addr=0,
        code_start=0,
    )
    load_hunk_analysis(
        analysis_cache_path=cache_root,
        code=b"\x00",
        relocs=[],
        hunk_index=1,
        base_addr=0,
        code_start=0,
    )

    assert seen_paths == [
        hunk_analysis_cache_path(
            analysis_cache_root(
                cache_root,
                seed_key="default",
                base_addr=0,
                code_start=0,
                entry_points=(),
            ),
            0,
        ),
        hunk_analysis_cache_path(
            analysis_cache_root(
                cache_root,
                seed_key="default",
                base_addr=0,
                code_start=0,
                entry_points=(),
            ),
            1,
        ),
    ]

def test_build_hunk_metadata_excludes_cross_hunk_reloc_targets_from_local_labels() -> None:
    metadata = build_hunk_metadata(
        code=(0x03FE).to_bytes(4, "big"),
        code_size=4,
        hunk_index=0,
        hunk_entities=[],
        ha=SimpleNamespace(
            blocks={},
            hint_blocks={},
            jump_tables=[],
            call_targets=set(),
            branch_targets=set(),
        ),
        hf_hunks=[
            Hunk(
                index=0,
                hunk_type=int(HunkType.HUNK_CODE),
                mem_type=int(MemType.ANY),
                alloc_size=4,
                data=(0x03FE).to_bytes(4, "big"),
                relocs=[
                    Reloc(
                        reloc_type=HunkType.HUNK_RELOC32,
                        target_hunk=1,
                        offsets=(0,),
                    )
                ],
            )
        ],
    )

    assert metadata.reloc_target_hunks == {0: 1}
    assert metadata.reloc_target_set == set()
    assert 0x03FE not in metadata.labels

def test_session_cross_hunk_labels_are_synthesized_and_uniquified() -> None:
    source = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0x40,
        entities=[],
        blocks={0x0000: _block(0x0000, 0x0002)},
        code_addrs={0x0000, 0x0001},
        reloc_map={0x0014: 0x0000, 0x003E: 0x0018},
        reloc_target_hunks={0x0014: 1, 0x003E: 1},
        labels={0x0000: "loc_0000"},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    target = HunkDisassemblySession(
        hunk_index=1,
        code=b"",
        code_size=0x40,
        entities=[],
        blocks={0x0000: _block(0x0000, 0x0002), 0x0018: _block(0x0018, 0x001A)},
        code_addrs={0x0000, 0x0001, 0x0018, 0x0019},
        reloc_target_hunks={},
        labels={0x0000: "loc_0000"},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    session_mod._ensure_cross_hunk_target_labels([source, target])
    session_mod._apply_session_unique_labels([source, target])
    session_mod._apply_cross_hunk_reloc_labels([source, target])

    assert source.labels[0x0000] == "hunk_0_loc_0000"
    assert target.labels[0x0000] == "hunk_1_loc_0000"
    assert target.labels[0x0018] == "loc_0018"
    assert source.reloc_labels == {
        0x0014: "hunk_1_loc_0000",
        0x003E: "loc_0018",
    }

def test_refresh_session_memory_cells_propagates_named_base_across_hunks() -> None:
    store_inst = disassemble(assemble_instruction("move.l a6,$00000192"))[0]
    load_inst = disassemble(b"\x2c\x79\x00\x00\x01\x92")[0]
    call_inst = disassemble(b"\x4e\xae\xff\x3a")[0]

    exec_region = TypedMemoryRegion(
        struct="ExecBase",
        size=runtime_os.STRUCTS["ExecBase"].size,
        provenance=provenance_named_base("exec.library"),
    )
    source_blocks: dict[int, DisasmBlockLike] = {0: _block(0, len(store_inst.raw))}
    source = HunkDisassemblySession(
        hunk_index=0,
        code=store_inst.raw,
        code_size=len(store_inst.raw),
        entities=[],
        blocks=source_blocks,
        code_addrs=set(range(len(store_inst.raw))),
        reloc_target_hunks={},
        labels={0: "store_exec_base"},
        region_map={0: {"a6": exec_region}},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    source_blocks[0] = replace(cast(_FakeBlock, source_blocks[0]), instructions=[store_inst])

    target_block = _FakeBlock(
        start=0,
        end=len(load_inst.raw) + len(call_inst.raw),
        successors=(),
        instructions=[load_inst, replace(call_inst, offset=len(load_inst.raw))],
    )
    target = HunkDisassemblySession(
        hunk_index=1,
        code=load_inst.raw + call_inst.raw,
        code_size=len(load_inst.raw) + len(call_inst.raw),
        entities=[],
        blocks={0: target_block},
        code_addrs=set(range(len(load_inst.raw) + len(call_inst.raw))),
        reloc_map={2: 0x0192},
        reloc_target_set={0x0192},
        reloc_target_hunks={2: 0},
        labels={0: "target_entry", 0x0192: "sub_0192"},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        lib_calls=(LibraryCall(
            addr=len(load_inst.raw),
            block=0,
            library="unknown",
            function="LVO_-198",
            lvo=-198,
        ),),
    )

    session_mod._refresh_session_memory_cells([source, target])

    assert source.labels[0x0192] == "exec_library_base"
    derivation = target.region_map[len(load_inst.raw)]["a6"].provenance.derivation
    assert derivation is not None
    assert derivation.named_base == "exec.library"
    assert target.lib_calls[0].library == "exec.library"
    assert target.lib_calls[0].function == "AllocMem"

def test_refresh_session_memory_cells_propagates_typed_field_across_hunks() -> None:
    store_inst = disassemble(assemble_instruction("move.w 20(a2),$00000180"))[0]

    code = bytearray(0x182)
    code[0x180:0x182] = b"\x00\x22"
    target = HunkDisassemblySession(
        hunk_index=1,
        code=bytes(code),
        code_size=len(code),
        entities=[],
        blocks={},
        reloc_target_hunks={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    source_blocks: dict[int, DisasmBlockLike] = {0: _block(0, len(store_inst.raw))}
    source = HunkDisassemblySession(
        hunk_index=0,
        code=store_inst.raw,
        code_size=len(store_inst.raw),
        entities=[],
        blocks=source_blocks,
        code_addrs=set(range(len(store_inst.raw))),
        reloc_map={4: 0x0180},
        reloc_target_hunks={4: 1},
        labels={0: "store_version"},
        region_map={
            0: {
                    "a2": TypedMemoryRegion(
                        struct="LIB",
                        size=runtime_os.STRUCTS["LIB"].size,
                        provenance=provenance_named_base("icon.library"),
                        context_name="icon.library",
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
    source_blocks[0] = replace(cast(_FakeBlock, source_blocks[0]), instructions=[store_inst])

    session_mod._refresh_session_memory_cells([source, target])

    assert target.typed_data_sizes[0x0180] == 2
    assert target.typed_data_fields[0x0180] == TypedDataFieldInfo(
        owner_struct="LIB",
        field_symbol="LIB_VERSION",
        context_name="icon.library",
    )
    assert target.addr_comments[0x0180] == "LIB.LIB_VERSION"

def test_refresh_session_memory_cells_normalizes_session_os_kb() -> None:
    source = HunkDisassemblySession(
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
            named_base_struct_overrides={"icon.library": "InferredIconLibraryBase"},
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    target = HunkDisassemblySession(
        hunk_index=1,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        reloc_target_hunks={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    session_mod._refresh_session_memory_cells([source, target])

    assert source.os_kb is target.os_kb
    assert "InferredIconLibraryBase" in target.os_kb.STRUCTS
    assert target.os_kb.META.named_base_structs["icon.library"] == "InferredIconLibraryBase"

def test_cross_hunk_control_entrypoints_collects_inbound_jsr_targets() -> None:
    source = Hunk(
        index=0,
        hunk_type=int(HunkType.HUNK_CODE),
        mem_type=int(MemType.ANY),
        alloc_size=6,
        data=b"\x4e\xb9\x00\x00\x00\x08",
        relocs=[
            Reloc(
                reloc_type=HunkType.HUNK_RELOC32,
                target_hunk=1,
                offsets=(2,),
            )
        ],
    )
    target = Hunk(
        index=1,
        hunk_type=int(HunkType.HUNK_CODE),
        mem_type=int(MemType.ANY),
        alloc_size=16,
        data=b"\x4e\x75" + b"\x00" * 14,
    )

    assert session_mod._cross_hunk_control_entrypoints([source, target]) == {1: (0x0008,)}

def test_disambiguate_generated_label_avoids_app_offset_collision() -> None:
    assert (
        session_mod._disambiguate_generated_label(
            labels={},
            app_offsets={0x22: "exec_library_base"},
            os_kb=runtime_os,
            addr=0x018E,
            symbol="exec_library_base",
        )
        == "exec_library_base_ptr"
    )

def test_rename_reserved_generated_labels_avoids_target_local_field_collision() -> None:
    os_kb = build_target_local_os_kb(
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
        named_base_struct_overrides={"icon.library": "InferredIconLibraryBase"},
    )
    labels = {0x0192: "exec_library_base"}

    session_mod._rename_reserved_generated_labels(
        labels=labels,
        entities=[],
        os_kb=os_kb,
        app_offsets={},
    )

    assert labels[0x0192] == "exec_library_base_ptr"

def test_target_local_struct_equ_rows_emit_custom_field_offsets() -> None:
    os_kb = build_target_local_os_kb(
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
        named_base_struct_overrides={"icon.library": "InferredIconLibraryBase"},
    )
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        reloc_target_hunks={},
        region_map={
            0x100: {
                "a2": TypedMemoryRegion(
                    struct="InferredIconLibraryBase",
                    size=46,
                    provenance=provenance_named_base("icon.library"),
                )
            }
        },
        platform=make_platform(),
        os_kb=os_kb,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    equs = emitter_mod._target_local_struct_equ_defs(hunk_session)

    assert equs == {"exec_library_base": 34}
