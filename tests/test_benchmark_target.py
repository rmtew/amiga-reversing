from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from disasm.analysis_loader import analysis_cache_root, hunk_analysis_cache_path
from disasm.target_metadata import (
    EntryRegisterSeedMetadata,
    ResidentAutoinitMetadata,
    ResidentTargetMetadata,
    SeededCodeEntrypointMetadata,
    TargetMetadata,
    load_target_metadata,
    write_target_metadata,
)
from m68k.hunk_parser import Hunk, HunkType, MemType
from scripts.benchmark_target import (
    AnalysisBenchmark,
    AnalysisTimingBenchmark,
    DisasmBenchmark,
    EntitiesTimingBenchmark,
    EntityBenchmark,
    LibraryLvoBenchmark,
    LvoBenchmark,
    SessionTimingBenchmark,
    SymbolUsageBenchmark,
    TargetBenchmark,
    TimingBenchmark,
    _analysis_cache_paths,
    _benchmark_record,
    _disk_project_benchmark,
    main,
)
from scripts.precommit import _benchmark_targets


def test_benchmark_record_uses_target_command_and_sizes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = tmp_path / "binary.analysis.hunk-0"
    entities = tmp_path / "entities.jsonl"
    disasm = tmp_path / "example.s"
    analysis.write_bytes(b"a" * 10)
    entities.write_bytes(b"b" * 20)
    disasm.write_bytes(b"c" * 30)

    monkeypatch.setattr(
        "scripts.benchmark_target._analysis_benchmark",
        lambda paths: AnalysisBenchmark(
            code_bytes=100,
            core_block_count=2,
            core_instruction_count=5,
            core_covered_bytes=20,
            core_coverage_ratio=0.2,
            hint_block_count=1,
            hint_instruction_count=2,
            hint_covered_bytes=8,
            hint_coverage_ratio=0.08,
            xref_count=3,
            jump_table_count=0,
            indirect_site_count=1,
            call_target_count=4,
            branch_target_count=5,
            library_call_count=6,
            resolved_library_call_count=4,
            library_count=2,
        ),
    )
    monkeypatch.setattr(
        "scripts.benchmark_target._entities_benchmark",
        lambda path: EntityBenchmark(
            entity_count=7,
            code_entity_count=3,
            data_entity_count=2,
            bss_entity_count=1,
            unknown_entity_count=1,
            named_entity_count=4,
            documented_entity_count=1,
        ),
    )

    record = _benchmark_record(
        "example",
        "bin/Example",
        "ok",
        12.345,
        [analysis],
        entities,
        disasm,
    )

    assert record.target == "example"
    assert record.binary == "bin/Example"
    assert record.command == "uv run scripts/benchmark_target.py example"
    assert record.status == "ok"
    assert record.elapsed_seconds == 12.35
    assert record.analysis_bytes == 10
    assert record.entities_bytes == 20
    assert record.disasm_bytes == 30
    assert record.timing is None
    assert record.analysis is not None
    assert record.analysis.core_block_count == 2
    assert record.analysis.library_call_count == 6
    assert record.entities is not None
    assert record.entities.entity_count == 7
    assert record.entities.named_entity_count == 4
    assert record.disasm is None
    assert record.error is None


def test_benchmark_record_sums_analysis_cache_sizes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis0 = tmp_path / "binary.analysis.hunk-0"
    analysis1 = tmp_path / "binary.analysis.hunk-1"
    entities = tmp_path / "entities.jsonl"
    disasm = tmp_path / "example.s"
    analysis0.write_bytes(b"a" * 10)
    analysis1.write_bytes(b"b" * 15)
    entities.write_bytes(b"c" * 20)
    disasm.write_bytes(b"d" * 30)

    monkeypatch.setattr("scripts.benchmark_target._analysis_benchmark", lambda paths: None)
    monkeypatch.setattr("scripts.benchmark_target._entities_benchmark", lambda path: None)

    record = _benchmark_record(
        "example",
        "bin/Example",
        "ok",
        1.0,
        [analysis0, analysis1],
        entities,
        disasm,
    )

    assert record.analysis_bytes == 25


def test_precommit_benchmark_targets_include_file_and_disk_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    targets_dir = tmp_path / "targets"
    file_target = targets_dir / "filedemo"
    disk_target = targets_dir / "amiga_disk_demo"
    raw_target = targets_dir / "rawdemo"
    disk_child_target = targets_dir / "diskdemo"
    empty_target = targets_dir / "empty"
    bin_dir = tmp_path / "bin"
    targets_dir.mkdir()
    file_target.mkdir()
    disk_target.mkdir()
    raw_target.mkdir()
    disk_child_target.mkdir()
    empty_target.mkdir()
    bin_dir.mkdir()
    (file_target / "entities.jsonl").write_text("")
    (raw_target / "entities.jsonl").write_text("")
    (disk_child_target / "entities.jsonl").write_text("")
    (empty_target / "entities.jsonl").write_text("")
    (bin_dir / "DemoGame").write_bytes(b"\x4e\x75")
    (bin_dir / "demo.adf").write_bytes(b"demo")
    (raw_target / "binary.bin").write_bytes(b"\x00" * 12 + b"\x4e\x75")
    (file_target / "source_binary.json").write_text(
        '{"kind":"hunk_file","path":"bin/DemoGame"}\n',
        encoding="utf-8",
    )
    (disk_child_target / "source_binary.json").write_text(
        '{"kind":"disk_entry","disk_id":"demo","disk_path":"bin/demo.adf","entry_path":"c/Run","parent_disk_id":"demo"}\n',
        encoding="utf-8",
    )
    (raw_target / "source_binary.json").write_text(
        '{"kind":"raw_binary","address_model":"local_offset","path":"targets/rawdemo/binary.bin","load_address":458752,"entrypoint":458764,"code_start_offset":0}\n',
        encoding="utf-8",
    )
    (disk_target / "manifest.json").write_text('{"schema_version":1,"disk_id":"demo","source_path":"bin/demo.adf","source_sha256":"deadbeef","analysis":{"disk_info":{"path":"demo.adf","size":901120,"variant":"DD","total_sectors":1760,"sectors_per_track":11,"is_dos":true},"boot_block":{"magic_ascii":"DOS","is_dos":true,"flags_byte":1,"fs_type":"FFS","fs_description":"DOS\\\\1 - Fast File System","checksum":"0x00000000","checksum_valid":true,"rootblock_ptr":880,"bootcode_size":1012,"bootcode_has_code":false,"bootcode_entropy":0.0}},"imported_targets":[],"bootblock_target_name":"amiga_disk_demo__amiga_raw_bootblock","bootblock_target_path":"targets/amiga_disk_demo/targets/amiga_raw_bootblock"}', encoding="utf-8")
    (disk_target / ".project.json").write_text('{"schema_version":1,"created_at":"2026-03-25T00:00:00+00:00","updated_at":"2026-03-25T00:00:00+00:00"}', encoding="utf-8")

    monkeypatch.setattr("scripts.precommit.TARGETS_DIR", targets_dir)
    monkeypatch.setattr("scripts.precommit.ROOT", tmp_path)

    assert _benchmark_targets() == ["amiga_disk_demo", "filedemo", "rawdemo"]


def test_benchmark_main_fails_when_any_target_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scripts.benchmark_target.benchmark_target",
        lambda target: type("Record", (), {"target": target, "status": "failed", "elapsed_seconds": 1.0})(),
    )

    assert main(["benchmark_target.py", "demo"]) == 1


def test_disk_project_benchmark_orders_children_by_manifest_entry_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    targets_dir = tmp_path / "targets"
    disk_target = targets_dir / "amiga_disk_demo"
    targets_dir.mkdir()
    disk_target.mkdir()
    (disk_target / "manifest.json").write_text(
        """{
  "schema_version": 1,
  "disk_id": "demo",
  "source_path": "bin/demo.adf",
  "source_sha256": "deadbeef",
  "analysis": {
    "disk_info": {
      "path": "demo.adf",
      "size": 901120,
      "variant": "DD",
      "total_sectors": 1760,
      "sectors_per_track": 11,
      "is_dos": true
    },
    "boot_block": {
      "magic_ascii": "DOS",
      "is_dos": true,
      "flags_byte": 1,
      "fs_type": "FFS",
      "fs_description": "DOS\\\\1 - Fast File System",
      "checksum": "0x00000000",
      "checksum_valid": true,
      "rootblock_ptr": 880,
      "bootcode_size": 1012,
      "bootcode_has_code": false,
      "bootcode_entropy": 0.0
    }
  },
  "bootblock_target_name": "amiga_disk_demo__amiga_raw_bootblock",
  "bootblock_target_path": "targets/amiga_disk_demo/targets/amiga_raw_bootblock",
  "imported_targets": [
    {
      "target_name": "amiga_disk_demo__amiga_hunk_z_last",
      "target_path": "targets/amiga_disk_demo/targets/amiga_hunk_z_last",
      "entry_path": "z/last",
      "binary_path": "bin/demo.adf::z/last",
      "target_type": "program"
    },
    {
      "target_name": "amiga_disk_demo__amiga_hunk_a_first",
      "target_path": "targets/amiga_disk_demo/targets/amiga_hunk_a_first",
      "entry_path": "a/first",
      "binary_path": "bin/demo.adf::a/first",
      "target_type": "program"
    }
  ]
}""",
        encoding="utf-8",
    )

    seen: list[str] = []

    def fake_benchmark_binary_target(target: str, *, write_output: bool) -> object:
        seen.append(target)
        return TargetBenchmark(
            target=target,
            binary=f"bin/{target}",
            command=f"uv run scripts/benchmark_target.py {target}",
            measured_at="2026-03-26T12:00:00+13:00",
            status="ok",
            elapsed_seconds=1.0,
            analysis_bytes=1,
            entities_bytes=1,
            disasm_bytes=1,
            timing=TimingBenchmark(
                entities=EntitiesTimingBenchmark(
                    parse_source_seconds=0.1,
                    analysis=AnalysisTimingBenchmark(
                        init_seconds=0.2,
                        core_seconds=0.3,
                        per_caller_seconds=0.4,
                        store_pass_seconds=0.5,
                        hint_scan_seconds=0.6,
                        os_call_seconds=0.7,
                    ),
                    naming_seconds=0.8,
                    write_seconds=0.9,
                ),
                session=SessionTimingBenchmark(
                    load_analysis_seconds=1.0,
                    metadata_seconds=1.1,
                    substitutions_seconds=1.2,
                    build_seconds=1.3,
                ),
                emit_seconds=0.3,
                render_seconds=0.4,
            ),
            analysis=None,
            entities=None,
            disasm=DisasmBenchmark(
                lvo=LvoBenchmark(
                    included_count=2,
                    inserted_count=1,
                    by_library={
                        "dos.library": LibraryLvoBenchmark(included=2, inserted=0),
                        "foo.library": LibraryLvoBenchmark(included=0, inserted=1),
                    },
                ),
                symbols=SymbolUsageBenchmark(
                    immediate_constant_count=5,
                    struct_field_count=6,
                    app_struct_field_count=7,
                ),
            ),
            error=None,
            targets=None,
        )

    monkeypatch.setattr("scripts.benchmark_target.TARGETS_DIR", targets_dir)
    monkeypatch.setattr("scripts.benchmark_target._benchmark_binary_target", fake_benchmark_binary_target)

    record = _disk_project_benchmark("amiga_disk_demo")

    assert seen == [
        "amiga_disk_demo__amiga_raw_bootblock",
        "amiga_disk_demo__amiga_hunk_a_first",
        "amiga_disk_demo__amiga_hunk_z_last",
    ]
    assert record.timing == TimingBenchmark(
        entities=EntitiesTimingBenchmark(
            parse_source_seconds=0.3,
            analysis=AnalysisTimingBenchmark(
                init_seconds=0.6,
                core_seconds=0.9,
                per_caller_seconds=1.2,
                store_pass_seconds=1.5,
                hint_scan_seconds=1.8,
                os_call_seconds=2.1,
            ),
            naming_seconds=2.4,
            write_seconds=2.7,
        ),
        session=SessionTimingBenchmark(
            load_analysis_seconds=3.0,
            metadata_seconds=3.3,
            substitutions_seconds=3.6,
            build_seconds=3.9,
        ),
        emit_seconds=0.9,
        render_seconds=1.2,
    )
    assert record.disasm == DisasmBenchmark(
        lvo=LvoBenchmark(
            included_count=6,
            inserted_count=3,
            by_library={
                "dos.library": LibraryLvoBenchmark(included=6, inserted=0),
                "foo.library": LibraryLvoBenchmark(included=0, inserted=3),
            },
        ),
        symbols=SymbolUsageBenchmark(
            immediate_constant_count=15,
            struct_field_count=18,
            app_struct_field_count=21,
        ),
    )


def test_analysis_cache_paths_for_resident_hunk_target_use_zero_code_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_dir = tmp_path / "targets" / "amiga_hunk_icon"
    bin_dir = tmp_path / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir()
    (target_dir / ".project.json").write_text(
        '{"schema_version":1,"created_at":"2026-03-25T00:00:00+00:00","updated_at":"2026-03-25T00:00:00+00:00"}',
        encoding="utf-8",
    )
    (target_dir / "source_binary.json").write_text(
        '{"kind":"hunk_file","path":"bin/icon.library"}\n',
        encoding="utf-8",
    )
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
    (bin_dir / "icon.library").write_bytes(b"fake")

    from disasm.binary_source import resolve_target_binary_source
    from disasm.entry_seeds import build_entry_seed_config

    monkeypatch.setattr(
        "scripts.benchmark_target.parse",
        lambda _data: SimpleNamespace(
            hunks=[
                Hunk(
                    index=0,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=2,
                    data=b"\x4e\x75",
                )
            ]
        ),
    )

    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None
    analysis_paths = _analysis_cache_paths(target_dir, binary_source)
    seed_key = build_entry_seed_config(load_target_metadata(target_dir)).seed_key
    expected_root = analysis_cache_root(
        binary_source.analysis_cache_path,
        seed_key=seed_key,
        base_addr=0,
        code_start=0,
        entry_points=(0x88, 0x90),
        extra_entry_points=(),
    )
    assert analysis_paths == [hunk_analysis_cache_path(expected_root, 0)]


def test_analysis_cache_paths_include_seeded_code_entrypoints_for_hunk_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_dir = tmp_path / "targets" / "amiga_hunk_demo"
    bin_dir = tmp_path / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir()
    (target_dir / ".project.json").write_text(
        '{"schema_version":1,"created_at":"2026-03-25T00:00:00+00:00","updated_at":"2026-03-25T00:00:00+00:00"}',
        encoding="utf-8",
    )
    (target_dir / "source_binary.json").write_text(
        '{"kind":"hunk_file","path":"bin/demo.bin"}\n',
        encoding="utf-8",
    )
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_code_entrypoints=(
                SeededCodeEntrypointMetadata(
                    addr=0x05D6,
                    name="check_keyboard",
                    hunk=0,
                    seed_origin="primary_doc",
                    review_status="seeded",
                    citation="seeded:demo-entry",
                ),
            ),
        ),
    )
    (bin_dir / "demo.bin").write_bytes(b"fake")

    from disasm.binary_source import resolve_target_binary_source
    from disasm.entry_seeds import build_entry_seed_config

    monkeypatch.setattr(
        "scripts.benchmark_target.parse",
        lambda _data: SimpleNamespace(
            hunks=[
                Hunk(
                    index=0,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=2,
                    data=b"\x4e\x75",
                )
            ]
        ),
    )

    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None
    analysis_paths = _analysis_cache_paths(target_dir, binary_source)
    seed_key = build_entry_seed_config(load_target_metadata(target_dir)).seed_key
    expected_root = analysis_cache_root(
        binary_source.analysis_cache_path,
        seed_key=seed_key,
        base_addr=0,
        code_start=0,
        entry_points=(),
        extra_entry_points=(0x05D6,),
    )
    assert analysis_paths == [hunk_analysis_cache_path(expected_root, 0)]
