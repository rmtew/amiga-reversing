from __future__ import annotations

from collections.abc import Callable

from disasm.assembler_profiles import VASM_PROFILE, AssemblerProfile
from disasm.instruction_rows import (
    emit_data_rows,
    make_instruction_row,
    make_text_rows,
    render_instruction_text,
)
from disasm.types import (
    BlockRowContext,
    HunkDisassemblySession,
    JumpTableRegion,
    ListingRow,
)


def _has_emitted_target_label(
    hunk_session: HunkDisassemblySession,
    target: int,
) -> bool:
    entity_addrs = {
        int(entity["addr"], 16)
        for entity in hunk_session.entities
        if isinstance(entity.get("addr"), str)
    }
    return (
        target in hunk_session.blocks
        or target in hunk_session.hint_blocks
        or target in entity_addrs
        or target in hunk_session.generic_data_label_addrs
        or target in hunk_session.string_addrs
        or target in hunk_session.jump_table_regions
    )


def _has_renderable_target_label(
    hunk_session: HunkDisassemblySession,
    target: int,
    assembler_profile: AssemblerProfile,
) -> bool:
    if not assembler_profile.render.require_label_anchor_for_self_relative_data:
        return target in hunk_session.labels
    return _has_emitted_target_label(hunk_session, target)


def _unaligned_dc_w_bytes_line(
    value: int,
    assembler_profile: AssemblerProfile,
) -> str:
    return (
        f"    {assembler_profile.render.directives.dc_b}    "
        f"${(value >> 8) & 0xFF:02x},${value & 0xFF:02x}\n"
    )


def emit_jump_table_rows(
    rows: list[ListingRow],
    hunk_session: HunkDisassemblySession,
    pos: int,
    entity_addr: int,
    used_structs: set[str],
    emit_label: Callable[[int], None],
    assembler_profile: AssemblerProfile = VASM_PROFILE,
) -> int:
    jt: JumpTableRegion = hunk_session.jump_table_regions[pos]
    hunk_index = getattr(hunk_session, "hunk_index", 0)
    if jt.pattern == "pc_inline_dispatch":
        from m68k.m68k_disasm import _decode_one, _Decoder

        dec = _Decoder(hunk_session.code, 0)
        dec.pos = pos
        while dec.pos < jt.table_end:
            if dec.pos in hunk_session.labels and dec.pos != pos:
                emit_label(dec.pos)
            inst = _decode_one(dec, None)
            if inst is None:
                break
            text, _comment, _comment_parts = render_instruction_text(
                inst, hunk_session, used_structs, include_arg_subs=False
            )
            rows.append(make_instruction_row(
                text, inst, hunk_session, entity_addr, "verified",
                source_context=BlockRowContext(
                    kind="jump-table-inline",
                    hunk_index=hunk_index,
                ),
                used_structs=used_structs,
                include_arg_subs=False,
            ))
        return int(jt.table_end)

    if jt.pattern == "string_dispatch_self_relative":
        chunk_pos = pos
        for entry in jt.entries:
            entry_addr = entry.entry_addr
            tgt = entry.target
            if chunk_pos < entry_addr:
                rows.extend(emit_data_rows(
                    hunk_session.code, chunk_pos, entry_addr,
                    hunk_session.labels, hunk_session.reloc_map,
                    hunk_session.string_addrs, hunk_session.reloc_labels,
                    hunk_session.data_access_sizes,
                    hunk_session.typed_data_sizes, hunk_session.typed_data_fields, hunk_session.os_kb,
                    hunk_session.addr_comments,
                    entity_addr,
                    BlockRowContext(
                        kind="jump-table",
                        hunk_index=hunk_index,
                        verified_state="verified",
                    ),
                    assembler_profile,
                ))
            if (
                assembler_profile.render.require_label_anchor_for_self_relative_data
                and entry_addr in hunk_session.labels
                and entry_addr != pos
            ):
                emit_label(entry_addr)
            target_has_label = _has_renderable_target_label(hunk_session, tgt, assembler_profile)
            tgt_expr = hunk_session.labels[tgt] if target_has_label else f"${(tgt - entry_addr) & 0xFFFF:04x}"
            entry_label = hunk_session.labels.get(entry_addr)
            if assembler_profile.render.auto_align_dc_w and entry_addr % 2 != 0:
                line = _unaligned_dc_w_bytes_line((tgt - entry_addr) & 0xFFFF, assembler_profile)
            elif assembler_profile.render.require_label_anchor_for_self_relative_data:
                assert entry_label is not None, (
                    f"Missing jump-table entry label for ${entry_addr:04x}"
                )
                if target_has_label:
                    line = (
                        f"    {assembler_profile.render.directives.dc_w}    "
                        f"{tgt_expr}-{entry_label}\n"
                    )
                else:
                    line = (
                        f"    {assembler_profile.render.directives.dc_w}    "
                        f"{tgt_expr}\n"
                    )
            else:
                line = f"    {assembler_profile.render.directives.dc_w}    {tgt_expr}-*\n"
            rows.extend(make_text_rows(
                "data",
                line,
                entity_addr=entity_addr,
                addr=entry_addr,
                verified_state="verified",
                source_context=BlockRowContext(
                    kind="jump-table",
                    hunk_index=hunk_index,
                ),
            ))
            chunk_pos = entry_addr + 2
        if chunk_pos < jt.table_end:
            rows.extend(emit_data_rows(
                hunk_session.code, chunk_pos, jt.table_end,
                hunk_session.labels, hunk_session.reloc_map,
                hunk_session.string_addrs, hunk_session.reloc_labels,
                hunk_session.data_access_sizes,
                hunk_session.typed_data_sizes, hunk_session.typed_data_fields, hunk_session.os_kb,
                hunk_session.addr_comments,
                entity_addr,
                BlockRowContext(
                    kind="jump-table",
                    hunk_index=hunk_index,
                    verified_state="verified",
                ),
                assembler_profile,
            ))
        return int(jt.table_end)

    chunk_pos = pos
    for entry in jt.entries:
        entry_addr = entry.entry_addr
        tgt = entry.target
        if chunk_pos < entry_addr:
            rows.extend(emit_data_rows(
                hunk_session.code, chunk_pos, entry_addr,
                hunk_session.labels, hunk_session.reloc_map,
                hunk_session.string_addrs, hunk_session.reloc_labels,
                hunk_session.data_access_sizes,
                hunk_session.typed_data_sizes, hunk_session.typed_data_fields, hunk_session.os_kb,
                hunk_session.addr_comments,
                entity_addr,
                BlockRowContext(
                    kind="jump-table",
                    hunk_index=hunk_index,
                    verified_state="verified",
                ),
                assembler_profile,
            ))
        if entry_addr in hunk_session.labels and entry_addr != pos:
            emit_label(entry_addr)
        target_has_label = _has_renderable_target_label(hunk_session, tgt, assembler_profile)
        tgt_expr = hunk_session.labels[tgt] if target_has_label else f"${(tgt - entry_addr) & 0xFFFF:04x}"
        entry_label = hunk_session.labels.get(entry_addr)
        if assembler_profile.render.auto_align_dc_w and entry_addr % 2 != 0:
            line = _unaligned_dc_w_bytes_line((tgt - entry_addr) & 0xFFFF, assembler_profile)
        elif jt.base_addr is None:
            if assembler_profile.render.require_label_anchor_for_self_relative_data:
                assert entry_label is not None, (
                    f"Missing jump-table entry label for ${entry_addr:04x}"
                )
                if target_has_label:
                    line = (
                        f"    {assembler_profile.render.directives.dc_w}    "
                        f"{tgt_expr}-{entry_label}\n"
                    )
                else:
                    line = (
                        f"    {assembler_profile.render.directives.dc_w}    "
                        f"{tgt_expr}\n"
                    )
            else:
                line = f"    {assembler_profile.render.directives.dc_w}    {tgt_expr}-*\n"
        else:
            if target_has_label:
                line = (
                    f"    {assembler_profile.render.directives.dc_w}    "
                    f"{tgt_expr}-{jt.base_label}\n"
                )
            else:
                line = (
                    f"    {assembler_profile.render.directives.dc_w}    "
                    f"{tgt_expr}\n"
                )
        rows.extend(make_text_rows(
            "data",
            line,
            entity_addr=entity_addr,
            addr=entry_addr,
            verified_state="verified",
            source_context=BlockRowContext(
                kind="jump-table",
                hunk_index=hunk_index,
            ),
        ))
        chunk_pos = entry_addr + 2
    if chunk_pos < jt.table_end:
        rows.extend(emit_data_rows(
            hunk_session.code, chunk_pos, jt.table_end,
            hunk_session.labels, hunk_session.reloc_map,
            hunk_session.string_addrs, hunk_session.reloc_labels,
            hunk_session.data_access_sizes,
            hunk_session.typed_data_sizes, hunk_session.typed_data_fields, hunk_session.os_kb,
            hunk_session.addr_comments,
            entity_addr,
            BlockRowContext(
                kind="jump-table",
                hunk_index=hunk_index,
                verified_state="verified",
            ),
            assembler_profile,
        ))
    return int(jt.table_end)
