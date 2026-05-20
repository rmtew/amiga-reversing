from __future__ import annotations

from collections.abc import Mapping, Sequence


def callback_slot_report(
    rows: Sequence[Mapping[str, object]],
    review_items: Sequence[Mapping[str, object]] = (),
    *,
    slot_symbol: str | None = None,
    slot_offset: int | None = None,
    lookback_rows: int = 4,
    lookahead_rows: int = 4,
) -> dict[str, object]:
    """Report code pointers stored in app slots that are later called indirectly."""

    row_list = list(rows)
    label_offsets = _label_offsets(row_list)
    target_rows = _rows_by_start_offset(row_list)
    review_by_start = _review_items_by_start(review_items)
    slot_filter = _slot_filter(slot_symbol=slot_symbol, slot_offset=slot_offset)
    consumers = _slot_consumers(row_list, slot_filter=slot_filter, lookahead_rows=lookahead_rows)
    assignments = _slot_assignments(
        row_list,
        slot_filter=slot_filter,
        label_offsets=label_offsets,
        target_rows=target_rows,
        review_by_start=review_by_start,
        lookback_rows=lookback_rows,
    )
    slots = sorted({*_slot_keys(consumers), *_slot_keys(assignments)})
    slot_reports = []
    for slot in slots:
        slot_consumers = [consumer for consumer in consumers if _entry_slot_key(consumer) == slot]
        slot_assignments = [assignment for assignment in assignments if _entry_slot_key(assignment) == slot]
        concrete_assignments = [
            assignment
            for assignment in slot_assignments
            if assignment.get("stored_source_offset") is not None
            and assignment.get("target_kind") != "instruction"
        ]
        slot_reports.append(
            {
                "slot_symbol": slot[0],
                "slot_offset": slot[1],
                "consumer_count": len(slot_consumers),
                "assignment_count": len(slot_assignments),
                "concrete_missed_code_target_count": len(concrete_assignments),
                "consumers": slot_consumers,
                "assignments": slot_assignments,
            }
        )
    return {
        "kind": "callback_slot_report",
        "slot_filter": {"slot_symbol": slot_symbol, "slot_offset": slot_offset},
        "slot_count": len(slot_reports),
        "slots": slot_reports,
        "summary": {
            "consumer_count": len(consumers),
            "assignment_count": len(assignments),
            "concrete_missed_code_target_count": sum(
                slot["concrete_missed_code_target_count"] for slot in slot_reports
            ),
        },
    }


def _slot_filter(
    *,
    slot_symbol: str | None,
    slot_offset: int | None,
):
    normalized_symbol = slot_symbol.strip() if isinstance(slot_symbol, str) and slot_symbol.strip() else None

    def matches(ref: Mapping[str, object]) -> bool:
        if normalized_symbol is not None and ref.get("symbol") != normalized_symbol:
            return False
        return not (slot_offset is not None and ref.get("displacement") != slot_offset)

    return matches


def _slot_consumers(
    rows: list[Mapping[str, object]],
    *,
    slot_filter,
    lookahead_rows: int,
) -> list[dict[str, object]]:
    consumers: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        ref = _first_app_slot_ref(row, access="read", slot_filter=slot_filter)
        if ref is None:
            continue
        register = _destination_register(row)
        if register is None:
            continue
        transfer = _following_indirect_transfer(rows, index, register, lookahead_rows=lookahead_rows)
        if transfer is None:
            continue
        consumers.append(
            {
                **_slot_payload(ref),
                "load": _row_payload(row),
                "register": register,
                "indirect_transfer": _row_payload(transfer),
                "evidence": "slot_read_to_address_register_then_indirect_control_transfer",
            }
        )
    return consumers


def _slot_assignments(
    rows: list[Mapping[str, object]],
    *,
    slot_filter,
    label_offsets: dict[str, int],
    target_rows: dict[int, Mapping[str, object]],
    review_by_start: dict[int, Mapping[str, object]],
    lookback_rows: int,
) -> list[dict[str, object]]:
    assignments: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        ref = _first_app_slot_ref(row, access="write", slot_filter=slot_filter)
        if ref is None:
            continue
        source_register = _source_register(row)
        symbol_row = _previous_symbol_load(rows, index, source_register, lookback_rows=lookback_rows)
        symbol = _symbol_operand(symbol_row) if symbol_row is not None else None
        target_offset = label_offsets.get(symbol) if symbol is not None else None
        target_row = target_rows.get(target_offset) if target_offset is not None else None
        review_item = review_by_start.get(target_offset) if target_offset is not None else None
        assignments.append(
            {
                **_slot_payload(ref),
                "store": _row_payload(row),
                "stored_register": source_register,
                "value_source": _row_payload(symbol_row),
                "stored_symbol": symbol,
                "stored_source_offset": target_offset,
                "target": _row_payload(target_row),
                "target_kind": target_row.get("kind") if target_row is not None else None,
                "review_item": _review_item_payload(review_item),
                "action_readiness": _assignment_action_readiness(target_row, review_item),
                "evidence": "pc_relative_symbol_loaded_then_stored_to_callback_slot",
            }
        )
    return assignments


def _assignment_action_readiness(
    target_row: Mapping[str, object] | None,
    review_item: Mapping[str, object] | None,
) -> dict[str, object]:
    if target_row is None:
        return {"status": "blocked", "blockers": ["target_row_missing"]}
    if target_row.get("kind") == "instruction":
        return {"status": "already_code", "blockers": []}
    if review_item is None:
        return {"status": "blocked", "blockers": ["missing_orphan_code_review_item"]}
    if review_item.get("kind") != "orphan_code_candidate":
        return {
            "status": "blocked",
            "blockers": ["review_item_is_not_code_classification"],
            "review_item_kind": review_item.get("kind"),
        }
    return {"status": "ready_for_review_seed_code", "command_id": "review.seed.code", "blockers": []}


def _first_app_slot_ref(
    row: Mapping[str, object],
    *,
    access: str,
    slot_filter,
) -> Mapping[str, object] | None:
    refs = row.get("app_slot_refs")
    if not isinstance(refs, list):
        return None
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        if ref.get("access") == access and slot_filter(ref):
            return ref
    return None


def _destination_register(row: Mapping[str, object]) -> str | None:
    registers = row.get("operand_registers")
    if not isinstance(registers, list) or not registers:
        return None
    register = registers[-1]
    return _address_register(register)


def _source_register(row: Mapping[str, object]) -> str | None:
    registers = row.get("operand_registers")
    if not isinstance(registers, list) or not registers:
        return None
    register = registers[0]
    return _address_register(register)


def _address_register(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.upper()
    if len(normalized) == 2 and normalized[0] == "A" and normalized[1].isdigit():
        return normalized
    return None


def _following_indirect_transfer(
    rows: list[Mapping[str, object]],
    index: int,
    register: str,
    *,
    lookahead_rows: int,
) -> Mapping[str, object] | None:
    expected = f"({register.lower()})"
    for candidate in rows[index + 1 : index + 1 + lookahead_rows]:
        opcode = str(candidate.get("opcode_or_directive") or "").lower()
        if opcode not in {"jsr", "jmp"}:
            continue
        if str(candidate.get("operand_text") or "").strip().lower() == expected:
            return candidate
    return None


def _previous_symbol_load(
    rows: list[Mapping[str, object]],
    index: int,
    register: str | None,
    *,
    lookback_rows: int,
) -> Mapping[str, object] | None:
    if register is None:
        return None
    for candidate in reversed(rows[max(0, index - lookback_rows) : index]):
        if _destination_register(candidate) != register:
            continue
        if _symbol_operand(candidate) is not None:
            return candidate
    return None


def _symbol_operand(row: Mapping[str, object] | None) -> str | None:
    if row is None:
        return None
    parts = row.get("operand_parts")
    if not isinstance(parts, list):
        return None
    for part in parts:
        if not isinstance(part, Mapping) or part.get("kind") != "symbol":
            continue
        metadata = part.get("metadata")
        if isinstance(metadata, Mapping):
            symbol = metadata.get("symbol")
            if isinstance(symbol, str) and symbol:
                return symbol
        text = part.get("text")
        if isinstance(text, str) and text:
            return text
    return None


def _label_offsets(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        label = row.get("label")
        start = row.get("start_offset")
        if isinstance(label, str) and isinstance(start, int) and not isinstance(start, bool):
            result[label] = start
    return result


def _rows_by_start_offset(rows: Sequence[Mapping[str, object]]) -> dict[int, Mapping[str, object]]:
    result: dict[int, Mapping[str, object]] = {}
    for row in rows:
        start = row.get("start_offset")
        if not isinstance(start, int) or isinstance(start, bool):
            continue
        if row.get("kind") in {"instruction", "data"} and start not in result:
            result[start] = row
    return result


def _review_items_by_start(review_items: Sequence[Mapping[str, object]]) -> dict[int, Mapping[str, object]]:
    result: dict[int, Mapping[str, object]] = {}
    for item in review_items:
        start = item.get("start")
        if isinstance(start, int) and not isinstance(start, bool):
            result[start] = item
    return result


def _slot_payload(ref: Mapping[str, object]) -> dict[str, object]:
    return {
        "slot_symbol": ref.get("symbol"),
        "slot_offset": ref.get("displacement"),
        "base_register": ref.get("base_register"),
    }


def _row_payload(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if row is None:
        return None
    return {
        "row_key": row.get("row_key"),
        "kind": row.get("kind"),
        "start_offset": row.get("start_offset"),
        "end_offset": row.get("end_offset"),
        "runtime_address": row.get("runtime_address"),
        "opcode_or_directive": row.get("opcode_or_directive"),
        "operand_text": row.get("operand_text"),
        "text": str(row.get("text") or "").strip(),
    }


def _review_item_payload(item: Mapping[str, object] | None) -> dict[str, object] | None:
    if item is None:
        return None
    return {
        "item_id": item.get("item_id"),
        "kind": item.get("kind"),
        "start": item.get("start"),
        "end": item.get("end"),
        "evidence_fingerprint": item.get("evidence_fingerprint"),
        "review_confidence": item.get("review_confidence"),
        "reason": item.get("reason"),
    }


def _entry_slot_key(entry: Mapping[str, object]) -> tuple[str | None, int | None]:
    symbol = entry.get("slot_symbol")
    offset = entry.get("slot_offset")
    return (
        symbol if isinstance(symbol, str) else None,
        offset if isinstance(offset, int) and not isinstance(offset, bool) else None,
    )


def _slot_keys(entries: Sequence[Mapping[str, object]]) -> set[tuple[str | None, int | None]]:
    return {_entry_slot_key(entry) for entry in entries}
