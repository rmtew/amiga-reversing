"""Synthetic native export fixtures verified as complete files by both assemblers."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm import source_export
from amiga_reversing.disasm.binary_source import BinarySourceKind, HunkFileBinarySource
from amiga_reversing.disasm.c_backend import (
    assemble_platform_source_text_with_c_backend,
)
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    build_target_identity,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, ProjectPaths
from amiga_reversing.disasm.reproduction import run_source_assembly_phase
from amiga_reversing.disasm.source_package import (
    materialize_source_package,
    source_package_zip,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata

pytestmark = pytest.mark.c_backend


@pytest.fixture
def native_target(tmp_path: Path, monkeypatch):
    if not (PROJECT_ROOT / "src/build/platform_file_lib.dll").exists():
        pytest.skip("Native backend unavailable; run make")
    binary = tmp_path / "fixture.hunk"
    original, _ = assemble_platform_source_text_with_c_backend(
        "amiga-hunk", """    SECTION code,code
start:
    lea.l interior.l,a0
    lea.l pointers.l,a1
    nop
    rts
    SECTION data,data
bitmap:
    dcb.b 4096,$a5
interior:
    dcb.b 4096,$a5
sample:
    dcb.b 512,$7e
second_bitmap:
    dcb.b 8192,$b6
palette:
    dc.w $0123,$0456,$0789,$0abc
pointers:
    dc.l bitmap+4096
unknown:
    dc.l $12345678,$00f00000
    dcb.b 256,$ef
""".replace("dcb.b 8192,$b6", "\n".join(
            "    dc.b " + ",".join(f"${(index * 73 + byte * 11) % 256:02x}" for byte in range(16))
            for index in range(512)
        )), output_path=binary, project_root=PROJECT_ROOT,
    )
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE, path=binary, display_path=str(binary),
        analysis_cache_path=target_dir / "binary.analysis",
    )
    (target_dir / "source_binary.json").write_text(json.dumps({"kind": "hunk_file", "path": str(binary)}))
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    records = [{"record": "manual_action_log_header", "version": 1,
                "target_identity": build_target_identity(binary_source)}]
    for sequence, (role, start, end, unit) in enumerate([
        ("bitmap", 0, 8192, "byte"), ("sound_sample", 8192, 8704, "byte"),
        ("bitmap", 8704, 16896, "byte"),
        ("palette", 16896, 16904, "word"), ("pointer_table", 16904, 16908, "pointer"),
    ], 1):
        records.append({
            "record": "manual_action", "action_id": f"a{sequence}", "sequence": sequence,
            "created_at": "2026-05-18T00:00:01+00:00", "kind": "create_manual_seed",
            "seed": {"seed_id": f"{role}-{sequence}", "kind": "data", "mode": "required", "hunk": 1,
                     "addr": start, "end": end, "data_role": role, "unit": unit},
        })
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text("".join(json.dumps(r) + "\n" for r in records))
    paths = ProjectPaths("asset-fixture", "binary", target_dir, None, binary_source)
    monkeypatch.setattr(source_export, "resolve_project_paths", lambda *args, **kwargs: paths)
    return original, paths


def test_native_binary_asset_export_complete_file_exact_both_assemblers(native_target, tmp_path: Path):
    original, _paths = native_target
    plain = source_export.source_export_payload("asset-fixture", project_root=PROJECT_ROOT)
    exported = source_export.source_export_payload(
        "asset-fixture", project_root=PROJECT_ROOT, binary_assets=True, minimum_asset_size=256,
    )
    assert exported["status"] == "ok", exported
    package = exported["package"]
    assets = [row for row in package["manifest"]["files"] if row["kind"] == "asset"]
    assert len(assets) >= 2
    assert {row["classification"] for row in assets} == {"bitmap", "sound_sample"}
    assert all(row["source_section_index"] == 1 for row in assets)
    assert all(row["source_offset"] + row["size"] <= 16896 for row in assets)
    text = exported["source_text"]
    assert "\tlea.l " in text and "\trts" in text
    assert "data_role=palette" in text and "data_role=pointer_table" in text
    assert "loc_1_00001000:" in text
    assert "lea.l loc_1_00001000.l,a0" in text
    assert "dc.l loc_1_00001000" in text
    assert all(not row["source_offset"] <= 4096 < row["source_offset"] + row["size"] for row in assets)
    assert "$12345678" in text or "$12,$34,$56,$78" in text
    assert len(text.encode()) < len(plain["source_text"].encode()) * 0.65
    again = source_export.source_export_payload(
        "asset-fixture", project_root=PROJECT_ROOT, binary_assets=True, minimum_asset_size=256,
    )
    assert source_package_zip(package) == source_package_zip(again["package"])
    framework = run_source_assembly_phase(
        backend="amiga-hunk", source_text=text, source_package=package,
        include_dir=None, target_cpu="68000", project_root=PROJECT_ROOT,
    )
    assert framework.rebuilt_bytes == original
    executable = os.environ.get("VASM") or str(PROJECT_ROOT / "ext/vasm/vasmm68k_mot")
    if not Path(executable).is_file() and not shutil.which(executable):
        pytest.skip("Real vasm unavailable; set VASM")
    entry = materialize_source_package(package, tmp_path / "portable-package")
    output = tmp_path / "vasm.hunk"
    completed = subprocess.run(
        [executable, "-Fhunkexe", "-kick1hunks", "-m68000", "-no-opt", "-quiet", "-nosym", "-o", str(output), str(entry)],
        cwd=entry.parent, capture_output=True, text=True, timeout=20,
    )
    assert completed.returncode == 0, completed.stderr[:2000]
    assert output.read_bytes() == original
    print(f"original={len(original)} plain_source={len(plain['source_text'].encode())} "
          f"package_source={len(text.encode())} assets={len(assets)} "
          f"asset_bytes={sum(row['size'] for row in assets)} both_assemblers=full_file_exact")


def test_unclassified_large_regions_are_not_externalized(native_target):
    _original, paths = native_target
    (paths.target_dir / MANUAL_ACTION_LOG_FILE_NAME).unlink()
    plain = source_export.source_export_payload("asset-fixture", project_root=PROJECT_ROOT)
    packaged = source_export.source_export_payload(
        "asset-fixture", project_root=PROJECT_ROOT, binary_assets=True, minimum_asset_size=1,
    )
    assert packaged["status"] == plain["status"]
    if packaged["status"] == "ok":
        assert all(record["kind"] == "source" for record in packaged["package"]["manifest"]["files"])
        assert packaged["source_text"] == plain["source_text"]
    else:
        assert "package" not in packaged


def test_explicit_bitmap_classification_cannot_hide_relocations(native_target):
    _original, paths = native_target
    log = paths.target_dir / MANUAL_ACTION_LOG_FILE_NAME
    records = [json.loads(line) for line in log.read_text().splitlines()]
    for record in records:
        if record.get("seed", {}).get("data_role") == "pointer_table":
            record["seed"].update(data_role="bitmap", unit="byte")
    log.write_text("".join(json.dumps(record) + "\n" for record in records))
    exported = source_export.source_export_payload(
        "asset-fixture", project_root=PROJECT_ROOT, binary_assets=True, minimum_asset_size=1,
    )
    assert exported["status"] == "ok", exported
    for record in exported["package"]["manifest"]["files"]:
        if record["kind"] == "asset" and record["source_section_index"] == 1:
            assert not record["source_offset"] <= 16904 < record["source_offset"] + record["size"]
    framework = run_source_assembly_phase(
        backend="amiga-hunk", source_text=exported["source_text"], source_package=exported["package"],
        include_dir=None, target_cpu="68000", project_root=PROJECT_ROOT,
    )
    assert framework.rebuilt_bytes == _original


def test_package_bundles_nested_includes_and_moves_without_sdk(tmp_path: Path):
    from amiga_reversing.disasm.source_package import (
        build_source_package,
        collect_package_includes,
    )

    sdk = tmp_path / "sdk"
    (sdk / "platform").mkdir(parents=True)
    (sdk / "platform/outer.i").write_text('    INCLUDE "platform/inner.i"\n')
    (sdk / "platform/inner.i").write_text("ASSET_TAG equ $1234\n")
    text = '    INCLUDE "platform/outer.i"\n    SECTION payload,data\n    dc.w ASSET_TAG\n    INCBIN "assets/data.bin"\n'
    package = build_source_package(
        {"filename": "main.s", "source_text": text, "target": "fixture", "assembler_profile": "vasm",
         "metadata_hash": "metadata", "target_identity_sha256": "target"},
        [{"path": "assets/data.bin", "data_hex": "abcd", "size": 2}], 1,
        includes=collect_package_includes(text, sdk),
    )
    sdk.rename(tmp_path / "sdk-unavailable")
    framework = run_source_assembly_phase(
        backend="amiga-raw", source_text=text, source_package=package,
        include_dir=sdk, target_cpu="68000", project_root=PROJECT_ROOT,
    )
    assert framework.rebuilt_bytes == bytes.fromhex("1234abcd")
    executable = os.environ.get("VASM") or str(PROJECT_ROOT / "ext/vasm/vasmm68k_mot")
    if not Path(executable).is_file() and not shutil.which(executable):
        pytest.skip("Real vasm unavailable; set VASM")
    entry = materialize_source_package(package, tmp_path / "moved-package")
    output = tmp_path / "moved.bin"
    result = subprocess.run(
        [executable, "-Fbin", "-quiet", "-o", str(output), str(entry)],
        cwd=entry.parent, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr[:2000]
    assert output.read_bytes() == framework.rebuilt_bytes
