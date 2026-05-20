from __future__ import annotations

import json
from pathlib import Path

from amiga_reversing.disasm.macos_fork_roles import (
    classify_inventory_items,
    resource_type_counts,
)

INVENTORY_PATH = Path("ext/macos_includes/mpw_gm/inventory.json")
ASM_CODE_RESOURCES_PATH = Path("ext/macos_tools/mpw_gm/asm_code_resources.json")
SAMPLE_A_PATH = "MPW-GM/MPW/Examples/AExamples/Sample.a"
ASM_PATH = "MPW-GM/MPW/Tools/Asm"


def _inventory_items() -> list[dict[str, object]]:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    items = inventory["items"]
    assert isinstance(items, list)
    return items


def _classified_by_path(paths: list[str]) -> dict[str, dict[str, object]]:
    resource_summary = json.loads(ASM_CODE_RESOURCES_PATH.read_text(encoding="utf-8"))
    entries = classify_inventory_items(
        _inventory_items(),
        selected_paths=paths,
        resource_type_counts_by_path={ASM_PATH: resource_type_counts(resource_summary)},
    )
    return {entry["path"]: entry for entry in entries if isinstance(entry["path"], str)}


def test_aexamples_text_files_classify_data_as_source_and_resource_as_editor_metadata() -> None:
    sample = _classified_by_path([SAMPLE_A_PATH])[SAMPLE_A_PATH]

    assert sample["cnid"] == 1543
    assert sample["type"] == "TEXT"
    assert sample["creator"] == "MPS "
    assert sample["data_size"] == 40288
    assert sample["resource_size"] == 430
    assert sample["fork_roles"] == {
        "data": {
            "role": "source_text",
            "evidence": [
                "ext/macos_includes/mpw_gm/inventory.json",
                "docs/macos-initial-analysis-research.md:276-290",
            ],
        },
        "resource": {
            "role": "editor_metadata",
            "evidence": [
                "ext/macos_includes/mpw_gm/inventory.json",
                "docs/macos-initial-analysis-research.md:276-290",
            ],
            "resource_types": {"MPSR": 2},
        },
    }


def test_mpw_asm_classifies_resource_fork_as_executable_and_data_fork_as_payload() -> None:
    asm = _classified_by_path([ASM_PATH])[ASM_PATH]

    assert asm["cnid"] == 2310
    assert asm["type"] == "MPST"
    assert asm["creator"] == "MPS "
    assert asm["data_size"] == 10752
    assert asm["resource_size"] == 213850
    assert asm["fork_roles"] == {
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
    }


def test_object_and_library_like_payload_types_classify_as_object_payloads() -> None:
    rows = classify_inventory_items(
        [
            {
                "path": "MPW-GM/MPW/Examples/AExamples/Count.a.o",
                "cnid": 1,
                "type": "OBJ ",
                "creator": "MPS ",
                "data_size": 64,
                "resource_size": 0,
            },
            {
                "path": "MPW-GM/MPW/Libraries/Runtime.o",
                "cnid": 2,
                "type": "XCOF",
                "creator": "MPS ",
                "data_size": 128,
                "resource_size": 0,
            },
            {
                "path": "MPW-GM/MPW/Libraries/Interface.o",
                "cnid": 3,
                "type": "stub",
                "creator": "MPS ",
                "data_size": 256,
                "resource_size": 0,
            },
        ]
    )

    assert [row["fork_roles"]["data"]["role"] for row in rows] == [
        "object_payload",
        "object_payload",
        "object_payload",
    ]
    assert all(row["fork_roles"]["resource"]["role"] == "absent" for row in rows)


def test_selected_inventory_drift_check_keeps_required_fixture_records_present() -> None:
    paths = [
        "MPW-GM/MPW/Examples/AExamples/Count.a",
        "MPW-GM/MPW/Examples/AExamples/Count.r",
        "MPW-GM/MPW/Examples/AExamples/FStubs.a",
        "MPW-GM/MPW/Examples/AExamples/Instructions",
        "MPW-GM/MPW/Examples/AExamples/MakeFile",
        "MPW-GM/MPW/Examples/AExamples/MemorySrc.a",
        SAMPLE_A_PATH,
        "MPW-GM/MPW/Examples/AExamples/Sample.h",
        "MPW-GM/MPW/Examples/AExamples/Sample.inc1.a",
        "MPW-GM/MPW/Examples/AExamples/Sample.make",
        "MPW-GM/MPW/Examples/AExamples/Sample.r",
        "MPW-GM/MPW/Examples/AExamples/SampleMisc.a",
        ASM_PATH,
    ]

    classified = _classified_by_path(paths)

    assert set(classified) == set(paths)
    for path in paths[:-1]:
        entry = classified[path]
        assert entry["type"] == "TEXT"
        assert entry["creator"] == "MPS "
        assert entry["resource_size"] == 430
        assert entry["fork_roles"]["data"]["role"] == "source_text"
        assert entry["fork_roles"]["resource"]["role"] == "editor_metadata"
