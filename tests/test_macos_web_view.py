from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from amiga_reversing.disasm.macos_asm_container import (
    DEFAULT_NDIF2RAW_PATH,
    import_mpw_asm_container,
)
from amiga_reversing.disasm.macos_source_project import build_macos_source_project
from amiga_reversing.disasm.macos_source_render import render_macos_source_views
from amiga_reversing.disasm.macos_web_view import build_macos_starter_web_payload

IMAGE_PATH = Path("resources/platform_macos/MPW-GM.img.bin")
MPW_DEPENDENCY = "\u00c4"
MPW_CONTINUATION = "\u00b6"


def _requires_real_fixture() -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    if not DEFAULT_NDIF2RAW_PATH.exists():
        pytest.skip("ndif2raw provider is not available")


def _source_project() -> dict[str, Any]:
    sample_inc = "rMenuBar EQU 128\nrWindow EQU 128\n"
    return cast(dict[str, Any], build_macos_source_project(
        project_id="mpw-sample",
        source_files={
            "MPW-GM/MPW/Examples/AExamples/Sample.a": """
\tIMPORT\t_WaitNextEvent
\tSEG\t'Initialize'
Initialize\tPROC
EventRecord\tRECORD\t0
\tENDR
\tENDP
\tSEG\t'Main'
StartUp\tMAIN
\tIMPORT\t_GetResource
\tENDP
""",
            "MPW-GM/MPW/Examples/AExamples/SampleMisc.a": """
\tSEG\t'Initialize'
GoGetRect\tFUNC\tEXPORT
\tENDF
""",
        },
        resource_files={
            "MPW-GM/MPW/Examples/AExamples/Sample.r": """
resource 'MBAR' (rMenuBar, preload) {
};
resource 'WIND' (rWindow, preload, purgeable) {
};
"""
        },
        build_files={
            "MPW-GM/MPW/Examples/AExamples/Sample.make": f"""
AObjs           = Sample.a.o {MPW_CONTINUATION}
                    SampleMisc.a.o

Sample          {MPW_DEPENDENCY}{MPW_DEPENDENCY} {{AObjs}} Sample.make
    Link -o {{Targ}} {{AObjs}}
    SetFile {{Targ}} -t APPL -c 'MOOS' -a B

Sample          {MPW_DEPENDENCY}{MPW_DEPENDENCY} Sample.r Sample.h Sample.make
    Rez -rd -o {{Targ}} Sample.r -append
"""
        },
        c_header_text="#define rMenuBar 128\n#define rWindow 128\n",
        asm_include_text=sample_inc,
    ))


def _payload() -> dict[str, Any]:
    _requires_real_fixture()
    source_project = _source_project()
    return cast(dict[str, Any], build_macos_starter_web_payload(
        source_project=source_project,
        source_render=render_macos_source_views(source_project),
        asm_container=import_mpw_asm_container(IMAGE_PATH),
    ))


def test_macos_web_source_payload_exposes_required_pivots() -> None:
    source_view = _payload()["source_view"]
    assert source_view["kind"] == "macos_source_project"
    pivots = source_view["pivots"]

    assert [item["file_name"] for item in pivots["source_files"]] == ["Sample.a", "SampleMisc.a"]
    assert [item["name"] for item in pivots["segments"]] == ["Initialize", "Main", "Initialize"]
    assert [item["name"] for item in pivots["routines"]] == ["Initialize", "StartUp", "GoGetRect"]
    assert [item["type"] for item in pivots["resources"]] == ["MBAR", "WIND"]
    assert [item["target"] for item in pivots["build_products"]] == ["Sample"]
    assert {item["name"] for item in pivots["api_facts"]} == {"_WaitNextEvent", "_GetResource", "EventRecord"}


def test_macos_web_container_payload_exposes_forks_code_and_unsupported_state() -> None:
    payload = _payload()
    container = payload["binary_container_view"]

    assert container["finder"] == {"type": "MPST", "creator": "MPS ", "cnid": 2310}
    assert [fork["name"] for fork in container["forks"]] == ["data", "resource"]
    assert container["code0"]["metadata"]["kind"] == "jump_table_segment"
    assert len(container["code_resources"]) == 28
    assert container["native_source"]["backend"] == "macos-code"
    assert container["native_source"]["source_kind"] == "macos_code_resource"
    assert container["selected_code_segment"]["name"] == "Main"
    assert container["selected_code_segment"]["native_source"]["resource_id"] == 1
    assert container["selected_code_segment"]["listing_preview"][0]["value"] == "$205F"
    restored_source = container["selected_code_segment"]["restored_source"]
    assert restored_source["model"] == "restored_source_model_v1"
    assert restored_source["authority"] == "c_owned"
    assert restored_source["round_trip_required"] is False
    assert restored_source["source_coverage_verifier"]["ok"] is True
    assert restored_source["source_ownership_ranges"]
    assert restored_source["source_reference_records"][0]["kind"] == "segment_loader_fixup_placeholder"
    assert restored_source["platform_extensions"]["a5_world"]["status"] == "deferred"
    placeholders = container["executable_resource_placeholders"]
    assert placeholders
    assert all(item["kind"] == "executable_resource_placeholder" for item in placeholders)
    assert all(item["source_visible"] is True for item in placeholders)
    assert all(item["source_context"]["status"] == "unlinked" for item in placeholders)
    assert all(item["reference_sites"][0]["kind"] == "resource_type_inventory" for item in placeholders)
    assert all(item["reference_sites"][0]["stable_identity"] == item["stable_identity"] for item in placeholders)
    assert all(item["reference_sites"][0]["link_status"] == "unlinked" for item in placeholders)
    assert container["source_mapping"] == {
        "maps_to_sample_source": False,
        "reason": "observed MPW/Tools/Asm CODE resources are not inferred from Sample source segments",
    }
    assert "byte-for-byte round-trip" in payload["unsupported"]


def test_022_012_web_payload_preserves_c_owned_restored_source_packet() -> None:
    packet = {
        "model": "restored_source_model_v1",
        "authority": "c_owned",
        "round_trip_required": False,
        "source_ownership_ranges": [{"role": "candidate_code", "start": 0, "end": 2, "status": "candidate"}],
        "source_reference_records": [{"kind": "segment_loader_fixup_placeholder"}],
        "source_coverage_verifier": {"ok": True},
    }
    payload = build_macos_starter_web_payload(
        source_project={"kind": "macos_source_project"},
        source_render={},
        asm_container={
            "container_kind": "hfs_file_with_resource_fork",
            "file": {"path": "MPW-GM/MPW/Tools/Asm"},
            "data_fork": {},
            "resource_fork": {"types": []},
            "selected_code_segment": {"id": 1, "restored_source": packet},
        },
    )

    assert payload["binary_container_view"]["selected_code_segment"]["restored_source"] == packet


def test_022_012_web_payload_missing_c_restored_source_fails_closed() -> None:
    payload = build_macos_starter_web_payload(
        source_project={"kind": "macos_source_project"},
        source_render={},
        asm_container={
            "container_kind": "hfs_file_with_resource_fork",
            "file": {"path": "MPW-GM/MPW/Tools/Asm"},
            "data_fork": {},
            "resource_fork": {"types": []},
            "selected_code_segment": {
                "id": 1,
                "code_layout": [{"kind": "candidate_code", "start": 0, "end": 2}],
                "relocation_fixups": {"status": "deferred"},
            },
        },
    )

    restored = payload["binary_container_view"]["selected_code_segment"]["restored_source"]
    assert restored == {
        "model": "restored_source_missing",
        "status": "blocked",
        "authority": "missing_c_owned_model",
        "reason": "selected CODE restored-source evidence is missing from the C-owned model",
    }
    assert "source_ownership_ranges" not in restored
    assert "source_reference_records" not in restored
    assert "source_coverage_verifier" not in restored


def test_macos_web_payload_keeps_source_and_observed_binary_facts_distinct() -> None:
    boundary = _payload()["source_binary_boundary"]

    assert boundary["source_project_kind"] == "macos_source_project"
    assert boundary["binary_container_kind"] == "hfs_file_with_resource_fork"
    assert boundary["source_segments_map_to_observed_code_resources"] is False
    assert boundary["observed_code_fixture"] == "MPW-GM/MPW/Tools/Asm"
