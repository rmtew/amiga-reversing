from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from _pytest.monkeypatch import MonkeyPatch

from amiga_reversing.amiga_disk.adf import (
    DiskAnalysisError,
    analyze_adf,
    derive_disk_id,
)
from amiga_reversing.amiga_disk.models import (
    AdfAnalysis,
    BitmapInfo,
    BlockUsageInfo,
    BootBlockInfo,
    BootloaderAnalysis,
    BootloaderDecodeRegion,
    BootloaderDecodeInputSourceKind,
    BootloaderDecodeRequiredSourceKind,
    BootloaderDerivedRegion,
    BootloaderDiskRead,
    BootloaderDiskCommand,
    BootloaderMemoryCopy,
    BootloaderStage,
    BootloaderTransferSourceKind,
    DiskFileEntry,
    DiskInfo,
    FileContentInfo,
    FileImportTargetInfo,
    FilesystemInfo,
    NonDosInfo,
    RawTrackSource,
    RawTrackSourceSpan,
    RootBlockInfo,
    TrackAnalysis,
    TrackInfo,
    TrackloaderAnalysis,
    TrackSpan,
)
from amiga_reversing.amiga_disk.project import (
    create_disk_project,
    import_adf,
    refresh_decompressed_payload_children,
)
from amiga_reversing.disasm.c_backend import (
    analyze_binary_source_with_c_backend,
    materialize_recognized_unpacker_event_with_c_backend,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata
from amiga_reversing.tools.analyze_disk import print_summary
from src.tests.test_platform_amiga_disk import (
    BLOCK_SIZE,
    ROOT_BLOCK,
    TOTAL_BLOCKS,
    _make_boot_block,
    _make_file_header,
    _make_root_block,
    _put_u32,
)


def _requires_c_backend_dlls() -> None:
    build_dir = PROJECT_ROOT / "src" / "build"
    if not (build_dir / "platform_file_lib.dll").exists() or not (build_dir / "platform_disk_lib.dll").exists():
        pytest.skip("C backend DLLs are missing; run cmd /c src\\build.bat")


def _hunk_executable(code: bytes) -> bytes:
    assert len(code) % 4 == 0
    words = [1011, 0, 1, 0, 0, len(code) // 4, 1001, len(code) // 4]
    return struct.pack(">" + "I" * len(words), *words) + code + struct.pack(">I", 1010)


def _ffs_adf_with_single_file(payload: bytes) -> bytes:
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(ROOT_BLOCK, 1)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(ROOT_BLOCK, 1)[BLOCK_SIZE:]
    blocks[ROOT_BLOCK][:] = _make_root_block("Workbench", [900])
    file_header = _make_file_header(900, "RUN", len(payload))
    _put_u32(file_header, 8, 1)
    _put_u32(file_header, 24 + 71 * 4, 910)
    blocks[900][:] = file_header
    blocks[910][: len(payload)] = payload
    return b"".join(bytes(block) for block in blocks)


def _content_from_c_disk_inspect(tmp_path: Path, payload: bytes) -> FileContentInfo:
    adf_path = tmp_path / "content.adf"
    adf_path.write_bytes(_ffs_adf_with_single_file(payload))
    analysis = analyze_adf(adf_path)
    assert analysis.files is not None
    content = analysis.files[0].content
    assert content is not None
    return content


def _program_import_target() -> FileImportTargetInfo:
    return FileImportTargetInfo(
        target_type="program",
        entry_path="s/Run",
        local_target_id="amiga_hunk_s__run_dcce9fe5",
        target_metadata={
            "target_type": "program",
            "entry_register_seeds": [],
            "bootblock": None,
            "resident": None,
            "library": None,
            "custom_structs": [],
            "rsset_layout_regions": [],
            "seeded_entities": [],
            "seeded_code_labels": [],
            "seeded_code_entrypoints": [],
            "absolute_code_labels": [],
            "execution_views": [],
            "suppressed_seeded_items": [],
        },
    )


def _bootblock_import_target(
    *,
    magic_ascii: str = "DOS",
    flags_byte: int = 1,
    fs_description: str = "DOS\\1 - Fast File System",
    checksum: str = "0x00000000",
    checksum_valid: bool = True,
    rootblock_ptr: int = 880,
    bootcode_size: int = 1012,
) -> FileImportTargetInfo:
    return FileImportTargetInfo(
        target_type="bootblock",
        entry_path="bootblock",
        local_target_id="amiga_raw_bootblock",
        source={
            "kind": "raw_binary",
            "address_model": "local_offset",
            "byte_offset": 0,
            "byte_size": bootcode_size + 12,
            "load_address": 0x70000,
            "entrypoint": 0x7000C,
            "code_start_offset": 0x0C,
        },
        target_metadata={
            "target_type": "bootblock",
            "entry_register_seeds": [
                {
                    "entry_offset": None,
                    "register": "A6",
                    "kind": "library_base",
                    "library_name": "exec.library",
                    "struct_name": "LIB",
                    "context_name": None,
                    "note": "ExecBase",
                },
                {
                    "entry_offset": None,
                    "register": "A1",
                    "kind": "struct_ptr",
                    "library_name": None,
                    "struct_name": "IO",
                    "context_name": "trackdisk.device",
                    "note": "IOStdReq (open trackdisk.device)",
                },
            ],
            "bootblock": {
                "magic_ascii": magic_ascii,
                "flags_byte": flags_byte,
                "fs_description": fs_description,
                "checksum": checksum,
                "checksum_valid": checksum_valid,
                "rootblock_ptr": rootblock_ptr,
                "bootcode_offset": 0x0C,
                "bootcode_size": bootcode_size,
                "load_address": 0x70000,
                "entrypoint": 0x7000C,
            },
            "resident": None,
            "library": None,
            "custom_structs": [],
            "rsset_layout_regions": [],
            "seeded_entities": [],
            "seeded_code_labels": [],
            "seeded_code_entrypoints": [],
            "absolute_code_labels": [],
            "execution_views": [],
            "suppressed_seeded_items": [],
        },
    )


def _bootloader_stage_import_target(
    *,
    byte_offset: int = 0x200,
    byte_size: int = 4,
    load_address: int = 0x40000,
    entrypoint: int = 0x40000,
    execution_views: list[dict[str, object]] | None = None,
) -> FileImportTargetInfo:
    return FileImportTargetInfo(
        target_type="bootloader_stage",
        entry_path="bootloader/stage_1",
        local_target_id="amiga_raw_bootloader_stage_1",
        source={
            "kind": "raw_binary",
            "address_model": "runtime_absolute",
            "byte_offset": byte_offset,
            "byte_size": byte_size,
            "load_address": load_address,
            "entrypoint": entrypoint,
            "code_start_offset": 0,
        },
        target_metadata={
            "target_type": "bootloader_stage",
            "entry_register_seeds": [
                {
                    "entry_offset": None,
                    "register": "A6",
                    "kind": "library_base",
                    "library_name": "exec.library",
                    "struct_name": "LIB",
                    "context_name": None,
                    "note": "ExecBase",
                },
                {
                    "entry_offset": None,
                    "register": "A1",
                    "kind": "struct_ptr",
                    "library_name": None,
                    "struct_name": "IO",
                    "context_name": "trackdisk.device",
                    "note": "IOStdReq (open trackdisk.device)",
                },
            ],
            "bootblock": None,
            "resident": None,
            "library": None,
            "custom_structs": [],
            "rsset_layout_regions": [],
            "seeded_entities": [],
            "seeded_code_labels": [],
            "seeded_code_entrypoints": [],
            "absolute_code_labels": [],
            "execution_views": [] if execution_views is None else execution_views,
            "suppressed_seeded_items": [],
        },
    )


def _raw_span_import_target(*, byte_offset: int, byte_size: int) -> FileImportTargetInfo:
    return FileImportTargetInfo(
        target_type="bootloader_raw_span",
        entry_path="bootloader/stage_2/raw_span_0",
        local_target_id="amiga_raw_bootloader_stage_2_raw_span_0",
        source={
            "kind": "raw_binary",
            "address_model": "local_offset",
            "byte_offset": byte_offset,
            "byte_size": byte_size,
            "load_address": 0,
            "entrypoint": 0,
            "code_start_offset": 0,
        },
        target_metadata={
            "target_type": "bootloader_raw_span",
            "entry_register_seeds": [],
            "bootblock": None,
            "resident": None,
            "library": None,
            "custom_structs": [],
            "rsset_layout_regions": [],
            "seeded_entities": [],
            "seeded_code_labels": [],
            "seeded_code_entrypoints": [],
            "absolute_code_labels": [],
            "execution_views": [],
            "suppressed_seeded_items": [],
        },
    )


def _single_program_disk_analysis(adf_file: str | Path) -> AdfAnalysis:
    return AdfAnalysis(
        disk_info=DiskInfo(
            path=Path(adf_file).name,
            size=901120,
            variant="DD",
            total_sectors=1760,
            sectors_per_track=11,
            is_dos=True,
        ),
        boot_block=BootBlockInfo(
            magic_ascii="DOS",
            is_dos=True,
            flags_byte=1,
            fs_type="FFS",
            fs_description="DOS\\1 - Fast File System",
            checksum="0x00000000",
            checksum_valid=True,
            rootblock_ptr=880,
            bootcode_size=1012,
            bootcode_has_code=True,
            bootcode_entropy=1.0,
            import_target=_bootblock_import_target(),
        ),
        root_block=RootBlockInfo(
            block_num=880,
            hash_table=[],
            checksum_valid=True,
            bm_flag=0,
            bm_pages=[],
            volume_name="DemoDisk",
            root_date="1978-01-01 00:00:00",
            volume_date="1978-01-01 00:00:00",
            creation_date="1978-01-01 00:00:00",
        ),
        filesystem=FilesystemInfo(
            type="FFS",
            volume_name="DemoDisk",
            directories=1,
            files=1,
            total_file_size=4,
        ),
        files=[
            DiskFileEntry(
                block_num=10,
                name="Run",
                full_path="s/Run",
                size=4,
                protection="----rwed",
                comment=None,
                date="1978-01-01 00:00:00",
                hash_chain=0,
                parent=0,
                extension_blocks=[],
                data_blocks=[11],
                data_block_count=1,
                checksum_valid=True,
                content=FileContentInfo(
                    kind="amiga_hunk_executable",
                    size=4,
                    sha256="deadbeef",
                    is_executable=True,
                    hunk_count=1,
                    target_type="program",
                    import_target=_program_import_target(),
                ),
            )
        ],
        directories=[],
        bitmap=BitmapInfo(
            checksum_valid=True,
            free_blocks=1,
            allocated_blocks=10,
            total_blocks=11,
            percent_used=90.9,
        ),
        block_usage=BlockUsageInfo(summary={"boot": 2}, orphan_blocks=[]),
    )


def _single_program_disk_analysis_with_startup(adf_file: str | Path) -> AdfAnalysis:
    analysis = _single_program_disk_analysis(adf_file)
    startup_entry = DiskFileEntry(
        block_num=20,
        name="startup-sequence",
        full_path="s/startup-sequence",
        size=5,
        protection="----rwed",
        comment=None,
        date="1978-01-01 00:00:00",
        hash_chain=0,
        parent=0,
        extension_blocks=[],
        data_blocks=[21],
        data_block_count=1,
        checksum_valid=True,
        content=FileContentInfo(
            kind="text",
            size=5,
            sha256="11" * 32,
            is_executable=False,
            target_type="text",
        ),
    )
    return replace(analysis, files=[startup_entry, *analysis.files])


def test_analyze_disk_help_loads_cleanly() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "amiga_reversing.tools.analyze_disk", "--help"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Analyze Amiga ADF disk images" in result.stdout


def test_import_adf_help_loads_cleanly() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "amiga_reversing.tools.import_adf", "--help"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Import an ADF into bin/imported and targets/" in result.stdout
    assert "--refresh-decompressed" in result.stdout


def test_derive_disk_id_normalizes_filename() -> None:
    assert (
        derive_disk_id("Search for the King, The (1991)(Accolade)(Disk 1 of 5).adf")
        == "search-for-the-king-the-1991-accolade-disk-1-of-5"
    )


def test_import_adf_creates_hidden_disk_manifest_and_targets(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert include_tracks is True
        assert extract_dir is None
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=901120,
                variant="DD",
                total_sectors=1760,
                sectors_per_track=11,
                is_dos=True,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=1,
                fs_type="FFS",
                fs_description="DOS\\1 - Fast File System",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=880,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=1.0,
                import_target=_bootblock_import_target(),
            ),
            root_block=RootBlockInfo(
                block_num=880,
                hash_table=[],
                checksum_valid=True,
                bm_flag=0,
                bm_pages=[],
                volume_name="DemoDisk",
                root_date="1978-01-01 00:00:00",
                volume_date="1978-01-01 00:00:00",
                creation_date="1978-01-01 00:00:00",
            ),
            filesystem=FilesystemInfo(
                type="FFS",
                volume_name="DemoDisk",
                directories=1,
                files=1,
                total_file_size=4,
            ),
            files=[
                DiskFileEntry(
                    block_num=10,
                    name="Run",
                    full_path="s/Run",
                    size=4,
                    protection="----rwed",
                    comment=None,
                    date="1978-01-01 00:00:00",
                    hash_chain=0,
                    parent=0,
                    extension_blocks=[],
                    data_blocks=[11],
                    data_block_count=1,
                    checksum_valid=True,
                    content=FileContentInfo(
                        kind="amiga_hunk_executable",
                        size=4,
                        sha256="deadbeef",
                        is_executable=True,
                        hunk_count=1,
                        target_type="program",
                        import_target=_program_import_target(),
                    ),
                )
            ],
            directories=[],
            bitmap=BitmapInfo(
                checksum_valid=True,
                free_blocks=1,
                allocated_blocks=10,
                total_blocks=11,
                percent_used=90.9,
            ),
            block_usage=BlockUsageInfo(summary={"boot": 2}, orphan_blocks=[]),
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    manifest = import_adf(adf_path, project_root=project_root)

    assert manifest.disk_id == "demo"
    manifest_path = project_root / "targets" / "amiga_disk_demo" / "manifest.json"
    assert manifest_path.exists()
    assert manifest.bootblock_target_name == "amiga_disk_demo__amiga_raw_bootblock"
    assert manifest.bootblock_target_path == "targets/amiga_disk_demo/targets/amiga_raw_bootblock"
    bootblock_dir = project_root / manifest.bootblock_target_path
    assert not (bootblock_dir / "entities.jsonl").exists()
    bootblock_source = json.loads((bootblock_dir / "source_binary.json").read_text(encoding="utf-8"))
    assert bootblock_source["kind"] == "raw_binary"
    assert bootblock_source["address_model"] == "local_offset"
    assert bootblock_source["load_address"] == 0x70000
    assert bootblock_source["entrypoint"] == 0x7000C
    assert bootblock_source["code_start_offset"] == 0x0C
    bootblock_metadata = json.loads((bootblock_dir / "target_metadata.json").read_text(encoding="utf-8"))
    assert bootblock_metadata["target_type"] == "bootblock"
    assert bootblock_metadata["entry_register_seeds"][0]["register"] == "A6"
    assert bootblock_metadata["entry_register_seeds"][1]["context_name"] == "trackdisk.device"
    assert bootblock_metadata["bootblock"]["entrypoint"] == 0x7000C

    assert [target.entry_path for target in manifest.imported_targets] == ["bootblock"]


def test_import_adf_materializes_c_decompressed_child_when_load_entry_known(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    startup_script = b"s:Run"

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        assert entry_path == "s/Run"
        return b"packed-parent"

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        lambda adf_file, *, extract_dir=None, include_tracks=False: _single_program_disk_analysis_with_startup(
            adf_file
        ),
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend",
        extract_disk_entry_with_startup,
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_binary_source_with_c_backend",
        lambda source_path, *, project_root: {
            "derived_target_suggestions": [
                {
                    "kind_id": 1,
                    "kind": "decompressed_payload",
                    "status_id": 2,
                    "status": "materializable",
                    "source_section": 0,
                    "source_section_offset": 0x1000,
                    "packed_size": 10,
                    "decompressed_size": 4,
                    "load_address": 0x4000,
                    "entrypoint": 0x4000,
                    "codec_id": "rnc1-old",
                    "codec_name": "RNC1: Rob Northen RNC1 Compressor (old)",
                    "payload_role": "stale_display_name",
                    "payload_role_id": 2,
                    "payload_role_confidence": "stale_display_name",
                    "payload_role_confidence_id": 1,
                    "parent_remains_active": "stale_display_name",
                    "parent_remains_active_id": 0,
                    "source_sha256": "11" * 32,
                    "decompressed_sha256": "22" * 32,
                }
            ]
        },
    )

    def fake_decompress(
        source_kind: str,
        source_path: str | Path,
        section_index: int,
        section_offset: int,
        packed_size: int,
        output_path: str | Path,
        *,
        project_root: Path,
    ) -> dict[str, object]:
        assert source_kind == "amiga-hunk"
        assert section_index == 0
        assert section_offset == 0x1000
        assert packed_size == 10
        Path(output_path).write_bytes(b"\x4E\x75\x4E\x75")
        return {
            "packed_payloads": [
                {
                    "found": True,
                    "provider_id": "ancient-cli",
                    "provider_path": "ext/tools/ancient/Ancient.exe",
                    "confidence": "provider-identified",
                    "source_sha256": "11" * 32,
                    "decompressed_sha256": "22" * 32,
                }
            ]
        }

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.decompress_packed_section_range_with_c_backend",
        fake_decompress,
    )

    manifest = import_adf(adf_path, project_root=project_root)

    parent = next(target for target in manifest.imported_targets if target.entry_path == "s/Run")
    child = next(target for target in manifest.imported_targets if target.target_type == "raw_binary")
    assert parent.derived_targets == [
        {
            "kind": "decompressed_payload",
            "kind_id": 1,
            "target_name": child.target_name,
            "packed_section_offset": 0x1000,
            "packed_size": 10,
            "codec_id": "rnc1-old",
            "payload_role": "primary_program",
            "payload_role_id": 2,
            "payload_role_confidence": "tool_inferred",
            "payload_role_confidence_id": 1,
            "parent_remains_active": "unknown",
            "parent_remains_active_id": 0,
        }
    ]
    assert child.derived_from is not None
    assert child.derived_from["parent_target"] == parent.target_name
    assert child.derived_from["load_address"] == 0x4000
    assert child.derived_from["payload_role"] == "primary_program"
    assert child.derived_from["payload_role_id"] == 2

    child_dir = project_root / child.target_path
    project = json.loads((child_dir / ".project.json").read_text(encoding="utf-8"))
    assert project["origin"]["project_origin_kind_id"] == 1
    assert project["origin"]["target_role_id"] == 1
    assert project["origin"]["payload_role"] == "primary_program"
    assert project["origin"]["payload_role_id"] == 2
    assert (child_dir / "binary.bin").read_bytes() == b"\x4E\x75\x4E\x75"
    source = json.loads((child_dir / "source_binary.json").read_text(encoding="utf-8"))
    assert source["kind"] == "raw_binary"
    assert source["address_model"] == "runtime_absolute"
    assert source["load_address"] == 0x4000
    assert source["entrypoint"] == 0x4000
    metadata = json.loads((child_dir / "target_metadata.json").read_text(encoding="utf-8"))
    assert metadata["target_type"] == "raw_binary"
    decompression = json.loads((child_dir / "decompression.json").read_text(encoding="utf-8"))
    assert decompression["compressor"]["id"] == "rnc1-old"
    assert decompression["payload_role"] == "primary_program"
    assert decompression["payload_role_id"] == 2
    assert decompression["packed"]["section_offset"] == 0x1000
    assert decompression["decompressed"]["sha256"] == "22" * 32


def test_import_adf_materializes_c_simulated_self_decrunch_child(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    output_bytes = b"\x4E\x75"
    output_hash = hashlib.sha256(output_bytes).hexdigest()
    event_id = "decompression:self_decrunch:section:0:00000000:00004000"
    startup_script = b"s:Run"

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        assert entry_path == "s/Run"
        return b"packed-parent"

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        lambda adf_file, *, extract_dir=None, include_tracks=False: _single_program_disk_analysis_with_startup(
            adf_file
        ),
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend",
        extract_disk_entry_with_startup,
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_binary_source_with_c_backend",
        lambda source_path, *, project_root: {
            "decompression_events": [
                {
                    "event_kind_id": 1,
                    "event_kind": "decompression",
                    "event_id": event_id,
                    "status_id": 5,
                    "status": "simulated_output_observed",
                    "source_kind_id": 3,
                    "source_kind": "self_decruncher",
                    "provider_id": "m68k-sim-decrunch",
                    "codec_id": "unknown-self-decrunch",
                    "codec_name": "Unidentified target-owned self-decruncher",
                    "payload_role_id": 2,
                    "payload_role": "primary_program",
                    "payload_role_confidence_id": 1,
                    "payload_role_confidence": "tool_inferred",
                    "parent_remains_active_id": 1,
                    "parent_remains_active": "false",
                    "decompressor_code_section": 0,
                    "decompressor_entry_offset": 0,
                    "transfer_offset": 14,
                    "load_address": 0x4000,
                    "entrypoint": 0x4000,
                    "simulated_output_size": len(output_bytes),
                    "simulated_output_sha256": output_hash,
                    "simulated_stop_reason_name": "pc_range",
                    "simulated_step_count": 4,
                    "simulated_write_count": 2,
                }
            ]
        },
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.decompress_packed_section_range_with_c_backend",
        lambda *args, **kwargs: pytest.fail("provider-backed decompression was used for simulated output"),
    )

    def fake_materialize(
        backend_name: str,
        path: str | Path,
        requested_event_id: str,
        output_path: str | Path,
        *,
        project_root: Path,
    ) -> dict[str, object]:
        assert backend_name == "amiga-hunk"
        assert requested_event_id == event_id
        Path(output_path).write_bytes(output_bytes)
        return {
            "status": "ok",
            "decompressed": {
                "size": len(output_bytes),
                "sha256": output_hash,
                "load_address": 0x4000,
                "entrypoint": 0x4000,
            },
        }

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.materialize_self_decrunch_event_with_c_backend",
        fake_materialize,
    )

    manifest = import_adf(adf_path, project_root=project_root)

    parent = next(target for target in manifest.imported_targets if target.entry_path == "s/Run")
    child = next(target for target in manifest.imported_targets if target.target_type == "raw_binary")
    assert parent.derived_targets == [
        {
            "kind": "decompressed_payload",
            "kind_id": 1,
            "target_name": child.target_name,
            "provider_id": "m68k-sim-decrunch",
            "event_id": event_id,
            "codec_id": "unknown-self-decrunch",
            "payload_role": "primary_program",
            "payload_role_id": 2,
            "payload_role_confidence": "tool_inferred",
            "payload_role_confidence_id": 1,
            "parent_remains_active": "false",
            "parent_remains_active_id": 1,
        }
    ]
    assert child.derived_from is not None
    assert child.derived_from["provider_id"] == "m68k-sim-decrunch"
    assert child.derived_from["event_id"] == event_id
    assert child.derived_from["payload_role"] == "primary_program"
    assert child.derived_from["payload_role_id"] == 2

    child_dir = project_root / child.target_path
    assert (child_dir / "binary.bin").read_bytes() == output_bytes
    source = json.loads((child_dir / "source_binary.json").read_text(encoding="utf-8"))
    assert source["kind"] == "raw_binary"
    assert source["load_address"] == 0x4000
    decompression = json.loads((child_dir / "decompression.json").read_text(encoding="utf-8"))
    assert decompression["source"]["kind"] == "self_decruncher"
    assert decompression["source"]["kind_id"] == 3
    assert decompression["source"]["event_id"] == event_id
    assert decompression["payload_role"] == "primary_program"
    assert decompression["payload_role_id"] == 2
    assert decompression["parent_remains_active"] == "false"
    assert decompression["parent_remains_active_id"] == 1
    assert decompression["decompressed"]["sha256"] == output_hash


def test_import_adf_materializes_c_recognized_unpacker_valid_child_from_real_fixture(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    _requires_c_backend_dlls()
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    fixture = PROJECT_ROOT / "tests" / "fixtures" / "hunk" / "damocles_tetragon_53b24620.bin"
    parent_bytes = fixture.read_bytes()
    startup_script = b"s:Run"

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        lambda adf_file, *, extract_dir=None, include_tracks=False: _single_program_disk_analysis_with_startup(
            adf_file
        ),
    )
    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "s/Run":
            return parent_bytes
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend",
        extract_disk_entry_with_startup,
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_binary_source_with_c_backend",
        lambda source_path, *, project_root: analyze_binary_source_with_c_backend(
            source_path, project_root=PROJECT_ROOT
        ),
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.materialize_recognized_unpacker_event_with_c_backend",
        lambda backend_name, path, event_id, output_path, *, project_root: (
            materialize_recognized_unpacker_event_with_c_backend(
                backend_name, path, event_id, output_path, project_root=PROJECT_ROOT
            )
        ),
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.decompress_packed_section_range_with_c_backend",
        lambda *args, **kwargs: pytest.fail("provider-backed decompression was used for native unpacker output"),
    )

    manifest = import_adf(adf_path, project_root=project_root)

    parent = next(target for target in manifest.imported_targets if target.entry_path == "s/Run")
    children = sorted(
        (target for target in manifest.imported_targets if target.target_type == "raw_binary"),
        key=lambda target: target.derived_from["source_section"] if target.derived_from is not None else -1,
    )
    assert len(children) == 1
    assert parent.derived_targets == [
        {
            "kind": "decompressed_payload",
            "kind_id": 1,
            "target_name": children[0].target_name,
            "provider_id": "c-tetragon-native",
            "event_id": children[0].derived_from["event_id"],
            "codec_id": "tetragon",
            "payload_role": "primary_program",
            "payload_role_id": 2,
            "payload_role_confidence": "native_unpack_entry_validated",
            "payload_role_confidence_id": 2,
            "parent_remains_active": "false",
            "parent_remains_active_id": 1,
        },
    ]
    expected = {
        1: (0x40000, 0x40000, 0x10000, "6fa11625a70f82fc4df5f318ccb149ceeb2687f4af36643c5089090d37a2c0b9"),
    }
    for child in children:
        assert child.derived_from is not None
        section = child.derived_from["source_section"]
        load_address, entrypoint, size, sha256 = expected[section]
        child_dir = project_root / child.target_path
        output = (child_dir / "binary.bin").read_bytes()
        assert len(output) == size
        assert hashlib.sha256(output).hexdigest() == sha256
        source = json.loads((child_dir / "source_binary.json").read_text(encoding="utf-8"))
        assert source["kind"] == "raw_binary"
        assert source["address_model"] == "runtime_absolute"
        assert source["load_address"] == load_address
        assert source["entrypoint"] == entrypoint
        decompression = json.loads((child_dir / "decompression.json").read_text(encoding="utf-8"))
        assert decompression["source"]["kind"] == "recognized_unpacker"
        assert decompression["source"]["kind_id"] == 2
        assert decompression["payload_role"] == "primary_program"
        assert decompression["payload_role_id"] == 2
        assert child.derived_from["payload_role"] == "primary_program"
        assert child.derived_from["payload_role_id"] == 2
        assert decompression["extraction"]["method"] == "c-tetragon-native"
        assert decompression["decompressed"]["sha256"] == sha256


def test_import_adf_refreshes_existing_c_decompressed_child(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    expected_packed_size = 10
    expected_bytes = b"\x4E\x75\x4E\x75"
    expected_hash = "22" * 32
    startup_script = b"s:Run"

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "s/Run":
            return b"packed-parent"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        lambda adf_file, *, extract_dir=None, include_tracks=False: _single_program_disk_analysis_with_startup(
            adf_file
        ),
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)

    def fake_analysis(source_path: str | Path, *, project_root: Path) -> dict[str, object]:
        return {
            "derived_target_suggestions": [
                {
                    "kind_id": 1,
                    "kind": "decompressed_payload",
                    "status_id": 2,
                    "status": "materializable",
                    "source_section": 0,
                    "source_section_offset": 0x1000,
                    "packed_size": expected_packed_size,
                    "decompressed_size": len(expected_bytes),
                    "load_address": 0x4000,
                    "entrypoint": 0x4000,
                    "codec_id": "rnc1-old",
                    "codec_name": "RNC1: Rob Northen RNC1 Compressor (old)",
                    "source_sha256": "11" * 32,
                    "decompressed_sha256": expected_hash,
                }
            ]
        }

    def fake_decompress(
        source_kind: str,
        source_path: str | Path,
        section_index: int,
        section_offset: int,
        packed_size: int,
        output_path: str | Path,
        *,
        project_root: Path,
    ) -> dict[str, object]:
        assert packed_size == expected_packed_size
        Path(output_path).write_bytes(expected_bytes)
        return {
            "packed_payloads": [
                {
                    "found": True,
                    "provider_id": "ancient-cli",
                    "provider_path": "ext/tools/ancient/Ancient.exe",
                    "confidence": "provider-identified",
                    "source_sha256": "11" * 32,
                    "decompressed_sha256": expected_hash,
                }
            ]
        }

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_binary_source_with_c_backend", fake_analysis)
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.decompress_packed_section_range_with_c_backend",
        fake_decompress,
    )

    first_manifest = import_adf(adf_path, project_root=project_root)
    child = next(target for target in first_manifest.imported_targets if target.target_type == "raw_binary")
    child_dir = project_root / child.target_path
    assert (child_dir / "binary.bin").read_bytes() == expected_bytes

    expected_packed_size = 12
    expected_bytes = b"\x60\x00\x00\x02"
    expected_hash = "33" * 32
    second_manifest = refresh_decompressed_payload_children("demo", project_root=project_root)
    refreshed = next(target for target in second_manifest.imported_targets if target.target_type == "raw_binary")
    assert refreshed.target_name == child.target_name
    assert (child_dir / "binary.bin").read_bytes() == expected_bytes
    decompression = json.loads((child_dir / "decompression.json").read_text(encoding="utf-8"))
    assert decompression["packed"]["size"] == 12
    assert decompression["decompressed"]["sha256"] == "33" * 32
    project = json.loads((child_dir / ".project.json").read_text(encoding="utf-8"))
    assert project["origin"]["packed_size"] == 12


def test_import_adf_refresh_removes_stale_decompressed_child_after_clean_reanalysis(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    output_bytes = b"\x4E\x75"
    startup_script = b"s:Run"

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "s/Run":
            return b"packed-parent"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        lambda adf_file, *, extract_dir=None, include_tracks=False: _single_program_disk_analysis_with_startup(
            adf_file
        ),
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)
    analysis_payload: dict[str, object] = {
        "derived_target_suggestions": [
            {
                "kind_id": 1,
                "kind": "decompressed_payload",
                "status_id": 2,
                "status": "materializable",
                "source_section": 0,
                "source_section_offset": 0x1000,
                "packed_size": 10,
                "decompressed_size": len(output_bytes),
                "load_address": 0x4000,
                "entrypoint": 0x4000,
                "codec_id": "rnc1-old",
                "codec_name": "RNC1: Rob Northen RNC1 Compressor (old)",
                "source_sha256": "11" * 32,
                "decompressed_sha256": "22" * 32,
            }
        ]
    }
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_binary_source_with_c_backend",
        lambda source_path, *, project_root: analysis_payload,
    )

    def fake_decompress(
        source_kind: str,
        source_path: str | Path,
        section_index: int,
        section_offset: int,
        packed_size: int,
        output_path: str | Path,
        *,
        project_root: Path,
    ) -> dict[str, object]:
        Path(output_path).write_bytes(output_bytes)
        return {
            "packed_payloads": [
                {
                    "found": True,
                    "provider_id": "ancient-cli",
                    "confidence": "provider-identified",
                    "source_sha256": "11" * 32,
                    "decompressed_sha256": "22" * 32,
                }
            ]
        }

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.decompress_packed_section_range_with_c_backend",
        fake_decompress,
    )

    first_manifest = import_adf(adf_path, project_root=project_root)
    child = next(target for target in first_manifest.imported_targets if target.target_type == "raw_binary")
    child_dir = project_root / child.target_path
    assert child_dir.exists()

    analysis_payload.clear()
    refreshed = refresh_decompressed_payload_children("demo", project_root=project_root)

    assert all(target.target_name != child.target_name for target in refreshed.imported_targets)
    assert not child_dir.exists()
    parent = next(target for target in refreshed.imported_targets if target.entry_path == "s/Run")
    assert parent.derived_targets is None


def test_import_adf_does_not_materialize_decompressed_child_without_runtime_metadata(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    startup_script = b"s:Run"

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "s/Run":
            return b"packed-parent"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        lambda adf_file, *, extract_dir=None, include_tracks=False: _single_program_disk_analysis_with_startup(
            adf_file
        ),
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_binary_source_with_c_backend",
        lambda source_path, *, project_root: {
            "derived_target_suggestions": [
                {
                    "kind_id": 1,
                    "kind": "decompressed_payload",
                    "status_id": 3,
                    "status": "needs_runtime_metadata",
                    "source_section": 0,
                    "source_section_offset": 0x1000,
                    "packed_size": 10,
                    "decompressed_size": 4,
                    "codec_id": "rnc1-old",
                }
            ]
        },
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.decompress_packed_section_range_with_c_backend",
        lambda *args, **kwargs: pytest.fail("weak decompression suggestion was materialized"),
    )

    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.entry_path for target in manifest.imported_targets] == ["bootblock", "s/Run"]
    parent = manifest.imported_targets[1]
    assert parent.derived_targets is None


def test_import_adf_does_not_materialize_non_materializable_decompressed_status(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    startup_script = b"s:Run"

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "s/Run":
            return b"packed-parent"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        lambda adf_file, *, extract_dir=None, include_tracks=False: _single_program_disk_analysis_with_startup(
            adf_file
        ),
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_binary_source_with_c_backend",
        lambda source_path, *, project_root: {
            "derived_target_suggestions": [
                {
                    "kind_id": 1,
                    "kind": "decompressed_payload",
                    "status_id": 0,
                    "status": "ambiguous",
                    "source_section": 0,
                    "source_section_offset": 0x1000,
                    "packed_size": 10,
                    "decompressed_size": 4,
                    "load_address": 0x4000,
                    "entrypoint": 0x4000,
                    "codec_id": "rnc1-old",
                }
            ]
        },
    )
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.decompress_packed_section_range_with_c_backend",
        lambda *args, **kwargs: pytest.fail("ambiguous decompression suggestion was materialized"),
    )

    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.entry_path for target in manifest.imported_targets] == ["bootblock", "s/Run"]
    assert manifest.imported_targets[0].derived_targets is None


def test_import_adf_ignores_loadwb_in_startup_sequence(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    startup_script = b"loadwb s/Run"

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "s/Run":
            return b"packed-parent"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        lambda adf_file, *, extract_dir=None, include_tracks=False: _single_program_disk_analysis_with_startup(
            adf_file
        ),
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)
    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.entry_path for target in manifest.imported_targets] == ["bootblock"]


def test_import_adf_ignores_startup_sequence_keyword_in_startup_sequence(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    startup_script = b"s/startup-sequence"

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "s/Run":
            return b"run-body"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        lambda adf_file, *, extract_dir=None, include_tracks=False: _single_program_disk_analysis_with_startup(
            adf_file
        ),
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)
    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.entry_path for target in manifest.imported_targets] == ["bootblock"]


def test_import_adf_ignores_echo_and_wait_commands_in_startup_sequence(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    startup_script = b'echo "                                             "\nwait 5\npandora'

    pandora_import_target = replace(
        _program_import_target(),
        entry_path="pandora",
        local_target_id="amiga_hunk_pandora_12345678",
    )
    def fake_analyze_adf(
        adf_file: str | Path, *, extract_dir: None | Path = None, include_tracks: bool = False
    ) -> AdfAnalysis:
        analysis = _single_program_disk_analysis_with_startup(adf_file)
        files = list(analysis.files)
        files.append(
            DiskFileEntry(
                block_num=30,
                name="pandora",
                full_path="pandora",
                size=4,
                protection="----rwed",
                comment=None,
                date="1978-01-01 00:00:00",
                hash_chain=0,
                parent=0,
                extension_blocks=[],
                data_blocks=[31],
                data_block_count=1,
                checksum_valid=True,
                content=FileContentInfo(
                    kind="amiga_hunk_executable",
                    size=4,
                    sha256="deadbeef",
                    is_executable=True,
                    hunk_count=1,
                    target_type="program",
                    import_target=pandora_import_target,
                ),
            ),
        )
        return replace(analysis, files=files)

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "pandora":
            return b"pandora-body"
        if entry_path == "s/Run":
            return b"run-body"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        fake_analyze_adf,
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)
    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.entry_path for target in manifest.imported_targets] == ["bootblock", "pandora"]


def test_import_adf_ignores_stack_command_in_root_if_only_c_variant_exists(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    startup_script = b"stack 1800"

    def fake_analyze_adf(
        adf_file: str | Path, *, extract_dir: None | Path = None, include_tracks: bool = False
    ) -> AdfAnalysis:
        analysis = _single_program_disk_analysis_with_startup(adf_file)
        files = list(analysis.files)
        files.append(
            DiskFileEntry(
                block_num=30,
                name="Stack",
                full_path="c/Stack",
                size=4,
                protection="----rwed",
                comment=None,
                date="1978-01-01 00:00:00",
                hash_chain=0,
                parent=0,
                extension_blocks=[],
                data_blocks=[31],
                data_block_count=1,
                checksum_valid=True,
                content=FileContentInfo(
                    kind="data",
                    size=4,
                    sha256="cafebabe",
                    is_executable=False,
                    hunk_count=None,
                    target_type="raw_binary",
                ),
            )
        )
        return replace(analysis, files=files)

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "s/Run":
            return b"run-body"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        fake_analyze_adf,
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)
    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.entry_path for target in manifest.imported_targets] == ["bootblock"]


def test_import_adf_allows_run_command_without_args_in_startup_sequence(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    startup_script = b"run"

    run_import_target = replace(
        _program_import_target(),
        entry_path="run",
        local_target_id="amiga_hunk_run_12345678",
    )
    def fake_analyze_adf(
        adf_file: str | Path, *, extract_dir: None | Path = None, include_tracks: bool = False
    ) -> AdfAnalysis:
        analysis = _single_program_disk_analysis_with_startup(adf_file)
        files = list(analysis.files)
        files.append(
            DiskFileEntry(
                block_num=30,
                name="run",
                full_path="run",
                size=4,
                protection="----rwed",
                comment=None,
                date="1978-01-01 00:00:00",
                hash_chain=0,
                parent=0,
                extension_blocks=[],
                data_blocks=[31],
                data_block_count=1,
                checksum_valid=True,
                content=FileContentInfo(
                    kind="amiga_hunk_executable",
                    size=4,
                    sha256="beefbeef",
                    is_executable=True,
                    hunk_count=1,
                    target_type="program",
                    import_target=run_import_target,
                ),
            ),
        )
        return replace(analysis, files=files)

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "run":
            return b"run-body"
        if entry_path == "s/Run":
            return b"run-body"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        fake_analyze_adf,
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)
    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.entry_path for target in manifest.imported_targets] == ["bootblock", "run"]


def test_import_adf_ignores_run_command_with_arguments_in_startup_sequence(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")
    startup_script = b"run System:Utilities"

    run_import_target = replace(
        _program_import_target(),
        entry_path="run",
        local_target_id="amiga_hunk_run_12345678",
    )
    def fake_analyze_adf(
        adf_file: str | Path, *, extract_dir: None | Path = None, include_tracks: bool = False
    ) -> AdfAnalysis:
        analysis = _single_program_disk_analysis_with_startup(adf_file)
        files = list(analysis.files)
        files.append(
            DiskFileEntry(
                block_num=30,
                name="run",
                full_path="run",
                size=4,
                protection="----rwed",
                comment=None,
                date="1978-01-01 00:00:00",
                hash_chain=0,
                parent=0,
                extension_blocks=[],
                data_blocks=[31],
                data_block_count=1,
                checksum_valid=True,
                content=FileContentInfo(
                    kind="amiga_hunk_executable",
                    size=4,
                    sha256="beefbeef",
                    is_executable=True,
                    hunk_count=1,
                    target_type="program",
                    import_target=run_import_target,
                ),
            ),
        )
        return replace(analysis, files=files)

    def extract_disk_entry_with_startup(
        adf_file: str | Path, entry_path: str, *, project_root: Path
    ) -> bytes:
        if entry_path == "s/startup-sequence":
            return startup_script
        if entry_path == "run":
            return b"run-body"
        if entry_path == "System:Utilities":
            return b"unused"
        if entry_path == "s/Run":
            return b"run-body"
        pytest.fail(f"unexpected entry_path: {entry_path}")

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project.analyze_adf",
        fake_analyze_adf,
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.extract_disk_entry_with_c_backend", extract_disk_entry_with_startup)
    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.entry_path for target in manifest.imported_targets] == ["bootblock"]


def test_import_adf_creates_raw_target_for_bootloader_disk_stage(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_bytes = bytearray(b"\x00" * 0x400)
    adf_bytes[0x200:0x204] = b"\x4E\x75\x4E\x75"
    adf_path.write_bytes(bytes(adf_bytes))

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert Path(adf_file) == adf_path
        assert extract_dir is None
        assert include_tracks is True
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=len(adf_bytes),
                variant="demo",
                total_sectors=2,
                sectors_per_track=1,
                is_dos=False,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=0,
                fs_type="0",
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=0,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=0.0,
                import_target=_bootblock_import_target(),
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
            ),
            bootloader_analysis=BootloaderAnalysis(
                stages=[
                    BootloaderStage(
                        name="boot",
                        base_addr=0x0C,
                        entry_addr=0x0C,
                        size=1012,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x40000,
                    ),
                    BootloaderStage(
                        name="stage_1",
                        base_addr=0x40000,
                        entry_addr=0x40000,
                        size=4,
                        materialized=True,
                        reachable_instruction_count=2,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[
                            BootloaderDiskRead(
                                instruction_addr=0x2E,
                                command_name=BootloaderDiskCommand.CMD_READ,
                                disk_offset=0x200,
                                byte_length=4,
                                destination_addr=0x40000,
                                source_kind=BootloaderTransferSourceKind.LOGICAL_DISK_OFFSET,
                            )
                        ],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x40000,
                        import_target=_bootloader_stage_import_target(),
                    ),
                ],
                memory_regions=[],
                transfers=[],
            ),
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    manifest = import_adf(adf_path, project_root=project_root)

    stage_target = next(target for target in manifest.imported_targets if target.target_type == "bootloader_stage")
    assert stage_target.target_name == "amiga_disk_demo__amiga_raw_bootloader_stage_1"
    assert stage_target.entry_path == "bootloader/stage_1"
    assert stage_target.binary_path == f"{adf_path.as_posix()}::bootloader/stage_1"
    stage_dir = project_root / stage_target.target_path
    assert (stage_dir / "binary.bin").read_bytes() == b"\x4E\x75\x4E\x75"
    source = json.loads((stage_dir / "source_binary.json").read_text(encoding="utf-8"))
    assert source["kind"] == "raw_binary"
    assert source["address_model"] == "runtime_absolute"
    assert source["load_address"] == 0x40000
    assert source["entrypoint"] == 0x40000
    assert source["code_start_offset"] == 0
    metadata = json.loads((stage_dir / "target_metadata.json").read_text(encoding="utf-8"))
    assert metadata["target_type"] == "bootloader_stage"
    assert metadata["entry_register_seeds"][0]["register"] == "A6"
    assert metadata["entry_register_seeds"][0]["note"] == "ExecBase"
    assert metadata["entry_register_seeds"][1]["register"] == "A1"


def test_import_adf_materializes_bootblock_disk_read_fact_stage(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_bytes = bytearray(b"\x00" * 0x600)
    adf_bytes[0x400:0x404] = b"\x4E\x75\x4E\x75"
    adf_path.write_bytes(bytes(adf_bytes))

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert Path(adf_file) == adf_path
        assert extract_dir is None
        assert include_tracks is True
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=len(adf_bytes),
                variant="demo",
                total_sectors=3,
                sectors_per_track=1,
                is_dos=False,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=0,
                fs_type="0",
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=0,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=0.0,
                import_target=_bootblock_import_target(),
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
            ),
        )

    def fake_bootblock_analysis(
        bootblock_target_dir: Path,
        *,
        project_root: Path,
    ) -> dict[str, object]:
        assert bootblock_target_dir == project_root / "targets" / "amiga_disk_demo" / "targets" / "amiga_raw_bootblock"
        return {
            "sections": [
                {
                    "recovered_platform_disk_reads": [
                        {
                            "offset": 0x3E,
                            "command_value": 2,
                            "command_name": "CMD_READ",
                            "disk_offset": 0x400,
                            "byte_length": 4,
                            "destination_addr": 0x1E200,
                            "source_kind": "logical_disk_offset",
                        }
                    ]
                }
            ]
        }

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project._analyze_bootblock_source_for_disk_reads",
        fake_bootblock_analysis,
    )

    manifest = import_adf(adf_path, project_root=project_root)

    stage_target = next(target for target in manifest.imported_targets if target.target_type == "bootloader_stage")
    assert stage_target.target_name == "amiga_disk_demo__amiga_raw_bootloader_stage_1"
    assert stage_target.entry_path == "bootloader/stage_1"
    assert stage_target.binary_path == f"{adf_path.as_posix()}::bootloader/stage_1"
    stage_dir = project_root / stage_target.target_path
    assert (stage_dir / "binary.bin").read_bytes() == b"\x4E\x75\x4E\x75"
    source = json.loads((stage_dir / "source_binary.json").read_text(encoding="utf-8"))
    assert source["kind"] == "raw_binary"
    assert source["address_model"] == "runtime_absolute"
    assert source["load_address"] == 0x1E200
    assert source["entrypoint"] == 0x1E200
    assert source["code_start_offset"] == 0
    assert source["parent_disk_id"] == "demo"
    assert source["disk_byte_offset"] == 0x400
    assert source["disk_byte_size"] == 4
    assert source["source_kind"] == "logical_disk_offset"
    assert source["bootblock_read_instruction_offset"] == 0x3E
    metadata = json.loads((stage_dir / "target_metadata.json").read_text(encoding="utf-8"))
    assert metadata["target_type"] == "bootloader_stage"
    manifest_payload = json.loads(
        (project_root / "targets" / "amiga_disk_demo" / "manifest.json").read_text(encoding="utf-8")
    )
    manifest_stage = next(
        target for target in manifest_payload["imported_targets"] if target["target_type"] == "bootloader_stage"
    )
    assert manifest_stage["target_name"] == "amiga_disk_demo__amiga_raw_bootloader_stage_1"
    assert manifest_stage["entry_path"] == "bootloader/stage_1"


def test_import_adf_does_not_materialize_incomplete_bootblock_disk_read_fact(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_bytes = b"\x00" * 0x600
    adf_path.write_bytes(adf_bytes)

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert Path(adf_file) == adf_path
        assert extract_dir is None
        assert include_tracks is True
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=len(adf_bytes),
                variant="demo",
                total_sectors=3,
                sectors_per_track=1,
                is_dos=False,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=0,
                fs_type="0",
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=0,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=0.0,
                import_target=_bootblock_import_target(),
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
            ),
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)
    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.project._analyze_bootblock_source_for_disk_reads",
        lambda bootblock_target_dir, *, project_root: {
            "sections": [
                {
                    "recovered_platform_disk_reads": [
                        {
                            "offset": 0x3E,
                            "command_name": "CMD_READ",
                            "disk_offset": 0x500,
                            "byte_length": 0x200,
                            "destination_addr": 0x1E200,
                            "source_kind": "logical_disk_offset",
                        }
                    ]
                }
            ]
        },
    )

    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.target_type for target in manifest.imported_targets] == ["bootblock"]
    assert not (project_root / "targets" / "amiga_disk_demo" / "targets" / "amiga_raw_bootloader_stage_1").exists()


def test_import_adf_does_not_create_raw_target_without_bootloader_stage_import(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"\x00" * 0x400)

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert Path(adf_file) == adf_path
        assert extract_dir is None
        assert include_tracks is True
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=0x400,
                variant="demo",
                total_sectors=2,
                sectors_per_track=1,
                is_dos=False,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=0,
                fs_type="0",
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=0,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=0.0,
                import_target=_bootblock_import_target(),
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
            ),
            bootloader_analysis=BootloaderAnalysis(
                stages=[
                    BootloaderStage(
                        name="boot",
                        base_addr=0x0C,
                        entry_addr=0x0C,
                        size=1012,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=None,
                    )
                ],
                memory_regions=[],
                transfers=[],
            ),
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    manifest = import_adf(adf_path, project_root=project_root)

    assert [target.target_type for target in manifest.imported_targets] == ["bootblock"]
    assert not (project_root / "targets" / "amiga_disk_demo" / "targets" / "amiga_raw_bootloader_stage_1").exists()


def test_import_adf_ice_uses_c_bootloader_stage_materialization(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    source_adf = repo_root / "bin" / "Ice (1991-06-28)(The Silents).adf"
    disk_cli = repo_root / "src" / "build" / "platform_disk_cli.exe"
    if not source_adf.exists():
        pytest.skip("Ice ADF fixture is not present")
    if not disk_cli.exists():
        pytest.skip("platform_disk_cli.exe is not built; run cmd /c src\\build.bat")
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / source_adf.name
    shutil.copy2(source_adf, adf_path)

    manifest = import_adf(adf_path, project_root=project_root)

    assert manifest.bootblock_target_name == "amiga_disk_ice-1991-06-28-the-silents__amiga_raw_bootblock"
    stage_target = next(target for target in manifest.imported_targets if target.entry_path == "bootloader/stage_1")
    assert stage_target.target_type == "bootloader_stage"
    stage_dir = project_root / stage_target.target_path
    assert (stage_dir / "binary.bin").stat().st_size == 21504
    source = json.loads((stage_dir / "source_binary.json").read_text(encoding="utf-8"))
    assert source["load_address"] == 0x40000
    assert source["entrypoint"] == 0x40000


def test_import_adf_epic_materializes_post_read_copy_handoff_view(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    source_adf = repo_root / "bin" / "Epic (1992)(Ocean)(Disk 1 of 3)[cr FSN - BST].adf"
    disk_cli = repo_root / "src" / "build" / "platform_disk_cli.exe"
    if not source_adf.exists():
        pytest.skip("Epic ADF fixture is not present")
    if not disk_cli.exists():
        pytest.skip("platform_disk_cli.exe is not built; run cmd /c src\\build.bat")
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / source_adf.name
    shutil.copy2(source_adf, adf_path)

    manifest = import_adf(adf_path, disk_id="epic", project_root=project_root)

    read_stage = None
    for target in manifest.imported_targets:
        if target.target_type != "bootloader_stage":
            continue
        stage_dir = project_root / target.target_path
        source = json.loads((stage_dir / "source_binary.json").read_text(encoding="utf-8"))
        if source["load_address"] == 0x1E200:
            read_stage = (target, source)
            break
    assert read_stage is not None
    stage_target, source = read_stage
    assert source["bootblock_read_instruction_offset"] == 0x58
    assert stage_target.entry_path == "bootloader/stage_2"
    stage_dir = project_root / stage_target.target_path
    metadata = json.loads((stage_dir / "target_metadata.json").read_text(encoding="utf-8"))
    assert metadata["execution_views"] == [
        {
            "source_start": 0x1E00,
            "source_end": 0x4E00,
            "base_addr": 0x864,
            "name": "bootstrapped_code",
            "seed_origin": "autodoc",
            "review_status": "seeded",
            "citation": "bootblock:runtime_copy:0000008c",
            "comment": "Bootblock copies $00020000-$00022FFF to $00000864 and hands off at $0000086C",
        }
    ]


def test_import_adf_materializes_bootloader_copy_handoff_as_execution_view(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    stage1_bytes = bytes.fromhex("1122334455667788")
    adf_bytes = bytearray(b"\x00" * 0x400)
    adf_bytes[0x200:0x200 + len(stage1_bytes)] = stage1_bytes
    adf_path.write_bytes(bytes(adf_bytes))

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert Path(adf_file) == adf_path
        assert extract_dir is None
        assert include_tracks is True
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=len(adf_bytes),
                variant="demo",
                total_sectors=2,
                sectors_per_track=1,
                is_dos=False,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=0,
                fs_type="0",
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=0,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=0.0,
                import_target=_bootblock_import_target(),
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
            ),
            bootloader_analysis=BootloaderAnalysis(
                stages=[
                    BootloaderStage(
                        name="boot",
                        base_addr=0x0C,
                        entry_addr=0x0C,
                        size=1012,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x40000,
                    ),
                    BootloaderStage(
                        name="stage_1",
                        base_addr=0x40000,
                        entry_addr=0x40000,
                        size=len(stage1_bytes),
                        materialized=True,
                        reachable_instruction_count=2,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[
                            BootloaderDiskRead(
                                instruction_addr=0x2E,
                                command_name=BootloaderDiskCommand.CMD_READ,
                                disk_offset=0x200,
                                byte_length=len(stage1_bytes),
                                destination_addr=0x40000,
                                source_kind=BootloaderTransferSourceKind.LOGICAL_DISK_OFFSET,
                            )
                        ],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x6000,
                        import_target=_bootloader_stage_import_target(byte_size=len(stage1_bytes)),
                    ),
                    BootloaderStage(
                        name="stage_2",
                        base_addr=0x6000,
                        entry_addr=0x6000,
                        size=4,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[
                            BootloaderMemoryCopy(
                                instruction_addr=0x40010,
                                source_addr=0x40002,
                                destination_addr=0x6000,
                                byte_length=4,
                            )
                        ],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x6000,
                    ),
                ],
                memory_regions=[],
                transfers=[],
            ),
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    manifest = import_adf(adf_path, project_root=project_root)

    assert all(target.entry_path != "bootloader/stage_2" for target in manifest.imported_targets)
    assert [target.entry_path for target in manifest.imported_targets if target.target_type == "bootloader_stage"] == [
        "bootloader/stage_1"
    ]
    stage1_target = next(target for target in manifest.imported_targets if target.entry_path == "bootloader/stage_1")
    stage1_dir = project_root / stage1_target.target_path
    stage1_metadata = json.loads((stage1_dir / "target_metadata.json").read_text(encoding="utf-8"))
    assert stage1_metadata["execution_views"] == [
        {
            "source_start": 2,
            "source_end": 6,
            "base_addr": 0x6000,
            "name": "bootstrapped_code",
            "seed_origin": "autodoc",
            "review_status": "seeded",
            "citation": "bootloader:stage_2:runtime_copy:00040010",
            "comment": "Bootloader copies $00040002-$00040005 to $00006000 and hands off at $00006000",
        }
    ]


def test_import_adf_keeps_bootloader_copy_metadata_without_creating_stage_2_target(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    stage1_bytes = bytes.fromhex("1122334455667788")
    adf_bytes = bytearray(b"\x00" * 0x400)
    adf_bytes[0x200:0x200 + len(stage1_bytes)] = stage1_bytes
    adf_path.write_bytes(bytes(adf_bytes))

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert Path(adf_file) == adf_path
        assert extract_dir is None
        assert include_tracks is True
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=len(adf_bytes),
                variant="demo",
                total_sectors=2,
                sectors_per_track=1,
                is_dos=False,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=0,
                fs_type="0",
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=0,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=0.0,
                import_target=_bootblock_import_target(),
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
            ),
            bootloader_analysis=BootloaderAnalysis(
                stages=[
                    BootloaderStage(
                        name="boot",
                        base_addr=0x0C,
                        entry_addr=0x0C,
                        size=1012,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x40000,
                    ),
                    BootloaderStage(
                        name="stage_1",
                        base_addr=0x40000,
                        entry_addr=0x40000,
                        size=len(stage1_bytes),
                        materialized=True,
                        reachable_instruction_count=2,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[
                            BootloaderDiskRead(
                                instruction_addr=0x2E,
                                command_name=BootloaderDiskCommand.CMD_READ,
                                disk_offset=0x200,
                                byte_length=len(stage1_bytes),
                                destination_addr=0x40000,
                                source_kind=BootloaderTransferSourceKind.LOGICAL_DISK_OFFSET,
                            )
                        ],
                        memory_copies=[
                            BootloaderMemoryCopy(
                                instruction_addr=0x40010,
                                source_addr=0x40002,
                                destination_addr=0x6000,
                                byte_length=4,
                            )
                        ],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x6000,
                        import_target=_bootloader_stage_import_target(
                            byte_size=len(stage1_bytes),
                            execution_views=[
                                {
                                    "source_start": 2,
                                    "source_end": 6,
                                    "base_addr": 0x6000,
                                    "name": "bootstrapped_code",
                                    "seed_origin": "autodoc",
                                    "review_status": "seeded",
                                    "citation": "bootloader:stage_1:handoff",
                                    "comment": "Embedded bootstrapped code executes from $00006000",
                                }
                            ],
                        ),
                    ),
                    BootloaderStage(
                        name="stage_2",
                        base_addr=0x6000,
                        entry_addr=0x6000,
                        size=4,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x6000,
                    ),
                ],
                memory_regions=[],
                transfers=[],
            ),
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    manifest = import_adf(adf_path, project_root=project_root)

    assert all(target.entry_path != "bootloader/stage_2" for target in manifest.imported_targets)

    stage1_target = next(target for target in manifest.imported_targets if target.entry_path == "bootloader/stage_1")
    stage1_dir = project_root / stage1_target.target_path
    stage1_metadata = json.loads((stage1_dir / "target_metadata.json").read_text(encoding="utf-8"))
    assert stage1_metadata.get("seeded_code_labels", []) == []
    assert stage1_metadata.get("seeded_code_entrypoints", []) == []
    assert stage1_metadata.get("absolute_code_labels", []) == []
    assert stage1_metadata["execution_views"][0]["name"] == "bootstrapped_code"
    assert stage1_metadata["execution_views"][0]["source_start"] == 2
    assert stage1_metadata["execution_views"][0]["base_addr"] == 0x6000


def test_import_adf_does_not_create_raw_target_for_bootloader_decoded_stage(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"\x00" * 0x400)

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert Path(adf_file) == adf_path
        assert extract_dir is None
        assert include_tracks is True
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=0x400,
                variant="demo",
                total_sectors=2,
                sectors_per_track=1,
                is_dos=False,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=0,
                fs_type="0",
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=0,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=0.0,
                import_target=_bootblock_import_target(),
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
            ),
            bootloader_analysis=BootloaderAnalysis(
                stages=[
                    BootloaderStage(
                        name="boot",
                        base_addr=0x0C,
                        entry_addr=0x0C,
                        size=1012,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x6000,
                    ),
                    BootloaderStage(
                        name="stage_1",
                        base_addr=0x6000,
                        entry_addr=0x6000,
                        size=4,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[
                            BootloaderDerivedRegion(
                                base_addr=0x6000,
                                byte_length=4,
                                concrete_byte_count=4,
                                complete=True,
                                data_hex="4e754e75",
                            )
                        ],
                        handoffs=[],
                        handoff_target=0x6000,
                    ),
                ],
                memory_regions=[],
                transfers=[],
            ),
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    manifest = import_adf(adf_path, project_root=project_root)

    assert not any(target.target_type == "bootloader_stage" for target in manifest.imported_targets)


def test_import_adf_creates_raw_target_for_unique_bootloader_raw_span(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_bytes = bytearray(b"\x00" * 0x400)
    adf_bytes[0x120:0x128] = b"\x44\x89\xAA\xBB\xCC\xDD\xEE\xFF"
    adf_path.write_bytes(bytes(adf_bytes))

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert Path(adf_file) == adf_path
        assert extract_dir is None
        assert include_tracks is True
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=len(adf_bytes),
                variant="demo",
                total_sectors=2,
                sectors_per_track=1,
                is_dos=False,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=0,
                fs_type="0",
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=0,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=0.0,
                import_target=_bootblock_import_target(),
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
            ),
            bootloader_analysis=BootloaderAnalysis(
                stages=[
                    BootloaderStage(
                        name="boot",
                        base_addr=0x0C,
                        entry_addr=0x0C,
                        size=1012,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x6000,
                    ),
                    BootloaderStage(
                        name="stage_2",
                        base_addr=0x6000,
                        entry_addr=0x6000,
                        size=4,
                        materialized=True,
                        reachable_instruction_count=1,
                        hardware_accesses=[],
                        loads=[],
                        disk_reads=[],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[
                            BootloaderDecodeRegion(
                                instruction_addr=0x6010,
                                input_buffer_addr=0x2000,
                                input_consumed_byte_offset=0,
                                input_consumed_byte_length=4,
                                checksum_gate_addr=None,
                                checksum_gate_kind=None,
                                input_source_kind=BootloaderDecodeInputSourceKind.CUSTOM_TRACK_DMA_BUFFER,
                                input_required_source_kind=BootloaderDecodeRequiredSourceKind.RAW_CUSTOM_TRACK_BYTES,
                                input_source_candidates=[
                                    RawTrackSource(track=0, cylinder=0, head=0, byte_offset=0x100, byte_length=0x100)
                                ],
                                input_source_candidate_spans=[
                                    RawTrackSourceSpan(
                                        start_track=0,
                                        end_track=0,
                                        start_byte_offset=0x120,
                                        byte_length=8,
                                    )
                                ],
                                input_required_byte_length=8,
                                input_concrete_byte_count=0,
                                input_complete=False,
                                input_materializable=False,
                                input_missing_reason="custom_track_decode_mapping_unresolved",
                                output_base_addr=0x6000,
                                output_addr=0x6000,
                                byte_length=4,
                                write_loop_addr=0x6010,
                                import_target=_raw_span_import_target(byte_offset=0x120, byte_size=8),
                            )
                        ],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x6000,
                    ),
                ],
                memory_regions=[],
                transfers=[],
            ),
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    manifest = import_adf(adf_path, project_root=project_root)

    span_target = next(target for target in manifest.imported_targets if target.target_type == "bootloader_raw_span")
    assert span_target.target_name == "amiga_disk_demo__amiga_raw_bootloader_stage_2_raw_span_0"
    assert span_target.entry_path == "bootloader/stage_2/raw_span_0"
    span_dir = project_root / span_target.target_path
    assert (span_dir / "binary.bin").read_bytes() == b"\x44\x89\xAA\xBB\xCC\xDD\xEE\xFF"
    source = json.loads((span_dir / "source_binary.json").read_text(encoding="utf-8"))
    assert source["kind"] == "raw_binary"
    assert source["address_model"] == "local_offset"
    assert source["load_address"] == 0
    assert source["entrypoint"] == 0
    assert source["code_start_offset"] == 0
    metadata = json.loads((span_dir / "target_metadata.json").read_text(encoding="utf-8"))
    assert metadata["target_type"] == "bootloader_raw_span"
    assert metadata["entry_register_seeds"] == []


def test_disk_content_summary_classifies_library_targets_from_resident_structure(
    tmp_path: Path,
) -> None:
    code = bytearray(0x80)
    code[0:2] = bytes.fromhex("4afc")
    code[2:6] = (0).to_bytes(4, byteorder="big")
    code[14:18] = (0x20).to_bytes(4, byteorder="big")
    code[18:22] = (0x30).to_bytes(4, byteorder="big")
    code[22:26] = (0x40).to_bytes(4, byteorder="big")
    code[10] = 0x00
    code[11] = 37
    code[12] = 9
    code[0x20:0x2D] = b"icon.library\x00"
    code[0x30:0x3A] = b"icon 37.1\x00"

    content = _content_from_c_disk_inspect(tmp_path, _hunk_executable(bytes(code)))

    assert content.target_type == "library"
    assert content.import_target is not None
    assert content.import_target.target_type == "library"
    assert content.import_target.target_metadata["target_type"] == "library"
    assert content.resident is not None
    assert content.resident.name == "icon.library"
    assert content.library is not None
    assert content.library.library_name == "icon.library"
    assert content.library.version == 37
    assert content.library.public_function_count == 12
    assert content.library.total_lvo_count == 19
    metadata = TargetMetadata.from_dict(content.import_target.target_metadata)
    assert metadata.resident is not None
    assert metadata.resident.offset == 0
    assert metadata.resident.matchword == 0x4AFC


def test_disk_content_summary_extracts_autoinit_library_entrypoints(
    tmp_path: Path,
) -> None:
    code = bytearray(0x120)
    code[0:2] = bytes.fromhex("4afc")
    code[2:6] = (0).to_bytes(4, byteorder="big")
    code[6:10] = (0x120).to_bytes(4, byteorder="big")
    code[10] = 0x80
    code[11] = 37
    code[12] = 9
    code[13] = 0
    code[14:18] = (0x20).to_bytes(4, byteorder="big")
    code[18:22] = (0x30).to_bytes(4, byteorder="big")
    code[22:26] = (0x40).to_bytes(4, byteorder="big")
    code[0x20:0x2D] = b"icon.library\x00"
    code[0x30:0x3A] = b"icon 37.1\x00"
    code[0x40:0x44] = (0x24).to_bytes(4, byteorder="big")
    code[0x44:0x48] = (0x50).to_bytes(4, byteorder="big")
    code[0x48:0x4C] = (0).to_bytes(4, byteorder="big")
    code[0x4C:0x50] = (0x90).to_bytes(4, byteorder="big")
    for index, target in enumerate((0xA0, 0xA8, 0xB0, 0xB8, 0xC0)):
        start = 0x50 + index * 4
        code[start:start + 4] = target.to_bytes(4, byteorder="big")
    code[0x64:0x68] = (0xFFFFFFFF).to_bytes(4, byteorder="big", signed=False)

    content = _content_from_c_disk_inspect(tmp_path, _hunk_executable(bytes(code)))

    assert content.target_type == "library"
    assert content.import_target is not None
    assert content.import_target.target_type == "library"
    assert content.resident is not None
    assert content.resident.autoinit is not None
    assert content.resident.autoinit.payload_offset == 0x40
    assert content.resident.autoinit.vectors_offset == 0x50
    assert content.resident.autoinit.vector_offsets == (0xA0, 0xA8, 0xB0, 0xB8, 0xC0)
    assert content.resident.autoinit.init_func_offset == 0x90
    metadata = TargetMetadata.from_dict(content.import_target.target_metadata)
    assert metadata.resident is not None
    assert metadata.resident.autoinit is not None
    assert metadata.resident.autoinit.init_func_offset == 0x90
    assert metadata.resident.autoinit.vector_offsets == (0xA0, 0xA8, 0xB0, 0xB8, 0xC0)


def test_disk_content_summary_defaults_to_program_without_resident(
    tmp_path: Path,
) -> None:
    content = _content_from_c_disk_inspect(tmp_path, _hunk_executable(b"\x4e\x75\x4e\x75"))

    assert content.target_type == "program"
    assert content.import_target is not None
    assert content.import_target.target_type == "program"
    assert content.import_target.target_metadata["target_type"] == "program"
    assert content.resident is None
    assert content.library is None


def test_disk_content_summary_classifies_iff_container(tmp_path: Path) -> None:
    payload = b"FORM" + (4).to_bytes(4, byteorder="big") + b"ILBM"

    content = _content_from_c_disk_inspect(tmp_path, payload)

    assert content.kind == "iff_container"
    assert content.size == len(payload)
    assert content.sha256
    assert content.group_id == "FORM"
    assert content.form_id == "ILBM"
    assert content.is_executable is None
    assert content.target_type is None
    assert content.import_target is None


def test_disk_content_summary_keeps_malformed_hunk_metadata_stable(tmp_path: Path) -> None:
    payload = b"\x00\x00\x03\xf3BROKEN"

    content = _content_from_c_disk_inspect(tmp_path, payload)

    assert content.kind == "amiga_hunk_executable"
    assert content.size == len(payload)
    assert content.sha256
    assert content.is_executable is False
    assert content.hunk_count is None
    assert content.target_type is None
    assert content.import_target is None
    assert content.resident is None
    assert content.library is None


def test_create_disk_project_keeps_non_dos_disk_without_imported_targets(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert include_tracks is True
        assert extract_dir is None
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=901120,
                variant="DD",
                total_sectors=1760,
                sectors_per_track=11,
                is_dos=True,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=0,
                fs_type="OFS",
                fs_description="DOS\\0 - Old File System",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=0,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=1.0,
                import_target=_bootblock_import_target(),
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
                dos_magic_without_filesystem=True,
                filesystem_parse_error="Unexpected root hash table size",
            ),
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    manifest = create_disk_project(adf_path, project_root=project_root)

    assert manifest.disk_id == "demo"
    assert manifest.analysis.disk_info.is_dos is True
    assert manifest.analysis.filesystem is None
    assert manifest.analysis.non_dos is not None
    assert [target.target_name for target in manifest.imported_targets] == [
        "amiga_disk_demo__amiga_raw_bootblock",
    ]
    assert (project_root / "targets" / "amiga_disk_demo" / "manifest.json").exists()


def test_create_disk_project_rejects_prefixed_disk_id(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert include_tracks is True
        assert extract_dir is None
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=901120,
                variant="DD",
                total_sectors=1760,
                sectors_per_track=11,
                is_dos=True,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=1,
                fs_type="FFS",
                fs_description="DOS\\1 - Fast File System",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=880,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=1.0,
                import_target=_bootblock_import_target(),
            ),
            filesystem=FilesystemInfo(
                type="FFS",
                volume_name="Demo",
                directories=1,
                files=1,
                total_file_size=4,
            ),
            files=[],
            directories=[],
            bitmap=None,
            block_usage=None,
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)
    with pytest.raises(
        DiskAnalysisError, match="disk_id argument must be bare disk id; do not prefix with 'amiga_disk_'"
    ):
        create_disk_project(adf_path, disk_id="amiga_disk_demo", project_root=project_root)
    assert not (project_root / "targets" / "amiga_disk_demo" / "manifest.json").exists()


def test_create_disk_project_requires_complete_dos_analysis(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert include_tracks is True
        assert extract_dir is None
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=901120,
                variant="DD",
                total_sectors=1760,
                sectors_per_track=11,
                is_dos=True,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=1,
                fs_type="FFS",
                fs_description="DOS\\1 - Fast File System",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=880,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=1.0,
                import_target=_bootblock_import_target(),
            ),
            filesystem=FilesystemInfo(
                type="FFS",
                volume_name="DemoDisk",
                directories=1,
                files=1,
                total_file_size=4,
            ),
            files=[],
            directories=[],
            bitmap=None,
            block_usage=None,
        )

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    with pytest.raises(DiskAnalysisError, match="DOS analysis is missing root block"):
        create_disk_project(adf_path, project_root=project_root)

    assert not (project_root / "targets" / "amiga_disk_demo").exists()


def test_create_disk_project_cleans_up_partial_disk_dir_on_failure(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(b"demo")

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        raise RuntimeError("boom")

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)

    with pytest.raises(RuntimeError, match="boom"):
        create_disk_project(adf_path, project_root=project_root)

    assert not (project_root / "targets" / "amiga_disk_demo").exists()


def test_create_disk_project_cleans_up_created_targets_on_import_failure(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    (project_root / "targets").mkdir()
    (project_root / "bin").mkdir()
    adf_path = project_root / "bin" / "demo.adf"
    adf_path.write_bytes(bytes(range(256)) * 4)

    def fake_analyze_adf(
        adf_file: str | Path,
        *,
        extract_dir: str | Path | None = None,
        include_tracks: bool = False,
    ) -> AdfAnalysis:
        assert include_tracks is True
        assert extract_dir is None
        return AdfAnalysis(
            disk_info=DiskInfo(
                path=Path(adf_file).name,
                size=901120,
                variant="DD",
                total_sectors=1760,
                sectors_per_track=11,
                is_dos=True,
            ),
            boot_block=BootBlockInfo(
                magic_ascii="DOS",
                is_dos=True,
                flags_byte=1,
                fs_type="FFS",
                fs_description="DOS\\1 - Fast File System",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=880,
                bootcode_size=1012,
                bootcode_has_code=True,
                bootcode_entropy=1.0,
                import_target=_bootblock_import_target(),
            ),
            root_block=RootBlockInfo(
                block_num=880,
                hash_table=[],
                checksum_valid=True,
                bm_flag=0,
                bm_pages=[],
                volume_name="DemoDisk",
                root_date="1978-01-01 00:00:00",
                volume_date="1978-01-01 00:00:00",
                creation_date="1978-01-01 00:00:00",
            ),
            filesystem=FilesystemInfo(
                type="FFS",
                volume_name="DemoDisk",
                directories=1,
                files=1,
                total_file_size=4,
            ),
            files=[
                DiskFileEntry(
                    block_num=10,
                    name="Run",
                    full_path="s/Run",
                    size=4,
                    protection="----rwed",
                    comment=None,
                    date="1978-01-01 00:00:00",
                    hash_chain=0,
                    parent=0,
                    extension_blocks=[],
                    data_blocks=[11],
                    data_block_count=1,
                    checksum_valid=True,
                    content=FileContentInfo(
                        kind="amiga_hunk_executable",
                        size=4,
                        sha256="deadbeef",
                        is_executable=True,
                        hunk_count=1,
                        target_type="program",
                        import_target=_program_import_target(),
                    ),
                )
            ],
            directories=[],
            bitmap=BitmapInfo(
                checksum_valid=True,
                free_blocks=1,
                allocated_blocks=10,
                total_blocks=11,
                percent_used=90.9,
            ),
            block_usage=BlockUsageInfo(summary={"boot": 2}, orphan_blocks=[]),
        )

    original_write_source_descriptor = create_disk_project.__globals__["write_source_descriptor"]
    call_count = 0

    def fail_on_second_source_write(target_dir: Path, payload: dict[str, object]) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("boom")
        original_write_source_descriptor(target_dir, payload)

    monkeypatch.setattr("amiga_reversing.amiga_disk.project.analyze_adf", fake_analyze_adf)
    monkeypatch.setattr("amiga_reversing.amiga_disk.project.write_source_descriptor", fail_on_second_source_write)

    with pytest.raises(RuntimeError, match="boom"):
        create_disk_project(adf_path, project_root=project_root)

    assert not (project_root / "targets" / "amiga_disk_demo").exists()
    assert not (project_root / "targets" / "amiga_disk_demo" / "targets" / "amiga_raw_bootblock").exists()


def test_analyze_adf_treats_invalid_dos_root_as_non_dos(tmp_path: Path) -> None:
    adf_path = tmp_path / "custom_boot.adf"
    image = bytearray(901120)
    image[0:3] = b"DOS"
    image[3] = 1
    image[8:12] = (880).to_bytes(4, byteorder="big")
    image[12:62] = bytes.fromhex(
        "48E7FFFE"
        "337C0002001C"
        "237C000400000028"
        "237C000054000024"
        "237C00000400002C"
        "4EAEFE38"
        "4EF900040000"
        "4CDF7FFF"
        "4E75"
    )
    stage1 = bytes.fromhex(
        "4DF900DFF000"
        "43FA001E"
        "4251"
        "3D7C40000024"
        "41F900002000"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C4489007E"
        "3D7C9B060024"
        "3D7C9B060024"
        "4A51"
        "67FC"
        "4251"
        "45F900002000"
        "700A"
        "0C5A4489"
        "66FA"
        "4BF900003000"
        "7204"
        "D28D"
        "2241"
        "7003"
        "7401"
        "22C2"
        "51C8FFFC"
        "4EF900003000"
    )
    image[0x400:0x400 + len(stage1)] = stage1
    adf_path.write_bytes(bytes(image))

    result = analyze_adf(adf_path, include_tracks=True)

    assert result.non_dos is not None
    assert result.non_dos.dos_magic_without_filesystem is True
    assert result.non_dos.filesystem_parse_error is not None
    assert "root" in result.non_dos.filesystem_parse_error
    assert result.track_analysis is not None
    assert result.track_analysis.track_size_bytes == 5632
    assert result.track_analysis.tracks[0].byte_offset == 0
    assert result.track_analysis.tracks[0].byte_length == 5632
    assert result.track_analysis.raw_sources[0].track == 0
    assert result.track_analysis.raw_sources[0].byte_offset == 0
    assert result.track_analysis.raw_sources[0].byte_length == 5632
    assert result.trackloader_analysis is not None
    assert result.trackloader_analysis.nonempty_track_spans[0].start_track == 0
    assert result.trackloader_analysis.nonempty_track_spans[0].end_track == 0
    assert result.trackloader_analysis.nonempty_head0_tracks == 1
    assert result.trackloader_analysis.nonempty_head1_tracks == 0
    assert result.bootloader_analysis is not None
    stages = {stage.name: stage for stage in result.bootloader_analysis.stages}
    assert stages["stage_1"].disk_reads[0].source_kind is BootloaderTransferSourceKind.LOGICAL_DISK_OFFSET
    assert stages["stage_1"].disk_reads[0].disk_offset == 1024


def test_analyze_adf_dos_path_emits_trackloader_and_bootloader_analysis(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    adf_path = tmp_path / "dos.adf"
    adf_path.write_bytes(b"\x00" * 901120)
    boot = BootBlockInfo(
        magic_ascii="DOS",
        is_dos=True,
        flags_byte=1,
        fs_type="FFS",
        fs_description="DOS\\1 - Fast File System",
        checksum="0x00000000",
        checksum_valid=True,
        rootblock_ptr=880,
        bootcode_size=1012,
        bootcode_has_code=True,
        bootcode_entropy=1.0,
    )
    filesystem = SimpleNamespace(
        boot=SimpleNamespace(flags_byte=1),
        root=RootBlockInfo(
            block_num=880,
            hash_table=[],
            checksum_valid=True,
            bm_flag=0,
            bm_pages=[],
            volume_name="DemoDisk",
            root_date="1978-01-01 00:00:00",
            volume_date="1978-01-01 00:00:00",
            creation_date="1978-01-01 00:00:00",
        ),
        directories=[],
        files=[],
        bitmap=BitmapInfo(
            checksum_valid=True,
            free_blocks=1,
            allocated_blocks=10,
            total_blocks=11,
            percent_used=90.9,
        ),
        block_usage=BlockUsageInfo(summary={"boot": 2}, orphan_blocks=[]),
    )
    expected_trackloader = TrackloaderAnalysis(
        boot_ascii_strings=["DOS"],
        candidate_code_tracks=[0],
        high_entropy_tracks=[],
        nonempty_track_spans=[TrackSpan(start_track=0, end_track=0)],
        repeated_track_groups=[],
        nonempty_head0_tracks=1,
        nonempty_head1_tracks=0,
    )
    expected_track_analysis = TrackAnalysis(
        total_tracks=160,
        track_size_bytes=5632,
        non_empty_tracks=1,
        tracks=[
            TrackInfo(
                track=0,
                cylinder=0,
                head=0,
                first_block=0,
                byte_offset=0,
                byte_length=5632,
                empty=False,
                entropy=1.0,
                m68k_pattern_count=0,
                has_code=True,
                ascii_strings=[],
            )
        ],
        raw_sources=[RawTrackSource(track=0, cylinder=0, head=0, byte_offset=0, byte_length=5632)],
    )
    expected_bootloader = BootloaderAnalysis(stages=[], memory_regions=[], transfers=[])

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.adf.inspect_disk_with_c_backend",
        lambda *_args, **_kwargs: {
            "disk_info": {
                "size": 901120,
                "variant": "DD",
                "total_sectors": 1760,
                "sectors_per_track": 11,
                "is_dos": 1,
            },
            "boot_block": boot.to_dict(),
            "track_analysis": expected_track_analysis.to_dict(),
            "trackloader_analysis": expected_trackloader.to_dict(),
            "bootloader_analysis": expected_bootloader.to_dict(),
        },
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.adf._load_dos_filesystem", lambda *_args, **_kwargs: filesystem)

    result = analyze_adf(adf_path, include_tracks=True)

    assert result.track_analysis == expected_track_analysis
    assert result.trackloader_analysis == expected_trackloader
    assert result.bootloader_analysis == expected_bootloader


def test_analyze_adf_dos_path_emits_bootloader_analysis_without_tracks(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    adf_path = tmp_path / "dos.adf"
    adf_path.write_bytes(b"\x00" * 901120)
    boot = BootBlockInfo(
        magic_ascii="DOS",
        is_dos=True,
        flags_byte=1,
        fs_type="FFS",
        fs_description="DOS\\1 - Fast File System",
        checksum="0x00000000",
        checksum_valid=True,
        rootblock_ptr=880,
        bootcode_size=1012,
        bootcode_has_code=True,
        bootcode_entropy=1.0,
    )
    filesystem = SimpleNamespace(
        boot=SimpleNamespace(flags_byte=1),
        root=RootBlockInfo(
            block_num=880,
            hash_table=[],
            checksum_valid=True,
            bm_flag=0,
            bm_pages=[],
            volume_name="DemoDisk",
            root_date="1978-01-01 00:00:00",
            volume_date="1978-01-01 00:00:00",
            creation_date="1978-01-01 00:00:00",
        ),
        directories=[],
        files=[],
        bitmap=BitmapInfo(
            checksum_valid=True,
            free_blocks=1,
            allocated_blocks=10,
            total_blocks=11,
            percent_used=90.9,
        ),
        block_usage=BlockUsageInfo(summary={"boot": 2}, orphan_blocks=[]),
    )
    expected_bootloader = BootloaderAnalysis(stages=[], memory_regions=[], transfers=[])

    monkeypatch.setattr(
        "amiga_reversing.amiga_disk.adf.inspect_disk_with_c_backend",
        lambda *_args, **_kwargs: {
            "disk_info": {
                "size": 901120,
                "variant": "DD",
                "total_sectors": 1760,
                "sectors_per_track": 11,
                "is_dos": 1,
            },
            "boot_block": boot.to_dict(),
            "bootloader_analysis": expected_bootloader.to_dict(),
        },
    )
    monkeypatch.setattr("amiga_reversing.amiga_disk.adf._load_dos_filesystem", lambda *_args, **_kwargs: filesystem)

    result = analyze_adf(adf_path, include_tracks=False)

    assert result.track_analysis is None
    assert result.trackloader_analysis is None
    assert result.bootloader_analysis == expected_bootloader


def test_print_summary_requires_bootloader_analysis() -> None:
    result = AdfAnalysis(
        disk_info=DiskInfo(
            path="demo.adf",
            size=901120,
            variant="DD",
            total_sectors=1760,
            sectors_per_track=11,
            is_dos=True,
        ),
        boot_block=BootBlockInfo(
            magic_ascii="DOS",
            is_dos=True,
            flags_byte=1,
            fs_type="FFS",
            fs_description="DOS\\1 - Fast File System",
            checksum="0x00000000",
            checksum_valid=True,
            rootblock_ptr=880,
            bootcode_size=1012,
            bootcode_has_code=True,
            bootcode_entropy=1.0,
            import_target=_bootblock_import_target(),
        ),
    )

    with pytest.raises(DiskAnalysisError, match="missing bootloader_analysis"):
        print_summary(result)


def test_print_summary_requires_trackloader_analysis_when_tracks_exist() -> None:
    result = AdfAnalysis(
        disk_info=DiskInfo(
            path="demo.adf",
            size=901120,
            variant="DD",
            total_sectors=1760,
            sectors_per_track=11,
            is_dos=True,
        ),
        boot_block=BootBlockInfo(
            magic_ascii="DOS",
            is_dos=True,
            flags_byte=1,
            fs_type="FFS",
            fs_description="DOS\\1 - Fast File System",
            checksum="0x00000000",
            checksum_valid=True,
            rootblock_ptr=880,
            bootcode_size=1012,
            bootcode_has_code=True,
            bootcode_entropy=1.0,
            import_target=_bootblock_import_target(),
        ),
        track_analysis=TrackAnalysis(
            total_tracks=160,
            track_size_bytes=5632,
            non_empty_tracks=1,
            tracks=[
                TrackInfo(
                    track=0,
                    cylinder=0,
                    head=0,
                    first_block=0,
                    byte_offset=0,
                    byte_length=5632,
                    empty=False,
                    entropy=1.0,
                    m68k_pattern_count=0,
                    has_code=False,
                    ascii_strings=[],
                )
            ],
            raw_sources=[
                RawTrackSource(
                    track=0,
                    cylinder=0,
                    head=0,
                    byte_offset=0,
                    byte_length=5632,
                )
            ],
        ),
        bootloader_analysis=BootloaderAnalysis(stages=[], memory_regions=[], transfers=[]),
    )

    with pytest.raises(DiskAnalysisError, match="missing trackloader_analysis"):
        print_summary(result)

