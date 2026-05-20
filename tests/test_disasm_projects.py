from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    resolve_target_binary_source,
)
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    build_target_identity,
)
from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.disasm.projects import (
    create_project,
    dedupe_project_name,
    delete_project,
    derive_project_name,
    get_project,
    list_projects,
    mark_project_opened,
)
from amiga_reversing.disasm.target_metadata import (
    EntryRegisterSeedKind,
    EntryRegisterSeedMetadata,
    RssetLayoutRegionMetadata,
    RssetLayoutStorageKind,
    SeededCodeEntrypointMetadata,
    SeededCodeLabelMetadata,
    SeededEntityMetadata,
    SuppressedSeededItemKind,
    SuppressedSeededItemMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    load_required_target_metadata,
    load_target_metadata,
    require_target_metadata,
    validate_target_seeded_metadata,
    write_target_corrections_metadata,
    write_target_metadata,
    write_target_seeded_metadata,
)


def _project_metadata_payload(kind: str = "test_project") -> dict[str, object]:
    return {
        "schema_version": 2,
        "created_at": "2026-03-25T00:00:00+00:00",
        "updated_at": "2026-03-25T00:00:00+00:00",
        "origin": {"kind": kind},
    }


def _disk_manifest_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "disk_id": "demo_disk",
        "source_path": "bin/demo.adf",
        "source_sha256": "deadbeef",
        "bootblock_target_name": "amiga_disk_demo_disk__amiga_raw_bootblock",
        "bootblock_target_path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock",
        "analysis": {
            "disk_info": {
                "path": "demo.adf",
                "size": 901120,
                "variant": "DD",
                "total_sectors": 1760,
                "sectors_per_track": 11,
                "is_dos": True,
            },
            "boot_block": {
                "magic_ascii": "DOS",
                "is_dos": True,
                "flags_byte": 1,
                "fs_type": "FFS",
                "fs_description": "DOS\\1 - Fast File System",
                "checksum": "0x00000000",
                "checksum_valid": True,
                "rootblock_ptr": 880,
                "bootcode_size": 1012,
                "bootcode_has_code": False,
                "bootcode_entropy": 0.0,
            },
            "filesystem": {
                "type": "FFS",
                "volume_name": "Demo",
                "directories": 1,
                "files": 1,
                "total_file_size": 1234,
            },
        },
        "imported_targets": [
            {
                "target_name": "amiga_disk_demo_disk__amiga_hunk_run_12345678",
                "target_path": "targets/amiga_disk_demo_disk/targets/amiga_hunk_run_12345678",
                "entry_path": "c/Run",
                "binary_path": "bin/demo.adf::c/Run",
                "target_type": "program",
            }
        ],
    }


def test_load_target_metadata_merges_seeded_metadata_file(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
        ),
    )
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=0x05D6,
                    end=0x0630,
                    type="code",
                    name="check_keyboard",
                    hunk=0,
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded:demo-code-range",
                    source_id="demo_seed",
                    source_path="seeded/demo_source.txt",
                    source_locator="DemoCodeRange",
                ),
            ),
            seeded_code_labels=(
                SeededCodeLabelMetadata(
                    addr=0x1234,
                    name="code_label",
                    hunk=0,
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded:demo-label",
                    source_id="demo_seed",
                    source_path="seeded/demo_source.txt",
                    source_locator="DemoCodeLabel",
                ),
            ),
            seeded_code_entrypoints=(
                SeededCodeEntrypointMetadata(
                    addr=0x2345,
                    name="code_entry",
                    hunk=0,
                    role="demo role",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded:demo-entry",
                    source_id="demo_seed",
                    source_path="seeded/demo_source.txt",
                    source_locator="DemoCodeEntry",
                ),
            ),
        ),
    )

    loaded = load_target_metadata(target_dir)

    assert loaded is not None
    assert loaded.seeded_entities == (
        SeededEntityMetadata(
            addr=0x05D6,
            end=0x0630,
            type="code",
            name="check_keyboard",
            hunk=0,
            seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
            review_status=TargetMetadataReviewStatus.SEEDED,
            citation="seeded:demo-code-range",
            source_id="demo_seed",
            source_path="seeded/demo_source.txt",
            source_locator="DemoCodeRange",
        ),
    )
    assert loaded.seeded_code_labels == (
        SeededCodeLabelMetadata(
            addr=0x1234,
            name="code_label",
            hunk=0,
            seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
            review_status=TargetMetadataReviewStatus.SEEDED,
            citation="seeded:demo-label",
            source_id="demo_seed",
            source_path="seeded/demo_source.txt",
            source_locator="DemoCodeLabel",
        ),
    )
    assert loaded.seeded_code_entrypoints == (
        SeededCodeEntrypointMetadata(
            addr=0x2345,
            name="code_entry",
            hunk=0,
            role="demo role",
            seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
            review_status=TargetMetadataReviewStatus.SEEDED,
            citation="seeded:demo-entry",
            source_id="demo_seed",
            source_path="seeded/demo_source.txt",
            source_locator="DemoCodeEntry",
        ),
    )


def test_load_target_metadata_allows_manual_seeded_entity_override(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=0x0100,
                    end=0x0200,
                    type="data",
                    name="map_data_keep",
                    hunk=0,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="manual",
                ),
            ),
        ),
    )
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=0x0100,
                    end=0x0200,
                    type="data",
                    hunk=0,
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded:demo-data-range",
                    source_id="demo_seed",
                    source_path="seeded/demo_source.txt",
                    source_locator="DemoDataRange",
                    struct_name="Node",
                    field_name="LN_SUCC",
                    field_type="APTR",
                    c_type="struct Node *",
                    pointer_struct="Node",
                    value_domain="node_ref",
                ),
            ),
        ),
    )

    loaded = load_target_metadata(target_dir)

    assert loaded is not None
    assert loaded.seeded_entities == (
        SeededEntityMetadata(
            addr=0x0100,
            end=0x0200,
            type="data",
            name="map_data_keep",
            hunk=0,
            unit=None,
            encoding=None,
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.SEEDED,
            citation="manual",
            source_id="demo_seed",
            source_path="seeded/demo_source.txt",
            source_locator="DemoDataRange",
            struct_name="Node",
            field_name="LN_SUCC",
            field_type="APTR",
            c_type="struct Node *",
            pointer_struct="Node",
            value_domain="node_ref",
        ),
    )


def test_load_target_metadata_keeps_same_address_seeded_entity_ranges(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=0x0100,
                    end=0x0102,
                    type="data",
                    name="short_data",
                    hunk=0,
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded:short",
                    source_id="demo_seed",
                    source_path="seeded/demo_source.txt",
                    source_locator="ShortData",
                ),
                SeededEntityMetadata(
                    addr=0x0100,
                    end=0x0104,
                    type="data",
                    name="long_data",
                    hunk=0,
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded:long",
                    source_id="demo_seed",
                    source_path="seeded/demo_source.txt",
                    source_locator="LongData",
                ),
            ),
        ),
    )

    loaded = load_target_metadata(target_dir)

    assert loaded is not None
    assert [(entity.hunk, entity.addr, entity.end, entity.type, entity.name) for entity in loaded.seeded_entities] == [
        (0, 0x0100, 0x0102, "data", "short_data"),
        (0, 0x0100, 0x0104, "data", "long_data"),
    ]


def test_load_target_metadata_preserves_extended_rsset_layout_metadata(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            rsset_layout_regions=(
                RssetLayoutRegionMetadata(
                    offset=552,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="manual",
                    size=2,
                    layout_name="work",
                    base_symbol="__game_work_base__",
                    sizeof_symbol="work_SIZEOF",
                    symbol="app_option_source_buffer",
                    storage_kind=RssetLayoutStorageKind.POINTER,
                    semantic_type="source_text_buffer",
                    parser_role="option_source",
                    parser_routine="sub_ab00",
                    parse_order=0,
                ),
                RssetLayoutRegionMetadata(
                    offset=0x196,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="manual",
                    size=4,
                    layout_name="app",
                    base_symbol="__amiga_app_base__",
                    symbol="app_item_ids",
                    storage_kind=RssetLayoutStorageKind.BYTE_ARRAY,
                    semantic_type="item_id_array",
                ),
            ),
        ),
    )

    loaded = load_target_metadata(target_dir)

    assert loaded is not None
    assert loaded.rsset_layout_regions[0].size == 2
    assert loaded.rsset_layout_regions[0].layout_name == "work"
    assert loaded.rsset_layout_regions[0].base_symbol == "__game_work_base__"
    assert loaded.rsset_layout_regions[0].sizeof_symbol == "work_SIZEOF"
    assert loaded.rsset_layout_regions[0].storage_kind is RssetLayoutStorageKind.POINTER
    assert loaded.rsset_layout_regions[0].semantic_type == "source_text_buffer"
    assert loaded.rsset_layout_regions[0].parser_role == "option_source"
    assert loaded.rsset_layout_regions[0].parser_routine == "sub_ab00"
    assert loaded.rsset_layout_regions[0].parse_order == 0
    assert loaded.rsset_layout_regions[1].storage_kind is RssetLayoutStorageKind.BYTE_ARRAY
    assert loaded.rsset_layout_regions[1].semantic_type == "item_id_array"


def test_load_target_metadata_applies_corrections_over_generated_seeded(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_code_labels=(
                SeededCodeLabelMetadata(
                    addr=0x0100,
                    name="generated_label",
                    hunk=0,
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="generated",
                    source_id="source",
                    source_path="source.asm",
                    source_locator="GeneratedLabel",
                ),
            ),
        ),
    )
    write_target_corrections_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_code_labels=(
                SeededCodeLabelMetadata(
                    addr=0x0100,
                    name="reviewed_label",
                    hunk=0,
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.VALIDATED,
                    citation="reviewed",
                ),
            ),
        ),
    )

    loaded = load_target_metadata(target_dir)

    assert loaded is not None
    assert loaded.seeded_code_labels == (
        SeededCodeLabelMetadata(
            addr=0x0100,
            name="reviewed_label",
            hunk=0,
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.VALIDATED,
            citation="reviewed",
            source_id="source",
            source_path="source.asm",
            source_locator="GeneratedLabel",
        ),
    )


def test_load_target_metadata_parses_suppressed_seeded_item_kind(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            suppressed_seeded_items=(
                SuppressedSeededItemMetadata(
                    kind=SuppressedSeededItemKind.SEEDED_ENTITY,
                    hunk=0,
                    addr=0x0100,
                ),
            ),
        ),
    )
    write_target_seeded_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_entities=(
                SeededEntityMetadata(
                    addr=0x0100,
                    hunk=0,
                    end=0x0104,
                    type="data",
                    seed_origin=TargetMetadataSeedOrigin.PRIMARY_DOC,
                    review_status=TargetMetadataReviewStatus.SEEDED,
                    citation="seeded",
                    source_id="source",
                    source_path="source.asm",
                    source_locator="GeneratedData",
                ),
            ),
        ),
    )

    loaded = load_target_metadata(target_dir)

    assert loaded is not None
    assert loaded.suppressed_seeded_items[0].kind is SuppressedSeededItemKind.SEEDED_ENTITY
    assert loaded.seeded_entities == ()


def test_validate_target_seeded_metadata_rejects_entry_register_seeds() -> None:
    with pytest.raises(ValueError, match="must not contain entry_register_seeds"):
        validate_target_seeded_metadata(
            TargetMetadata(
                target_type="program",
                entry_register_seeds=(
                    EntryRegisterSeedMetadata(
                        entry_offset=None,
                        register="A6",
                        kind=EntryRegisterSeedKind.LIBRARY_BASE,
                        note="ExecBase",
                        library_name="exec.library",
                        struct_name="LIB",
                        context_name=None,
                    ),
                ),
            )
        )


def test_load_target_metadata_rejects_non_object_root(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "target_metadata.json").write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="Bad target_metadata.json"):
        load_target_metadata(target_dir)


def test_load_target_metadata_rejects_non_string_target_type(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "target_metadata.json").write_text(
        json.dumps(
            {
                "target_type": 123,
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Bad target_metadata.json"):
        load_target_metadata(target_dir)


def test_require_target_metadata_rejects_missing_raw_binary_metadata() -> None:
    with pytest.raises(ValueError, match="Missing target_metadata.json for raw binary target"):
        require_target_metadata(
            None,
            target_dir=Path("targets/demo"),
            source_kind=BinarySourceKind.RAW_BINARY,
            parent_disk_id=None,
        )


def test_require_target_metadata_rejects_missing_internal_target_metadata() -> None:
    with pytest.raises(ValueError, match="Missing target_metadata.json for internal target"):
        require_target_metadata(
            None,
            target_dir=Path("targets/demo"),
            source_kind=BinarySourceKind.HUNK_FILE,
            parent_disk_id="demo_disk",
        )


def test_load_required_target_metadata_allows_missing_optional_hunk_metadata(tmp_path: Path) -> None:
    assert load_required_target_metadata(
        target_dir=tmp_path,
        source_kind=BinarySourceKind.HUNK_FILE,
        parent_disk_id=None,
    ) is None


def _dos_magic_non_dos_manifest_payload() -> dict[str, object]:
    payload = _disk_manifest_payload()
    analysis = payload["analysis"]
    assert isinstance(analysis, dict)
    analysis.pop("filesystem", None)
    analysis["non_dos"] = {
        "description": "Custom format disk (non-AmigaDOS)",
        "bootcode_present": True,
        "dos_magic_without_filesystem": True,
        "filesystem_parse_error": "Unexpected root hash table size",
    }
    return payload


def test_resolve_project_paths_uses_recorded_binary_path(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    binary_path = bin_dir / "DemoGame"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "hunk_file",
        "path": str(binary_path),
    }))
    (target_dir / "DemoGame.s").write_text("; output\n")

    resolved = resolve_project_paths("demo", project_root=project_root)

    assert resolved.binary_source.kind is BinarySourceKind.HUNK_FILE
    assert resolved.binary_source.path == binary_path
    assert resolved.binary_source.display_path == str(binary_path)
    assert resolved.output_path == target_dir / "DemoGame.s"
    assert resolved.kind == "binary"


def test_resolve_project_paths_supports_disk_entry_binary_source(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_hunk_run_12345678"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    adf_path = bin_dir / "demo.adf"
    adf_path.write_bytes(b"demo")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "disk_entry",
        "disk_id": "demo_disk",
        "disk_path": "bin/demo.adf",
        "entry_path": "c/Run",
        "parent_disk_id": "demo_disk",
    }))

    resolved = resolve_project_paths("amiga_disk_demo_disk__amiga_hunk_run_12345678", project_root=project_root)

    assert resolved.binary_source.kind is BinarySourceKind.DISK_ENTRY
    assert resolved.binary_source.adf_path == adf_path
    assert resolved.binary_source.entry_path == "c/Run"
    assert resolved.binary_source.analysis_cache_path == target_dir / "binary.analysis"


def test_resolve_project_paths_supports_raw_binary_source(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x00" * 0x0C + b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000C,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))

    resolved = resolve_project_paths("amiga_disk_demo_disk__amiga_raw_bootblock", project_root=project_root)

    assert resolved.binary_source.kind is BinarySourceKind.RAW_BINARY
    assert resolved.binary_source.path == binary_path
    assert resolved.binary_source.load_address == 0x70000
    assert resolved.binary_source.entrypoint == 0x7000C
    assert resolved.binary_source.code_start_offset == 0x0C


def test_resolve_target_binary_source_rejects_non_object_descriptor(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "source_binary.json").write_text("null", encoding="utf-8")

    with pytest.raises(TypeError, match="Expected JSON object"):
        resolve_target_binary_source(target_dir)


def test_resolve_target_binary_source_rejects_raw_code_start_outside_file(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": str(binary_path),
                "load_address": 0x70000,
                "entrypoint": 0x70000,
                "code_start_offset": 2,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="code_start_offset 0x2 lies outside file of 2 bytes"):
        resolve_target_binary_source(target_dir)


def test_resolve_target_binary_source_rejects_raw_entrypoint_outside_code_range(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x00" * 0x0C + b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": str(binary_path),
                "load_address": 0x70000,
                "entrypoint": 0x7000E,
                "code_start_offset": 0x0C,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"entrypoint 0x7000E lies outside code range 0x7000C\.\.0x7000D"):
        resolve_target_binary_source(target_dir)


def test_resolve_project_paths_allows_missing_entities_by_default(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x00" * 0x0C + b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000C,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))

    resolved = resolve_project_paths("amiga_disk_demo_disk__amiga_raw_bootblock", project_root=project_root)

    assert resolved.binary_source.kind is BinarySourceKind.RAW_BINARY


def test_resolve_project_paths_rejects_disk_project_name(tmp_path: Path) -> None:
    disk_dir = tmp_path / "targets" / "amiga_disk_demo"
    disk_dir.mkdir(parents=True)
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))

    with pytest.raises(ValueError, match="Disk project"):
        resolve_project_paths("amiga_disk_demo", project_root=tmp_path)


def test_list_projects_includes_unready_binary_project(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))

    projects = list_projects(project_root=project_root)

    assert len(projects) == 1
    assert projects[0].id == "demo"
    assert projects[0].kind == "binary"
    assert projects[0].ready is False
    assert projects[0].binary_path is None
    assert projects[0].parent_project_id is None
    assert projects[0].created_at
    assert projects[0].updated_at


def test_list_projects_includes_disk_project(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))

    projects = list_projects(project_root=project_root)

    assert len(projects) == 1
    assert projects[0].id == "amiga_disk_demo_disk"
    assert projects[0].kind == "disk"
    assert projects[0].manifest_path == str(disk_dir / "manifest.json")
    assert projects[0].target_count == 2
    assert projects[0].ready is False
    assert projects[0].disk_type == "DOS"


def test_disk_manifest_preserves_decompressed_target_relationship(tmp_path: Path) -> None:
    disk_dir = tmp_path / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    payload = _disk_manifest_payload()
    payload["imported_targets"][0]["derived_targets"] = [
        {
            "kind_id": 1,
            "kind": "decompressed_payload",
            "target_name": "amiga_disk_demo_disk__amiga_raw_run_rnc_00001000",
            "packed_file_offset": 0x1020,
            "packed_section_offset": 0x1000,
        }
    ]
    payload["imported_targets"].append(
        {
            "target_name": "amiga_disk_demo_disk__amiga_raw_run_rnc_00001000",
            "target_path": "targets/amiga_disk_demo_disk/targets/amiga_raw_run_rnc_00001000",
            "entry_path": "c/Run::rnc_00001000",
            "binary_path": "targets/amiga_disk_demo_disk/targets/amiga_raw_run_rnc_00001000/binary.bin",
            "target_type": "raw_binary",
            "derived_from": {
                "kind_id": 1,
                "kind": "decompressed_payload",
                "parent_target": "amiga_disk_demo_disk__amiga_hunk_run_12345678",
                "parent_entry_path": "c/Run",
                "packed_file_offset": 0x1020,
                "packed_section_offset": 0x1000,
                "compressor": "RNC1: Rob Northen RNC1 Compressor (old)",
                "load_address": 0x4000,
                "entrypoint": 0x4000,
            },
        }
    )
    manifest_path = disk_dir / "manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    from amiga_reversing.amiga_disk.models import DiskManifest

    manifest = DiskManifest.load(manifest_path)
    manifest_dict = manifest.to_dict()

    parent = manifest_dict["imported_targets"][0]
    child = manifest_dict["imported_targets"][1]
    assert parent["derived_targets"][0]["target_name"] == "amiga_disk_demo_disk__amiga_raw_run_rnc_00001000"
    assert child["derived_from"]["parent_target"] == "amiga_disk_demo_disk__amiga_hunk_run_12345678"
    assert child["derived_from"]["packed_section_offset"] == 0x1000


def test_list_projects_hides_imported_disk_child_targets(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))
    child_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_hunk_run_12345678"
    child_dir.mkdir(parents=True)
    (child_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    bootblock_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    bootblock_dir.mkdir(parents=True)
    (bootblock_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    (bootblock_dir / "binary.bin").write_bytes(b"\x4e\x75")
    (bootblock_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000C,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))
    (child_dir / "source_binary.json").write_text(json.dumps({
        "kind": "disk_entry",
        "disk_id": "demo_disk",
        "disk_path": "bin/demo.adf",
        "entry_path": "c/Run",
        "parent_disk_id": "demo_disk",
    }))

    projects = list_projects(project_root=project_root)

    assert [project.id for project in projects] == ["amiga_disk_demo_disk"]


def test_list_projects_requires_disk_manifest(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_broken_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(
        json.dumps(_project_metadata_payload())
    )

    with pytest.raises(FileNotFoundError, match="Missing manifest.json for disk project: amiga_disk_broken_disk"):
        list_projects(project_root=project_root)


def test_get_project_reads_disk_project(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))

    project = get_project("amiga_disk_demo_disk", project_root=project_root)

    assert project.name == "demo_disk"
    assert project.kind == "disk"
    assert project.source_path == "bin/demo.adf"
    assert project.disk_type == "DOS"
    assert project.parent_project_id is None


def test_get_project_marks_dos_magic_without_filesystem_as_non_dos(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    (disk_dir / "manifest.json").write_text(json.dumps(_dos_magic_non_dos_manifest_payload()))

    project = get_project("amiga_disk_demo_disk", project_root=project_root)

    assert project.disk_type == "non-DOS"


def test_get_project_sets_parent_project_for_disk_entry_target(tmp_path: Path) -> None:
    project_root = tmp_path
    disk_dir = project_root / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))
    target_dir = project_root / "targets" / "amiga_disk_demo_disk" / "targets" / "amiga_hunk_run_12345678"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir()
    (target_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    (target_dir / "binary.analysis").write_text("")
    adf_path = bin_dir / "demo.adf"
    adf_path.write_bytes(b"demo")
    (target_dir / "source_binary.json").write_text(json.dumps({
        "kind": "disk_entry",
        "disk_id": "demo_disk",
        "disk_path": "bin/demo.adf",
        "entry_path": "c/Run",
        "parent_disk_id": "demo_disk",
    }))

    project = get_project("amiga_disk_demo_disk__amiga_hunk_run_12345678", project_root=project_root)

    assert project.parent_project_id == "amiga_disk_demo_disk"


def test_get_project_exposes_manual_action_log_projection(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir()
    (target_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    binary_path = bin_dir / "demo.bin"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": "bin/demo.bin",
                "load_address": 0x70000,
                "entrypoint": 0x70000,
                "code_start_offset": 0,
            }
        )
    )
    binary_source = resolve_target_binary_source(target_dir, project_root=project_root)
    assert binary_source is not None
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "record": "manual_action_log_header",
                        "version": 1,
                        "target_identity": build_target_identity(binary_source),
                    },
                    sort_keys=True,
                ),
                json.dumps(
                    {
                        "record": "manual_action",
                        "action_id": "a1",
                        "sequence": 1,
                        "created_at": "2026-05-13T00:00:00+00:00",
                        "kind": "create_manual_seed",
                        "seed": {"seed_id": "s1", "kind": "code"},
                    },
                    sort_keys=True,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    project = get_project("demo", project_root=project_root)

    assert project.manual_action_log_path == str(target_dir / MANUAL_ACTION_LOG_FILE_NAME)
    assert project.review_state == "clear"
    assert project.manual_state is not None
    assert project.manual_state["seeds"] == ({"seed_id": "s1", "kind": "code"},)


def test_get_project_reports_manual_seed_conflict_with_target_metadata(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir()
    (target_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    binary_path = bin_dir / "demo.bin"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": "bin/demo.bin",
                "load_address": 0x70000,
                "entrypoint": 0x70000,
                "code_start_offset": 0,
            }
        )
    )
    write_target_metadata(
        target_dir,
        TargetMetadata(
            target_type="program",
            entry_register_seeds=(),
            seeded_code_entrypoints=(
                SeededCodeEntrypointMetadata(
                    addr=1,
                    hunk=0,
                    name="entry",
                    seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                    review_status=TargetMetadataReviewStatus.VALIDATED,
                    citation="target_metadata",
                ),
            ),
        ),
    )
    binary_source = resolve_target_binary_source(target_dir, project_root=project_root)
    assert binary_source is not None
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "record": "manual_action_log_header",
                        "version": 1,
                        "target_identity": build_target_identity(binary_source),
                    },
                    sort_keys=True,
                ),
                json.dumps(
                    {
                        "record": "manual_action",
                        "action_id": "a1",
                        "sequence": 1,
                        "created_at": "2026-05-13T00:00:00+00:00",
                        "kind": "create_manual_seed",
                        "seed": {
                            "seed_id": "text-range",
                            "kind": "data",
                            "mode": "required",
                            "range": "h0:$00000001..$00000002",
                        },
                    },
                    sort_keys=True,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    project = get_project("demo", project_root=project_root)

    assert project.review_state == "blocked"
    assert project.manual_state is not None
    assert project.manual_state["review_state"] == "blocked"
    review_items = project.manual_state["review_items"]
    assert isinstance(review_items, tuple)
    assert len(review_items) == 1
    item = review_items[0]
    assert isinstance(item, dict)
    for key, value in {
        "kind": "manual_seed_conflict",
        "item_id": "manual_seed_conflict:text-range:seeded_code_entrypoint:h0:$00000001",
        "scope": "range",
        "state": "open",
        "seed_ids": ["text-range"],
        "stronger_kind": "code",
        "stronger_source": "seeded_code_entrypoint:h0:$00000001",
        "stronger_name": "entry",
        "hunk": 0,
        "start": 1,
        "end": 2,
        "message": "Required manual seed text-range conflicts with stronger seeded_code_entrypoint:h0:$00000001",
    }.items():
        assert item.get(key) == value
    assert isinstance(item.get("evidence_fingerprint"), str)
    assert item.get("review_confidence") == "high"
    assert isinstance(item.get("suggested_actions"), list)


def test_get_project_blocks_on_reproduction_content_mismatch(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir()
    (target_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    binary_path = bin_dir / "demo.bin"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": "bin/demo.bin",
                "load_address": 0x70000,
                "entrypoint": 0x70000,
                "code_start_offset": 0,
            }
        )
    )
    (target_dir / "reproduction.json").write_text(
        json.dumps(
            {
                "status": "binary_mismatch",
                "exact": False,
                "comparison": {
                    "status": "mismatch",
                    "content_exact": False,
                    "full_file_exact": False,
                    "failure_kinds": ["payload_mismatch"],
                },
            }
        ),
        encoding="utf-8",
    )

    project = get_project("demo", project_root=project_root)

    assert project.review_state == "blocked"
    assert len(project.review_items) == 1
    item = project.review_items[0]
    assert item["kind"] == "reproduction_mismatch"
    assert item["review_blocker"] is True
    assert item["state"] == "open"
    assert item["failure_kinds"] == ["payload_mismatch"]
    assert isinstance(item["evidence_fingerprint"], str)
    assert item["suggested_actions"] == [
        {"action": "open_reproduction_report"},
        {"action": "rerun_round_trip_verification"},
    ]


def test_get_project_blocks_on_decompression_review_event(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir()
    (target_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    binary_path = bin_dir / "demo.bin"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": "bin/demo.bin",
                "load_address": 0x70000,
                "entrypoint": 0x70000,
                "code_start_offset": 0,
            }
        )
    )
    (target_dir / "binary.analysis").write_text(
        json.dumps(
            {
                "decompression_events": [
                    {
                        "event_id": "decompression:recognized_unpacker:section:2:00000060:tetragon",
                        "status_id": 6,
                        "status": "needs_review_blocker",
                        "reason": "invalid_decompressed_entrypoint",
                        "source_section": 2,
                        "source_section_offset": 0x60,
                    }
                ]
            }
        )
    )

    project = get_project("demo", project_root=project_root)

    assert project.review_state == "blocked"
    assert len(project.review_items) == 1
    item = project.review_items[0]
    assert item["kind"] == "decompression_blocker"
    assert item["review_blocker"] is True
    assert item["event_id"] == "decompression:recognized_unpacker:section:2:00000060:tetragon"
    assert item["reason"] == "invalid_decompressed_entrypoint"


def test_get_project_reports_container_only_reproduction_difference_without_blocking(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir()
    (target_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    binary_path = bin_dir / "demo.bin"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": "bin/demo.bin",
                "load_address": 0x70000,
                "entrypoint": 0x70000,
                "code_start_offset": 0,
            }
        )
    )
    (target_dir / "reproduction.json").write_text(
        json.dumps(
            {
                "status": "binary_mismatch",
                "exact": False,
                "comparison": {
                    "status": "container_shape_mismatch",
                    "content_exact": True,
                    "full_file_exact": False,
                    "file_structure_issue_kinds": ["unsupported_container_shape"],
                },
            }
        ),
        encoding="utf-8",
    )

    project = get_project("demo", project_root=project_root)

    assert project.review_state == "needs_review"
    assert len(project.review_items) == 1
    item = project.review_items[0]
    assert item["kind"] == "unsupported_container_shape"
    assert item["review_blocker"] is False
    assert item["file_structure_issue_kinds"] == ["unsupported_container_shape"]
    assert isinstance(item["evidence_fingerprint"], str)


def test_create_project_does_not_create_legacy_entities_file(tmp_path: Path) -> None:
    project = create_project("demo", project_root=tmp_path)

    assert project.id == "demo"
    assert project.kind == "binary"
    assert not (tmp_path / "targets" / "demo" / "entities.jsonl").exists()
    metadata = json.loads((tmp_path / "targets" / "demo" / ".project.json").read_text())
    assert metadata["schema_version"] == 2
    assert metadata["created_at"] == project.created_at
    assert metadata["updated_at"] == project.updated_at
    assert metadata["origin"] == {"kind": "manual_project", "project_id": "demo"}


def test_derive_project_name_uses_filename_stem() -> None:
    assert derive_project_name("Bloodwych (1990).adf") == "amiga_hunk_bloodwych-1990"


def test_dedupe_project_name_suffixes_existing_binary_and_disk_projects(tmp_path: Path) -> None:
    create_project("demo", project_root=tmp_path)
    disk_dir = tmp_path / "targets" / "demo-2"
    disk_dir.mkdir(parents=True)
    (disk_dir / "manifest.json").write_text(json.dumps(_disk_manifest_payload()))

    assert dedupe_project_name("demo", project_root=tmp_path) == "demo-3"


def test_mark_project_opened_records_recent_timestamp_for_binary_and_disk(tmp_path: Path) -> None:
    create_project("demo", project_root=tmp_path)
    disk_dir = tmp_path / "targets" / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    payload = _disk_manifest_payload()
    payload["imported_targets"] = []
    (disk_dir / "manifest.json").write_text(json.dumps(payload))

    binary_project = mark_project_opened("demo", project_root=tmp_path)
    disk_project = mark_project_opened("amiga_disk_demo_disk", project_root=tmp_path)
    state = json.loads((tmp_path / "targets" / ".browser_state.json").read_text())

    assert binary_project.last_opened == state["recent_projects"]["demo"]
    assert disk_project.last_opened == state["recent_projects"]["amiga_disk_demo_disk"]


def test_list_projects_orders_by_most_recently_opened(tmp_path: Path) -> None:
    create_project("older", project_root=tmp_path)
    create_project("newer", project_root=tmp_path)
    mark_project_opened("older", project_root=tmp_path)
    mark_project_opened("newer", project_root=tmp_path)

    projects = list_projects(project_root=tmp_path)

    assert [project.id for project in projects] == ["newer", "older"]


def test_delete_binary_project_removes_target_dir_and_state(tmp_path: Path) -> None:
    create_project("demo", project_root=tmp_path)
    mark_project_opened("demo", project_root=tmp_path)

    delete_project("demo", project_root=tmp_path)

    assert not (tmp_path / "targets" / "demo").exists()
    state = json.loads((tmp_path / "targets" / ".browser_state.json").read_text())
    assert "demo" not in state["recent_projects"]


def test_delete_disk_project_removes_manifest_targets_and_source(tmp_path: Path) -> None:
    targets_dir = tmp_path / "targets"
    bin_dir = tmp_path / "bin" / "uploads"
    targets_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    source_path = bin_dir / "demo.adf"
    source_path.write_bytes(b"demo")
    disk_dir = targets_dir / "amiga_disk_demo_disk"
    disk_dir.mkdir(parents=True)
    (disk_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    imported_dir = targets_dir / "amiga_disk_demo_disk" / "targets" / "amiga_hunk_run_12345678"
    imported_dir.mkdir(parents=True)
    (imported_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    (imported_dir / "source_binary.json").write_text(json.dumps({
        "kind": "disk_entry",
        "disk_id": "demo_disk",
        "disk_path": "bin/uploads/demo.adf",
        "entry_path": "c/Run",
        "parent_disk_id": "demo_disk",
    }))
    bootblock_dir = targets_dir / "amiga_disk_demo_disk" / "targets" / "amiga_raw_bootblock"
    bootblock_dir.mkdir(parents=True)
    (bootblock_dir / ".project.json").write_text(json.dumps(_project_metadata_payload()))
    (bootblock_dir / "binary.bin").write_bytes(b"\x00" * 0x0C + b"\x4e\x75")
    (bootblock_dir / "source_binary.json").write_text(json.dumps({
        "kind": "raw_binary",
        "address_model": "local_offset",
        "path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock/binary.bin",
        "load_address": 0x70000,
        "entrypoint": 0x7000C,
        "code_start_offset": 0x0C,
        "parent_disk_id": "demo_disk",
    }))
    payload = _disk_manifest_payload()
    payload["source_path"] = "bin/uploads/demo.adf"
    (disk_dir / "manifest.json").write_text(json.dumps(payload))
    mark_project_opened("amiga_disk_demo_disk", project_root=tmp_path)
    mark_project_opened("amiga_disk_demo_disk__amiga_hunk_run_12345678", project_root=tmp_path)
    mark_project_opened("amiga_disk_demo_disk__amiga_raw_bootblock", project_root=tmp_path)

    delete_project("amiga_disk_demo_disk", project_root=tmp_path)

    assert not disk_dir.exists()
    assert not imported_dir.exists()
    assert not bootblock_dir.exists()
    assert not source_path.exists()
    state = json.loads((targets_dir / ".browser_state.json").read_text())
    assert "amiga_disk_demo_disk" not in state["recent_projects"]
    assert "amiga_disk_demo_disk__amiga_hunk_run_12345678" not in state["recent_projects"]
    assert "amiga_disk_demo_disk__amiga_raw_bootblock" not in state["recent_projects"]


def test_get_project_requires_project_metadata(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match=r"Missing \.project\.json for project: demo"):
        get_project("demo", project_root=tmp_path)


def test_list_projects_requires_project_metadata(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match=r"Missing \.project\.json for project: demo"):
        list_projects(project_root=tmp_path)
