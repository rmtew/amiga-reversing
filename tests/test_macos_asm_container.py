from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    build_listing_artifact_profile_from_binary_source,
)
from amiga_reversing.disasm.macos_asm_container import (
    DEFAULT_NDIF2RAW_PATH,
    MPW_ASM_PATH,
    extract_mpw_asm_code_bytes,
    import_mpw_asm_container,
)
from amiga_reversing.disasm.macos_listing_source import MacosCodeListingArtifact

IMAGE_PATH = Path("resources/platform_macos/MPW-GM.img.bin")
ASM_CODE_RESOURCES_PATH = Path("ext/macos_tools/mpw_gm/asm_code_resources.json")


def _requires_real_fixture() -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    if not DEFAULT_NDIF2RAW_PATH.exists():
        pytest.skip("ndif2raw provider is not available")


def _imported() -> dict[str, Any]:
    _requires_real_fixture()
    return cast(dict[str, Any], import_mpw_asm_container(IMAGE_PATH))


def _code_resource(summary: dict[str, Any], resource_id: int) -> dict[str, Any]:
    for resource in summary["resources"]:
        assert isinstance(resource, dict)
        if resource.get("type") == "CODE" and resource.get("id") == resource_id:
            return cast(dict[str, Any], resource)
    raise AssertionError(f"CODE {resource_id} not found")


def test_real_asm_hfs_item_is_recognized_with_fork_roles() -> None:
    container = _imported()

    assert container["platform"] == "macos"
    assert container["volume"]["name"] == "MPW-GM"
    assert container["file"] == {
        "path": MPW_ASM_PATH,
        "cnid": 2310,
        "type": "MPST",
        "creator": "MPS ",
        "data_size": 10752,
        "resource_size": 213850,
        "fork_roles": {
            "data": {
                "role": "data_string_payload",
                "evidence": [
                    "ext/macos_includes/mpw_gm/inventory.json",
                    "docs/macos-initial-analysis-research.md:294-309",
                ],
            },
            "resource": {
                "role": "executable_resource_fork",
                "evidence": [
                    "ext/macos_includes/mpw_gm/inventory.json",
                    "docs/macos-initial-analysis-research.md:294-309",
                    "ext/macos_tools/mpw_gm/asm_code_resources.json",
                ],
                "resource_types": {"CODE": 28},
            },
        },
    }
    assert container["data_fork"]["role"] == "data_string_payload"
    assert container["data_fork"]["size"] == 10752


def test_real_asm_code_inventory_matches_committed_drift_metadata() -> None:
    container = _imported()
    expected = json.loads(ASM_CODE_RESOURCES_PATH.read_text(encoding="utf-8"))
    expected_code0 = _code_resource(expected, 0)
    expected_code1 = _code_resource(expected, 1)

    assert container["resource_fork"]["header"] == expected["header"]
    resource_types = container["resource_fork"]["types"]
    assert {"type": "CODE", "count": 28} in resource_types
    assert {"type": "vers", "count": 1} in resource_types
    assert len(container["code_resources"]) == 28
    assert container["code0"] == {
        "role": "jump_table_segment",
        "resource": {
            "type": "CODE",
            "id": 0,
            "name": None,
            "size": expected_code0["size"],
            "sha256": expected_code0["sha256"],
            "code": expected_code0["code"],
        },
        "metadata": expected_code0["code"],
    }
    assert container["selected_code_segment"]["name"] == "Main"
    assert container["selected_code_segment"]["payload_size"] == expected_code1["size"]
    assert container["selected_code_segment"]["sha256"] == expected_code1["sha256"]


def test_code1_main_has_code_byte_listing_preview_and_explicit_unsupported_state() -> None:
    container = _imported()
    selected = container["selected_code_segment"]

    assert selected["resource_type"] == "CODE"
    assert selected["id"] == 1
    assert selected["role"] == "code_segment"
    assert selected["code_header_size"] == 4
    assert selected["code_entry_offset"] == 40
    assert selected["code_bytes_size"] == 28984
    assert selected["code_layout"][:3] == [
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
            "size": 36,
            "end": 40,
            "entrypoint": False,
            "evidence": "prefix_before_stack_entry",
            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        },
        {
            "kind": "candidate_code",
            "start": 40,
            "size": 28984,
            "end": 29024,
            "entrypoint": True,
            "evidence": "m68k_movea_l_stack_to_a0_entry",
            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
        },
    ]
    assert selected["listing_preview"][:4] == [
        {"offset": 0, "bytes": "20 5F", "directive": "dc.w", "value": "$205F"},
        {"offset": 2, "bytes": "20 0F", "directive": "dc.w", "value": "$200F"},
        {"offset": 4, "bytes": "90 B8", "directive": "dc.w", "value": "$90B8"},
        {"offset": 6, "bytes": "01 14", "directive": "dc.w", "value": "$0114"},
    ]
    assert container["unsupported"] == [
        "relocation/fixups",
        "complete Segment Loader behavior",
        "source mapping",
        "byte-for-byte round-trip",
    ]


def test_code1_main_is_decodable_by_existing_m68k_listing_backend(tmp_path: Path) -> None:
    _requires_real_fixture()
    container = _imported()
    selected = container["selected_code_segment"]
    code_bytes = extract_mpw_asm_code_bytes(IMAGE_PATH, resource_id=1)
    code_path = tmp_path / "mpw_asm_CODE_1_Main.bin"
    code_path.write_bytes(code_bytes[:256])

    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=code_path,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path="MPW/Tools/Asm CODE 1 Main",
        analysis_cache_path=tmp_path / "mpw_asm_CODE_1_Main.analysis",
    )

    _total_rows, _profile, raw_artifact = build_listing_artifact_profile_from_binary_source(source)
    artifact = MacosCodeListingArtifact(
        raw_artifact,
        {
            "hfs_path": MPW_ASM_PATH,
            "fork": "resource",
            "resource_type": "CODE",
            "resource_id": 1,
            "resource_name": "Main",
            "classified_range": selected["code_layout"][2],
        },
    )
    try:
        listing, _listing_profile = artifact.source_text_with_profile()
    finally:
        artifact.close()

    assert "; Classic Mac OS CODE resource listing" in listing
    assert "SECTION code,code" not in listing
    assert "ori.b #16,d0" not in listing
    assert "movea.l (a7)+,a0" in listing
