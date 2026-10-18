"""A static field-cell seed preserves its position in the owning root."""

from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    CListingArtifact,
    _CBackendSourceFile,
    effective_policy_project_source_with_c_backend,
)

ROOT = Path(__file__).resolve().parents[1]


def _seed(addr=40, end=44, field_name="node_ptr", **kwargs):
    return {
        "addr": addr,
        "end": end,
        "hunk": 0,
        "type": "data",
        "subtype": "struct",
        "unit": "long",
        "struct_name": "Root",
        "field_name": field_name,
        **kwargs,
    }


def _fields(tmp_path, seeds, target=40, instruction_tail="4a9022504a914e75", root_fields=None):
    if not (ROOT / "src/build/platform_file_lib.dll").exists():
        pytest.skip("native backend must be built")
    binary = tmp_path / "field-cell.bin"
    # LEA field-cell,A0; TST.L (A0); MOVEA.L (A0),A1; TST.L (A1); RTS.
    code = bytes.fromhex("41fa") + (target - 2).to_bytes(2, "big") + bytes.fromhex(instruction_tail)
    binary.write_bytes(code + bytes(80 - len(code)))
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({
        "target_type": "raw_binary",
        "seeded_entities": seeds,
        "custom_structs": [
            {"name": "Root", "size": 16, "fields": root_fields if root_fields is not None else [
                {"name": "geometry", "type": "long", "offset": 0, "size": 4},
                {"name": "node_ptr", "type": "long", "offset": 8, "size": 4,
                 "pointer_struct": "Node"},
            ]},
            {"name": "Node", "size": 4, "fields": [
                {"name": "value", "type": "long", "offset": 0, "size": 4},
            ]},
        ],
    }), encoding="utf-8")
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(binary),
        analysis_cache_path=tmp_path / "field-cell.analysis",
    )
    policy = effective_policy_project_source_with_c_backend(
        source, metadata_path=metadata, project_root=ROOT,
    )["analysis_policy"]
    assert {struct["name"] for struct in policy["custom_structs"]} == {"Root", "Node"}
    assert [
        (item["offset"], item["size"], item["struct_name"], item["field_name"] or "", item["field_type"])
        for item in policy["structured_data_items"]
    ] == [
        (seed["addr"], seed["end"] - seed["addr"], "Root", seed["field_name"],
         seed.get("field_type", seed["unit"]))
        for seed in seeds
    ]
    with closing(CListingArtifact.create(
        _CBackendSourceFile(binary, "amiga-raw", entry_offset=0),
        metadata_text=str(metadata),
        include_dir=str(ROOT / "ext/amiga_includes/ndk_2.0/include"),
        project_root=ROOT,
    )) as artifact:
        return artifact.query_payload("fields", limit=100)["items"]


@pytest.mark.parametrize("seed", [
    _seed(),
    _seed(addr=32, end=48, field_name="", unit="byte"),
    _seed(addr=32, end=64, field_name="", unit="byte"),
])
def test_static_field_cell_and_full_root_interior_resolve_field_eight(tmp_path, seed):
    target = 56 if seed["end"] == 64 else 40
    fields = _fields(tmp_path, [seed], target)
    assert {(field["source_offset"], field["field_name"]) for field in fields} >= {
        (4, "node_ptr"), (6, "node_ptr"), (8, "value"),
    }
    assert not any(field["field_name"] == "geometry" for field in fields)


@pytest.mark.parametrize("seeds", [
    [_seed(field_name="missing")],
    [_seed(end=42, unit="word")],
    [_seed(field_type="unknown")],
    [_seed(), _seed(field_name="geometry")],
    [_seed(addr=32, end=48, field_name="", unit="byte"), _seed(field_name="missing")],
    [_seed(field_name="missing"), _seed(addr=32, end=48, field_name="", unit="byte")],
])
def test_invalid_or_conflicting_static_field_seed_is_not_a_trusted_root(tmp_path, seeds):
    fields = _fields(tmp_path, seeds)
    assert {(field["source_offset"], field.get("status")) for field in fields} == {
        (4, "unresolved"), (6, "unresolved"),
    }
    assert all(field["field_offset"] is None for field in fields)


def test_static_field_seed_postincrement_advances_to_next_field_cursor(tmp_path):
    fields = _fields(
        tmp_path, [_seed(end=42, field_name="world_x", unit="word")],
        instruction_tail="301832104e75",  # MOVE.W (A0)+,D0; MOVE.W (A0),D1; RTS.
        root_fields=[
            {"name": "world_x", "type": "word", "offset": 8, "size": 2},
            {"name": "world_y", "type": "word", "offset": 10, "size": 2},
        ],
    )
    assert [(field["source_offset"], field.get("status"), field["field_offset"]) for field in fields] == [
        (4, None, 8),
        (6, None, 10),
    ]
    assert [field["field_name"] for field in fields] == ["world_x", "world_y"]


@pytest.mark.parametrize("instruction_tail", [
    "302032104e75",  # Predecrement enters an unmodelled prefix field gap.
    "205832104e75",  # MOVEA.L (A0)+,A0 also writes the updated base.
    "b14832104e75",  # CMPM.W (A0)+,(A0)+ has ambiguous same-base phases.
    "309832104e75",  # MOVE.W (A0)+,(A0) also uses the updated base.
    "32d832104e75",  # MOVE.W (A0)+,(A1)+ has multiple EA updates.
])
def test_static_field_seed_unmodelled_update_cannot_resolve_or_reuse_cursor(tmp_path, instruction_tail):
    fields = _fields(
        tmp_path, [_seed(end=42, field_name="world_x", unit="word")],
        instruction_tail=instruction_tail,
        root_fields=[
            {"name": "world_x", "type": "word", "offset": 8, "size": 2},
            {"name": "world_y", "type": "word", "offset": 10, "size": 2},
        ],
    )
    assert fields
    assert all(field.get("status") == "unresolved" for field in fields)
    assert all(field["field_offset"] is None for field in fields)


def test_static_field_seed_postincrement_invalidates_one_past_root(tmp_path):
    fields = _fields(
        tmp_path, [_seed(end=42, field_name="last", unit="word")],
        instruction_tail="301832104e75",
        root_fields=[{"name": "last", "type": "word", "offset": 14, "size": 2}],
    )
    assert [(field["source_offset"], field["field_offset"]) for field in fields] == [(4, 14)]


def test_static_root_array_postincrement_advances_into_declared_next_element(tmp_path):
    fields = _fields(
        tmp_path, [_seed(addr=32, end=64, field_name="", unit="byte")], target=46,
        instruction_tail="301832104e75",
        root_fields=[
            {"name": "first", "type": "word", "offset": 0, "size": 2},
            {"name": "last", "type": "word", "offset": 14, "size": 2},
        ],
    )
    assert [(field["source_offset"], field["field_offset"], field["field_name"]) for field in fields] == [
        (4, 14, "last"), (6, 0, "first"),
    ]


def test_static_root_array_postincrement_invalidates_after_declared_final_element(tmp_path):
    fields = _fields(
        tmp_path, [_seed(addr=32, end=64, field_name="", unit="byte")], target=62,
        instruction_tail="301832104e75",
        root_fields=[
            {"name": "first", "type": "word", "offset": 0, "size": 2},
            {"name": "last", "type": "word", "offset": 14, "size": 2},
        ],
    )
    assert [(field["source_offset"], field["field_offset"]) for field in fields] == [(4, 14)]
