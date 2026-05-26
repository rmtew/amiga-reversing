from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from amiga_reversing.disasm import macos_project_payload
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord
from amiga_reversing.tools import platform_executable_formats

IMAGE_PATH = Path("resources/platform_macos/MPW-GM.img.bin")
NDIF2RAW_PATH = Path("ext/tools/ndif2raw/ndif2raw.exe")
SAMPLE_DIR = Path("ext/macos_includes/mpw_gm/Interfaces/AStructMacs")


def _c_owned_restored_source_packet(
    *,
    resource_id: int,
    payload_size: int,
    ranges: list[dict[str, object]],
    resource_name: str | None = None,
) -> dict[str, object]:
    return {
        "model": "restored_source_model_v1",
        "platform": "macos",
        "source_kind": "macos_code_resource",
        "authority": "c_owned",
        "round_trip_required": False,
        "source_ownership_ranges": ranges,
        "source_coverage_verifier": {
            "ok": True,
            "gap_count": 0,
            "overlap_count": 0,
            "invalid_instruction_ownership_count": 0,
            "explicit_unknown_missing_detail_count": 0,
        },
        "source_reference_records": [
            {
                "kind": "segment_loader_fixup_placeholder",
                "ownership_range_index": 0,
                "source_offset": None,
                "size": 0,
                "target": "unresolved_segment_loader_fixup",
                "status": "deferred",
                "reason": "Segment Loader relocation/fixup bytes and effects are deferred in the executable-format KB.",
                "provenance": "platform_file_lib.macos_hfs_code_summary",
                "source_visible": True,
                "rendering": {"kind": "placeholder", "text": "deferred Segment Loader relocation/fixup effect"},
                "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                "fact_id": "macos.segment_loader.relocation_fixups.deferred",
                "fact_status": "deferred",
                "parser_use": "deferred_only",
            }
        ],
        "platform_extensions": {
            "code_resource": {
                "resource_type": "CODE",
                "resource_id": resource_id,
                "resource_name": resource_name,
                "payload_size": payload_size,
            },
            "a5_world": {
                "status": "deferred",
                "reason": "Classic Mac A5/world conventions are preserved as platform context, not promoted to executable byte-entry proof.",
            },
        },
    }


def _restored_ranges_from_layout(layout_ranges: list[dict[str, object]], payload_size: int) -> list[dict[str, object]]:
    ranges: list[dict[str, object]] = []
    cursor = 0
    for index, source in enumerate(layout_ranges):
        start = int(source["start"])
        end = int(source["end"])
        if start > cursor:
            ranges.append(
                {
                    "index": len(ranges),
                    "role": "unknown",
                    "start": cursor,
                    "end": start,
                    "size": start - cursor,
                    "status": "deferred",
                    "source_visible": True,
                    "reason": "No parser-owned restored-source range covers these bytes.",
                    "provenance": "platform_file_lib.macos_hfs_code_summary",
                }
            )
        item = dict(source)
        item["index"] = len(ranges)
        item["role"] = "candidate_code" if item.get("kind") == "candidate_code" else item.get("kind")
        item["status"] = item.get("fact_status")
        item["source_visible"] = True
        item["provenance"] = "platform_file_lib.macos_hfs_code_summary"
        ranges.append(item)
        cursor = max(cursor, end)
    if cursor < payload_size:
        ranges.append(
            {
                "index": len(ranges),
                "role": "unknown",
                "start": cursor,
                "end": payload_size,
                "size": payload_size - cursor,
                "status": "deferred",
                "source_visible": True,
                "reason": "No parser-owned restored-source range covers these bytes.",
                "provenance": "platform_file_lib.macos_hfs_code_summary",
            }
        )
    for index, item in enumerate(ranges):
        item["index"] = index
    return ranges


def _summary_with_c_owned_restored_sources(summary: dict[str, object]) -> dict[str, object]:
    resource_fork = summary["resource_fork"]
    assert isinstance(resource_fork, dict)
    code_resources = resource_fork["code_resources"]
    assert isinstance(code_resources, list)
    for resource in code_resources:
        assert isinstance(resource, dict)
        code = resource.get("code")
        if not isinstance(code, dict):
            continue
        payload_size = int(resource["payload_size"])
        layout_ranges = code.get("layout_ranges")
        if not isinstance(layout_ranges, list):
            continue
        code["restored_source"] = _c_owned_restored_source_packet(
            resource_id=int(resource["id"]),
            resource_name=resource.get("name") if isinstance(resource.get("name"), str) else None,
            payload_size=payload_size,
            ranges=_restored_ranges_from_layout(cast(list[dict[str, object]], layout_ranges), payload_size),
        )
    selected = summary.get("selected_code")
    if isinstance(selected, dict):
        selected_code = selected.get("code")
        if isinstance(selected_code, dict):
            layout_ranges = selected_code.get("layout_ranges")
            if isinstance(layout_ranges, list):
                selected_code["restored_source"] = _c_owned_restored_source_packet(
                    resource_id=int(selected["id"]),
                    payload_size=int(selected["payload_size"]),
                    ranges=_restored_ranges_from_layout(cast(list[dict[str, object]], layout_ranges), int(selected["payload_size"])),
                )
    return summary


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
        return _summary_with_c_owned_restored_sources({
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
                "types": [{"type": "CODE", "count": 4}, {"type": "WIND", "count": 1}],
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
                    {
                        "type": "CODE",
                        "id": 3,
                        "name": "Tiny",
                        "payload_size": 7,
                        "sha256": "code3-hash",
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
                                    "kind": "candidate_code",
                                    "start": 6,
                                    "size": 1,
                                    "end": 7,
                                    "entrypoint": True,
                                    "evidence": "m68k_movea_l_stack_to_a0_entry",
                                    "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                                    "fact_status": "candidate",
                                    "parser_use": "candidate_only",
                                },
                            ],
                            "orphan_ranges": [],
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
        })

    def fake_extract(data: bytes, hfs_path: str, resource_id: int, **kwargs: object) -> bytes:
        calls.setdefault("extract_args", []).append((data, hfs_path, resource_id, kwargs.get("project_root")))
        if resource_id == 2:
            return b"\x00\x00\x00\x00\x00\x00\x20\x5f\x4e\x75"
        if resource_id == 3:
            return b"\x00\x00\x00\x00\x00\x00\x20"
        raise AssertionError(resource_id)

    class FakeDecodeArtifact:
        def window_payload(self, *, start: int, count: int) -> tuple[dict[str, object], dict[str, object]]:
            assert start == 0
            assert count >= 4
            return (
                {
                    "rows": [
                        {
                            "kind": "instruction",
                            "text": "movea.l (a7)+,a0\n",
                            "start_offset": 0,
                            "end_offset": 2,
                            "bytes": "205f",
                            "opcode_or_directive": "movea.l",
                            "operand_text": "(a7)+,a0",
                        },
                        {
                            "kind": "instruction",
                            "text": "rts\n",
                            "start_offset": 2,
                            "end_offset": 4,
                            "bytes": "4e75",
                            "opcode_or_directive": "rts",
                            "operand_text": "",
                        },
                    ]
                },
                {},
            )

        def close(self) -> None:
            calls["decode_closed"] = True

    def fake_build_listing(
        code_bytes: bytes,
        *,
        display_path: str,
        **kwargs: object,
    ) -> tuple[int, dict[str, object], FakeDecodeArtifact]:
        calls.setdefault("decode_bytes", []).append(code_bytes)
        calls.setdefault("decode_display_paths", []).append(display_path)
        calls.setdefault("decode_project_roots", []).append(kwargs.get("project_root"))
        return 2, {"backend": "macos-code", "source_kind": "macos_code_resource"}, FakeDecodeArtifact()

    monkeypatch.setattr(macos_project_payload, "read_macos_hfs_image_bytes", fake_read_hfs)
    monkeypatch.setattr(macos_project_payload, "inspect_macos_hfs_code_summary_with_c_backend", fake_summary)
    monkeypatch.setattr(macos_project_payload, "extract_macos_hfs_code_resource_bytes_with_c_backend", fake_extract)
    monkeypatch.setattr(macos_project_payload, "build_macos_code_bytes_listing_artifact_profile", fake_build_listing)
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
    coverage = platform_executable_formats.build_parser_fact_coverage_report([payload], labels=["macos_project_payload"])
    assert coverage["summary"]["invalid"] == 0
    assert coverage["summary"]["candidate"] > 0
    assert coverage["summary"]["deferred"] > 0
    movea_refs = [
        item
        for item in coverage["emitted_fact_refs"]
        if item["fact_id"] == "macos.code_resource.movea_stack_a0.boundary.candidate"
    ]
    relocation_refs = [
        item
        for item in coverage["emitted_fact_refs"]
        if item["fact_id"] == "macos.segment_loader.relocation_fixups.deferred"
    ]
    assert movea_refs and all(item["classification"] == "candidate" for item in movea_refs)
    assert relocation_refs and all(item["classification"] == "deferred" for item in relocation_refs)
    assert payload["platform"] == "macos"
    assert calls["image_path"] == image_path
    assert calls["summary_args"] == (b"hfs", "MPW-GM/MPW/Tools/Asm")
    assert container["kind"] == "hfs_resource_code_file"
    assert container["finder"] == {"type": "MPST", "creator": "MPS ", "cnid": 2310}
    assert container["resource_fork"]["non_code_resource_details"] == [
        {
            "resource_type": "WIND",
            "resource_count": 1,
            "role": "resource_metadata_inventory",
            "semantic_status": "candidate",
            "payload_decode_status": "unsupported",
            "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
            "fact_id": "macos.resource_fork.non_code_metadata.inventory.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
            "evidence": "resource fork type inventory; payload semantics are not decoded",
            "inventory_source": "platform_file_lib.macos_hfs_code_summary resource_fork.types",
            "reason": "non-CODE resource metadata is inventory-only and not executable CODE",
            }
        ]
    placeholders = container["executable_resource_placeholders"]
    assert placeholders == container["resource_fork"]["executable_resource_placeholders"]
    assert placeholders == [
        {
            "kind": "executable_resource_placeholder",
            "resource_type": "WIND",
            "resource_id": None,
            "resource_name": None,
            "resource_count": 1,
            "byte_size": None,
            "sha256": None,
            "stable_identity": "macos-resource:MPW-GM.img.bin:MPW-GM/MPW/Tools/Asm:WIND:*",
            "status": "candidate",
            "reason": "non-CODE resource metadata is inventory-only and not executable CODE",
            "provenance": "platform_file_lib.macos_hfs_code_summary resource_fork.types",
            "source_visible": True,
            "reference_sites": [
                {
                    "kind": "resource_type_inventory",
                    "resource_type": "WIND",
                    "resource_id": None,
                    "source_offset": None,
                    "reason": "No direct CODE source reference site is known for this resource type yet.",
                }
            ],
            "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
            "fact_id": "macos.resource_fork.non_code_metadata.inventory.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        }
    ]
    assert container["selected_code_segment"]["code_entry_offset"] == 6
    assert container["selected_code_segment"]["code_layout"][2]["kind"] == "candidate_code"
    assert container["selected_code_segment"]["code_layout"][2]["fact_status"] == "candidate"
    selected_restored = container["selected_code_segment"]["restored_source"]
    assert selected_restored["model"] == "restored_source_model_v1"
    assert selected_restored["authority"] == "c_owned"
    assert selected_restored["round_trip_required"] is False
    assert selected_restored["source_coverage_verifier"]["ok"] is True
    assert [item["role"] for item in selected_restored["source_ownership_ranges"]] == [
        "metadata",
        "data",
        "candidate_code",
    ]
    assert selected_restored["source_reference_records"][0]["kind"] == "segment_loader_fixup_placeholder"
    assert selected_restored["source_reference_records"][0]["parser_use"] == "deferred_only"
    assert selected_restored["platform_extensions"]["code_resource"]["resource_id"] == 1
    assert selected_restored["platform_extensions"]["a5_world"]["status"] == "deferred"
    assert container["code_segment_map"][0]["fact_id"] == "macos.code_resource.segment_jump_table_span.accepted"
    assert container["code_segment_map"][0]["routine_entry_candidates"][0]["fact_status"] == "candidate"
    assert container["selected_code_segment"]["orphan_ranges"][0]["fact_status"] == "candidate"
    assert container["selected_code_segment"]["relocation_fixups"]["parser_use"] == "deferred_only"
    assert [item["id"] for item in container["code_resource_details"]] == [0, 1, 2, 3]
    code0_detail = container["code_resource_details"][0]
    code1_detail = container["code_resource_details"][1]
    code2_detail = container["code_resource_details"][2]
    code3_detail = container["code_resource_details"][3]
    assert code0_detail["role"] == "code0_metadata"
    assert code0_detail["listing"] == {
        "kind": "metadata",
        "available": False,
        "reason": "CODE 0 is jump-table/application metadata, not ordinary m68k code",
    }
    assert code0_detail["preview_windows"] == []
    assert code0_detail["jump_table_rows"] == [
        {
            "kind": "code0_jump_table_entry",
            "entry_index": 0,
            "code0_payload_offset": 16,
            "entry_size": 8,
            "raw_entry_bytes": None,
            "raw_entry_fields": {"jump_table_start": 16, "entry_size": 8},
            "target_resource_id": 1,
            "jump_table_offset": 0,
            "routine_offset_from_segment": 4,
            "accepted_layout": {
                "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                "fact_id": "macos.jump_table.entries.accepted",
                "fact_status": "validated",
                "parser_use": "accepted_parser_output",
            },
            "candidate_target": {
                "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                "fact_id": "macos.code_resource.jump_table.routine_offsets.candidate",
                "fact_status": "candidate",
                "parser_use": "candidate_only",
                "classification": "candidate_routine_entry",
            },
        },
        {
            "kind": "code0_jump_table_entry",
            "entry_index": 1,
            "code0_payload_offset": 24,
            "entry_size": 8,
            "raw_entry_bytes": None,
            "raw_entry_fields": {"jump_table_start": 16, "entry_size": 8},
            "target_resource_id": 2,
            "jump_table_offset": 8,
            "routine_offset_from_segment": 6,
            "accepted_layout": {
                "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                "fact_id": "macos.jump_table.entries.accepted",
                "fact_status": "validated",
                "parser_use": "accepted_parser_output",
            },
            "candidate_target": {
                "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
                "fact_id": "macos.code_resource.jump_table.routine_offsets.candidate",
                "fact_status": "candidate",
                "parser_use": "candidate_only",
                "classification": "candidate_routine_entry",
            },
        },
    ]
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
    assert code2_detail["preview_windows"][0].get("backend") != "amiga-raw"
    assert code2_detail["preview_windows"][0].get("wrapped_backend") != "amiga-raw"
    assert code2_detail["preview_windows"][0]["start"] == 6
    assert code2_detail["preview_windows"][0]["end"] == 10
    assert code2_detail["preview_windows"][0]["fact_status"] == "candidate"
    assert code2_detail["preview_windows"][0]["parser_use"] == "candidate_only"
    assert code2_detail["preview_windows"][0]["deferred_reasons"][0]["parser_use"] == "deferred_only"
    assert [row["offset"] for row in code2_detail["preview_windows"][0]["rows"]] == [6, 8]
    assert all(row["fact_status"] == "candidate" for row in code2_detail["preview_windows"][0]["rows"])
    assert all(row["parser_use"] == "candidate_only" for row in code2_detail["preview_windows"][0]["rows"])
    assert all(row["offset"] >= 6 and row["end"] <= 10 for row in code2_detail["preview_windows"][0]["rows"])
    assert code2_detail["preview_windows"][0]["rows"][0]["text"] == "movea.l (a7)+,a0"
    assert code2_detail["preview_windows"][0]["rows"][0]["decode_status"] == "decoded"
    assert code2_detail["preview_windows"][0]["rows"][0]["decoded"] is True
    assert code2_detail["preview_windows"][0]["rows"][0]["row_kind"] == "instruction"
    assert code2_detail["preview_windows"][0]["rows"][0]["fallback_reason"] is None
    assert code3_detail["listing"]["kind"] == "candidate_preview"
    code3_restored = code3_detail["restored_source"]
    assert [item["role"] for item in code3_restored["source_ownership_ranges"]] == [
        "metadata",
        "unknown",
        "candidate_code",
    ]
    assert code3_restored["source_ownership_ranges"][1]["source_visible"] is True
    assert code3_restored["source_ownership_ranges"][1]["status"] == "deferred"
    assert code3_restored["source_coverage_verifier"]["ok"] is True
    assert code3_detail["preview_windows"][0]["rows"] == [
        {
            "offset": 6,
            "end": 7,
            "size": 1,
            "bytes": "20",
            "directive": "dc.b",
            "value": 32,
            "text": "dc.b $20",
            "row_kind": "data",
            "decoded": False,
            "decode_status": "fallback_data",
            "fallback_reason": "preview shorter than one m68k instruction word",
            "range_kind": "candidate_code",
            "evidence": "m68k_movea_l_stack_to_a0_entry",
            "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        }
    ]
    assert calls["decode_bytes"] == [b"\x20\x5f\x4e\x75"]
    assert calls["decode_display_paths"] == ["Mac OS candidate preview CODE 2 FPOpTable"]
    assert calls["decode_closed"] is True
    assert calls["extract_args"] == [
        (b"hfs", "MPW-GM/MPW/Tools/Asm", 2, tmp_path),
        (b"hfs", "MPW-GM/MPW/Tools/Asm", 3, tmp_path),
    ]
    navigation_groups = container["navigation"]["groups"]
    assert navigation_groups[0]["id"] == "macos-code-resources"
    assert len(navigation_groups[0]["items"]) == 4
    assert navigation_groups[1]["id"] == "macos-code-anchors"
    listing = container["selected_code_segment"]["listing"]
    assert listing["backend"] == "macos-code"
    assert listing["source_kind"] == "macos_code_resource"
    assert listing.get("wrapped_backend") != "amiga-raw"
    assert listing["native_source"]["resource_id"] == 1
    assert {
        key: value
        for key, value in listing.items()
        if key not in {"backend", "source_kind", "native_source", "restored_source"}
    } == {
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


def test_022_012_project_restored_source_missing_c_packet_fails_closed() -> None:
    code = {
        "layout_ranges": [
            {
                "kind": "candidate_code",
                "start": 0,
                "size": 2,
                "end": 2,
                "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
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
    }

    restored = macos_project_payload._c_owned_restored_source_packet(code, scope="selected CODE")

    assert restored == {
        "model": "restored_source_missing",
        "status": "blocked",
        "authority": "missing_c_owned_model",
        "reason": "selected CODE restored-source evidence is missing from the C-owned model",
    }
    assert "source_ownership_ranges" not in restored
    assert "source_reference_records" not in restored
    assert "source_coverage_verifier" not in restored


def test_021_011_macos_preview_decode_source_stays_native() -> None:
    source = (PROJECT_ROOT / "amiga_reversing" / "disasm" / "macos_project_payload.py").read_text(encoding="utf-8")
    start = source.index("def _preview_decode_rows(")
    end = source.index("def _decoded_preview_rows(", start)
    body = source[start:end]

    assert "build_macos_code_bytes_listing_artifact_profile(" in body
    assert "RawBinarySource" not in body
    assert "NamedTemporaryFile" not in body
    assert "build_listing_artifact_profile_from_binary_source(" not in body
    assert "amiga-raw" not in body


def test_macos_code_preview_extraction_cache_hits_and_isolates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[bytes, str, int, object]] = []

    def fake_extract(data: bytes, hfs_path: str, resource_id: int, **kwargs: object) -> bytes:
        calls.append((data, hfs_path, resource_id, kwargs.get("project_root")))
        return f"{hfs_path}:{resource_id}".encode("ascii")

    monkeypatch.setattr(macos_project_payload, "extract_macos_hfs_code_resource_bytes_with_c_backend", fake_extract)
    extraction_cache: dict[tuple[str, str, int], bytes] = {}

    first = macos_project_payload._extract_macos_code_resource_payload(
        b"hfs-one",
        source_image="image-a",
        hfs_path="MPW-GM/MPW/Tools/Asm",
        resource_id=2,
        project_root=tmp_path,
        extraction_cache=extraction_cache,
    )
    second = macos_project_payload._extract_macos_code_resource_payload(
        b"hfs-one",
        source_image="image-a",
        hfs_path="MPW-GM/MPW/Tools/Asm",
        resource_id=2,
        project_root=tmp_path,
        extraction_cache=extraction_cache,
    )
    different_resource = macos_project_payload._extract_macos_code_resource_payload(
        b"hfs-one",
        source_image="image-a",
        hfs_path="MPW-GM/MPW/Tools/Asm",
        resource_id=3,
        project_root=tmp_path,
        extraction_cache=extraction_cache,
    )
    different_hfs_path = macos_project_payload._extract_macos_code_resource_payload(
        b"hfs-one",
        source_image="image-a",
        hfs_path="MPW-GM/MPW/Tools/Link",
        resource_id=2,
        project_root=tmp_path,
        extraction_cache=extraction_cache,
    )
    different_source_image = macos_project_payload._extract_macos_code_resource_payload(
        b"hfs-two",
        source_image="image-b",
        hfs_path="MPW-GM/MPW/Tools/Asm",
        resource_id=2,
        project_root=tmp_path,
        extraction_cache=extraction_cache,
    )

    assert first == second == b"MPW-GM/MPW/Tools/Asm:2"
    assert different_resource == b"MPW-GM/MPW/Tools/Asm:3"
    assert different_hfs_path == b"MPW-GM/MPW/Tools/Link:2"
    assert different_source_image == b"MPW-GM/MPW/Tools/Asm:2"
    assert calls == [
        (b"hfs-one", "MPW-GM/MPW/Tools/Asm", 2, tmp_path),
        (b"hfs-one", "MPW-GM/MPW/Tools/Asm", 3, tmp_path),
        (b"hfs-one", "MPW-GM/MPW/Tools/Link", 2, tmp_path),
        (b"hfs-two", "MPW-GM/MPW/Tools/Asm", 2, tmp_path),
    ]


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
    non_code_details = container["resource_fork"]["non_code_resource_details"]
    assert non_code_details
    assert {item["resource_type"] for item in non_code_details} == {"acur", "CURS", "cmdo", "vers"}
    curs_detail = next(item for item in non_code_details if item["resource_type"] == "CURS")
    candidate_details = [item for item in non_code_details if item["resource_type"] != "CURS"]
    assert curs_detail["semantic_status"] == "validated"
    assert curs_detail["fact_id"] == "macos.resource_fork.curs.layout.accepted"
    assert curs_detail["fact_status"] == "validated"
    assert curs_detail["parser_use"] == "accepted_parser_output"
    assert curs_detail["semantic"] == {
        "kind": "classic_cursor_16x16",
        "image_bytes": 32,
        "mask_bytes": 32,
        "hotspot_bytes": 4,
    }
    assert all(item["fact_status"] == "candidate" for item in candidate_details)
    assert all(item["parser_use"] == "candidate_only" for item in candidate_details)
    assert all(item["payload_decode_status"] == "unsupported" for item in non_code_details)
    placeholders = container["executable_resource_placeholders"]
    assert placeholders
    assert {item["resource_type"] for item in placeholders} == {"acur", "CURS", "cmdo", "vers"}
    assert all(item["source_visible"] is True for item in placeholders)
    assert all(item["stable_identity"].startswith("macos-resource:") for item in placeholders)
    assert all(item["reference_sites"][0]["kind"] == "resource_type_inventory" for item in placeholders)
    assert len(container["code_resource_details"]) == len(container["code_resources"])
    assert container["code_resource_details"][0]["role"] == "code0_metadata"
    assert container["code_resource_details"][0]["listing"]["kind"] == "metadata"
    assert container["code_resource_details"][0]["listing"]["available"] is False
    assert container["code_resource_details"][0]["preview_windows"] == []
    assert container["code_resource_details"][0]["jump_table_rows"]
    assert all(
        row["accepted_layout"]["fact_status"] == "validated"
        for row in container["code_resource_details"][0]["jump_table_rows"]
    )
    assert any(
        row["candidate_target"]["fact_status"] == "candidate"
        for row in container["code_resource_details"][0]["jump_table_rows"]
    )
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
    assert any(
        row.get("decode_status") == "decoded" and row.get("row_kind") == "instruction"
        for detail in preview_details
        for preview in detail["preview_windows"]
        for row in preview["rows"]
    )
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
    assert payload["native_source"]["backend"] == "macos-code"
    assert payload["native_source"]["source_kind"] == "macos_code_resource"
    assert payload["native_source"]["wrapped_backend"] is None
    assert container["native_source"]["source_kind"] == "macos_code_resource"
    assert container["selected_code_segment"]["native_source"]["resource_id"] == 1
    assert container["selected_code_segment"]["listing"]["source_kind"] == "macos_code_resource"
    assert container["selected_code_segment"]["code_bytes_size"] == 28984
    assert container["selected_code_segment"]["code_layout"][2]["kind"] == "candidate_code"
    assert container["selected_code_segment"]["code_layout"][2]["fact_status"] == "candidate"
    restored_source = container["selected_code_segment"]["restored_source"]
    assert restored_source["model"] == "restored_source_model_v1"
    assert restored_source["round_trip_required"] is False
    assert restored_source["source_coverage_verifier"]["ok"] is True
    assert [item["role"] for item in restored_source["source_ownership_ranges"]] == [
        "metadata",
        "data",
        "candidate_code",
    ]
    assert restored_source["source_reference_records"][0]["fact_id"] == "macos.segment_loader.relocation_fixups.deferred"
    assert restored_source["platform_extensions"]["a5_world"]["status"] == "deferred"
    assert container["selected_code_segment"]["orphan_ranges"][0]["fact_status"] == "candidate"
    assert container["selected_code_segment"]["relocation_fixups"]["parser_use"] == "deferred_only"
    assert payload["provenance"]["source_image"] == IMAGE_PATH.as_posix()
