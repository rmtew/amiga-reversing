from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import macos_listing_source
from amiga_reversing.disasm.c_backend import (
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import read_macos_hfs_image_bytes
from amiga_reversing.disasm.macos_listing_source import (
    build_macos_code_listing_source,
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


def test_020_006_macos_listing_requires_shared_executable_ranges(monkeypatch: pytest.MonkeyPatch) -> None:
    project = get_project(MACOS_EXAMPLE_PROJECT_ID)
    monkeypatch.setattr(macos_listing_source, "read_macos_hfs_image_bytes", lambda path: b"image")
    monkeypatch.setattr(
        macos_listing_source,
        "extract_macos_hfs_code_resource_bytes_with_c_backend",
        lambda image_data, hfs_path, resource_id: b"\x4e\x75",
    )
    monkeypatch.setattr(
        macos_listing_source,
        "inspect_macos_hfs_code_summary_with_c_backend",
        lambda image_data, hfs_path: {
            "selected_code": {"name": "Main"},
            "resource_fork": {"code_resources": [{"id": 1, "name": "Main"}]},
            "file": {},
        },
    )

    with pytest.raises(ValueError, match="shared executable ranges"):
        build_macos_code_listing_source(project)


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
    assert ";     candidate_code: start=40 end=29024 entrypoint=True" in asm_text
    assert "fact=macos.code_resource.movea_stack_a0.boundary.candidate status=candidate" in asm_text
    assert "; CODE resource coverage" in asm_text
    assert ";   CODE 0 unknown: status=metadata-only" in asm_text
    assert ";   CODE 1 Main: status=rendered" in asm_text
    assert ";   CODE 2 FPOpTable: status=partial" in asm_text
    assert ";   CODE 19 SetupArgV: status=deferred" in asm_text
    assert "; CODE segment/routine map" in asm_text
    assert "fact=macos.code_resource.segment_jump_table_span.accepted status=validated" in asm_text
    assert "fact=macos.code_resource.jump_table.routine_offsets.candidate status=candidate" in asm_text
    assert "; CODE resource detail subviews" in asm_text
    assert ";   CODE 0 unknown: role=code0_metadata" in asm_text
    assert "listing: kind=metadata available=False" in asm_text
    assert "reason=CODE 0 is jump-table/application metadata, not ordinary m68k code" in asm_text
    assert ";     jump_table_rows:" in asm_text
    assert "layout_fact=macos.jump_table.entries.accepted layout_status=validated" in asm_text
    assert "target_fact=macos.code_resource.jump_table.routine_offsets.candidate target_status=candidate" in asm_text
    assert ";   CODE 1 Main: role=code_segment" in asm_text
    assert "listing: kind=full_listing available=True route=listing" in asm_text
    assert "listing: kind=candidate_preview available=True route=code_preview" in asm_text
    assert "listing: kind=structured_placeholder available=False" in asm_text
    assert ";     previews:" in asm_text
    assert "candidate_code_preview: start=" in asm_text
    assert "range=candidate_code fact=macos.code_resource.movea_stack_a0.boundary.candidate" in asm_text
    assert "bounded=True" in asm_text
    assert "row: offset=" in asm_text
    assert "decode=decoded row_kind=instruction" in asm_text
    assert "accepted_segment_metadata" in asm_text
    assert "candidate_routine_entry" in asm_text
    assert "status=candidate parser_use=candidate_only" in asm_text
    assert ";   orphan_ranges:" in asm_text
    assert "candidate_data_island: start=4 end=40" in asm_text
    assert "fact=macos.code_resource.orphan_layout_ranges.candidate status=candidate" in asm_text
    assert ";   relocation_fixups:" in asm_text
    assert "fact=macos.segment_loader.relocation_fixups.deferred parser_use=deferred_only" in asm_text
    assert not any(
        "macos.code_resource.movea_stack_a0.boundary.candidate" in line and "accepted_parser_output" in line
        for line in asm_text.splitlines()
    )
    assert not any(
        "macos.segment_loader.relocation_fixups.deferred" in line and "accepted_parser_output" in line
        for line in asm_text.splitlines()
    )
    assert "no candidate preview range; classifier deferred byte-entry evidence" in asm_text
    assert "missing_m68k_movea_l_stack_to_a0_entry" in asm_text
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


def test_committed_macos_asm_artifact_covers_every_code_resource() -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    if not NDIF2RAW_PATH.exists():
        pytest.skip("ndif2raw provider is not available")
    asm_path = Path.cwd() / MACOS_EXAMPLE_ASM_RELPATH
    if not asm_path.exists():
        pytest.skip("committed Mac OS example asm artifact is not available")

    summary = inspect_macos_hfs_code_summary_with_c_backend(
        read_macos_hfs_image_bytes(IMAGE_PATH),
        "MPW-GM/MPW/Tools/Asm",
    )
    expected = summary["resource_fork"]["code_resources"]
    asm_lines = asm_path.read_text(encoding="utf-8").splitlines()
    coverage_start = asm_lines.index("; CODE resource coverage")
    segment_map_start = asm_lines.index("; CODE segment/routine map")
    detail_start = asm_lines.index("; CODE resource detail subviews")
    non_code_start = asm_lines.index("; Non-CODE resource placeholders")
    coverage_lines = [
        line for line in asm_lines[coverage_start:segment_map_start] if line.startswith(";   CODE ") and "status=" in line
    ]
    detail_lines = [
        line
        for line in asm_lines[detail_start:non_code_start]
        if line.startswith(";   CODE ") and "role=" in line and "payload_size=" in line
    ]

    assert len(coverage_lines) == len(expected)
    assert len(detail_lines) == len(expected)
    for resource in expected:
        prefix = f";   CODE {resource['id']} "
        assert any(line.startswith(prefix) for line in coverage_lines), prefix
        assert any(line.startswith(prefix) for line in detail_lines), prefix


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
    assert macos["classified_range"]["load_offset"] == 40
    assert macos["classified_range"]["role"] == "candidate_code"
    assert macos["classified_range"]["fact_status"] == "candidate"
