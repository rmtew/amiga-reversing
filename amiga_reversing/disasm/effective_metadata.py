from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import cast

from amiga_reversing.disasm.binary_source import (
    DiskEntryBinarySource,
    RawAddressModel,
    RawBinarySource,
    resolve_target_binary_source,
)
from amiga_reversing.disasm.decision_journal import decision_journal_report
from amiga_reversing.disasm.manual_actions import (
    ManualLabelScope,
    ManualSeedKind,
    ManualSeedMode,
    ReviewItemKind,
    load_manual_projection,
)
from amiga_reversing.disasm.source_numbers import parse_source_int
from amiga_reversing.disasm.target_metadata import (
    AbsoluteCodeLabelMetadata,
    CustomStructFieldMetadata,
    CustomStructMetadata,
    DataBlockElementKind,
    DataBlockElementMetadata,
    DataBlockLayoutMetadata,
    EntryCommentMetadata,
    EntryRegisterSeedKind,
    EntryRegisterSeedMetadata,
    ExecutionViewMetadata,
    ManualRepresentationMetadata,
    ManualRepresentationStyle,
    ManualRuntimeAddressRefMetadata,
    RssetLayoutRegionMetadata,
    RssetLayoutStorageKind,
    RssetUseSiteBindingMetadata,
    SeededCodeEntrypointMetadata,
    SeededCodeLabelMetadata,
    SeededEntityMetadata,
    SuppressedSeededItemMetadata,
    TargetEquateMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    apply_suppressed_seeded_items,
    load_target_metadata,
    target_metadata_json_payload,
)


def effective_target_metadata(target_dir: Path, *, include_decision_journal: bool = True) -> TargetMetadata | None:
    metadata = load_target_metadata(target_dir)
    metadata = _apply_manual_seed_projection(target_dir, metadata)
    if include_decision_journal:
        metadata = _apply_decision_journal_projection(target_dir, metadata)
    return metadata


def _manual_seed_int(seed: Mapping[str, object], field_name: str) -> int | None:
    value = seed.get(field_name)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return parse_source_int(value)
        except ValueError:
            return None
    return None


def _parse_manual_seed_range(seed: dict[str, object]) -> tuple[int, int, int | None] | None:
    hunk = _manual_seed_int(seed, "hunk") or 0
    addr = _manual_seed_int(seed, "addr")
    end = _manual_seed_int(seed, "end")
    if addr is not None:
        return hunk, addr, end
    raw_range = seed.get("range")
    if not isinstance(raw_range, str):
        return None
    range_text = raw_range.strip()
    if ":" in range_text:
        hunk_text, range_text = range_text.split(":", 1)
        if hunk_text.lower().startswith("h"):
            try:
                hunk = parse_source_int(hunk_text[1:])
            except ValueError:
                return None
    if ".." in range_text:
        start_text, end_text = range_text.split("..", 1)
        try:
            return hunk, parse_source_int(start_text), parse_source_int(end_text)
        except ValueError:
            return None
    try:
        return hunk, parse_source_int(range_text), None
    except ValueError:
        return None


def _manual_seed_text(seed: Mapping[str, object], field_name: str) -> str | None:
    value = seed.get(field_name)
    return value if isinstance(value, str) and value else None


def _mapping_sequence(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, str) or not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _manual_seed_name(seed: dict[str, object]) -> str:
    name = _manual_seed_text(seed, "name")
    if name is not None:
        return name
    seed_id = _manual_seed_text(seed, "seed_id") or "unnamed"
    safe = "".join(char if char.isalnum() or char == "_" else "_" for char in seed_id)
    return f"manual_seed_{safe}"


def _manual_seed_citation(seed: dict[str, object]) -> str:
    seed_id = _manual_seed_text(seed, "seed_id") or "unnamed"
    return f"manual_action_log:{seed_id}"


def _manual_seed_source_locator(seed: dict[str, object]) -> str:
    seed_id = _manual_seed_text(seed, "seed_id") or "unnamed"
    return f"ManualSeed:{seed_id}"


def _manual_label_source_locator(label: dict[str, object]) -> str:
    label_id = _manual_seed_text(label, "label_id") or "unnamed"
    return f"ManualLabel:{label_id}"


def _manual_comment_source_locator(comment: dict[str, object]) -> str:
    comment_id = _manual_seed_text(comment, "comment_id") or "unnamed"
    return f"ManualComment:{comment_id}"


def _manual_representation_source_locator(representation: dict[str, object]) -> str:
    representation_id = _manual_seed_text(representation, "representation_id") or "unnamed"
    return f"ManualRepresentation:{representation_id}"


def _manual_semantic_hint_source_locator(hint: dict[str, object]) -> str:
    hint_id = _manual_seed_text(hint, "semantic_hint_id") or "unnamed"
    return f"ManualSemanticHint:{hint_id}"


def _manual_action_citation(action_object: Mapping[str, object], id_field: str) -> str:
    action_id = _manual_seed_text(action_object, id_field) or "unnamed"
    return f"manual_action_log:{action_id}"


def _manual_seed_comment(seed: dict[str, object]) -> str | None:
    comment = _manual_seed_text(seed, "comment")
    if comment is not None:
        return comment
    details: list[str] = []
    for key in ("mode", "data_role", "unit", "encoding"):
        value = _manual_seed_text(seed, key)
        if value is not None:
            details.append(f"{key}={value}")
    return ", ".join(details) if details else None


def _manual_seed_to_code_entrypoint(seed: dict[str, object]) -> SeededCodeEntrypointMetadata | None:
    parsed_range = _parse_manual_seed_range(seed)
    if parsed_range is None:
        return None
    hunk, addr, _end = parsed_range
    return SeededCodeEntrypointMetadata(
        addr=addr,
        hunk=hunk,
        name=_manual_seed_name(seed),
        role=_manual_seed_text(seed, "role"),
        comment=_manual_seed_comment(seed),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_seed_citation(seed),
        source_id="manual_action_log",
        source_locator=_manual_seed_source_locator(seed),
    )


def _manual_seed_to_data_entity(seed: dict[str, object]) -> SeededEntityMetadata | None:
    parsed_range = _parse_manual_seed_range(seed)
    if parsed_range is None:
        return None
    hunk, addr, end = parsed_range
    return SeededEntityMetadata(
        addr=addr,
        end=end,
        hunk=hunk,
        name=_manual_seed_text(seed, "name"),
        comment=_manual_seed_comment(seed),
        type="data",
        subtype=_manual_seed_text(seed, "data_role"),
        unit=_manual_seed_text(seed, "unit"),
        encoding=_manual_seed_text(seed, "encoding"),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_seed_citation(seed),
        source_id="manual_action_log",
        source_locator=_manual_seed_source_locator(seed),
    )


def _manual_label_to_code_label(label: dict[str, object]) -> SeededCodeLabelMetadata | None:
    if _manual_seed_text(label, "address_domain") == "runtime":
        return None
    if label.get("scope") is ManualLabelScope.LOCAL:
        return None
    parsed_range = _parse_manual_seed_range(label)
    if parsed_range is None:
        return None
    hunk, addr, _end = parsed_range
    name = _manual_seed_text(label, "name")
    if name is None:
        return None
    return SeededCodeLabelMetadata(
        addr=addr,
        hunk=hunk,
        name=name,
        comment=_manual_seed_text(label, "comment"),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(label, "label_id"),
        source_id="manual_action_log",
        source_locator=_manual_label_source_locator(label),
    )


def _manual_label_to_absolute_code_label(label: dict[str, object]) -> AbsoluteCodeLabelMetadata | None:
    if _manual_seed_text(label, "address_domain") != "runtime":
        return None
    addr = _manual_seed_int(label, "addr")
    name = _manual_seed_text(label, "name")
    if addr is None or name is None:
        return None
    return AbsoluteCodeLabelMetadata(
        addr=addr,
        name=name,
        comment=_manual_seed_text(label, "comment"),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(label, "label_id"),
    )


def _manual_comment_to_entry_comment(comment: dict[str, object]) -> EntryCommentMetadata | None:
    parsed_range = _parse_manual_seed_range(comment)
    if parsed_range is None:
        return None
    hunk, addr, _end = parsed_range
    text = _manual_seed_text(comment, "text") or _manual_seed_text(comment, "comment")
    if text is None:
        return None
    return EntryCommentMetadata(
        addr=addr,
        hunk=hunk,
        comment=text,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(comment, "comment_id"),
        source_id="manual_action_log",
        source_locator=_manual_comment_source_locator(comment),
    )


def _manual_representation_to_metadata(representation: dict[str, object]) -> ManualRepresentationMetadata | None:
    parsed_range = _parse_manual_seed_range(representation)
    if parsed_range is None:
        return None
    style_text = _manual_seed_text(representation, "style")
    if style_text is None:
        return None
    hunk, addr, end = parsed_range
    try:
        style = ManualRepresentationStyle(style_text)
    except ValueError:
        return None
    return ManualRepresentationMetadata(
        addr=addr,
        end=end,
        hunk=hunk,
        style=style,
        element_kind=_manual_seed_text(representation, "element_kind"),
        operand_index=_manual_seed_int(representation, "operand_index"),
        symbol=_manual_seed_text(representation, "symbol"),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(representation, "representation_id"),
        source_id="manual_action_log",
        source_locator=_manual_representation_source_locator(representation),
    )


def _manual_semantic_hint_symbol(hint: dict[str, object]) -> str | None:
    domain = _manual_seed_text(hint, "domain")
    symbol = _manual_seed_text(hint, "symbol")
    if symbol is None:
        return None
    if domain == "equate":
        return symbol
    if domain == "lvo":
        function = _manual_seed_text(hint, "function")
        if function is None and "/" in symbol:
            function = symbol.rsplit("/", 1)[-1]
        if function is None:
            return None
        return function if function.startswith("_LVO") else f"_LVO{function}"
    if domain == "struct_offset":
        field = _manual_seed_text(hint, "field")
        if field is None and "." in symbol:
            field = symbol.rsplit(".", 1)[-1]
        if field is None:
            return None
        return field.upper()
    return None


def _manual_semantic_hint_to_representation(hint: dict[str, object]) -> ManualRepresentationMetadata | None:
    symbol = _manual_semantic_hint_symbol(hint)
    if symbol is None:
        return None
    parsed_range = _parse_manual_seed_range(hint)
    if parsed_range is None:
        return None
    hunk, addr, end = parsed_range
    return ManualRepresentationMetadata(
        addr=addr,
        end=end,
        hunk=hunk,
        style=ManualRepresentationStyle.SYMBOL,
        element_kind=_manual_seed_text(hint, "element_kind"),
        operand_index=_manual_seed_int(hint, "operand_index"),
        symbol=symbol,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(hint, "semantic_hint_id"),
        source_id="manual_action_log",
        source_locator=_manual_semantic_hint_source_locator(hint),
    )


def _manual_register_seed_to_metadata(register_seed: dict[str, object]) -> EntryRegisterSeedMetadata | None:
    register = _manual_seed_text(register_seed, "register")
    kind_text = _manual_seed_text(register_seed, "kind")
    if register is None or kind_text is None:
        return None
    try:
        kind = EntryRegisterSeedKind(kind_text)
    except ValueError:
        return None
    entry_offset = _manual_seed_int(register_seed, "entry_offset")
    path_lifetime_scope = register_seed.get("path_lifetime_scope")
    conflicts = register_seed.get("conflicts", [])
    parent_evidence_ids = register_seed.get("parent_evidence_ids", [])
    cleanup_scope = register_seed.get("cleanup_scope")
    return EntryRegisterSeedMetadata(
        entry_offset=entry_offset,
        register=register,
        kind=kind,
        note=_manual_seed_text(register_seed, "note") or _manual_action_citation(register_seed, "register_seed_id"),
        library_name=_manual_seed_text(register_seed, "library_name"),
        struct_name=_manual_seed_text(register_seed, "struct_name"),
        context_name=_manual_seed_text(register_seed, "context_name"),
        source_evidence_id=_manual_seed_text(register_seed, "source_evidence_id"),
        source_family=_manual_seed_text(register_seed, "source_family"),
        source_evidence_status=_manual_seed_text(register_seed, "source_evidence_status"),
        path_lifetime_scope=cast(dict[str, object], path_lifetime_scope) if isinstance(path_lifetime_scope, dict) else None,
        confidence=_manual_seed_text(register_seed, "confidence"),
        conflicts=tuple(cast(dict[str, object], item) for item in conflicts if isinstance(item, dict))
        if isinstance(conflicts, list | tuple)
        else (),
        parent_evidence_ids=tuple(item for item in parent_evidence_ids if isinstance(item, str))
        if isinstance(parent_evidence_ids, list | tuple)
        else (),
        contradicted_evidence_id=_manual_seed_text(register_seed, "contradicted_evidence_id"),
        reason=_manual_seed_text(register_seed, "reason"),
        cleanup_scope=cast(dict[str, object], cleanup_scope) if isinstance(cleanup_scope, dict) else None,
    )


def _manual_suppressed_seeded_item_to_metadata(item: dict[str, object]) -> SuppressedSeededItemMetadata | None:
    kind = _manual_seed_text(item, "kind")
    hunk = _manual_seed_int(item, "hunk")
    addr = _manual_seed_int(item, "addr")
    end = _manual_seed_int(item, "end")
    if kind is None or hunk is None or addr is None:
        return None
    try:
        payload = {"kind": kind, "hunk": hunk, "addr": addr}
        if end is not None:
            payload["end"] = end
        return SuppressedSeededItemMetadata.from_dict(payload)
    except AssertionError:
        return None


def _merge_seeded_entity_projection(
    existing: SeededEntityMetadata,
    override: SeededEntityMetadata,
) -> SeededEntityMetadata:
    return SeededEntityMetadata(
        addr=override.addr,
        hunk=override.hunk,
        end=override.end if override.end is not None else existing.end,
        name=override.name if override.name is not None else existing.name,
        comment=override.comment if override.comment is not None else existing.comment,
        type=override.type if override.type is not None else existing.type,
        subtype=override.subtype if override.subtype is not None else existing.subtype,
        unit=override.unit if override.unit is not None else existing.unit,
        encoding=override.encoding if override.encoding is not None else existing.encoding,
        seed_origin=override.seed_origin,
        review_status=override.review_status,
        citation=override.citation,
        source_id=override.source_id if override.source_id is not None else existing.source_id,
        source_path=override.source_path if override.source_path is not None else existing.source_path,
        source_locator=override.source_locator if override.source_locator is not None else existing.source_locator,
        struct_name=override.struct_name if override.struct_name is not None else existing.struct_name,
        field_name=override.field_name if override.field_name is not None else existing.field_name,
        field_type=override.field_type if override.field_type is not None else existing.field_type,
        c_type=override.c_type if override.c_type is not None else existing.c_type,
        pointer_struct=override.pointer_struct if override.pointer_struct is not None else existing.pointer_struct,
        value_domain=override.value_domain if override.value_domain is not None else existing.value_domain,
    )


def _seeded_entity_projection_key(entity: SeededEntityMetadata) -> tuple[int, int, int | None, str | None]:
    return (entity.hunk, entity.addr, entity.end, entity.type)


def _seeded_entity_projection_sort_key(key: tuple[int, int, int | None, str | None]) -> tuple[int, int, int, str]:
    hunk, addr, end, entity_type = key
    return (hunk, addr, -1 if end is None else end, entity_type or "")


def _merge_projected_seeded_entities(
    entities: list[SeededEntityMetadata],
) -> tuple[SeededEntityMetadata, ...]:
    merged: dict[tuple[int, int, int | None, str | None], SeededEntityMetadata] = {}
    for entity in entities:
        key = _seeded_entity_projection_key(entity)
        existing = merged.get(key)
        merged[key] = entity if existing is None else _merge_seeded_entity_projection(existing, entity)
    return tuple(merged[key] for key in sorted(merged, key=_seeded_entity_projection_sort_key))


def _manual_execution_view_to_metadata(view: dict[str, object]) -> ExecutionViewMetadata | None:
    source_start = _manual_seed_int(view, "source_start")
    source_end = _manual_seed_int(view, "source_end")
    base_addr = _manual_seed_int(view, "base_addr")
    name = _manual_seed_text(view, "name")
    if source_start is None or source_end is None or base_addr is None or name is None:
        return None
    if source_start < 0 or source_end <= source_start or base_addr < 0:
        return None
    return ExecutionViewMetadata(
        source_start=source_start,
        source_end=source_end,
        base_addr=base_addr,
        name=name,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(view, "execution_view_id"),
        comment=_manual_seed_text(view, "comment"),
    )


def _manual_target_equate_to_metadata(equate: dict[str, object]) -> TargetEquateMetadata | None:
    name = _manual_seed_text(equate, "name")
    value = _manual_seed_int(equate, "value")
    if name is None or value is None:
        return None
    representation_text = _manual_seed_text(equate, "value_representation")
    try:
        value_representation = None if representation_text is None else ManualRepresentationStyle(representation_text)
    except ValueError:
        return None
    return TargetEquateMetadata(
        name=name,
        value=value,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(equate, "target_equate_id"),
        comment=_manual_seed_text(equate, "comment"),
        value_representation=value_representation,
        value_expression=_manual_seed_text(equate, "value_expression"),
    )


def _manual_target_equate_rename(equate: dict[str, object]) -> tuple[str, str] | None:
    previous_name = _manual_seed_text(equate, "previous_name")
    name = _manual_seed_text(equate, "name")
    if previous_name is None or name is None:
        return None
    return previous_name, name


def _renamed_target_equate_symbol(symbol: str, renames: Mapping[str, str]) -> str:
    current = symbol
    seen = {current}
    while current in renames:
        current = renames[current]
        if current in seen:
            break
        seen.add(current)
    return current


def _manual_custom_struct_field_to_metadata(field: dict[str, object]) -> CustomStructFieldMetadata | None:
    name = _manual_seed_text(field, "name")
    field_type = _manual_seed_text(field, "type")
    offset = _manual_seed_int(field, "offset")
    size = _manual_seed_int(field, "size")
    if name is None or field_type is None or offset is None or size is None:
        return None
    if offset < 0 or size <= 0:
        return None
    return CustomStructFieldMetadata(
        name=name,
        type=field_type,
        offset=offset,
        size=size,
        available_since=_manual_seed_text(field, "available_since") or "1.0",
        struct=_manual_seed_text(field, "struct"),
        pointer_struct=_manual_seed_text(field, "pointer_struct"),
        named_base=_manual_seed_text(field, "named_base"),
    )


def _manual_custom_struct_to_metadata(struct: dict[str, object]) -> CustomStructMetadata | None:
    name = _manual_seed_text(struct, "name")
    size = _manual_seed_int(struct, "size")
    if name is None or size is None or size <= 0:
        return None
    raw_fields = struct.get("fields", ())
    if not isinstance(raw_fields, list | tuple):
        return None
    fields: list[CustomStructFieldMetadata] = []
    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            return None
        field = _manual_custom_struct_field_to_metadata(raw_field)
        if field is None:
            return None
        fields.append(field)
    base_offset = _manual_seed_int(struct, "base_offset")
    return CustomStructMetadata(
        name=name,
        size=size,
        fields=tuple(fields),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=f"manual_action_log:{_manual_seed_text(struct, 'custom_struct_id') or name}",
        source="manual_action_log",
        base_offset=base_offset if base_offset is not None else 0,
        base_struct=_manual_seed_text(struct, "base_struct"),
        available_since=_manual_seed_text(struct, "available_since") or "1.0",
    )


def _manual_custom_struct_field_container_name(field: dict[str, object]) -> str | None:
    return _manual_seed_text(field, "struct_name")


def _manual_custom_struct_field_key(field: dict[str, object]) -> tuple[str, int] | None:
    struct_name = _manual_custom_struct_field_container_name(field)
    offset = _manual_seed_int(field, "offset")
    if struct_name is None or offset is None or offset < 0:
        return None
    return struct_name, offset


def _manual_custom_struct_rename(struct: dict[str, object]) -> tuple[str, str] | None:
    previous_name = _manual_seed_text(struct, "previous_name")
    name = _manual_seed_text(struct, "name")
    if previous_name is None or name is None:
        return None
    return previous_name, name


def _custom_struct_with_manual_field_projection(
    struct: CustomStructMetadata,
    field_projections: tuple[dict[str, object], ...],
    removed_field_keys: set[tuple[str, int]],
    renamed_fields: dict[tuple[str, int], str],
) -> CustomStructMetadata:
    fields = [
        replace(field, name=renamed_fields.get((struct.name, field.offset), field.name))
        for field in struct.fields
        if (struct.name, field.offset) not in removed_field_keys
    ]
    for raw_field in field_projections:
        if _manual_custom_struct_field_container_name(raw_field) != struct.name:
            continue
        field = _manual_custom_struct_field_to_metadata(raw_field)
        if field is not None:
            fields.append(field)
    merged_fields = {field.offset: field for field in fields}
    return replace(struct, fields=tuple(merged_fields.values()))


def _manual_rsset_layout_region_to_metadata(region: dict[str, object]) -> RssetLayoutRegionMetadata | None:
    offset = _manual_seed_int(region, "offset")
    if offset is None or offset < 0 or offset > 0x7FFF:
        return None
    symbol = _manual_seed_text(region, "symbol")
    if symbol is None:
        return None
    size = _manual_seed_int(region, "size")
    if size is not None and (size <= 0 or size > 255):
        return None
    storage_kind_text = _manual_seed_text(region, "storage_kind")
    try:
        storage_kind = None if storage_kind_text is None else RssetLayoutStorageKind(storage_kind_text)
    except ValueError:
        return None
    return RssetLayoutRegionMetadata(
        offset=offset,
        size=size,
        layout_name=_manual_seed_text(region, "layout_name"),
        base_symbol=_manual_seed_text(region, "base_symbol"),
        sizeof_symbol=_manual_seed_text(region, "sizeof_symbol"),
        symbol=symbol,
        struct_name=_manual_seed_text(region, "struct_name"),
        pointer_struct=_manual_seed_text(region, "pointer_struct"),
        storage_kind=storage_kind,
        semantic_type=_manual_seed_text(region, "semantic_type"),
        parser_role=_manual_seed_text(region, "parser_role"),
        parser_routine=_manual_seed_text(region, "parser_routine"),
        parse_order=_manual_seed_int(region, "parse_order"),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(region, "rsset_layout_region_id"),
    )


def _manual_rsset_layout_region_key(region: dict[str, object]) -> tuple[str, str, int] | None:
    offset = _manual_seed_int(region, "offset")
    if offset is None or offset < 0:
        return None
    return (
        _manual_seed_text(region, "layout_name") or "app",
        _manual_seed_text(region, "base_symbol") or "__amiga_app_base__",
        offset,
    )


def _manual_rsset_use_site_binding_to_metadata(binding: dict[str, object]) -> RssetUseSiteBindingMetadata | None:
    hunk = _manual_seed_int(binding, "hunk")
    addr = _manual_seed_int(binding, "addr")
    operand_index = _manual_seed_int(binding, "operand_index")
    displacement = _manual_seed_int(binding, "displacement")
    base_register = _manual_seed_text(binding, "base_register")
    layout_name = _manual_seed_text(binding, "layout_name")
    base_symbol = _manual_seed_text(binding, "base_symbol")
    base_evidence_id = _manual_seed_text(binding, "base_evidence_id")
    if (
        hunk is None
        or hunk < 0
        or addr is None
        or addr < 0
        or operand_index is None
        or operand_index < 0
        or displacement is None
        or displacement < 0
        or displacement > 0x7FFF
        or base_register is None
        or layout_name is None
        or base_symbol is None
        or base_evidence_id is None
    ):
        return None
    base_evidence_refs = binding.get("base_evidence_refs")
    return RssetUseSiteBindingMetadata(
        hunk=hunk,
        addr=addr,
        operand_index=operand_index,
        base_register=base_register.upper(),
        displacement=displacement,
        layout_name=layout_name,
        base_symbol=base_symbol,
        base_evidence_id=base_evidence_id,
        binding_id=_manual_seed_text(binding, "rsset_use_site_binding_id"),
        access=_manual_seed_text(binding, "access"),
        width_bytes=_manual_seed_int(binding, "width_bytes"),
        owner_action_id=_manual_seed_text(binding, "owner_action_id"),
        source_evidence_id=_manual_seed_text(binding, "source_evidence_id"),
        source_family=_manual_seed_text(binding, "source_family"),
        source_evidence_status=_manual_seed_text(binding, "source_evidence_status"),
        path_lifetime_scope=cast(dict[str, object], binding.get("path_lifetime_scope"))
        if isinstance(binding.get("path_lifetime_scope"), dict)
        else None,
        confidence=_manual_seed_text(binding, "confidence"),
        base_evidence_refs=tuple(
            dict(ref)
            for ref in base_evidence_refs
            if isinstance(ref, dict)
        )
        if isinstance(base_evidence_refs, list | tuple)
        else (),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(binding, "rsset_use_site_binding_id"),
    )


def _manual_data_block_element_to_metadata(
    element: dict[str, object],
    reference_interpretations: Mapping[tuple[str, int], dict[str, object]] | None = None,
) -> DataBlockElementMetadata | None:
    layout_id = _manual_seed_text(element, "layout_id")
    offset = _manual_seed_int(element, "offset")
    width = _manual_seed_int(element, "width")
    kind_text = _manual_seed_text(element, "kind")
    if layout_id is None or offset is None or width is None or kind_text is None:
        return None
    if offset < 0 or width <= 0:
        return None
    array_count = _manual_seed_int(element, "array_count")
    array_stride = _manual_seed_int(element, "array_stride")
    if array_count is not None and array_count <= 0:
        return None
    if array_stride is not None and array_stride <= 0:
        return None
    representation_text = _manual_seed_text(element, "representation")
    try:
        kind = DataBlockElementKind(kind_text)
        representation = None if representation_text is None else ManualRepresentationStyle(representation_text)
    except ValueError:
        return None
    type_binding = element.get("type_binding")
    reference_interpretation = element.get("reference_interpretation")
    if reference_interpretations is not None:
        reference_interpretation = reference_interpretations.get((layout_id, offset), reference_interpretation)
    provenance = element.get("provenance")
    if type_binding is not None and not isinstance(type_binding, dict):
        return None
    if reference_interpretation is not None and not isinstance(reference_interpretation, dict):
        return None
    if provenance is not None and not isinstance(provenance, dict):
        return None
    return DataBlockElementMetadata(
        layout_id=layout_id,
        offset=offset,
        width=width,
        kind=kind,
        name=_manual_seed_text(element, "name"),
        array_count=array_count,
        array_stride=array_stride,
        representation=representation,
        type_binding=type_binding,
        reference_interpretation=reference_interpretation,
        provenance=provenance,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(element, "data_block_element_id"),
    )


def _manual_data_block_layout_to_metadata(
    layout: dict[str, object],
    elements: tuple[dict[str, object], ...],
    reference_interpretations: Mapping[tuple[str, int], dict[str, object]] | None = None,
) -> DataBlockLayoutMetadata | None:
    layout_id = _manual_seed_text(layout, "layout_id")
    hunk = _manual_seed_int(layout, "hunk")
    source_start = _manual_seed_int(layout, "source_start")
    source_end = _manual_seed_int(layout, "source_end")
    if layout_id is None or hunk is None or source_start is None or source_end is None:
        return None
    if hunk < 0 or source_start < 0 or source_end <= source_start:
        return None
    runtime_start = _manual_seed_int(layout, "runtime_start")
    runtime_end = _manual_seed_int(layout, "runtime_end")
    if runtime_start is not None and runtime_start < 0:
        return None
    if runtime_end is not None and (runtime_start is None or runtime_end <= runtime_start):
        return None
    version = _manual_seed_int(layout, "version")
    if version is None:
        version = 1
    if version <= 0:
        return None
    provenance = layout.get("provenance")
    if provenance is not None and not isinstance(provenance, dict):
        return None
    projected_elements = tuple(
        element
        for raw_element in elements
        if raw_element.get("layout_id") == layout_id
        if (element := _manual_data_block_element_to_metadata(raw_element, reference_interpretations)) is not None
    )
    try:
        return DataBlockLayoutMetadata(
            layout_id=layout_id,
            hunk=hunk,
            source_start=source_start,
            source_end=source_end,
            runtime_execution_view_id=_manual_seed_text(layout, "runtime_execution_view_id"),
            runtime_start=runtime_start,
            runtime_end=runtime_end,
            role=_manual_seed_text(layout, "role"),
            name=_manual_seed_text(layout, "name"),
            default_unit=_manual_seed_text(layout, "default_unit"),
            version=version,
            provenance=provenance,
            elements=projected_elements,
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.SEEDED,
            citation=_manual_action_citation(layout, "layout_id"),
        )
    except AssertionError:
        return None


def _manual_data_block_layout_key(layout: dict[str, object]) -> str | None:
    return _manual_seed_text(layout, "layout_id")


def _manual_data_block_element_key(element: dict[str, object]) -> tuple[str, int] | None:
    layout_id = _manual_seed_text(element, "layout_id")
    offset = _manual_seed_int(element, "offset")
    if layout_id is None or offset is None or offset < 0:
        return None
    return layout_id, offset


def _manual_data_block_reference_interpretations(
    refs: tuple[dict[str, object], ...],
) -> dict[tuple[str, int], dict[str, object]]:
    interpretations: dict[tuple[str, int], dict[str, object]] = {}
    for ref in refs:
        key = _manual_data_block_element_key(ref)
        if key is not None:
            interpretations[key] = dict(ref)
    return interpretations


def _manual_data_block_reference_id(ref: Mapping[str, object]) -> str | None:
    for field_name in ("data_block_ref_id", "interpreted_ref_id"):
        value = ref.get(field_name)
        if isinstance(value, str) and value:
            return value
    return None


def _manual_data_block_reference_removals(
    refs: tuple[dict[str, object], ...],
) -> dict[tuple[str, int], set[str]]:
    removals: dict[tuple[str, int], set[str]] = {}
    for ref in refs:
        key = _manual_data_block_element_key(ref)
        ref_id = _manual_data_block_reference_id(ref)
        if key is not None and ref_id is not None:
            removals.setdefault(key, set()).add(ref_id)
    return removals


def _data_block_element_ref_is_removed(
    element: DataBlockElementMetadata,
    removals: Mapping[tuple[str, int], set[str]],
) -> bool:
    removed_ids = removals.get((element.layout_id, element.offset))
    if not removed_ids or not isinstance(element.reference_interpretation, dict):
        return False
    ref_id = _manual_data_block_reference_id(element.reference_interpretation)
    return ref_id in removed_ids


def _data_block_element_span(layout: DataBlockLayoutMetadata, element: DataBlockElementMetadata) -> tuple[int, int]:
    return layout.source_start + element.offset, layout.source_start + element.offset + element.width


def _data_block_element_unit(layout: DataBlockLayoutMetadata, element: DataBlockElementMetadata) -> str:
    if element.kind is DataBlockElementKind.SCALAR:
        return _data_block_unit_from_width(element.width)
    if element.kind is DataBlockElementKind.ARRAY and element.array_stride in {1, 2, 4}:
        return _data_block_unit_from_width(element.array_stride)
    default_unit = layout.default_unit
    if isinstance(default_unit, str) and default_unit in {"byte", "word", "long"}:
        return default_unit
    return _data_block_unit_from_width(element.width)


def _data_block_unit_from_width(width: int) -> str:
    if width == 4:
        return "long"
    if width == 2:
        return "word"
    return "byte"


def _data_block_bound_custom_struct(
    element: DataBlockElementMetadata,
    custom_structs: Mapping[str, CustomStructMetadata],
) -> CustomStructMetadata | None:
    binding = element.type_binding
    if not isinstance(binding, dict) or binding.get("binding_kind") != "custom_struct":
        return None
    bound_type = binding.get("bound_type_id")
    if not isinstance(bound_type, str) or not bound_type:
        return None
    return custom_structs.get(bound_type)


def _json_object_pairs_last(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        result[key] = value
    return result


@lru_cache(maxsize=1)
def _amiga_ndk_include_data() -> Mapping[str, object]:
    path = Path(__file__).resolve().parents[2] / "knowledge" / "amiga_ndk_includes_parsed.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_json_object_pairs_last)
    return data if isinstance(data, dict) else {}


def _mapping_value(payload: Mapping[str, object], key: str) -> Mapping[str, object] | None:
    value = payload.get(key)
    return value if isinstance(value, dict) else None


def _platform_struct_payload(struct_name: str) -> tuple[str, Mapping[str, object]] | None:
    data = _amiga_ndk_include_data()
    structs = _mapping_value(data, "structs")
    if structs is None:
        return None
    name = struct_name.strip()
    payload = structs.get(name)
    if isinstance(payload, dict):
        return name, payload
    meta = _mapping_value(data, "_meta")
    aliases = _mapping_value(meta, "struct_name_map") if meta is not None else None
    alias = aliases.get(name) if aliases is not None else None
    if not isinstance(alias, str) or not alias:
        return None
    payload = structs.get(alias)
    if isinstance(payload, dict):
        return alias, payload
    return None


def _platform_struct_field_metadata(
    raw_field: Mapping[str, object],
    *,
    name_prefix: str = "",
    offset_base: int = 0,
) -> CustomStructFieldMetadata | None:
    name = raw_field.get("name")
    field_type = raw_field.get("type")
    offset = raw_field.get("offset")
    size = raw_field.get("size")
    pointer_struct = raw_field.get("pointer_struct")
    if not isinstance(name, str) or not name:
        return None
    if not isinstance(field_type, str) or not field_type:
        return None
    if not isinstance(offset, int) or not isinstance(size, int) or size <= 0:
        return None
    if pointer_struct is not None and not isinstance(pointer_struct, str):
        pointer_struct = None
    return CustomStructFieldMetadata(
        name=f"{name_prefix}{name}",
        type=field_type,
        offset=offset_base + offset,
        size=size,
        pointer_struct=pointer_struct,
    )


def _platform_struct_fields(
    struct_name: str,
    *,
    name_prefix: str = "",
    offset_base: int = 0,
    seen: frozenset[str] = frozenset(),
) -> tuple[CustomStructFieldMetadata, ...]:
    resolved = _platform_struct_payload(struct_name)
    if resolved is None:
        return ()
    canonical_name, payload = resolved
    if canonical_name in seen:
        return ()
    next_seen = seen | {canonical_name}
    fields: list[CustomStructFieldMetadata] = []
    base_struct = payload.get("base_struct")
    if isinstance(base_struct, str) and base_struct:
        fields.extend(
            _platform_struct_fields(base_struct, name_prefix=name_prefix, offset_base=offset_base, seen=next_seen)
        )
    raw_fields = payload.get("fields")
    if not isinstance(raw_fields, list):
        return tuple(fields)
    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue
        nested_struct = raw_field.get("struct")
        if raw_field.get("type") == "STRUCT" and isinstance(nested_struct, str) and nested_struct:
            nested_offset = raw_field.get("offset")
            nested_name = raw_field.get("name")
            if isinstance(nested_offset, int) and isinstance(nested_name, str) and nested_name:
                nested_fields = _platform_struct_fields(
                    nested_struct,
                    name_prefix=f"{name_prefix}{nested_name}.",
                    offset_base=offset_base + nested_offset,
                    seen=next_seen,
                )
                if nested_fields:
                    fields.extend(nested_fields)
                    continue
        field = _platform_struct_field_metadata(raw_field, name_prefix=name_prefix, offset_base=offset_base)
        if field is not None:
            fields.append(field)
    return tuple(fields)


@lru_cache(maxsize=256)
def _platform_struct_metadata(struct_name: str) -> CustomStructMetadata | None:
    resolved = _platform_struct_payload(struct_name)
    if resolved is None:
        return None
    canonical_name, payload = resolved
    size = payload.get("size")
    if not isinstance(size, int) or size <= 0:
        return None
    return CustomStructMetadata(
        name=canonical_name,
        size=size,
        fields=_platform_struct_fields(canonical_name),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=f"amiga_ndk_includes_parsed:{canonical_name}",
        source="parsed_ndk_include",
    )


def _data_block_bound_platform_struct(element: DataBlockElementMetadata) -> CustomStructMetadata | None:
    binding = element.type_binding
    if not isinstance(binding, dict) or binding.get("binding_kind") != "platform_struct":
        return None
    bound_type = binding.get("bound_type_id")
    if not isinstance(bound_type, str) or not bound_type:
        return None
    return _platform_struct_metadata(bound_type)


def _data_block_bound_struct(
    element: DataBlockElementMetadata,
    custom_structs: Mapping[str, CustomStructMetadata],
) -> CustomStructMetadata | None:
    return _data_block_bound_custom_struct(element, custom_structs) or _data_block_bound_platform_struct(element)


def _data_block_bound_value_domain(element: DataBlockElementMetadata) -> str | None:
    binding = element.type_binding
    if not isinstance(binding, dict) or binding.get("binding_kind") not in {"enum_domain", "equate_domain"}:
        return None
    bound_domain = binding.get("bound_domain_id")
    if not isinstance(bound_domain, str) or not bound_domain:
        return None
    return bound_domain


def _data_block_type_binding_locator(element: DataBlockElementMetadata) -> str | None:
    binding = element.type_binding
    if not isinstance(binding, dict):
        return None
    binding_id = binding.get("type_binding_id")
    if binding_id is None:
        return None
    return str(binding_id)


def _data_block_type_binding_parent_evidence_ids(element: DataBlockElementMetadata) -> tuple[str, ...]:
    binding = element.type_binding
    if not isinstance(binding, dict):
        return ()
    parent_ids = binding.get("parent_evidence_ids")
    if not isinstance(parent_ids, list | tuple):
        return ()
    return tuple(item for item in parent_ids if isinstance(item, str) and item)


def _data_block_type_binding_text(element: DataBlockElementMetadata, field_name: str) -> str | None:
    binding = element.type_binding
    if not isinstance(binding, dict):
        return None
    return _manual_seed_text(binding, field_name)


def _data_block_typed_field_label(base_label: str | None, field_name: str, index: int | None) -> str | None:
    if not base_label:
        return None
    suffix = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in field_name).strip("_")
    if not suffix:
        return None
    label = f"{base_label}_{suffix}"
    if index is not None:
        label = f"{label}_{index}"
    if label[0].isdigit():
        label = f"dblk_{label}"
    return label if len(label) < 64 else None


def _data_block_typed_gap_label(base_label: str | None, offset: int, index: int | None) -> str | None:
    if not base_label:
        return None
    label = f"{base_label}_gap_{offset:X}"
    if index is not None:
        label = f"{label}_{index}"
    if label[0].isdigit():
        label = f"dblk_{label}"
    return label if len(label) < 64 else None


def _data_block_custom_struct_field_entity(
    layout: DataBlockLayoutMetadata,
    element: DataBlockElementMetadata,
    struct: CustomStructMetadata,
    field: CustomStructFieldMetadata,
    instance_offset: int,
    instance_index: int | None,
    base_label: str | None,
) -> SeededEntityMetadata | None:
    if field.offset < 0 or field.size <= 0:
        return None
    relative_end = instance_offset + field.offset + field.size
    if relative_end > element.width:
        return None
    addr = layout.source_start + element.offset + instance_offset + field.offset
    end = addr + field.size
    if end > layout.source_end:
        return None
    return SeededEntityMetadata(
        addr=addr,
        end=end,
        hunk=layout.hunk,
        name=_data_block_typed_field_label(base_label, field.name, instance_index),
        type="data",
        unit=_data_block_unit_from_width(field.size),
        struct_name=struct.name,
        field_name=field.name,
        field_type=field.type,
        c_type=field.type,
        pointer_struct=field.pointer_struct,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=element.citation,
        source_id="manual_action_log",
        source_locator=_data_block_type_binding_locator(element),
        owner_action_id=_data_block_type_binding_text(element, "owner_action_id"),
        source_evidence_id=_data_block_type_binding_text(element, "source_evidence_id"),
        parent_evidence_ids=_data_block_type_binding_parent_evidence_ids(element),
    )


def _data_block_custom_struct_gap_entity(
    layout: DataBlockLayoutMetadata,
    element: DataBlockElementMetadata,
    offset: int,
    width: int,
    instance_index: int | None,
    base_label: str | None,
) -> SeededEntityMetadata | None:
    if width <= 0:
        return None
    if offset < 0 or offset + width > element.width:
        return None
    addr = layout.source_start + element.offset + offset
    end = addr + width
    if end > layout.source_end:
        return None
    return SeededEntityMetadata(
        addr=addr,
        end=end,
        hunk=layout.hunk,
        name=_data_block_typed_gap_label(base_label, offset, instance_index),
        comment="typed data block gap",
        type="data",
        unit=_data_block_unit_from_width(width),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=element.citation,
        source_id="manual_action_log",
        source_locator=_data_block_type_binding_locator(element),
        owner_action_id=_data_block_type_binding_text(element, "owner_action_id"),
        source_evidence_id=_data_block_type_binding_text(element, "source_evidence_id"),
        parent_evidence_ids=_data_block_type_binding_parent_evidence_ids(element),
    )


def _data_block_bound_struct_entities(
    layout: DataBlockLayoutMetadata,
    element: DataBlockElementMetadata,
    custom_structs: Mapping[str, CustomStructMetadata],
) -> tuple[SeededEntityMetadata, ...]:
    struct = _data_block_bound_struct(element, custom_structs)
    if struct is None or struct.size <= 0:
        return ()
    binding = element.type_binding if isinstance(element.type_binding, dict) else {}
    array_count = _manual_seed_int(binding, "array_count") or element.array_count or 1
    stride = element.array_stride or struct.size
    if array_count <= 0 or stride <= 0 or stride < struct.size:
        return ()
    if (array_count - 1) * stride + struct.size > element.width:
        return ()
    # The start of a typed layout is the object's public identity.  Element
    # names such as "fields" or "shared_fields" describe only the projection
    # plumbing and must not hide that identity in generated field labels.
    base_label = layout.name if element.offset == 0 and layout.name else element.name
    entities: list[SeededEntityMetadata] = []
    for index in range(array_count):
        instance_offset = index * stride
        instance_index = index if array_count > 1 else None
        cursor = 0
        for field in sorted(struct.fields, key=lambda item: item.offset):
            if field.offset < cursor:
                return ()
            if field.offset + field.size > struct.size:
                return ()
            gap_width = field.offset - cursor
            if gap_width:
                gap = _data_block_custom_struct_gap_entity(
                    layout, element, instance_offset + cursor, gap_width, instance_index, base_label
                )
                if gap is None:
                    return ()
                entities.append(gap)
            field_entity = _data_block_custom_struct_field_entity(
                layout, element, struct, field, instance_offset, instance_index, base_label
            )
            if field_entity is None:
                return ()
            entities.append(field_entity)
            cursor = field.offset + field.size
        if cursor < struct.size:
            gap = _data_block_custom_struct_gap_entity(
                layout, element, instance_offset + cursor, struct.size - cursor, instance_index, base_label
            )
            if gap is None:
                return ()
            entities.append(gap)
    covered = (array_count - 1) * stride + struct.size
    if covered < element.width:
        gap = _data_block_custom_struct_gap_entity(layout, element, covered, element.width - covered, None, base_label)
        if gap is None:
            return ()
        entities.append(gap)
    return tuple(entities)


def _data_block_element_entity(
    layout: DataBlockLayoutMetadata,
    element: DataBlockElementMetadata,
) -> SeededEntityMetadata | None:
    addr, end = _data_block_element_span(layout, element)
    if end <= addr or end > layout.source_end:
        return None
    name = element.name or (layout.name if element.offset == 0 else None)
    comment = layout.role
    value_domain = _data_block_bound_value_domain(element)
    return SeededEntityMetadata(
        addr=addr,
        end=end,
        hunk=layout.hunk,
        name=name,
        comment=comment,
        type="data",
        subtype=layout.role,
        unit=_data_block_element_unit(layout, element),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=element.citation,
        source_id="manual_action_log" if value_domain is not None else None,
        source_locator=_data_block_type_binding_locator(element) if value_domain is not None else None,
        value_domain=value_domain,
        owner_action_id=_data_block_type_binding_text(element, "owner_action_id") if value_domain is not None else None,
        source_evidence_id=_data_block_type_binding_text(element, "source_evidence_id") if value_domain is not None else None,
        parent_evidence_ids=_data_block_type_binding_parent_evidence_ids(element) if value_domain is not None else (),
    )


def _data_block_element_representation(
    layout: DataBlockLayoutMetadata,
    element: DataBlockElementMetadata,
) -> ManualRepresentationMetadata | None:
    if element.representation is None:
        return None
    addr, end = _data_block_element_span(layout, element)
    if end <= addr or end > layout.source_end:
        return None
    return ManualRepresentationMetadata(
        addr=addr,
        end=end,
        hunk=layout.hunk,
        style=element.representation,
        element_kind="data_block_element",
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=element.citation,
    )


def _data_block_interpreted_ref_symbol(ref: Mapping[str, object]) -> str | None:
    if ref.get("reference_kind") != "absolute":
        return None
    width = _manual_seed_int(ref, "width")
    target_hunk = _manual_seed_int(ref, "target_hunk")
    target_offset = _manual_seed_int(ref, "target_offset")
    source_value = _manual_seed_int(ref, "source_value")
    target_locator = ref.get("target_locator")
    if width not in {1, 2, 4} or target_hunk is None or target_hunk < 0:
        return None
    if target_offset is None or target_offset < 0 or source_value is None or source_value < 0:
        return None
    if source_value != target_offset or source_value >= (1 << (width * 8)):
        return None
    if not isinstance(target_locator, Mapping):
        return None
    if _manual_seed_int(target_locator, "hunk") != target_hunk:
        return None
    if _manual_seed_int(target_locator, "offset") != target_offset:
        return None
    return f"dblk_ref_h{target_hunk}_{target_offset:08X}"


def _data_block_interpreted_ref_equate(ref: Mapping[str, object]) -> TargetEquateMetadata | None:
    symbol = _data_block_interpreted_ref_symbol(ref)
    target_offset = _manual_seed_int(ref, "target_offset")
    if symbol is None or target_offset is None:
        return None
    return TargetEquateMetadata(
        name=symbol,
        value=target_offset,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(ref, "data_block_ref_id"),
        comment="data-block interpreted absolute reference",
    )


def _data_block_element_interpreted_ref_representation(
    layout: DataBlockLayoutMetadata,
    element: DataBlockElementMetadata,
) -> ManualRepresentationMetadata | None:
    if not isinstance(element.reference_interpretation, dict):
        return None
    symbol = _data_block_interpreted_ref_symbol(element.reference_interpretation)
    if symbol is None:
        return None
    addr, end = _data_block_element_span(layout, element)
    if end <= addr or end > layout.source_end:
        return None
    width = _manual_seed_int(element.reference_interpretation, "width")
    if width not in {1, 2, 4} or end - addr != width:
        return None
    return ManualRepresentationMetadata(
        addr=addr,
        end=end,
        hunk=layout.hunk,
        style=ManualRepresentationStyle.SYMBOL,
        element_kind="data_block_interpreted_ref",
        symbol=symbol,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(element.reference_interpretation, "data_block_ref_id"),
        source_id="manual_action_log",
        source_locator=_manual_data_block_reference_id(element.reference_interpretation),
    )


def _data_block_element_interpreted_ref_runtime_address_ref(
    layout: DataBlockLayoutMetadata,
    element: DataBlockElementMetadata,
) -> ManualRuntimeAddressRefMetadata | None:
    ref = element.reference_interpretation
    if not isinstance(ref, dict):
        return None
    if _data_block_interpreted_ref_symbol(ref) is None:
        return None
    mode = ref.get("xref_generation_mode") or "bidirectional"
    if mode not in {"bidirectional", "source_only"}:
        return None
    addr, end = _data_block_element_span(layout, element)
    width = _manual_seed_int(ref, "width")
    target_hunk = _manual_seed_int(ref, "target_hunk")
    target_offset = _manual_seed_int(ref, "target_offset")
    if end <= addr or end > layout.source_end or width not in {1, 2, 4} or end - addr != width:
        return None
    if target_hunk is None or target_offset is None:
        return None
    confidence = ref.get("confidence")
    confidence_id = {"manual": 3, "high": 3, "medium": 2, "low": 1}.get(str(confidence or "manual"), 3)
    ref_id = _manual_data_block_reference_id(ref)
    layout_id = ref.get("layout_id")
    offset = _manual_seed_int(ref, "offset")
    if ref_id is None or not isinstance(layout_id, str) or offset is None:
        return None
    return ManualRuntimeAddressRefMetadata(
        addr=addr,
        hunk=layout.hunk,
        size=width,
        target_hunk=target_hunk,
        target_offset=target_offset,
        runtime_address=target_offset,
        confidence=confidence_id,
        owner_kind="data_block_interpreted_ref",
        owner_id=ref_id,
        owner_layout_id=layout_id,
        owner_element_offset=offset,
        xref_generation_mode=str(mode),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(ref, "data_block_ref_id"),
    )


def _immediate_interpreted_ref_symbol(ref: Mapping[str, object]) -> str | None:
    explicit = _manual_seed_text(ref, "symbol")
    if explicit is not None:
        return explicit
    target_hunk = _manual_seed_int(ref, "target_hunk")
    target_offset = _manual_seed_int(ref, "target_offset")
    runtime_address = _manual_seed_int(ref, "runtime_address")
    if target_hunk is None or target_offset is None:
        return None
    if runtime_address is not None:
        return f"imm_ref_h{target_hunk}_{target_offset:08X}_rt_{runtime_address:08X}"
    return f"imm_ref_h{target_hunk}_{target_offset:08X}"


def _immediate_interpreted_ref_equate(ref: Mapping[str, object]) -> TargetEquateMetadata | None:
    symbol = _immediate_interpreted_ref_symbol(ref)
    value = _manual_seed_int(ref, "source_value")
    if symbol is None or value is None:
        return None
    return TargetEquateMetadata(
        name=symbol,
        value=value,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(ref, "immediate_ref_id"),
        comment="immediate interpreted absolute reference",
    )


def _immediate_interpreted_ref_representation(ref: Mapping[str, object]) -> ManualRepresentationMetadata | None:
    symbol = _immediate_interpreted_ref_symbol(ref)
    hunk = _manual_seed_int(ref, "hunk")
    addr = _manual_seed_int(ref, "addr")
    end = _manual_seed_int(ref, "end")
    operand_index = _manual_seed_int(ref, "operand_index")
    if symbol is None or hunk is None or addr is None or end is None or end <= addr:
        return None
    if operand_index is None or operand_index < 0:
        return None
    return ManualRepresentationMetadata(
        addr=addr,
        end=end,
        hunk=hunk,
        style=ManualRepresentationStyle.SYMBOL,
        element_kind="immediate_interpreted_ref",
        operand_index=operand_index,
        symbol=symbol,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(ref, "immediate_ref_id"),
        source_id="manual_action_log",
        source_locator=str(ref.get("immediate_ref_id") or ""),
    )


def _a5_hardware_ref_representation(ref: Mapping[str, object]) -> ManualRepresentationMetadata | None:
    symbol = _manual_seed_text(ref, "symbol")
    hunk = _manual_seed_int(ref, "hunk")
    addr = _manual_seed_int(ref, "addr")
    end = _manual_seed_int(ref, "end")
    operand_index = _manual_seed_int(ref, "operand_index")
    displacement = _manual_seed_int(ref, "displacement")
    custom_base_offset = _manual_seed_int(ref, "custom_base_offset") or 0
    if symbol is None or hunk is None or addr is None or end is None or end <= addr:
        return None
    if operand_index is None or operand_index < 0:
        return None
    if displacement == 0 or custom_base_offset != 0:
        return None
    return ManualRepresentationMetadata(
        addr=addr,
        end=end,
        hunk=hunk,
        style=ManualRepresentationStyle.SYMBOL,
        element_kind="a5_hardware_ref",
        operand_index=operand_index,
        symbol=symbol,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_a5_hardware_ref_citation(ref),
        source_id=_a5_hardware_ref_source_id(ref),
        source_path=_a5_hardware_ref_source_path(ref),
        source_locator=str(ref.get("a5_hardware_ref_id") or ""),
    )


def _a5_hardware_ref_entry_comment(ref: Mapping[str, object]) -> EntryCommentMetadata | None:
    symbol = _manual_seed_text(ref, "symbol")
    hunk = _manual_seed_int(ref, "hunk")
    addr = _manual_seed_int(ref, "addr")
    displacement = _manual_seed_int(ref, "displacement")
    custom_base_offset = _manual_seed_int(ref, "custom_base_offset") or 0
    hardware_register_offset = _manual_seed_int(ref, "hardware_register_offset")
    if symbol is None or hunk is None or addr is None or displacement is None or hardware_register_offset is None:
        return None
    if displacement != 0 and custom_base_offset == 0:
        return None
    return EntryCommentMetadata(
        addr=addr,
        hunk=hunk,
        comment=_a5_hardware_ref_entry_comment_text(symbol, hardware_register_offset, displacement),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_a5_hardware_ref_citation(ref),
        source_id=_a5_hardware_ref_source_id(ref),
        source_path=_a5_hardware_ref_source_path(ref),
        source_locator=str(ref.get("a5_hardware_ref_id") or ""),
    )


def _a5_hardware_ref_citation(ref: Mapping[str, object]) -> str:
    decision_id = _manual_seed_text(ref, "decision_id")
    if decision_id is not None:
        return f"Decision Journal {decision_id}"
    return _manual_action_citation(dict(ref), "a5_hardware_ref_id")


def _a5_hardware_ref_source_id(ref: Mapping[str, object]) -> str:
    decision_id = _manual_seed_text(ref, "decision_id")
    return decision_id if decision_id is not None else "manual_action_log"


def _a5_hardware_ref_source_path(ref: Mapping[str, object]) -> str | None:
    return "decision_journal.jsonl" if _manual_seed_text(ref, "decision_id") is not None else None


def _a5_hardware_ref_entry_comment_text(symbol: str, hardware_register_offset: int, displacement: int) -> str:
    return (
        f"A5 hardware ref: {symbol} at _custom+${hardware_register_offset:04X}; "
        f"operand kept as {_a5_displacement_operand_text(displacement)}"
    )


def _a5_displacement_operand_text(displacement: int) -> str:
    if displacement == 0:
        return "(a5)"
    sign = "-" if displacement < 0 else ""
    return f"{sign}${abs(displacement):04X}(a5)"


def _immediate_interpreted_ref_runtime_address_ref(ref: Mapping[str, object]) -> ManualRuntimeAddressRefMetadata | None:
    hunk = _manual_seed_int(ref, "hunk")
    addr = _manual_seed_int(ref, "addr")
    width = _manual_seed_int(ref, "width")
    target_hunk = _manual_seed_int(ref, "target_hunk")
    target_offset = _manual_seed_int(ref, "target_offset")
    runtime_address = _manual_seed_int(ref, "runtime_address") or _manual_seed_int(ref, "source_value")
    operand_index = _manual_seed_int(ref, "operand_index")
    ref_id = _manual_seed_text(ref, "immediate_ref_id")
    if (
        hunk is None
        or addr is None
        or width not in {1, 2, 4}
        or target_hunk is None
        or target_offset is None
        or runtime_address is None
        or operand_index is None
        or ref_id is None
    ):
        return None
    return ManualRuntimeAddressRefMetadata(
        addr=addr,
        hunk=hunk,
        size=width,
        target_hunk=target_hunk,
        target_offset=target_offset,
        runtime_address=runtime_address,
        confidence=3,
        owner_kind="immediate_interpreted_ref",
        owner_id=ref_id,
        owner_layout_id="immediate",
        owner_element_offset=operand_index,
        xref_generation_mode=str(ref.get("xref_generation_mode") or "bidirectional"),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(ref, "immediate_ref_id"),
    )


def _metadata_range_end(addr: int, end: int | None) -> int:
    return end if end is not None and end > addr else addr + 1


def _ranges_overlap(left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
    return left_start < right_end and right_start < left_end


def _data_block_element_representation_ranges(
    layouts: list[DataBlockLayoutMetadata],
) -> set[tuple[int, int, int]]:
    ranges: set[tuple[int, int, int]] = set()
    for layout in layouts:
        for element in layout.elements:
            if element.representation is None:
                continue
            addr, end = _data_block_element_span(layout, element)
            if end > addr and end <= layout.source_end:
                ranges.add((layout.hunk, addr, end))
    return ranges


def _representation_overlaps_data_block_element(
    representation: ManualRepresentationMetadata,
    ranges: set[tuple[int, int, int]],
) -> bool:
    rep_start = representation.addr
    rep_end = _metadata_range_end(representation.addr, representation.end)
    return any(
        representation.hunk == hunk and _ranges_overlap(rep_start, rep_end, element_start, element_end)
        for hunk, element_start, element_end in ranges
    )


def _manual_execution_view_key(view: dict[str, object]) -> tuple[int, int, int] | None:
    source_start = _manual_seed_int(view, "source_start")
    source_end = _manual_seed_int(view, "source_end")
    base_addr = _manual_seed_int(view, "base_addr")
    if source_start is None or source_end is None or base_addr is None:
        return None
    if source_start < 0 or source_end <= source_start or base_addr < 0:
        return None
    return source_start, source_end, base_addr


def _apply_manual_seed_projection(target_dir: Path, metadata: TargetMetadata | None) -> TargetMetadata | None:
    projection = load_manual_projection(
        target_dir,
        binary_source=resolve_target_binary_source(target_dir),
        stronger_metadata=metadata,
    )
    conflicted_seed_ids: set[str] = set()
    conflicted_label_ids: set[str] = set()
    for item in projection.review_items:
        kind = item.get("kind")
        if not isinstance(kind, ReviewItemKind):
            raise TypeError("review item kind must be a ReviewItemKind")
        if kind is ReviewItemKind.MANUAL_SEED_CONFLICT:
            seed_ids = item.get("seed_ids")
            if isinstance(seed_ids, list | tuple):
                conflicted_seed_ids.update(seed_id for seed_id in seed_ids if isinstance(seed_id, str))
        elif kind is ReviewItemKind.LABEL_SCOPE_CONFLICT:
            label_ids = item.get("label_ids")
            if isinstance(label_ids, list | tuple):
                conflicted_label_ids.update(label_id for label_id in label_ids if isinstance(label_id, str))
    required_seeds = tuple(
        seed for seed in projection.seeds
        if seed.get("mode") is ManualSeedMode.REQUIRED or seed.get("mode") is None
        if seed.get("seed_id") not in conflicted_seed_ids
    )
    labels = tuple(
        label for label in projection.labels
        if label.get("label_id") not in conflicted_label_ids
    )
    comments = projection.comments
    representations = projection.representations
    semantic_hints = projection.semantic_hints
    register_seed_projections = projection.register_seeds
    suppressed_seeded_item_projections = projection.suppressed_seeded_items
    target_equate_projections = projection.target_equates
    renamed_target_equate_projections = projection.renamed_target_equates
    removed_target_equate_projections = projection.removed_target_equates
    custom_struct_projections = projection.custom_structs
    renamed_custom_struct_projections = projection.renamed_custom_structs
    removed_custom_struct_projections = projection.removed_custom_structs
    custom_struct_field_projections = projection.custom_struct_fields
    renamed_custom_struct_field_projections = projection.renamed_custom_struct_fields
    removed_custom_struct_field_projections = projection.removed_custom_struct_fields
    rsset_layout_region_projections = projection.rsset_layout_regions
    removed_rsset_layout_region_projections = projection.removed_rsset_layout_regions
    rsset_use_site_binding_projections = projection.rsset_use_site_bindings
    removed_rsset_use_site_binding_projections = projection.removed_rsset_use_site_bindings
    data_block_layout_projections = projection.data_block_layouts
    removed_data_block_layout_projections = projection.removed_data_block_layouts
    data_block_element_projections = projection.data_block_elements
    removed_data_block_element_projections = projection.removed_data_block_elements
    data_block_interpreted_ref_projections = projection.data_block_interpreted_refs
    removed_data_block_interpreted_ref_projections = projection.removed_data_block_interpreted_refs
    immediate_interpreted_ref_projections = projection.immediate_interpreted_refs
    a5_hardware_ref_projections = projection.a5_hardware_refs
    execution_view_projections = projection.execution_views
    removed_execution_view_projections = projection.removed_execution_views
    if (
        not required_seeds
        and not labels
        and not comments
        and not representations
        and not semantic_hints
        and not register_seed_projections
        and not suppressed_seeded_item_projections
        and not target_equate_projections
        and not renamed_target_equate_projections
        and not removed_target_equate_projections
        and not custom_struct_projections
        and not renamed_custom_struct_projections
        and not removed_custom_struct_projections
        and not custom_struct_field_projections
        and not renamed_custom_struct_field_projections
        and not removed_custom_struct_field_projections
        and not rsset_layout_region_projections
        and not removed_rsset_layout_region_projections
        and not rsset_use_site_binding_projections
        and not removed_rsset_use_site_binding_projections
        and not data_block_layout_projections
        and not removed_data_block_layout_projections
        and not data_block_element_projections
        and not removed_data_block_element_projections
        and not data_block_interpreted_ref_projections
        and not removed_data_block_interpreted_ref_projections
        and not immediate_interpreted_ref_projections
        and not a5_hardware_ref_projections
        and not execution_view_projections
        and not removed_execution_view_projections
    ):
        return metadata
    if metadata is None:
        metadata = TargetMetadata(target_type="program", entry_register_seeds=())
    seeded_entities = list(metadata.seeded_entities)
    seeded_code_labels = list(metadata.seeded_code_labels)
    seeded_code_entrypoints = list(metadata.seeded_code_entrypoints)
    absolute_code_labels = list(metadata.absolute_code_labels)
    entry_comments = list(metadata.entry_comments)
    entry_register_seeds = list(metadata.entry_register_seeds)
    manual_representations = list(metadata.manual_representations)
    target_equates = list(metadata.target_equates)
    manual_runtime_address_refs = list(metadata.manual_runtime_address_refs)
    custom_structs = list(metadata.custom_structs)
    rsset_layout_regions = list(metadata.rsset_layout_regions)
    rsset_use_site_bindings = list(metadata.rsset_use_site_bindings)
    data_block_layouts = list(metadata.data_block_layouts)
    execution_views = list(metadata.execution_views)
    suppressed_seeded_items = list(metadata.suppressed_seeded_items)
    removed_target_equate_names = {
        removed_equate_name
        for equate in removed_target_equate_projections
        if (removed_equate_name := _manual_seed_text(equate, "name")) is not None
    }
    renamed_target_equates = {
        previous_equate_name: new_equate_name
        for equate in renamed_target_equate_projections
        if (rename := _manual_target_equate_rename(equate)) is not None
        for previous_equate_name, new_equate_name in (rename,)
    }
    if renamed_target_equates:
        target_equates = [
            replace(equate, name=renamed_target_equates.get(equate.name, equate.name))
            for equate in target_equates
        ]
    if removed_target_equate_names:
        target_equates = [equate for equate in target_equates if equate.name not in removed_target_equate_names]
    removed_execution_view_keys = {
        removed_execution_view_key
        for view in removed_execution_view_projections
        if (removed_execution_view_key := _manual_execution_view_key(view)) is not None
    }
    if removed_execution_view_keys:
        execution_views = [
            view
            for view in execution_views
            if (view.source_start, view.source_end, view.base_addr) not in removed_execution_view_keys
        ]
    removed_custom_struct_names = {
        removed_struct_name
        for struct in removed_custom_struct_projections
        if (removed_struct_name := _manual_seed_text(struct, "name")) is not None
    }
    renamed_custom_structs = {
        previous_struct_name: new_struct_name
        for struct in renamed_custom_struct_projections
        if (rename := _manual_custom_struct_rename(struct)) is not None
        for previous_struct_name, new_struct_name in (rename,)
    }
    if renamed_custom_structs:
        custom_structs = [
            replace(struct, name=renamed_custom_structs.get(struct.name, struct.name))
            for struct in custom_structs
        ]
    if removed_custom_struct_names:
        custom_structs = [
            struct
            for struct in custom_structs
            if struct.name not in removed_custom_struct_names
        ]
    removed_rsset_layout_region_keys = {
        removed_region_key
        for region in removed_rsset_layout_region_projections
        if (removed_region_key := _manual_rsset_layout_region_key(region)) is not None
    }
    if removed_rsset_layout_region_keys:
        rsset_layout_regions = [
            region
            for region in rsset_layout_regions
            if (region.layout_name or "app", region.base_symbol or "__amiga_app_base__", region.offset)
            not in removed_rsset_layout_region_keys
        ]
    removed_rsset_use_site_binding_ids = {
        binding_id
        for binding in removed_rsset_use_site_binding_projections
        if (binding_id := _manual_seed_text(binding, "rsset_use_site_binding_id")) is not None
    }
    if removed_rsset_use_site_binding_ids:
        rsset_use_site_bindings = [
            binding
            for binding in rsset_use_site_bindings
            if binding.binding_id not in removed_rsset_use_site_binding_ids
        ]
    removed_data_block_layout_ids = {
        layout_id
        for layout in removed_data_block_layout_projections
        if (layout_id := _manual_data_block_layout_key(layout)) is not None
    }
    if removed_data_block_layout_ids:
        data_block_layouts = [
            layout for layout in data_block_layouts if layout.layout_id not in removed_data_block_layout_ids
        ]
        manual_runtime_address_refs = [
            ref for ref in manual_runtime_address_refs if ref.owner_layout_id not in removed_data_block_layout_ids
        ]
    removed_data_block_element_keys = {
        removed_element_key
        for element in removed_data_block_element_projections
        if (removed_element_key := _manual_data_block_element_key(element)) is not None
    }
    if removed_data_block_element_keys:
        data_block_layouts = [
            replace(
                layout,
                elements=tuple(
                    element
                    for element in layout.elements
                    if (element.layout_id, element.offset) not in removed_data_block_element_keys
                ),
            )
            for layout in data_block_layouts
        ]
        manual_runtime_address_refs = [
            ref
            for ref in manual_runtime_address_refs
            if (ref.owner_layout_id, ref.owner_element_offset) not in removed_data_block_element_keys
        ]
    removed_data_block_interpreted_refs = _manual_data_block_reference_removals(
        removed_data_block_interpreted_ref_projections
    )
    if removed_data_block_interpreted_refs:
        removed_ref_ids = {
            ref_id
            for ref_ids in removed_data_block_interpreted_refs.values()
            for ref_id in ref_ids
        }
        data_block_layouts = [
            replace(
                layout,
                elements=tuple(
                    replace(element, reference_interpretation=None)
                    if _data_block_element_ref_is_removed(element, removed_data_block_interpreted_refs)
                    else element
                    for element in layout.elements
                ),
            )
            for layout in data_block_layouts
        ]
        manual_runtime_address_refs = [
            ref for ref in manual_runtime_address_refs if ref.owner_id not in removed_ref_ids
        ]
    for seed in required_seeds:
        seed_kind = seed.get("kind")
        if seed_kind is ManualSeedKind.CODE:
            entrypoint = _manual_seed_to_code_entrypoint(seed)
            if entrypoint is not None:
                seeded_code_entrypoints.append(entrypoint)
        elif seed_kind is ManualSeedKind.DATA:
            entity = _manual_seed_to_data_entity(seed)
            if entity is not None:
                seeded_entities.append(entity)
    for label in labels:
        code_label = _manual_label_to_code_label(label)
        if code_label is not None:
            seeded_code_labels.append(code_label)
        absolute_label = _manual_label_to_absolute_code_label(label)
        if absolute_label is not None:
            absolute_code_labels.append(absolute_label)
    for comment in comments:
        entry_comment = _manual_comment_to_entry_comment(comment)
        if entry_comment is not None:
            entry_comments.append(entry_comment)
    for representation in representations:
        manual_representation = _manual_representation_to_metadata(representation)
        if manual_representation is not None:
            manual_representations.append(manual_representation)
    for hint in semantic_hints:
        manual_representation = _manual_semantic_hint_to_representation(hint)
        if manual_representation is not None:
            manual_representations.append(manual_representation)
    if renamed_target_equates:
        manual_representations = [
            replace(representation, symbol=_renamed_target_equate_symbol(representation.symbol, renamed_target_equates))
            if representation.symbol is not None
            else representation
            for representation in manual_representations
        ]
    if removed_target_equate_names:
        manual_representations = [
            representation
            for representation in manual_representations
            if representation.symbol not in removed_target_equate_names
        ]
    for register_seed in register_seed_projections:
        entry_register_seed = _manual_register_seed_to_metadata(register_seed)
        if entry_register_seed is not None:
            entry_register_seeds.append(entry_register_seed)
    for item in suppressed_seeded_item_projections:
        suppressed_seeded_item = _manual_suppressed_seeded_item_to_metadata(item)
        if suppressed_seeded_item is not None:
            suppressed_seeded_items.append(suppressed_seeded_item)
    for equate in target_equate_projections:
        target_equate = _manual_target_equate_to_metadata(equate)
        if target_equate is not None:
            target_equates.append(target_equate)
    for ref in immediate_interpreted_ref_projections:
        immediate_equate = _immediate_interpreted_ref_equate(ref)
        immediate_representation = _immediate_interpreted_ref_representation(ref)
        immediate_runtime_ref = _immediate_interpreted_ref_runtime_address_ref(ref)
        if immediate_equate is not None and immediate_representation is not None:
            target_equates.append(immediate_equate)
            manual_representations.append(immediate_representation)
            if immediate_runtime_ref is not None:
                manual_runtime_address_refs.append(immediate_runtime_ref)
    for ref in a5_hardware_ref_projections:
        a5_representation = _a5_hardware_ref_representation(ref)
        if a5_representation is not None:
            manual_representations.append(a5_representation)
        a5_entry_comment = _a5_hardware_ref_entry_comment(ref)
        if a5_entry_comment is not None:
            entry_comments.append(a5_entry_comment)
    merged_target_equates = {equate.name: equate for equate in target_equates}
    for struct in custom_struct_projections:
        custom_struct = _manual_custom_struct_to_metadata(struct)
        if custom_struct is not None:
            custom_structs.append(custom_struct)
    removed_custom_struct_field_keys = {
        removed_field_key
        for field in removed_custom_struct_field_projections
        if (removed_field_key := _manual_custom_struct_field_key(field)) is not None
    }
    renamed_custom_struct_fields = {
        renamed_field_key: renamed_field_name
        for field in renamed_custom_struct_field_projections
        if (renamed_field_key := _manual_custom_struct_field_key(field)) is not None
        if (renamed_field_name := _manual_seed_text(field, "name")) is not None
    }
    if custom_struct_field_projections or renamed_custom_struct_fields or removed_custom_struct_field_keys:
        custom_structs = [
            _custom_struct_with_manual_field_projection(
                struct,
                custom_struct_field_projections,
                removed_custom_struct_field_keys,
                renamed_custom_struct_fields,
            )
            for struct in custom_structs
        ]
    merged_custom_structs = {struct.name: struct for struct in custom_structs}
    for region in rsset_layout_region_projections:
        rsset_layout_region = _manual_rsset_layout_region_to_metadata(region)
        if rsset_layout_region is not None:
            rsset_layout_regions.append(rsset_layout_region)
    merged_rsset_layout_regions = {
        (region.layout_name or "app", region.base_symbol or "__amiga_app_base__", region.offset): region
        for region in rsset_layout_regions
    }
    for binding in rsset_use_site_binding_projections:
        rsset_use_site_binding = _manual_rsset_use_site_binding_to_metadata(binding)
        if rsset_use_site_binding is not None:
            rsset_use_site_bindings.append(rsset_use_site_binding)
    merged_rsset_use_site_bindings = {
        (
            binding.hunk,
            binding.addr,
            binding.operand_index,
            binding.base_register,
            binding.displacement,
            binding.layout_name,
            binding.base_symbol,
            binding.base_evidence_id,
        ): binding
        for binding in rsset_use_site_bindings
    }
    data_block_reference_interpretations = _manual_data_block_reference_interpretations(
        data_block_interpreted_ref_projections
    )
    for layout_projection in data_block_layout_projections:
        data_block_layout = _manual_data_block_layout_to_metadata(
            layout_projection,
            data_block_element_projections,
            data_block_reference_interpretations,
        )
        if data_block_layout is not None:
            data_block_layouts.append(data_block_layout)
    merged_data_block_layouts = {layout.layout_id: layout for layout in data_block_layouts}
    effective_data_block_layouts = list(merged_data_block_layouts.values())
    data_block_representation_ranges = _data_block_element_representation_ranges(effective_data_block_layouts)
    if data_block_representation_ranges:
        manual_representations = [
            representation
            for representation in manual_representations
            if not _representation_overlaps_data_block_element(representation, data_block_representation_ranges)
        ]
    for effective_layout in effective_data_block_layouts:
        for element in effective_layout.elements:
            typed_entities = _data_block_bound_struct_entities(effective_layout, element, merged_custom_structs)
            if typed_entities:
                seeded_entities.extend(typed_entities)
            else:
                entity = _data_block_element_entity(effective_layout, element)
                if entity is not None:
                    seeded_entities.append(entity)
            interpreted_ref_equate = (
                _data_block_interpreted_ref_equate(element.reference_interpretation)
                if isinstance(element.reference_interpretation, dict)
                else None
            )
            interpreted_ref_representation = _data_block_element_interpreted_ref_representation(effective_layout, element)
            interpreted_ref_runtime_ref = _data_block_element_interpreted_ref_runtime_address_ref(effective_layout, element)
            if interpreted_ref_equate is not None and interpreted_ref_representation is not None:
                target_equates.append(interpreted_ref_equate)
                manual_representations.append(interpreted_ref_representation)
                if interpreted_ref_runtime_ref is not None:
                    manual_runtime_address_refs.append(interpreted_ref_runtime_ref)
            elif not typed_entities:
                element_representation = _data_block_element_representation(effective_layout, element)
                if element_representation is not None:
                    manual_representations.append(element_representation)
    merged_target_equates = {equate.name: equate for equate in target_equates}
    merged_manual_runtime_address_refs = {
        (ref.owner_kind, ref.owner_id, ref.hunk, ref.addr, ref.target_hunk, ref.target_offset): ref
        for ref in manual_runtime_address_refs
    }
    for view in execution_view_projections:
        execution_view = _manual_execution_view_to_metadata(view)
        if execution_view is not None:
            execution_views.append(execution_view)
    merged_execution_views = {
        (view.source_start, view.source_end, view.base_addr): view for view in execution_views
    }
    result = replace(
        metadata,
        entry_register_seeds=tuple(entry_register_seeds),
        seeded_entities=_merge_projected_seeded_entities(seeded_entities),
        seeded_code_labels=tuple(seeded_code_labels),
        absolute_code_labels=tuple(absolute_code_labels),
        seeded_code_entrypoints=tuple(seeded_code_entrypoints),
        entry_comments=tuple(entry_comments),
        manual_representations=tuple(manual_representations),
        target_equates=tuple(merged_target_equates.values()),
        manual_runtime_address_refs=tuple(merged_manual_runtime_address_refs.values()),
        custom_structs=tuple(merged_custom_structs.values()),
        rsset_layout_regions=tuple(merged_rsset_layout_regions.values()),
        rsset_use_site_bindings=tuple(merged_rsset_use_site_bindings.values()),
        data_block_layouts=tuple(effective_data_block_layouts),
        execution_views=tuple(merged_execution_views.values()),
        suppressed_seeded_items=tuple(suppressed_seeded_items),
    )
    if suppressed_seeded_items:
        result = apply_suppressed_seeded_items(result, tuple(suppressed_seeded_items))
        result = replace(result, suppressed_seeded_items=tuple(suppressed_seeded_items))
    return result


def _apply_decision_journal_projection(target_dir: Path, metadata: TargetMetadata | None) -> TargetMetadata | None:
    if metadata is None:
        return None
    try:
        report = decision_journal_report(target_dir)
    except Exception:
        return metadata
    projection = report.get("projection") if isinstance(report, Mapping) else None
    if not isinstance(projection, Mapping) or projection.get("valid") is not True:
        return metadata
    accepted_entrypoints = [
        entrypoint
        for record in _mapping_sequence(projection.get("accepted_facts"))
        if (entrypoint := _callback_decision_to_code_entrypoint(record)) is not None
    ]
    accepted_a5_refs = [
        ref
        for record in _mapping_sequence(projection.get("accepted_facts"))
        if (ref := _a5_decision_to_hardware_ref(record)) is not None
    ]
    if not accepted_entrypoints and not accepted_a5_refs:
        return metadata
    known_locations = {(entrypoint.hunk, entrypoint.addr) for entrypoint in metadata.seeded_code_entrypoints}
    merged_entrypoints = list(metadata.seeded_code_entrypoints)
    for entrypoint in accepted_entrypoints:
        key = (entrypoint.hunk, entrypoint.addr)
        if key in known_locations:
            continue
        merged_entrypoints.append(entrypoint)
        known_locations.add(key)
    entry_comments = list(metadata.entry_comments)
    manual_representations = list(metadata.manual_representations)
    for ref in accepted_a5_refs:
        a5_representation = _a5_hardware_ref_representation(ref)
        if a5_representation is not None:
            manual_representations.append(a5_representation)
        a5_entry_comment = _a5_hardware_ref_entry_comment(ref)
        if a5_entry_comment is not None:
            entry_comments.append(a5_entry_comment)
    return replace(
        metadata,
        seeded_code_entrypoints=tuple(merged_entrypoints),
        entry_comments=tuple(entry_comments),
        manual_representations=tuple(manual_representations),
    )


def _callback_decision_to_code_entrypoint(record: Mapping[str, object]) -> SeededCodeEntrypointMetadata | None:
    if record.get("action") != "accept_fact" or record.get("fact_type") != "callback_derived_code":
        return None
    scope = record.get("scope")
    selected_identity = record.get("selected_identity")
    if not isinstance(scope, Mapping) or scope.get("kind") != "selected_callback_target":
        return None
    if not isinstance(selected_identity, Mapping):
        return None
    hunk = _manual_seed_int(scope, "hunk")
    addr = _manual_seed_int(scope, "addr")
    if hunk is None:
        hunk = _manual_seed_int(selected_identity, "hunk") or 0
    if addr is None:
        addr = _manual_seed_int(selected_identity, "addr")
    decision_id = _manual_seed_text(record, "decision_id")
    candidate_id = _manual_seed_text(record, "candidate_id")
    packet_id = _manual_seed_text(record, "packet_id")
    if addr is None or decision_id is None:
        return None
    return SeededCodeEntrypointMetadata(
        addr=addr,
        hunk=hunk,
        name=f"callback_{hunk}_{addr:08x}",
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.VALIDATED,
        citation=f"Decision Journal {decision_id}",
        source_id=decision_id,
        source_path="decision_journal.jsonl",
        source_locator=packet_id or candidate_id or decision_id,
        comment="callback-derived code target accepted through Decision Journal",
        role="callback_derived_code",
    )


def _a5_decision_to_hardware_ref(record: Mapping[str, object]) -> dict[str, object] | None:
    if record.get("action") != "accept_fact" or record.get("fact_type") != "a5_hardware_ref":
        return None
    ref = record.get("a5_hardware_ref")
    selected_identity = record.get("selected_identity")
    if not isinstance(ref, Mapping) or not isinstance(selected_identity, Mapping):
        return None
    if not _a5_decision_identity_matches_ref(selected_identity, ref):
        return None
    result = dict(ref)
    decision_id = _manual_seed_text(record, "decision_id")
    if decision_id is not None:
        result.setdefault("decision_id", decision_id)
    return result


def _a5_decision_identity_matches_ref(identity: Mapping[str, object], ref: Mapping[str, object]) -> bool:
    checks = (
        ("target_id", "target_id"),
        ("row_key", "row_key"),
        ("addr", "addr"),
        ("end", "end"),
        ("operand_index", "operand_index"),
        ("base_register", "base_register"),
        ("displacement", "displacement"),
        ("hardware_register_offset", "hardware_register_offset"),
        ("parent_evidence_id", "source_evidence_id"),
    )
    for identity_key, ref_key in checks:
        if identity_key in identity and identity.get(identity_key) != ref.get(ref_key):
            return False
    return True


def effective_metadata_text(target_dir: Path, *, include_decision_journal: bool = True) -> str:
    metadata = effective_target_metadata(target_dir, include_decision_journal=include_decision_journal)
    if metadata is None:
        return ""
    payload = target_metadata_json_payload(metadata)
    projection = load_manual_projection(
        target_dir,
        binary_source=resolve_target_binary_source(target_dir),
    )
    if projection.runtime_observation_views:
        payload["runtime_observation_views"] = [dict(view) for view in projection.runtime_observation_views]
    _add_source_context(target_dir, payload)
    _add_source_descriptor_execution_view(target_dir, payload)
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _add_source_context(target_dir: Path, payload: dict[str, object]) -> None:
    binary_source = resolve_target_binary_source(target_dir)
    if not isinstance(binary_source, DiskEntryBinarySource):
        return
    payload["source_context"] = {
        "kind": "disk_entry",
        "disk_id": binary_source.disk_id,
        "disk_path": str(binary_source.adf_path),
        "entry_path": binary_source.entry_path,
        "parent_disk_id": binary_source.parent_disk_id,
    }


def _add_source_descriptor_execution_view(target_dir: Path, payload: dict[str, object]) -> None:
    binary_source = resolve_target_binary_source(target_dir)
    if not isinstance(binary_source, RawBinarySource):
        return
    if binary_source.address_model is not RawAddressModel.RUNTIME_ABSOLUTE:
        return
    source_end = binary_source.path.stat().st_size
    if source_end <= 0:
        return
    existing_views = payload.get("execution_views")
    if existing_views is None:
        raw_views: list[object] = []
    elif isinstance(existing_views, tuple):
        raw_views = list(existing_views)
    elif isinstance(existing_views, list):
        raw_views = existing_views
    else:
        return
    payload["execution_views"] = raw_views
    for raw_view in raw_views:
        if not isinstance(raw_view, dict):
            continue
        if (
            raw_view.get("source_start") == 0
            and raw_view.get("source_end") == source_end
            and raw_view.get("base_addr") == binary_source.load_address
        ):
            return
    raw_views.append(
        {
            "base_addr": binary_source.load_address,
            "citation": "source_binary.json",
            "comment": "Runtime absolute raw source load view.",
            "name": "source_binary",
            "review_status": "validated",
            "seed_origin": "manual_analysis",
            "source_end": source_end,
            "source_start": 0,
        }
    )


def effective_metadata_hash(target_dir: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(effective_metadata_text(target_dir).encode("utf-8"))
    return hasher.hexdigest()


@contextmanager
def effective_metadata_file(target_dir: Path, *, include_decision_journal: bool = True) -> Iterator[Path | None]:
    text = effective_metadata_text(target_dir, include_decision_journal=include_decision_journal)
    if not text:
        yield None
        return
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as temp_file:
            temp_file.write(text)
            temp_path = Path(temp_file.name)
        yield temp_path
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
