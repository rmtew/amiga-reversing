from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, NotRequired, TypedDict, cast

from amiga_reversing.disasm.listing_types import (
    AddressRowContext,
    AppSlotRef,
    BlockRowContext,
    HeaderRowContext,
    ListingRow,
    PlatformTypedAccess,
    PlatformUnresolvedTypedAccess,
    RowSourceContext,
    SemanticOperand,
    SemanticOperandMetadata,
)
from amiga_reversing.disasm.text import listing_window

type _RowSourceContextDataclass = HeaderRowContext | BlockRowContext | AddressRowContext


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


class SerializedAppSlotRef(TypedDict):
    symbol: str
    displacement: int
    base_register: str
    operand_index: int
    access: str


class SerializedTypedAccess(TypedDict):
    operand_index: int
    base_register: str
    displacement: int
    field_offset: int
    root_struct_name: str | None
    owner_struct_name: str | None
    field_name: str | None
    field_expr: str
    inherited: bool
    nested: bool


class SerializedUnresolvedTypedAccess(TypedDict):
    operand_index: int
    base_register: str
    displacement: int
    struct_size: int | None
    root_struct_name: str | None
    classification: str | None
    container_candidate_count: int | None
    container_struct_name: str | None
    container_field_expr: str | None
    refinement_applied: bool
    refined_struct_name: str | None


class SerializedApiInput(TypedDict):
    name: str
    regs: list[str]
    type: str | None
    i_struct: str | None
    source: str
    semantic_kind: str | None
    value_domain: str | None


class SerializedApiOutput(TypedDict):
    name: str
    regs: list[str]
    type: str | None
    o_struct: str | None
    source: str
    semantic_kind: str | None
    value_domain: str | None


class SerializedApiCall(TypedDict):
    library: str
    function: str
    inputs: list[SerializedApiInput]
    outputs: list[SerializedApiOutput]


class SerializedRow(TypedDict):
    row_id: str
    kind: str
    text: str
    stable_key: str | None
    analysis_generation: str
    analysis_phase: str | None
    section_index: int | None
    start_offset: int | None
    end_offset: int | None
    storage_address: int | None
    runtime_address: int | None
    runtime_view_id: int | None
    addr: int | None
    entity_addr: int | None
    verified_state: str | None
    bytes: str | None
    label: str | None
    opcode_or_directive: str | None
    operation_type: str | None
    operand_parts: list[SerializedOperand]
    operand_accesses: list[str]
    operand_registers: list[str | None]
    app_slot_refs: list[SerializedAppSlotRef]
    typed_accesses: list[SerializedTypedAccess]
    unresolved_typed_accesses: list[SerializedUnresolvedTypedAccess]
    operand_text: str
    comment_parts: list[str]
    comment_text: str
    source_context: dict[str, object]
    data_class: str | None
    structured_data: dict[str, object] | None
    entity: dict[str, object] | None
    view_annotations: list[str]
    api_call: SerializedApiCall | None
    repro_issues: NotRequired[list[dict[str, object]]]


class SessionHunkMetadata(TypedDict):
    hunk_index: int
    code_size: int
    entity_count: int
    label_count: int
    core_block_count: int
    hint_block_count: int
    jump_table_count: int
    relocated: bool
    execution_view_count: int


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
    analysis_generation: NotRequired[str | None]
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


def serialize_app_slot_ref(ref: AppSlotRef) -> SerializedAppSlotRef:
    return {
        "symbol": ref.symbol,
        "displacement": ref.displacement,
        "base_register": ref.base_register,
        "operand_index": ref.operand_index,
        "access": ref.access,
    }


def serialize_typed_access(access: PlatformTypedAccess) -> SerializedTypedAccess:
    return {
        "operand_index": access.operand_index,
        "base_register": access.base_register,
        "displacement": access.displacement,
        "field_offset": access.field_offset,
        "root_struct_name": access.root_struct_name,
        "owner_struct_name": access.owner_struct_name,
        "field_name": access.field_name,
        "field_expr": access.field_expr,
        "inherited": access.inherited,
        "nested": access.nested,
    }


def serialize_unresolved_typed_access(access: PlatformUnresolvedTypedAccess) -> SerializedUnresolvedTypedAccess:
    return {
        "operand_index": access.operand_index,
        "base_register": access.base_register,
        "displacement": access.displacement,
        "struct_size": access.struct_size,
        "root_struct_name": access.root_struct_name,
        "classification": access.classification,
        "container_candidate_count": access.container_candidate_count,
        "container_struct_name": access.container_struct_name,
        "container_field_expr": access.container_field_expr,
        "refinement_applied": access.refinement_applied,
        "refined_struct_name": access.refined_struct_name,
    }


def serialize_row(row: ListingRow) -> SerializedRow:
    return {
        "row_id": row.row_id,
        "kind": row.kind,
        "text": row.text,
        "stable_key": row.stable_key,
        "analysis_generation": row.analysis_generation,
        "analysis_phase": row.analysis_phase,
        "section_index": row.section_index,
        "start_offset": row.start_offset,
        "end_offset": row.end_offset,
        "storage_address": row.storage_address,
        "runtime_address": row.runtime_address,
        "runtime_view_id": row.runtime_view_id,
        "addr": row.addr,
        "entity_addr": row.entity_addr,
        "verified_state": row.verified_state,
        "bytes": row.bytes.hex() if row.bytes is not None else None,
        "label": row.label,
        "opcode_or_directive": row.opcode_or_directive,
        "operation_type": row.operation_type,
        "operand_parts": [serialize_operand(op) for op in row.operand_parts],
        "operand_accesses": list(row.operand_accesses),
        "operand_registers": list(row.operand_registers),
        "app_slot_refs": [serialize_app_slot_ref(ref) for ref in row.app_slot_refs],
        "typed_accesses": [serialize_typed_access(access) for access in row.typed_accesses],
        "unresolved_typed_accesses": [
            serialize_unresolved_typed_access(access)
            for access in row.unresolved_typed_accesses
        ],
        "operand_text": row.operand_text,
        "comment_parts": list(row.comment_parts),
        "comment_text": row.comment_text,
        "source_context": _row_source_context_dict(row.source_context),
        "data_class": row.data_class,
        "structured_data": cast(dict[str, object] | None, row.structured_data),
        "entity": None,
        "view_annotations": [],
        "api_call": None,
    }


def session_metadata(session: Any) -> SessionMetadata:
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
                "relocated": bool(hunk.execution_views),
                "execution_view_count": len(hunk.execution_views),
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


def listing_index_window_payload(rows: list[ListingRow], start: int,
                                 count: int) -> ListingWindowPayload:
    safe_count = max(0, count)
    if safe_count == 0 or not rows:
        safe_start = 0
    else:
        max_start = max(0, len(rows) - safe_count)
        safe_start = max(0, min(start, max_start))
    end = min(len(rows), safe_start + safe_count)
    return {
        "anchor_addr": rows[safe_start].addr if safe_start < len(rows) else None,
        "start": safe_start,
        "end": end,
        "has_more_before": safe_start > 0,
        "has_more_after": end < len(rows),
        "total_rows": len(rows),
        "rows": [serialize_row(row) for row in rows[safe_start:end]],
    }
