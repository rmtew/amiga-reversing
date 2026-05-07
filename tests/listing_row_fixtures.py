from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, cast

from tests.listing_types_fixtures import (
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

type _RowSourceContextDataclass = HeaderRowContext | BlockRowContext | AddressRowContext
type SerializedRow = dict[str, object]


def _dataclass_dict(value: object) -> dict[str, object]:
    return cast(dict[str, object], asdict(cast(Any, value)))


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


def serialize_operand(operand: SemanticOperand) -> dict[str, object]:
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


def serialize_app_slot_ref(ref: AppSlotRef) -> dict[str, object]:
    return {
        "symbol": ref.symbol,
        "displacement": ref.displacement,
        "base_register": ref.base_register,
        "operand_index": ref.operand_index,
        "access": ref.access,
    }


def serialize_typed_access(access: PlatformTypedAccess) -> dict[str, object]:
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


def serialize_unresolved_typed_access(access: PlatformUnresolvedTypedAccess) -> dict[str, object]:
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
    serialized: dict[str, object] = {
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
        "source_context": _row_source_context_dict(row.source_context),
    }
    if row.verified_state is not None:
        serialized["verified_state"] = row.verified_state
    if row.bytes is not None:
        serialized["bytes"] = row.bytes.hex()
    if row.label is not None:
        serialized["label"] = row.label
    if row.opcode_or_directive is not None:
        serialized["opcode_or_directive"] = row.opcode_or_directive
    if row.operation_type is not None:
        serialized["operation_type"] = row.operation_type
    if row.operand_parts:
        serialized["operand_parts"] = [serialize_operand(op) for op in row.operand_parts]
    if row.operand_accesses:
        serialized["operand_accesses"] = list(row.operand_accesses)
    if row.operand_registers:
        serialized["operand_registers"] = list(row.operand_registers)
    if row.app_slot_refs:
        serialized["app_slot_refs"] = [serialize_app_slot_ref(ref) for ref in row.app_slot_refs]
    if row.typed_accesses:
        serialized["typed_accesses"] = [serialize_typed_access(access) for access in row.typed_accesses]
    if row.unresolved_typed_accesses:
        serialized["unresolved_typed_accesses"] = [
            serialize_unresolved_typed_access(access)
            for access in row.unresolved_typed_accesses
        ]
    if row.operand_text:
        serialized["operand_text"] = row.operand_text
    if row.comment_parts:
        serialized["comment_parts"] = list(row.comment_parts)
    if row.comment_text:
        serialized["comment_text"] = row.comment_text
    if row.data_class is not None:
        serialized["data_class"] = row.data_class
    if row.structured_data is not None:
        serialized["structured_data"] = cast(dict[str, object], row.structured_data)
    return cast(SerializedRow, serialized)
