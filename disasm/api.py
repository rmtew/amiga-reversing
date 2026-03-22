from __future__ import annotations

from dataclasses import asdict, is_dataclass

from disasm.text import listing_window
from disasm.types import (
    DisassemblySession,
    ListingRow,
    SemanticOperand,
)


def _row_source_context_dict(source_context) -> dict:
    if source_context is None:
        return {}
    if is_dataclass(source_context):
        return asdict(source_context)
    raise TypeError(f"Unsupported row source_context type: {type(source_context)!r}")


def _semantic_metadata_dict(metadata) -> dict:
    if isinstance(metadata, dict):
        return dict(metadata)
    if is_dataclass(metadata):
        return asdict(metadata)
    raise TypeError(f"Unsupported semantic metadata type: {type(metadata)!r}")


def serialize_operand(operand: SemanticOperand) -> dict:
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


def serialize_row(row: ListingRow) -> dict:
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


def session_metadata(session: DisassemblySession) -> dict:
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
                           before: int = 80, after: int = 160) -> dict:
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
