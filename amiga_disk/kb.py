from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _json_object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _json_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return value


def _field_map(fields: object) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for raw_field in _json_list(fields):
        field = _json_object(raw_field)
        name = field["name"]
        assert isinstance(name, str)
        result[name] = field
    return result


def _offset_value(raw_offset: object, block_size: int) -> int:
    assert isinstance(raw_offset, str)
    if raw_offset.startswith("offset "):
        raw_offset = raw_offset.removeprefix("offset ")
    if raw_offset.startswith("0x"):
        return int(raw_offset, 16)
    if raw_offset.startswith("BSIZE-"):
        return block_size - int(raw_offset.removeprefix("BSIZE-"), 10)
    raise AssertionError(f"Unsupported offset expression: {raw_offset}")


def _field_offset(fields: dict[str, dict[str, object]], field_name: str, block_size: int) -> int:
    return _offset_value(fields[field_name]["offset"], block_size)


def _field_size(fields: dict[str, dict[str, object]], field_name: str) -> int:
    size = fields[field_name]["size"]
    assert isinstance(size, int)
    return size


@dataclass(frozen=True, slots=True)
class AdfVariant:
    name: str
    size_bytes: int
    sectors_per_track: int
    total_sectors: int
    bytes_per_sector: int


@dataclass(frozen=True, slots=True)
class BootBlockLayout:
    magic_offset: int
    flags_offset: int
    checksum_offset: int
    rootblock_offset: int
    bootcode_offset: int
    boot_block_bytes: int


@dataclass(frozen=True, slots=True)
class EntryRegisterSeedKb:
    register: str
    kind: str
    note: str
    library_name: str | None = None
    struct_name: str | None = None
    context_name: str | None = None


@dataclass(frozen=True, slots=True)
class BootEntryKb:
    entry_point_offset: int
    registers: tuple[EntryRegisterSeedKb, ...]


@dataclass(frozen=True, slots=True)
class RootBlockLayout:
    type_offset: int
    hash_table_size_offset: int
    checksum_offset: int
    hash_table_offset: int
    bitmap_valid_flag_offset: int
    bitmap_pages_offset: int
    bitmap_pages_count: int
    root_date_offset: int
    volume_name_offset: int
    volume_name_max_length: int
    volume_date_offset: int
    creation_date_offset: int
    sec_type_offset: int


@dataclass(frozen=True, slots=True)
class FileHeaderLayout:
    type_offset: int
    high_seq_offset: int
    checksum_offset: int
    data_blocks_offset: int
    data_blocks_count: int
    protection_offset: int
    byte_size_offset: int
    comment_length_offset: int
    comment_max_length: int
    date_offset: int
    name_length_offset: int
    name_max_length: int
    hash_chain_offset: int
    parent_offset: int
    extension_offset: int
    sec_type_offset: int


@dataclass(frozen=True, slots=True)
class DataBlockLayout:
    data_size_offset: int
    data_offset: int


@dataclass(frozen=True, slots=True)
class ProtectionBit:
    char: str
    mask: int
    set_means_present: bool


@dataclass(frozen=True, slots=True)
class OpcodeSignature:
    word: int
    name: str


@dataclass(frozen=True, slots=True)
class NonDosAnalysisKb:
    boot_ascii_min_length: int
    track_ascii_min_length: int
    max_boot_ascii_strings: int
    max_track_ascii_strings: int
    high_entropy_threshold: float
    max_high_entropy_tracks: int
    max_repeated_track_groups: int
    code_track_min_pattern_hits: int
    m68k_code_word_signatures: tuple[OpcodeSignature, ...]


@dataclass(frozen=True, slots=True)
class CommandKb:
    value: int
    description: str


@dataclass(frozen=True, slots=True)
class ExecVectorKb:
    lvo: int
    description: str


@dataclass(frozen=True, slots=True)
class BootLoaderKb:
    load_address: int
    entry_offset: int
    dsklen_length_mask: int
    dsklen_length_unit_bytes: int
    cia_port_b_symbol: str
    initial_cylinder: int
    initial_head: int
    motor_bit_mask: int
    motor_active_low: bool
    drive_select_masks: dict[int, int]
    drive_select_active_low: bool
    side_bit_mask: int
    side_zero_head: int
    side_one_head: int
    direction_bit_mask: int
    direction_zero_means: str
    direction_one_means: str
    step_bit_mask: int
    step_active_low: bool
    step_pulse_edge: str
    trace_watch_input_prefix_bytes_when_output_unknown: int
    max_candidate_replay_stage_bytes: int
    max_candidate_replay_spans: int
    hardware_access_group_gap_bytes: int
    decode_output_backscan_instructions: int
    decode_output_add_base_backscan_instructions: int
    wait_loop_search_bytes: int
    buffer_scan_search_bytes: int
    iostdreq_offsets: dict[str, int]
    trackdisk_commands: dict[int, str]
    exec_vectors_by_lvo: dict[int, str]
    tracked_hardware_registers: dict[int, str]


@dataclass(frozen=True, slots=True)
class DiskKb:
    bytes_per_sector: int
    amiga_epoch: dt.datetime
    variants: dict[str, AdfVariant]
    dos_types: dict[int, tuple[str, str]]
    ffs_flag_mask: int
    block_types: dict[str, int]
    protection_bits: tuple[ProtectionBit, ...]
    non_dos_analysis: NonDosAnalysisKb
    boot_loader: BootLoaderKb
    root_hash_table_size: int
    boot_block: BootBlockLayout
    boot_entry: BootEntryKb
    root_block: RootBlockLayout
    file_header: FileHeaderLayout
    file_extension: FileHeaderLayout
    ofs_data_block: DataBlockLayout
    iff_group_ids: tuple[bytes, ...]
    hunk_header_magic: bytes


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _json_object(payload)


def load_disk_kb(project_root: Path = PROJECT_ROOT) -> DiskKb:
    disk_kb = _load_json(project_root / "knowledge" / "amiga_disk_formats.json")
    hunk_kb = _load_json(project_root / "knowledge" / "amiga_hunk_format.json")
    iff_kb = _load_json(project_root / "knowledge" / "amiga_iff_formats.json")

    adf_format = _json_object(disk_kb["adf_format"])
    variants_payload = _json_object(adf_format["variants"])
    variants: dict[str, AdfVariant] = {}
    bytes_per_sector: int | None = None
    for name, raw_variant in variants_payload.items():
        assert isinstance(name, str)
        payload = _json_object(raw_variant)
        size_bytes = payload["size_bytes"]
        sectors_per_track = payload["sectors_per_track"]
        total_sectors = payload["total_sectors"]
        variant_bytes_per_sector = payload["bytes_per_sector"]
        assert isinstance(size_bytes, int)
        assert isinstance(sectors_per_track, int)
        assert isinstance(total_sectors, int)
        assert isinstance(variant_bytes_per_sector, int)
        variant = AdfVariant(
            name=name,
            size_bytes=size_bytes,
            sectors_per_track=sectors_per_track,
            total_sectors=total_sectors,
            bytes_per_sector=variant_bytes_per_sector,
        )
        if bytes_per_sector is None:
            bytes_per_sector = variant.bytes_per_sector
        else:
            assert variant.bytes_per_sector == bytes_per_sector
        variants[name] = variant
    assert bytes_per_sector is not None

    boot_block_payload = _json_object(disk_kb["boot_block"])
    boot_block_fields = _field_map(boot_block_payload["fields"])
    boot_entry_payload = _json_object(boot_block_payload["boot_entry"])
    boot_entry_point = boot_entry_payload["entry_point"]
    boot_entry_registers_payload = _json_object(boot_entry_payload["registers"])
    assert isinstance(boot_entry_point, str)
    boot_entry_registers: list[EntryRegisterSeedKb] = []
    for register, raw_seed in boot_entry_registers_payload.items():
        assert isinstance(register, str)
        seed = _json_object(raw_seed)
        kind = seed["kind"]
        note = seed["note"]
        library_name = seed["library_name"]
        struct_name = seed["struct_name"]
        context_name = seed["context_name"]
        assert isinstance(kind, str)
        assert isinstance(note, str)
        assert library_name is None or isinstance(library_name, str)
        assert struct_name is None or isinstance(struct_name, str)
        assert context_name is None or isinstance(context_name, str)
        boot_entry_registers.append(
            EntryRegisterSeedKb(
                register=register,
                kind=kind,
                note=note,
                library_name=library_name,
                struct_name=struct_name,
                context_name=context_name,
            )
        )
    boot_layout = BootBlockLayout(
        magic_offset=_field_offset(boot_block_fields, "magic", bytes_per_sector),
        flags_offset=_field_offset(boot_block_fields, "flags", bytes_per_sector),
        checksum_offset=_field_offset(boot_block_fields, "checksum", bytes_per_sector),
        rootblock_offset=_field_offset(boot_block_fields, "rootblock", bytes_per_sector),
        bootcode_offset=_field_offset(boot_block_fields, "bootcode", bytes_per_sector),
        boot_block_bytes=bytes_per_sector * 2,
    )
    boot_entry = BootEntryKb(
        entry_point_offset=_offset_value(boot_entry_point, bytes_per_sector * 2),
        registers=tuple(boot_entry_registers),
    )
    flags_byte = _json_object(boot_block_payload["flags_byte"])
    combinations = _json_object(flags_byte["combinations"])
    dos_types: dict[int, tuple[str, str]] = {}
    for raw_value, description in combinations.items():
        assert isinstance(raw_value, str)
        assert isinstance(description, str)
        assert raw_value.startswith("0x")
        value = int(raw_value, 16)
        short_name = description.split(" - ", 1)[0].removeprefix("DOS\\")
        dos_types[value] = (short_name, description)
    ffs_flag_description = flags_byte["bit_0"]
    assert isinstance(ffs_flag_description, str)
    ffs_flag_mask = 1

    amigados = _json_object(disk_kb["amigados_filesystem"])
    date_format = _json_object(amigados["date_format"])
    base_date = date_format["base_date"]
    assert isinstance(base_date, str)
    amiga_epoch = dt.datetime.fromisoformat(base_date)

    block_types_payload = _json_object(amigados["block_types"])
    block_types: dict[str, int] = {}
    for name, block_type_value in block_types_payload.items():
        assert isinstance(name, str)
        assert isinstance(block_type_value, int)
        block_types[name] = block_type_value

    protection_payload = _json_object(amigados["protection_bits"])
    protection_bits_raw = _json_list(protection_payload["bits"])
    protection_bits: list[ProtectionBit] = []
    for raw_bit in protection_bits_raw:
        bit = _json_object(raw_bit)
        char = bit["char"]
        mask = bit["mask"]
        set_means_present = bit["set_means_present"]
        assert isinstance(char, str)
        assert len(char) == 1
        assert isinstance(mask, int)
        assert isinstance(set_means_present, bool)
        protection_bits.append(
            ProtectionBit(
                char=char,
                mask=mask,
                set_means_present=set_means_present,
            )
        )

    non_dos_payload = _json_object(disk_kb["non_dos_analysis"])
    boot_ascii_min_length = non_dos_payload["boot_ascii_min_length"]
    track_ascii_min_length = non_dos_payload["track_ascii_min_length"]
    max_boot_ascii_strings = non_dos_payload["max_boot_ascii_strings"]
    max_track_ascii_strings = non_dos_payload["max_track_ascii_strings"]
    high_entropy_threshold = non_dos_payload["high_entropy_threshold"]
    max_high_entropy_tracks = non_dos_payload["max_high_entropy_tracks"]
    max_repeated_track_groups = non_dos_payload["max_repeated_track_groups"]
    code_track_min_pattern_hits = non_dos_payload["code_track_min_pattern_hits"]
    assert isinstance(boot_ascii_min_length, int)
    assert isinstance(track_ascii_min_length, int)
    assert isinstance(max_boot_ascii_strings, int)
    assert isinstance(max_track_ascii_strings, int)
    assert isinstance(high_entropy_threshold, int | float)
    assert isinstance(max_high_entropy_tracks, int)
    assert isinstance(max_repeated_track_groups, int)
    assert isinstance(code_track_min_pattern_hits, int)
    raw_signatures = _json_list(non_dos_payload["m68k_code_word_signatures"])
    m68k_code_word_signatures: list[OpcodeSignature] = []
    for raw_signature in raw_signatures:
        signature = _json_object(raw_signature)
        raw_word = signature["word"]
        raw_name = signature["name"]
        assert isinstance(raw_word, str)
        assert raw_word.startswith("0x")
        assert isinstance(raw_name, str)
        m68k_code_word_signatures.append(OpcodeSignature(word=int(raw_word, 16), name=raw_name))

    boot_loader_payload = _json_object(disk_kb["boot_loader_analysis"])
    load_address = boot_loader_payload["load_address"]
    entry_offset = boot_loader_payload["entry_offset"]
    assert isinstance(load_address, str)
    assert isinstance(entry_offset, str)
    custom_disk_dma = _json_object(boot_loader_payload["custom_disk_dma"])
    dsklen_length_mask = custom_disk_dma["dsklen_length_mask"]
    dsklen_length_unit_bytes = custom_disk_dma["dsklen_length_unit_bytes"]
    assert isinstance(dsklen_length_mask, str)
    assert isinstance(dsklen_length_unit_bytes, int)
    floppy_control = _json_object(boot_loader_payload["floppy_control"])
    cia_port_b_symbol = floppy_control["cia_port_b_symbol"]
    initial_cylinder = floppy_control["initial_cylinder"]
    initial_head = floppy_control["initial_head"]
    motor_bit = _json_object(floppy_control["motor_bit"])
    drive_select_bits = _json_list(floppy_control["drive_select_bits"])
    side_bit = _json_object(floppy_control["side_bit"])
    direction_bit = _json_object(floppy_control["direction_bit"])
    step_bit = _json_object(floppy_control["step_bit"])
    assert isinstance(cia_port_b_symbol, str)
    assert isinstance(initial_cylinder, int)
    assert isinstance(initial_head, int)
    motor_bit_mask = motor_bit["mask"]
    motor_active_low = motor_bit["active_low"]
    assert isinstance(motor_bit_mask, str)
    assert isinstance(motor_active_low, bool)
    drive_select_masks: dict[int, int] = {}
    drive_select_active_low: bool | None = None
    for raw_drive_select in drive_select_bits:
        drive_select = _json_object(raw_drive_select)
        drive = drive_select["drive"]
        mask = drive_select["mask"]
        active_low = drive_select["active_low"]
        assert isinstance(drive, int)
        assert isinstance(mask, str)
        assert isinstance(active_low, bool)
        drive_select_masks[drive] = int(mask, 16)
        if drive_select_active_low is None:
            drive_select_active_low = active_low
        else:
            assert drive_select_active_low == active_low
    assert drive_select_active_low is not None
    side_bit_mask = side_bit["mask"]
    side_zero_head = side_bit["zero_means_head"]
    side_one_head = side_bit["one_means_head"]
    assert isinstance(side_bit_mask, str)
    assert isinstance(side_zero_head, int)
    assert isinstance(side_one_head, int)
    direction_bit_mask = direction_bit["mask"]
    direction_zero_means = direction_bit["zero_means"]
    direction_one_means = direction_bit["one_means"]
    assert isinstance(direction_bit_mask, str)
    assert isinstance(direction_zero_means, str)
    assert isinstance(direction_one_means, str)
    step_bit_mask = step_bit["mask"]
    step_active_low = step_bit["active_low"]
    step_pulse_edge = step_bit["pulse_edge"]
    trace_watch = _json_object(boot_loader_payload["trace_watch"])
    candidate_replay = _json_object(boot_loader_payload["candidate_replay"])
    inference_limits = _json_object(boot_loader_payload["inference_limits"])
    trace_watch_input_prefix_bytes_when_output_unknown = trace_watch["input_prefix_bytes_when_output_unknown"]
    max_candidate_replay_stage_bytes = candidate_replay["max_stage_bytes"]
    max_candidate_replay_spans = candidate_replay["max_candidate_spans"]
    hardware_access_group_gap_bytes = inference_limits["hardware_access_group_gap_bytes"]
    decode_output_backscan_instructions = inference_limits["decode_output_backscan_instructions"]
    decode_output_add_base_backscan_instructions = inference_limits["decode_output_add_base_backscan_instructions"]
    wait_loop_search_bytes = inference_limits["wait_loop_search_bytes"]
    buffer_scan_search_bytes = inference_limits["buffer_scan_search_bytes"]
    assert isinstance(step_bit_mask, str)
    assert isinstance(step_active_low, bool)
    assert isinstance(step_pulse_edge, str)
    assert isinstance(trace_watch_input_prefix_bytes_when_output_unknown, int)
    assert isinstance(max_candidate_replay_stage_bytes, int)
    assert isinstance(max_candidate_replay_spans, int)
    assert isinstance(hardware_access_group_gap_bytes, int)
    assert isinstance(decode_output_backscan_instructions, int)
    assert isinstance(decode_output_add_base_backscan_instructions, int)
    assert isinstance(wait_loop_search_bytes, int)
    assert isinstance(buffer_scan_search_bytes, int)
    iostdreq_fields = _json_object(boot_loader_payload["trackdisk_iostdreq_fields"])
    iostdreq_offsets: dict[str, int] = {}
    for field_name, raw_offset in iostdreq_fields.items():
        assert isinstance(field_name, str)
        assert isinstance(raw_offset, int)
        iostdreq_offsets[field_name] = raw_offset
    raw_trackdisk_commands = _json_object(boot_loader_payload["trackdisk_commands"])
    trackdisk_commands: dict[int, str] = {}
    for command_name, raw_command in raw_trackdisk_commands.items():
        assert isinstance(command_name, str)
        command = _json_object(raw_command)
        command_value_obj = command["value"]
        command_description_obj = command["description"]
        assert isinstance(command_value_obj, int)
        assert isinstance(command_description_obj, str)
        trackdisk_commands[command_value_obj] = command_name
    raw_exec_vectors = _json_object(boot_loader_payload["exec_library_vectors"])
    exec_vectors_by_lvo: dict[int, str] = {}
    for vector_name, raw_vector in raw_exec_vectors.items():
        assert isinstance(vector_name, str)
        vector = _json_object(raw_vector)
        raw_lvo = vector["lvo"]
        assert isinstance(raw_lvo, int)
        exec_vectors_by_lvo[raw_lvo] = vector_name

    root_block_payload = _json_object(amigados["root_block"])
    root_block_fields = _field_map(root_block_payload["fields"])
    root_hash_table_size = _field_size(root_block_fields, "hash_table[72]") // 4
    assert root_hash_table_size > 0
    root_layout = RootBlockLayout(
        type_offset=_field_offset(root_block_fields, "type", bytes_per_sector),
        hash_table_size_offset=_field_offset(root_block_fields, "ht_size", bytes_per_sector),
        checksum_offset=_field_offset(root_block_fields, "checksum", bytes_per_sector),
        hash_table_offset=_field_offset(root_block_fields, "hash_table[72]", bytes_per_sector),
        bitmap_valid_flag_offset=_field_offset(root_block_fields, "bm_flag", bytes_per_sector),
        bitmap_pages_offset=_field_offset(root_block_fields, "bm_pages[25]", bytes_per_sector),
        bitmap_pages_count=_field_size(root_block_fields, "bm_pages[25]") // 4,
        root_date_offset=_field_offset(root_block_fields, "r_date", bytes_per_sector),
        volume_name_offset=_field_offset(root_block_fields, "name_len", bytes_per_sector),
        volume_name_max_length=_field_size(root_block_fields, "diskname"),
        volume_date_offset=_field_offset(root_block_fields, "v_date", bytes_per_sector),
        creation_date_offset=_field_offset(root_block_fields, "c_date", bytes_per_sector),
        sec_type_offset=_field_offset(root_block_fields, "sec_type", bytes_per_sector),
    )

    file_header_payload = _json_object(amigados["file_header_block"])
    file_header_fields = _field_map(file_header_payload["fields"])
    file_header_layout = FileHeaderLayout(
        type_offset=_field_offset(file_header_fields, "type", bytes_per_sector),
        high_seq_offset=_field_offset(file_header_fields, "high_seq", bytes_per_sector),
        checksum_offset=_field_offset(file_header_fields, "checksum", bytes_per_sector),
        data_blocks_offset=_field_offset(file_header_fields, "data_blocks[72]", bytes_per_sector),
        data_blocks_count=_field_size(file_header_fields, "data_blocks[72]") // 4,
        protection_offset=_field_offset(file_header_fields, "protect", bytes_per_sector),
        byte_size_offset=_field_offset(file_header_fields, "byte_size", bytes_per_sector),
        comment_length_offset=_field_offset(file_header_fields, "comm_len", bytes_per_sector),
        comment_max_length=_field_size(file_header_fields, "comment"),
        date_offset=_field_offset(file_header_fields, "date", bytes_per_sector),
        name_length_offset=_field_offset(file_header_fields, "name_len", bytes_per_sector),
        name_max_length=_field_size(file_header_fields, "filename"),
        hash_chain_offset=_field_offset(file_header_fields, "hash_chain", bytes_per_sector),
        parent_offset=_field_offset(file_header_fields, "parent", bytes_per_sector),
        extension_offset=_field_offset(file_header_fields, "extension", bytes_per_sector),
        sec_type_offset=_field_offset(file_header_fields, "sec_type", bytes_per_sector),
    )

    extension_payload = _json_object(amigados["file_extension_block"])
    extension_fields = _field_map(extension_payload["fields"])
    extension_layout = FileHeaderLayout(
        type_offset=_field_offset(extension_fields, "type", bytes_per_sector),
        high_seq_offset=_field_offset(extension_fields, "high_seq", bytes_per_sector),
        checksum_offset=_field_offset(extension_fields, "checksum", bytes_per_sector),
        data_blocks_offset=_field_offset(extension_fields, "data_blocks[72]", bytes_per_sector),
        data_blocks_count=_field_size(extension_fields, "data_blocks[72]") // 4,
        protection_offset=file_header_layout.protection_offset,
        byte_size_offset=file_header_layout.byte_size_offset,
        comment_length_offset=file_header_layout.comment_length_offset,
        comment_max_length=file_header_layout.comment_max_length,
        date_offset=file_header_layout.date_offset,
        name_length_offset=file_header_layout.name_length_offset,
        name_max_length=file_header_layout.name_max_length,
        hash_chain_offset=file_header_layout.hash_chain_offset,
        parent_offset=_field_offset(extension_fields, "parent", bytes_per_sector),
        extension_offset=_field_offset(extension_fields, "extension", bytes_per_sector),
        sec_type_offset=_field_offset(extension_fields, "sec_type", bytes_per_sector),
    )

    ofs_data_payload = _json_object(amigados["data_block_ofs"])
    ofs_data_fields = _field_map(ofs_data_payload["fields"])
    ofs_data_layout = DataBlockLayout(
        data_size_offset=_field_offset(ofs_data_fields, "data_size", bytes_per_sector),
        data_offset=_field_offset(ofs_data_fields, "data", bytes_per_sector),
    )

    iff_container = _json_object(iff_kb["iff_container"])
    group_types = _json_object(iff_container["group_types"])
    iff_group_ids = tuple(group_id.encode("ascii") for group_id in group_types)
    assert iff_group_ids

    hw_symbols = _load_json(project_root / "knowledge" / "amiga_hw_symbols.json")
    raw_registers = _json_list(hw_symbols["registers"])
    tracked_symbols_raw = _json_list(boot_loader_payload["tracked_hardware_register_symbols"])
    assert all(isinstance(symbol, str) for symbol in tracked_symbols_raw)
    tracked_symbols = {cast(str, symbol).casefold() for symbol in tracked_symbols_raw}
    tracked_hardware_registers: dict[int, str] = {}
    for raw_register in raw_registers:
        register_payload = _json_object(raw_register)
        cpu_address = register_payload["cpu_address"]
        symbols = _json_list(register_payload["symbols"])
        assert isinstance(cpu_address, str)
        address = int(cpu_address, 16)
        assert all(isinstance(symbol, str) for symbol in symbols)
        symbol_names = [cast(str, symbol) for symbol in symbols]
        for symbol in symbol_names:
            if symbol.casefold() in tracked_symbols:
                tracked_hardware_registers[address] = symbol
    missing_tracked_symbols = tracked_symbols.difference(symbol.casefold() for symbol in tracked_hardware_registers.values())
    assert not missing_tracked_symbols

    hunk_types = _json_object(hunk_kb["hunk_types"])
    hunk_header = _json_object(hunk_types["HUNK_HEADER"])
    hunk_header_id = hunk_header["id"]
    assert isinstance(hunk_header_id, int)
    hunk_header_magic = hunk_header_id.to_bytes(4, byteorder="big")

    return DiskKb(
        bytes_per_sector=bytes_per_sector,
        amiga_epoch=amiga_epoch,
        variants=variants,
        dos_types=dos_types,
        ffs_flag_mask=ffs_flag_mask,
        block_types=block_types,
        protection_bits=tuple(protection_bits),
        non_dos_analysis=NonDosAnalysisKb(
            boot_ascii_min_length=boot_ascii_min_length,
            track_ascii_min_length=track_ascii_min_length,
            max_boot_ascii_strings=max_boot_ascii_strings,
            max_track_ascii_strings=max_track_ascii_strings,
            high_entropy_threshold=float(high_entropy_threshold),
            max_high_entropy_tracks=max_high_entropy_tracks,
            max_repeated_track_groups=max_repeated_track_groups,
            code_track_min_pattern_hits=code_track_min_pattern_hits,
            m68k_code_word_signatures=tuple(m68k_code_word_signatures),
        ),
        boot_loader=BootLoaderKb(
            load_address=int(load_address, 16),
            entry_offset=int(entry_offset, 16),
            dsklen_length_mask=int(dsklen_length_mask, 16),
            dsklen_length_unit_bytes=dsklen_length_unit_bytes,
            cia_port_b_symbol=cia_port_b_symbol,
            initial_cylinder=initial_cylinder,
            initial_head=initial_head,
            motor_bit_mask=int(motor_bit_mask, 16),
            motor_active_low=motor_active_low,
            drive_select_masks=drive_select_masks,
            drive_select_active_low=drive_select_active_low,
            side_bit_mask=int(side_bit_mask, 16),
            side_zero_head=side_zero_head,
            side_one_head=side_one_head,
            direction_bit_mask=int(direction_bit_mask, 16),
            direction_zero_means=direction_zero_means,
            direction_one_means=direction_one_means,
            step_bit_mask=int(step_bit_mask, 16),
            step_active_low=step_active_low,
            step_pulse_edge=step_pulse_edge,
            trace_watch_input_prefix_bytes_when_output_unknown=trace_watch_input_prefix_bytes_when_output_unknown,
            max_candidate_replay_stage_bytes=max_candidate_replay_stage_bytes,
            max_candidate_replay_spans=max_candidate_replay_spans,
            hardware_access_group_gap_bytes=hardware_access_group_gap_bytes,
            decode_output_backscan_instructions=decode_output_backscan_instructions,
            decode_output_add_base_backscan_instructions=decode_output_add_base_backscan_instructions,
            wait_loop_search_bytes=wait_loop_search_bytes,
            buffer_scan_search_bytes=buffer_scan_search_bytes,
            iostdreq_offsets=iostdreq_offsets,
            trackdisk_commands=trackdisk_commands,
            exec_vectors_by_lvo=exec_vectors_by_lvo,
            tracked_hardware_registers=tracked_hardware_registers,
        ),
        root_hash_table_size=root_hash_table_size,
        boot_block=boot_layout,
        boot_entry=boot_entry,
        root_block=root_layout,
        file_header=file_header_layout,
        file_extension=extension_layout,
        ofs_data_block=ofs_data_layout,
        iff_group_ids=iff_group_ids,
        hunk_header_magic=hunk_header_magic,
    )
