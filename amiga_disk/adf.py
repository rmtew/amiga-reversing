from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import shutil
import struct
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from amiga_disk.bootloader import analyze_bootloader
from amiga_disk.kb import PROJECT_ROOT, DiskKb, load_disk_kb
from amiga_disk.models import (
    AdfAnalysis,
    BitmapInfo,
    BlockUsageInfo,
    BootBlockInfo,
    DiskDirectoryEntry,
    DiskFileEntry,
    DiskInfo,
    DiskManifest,
    FileContentInfo,
    FilesystemInfo,
    ImportedTarget,
    LibraryInfo,
    NonDosInfo,
    RawTrackSource,
    ResidentInfo,
    RootBlockInfo,
    TrackAnalysis,
    TrackInfo,
    TrackloaderAnalysis,
    TrackSpan,
)
from disasm.amiga_metadata import ResidentAutoinitMetadata
from disasm.binary_source import write_source_descriptor
from disasm.project_ids import (
    bootblock_local_target_id,
    derive_disk_id_from_stem,
    disk_child_project_id,
    disk_child_target_relpath,
    disk_entry_local_target_id,
    disk_project_root,
    disk_project_targets_dir,
)
from disasm.target_metadata import (
    BootBlockTargetMetadata,
    EntryRegisterSeedMetadata,
    LibraryTargetMetadata,
    ResidentTargetMetadata,
    TargetMetadata,
    write_target_metadata,
)
from m68k.hunk_parser import HunkFile, parse
from m68k_kb import runtime_os


class DiskAnalysisError(ValueError):
    """Raised when disk analysis or import cannot proceed."""


SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True, slots=True)
class FileHeader:
    block_num: int
    name: str
    is_directory: bool
    size: int
    protection: str
    comment: str | None
    date: str
    hash_chain: int
    parent: int
    extension_blocks: list[int]
    data_blocks: list[int]
    checksum_valid: bool
    hash_table: list[int] | None = None


@dataclass(frozen=True, slots=True)
class BlockUsageState:
    summary: dict[str, int]
    orphan_blocks: list[int]
    usage: list[str]
    owner: list[str]


@dataclass(frozen=True, slots=True)
class DosFilesystem:
    boot: BootBlockInfo
    root: RootBlockInfo
    directories: list[DiskDirectoryEntry]
    files: list[DiskFileEntry]
    bitmap: BitmapInfo
    block_usage: BlockUsageInfo


def _u32(data: bytes, offset: int) -> int:
    return int(struct.unpack_from(">I", data, offset)[0])


def _s32(data: bytes, offset: int) -> int:
    return int(struct.unpack_from(">i", data, offset)[0])


def _u16(data: bytes, offset: int) -> int:
    return int(struct.unpack_from(">H", data, offset)[0])


def _read_block(data: bytes, block_num: int, block_size: int) -> bytes:
    start = block_num * block_size
    end = start + block_size
    if end > len(data):
        raise DiskAnalysisError(f"Block {block_num} lies outside disk image")
    return data[start:end]


def _read_bcpl_string(data: bytes, offset: int, max_len: int) -> str:
    if offset >= len(data):
        raise DiskAnalysisError("BCPL string offset lies outside block")
    length = min(data[offset], max_len)
    end = offset + 1 + length
    return data[offset + 1:end].decode("latin-1", errors="replace")


def _compute_boot_checksum(boot_data: bytes, block_size: int) -> int:
    longword_count = (block_size * 2) // 4
    total = 0
    for index in range(longword_count):
        if index == 1:
            continue
        total += _u32(boot_data, index * 4)
        if total > 0xFFFFFFFF:
            total = (total + 1) & 0xFFFFFFFF
    return (~total) & 0xFFFFFFFF


def _verify_block_checksum(block: bytes, block_size: int) -> bool:
    total = 0
    for index in range(block_size // 4):
        total = (total + _u32(block, index * 4)) & 0xFFFFFFFF
    return total == 0


def _amiga_date_to_iso(kb: DiskKb, days: int, mins: int, ticks: int) -> str:
    try:
        stamp = kb.amiga_epoch + dt.timedelta(
            days=days,
            minutes=mins,
            seconds=ticks // 50,
        )
    except (OverflowError, ValueError) as exc:
        raise DiskAnalysisError(f"Invalid Amiga date tuple ({days},{mins},{ticks})") from exc
    formatted = stamp.strftime("%Y-%m-%d %H:%M:%S")
    assert isinstance(formatted, str)
    return formatted


def _format_protection(kb: DiskKb, prot: int) -> str:
    chars: list[str] = []
    for bit in kb.protection_bits:
        has_flag = bool(prot & bit.mask)
        is_present = has_flag if bit.set_means_present else not has_flag
        chars.append(bit.char if is_present else "-")
    return "".join(chars)


def _shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = [0] * 256
    for value in data:
        freq[value] += 1
    total = len(data)
    entropy = 0.0
    for count in freq:
        if count == 0:
            continue
        probability = count / total
        entropy -= probability * math.log2(probability)
    return entropy


def _scan_ascii_strings(data: bytes, min_length: int = 4) -> list[dict[str, object]]:
    strings: list[dict[str, object]] = []
    current: list[str] = []
    start = 0
    for index, value in enumerate(data):
        if 0x20 <= value <= 0x7E:
            if not current:
                start = index
            current.append(chr(value))
            continue
        if len(current) >= min_length:
            strings.append({"offset": start, "text": "".join(current)})
        current = []
    if len(current) >= min_length:
        strings.append({"offset": start, "text": "".join(current)})
    return strings


def _parse_boot_block(kb: DiskKb, data: bytes) -> BootBlockInfo:
    layout = kb.boot_block
    boot = data[:layout.boot_block_bytes]
    magic = boot[layout.magic_offset:layout.magic_offset + 3]
    flags = boot[layout.flags_offset]
    checksum = _u32(boot, layout.checksum_offset)
    rootblock_ptr = _u32(boot, layout.rootblock_offset)
    expected_checksum = _compute_boot_checksum(boot, kb.bytes_per_sector)

    if magic == b"DOS":
        if flags not in kb.dos_types:
            raise DiskAnalysisError(f"Unknown DOS flags byte 0x{flags:02X}")
        fs_type, fs_description = kb.dos_types[flags]
    else:
        fs_type, fs_description = "", ""

    return BootBlockInfo(
        magic_ascii=magic.decode("latin-1", errors="replace"),
        is_dos=magic == b"DOS",
        flags_byte=flags,
        fs_type=fs_type,
        fs_description=fs_description,
        checksum=f"0x{checksum:08X}",
        checksum_valid=checksum == expected_checksum,
        rootblock_ptr=rootblock_ptr,
        bootcode_size=len(boot) - layout.bootcode_offset,
        bootcode_has_code=any(byte != 0 for byte in boot[layout.bootcode_offset:]),
        bootcode_entropy=round(_shannon_entropy(boot[layout.bootcode_offset:]), 2),
    )


def _parse_root_block(kb: DiskKb, data: bytes, block_num: int) -> RootBlockInfo:
    layout = kb.root_block
    block = _read_block(data, block_num, kb.bytes_per_sector)
    root_type = kb.block_types["T_HEADER"]
    root_sec_type = kb.block_types["ST_ROOT"]
    hash_table_size = _u32(block, layout.hash_table_size_offset)
    if hash_table_size != kb.root_hash_table_size:
        raise DiskAnalysisError(
            f"Unexpected root hash table size {hash_table_size}; expected {kb.root_hash_table_size}"
        )
    hash_table = [_u32(block, layout.hash_table_offset + index * 4) for index in range(hash_table_size)]
    volume_name = _read_bcpl_string(block, layout.volume_name_offset, layout.volume_name_max_length)
    root_days = _u32(block, layout.root_date_offset)
    root_mins = _u32(block, layout.root_date_offset + 4)
    root_ticks = _u32(block, layout.root_date_offset + 8)
    volume_days = _u32(block, layout.volume_date_offset)
    volume_mins = _u32(block, layout.volume_date_offset + 4)
    volume_ticks = _u32(block, layout.volume_date_offset + 8)
    create_days = _u32(block, layout.creation_date_offset)
    create_mins = _u32(block, layout.creation_date_offset + 4)
    create_ticks = _u32(block, layout.creation_date_offset + 8)

    type_field = _u32(block, layout.type_offset)
    sec_type = _s32(block, layout.sec_type_offset)
    if type_field != root_type or sec_type != root_sec_type:
        raise DiskAnalysisError(
            f"Invalid root block type pair ({type_field}, {sec_type}) at block {block_num}"
        )

    return RootBlockInfo(
        block_num=block_num,
        hash_table=hash_table,
        checksum_valid=_verify_block_checksum(block, kb.bytes_per_sector),
        bm_flag=_s32(block, layout.bitmap_valid_flag_offset),
        bm_pages=[
            _u32(block, layout.bitmap_pages_offset + index * 4)
            for index in range(layout.bitmap_pages_count)
            if _u32(block, layout.bitmap_pages_offset + index * 4) != 0
        ],
        volume_name=volume_name,
        root_date=_amiga_date_to_iso(kb, root_days, root_mins, root_ticks),
        volume_date=_amiga_date_to_iso(kb, volume_days, volume_mins, volume_ticks),
        creation_date=_amiga_date_to_iso(kb, create_days, create_mins, create_ticks),
    )


def _parse_file_header(kb: DiskKb, data: bytes, block_num: int) -> FileHeader | None:
    layout = kb.file_header
    block = _read_block(data, block_num, kb.bytes_per_sector)
    if _u32(block, layout.type_offset) != kb.block_types["T_HEADER"]:
        return None
    sec_type = _s32(block, layout.sec_type_offset)
    is_directory = sec_type == kb.block_types["ST_USERDIR"]
    is_file = sec_type == kb.block_types["ST_FILE"]
    if not is_directory and not is_file:
        return None

    high_seq = _u32(block, layout.high_seq_offset)
    raw_ptrs = [_u32(block, layout.data_blocks_offset + index * 4) for index in range(layout.data_blocks_count)]
    start_idx = max(0, kb.root_hash_table_size - high_seq)
    data_blocks = [ptr for ptr in raw_ptrs[start_idx:] if ptr != 0]
    data_blocks.reverse()

    name = _read_bcpl_string(block, layout.name_length_offset, layout.name_max_length)
    byte_size = _u32(block, layout.byte_size_offset)
    protection = _u32(block, layout.protection_offset)
    comment = _read_bcpl_string(block, layout.comment_length_offset, layout.comment_max_length)
    days = _u32(block, layout.date_offset)
    mins = _u32(block, layout.date_offset + 4)
    ticks = _u32(block, layout.date_offset + 8)
    hash_chain = _u32(block, layout.hash_chain_offset)
    parent = _u32(block, layout.parent_offset)
    extension = _u32(block, layout.extension_offset)

    extension_blocks: list[int] = []
    if is_file:
        visited = {block_num}
        while extension != 0:
            if extension in visited:
                raise DiskAnalysisError(f"Extension loop detected at block {extension}")
            visited.add(extension)
            ext_layout = kb.file_extension
            ext_block = _read_block(data, extension, kb.bytes_per_sector)
            if _u32(ext_block, ext_layout.type_offset) != kb.block_types["T_LIST"]:
                raise DiskAnalysisError(f"Invalid extension block type at block {extension}")
            extension_blocks.append(extension)
            ext_high_seq = _u32(ext_block, ext_layout.high_seq_offset)
            ext_ptrs = [
                _u32(ext_block, ext_layout.data_blocks_offset + index * 4)
                for index in range(ext_layout.data_blocks_count)
            ]
            ext_start = max(0, kb.root_hash_table_size - ext_high_seq)
            ext_data_blocks = [ptr for ptr in ext_ptrs[ext_start:] if ptr != 0]
            ext_data_blocks.reverse()
            data_blocks.extend(ext_data_blocks)
            extension = _u32(ext_block, ext_layout.extension_offset)

    return FileHeader(
        block_num=block_num,
        name=name,
        is_directory=is_directory,
        size=byte_size,
        protection=_format_protection(kb, protection),
        comment=comment or None,
        date=_amiga_date_to_iso(kb, days, mins, ticks),
        hash_chain=hash_chain,
        parent=parent,
        extension_blocks=extension_blocks,
        data_blocks=data_blocks if is_file else [],
        checksum_valid=_verify_block_checksum(block, kb.bytes_per_sector),
        hash_table=raw_ptrs if is_directory else None,
    )


def _walk_directory(
    kb: DiskKb,
    data: bytes,
    hash_table: list[int],
    parent_path: str,
    total_sectors: int,
) -> tuple[list[DiskDirectoryEntry], list[DiskFileEntry]]:
    directories: list[DiskDirectoryEntry] = []
    files: list[DiskFileEntry] = []
    visited: set[int] = set()
    for slot_ptr in hash_table:
        block_num = slot_ptr
        while block_num != 0:
            if block_num in visited:
                raise DiskAnalysisError(f"Directory cycle detected at block {block_num}")
            if block_num >= total_sectors:
                raise DiskAnalysisError(f"Directory entry block {block_num} outside disk")
            visited.add(block_num)
            entry = _parse_file_header(kb, data, block_num)
            if entry is None:
                raise DiskAnalysisError(f"Invalid file header at block {block_num}")
            full_path = f"{parent_path}/{entry.name}" if parent_path else entry.name
            if entry.is_directory:
                directories.append(
                    DiskDirectoryEntry(
                        block_num=entry.block_num,
                        name=entry.name,
                        full_path=full_path,
                        protection=entry.protection,
                        comment=entry.comment,
                        date=entry.date,
                        hash_chain=entry.hash_chain,
                        parent=entry.parent,
                        checksum_valid=entry.checksum_valid,
                    )
                )
                if entry.hash_table is None:
                    raise DiskAnalysisError(f"Directory {full_path} is missing hash table data")
                subdirs, subfiles = _walk_directory(
                    kb,
                    data,
                    entry.hash_table,
                    full_path,
                    total_sectors,
                )
                directories.extend(subdirs)
                files.extend(subfiles)
            else:
                files.append(
                    DiskFileEntry(
                        block_num=entry.block_num,
                        name=entry.name,
                        full_path=full_path,
                        size=entry.size,
                        protection=entry.protection,
                        comment=entry.comment,
                        date=entry.date,
                        hash_chain=entry.hash_chain,
                        parent=entry.parent,
                        extension_blocks=entry.extension_blocks,
                        data_blocks=entry.data_blocks,
                        data_block_count=len(entry.data_blocks),
                        checksum_valid=entry.checksum_valid,
                    )
                )
            block_num = entry.hash_chain
    return directories, files


def _parse_bitmap(kb: DiskKb, data: bytes, bm_pages: list[int], total_sectors: int) -> tuple[BitmapInfo, list[bool | None]]:
    block_size = kb.bytes_per_sector
    block_map: list[bool | None] = [None] * total_sectors
    block_map[0] = False
    block_map[1] = False
    checksum_valid = True
    for bm_block_num in bm_pages:
        if bm_block_num >= total_sectors:
            raise DiskAnalysisError(f"Bitmap block {bm_block_num} outside disk")
        bm_block = _read_block(data, bm_block_num, block_size)
        if not _verify_block_checksum(bm_block, block_size):
            checksum_valid = False
        for byte_index in range(4, block_size):
            byte_value = bm_block[byte_index]
            for bit in range(8):
                block_index = 2 + (byte_index - 4) * 8 + bit
                if block_index >= total_sectors:
                    break
                block_map[block_index] = bool(byte_value & (1 << bit))
    free_count = sum(1 for item in block_map if item is True)
    allocated_count = sum(1 for item in block_map if item is False)
    return (
        BitmapInfo(
            checksum_valid=checksum_valid,
            free_blocks=free_count,
            allocated_blocks=allocated_count,
            total_blocks=total_sectors,
            percent_used=round(allocated_count / total_sectors * 100, 1),
        ),
        block_map,
    )


def _build_block_usage(
    total_sectors: int,
    root_block_num: int,
    bm_pages: list[int],
    directories: list[DiskDirectoryEntry],
    files: list[DiskFileEntry],
    bitmap_map: list[bool | None],
) -> BlockUsageState:
    usage = ["unknown"] * total_sectors
    owner = [""] * total_sectors
    usage[0] = "boot"
    usage[1] = "boot"
    usage[root_block_num] = "root"
    for bm_page in bm_pages:
        usage[bm_page] = "bitmap"
    for directory in directories:
        usage[directory.block_num] = "dir_header"
        owner[directory.block_num] = directory.full_path
    for file_entry in files:
        usage[file_entry.block_num] = "file_header"
        owner[file_entry.block_num] = file_entry.full_path
        for data_block in file_entry.data_blocks:
            usage[data_block] = "data"
            owner[data_block] = file_entry.full_path
        for extension_block in file_entry.extension_blocks:
            usage[extension_block] = "extension"
            owner[extension_block] = file_entry.full_path
    orphan_blocks: list[int] = []
    for index, bitmap_value in enumerate(bitmap_map):
        if bitmap_value is True and usage[index] == "unknown":
            usage[index] = "free"
        elif bitmap_value is False and usage[index] == "unknown":
            usage[index] = "allocated_orphan"
            orphan_blocks.append(index)
    summary: dict[str, int] = {}
    for item in usage:
        summary[item] = summary.get(item, 0) + 1
    return BlockUsageState(summary=summary, orphan_blocks=orphan_blocks, usage=usage, owner=owner)


def _analyze_track(kb: DiskKb, data: bytes, track_num: int, sectors_per_track: int) -> TrackInfo:
    block_size = kb.bytes_per_sector
    first_block = track_num * sectors_per_track
    start = first_block * block_size
    end = start + sectors_per_track * block_size
    track_data = data[start:end]
    if not track_data:
        return TrackInfo(
            track=track_num,
            cylinder=track_num // 2,
            head=track_num % 2,
            first_block=first_block,
            byte_offset=start,
            byte_length=end - start,
            empty=True,
            entropy=0.0,
            m68k_pattern_count=0,
            has_code=False,
            ascii_strings=[],
        )
    m68k_words = {
        signature.word: signature.name for signature in kb.non_dos_analysis.m68k_code_word_signatures
    }
    m68k_hits = [
        {"offset": offset, "instruction": m68k_words[word]}
        for offset in range(0, len(track_data) - 1, 2)
        if (word := _u16(track_data, offset)) in m68k_words
    ]
    return TrackInfo(
        track=track_num,
        cylinder=track_num // 2,
        head=track_num % 2,
        first_block=first_block,
        byte_offset=start,
        byte_length=end - start,
        empty=all(byte == 0 for byte in track_data),
        entropy=round(_shannon_entropy(track_data), 2),
        m68k_pattern_count=len(m68k_hits),
        has_code=len(m68k_hits) >= kb.non_dos_analysis.code_track_min_pattern_hits,
        ascii_strings=_scan_ascii_strings(track_data, kb.non_dos_analysis.track_ascii_min_length)[
            :kb.non_dos_analysis.max_track_ascii_strings
        ],
    )


def _build_trackloader_analysis(
    kb: DiskKb,
    disk_data: bytes,
    tracks: list[TrackInfo],
    track_size_bytes: int,
) -> TrackloaderAnalysis:
    heuristics = kb.non_dos_analysis
    boot_ascii_strings: list[str] = []
    for item in _scan_ascii_strings(
        disk_data[kb.boot_block.bootcode_offset:kb.boot_block.boot_block_bytes],
        heuristics.boot_ascii_min_length,
    )[:heuristics.max_boot_ascii_strings]:
        text = item["text"]
        assert isinstance(text, str)
        boot_ascii_strings.append(text)
    candidate_code_tracks = [track.track for track in tracks if track.has_code]
    high_entropy_tracks = [
        track.track for track in tracks if track.entropy >= heuristics.high_entropy_threshold
    ][:heuristics.max_high_entropy_tracks]
    nonempty_track_numbers = [track.track for track in tracks]
    nonempty_track_spans: list[TrackSpan] = []
    if nonempty_track_numbers:
        start = nonempty_track_numbers[0]
        end = start
        for track_num in nonempty_track_numbers[1:]:
            if track_num == end + 1:
                end = track_num
                continue
            nonempty_track_spans.append(TrackSpan(start_track=start, end_track=end))
            start = end = track_num
        nonempty_track_spans.append(TrackSpan(start_track=start, end_track=end))

    repeated_track_groups: list[list[int]] = []
    repeated_by_hash: dict[str, list[int]] = defaultdict(list)
    total_tracks = len(disk_data) // track_size_bytes
    for track_num in range(total_tracks):
        start = track_num * track_size_bytes
        end = start + track_size_bytes
        track_bytes = disk_data[start:end]
        if not any(track_bytes):
            continue
        repeated_by_hash[hashlib.sha1(track_bytes).hexdigest()].append(track_num)
    repeated_track_groups = [
        group
        for group in repeated_by_hash.values()
        if len(group) > 1
    ]
    repeated_track_groups.sort(key=len, reverse=True)

    nonempty_head0_tracks = sum(1 for track in tracks if track.head == 0)
    nonempty_head1_tracks = sum(1 for track in tracks if track.head == 1)
    return TrackloaderAnalysis(
        boot_ascii_strings=boot_ascii_strings,
        candidate_code_tracks=candidate_code_tracks,
        high_entropy_tracks=high_entropy_tracks,
        nonempty_track_spans=nonempty_track_spans,
        repeated_track_groups=repeated_track_groups[:heuristics.max_repeated_track_groups],
        nonempty_head0_tracks=nonempty_head0_tracks,
        nonempty_head1_tracks=nonempty_head1_tracks,
    )


def _non_dos_analysis(
    kb: DiskKb,
    data: bytes,
    boot: BootBlockInfo,
    variant_total_sectors: int,
    sectors_per_track: int,
    include_tracks: bool,
    filesystem_parse_error: str | None = None,
) -> tuple[NonDosInfo, TrackAnalysis | None, TrackloaderAnalysis | None]:
    track_analysis = None
    trackloader_analysis = None
    if include_tracks:
        total_tracks = variant_total_sectors // sectors_per_track
        tracks = [
            track
            for track in (
                _analyze_track(kb, data, track_num, sectors_per_track)
                for track_num in range(total_tracks)
            )
            if not track.empty
        ]
        track_analysis = TrackAnalysis(
            total_tracks=total_tracks,
            track_size_bytes=kb.bytes_per_sector * sectors_per_track,
            non_empty_tracks=len(tracks),
            tracks=tracks,
            raw_sources=[
                RawTrackSource(
                    track=track.track,
                    cylinder=track.cylinder,
                    head=track.head,
                    byte_offset=track.byte_offset,
                    byte_length=track.byte_length,
                )
                for track in tracks
            ],
        )
        trackloader_analysis = _build_trackloader_analysis(
            kb,
            data,
            tracks,
            kb.bytes_per_sector * sectors_per_track,
        )
    return (
        NonDosInfo(
            description="Custom format disk (non-AmigaDOS)",
            bootcode_present=boot.bootcode_has_code,
            dos_magic_without_filesystem=boot.is_dos,
            filesystem_parse_error=filesystem_parse_error,
        ),
        track_analysis,
        trackloader_analysis,
    )


def _extract_file(kb: DiskKb, data: bytes, entry: DiskFileEntry, output_dir: Path, is_ffs: bool) -> Path:
    destination = output_dir / entry.full_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(_read_file_payload(kb, data, entry, is_ffs))
    assert isinstance(destination, Path)
    return destination


def _read_file_payload(kb: DiskKb, data: bytes, entry: DiskFileEntry, is_ffs: bool) -> bytes:
    collected = bytearray()
    for block_num in entry.data_blocks:
        block = _read_block(data, block_num, kb.bytes_per_sector)
        if is_ffs:
            collected.extend(block)
        else:
            data_size = _u32(block, kb.ofs_data_block.data_size_offset)
            start = kb.ofs_data_block.data_offset
            collected.extend(block[start:start + data_size])
    return bytes(collected[:entry.size])


def _classify_file_content(kb: DiskKb, payload: bytes) -> FileContentInfo:
    result = FileContentInfo(
        kind="unknown",
        size=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
    )
    if len(payload) >= 4 and payload[:4] == kb.hunk_header_magic:
        try:
            hunk_file = parse(payload)
        except Exception as exc:
            return FileContentInfo(
                kind="amiga_hunk_executable",
                size=result.size,
                sha256=result.sha256,
                is_executable=False,
                hunk_parse_error=str(exc),
            )
        target_type, resident, library = _classify_hunk_target(hunk_file)
        return FileContentInfo(
            kind="amiga_hunk_executable",
            size=result.size,
            sha256=result.sha256,
            is_executable=hunk_file.is_executable,
            hunk_count=len(hunk_file.hunks),
            target_type=target_type,
            resident=resident,
            library=library,
        )
    if len(payload) >= 12 and payload[:4] in kb.iff_group_ids:
        total_size = 8 + _u32(payload, 4)
        if total_size <= len(payload):
            return FileContentInfo(
                kind="iff_container",
                size=result.size,
                sha256=result.sha256,
                group_id=payload[:4].decode("ascii"),
                form_id=payload[8:12].decode("ascii", errors="replace"),
            )
    return result


def _read_u16_be(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], byteorder="big", signed=False)


def _read_u32_be(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], byteorder="big", signed=False)


def _read_i8(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 1], byteorder="big", signed=True)


def _read_c_string(data: bytes, offset: int) -> str | None:
    if offset < 0 or offset >= len(data):
        return None
    end = data.find(b"\x00", offset)
    if end == -1:
        return None
    return data[offset:end].decode("latin-1", errors="replace")


def _os_const(name: str) -> int:
    value = runtime_os.CONSTANTS[name].value
    assert value is not None, f"OS constant {name} is missing a value"
    assert isinstance(value, int), f"OS constant {name} has non-integer value {value!r}"
    return value


def _resident_type_name(node_type: int) -> str:
    for name, constant in runtime_os.CONSTANTS.items():
        assert isinstance(name, str)
        if not name.startswith("NT_"):
            continue
        if constant.value == node_type:
            return name.removeprefix("NT_").lower()
    return f"type_{node_type}"


def _find_resident_info(hunk_file: HunkFile) -> ResidentInfo | None:
    code_hunks = [hunk for hunk in hunk_file.hunks if hunk.type_name == "CODE"]
    if not code_hunks:
        return None
    code = code_hunks[0].data
    matchword = _os_const("RTC_MATCHWORD")
    auto_init_flag = _os_const("RTF_AUTOINIT")
    resident_struct = runtime_os.STRUCTS["RT"]
    offsets = {field.name: field.offset for field in resident_struct.fields}
    for offset in range(0, max(0, len(code) - resident_struct.size + 1), 2):
        if _read_u16_be(code, offset + offsets["RT_MATCHWORD"]) != matchword:
            continue
        matchtag = _read_u32_be(code, offset + offsets["RT_MATCHTAG"])
        if matchtag != offset:
            continue
        init_offset = _read_u32_be(code, offset + offsets["RT_INIT"])
        name_offset = _read_u32_be(code, offset + offsets["RT_NAME"])
        id_offset = _read_u32_be(code, offset + offsets["RT_IDSTRING"])
        flags = code[offset + offsets["RT_FLAGS"]]
        version = code[offset + offsets["RT_VERSION"]]
        node_type = code[offset + offsets["RT_TYPE"]]
        priority = _read_i8(code, offset + offsets["RT_PRI"])
        return ResidentInfo(
            offset=offset,
            flags=flags,
            version=version,
            node_type=node_type,
            node_type_name=_resident_type_name(node_type),
            priority=priority,
            name=_read_c_string(code, name_offset),
            id_string=_read_c_string(code, id_offset),
            init_offset=init_offset,
            auto_init=(flags & auto_init_flag) == auto_init_flag,
        )
    return None


def _parse_resident_autoinit_info(
    hunk_file: HunkFile,
    resident: ResidentInfo,
    target_type: str,
) -> ResidentAutoinitMetadata | None:
    if not resident.auto_init:
        return None
    code_hunks = [hunk for hunk in hunk_file.hunks if hunk.type_name == "CODE"]
    if not code_hunks:
        raise DiskAnalysisError("Resident auto-init target is missing CODE hunk")
    if target_type not in runtime_os.META.resident_vector_prefixes:
        raise DiskAnalysisError(f"Missing KB resident vector metadata for target type {target_type}")
    code = code_hunks[0].data
    payload_offset = resident.init_offset
    if payload_offset < 0 or payload_offset + 16 > len(code):
        raise DiskAnalysisError(
            f"Resident auto-init payload at 0x{payload_offset:X} lies outside first CODE hunk"
        )
    payload_words = runtime_os.META.resident_autoinit_words
    if payload_words != ("base_size", "vectors", "structure_init", "init_func"):
        raise DiskAnalysisError(f"Unexpected resident autoinit word layout {payload_words!r}")
    base_size = _read_u32_be(code, payload_offset)
    vectors_offset = _read_u32_be(code, payload_offset + 4)
    init_struct_offset = _read_u32_be(code, payload_offset + 8)
    init_func_offset = _read_u32_be(code, payload_offset + 12)
    if base_size <= 0:
        raise DiskAnalysisError("Resident auto-init payload is missing library/device base size")
    if vectors_offset <= 0 or vectors_offset >= len(code):
        raise DiskAnalysisError(
            f"Resident auto-init vector table at 0x{vectors_offset:X} lies outside first CODE hunk"
        )
    vector_offsets: list[int] = []
    vector_format = "offset32"
    first_word = _read_u16_be(code, vectors_offset)
    if first_word == 0xFFFF:
        if not runtime_os.META.resident_autoinit_supports_short_vectors:
            raise DiskAnalysisError("Resident auto-init short vector tables are missing KB support")
        vector_format = "disp16"
        table_offset = vectors_offset + 2
        while True:
            if table_offset + 2 > len(code):
                raise DiskAnalysisError("Resident auto-init short vector table is unterminated")
            disp = int.from_bytes(code[table_offset:table_offset + 2], byteorder="big", signed=True)
            table_offset += 2
            if disp == -1:
                break
            target_offset = vectors_offset + disp
            if target_offset < 0 or target_offset >= len(code):
                raise DiskAnalysisError(
                    f"Resident auto-init vector target 0x{target_offset:X} lies outside first CODE hunk"
                )
            vector_offsets.append(target_offset)
    else:
        table_offset = vectors_offset
        while True:
            if table_offset + 4 > len(code):
                raise DiskAnalysisError("Resident auto-init vector table is unterminated")
            target_offset = _read_u32_be(code, table_offset)
            table_offset += 4
            if target_offset == 0xFFFFFFFF:
                break
            if target_offset < 0 or target_offset >= len(code):
                raise DiskAnalysisError(
                    f"Resident auto-init vector target 0x{target_offset:X} lies outside first CODE hunk"
                )
            vector_offsets.append(target_offset)
    init_struct = None if init_struct_offset == 0 else init_struct_offset
    if init_struct is not None and not (0 <= init_struct < len(code)):
        raise DiskAnalysisError(
            f"Resident auto-init init-struct pointer 0x{init_struct:X} lies outside first CODE hunk"
        )
    init_func = None if init_func_offset == 0 else init_func_offset
    if init_func is not None and not (0 <= init_func < len(code)):
        raise DiskAnalysisError(
            f"Resident auto-init init function 0x{init_func:X} lies outside first CODE hunk"
        )
    return ResidentAutoinitMetadata(
        payload_offset=payload_offset,
        base_size=base_size,
        vectors_offset=vectors_offset,
        vector_format=vector_format,
        vector_offsets=tuple(vector_offsets),
        init_struct_offset=init_struct,
        init_func_offset=init_func,
    )


def _library_info_from_resident(resident: ResidentInfo | None) -> LibraryInfo | None:
    if resident is None or resident.node_type != _os_const("NT_LIBRARY") or resident.name is None:
        return None
    kb_library = runtime_os.LIBRARIES.get(resident.name)
    total_lvo_count = None if kb_library is None else len(kb_library.lvo_index)
    public_function_count = None
    if kb_library is not None:
        public_function_count = sum(1 for function in kb_library.functions.values() if not function.private)
    return LibraryInfo(
        library_name=resident.name,
        id_string=resident.id_string,
        version=resident.version,
        public_function_count=public_function_count,
        total_lvo_count=total_lvo_count,
    )


def _classify_hunk_target(hunk_file: HunkFile) -> tuple[str, ResidentInfo | None, LibraryInfo | None]:
    resident = _find_resident_info(hunk_file)
    if resident is None:
        return "program", None, None
    if resident.node_type == _os_const("NT_LIBRARY"):
        resident = ResidentInfo(**{**resident.to_dict(), "autoinit": _parse_resident_autoinit_info(hunk_file, resident, "library")})
        return "library", resident, _library_info_from_resident(resident)
    if resident.node_type == _os_const("NT_DEVICE"):
        resident = ResidentInfo(**{**resident.to_dict(), "autoinit": _parse_resident_autoinit_info(hunk_file, resident, "device")})
        return "device", resident, None
    if resident.node_type == _os_const("NT_RESOURCE"):
        resident = ResidentInfo(**{**resident.to_dict(), "autoinit": _parse_resident_autoinit_info(hunk_file, resident, "resource")})
        return "resource", resident, None
    return "program", resident, None


def _load_dos_filesystem(
    kb: DiskKb,
    data: bytes,
    total_sectors: int,
) -> DosFilesystem:
    boot = _parse_boot_block(kb, data)
    assert boot.is_dos
    root_block_num = boot.rootblock_ptr
    if root_block_num == 0:
        raise DiskAnalysisError("DOS boot block is missing root block pointer")
    root = _parse_root_block(kb, data, root_block_num)
    directories, files = _walk_directory(kb, data, root.hash_table, "", total_sectors)
    bitmap, bitmap_map = _parse_bitmap(kb, data, root.bm_pages, total_sectors)
    block_usage_state = _build_block_usage(
        total_sectors,
        root_block_num,
        root.bm_pages,
        directories,
        files,
        bitmap_map,
    )
    return DosFilesystem(
        boot=boot,
        root=root,
        directories=directories,
        files=files,
        bitmap=bitmap,
        block_usage=BlockUsageInfo(
            summary=block_usage_state.summary,
            orphan_blocks=block_usage_state.orphan_blocks,
        ),
    )


def analyze_adf(
    adf_path: str | Path,
    *,
    extract_dir: str | Path | None = None,
    include_tracks: bool = False,
    kb_root: Path = PROJECT_ROOT,
) -> AdfAnalysis:
    kb = load_disk_kb(kb_root)
    adf_file = Path(adf_path)
    data = adf_file.read_bytes()
    matching_variants = [variant for variant in kb.variants.values() if variant.size_bytes == len(data)]
    if len(matching_variants) != 1:
        raise DiskAnalysisError(f"ADF size {len(data)} does not match exactly one known variant")
    variant = matching_variants[0]
    boot = _parse_boot_block(kb, data)
    disk_info = DiskInfo(
        path=adf_file.name,
        size=len(data),
        variant=variant.name,
        total_sectors=variant.total_sectors,
        sectors_per_track=variant.sectors_per_track,
        is_dos=boot.is_dos,
    )

    if not boot.is_dos:
        non_dos, track_analysis, trackloader_analysis = _non_dos_analysis(
            kb,
            data,
            boot,
            variant.total_sectors,
            variant.sectors_per_track,
            include_tracks,
        )
        return AdfAnalysis(
            disk_info=disk_info,
            boot_block=boot,
            non_dos=non_dos,
            track_analysis=track_analysis,
            trackloader_analysis=trackloader_analysis,
            bootloader_analysis=analyze_bootloader(
                data[kb.boot_block.bootcode_offset:kb.boot_block.boot_block_bytes],
                disk_bytes=data,
                raw_track_sources=[] if track_analysis is None else track_analysis.raw_sources,
                kb=kb,
            ),
        )

    try:
        filesystem = _load_dos_filesystem(kb, data, variant.total_sectors)
    except DiskAnalysisError as exc:
        non_dos, track_analysis, trackloader_analysis = _non_dos_analysis(
            kb,
            data,
            boot,
            variant.total_sectors,
            variant.sectors_per_track,
            include_tracks,
            filesystem_parse_error=str(exc),
        )
        return AdfAnalysis(
            disk_info=disk_info,
            boot_block=boot,
            non_dos=non_dos,
            track_analysis=track_analysis,
            trackloader_analysis=trackloader_analysis,
            bootloader_analysis=analyze_bootloader(
                data[kb.boot_block.bootcode_offset:kb.boot_block.boot_block_bytes],
                disk_bytes=data,
                raw_track_sources=[] if track_analysis is None else track_analysis.raw_sources,
                kb=kb,
            ),
        )
    root = filesystem.root
    directories = filesystem.directories
    files = filesystem.files
    bitmap = filesystem.bitmap

    extracted_files: list[DiskFileEntry] = files
    is_ffs = filesystem.boot.flags_byte & kb.ffs_flag_mask == kb.ffs_flag_mask
    classified_files: list[DiskFileEntry] = []
    for entry in files:
        payload = _read_file_payload(kb, data, entry, is_ffs)
        classified_files.append(
            DiskFileEntry(
                block_num=entry.block_num,
                name=entry.name,
                full_path=entry.full_path,
                size=entry.size,
                protection=entry.protection,
                comment=entry.comment,
                date=entry.date,
                hash_chain=entry.hash_chain,
                parent=entry.parent,
                extension_blocks=entry.extension_blocks,
                data_blocks=entry.data_blocks,
                data_block_count=entry.data_block_count,
                checksum_valid=entry.checksum_valid,
                content=_classify_file_content(kb, payload),
            )
        )
    extracted_files = classified_files
    if extract_dir is not None:
        output_dir = Path(extract_dir)
        if output_dir.exists():
            raise DiskAnalysisError(f"Extraction directory already exists: {output_dir}")
        output_dir.mkdir(parents=True)
        extracted_entries: list[DiskFileEntry] = []
        for entry in extracted_files:
            extracted_path = _extract_file(kb, data, entry, output_dir, is_ffs)
            extracted_entries.append(
                DiskFileEntry(
                    block_num=entry.block_num,
                    name=entry.name,
                    full_path=entry.full_path,
                    size=entry.size,
                    protection=entry.protection,
                    comment=entry.comment,
                    date=entry.date,
                    hash_chain=entry.hash_chain,
                    parent=entry.parent,
                    extension_blocks=entry.extension_blocks,
                    data_blocks=entry.data_blocks,
                    data_block_count=entry.data_block_count,
                    checksum_valid=entry.checksum_valid,
                    extracted_path=str(extracted_path),
                    content=entry.content,
                )
            )
        extracted_files = extracted_entries

    track_analysis = None
    trackloader_analysis = None
    if include_tracks:
        total_tracks = variant.total_sectors // variant.sectors_per_track
        tracks = [
            track
            for track in (
                _analyze_track(kb, data, track_num, variant.sectors_per_track)
                for track_num in range(total_tracks)
            )
            if not track.empty
        ]
        track_analysis = TrackAnalysis(
            total_tracks=total_tracks,
            track_size_bytes=kb.bytes_per_sector * variant.sectors_per_track,
            non_empty_tracks=len(tracks),
            tracks=tracks,
            raw_sources=[
                RawTrackSource(
                    track=track.track,
                    cylinder=track.cylinder,
                    head=track.head,
                    byte_offset=track.byte_offset,
                    byte_length=track.byte_length,
                )
                for track in tracks
            ],
        )
        trackloader_analysis = _build_trackloader_analysis(
            kb,
            data,
            tracks,
            kb.bytes_per_sector * variant.sectors_per_track,
        )
    bootloader_analysis = analyze_bootloader(
        data[kb.boot_block.bootcode_offset:kb.boot_block.boot_block_bytes],
        disk_bytes=data,
        raw_track_sources=[] if track_analysis is None else track_analysis.raw_sources,
        kb=kb,
    )

    return AdfAnalysis(
        disk_info=disk_info,
        boot_block=boot,
        root_block=root,
        filesystem=FilesystemInfo(
            type=boot.fs_type,
            volume_name=root.volume_name,
            directories=len(directories),
            files=len(files),
            total_file_size=sum(entry.size for entry in files),
        ),
        files=extracted_files,
        directories=directories,
        bitmap=bitmap,
        block_usage=filesystem.block_usage,
        track_analysis=track_analysis,
        trackloader_analysis=trackloader_analysis,
        bootloader_analysis=bootloader_analysis,
    )


def derive_disk_id(adf_path: str | Path) -> str:
    try:
        return cast(str, derive_disk_id_from_stem(Path(adf_path).stem.strip()))
    except ValueError as exc:
        raise DiskAnalysisError(str(exc)) from exc


def _local_target_name_for_entry(full_path: str) -> str:
    return cast(str, disk_entry_local_target_id(full_path))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _has_dos_filesystem(analysis: AdfAnalysis) -> bool:
    return analysis.filesystem is not None


def _require_complete_dos_analysis(analysis: AdfAnalysis) -> None:
    if analysis.root_block is None:
        raise DiskAnalysisError("DOS analysis is missing root block")
    if analysis.files is None:
        raise DiskAnalysisError("DOS analysis is missing file inventory")
    if analysis.directories is None:
        raise DiskAnalysisError("DOS analysis is missing directory inventory")
    if analysis.bitmap is None:
        raise DiskAnalysisError("DOS analysis is missing bitmap summary")
    if analysis.block_usage is None:
        raise DiskAnalysisError("DOS analysis is missing block usage summary")


def _bootblock_target_name(disk_id: str) -> str:
    return cast(str, disk_child_project_id(disk_id, bootblock_local_target_id()))


def _target_metadata_for_content(content: FileContentInfo) -> TargetMetadata:
    resident = None
    library = None
    entry_register_seeds: list[EntryRegisterSeedMetadata] = []
    library_name: str | None = None
    if content.resident is not None:
        resident_matchword = runtime_os.CONSTANTS["RTC_MATCHWORD"].value
        resident = ResidentTargetMetadata(
            offset=content.resident.offset,
            matchword=resident_matchword,
            flags=content.resident.flags,
            version=content.resident.version,
            node_type_name=content.resident.node_type_name,
            priority=content.resident.priority,
            name=content.resident.name,
            id_string=content.resident.id_string,
            init_offset=content.resident.init_offset,
            auto_init=content.resident.auto_init,
            autoinit=(
                None
                if content.resident.autoinit is None
                else content.resident.autoinit
            ),
        )
    if content.library is not None:
        library_name = content.library.library_name
        library = LibraryTargetMetadata(
            library_name=content.library.library_name,
            id_string=content.library.id_string,
            version=content.library.version,
            public_function_count=content.library.public_function_count,
            total_lvo_count=content.library.total_lvo_count,
        )
    if resident is not None and resident.auto_init:
        autoinit = resident.autoinit
        if autoinit is None:
            raise DiskAnalysisError("Auto-init resident is missing autoinit metadata")
        if autoinit.init_func_offset is not None:
            entry_register_seeds.append(
                EntryRegisterSeedMetadata(
                    entry_offset=autoinit.init_func_offset,
                    register="A6",
                    kind="library_base",
                    library_name=runtime_os.META.exec_base_addr.library,
                    struct_name="LIB",
                    context_name=None,
                    note="ExecBase",
                )
            )
        if library_name is None:
            raise DiskAnalysisError("Auto-init resident library target is missing library metadata")
        for vector_offset in autoinit.vector_offsets:
            entry_register_seeds.append(
                EntryRegisterSeedMetadata(
                    entry_offset=vector_offset,
                    register="A6",
                    kind="library_base",
                    library_name=library_name,
                    struct_name="LIB",
                    context_name=None,
                    note=f"{library_name} base",
                )
            )
    elif library_name is not None:
        entry_register_seeds.append(
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A6",
                kind="library_base",
                library_name=library_name,
                struct_name="LIB",
                context_name=None,
                note=f"{library_name} base",
            )
        )
    target_type = content.target_type
    assert isinstance(target_type, str)
    return TargetMetadata(
        target_type=target_type,
        entry_register_seeds=tuple(entry_register_seeds),
        resident=resident,
        library=library,
    )


def create_disk_project(
    adf_path: str | Path,
    *,
    disk_id: str | None = None,
    project_root: Path = PROJECT_ROOT,
    progress_fn: Callable[[str, int, int], None] | None = None,
) -> DiskManifest:
    from disasm.projects import (
        create_project_at_path,
        initialize_project_metadata,
        mark_project_updated,
    )

    adf_file = Path(adf_path)
    resolved_disk_id = disk_id or derive_disk_id(adf_file)
    disk_target_root = disk_project_root(project_root, resolved_disk_id)
    disk_children_root = disk_project_targets_dir(project_root, resolved_disk_id)
    manifest_path = disk_target_root / "manifest.json"
    if disk_target_root.exists():
        raise DiskAnalysisError(f"Disk target root already exists: {disk_target_root}")
    disk_target_root.mkdir(parents=True)
    initialize_project_metadata(disk_target_root)
    created_target_dirs: list[Path] = []
    try:
        disk_kb = load_disk_kb(PROJECT_ROOT)
        disk_bytes = adf_file.read_bytes()
        if progress_fn is not None:
            progress_fn("analyze_disk", 1, 4)
        analysis = analyze_adf(adf_file, include_tracks=True)

        if progress_fn is not None:
            progress_fn("create_bootblock_target", 2, 4)
        bootblock_local_name = bootblock_local_target_id()
        bootblock_target_name = _bootblock_target_name(resolved_disk_id)
        bootblock_target_dir = disk_children_root / bootblock_local_name
        if bootblock_target_dir.exists():
            raise DiskAnalysisError(f"Target already exists: {bootblock_target_name}")
        create_project_at_path(
            disk_child_target_relpath(resolved_disk_id, bootblock_local_name).as_posix(),
            project_root=project_root,
        )
        created_target_dirs.append(bootblock_target_dir)
        bootblock_binary_path = bootblock_target_dir / "binary.bin"
        _write_bytes(bootblock_binary_path, disk_bytes[: analysis.boot_block.bootcode_size + disk_kb.boot_loader.entry_offset])
        write_source_descriptor(
            bootblock_target_dir,
            {
                "kind": "raw_binary",
                "path": bootblock_binary_path.relative_to(project_root).as_posix(),
                "address_model": "local_offset",
                "load_address": disk_kb.boot_loader.load_address,
                "entrypoint": disk_kb.boot_loader.load_address + disk_kb.boot_loader.entry_offset,
                "code_start_offset": disk_kb.boot_entry.entry_point_offset,
                "parent_disk_id": resolved_disk_id,
            },
        )
        write_target_metadata(
            bootblock_target_dir,
            TargetMetadata(
                target_type="bootblock",
                entry_register_seeds=tuple(
                    EntryRegisterSeedMetadata(
                        entry_offset=None,
                        register=seed.register,
                        kind=seed.kind,
                        library_name=seed.library_name,
                        struct_name=seed.struct_name,
                        context_name=seed.context_name,
                        note=seed.note,
                    )
                    for seed in disk_kb.boot_entry.registers
                ),
                bootblock=BootBlockTargetMetadata(
                    magic_ascii=analysis.boot_block.magic_ascii,
                    flags_byte=analysis.boot_block.flags_byte,
                    fs_description=analysis.boot_block.fs_description,
                    checksum=analysis.boot_block.checksum,
                    checksum_valid=analysis.boot_block.checksum_valid,
                    rootblock_ptr=analysis.boot_block.rootblock_ptr,
                    bootcode_offset=disk_kb.boot_entry.entry_point_offset,
                    bootcode_size=analysis.boot_block.bootcode_size,
                    load_address=disk_kb.boot_loader.load_address,
                    entrypoint=disk_kb.boot_loader.load_address + disk_kb.boot_loader.entry_offset,
                ),
            ),
        )
        mark_project_updated(bootblock_target_dir)

        imported_targets: list[ImportedTarget] = []
        if _has_dos_filesystem(analysis):
            _require_complete_dos_analysis(analysis)
            if progress_fn is not None:
                progress_fn("import_targets", 3, 4)
            assert analysis.files is not None
            for entry in analysis.files:
                if entry.content is None:
                    raise DiskAnalysisError(f"Extracted file is missing content classification: {entry.full_path}")
                if entry.content.kind != "amiga_hunk_executable" or entry.content.is_executable is not True:
                    continue
                local_target_name = _local_target_name_for_entry(entry.full_path)
                target_name = cast(str, disk_child_project_id(resolved_disk_id, local_target_name))
                target_dir = disk_children_root / local_target_name
                if target_dir.exists():
                    raise DiskAnalysisError(f"Target already exists: {target_name}")
                create_project_at_path(
                    disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                    project_root=project_root,
                )
                created_target_dirs.append(target_dir)
                write_source_descriptor(
                    target_dir,
                    {
                        "kind": "disk_entry",
                        "disk_id": resolved_disk_id,
                        "disk_path": adf_file.as_posix(),
                        "entry_path": entry.full_path,
                        "parent_disk_id": resolved_disk_id,
                    },
                )
                write_target_metadata(target_dir, _target_metadata_for_content(entry.content))
                mark_project_updated(target_dir)
                imported_targets.append(
                    ImportedTarget(
                        target_name=target_name,
                        target_path=disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                        entry_path=entry.full_path,
                        binary_path=f"{adf_file.as_posix()}::{entry.full_path}",
                        target_type=entry.content.target_type,
                    )
                )

        if progress_fn is not None:
            progress_fn("write_manifest", 4, 4)
        imported_targets.sort(key=lambda target: target.entry_path)
        manifest = DiskManifest(
            schema_version=1,
            disk_id=resolved_disk_id,
            source_path=adf_file.as_posix(),
            source_sha256=hashlib.sha256(disk_bytes).hexdigest(),
            analysis=analysis,
            imported_targets=imported_targets,
            bootblock_target_name=bootblock_target_name,
            bootblock_target_path=disk_child_target_relpath(resolved_disk_id, bootblock_local_name).as_posix(),
        )
        _write_text(manifest_path, json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n")
        mark_project_updated(disk_target_root)
        return manifest
    except Exception:
        for target_dir in reversed(created_target_dirs):
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.rmtree(disk_target_root, ignore_errors=True)
        raise


def import_adf(
    adf_path: str | Path,
    *,
    disk_id: str | None = None,
    project_root: Path = PROJECT_ROOT,
    progress_fn: Callable[[str, int, int], None] | None = None,
) -> DiskManifest:
    return create_disk_project(adf_path, disk_id=disk_id, project_root=project_root, progress_fn=progress_fn)


def read_adf_entry(
    adf_path: str | Path,
    entry_path: str,
    *,
    kb_root: Path = PROJECT_ROOT,
) -> bytes:
    kb = load_disk_kb(kb_root)
    adf_file = Path(adf_path)
    data = adf_file.read_bytes()
    matching_variants = [variant for variant in kb.variants.values() if variant.size_bytes == len(data)]
    if len(matching_variants) != 1:
        raise DiskAnalysisError(f"ADF size {len(data)} does not match exactly one known variant")
    variant = matching_variants[0]
    filesystem = _load_dos_filesystem(kb, data, variant.total_sectors)
    is_ffs = filesystem.boot.flags_byte & kb.ffs_flag_mask == kb.ffs_flag_mask
    for entry in filesystem.files:
        if entry.full_path == entry_path:
            return _read_file_payload(kb, data, entry, is_ffs)
    raise DiskAnalysisError(f"ADF entry not found: {entry_path}")


# TODO(X) Move to the script
def print_summary(result: AdfAnalysis) -> None:
    info = result.disk_info
    boot = result.boot_block
    if result.bootloader_analysis is None:
        raise DiskAnalysisError("ADF analysis is missing bootloader_analysis")
    if result.track_analysis is not None and result.trackloader_analysis is None:
        raise DiskAnalysisError("ADF analysis is missing trackloader_analysis for track analysis")
    print(f"=== {info.path} ===")
    print(f"  Size: {info.size} bytes ({info.variant})")
    print(f"  Sectors: {info.total_sectors}")
    print(
        f"  Boot: {'DOS' if info.is_dos else 'Non-DOS'} "
        f"(checksum {'OK' if boot.checksum_valid else 'FAIL'})"
    )
    if boot.fs_description:
        print(f"  Filesystem: {boot.fs_description}")
    if boot.bootcode_has_code:
        print(f"  Boot code: yes (entropy: {boot.bootcode_entropy})")
    if result.filesystem is not None and result.bitmap is not None:
        filesystem = result.filesystem
        bitmap = result.bitmap
        print(f"\n  Volume: {filesystem.volume_name}")
        print(f"  Files: {filesystem.files}, Directories: {filesystem.directories}")
        print(f"  Total file data: {filesystem.total_file_size:,} bytes")
        print(
            f"  Blocks: {bitmap.allocated_blocks} allocated, "
            f"{bitmap.free_blocks} free ({bitmap.percent_used}% used)"
        )
        imported_candidates = [
            entry for entry in (result.files or [])
            if entry.content is not None and entry.content.is_executable is True
        ]
        if imported_candidates:
            print(f"  Hunk executables: {len(imported_candidates)}")
    if result.track_analysis is not None:
        track_analysis = result.track_analysis
        print(
            f"\n  Tracks: {track_analysis.total_tracks} total, "
            f"{track_analysis.non_empty_tracks} non-empty"
        )
    if result.trackloader_analysis is not None:
        trackloader = result.trackloader_analysis
        if trackloader.boot_ascii_strings:
            print(f"  Boot strings: {len(trackloader.boot_ascii_strings)}")
        if trackloader.candidate_code_tracks:
            print(f"  Candidate code tracks: {', '.join(str(track) for track in trackloader.candidate_code_tracks[:12])}")
        if trackloader.nonempty_track_spans:
            spans = ", ".join(
                f"{span.start_track}-{span.end_track}" if span.start_track != span.end_track else str(span.start_track)
                for span in trackloader.nonempty_track_spans[:8]
            )
            print(f"  Non-empty spans: {spans}")
    if result.bootloader_analysis.stages:
        print("  Memory regions:")
        for region in result.bootloader_analysis.memory_regions[:12]:
            print(
                f"    {region.stage_name} {region.region_kind}: "
                f"{region.base_addr:#x}..{region.base_addr + region.byte_length - 1:#x} "
                f"materialized={region.materialized}"
            )
        print("  Transfers:")
        for transfer in result.bootloader_analysis.transfers[:16]:
            if transfer.transfer_kind == "disk_read":
                print(
                    f"    {transfer.stage_name}: disk {transfer.disk_offset:#x} -> "
                    f"{transfer.destination_addr:#x} bytes={transfer.byte_length:#x}"
                )
                continue
            if transfer.transfer_kind == "memory_copy":
                print(
                    f"    {transfer.stage_name}: copy {transfer.source_addr:#x} -> "
                    f"{transfer.destination_addr:#x} bytes={transfer.byte_length:#x}"
                )
                continue
            if transfer.transfer_kind == "decode":
                parts = [
                    f"{transfer.stage_name}: decode",
                    f"input={transfer.input_buffer_addr:#x}" if transfer.input_buffer_addr is not None else "input=?",
                    f"output={transfer.destination_addr:#x}" if transfer.destination_addr is not None else "output=?",
                ]
                if transfer.byte_length is not None:
                    parts.append(f"bytes={transfer.byte_length:#x}")
                if transfer.start_track is not None:
                    span = (
                        f"{transfer.start_track}-{transfer.end_track}"
                        if transfer.end_track is not None and transfer.end_track != transfer.start_track
                        else str(transfer.start_track)
                    )
                    parts.append(f"track_span={span}")
                if transfer.start_byte_offset is not None:
                    parts.append(f"disk_byte={transfer.start_byte_offset:#x}")
                if transfer.checksum_gate_kind is not None:
                    parts.append(f"gate={transfer.checksum_gate_kind}@{transfer.checksum_gate_addr:#x}")
                print(f"    {' '.join(parts)}")
                continue
            if transfer.transfer_kind == "handoff":
                print(f"    {transfer.stage_name}: jump -> {transfer.target_addr:#x} ({transfer.source_kind})")
