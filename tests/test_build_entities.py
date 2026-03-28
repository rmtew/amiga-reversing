from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections.abc import MutableMapping
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import cast

import pytest
from _pytest.monkeypatch import MonkeyPatch

from disasm.binary_source import RawBinarySource
from disasm.target_metadata import (
    BootBlockTargetMetadata,
    EntryRegisterSeedMetadata,
    ResidentAutoinitMetadata,
    ResidentTargetMetadata,
    SeededCodeEntrypointMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    write_target_metadata,
)
from m68k.hunk_parser import Hunk, HunkType, MemType
from m68k.indirect_core import IndirectSite, IndirectSiteStatus
from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble
from m68k.m68k_executor import BasicBlock
from m68k.name_entities import name_subroutines
from m68k.os_calls import AppSlotInfo, LibraryCall
from m68k_kb import runtime_m68k_analysis, runtime_os
from tests.os_kb_helpers import make_empty_os_kb
from tests.platform_helpers import make_platform


def test_build_entities_help_loads_cleanly() -> None:
    script = Path(__file__).resolve().parent.parent / "scripts" / "build_entities.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Build entities.jsonl from hunk binary analysis" in result.stdout


def test_structured_prefix_entities_only_emit_when_requested() -> None:
    module = _load_build_entities_module()
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
            auto_init=False,
        ),
    )

    assert module._structured_prefix_entities(metadata, 0, include_structure=False) == []
    payloads = module._structured_prefix_entities(metadata, 0, include_structure=True)
    assert payloads == [{
        "addr": "0x0004",
        "end": "0x001E",
        "type": "data",
        "subtype": "struct_instance",
        "confidence": "tool-inferred",
        "hunk": 0,
        "struct": "RT",
    }]


def test_apply_seeded_entities_merges_name_and_inserts_data_range() -> None:
    module = _load_build_entities_module()

    entities = [
        {
            "addr": "0x0010",
            "end": "0x0020",
            "type": "code",
            "confidence": "tool-inferred",
            "hunk": 0,
        }
    ]
    seeded = (
        SeededEntityMetadata(
            addr=0x0010,
            end=0x0020,
            hunk=0,
            type="code",
            name="check_keyboard",
            seed_origin="primary_doc",
            review_status="seeded",
            citation="seeded:demo-code-range",
        ),
        SeededEntityMetadata(
            addr=0x0100,
            end=0x1100,
            hunk=0,
            type="data",
            subtype="level_data",
            name="map_data_keep",
            seed_origin="primary_doc",
            review_status="seeded",
            citation="seeded:demo-data-range",
        ),
    )

    merged = module._apply_seeded_entities(entities, seeded, hunk_idx=0)
    merged.sort(key=lambda ent: int(ent["addr"], 16))

    assert merged == [
        {
            "addr": "0x0010",
            "end": "0x0020",
            "type": "code",
            "confidence": "tool-inferred",
            "hunk": 0,
            "name": "check_keyboard",
        },
        {
            "addr": "0x0100",
            "end": "0x1100",
            "type": "data",
            "subtype": "level_data",
            "confidence": "seeded",
            "hunk": 0,
            "name": "map_data_keep",
        },
    ]


def test_apply_seeded_entities_allows_label_only_overlay_on_existing_entity() -> None:
    module = _load_build_entities_module()

    entities = [
        {
            "addr": "0x05D6",
            "end": "0x0630",
            "type": "code",
            "confidence": "tool-inferred",
            "hunk": 0,
        }
    ]
    seeded = (
        SeededEntityMetadata(
            addr=0x05D6,
            hunk=0,
            type="code",
            name="check_keyboard",
            seed_origin="primary_doc",
            review_status="seeded",
            citation="seeded:demo-code-range",
        ),
    )

    merged = module._apply_seeded_entities(entities, seeded, hunk_idx=0)

    assert merged == [
        {
            "addr": "0x05D6",
            "end": "0x0630",
            "type": "code",
            "confidence": "tool-inferred",
            "hunk": 0,
            "name": "check_keyboard",
        }
    ]


def test_apply_seeded_entities_rejects_overlapping_insert() -> None:
    module = _load_build_entities_module()

    entities = [
        {
            "addr": "0x0010",
            "end": "0x0020",
            "type": "code",
            "confidence": "verified",
            "hunk": 0,
        }
    ]
    seeded = (
        SeededEntityMetadata(
            addr=0x0018,
            end=0x0028,
            hunk=0,
            type="data",
            seed_origin="primary_doc",
            review_status="seeded",
            citation="seeded:demo-overlap",
        ),
    )

    with pytest.raises(ValueError, match="overlaps existing entity"):
        module._apply_seeded_entities(entities, seeded, hunk_idx=0)


def test_apply_seeded_entities_replaces_fully_contained_tool_inferred_entities() -> None:
    module = _load_build_entities_module()

    entities = [
        {
            "addr": "0x0100",
            "end": "0x0140",
            "type": "code",
            "confidence": "tool-inferred",
            "hunk": 0,
            "name": "sub_0100",
        },
        {
            "addr": "0x0180",
            "end": "0x01C0",
            "type": "code",
            "confidence": "tool-inferred",
            "hunk": 0,
            "name": "sub_0180",
        },
    ]
    seeded = (
        SeededEntityMetadata(
            addr=0x0000,
            end=0x0200,
            hunk=0,
            type="data",
            subtype="level_data",
            name="map_data_keep",
            seed_origin="primary_doc",
            review_status="seeded",
            citation="seeded:demo-data-range",
        ),
    )

    merged = module._apply_seeded_entities(entities, seeded, hunk_idx=0)

    assert merged == [
        {
            "addr": "0x0000",
            "end": "0x0200",
            "type": "data",
            "subtype": "level_data",
            "confidence": "seeded",
            "hunk": 0,
            "name": "map_data_keep",
        },
    ]


def test_apply_seeded_code_entrypoints_name_matching_code_entities() -> None:
    module = _load_build_entities_module()

    entities = [
        {
            "addr": "0x05D6",
            "end": "0x0630",
            "type": "code",
            "confidence": "tool-inferred",
            "hunk": 0,
        }
    ]
    seeded = (
        SeededCodeEntrypointMetadata(
            addr=0x05D6,
            hunk=0,
            name="check_keyboard",
            comment="entry seed",
            seed_origin="primary_doc",
            review_status="seeded",
            citation="seeded:demo-entry",
        ),
    )

    merged = module._apply_seeded_code_entrypoints(entities, seeded, hunk_idx=0)

    assert merged == [
        {
            "addr": "0x05D6",
            "end": "0x0630",
            "type": "code",
            "confidence": "tool-inferred",
            "hunk": 0,
            "name": "check_keyboard",
            "comment": "entry seed",
        }
    ]


def _load_build_entities_module() -> ModuleType:
    path = Path(__file__).resolve().parent.parent / "scripts" / "build_entities.py"
    spec = importlib.util.spec_from_file_location("build_entities_script", path)
    if spec is None or spec.loader is None:
        raise ValueError("Unable to load build_entities.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_subroutine_app_slots_uses_containing_struct_region() -> None:
    module = _load_build_entities_module()
    inst = disassemble(assemble_instruction("movea.l 4300(a6),a0"), max_cpu="68010")[0]
    sub = module.SubroutineRange(addr=0x20, end=0x24, block_count=1, instr_count=1)
    blocks = {
        0x20: SimpleNamespace(start=0x20, instructions=[inst]),
    }
    slot_infos = (
        AppSlotInfo(
            offset=0x10B8,
            symbol="app_timer_device_iorequest",
            usages=(),
            struct="IO",
            size=48,
            named_base="timer.device",
        ),
    )

    app_slots = module.collect_subroutine_app_slots(sub, blocks, slot_infos, 6)

    assert app_slots == (
        module.ReferencedAppSlot(
            offset=0x10B8,
            symbol="app_timer_device_iorequest",
            struct="IO",
            size=48,
            pointer_struct=None,
            named_base="timer.device",
        ),
    )


def test_os_input_reg_key_joins_grouped_registers() -> None:
    module = _load_build_entities_module()

    assert module._os_input_reg_key(("D0",)) == "D0"
    assert module._os_input_reg_key(("D0", "D1")) == "D0/D1"


def test_grouped_os_call_inputs_are_emitted_in_entity_payload() -> None:
    module = _load_build_entities_module()
    payload = module._typed_call_inputs_payload((
        runtime_os.OsInput(
            name="parm",
            regs=("D0", "D1"),
            type="DOUBLE",
            i_struct=None,
            semantic_kind=None,
            semantic_note=None,
        ),
    ))

    assert payload == {
        "D0/D1": {"type": "DOUBLE"},
    }


def test_app_slot_entity_payloads_emit_struct_and_named_base() -> None:
    module = _load_build_entities_module()

    payloads = module.app_slot_entity_payloads((
        module.ReferencedAppSlot(
            offset=0x0CD6,
            symbol="app_dos_library_base",
            struct=None,
            size=None,
            pointer_struct="DosLibrary",
            named_base="dos.library",
        ),
    ))

    assert payloads == [{
        "offset": "0x0CD6",
        "symbol": "app_dos_library_base",
        "kind": "struct_pointer",
        "pointer_struct": "DosLibrary",
        "named_base": "dos.library",
    }]


def test_app_slot_entity_payloads_format_negative_offsets() -> None:
    module = _load_build_entities_module()

    payloads = module.app_slot_entity_payloads((
        module.ReferencedAppSlot(
            offset=-2,
            symbol="app_freemem_memoryblock",
            struct=None,
            size=None,
            pointer_struct=None,
            named_base=None,
        ),
    ))

    assert payloads == [{
        "offset": "-0x0002",
        "symbol": "app_freemem_memoryblock",
    }]


def test_summarize_entity_app_slots_adds_direct_and_transitive_summaries() -> None:
    module = _load_build_entities_module()
    entities = [
        {
            "addr": "0x0000",
            "end": "0x0010",
            "type": "code",
            "calls": ["0x0100"],
            "app_slots": [{
                "offset": "0x10B8",
                "symbol": "app_timer_device_iorequest",
                "struct": "IO",
                "named_base": "timer.device",
            }],
        },
        {
            "addr": "0x0100",
            "end": "0x0110",
            "type": "code",
            "app_slots": [{
                "offset": "0x0CD6",
                "symbol": "app_dos_library_base",
                "kind": "struct_pointer",
                "pointer_struct": "DosLibrary",
                "named_base": "dos.library",
            }],
        },
    ]

    module.summarize_entity_app_slots(entities)

    assert entities[0]["named_bases"] == ["timer.device"]
    assert entities[0]["struct_refs"] == ["IO"]
    assert entities[0]["named_bases_transitive"] == ["dos.library", "timer.device"]
    assert entities[0]["struct_refs_transitive"] == ["DosLibrary", "IO"]
    assert entities[1]["named_bases"] == ["dos.library"]
    assert entities[1]["struct_refs"] == ["DosLibrary"]


def test_collect_subroutine_indirect_sites_keeps_dispatch_metadata() -> None:
    module = _load_build_entities_module()
    sub = module.SubroutineRange(addr=0x20, end=0x40, block_count=1, instr_count=1)
    sites = [
        IndirectSite(
            addr=0x24,
            mnemonic="jsr",
            flow_type=runtime_m68k_analysis.FlowType.CALL,
            shape="index.brief",
            status=IndirectSiteStatus.PER_CALLER,
            target=None,
            detail="dispatch",
            target_count=2,
        ),
    ]

    indirect_sites = module.collect_subroutine_indirect_sites(sub, sites)

    assert indirect_sites == (
        module.ReferencedIndirectSite(
            addr=0x24,
            shape="index.brief",
            status="per_caller",
            flow="call",
            detail="dispatch",
            target_count=2,
        ),
    )


def test_name_subroutines_uses_transitive_named_base_for_dispatch_wrapper() -> None:
    entities: list[MutableMapping[str, object]] = [{
        "addr": "0x0010",
        "end": "0x0018",
        "type": "code",
        "named_bases_transitive": ["dos.library"],
        "indirect_sites": [{
            "addr": "0x0014",
            "shape": "index.brief",
            "status": "per_caller",
            "flow": "call",
        }],
    }]

    named = name_subroutines(entities, {}, b"", [])

    assert named == 1
    assert entities[0]["name"] == "dos_dispatch"


def test_name_subroutines_ignores_unknown_library_call_names() -> None:
    entities: list[MutableMapping[str, object]] = [{
        "addr": "0x0010",
        "end": "0x0018",
        "type": "code",
    }]

    named = name_subroutines(
        entities,
        {},
        b"",
        [LibraryCall(
            addr=0x0012,
            block=0x0010,
            library="unknown",
            function="LVO_48",
            lvo=-48,
        )],
    )

    assert named == 0
    assert "name" not in entities[0]


def test_name_subroutines_uses_explicit_library_call_owner_sub() -> None:
    entities: list[MutableMapping[str, object]] = [{
        "addr": "0x0010",
        "end": "0x0018",
        "type": "code",
    }, {
        "addr": "0x0030",
        "end": "0x0038",
        "type": "code",
    }]

    named = name_subroutines(
        entities,
        {},
        b"",
        [LibraryCall(
            addr=0x0032,
            block=0x0030,
            owner_sub=0x0010,
            library="dos.library",
            function="Open",
            lvo=-30,
        )],
    )

    assert named == 1
    assert entities[0]["name"] == "call_open"
    assert "name" not in entities[1]


def test_name_subroutines_errors_when_library_call_owner_sub_missing() -> None:
    entities: list[MutableMapping[str, object]] = [{
        "addr": "0x0010",
        "end": "0x0018",
        "type": "code",
    }]

    with pytest.raises(ValueError, match="missing owner_sub"):
        name_subroutines(
            entities,
            {},
            b"",
            [LibraryCall(
                addr=0x0012,
                block=0x0010,
                library="dos.library",
                function="Open",
                lvo=-30,
            )],
        )


def test_build_entities_from_raw_binary_rebases_addresses_to_local_offsets(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    target_dir = tmp_path / "targets" / "bootblock"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x00" * 0x0C + b"\x4E\x75")
    output_path = target_dir / "entities.jsonl"
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="bootblock",
            entry_register_seeds=(),
            bootblock=BootBlockTargetMetadata(
                magic_ascii="DOS",
                flags_byte=0,
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=880,
                bootcode_offset=0x0C,
                bootcode_size=2,
                load_address=0x70000,
                entrypoint=0x7000C,
            ),
        ),
    )
    inst = disassemble(b"\x4E\x75")[0]
    inst.offset = 0x000C
    block = BasicBlock(
        start=0x0000,
        end=0x000E,
        instructions=[inst],
        is_entry=True,
        is_return=True,
    )
    fake_analysis = SimpleNamespace(
        blocks={0x0000: block},
        xrefs=[],
        call_targets=set(),
        hint_blocks={},
        hint_reasons={},
        lib_calls=[],
        os_kb=make_empty_os_kb(),
        platform=make_platform(),
        indirect_sites=[],
        save=lambda path: None,
    )
    def fake_analyze_hunk(*args: object, **kwargs: object) -> SimpleNamespace:
        assert kwargs["base_addr"] == 0x0C
        assert kwargs["code_start"] == 0x0C
        assert kwargs["entry_points"] == (0x0C,)
        assert kwargs["extra_entry_points"] == ()
        return fake_analysis

    monkeypatch.setattr(module, "analyze_hunk", fake_analyze_hunk)
    monkeypatch.setattr(module, "build_app_slot_infos", lambda *args, **kwargs: ())
    monkeypatch.setattr(module, "name_subroutines", lambda *args, **kwargs: 0)
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

    result = module.build_entities_from_source(source, str(output_path))

    assert result == 0
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert payloads[0]["addr"] == "0x0000"
    assert payloads[0]["end"] == "0x000C"
    assert payloads[0]["type"] == "data"
    assert payloads[0]["subtype"] == "struct_instance"
    assert payloads[1]["addr"] == "0x000C"
    assert payloads[1]["end"] == "0x000E"


def test_build_entities_from_runtime_absolute_raw_binary_normalizes_to_local_offsets(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    target_dir = tmp_path / "targets" / "absolute_raw"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x00" * 0x0C + b"\x4E\x75")
    output_path = target_dir / "entities.jsonl"
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="bootblock",
            entry_register_seeds=(),
            bootblock=BootBlockTargetMetadata(
                magic_ascii="DOS",
                flags_byte=0,
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=880,
                bootcode_offset=0x0C,
                bootcode_size=2,
                load_address=0x70000,
                entrypoint=0x7000C,
            ),
        ),
    )
    inst = disassemble(b"\x4E\x75")[0]
    inst.offset = 0x7000C
    block = BasicBlock(
        start=0x7000C,
        end=0x7000E,
        instructions=[inst],
        is_entry=True,
        is_return=True,
    )
    fake_analysis = SimpleNamespace(
        blocks={0x7000C: block},
        xrefs=[],
        call_targets=set(),
        hint_blocks={},
        hint_reasons={},
        lib_calls=[],
        os_kb=make_empty_os_kb(),
        platform=make_platform(),
        indirect_sites=[],
        save=lambda path: None,
    )
    def fake_analyze_hunk(*args: object, **kwargs: object) -> SimpleNamespace:
        assert kwargs["base_addr"] == 0x7000C
        assert kwargs["code_start"] == 0x0C
        assert kwargs["entry_points"] == (0x7000C,)
        assert kwargs["extra_entry_points"] == ()
        return fake_analysis

    monkeypatch.setattr(module, "analyze_hunk", fake_analyze_hunk)
    monkeypatch.setattr(module, "build_app_slot_infos", lambda *args, **kwargs: ())
    monkeypatch.setattr(module, "name_subroutines", lambda *args, **kwargs: 0)
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

    result = module.build_entities_from_source(source, str(output_path))

    assert result == 0
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert payloads[0]["addr"] == "0x0000"
    assert payloads[0]["end"] == "0x000C"
    assert payloads[0]["type"] == "data"
    assert payloads[0]["subtype"] == "struct_instance"
    assert payloads[1]["addr"] == "0x000C"
    assert payloads[1]["end"] == "0x000E"


def test_build_entities_uses_all_structured_entrypoints_for_autoinit_resident(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    target_dir = tmp_path / "targets" / "library"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "library.bin"
    binary_path.write_bytes(b"fake")
    output_path = target_dir / "entities.jsonl"
    write_target_metadata(
        target_dir,
        TargetMetadata(
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
        ),
    )

    hunk = Hunk(
        index=0,
        hunk_type=int(HunkType.HUNK_CODE),
        mem_type=int(MemType.ANY),
        alloc_size=2,
        data=b"\x4e\x75",
    )
    monkeypatch.setattr(module, "parse", lambda _data: SimpleNamespace(is_executable=True, hunks=[hunk]))
    seen: dict[str, object] = {}
    fake_analysis = SimpleNamespace(
        blocks={0x88: BasicBlock(start=0x88, end=0x8A, instructions=[], is_entry=True)},
        xrefs=[],
        call_targets=set(),
        hint_blocks={},
        hint_reasons={},
        lib_calls=[],
        os_kb=make_empty_os_kb(),
        platform=make_platform(),
        indirect_sites=[],
        save=lambda path: None,
    )

    def fake_analyze_hunk(*args: object, **kwargs: object) -> SimpleNamespace:
        seen["entry_points"] = kwargs["entry_points"]
        seen["extra_entry_points"] = kwargs["extra_entry_points"]
        seen["entry_initial_states"] = kwargs["entry_initial_states"]
        return fake_analysis

    monkeypatch.setattr(module, "analyze_hunk", fake_analyze_hunk)
    monkeypatch.setattr(module, "build_app_slot_infos", lambda *args, **kwargs: ())
    monkeypatch.setattr(module, "name_subroutines", lambda *args, **kwargs: 0)

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    assert seen["entry_points"] == (0x88, 0x90)
    assert seen["extra_entry_points"] == ()
    assert set(cast(dict[int, object], seen["entry_initial_states"])) == {0x88, 0x90}


def test_build_entities_passes_seeded_code_entrypoints_as_additive_hunk_seeds(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"fake")
    output_path = target_dir / "entities.jsonl"
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_code_entrypoints=(
                SeededCodeEntrypointMetadata(
                    addr=0x0123,
                    name="seeded_entry",
                    hunk=0,
                    seed_origin="primary_doc",
                    review_status="seeded",
                    citation="seeded:demo-entry",
                ),
            ),
        ),
    )
    hunk = Hunk(
        index=0,
        hunk_type=int(HunkType.HUNK_CODE),
        mem_type=int(MemType.ANY),
        alloc_size=2,
        data=b"\x4e\x75",
    )
    monkeypatch.setattr(module, "parse", lambda _data: SimpleNamespace(is_executable=True, hunks=[hunk]))
    seen: dict[str, object] = {}
    fake_analysis = SimpleNamespace(
        blocks={0: BasicBlock(start=0, end=2, instructions=[], is_entry=True)},
        xrefs=[],
        call_targets=set(),
        hint_blocks={},
        hint_reasons={},
        lib_calls=[],
        os_kb=make_empty_os_kb(),
        platform=make_platform(),
        indirect_sites=[],
        save=lambda path: None,
    )

    def fake_analyze_hunk(*args: object, **kwargs: object) -> SimpleNamespace:
        seen["entry_points"] = kwargs["entry_points"]
        seen["extra_entry_points"] = kwargs["extra_entry_points"]
        return fake_analysis

    monkeypatch.setattr(module, "analyze_hunk", fake_analyze_hunk)
    monkeypatch.setattr(module, "build_app_slot_infos", lambda *args, **kwargs: ())
    monkeypatch.setattr(module, "name_subroutines", lambda *args, **kwargs: 0)

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    assert seen["entry_points"] == ()
    assert seen["extra_entry_points"] == (0x0123,)


def test_apply_seeded_code_entrypoints_uses_role_as_comment_when_comment_missing() -> None:
    module = _load_build_entities_module()

    entities = [
        {
            "addr": "0x0123",
            "end": "0x0130",
            "type": "code",
            "confidence": "tool-inferred",
            "hunk": 0,
        }
    ]
    seeded = (
        SeededCodeEntrypointMetadata(
            addr=0x0123,
            name="seeded_entry",
            hunk=0,
            role="keyboard input routine",
            seed_origin="primary_doc",
            review_status="seeded",
            citation="seeded:demo-entry",
        ),
    )

    merged = module._apply_seeded_code_entrypoints(entities, seeded, hunk_idx=0)

    assert merged[0]["name"] == "seeded_entry"
    assert merged[0]["comment"] == "keyboard input routine"
