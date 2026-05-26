from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any, cast

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    MacosCodeAddressModel,
    MacosCodeResourceSource,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    CListingArtifact,
    build_flat_m68k_bytes_listing_artifact_profile,
    build_listing_artifact_profile_from_binary_source,
    build_macos_code_bytes_listing_artifact_profile,
    extract_macos_hfs_code_resource_bytes_with_c_backend,
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import (
    DEFAULT_NDIF2RAW_PATH,
    read_macos_hfs_image_bytes,
)
from amiga_reversing.disasm.macos_code_provider import (
    macos_code_resource_byte_view_with_c_backend,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.tools import platform_executable_formats
from src.tests._build_helpers import require_built_tools

IMAGE_PATH = Path("resources/platform_macos/MPW-GM.img.bin")
ASM_CODE_RESOURCES_PATH = Path("ext/macos_tools/mpw_gm/asm_code_resources.json")


def _u16(value: int) -> bytes:
    return struct.pack(">H", value)


def _u24(value: int) -> bytes:
    return value.to_bytes(3, "big")


def _u32(value: int) -> bytes:
    return struct.pack(">I", value)


def _put(data: bytearray, offset: int, payload: bytes) -> None:
    data[offset : offset + len(payload)] = payload


def _put_name_key(node: bytearray, offset: int, parent_id: int, name: str) -> None:
    encoded = name.encode("macroman")
    node[offset] = 6 + len(encoded)
    _put(node, offset + 2, _u32(parent_id))
    node[offset + 6] = len(encoded)
    _put(node, offset + 7, encoded)


def _put_extent(data: bytearray, offset: int, start: int, count: int) -> None:
    _put(data, offset, _u16(start) + _u16(count))


def _make_code_resource_fork() -> bytes:
    data = bytearray(512)
    data_offset = 0x100
    map_offset = 0x140
    map_length = 0x60
    code0_payload = data_offset + 4
    code1_record = data_offset + 36
    code1_payload = code1_record + 4
    type_list = map_offset + 28
    ref_list = type_list + 10
    for offset, value in (
        (0, data_offset),
        (4, map_offset),
        (8, 54),
        (12, map_length),
        (map_offset, data_offset),
        (map_offset + 4, map_offset),
        (map_offset + 8, 54),
        (map_offset + 12, map_length),
    ):
        _put(data, offset, _u32(value))
    _put(data, data_offset, _u32(32))
    _put(data, code0_payload, _u32(48) + _u32(64) + _u32(16) + _u32(32))
    _put(data, code0_payload + 16, _u16(10) + b"\x3f\x3c\x00\x01\xa9\xf0")
    _put(data, code0_payload + 24, _u16(12) + b"\x3f\x3c\x00\x01\xa9\xf0")
    _put(data, code1_record, _u32(14))
    _put(data, code1_payload, _u16(0) + _u16(2) + b"\x00\x00\x00\x10\x00\x00\x20\x5f\x4e\x75")
    _put(data, map_offset + 24, _u16(28))
    _put(data, map_offset + 26, _u16(58))
    _put(data, type_list, _u16(0) + b"CODE" + _u16(1) + _u16(10))
    _put(data, ref_list, _u16(0) + _u16(0xFFFF) + b"\x20" + _u24(0) + b"\x00\x00\x00\x00")
    _put(data, ref_list + 12, _u16(1) + _u16(0xFFFF) + b"\x00" + _u24(36) + b"\x00\x00\x00\x00")
    return bytes(data)


def _make_hfs_image() -> bytes:
    image = bytearray(4096)
    mdb = 1024
    catalog_offset = 2048
    leaf_offset = catalog_offset + 512
    directory_record = 14
    directory_data = 26
    file_record = 80
    file_data = 90
    image[mdb : mdb + 2] = b"BD"
    _put(image, mdb + 18, _u16(16))
    _put(image, mdb + 20, _u32(512))
    _put(image, mdb + 28, _u16(4))
    image[mdb + 36] = 6
    _put(image, mdb + 37, b"MPW-GM")
    _put(image, mdb + 146, _u32(1024))
    _put_extent(image, mdb + 150, 0, 2)
    _put(image, catalog_offset + 10, _u16(1))
    _put(image, catalog_offset + 512 - 2, _u16(14))
    _put(image, catalog_offset + 14 + 18, _u16(512))
    image[leaf_offset + 8] = 0xFF
    _put(image, leaf_offset + 10, _u16(2))
    _put_name_key(image, leaf_offset + directory_record, 2, "Tools")
    _put(image, leaf_offset + directory_data, _u16(0x0100))
    _put(image, leaf_offset + directory_data + 4, _u16(1))
    _put(image, leaf_offset + directory_data + 6, _u32(42))
    _put_name_key(image, leaf_offset + file_record, 42, "Asm")
    _put(image, leaf_offset + file_data, _u16(0x0200))
    _put(image, leaf_offset + file_data + 4, b"MPST")
    _put(image, leaf_offset + file_data + 8, b"MPS ")
    _put(image, leaf_offset + file_data + 20, _u32(2310))
    _put(image, leaf_offset + file_data + 26, _u32(128))
    _put(image, leaf_offset + file_data + 36, _u32(512))
    _put_extent(image, leaf_offset + file_data + 74, 2, 1)
    _put_extent(image, leaf_offset + file_data + 86, 3, 1)
    _put(image, leaf_offset + 512 - 2, _u16(directory_record))
    _put(image, leaf_offset + 512 - 4, _u16(file_record))
    _put(image, 2048 + 2 * 512, b"DATA-FORK")
    _put(image, 2048 + 3 * 512, _make_code_resource_fork())
    return bytes(image)


def _macos_code_descriptor(image_path: Path, resource_id: int) -> MacosCodeResourceSource:
    return MacosCodeResourceSource(
        kind=BinarySourceKind.MACOS_CODE_RESOURCE,
        source_image=image_path,
        hfs_path="MPW-GM/Tools/Asm",
        resource_type="CODE",
        resource_id=resource_id,
        resource_name="Main" if resource_id == 1 else None,
        address_model=MacosCodeAddressModel.RESOURCE_OFFSET,
        display_path=f"{image_path.as_posix()}::MPW-GM/Tools/Asm::CODE {resource_id}",
        analysis_cache_path=image_path.parent / f"CODE_{resource_id}.analysis",
        cache_identity=f"macos-code-resource:{image_path.as_posix()}:MPW-GM/Tools/Asm:CODE:{resource_id}",
        project_root=image_path.parent,
    )


def test_python_wrapper_uses_c_macos_hfs_code_summary() -> None:
    require_built_tools()
    image = _make_hfs_image()
    summary = inspect_macos_hfs_code_summary_with_c_backend(image, "MPW-GM/Tools/Asm")
    assert platform_executable_formats.validate_parser_fact_references(summary) == []
    coverage = platform_executable_formats.build_parser_fact_coverage_report([summary], labels=["macos_c_backend"])
    assert coverage["summary"]["invalid"] == 0
    assert coverage["summary"]["accepted"] >= 4
    assert coverage["summary"]["candidate"] >= 3
    assert coverage["summary"]["deferred"] >= 1
    assert summary["platform"] == "macos"
    assert summary["container_kind"] == "hfs_resource_code_file"
    assert summary["volume"]["name"] == "MPW-GM"
    assert summary["file"]["path"] == "Tools/Asm"
    assert summary["file"]["type"] == "MPST"
    assert summary["file"]["creator"] == "MPS "
    assert summary["file"]["forks"]["data"]["size"] == 128
    assert summary["file"]["forks"]["resource"]["size"] == 512
    assert summary["resource_fork"]["type_count"] == 1
    assert summary["resource_fork"]["resource_count"] == 2
    assert [item["id"] for item in summary["resource_fork"]["code_resources"]] == [0, 1]
    code0 = summary["resource_fork"]["code_resources"][0]["code"]
    assert code0["jump_table"] == {
        "kind": "code0_jump_table",
        "start": 16,
        "size": 16,
        "end": 32,
        "entry_size": 8,
        "entry_count": 2,
        "trailing_bytes": 0,
        "fact_id": "macos.jump_table.entries.accepted",
        "fact_status": "validated",
        "parser_use": "accepted_parser_output",
    }
    segment_map = summary["resource_fork"]["code_segment_map"]
    assert segment_map[0]["fact_id"] == "macos.code_resource.segment_jump_table_span.accepted"
    assert segment_map[0]["fact_status"] == "validated"
    assert segment_map[0]["routine_entry_candidates"] == [
        {
            "index": 0,
            "jump_table_offset": 0,
            "code0_payload_offset": 16,
            "routine_offset_from_segment": 10,
            "classification": "candidate_routine_entry",
            "fact_id": "macos.code_resource.jump_table.routine_offsets.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        },
        {
            "index": 1,
            "jump_table_offset": 8,
            "code0_payload_offset": 24,
            "routine_offset_from_segment": 12,
            "classification": "candidate_routine_entry",
            "fact_id": "macos.code_resource.jump_table.routine_offsets.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        },
    ]
    assert summary["selected_code"]["available"] is True
    assert summary["selected_code"]["payload_size"] == 14
    assert summary["selected_code"]["code_bytes_offset"] == summary["selected_code"]["payload_offset"] + 10
    assert summary["selected_code"]["code_bytes_size"] == 4
    assert summary["selected_code"]["code_bytes_sha256"] == hashlib.sha256(b"\x20\x5f\x4e\x75").hexdigest()
    assert summary["selected_code"]["code"]["layout_ranges"] == [
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
            "size": 6,
            "end": 10,
            "entrypoint": False,
            "evidence": "prefix_before_stack_entry",
            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        },
        {
            "kind": "candidate_code",
            "start": 10,
            "size": 4,
            "end": 14,
            "entrypoint": True,
            "evidence": "m68k_movea_l_stack_to_a0_entry",
            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        },
    ]
    assert summary["selected_code"]["code"]["orphan_ranges"] == [
        {
            "classification": "candidate_data_island",
            "start": 4,
            "size": 6,
            "end": 10,
            "evidence": "prefix_before_stack_entry",
            "reason": "bytes before candidate byte-entry evidence; exact CODE entry rule remains deferred",
            "fact_id": "macos.code_resource.orphan_layout_ranges.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        }
    ]
    assert summary["selected_code"]["code"]["relocation_fixups"] == {
        "status": "deferred",
        "reason": "Segment Loader relocation/fixup interpretation is not yet represented by the parser",
        "fact_id": "macos.segment_loader.relocation_fixups.deferred",
        "fact_status": "deferred",
        "parser_use": "deferred_only",
    }
    restored_source = summary["selected_code"]["code"]["restored_source"]
    assert restored_source["model"] == "restored_source_model_v1"
    assert restored_source["authority"] == "c_owned"
    assert restored_source["round_trip_required"] is False
    assert restored_source["source_coverage_verifier"] == {
        "ok": True,
        "gap_count": 0,
        "overlap_count": 0,
        "invalid_instruction_ownership_count": 0,
        "explicit_unknown_missing_detail_count": 0,
    }
    assert [item["role"] for item in restored_source["source_ownership_ranges"]] == [
        "metadata",
        "data",
        "candidate_code",
    ]
    assert restored_source["source_reference_records"][0]["kind"] == "segment_loader_fixup_placeholder"
    assert restored_source["source_reference_records"][0]["parser_use"] == "deferred_only"
    assert restored_source["platform_extensions"]["code_resource"]["resource_id"] == 1
    shared_ranges = summary["executable_ranges"]
    assert summary["executable_model"] == "platform_executable_summary_v1"
    assert any(
        item["resource_id"] == 0
        and item["role"] == "metadata"
        and item["stored_offset_space"] == "resource_fork_payload"
        and item["fact_id"] == "macos.code_resource.0.jump_table_metadata"
        for item in shared_ranges
    )
    assert any(
        item["resource_id"] == 1
        and item["role"] == "metadata"
        and item["fact_id"] == "macos.code_resource.nonzero.segment_header"
        and item["fact_status"] == "validated"
        for item in shared_ranges
    )
    assert any(
        item["resource_id"] == 1
        and item["role"] == "candidate_code"
        and item["stored_offset_space"] == "resource_fork_payload"
        and item["fact_id"] == "macos.code_resource.movea_stack_a0.boundary.candidate"
        and item["fact_status"] == "candidate"
        and item["parser_use"] == "candidate_only"
        for item in shared_ranges
    )
    assert summary["executable_deferred"] == [
        {
            "kind": "relocation_breadth",
            "kb_record_id": "macos.hfs_resource_fork.code_resources.mpw_application",
            "status": "deferred",
            "fact_id": "macos.segment_loader.relocation_fixups.deferred",
            "fact_status": "deferred",
            "parser_use": "deferred_only",
        }
    ]
    assert extract_macos_hfs_code_resource_bytes_with_c_backend(image, "Tools/Asm", 1) == b"\x20\x5f\x4e\x75"


def test_021_002_native_macos_code_byte_provider_returns_code1_view(tmp_path: Path) -> None:
    require_built_tools()
    image_path = tmp_path / "mpw.raw"
    image_path.write_bytes(_make_hfs_image())

    payload, profile = macos_code_resource_byte_view_with_c_backend(_macos_code_descriptor(image_path, 1))

    assert profile == {
        "backend": "macos-code",
        "source_kind": "macos_code_resource",
        "wrapped_backend": None,
        "executable_model": "platform_executable_summary_v1",
        "cache_identity": f"macos-code-resource:{image_path.as_posix()}:MPW-GM/Tools/Asm:CODE:1",
    }
    assert payload["backend"] == "macos-code"
    assert payload["source_kind"] == "macos_code_resource"
    assert payload["wrapped_backend"] is None
    assert payload["code_bytes"] == b"\x20\x5f\x4e\x75"
    assert payload["executable_model"] == "platform_executable_summary_v1"
    ranges = cast(list[dict[str, Any]], payload["executable_ranges"])
    deferred = cast(list[dict[str, Any]], payload["executable_deferred"])
    assert ranges[0]["resource_id"] == 1
    assert ranges[0]["role"] == "candidate_code"
    assert ranges[0]["fact_status"] == "candidate"
    assert ranges[0]["parser_use"] == "candidate_only"
    assert deferred[0]["fact_status"] == "deferred"
    provenance = payload["provenance"]
    assert isinstance(provenance, dict)
    assert provenance["resource_type"] == "CODE"
    assert provenance["resource_id"] == 1
    assert provenance["source_kind"] == "macos_code_resource"


def test_021_002_native_macos_code_byte_provider_fails_code0_metadata_only(tmp_path: Path) -> None:
    require_built_tools()
    image_path = tmp_path / "mpw.raw"
    image_path.write_bytes(_make_hfs_image())

    with pytest.raises(ValueError, match="metadata-only"):
        macos_code_resource_byte_view_with_c_backend(_macos_code_descriptor(image_path, 0))


def test_021_002_native_macos_code_byte_provider_fails_missing_resource(tmp_path: Path) -> None:
    require_built_tools()
    image_path = tmp_path / "mpw.raw"
    image_path.write_bytes(_make_hfs_image())

    with pytest.raises(ValueError, match="CODE 99 resource is missing"):
        macos_code_resource_byte_view_with_c_backend(_macos_code_descriptor(image_path, 99))


def test_021_002_native_macos_code_byte_provider_fails_deferred_no_entry(tmp_path: Path) -> None:
    require_built_tools()
    image = bytearray(_make_hfs_image())
    resource_fork_base = 2048 + 3 * 512
    code1_payload = 0x128
    image[resource_fork_base + code1_payload + 10 : resource_fork_base + code1_payload + 12] = b"\x4e\x75"
    image_path = tmp_path / "mpw.raw"
    image_path.write_bytes(image)

    with pytest.raises(ValueError, match="deferred byte-entry evidence"):
        macos_code_resource_byte_view_with_c_backend(_macos_code_descriptor(image_path, 1))


def test_021_007_macos_code_source_uses_native_buffer_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_built_tools()
    image_path = tmp_path / "mpw.raw"
    image_path.write_bytes(_make_hfs_image())
    calls: dict[str, object] = {}

    class FakeArtifact:
        def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return {"total_rows": 2}, {"backend": "macos-code", "source_kind": "macos_code_resource"}

        def close(self) -> None:
            calls["closed"] = True

    def fail_raw_transport(*args: object, **kwargs: object) -> object:
        raise AssertionError("Mac CODE must not enter _source_file_for_c_backend")

    def fake_create_macos_code_bytes(
        code_bytes: bytes,
        *,
        display_path: str,
        metadata_text: str,
        include_dir: str,
        project_root: Path,
    ) -> FakeArtifact:
        calls["code_bytes"] = code_bytes
        calls["display_path"] = display_path
        calls["metadata_text"] = metadata_text
        calls["include_dir"] = include_dir
        calls["project_root"] = project_root
        return FakeArtifact()

    monkeypatch.setattr(c_backend, "_source_file_for_c_backend", fail_raw_transport)
    monkeypatch.setattr(CListingArtifact, "create_macos_code_bytes", staticmethod(fake_create_macos_code_bytes))

    total_rows, profile, artifact = build_listing_artifact_profile_from_binary_source(
        _macos_code_descriptor(image_path, 1),
        project_root=tmp_path,
    )

    assert total_rows == 2
    assert profile["backend"] == "macos-code"
    assert profile["source_kind"] == "macos_code_resource"
    assert calls["code_bytes"] == b"\x20\x5f\x4e\x75"
    assert calls["display_path"] == f"{image_path.as_posix()}::MPW-GM/Tools/Asm::CODE 1"
    assert calls["project_root"] == tmp_path
    assert artifact is not None


def test_021_007_macos_code_bytes_artifact_profile_is_native(tmp_path: Path) -> None:
    require_built_tools()

    _total_rows, profile, artifact = build_macos_code_bytes_listing_artifact_profile(
        b"\x20\x5f\x4e\x75",
        display_path="Mac OS candidate preview CODE 1 Main",
        project_root=PROJECT_ROOT,
    )
    try:
        analysis, _analysis_profile = artifact.analysis_payload()
        _source_text, source_profile = artifact.source_text_with_profile()
        window, window_profile = artifact.window_payload(start=0, count=8)
    finally:
        artifact.close()

    for observed_profile in (profile, source_profile, window_profile):
        assert observed_profile["backend"] == "macos-code"
        assert observed_profile.get("wrapped_backend") != "amiga-raw"
    assert analysis["restored_source_model"] == "restored_source_model_v1"
    assert analysis["round_trip_required"] is False
    assert analysis["source_coverage_verifier"] == {
        "ok": True,
        "gap_count": 0,
        "overlap_count": 0,
        "invalid_instruction_ownership_count": 0,
        "explicit_unknown_missing_detail_count": 0,
    }
    references = cast(list[dict[str, Any]], analysis["source_reference_records"])
    assert references == [
        {
            "kind": "segment_loader_fixup_placeholder",
            "ownership_range_index": 0,
            "source_section_index": 0,
            "source_offset": 0,
            "size": 0,
            "target_section_index": None,
            "target_offset": 0,
            "addend": 0,
            "row_id": None,
            "target": "unresolved_segment_loader_fixup",
            "status": "deferred",
            "fact_id": "macos.segment_loader.relocation_fixups.deferred",
            "fact_status": "deferred",
            "parser_use": "deferred_only",
            "provenance": "platform_executable_summary_v1",
        }
    ]
    ownership = cast(list[dict[str, Any]], analysis["source_ownership_ranges"])
    assert ownership == [
        {
            "role": "candidate_code",
            "byte_space": "selected_code_bytes",
            "platform": "macos",
            "source_kind": "macos_code_resource",
            "section_index": 0,
            "start": 0,
            "size": 4,
            "stored_offset": 0,
            "stored_size": 4,
            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
            "provenance": "platform_file_facts_v2_listing_artifact_macos_code_buffer_create",
            "reason": "selected Mac CODE bytes remain candidate because byte-entry evidence is not accepted",
        }
    ]
    assert any(str(row.get("text") or "").strip() == "movea.l (a7)+,a0" for row in window["rows"])


def test_021_011_macos_code_buffer_entrypoint_stays_off_amiga_raw_internals() -> None:
    source = (PROJECT_ROOT / "src" / "platform_file_lib.c").read_text(encoding="utf-8")
    start = source.index("int platform_file_facts_v2_listing_artifact_macos_code_buffer_create(")
    end = source.index("int platform_file_facts_v2_listing_artifact_window_json_alloc(", start)
    body = source[start:end]

    assert "load_flat_m68k_object_from_buffer(" in body
    assert "configure_flat_m68k_buffer_policy(" in body
    assert "amiga-raw" not in body
    assert "load_raw_object_from_buffer(" not in body
    assert "configure_analysis_policy_for_alloc(" not in body


def test_021_009_flat_m68k_buffer_artifact_profile_is_neutral() -> None:
    require_built_tools()

    _total_rows, profile, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        b"\x20\x5f\x4e\x75",
        display_path="flat m68k test buffer",
        project_root=PROJECT_ROOT,
    )
    try:
        _source_text, source_profile = artifact.source_text_with_profile()
        window, window_profile = artifact.window_payload(start=0, count=8)
    finally:
        artifact.close()

    assert profile["backend"] == "m68k-flat-buffer"
    assert source_profile["backend"] == "m68k-flat-buffer"
    assert window_profile["backend"] == "m68k-flat-buffer"
    assert profile["backend"] != "amiga-raw"
    assert any(str(row.get("text") or "").strip() == "movea.l (a7)+,a0" for row in window["rows"])
    assert any(str(row.get("text") or "").strip() == "rts" for row in window["rows"])


def test_c_macos_summary_defers_code_without_entry_evidence() -> None:
    require_built_tools()
    image = bytearray(_make_hfs_image())
    resource_fork_base = 2048 + 3 * 512
    code1_payload = 0x128
    image[resource_fork_base + code1_payload + 10 : resource_fork_base + code1_payload + 12] = b"\x4e\x75"

    summary = inspect_macos_hfs_code_summary_with_c_backend(bytes(image), "MPW-GM/Tools/Asm")

    assert platform_executable_formats.validate_parser_fact_references(summary) == []
    assert summary["selected_code"]["code_bytes_size"] == 0
    assert summary["selected_code"]["code"]["layout_ranges"] == [
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
            "kind": "deferred",
            "start": 4,
            "size": 10,
            "end": 14,
            "entrypoint": False,
            "evidence": "missing_m68k_movea_l_stack_to_a0_entry",
            "fact_id": "macos.code_resource.byte_entry_rule.unknown",
            "fact_status": "deferred",
            "parser_use": "deferred_only",
        },
    ]
    assert summary["selected_code"]["code"]["orphan_ranges"] == [
        {
            "classification": "deferred_code_or_data_island",
            "start": 4,
            "size": 10,
            "end": 14,
            "evidence": "missing_m68k_movea_l_stack_to_a0_entry",
            "reason": "no candidate byte-entry evidence found; code/data interpretation remains deferred",
            "fact_id": "macos.code_resource.byte_entry_rule.unknown",
            "fact_status": "deferred",
            "parser_use": "deferred_only",
        }
    ]
    assert summary["selected_code"]["code"]["relocation_fixups"]["parser_use"] == "deferred_only"
    deferred_ranges = [
        item
        for item in summary["executable_ranges"]
        if item["fact_id"] == "macos.code_resource.byte_entry_rule.unknown"
    ]
    assert deferred_ranges
    assert all(item["fact_status"] == "deferred" for item in deferred_ranges)
    with pytest.raises(RuntimeError, match="no confirmed executable range"):
        extract_macos_hfs_code_resource_bytes_with_c_backend(bytes(image), "Tools/Asm", 1)


def test_c_macos_code_bytes_feed_shared_listing_artifact(tmp_path: Path) -> None:
    require_built_tools()
    code_bytes = extract_macos_hfs_code_resource_bytes_with_c_backend(_make_hfs_image(), "MPW-GM/Tools/Asm", 1)
    code_path = tmp_path / "CODE_1_Main.bin"
    code_path.write_bytes(code_bytes)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=code_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path="MPW-GM/Tools/Asm CODE 1 Main",
        analysis_cache_path=tmp_path / "CODE_1_Main.analysis",
    )

    total_rows, _profile, artifact = build_listing_artifact_profile_from_binary_source(source)
    try:
        listing, _listing_profile = artifact.window_payload(start=0, count=32)
    finally:
        artifact.close()

    rendered = "\n".join(str(row.get("text") or "") for row in listing["rows"] if isinstance(row, dict))
    assert total_rows > 0
    assert "rts" in rendered


def test_c_macos_hfs_code_summary_matches_committed_mpw_asm_metadata() -> None:
    require_built_tools()
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    if not DEFAULT_NDIF2RAW_PATH.exists():
        pytest.skip("ndif2raw provider is not available")
    expected = json.loads(ASM_CODE_RESOURCES_PATH.read_text(encoding="utf-8"))
    expected_code0 = next(item for item in expected["resources"] if item["type"] == "CODE" and item["id"] == 0)
    expected_code1 = next(item for item in expected["resources"] if item["type"] == "CODE" and item["id"] == 1)

    summary = inspect_macos_hfs_code_summary_with_c_backend(
        read_macos_hfs_image_bytes(IMAGE_PATH),
        "MPW-GM/MPW/Tools/Asm",
    )
    assert platform_executable_formats.validate_parser_fact_references(summary) == []
    code_resources = summary["resource_fork"]["code_resources"]
    code0 = next(item for item in code_resources if item["id"] == 0)

    assert summary["file"]["path"] == "MPW-GM/MPW/Tools/Asm"
    assert summary["file"]["type"] == "MPST"
    assert summary["file"]["creator"] == "MPS "
    assert len(code_resources) == 28
    assert summary["resource_fork"]["code_segment_map"]
    assert any(
        item["fact_id"] == "macos.code_resource.segment_jump_table_span.accepted"
        for item in summary["resource_fork"]["code_segment_map"]
    )
    assert code0["payload_size"] == expected_code0["size"]
    assert code0["code"]["kind"] == "jump_table_segment"
    assert code0["code"]["jump_table"]["entry_size"] == 8
    assert code0["code"]["jump_table"]["fact_id"] == "macos.jump_table.entries.accepted"
    assert code0["code"]["above_a5_size"] == expected_code0["code"]["above_a5_size"]
    assert code0["code"]["below_a5_size"] == expected_code0["code"]["below_a5_size"]
    assert summary["selected_code"]["payload_size"] == expected_code1["size"]
    assert summary["selected_code"]["payload_sha256"] == expected_code1["sha256"]
    assert summary["selected_code"]["code_bytes_offset"] == summary["selected_code"]["payload_offset"] + 40
    assert summary["selected_code"]["code_bytes_size"] == expected_code1["size"] - 40
    assert summary["selected_code"]["code"]["layout_ranges"][0]["kind"] == "metadata"
    assert summary["selected_code"]["code"]["layout_ranges"][1]["kind"] == "data"
    assert summary["selected_code"]["code"]["layout_ranges"][2]["kind"] == "candidate_code"
    assert summary["selected_code"]["code"]["layout_ranges"][2]["start"] == 40
    assert summary["selected_code"]["code"]["layout_ranges"][2]["fact_status"] == "candidate"
    shared_code0 = [
        item for item in summary["executable_ranges"] if item["resource_id"] == 0
    ]
    assert shared_code0
    assert {item["role"] for item in shared_code0} == {"metadata"}
    assert any(
        item["resource_id"] == 1
        and item["role"] == "candidate_code"
        and item["load_offset"] == 40
        and item["fact_status"] == "candidate"
        for item in summary["executable_ranges"]
    )
    assert summary["selected_code"]["code"]["orphan_ranges"][0]["fact_status"] == "candidate"
    assert summary["selected_code"]["code"]["relocation_fixups"]["parser_use"] == "deferred_only"
    assert extract_macos_hfs_code_resource_bytes_with_c_backend(
        read_macos_hfs_image_bytes(IMAGE_PATH),
        "MPW-GM/MPW/Tools/Asm",
        1,
    ).startswith(b"\x20\x5f")
