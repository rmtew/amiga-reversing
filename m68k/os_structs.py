"""KB-driven helpers for Amiga OS struct composition and field lookup."""

from __future__ import annotations

from m68k_kb.runtime_os import OsStruct


def resolve_struct_field(structs: dict[str, OsStruct], struct_name: str, offset: int,
                         active: frozenset[str] = frozenset()
                         ) -> dict[str, str] | None:
    if struct_name in active:
        raise ValueError(f"Cyclic struct embedding detected for {struct_name}")
    struct_def = structs[struct_name]
    if offset < 0 or offset >= struct_def.size:
        return None

    next_active = active | {struct_name}

    for field in struct_def.fields:
        field_offset = field.offset
        field_type = field.type
        if field_type == "LABEL":
            continue
        if field_type != "STRUCT" and field_offset == offset:
            return {"name": field.name, "struct": struct_name}

    if struct_def.base_struct is not None:
        base_struct = struct_def.base_struct
        base_offset = struct_def.base_offset
        if offset < base_offset:
            return resolve_struct_field(structs, base_struct, offset, next_active)

    for field in struct_def.fields:
        if field.type != "STRUCT":
            continue
        if field.struct is None:
            continue
        embedded_struct = field.struct
        embedded_size = field.size
        field_offset = field.offset
        if field_offset <= offset < field_offset + embedded_size:
            return resolve_struct_field(
                structs, embedded_struct, offset - field_offset, next_active)

    return None
