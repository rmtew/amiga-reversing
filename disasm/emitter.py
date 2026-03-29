from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from disasm.hint_validation import is_valid_hint_block
from disasm.instruction_rows import (
    emit_data_rows,
    make_instruction_row,
    make_row,
    make_text_rows,
    render_instruction_text,
)
from disasm.jump_tables import emit_jump_table_rows
from disasm.os_compat import (
    collect_used_struct_fields,
    infer_emit_compatibility_floor,
    max_compatibility_version,
    select_struct_field_name,
)
from disasm.os_include_kb import load_os_include_kb
from disasm.session import build_disassembly_session
from disasm.target_metadata import (
    EntryRegisterSeedMetadata,
    StructuredRegionSpec,
    effective_entry_register_seeds,
    target_structure_spec,
)
from disasm.text import ListingWindow, render_rows
from disasm.text import listing_window as _listing_window
from disasm.typed_data_streams import (
    decode_stream_by_name,
    try_render_typed_data_stream_macro,
)
from disasm.types import (
    BlockRowContext,
    DisassemblySession,
    EntityRecord,
    HeaderRowContext,
    HunkDisassemblySession,
    ListingRow,
    StructFieldOperandMetadata,
)
from disasm.validation import has_valid_branch_target, is_valid_encoding
from m68k.os_calls import AppBaseInfo
from m68k_kb import runtime_hardware, runtime_os

_OS_INCLUDE_KB = load_os_include_kb()


def _app_slot_equ_value(base_info: AppBaseInfo, offset: int) -> str:
    if base_info.kind.name == "ABSOLUTE":
        addr = (base_info.concrete + offset) & 0xFFFFFFFF
        return f"${addr:X}"
    return str(offset)


def _fd_version_value(raw_version: str | None) -> int | None:
    if raw_version is None:
        return None
    digits = "".join(ch for ch in raw_version if ch.isdigit())
    if not digits:
        return None
    return int(digits)


def _unique_entry_register_notes(
    entry_register_seeds: tuple[EntryRegisterSeedMetadata, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    notes: list[str] = []
    for seed in entry_register_seeds:
        rendered = f"{seed.register}={seed.note}"
        if rendered in seen:
            continue
        seen.add(rendered)
        notes.append(rendered)
    return tuple(notes)


def _library_export_names(library_name: str, library_version: int) -> list[str]:
    functions = runtime_os.LIBRARIES.get(library_name)
    if functions is None:
        return []
    public_names: list[str] = []
    for _lvo, name in sorted(functions.lvo_index.items(), key=lambda item: int(item[0])):
        function = functions.functions[name]
        if function.private:
            continue
        fd_version = _fd_version_value(function.fd_version)
        if fd_version is not None and fd_version > library_version:
            continue
        public_names.append(name)
    return public_names


def emit_session_rows(session: DisassemblySession) -> list[ListingRow]:
    rows: list[ListingRow] = []
    total_code_size = sum(hunk_session.code_size for hunk_session in session.hunk_sessions)
    total_entities = sum(len(hunk_session.entities) for hunk_session in session.hunk_sessions)
    total_blocks = sum(len(hunk_session.blocks) for hunk_session in session.hunk_sessions)
    rows.append(make_row(
        "comment",
        "; Generated disassembly -- vasm Motorola syntax\n",
        source_context=HeaderRowContext(section="header"),
    ))
    rows.append(make_row(
        "comment",
        "; Source: " + str(session.binary_path) + "\n",
        source_context=HeaderRowContext(section="header"),
    ))
    rows.append(make_row(
        "comment",
        f"; {total_code_size} bytes, {total_entities} entities, {total_blocks} blocks\n",
        source_context=HeaderRowContext(section="header"),
    ))
    compatibility_floors: list[str] = []
    body_rows: list[ListingRow] = []
    body_rows.extend(_emit_target_structure_rows(session))
    structure = target_structure_spec(session.target_metadata)
    for index, hunk_session in enumerate(session.hunk_sessions):
        if index > 0:
            body_rows.append(make_row("blank", "\n"))
        target_regions = () if structure is None or index != 0 else structure.regions
        structured_regions = target_regions + hunk_session.dynamic_structured_regions
        hunk_rows, hunk_floor = _emit_hunk_rows(
            hunk_session,
            include_header=len(session.hunk_sessions) > 1,
            structured_regions=structured_regions,
            session=session,
        )
        compatibility_floors.append(hunk_floor)
        body_rows.extend(hunk_rows)
    rows.append(make_row(
        "comment",
        f"; OS compatibility floor: {max_compatibility_version(compatibility_floors)}\n",
        source_context=HeaderRowContext(section="header"),
    ))
    rows.append(make_row("blank", "\n"))
    rows.extend(body_rows)
    return rows


def _emit_target_structure_rows(session: DisassemblySession) -> list[ListingRow]:
    metadata = session.target_metadata
    if metadata is None:
        return []
    rows: list[ListingRow] = []
    entry_register_seeds = effective_entry_register_seeds(metadata)
    if metadata.bootblock is not None:
        bootblock = metadata.bootblock
        rows.append(make_row("comment", "; Boot block structure\n"))
        rows.append(make_row("comment", f";   magic: {bootblock.magic_ascii!r}\n"))
        rows.append(make_row("comment", f";   flags: 0x{bootblock.flags_byte:02X} ({bootblock.fs_description})\n"))
        rows.append(make_row(
            "comment",
            f";   checksum: {bootblock.checksum} ({'valid' if bootblock.checksum_valid else 'invalid'})\n",
        ))
        rows.append(make_row("comment", f";   root block: {bootblock.rootblock_ptr}\n"))
        rows.append(
            make_row(
                "comment",
                f";   boot code: offset 0x{bootblock.bootcode_offset:X}, "
                f"size {bootblock.bootcode_size} bytes\n",
            )
        )
        if session.source_kind == "raw_binary" and session.raw_address_model == "runtime_absolute":
            rows.append(
                make_row(
                    "comment",
                    f";   execution context: load 0x{bootblock.load_address:X}, "
                    f"entry 0x{bootblock.entrypoint:X}\n",
                )
            )
        if entry_register_seeds:
            registers = ", ".join(
                f"{seed.register}={seed.note}" for seed in entry_register_seeds
            )
            rows.append(make_row("comment", f";   entry registers: {registers}\n"))
        rows.append(make_row("blank", "\n"))
    if metadata.resident is not None:
        resident = metadata.resident
        rows.append(make_row("comment", "; Resident structure\n"))
        rows.append(make_row("comment", f";   matchword: 0x{resident.matchword:04X}\n"))
        rows.append(make_row("comment", f";   version: {resident.version}, type: {resident.node_type_name}, priority: {resident.priority}\n"))
        rows.append(make_row("comment", f";   flags: 0x{resident.flags:02X}, auto-init: {resident.auto_init}\n"))
        if resident.name is not None:
            rows.append(make_row("comment", f";   name: {resident.name}\n"))
        if resident.id_string is not None:
            rows.append(make_row("comment", f";   id string: {resident.id_string}\n"))
        rows.append(make_row("comment", f";   init offset: 0x{resident.init_offset:X}\n"))
        rows.append(make_row("blank", "\n"))
    if metadata.library is not None:
        library = metadata.library
        rows.append(make_row("comment", "; Library structure\n"))
        if entry_register_seeds:
            registers = ", ".join(
                _unique_entry_register_notes(entry_register_seeds)
            )
            rows.append(make_row("comment", f";   entry registers: {registers}\n"))
        rows.append(make_row("comment", f";   name: {library.library_name}\n"))
        rows.append(make_row("comment", f";   version: {library.version}\n"))
        if library.id_string is not None:
            rows.append(make_row("comment", f";   id string: {library.id_string}\n"))
        if library.public_function_count is not None:
            rows.append(make_row("comment", f";   public functions: {library.public_function_count}\n"))
        if library.total_lvo_count is not None:
            rows.append(make_row("comment", f";   total LVOs: {library.total_lvo_count}\n"))
        public_names = _library_export_names(library.library_name, library.version)
        if public_names:
            rows.append(make_row("comment", f";   exports: {', '.join(public_names[:12])}\n"))
        rows.append(make_row("blank", "\n"))
    return rows


def _collect_used_absolute_addrs(rows: list[ListingRow],
                                 hunk_session: HunkDisassemblySession) -> set[int]:
    used: set[int] = set()
    for row in rows:
        for operand in row.operand_parts:
            if operand.segment_addr is None:
                continue
            if operand.segment_addr in runtime_hardware.REGISTER_DEFS:
                used.add(operand.segment_addr)
                continue
            label = hunk_session.absolute_labels.get(operand.segment_addr)
            if label is None:
                continue
            if operand.text in {label, f"#{label}"}:
                used.add(operand.segment_addr)
    return used


def _struct_include_source(hunk_session: HunkDisassemblySession,
                           struct_name: str) -> str | None:
    include_path = str(hunk_session.os_kb.STRUCTS[struct_name].source).lower()
    if include_path not in hunk_session.os_kb.META.include_min_versions:
        return None
    return include_path


def _absolute_symbol_rows(used_absolute_addrs: set[int],
                          hunk_session: HunkDisassemblySession
                          ) -> tuple[list[ListingRow], set[str]]:
    equ_rows: list[ListingRow] = []
    include_paths: set[str] = set()
    equ_defs: list[tuple[int, str]] = []
    for addr in sorted(used_absolute_addrs):
        register = runtime_hardware.REGISTER_DEFS.get(addr)
        if register is not None and register["include"]:
            include = register["include"]
            if not include:
                raise ValueError(
                    f"Missing include path for hardware register ${addr:08X} ({register['symbol']})"
                )
            include_paths.add(include)
            continue
        label = hunk_session.absolute_labels.get(addr)
        if label is None:
            raise ValueError(f"Missing absolute label for used address ${addr:08X}")
        equ_defs.append((addr, label))
    if equ_defs:
        equ_rows.append(make_row("comment", "; Absolute symbols\n"))
        for addr, name in equ_defs:
            equ_rows.append(make_row(
                "directive",
                f"{name}\tEQU\t${addr:X}\n",
                opcode_or_directive="EQU",
            ))
        equ_rows.append(make_row("blank", "\n"))
    return equ_rows, include_paths


def _emit_hunk_rows(hunk_session: HunkDisassemblySession,
                    *,
                    include_header: bool,
                    structured_regions: tuple[StructuredRegionSpec, ...] = (),
                    session: DisassemblySession | None = None,
                    ) -> tuple[list[ListingRow], str]:
    rows: list[ListingRow] = []
    used_structs: set[str] = set()
    include_paths: set[str] = set()
    if session is None:
        session = DisassemblySession(
            target_name=None,
            binary_path=Path("."),
            entities_path=Path("."),
            analysis_cache_path=Path("."),
            output_path=None,
            entities=[],
            hunk_sessions=[hunk_session],
        )
    if include_header:
        rows.append(make_row(
            "comment",
            f"; Hunk {hunk_session.hunk_index}: {hunk_session.code_size} bytes, "
            f"{len(hunk_session.entities)} entities, {len(hunk_session.blocks)} blocks\n",
            source_context=HeaderRowContext(section="header"),
        ))
        rows.append(make_row("blank", "\n"))

    for lib_name in sorted(hunk_session.lvo_equs):
        owner = _OS_INCLUDE_KB.library_lvo_owners.get(lib_name)
        if owner is None:
            raise ValueError(f"Missing KB library include owner for LVO symbols: {lib_name}")
        if owner.kind == "native_include":
            include_path = owner.include_path
            if include_path is None:
                raise ValueError(f"Missing native include path for LVO symbols: {lib_name}")
            include_paths.add(include_path)
        elif owner.kind == "fd_only":
            rows.append(make_row("comment", f"; LVO offsets: {lib_name} (FD-derived)\n"))
            by_lvo = hunk_session.lvo_equs[lib_name]
            for lvo_val in sorted(by_lvo):
                rows.append(make_row(
                    "directive",
                    f"{by_lvo[lvo_val]}\tEQU\t{lvo_val}\n",
                    opcode_or_directive="EQU",
                ))
            rows.append(make_row("blank", "\n"))
        else:
            raise ValueError(f"Unknown OS include owner kind for {lib_name}: {owner.kind}")

    if hunk_session.arg_equs:
        rows.append(make_row("comment", "; OS function argument constants\n"))
        for name in sorted(hunk_session.arg_equs):
            rows.append(make_row(
                "directive",
                f"{name}\tEQU\t{hunk_session.arg_equs[name]}\n",
                opcode_or_directive="EQU",
            ))
        rows.append(make_row("blank", "\n"))

    base_info = hunk_session.platform.app_base
    if hunk_session.app_offsets:
        assert base_info is not None, "app_offsets present but platform.app_base is missing"
        if base_info.kind.name == "ABSOLUTE":
            comment = (
                f"; App memory addresses (base register A{base_info.reg_num} "
                f"anchored at ${base_info.concrete:X})\n"
            )
        else:
            comment = f"; App memory offsets (base register A{base_info.reg_num})\n"
        rows.append(make_row(
            "comment",
            comment,
        ))
        for off in sorted(hunk_session.app_offsets):
            rows.append(make_row(
                "directive",
                f"{hunk_session.app_offsets[off]}\tEQU\t{_app_slot_equ_value(base_info, off)}\n",
                opcode_or_directive="EQU",
            ))
        rows.append(make_row("blank", "\n"))

    rows.append(make_row(
        "section",
        "    section code,code\n",
        opcode_or_directive="section",
    ))
    rows.append(make_row("blank", "\n"))

    def emit_label(addr: int) -> None:
        lbl = hunk_session.labels[addr]
        addr_comment = hunk_session.addr_comments.get(addr)
        if addr_comment is not None and addr not in hunk_session.typed_data_sizes:
            rows.extend(make_text_rows(
                "comment",
                f"; {addr_comment}\n",
                entity_addr=addr,
                addr=addr,
            ))
        sources = hunk_session.jump_table_target_sources.get(addr)
        if sources:
            comment = ", ".join(sources)
            rows.extend(make_text_rows(
                "label",
                f"{lbl}: ; jt: {comment}\n",
                entity_addr=addr,
                addr=addr,
            ))
        else:
            rows.extend(make_text_rows(
                "label",
                f"{lbl}:\n",
                entity_addr=addr,
                addr=addr,
            ))

    def emit_data(start: int, stop: int, entity_addr: int | None = None,
                  verified_state: str = "verified") -> None:
        start_comment = hunk_session.addr_comments.get(start)
        if (
            start_comment is not None
            and start not in hunk_session.labels
            and start not in hunk_session.typed_data_sizes
        ):
            rows.extend(make_text_rows(
                "comment",
                f"; {start_comment}\n",
                entity_addr=entity_addr,
                addr=start,
            ))
        rows.extend(emit_data_rows(
            hunk_session.code, start, stop, hunk_session.labels,
            hunk_session.reloc_map, hunk_session.string_addrs,
            hunk_session.data_access_sizes, hunk_session.typed_data_sizes,
            hunk_session.typed_data_fields, hunk_session.os_kb,
            hunk_session.addr_comments, entity_addr,
            BlockRowContext(
                kind="data",
                hunk_index=hunk_session.hunk_index,
                verified_state=verified_state,
            ),
        ))

    def emit_structured_region(region: StructuredRegionSpec, entity_addr: int | None = None) -> None:
        if region.subtype == "typed_data_stream" and region.stream_format is not None:
            spec = hunk_session.os_kb.META.typed_data_stream_formats.get(region.stream_format)
            if spec is None:
                emit_data(region.start, region.end, entity_addr)
                return
            stream = decode_stream_by_name(
                hunk_session.code,
                region.start,
                hunk_session.os_kb,
                region.stream_format,
            )
            if stream is None:
                emit_data(region.start, region.end, entity_addr)
                return
            stream_spec = cast(Mapping[str, Any], spec)
            include_paths.add(str(stream_spec["include_path"]))
            rows.extend(make_text_rows(
                "label",
                f"{hunk_session.labels.get(region.start, 'typed_data_stream')}:\n",
                entity_addr=entity_addr,
                addr=region.start,
            ))
            for command in stream.commands:
                macro = try_render_typed_data_stream_macro(
                    command,
                    spec=spec,
                    code=hunk_session.code,
                    labels=hunk_session.labels,
                    reloc_map=hunk_session.reloc_map,
                    structs=hunk_session.os_kb.STRUCTS,
                    struct_name=region.struct_name,
                )
                if macro is None:
                    emit_data(command.start, command.end, entity_addr)
                    continue
                rows.extend(make_text_rows(
                    "directive",
                    f"    {macro}\n",
                    entity_addr=entity_addr,
                    addr=command.start,
                    verified_state="verified",
                    source_context=BlockRowContext(
                        kind="data",
                        hunk_index=hunk_session.hunk_index,
                        verified_state="verified",
                    ),
                ))
            emit_data(stream.end - 1, stream.end, entity_addr)
            return
        by_offset = {
            field.offset: field
            for field in region.fields
            if region.start <= field.offset < region.end
        }
        field_offsets = sorted(by_offset)
        pos = region.start
        for index, field_offset in enumerate(field_offsets):
            if pos < field_offset:
                emit_data(pos, field_offset, entity_addr)
                pos = field_offset
            boundary = region.end if index + 1 == len(field_offsets) else field_offsets[index + 1]
            field = by_offset.get(pos)
            assert field is not None, f"Missing structured field at 0x{pos:X}"
            rows.extend(make_text_rows(
                "label",
                f"{field.label}:\n",
                entity_addr=entity_addr,
                addr=pos,
            ))
            if field.is_string:
                raw = hunk_session.code[pos:boundary]
                nul = raw.find(0)
                if nul == -1:
                    raise ValueError(f"Structured string field {field.label} is missing terminator")
                text = raw[:nul].decode("latin-1")
                escaped = text.replace('"', '\\"')
                rows.extend(make_text_rows(
                    "data",
                    f'    dc.b    "{escaped}",0\n',
                    entity_addr=entity_addr,
                    addr=pos,
                    verified_state="verified",
                    source_context=BlockRowContext(
                        kind="data",
                        hunk_index=hunk_session.hunk_index,
                        verified_state="verified",
                    ),
                ))
            elif field.size == 4:
                value = struct.unpack_from(">I", hunk_session.code, pos)[0]
                rendered = hunk_session.labels.get(value) if field.pointer else None
                if rendered is None:
                    rendered = f"${value:08x}"
                rows.extend(make_text_rows(
                    "data",
                    f"    dc.l    {rendered}\n",
                    entity_addr=entity_addr,
                    addr=pos,
                    verified_state="verified",
                    source_context=BlockRowContext(
                        kind="data",
                        hunk_index=hunk_session.hunk_index,
                        verified_state="verified",
                    ),
                ))
            elif field.size == 2:
                value = struct.unpack_from(">H", hunk_session.code, pos)[0]
                rendered = hunk_session.labels.get(value) if field.pointer else None
                if rendered is None:
                    rendered = f"${value:04x}"
                rows.extend(make_text_rows(
                    "data",
                    f"    dc.w    {rendered}\n",
                    entity_addr=entity_addr,
                    addr=pos,
                    verified_state="verified",
                    source_context=BlockRowContext(
                        kind="data",
                        hunk_index=hunk_session.hunk_index,
                        verified_state="verified",
                    ),
                ))
            elif field.size == 1:
                value = hunk_session.code[pos]
                rows.extend(make_text_rows(
                    "data",
                    f"    dc.b    ${value:02x}\n",
                    entity_addr=entity_addr,
                    addr=pos,
                    verified_state="verified",
                    source_context=BlockRowContext(
                        kind="data",
                        hunk_index=hunk_session.hunk_index,
                        verified_state="verified",
                    ),
                ))
            else:
                emit_data(pos, boundary, entity_addr)
            pos = boundary
        if pos < region.end:
            emit_data(pos, region.end, entity_addr)

    emit_passes = [(0, hunk_session.code_size)]
    if hunk_session.relocated_segments:
        emit_passes = [
            (0, hunk_session.reloc_file_offset),
            (hunk_session.reloc_base_addr, hunk_session.code_size),
        ]

    entity_lookup: dict[int, EntityRecord] = {}
    for entity in hunk_session.entities:
        raw_addr = entity["addr"]
        entity_lookup[int(raw_addr, 16)] = entity

    for pass_idx, (pass_start, pass_end) in enumerate(emit_passes):
        if pass_idx == 1:
            rows.append(make_row(
                "org",
                f"\n    org ${hunk_session.reloc_base_addr:X}\n\n",
                opcode_or_directive="org",
            ))
        structured_by_start = {
            region.start: region
            for region in structured_regions
            if pass_start <= region.start < pass_end
        }
        pos = pass_start
        while pos < pass_end:
            structured_region = structured_by_start.get(pos)
            if pos in hunk_session.labels and structured_region is None:
                emit_label(pos)

            current_entity: EntityRecord | None = entity_lookup.get(pos)
            if current_entity is None:
                entity_addr = pos
            else:
                raw_addr = current_entity["addr"]
                entity_addr = int(raw_addr, 16)

            if structured_region is not None:
                emit_structured_region(structured_region, entity_addr)
                pos = structured_region.end
                continue

            if pos in hunk_session.blocks:
                blk = hunk_session.blocks[pos]
                for inst in blk.instructions:
                    if inst.offset != pos and inst.offset in hunk_session.labels:
                        emit_label(inst.offset)
                    if inst.kb_mnemonic is None or inst.operand_size is None:
                        emit_data(inst.offset, inst.offset + inst.size, entity_addr)
                        continue
                    if (not is_valid_encoding(inst.raw,
                                               inst.offset,
                                               inst.kb_mnemonic, inst.operand_size)
                            or not has_valid_branch_target(inst)):
                        emit_data(inst.offset, inst.offset + inst.size, entity_addr)
                        continue
                    text, comment, comment_parts = render_instruction_text(
                        inst, hunk_session, used_structs, include_arg_subs=True)
                    rows.append(make_instruction_row(
                        text, inst, hunk_session, entity_addr, "verified",
                        source_context=BlockRowContext(
                            kind="core-block",
                            hunk_index=hunk_session.hunk_index,
                        ),
                        comment_text=comment,
                        comment_parts=comment_parts,
                        used_structs=used_structs,
                        include_arg_subs=True,
                    ))
                pos = blk.end
            elif pos in hunk_session.typed_data_sizes:
                data_end = pos + 1
                while (data_end < pass_end
                       and data_end not in hunk_session.blocks
                       and data_end not in hunk_session.hint_blocks
                       and data_end not in hunk_session.labels):
                    data_end += 1
                emit_data(pos, data_end, entity_addr)
                pos = data_end
            elif pos in hunk_session.code_addrs:
                pos += 1
            elif pos in hunk_session.hint_blocks:
                blk = hunk_session.hint_blocks[pos]
                valid_hint = is_valid_hint_block(blk)
                if not valid_hint:
                    emit_data(pos, blk.end, entity_addr, verified_state="unverified")
                    pos = blk.end
                    continue

                rows.append(make_row("comment", "; --- unverified ---\n"))
                for inst in blk.instructions:
                    if inst.offset != pos and inst.offset in hunk_session.labels:
                        emit_label(inst.offset)
                    text, comment, comment_parts = render_instruction_text(
                        inst, hunk_session, used_structs, include_arg_subs=False)
                    rows.append(make_instruction_row(
                        text, inst, hunk_session, entity_addr, "unverified",
                        source_context=BlockRowContext(
                            kind="hint-block",
                            hunk_index=hunk_session.hunk_index,
                            verified_state="unverified",
                        ),
                        comment_text=comment,
                        comment_parts=comment_parts,
                        used_structs=used_structs,
                        include_arg_subs=False,
                    ))
                pos = blk.end
            elif pos in hunk_session.hint_addrs:
                pos += 1
            elif pos in hunk_session.jump_table_regions:
                pos = emit_jump_table_rows(
                    rows, hunk_session, pos, entity_addr, used_structs, emit_label)
            else:
                data_end = pos + 1
                while (data_end < pass_end
                       and data_end not in hunk_session.blocks
                       and data_end not in hunk_session.hint_blocks
                       and data_end not in hunk_session.labels):
                    data_end += 1
                emit_data(pos, data_end, entity_addr)
                pos = data_end

    compat_floor = infer_emit_compatibility_floor(
        session,
        include_paths={
            *include_paths,
            *(
                include_path
                for struct_name in sorted(used_structs)
                if (include_path := _struct_include_source(hunk_session, struct_name)) is not None
            ),
        },
        struct_fields=collect_used_struct_fields(rows),
    )
    rows = _apply_compatibility_field_names(rows, hunk_session, compat_floor)
    used_absolute_addrs = _collect_used_absolute_addrs(rows, hunk_session)
    absolute_symbol_rows, hardware_includes = _absolute_symbol_rows(
        used_absolute_addrs, hunk_session)
    if absolute_symbol_rows:
        insert_at = 0
        for idx, row in enumerate(rows):
            if row.kind == "section":
                insert_at = idx
                break
        rows[insert_at:insert_at] = absolute_symbol_rows
    includes = set(include_paths)
    os_includes = set(include_paths)
    includes.update(hardware_includes)
    if used_structs:
        for struct_name in sorted(used_structs):
            os_include = _struct_include_source(hunk_session, struct_name)
            if os_include is None:
                continue
            includes.add(os_include)
            os_includes.add(os_include)
    if includes:
        insert_at = 0
        for idx, row in enumerate(rows):
            if row.kind == "section":
                insert_at = idx
                break
        include_rows = []
        for inc in sorted(includes):
            if inc in os_includes:
                include_since = hunk_session.os_kb.META.include_min_versions.get(inc.lower())
                if include_since is None:
                    raise ValueError(f"Missing KB include compatibility for {inc}")
                if hunk_session.os_kb.META.compatibility_versions.index(include_since) > hunk_session.os_kb.META.compatibility_versions.index(compat_floor):
                    raise ValueError(
                        f"Include {inc} requires OS {include_since}, above compatibility floor {compat_floor}"
                    )
            include_rows.append(make_row(
                "directive",
                f'    INCLUDE "{inc}"\n',
                opcode_or_directive="INCLUDE",
            ))
        include_rows.append(make_row("blank", "\n"))
        rows[insert_at:insert_at] = include_rows

    return rows, compat_floor


def _apply_compatibility_field_names(
    rows: list[ListingRow],
    hunk_session: HunkDisassemblySession,
    compatibility_floor: str,
) -> list[ListingRow]:
    rewritten: list[ListingRow] = []
    for row in rows:
        updated_operands = list(row.operand_parts)
        changed = False
        for index, operand in enumerate(updated_operands):
            metadata = operand.metadata
            if not isinstance(metadata, StructFieldOperandMetadata):
                continue
            field_symbol = metadata.field_symbol
            if field_symbol is None:
                continue
            struct_def = hunk_session.os_kb.STRUCTS.get(metadata.owner_struct)
            if struct_def is None:
                raise ValueError(
                    f"Missing KB struct for compatibility rendering: {metadata.owner_struct}"
                )
            field_def = next((field for field in struct_def.fields if field.name == field_symbol), None)
            if field_def is None:
                raise ValueError(
                    f"Missing KB struct field for compatibility rendering: "
                    f"{metadata.owner_struct}.{field_symbol}"
                )
            compat_name = select_struct_field_name(field_def, compatibility_floor)
            if compat_name == field_symbol:
                continue
            updated_operands[index] = replace(
                operand,
                text=operand.text.replace(field_symbol, compat_name),
                metadata=replace(metadata, symbol=compat_name, field_symbol=compat_name),
            )
            changed = True
        if not changed:
            rewritten.append(row)
            continue
        operand_parts = tuple(updated_operands)
        operand_text = ",".join(part.text for part in operand_parts)
        text = row.text
        if row.operand_text:
            text = text.replace(row.operand_text, operand_text, 1)
        rewritten.append(replace(
            row,
            operand_parts=operand_parts,
            operand_text=operand_text,
            text=text,
        ))
    return rewritten


def build_listing_rows(binary_path: str, entities_path: str,
                       base_addr: int = 0,
                       code_start: int = 0) -> list[ListingRow]:
    session = build_disassembly_session(
        binary_path, entities_path, None,
        base_addr=base_addr, code_start=code_start,
    )
    return emit_session_rows(session)


def build_listing_window(binary_path: str, entities_path: str,
                         addr: int | None,
                         before: int = 80, after: int = 160,
                         base_addr: int = 0, code_start: int = 0) -> ListingWindow:
    rows = build_listing_rows(binary_path, entities_path,
                              base_addr=base_addr, code_start=code_start)
    return _listing_window(rows, addr, before=before, after=after)


def render_session_text(session: DisassemblySession) -> str:
    rendered = render_rows(emit_session_rows(session))
    assert isinstance(rendered, str)
    return rendered

