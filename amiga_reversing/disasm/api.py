from __future__ import annotations

from typing import Any, NotRequired, TypedDict


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


