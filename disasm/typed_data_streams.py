from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from m68k.os_structs import resolve_struct_field


@dataclass(frozen=True, slots=True)
class TypedDataStreamCommand:
    start: int
    end: int
    opcode: int
    dest_offset: int
    unit_size: int
    count: int
    repeat: bool
    data_start: int
    data_end: int


@dataclass(frozen=True, slots=True)
class TypedDataStream:
    start: int
    end: int
    commands: tuple[TypedDataStreamCommand, ...]


def _lookup_stream_spec(
    os_kb: object,
    stream_name: str,
) -> Mapping[str, Any] | None:
    meta = getattr(os_kb, "META", None)
    if meta is None:
        return None
    stream_formats = getattr(meta, "typed_data_stream_formats", None)
    if stream_formats is None:
        return None
    spec = stream_formats.get(stream_name)
    if spec is None:
        return None
    return cast(Mapping[str, Any], spec)


def decode_typed_data_stream(
    code: bytes,
    start: int,
    spec: Mapping[str, Any],
) -> TypedDataStream | None:
    if not (0 <= start < len(code)):
        return None
    command_byte = spec["command_byte"]
    destination_modes = command_byte["destination_modes"]
    source_sizes = {int(key): value for key, value in command_byte["source_sizes"].items()}
    pos = start
    next_dest = 0
    commands: list[TypedDataStreamCommand] = []
    while pos < len(code):
        if pos % int(spec["alignment"]):
            pos += 1
            continue
        command_start = pos
        opcode = code[pos]
        pos += 1
        if opcode == int(spec["terminator_opcode"]):
            return TypedDataStream(
                start=start,
                end=pos,
                commands=tuple(commands),
            )
        dest_mode = (
            opcode >> int(command_byte["destination_shift"])
        ) & int(command_byte["destination_mask"])
        source_mode = (
            opcode >> int(command_byte["size_shift"])
        ) & int(command_byte["size_mask"])
        count = (opcode & int(command_byte["count_mask"])) + 1
        if source_mode == int(command_byte["invalid_size_value"]):
            return None
        if dest_mode == int(destination_modes["next_count"]):
            dest_offset = next_dest
            repeat = False
        elif dest_mode == int(destination_modes["next_repeat"]):
            dest_offset = next_dest
            repeat = True
        elif dest_mode == int(destination_modes["byte_offset_count"]):
            if pos >= len(code):
                return None
            dest_offset = code[pos]
            pos += 1
            repeat = False
        else:
            if pos + 3 > len(code):
                return None
            dest_offset = int.from_bytes(code[pos : pos + 3], byteorder="big")
            pos += 3
            repeat = False
        if pos % int(spec["alignment"]):
            pos += 1
        unit_size = int(source_sizes[source_mode])
        data_size = unit_size if repeat else unit_size * count
        if pos + data_size > len(code):
            return None
        data_start = pos
        pos += data_size
        align = int(spec["alignment"])
        end = pos if pos % align == 0 else pos + (align - (pos % align))
        commands.append(
            TypedDataStreamCommand(
                start=command_start,
                end=end,
                opcode=opcode,
                dest_offset=dest_offset,
                unit_size=unit_size,
                count=count,
                repeat=repeat,
                data_start=data_start,
                data_end=pos,
            )
        )
        next_dest = dest_offset + (unit_size * count)
        pos = end
    return None


def decode_stream_by_name(
    code: bytes,
    start: int,
    os_kb: object,
    stream_name: str,
) -> TypedDataStream | None:
    spec = _lookup_stream_spec(os_kb, stream_name)
    if spec is None:
        return None
    return decode_typed_data_stream(code, start, spec)


def _resolve_typed_data_stream_values(
    command: TypedDataStreamCommand,
    *,
    code: bytes,
    labels: dict[int, str],
    reloc_map: dict[int, int],
    reloc_labels: dict[int, str],
) -> list[str]:
    values: list[str] = []
    for pos in range(command.data_start, command.data_end, command.unit_size):
        chunk = code[pos : pos + command.unit_size]
        if command.unit_size == 4:
            if pos in reloc_labels:
                values.append(reloc_labels[pos])
            elif pos in reloc_map and reloc_map[pos] in labels:
                values.append(labels[reloc_map[pos]])
            else:
                values.append(f"${int.from_bytes(chunk, byteorder='big'):08x}")
        elif command.unit_size == 2:
            values.append(f"${int.from_bytes(chunk, byteorder='big'):04x}")
        else:
            values.append(f"${chunk[0]:02x}")
    return values


def _resolve_typed_data_stream_dest(
    command: TypedDataStreamCommand,
    *,
    structs: object,
    struct_name: str | None,
) -> str:
    dest = f"${command.dest_offset:02x}"
    if struct_name is not None:
        resolved = resolve_struct_field(structs, struct_name, command.dest_offset)
        if resolved is not None and resolved.field.offset == command.dest_offset:
            dest = resolved.field.name
    return dest


def try_render_typed_data_stream_macro(
    command: TypedDataStreamCommand,
    *,
    spec: Mapping[str, Any],
    code: bytes,
    labels: dict[int, str],
    reloc_map: dict[int, int],
    reloc_labels: dict[int, str],
    structs: object,
    struct_name: str | None,
) -> str | None:
    if command.repeat or command.count != 1:
        return None
    dest_mode = (
        "byte_offset_count"
        if command.dest_offset <= 0xFF
        else "long_offset_count"
    )
    for constructor in spec["constructors"]:
        if (
            int(constructor["unit_size"]) != command.unit_size
            or int(constructor["count"]) != command.count
            or constructor["destination_mode"] != dest_mode
        ):
            continue
        dest = _resolve_typed_data_stream_dest(
            command,
            structs=structs,
            struct_name=struct_name,
        )
        values = _resolve_typed_data_stream_values(
            command,
            code=code,
            labels=labels,
            reloc_map=reloc_map,
            reloc_labels=reloc_labels,
        )
        return f"{constructor['name']} {dest},{values[0]}"
    return None


def format_typed_data_stream_command(
    command: TypedDataStreamCommand,
    *,
    spec: Mapping[str, Any],
    code: bytes,
    labels: dict[int, str],
    reloc_map: dict[int, int],
    reloc_labels: dict[int, str],
    structs: object,
    struct_name: str | None,
) -> str:
    macro = try_render_typed_data_stream_macro(
        command,
        spec=spec,
        code=code,
        labels=labels,
        reloc_map=reloc_map,
        reloc_labels=reloc_labels,
        structs=structs,
        struct_name=struct_name,
    )
    if macro is not None:
        return macro
    dest = _resolve_typed_data_stream_dest(
        command,
        structs=structs,
        struct_name=struct_name,
    )
    values = _resolve_typed_data_stream_values(
        command,
        code=code,
        labels=labels,
        reloc_map=reloc_map,
        reloc_labels=reloc_labels,
    )
    generic = spec["generic_constructor"]
    size_encoding = generic["size_param_encoding"][str(command.unit_size)]
    count_arg = command.count - int(generic["count_bias"])
    rendered = f"{generic['name']} {size_encoding},{dest},0,{count_arg}"
    if values:
        rendered += f" ; data {','.join(values)}"
    return rendered
