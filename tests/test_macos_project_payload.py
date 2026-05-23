from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from amiga_reversing.disasm import macos_project_payload
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord
from amiga_reversing.tools import platform_executable_formats

IMAGE_PATH = Path("resources/platform_macos/MPW-GM.img.bin")
NDIF2RAW_PATH = Path("ext/tools/ndif2raw/ndif2raw.exe")
SAMPLE_DIR = Path("ext/macos_includes/mpw_gm/Interfaces/AStructMacs")


def test_macos_project_payload_uses_c_summary_and_source_fixture_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "sample.a"
    resource_path = tmp_path / "sample.r"
    build_path = tmp_path / "sample.make"
    image_path = tmp_path / "MPW-GM.img.bin"
    source_path.write_text("\tSEG\t'Main'\nStart\tPROC\n\tENDP\n", encoding="utf-8")
    resource_path.write_text("resource 'WIND' (128) {\n};\n", encoding="utf-8")
    build_path.write_text("Sample  \u00c4\u00c4 Sample.a\n    Link -o {Targ} Sample.a.o\n", encoding="utf-8")
    image_path.write_bytes(b"macbinary")
    calls: dict[str, Any] = {}

    def fake_read_hfs(path: Path) -> bytes:
        calls["image_path"] = path
        return b"hfs"

    def fake_summary(data: bytes, hfs_path: str) -> dict[str, object]:
        calls["summary_args"] = (data, hfs_path)
        return {
            "container_kind": "hfs_resource_code_file",
            "file": {
                "path": "MPW-GM/MPW/Tools/Asm",
                "type": "MPST",
                "creator": "MPS ",
                "cnid": 2310,
                "forks": {
                    "data": {"size": 10, "sha256": "data-hash"},
                    "resource": {"size": 20, "sha256": "resource-hash"},
                },
            },
            "resource_fork": {
                "types": [{"type": "CODE", "count": 3}],
                "code_resources": [
                    {
                        "type": "CODE",
                        "id": 0,
                        "name": "unknown",
                        "payload_size": 32,
                        "sha256": "code0-hash",
                        "code": {
                            "kind": "jump_table_segment",
                            "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                            "fact_id": "macos.code_resource.0.jump_table_metadata",
                            "fact_status": "validated",
                            "parser_use": "accepted_parser_output",
                            "jump_table": {
                                "kind": "code0_jump_table",
                                "start": 16,
                                "size": 8,
                                "end": 24,
                                "entry_size": 8,
                                "entry_count": 1,
                                "trailing_bytes": 0,
                                "fact_id": "macos.jump_table.entries.accepted",
                                "fact_status": "validated",
                                "parser_use": "accepted_parser_output",
                            },
                            "layout_ranges": [{"kind": "metadata", "start": 0, "size": 32, "end": 32}],
                            "orphan_ranges": [],
                            "relocation_fixups": {
                                "status": "deferred",
                                "fact_id": "macos.segment_loader.relocation_fixups.deferred",
                                "fact_status": "deferred",
                                "parser_use": "deferred_only",
                            },
                        },
                    },
                    {
                        "type": "CODE",
                        "id": 1,
                        "name": None,
                        "payload_size": 8,
                        "sha256": "payload-hash",
                        "code": {
                            "kind": "code_segment",
                            "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                            "fact_id": "macos.resource_fork.code_resources.accepted",
                            "fact_status": "validated",
                            "parser_use": "accepted_parser_output",
                            "layout_ranges": [
                                {
                                    "kind": "metadata",
                                    "start": 0,
                                    "size": 4,
                                    "end": 4,
                                    "entrypoint": False,
                                    "evidence": "nonzero_code_segment_header",
                                    "fact_id": "macos.code_resource.nonzero.segment_header",
                                    "fact_status": "validated",
                                    "parser_use": "accepted_parser_output",
                                },
                                {
                                    "kind": "data",
                                    "start": 4,
                                    "size": 2,
                                    "end": 6,
                                    "entrypoint": False,
                                    "evidence": "prefix_before_stack_entry",
                                    "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                                    "fact_status": "candidate",
                                    "parser_use": "candidate_only",
                                },
                                {
                                    "kind": "candidate_code",
                                    "start": 6,
                                    "size": 2,
                                    "end": 8,
                                    "entrypoint": True,
                                    "evidence": "m68k_movea_l_stack_to_a0_entry",
                                    "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                                    "fact_status": "candidate",
                                    "parser_use": "candidate_only",
                                },
                            ],
                            "orphan_ranges": [
                                {
                                    "classification": "candidate_data_island",
                                    "start": 4,
                                    "size": 2,
                                    "end": 6,
                                    "evidence": "prefix_before_stack_entry",
                                    "fact_id": "macos.code_resource.orphan_layout_ranges.candidate",
                                    "fact_status": "candidate",
                                    "parser_use": "candidate_only",
                                }
                            ],
                            "relocation_fixups": {
                                "status": "deferred",
                                "fact_id": "macos.segment_loader.relocation_fixups.deferred",
                                "fact_status": "deferred",
                                "parser_use": "deferred_only",
                            },
                        },
                    },
                    {
                        "type": "CODE",
                        "id": 2,
                        "name": "FPOpTable",
                        "payload_size": 10,
                        "sha256": "code2-hash",
                        "code": {
                            "kind": "code_segment",
                            "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                            "fact_id": "macos.resource_fork.code_resources.accepted",
                            "fact_status": "validated",
                            "parser_use": "accepted_parser_output",
                            "layout_ranges": [
                                {
                                    "kind": "metadata",
                                    "start": 0,
                                    "size": 4,
                                    "end": 4,
                                    "entrypoint": False,
                                    "evidence": "nonzero_code_segment_header",
                                    "fact_id": "macos.code_resource.nonzero.segment_header",
                                    "fact_status": "validated",
                                    "parser_use": "accepted_parser_output",
                                },
                                {
                                    "kind": "data",
                                    "start": 4,
                                    "size": 2,
                                    "end": 6,
                                    "entrypoint": False,
                                    "evidence": "prefix_before_stack_entry",
                                    "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                                    "fact_status": "candidate",
                                    "parser_use": "candidate_only",
                                },
                                {
                                    "kind": "candidate_code",
                                    "start": 6,
                                    "size": 4,
                                    "end": 10,
                                    "entrypoint": True,
                                    "evidence": "m68k_movea_l_stack_to_a0_entry",
                                    "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                                    "fact_status": "candidate",
                                    "parser_use": "candidate_only",
                                },
                            ],
                            "orphan_ranges": [
                                {
                                    "classification": "candidate_data_island",
                                    "start": 4,
                                    "size": 2,
                                    "end": 6,
                                    "evidence": "prefix_before_stack_entry",
                                    "fact_id": "macos.code_resource.orphan_layout_ranges.candidate",
                                    "fact_status": "candidate",
                                    "parser_use": "candidate_only",
                                }
                            ],
                            "relocation_fixups": {
                                "status": "deferred",
                                "fact_id": "macos.segment_loader.relocation_fixups.deferred",
                                "fact_status": "deferred",
                                "parser_use": "deferred_only",
                                "reason": "Segment Loader relocation/fixup interpretation is not represented",
                            },
                        },
                    },
                ],
                "code_segment_map": [
                    {
                        "resource_id": 1,
                        "kind": "nonzero_code_segment",
                        "first_jump_table_entry_offset": 0,
                        "jump_table_entry_count": 1,
                        "jump_table_entry_size": 8,
                        "jump_table_span_size": 8,
                        "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                        "fact_id": "macos.code_resource.segment_jump_table_span.accepted",
                        "fact_status": "validated",
                        "parser_use": "accepted_parser_output",
                        "routine_entry_candidates": [
                            {
                                "index": 0,
                                "jump_table_offset": 0,
                                "code0_payload_offset": 16,
                                "routine_offset_from_segment": 4,
                                "classification": "candidate_routine_entry",
                                "fact_id": "macos.code_resource.jump_table.routine_offsets.candidate",
                                "fact_status": "candidate",
                                "parser_use": "candidate_only",
                            }
                        ],
                    },
                    {
                        "resource_id": 2,
                        "kind": "nonzero_code_segment",
                        "first_jump_table_entry_offset": 8,
                        "jump_table_entry_count": 1,
                        "jump_table_entry_size": 8,
                        "jump_table_span_size": 8,
                        "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                        "fact_id": "macos.code_resource.segment_jump_table_span.accepted",
                        "fact_status": "validated",
                        "parser_use": "accepted_parser_output",
                        "routine_entry_candidates": [
                            {
                                "index": 0,
                                "jump_table_offset": 8,
                                "code0_payload_offset": 24,
                                "routine_offset_from_segment": 6,
                                "classification": "candidate_routine_entry",
                                "fact_id": "macos.code_resource.jump_table.routine_offsets.candidate",
                                "fact_status": "candidate",
                                "parser_use": "candidate_only",
                            }
                        ],
                    },
                ],
            },
            "selected_code": {
                "available": True,
                "id": 1,
                "payload_offset": 100,
                "payload_size": 8,
                "code_bytes_offset": 106,
                "code_bytes_size": 2,
                "payload_sha256": "payload-hash",
                "code_bytes_sha256": "code-hash",
                "code": {
                    "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                    "fact_id": "macos.resource_fork.code_resources.accepted",
                    "fact_status": "validated",
                    "parser_use": "accepted_parser_output",
                    "layout_ranges": [
                        {
                            "kind": "metadata",
                            "start": 0,
                            "size": 4,
                            "end": 4,
                            "entrypoint": False,
                            "evidence": "nonzero_code_segment_header",
                            "fact_id": "macos.code_resource.nonzero.segment_header",
                            "fact_status": "validated",
                            "parser_use": "accepted_parser_output",
                        },
                        {
                            "kind": "data",
                            "start": 4,
                            "size": 2,
                            "end": 6,
                            "entrypoint": False,
                            "evidence": "prefix_before_stack_entry",
                            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                            "fact_status": "candidate",
                            "parser_use": "candidate_only",
                        },
                        {
                            "kind": "candidate_code",
                            "start": 6,
                            "size": 2,
                            "end": 8,
                            "entrypoint": True,
                            "evidence": "m68k_movea_l_stack_to_a0_entry",
                            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                            "fact_status": "candidate",
                            "parser_use": "candidate_only",
                        },
                    ],
                    "orphan_ranges": [
                        {
                            "classification": "candidate_data_island",
                            "start": 4,
                            "size": 2,
                            "end": 6,
                            "evidence": "prefix_before_stack_entry",
                            "fact_id": "macos.code_resource.orphan_layout_ranges.candidate",
                            "fact_status": "candidate",
                            "parser_use": "candidate_only",
                        }
                    ],
                    "relocation_fixups": {
                        "status": "deferred",
                        "fact_id": "macos.segment_loader.relocation_fixups.deferred",
                        "fact_status": "deferred",
                        "parser_use": "deferred_only",
                    },
                },
            },
            "unsupported": ["segment_loader_relocations"],
        }

    def fake_extract(data: bytes, hfs_path: str, resource_id: int, **kwargs: object) -> bytes:
        calls.setdefault("extract_args", []).append((data, hfs_path, resource_id, kwargs.get("project_root")))
        assert resource_id == 2
        return b"\x00\x00\x00\x00\x00\x00\x20\x5f\x4e\x75"

    monkeypatch.setattr(macos_project_payload, "read_macos_hfs_image_bytes", fake_read_hfs)
    monkeypatch.setattr(macos_project_payload, "inspect_macos_hfs_code_summary_with_c_backend", fake_summary)
    monkeypatch.setattr(macos_project_payload, "extract_macos_hfs_code_resource_bytes_with_c_backend", fake_extract)
    project = ProjectRecord(
        id="macos_mpw_sample",
        name="macos_mpw_sample",
        kind=ProjectKind.MACOS,
        target_dir=str(tmp_path / "targets" / "macos_mpw_sample"),
        output_path=None,
        binary_path=str(image_path),
        ready=True,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=str(image_path),
        disk_type="HFS",
        parent_project_id=None,
        target_type="macos_hfs_resource_code_file",
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
        origin={
            "kind": "macos_mpw_fixture",
            "source_image": image_path.name,
            "hfs_path": "MPW-GM/MPW/Tools/Asm",
            "source_files": [source_path.name],
            "resource_files": [resource_path.name],
            "build_files": [build_path.name],
        },
    )

    payload = macos_project_payload.build_macos_project_payload(project, project_root=tmp_path)
    container = payload["binary_container_view"]

    assert platform_executable_formats.validate_parser_fact_references(payload) == []
    assert payload["platform"] == "macos"
    assert calls["image_path"] == image_path
    assert calls["summary_args"] == (b"hfs", "MPW-GM/MPW/Tools/Asm")
    assert container["kind"] == "hfs_resource_code_file"
    assert container["finder"] == {"type": "MPST", "creator": "MPS ", "cnid": 2310}
    assert container["selected_code_segment"]["code_entry_offset"] == 6
    assert container["selected_code_segment"]["code_layout"][2]["kind"] == "candidate_code"
    assert container["selected_code_segment"]["code_layout"][2]["fact_status"] == "candidate"
    assert container["code_segment_map"][0]["fact_id"] == "macos.code_resource.segment_jump_table_span.accepted"
    assert container["code_segment_map"][0]["routine_entry_candidates"][0]["fact_status"] == "candidate"
    assert container["selected_code_segment"]["orphan_ranges"][0]["fact_status"] == "candidate"
    assert container["selected_code_segment"]["relocation_fixups"]["parser_use"] == "deferred_only"
    assert [item["id"] for item in container["code_resource_details"]] == [0, 1, 2]
    code0_detail = container["code_resource_details"][0]
    code1_detail = container["code_resource_details"][1]
    code2_detail = container["code_resource_details"][2]
    assert code0_detail["role"] == "code0_metadata"
    assert code0_detail["listing"] == {
        "kind": "metadata",
        "available": False,
        "reason": "CODE 0 is jump-table/application metadata, not ordinary m68k code",
    }
    assert code0_detail["preview_windows"] == []
    assert any(anchor["kind"] == "accepted_jump_table" for anchor in code0_detail["navigation_anchors"])
    assert any(anchor["kind"] == "candidate_routine_jump_table_entry" for anchor in code0_detail["navigation_anchors"])
    assert code1_detail["role"] == "code_segment"
    assert code1_detail["listing"]["kind"] == "full_listing"
    assert code1_detail["listing"]["available"] is True
    assert code1_detail["preview_windows"] == []
    assert any(anchor["kind"] == "accepted_segment_metadata" for anchor in code1_detail["navigation_anchors"])
    candidate_anchor = next(
        anchor for anchor in code1_detail["navigation_anchors"] if anchor["kind"] == "candidate_routine_entry"
    )
    assert candidate_anchor["fact_status"] == "candidate"
    assert candidate_anchor["parser_use"] == "candidate_only"
    assert code2_detail["listing"]["kind"] == "candidate_preview"
    assert code2_detail["listing"]["available"] is True
    assert code2_detail["listing"]["route"] == "code_preview"
    assert code2_detail["preview_windows"][0]["range_kind"] == "candidate_code"
    assert code2_detail["preview_windows"][0]["start"] == 6
    assert code2_detail["preview_windows"][0]["end"] == 10
    assert code2_detail["preview_windows"][0]["fact_status"] == "candidate"
    assert code2_detail["preview_windows"][0]["parser_use"] == "candidate_only"
    assert code2_detail["preview_windows"][0]["deferred_reasons"][0]["parser_use"] == "deferred_only"
    assert [row["offset"] for row in code2_detail["preview_windows"][0]["rows"]] == [6, 8]
    assert all(row["fact_status"] == "candidate" for row in code2_detail["preview_windows"][0]["rows"])
    assert all(row["parser_use"] == "candidate_only" for row in code2_detail["preview_windows"][0]["rows"])
    assert all(row["offset"] >= 6 and row["end"] <= 10 for row in code2_detail["preview_windows"][0]["rows"])
    assert calls["extract_args"] == [(b"hfs", "MPW-GM/MPW/Tools/Asm", 2, tmp_path)]
    navigation_groups = container["navigation"]["groups"]
    assert navigation_groups[0]["id"] == "macos-code-resources"
    assert len(navigation_groups[0]["items"]) == 3
    assert navigation_groups[1]["id"] == "macos-code-anchors"
    assert container["selected_code_segment"]["listing"] == {
        "project_id": "macos_mpw_sample",
        "route": "listing",
        "source_range": {"section_index": 0, "start_offset": 0, "size": 2},
        "resource_type": "CODE",
        "resource_id": 1,
        "resource_name": None,
        "fork": "resource",
        "payload_size": 8,
        "payload_sha256": "payload-hash",
        "code_bytes_sha256": "code-hash",
        "unsupported": ["segment_loader_relocations"],
    }
    assert payload["source_binary_boundary"]["observed_code_fixture"] == "MPW-GM/MPW/Tools/Asm"
    assert payload["provenance"]["binary_container_source"] == "platform_file_lib.macos_hfs_code_summary"


def test_macos_project_payload_reads_committed_mpw_fixture_when_available() -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    if not NDIF2RAW_PATH.exists():
        pytest.skip("ndif2raw provider is not available")
    required = [SAMPLE_DIR / "Sample.a", SAMPLE_DIR / "Sample.r", SAMPLE_DIR / "Sample.make"]
    if any(not path.exists() for path in required):
        pytest.skip("MPW-GM source fixture metadata is not available")
    project = ProjectRecord(
        id="macos_mpw_sample",
        name="macos_mpw_sample",
        kind=ProjectKind.MACOS,
        target_dir="targets/macos_mpw_sample",
        output_path=None,
        binary_path=IMAGE_PATH.as_posix(),
        ready=True,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=IMAGE_PATH.as_posix(),
        disk_type="HFS",
        parent_project_id=None,
        target_type="macos_hfs_resource_code_file",
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
        origin={
            "kind": "macos_mpw_fixture",
            "source_image": IMAGE_PATH.as_posix(),
            "hfs_path": "MPW-GM/MPW/Tools/Asm",
            "source_files": [(SAMPLE_DIR / "Sample.a").as_posix()],
            "resource_files": [(SAMPLE_DIR / "Sample.r").as_posix()],
            "build_files": [(SAMPLE_DIR / "Sample.make").as_posix()],
        },
    )

    payload = macos_project_payload.build_macos_project_payload(project)
    container = payload["binary_container_view"]

    assert platform_executable_formats.validate_parser_fact_references(payload) == []
    assert payload["platform"] == "macos"
    assert container["finder"] == {"type": "MPST", "creator": "MPS ", "cnid": 2310}
    assert len(container["code_resources"]) == 28
    assert len(container["code_resource_details"]) == len(container["code_resources"])
    assert container["code_resource_details"][0]["role"] == "code0_metadata"
    assert container["code_resource_details"][0]["listing"]["kind"] == "metadata"
    assert container["code_resource_details"][0]["listing"]["available"] is False
    assert container["code_resource_details"][0]["preview_windows"] == []
    selected_detail = next(detail for detail in container["code_resource_details"] if detail["id"] == 1)
    assert selected_detail["listing"]["kind"] == "full_listing"
    assert selected_detail["preview_windows"] == []
    preview_details = [
        detail
        for detail in container["code_resource_details"]
        if detail["id"] not in {0, 1} and detail["preview_windows"]
    ]
    assert preview_details
    first_preview = preview_details[0]["preview_windows"][0]
    assert first_preview["kind"] == "candidate_code_preview"
    assert first_preview["fact_status"] == "candidate"
    assert first_preview["parser_use"] == "candidate_only"
    assert first_preview["range_kind"] == "candidate_code"
    assert first_preview["deferred_reasons"][0]["parser_use"] == "deferred_only"
    assert all(row["fact_status"] == "candidate" for row in first_preview["rows"])
    assert all(row["parser_use"] == "candidate_only" for row in first_preview["rows"])
    for detail in preview_details:
        preview = detail["preview_windows"][0]
        candidate = next(item for item in detail["code_layout"] if item.get("kind") == "candidate_code")
        non_code_ranges = [item for item in detail["code_layout"] if item.get("kind") != "candidate_code"]
        assert candidate["start"] <= preview["start"] < preview["end"] <= candidate["end"]
        for non_code in non_code_ranges:
            assert preview["end"] <= non_code["start"] or preview["start"] >= non_code["end"]
    no_preview = [
        detail
        for detail in container["code_resource_details"]
        if detail["id"] not in {0, 1} and not detail["preview_windows"]
    ]
    assert no_preview
    assert all("no candidate" in detail["listing"]["reason"] for detail in no_preview)
    assert all("navigation_anchors" in item for item in container["code_resource_details"])
    assert any(
        anchor.get("fact_status") == "candidate"
        for detail in container["code_resource_details"]
        for anchor in detail["navigation_anchors"]
        if isinstance(anchor, dict)
    )
    assert any(
        detail["relocation_fixups"].get("parser_use") == "deferred_only"
        for detail in container["code_resource_details"]
    )
    assert len(container["navigation"]["groups"][0]["items"]) == len(container["code_resources"])
    assert container["code_segment_map"]
    assert any(
        item.get("fact_id") == "macos.code_resource.segment_jump_table_span.accepted"
        for item in container["code_segment_map"]
        if isinstance(item, dict)
    )
    assert container["selected_code_segment"]["code_entry_offset"] == 40
    assert container["selected_code_segment"]["code_bytes_size"] == 28984
    assert container["selected_code_segment"]["code_layout"][2]["kind"] == "candidate_code"
    assert container["selected_code_segment"]["code_layout"][2]["fact_status"] == "candidate"
    assert container["selected_code_segment"]["orphan_ranges"][0]["fact_status"] == "candidate"
    assert container["selected_code_segment"]["relocation_fixups"]["parser_use"] == "deferred_only"
    assert payload["provenance"]["source_image"] == IMAGE_PATH.as_posix()
