from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm.binary_source import BinarySourceKind
from amiga_reversing.tools import precommit
from amiga_reversing.tools.benchmark_target import (
    TargetBenchmark,
    _assembler_profile_for_target,
    _benchmark_binary_target,
    _benchmark_record,
    _disk_project_benchmark,
    main,
)
from amiga_reversing.tools.precommit import _benchmark_targets


def test_benchmark_record_uses_target_command_and_sizes(
    tmp_path: Path,
) -> None:
    c_benchmark: dict[str, object] = {
        "analysis": {"violation_count": 2},
        "facts_v2": {"decoded_candidates": 3},
    }
    disasm = tmp_path / "example.s"
    disasm.write_bytes(b"c" * 30)

    record = _benchmark_record(
        "example",
        "bin/Example",
        "ok",
        12.345,
        c_benchmark,
        disasm,
    )

    assert record.target == "example"
    assert record.binary == "bin/Example"
    assert record.command == "uv run amiga-benchmark-target example"
    assert record.status == "ok"
    assert record.elapsed_seconds == 12.35
    assert record.benchmark_bytes is not None
    assert record.disasm_bytes == 30
    assert record.analysis == {"violation_count": 2}
    assert record.facts_v2 == {"decoded_candidates": 3}
    assert record.error is None


def test_benchmark_record_uses_c_benchmark_json_size(
    tmp_path: Path,
) -> None:
    c_benchmark: dict[str, object] = {"analysis": {"violation_counts": {"unresolved_indirect": 1}}}
    disasm = tmp_path / "example.s"
    disasm.write_bytes(b"d" * 30)

    record = _benchmark_record(
        "example",
        "bin/Example",
        "ok",
        1.0,
        c_benchmark,
        disasm,
    )

    assert record.benchmark_bytes == len(json.dumps(c_benchmark, sort_keys=True).encode("utf-8"))


def test_benchmark_binary_target_uses_c_analysis_and_render(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    disasm_path = target_dir / "demo.s"

    monkeypatch.setattr(
        "amiga_reversing.tools.benchmark_target.resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=SimpleNamespace(
                kind=BinarySourceKind.HUNK_FILE,
                path=Path("bin/demo"),
                display_path="bin/demo",
            ),
            output_path=disasm_path,
        ),
    )
    monkeypatch.setattr(
        "amiga_reversing.tools.benchmark_target.benchmark_project_source_with_text_from_c_backend",
        lambda source, metadata_path, project_root: (
            {"analysis": {"violation_count": 1}, "analysis_backend": "facts_v2"},
            "; demo\n",
        ),
    )

    record = _benchmark_binary_target("demo", write_output=True)

    assert record.status == "ok"
    assert record.analysis == {"violation_count": 1}
    assert record.command == "uv run amiga-benchmark-target demo"
    assert disasm_path.read_text(encoding="utf-8") == "; demo\n"


def test_assembler_profile_for_target_uses_devpac_for_genam(tmp_path: Path) -> None:
    assert _assembler_profile_for_target(tmp_path / "amiga_hunk_genam") == "devpac"
    assert _assembler_profile_for_target(tmp_path / "amiga_hunk_demo") == "vasm"


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
    (disk_target / ".project.json").write_text(
        '{"schema_version":2,"created_at":"2026-03-25T00:00:00+00:00","updated_at":"2026-03-25T00:00:00+00:00","origin":{"kind":"test_project"}}',
        encoding="utf-8",
    )

    monkeypatch.setattr("amiga_reversing.tools.precommit.TARGETS_DIR", targets_dir)
    monkeypatch.setattr("amiga_reversing.tools.precommit.ROOT", tmp_path)

    assert _benchmark_targets() == ["amiga_disk_demo", "filedemo", "rawdemo"]


def test_precommit_benchmark_step_runs_target_benchmark(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target_name = "amiga_disk_demo"
    targets_dir = tmp_path / "targets"
    monkeypatch.setenv(precommit.FACTS_V2_GATE_ENV, "0")
    commands: list[list[str]] = []
    target_root = targets_dir / target_name
    target_root.mkdir(parents=True, exist_ok=True)
    (target_root / "manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(precommit, "TARGETS_DIR", targets_dir)
    monkeypatch.setattr(precommit, "ROOT", tmp_path)
    monkeypatch.setattr(precommit, "_run", lambda command: commands.append(command) or 0)

    assert precommit.main(["precommit.py", target_name]) == 0

    assert commands[-1] == [
        "uv",
        "run",
        "amiga-benchmark-target",
        target_name,
    ]


def test_precommit_can_run_facts_v2_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_name = "amiga_disk_demo"
    targets_dir = tmp_path / "targets"
    target_root = targets_dir / target_name
    target_root.mkdir(parents=True, exist_ok=True)
    (target_root / "manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(precommit, "TARGETS_DIR", targets_dir)
    monkeypatch.setattr(precommit, "ROOT", tmp_path)
    monkeypatch.delenv(precommit.FACTS_V2_GATE_ENV, raising=False)
    commands: list[list[str]] = []
    envs: list[dict[str, str] | None] = []

    def fake_run(command: list[str], *, env: dict[str, str] | None = None) -> int:
        commands.append(command)
        envs.append(env)
        return 0

    monkeypatch.setattr(precommit, "_run", fake_run)

    assert precommit.main(["precommit.py", target_name]) == 0

    assert commands[-2] == [
        precommit.sys.executable,
        "-m",
        "pytest",
        "tests/test_full_reproduction_integration.py",
        "-q",
    ]
    assert envs[-2] is not None
    assert envs[-2][precommit.FULL_REPRO_INTEGRATION_ENV] == "1"
    assert envs[-2][precommit.FULL_REPRO_PROFILE_ENV] == "1"
    assert precommit.FULL_REPRO_FACTS_V2_SOURCE_GATE_ENV not in envs[-2]
    assert commands[-1] == commands[-2]
    assert envs[-1] is not None
    assert envs[-1][precommit.FULL_REPRO_FACTS_V2_SOURCE_GATE_ENV] == "1"


def test_precommit_can_disable_facts_v2_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_name = "amiga_disk_demo"
    targets_dir = tmp_path / "targets"
    target_root = targets_dir / target_name
    target_root.mkdir(parents=True, exist_ok=True)
    (target_root / "manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(precommit, "TARGETS_DIR", targets_dir)
    monkeypatch.setattr(precommit, "ROOT", tmp_path)
    monkeypatch.setenv(precommit.FACTS_V2_GATE_ENV, "0")
    commands: list[list[str]] = []
    monkeypatch.setattr(precommit, "_run", lambda command: commands.append(command) or 0)

    assert precommit.main(["precommit.py", target_name]) == 0

    assert not any("tests/test_full_reproduction_integration.py" in command for command in commands)


def test_benchmark_main_fails_when_any_target_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "amiga_reversing.tools.benchmark_target.benchmark_target",
        lambda target: type(
            "Record",
            (),
            {"target": target, "status": "failed", "elapsed_seconds": 1.0},
        )(),
    )

    assert main(["benchmark_target.py", "demo"]) == 1


def test_benchmark_main_passes_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_benchmark_target(target: str) -> object:
        calls.append(target)
        return type("Record", (), {"target": target, "status": "ok", "elapsed_seconds": 1.0})()

    monkeypatch.setattr("amiga_reversing.tools.benchmark_target.benchmark_target", fake_benchmark_target)

    assert main(["benchmark_target.py", "demo"]) == 0
    assert calls == ["demo"]


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

    seen_write_output: list[bool] = []

    def fake_benchmark_binary_target(target: str, *, write_output: bool) -> object:
        seen.append(target)
        seen_write_output.append(write_output)
        return TargetBenchmark(
            target=target,
            binary=f"bin/{target}",
            command=f"uv run amiga-benchmark-target {target}",
            measured_at="2026-03-26T12:00:00+13:00",
            status="ok",
            elapsed_seconds=1.0,
            benchmark_bytes=1,
            disasm_bytes=1,
            benchmark_version=1,
            platform="amiga-hunk",
            timing={"analysis_seconds": 0.3, "ir_build_seconds": 0.2, "render_seconds": 0.4, "total_seconds": 0.9},
            file=None,
            analysis=None,
            render=None,
            sections=None,
            error=None,
            targets=None,
        )

    monkeypatch.setattr("amiga_reversing.tools.benchmark_target.TARGETS_DIR", targets_dir)
    monkeypatch.setattr("amiga_reversing.tools.benchmark_target._benchmark_binary_target", fake_benchmark_binary_target)

    record = _disk_project_benchmark("amiga_disk_demo")

    assert seen == [
        "amiga_disk_demo__amiga_raw_bootblock",
        "amiga_disk_demo__amiga_hunk_a_first",
        "amiga_disk_demo__amiga_hunk_z_last",
    ]
    assert seen_write_output == [True, True, True]
    assert record.timing == {
        "analysis_seconds": 0.9,
        "ir_build_seconds": 0.6,
        "render_seconds": 1.2,
        "total_seconds": 2.7,
    }
