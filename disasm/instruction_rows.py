from __future__ import annotations

from typing import Any

from disasm.comments import build_instruction_comment_parts, render_comment_parts
from disasm.data_render import iter_data_region_lines
from disasm.operands import build_instruction_semantic_operands
from disasm.types import (
    BlockRowContext,
    HunkDisassemblySession,
    ListingRow,
    RowSourceContext,
    SemanticOperand,
    TypedDataFieldInfo,
)
from m68k.m68k_disasm import Instruction


def render_semantic_operands(operands: tuple[SemanticOperand, ...]) -> str:
    return ",".join(op.text for op in operands)


def make_row(
    kind: str,
    text: str,
    *,
    row_id: str | None = None,
    addr: int | None = None,
    entity_addr: int | None = None,
    verified_state: str | None = None,
    bytes: bytes | None = None,
    label: str | None = None,
    opcode_or_directive: str | None = None,
    operand_parts: tuple[SemanticOperand, ...] = (),
    operand_text: str = "",
    comment_parts: tuple[str, ...] = (),
    comment_text: str = "",
    source_context: RowSourceContext | None = None,
) -> ListingRow:
    if row_id is None:
        row_id = (
            f"{kind}:{addr:06x}" if isinstance(addr, int) else f"{kind}:{hash(text)}"
        )
    return ListingRow(
        row_id=row_id,
        kind=kind,
        text=text,
        addr=addr,
        entity_addr=entity_addr,
        verified_state=verified_state,
        bytes=bytes,
        label=label,
        opcode_or_directive=opcode_or_directive,
        operand_parts=operand_parts,
        operand_text=operand_text,
        comment_parts=comment_parts,
        comment_text=comment_text,
        source_context=source_context,
    )


def _instruction_opcode_text(inst: Instruction) -> str:
    assert inst.opcode_text is not None, (
        f"Instruction at ${inst.offset:06x} is missing opcode_text"
    )
    return inst.opcode_text


def make_instruction_row(
    text: str,
    inst: Instruction,
    hunk_session: HunkDisassemblySession,
    entity_addr: int,
    verified_state: str,
    source_context: RowSourceContext | None = None,
    comment_text: str = "",
    comment_parts: tuple[str, ...] = (),
    used_structs: set[str] | None = None,
    include_arg_subs: bool = True,
) -> ListingRow:
    opcode = _instruction_opcode_text(inst)
    operand_parts = build_instruction_semantic_operands(
        inst, hunk_session, used_structs=used_structs, include_arg_subs=include_arg_subs
    )
    operands = render_semantic_operands(operand_parts)
    rendered_comment = (
        render_comment_parts(comment_parts) if comment_parts else comment_text
    )
    rendered_line = f"    {opcode}"
    if operands:
        rendered_line += f" {operands}"
    if rendered_comment:
        rendered_line += f" ; {rendered_comment}"
    return ListingRow(
        row_id=f"instruction:{inst.offset:06x}",
        kind="instruction",
        text=rendered_line + "\n",
        addr=inst.offset,
        entity_addr=entity_addr,
        verified_state=verified_state,
        bytes=inst.raw,
        opcode_or_directive=opcode,
        operand_parts=operand_parts,
        operand_text=operands,
        comment_parts=comment_parts
        if comment_parts
        else ((comment_text,) if comment_text else ()),
        comment_text=rendered_comment,
        source_context=source_context,
    )


def make_text_rows(
    kind: str,
    text: str,
    entity_addr: int | None = None,
    addr: int | None = None,
    verified_state: str | None = None,
    source_context: RowSourceContext | None = None,
) -> list[ListingRow]:
    rows: list[ListingRow] = []
    for idx, line in enumerate(text.splitlines(keepends=True)):
        stripped = line.rstrip("\n")
        label = None
        opcode = None
        operands = ""
        comment = ""
        if kind == "label":
            label = stripped.rstrip(":")
        elif kind in {"data", "directive", "comment"}:
            comment_split = stripped.split(";", 1)
            code_text = comment_split[0].strip()
            comment = comment_split[1].strip() if len(comment_split) > 1 else ""
            parts = code_text.split(None, 1)
            if parts:
                opcode = parts[0]
                operands = parts[1] if len(parts) > 1 else ""
        operand_parts: tuple[SemanticOperand, ...] = ()
        if operands:
            tokens = []
            start = 0
            depth = 0
            for pos, ch in enumerate(operands):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                elif ch == "," and depth == 0:
                    tokens.append(operands[start:pos].strip())
                    start = pos + 1
            tokens.append(operands[start:].strip())
            operand_parts = tuple(
                SemanticOperand(kind="text", text=token) for token in tokens if token
            )
        rows.append(
            ListingRow(
                row_id=f"{kind}:{addr if addr is not None else 'none'}:{idx}",
                kind=kind,
                text=line,
                addr=addr,
                entity_addr=entity_addr,
                verified_state=verified_state,
                label=label,
                opcode_or_directive=opcode,
                operand_parts=operand_parts,
                operand_text=operands,
                comment_parts=(comment,) if comment else (),
                comment_text=comment,
                source_context=source_context,
            )
        )
    return rows


def emit_data_rows(
    code: bytes,
    start: int,
    end: int,
    labels: dict[int, str],
    reloc_map: dict[int, int],
    string_addrs: set[int],
    reloc_labels: dict[int, str] | None,
    access_sizes: dict[int, int],
    typed_data_sizes: dict[int, int],
    typed_data_fields: dict[int, TypedDataFieldInfo],
    os_kb: Any,
    addr_comments: dict[int, str],
    entity_addr: int | None,
    source_context: BlockRowContext,
) -> list[ListingRow]:
    rows: list[ListingRow] = []
    for line_addr, line in iter_data_region_lines(
        code,
        start,
        end,
        labels,
        reloc_map,
        string_addrs,
        reloc_labels,
        access_sizes=access_sizes,
        typed_sizes=typed_data_sizes,
        typed_fields=typed_data_fields,
        os_kb=os_kb,
        addr_comments=addr_comments,
    ):
        stripped = line.lstrip()
        if line.startswith(";"):
            kind = "comment"
        elif (
            stripped
            and not line.startswith(" ")
            and stripped.endswith(":\n")
            or stripped
            and not line.startswith(" ")
            and stripped.endswith(":")
            or stripped
            and not line.startswith(" ")
            and stripped.rstrip("\n").endswith(":")
        ):
            kind = "label"
        else:
            kind = "data"
        rows.extend(
            make_text_rows(
                kind,
                line,
                entity_addr=entity_addr,
                addr=line_addr,
                verified_state=source_context.verified_state,
                source_context=source_context,
            )
        )
    return rows


def render_instruction_text(
    inst: Instruction,
    hunk_session: HunkDisassemblySession,
    used_structs: set[str],
    include_arg_subs: bool = True,
) -> tuple[str, str, tuple[str, ...]]:
    opcode = _instruction_opcode_text(inst)
    operand_parts = build_instruction_semantic_operands(
        inst,
        hunk_session,
        used_structs=used_structs,
        include_arg_subs=include_arg_subs,
    )
    operand_text = render_semantic_operands(operand_parts)
    text = opcode if not operand_text else f"{opcode} {operand_text}"
    comment_parts = build_instruction_comment_parts(
        inst,
        hunk_session,
        operand_parts=operand_parts,
        include_arg_subs=include_arg_subs,
    )
    return text, "; ".join(comment_parts), comment_parts
