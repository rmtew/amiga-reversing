"""An explicit byte rename must preserve an adjacent native LONG declaration."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_action
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_c_backend import _requires_c_backend_dlls

pytestmark = pytest.mark.c_backend


def _vasm(tmp_path: Path, name: str, text: str) -> bytes:
    source_path = tmp_path / f"{name}.s"
    output_path = tmp_path / f"{name}.bin"
    source_path.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [str(PROJECT_ROOT / "tools" / "vasmm68k_mot.exe"), "-Fbin", "-quiet",
         "-o", str(output_path), str(source_path)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return output_path.read_bytes()


def _render(target_dir: Path, source: RawBinarySource) -> str:
    with effective_metadata_file(target_dir) as metadata_path:
        return c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT,
        )


def test_explicit_byte_rsset_rename_preserves_neighbor_and_exact_bytes(tmp_path: Path) -> None:
    _requires_c_backend_dlls()
    original = _vasm(tmp_path, "original", "\n".join([
        "    SECTION section,code",
        "    move.b $0201(a6),d0",
        "    movea.l $0202(a6),a0",
        "    rts", "",
    ]))
    binary_path = tmp_path / "fixture.bin"
    binary_path.write_bytes(original)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY, path=binary_path,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0,
        entrypoint=0, code_start_offset=0, display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis",
    )
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    baseline = _render(tmp_path, source)
    assert "app_0201 RS.B 1\napp_0202 RS.L 1\n" in baseline

    kind, payload = target_catalog_manual_payload("target.rsset_region.rename", {
        "offset": 0x201, "size": 1, "symbol": "phase_byte", "storage_kind": "scalar",
    })
    action = append_manual_action(
        tmp_path, kind=ManualActionKind(kind), payload=payload, binary_source=source,
    )
    assert action["rsset_layout_region"]["size"] == 1
    renamed = _render(tmp_path, source)
    assert "phase_byte RS.B 1\napp_0202 RS.L 1\n" in renamed
    assert "phase_byte RS.B 4\n" not in renamed
    assert "\tmove.b phase_byte(a6),d0\n" in renamed
    assert "\tmovea.l app_0202(a6),a0\n" in renamed
    for name, rendered in (("baseline", baseline), ("renamed", renamed)):
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
            "amiga-raw", rendered, project_root=PROJECT_ROOT,
        )
        assert rebuilt == original
        assert _vasm(tmp_path, name, rendered) == original
