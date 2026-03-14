"""Amiga hunk binary format parser.

Parses both executable (HUNK_HEADER) and object (HUNK_UNIT) files.
All data is big-endian (Motorola byte order).
"""

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path


class HunkType(IntEnum):
    HUNK_UNIT = 0x3E7
    HUNK_NAME = 0x3E8
    HUNK_CODE = 0x3E9
    HUNK_DATA = 0x3EA
    HUNK_BSS = 0x3EB
    HUNK_RELOC32 = 0x3EC
    HUNK_RELOC16 = 0x3ED
    HUNK_RELOC8 = 0x3EE
    HUNK_EXT = 0x3EF
    HUNK_SYMBOL = 0x3F0
    HUNK_DEBUG = 0x3F1
    HUNK_END = 0x3F2
    HUNK_HEADER = 0x3F3
    HUNK_OVERLAY = 0x3F5
    HUNK_BREAK = 0x3F6
    HUNK_DREL32 = 0x3F7
    HUNK_DREL16 = 0x3F8
    HUNK_DREL8 = 0x3F9
    HUNK_LIB = 0x3FA
    HUNK_INDEX = 0x3FB
    HUNK_RELOC32SHORT = 0x3FC
    HUNK_RELRELOC32 = 0x3FD
    HUNK_ABSRELOC16 = 0x3FE


class MemType(IntEnum):
    ANY = 0
    CHIP = 1
    FAST = 2
    EXTENDED = 3


class ExtType(IntEnum):
    EXT_SYMB = 0
    EXT_DEF = 1
    EXT_ABS = 2
    EXT_RES = 3
    EXT_REF32 = 129
    EXT_COMMON = 130
    EXT_REF16 = 131
    EXT_REF8 = 132
    EXT_DEXT32 = 133
    EXT_DEXT16 = 134
    EXT_DEXT8 = 135
    EXT_RELREF32 = 136
    EXT_RELCOMMON = 137
    EXT_ABSREF16 = 138
    EXT_ABSREF8 = 139


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
    offsets: list[int]


@dataclass
class Reloc:
    reloc_type: int  # HunkType value
    target_hunk: int
    offsets: list[int]


@dataclass
class Hunk:
    index: int
    hunk_type: int  # HUNK_CODE, HUNK_DATA, or HUNK_BSS
    mem_type: int  # MemType value
    alloc_size: int  # in bytes
    data: bytes  # empty for BSS
    name: str = ""
    relocs: list[Reloc] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    ext_defs: list[ExtDef] = field(default_factory=list)
    ext_refs: list[ExtRef] = field(default_factory=list)
    debug_data: bytes = b""

    @property
    def type_name(self) -> str:
        names = {HunkType.HUNK_CODE: "CODE", HunkType.HUNK_DATA: "DATA",
                 HunkType.HUNK_BSS: "BSS"}
        return names.get(self.hunk_type, f"${self.hunk_type:03X}")

    @property
    def mem_name(self) -> str:
        names = {MemType.ANY: "", MemType.CHIP: "CHIP", MemType.FAST: "FAST"}
        return names.get(self.mem_type, "EXT")


class HunkParseError(Exception):
    pass


class HunkFile:
    """Parsed Amiga hunk file."""

    def __init__(self):
        self.file_type: int = 0  # HUNK_HEADER or HUNK_UNIT
        self.unit_name: str = ""
        self.hunks: list[Hunk] = []

    @property
    def is_executable(self) -> bool:
        return self.file_type == HunkType.HUNK_HEADER

    @property
    def is_object(self) -> bool:
        return self.file_type == HunkType.HUNK_UNIT


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
        return val

    def read_u16(self) -> int:
        if self.pos + 2 > len(self.data):
            raise HunkParseError(f"unexpected EOF at offset {self.pos}")
        val = struct.unpack_from(">H", self.data, self.pos)[0]
        self.pos += 2
        return val

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
        raw = self.read_bytes(num_longs * 4)
        # Strip NUL padding
        return raw.rstrip(b"\x00").decode("latin-1")

    def align4(self):
        """Align position to next 4-byte boundary."""
        rem = self.pos % 4
        if rem:
            self.pos += 4 - rem

    def peek_u32(self) -> int | None:
        if self.pos + 4 > len(self.data):
            return None
        return struct.unpack_from(">I", self.data, self.pos)[0]


def _parse_hunk_id(raw: int) -> int:
    """Extract hunk type ID (lower 29 bits)."""
    return raw & 0x1FFFFFFF


def _parse_mem_flags(raw: int) -> int:
    """Extract memory type from bits 30-31."""
    return (raw >> 30) & 3


def _parse_size_and_mem(raw: int, r: _Reader) -> tuple[int, int]:
    """Parse size longword, return (size_in_bytes, mem_type).

    If mem_type == EXTENDED (3), reads additional ULONG for extended attrs.
    """
    mem = _parse_mem_flags(raw)
    size_longs = raw & 0x3FFFFFFF
    if mem == MemType.EXTENDED:
        _ext_attrs = r.read_u32()  # read and discard extended attrs for now
    return size_longs * 4, mem


def _parse_reloc(r: _Reader, reloc_type: int) -> list[Reloc]:
    """Parse standard relocation block (ULONG offsets)."""
    relocs = []
    while True:
        num = r.read_u32()
        if num == 0:
            break
        target = r.read_u32()
        offsets = [r.read_u32() for _ in range(num)]
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
        offsets = [r.read_u16() for _ in range(num)]
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
        name = r.read_bytes(name_len * 4).rstrip(b"\x00").decode("latin-1")
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
        ext_type = (type_and_len >> 24) & 0xFF
        name_len = type_and_len & 0xFFFFFF
        name = r.read_bytes(name_len * 4).rstrip(b"\x00").decode("latin-1")

        if ext_type < 128:
            # Definition
            value = r.read_u32()
            defs.append(ExtDef(name=name, ext_type=ext_type, value=value))
        else:
            # Reference
            common_size = 0
            if ext_type in (ExtType.EXT_COMMON, ExtType.EXT_RELCOMMON):
                common_size = r.read_u32()
            ref_count = r.read_u32()
            offsets = [r.read_u32() for _ in range(ref_count)]
            refs.append(ExtRef(name=name, ext_type=ext_type,
                               common_size=common_size, offsets=offsets))
    return defs, refs


def _parse_debug(r: _Reader) -> bytes:
    """Parse HUNK_DEBUG block, return raw data."""
    num_longs = r.read_u32()
    return r.read_bytes(num_longs * 4)


def parse(data: bytes) -> HunkFile:
    """Parse an Amiga hunk file from raw bytes."""
    r = _Reader(data)
    hf = HunkFile()

    magic = r.read_u32()
    if magic == HunkType.HUNK_HEADER:
        hf.file_type = HunkType.HUNK_HEADER
        _parse_executable(r, hf)
    elif magic == HunkType.HUNK_UNIT:
        hf.file_type = HunkType.HUNK_UNIT
        _parse_object(r, hf)
    else:
        raise HunkParseError(f"unknown magic: ${magic:08X}")

    return hf


def _parse_executable(r: _Reader, hf: HunkFile):
    """Parse HUNK_HEADER executable."""
    # Skip resident library names
    while True:
        name = r.read_bstr()
        if not name:
            break

    table_size = r.read_u32()
    first_hunk = r.read_u32()
    last_hunk = r.read_u32()
    num_hunks = last_hunk - first_hunk + 1

    # Read hunk size table
    hunk_allocs = []
    for _ in range(num_hunks):
        raw = r.read_u32()
        size_bytes, mem = _parse_size_and_mem(raw, r)
        hunk_allocs.append((size_bytes, mem))

    # Read hunk contents
    for i in range(num_hunks):
        alloc_size, mem = hunk_allocs[i]
        hunk = _parse_hunk_block(r, i + first_hunk, alloc_size, mem)
        hf.hunks.append(hunk)


def _parse_object(r: _Reader, hf: HunkFile):
    """Parse HUNK_UNIT object file."""
    hf.unit_name = r.read_bstr()

    hunk_index = 0
    while r.remaining() >= 4:
        peek = r.peek_u32()
        if peek is None:
            break
        hunk_id = _parse_hunk_id(peek)

        if hunk_id == HunkType.HUNK_UNIT:
            # Another unit — stop (we only parse first unit)
            break
        elif hunk_id == HunkType.HUNK_NAME:
            r.read_u32()  # consume
            name = r.read_bstr()
            # Name applies to next hunk
            hunk = _parse_hunk_block(r, hunk_index, 0, MemType.ANY)
            hunk.name = name
            hf.hunks.append(hunk)
            hunk_index += 1
        elif hunk_id in (HunkType.HUNK_CODE, HunkType.HUNK_DATA, HunkType.HUNK_BSS):
            hunk = _parse_hunk_block(r, hunk_index, 0, MemType.ANY)
            hf.hunks.append(hunk)
            hunk_index += 1
        else:
            # Skip unknown
            r.read_u32()
            break


def _parse_hunk_block(r: _Reader, index: int, alloc_size: int, mem: int) -> Hunk:
    """Parse a single hunk block (CODE/DATA/BSS) and its associated sub-blocks."""
    raw_type = r.read_u32()
    hunk_id = _parse_hunk_id(raw_type)
    block_mem = _parse_mem_flags(raw_type)
    if block_mem != MemType.ANY:
        mem = block_mem

    if hunk_id == HunkType.HUNK_CODE or hunk_id == HunkType.HUNK_DATA:
        num_longs = r.read_u32()
        data = r.read_bytes(num_longs * 4)
        data_size = num_longs * 4
        if alloc_size == 0:
            alloc_size = data_size
    elif hunk_id == HunkType.HUNK_BSS:
        num_longs = r.read_u32()
        data = b""
        if alloc_size == 0:
            alloc_size = num_longs * 4
    else:
        raise HunkParseError(f"expected CODE/DATA/BSS, got ${hunk_id:03X} at offset {r.pos - 4}")

    hunk = Hunk(index=index, hunk_type=hunk_id, mem_type=mem,
                alloc_size=alloc_size, data=data)

    # Parse associated sub-blocks until HUNK_END
    while r.remaining() >= 4:
        sub_raw = r.peek_u32()
        if sub_raw is None:
            break
        sub_id = _parse_hunk_id(sub_raw)

        if sub_id == HunkType.HUNK_END:
            r.read_u32()  # consume
            break
        elif sub_id == HunkType.HUNK_BREAK:
            r.read_u32()  # consume
            break
        elif sub_id in (HunkType.HUNK_RELOC32, HunkType.HUNK_RELOC16,
                        HunkType.HUNK_RELOC8,
                        HunkType.HUNK_DREL16, HunkType.HUNK_DREL8,
                        HunkType.HUNK_RELRELOC32, HunkType.HUNK_ABSRELOC16):
            r.read_u32()  # consume type
            hunk.relocs.extend(_parse_reloc(r, sub_id))
        elif sub_id == HunkType.HUNK_DREL32:
            # 0x3F7: ambiguous — officially HUNK_DREL32 (32-bit format)
            # but vasm uses it for short relocs (16-bit format).
            # Detect by checking if the first 32-bit word is a plausible
            # count (small) or looks like two 16-bit values.
            r.read_u32()  # consume type
            saved = r.pos
            first_u32 = r.read_u32()
            r.pos = saved
            first_u16 = (first_u32 >> 16) & 0xFFFF
            if first_u32 == 0 or (first_u16 > 0 and first_u16 < 0x8000
                                  and first_u32 > hunk.alloc_size):
                # First 32-bit word is too large for a count but the
                # upper 16 bits are a plausible count → short format
                hunk.relocs.extend(_parse_reloc32short(r))
            else:
                hunk.relocs.extend(_parse_reloc(r, sub_id))
        elif sub_id == HunkType.HUNK_RELOC32SHORT:
            r.read_u32()  # consume type
            hunk.relocs.extend(_parse_reloc32short(r))
        elif sub_id == HunkType.HUNK_SYMBOL:
            r.read_u32()  # consume type
            hunk.symbols.extend(_parse_symbol(r))
        elif sub_id == HunkType.HUNK_EXT:
            r.read_u32()  # consume type
            defs, refs = _parse_ext(r)
            hunk.ext_defs.extend(defs)
            hunk.ext_refs.extend(refs)
        elif sub_id == HunkType.HUNK_DEBUG:
            r.read_u32()  # consume type
            hunk.debug_data = _parse_debug(r)
        elif sub_id in (HunkType.HUNK_CODE, HunkType.HUNK_DATA,
                        HunkType.HUNK_BSS, HunkType.HUNK_NAME):
            # Next hunk starts — no HUNK_END (some tools omit it)
            break
        else:
            # Unknown sub-block, skip it
            r.read_u32()
            if r.remaining() >= 4:
                skip_len = r.read_u32()
                r.read_bytes(skip_len * 4)

    return hunk


def parse_file(path: str | Path) -> HunkFile:
    """Parse an Amiga hunk file from disk."""
    data = Path(path).read_bytes()
    return parse(data)


def dump(hf: HunkFile):
    """Print summary of parsed hunk file."""
    kind = "Executable" if hf.is_executable else "Object"
    print(f"{kind}")
    if hf.unit_name:
        print(f"  Unit: {hf.unit_name}")
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
            print(f"        ext_ref: {er.name} ({tname}) × {len(er.offsets)}")

        if h.debug_data:
            print(f"        debug: {len(h.debug_data)} bytes")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hunk_file>")
        sys.exit(1)
    hf = parse_file(sys.argv[1])
    dump(hf)
