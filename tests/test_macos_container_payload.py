from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.macos_container_payload import (
    build_macos_container_payload,
    import_macos_resource_code_file,
)
from amiga_reversing.disasm.projects import (
    ProjectKind,
    ProjectRecord,
    initialize_project_metadata,
)

IMAGE_PATH = Path("resources/platform_macos/MPW-GM.img.bin")


def _container_project(target_dir: Path) -> ProjectRecord:
    return ProjectRecord(
        id="macos_hfs_mpw_gm",
        name="macos_hfs_mpw_gm",
        kind=ProjectKind.MACOS,
        target_dir=str(target_dir),
        output_path=None,
        binary_path="resources/platform_macos/MPW-GM.img.bin",
        ready=True,
        last_opened=None,
        manifest_path=None,
        target_count=0,
        source_path="resources/platform_macos/MPW-GM.img.bin",
        disk_type="HFS",
        parent_project_id=None,
        target_type="macos_hfs_container",
        created_at="2026-05-21T00:00:00+00:00",
        updated_at="2026-05-21T00:00:00+00:00",
        origin={"kind": "macos_mpw_fixture", "source_image": "resources/platform_macos/MPW-GM.img.bin"},
    )


def test_macos_container_payload_lists_hfs_resources(tmp_path: Path) -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    parent_dir = tmp_path / "targets" / "macos_hfs_mpw_gm"
    child_dir = parent_dir / "targets" / "macos_file_mpw_tools_asm"
    child_dir.mkdir(parents=True)
    initialize_project_metadata(parent_dir, origin=_container_project(parent_dir).origin)
    initialize_project_metadata(
        child_dir,
        origin={
            "kind": "macos_hfs_resource_code_file",
            "parent_project_id": "macos_hfs_mpw_gm",
            "source_image": "resources/platform_macos/MPW-GM.img.bin",
            "hfs_path": "MPW-GM/MPW/Tools/Asm",
            "resource_type": "CODE",
            "selected_code_resource_id": 1,
        },
    )

    payload = build_macos_container_payload(_container_project(parent_dir), project_root=Path.cwd())
    asm_file = next(file for file in payload["files"] if file["path"] == "MPW-GM/MPW/Tools/Asm")

    assert payload["kind"] == "macos_hfs_container"
    assert asm_file["finder_type"] == "MPST"
    assert "macos_hfs_resource_code_file" in asm_file["supported_imports"]
    assert asm_file["imported_target_id"] == "macos_hfs_mpw_gm__macos_file_mpw_tools_asm"
    assert any(resource["type"] == "CODE" for resource in asm_file["resource_fork"]["resources"])


def test_macos_container_import_writes_child_source_descriptor(tmp_path: Path) -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    parent_dir = tmp_path / "targets" / "macos_hfs_mpw_gm"
    parent_dir.mkdir(parents=True)
    initialize_project_metadata(parent_dir, origin=_container_project(parent_dir).origin)

    result = import_macos_resource_code_file(
        _container_project(parent_dir),
        hfs_path="MPW-GM/MPW/Tools/Asm",
        selected_code_resource_id=1,
        project_root=Path.cwd(),
    )
    child_dir = parent_dir / "targets" / "macos_file_mpw_tools_asm"
    source_descriptor = json.loads((child_dir / "source_binary.json").read_text(encoding="utf-8"))

    assert result["target_id"] == "macos_hfs_mpw_gm__macos_file_mpw_tools_asm"
    assert source_descriptor["kind"] == "macos_code_resource"
    assert source_descriptor["hfs_path"] == "MPW-GM/MPW/Tools/Asm"
    assert source_descriptor["parent_project_id"] == "macos_hfs_mpw_gm"
    assert (child_dir / "macos_resource_inventory.json").exists()
