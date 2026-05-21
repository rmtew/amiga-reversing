from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.macos_listing_source import (
    build_macos_project_listing_artifact_profile,
)
from amiga_reversing.disasm.macos_target_artifact import (
    MACOS_EXAMPLE_ASM_RELPATH,
    MACOS_EXAMPLE_PROJECT_ID,
    MACOS_EXAMPLE_SUBTARGET_ID,
    MACOS_EXAMPLE_SUBTARGET_RELPATH,
    MACOS_EXAMPLE_TARGET_RELPATH,
    render_macos_example_asm,
)
from amiga_reversing.disasm.projects import ProjectKind, get_project

IMAGE_PATH = Path("resources/platform_macos/MPW-GM.img.bin")
NDIF2RAW_PATH = Path("ext/tools/ndif2raw/ndif2raw.exe")


def test_committed_macos_example_target_loads_through_project_record() -> None:
    if not (Path.cwd() / MACOS_EXAMPLE_TARGET_RELPATH / ".project.json").exists():
        pytest.skip("committed Mac OS example target is not available")

    project = get_project(MACOS_EXAMPLE_PROJECT_ID)

    assert project.kind is ProjectKind.MACOS
    assert project.target_type == "macos_hfs_resource_code_file"
    assert project.origin["kind"] == "macos_mpw_fixture"
    assert project.origin["hfs_path"] == "MPW-GM/MPW/Tools/Asm"
    assert project.origin["selected_code_resource_id"] == 1


def test_committed_macos_subtarget_metadata_and_asm_shape() -> None:
    subtarget_metadata_path = Path.cwd() / MACOS_EXAMPLE_SUBTARGET_RELPATH / ".project.json"
    asm_path = Path.cwd() / MACOS_EXAMPLE_ASM_RELPATH
    if not subtarget_metadata_path.exists() or not asm_path.exists():
        pytest.skip("committed Mac OS example subtarget is not available")

    metadata = json.loads(subtarget_metadata_path.read_text(encoding="utf-8"))
    asm_text = asm_path.read_text(encoding="utf-8")

    assert metadata["origin"]["parent_project_id"] == MACOS_EXAMPLE_PROJECT_ID
    assert metadata["origin"]["selected_code_resource_name"] == "Main"
    assert MACOS_EXAMPLE_SUBTARGET_ID in str(MACOS_EXAMPLE_SUBTARGET_RELPATH)
    assert "; Finder type: MPST" in asm_text
    assert "; HFS path: MPW-GM/MPW/Tools/Asm" in asm_text
    assert "; CODE 0 jump-table/application metadata" in asm_text
    assert "CODE 1 Main:" in asm_text
    assert "; Non-CODE resource placeholders" in asm_text
    assert "; CODE 1 Main listing follows." in asm_text
    assert ";   code_entry_offset: 40" in asm_text
    assert ";     data: start=4 end=40 entrypoint=False evidence=prefix_before_stack_entry" in asm_text
    assert "; Classic Mac OS CODE resource listing" in asm_text
    assert "; resource: CODE 1 Main" in asm_text
    assert "movea.l (a7)+,a0" in asm_text
    assert "SECTION code,code" not in asm_text
    assert "\tori.b #16,d0" not in asm_text


def test_committed_macos_asm_artifact_matches_renderer() -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    if not NDIF2RAW_PATH.exists():
        pytest.skip("ndif2raw provider is not available")
    asm_path = Path.cwd() / MACOS_EXAMPLE_ASM_RELPATH
    if not asm_path.exists():
        pytest.skip("committed Mac OS example asm artifact is not available")

    assert asm_path.read_text(encoding="utf-8") == render_macos_example_asm()


def test_macos_listing_artifact_uses_macos_source_and_row_provenance() -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    if not NDIF2RAW_PATH.exists():
        pytest.skip("ndif2raw provider is not available")
    if not (Path.cwd() / MACOS_EXAMPLE_TARGET_RELPATH / ".project.json").exists():
        pytest.skip("committed Mac OS example target is not available")

    project = get_project(MACOS_EXAMPLE_PROJECT_ID)
    _total_rows, profile, artifact = build_macos_project_listing_artifact_profile(project)
    try:
        source_text, source_profile = artifact.source_text_with_profile()
        window, _window_profile = artifact.window_payload(start=0, count=16)
    finally:
        artifact.close()

    assert profile["backend"] == "amiga-raw"
    assert source_profile["backend"] == "macos-code"
    assert source_profile["wrapped_backend"] == "amiga-raw"
    assert "; Classic Mac OS CODE resource listing" in source_text
    assert "; HFS path: MPW-GM/MPW/Tools/Asm" in source_text
    assert "SECTION code,code" not in source_text
    assert "\tori.b #16,d0" not in source_text
    assert any(str(row.get("text") or "").strip() == "movea.l (a7)+,a0" for row in window["rows"])
    assert all(str(row.get("text") or "").strip() != "SECTION code,code" for row in window["rows"])
    first_instruction = next(row for row in window["rows"] if str(row.get("text") or "").strip() == "movea.l (a7)+,a0")
    macos = first_instruction["macos"]
    assert macos["hfs_path"] == "MPW-GM/MPW/Tools/Asm"
    assert macos["fork"] == "resource"
    assert macos["resource_type"] == "CODE"
    assert macos["resource_id"] == 1
    assert macos["resource_name"] == "Main"
    assert macos["classified_range"]["start"] == 40
