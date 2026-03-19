import struct

from .decode_errors import DecodeError


def _xf(word: int, field_spec: tuple[int, int, int]) -> int:
    bit_hi, bit_lo, width = field_spec
    return (word >> bit_lo) & ((1 << width) - 1)


def _field_map(fields_def: list[dict]) -> dict[str, tuple[int, int, int]]:
    return {
        field["name"]: (
            field["bit_hi"],
            field["bit_lo"],
            field["bit_hi"] - field["bit_lo"] + 1,
        )
        for field in fields_def
    }


def parse_full_extension(ext: int, data: bytes, pos: int, meta: dict,
                         *, base_register: str | None,
                         pc_offset: int | None) -> tuple[dict[str, object], int]:
    fields = _field_map(meta["ea_full_ext_word"])
    iis = _xf(ext, fields["I/IS"])
    if iis == 4:
        raise DecodeError("Reserved full extension I/IS value")

    bd_kind = meta["ea_full_ext_bd_size"].get(str(_xf(ext, fields["BD SIZE"])))
    if bd_kind is None or bd_kind == "reserved":
        raise DecodeError("Reserved full extension BD SIZE value")

    new_pos = pos
    base_displacement = None
    if bd_kind == "word":
        if new_pos + 2 > len(data):
            raise DecodeError("Truncated full extension base displacement")
        base_displacement = struct.unpack_from(">h", data, new_pos)[0]
        new_pos += 2
    elif bd_kind == "long":
        if new_pos + 4 > len(data):
            raise DecodeError("Truncated full extension base displacement")
        base_displacement = struct.unpack_from(">i", data, new_pos)[0]
        new_pos += 4

    outer_kind = None
    if iis in (1, 5):
        outer_kind = "null"
    elif iis in (2, 6):
        outer_kind = "word"
    elif iis in (3, 7):
        outer_kind = "long"

    outer_displacement = None
    if outer_kind == "word":
        if new_pos + 2 > len(data):
            raise DecodeError("Truncated full extension outer displacement")
        outer_displacement = struct.unpack_from(">h", data, new_pos)[0]
        new_pos += 2
    elif outer_kind == "long":
        if new_pos + 4 > len(data):
            raise DecodeError("Truncated full extension outer displacement")
        outer_displacement = struct.unpack_from(">i", data, new_pos)[0]
        new_pos += 4

    base_suppressed = _xf(ext, fields["BS"]) == 1
    index_suppressed = _xf(ext, fields["IS"]) == 1
    index_is_addr = _xf(ext, fields["D/A"]) == 1
    index_reg = _xf(ext, fields["REGISTER"])
    index_size = "l" if _xf(ext, fields["W/L"]) == 1 else "w"
    index_scale = 1 << _xf(ext, fields["SCALE"])
    memory_indirect = iis != 0
    preindexed = iis in (1, 2, 3)
    postindexed = iis in (5, 6, 7)

    base_target = None
    if pc_offset is not None and not base_suppressed:
        base_target = pc_offset + meta["opword_bytes"] + (base_displacement or 0)

    return {
        "base_register": None if base_suppressed else base_register,
        "base_suppressed": base_suppressed,
        "base_displacement": base_displacement,
        "index_suppressed": index_suppressed,
        "index_register": None if index_suppressed else f"{'a' if index_is_addr else 'd'}{index_reg}",
        "index_reg_num": None if index_suppressed else index_reg,
        "index_is_addr": index_is_addr,
        "index_size": None if index_suppressed else index_size,
        "index_scale": None if index_suppressed else index_scale,
        "memory_indirect": memory_indirect,
        "preindexed": preindexed,
        "postindexed": postindexed,
        "outer_displacement": outer_displacement,
        "base_target": base_target,
    }, new_pos
