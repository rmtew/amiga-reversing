from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from amiga_reversing.disasm import macos_listing_source
from amiga_reversing.disasm.binary_source import MacosCodeResourceSource
from amiga_reversing.disasm.c_backend import (
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
    assert classified_range["fact_status"] == "candidate"


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
    assert "; CODE 0 jump-table/application metadata" in asm_text
    assert "CODE 1 Main:" in asm_text
    assert "; Non-CODE resource placeholders" in asm_text
    assert "; CODE source body sections" in asm_text
    assert "; CODE 1 Main byte-real source follows." in asm_text
    assert ";   source_kind: macos_code_resource" in asm_text
    assert ";   backend: macos-code" in asm_text
    assert ";   selected_code_entry_offset: 40" in asm_text
    assert "role=metadata span=0..40 status=validated parser_use=accepted_parser_output reason=far_model_segment_header" in asm_text
    assert "role=candidate_code span=40..29024 status=candidate parser_use=candidate_only" in asm_text
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
    assert "listing: kind=semantic_listing available=True route=listing" in asm_text
    assert "listing: kind=candidate_preview available=True route=code_preview" not in asm_text
    assert "listing: kind=structured_placeholder available=False" in asm_text
    assert "candidate_code_preview: start=" not in asm_text
    assert "candidate_code payload[" in asm_text
    assert "bounded=True" not in asm_text
    assert "row: offset=" not in asm_text
    assert "decode=decoded row_kind=instruction" not in asm_text
    assert "accepted_segment_metadata" in asm_text
    assert "candidate_routine_entry" in asm_text
    assert "status=candidate parser_use=candidate_only" in asm_text
    assert ";   orphan_ranges:" not in asm_text
    assert "candidate_data_island: start=4 end=40" not in asm_text
    assert ";   relocation_fixups:" not in asm_text
    assert "; Executable resource placeholders" in asm_text
    assert "executable_resource_placeholder: type=CURS" in asm_text
    assert "reference_site=resource_type_inventory" in asm_text
    assert "source_context=unlinked" in asm_text
    assert "link_status=unlinked" in asm_text
    assert "identity=macos-resource:" in asm_text
    assert ";   restored_source_model:" in asm_text
    assert asm_text.count("source_presentation: kind=c_owned_restored_source_packet status=covered") >= 28
    assert "model=restored_source_model_v1 round_trip_required=false" in asm_text
    assert asm_text.count("model=restored_source_model_v1 round_trip_required=false") >= 28
    assert asm_text.count("coverage ok=true gaps=0 overlaps=0 unknown_detail=0") >= 28
    assert asm_text.count("source_reference_records:") >= 28
    assert "ownership_ranges:" in asm_text
    assert "role=candidate_code" in asm_text
    assert "kind=segment_loader_fixup_placeholder" in asm_text
    assert "kind=code0_dispatch_reference" in asm_text
    assert "target=CODE:27" in asm_text
    assert "target=CODE:1" not in asm_text
    assert "kind=code0_routing_table" in asm_text
    assert "kind=a5_world_context_placeholder" in asm_text
    assert "a5_world status=deferred" in asm_text
    assert "macos_code_CODE_0:" in asm_text
    assert "macos_code_CODE_27:" in asm_text
    assert "macos_CODE_0_above_a5_size:" in asm_text
    assert "macos_CODE_0_jump_table:" in asm_text
    assert "macos_CODE_0_jump_table_entry_0:" in asm_text
    assert "\tmove.w #27,-(a7)" in asm_text
    assert "\tdc.l $0000601E" in asm_text
    assert "jump_table payload[16..2784) entry_size=8 entry_count=346 status=validated" in asm_text
    assert (
        "candidate_target target_section=macos_code_CODE_27 target_resource_id=27 "
        "routine_offset=0 status=candidate parser_use=candidate_only"
    ) in asm_text
    assert (
        "generated_xref source=macos_CODE_0_jump_table_entry_0 "
        "target=macos_code_CODE_27_routine_candidate_000000cc link_status=linked_candidate"
    ) in asm_text
    assert "macos_code_CODE_27_routine_candidate_000000cc:" in asm_text
    assert (
        "from=macos_CODE_0_jump_table_entry_0 source_payload=16 target_payload=204 "
        "status=candidate parser_use=candidate_only"
    ) in asm_text
    assert "raw_entry_bytes=" not in asm_text
    assert "raw_byte_gap: CODE 0 row bytes are not exposed" not in asm_text
    assert "target_section=macos_code_CODE_1 target_resource_id=1" in asm_text
    assert "target=macos_code_CODE_1_routine_candidate_0000003e link_status=linked_candidate" in asm_text
    assert "target_section=macos_code_CODE_1 target_resource_id=1 routine_offset=0 status=validated" not in asm_text
    code0_start = asm_text.index(";   CODE 0 unknown: role=code0_metadata")
    code1_start = asm_text.index(";   CODE 1 Main: role=code_segment")
    code0_block = asm_text[code0_start:code1_start]
    assert "kind=code0_routing_table" in code0_block
    assert "kind=segment_loader_fixup_placeholder" not in code0_block
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
    assert ";   byte_real_source:" in asm_text
    assert "macos_code_CODE_2_loc_00000176:" in asm_text
    assert "\tmovea.l (a7)+,a0\n" in asm_text
    assert "macos_code_CODE_1_loc_00000028:" in asm_text
    assert "\tmovea.l (a7)+,a0\n" in asm_text
    assert "macos_code_CODE_1_candidate_code_00000028:\n\tdc.b $20,$5F" not in asm_text
    assert "; CODE 1 Main byte-real source follows." in asm_text
    assert "; Source quality gate" in asm_text
    assert ";   status: byte_real_baseline" in asm_text
    assert ";   semantic_closeout_status: blocked_residual_decode_gaps" in asm_text
    assert ";   baseline_status: passed_with_deferred_semantics" in asm_text
    assert "this is not semantic source closeout" in asm_text
    assert ";     semantic_disassembly_status: residual_decode_gaps_present" in asm_text
    assert ";     label_xref_status: generated_labels_and_xrefs_present" in asm_text
    assert ";     no_fake_disassembly: True" in asm_text
    assert ";     no_vague_orphan_bucket: True" in asm_text
    assert ";     range_ownership_complete: True" in asm_text
    assert ";     reachable_code_evidence_recorded: True" in asm_text
    assert ";     residuals_explicit: True" in asm_text
    assert ";     stable_labels_present: True" in asm_text
    assert ";     accepted byte-entry proof" in asm_text
    assert ";     decoded Segment Loader relocation/fixup semantics" in asm_text
    assert ";     A5 lifetime proof" in asm_text
    assert ";   non_blocking_for_semantic_disassembly:" in asm_text
    assert ";     missing human semantic names" in asm_text
    assert ";     deferred A5 lifetime proof" in asm_text
    assert (
        ";     CODE 1: section=macos-code-CODE-1 ownership=candidate_code,metadata "
        "coverage=True labels=120 xrefs=1902 instructions=7818 body_spans=1 byte_real_only_body=False "
        "reachable_evidence=117 residuals=138"
    ) in asm_text
    assert "residual semantic_decode_gap payload[62..29024)" not in asm_text
    assert "residual_summary candidate_unvisited_entry_pattern count=11" in asm_text
    assert "residual candidate_unvisited_entry_pattern payload[" not in asm_text
    assert ";     semantic_source: kind=macos_code_semantic_source_v1 status=decoded" in asm_text
    assert "macos_code_CODE_1_loc_00000028:" in asm_text
    assert "\tmovea.l (a7)+,a0\n" in asm_text
    assert "\tmove.l a7,d0\n" in asm_text
    assert "\tmovea.l (a7)+,a0\t; payload+" not in asm_text
    assert " bytes=20 5F" not in asm_text
    assert "macos_code_CODE_1_loc_0000003e:" in asm_text
    assert "macos_code_CODE_1_semantic_decode_gap_0000003e:" not in asm_text
    assert "macos_code_CODE_1_semantic_string_data_gap_0000027e:" in asm_text
    assert "macos_code_CODE_1_semantic_dispatch_table_gap_00000f94:" in asm_text
    assert "macos_code_CODE_12_semantic_alignment_padding_gap_000009c6:\n\tds.b 2" in asm_text
    assert "loc_0_" not in asm_text
    assert "macos_code_CODE_1_loc_0000372c(pc,d0.w)" in asm_text
    assert ";       xref code_start_ref payload+" not in asm_text
    assert "macos_code_CODE_1_candidate_code_00000028:\n\tdc.b $20,$5F" not in asm_text
    assert "residual candidate_code payload[40..29024)" not in asm_text
    assert "candidate_data_island" not in asm_text
    assert "SECTION code,code" not in asm_text
    assert "\tori.b #16,d0" not in asm_text
    assert "macos_CODE_1_far_model_header:" in asm_text
    assert "payload[0..40) status=validated parser_use=accepted_parser_output reason=far_model_segment_header" in asm_text
    assert "macos_CODE_1_candidate_entry_stub:" in asm_text
    assert (
        "payload[40..62) selected_code_bytes[0..22) status=candidate parser_use=candidate_only "
        "reason=entry/stub bytes begin at candidate movea.l (a7)+,a0 boundary"
    ) in asm_text
    assert "macos_CODE_1_candidate_body_after_stub:" in asm_text
    assert "payload[62..29024) status=candidate parser_use=candidate_only" in asm_text
    assert "accepted byte-entry proof remains deferred" in asm_text
    assert "orphan code" not in asm_text.lower()
    source_start = asm_text.index("; CODE source body sections")
    code0_source_start = asm_text.index("; CODE 0 unknown source section")
    code1_header = asm_text.index("macos_CODE_1_far_model_header:")
    code1_stub = asm_text.index("macos_CODE_1_candidate_entry_stub:")
    listing_start = asm_text.index("; CODE 1 Main byte-real source follows.")
    first_instruction = asm_text.index("\tmovea.l (a7)+,a0\n", listing_start)
    quality_start = asm_text.index("; Source quality gate")
    evidence_start = asm_text.index("; Supporting evidence follows after the source body.")
    assert (
        source_start
        < code0_source_start
        < code1_header
        < code1_stub
        < listing_start
        < first_instruction
        < quality_start
        < evidence_start
    )
    assert evidence_start < asm_text.index("; File forks")
    assert asm_text.index("; Resource fork") > evidence_start
    assert asm_text.index("; CODE resources") > evidence_start


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
    source_start = asm_lines.index("; CODE source body sections")
    evidence_start = asm_lines.index("; Supporting evidence follows after the source body.")
    coverage_start = asm_lines.index("; CODE resource coverage")
    segment_map_start = asm_lines.index("; CODE segment/routine map")
    detail_start = asm_lines.index("; CODE resource detail subviews")
    non_code_start = asm_lines.index("; Non-CODE resource placeholders")
    source_lines = [
        line
        for line in asm_lines[source_start:evidence_start]
        if line.startswith("; CODE ") and line.endswith(" source section")
    ]
    coverage_lines = [
        line for line in asm_lines[coverage_start:segment_map_start] if line.startswith(";   CODE ") and "status=" in line
    ]
    detail_lines = [
        line
        for line in asm_lines[detail_start:non_code_start]
        if line.startswith(";   CODE ") and "role=" in line and "payload_size=" in line
    ]

    assert len(source_lines) == len(expected)
    assert len(coverage_lines) == len(expected)
    assert len(detail_lines) == len(expected)
    for resource in expected:
        source_prefix = f"; CODE {resource['id']} "
        report_prefix = f";   CODE {resource['id']} "
        assert any(line.startswith(source_prefix) for line in source_lines), source_prefix
        source_index = next(index for index, line in enumerate(asm_lines) if line.startswith(source_prefix))
        assert source_start < source_index < evidence_start
        source_block_end = next(
            (
                index
                for index in range(source_index + 1, evidence_start)
                if asm_lines[index].startswith("; CODE ") and asm_lines[index].endswith(" source section")
            ),
            evidence_start,
        )
        source_block = "\n".join(asm_lines[source_index:source_block_end])
        assert f";   source_section_id: macos-code-CODE-{resource['id']}" in source_block
        assert f";   payload_size: {resource['payload_size']}" in source_block
        assert ";   source_body_ranges:" in source_block
        assert "byte_preserving_placeholder:" in source_block
        assert ";   byte_real_source:" in source_block
        prefix = report_prefix
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
    assert analysis_ranges[0]["role"] == "candidate_code"
    assert analysis_ranges[0]["fact_status"] == "candidate"
    assert analysis_ranges[0]["parser_use"] == "candidate_only"
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
    assert macos["classified_range"]["role"] == "candidate_code"
    assert macos["classified_range"]["fact_status"] == "candidate"
