from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from _pytest.monkeypatch import MonkeyPatch

from amiga_disk.adf import (
    DiskAnalysisError,
    _classify_file_content,
    _target_metadata_for_content,
    analyze_adf,
    create_disk_project,
    derive_disk_id,
    import_adf,
    print_summary,
)
from amiga_disk.kb import load_disk_kb
from amiga_disk.models import (
    AdfAnalysis,
    BitmapInfo,
    BlockUsageInfo,
    BootBlockInfo,
    BootloaderAnalysis,
    BootloaderDecodeRegion,
    BootloaderDerivedRegion,
    BootloaderDiskRead,
    BootloaderMemoryCopy,
    BootloaderStage,
    DiskFileEntry,
    DiskInfo,
    FileContentInfo,
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
from disasm.target_metadata import target_structure_spec
from m68k.hunk_parser import Hunk, HunkFile, HunkType, MemType
from m68k_kb import runtime_os


def test_analyze_disk_help_loads_cleanly() -> None:
    script = Path(__file__).resolve().parent.parent / "scripts" / "analyze_disk.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Analyze Amiga ADF disk images" in result.stdout


def test_import_adf_help_loads_cleanly() -> None:
    script = Path(__file__).resolve().parent.parent / "scripts" / "import_adf.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Import an ADF into bin/imported and targets/" in result.stdout


def test_load_disk_kb_exposes_required_structured_values() -> None:
    kb = load_disk_kb()

    assert kb.bytes_per_sector == 512
    assert kb.amiga_epoch.isoformat() == "1978-01-01T00:00:00"
    assert kb.hunk_header_magic == b"\x00\x00\x03\xf3"
    assert b"FORM" in kb.iff_group_ids
    assert kb.block_types["T_HEADER"] == 2
    assert kb.ffs_flag_mask == 1
    assert kb.boot_block.rootblock_offset == 8
    assert kb.root_block.hash_table_offset == 0x18
    assert kb.file_header.data_blocks_offset == 0x18
    assert tuple(bit.char for bit in kb.protection_bits) == tuple("hsparwed")
    assert kb.non_dos_analysis.code_track_min_pattern_hits == 4
    assert kb.non_dos_analysis.high_entropy_threshold == 7.8
    assert tuple(signature.name for signature in kb.non_dos_analysis.m68k_code_word_signatures) == (
        "RTS",
        "RTE",
        "NOP",
        "STOP",
        "JMP_abs",
        "JSR_abs",
    )
    assert kb.boot_loader.entry_offset == 0x0C
    assert kb.boot_loader.load_address == 0x70000
    assert kb.boot_entry.entry_point_offset == 0x0C
    assert len(kb.boot_entry.registers) == 2
    a6_seed = next(seed for seed in kb.boot_entry.registers if seed.register == "A6")
    a1_seed = next(seed for seed in kb.boot_entry.registers if seed.register == "A1")
    assert a6_seed.kind == "library_base"
    assert a6_seed.library_name == "exec.library"
    assert a6_seed.struct_name == "LIB"
    assert a6_seed.context_name is None
    assert a6_seed.note == "ExecBase"
    assert a1_seed.kind == "struct_ptr"
    assert a1_seed.struct_name == "IO"
    assert a1_seed.context_name == "trackdisk.device"
    assert a1_seed.note == "IOStdReq (open trackdisk.device)"
    assert kb.boot_loader.dsklen_length_mask == 0x3FFF
    assert kb.boot_loader.dsklen_length_unit_bytes == 2
    assert kb.boot_loader.cia_port_b_symbol == "ciaprb"
    assert kb.boot_loader.initial_cylinder == 0
    assert kb.boot_loader.initial_head == 0
    assert kb.boot_loader.drive_select_masks[0] == 0x08
    assert kb.boot_loader.side_bit_mask == 0x04
    assert kb.boot_loader.direction_bit_mask == 0x02
    assert kb.boot_loader.step_bit_mask == 0x01
    assert kb.boot_loader.trace_watch_input_prefix_bytes_when_output_unknown == 64
    assert kb.boot_loader.max_candidate_replay_stage_bytes == 1024
    assert kb.boot_loader.max_candidate_replay_spans == 4
    assert kb.boot_loader.hardware_access_group_gap_bytes == 16
    assert kb.boot_loader.decode_output_backscan_instructions == 16
    assert kb.boot_loader.decode_output_add_base_backscan_instructions == 4
    assert kb.boot_loader.wait_loop_search_bytes == 24
    assert kb.boot_loader.buffer_scan_search_bytes == 40
    assert kb.boot_loader.iostdreq_offsets["io_Command"] == 28
    assert kb.boot_loader.trackdisk_commands[2] == "CMD_READ"
    assert kb.boot_loader.exec_vectors_by_lvo[-456] == "DoIO"
    assert kb.boot_loader.tracked_hardware_registers[0xDFF07E] == "dsksync"
    assert kb.boot_loader.tracked_hardware_registers[0xBFD100] == "ciaprb"


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
                    full_path="c/Run",
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

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)

    manifest = import_adf(adf_path, project_root=project_root)

    assert manifest.disk_id == "demo"
    manifest_path = project_root / "targets" / "amiga_disk_demo" / "manifest.json"
    assert manifest_path.exists()
    assert manifest.bootblock_target_name == "amiga_disk_demo__amiga_raw_bootblock"
    assert manifest.bootblock_target_path == "targets/amiga_disk_demo/targets/amiga_raw_bootblock"
    bootblock_dir = project_root / manifest.bootblock_target_path
    assert (bootblock_dir / "entities.jsonl").exists()
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

    target_name = manifest.imported_targets[0].target_name
    assert target_name == "amiga_disk_demo__amiga_hunk_c__run_dcce9fe5"
    assert manifest.imported_targets[0].target_path == "targets/amiga_disk_demo/targets/amiga_hunk_c__run_dcce9fe5"
    target_dir = project_root / manifest.imported_targets[0].target_path
    assert (target_dir / "entities.jsonl").exists()
    source_disk = json.loads((target_dir / "source_binary.json").read_text(encoding="utf-8"))
    assert source_disk["kind"] == "disk_entry"
    assert source_disk["disk_id"] == "demo"
    assert source_disk["entry_path"] == "c/Run"
    assert source_disk["disk_path"] == adf_path.as_posix()
    assert manifest.imported_targets[0].target_type == "program"
    target_metadata = json.loads((target_dir / "target_metadata.json").read_text(encoding="utf-8"))
    assert target_metadata["target_type"] == "program"


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
                                command_name="CMD_READ",
                                disk_offset=0x200,
                                byte_length=4,
                                destination_addr=0x40000,
                                source_kind="logical_disk_offset",
                            )
                        ],
                        memory_copies=[],
                        read_setups=[],
                        decode_outputs=[],
                        decode_regions=[],
                        derived_regions=[],
                        handoffs=[],
                        handoff_target=0x40000,
                    ),
                ],
                memory_regions=[],
                transfers=[],
            ),
        )

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)

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


def test_import_adf_does_not_create_raw_target_for_bootloader_copied_stage(
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
                                command_name="CMD_READ",
                                disk_offset=0x200,
                                byte_length=len(stage1_bytes),
                                destination_addr=0x40000,
                                source_kind="logical_disk_offset",
                            )
                        ],
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

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)

    manifest = import_adf(adf_path, project_root=project_root)

    assert all(target.entry_path != "bootloader/stage_2" for target in manifest.imported_targets)
    assert [target.entry_path for target in manifest.imported_targets if target.target_type == "bootloader_stage"] == [
        "bootloader/stage_1"
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
                                command_name="CMD_READ",
                                disk_offset=0x200,
                                byte_length=len(stage1_bytes),
                                destination_addr=0x40000,
                                source_kind="logical_disk_offset",
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

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)

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

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)

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
                                input_source_kind="custom_track_dma_buffer",
                                input_required_source_kind="raw_custom_track_bytes",
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

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)

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


def test_classify_file_content_classifies_library_targets_from_resident_structure(
    monkeypatch: MonkeyPatch,
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

    hunk_file = HunkFile()
    hunk_file.file_type = int(HunkType.HUNK_HEADER)
    hunk_file.hunks = [
        Hunk(
            index=0,
            hunk_type=int(HunkType.HUNK_CODE),
            mem_type=int(MemType.ANY),
            alloc_size=len(code),
            data=bytes(code),
        )
    ]
    monkeypatch.setattr("amiga_disk.adf.parse", lambda _data: hunk_file)
    kb = load_disk_kb()

    content = _classify_file_content(kb, b"\x00\x00\x03\xf3demo")

    assert content.target_type == "library"
    assert content.resident is not None
    assert content.resident.name == "icon.library"
    assert content.library is not None
    assert content.library.library_name == "icon.library"
    assert content.library.version == 37
    assert content.library.public_function_count == 12
    assert content.library.total_lvo_count == 19
    metadata = _target_metadata_for_content(content)
    assert metadata.resident is not None
    assert metadata.resident.offset == 0
    assert metadata.resident.matchword == runtime_os.CONSTANTS["RTC_MATCHWORD"].value


def test_classify_file_content_extracts_autoinit_library_entrypoints(
    monkeypatch: MonkeyPatch,
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

    hunk_file = HunkFile()
    hunk_file.file_type = int(HunkType.HUNK_HEADER)
    hunk_file.hunks = [
        Hunk(
            index=0,
            hunk_type=int(HunkType.HUNK_CODE),
            mem_type=int(MemType.ANY),
            alloc_size=len(code),
            data=bytes(code),
        )
    ]
    monkeypatch.setattr("amiga_disk.adf.parse", lambda _data: hunk_file)
    kb = load_disk_kb()

    content = _classify_file_content(kb, b"\x00\x00\x03\xf3demo")

    assert content.target_type == "library"
    assert content.resident is not None
    assert content.resident.autoinit is not None
    assert content.resident.autoinit.payload_offset == 0x40
    assert content.resident.autoinit.vectors_offset == 0x50
    assert content.resident.autoinit.vector_offsets == (0xA0, 0xA8, 0xB0, 0xB8, 0xC0)
    assert content.resident.autoinit.init_func_offset == 0x90
    metadata = _target_metadata_for_content(content)
    structure = target_structure_spec(metadata)
    assert structure is not None
    assert structure.analysis_start_offset == 0x90
    assert [seed.entry_offset for seed in metadata.entry_register_seeds] == [0x90, 0xA0, 0xA8, 0xB0, 0xB8, 0xC0]
    assert metadata.entry_register_seeds[0].library_name == "exec.library"
    assert all(seed.register == "A6" for seed in metadata.entry_register_seeds)
    assert all(seed.library_name == "icon.library" for seed in metadata.entry_register_seeds[1:])
    assert [entry.label for entry in structure.entrypoints] == [
        "library_init",
        "lib_open",
        "lib_close",
        "lib_expunge",
        "lib_extfunc",
        "icon_private_1",
    ]
    assert [entry.offset for entry in structure.entrypoints] == [
        0x90,
        0xA0,
        0xA8,
        0xB0,
        0xB8,
        0xC0,
    ]


def test_classify_file_content_defaults_to_program_without_resident(
    monkeypatch: MonkeyPatch,
) -> None:
    hunk_file = HunkFile()
    hunk_file.file_type = int(HunkType.HUNK_HEADER)
    hunk_file.hunks = [
        Hunk(
            index=0,
            hunk_type=int(HunkType.HUNK_CODE),
            mem_type=int(MemType.ANY),
            alloc_size=4,
            data=b"\x4e\x75\x4e\x75",
        )
    ]

    monkeypatch.setattr("amiga_disk.adf.parse", lambda _data: hunk_file)
    kb = load_disk_kb()

    content = _classify_file_content(kb, b"\x00\x00\x03\xf3demo")

    assert content.target_type == "program"
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
            ),
            non_dos=NonDosInfo(
                description="Custom format disk (non-AmigaDOS)",
                bootcode_present=True,
                dos_magic_without_filesystem=True,
                filesystem_parse_error="Unexpected root hash table size",
            ),
        )

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)

    manifest = create_disk_project(adf_path, project_root=project_root)

    assert manifest.disk_id == "demo"
    assert manifest.analysis.disk_info.is_dos is True
    assert manifest.analysis.filesystem is None
    assert manifest.analysis.non_dos is not None
    assert manifest.imported_targets == []
    assert (project_root / "targets" / "amiga_disk_demo" / "manifest.json").exists()


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

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)

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

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)

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
                    full_path="c/Run",
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
        if call_count == 2:
            raise RuntimeError("boom")
        original_write_source_descriptor(target_dir, payload)

    monkeypatch.setattr("amiga_disk.adf.analyze_adf", fake_analyze_adf)
    monkeypatch.setattr("amiga_disk.adf.write_source_descriptor", fail_on_second_source_write)

    with pytest.raises(RuntimeError, match="boom"):
        create_disk_project(adf_path, project_root=project_root)

    assert not (project_root / "targets" / "amiga_disk_demo").exists()
    assert not (project_root / "targets" / "amiga_disk_demo" / "targets" / "amiga_raw_bootblock").exists()
    assert not (project_root / "targets" / "amiga_disk_demo" / "targets" / "amiga_hunk_c__run_dcce9fe5").exists()


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
    assert "Unexpected root hash table size" in result.non_dos.filesystem_parse_error
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
    assert len(result.bootloader_analysis.stages) == 2
    assert result.bootloader_analysis.stages[0].loads[0].destination_addr == 0x40000
    assert result.bootloader_analysis.stages[1].decode_regions[0].input_source_candidates[0].track == 0
    symbols = [access.symbol for access in result.bootloader_analysis.stages[1].hardware_accesses]
    assert "dskpt" in symbols
    assert "dsksync" in symbols
    assert symbols.count("adkcon") == 2
    assert symbols.count("dsklen") >= 2


def test_analyze_adf_dos_path_emits_trackloader_and_bootloader_analysis(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    adf_path = tmp_path / "dos.adf"
    adf_path.write_bytes(b"\x00" * 901120)
    disk_kb = load_disk_kb()
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
    expected_bootloader = BootloaderAnalysis(stages=[], memory_regions=[], transfers=[])

    monkeypatch.setattr("amiga_disk.adf._parse_boot_block", lambda _kb, _data: boot)
    monkeypatch.setattr("amiga_disk.adf._load_dos_filesystem", lambda *_args, **_kwargs: filesystem)
    monkeypatch.setattr(
        "amiga_disk.adf._analyze_track",
        lambda _kb, _data, track_num, _sectors_per_track: TrackInfo(
            track=track_num,
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
        ),
    )
    monkeypatch.setattr(
        "amiga_disk.adf._build_trackloader_analysis",
        lambda _kb, _data, _tracks, _track_size_bytes: expected_trackloader,
    )

    def fake_analyze_bootloader(
        boot_code: bytes,
        *,
        disk_bytes: bytes | None = None,
        raw_track_sources: list[RawTrackSource] | None = None,
        kb: object | None = None,
        kb_root: Path = Path("."),
        entry_addr: int | None = None,
    ) -> BootloaderAnalysis:
        assert len(boot_code) == disk_kb.boot_block.boot_block_bytes - disk_kb.boot_block.bootcode_offset
        assert disk_bytes == adf_path.read_bytes()
        assert raw_track_sources is not None
        assert len(raw_track_sources) == 160
        assert raw_track_sources[0].track == 0
        return expected_bootloader

    monkeypatch.setattr("amiga_disk.adf.analyze_bootloader", fake_analyze_bootloader)

    result = analyze_adf(adf_path, include_tracks=True)

    assert result.track_analysis is not None
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

    monkeypatch.setattr("amiga_disk.adf._parse_boot_block", lambda _kb, _data: boot)
    monkeypatch.setattr("amiga_disk.adf._load_dos_filesystem", lambda *_args, **_kwargs: filesystem)

    def fake_analyze_bootloader(
        boot_code: bytes,
        *,
        disk_bytes: bytes | None = None,
        raw_track_sources: list[RawTrackSource] | None = None,
        kb: object | None = None,
        kb_root: Path = Path("."),
        entry_addr: int | None = None,
    ) -> BootloaderAnalysis:
        assert disk_bytes == adf_path.read_bytes()
        assert raw_track_sources == []
        return expected_bootloader

    monkeypatch.setattr("amiga_disk.adf.analyze_bootloader", fake_analyze_bootloader)

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
