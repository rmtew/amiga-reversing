"""Amiga hunk binary format parser.

Parses both executable (HUNK_HEADER) and object (HUNK_UNIT) files.
All data is big-endian (Motorola byte order).

Type IDs and format metadata loaded from the generated runtime hunk KB,
derived from NDK 3.1 DOSHUNKS.H by parse_hunk_format.py.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import cast

from m68k_kb import runtime_hunk
from m68k_kb.runtime_types import (
    ExtTypeCategoryDef,
    HunkMeta,
    HunkTypeDef,
    MemoryTypeCodeDef,
)

_HUNK_KB = runtime_hunk
_HUNK_META = cast(HunkMeta, _HUNK_KB.META)
_HUNK_TYPES = cast(dict[str, HunkTypeDef], _HUNK_KB.HUNK_TYPES)
_EXT_TYPES = cast(dict[str, HunkTypeDef], _HUNK_KB.EXT_TYPES)
_MEMORY_TYPE_CODES = cast(dict[str, MemoryTypeCodeDef], _HUNK_KB.MEMORY_TYPE_CODES)
_EXT_TYPE_CATEGORIES = cast(ExtTypeCategoryDef, _HUNK_KB.EXT_TYPE_CATEGORIES)
_HUNK_CONTENT_FORMATS = runtime_hunk.HUNK_CONTENT_FORMATS


class HunkType(IntEnum):
    HUNK_UNIT = _HUNK_TYPES["HUNK_UNIT"]["id"]
    HUNK_NAME = _HUNK_TYPES["HUNK_NAME"]["id"]
    HUNK_CODE = _HUNK_TYPES["HUNK_CODE"]["id"]
    HUNK_DATA = _HUNK_TYPES["HUNK_DATA"]["id"]
    HUNK_BSS = _HUNK_TYPES["HUNK_BSS"]["id"]
    HUNK_RELOC32 = _HUNK_TYPES["HUNK_RELOC32"]["id"]
    HUNK_RELOC16 = _HUNK_TYPES["HUNK_RELOC16"]["id"]
    HUNK_RELOC8 = _HUNK_TYPES["HUNK_RELOC8"]["id"]
    HUNK_EXT = _HUNK_TYPES["HUNK_EXT"]["id"]
    HUNK_SYMBOL = _HUNK_TYPES["HUNK_SYMBOL"]["id"]
    HUNK_DEBUG = _HUNK_TYPES["HUNK_DEBUG"]["id"]
    HUNK_END = _HUNK_TYPES["HUNK_END"]["id"]
    HUNK_HEADER = _HUNK_TYPES["HUNK_HEADER"]["id"]
    HUNK_OVERLAY = _HUNK_TYPES["HUNK_OVERLAY"]["id"]
    HUNK_BREAK = _HUNK_TYPES["HUNK_BREAK"]["id"]
    HUNK_DREL32 = _HUNK_TYPES["HUNK_DREL32"]["id"]
    HUNK_DREL16 = _HUNK_TYPES["HUNK_DREL16"]["id"]
    HUNK_DREL8 = _HUNK_TYPES["HUNK_DREL8"]["id"]
    HUNK_LIB = _HUNK_TYPES["HUNK_LIB"]["id"]
    HUNK_INDEX = _HUNK_TYPES["HUNK_INDEX"]["id"]
    HUNK_RELOC32SHORT = _HUNK_TYPES["HUNK_RELOC32SHORT"]["id"]
    HUNK_RELRELOC32 = _HUNK_TYPES["HUNK_RELRELOC32"]["id"]
    HUNK_ABSRELOC16 = _HUNK_TYPES["HUNK_ABSRELOC16"]["id"]


class ExtType(IntEnum):
    EXT_SYMB = _EXT_TYPES["EXT_SYMB"]["id"]
    EXT_DEF = _EXT_TYPES["EXT_DEF"]["id"]
    EXT_ABS = _EXT_TYPES["EXT_ABS"]["id"]
    EXT_RES = _EXT_TYPES["EXT_RES"]["id"]
    EXT_REF32 = _EXT_TYPES["EXT_REF32"]["id"]
    EXT_COMMON = _EXT_TYPES["EXT_COMMON"]["id"]
    EXT_REF16 = _EXT_TYPES["EXT_REF16"]["id"]
    EXT_REF8 = _EXT_TYPES["EXT_REF8"]["id"]
    EXT_DEXT32 = _EXT_TYPES["EXT_DEXT32"]["id"]
    EXT_DEXT16 = _EXT_TYPES["EXT_DEXT16"]["id"]
    EXT_DEXT8 = _EXT_TYPES["EXT_DEXT8"]["id"]
    EXT_RELREF32 = _EXT_TYPES["EXT_RELREF32"]["id"]
    EXT_RELCOMMON = _EXT_TYPES["EXT_RELCOMMON"]["id"]
    EXT_ABSREF16 = _EXT_TYPES["EXT_ABSREF16"]["id"]
    EXT_ABSREF8 = _EXT_TYPES["EXT_ABSREF8"]["id"]


class MemType(IntEnum):
    ANY = int(next(key for key, value in _MEMORY_TYPE_CODES.items() if value["name"] == "ANY"))
    CHIP = int(next(key for key, value in _MEMORY_TYPE_CODES.items() if value["name"] == "CHIP"))
    FAST = int(next(key for key, value in _MEMORY_TYPE_CODES.items() if value["name"] == "FAST"))
    EXTENDED = int(next(key for key, value in _MEMORY_TYPE_CODES.items() if value["name"] == "EXTENDED"))

# All constants derived from KB - no hardcoded values.
_HUNK_TYPE_ID_MASK = _HUNK_META["hunk_type_id_mask"]
_SIZE_LONGS_MASK = _HUNK_META["size_longs_mask"]
_MEM_FLAGS_SHIFT = _HUNK_META["mem_flags_shift"]
_LONGWORD_BYTES = _HUNK_META["longword_bytes"]
_EXT_BOUNDARY = _EXT_TYPE_CATEGORIES["boundary"]

_HUNK_UNIT = int(HunkType.HUNK_UNIT)
_HUNK_NAME = int(HunkType.HUNK_NAME)
_HUNK_CODE = int(HunkType.HUNK_CODE)
_HUNK_DATA = int(HunkType.HUNK_DATA)
_HUNK_BSS = int(HunkType.HUNK_BSS)
_HUNK_RELOC32 = int(HunkType.HUNK_RELOC32)
_HUNK_RELOC16 = int(HunkType.HUNK_RELOC16)
_HUNK_RELOC8 = int(HunkType.HUNK_RELOC8)
_HUNK_EXT = int(HunkType.HUNK_EXT)
_HUNK_SYMBOL = int(HunkType.HUNK_SYMBOL)
_HUNK_DEBUG = int(HunkType.HUNK_DEBUG)
_HUNK_END = int(HunkType.HUNK_END)
_HUNK_HEADER = int(HunkType.HUNK_HEADER)
_HUNK_BREAK = int(HunkType.HUNK_BREAK)
_HUNK_DREL32 = int(HunkType.HUNK_DREL32)
_HUNK_DREL16 = int(HunkType.HUNK_DREL16)
_HUNK_DREL8 = int(HunkType.HUNK_DREL8)
_HUNK_RELOC32SHORT = int(HunkType.HUNK_RELOC32SHORT)
_HUNK_RELRELOC32 = int(HunkType.HUNK_RELRELOC32)
_HUNK_ABSRELOC16 = int(HunkType.HUNK_ABSRELOC16)
_HUNKEXE_SUPPORTED_RELOCATION_TYPES = frozenset(
    runtime_hunk.HUNKEXE_SUPPORTED_RELOCATION_TYPES
)

_MEM_ANY = int(MemType.ANY)
_MEM_CHIP = int(MemType.CHIP)
_MEM_FAST = int(MemType.FAST)
_MEM_EXTENDED = int(MemType.EXTENDED)

# Reverse lookup: ext type ID -> KB name (for has_common_size etc.)
_ext_id_to_name = {
    v["id"]: k
    for k, v in _EXT_TYPES.items()
    if "id" in v
}


@dataclass
class Symbol:
    name: str
    value: int


@dataclass
class ExtDef:
    name: str
    ext_type: int
    value: int


@dataclass
class ExtRef:
    name: str
    ext_type: int
    common_size: int  # 0 for non-common
    offsets: tuple[int, ...]


@dataclass
class Reloc:
    reloc_type: HunkType
    target_hunk: int
    offsets: tuple[int, ...]


@dataclass
class Hunk:
    index: int
    hunk_type: int  # HUNK_CODE, HUNK_DATA, or HUNK_BSS
    mem_type: int  # MemType value
    alloc_size: int  # in bytes
    data: bytes  # empty for BSS
    stored_size: int = 0
    mem_attrs: int | None = None  # extended exec memory attrs when mem_type == EXTENDED
    name: str = ""
    container_offset_longs: int | None = None
    relocs: list[Reloc] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    ext_defs: list[ExtDef] = field(default_factory=list)
    ext_refs: list[ExtRef] = field(default_factory=list)
    debug_data: bytes = b""
    debug_line: HunkDebugLineInfo | None = None

    def __post_init__(self) -> None:
        if self.stored_size == 0:
            self.stored_size = len(self.data)
        assert self.stored_size == len(self.data), (
            f"Hunk #{self.index} stored_size mismatch: {self.stored_size} != {len(self.data)}"
        )
        assert self.alloc_size >= self.stored_size, (
            f"Hunk #{self.index} alloc_size {self.alloc_size} < stored_size {self.stored_size}"
        )

    @property
    def type_name(self) -> str:
        names = {_HUNK_CODE: "CODE", _HUNK_DATA: "DATA", _HUNK_BSS: "BSS"}
        return names.get(self.hunk_type, f"${self.hunk_type:03X}")

    @property
    def mem_name(self) -> str:
        names = {_MEM_ANY: "", _MEM_CHIP: "CHIP", _MEM_FAST: "FAST"}
        return names.get(self.mem_type, "EXT")


@dataclass
class HunkUnit:
    name: str
    hunks: list[Hunk] = field(default_factory=list)


@dataclass(frozen=True)
class HunkIndexDefinition:
    name_offset: int
    value_low16: int
    abs_value_hi8: int
    abs_value_sign_and_type: int


@dataclass(frozen=True)
class HunkIndexHunkEntry:
    name_offset: int
    mem_type: int
    hunk_type: int
    ref_name_offsets: tuple[int, ...]
    definitions: tuple[HunkIndexDefinition, ...]


@dataclass(frozen=True)
class HunkIndexUnit:
    name_offset: int
    first_hunk_long_offset: int
    hunk_entries: tuple[HunkIndexHunkEntry, ...]


@dataclass(frozen=True)
class HunkIndexBlock:
    length_longs: int
    string_table_size_bytes: int
    string_table: bytes
    units: tuple[HunkIndexUnit, ...]


@dataclass
class HunkLibraryBlock:
    length_longs: int
    hunks: list[Hunk] = field(default_factory=list)
    index: HunkIndexBlock | None = None


@dataclass(frozen=True)
class HunkDebugLineEntry:
    line: int
    offset: int


@dataclass(frozen=True)
class HunkDebugLineInfo:
    base_offset: int
    filename: str
    entries: tuple[HunkDebugLineEntry, ...]


class HunkParseError(Exception):
    pass


class HunkFile:
    """Parsed Amiga hunk file."""

    def __init__(self) -> None:
        self.file_type: int = 0  # HUNK_HEADER, HUNK_UNIT, or HUNK_LIB
        self.units: list[HunkUnit] = []
        self._exec_hunks: list[Hunk] = []
        self.library_blocks: list[HunkLibraryBlock] = []

    @property
    def is_executable(self) -> bool:
        return self.file_type == _HUNK_HEADER

    @property
    def is_object(self) -> bool:
        return self.file_type == _HUNK_UNIT

    @property
    def is_library(self) -> bool:
        return self.file_type == int(HunkType.HUNK_LIB)

    @property
    def unit_name(self) -> str:
        if not self.units:
            return ""
        assert len(self.units) == 1, (
            f"unit_name is ambiguous for multi-unit object file: {len(self.units)} units"
        )
        return self.units[0].name

    @property
    def hunks(self) -> list[Hunk]:
        if self.is_executable:
            return self._exec_hunks
        if self.is_library:
            library_hunks: list[Hunk] = []
            for block in self.library_blocks:
                library_hunks.extend(block.hunks)
            return library_hunks
        object_hunks: list[Hunk] = []
        for unit in self.units:
            object_hunks.extend(unit.hunks)
        return object_hunks

    @hunks.setter
    def hunks(self, value: list[Hunk]) -> None:
        if self.is_library:
            self.library_blocks = [HunkLibraryBlock(length_longs=0, hunks=value)]
        elif self.is_object:
            self.units = [HunkUnit(name="", hunks=value)]
        else:
            self._exec_hunks = value


class _Reader:
    """Binary reader for big-endian hunk data."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def remaining(self) -> int:
        return len(self.data) - self.pos

    def read_u32(self) -> int:
        if self.pos + 4 > len(self.data):
            raise HunkParseError(f"unexpected EOF at offset {self.pos}")
        val = struct.unpack_from(">I", self.data, self.pos)[0]
        self.pos += 4
        return cast(int, val)

    def read_u16(self) -> int:
        if self.pos + 2 > len(self.data):
            raise HunkParseError(f"unexpected EOF at offset {self.pos}")
        val = struct.unpack_from(">H", self.data, self.pos)[0]
        self.pos += 2
        return cast(int, val)

    def read_bytes(self, n: int) -> bytes:
        if self.pos + n > len(self.data):
            raise HunkParseError(f"unexpected EOF at offset {self.pos}, need {n} bytes")
        val = self.data[self.pos:self.pos + n]
        self.pos += n
        return val

    def read_bstr(self) -> str:
        """Read longword-aligned string (BSTR format)."""
        num_longs = self.read_u32()
        if num_longs == 0:
            return ""
        raw = self.read_bytes(num_longs * _LONGWORD_BYTES)
        # Strip NUL padding
        return raw.rstrip(b"\x00").decode("latin-1")

    def align4(self) -> None:
        """Align position to next 4-byte boundary."""
        rem = self.pos % 4
        if rem:
            self.pos += 4 - rem

    def peek_u32(self) -> int | None:
        if self.pos + 4 > len(self.data):
            return None
        return cast(int, struct.unpack_from(">I", self.data, self.pos)[0])


def _parse_hunk_id(raw: int) -> int:
    """Extract hunk type ID, masking off flag bits.

    Mask from KB: strips ADVISORY (bit 29), CHIP (bit 30), FAST (bit 31).
    """
    return int(raw & int(_HUNK_TYPE_ID_MASK))


def _parse_mem_flags(raw: int) -> int:
    """Extract memory type code from flag bits.

    Shift and width from KB memory_flags bit positions.
    """
    return int((raw >> int(_MEM_FLAGS_SHIFT)) & (len(_HUNK_KB.MEMORY_TYPE_CODES) - 1))


def _parse_size_and_mem(raw: int, r: _Reader) -> tuple[int, int, int | None]:
    """Parse size longword, return (size_in_bytes, mem_type).

    If mem_type == EXTENDED, reads additional ULONG for extended attrs.
    Masks and multiplier from KB.
    """
    mem = _parse_mem_flags(raw)
    size_longs = raw & _SIZE_LONGS_MASK
    mem_attrs: int | None = None
    if mem == _MEM_EXTENDED:
        mem_attrs = r.read_u32()
    return size_longs * _LONGWORD_BYTES, mem, mem_attrs


def _parse_reloc(r: _Reader, reloc_type: HunkType) -> list[Reloc]:
    """Parse standard relocation block (ULONG offsets)."""
    relocs = []
    while True:
        num = r.read_u32()
        if num == 0:
            break
        target = r.read_u32()
        offsets = tuple(r.read_u32() for _ in range(num))
        relocs.append(Reloc(reloc_type=reloc_type, target_hunk=target, offsets=offsets))
    return relocs


def _parse_reloc32short(r: _Reader) -> list[Reloc]:
    """Parse compact relocation block (UWORD offsets)."""
    relocs = []
    while True:
        num = r.read_u16()
        if num == 0:
            break
        target = r.read_u16()
        offsets = tuple(r.read_u16() for _ in range(num))
        relocs.append(Reloc(reloc_type=HunkType.HUNK_RELOC32SHORT,
                            target_hunk=target, offsets=offsets))
    # Align to longword after 16-bit data
    r.align4()
    return relocs


def _parse_symbol(r: _Reader) -> list[Symbol]:
    """Parse HUNK_SYMBOL block."""
    symbols = []
    while True:
        name_len = r.read_u32()
        if name_len == 0:
            break
        name = r.read_bytes(name_len * _LONGWORD_BYTES).rstrip(b"\x00").decode("latin-1")
        value = r.read_u32()
        symbols.append(Symbol(name=name, value=value))
    return symbols


def _parse_ext(r: _Reader) -> tuple[list[ExtDef], list[ExtRef]]:
    """Parse HUNK_EXT block."""
    defs = []
    refs = []
    while True:
        type_and_len = r.read_u32()
        if type_and_len == 0:
            break
        _ext_pack = cast(dict[str, int], _HUNK_META["ext_type_and_len_packing"])
        ext_type = (type_and_len >> _ext_pack["name_len_width"]) & \
            ((1 << _ext_pack["type_width"]) - 1)
        name_len = type_and_len & ((1 << _ext_pack["name_len_width"]) - 1)
        name = r.read_bytes(name_len * _LONGWORD_BYTES).rstrip(b"\x00").decode("latin-1")

        if ext_type < _EXT_BOUNDARY:
            # Definition
            value = r.read_u32()
            defs.append(ExtDef(name=name, ext_type=ext_type, value=value))
        else:
            # Reference - check KB for common_size field
            common_size = 0
            ext_name = _ext_id_to_name.get(ext_type)
            if ext_name and _EXT_TYPES.get(ext_name, {}).get("has_common_size"):
                common_size = r.read_u32()
            ref_count = r.read_u32()
            offsets = tuple(r.read_u32() for _ in range(ref_count))
            refs.append(ExtRef(name=name, ext_type=ext_type,
                               common_size=common_size, offsets=offsets))
    return defs, refs


def _parse_debug(r: _Reader) -> bytes:
    """Parse HUNK_DEBUG block, return raw data."""
    num_longs = r.read_u32()
    return r.read_bytes(num_longs * _LONGWORD_BYTES)


def _parse_debug_line(raw: bytes) -> HunkDebugLineInfo | None:
    debug_spec = _HUNK_CONTENT_FORMATS.get("HUNK_DEBUG")
    assert isinstance(debug_spec, dict), "HUNK_DEBUG spec missing from runtime hunk KB"
    sub_formats = debug_spec.get("sub_formats")
    assert isinstance(sub_formats, dict), "HUNK_DEBUG sub_formats missing from runtime hunk KB"
    line_spec = sub_formats.get("LINE")
    assert isinstance(line_spec, dict), "HUNK_DEBUG.LINE spec missing from runtime hunk KB"
    magic = int(line_spec["magic"])
    if len(raw) < 12:
        return None
    reader = _Reader(raw)
    base_offset = reader.read_u32()
    if reader.read_u32() != magic:
        return None
    filename = reader.read_bstr()
    entries: list[HunkDebugLineEntry] = []
    while reader.remaining() > 0:
        assert reader.remaining() % 8 == 0, (
            f"HUNK_DEBUG LINE payload has trailing {reader.remaining()} bytes"
        )
        entries.append(
            HunkDebugLineEntry(
                line=reader.read_u32(),
                offset=reader.read_u32(),
            )
        )
    return HunkDebugLineInfo(
        base_offset=base_offset,
        filename=filename,
        entries=tuple(entries),
    )


def parse(data: bytes) -> HunkFile:
    """Parse an Amiga hunk file from raw bytes."""
    r = _Reader(data)
    hf = HunkFile()

    magic = r.read_u32()
    if magic == _HUNK_HEADER:
        hf.file_type = _HUNK_HEADER
        _parse_executable(r, hf)
    elif magic == _HUNK_UNIT:
        hf.file_type = _HUNK_UNIT
        _parse_object(r, hf)
    elif magic == int(HunkType.HUNK_LIB):
        hf.file_type = int(HunkType.HUNK_LIB)
        _parse_library(r, hf)
    else:
        raise HunkParseError(f"unknown magic: ${magic:08X}")

    return hf


def _parse_executable(r: _Reader, hf: HunkFile) -> None:
    """Parse HUNK_HEADER executable."""
    # Skip resident library names
    while True:
        name = r.read_bstr()
        if not name:
            break

    _ = r.read_u32()
    first_hunk = r.read_u32()
    last_hunk = r.read_u32()
    num_hunks = last_hunk - first_hunk + 1

    # Read hunk size table
    hunk_allocs = []
    for _ in range(num_hunks):
        raw = r.read_u32()
        size_bytes, mem, mem_attrs = _parse_size_and_mem(raw, r)
        hunk_allocs.append((size_bytes, mem, mem_attrs))

    # Read hunk contents
    for i in range(num_hunks):
        alloc_size, mem, mem_attrs = hunk_allocs[i]
        hunk = _parse_hunk_block(r, i + first_hunk, alloc_size, mem,
                                mem_attrs=mem_attrs, is_executable=True)
        hf._exec_hunks.append(hunk)


def _parse_object(r: _Reader, hf: HunkFile) -> None:
    """Parse one or more HUNK_UNIT object units."""
    while True:
        unit_name = r.read_bstr()
        unit = HunkUnit(name=unit_name)
        _parse_object_unit_body(r, unit)
        hf.units.append(unit)
        if r.remaining() < 4:
            break
        peek = r.peek_u32()
        assert peek is not None
        next_id = _parse_hunk_id(peek)
        if next_id != _HUNK_UNIT:
            raise HunkParseError(
                f"unexpected top-level hunk ${next_id:03X} after object unit '{unit_name}'"
            )
        r.read_u32()  # consume next HUNK_UNIT marker and continue


def _parse_object_unit_body(r: _Reader, unit: HunkUnit) -> None:
    hunk_index = len(unit.hunks)
    pending_name = ""
    while r.remaining() >= 4:
        peek = r.peek_u32()
        if peek is None:
            break
        hunk_id = _parse_hunk_id(peek)
        if hunk_id == _HUNK_UNIT:
            break
        if hunk_id == _HUNK_NAME:
            r.read_u32()
            assert pending_name == "", (
                f"duplicate HUNK_NAME before section in object unit '{unit.name}'"
            )
            pending_name = r.read_bstr()
            continue
        assert hunk_id in (_HUNK_CODE, _HUNK_DATA, _HUNK_BSS), (
            f"unexpected top-level object hunk ${hunk_id:03X} in unit '{unit.name}'"
        )
        hunk = _parse_hunk_block(r, hunk_index, 0, _MEM_ANY)
        if pending_name:
            hunk.name = pending_name
            pending_name = ""
        unit.hunks.append(hunk)
        hunk_index += 1
    assert pending_name == "", f"dangling HUNK_NAME in object unit '{unit.name}'"


def _parse_library(r: _Reader, hf: HunkFile) -> None:
    """Parse one or more HUNK_LIB/HUNK_INDEX library blocks."""
    while True:
        block = _parse_library_block(r)
        hf.library_blocks.append(block)
        if r.remaining() == 0:
            break
        next_id = r.read_u32()
        if next_id != int(HunkType.HUNK_LIB):
            raise HunkParseError(
                f"unexpected top-level hunk ${next_id:08X} after HUNK_INDEX"
            )


def _parse_library_block(r: _Reader) -> HunkLibraryBlock:
    length_longs = r.read_u32()
    payload = r.read_bytes(length_longs * _LONGWORD_BYTES)
    block = HunkLibraryBlock(length_longs=length_longs)
    _parse_library_payload_into_block(payload, block)
    index_magic = r.read_u32()
    if index_magic != int(HunkType.HUNK_INDEX):
        raise HunkParseError(
            f"HUNK_LIB must be followed by HUNK_INDEX, got ${index_magic:08X}"
        )
    block.index = _parse_library_index(r, block)
    return block


def _parse_library_payload_into_block(payload: bytes, block: HunkLibraryBlock) -> None:
    payload_reader = _Reader(payload)
    while payload_reader.remaining() >= 4:
        start_pos = payload_reader.pos
        hunk = _parse_hunk_block(payload_reader, len(block.hunks), 0, _MEM_ANY)
        hunk.container_offset_longs = (start_pos // _LONGWORD_BYTES) + 2
        assert hunk.name == "", "HUNK_LIB payload must not contain HUNK_NAME-derived names"
        block.hunks.append(hunk)
    assert payload_reader.remaining() == 0, (
        f"HUNK_LIB payload has trailing bytes: {payload_reader.remaining()}"
    )


def _parse_library_index(r: _Reader, block: HunkLibraryBlock) -> HunkIndexBlock:
    length_longs = r.read_u32()
    payload = r.read_bytes(length_longs * _LONGWORD_BYTES)
    idx_reader = _Reader(payload)
    string_table_size_bytes = idx_reader.read_u16()
    assert string_table_size_bytes % 2 == 0, (
        f"HUNK_INDEX string table size must be even, got {string_table_size_bytes}"
    )
    string_table = idx_reader.read_bytes(string_table_size_bytes)
    units: list[HunkIndexUnit] = []
    while idx_reader.remaining() > 0:
        unit_name_offset = idx_reader.read_u16()
        first_hunk_long_offset = idx_reader.read_u16()
        hunk_count = idx_reader.read_u16()
        hunk_entries: list[HunkIndexHunkEntry] = []
        for _ in range(hunk_count):
            hunk_name_offset = idx_reader.read_u16()
            mem_type_and_hunk_type = idx_reader.read_u16()
            mem_type = (mem_type_and_hunk_type >> 14) & 0x3
            hunk_type = mem_type_and_hunk_type & 0x3FFF
            ref_count = idx_reader.read_u16()
            ref_name_offsets = tuple(idx_reader.read_u16() for _ in range(ref_count))
            def_count = idx_reader.read_u16()
            definitions = tuple(
                HunkIndexDefinition(
                    name_offset=idx_reader.read_u16(),
                    value_low16=idx_reader.read_u16(),
                    abs_value_hi8=int(idx_reader.read_bytes(1)[0]),
                    abs_value_sign_and_type=int(idx_reader.read_bytes(1)[0]),
                )
                for _ in range(def_count)
            )
            hunk_entries.append(
                HunkIndexHunkEntry(
                    name_offset=hunk_name_offset,
                    mem_type=mem_type,
                    hunk_type=hunk_type,
                    ref_name_offsets=ref_name_offsets,
                    definitions=definitions,
                )
            )
        units.append(
            HunkIndexUnit(
                name_offset=unit_name_offset,
                first_hunk_long_offset=first_hunk_long_offset,
                hunk_entries=tuple(hunk_entries),
            )
        )
    index = HunkIndexBlock(
        length_longs=length_longs,
        string_table_size_bytes=string_table_size_bytes,
        string_table=string_table,
        units=tuple(units),
    )
    _validate_library_index(block, index)
    return index


def _validate_library_index(block: HunkLibraryBlock, index: HunkIndexBlock) -> None:
    offset_to_hunk = {
        hunk.container_offset_longs: hunk
        for hunk in block.hunks
        if hunk.container_offset_longs is not None
    }
    string_limit = len(index.string_table)

    def _check_string_offset(offset: int) -> None:
        assert 0 <= offset < string_limit, (
            f"HUNK_INDEX string offset {offset} out of range 0..{string_limit - 1}"
        )

    for unit in index.units:
        _check_string_offset(unit.name_offset)
        assert unit.first_hunk_long_offset in offset_to_hunk, (
            f"HUNK_INDEX first_hunk_long_offset {unit.first_hunk_long_offset} "
            "does not point to a hunk in the preceding HUNK_LIB"
        )
        start_idx = next(
            idx for idx, hunk in enumerate(block.hunks)
            if hunk.container_offset_longs == unit.first_hunk_long_offset
        )
        assert start_idx + len(unit.hunk_entries) <= len(block.hunks), (
            "HUNK_INDEX hunk_count exceeds available HUNK_LIB hunks"
        )
        for rel_idx, hunk_entry in enumerate(unit.hunk_entries):
            _check_string_offset(hunk_entry.name_offset)
            lib_hunk = block.hunks[start_idx + rel_idx]
            assert lib_hunk.hunk_type == hunk_entry.hunk_type, (
                f"HUNK_INDEX hunk type {hunk_entry.hunk_type} does not match "
                f"HUNK_LIB hunk type {lib_hunk.hunk_type}"
            )
            assert lib_hunk.mem_type == hunk_entry.mem_type, (
                f"HUNK_INDEX mem type {hunk_entry.mem_type} does not match "
                f"HUNK_LIB mem type {lib_hunk.mem_type}"
            )
            for ref_name_offset in hunk_entry.ref_name_offsets:
                _check_string_offset(ref_name_offset)
            for definition in hunk_entry.definitions:
                _check_string_offset(definition.name_offset)
                assert (definition.abs_value_sign_and_type & 0x80) == 0, (
                    "HUNK_INDEX definition marker bit must be 0"
                )


def _parse_hunk_block(r: _Reader, index: int, alloc_size: int, mem: int,
                      mem_attrs: int | None = None,
                      is_executable: bool = False) -> Hunk:
    """Parse a single hunk block (CODE/DATA/BSS) and its associated sub-blocks."""
    raw_type = r.read_u32()
    hunk_id = _parse_hunk_id(raw_type)
    block_mem = _parse_mem_flags(raw_type)
    if block_mem != _MEM_ANY:
        mem = block_mem
        if block_mem == _MEM_EXTENDED:
            mem_attrs = r.read_u32()

    if hunk_id in (_HUNK_CODE, _HUNK_DATA):
        num_longs = r.read_u32()
        data = r.read_bytes(num_longs * _LONGWORD_BYTES)
        data_size = num_longs * 4
        if alloc_size == 0:
            alloc_size = data_size
    elif hunk_id == _HUNK_BSS:
        num_longs = r.read_u32()
        data = b""
        if alloc_size == 0:
            alloc_size = num_longs * 4
    else:
        raise HunkParseError(f"expected CODE/DATA/BSS, got ${hunk_id:03X} at offset {r.pos - 4}")

    hunk = Hunk(
        index=index,
        hunk_type=hunk_id,
        mem_type=mem,
        mem_attrs=mem_attrs,
        alloc_size=alloc_size,
        data=data,
        stored_size=data_size if hunk_id in (_HUNK_CODE, _HUNK_DATA) else 0,
    )

    # Parse associated sub-blocks until HUNK_END
    while r.remaining() >= 4:
        sub_raw = r.peek_u32()
        if sub_raw is None:
            break
        sub_id = _parse_hunk_id(sub_raw)

        if sub_id == _HUNK_END:
            r.read_u32()  # consume
            break
        if sub_id == _HUNK_BREAK:
            r.read_u32()  # consume
            break
        if sub_id in (_HUNK_RELOC32, _HUNK_RELOC16,
                        _HUNK_RELOC8,
                        _HUNK_DREL16, _HUNK_DREL8,
                        _HUNK_RELRELOC32, _HUNK_ABSRELOC16):
            r.read_u32()  # consume type
            hunk.relocs.extend(_parse_reloc(r, HunkType(sub_id)))
        elif sub_id == _HUNK_DREL32:
            # DOSHUNKS.H: "V37 LoadSeg uses 1015 (HUNK_DREL32) by
            # mistake... HUNK_DREL32 is illegal in load files anyways."
            # In executables: 1015 = short relocs (16-bit format).
            # In object files: 1015 = data-relative relocs (32-bit).
            r.read_u32()  # consume type
            if is_executable:
                hunk.relocs.extend(_parse_reloc32short(r))
            else:
                hunk.relocs.extend(_parse_reloc(r, HunkType(sub_id)))
        elif sub_id == _HUNK_RELOC32SHORT:
            r.read_u32()  # consume type
            hunk.relocs.extend(_parse_reloc32short(r))
        elif sub_id == _HUNK_SYMBOL:
            r.read_u32()  # consume type
            hunk.symbols.extend(_parse_symbol(r))
        elif sub_id == _HUNK_EXT:
            r.read_u32()  # consume type
            defs, refs = _parse_ext(r)
            hunk.ext_defs.extend(defs)
            hunk.ext_refs.extend(refs)
        elif sub_id == _HUNK_DEBUG:
            r.read_u32()  # consume type
            hunk.debug_data = _parse_debug(r)
            hunk.debug_line = _parse_debug_line(hunk.debug_data)
        elif sub_id in (_HUNK_CODE, _HUNK_DATA,
                        _HUNK_BSS, _HUNK_NAME):
            # Next hunk starts - no HUNK_END (some tools omit it)
            break
        else:
            # Unknown sub-block, skip it
            r.read_u32()
            if r.remaining() >= 4:
                skip_len = r.read_u32()
                r.read_bytes(skip_len * _LONGWORD_BYTES)

    if is_executable:
        for reloc in hunk.relocs:
            reloc_name = HunkType(reloc.reloc_type).name
            if reloc_name not in _HUNKEXE_SUPPORTED_RELOCATION_TYPES:
                raise HunkParseError(
                    "Executable uses relocation type not supported by vasm hunkexe: "
                    f"{reloc_name} in hunk #{index}"
                )

    return hunk


def parse_file(path: str | Path) -> HunkFile:
    """Parse an Amiga hunk file from disk."""
    data = Path(path).read_bytes()
    return parse(data)


def dump(hf: HunkFile) -> None:
    """Print summary of parsed hunk file."""
    if hf.is_executable:
        kind = "Executable"
    elif hf.is_library:
        kind = "Library"
    else:
        kind = "Object"
    print(f"{kind}")
    if hf.is_object:
        print(f"  Units: {len(hf.units)}")
        for i, unit in enumerate(hf.units):
            print(f"    [{i}] {unit.name or '<unnamed>'}: {len(unit.hunks)} hunks")
    if hf.is_library:
        print(f"  Library blocks: {len(hf.library_blocks)}")
    print(f"  Hunks: {len(hf.hunks)}")
    print()

    for h in hf.hunks:
        mem_str = f" ({h.mem_name})" if h.mem_name else ""
        name_str = f" '{h.name}'" if h.name else ""
        print(f"  #{h.index:03d}  {h.type_name}{mem_str}{name_str}")
        print(f"        alloc={h.alloc_size} bytes, data={len(h.data)} bytes")

        for rel in h.relocs:
            rtype = HunkType(rel.reloc_type).name
            print(f"        {rtype} -> hunk #{rel.target_hunk}: "
                  f"{len(rel.offsets)} entries")

        for sym in h.symbols:
            print(f"        sym: {sym.name} = ${sym.value:08X}")

        for ed in h.ext_defs:
            tname = ExtType(ed.ext_type).name if ed.ext_type in ExtType._value2member_map_ else f"${ed.ext_type:02X}"
            print(f"        ext_def: {ed.name} ({tname}) = ${ed.value:08X}")

        for er in h.ext_refs:
            tname = ExtType(er.ext_type).name if er.ext_type in ExtType._value2member_map_ else f"${er.ext_type:02X}"
            print(f"        ext_ref: {er.name} ({tname}) x {len(er.offsets)}")

        if h.debug_data:
            print(f"        debug: {len(h.debug_data)} bytes")
        if h.debug_line is not None:
            print(
                f"        debug LINE: base=${h.debug_line.base_offset:08X} "
                f"file={h.debug_line.filename!r} entries={len(h.debug_line.entries)}"
            )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hunk_file>")
        sys.exit(1)
    hf = parse_file(sys.argv[1])
    dump(hf)
