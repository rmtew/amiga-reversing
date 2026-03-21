from __future__ import annotations

from disasm.instruction_rows import (emit_data_rows, make_instruction_row,
                                     make_text_rows, render_instruction_text)
from disasm.types import BlockRowContext


def emit_jump_table_rows(rows: list, hunk_session, pos: int, entity_addr: int,
                         used_structs: set[str], emit_label) -> int:
    jt = hunk_session.jump_table_regions[pos]
    if jt.pattern == "pc_inline_dispatch":
        from m68k.m68k_disasm import _Decoder, _decode_one

        dec = _Decoder(hunk_session.code, 0)
        dec.pos = pos
        while dec.pos < jt.table_end:
            if dec.pos in hunk_session.labels and dec.pos != pos:
                emit_label(dec.pos)
            inst = _decode_one(dec, None)
            if inst is None:
                break
            text, _comment, _comment_parts = render_instruction_text(
                inst, hunk_session, used_structs, include_arg_subs=False)
            rows.append(make_instruction_row(
                text, inst, hunk_session, entity_addr, "verified",
                source_context=BlockRowContext(kind="jump-table-inline"),
                used_structs=used_structs,
                include_arg_subs=False,
            ))
        return jt.table_end

    if jt.pattern == "string_dispatch_self_relative":
        chunk_pos = pos
        for entry in jt.entries:
            entry_addr = entry.entry_addr
            tgt = entry.target
            if chunk_pos < entry_addr:
                rows.extend(emit_data_rows(
                    hunk_session.code, chunk_pos, entry_addr,
                    hunk_session.labels, hunk_session.reloc_map,
                    hunk_session.string_addrs, hunk_session.data_access_sizes,
                    entity_addr,
                    BlockRowContext(kind="jump-table", verified_state="verified"),
                ))
            tgt_label = hunk_session.labels[tgt]
            rows.extend(make_text_rows(
                "data",
                f"    dc.w    {tgt_label}-*\n",
                entity_addr=entity_addr,
                addr=entry_addr,
                verified_state="verified",
                source_context=BlockRowContext(kind="jump-table"),
            ))
            chunk_pos = entry_addr + 2
        if chunk_pos < jt.table_end:
            rows.extend(emit_data_rows(
                hunk_session.code, chunk_pos, jt.table_end,
                hunk_session.labels, hunk_session.reloc_map,
                hunk_session.string_addrs, hunk_session.data_access_sizes,
                entity_addr,
                BlockRowContext(kind="jump-table", verified_state="verified"),
            ))
        return jt.table_end

    chunk_pos = pos
    for entry in jt.entries:
        entry_addr = entry.entry_addr
        tgt = entry.target
        if chunk_pos < entry_addr:
            rows.extend(emit_data_rows(
                hunk_session.code, chunk_pos, entry_addr,
                hunk_session.labels, hunk_session.reloc_map,
                hunk_session.string_addrs, hunk_session.data_access_sizes,
                entity_addr,
                BlockRowContext(kind="jump-table", verified_state="verified"),
            ))
        if entry_addr in hunk_session.labels and entry_addr != pos:
            emit_label(entry_addr)
        tgt_label = hunk_session.labels[tgt]
        if jt.base_addr is None:
            line = f"    dc.w    {tgt_label}-*\n"
        else:
            line = f"    dc.w    {tgt_label}-{jt.base_label}\n"
        rows.extend(make_text_rows(
            "data",
            line,
            entity_addr=entity_addr,
            addr=entry_addr,
            verified_state="verified",
            source_context=BlockRowContext(kind="jump-table"),
        ))
        chunk_pos = entry_addr + 2
    if chunk_pos < jt.table_end:
        rows.extend(emit_data_rows(
            hunk_session.code, chunk_pos, jt.table_end,
            hunk_session.labels, hunk_session.reloc_map,
            hunk_session.string_addrs, hunk_session.data_access_sizes,
            entity_addr,
            BlockRowContext(kind="jump-table", verified_state="verified"),
        ))
    return jt.table_end
