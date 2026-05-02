from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

import amiga_reversing.disasm.entity_builder as entity_builder
from amiga_reversing.disasm.binary_source import RawBinarySource
from amiga_reversing.disasm.target_metadata import (
    BootBlockTargetMetadata,
    EntryRegisterSeedMetadata,
    ResidentAutoinitMetadata,
    ResidentTargetMetadata,
    SeededCodeEntrypointMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    write_target_metadata,
)


def _fake_naming_catalog() -> dict[str, object]:
    return {
        "patterns": [
            {"functions": ["AllocMem"], "name": "alloc_memory", "partial": False},
        ],
        "trivial_functions": ["AllocMem", "FreeMem", "SetSignal"],
        "generic_prefix": "call_",
        "libraries": ["dos.library", "exec.library", "icon.library"],
    }


def test_build_entities_help_loads_cleanly() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "amiga_reversing.tools.build_entities", "--help"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Build entities.jsonl from C backend binary analysis" in result.stdout


def test_structured_prefix_entities_only_emit_when_requested() -> None:
    module = _load_build_entities_module()
    effective_policy = {
        "analysis_policy": {
            "structured_data_items": [{
                "section_index": 0,
                "offset": 4,
                "size": 26,
                "struct_name": "RT",
            }]
        }
    }

    assert module._structured_prefix_entities(effective_policy, 0, include_structure=False) == []
    payloads = module._structured_prefix_entities(effective_policy, 0, include_structure=True)
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


def _load_build_entities_module() -> object:
    return entity_builder


def _empty_effective_policy() -> dict[str, object]:
    return {"analysis_policy": {}}


def _stub_effective_policy(
    monkeypatch: MonkeyPatch,
    module: object,
    policy: dict[str, object] | None = None,
) -> None:
    monkeypatch.setattr(
        module,
        "effective_policy_project_source_with_c_backend",
        lambda *args, **kwargs: _empty_effective_policy() if policy is None else policy,
    )


def _c_analysis_section(
    *,
    section_index: int = 0,
    section_kind: int = 1,
    section_size: int,
    blocks: list[dict[str, int]] | None = None,
    edges: list[dict[str, int]] | None = None,
    calls: list[dict[str, object]] | None = None,
    effects: list[dict[str, object]] | None = None,
    entity_hints: list[dict[str, object]] | None = None,
    indirect_sites: list[dict[str, object]] | None = None,
    string_refs: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "section_index": section_index,
        "section_kind": section_kind,
        "section_size": section_size,
        "blocks": [] if blocks is None else blocks,
        "edges": [] if edges is None else edges,
        "entity_hints": [] if entity_hints is None else entity_hints,
        "recovered_platform_calls": [] if calls is None else calls,
        "recovered_platform_effects": [] if effects is None else effects,
        "recovered_indirect_sites": [] if indirect_sites is None else indirect_sites,
        "recovered_string_refs": [] if string_refs is None else string_refs,
    }


def test_os_input_reg_key_joins_grouped_registers() -> None:
    module = _load_build_entities_module()

    assert module._os_input_reg_key(("D0",)) == "D0"
    assert module._os_input_reg_key(("D0", "D1")) == "D0/D1"


def test_grouped_os_call_inputs_are_emitted_in_entity_payload() -> None:
    module = _load_build_entities_module()
    payload = module._c_api_call_type_payload("exec.library/Foo", {
        "inputs": [{
            "name": "parm",
            "regs": ["D0", "D1"],
            "type": "DOUBLE",
        }],
    })

    assert payload == {
        "call": "exec.library/Foo",
        "inputs": {"D0/D1": {"type": "DOUBLE"}},
    }


def test_grouped_os_call_outputs_are_emitted_in_entity_payload() -> None:
    module = _load_build_entities_module()
    payload = module._c_api_call_type_payload(
        "exec.library/CreateMsgPort",
        {
            "outputs": [
                {
                    "name": "port",
                    "regs": ["D0"],
                    "type": "struct MsgPort *",
                    "o_struct": "MsgPort",
                    "value_domain": "exec.msgport",
                }
            ],
        },
    )

    assert payload == {
        "call": "exec.library/CreateMsgPort",
        "outputs": {"D0": {"type": "struct MsgPort *", "o_struct": "MsgPort", "value_domain": "exec.msgport"}},
    }


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


def test_c_subroutine_map_keeps_unowned_reached_blocks_as_code() -> None:
    module = _load_build_entities_module()
    section = _c_analysis_section(
        section_size=0x20,
        blocks=[
            {"start_offset": 0x00, "end_offset": 0x02, "certainty": 1, "edge_start": 0, "edge_count": 0},
            {"start_offset": 0x10, "end_offset": 0x12, "certainty": 1, "edge_start": 0, "edge_count": 0},
        ],
    )

    subroutines = module._build_c_subroutine_map(section, {0x00})

    assert [(sub.addr, sub.end, sub.reached) for sub in subroutines] == [
        (0x00, 0x02, True),
        (0x10, 0x12, True),
    ]


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
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=0x0E,
                blocks=[
                    {
                        "start_offset": 0x0C,
                        "end_offset": 0x0E,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    }
                ],
            )
        ]
    }
    seen: dict[str, object] = {}

    def fake_analyze_project_source_with_c_backend(*args: object, **kwargs: object) -> dict[str, object]:
        seen["source"] = args[0]
        seen["metadata_path"] = kwargs["metadata_path"]
        seen["entry_offset_args"] = kwargs["entry_offset_args"]
        return fake_analysis

    monkeypatch.setattr(
        module,
        "analyze_project_source_with_c_backend",
        fake_analyze_project_source_with_c_backend,
    )

    result = module.build_entities_from_source(source, str(output_path))

    assert result == 0
    assert seen["source"] is source
    assert seen["metadata_path"] == target_dir / "target_metadata.json"
    assert seen["entry_offset_args"] == ()
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
    assert payloads[1]["name"] == "boot_entry"


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
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=0x0E,
                blocks=[
                    {
                        "start_offset": 0x0C,
                        "end_offset": 0x0E,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    }
                ],
            )
        ]
    }
    seen: dict[str, object] = {}

    def fake_analyze_project_source_with_c_backend(*args: object, **kwargs: object) -> dict[str, object]:
        seen["source"] = args[0]
        seen["metadata_path"] = kwargs["metadata_path"]
        seen["entry_offset_args"] = kwargs["entry_offset_args"]
        return fake_analysis

    monkeypatch.setattr(
        module,
        "analyze_project_source_with_c_backend",
        fake_analyze_project_source_with_c_backend,
    )

    result = module.build_entities_from_source(source, str(output_path))

    assert result == 0
    assert seen["source"] is source
    assert seen["metadata_path"] == target_dir / "target_metadata.json"
    assert seen["entry_offset_args"] == ()
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
    assert payloads[1]["name"] == "boot_entry"


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

    seen: dict[str, object] = {}
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=0x92,
                blocks=[
                    {
                        "start_offset": 0x88,
                        "end_offset": 0x8A,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    },
                    {
                        "start_offset": 0x90,
                        "end_offset": 0x92,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    },
                ],
            )
        ]
    }

    def fake_analyze_project_source_with_c_backend(*args: object, **kwargs: object) -> dict[str, object]:
        seen["metadata_path"] = kwargs["metadata_path"]
        seen["entry_offset_args"] = kwargs["entry_offset_args"]
        return fake_analysis

    monkeypatch.setattr(
        module,
        "analyze_project_source_with_c_backend",
        fake_analyze_project_source_with_c_backend,
    )
    _stub_effective_policy(
        monkeypatch,
        module,
        {
            "analysis_policy": {
                "entrypoints": [
                    {"section_index": 0, "offset": 0x88},
                    {"section_index": 0, "offset": 0x90},
                ],
                "register_seeds": [],
            }
        },
    )

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    assert seen["metadata_path"] == target_dir / "target_metadata.json"
    assert seen["entry_offset_args"] == ()
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    code_addrs = {payload["addr"] for payload in payloads if payload["type"] == "code"}
    assert {"0x0088", "0x0090"} <= code_addrs


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
    seen: dict[str, object] = {}
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=0x125,
                blocks=[
                    {
                        "start_offset": 0x0123,
                        "end_offset": 0x0125,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    }
                ],
            )
        ]
    }

    def fake_analyze_project_source_with_c_backend(*args: object, **kwargs: object) -> dict[str, object]:
        seen["metadata_path"] = kwargs["metadata_path"]
        seen["entry_offset_args"] = kwargs["entry_offset_args"]
        return fake_analysis

    monkeypatch.setattr(
        module,
        "analyze_project_source_with_c_backend",
        fake_analyze_project_source_with_c_backend,
    )
    _stub_effective_policy(monkeypatch, module)

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    assert seen["metadata_path"] == target_dir / "target_metadata.json"
    assert seen["entry_offset_args"] == ()
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    seeded_entity = next(payload for payload in payloads if payload["addr"] == "0x0123")
    assert seeded_entity["name"] == "seeded_entry"


def test_build_entities_names_from_c_os_calls(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"fake")
    output_path = target_dir / "entities.jsonl"
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=0x20,
                blocks=[
                    {
                        "start_offset": 0,
                        "end_offset": 0x20,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    }
                ],
                calls=[
                    {
                        "offset": 0x10,
                        "function_name": "AllocMem",
                        "library_name": "exec.library",
                        "inputs": [],
                    }
                ],
            )
        ]
    }
    monkeypatch.setattr(module, "analyze_project_source_with_c_backend", lambda *args, **kwargs: fake_analysis)
    monkeypatch.setattr(module, "_c_naming_catalog", _fake_naming_catalog)
    _stub_effective_policy(monkeypatch, module)

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    code_entity = next(payload for payload in payloads if payload["type"] == "code")
    assert code_entity["name"] == "alloc_memory"
    assert code_entity["status"] == "named"


def test_build_entities_projects_c_effects_to_app_slots(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"fake")
    output_path = target_dir / "entities.jsonl"
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=0x20,
                blocks=[
                    {
                        "start_offset": 0,
                        "end_offset": 0x20,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    }
                ],
                effects=[
                    {
                        "offset": 0x04,
                        "kind": 5,
                        "reg_kind": 2,
                        "reg_index": 0,
                        "displacement": 0x10,
                        "field_disp": -32768,
                        "base_name": None,
                        "symbol_name": None,
                        "type_name": "IO",
                        "semantic_kind": None,
                        "value_domain_name": None,
                        "has_constant_value": 0,
                        "constant_value": 0,
                    },
                    {
                        "offset": 0x08,
                        "kind": 2,
                        "reg_kind": 2,
                        "reg_index": 0,
                        "displacement": 0x20,
                        "field_disp": -32768,
                        "base_name": "DOSBase",
                        "symbol_name": None,
                        "type_name": None,
                        "semantic_kind": None,
                        "value_domain_name": None,
                        "has_constant_value": 0,
                        "constant_value": 0,
                    },
                    {
                        "offset": 0x0C,
                        "kind": 3,
                        "reg_kind": 2,
                        "reg_index": 1,
                        "displacement": 0x30,
                        "field_disp": 4,
                        "base_name": None,
                        "symbol_name": None,
                        "type_name": "IO",
                        "semantic_kind": "code_ptr",
                        "value_domain_name": None,
                        "has_constant_value": 0,
                        "constant_value": 0,
                    },
                ],
            )
        ]
    }
    monkeypatch.setattr(module, "analyze_project_source_with_c_backend", lambda *args, **kwargs: fake_analysis)
    _stub_effective_policy(monkeypatch, module)

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    code_entity = next(payload for payload in payloads if payload["type"] == "code")
    assert code_entity["named_bases"] == ["DOSBase"]
    assert code_entity["struct_refs"] == ["IO"]
    slots = {slot["offset"]: slot for slot in code_entity["app_slots"]}
    assert slots["0x0010"]["kind"] == "struct_instance"
    assert slots["0x0010"]["struct"] == "IO"
    assert slots["0x0020"]["named_base"] == "DOSBase"
    assert slots["0x0030"]["kind"] == "code_pointer"
    assert slots["0x0030"]["owner_type"] == "IO"
    assert slots["0x0030"]["field_offset"] == "0x0004"


def test_build_entities_prefers_c_entity_hints_for_app_slots(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    binary_path = tmp_path / "program.bin"
    output_path = tmp_path / "entities.jsonl"
    binary_path.write_bytes(b"\x4e\x75")
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=2,
                blocks=[{"start_offset": 0, "end_offset": 2}],
                entity_hints=[
                    {
                        "offset": 0,
                        "hint_kind": "app_slot",
                        "app_slot": {
                            "offset": "0x0020",
                            "symbol": "app_slot_0020",
                            "named_base": "DOSBase",
                        },
                    }
                ],
                effects=[
                    {
                        "offset": 0,
                        "kind": 2,
                        "displacement": 0x20,
                        "base_name": "stale",
                    }
                ],
            )
        ]
    }
    monkeypatch.setattr(module, "analyze_project_source_with_c_backend", lambda *args, **kwargs: fake_analysis)
    _stub_effective_policy(monkeypatch, module)

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    code_entity = next(payload for payload in payloads if payload["type"] == "code")
    assert code_entity["app_slots"] == [
        {
            "offset": "0x0020",
            "symbol": "app_slot_0020",
            "named_base": "DOSBase",
        }
    ]


def test_build_entities_projects_c_platform_calls_to_indirect_sites(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"fake")
    output_path = target_dir / "entities.jsonl"
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=0x20,
                blocks=[
                    {
                        "start_offset": 0,
                        "end_offset": 0x20,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    }
                ],
                calls=[
                    {
                        "offset": 0x04,
                        "kind": 3,
                        "symbol_name": None,
                        "note_kind": 2,
                        "note_base_name": "IO",
                        "note_symbol_name": "io_CallBack",
                        "note_reg": 0,
                        "note_disp": 0x10B8,
                        "note_field_disp": 4,
                    },
                    {
                        "offset": 0x08,
                        "kind": 2,
                        "symbol_name": None,
                        "note_kind": 3,
                        "note_base_name": "DOSBase",
                        "note_symbol_name": "_LVORead",
                        "note_reg": 0,
                        "note_disp": -32768,
                        "note_field_disp": -32768,
                        "library_name": "dos.library",
                        "function_name": "Read",
                        "inputs": [],
                    },
                    {
                        "offset": 0x0C,
                        "kind": 2,
                        "symbol_name": None,
                        "note_kind": 1,
                        "note_base_name": "DOSBase",
                        "note_symbol_name": None,
                        "note_reg": 0,
                        "note_disp": -32768,
                        "note_field_disp": -32768,
                        "library_name": "dos.library",
                    },
                ],
            )
        ]
    }
    monkeypatch.setattr(module, "analyze_project_source_with_c_backend", lambda *args, **kwargs: fake_analysis)
    _stub_effective_policy(monkeypatch, module)

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    code_entity = next(payload for payload in payloads if payload["type"] == "code")
    sites = {site["addr"]: site for site in code_entity["indirect_sites"]}
    assert sites["0x0004"] == {
        "addr": "0x0004",
        "shape": "callback_field",
        "status": "per_caller",
        "flow": "call",
        "detail": "IO.io_CallBack",
        "base_offset": "0x10B8",
        "field_offset": "0x0004",
    }
    assert sites["0x0008"] == {
        "addr": "0x0008",
        "shape": "local_wrapper_dispatch",
        "status": "external",
        "flow": "call",
        "detail": "DOSBase/_LVORead",
        "library": "dos.library",
    }
    assert sites["0x000C"] == {
        "addr": "0x000C",
        "shape": "indexed_library_dispatch",
        "status": "per_caller",
        "flow": "call",
        "detail": "DOSBase",
        "library": "dos.library",
    }


def test_build_entities_summarizes_c_indirect_site_library() -> None:
    module = _load_build_entities_module()
    entities = [{
        "addr": "0x0010",
        "end": "0x0018",
        "type": "code",
        "indirect_sites": [{
            "addr": "0x0014",
            "shape": "indexed_library_dispatch",
            "status": "per_caller",
            "flow": "call",
            "library": "dos.library",
        }],
    }]

    module.summarize_entity_app_slots(entities)
    named = module._name_c_hunk_entities(entities)

    assert entities[0]["named_bases"] == ["dos.library"]
    assert entities[0]["struct_refs"] == ["DosLibrary"]
    assert named == 1
    assert entities[0]["name"] == "dos_dispatch"


def test_name_c_hunk_entities_uses_c_string_refs(monkeypatch: MonkeyPatch) -> None:
    module = _load_build_entities_module()
    monkeypatch.setattr(module, "_c_naming_catalog", _fake_naming_catalog)
    entities = [{
        "addr": "0x0010",
        "end": "0x0018",
        "type": "code",
        "string_refs": [{
            "addr": "0x0012",
            "target": "0x0080",
            "text": "Line malformed",
        }],
    }]

    named = module._name_c_hunk_entities(entities)

    assert named == 1
    assert entities[0]["name"] == "line_malformed"


def test_build_entities_projects_c_generic_indirect_sites(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"fake")
    output_path = target_dir / "entities.jsonl"
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=0x20,
                blocks=[
                    {
                        "start_offset": 0,
                        "end_offset": 0x20,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    }
                ],
                indirect_sites=[
                    {
                        "offset": 0x04,
                        "shape": "pcindex.brief",
                        "status": "jump_table",
                        "flow": "call",
                        "detail": "word_dispatch",
                        "target_count": 3,
                    }
                ],
            )
        ]
    }
    monkeypatch.setattr(module, "analyze_project_source_with_c_backend", lambda *args, **kwargs: fake_analysis)
    monkeypatch.setattr(module, "_c_naming_catalog", _fake_naming_catalog)
    _stub_effective_policy(monkeypatch, module)

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    code_entity = next(payload for payload in payloads if payload["type"] == "code")
    assert code_entity["indirect_sites"] == [
        {
            "addr": "0x0004",
            "shape": "pcindex.brief",
            "status": "jump_table",
            "flow": "call",
            "detail": "word_dispatch",
            "target_count": 3,
        }
    ]


def test_build_entities_projects_c_string_refs(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_entities_module()
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"fake")
    output_path = target_dir / "entities.jsonl"
    fake_analysis = {
        "sections": [
            _c_analysis_section(
                section_size=0x40,
                blocks=[
                    {
                        "start_offset": 0,
                        "end_offset": 0x20,
                        "certainty": 1,
                        "edge_start": 0,
                        "edge_count": 0,
                    }
                ],
                string_refs=[
                    {
                        "offset": 0x04,
                        "target": 0x30,
                        "text": "Sign extended operand",
                    }
                ],
            )
        ]
    }
    monkeypatch.setattr(module, "analyze_project_source_with_c_backend", lambda *args, **kwargs: fake_analysis)
    _stub_effective_policy(monkeypatch, module)

    result = module.build_entities(str(binary_path), str(output_path))

    assert result == 0
    payloads = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    code_entity = next(payload for payload in payloads if payload["type"] == "code")
    assert code_entity["string_refs"] == [
        {
            "addr": "0x0004",
            "target": "0x0030",
            "text": "Sign extended operand",
        }
    ]
    assert code_entity["name"] == "sign_extended_operand"


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
