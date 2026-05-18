from __future__ import annotations

from collections.abc import Mapping, Sequence


def listing_row_context(row: Mapping[str, object]) -> dict[str, object]:
    context: dict[str, object] = {
        "kind": "row",
        "row_index": _optional_int(row.get("row_index")),
        "row_kind": _str_or_none(row.get("kind")),
        "stable_key": _str_or_none(row.get("stable_key") or row.get("stableKey")),
        "hunk": _optional_int(_first_present(row, "section_index", "sectionIndex")),
        "addr": _optional_int(row.get("addr")),
        "start_offset": _optional_int(_first_present(row, "start_offset", "startOffset")),
        "end_offset": _optional_int(_first_present(row, "end_offset", "endOffset")),
    }
    return {key: value for key, value in context.items() if value is not None}


def listing_element_contexts(row: Mapping[str, object]) -> list[dict[str, object]]:
    contexts: list[dict[str, object]] = []
    _append_operand_contexts(contexts, row)
    _append_app_slot_contexts(contexts, row)
    _append_typed_access_contexts(contexts, row)
    _append_runtime_address_ref_contexts(contexts, row)
    _append_data_literal_context(contexts, row)
    _append_label_context(contexts, row)
    _append_comment_context(contexts, row)
    return contexts


def selected_listing_element_context(
    row: Mapping[str, object],
    selector: Mapping[str, object],
) -> dict[str, object]:
    candidates = listing_element_contexts(row)
    element_id = _str_or_none(selector.get("element_id") or selector.get("elementId"))
    if element_id:
        for context in candidates:
            if context.get("element_id") == element_id:
                return context
        raise ValueError(f"Listing element is not available: {element_id}")

    element_kind = _str_or_none(selector.get("element_kind") or selector.get("elementKind"))
    operand_index = _optional_int(selector.get("operand_index") or selector.get("operandIndex"))
    symbol = _str_or_none(selector.get("symbol"))
    access = _str_or_none(selector.get("access"))
    value = _optional_int(selector.get("value"))

    matches = candidates
    if element_kind:
        matches = [context for context in matches if context.get("element_kind") == element_kind]
    if operand_index is not None:
        matches = [context for context in matches if context.get("operand_index") == operand_index]
    if symbol:
        matches = [context for context in matches if context.get("symbol") == symbol]
    if access:
        matches = [context for context in matches if context.get("access") == access]
    if value is not None:
        matches = [context for context in matches if context.get("value") == value]

    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError("Listing element is not available for the supplied context")
    raise ValueError("Listing element context is ambiguous; element_id is required")


def element_numeric_values(context: Mapping[str, object]) -> tuple[int, ...]:
    values: list[int] = []
    for key in ("signed_value", "value"):
        value = _optional_int(context.get(key))
        if value is not None and value not in values:
            values.append(value)
    return tuple(values)


def _append_operand_contexts(contexts: list[dict[str, object]], row: Mapping[str, object]) -> None:
    operand_parts = row.get("operand_parts") or row.get("operandParts")
    if not isinstance(operand_parts, Sequence) or isinstance(operand_parts, (str, bytes, bytearray)):
        return
    accesses = _sequence(row.get("operand_accesses") or row.get("operandAccesses"))
    registers = _sequence(row.get("operand_registers") or row.get("operandRegisters"))
    for fallback_index, raw_part in enumerate(operand_parts):
        if not isinstance(raw_part, Mapping):
            continue
        operand_index = _optional_int(raw_part.get("operand_index") or raw_part.get("operandIndex"))
        if operand_index is None:
            operand_index = fallback_index
        raw_kind = _str_or_none(raw_part.get("kind")) or "operand"
        metadata = raw_part.get("metadata")
        symbol = _str_or_none(raw_part.get("symbol"))
        if isinstance(metadata, Mapping):
            symbol = symbol or _str_or_none(metadata.get("symbol"))
        element_kind = "symbol" if symbol else raw_kind
        context = _element_base(row, element_kind, f"{element_kind}:{operand_index}:{symbol or _value_token(raw_part)}")
        context["operand_index"] = operand_index
        context["source_kind"] = raw_kind
        if symbol:
            context["symbol"] = symbol
            context["role"] = _str_or_none(raw_part.get("role")) or "reference"
            _copy_api_call_context(context, row, symbol)
        _copy_optional_int(context, raw_part, "value")
        _copy_optional_int(context, raw_part, "signed_value", "signedValue")
        _copy_optional_int(context, raw_part, "width_bits", "widthBits")
        _copy_optional_int(context, raw_part, "width_bytes", "widthBytes")
        _copy_optional_int(context, raw_part, "displacement")
        _copy_optional_int(context, raw_part, "segment_addr", "segmentAddr")
        for key in ("register", "base_register"):
            value = _str_or_none(raw_part.get(key) or raw_part.get(_camel(key)))
            if value:
                context[key] = value
        if operand_index < len(accesses) and isinstance(accesses[operand_index], str):
            context["access"] = accesses[operand_index]
        if operand_index < len(registers) and isinstance(registers[operand_index], str):
            context["register"] = registers[operand_index]
        contexts.append(context)


def _copy_api_call_context(context: dict[str, object], row: Mapping[str, object], symbol: str) -> None:
    api_call = row.get("api_call") or row.get("apiCall")
    if not isinstance(api_call, Mapping):
        return
    library = _str_or_none(api_call.get("library"))
    function = _str_or_none(api_call.get("function"))
    if not library or not function or symbol != f"_LVO{function}":
        return
    context["api_library"] = library
    context["api_function"] = function
    context["domain"] = "lvo"


def _append_app_slot_contexts(contexts: list[dict[str, object]], row: Mapping[str, object]) -> None:
    for raw_ref in _mapping_sequence(row.get("app_slot_refs") or row.get("appSlotRefs")):
        symbol = _str_or_none(raw_ref.get("symbol"))
        if not symbol:
            continue
        operand_index = _optional_int(raw_ref.get("operand_index") or raw_ref.get("operandIndex"))
        access = _str_or_none(raw_ref.get("access")) or "reference"
        token = f"app_slot:{operand_index if operand_index is not None else ''}:{symbol}:{access}"
        context = _element_base(row, "app_slot", token)
        context["symbol"] = symbol
        context["access"] = access
        context["role"] = "reference"
        if operand_index is not None:
            context["operand_index"] = operand_index
        _copy_optional_int(context, raw_ref, "displacement")
        base_register = _str_or_none(raw_ref.get("base_register") or raw_ref.get("baseRegister"))
        if base_register:
            context["base_register"] = base_register
        contexts.append(context)


def _append_typed_access_contexts(contexts: list[dict[str, object]], row: Mapping[str, object]) -> None:
    for element_kind, field_name, raw_accesses in (
        ("typed_access", "field_name", row.get("typed_accesses") or row.get("typedAccesses")),
        ("typed_gap", "classification", row.get("unresolved_typed_accesses") or row.get("unresolvedTypedAccesses")),
    ):
        for raw_access in _mapping_sequence(raw_accesses):
            operand_index = _optional_int(raw_access.get("operand_index") or raw_access.get("operandIndex"))
            field = _str_or_none(raw_access.get(field_name) or raw_access.get(_camel(field_name))) or ""
            token = f"{element_kind}:{operand_index if operand_index is not None else ''}:{field}"
            context = _element_base(row, element_kind, token)
            if operand_index is not None:
                context["operand_index"] = operand_index
            _copy_optional_int(context, raw_access, "displacement")
            _copy_optional_int(context, raw_access, "field_offset", "fieldOffset")
            _copy_optional_int(context, raw_access, "struct_size", "structSize")
            _copy_optional_int(context, raw_access, "container_candidate_count", "containerCandidateCount")
            for key in (
                "base_register",
                "root_struct_name",
                "owner_struct_name",
                "field_name",
                "field_expr",
                "classification",
                "container_struct_name",
                "container_field_expr",
                "refined_struct_name",
            ):
                value = _str_or_none(raw_access.get(key) or raw_access.get(_camel(key)))
                if value:
                    context[key] = value
            refinement_applied = _first_present(raw_access, "refinement_applied", "refinementApplied")
            if isinstance(refinement_applied, bool):
                context["refinement_applied"] = refinement_applied
            contexts.append(context)


def _append_runtime_address_ref_contexts(contexts: list[dict[str, object]], row: Mapping[str, object]) -> None:
    for raw_ref in _mapping_sequence(row.get("runtime_address_refs") or row.get("runtimeAddressRefs")):
        target_hunk = _optional_int(_first_present(raw_ref, "target_section_index", "targetSectionIndex"))
        target_addr = _optional_int(_first_present(raw_ref, "target_offset", "targetOffset"))
        if target_hunk is None or target_addr is None:
            continue
        operand_index = _optional_int(_first_present(raw_ref, "operand_index", "operandIndex"))
        token = f"data_ref:{operand_index if operand_index is not None else ''}:{target_hunk}:{target_addr:08X}"
        context = _element_base(row, "data_ref", token)
        context["role"] = "reference"
        context["access"] = "reference"
        context["target_hunk"] = target_hunk
        context["target_addr"] = target_addr
        if operand_index is not None:
            context["operand_index"] = operand_index
        size = _optional_int(raw_ref.get("size"))
        if size is not None and size > 0:
            context["target_end"] = target_addr + size
            context["size"] = size
        _copy_optional_int(context, raw_ref, "runtime_address", "runtimeAddress")
        data_class = _str_or_none(raw_ref.get("data_class") or raw_ref.get("dataClass"))
        if data_class:
            context["data_class"] = data_class
        symbol = _str_or_none(raw_ref.get("symbol") or raw_ref.get("name") or raw_ref.get("label"))
        if symbol:
            context["symbol"] = symbol
        contexts.append(context)


def _append_data_literal_context(contexts: list[dict[str, object]], row: Mapping[str, object]) -> None:
    if _str_or_none(row.get("kind")) != "data":
        return
    raw_bytes = row.get("bytes")
    if not isinstance(raw_bytes, str) or not raw_bytes:
        return
    byte_count = len(raw_bytes) // 2
    context = _element_base(row, "data_literal", f"data_literal:{row.get('start_offset') or row.get('addr')}")
    context["byte_count"] = byte_count
    context["width_bytes"] = byte_count
    if 0 < byte_count <= 4:
        context["value"] = int(raw_bytes[: byte_count * 2], 16)
    contexts.append(context)


def _append_label_context(contexts: list[dict[str, object]], row: Mapping[str, object]) -> None:
    symbol = _str_or_none(row.get("label"))
    if not symbol or _str_or_none(row.get("kind")) != "label":
        return
    context = _element_base(row, "label", f"label:{symbol}")
    context["symbol"] = symbol
    context["role"] = "definition"
    contexts.append(context)


def _append_comment_context(contexts: list[dict[str, object]], row: Mapping[str, object]) -> None:
    if not _str_or_none(row.get("comment_text") or row.get("commentText")):
        return
    contexts.append(_element_base(row, "comment", "comment"))


def _element_base(row: Mapping[str, object], element_kind: str, token: str) -> dict[str, object]:
    context = listing_row_context(row)
    context["kind"] = "element"
    context["element_kind"] = element_kind
    context["element_id"] = f"{context.get('stable_key') or context.get('row_index') or 'row'}:{token}"
    return context


def _mapping_sequence(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _sequence(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return list(value)


def _copy_optional_int(
    target: dict[str, object],
    source: Mapping[str, object],
    snake_key: str,
    camel_key: str | None = None,
) -> None:
    value = _optional_int(source.get(snake_key))
    if value is None and camel_key:
        value = _optional_int(source.get(camel_key))
    if value is not None:
        target[snake_key] = value


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _camel(key: str) -> str:
    head, *tail = key.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in tail)


def _value_token(raw_part: Mapping[str, object]) -> str:
    value = raw_part.get("signed_value") or raw_part.get("signedValue") or raw_part.get("value")
    return str(value) if isinstance(value, int) and not isinstance(value, bool) else "operand"


def _first_present(source: Mapping[str, object], *keys: str) -> object:
    for key in keys:
        if key in source:
            return source[key]
    return None
