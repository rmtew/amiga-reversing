from __future__ import annotations

from pathlib import Path

from disasm.hint_validation import is_valid_hint_block
from disasm.instruction_rows import (emit_data_rows, make_instruction_row,
                                     make_row, make_text_rows,
                                     render_instruction_text)
from disasm.jump_tables import emit_jump_table_rows
from disasm.validation import is_valid_encoding, has_valid_branch_target
from disasm.text import listing_window as _listing_window, render_rows
from disasm.types import DisassemblySession, HunkDisassemblySession, ListingRow
from disasm.session import build_disassembly_session


def emit_session_rows(session: DisassemblySession) -> list[ListingRow]:
    rows: list[ListingRow] = []
    for hunk_session in session.hunk_sessions:
        rows.extend(_emit_hunk_rows(hunk_session, session.binary_path))
    return rows


def _emit_hunk_rows(hunk_session: HunkDisassemblySession,
                    binary_path: Path) -> list[ListingRow]:
    rows: list[ListingRow] = []
    used_structs: set[str] = set()
    rows.append(make_row(
        "comment",
        "; Generated disassembly -- vasm Motorola syntax\n",
        source_context={"section": "header"},
    ))
    rows.append(make_row(
        "comment",
        "; Source: " + str(binary_path) + "\n",
        source_context={"section": "header"},
    ))
    rows.append(make_row(
        "comment",
        f"; {hunk_session.code_size} bytes, {len(hunk_session.entities)} entities, "
        f"{len(hunk_session.blocks)} blocks\n",
        source_context={"section": "header"},
    ))
    rows.append(make_row("blank", "\n"))

    for lib_name in sorted(hunk_session.lvo_equs):
        rows.append(make_row("comment", f"; LVO offsets: {lib_name}\n"))
        by_lvo = hunk_session.lvo_equs[lib_name]
        for lvo_val in sorted(by_lvo):
            rows.append(make_row(
                "directive",
                f"{by_lvo[lvo_val]}\tEQU\t{lvo_val}\n",
                opcode_or_directive="EQU",
            ))
        rows.append(make_row("blank", "\n"))

    if hunk_session.arg_equs:
        rows.append(make_row("comment", "; OS function argument constants\n"))
        for name in sorted(hunk_session.arg_equs):
            rows.append(make_row(
                "directive",
                f"{name}\tEQU\t{hunk_session.arg_equs[name]}\n",
                opcode_or_directive="EQU",
            ))
        rows.append(make_row("blank", "\n"))

    base_info = hunk_session.platform.get("initial_base_reg")
    if hunk_session.app_offsets:
        rows.append(make_row(
            "comment",
            f"; App memory offsets (base register A{base_info[0]})\n",
        ))
        for off in sorted(hunk_session.app_offsets):
            rows.append(make_row(
                "directive",
                f"{hunk_session.app_offsets[off]}\tEQU\t{off}\n",
                opcode_or_directive="EQU",
            ))
        rows.append(make_row("blank", "\n"))

    rows.append(make_row(
        "section",
        "    section code,code\n",
        opcode_or_directive="section",
    ))
    rows.append(make_row("blank", "\n"))

    def emit_label(addr: int):
        lbl = hunk_session.labels[addr]
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
                  verified_state: str = "verified"):
        rows.extend(emit_data_rows(
            hunk_session.code, start, stop, hunk_session.labels,
            hunk_session.reloc_map, hunk_session.string_addrs,
            hunk_session.data_access_sizes, entity_addr,
            {"verified_state": verified_state},
        ))

    emit_passes = [(0, hunk_session.code_size)]
    if hunk_session.relocated_segments:
        emit_passes = [
            (0, hunk_session.reloc_file_offset),
            (hunk_session.reloc_base_addr, hunk_session.code_size),
        ]

    entity_lookup = {
        int(entity["addr"], 16): entity
        for entity in hunk_session.entities
    }

    for pass_idx, (pass_start, pass_end) in enumerate(emit_passes):
        if pass_idx == 1:
            rows.append(make_row(
                "org",
                f"\n    org ${hunk_session.reloc_base_addr:X}\n\n",
                opcode_or_directive="org",
            ))
        pos = pass_start
        while pos < pass_end:
            if pos in hunk_session.labels:
                emit_label(pos)

            entity = entity_lookup.get(pos)
            entity_addr = int(entity["addr"], 16) if entity else pos

            if pos in hunk_session.blocks:
                blk = hunk_session.blocks[pos]
                for inst in blk.instructions:
                    if inst.offset != pos and inst.offset in hunk_session.labels:
                        emit_label(inst.offset)
                    if (not is_valid_encoding(inst.text, inst.raw,
                                               inst.offset, hunk_session.kb,
                                               inst.kb_mnemonic)
                            or not has_valid_branch_target(inst, hunk_session.kb)):
                        emit_data(inst.offset, inst.offset + inst.size, entity_addr)
                        continue
                    text, comment, comment_parts = render_instruction_text(
                        inst, hunk_session, used_structs, include_arg_subs=True)
                    rows.append(make_instruction_row(
                        text, inst, hunk_session, entity_addr, "verified",
                        source_context={"kind": "core-block"},
                        comment_text=comment,
                        comment_parts=comment_parts,
                        used_structs=used_structs,
                        include_arg_subs=True,
                    ))
                pos = blk.end
            elif pos in hunk_session.code_addrs:
                pos += 1
            elif pos in hunk_session.hint_blocks:
                blk = hunk_session.hint_blocks[pos]
                valid_hint = is_valid_hint_block(blk, hunk_session.kb)
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
                        source_context={"kind": "hint-block"},
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

    if used_structs:
        includes = set()
        for struct_name in sorted(used_structs):
            struct_def = hunk_session.os_kb["structs"][struct_name]
            includes.add(struct_def["source"].lower())
        if includes:
            insert_at = 0
            for idx, row in enumerate(rows):
                if row.kind == "section":
                    insert_at = idx
                    break
            include_rows = []
            for inc in sorted(includes):
                include_rows.append(make_row(
                    "directive",
                    f'    INCLUDE "{inc}"\n',
                    opcode_or_directive="INCLUDE",
                ))
            include_rows.append(make_row("blank", "\n"))
            rows[insert_at:insert_at] = include_rows

    return rows


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
                         base_addr: int = 0, code_start: int = 0) -> dict:
    rows = build_listing_rows(binary_path, entities_path,
                              base_addr=base_addr, code_start=code_start)
    return _listing_window(rows, addr, before=before, after=after)


def render_session_text(session: DisassemblySession) -> str:
    return render_rows(emit_session_rows(session))
