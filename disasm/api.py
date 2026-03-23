from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, TypeAlias, TypedDict, cast

from disasm.text import listing_window
from disasm.types import (
    AddressRowContext,
    BlockRowContext,
    RowSourceContext,
    DisassemblySession,
    HeaderRowContext,
    ListingRow,
    SemanticOperand,
    SemanticOperandMetadata,
)


_RowSourceContextDataclass: TypeAlias = HeaderRowContext | BlockRowContext | AddressRowContext


def _dataclass_dict(value: object) -> dict[str, object]:
    return cast(dict[str, object], asdict(cast(Any, value)))


class SerializedOperand(TypedDict):
    kind: str
    text: str
    value: int | None
    register: str | None
    base_register: str | None
    displacement: int | None
    segment_addr: int | None
    metadata: dict[str, object]


class SerializedRow(TypedDict):
    row_id: str
    kind: str
    text: str
    addr: int | None
    entity_addr: int | None
    verified_state: str | None
    bytes: str | None
    label: str | None
    opcode_or_directive: str | None
    operand_parts: list[SerializedOperand]
    operand_text: str
    comment_parts: list[str]
    comment_text: str
    source_context: dict[str, object]


class SessionHunkMetadata(TypedDict):
    hunk_index: int
    code_size: int
    entity_count: int
    label_count: int
    core_block_count: int
    hint_block_count: int
    jump_table_count: int
    relocated: bool


class SessionMetadata(TypedDict):
    target_name: str | None
    binary_path: str
    entities_path: str
    analysis_cache_path: str
    output_path: str | None
    entity_count: int
    hunk_count: int
    hunks: list[SessionHunkMetadata]


class ListingWindowPayload(TypedDict):
    anchor_addr: int | None
    start: int
    end: int
    has_more_before: bool
    has_more_after: bool
    total_rows: int
    rows: list[SerializedRow]


def _row_source_context_dict(source_context: RowSourceContext | None) -> dict[str, object]:
    if source_context is None:
        return {}
    if is_dataclass(source_context):
        return _dataclass_dict(source_context)
    raise TypeError(f"Unsupported row source_context type: {type(source_context)!r}")


def _semantic_metadata_dict(metadata: SemanticOperandMetadata | None) -> dict[str, object]:
    if metadata is None:
        return {}
    if is_dataclass(metadata):
        return _dataclass_dict(metadata)
    raise TypeError(f"Unsupported semantic metadata type: {type(metadata)!r}")


def serialize_operand(operand: SemanticOperand) -> SerializedOperand:
    return {
        "kind": operand.kind,
        "text": operand.text,
        "value": operand.value,
        "register": operand.register,
        "base_register": operand.base_register,
        "displacement": operand.displacement,
        "segment_addr": operand.segment_addr,
        "metadata": _semantic_metadata_dict(operand.metadata),
    }


def serialize_row(row: ListingRow) -> SerializedRow:
    return {
        "row_id": row.row_id,
        "kind": row.kind,
        "text": row.text,
        "addr": row.addr,
        "entity_addr": row.entity_addr,
        "verified_state": row.verified_state,
        "bytes": row.bytes.hex() if row.bytes is not None else None,
        "label": row.label,
        "opcode_or_directive": row.opcode_or_directive,
        "operand_parts": [serialize_operand(op) for op in row.operand_parts],
        "operand_text": row.operand_text,
        "comment_parts": list(row.comment_parts),
        "comment_text": row.comment_text,
        "source_context": _row_source_context_dict(row.source_context),
    }


def session_metadata(session: DisassemblySession) -> SessionMetadata:
    return {
        "target_name": session.target_name,
        "binary_path": str(session.binary_path),
        "entities_path": str(session.entities_path),
        "analysis_cache_path": str(session.analysis_cache_path),
        "output_path": str(session.output_path) if session.output_path else None,
        "entity_count": len(session.entities),
        "hunk_count": len(session.hunk_sessions),
        "hunks": [
            {
                "hunk_index": hunk.hunk_index,
                "code_size": hunk.code_size,
                "entity_count": len(hunk.entities),
                "label_count": len(hunk.labels),
                "core_block_count": len(hunk.blocks),
                "hint_block_count": len(hunk.hint_blocks),
                "jump_table_count": len(hunk.jump_table_regions),
                "relocated": bool(hunk.relocated_segments),
            }
            for hunk in session.hunk_sessions
        ],
    }


def listing_window_payload(rows: list[ListingRow], addr: int | None,
                           before: int = 80, after: int = 160) -> ListingWindowPayload:
    window = listing_window(rows, addr, before=before, after=after)
    return {
        "anchor_addr": window["anchor_addr"],
        "start": window["start"],
        "end": window["end"],
        "has_more_before": window["has_more_before"],
        "has_more_after": window["has_more_after"],
        "total_rows": window["total_rows"],
        "rows": [serialize_row(row) for row in window["rows"]],
    }
