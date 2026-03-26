from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast


def _json_object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _json_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return value


@dataclass(frozen=True, slots=True)
class ResidentInfo:
    offset: int
    flags: int
    version: int
    node_type: int
    node_type_name: str
    priority: int
    name: str | None
    id_string: str | None
    init_offset: int
    auto_init: bool

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ResidentInfo:
        offset = payload["offset"]
        flags = payload["flags"]
        version = payload["version"]
        node_type = payload["node_type"]
        node_type_name = payload["node_type_name"]
        priority = payload["priority"]
        name = payload.get("name")
        id_string = payload.get("id_string")
        init_offset = payload["init_offset"]
        auto_init = payload["auto_init"]
        assert isinstance(offset, int)
        assert isinstance(flags, int)
        assert isinstance(version, int)
        assert isinstance(node_type, int)
        assert isinstance(node_type_name, str)
        assert isinstance(priority, int)
        assert name is None or isinstance(name, str)
        assert id_string is None or isinstance(id_string, str)
        assert isinstance(init_offset, int)
        assert isinstance(auto_init, bool)
        return cls(
            offset=offset,
            flags=flags,
            version=version,
            node_type=node_type,
            node_type_name=node_type_name,
            priority=priority,
            name=name,
            id_string=id_string,
            init_offset=init_offset,
            auto_init=auto_init,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class LibraryInfo:
    library_name: str
    id_string: str | None
    version: int
    public_function_count: int | None
    total_lvo_count: int | None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> LibraryInfo:
        library_name = payload["library_name"]
        id_string = payload.get("id_string")
        version = payload["version"]
        public_function_count = payload.get("public_function_count")
        total_lvo_count = payload.get("total_lvo_count")
        assert isinstance(library_name, str)
        assert id_string is None or isinstance(id_string, str)
        assert isinstance(version, int)
        assert public_function_count is None or isinstance(public_function_count, int)
        assert total_lvo_count is None or isinstance(total_lvo_count, int)
        return cls(
            library_name=library_name,
            id_string=id_string,
            version=version,
            public_function_count=public_function_count,
            total_lvo_count=total_lvo_count,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class FileContentInfo:
    kind: str
    size: int
    sha256: str
    is_executable: bool | None = None
    hunk_count: int | None = None
    hunk_parse_error: str | None = None
    group_id: str | None = None
    form_id: str | None = None
    target_type: str | None = None
    resident: ResidentInfo | None = None
    library: LibraryInfo | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> FileContentInfo:
        kind = payload["kind"]
        size = payload["size"]
        sha256 = payload["sha256"]
        is_executable = payload.get("is_executable")
        hunk_count = payload.get("hunk_count")
        hunk_parse_error = payload.get("hunk_parse_error")
        group_id = payload.get("group_id")
        form_id = payload.get("form_id")
        target_type = payload.get("target_type")
        resident = payload.get("resident")
        library = payload.get("library")
        assert isinstance(kind, str)
        assert isinstance(size, int)
        assert isinstance(sha256, str)
        assert is_executable is None or isinstance(is_executable, bool)
        assert hunk_count is None or isinstance(hunk_count, int)
        assert hunk_parse_error is None or isinstance(hunk_parse_error, str)
        assert group_id is None or isinstance(group_id, str)
        assert form_id is None or isinstance(form_id, str)
        assert target_type is None or isinstance(target_type, str)
        return cls(
            kind=kind,
            size=size,
            sha256=sha256,
            is_executable=is_executable,
            hunk_count=hunk_count,
            hunk_parse_error=hunk_parse_error,
            group_id=group_id,
            form_id=form_id,
            target_type=target_type,
            resident=None if resident is None else ResidentInfo.from_dict(_json_object(resident)),
            library=None if library is None else LibraryInfo.from_dict(_json_object(library)),
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class DiskFileEntry:
    block_num: int
    name: str
    full_path: str
    size: int
    protection: str
    comment: str | None
    date: str
    hash_chain: int
    parent: int
    extension_blocks: list[int]
    data_blocks: list[int]
    data_block_count: int
    checksum_valid: bool
    extracted_path: str | None = None
    content: FileContentInfo | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> DiskFileEntry:
        block_num = payload["block_num"]
        name = payload["name"]
        full_path = payload["full_path"]
        size = payload["size"]
        protection = payload["protection"]
        comment = payload.get("comment")
        date = payload["date"]
        hash_chain = payload["hash_chain"]
        parent = payload["parent"]
        extension_blocks = _json_list(payload["extension_blocks"])
        data_blocks = _json_list(payload["data_blocks"])
        data_block_count = payload["data_block_count"]
        checksum_valid = payload["checksum_valid"]
        extracted_path = payload.get("extracted_path")
        content_payload = payload.get("content")
        assert isinstance(block_num, int)
        assert isinstance(name, str)
        assert isinstance(full_path, str)
        assert isinstance(size, int)
        assert isinstance(protection, str)
        assert comment is None or isinstance(comment, str)
        assert isinstance(date, str)
        assert isinstance(hash_chain, int)
        assert isinstance(parent, int)
        assert all(isinstance(item, int) for item in extension_blocks)
        assert all(isinstance(item, int) for item in data_blocks)
        assert isinstance(data_block_count, int)
        assert isinstance(checksum_valid, bool)
        assert extracted_path is None or isinstance(extracted_path, str)
        return cls(
            block_num=block_num,
            name=name,
            full_path=full_path,
            size=size,
            protection=protection,
            comment=comment,
            date=date,
            hash_chain=hash_chain,
            parent=parent,
            extension_blocks=[cast(int, item) for item in extension_blocks],
            data_blocks=[cast(int, item) for item in data_blocks],
            data_block_count=data_block_count,
            checksum_valid=checksum_valid,
            extracted_path=extracted_path,
            content=None if content_payload is None else FileContentInfo.from_dict(_json_object(content_payload)),
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class DiskDirectoryEntry:
    block_num: int
    name: str
    full_path: str
    protection: str
    comment: str | None
    date: str
    hash_chain: int
    parent: int
    checksum_valid: bool

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> DiskDirectoryEntry:
        block_num = payload["block_num"]
        name = payload["name"]
        full_path = payload["full_path"]
        protection = payload["protection"]
        comment = payload.get("comment")
        date = payload["date"]
        hash_chain = payload["hash_chain"]
        parent = payload["parent"]
        checksum_valid = payload["checksum_valid"]
        assert isinstance(block_num, int)
        assert isinstance(name, str)
        assert isinstance(full_path, str)
        assert isinstance(protection, str)
        assert comment is None or isinstance(comment, str)
        assert isinstance(date, str)
        assert isinstance(hash_chain, int)
        assert isinstance(parent, int)
        assert isinstance(checksum_valid, bool)
        return cls(
            block_num=block_num,
            name=name,
            full_path=full_path,
            protection=protection,
            comment=comment,
            date=date,
            hash_chain=hash_chain,
            parent=parent,
            checksum_valid=checksum_valid,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class DiskInfo:
    path: str
    size: int
    variant: str
    total_sectors: int
    sectors_per_track: int
    is_dos: bool

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> DiskInfo:
        path = payload["path"]
        size = payload["size"]
        variant = payload["variant"]
        total_sectors = payload["total_sectors"]
        sectors_per_track = payload["sectors_per_track"]
        is_dos = payload["is_dos"]
        assert isinstance(path, str)
        assert isinstance(size, int)
        assert isinstance(variant, str)
        assert isinstance(total_sectors, int)
        assert isinstance(sectors_per_track, int)
        assert isinstance(is_dos, bool)
        return cls(path=path, size=size, variant=variant, total_sectors=total_sectors, sectors_per_track=sectors_per_track, is_dos=is_dos)

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootBlockInfo:
    magic_ascii: str
    is_dos: bool
    flags_byte: int
    fs_type: str
    fs_description: str
    checksum: str
    checksum_valid: bool
    rootblock_ptr: int
    bootcode_size: int
    bootcode_has_code: bool
    bootcode_entropy: float

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootBlockInfo:
        magic_ascii = payload["magic_ascii"]
        is_dos = payload["is_dos"]
        flags_byte = payload["flags_byte"]
        fs_type = payload["fs_type"]
        fs_description = payload["fs_description"]
        checksum = payload["checksum"]
        checksum_valid = payload["checksum_valid"]
        rootblock_ptr = payload["rootblock_ptr"]
        bootcode_size = payload["bootcode_size"]
        bootcode_has_code = payload["bootcode_has_code"]
        bootcode_entropy = payload["bootcode_entropy"]
        assert isinstance(magic_ascii, str)
        assert isinstance(is_dos, bool)
        assert isinstance(flags_byte, int)
        assert isinstance(fs_type, str)
        assert isinstance(fs_description, str)
        assert isinstance(checksum, str)
        assert isinstance(checksum_valid, bool)
        assert isinstance(rootblock_ptr, int)
        assert isinstance(bootcode_size, int)
        assert isinstance(bootcode_has_code, bool)
        assert isinstance(bootcode_entropy, int | float)
        return cls(
            magic_ascii=magic_ascii,
            is_dos=is_dos,
            flags_byte=flags_byte,
            fs_type=fs_type,
            fs_description=fs_description,
            checksum=checksum,
            checksum_valid=checksum_valid,
            rootblock_ptr=rootblock_ptr,
            bootcode_size=bootcode_size,
            bootcode_has_code=bootcode_has_code,
            bootcode_entropy=float(bootcode_entropy),
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class RootBlockInfo:
    block_num: int
    hash_table: list[int]
    checksum_valid: bool
    bm_flag: int
    bm_pages: list[int]
    volume_name: str
    root_date: str
    volume_date: str
    creation_date: str

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> RootBlockInfo:
        block_num = payload["block_num"]
        hash_table = _json_list(payload["hash_table"])
        checksum_valid = payload["checksum_valid"]
        bm_flag = payload["bm_flag"]
        bm_pages = _json_list(payload["bm_pages"])
        volume_name = payload["volume_name"]
        root_date = payload["root_date"]
        volume_date = payload["volume_date"]
        creation_date = payload["creation_date"]
        assert isinstance(block_num, int)
        assert all(isinstance(item, int) for item in hash_table)
        assert isinstance(checksum_valid, bool)
        assert isinstance(bm_flag, int)
        assert all(isinstance(item, int) for item in bm_pages)
        assert isinstance(volume_name, str)
        assert isinstance(root_date, str)
        assert isinstance(volume_date, str)
        assert isinstance(creation_date, str)
        return cls(
            block_num=block_num,
            hash_table=[cast(int, item) for item in hash_table],
            checksum_valid=checksum_valid,
            bm_flag=bm_flag,
            bm_pages=[cast(int, item) for item in bm_pages],
            volume_name=volume_name,
            root_date=root_date,
            volume_date=volume_date,
            creation_date=creation_date,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class FilesystemInfo:
    type: str
    volume_name: str
    directories: int
    files: int
    total_file_size: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> FilesystemInfo:
        type_name = payload["type"]
        volume_name = payload["volume_name"]
        directories = payload["directories"]
        files = payload["files"]
        total_file_size = payload["total_file_size"]
        assert isinstance(type_name, str)
        assert isinstance(volume_name, str)
        assert isinstance(directories, int)
        assert isinstance(files, int)
        assert isinstance(total_file_size, int)
        return cls(type=type_name, volume_name=volume_name, directories=directories, files=files, total_file_size=total_file_size)

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BitmapInfo:
    checksum_valid: bool
    free_blocks: int
    allocated_blocks: int
    total_blocks: int
    percent_used: float

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BitmapInfo:
        checksum_valid = payload["checksum_valid"]
        free_blocks = payload["free_blocks"]
        allocated_blocks = payload["allocated_blocks"]
        total_blocks = payload["total_blocks"]
        percent_used = payload["percent_used"]
        assert isinstance(checksum_valid, bool)
        assert isinstance(free_blocks, int)
        assert isinstance(allocated_blocks, int)
        assert isinstance(total_blocks, int)
        assert isinstance(percent_used, int | float)
        return cls(
            checksum_valid=checksum_valid,
            free_blocks=free_blocks,
            allocated_blocks=allocated_blocks,
            total_blocks=total_blocks,
            percent_used=float(percent_used),
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BlockUsageInfo:
    summary: dict[str, int]
    orphan_blocks: list[int]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BlockUsageInfo:
        summary = _json_object(payload["summary"])
        orphan_blocks = _json_list(payload["orphan_blocks"])
        assert all(isinstance(key, str) and isinstance(value, int) for key, value in summary.items())
        assert all(isinstance(item, int) for item in orphan_blocks)
        return cls(
            summary={key: cast(int, value) for key, value in summary.items()},
            orphan_blocks=[cast(int, item) for item in orphan_blocks],
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class RawTrackSource:
    track: int
    cylinder: int
    head: int
    byte_offset: int
    byte_length: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> RawTrackSource:
        track = payload["track"]
        cylinder = payload["cylinder"]
        head = payload["head"]
        byte_offset = payload["byte_offset"]
        byte_length = payload["byte_length"]
        assert isinstance(track, int)
        assert isinstance(cylinder, int)
        assert isinstance(head, int)
        assert isinstance(byte_offset, int)
        assert isinstance(byte_length, int)
        return cls(
            track=track,
            cylinder=cylinder,
            head=head,
            byte_offset=byte_offset,
            byte_length=byte_length,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class RawTrackSourceSpan:
    start_track: int
    end_track: int
    start_byte_offset: int
    byte_length: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> RawTrackSourceSpan:
        start_track = payload["start_track"]
        end_track = payload["end_track"]
        start_byte_offset = payload["start_byte_offset"]
        byte_length = payload["byte_length"]
        assert isinstance(start_track, int)
        assert isinstance(end_track, int)
        assert isinstance(start_byte_offset, int)
        assert isinstance(byte_length, int)
        return cls(
            start_track=start_track,
            end_track=end_track,
            start_byte_offset=start_byte_offset,
            byte_length=byte_length,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class TrackInfo:
    track: int
    cylinder: int
    head: int
    first_block: int
    byte_offset: int
    byte_length: int
    empty: bool
    entropy: float
    m68k_pattern_count: int
    has_code: bool
    ascii_strings: list[dict[str, object]]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> TrackInfo:
        track = payload["track"]
        cylinder = payload["cylinder"]
        head = payload["head"]
        first_block = payload["first_block"]
        byte_offset = payload["byte_offset"]
        byte_length = payload["byte_length"]
        empty = payload["empty"]
        entropy = payload["entropy"]
        m68k_pattern_count = payload["m68k_pattern_count"]
        has_code = payload["has_code"]
        ascii_strings = _json_list(payload["ascii_strings"])
        assert isinstance(track, int)
        assert isinstance(cylinder, int)
        assert isinstance(head, int)
        assert isinstance(first_block, int)
        assert isinstance(byte_offset, int)
        assert isinstance(byte_length, int)
        assert isinstance(empty, bool)
        assert isinstance(entropy, int | float)
        assert isinstance(m68k_pattern_count, int)
        assert isinstance(has_code, bool)
        return cls(
            track=track,
            cylinder=cylinder,
            head=head,
            first_block=first_block,
            byte_offset=byte_offset,
            byte_length=byte_length,
            empty=empty,
            entropy=float(entropy),
            m68k_pattern_count=m68k_pattern_count,
            has_code=has_code,
            ascii_strings=[_json_object(item) for item in ascii_strings],
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class TrackAnalysis:
    total_tracks: int
    track_size_bytes: int
    non_empty_tracks: int
    tracks: list[TrackInfo]
    raw_sources: list[RawTrackSource]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> TrackAnalysis:
        total_tracks = payload["total_tracks"]
        track_size_bytes = payload["track_size_bytes"]
        non_empty_tracks = payload["non_empty_tracks"]
        tracks = _json_list(payload["tracks"])
        raw_sources = _json_list(payload["raw_sources"])
        assert isinstance(total_tracks, int)
        assert isinstance(track_size_bytes, int)
        assert isinstance(non_empty_tracks, int)
        return cls(
            total_tracks=total_tracks,
            track_size_bytes=track_size_bytes,
            non_empty_tracks=non_empty_tracks,
            tracks=[TrackInfo.from_dict(_json_object(item)) for item in tracks],
            raw_sources=[RawTrackSource.from_dict(_json_object(item)) for item in raw_sources],
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class TrackSpan:
    start_track: int
    end_track: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> TrackSpan:
        start_track = payload["start_track"]
        end_track = payload["end_track"]
        assert isinstance(start_track, int)
        assert isinstance(end_track, int)
        return cls(start_track=start_track, end_track=end_track)

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class TrackloaderAnalysis:
    boot_ascii_strings: list[str]
    candidate_code_tracks: list[int]
    high_entropy_tracks: list[int]
    nonempty_track_spans: list[TrackSpan]
    repeated_track_groups: list[list[int]]
    nonempty_head0_tracks: int
    nonempty_head1_tracks: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> TrackloaderAnalysis:
        boot_ascii_strings = _json_list(payload["boot_ascii_strings"])
        candidate_code_tracks = _json_list(payload["candidate_code_tracks"])
        high_entropy_tracks = _json_list(payload["high_entropy_tracks"])
        nonempty_track_spans = _json_list(payload["nonempty_track_spans"])
        repeated_track_groups = _json_list(payload["repeated_track_groups"])
        nonempty_head0_tracks = payload["nonempty_head0_tracks"]
        nonempty_head1_tracks = payload["nonempty_head1_tracks"]
        assert all(isinstance(item, str) for item in boot_ascii_strings)
        assert all(isinstance(item, int) for item in candidate_code_tracks)
        assert all(isinstance(item, int) for item in high_entropy_tracks)
        assert isinstance(nonempty_head0_tracks, int)
        assert isinstance(nonempty_head1_tracks, int)
        parsed_repeat_groups: list[list[int]] = []
        for group in repeated_track_groups:
            raw_group = _json_list(group)
            assert all(isinstance(item, int) for item in raw_group)
            parsed_repeat_groups.append([cast(int, item) for item in raw_group])
        return cls(
            boot_ascii_strings=[cast(str, item) for item in boot_ascii_strings],
            candidate_code_tracks=[cast(int, item) for item in candidate_code_tracks],
            high_entropy_tracks=[cast(int, item) for item in high_entropy_tracks],
            nonempty_track_spans=[TrackSpan.from_dict(_json_object(item)) for item in nonempty_track_spans],
            repeated_track_groups=parsed_repeat_groups,
            nonempty_head0_tracks=nonempty_head0_tracks,
            nonempty_head1_tracks=nonempty_head1_tracks,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderMemoryAccess:
    instruction_addr: int
    access: str
    width_bits: int
    address: int
    symbol: str | None
    value: int | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderMemoryAccess:
        instruction_addr = payload["instruction_addr"]
        access = payload["access"]
        width_bits = payload["width_bits"]
        address = payload["address"]
        symbol = payload.get("symbol")
        value = payload.get("value")
        assert isinstance(instruction_addr, int)
        assert isinstance(access, str)
        assert isinstance(width_bits, int)
        assert isinstance(address, int)
        assert symbol is None or isinstance(symbol, str)
        assert value is None or isinstance(value, int)
        return cls(
            instruction_addr=instruction_addr,
            access=access,
            width_bits=width_bits,
            address=address,
            symbol=symbol,
            value=value,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderLoad:
    instruction_addr: int
    command_name: str
    disk_offset: int
    byte_length: int
    destination_addr: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderLoad:
        instruction_addr = payload["instruction_addr"]
        command_name = payload["command_name"]
        disk_offset = payload["disk_offset"]
        byte_length = payload["byte_length"]
        destination_addr = payload["destination_addr"]
        assert isinstance(instruction_addr, int)
        assert isinstance(command_name, str)
        assert isinstance(disk_offset, int)
        assert isinstance(byte_length, int)
        assert isinstance(destination_addr, int)
        return cls(
            instruction_addr=instruction_addr,
            command_name=command_name,
            disk_offset=disk_offset,
            byte_length=byte_length,
            destination_addr=destination_addr,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderMemoryCopy:
    instruction_addr: int
    source_addr: int
    destination_addr: int
    byte_length: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderMemoryCopy:
        instruction_addr = payload["instruction_addr"]
        source_addr = payload["source_addr"]
        destination_addr = payload["destination_addr"]
        byte_length = payload["byte_length"]
        assert isinstance(instruction_addr, int)
        assert isinstance(source_addr, int)
        assert isinstance(destination_addr, int)
        assert isinstance(byte_length, int)
        return cls(
            instruction_addr=instruction_addr,
            source_addr=source_addr,
            destination_addr=destination_addr,
            byte_length=byte_length,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderReadSetup:
    instruction_addr: int
    buffer_addr: int | None
    sync_word: int | None
    dsklen_value: int | None
    dma_byte_length: int | None
    drive: int | None
    cylinder: int | None
    head: int | None
    track: int | None
    adkcon_values: list[int]
    dmacon_values: list[int]
    wait_loop_addr: int | None = None
    buffer_scan_addr: int | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderReadSetup:
        instruction_addr = payload["instruction_addr"]
        buffer_addr = payload["buffer_addr"]
        sync_word = payload["sync_word"]
        dsklen_value = payload["dsklen_value"]
        dma_byte_length = payload["dma_byte_length"]
        drive = payload["drive"]
        cylinder = payload["cylinder"]
        head = payload["head"]
        track = payload["track"]
        adkcon_values = _json_list(payload["adkcon_values"])
        dmacon_values = _json_list(payload["dmacon_values"])
        wait_loop_addr = payload["wait_loop_addr"]
        buffer_scan_addr = payload["buffer_scan_addr"]
        assert isinstance(instruction_addr, int)
        assert buffer_addr is None or isinstance(buffer_addr, int)
        assert sync_word is None or isinstance(sync_word, int)
        assert dsklen_value is None or isinstance(dsklen_value, int)
        assert dma_byte_length is None or isinstance(dma_byte_length, int)
        assert drive is None or isinstance(drive, int)
        assert cylinder is None or isinstance(cylinder, int)
        assert head is None or isinstance(head, int)
        assert track is None or isinstance(track, int)
        assert all(isinstance(item, int) for item in adkcon_values)
        assert all(isinstance(item, int) for item in dmacon_values)
        assert wait_loop_addr is None or isinstance(wait_loop_addr, int)
        assert buffer_scan_addr is None or isinstance(buffer_scan_addr, int)
        return cls(
            instruction_addr=instruction_addr,
            buffer_addr=buffer_addr,
            sync_word=sync_word,
            dsklen_value=dsklen_value,
            dma_byte_length=dma_byte_length,
            drive=drive,
            cylinder=cylinder,
            head=head,
            track=track,
            adkcon_values=[cast(int, item) for item in adkcon_values],
            dmacon_values=[cast(int, item) for item in dmacon_values],
            wait_loop_addr=wait_loop_addr,
            buffer_scan_addr=buffer_scan_addr,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderDecodeOutput:
    instruction_addr: int
    write_loop_addr: int
    output_addr: int | None
    output_base_addr: int | None
    longword_count: int | None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderDecodeOutput:
        instruction_addr = payload["instruction_addr"]
        write_loop_addr = payload["write_loop_addr"]
        output_addr = payload["output_addr"]
        output_base_addr = payload["output_base_addr"]
        longword_count = payload["longword_count"]
        assert isinstance(instruction_addr, int)
        assert isinstance(write_loop_addr, int)
        assert output_addr is None or isinstance(output_addr, int)
        assert output_base_addr is None or isinstance(output_base_addr, int)
        assert longword_count is None or isinstance(longword_count, int)
        return cls(
            instruction_addr=instruction_addr,
            write_loop_addr=write_loop_addr,
            output_addr=output_addr,
            output_base_addr=output_base_addr,
            longword_count=longword_count,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderDiskRead:
    instruction_addr: int
    command_name: str
    source_kind: str
    disk_offset: int
    byte_length: int
    destination_addr: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderDiskRead:
        instruction_addr = payload["instruction_addr"]
        command_name = payload["command_name"]
        source_kind = payload["source_kind"]
        disk_offset = payload["disk_offset"]
        byte_length = payload["byte_length"]
        destination_addr = payload["destination_addr"]
        assert isinstance(instruction_addr, int)
        assert isinstance(command_name, str)
        assert isinstance(source_kind, str)
        assert isinstance(disk_offset, int)
        assert isinstance(byte_length, int)
        assert isinstance(destination_addr, int)
        return cls(
            instruction_addr=instruction_addr,
            command_name=command_name,
            source_kind=source_kind,
            disk_offset=disk_offset,
            byte_length=byte_length,
            destination_addr=destination_addr,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderDecodeRegion:
    instruction_addr: int
    input_buffer_addr: int | None
    input_consumed_byte_offset: int | None
    input_consumed_byte_length: int | None
    checksum_gate_addr: int | None
    checksum_gate_kind: str | None
    input_source_kind: str
    input_required_source_kind: str
    input_source_candidates: list[RawTrackSource]
    input_source_candidate_spans: list[RawTrackSourceSpan]
    input_required_byte_length: int | None
    input_concrete_byte_count: int
    input_complete: bool
    input_materializable: bool
    input_missing_reason: str | None
    output_base_addr: int | None
    output_addr: int | None
    byte_length: int | None
    write_loop_addr: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderDecodeRegion:
        instruction_addr = payload["instruction_addr"]
        input_buffer_addr = payload["input_buffer_addr"]
        input_consumed_byte_offset = payload["input_consumed_byte_offset"]
        input_consumed_byte_length = payload["input_consumed_byte_length"]
        checksum_gate_addr = payload["checksum_gate_addr"]
        checksum_gate_kind = payload["checksum_gate_kind"]
        input_source_kind = payload["input_source_kind"]
        input_required_source_kind = payload["input_required_source_kind"]
        input_source_candidates = _json_list(payload["input_source_candidates"])
        input_source_candidate_spans = _json_list(payload["input_source_candidate_spans"])
        input_required_byte_length = payload["input_required_byte_length"]
        input_concrete_byte_count = payload["input_concrete_byte_count"]
        input_complete = payload["input_complete"]
        input_materializable = payload["input_materializable"]
        input_missing_reason = payload["input_missing_reason"]
        output_base_addr = payload["output_base_addr"]
        output_addr = payload["output_addr"]
        byte_length = payload["byte_length"]
        write_loop_addr = payload["write_loop_addr"]
        assert isinstance(instruction_addr, int)
        assert input_buffer_addr is None or isinstance(input_buffer_addr, int)
        assert input_consumed_byte_offset is None or isinstance(input_consumed_byte_offset, int)
        assert input_consumed_byte_length is None or isinstance(input_consumed_byte_length, int)
        assert checksum_gate_addr is None or isinstance(checksum_gate_addr, int)
        assert checksum_gate_kind is None or isinstance(checksum_gate_kind, str)
        assert isinstance(input_source_kind, str)
        assert isinstance(input_required_source_kind, str)
        assert all(isinstance(item, dict) for item in input_source_candidates)
        assert all(isinstance(item, dict) for item in input_source_candidate_spans)
        assert input_required_byte_length is None or isinstance(input_required_byte_length, int)
        assert isinstance(input_concrete_byte_count, int)
        assert isinstance(input_complete, bool)
        assert isinstance(input_materializable, bool)
        assert input_missing_reason is None or isinstance(input_missing_reason, str)
        assert output_base_addr is None or isinstance(output_base_addr, int)
        assert output_addr is None or isinstance(output_addr, int)
        assert byte_length is None or isinstance(byte_length, int)
        assert isinstance(write_loop_addr, int)
        return cls(
            instruction_addr=instruction_addr,
            input_buffer_addr=input_buffer_addr,
            input_consumed_byte_offset=input_consumed_byte_offset,
            input_consumed_byte_length=input_consumed_byte_length,
            checksum_gate_addr=checksum_gate_addr,
            checksum_gate_kind=checksum_gate_kind,
            input_source_kind=input_source_kind,
            input_required_source_kind=input_required_source_kind,
            input_source_candidates=[RawTrackSource.from_dict(_json_object(item)) for item in input_source_candidates],
            input_source_candidate_spans=[RawTrackSourceSpan.from_dict(_json_object(item)) for item in input_source_candidate_spans],
            input_required_byte_length=input_required_byte_length,
            input_concrete_byte_count=input_concrete_byte_count,
            input_complete=input_complete,
            input_materializable=input_materializable,
            input_missing_reason=input_missing_reason,
            output_base_addr=output_base_addr,
            output_addr=output_addr,
            byte_length=byte_length,
            write_loop_addr=write_loop_addr,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderHandoff:
    instruction_addr: int
    target_addr: int
    source_kind: str

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderHandoff:
        instruction_addr = payload["instruction_addr"]
        target_addr = payload["target_addr"]
        source_kind = payload["source_kind"]
        assert isinstance(instruction_addr, int)
        assert isinstance(target_addr, int)
        assert isinstance(source_kind, str)
        return cls(
            instruction_addr=instruction_addr,
            target_addr=target_addr,
            source_kind=source_kind,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderDerivedRegion:
    base_addr: int
    byte_length: int
    concrete_byte_count: int
    complete: bool
    data_hex: str | None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderDerivedRegion:
        base_addr = payload["base_addr"]
        byte_length = payload["byte_length"]
        concrete_byte_count = payload["concrete_byte_count"]
        complete = payload["complete"]
        data_hex = payload["data_hex"]
        assert isinstance(base_addr, int)
        assert isinstance(byte_length, int)
        assert isinstance(concrete_byte_count, int)
        assert isinstance(complete, bool)
        assert data_hex is None or isinstance(data_hex, str)
        return cls(
            base_addr=base_addr,
            byte_length=byte_length,
            concrete_byte_count=concrete_byte_count,
            complete=complete,
            data_hex=data_hex,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderStage:
    name: str
    base_addr: int
    entry_addr: int
    size: int
    materialized: bool
    reachable_instruction_count: int
    hardware_accesses: list[BootloaderMemoryAccess]
    loads: list[BootloaderLoad]
    disk_reads: list[BootloaderDiskRead]
    memory_copies: list[BootloaderMemoryCopy]
    read_setups: list[BootloaderReadSetup]
    decode_outputs: list[BootloaderDecodeOutput]
    decode_regions: list[BootloaderDecodeRegion]
    derived_regions: list[BootloaderDerivedRegion]
    handoffs: list[BootloaderHandoff]
    handoff_target: int | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderStage:
        name = payload["name"]
        base_addr = payload["base_addr"]
        entry_addr = payload["entry_addr"]
        size = payload["size"]
        materialized = payload["materialized"]
        reachable_instruction_count = payload["reachable_instruction_count"]
        hardware_accesses = _json_list(payload["hardware_accesses"])
        loads = _json_list(payload["loads"])
        disk_reads = _json_list(payload["disk_reads"])
        memory_copies = _json_list(payload["memory_copies"])
        read_setups = _json_list(payload["read_setups"])
        decode_outputs = _json_list(payload["decode_outputs"])
        decode_regions = _json_list(payload["decode_regions"])
        derived_regions = _json_list(payload["derived_regions"])
        handoffs = _json_list(payload["handoffs"])
        handoff_target = payload["handoff_target"]
        assert isinstance(name, str)
        assert isinstance(base_addr, int)
        assert isinstance(entry_addr, int)
        assert isinstance(size, int)
        assert isinstance(materialized, bool)
        assert isinstance(reachable_instruction_count, int)
        assert handoff_target is None or isinstance(handoff_target, int)
        return cls(
            name=name,
            base_addr=base_addr,
            entry_addr=entry_addr,
            size=size,
            materialized=materialized,
            reachable_instruction_count=reachable_instruction_count,
            hardware_accesses=[BootloaderMemoryAccess.from_dict(_json_object(item)) for item in hardware_accesses],
            loads=[BootloaderLoad.from_dict(_json_object(item)) for item in loads],
            disk_reads=[BootloaderDiskRead.from_dict(_json_object(item)) for item in disk_reads],
            memory_copies=[BootloaderMemoryCopy.from_dict(_json_object(item)) for item in memory_copies],
            read_setups=[BootloaderReadSetup.from_dict(_json_object(item)) for item in read_setups],
            decode_outputs=[BootloaderDecodeOutput.from_dict(_json_object(item)) for item in decode_outputs],
            decode_regions=[BootloaderDecodeRegion.from_dict(_json_object(item)) for item in decode_regions],
            derived_regions=[BootloaderDerivedRegion.from_dict(_json_object(item)) for item in derived_regions],
            handoffs=[BootloaderHandoff.from_dict(_json_object(item)) for item in handoffs],
            handoff_target=handoff_target,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderMemoryRegion:
    stage_name: str
    region_kind: str
    base_addr: int
    byte_length: int
    materialized: bool

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderMemoryRegion:
        stage_name = payload["stage_name"]
        region_kind = payload["region_kind"]
        base_addr = payload["base_addr"]
        byte_length = payload["byte_length"]
        materialized = payload["materialized"]
        assert isinstance(stage_name, str)
        assert isinstance(region_kind, str)
        assert isinstance(base_addr, int)
        assert isinstance(byte_length, int)
        assert isinstance(materialized, bool)
        return cls(
            stage_name=stage_name,
            region_kind=region_kind,
            base_addr=base_addr,
            byte_length=byte_length,
            materialized=materialized,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderTransfer:
    stage_name: str
    transfer_kind: str
    source_kind: str
    destination_addr: int | None
    byte_length: int | None
    source_addr: int | None = None
    disk_offset: int | None = None
    input_buffer_addr: int | None = None
    output_addr: int | None = None
    target_addr: int | None = None
    start_track: int | None = None
    end_track: int | None = None
    start_byte_offset: int | None = None
    checksum_gate_addr: int | None = None
    checksum_gate_kind: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderTransfer:
        stage_name = payload["stage_name"]
        transfer_kind = payload["transfer_kind"]
        source_kind = payload["source_kind"]
        destination_addr = payload["destination_addr"]
        byte_length = payload["byte_length"]
        source_addr = payload["source_addr"]
        disk_offset = payload["disk_offset"]
        input_buffer_addr = payload["input_buffer_addr"]
        output_addr = payload["output_addr"]
        target_addr = payload["target_addr"]
        start_track = payload["start_track"]
        end_track = payload["end_track"]
        start_byte_offset = payload["start_byte_offset"]
        checksum_gate_addr = payload["checksum_gate_addr"]
        checksum_gate_kind = payload["checksum_gate_kind"]
        assert isinstance(stage_name, str)
        assert isinstance(transfer_kind, str)
        assert isinstance(source_kind, str)
        assert destination_addr is None or isinstance(destination_addr, int)
        assert byte_length is None or isinstance(byte_length, int)
        assert source_addr is None or isinstance(source_addr, int)
        assert disk_offset is None or isinstance(disk_offset, int)
        assert input_buffer_addr is None or isinstance(input_buffer_addr, int)
        assert output_addr is None or isinstance(output_addr, int)
        assert target_addr is None or isinstance(target_addr, int)
        assert start_track is None or isinstance(start_track, int)
        assert end_track is None or isinstance(end_track, int)
        assert start_byte_offset is None or isinstance(start_byte_offset, int)
        assert checksum_gate_addr is None or isinstance(checksum_gate_addr, int)
        assert checksum_gate_kind is None or isinstance(checksum_gate_kind, str)
        return cls(
            stage_name=stage_name,
            transfer_kind=transfer_kind,
            source_kind=source_kind,
            destination_addr=destination_addr,
            byte_length=byte_length,
            source_addr=source_addr,
            disk_offset=disk_offset,
            input_buffer_addr=input_buffer_addr,
            output_addr=output_addr,
            target_addr=target_addr,
            start_track=start_track,
            end_track=end_track,
            start_byte_offset=start_byte_offset,
            checksum_gate_addr=checksum_gate_addr,
            checksum_gate_kind=checksum_gate_kind,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class BootloaderAnalysis:
    stages: list[BootloaderStage]
    memory_regions: list[BootloaderMemoryRegion]
    transfers: list[BootloaderTransfer]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootloaderAnalysis:
        stages = _json_list(payload["stages"])
        memory_regions = _json_list(payload["memory_regions"])
        transfers = _json_list(payload["transfers"])
        return cls(
            stages=[BootloaderStage.from_dict(_json_object(item)) for item in stages],
            memory_regions=[BootloaderMemoryRegion.from_dict(_json_object(item)) for item in memory_regions],
            transfers=[BootloaderTransfer.from_dict(_json_object(item)) for item in transfers],
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class NonDosInfo:
    description: str
    bootcode_present: bool
    dos_magic_without_filesystem: bool = False
    filesystem_parse_error: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> NonDosInfo:
        description = payload["description"]
        bootcode_present = payload["bootcode_present"]
        dos_magic_without_filesystem = payload["dos_magic_without_filesystem"]
        filesystem_parse_error = payload["filesystem_parse_error"]
        assert isinstance(description, str)
        assert isinstance(bootcode_present, bool)
        assert isinstance(dos_magic_without_filesystem, bool)
        assert filesystem_parse_error is None or isinstance(filesystem_parse_error, str)
        return cls(
            description=description,
            bootcode_present=bootcode_present,
            dos_magic_without_filesystem=dos_magic_without_filesystem,
            filesystem_parse_error=filesystem_parse_error,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class ImportedTarget:
    target_name: str
    target_path: str
    entry_path: str
    binary_path: str
    target_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ImportedTarget:
        target_name = payload["target_name"]
        target_path = payload["target_path"]
        entry_path = payload["entry_path"]
        binary_path = payload["binary_path"]
        target_type = payload["target_type"]
        assert isinstance(target_name, str)
        assert isinstance(target_path, str)
        assert isinstance(entry_path, str)
        assert isinstance(binary_path, str)
        assert isinstance(target_type, str)
        return cls(
            target_name=target_name,
            target_path=target_path,
            entry_path=entry_path,
            binary_path=binary_path,
            target_type=target_type,
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class AdfAnalysis:
    disk_info: DiskInfo
    boot_block: BootBlockInfo
    non_dos: NonDosInfo | None = None
    root_block: RootBlockInfo | None = None
    filesystem: FilesystemInfo | None = None
    files: list[DiskFileEntry] | None = None
    directories: list[DiskDirectoryEntry] | None = None
    bitmap: BitmapInfo | None = None
    block_usage: BlockUsageInfo | None = None
    track_analysis: TrackAnalysis | None = None
    trackloader_analysis: TrackloaderAnalysis | None = None
    bootloader_analysis: BootloaderAnalysis | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> AdfAnalysis:
        non_dos = payload.get("non_dos")
        root_block = payload.get("root_block")
        filesystem = payload.get("filesystem")
        files = payload.get("files")
        directories = payload.get("directories")
        bitmap = payload.get("bitmap")
        block_usage = payload.get("block_usage")
        track_analysis = payload.get("track_analysis")
        trackloader_analysis = payload.get("trackloader_analysis")
        bootloader_analysis = payload.get("bootloader_analysis")
        return cls(
            disk_info=DiskInfo.from_dict(_json_object(payload["disk_info"])),
            boot_block=BootBlockInfo.from_dict(_json_object(payload["boot_block"])),
            non_dos=None if non_dos is None else NonDosInfo.from_dict(_json_object(non_dos)),
            root_block=None if root_block is None else RootBlockInfo.from_dict(_json_object(root_block)),
            filesystem=None if filesystem is None else FilesystemInfo.from_dict(_json_object(filesystem)),
            files=None if files is None else [DiskFileEntry.from_dict(_json_object(item)) for item in _json_list(files)],
            directories=None if directories is None else [DiskDirectoryEntry.from_dict(_json_object(item)) for item in _json_list(directories)],
            bitmap=None if bitmap is None else BitmapInfo.from_dict(_json_object(bitmap)),
            block_usage=None if block_usage is None else BlockUsageInfo.from_dict(_json_object(block_usage)),
            track_analysis=None if track_analysis is None else TrackAnalysis.from_dict(_json_object(track_analysis)),
            trackloader_analysis=None if trackloader_analysis is None else TrackloaderAnalysis.from_dict(_json_object(trackloader_analysis)),
            bootloader_analysis=None if bootloader_analysis is None else BootloaderAnalysis.from_dict(_json_object(bootloader_analysis)),
        )

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


@dataclass(frozen=True, slots=True)
class DiskManifest:
    schema_version: int
    disk_id: str
    source_path: str
    source_sha256: str
    analysis: AdfAnalysis
    imported_targets: list[ImportedTarget]
    bootblock_target_name: str
    bootblock_target_path: str

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> DiskManifest:
        schema_version = payload["schema_version"]
        disk_id = payload["disk_id"]
        source_path = payload["source_path"]
        source_sha256 = payload["source_sha256"]
        bootblock_target_name = payload["bootblock_target_name"]
        bootblock_target_path = payload["bootblock_target_path"]
        imported_targets = _json_list(payload["imported_targets"])
        assert isinstance(schema_version, int)
        assert isinstance(disk_id, str)
        assert isinstance(source_path, str)
        assert isinstance(source_sha256, str)
        assert isinstance(bootblock_target_name, str)
        assert isinstance(bootblock_target_path, str)
        return cls(
            schema_version=schema_version,
            disk_id=disk_id,
            source_path=source_path,
            source_sha256=source_sha256,
            analysis=AdfAnalysis.from_dict(_json_object(payload["analysis"])),
            bootblock_target_name=bootblock_target_name,
            bootblock_target_path=bootblock_target_path,
            imported_targets=[ImportedTarget.from_dict(_json_object(item)) for item in imported_targets],
        )

    @classmethod
    def load(cls, path: Path) -> DiskManifest:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(_json_object(payload))

    def to_dict(self) -> dict[str, object]:
        return _as_json_dict(self)


type JsonDataclass = (
    ResidentInfo
    | LibraryInfo
    | FileContentInfo
    | DiskFileEntry
    | DiskDirectoryEntry
    | DiskInfo
    | BootBlockInfo
    | RootBlockInfo
    | FilesystemInfo
    | BitmapInfo
    | BlockUsageInfo
    | RawTrackSource
    | RawTrackSourceSpan
    | TrackInfo
    | TrackAnalysis
    | TrackSpan
    | TrackloaderAnalysis
    | BootloaderMemoryAccess
    | BootloaderLoad
    | BootloaderMemoryCopy
    | BootloaderReadSetup
    | BootloaderDecodeOutput
    | BootloaderDiskRead
    | BootloaderDecodeRegion
    | BootloaderDerivedRegion
    | BootloaderHandoff
    | BootloaderMemoryRegion
    | BootloaderStage
    | BootloaderTransfer
    | BootloaderAnalysis
    | NonDosInfo
    | ImportedTarget
    | AdfAnalysis
    | DiskManifest
)


def _as_json_dict(value: JsonDataclass) -> dict[str, object]:
    result = asdict(value)
    assert isinstance(result, dict)
    return result
