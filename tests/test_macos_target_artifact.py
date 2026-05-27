from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from amiga_reversing.disasm import macos_listing_source
from amiga_reversing.disasm.binary_source import MacosCodeResourceSource
from amiga_reversing.disasm.c_backend import (
    build_macos_code_bytes_listing_artifact_profile,
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import read_macos_hfs_image_bytes
from amiga_reversing.disasm.macos_listing_source import (
    build_macos_code_listing_source,
    build_macos_project_listing_artifact_profile,
)
from amiga_reversing.disasm.macos_project_origin import (
    macos_code_source_descriptor_from_project,
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


def test_021_001_committed_mpw_asm_project_resolves_native_code_source_descriptor() -> None:
    if not (Path.cwd() / MACOS_EXAMPLE_TARGET_RELPATH / ".project.json").exists():
        pytest.skip("committed Mac OS example target is not available")

    project = get_project(MACOS_EXAMPLE_PROJECT_ID)
    descriptor = macos_code_source_descriptor_from_project(project)

    assert descriptor.kind == "macos_code_resource"
    assert descriptor.source_image == (Path.cwd() / "resources/platform_macos/MPW-GM.img.bin").resolve()
    assert descriptor.hfs_path == "MPW-GM/MPW/Tools/Asm"
    assert descriptor.resource_type == "CODE"
    assert descriptor.resource_id == 1
    assert descriptor.address_model == "macos_code_resource_offset"
    assert descriptor.display_path == "resources/platform_macos/MPW-GM.img.bin::MPW-GM/MPW/Tools/Asm::CODE 1"
    assert descriptor.stable_cache_identity == (
        "macos-code-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:CODE:1"
    )


def test_021_001_macos_listing_source_sits_behind_native_descriptor() -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    if not NDIF2RAW_PATH.exists():
        pytest.skip("ndif2raw provider is not available")

    project = get_project(MACOS_EXAMPLE_PROJECT_ID)
    listing_source = build_macos_code_listing_source(project)
    descriptor = cast(dict[str, object], listing_source["source_descriptor"])
    classified_range = cast(dict[str, object], listing_source["classified_range"])

    assert isinstance(descriptor, dict)
    assert descriptor["kind"] == "macos_code_resource"
    assert descriptor["source_image"] == "resources/platform_macos/MPW-GM.img.bin"
    assert descriptor["hfs_path"] == "MPW-GM/MPW/Tools/Asm"
    assert descriptor["resource_type"] == "CODE"
    assert descriptor["resource_id"] == 1
    assert descriptor["address_model"] == "macos_code_resource_offset"
    assert descriptor["cache_identity"] == (
        "macos-code-resource:resources/platform_macos/MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:CODE:1"
    )
    assert classified_range["fact_status"] == "validated"


def test_macos_code_listing_artifact_uses_macos_platform_backend_for_opword_calls() -> None:
    _total_rows, profile, artifact = build_macos_code_bytes_listing_artifact_profile(
        b"\xA9\xF1\x4E\x75",
        display_path="synthetic CODE trap",
    )
    try:
        source_text, source_profile = artifact.source_text_with_profile()
        window, window_profile = artifact.window_payload(start=0, count=8)
    finally:
        artifact.close()

    for observed in (profile, source_profile, window_profile):
        assert observed["backend"] == "macos-code"
        assert observed["source_kind"] == "macos_code_resource"
    assert 'INCLUDE "SegLoad.a"' in source_text
    assert "\t_UnloadSeg\n" in source_text
    assert "\trts\n" in source_text
    assert "dc.w $A9F1" not in source_text
    trap_row = next(row for row in window["rows"] if str(row.get("text") or "").strip() == "_UnloadSeg")
    api_call = trap_row.get("api_call")
    assert isinstance(api_call, dict)
    assert api_call["function"] == "_UnloadSeg"
    assert api_call["note_symbol_name"] == "_UnloadSeg"


def test_021_005_macos_listing_profile_uses_native_descriptor_not_raw_bridge(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "MPW-GM.img.bin"
    image_path.write_bytes(b"fixture")
    calls: dict[str, object] = {}

    class FakeArtifact:
        def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return {"total_rows": 1}, {}

    project = type(
        "Project",
        (),
        {
            "id": "macos_sample",
            "origin": {
                "kind": "macos_mpw_fixture",
                "source_image": image_path.name,
                "hfs_path": "MPW-GM/MPW/Tools/Asm",
                "selected_code_resource_id": 1,
            },
        },
    )()

    def fake_listing_source(project_obj: object, *, project_root: Path) -> dict[str, object]:
        calls["listing_project"] = project_obj
        return {
            "hfs_path": "MPW-GM/MPW/Tools/Asm",
            "fork": "resource",
            "resource_type": "CODE",
            "resource_id": 1,
            "resource_name": "Main",
            "classified_range": {"load_offset": 40, "size": 4},
            "executable_deferred": [],
        }

    def fake_build(binary_source: object, **kwargs: object) -> tuple[int, dict[str, object], FakeArtifact]:
        calls["binary_source"] = binary_source
        calls["project_root"] = kwargs.get("project_root")
        return 1, {"backend": "amiga-raw", "wrapped_backend": "amiga-raw"}, FakeArtifact()

    monkeypatch.setattr(macos_listing_source, "build_macos_code_listing_source", fake_listing_source)
    monkeypatch.setattr(macos_listing_source, "build_listing_artifact_profile_from_binary_source", fake_build)

    _total_rows, profile, artifact = macos_listing_source.build_macos_project_listing_artifact_profile(
        project,
        project_root=tmp_path,
    )

    assert isinstance(calls["binary_source"], MacosCodeResourceSource)
    assert not hasattr(calls["binary_source"], "read_bytes")
    assert profile["backend"] == "macos-code"
    assert profile["source_kind"] == "macos_code_resource"
    assert "wrapped_backend" not in profile
    assert isinstance(artifact, macos_listing_source.MacosCodeListingArtifact)


def test_021_001_macos_code_source_descriptor_fails_closed_for_invalid_origin() -> None:
    project = get_project(MACOS_EXAMPLE_PROJECT_ID)
    bad_project = type(
        "BadProject",
        (),
        {"id": project.id, "origin": {"kind": "macos_mpw_fixture", "selected_code_resource_id": 1}},
    )()

    with pytest.raises(ValueError, match="source_image"):
        macos_code_source_descriptor_from_project(bad_project)


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
    assert asm_text.index('\tINCLUDE "SegLoad.a"\n') < asm_text.index("CODE_0:")
    assert "CODE_0:" in asm_text
    assert "CODE_27:" in asm_text
    assert "CODE_0_above_a5_size:" in asm_text
    assert "CODE_0_jump_table:" in asm_text
    assert "CODE_0_jump_table_entry_0:" in asm_text
    assert "\tmove.w #27,-(a7)" in asm_text
    assert "\t_LoadSeg\n" in asm_text
    assert "\tdc.w $A9F0" not in asm_text
    assert "\tdc.l CODE_1_loc_0000601e-CODE_1" in asm_text
    assert "\tdc.l CODE_1_loc_0000003e-CODE_1" in asm_text
    assert "\tdc.l $0000601E" not in asm_text
    assert "generated_xref source=CODE_0_jump_table_entry_0" not in asm_text
    assert "candidate_target target_section=CODE_unknown" not in asm_text
    assert "CODE_27_routine_candidate_000000cc:" not in asm_text
    assert "CODE_27_loc_00000004:" in asm_text
    assert "incoming_CODE0_xrefs:" not in asm_text
    assert "raw_entry_bytes=" not in asm_text
    assert "raw_byte_gap" not in asm_text
    assert "target_section=CODE_1 target_resource_id=1" not in asm_text
    assert "target=CODE_1_loc_0000003e link_status=linked_candidate" not in asm_text
    assert "CODE_1_loc_0000003e:" in asm_text
    assert "CODE_1_routine_candidate_0000003e:" not in asm_text
    assert "target_section=CODE_1 target_resource_id=1 routine_offset=0 status=validated" not in asm_text
    assert not any(
        "macos.code_resource.movea_stack_a0.boundary.candidate" in line and "accepted_parser_output" in line
        for line in asm_text.splitlines()
    )
    assert not any(
        "macos.segment_loader.relocation_fixups.deferred" in line and "accepted_parser_output" in line
        for line in asm_text.splitlines()
    )
    assert "no candidate preview range; classifier deferred byte-entry evidence" not in asm_text
    assert "missing_m68k_movea_l_stack_to_a0_entry" not in asm_text
    assert ";   source_rows:" not in asm_text
    assert "placeholder_reason: semantic CODE disassembly remains deferred" not in asm_text
    assert "CODE_2_loc_00000028:" in asm_text
    assert "\tmovea.l (a7)+,a0\n" in asm_text
    assert "CODE_1_loc_00000028:" in asm_text
    assert "\tmovea.l (a7)+,a0\n" in asm_text
    assert "CODE_1_candidate_code_00000028:\n\tdc.b $20,$5F" not in asm_text
    assert "; CODE 1 Main restored source follows." not in asm_text
    assert "; Source quality gate" not in asm_text
    assert "this is not semantic source closeout" not in asm_text
    assert "residual semantic_decode_gap payload[62..29024)" not in asm_text
    assert "residual candidate_unvisited_entry_pattern payload[" not in asm_text
    assert asm_text.count('\tINCLUDE "SegLoad.a"\n') == 1
    assert "\t_UnloadSeg\n" in asm_text
    assert "CODE_1_data_00002038:\n\tdc.b $A9,$F1" not in asm_text
    assert "CODE_1_loc_00000028:" in asm_text
    assert "\tmovea.l (a7)+,a0\n" in asm_text
    assert "\tmove.l a7,d0\n" in asm_text
    assert "\tmovea.l (a7)+,a0\t; payload+" not in asm_text
    assert " bytes=20 5F" not in asm_text
    assert "CODE_1_loc_0000003e:" in asm_text
    assert "CODE_1_semantic_decode_gap_0000003e:" not in asm_text
    assert "CODE_1_loc_0000027e:\n\tdc.b $30,$31,$32,$33" in asm_text
    assert "CODE_1_loc_00000f94:\n\tdc.w CODE_1_loc_00000fb4-CODE_1_loc_00000f94" in asm_text
    assert "CODE_12_data_000009c6:\n\tdc.w $0000" in asm_text
    asm_lines = asm_text.splitlines()
    consecutive_label_pairs = [
        (line, next_line)
        for line, next_line in zip(asm_lines, asm_lines[1:])
        if line.startswith("CODE_")
        and line.endswith(":")
        and next_line.startswith("CODE_")
        and next_line.endswith(":")
        and not line.removeprefix("CODE_").removesuffix(":").isdigit()
    ]
    assert consecutive_label_pairs == [
        ("CODE_0_metadata_00000000:", "CODE_0_above_a5_size:"),
        ("CODE_0_jump_table:", "CODE_0_jump_table_entry_0:"),
    ]
    assert "CODE_1_semantic_string_data_gap_0000027e:" not in asm_text
    assert "CODE_1_semantic_dispatch_table_gap_00000f94:" not in asm_text
    assert "loc_0_" not in asm_text
    assert "CODE_1_loc_00003754(pc,d0.w)" in asm_text
    assert ";       xref code_start_ref payload+" not in asm_text
    assert "CODE_1_candidate_code_00000028:\n\tdc.b $20,$5F" not in asm_text
    assert "residual candidate_code payload[40..29024)" not in asm_text
    assert "candidate_data_island" not in asm_text
    assert "SECTION code,code" not in asm_text
    assert "\tori.b #16,d0" not in asm_text
    assert "CODE_1_metadata_00000000:" in asm_text
    assert "CODE_1_far_model_header:" not in asm_text
    assert "CODE_1_candidate_entry_stub:" not in asm_text
    assert "CODE_1_candidate_body_after_stub:" not in asm_text
    assert "accepted byte-entry proof remains deferred" not in asm_text
    assert "orphan code" not in asm_text.lower()
    assert "; Analysis reports" not in asm_text
    assert "; File forks" not in asm_text
    assert "; Resource fork" not in asm_text
    assert "; CODE resources" not in asm_text
    assert "source_presentation:" not in asm_text
    assert "restored_source_model" not in asm_text
    assert "candidate_target" not in asm_text
    assert "payload[" not in asm_text
    assert " bytes=" not in asm_text
    assert "row: offset=" not in asm_text
    assert asm_text.index("CODE_0:") < asm_text.index("CODE_1:") < asm_text.index("\tmovea.l (a7)+,a0\n")


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
    source_lines = [
        line
        for line in asm_lines
        if line.startswith("; CODE ") and not line.startswith("; CODE source")
    ]

    assert len(source_lines) == len(expected)
    for resource in expected:
        source_prefix = f"; CODE {resource['id']} "
        assert any(line.startswith(source_prefix) for line in source_lines), source_prefix
        source_index = next(index for index, line in enumerate(asm_lines) if line.startswith(source_prefix))
        source_block_end = next(
            (
                index
                for index in range(source_index + 1, len(asm_lines))
                if asm_lines[index].startswith("; CODE ")
            ),
            len(asm_lines),
        )
        source_block = "\n".join(asm_lines[source_index:source_block_end])
        assert f"CODE_{resource['id']}:" in source_block
        assert "\tdc.b " in source_block or "\tdc.w " in source_block or "\tdc.l " in source_block or "\tmove" in source_block


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
        analysis, analysis_profile = artifact.analysis_payload()
        summary, summary_profile = artifact.summary_payload()
        navigation, navigation_profile = artifact.navigation_payload()
        source_text, source_profile = artifact.source_text_with_profile()
        window, window_profile = artifact.window_payload(start=0, count=16)
    finally:
        artifact.close()

    analysis_ranges = cast(list[dict[str, Any]], analysis["executable_ranges"])
    analysis_deferred = cast(list[dict[str, Any]], analysis["executable_deferred"])
    for observed_profile in (
        profile,
        analysis_profile,
        summary_profile,
        navigation_profile,
        source_profile,
        window_profile,
    ):
        assert observed_profile["backend"] == "macos-code"
        assert observed_profile["source_kind"] == "macos_code_resource"
        assert observed_profile.get("wrapped_backend") != "amiga-raw"
    assert summary["total_rows"] > 0
    assert navigation["groups"]
    assert analysis["executable_model"] == "platform_executable_summary_v1"
    assert analysis_ranges[0]["role"] == "code"
    assert analysis_ranges[0]["fact_status"] == "validated"
    assert analysis_ranges[0]["parser_use"] == "accepted_parser_output"
    assert analysis_deferred[0]["fact_status"] == "deferred"
    assert "; Classic Mac OS CODE resource listing" in source_text
    assert "; source kind: macos_code_resource" in source_text
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
    assert macos["classified_range"]["role"] == "code"
    assert macos["classified_range"]["fact_status"] == "validated"
