from __future__ import annotations

import copy
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import cast

from amiga_reversing.disasm import decision_journal

_MIN_CALLBACK_ADDRESS_VALUE = 0x1000


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
    runtime_rows = _rows_by_runtime_address(row_list)
    review_by_start = _review_items_by_start(review_items)
    slot_filter = _slot_filter(slot_symbol=slot_symbol, slot_offset=slot_offset)
    consumers = _slot_consumers(row_list, slot_filter=slot_filter, lookahead_rows=lookahead_rows)
    assignments = _slot_assignments(
        row_list,
        slot_filter=slot_filter,
        label_offsets=label_offsets,
        target_rows=target_rows,
        runtime_rows=runtime_rows,
        review_by_start=review_by_start,
        lookback_rows=lookback_rows,
    )
    slots = sorted({*_slot_keys(consumers), *_slot_keys(assignments)})
    slot_reports: list[dict[str, object]] = []
    for slot in slots:
        slot_consumers = [consumer for consumer in consumers if _entry_slot_key(consumer) == slot]
        slot_assignments = [assignment for assignment in assignments if _entry_slot_key(assignment) == slot]
        for assignment in slot_assignments:
            assignment["evidence_packet"] = _callback_assignment_evidence_packet(
                assignment,
                slot_consumers,
            )
            assignment["generated_orphan_code_signal"] = _callback_assignment_orphan_code_signal(
                cast(Mapping[str, object], assignment["evidence_packet"])
            )
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
    summary = {
        "consumer_count": len(consumers),
        "assignment_count": len(assignments),
        "concrete_missed_code_target_count": sum(
            cast(int, slot["concrete_missed_code_target_count"]) for slot in slot_reports
        ),
    }
    summary["blocker_triage"] = _callback_blocker_triage_summary(slot_reports)
    summary["recovered_target_classification"] = _callback_recovered_target_classification_summary(slot_reports)
    return {
        "kind": "callback_slot_report",
        "slot_filter": {"slot_symbol": slot_symbol, "slot_offset": slot_offset},
        "slot_count": len(slot_reports),
        "slots": slot_reports,
        "summary": summary,
    }


def callback_orphan_code_signals(callback_report: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    """Return callback-derived orphan-code signals that passed packet guards."""

    signals: list[dict[str, object]] = []
    for assignment in _callback_report_assignments(callback_report):
        generated = assignment.get("generated_orphan_code_signal")
        if not isinstance(generated, Mapping) or generated.get("status") != "generated":
            continue
        signal = generated.get("signal")
        if isinstance(signal, Mapping):
            signals.append(dict(signal))
    return tuple(signals)


def analysis_with_callback_orphan_code_signals(
    analysis: Mapping[str, object],
    signals: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Project callback-derived signal records into analysis sections without mutating input."""

    projected = copy.deepcopy(dict(analysis))
    sections = projected.get("sections")
    if not isinstance(sections, list):
        projected["sections"] = []
        sections = projected["sections"]
    by_section: dict[int, list[dict[str, object]]] = {}
    for signal in signals:
        section_index = _int_or_none(signal.get("section_index"))
        if section_index is None:
            section_index = _int_or_none(signal.get("hunk"))
        if section_index is None:
            section_index = 0
        payload = dict(signal)
        payload.pop("section_index", None)
        payload.pop("hunk", None)
        by_section.setdefault(section_index, []).append(payload)
    for section_index, section_signals in by_section.items():
        section = _analysis_section(sections, section_index)
        existing = section.get("orphan_code_signals")
        if not isinstance(existing, list):
            existing = []
            section["orphan_code_signals"] = existing
        known = {
            (
                _int_or_none(item.get("offset")),
                _int_or_none(item.get("size")),
                str(item.get("reason_name") or item.get("reason") or ""),
            )
            for item in existing
            if isinstance(item, Mapping)
        }
        for signal in section_signals:
            key = (
                _int_or_none(signal.get("offset")),
                _int_or_none(signal.get("size")),
                str(signal.get("reason_name") or signal.get("reason") or ""),
            )
            if key not in known:
                existing.append(signal)
                known.add(key)
    return projected


def callback_decision_record(
    packet: Mapping[str, object],
    action: str,
    *,
    target_id: str,
    decision_id: str,
    prev: str | None = None,
    reason: str | None = None,
    created_at: str = "2026-05-24T00:00:00+00:00",
) -> dict[str, object]:
    """Build a Decision Journal record for a callback-derived code packet."""

    selected_identity = _packet_selected_identity(packet, target_id)
    candidate_id = str(packet.get("candidate_id") or f"callback-code:{selected_identity['selected_use_id']}")
    record: dict[str, object] = {
        "schema": decision_journal.DECISION_JOURNAL_SCHEMA,
        "decision_id": decision_id,
        "prev": prev,
        "created_at": created_at,
        "actor": {"kind": "llm", "name": "codex"},
        "action": action,
        "packet_id": packet.get("packet_id"),
        "candidate_id": candidate_id,
        "selected_identity": selected_identity,
        "evidence_refs": [str(packet.get("packet_id") or candidate_id)],
        "conflicts": [],
    }
    if action == "accept_fact":
        record.update(
            {
                "fact_type": "callback_derived_code",
                "scope": {
                    "kind": "selected_callback_target",
                    "hunk": selected_identity["hunk"],
                    "addr": selected_identity["addr"],
                    "operand_index": selected_identity["operand_index"],
                },
                "render_intent": {
                    "effect": "classify_range_as_code",
                    "selected_identity": selected_identity,
                    "source": "callback_slot",
                },
            }
        )
    elif action == "defer_fact":
        record["defer_reason"] = reason or "callback-derived code evidence requires more review"
    elif action == "reject_fact":
        record["reject_reason"] = reason or "callback-derived code evidence rejected"
    else:
        raise ValueError(action)
    return record


def callback_decision_lane(
    packet: Mapping[str, object],
    journal_projection: Mapping[str, object],
    *,
    target_id: str,
) -> dict[str, object]:
    selected_identity = _packet_selected_identity(packet, target_id)
    key = f"{target_id}:{selected_identity['selected_use_id']}"
    by_identity = journal_projection.get("by_selected_identity")
    group = by_identity.get(key) if isinstance(by_identity, Mapping) else None
    group = group if isinstance(group, Mapping) else {}
    accepted = _matching_callback_decisions(group.get("accepted_facts"), packet)
    deferred = _matching_callback_decisions(group.get("deferred_facts"), packet)
    rejected = _matching_callback_decisions(group.get("rejected_facts"), packet)
    return {
        "authority": "decision_journal",
        "status": "accepted" if accepted else "deferred" if deferred else "rejected" if rejected else "missing",
        "accepted": accepted,
        "deferred": deferred,
        "rejected": rejected,
    }


def analysis_with_accepted_callback_code(
    analysis: Mapping[str, object],
    journal_projection: Mapping[str, object],
) -> dict[str, object]:
    projected = copy.deepcopy(dict(analysis))
    accepted = [
        record
        for record in _mapping_sequence(journal_projection.get("accepted_facts"))
        if record.get("fact_type") == "callback_derived_code"
    ]
    projected["accepted_callback_code_facts"] = accepted
    by_section: dict[int, list[dict[str, object]]] = {}
    for record in accepted:
        scope = record.get("scope")
        if not isinstance(scope, Mapping) or scope.get("kind") != "selected_callback_target":
            continue
        hunk = _int_or_none(scope.get("hunk")) or 0
        addr = _int_or_none(scope.get("addr")) or 0
        by_section.setdefault(hunk, []).append(
            {
                "offset": addr,
                "size": 1,
                "source_evidence_id": record.get("decision_id"),
                "source_family": "callback_derived_code",
                "status": "accepted",
            }
        )
    sections = projected.get("sections")
    if not isinstance(sections, list):
        projected["sections"] = []
        sections = projected["sections"]
    for hunk, facts in by_section.items():
        section = _analysis_section(sections, hunk)
        section["accepted_callback_code_ranges"] = [
            *[dict(item) for item in _mapping_sequence(section.get("accepted_callback_code_ranges"))],
            *facts,
        ]
    return projected


def callback_render_effect(
    packet: Mapping[str, object],
    journal_projection: Mapping[str, object],
    *,
    target_id: str,
    verifier_report: Mapping[str, object] | None = None,
) -> dict[str, object]:
    lane = callback_decision_lane(packet, journal_projection, target_id=target_id)
    if lane["status"] != "accepted":
        return {"status": "blocked", "blockers": ["accepted_callback_code_fact_required"], "effect": None}
    verifier = callback_verifier_gate(packet, journal_projection, target_id=target_id, verifier_report=verifier_report)
    if verifier["status"] != "passed":
        return {"status": "blocked", "blockers": verifier["blockers"], "effect": None}
    selected_identity = _packet_selected_identity(packet, target_id)
    return {
        "status": "ready",
        "blockers": [],
        "effect": {
            "kind": "classify_range_as_code",
            "hunk": selected_identity["hunk"],
            "start": selected_identity["addr"],
            "end": _packet_target_end(packet),
            "source": "accepted_callback_derived_code",
        },
    }


def callback_verifier_gate(
    packet: Mapping[str, object],
    journal_projection: Mapping[str, object],
    *,
    target_id: str,
    verifier_report: Mapping[str, object] | None,
) -> dict[str, object]:
    lane = callback_decision_lane(packet, journal_projection, target_id=target_id)
    blockers: list[str] = []
    if lane["status"] != "accepted":
        blockers.append("accepted_callback_code_fact_required")
    if verifier_report is None:
        blockers.extend(["missing_semantic_reload", "missing_generated_source_diff", "missing_negative_safety", "missing_exact_round_trip"])
    else:
        for layer in ("semantic_reload", "generated_source", "negative_safety", "exact_round_trip"):
            if verifier_report.get(layer) != "passed":
                blockers.append(f"{layer}_not_passed")
    return {
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "required_layers": ["semantic_reload", "generated_source", "negative_safety", "exact_round_trip"],
    }


def _slot_filter(
    *,
    slot_symbol: str | None,
    slot_offset: int | None,
) -> Callable[[Mapping[str, object]], bool]:
    normalized_symbol = slot_symbol.strip() if isinstance(slot_symbol, str) and slot_symbol.strip() else None

    def matches(ref: Mapping[str, object]) -> bool:
        if normalized_symbol is not None and ref.get("symbol") != normalized_symbol:
            return False
        return not (slot_offset is not None and ref.get("displacement") != slot_offset)

    return matches


def _slot_consumers(
    rows: list[Mapping[str, object]],
    *,
    slot_filter: Callable[[Mapping[str, object]], bool],
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
    slot_filter: Callable[[Mapping[str, object]], bool],
    label_offsets: dict[str, int],
    target_rows: dict[int, Mapping[str, object]],
    runtime_rows: dict[int, Mapping[str, object]],
    review_by_start: dict[int, Mapping[str, object]],
    lookback_rows: int,
) -> list[dict[str, object]]:
    assignments: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        ref = _first_app_slot_ref(row, access="write", slot_filter=slot_filter)
        if ref is None:
            continue
        source_register = _source_register(row)
        source = _stored_source_recovery(
            rows,
            index,
            source_register=source_register,
            label_offsets=label_offsets,
            target_rows=target_rows,
            runtime_rows=runtime_rows,
            lookback_rows=max(lookback_rows, 32),
        )
        symbol_row = source.get("value_source")
        symbol_row = symbol_row if isinstance(symbol_row, Mapping) else None
        symbol = source.get("stored_symbol") if isinstance(source.get("stored_symbol"), str) else None
        target_offset = _int_or_none(source.get("stored_source_offset"))
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
                "stored_source_offset_provenance": source.get("provenance"),
                "target": _row_payload(target_row),
                "target_kind": target_row.get("kind") if target_row is not None else None,
                "review_item": _review_item_payload(review_item),
                "action_readiness": _assignment_action_readiness(target_row, review_item),
                "evidence": "pc_relative_symbol_loaded_then_stored_to_callback_slot",
            }
        )
    return assignments


def _stored_source_recovery(
    rows: list[Mapping[str, object]],
    index: int,
    *,
    source_register: str | None,
    label_offsets: Mapping[str, int],
    target_rows: Mapping[int, Mapping[str, object]],
    runtime_rows: Mapping[int, Mapping[str, object]],
    lookback_rows: int,
) -> dict[str, object]:
    row = rows[index]
    direct = _direct_store_source_recovery(row, label_offsets, target_rows, runtime_rows)
    if direct is not None:
        return direct
    register = _register_store_source_recovery(
        rows,
        index,
        source_register=source_register,
        label_offsets=label_offsets,
        lookback_rows=lookback_rows,
    )
    if register is not None:
        return register
    return {
        "stored_symbol": None,
        "stored_source_offset": None,
        "value_source": None,
        "provenance": {
            "kind": "unresolved",
            "status": "blocked",
            "reason": "store_does_not_write_an_address_register_value"
            if source_register is None
            else "stored_register_has_no_nearby_symbol_load",
        },
    }


def _direct_store_source_recovery(
    row: Mapping[str, object],
    label_offsets: Mapping[str, int],
    target_rows: Mapping[int, Mapping[str, object]],
    runtime_rows: Mapping[int, Mapping[str, object]],
) -> dict[str, object] | None:
    immediate = _store_immediate_value(row)
    if immediate is None:
        return None
    if isinstance(immediate, str):
        offset = label_offsets.get(immediate)
        return {
            "stored_symbol": immediate,
            "stored_source_offset": offset,
            "value_source": row,
            "provenance": {
                "kind": "absolute_label",
                "status": "resolved" if offset is not None else "blocked",
                "symbol": immediate,
                "reason": "absolute_label_resolved" if offset is not None else "absolute_label_missing_listing_offset",
            },
        }
    if immediate < _MIN_CALLBACK_ADDRESS_VALUE:
        return {
            "stored_symbol": None,
            "stored_source_offset": None,
            "value_source": row,
            "provenance": {
                "kind": "direct_immediate",
                "status": "blocked",
                "value": immediate,
                "reason": "direct_immediate_below_address_threshold",
            },
        }
    source_row = target_rows.get(immediate)
    runtime_row = runtime_rows.get(immediate)
    if source_row is not None and runtime_row is not None:
        runtime_source_offset = _int_or_none(runtime_row.get("start_offset"))
        return {
            "stored_symbol": None,
            "stored_source_offset": None,
            "value_source": row,
            "provenance": {
                "kind": "direct_immediate_ambiguous_address",
                "status": "blocked",
                "value": immediate,
                "source_offset_target": immediate,
                "runtime_address_target_offset": runtime_source_offset,
                "reason": "direct_immediate_matches_source_offset_and_runtime_address",
            },
        }
    if source_row is not None:
        return {
            "stored_symbol": None,
            "stored_source_offset": immediate,
            "value_source": row,
            "provenance": {
                "kind": "direct_source_offset",
                "status": "resolved",
                "value": immediate,
                "reason": "direct_immediate_matches_listing_source_offset",
            },
        }
    if runtime_row is not None:
        source_offset = _int_or_none(runtime_row.get("start_offset"))
        return {
            "stored_symbol": None,
            "stored_source_offset": source_offset,
            "value_source": row,
            "provenance": {
                "kind": "runtime_address",
                "status": "resolved" if source_offset is not None else "blocked",
                "value": immediate,
                "reason": "direct_immediate_matches_listing_runtime_address"
                if source_offset is not None
                else "runtime_address_row_missing_source_offset",
            },
        }
    return {
        "stored_symbol": None,
        "stored_source_offset": None,
        "value_source": row,
        "provenance": {
            "kind": "direct_immediate",
            "status": "blocked",
            "value": immediate,
            "reason": "direct_immediate_not_listing_source_or_runtime_address",
        },
    }


def _register_store_source_recovery(
    rows: list[Mapping[str, object]],
    index: int,
    *,
    source_register: str | None,
    label_offsets: Mapping[str, int],
    lookback_rows: int,
) -> dict[str, object] | None:
    if source_register is None:
        return None
    source, blocker = _previous_symbol_load_or_blocker(rows, index, source_register, lookback_rows=lookback_rows)
    if source is None:
        return {
            "stored_symbol": None,
            "stored_source_offset": None,
            "value_source": None,
            "provenance": {
                "kind": "register_local_provenance",
                "status": "blocked",
                "register": source_register,
                "reason": blocker or "stored_register_has_no_nearby_symbol_load",
            },
        }
    symbol = _symbol_operand(source)
    offset = label_offsets.get(symbol) if symbol is not None else None
    return {
        "stored_symbol": symbol,
        "stored_source_offset": offset,
        "value_source": source,
        "provenance": {
            "kind": "register_symbol_load",
            "status": "resolved" if offset is not None else "blocked",
            "register": source_register,
            "symbol": symbol,
            "reason": "local_register_symbol_load_resolved"
            if offset is not None
            else "local_register_symbol_load_missing_listing_offset",
            "lookback_row_count": min(index, lookback_rows),
        },
    }


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


def _callback_assignment_evidence_packet(
    assignment: Mapping[str, object],
    consumers: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    target = assignment.get("target")
    target = target if isinstance(target, Mapping) else None
    store = assignment.get("store")
    store = store if isinstance(store, Mapping) else None
    review_item = assignment.get("review_item")
    review_item = review_item if isinstance(review_item, Mapping) else None
    hunk = _row_hunk(target) if target is not None else _row_hunk(store)
    target_start = _int_or_none(assignment.get("stored_source_offset"))
    target_end = _int_or_none(target.get("end_offset")) if target is not None else None
    target_bytes = _row_bytes(target)
    selected_identity = {
        "segment_id": f"s{hunk or 0}",
        "hunk": hunk or 0,
        "addr": target_start,
        "operand_index": 0,
        "selected_use_id": f"s{hunk or 0}:{target_start or 0:08X}:op0",
    }
    false_positive_checks = _callback_false_positive_checks(target, target_bytes)
    review_gate_blockers = list(_string_sequence(assignment.get("action_readiness"), "blockers"))
    blockers = [
        check["kind"]
        for check in false_positive_checks
        if check.get("status") == "risk"
    ]
    if not consumers:
        blockers.append("missing_callback_consumer")
    if target_start is None:
        blockers.append("missing_stored_source_offset")
    if target is None:
        blockers.append("target_row_missing")
    elif target.get("kind") == "instruction":
        blockers.append("target_already_code")
    packet_id = "callback-code-packet:{}:{}:{}".format(
        assignment.get("slot_symbol") or "unknown_slot",
        _row_id(store) or "unknown_store",
        selected_identity["selected_use_id"],
    )
    blockers = sorted(set(blockers))
    recovered_target_classification = _callback_recovered_target_classification(
        assignment,
        consumers,
        target,
        target_bytes,
        false_positive_checks,
        blockers,
    )
    return {
        "packet_kind": "callback_derived_code_evidence_packet",
        "schema_version": 1,
        "packet_id": packet_id,
        "candidate_id": f"callback-code:{selected_identity['selected_use_id']}",
        "selected_identity": selected_identity,
        "callback_slot": {
            "slot_symbol": assignment.get("slot_symbol"),
            "slot_offset": assignment.get("slot_offset"),
            "base_register": assignment.get("base_register"),
        },
        "callback_store": {
            "store": store,
            "stored_register": assignment.get("stored_register"),
            "value_source": assignment.get("value_source"),
            "stored_symbol": assignment.get("stored_symbol"),
            "stored_source_offset": target_start,
            "stored_source_offset_provenance": assignment.get("stored_source_offset_provenance"),
        },
        "callback_consumers": list(consumers),
        "target": {
            "row": target,
            "bytes": target_bytes,
            "classification": target.get("kind") if target is not None else None,
            "range": {"hunk": hunk or 0, "start": target_start, "end": target_end},
        },
        "review_item": review_item,
        "existing_review_gate": {
            "status": assignment.get("action_readiness", {}).get("status")
            if isinstance(assignment.get("action_readiness"), Mapping)
            else None,
            "blockers": review_gate_blockers,
        },
        "xrefs": [
            {
                "kind": "callback_slot_store",
                "source": store,
                "target": target,
            },
            *(
                {
                    "kind": "callback_slot_indirect_consumer",
                    "source": consumer.get("load"),
                    "target": consumer.get("indirect_transfer"),
                }
                for consumer in consumers
            ),
        ],
        "false_positive_checks": false_positive_checks,
        "conflicts": {"status": "explicit_empty", "explicit_empty": True, "items": []},
        "blockers": blockers,
        "blocker_triage": _callback_blocker_triage(
            assignment,
            consumers,
            target,
            target_bytes,
            blockers,
        ),
        "recovered_target_classification": recovered_target_classification,
        "status": "blocked" if blockers else "action_ready",
        "render_readiness": {
            "status": "blocked",
            "blockers": ["decision_journal_accept_required", "verifier_gates_required"],
        },
        "verifier_readiness": {
            "status": "blocked",
            "required_layers": ["semantic_reload", "generated_source", "negative_safety", "exact_round_trip"],
        },
    }


def _callback_assignment_orphan_code_signal(packet: Mapping[str, object]) -> dict[str, object]:
    blockers = list(_string_sequence(packet, "blockers"))
    target = packet.get("target")
    target = target if isinstance(target, Mapping) else {}
    row = target.get("row")
    row = row if isinstance(row, Mapping) else {}
    selected_identity = packet.get("selected_identity")
    selected_identity = selected_identity if isinstance(selected_identity, Mapping) else {}
    target_range = target.get("range")
    target_range = target_range if isinstance(target_range, Mapping) else {}
    target_bytes = [value for value in target.get("bytes", []) if isinstance(value, int)]
    if row.get("kind") != "data":
        blockers.append("target_not_data_row")
    if not _looks_like_terminal_code_bytes(target_bytes):
        blockers.append("target_bytes_not_terminal_callback_code")
    if blockers:
        return {"status": "blocked", "blockers": sorted(set(blockers))}
    start = _int_or_none(target_range.get("start")) or 0
    end = _int_or_none(target_range.get("end")) or start + len(target_bytes)
    size = max(1, min(len(target_bytes), end - start))
    return {
        "status": "generated",
        "signal": {
            "section_index": _int_or_none(target_range.get("hunk")) or 0,
            "offset": start,
            "size": size,
            "terminal_offset": max(start, start + size - 2),
            "reason_name": "callback_slot",
            "status_name": "unresolved",
            "context": "callback_slot_store",
            "missing_inbound": "callback",
            "callback_slot": packet.get("callback_slot"),
            "stored_code_pointer": packet.get("callback_store"),
            "refs": packet.get("xrefs"),
            "packet_id": packet.get("packet_id"),
            "selected_identity": dict(selected_identity),
        },
    }


def _callback_recovered_target_classification(
    assignment: Mapping[str, object],
    consumers: Sequence[Mapping[str, object]],
    target: Mapping[str, object] | None,
    target_bytes: Sequence[int],
    false_positive_checks: Sequence[Mapping[str, object]],
    blockers: Sequence[str],
) -> dict[str, object] | None:
    target_start = _int_or_none(assignment.get("stored_source_offset"))
    if target_start is None:
        return None
    review_item = assignment.get("review_item")
    review_item = review_item if isinstance(review_item, Mapping) else None
    target_kind = target.get("kind") if target is not None else None
    base: dict[str, object] = {
        "target_offset": target_start,
        "target_kind": target_kind,
        "target_bytes": list(target_bytes),
        "review_item_kind": review_item.get("kind") if review_item is not None else None,
        "consumer_count": len(consumers),
        "stored_source_offset_provenance": assignment.get("stored_source_offset_provenance"),
    }
    if target is None:
        return {
            **base,
            "category": "blocked_non_code",
            "reason": "recovered_offset_has_no_listing_target_row",
            "bridge_action": "blocked",
        }
    if target_kind == "instruction":
        return {
            **base,
            "category": "already_represented",
            "reason": "target_listing_row_is_already_instruction",
            "bridge_action": "none",
        }
    if target_kind != "data":
        return {
            **base,
            "category": "blocked_non_code",
            "reason": "recovered_target_row_is_not_data_or_instruction",
            "bridge_action": "blocked",
        }
    if review_item is not None and review_item.get("kind") == "orphan_code_candidate":
        return {
            **base,
            "category": "already_represented",
            "reason": "orphan_code_candidate_review_item_already_exists",
            "bridge_action": "existing_review_item",
        }
    risk_kinds = {
        str(check.get("kind"))
        for check in false_positive_checks
        if check.get("status") == "risk"
    }
    if risk_kinds & {"all_zero_data", "data_like_directive"}:
        return {
            **base,
            "category": "real_data",
            "reason": "target_data_is_zero_fill_or_data_directive",
            "bridge_action": "blocked",
            "risk_kinds": sorted(risk_kinds),
        }
    code_like = _looks_like_terminal_code_bytes(target_bytes)
    if not code_like:
        return {
            **base,
            "category": "real_data",
            "reason": "target_bytes_do_not_look_like_terminal_callback_code",
            "bridge_action": "blocked",
        }
    if not consumers:
        return {
            **base,
            "category": "blocked_non_code",
            "reason": "code_like_data_lacks_callback_consumer",
            "bridge_action": "blocked",
        }
    if review_item is not None and review_item.get("kind") != "orphan_code_candidate":
        return {
            **base,
            "category": "missed_code_candidate",
            "reason": "code_like_data_has_non_code_review_item",
            "bridge_action": "surface_orphan_code_signal",
            "existing_blockers": list(blockers),
        }
    return {
        **base,
        "category": "missed_code_candidate",
        "reason": "code_like_data_has_callback_consumer_and_no_review_item",
        "bridge_action": "surface_orphan_code_signal",
    }


def _callback_recovered_target_classification_summary(slot_reports: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_category: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    for slot in slot_reports:
        assignments = slot.get("assignments")
        if not isinstance(assignments, Sequence) or isinstance(assignments, str):
            continue
        for assignment in assignments:
            if not isinstance(assignment, Mapping):
                continue
            packet = assignment.get("evidence_packet")
            packet = packet if isinstance(packet, Mapping) else {}
            classification = packet.get("recovered_target_classification")
            if not isinstance(classification, Mapping):
                continue
            category = classification.get("category")
            reason = classification.get("reason")
            if isinstance(category, str):
                by_category[category] = by_category.get(category, 0) + 1
            if isinstance(reason, str):
                by_reason[reason] = by_reason.get(reason, 0) + 1
    return {
        "by_category": dict(sorted(by_category.items())),
        "by_reason": dict(sorted(by_reason.items())),
    }


def _callback_blocker_triage(
    assignment: Mapping[str, object],
    consumers: Sequence[Mapping[str, object]],
    target: Mapping[str, object] | None,
    target_bytes: Sequence[int],
    blockers: Sequence[str],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    target_start = _int_or_none(assignment.get("stored_source_offset"))
    store = assignment.get("store")
    store = store if isinstance(store, Mapping) else {}
    operand_text = str(store.get("operand_text") or "")
    stored_register = assignment.get("stored_register")
    value_source = assignment.get("value_source")
    value_source = value_source if isinstance(value_source, Mapping) else None
    provenance = assignment.get("stored_source_offset_provenance")
    provenance = provenance if isinstance(provenance, Mapping) else None
    for blocker in blockers:
        if blocker == "missing_stored_source_offset":
            result.append(
                {
                    "blocker": blocker,
                    "classification": "narrower_follow_up",
                    "reason": _missing_stored_source_offset_reason(
                        operand_text=operand_text,
                        stored_register=stored_register,
                        value_source=value_source,
                        provenance=provenance,
                    ),
                    "provenance": dict(provenance) if provenance is not None else None,
                }
            )
        elif blocker == "target_row_missing":
            result.append(
                {
                    "blocker": blocker,
                    "classification": "derived_blocker" if target_start is None else "lookup_gap",
                    "reason": "stored_source_offset_missing" if target_start is None else "no_listing_row_at_stored_source_offset",
                }
            )
        elif blocker == "missing_target_bytes":
            result.append(
                {
                    "blocker": blocker,
                    "classification": "derived_blocker" if target is None else "extraction_gap",
                    "reason": "target_row_missing" if target is None else "data_listing_row_has_no_bytes",
                }
            )
        elif blocker == "missing_callback_consumer":
            result.append(
                {
                    "blocker": blocker,
                    "classification": "factual_non_actionable",
                    "reason": "no_slot_read_to_indirect_jsr_or_jmp_consumer",
                    "consumer_count": len(consumers),
                }
            )
        elif blocker == "target_already_code":
            result.append(
                {
                    "blocker": blocker,
                    "classification": "already_satisfied",
                    "reason": "target_listing_row_is_already_instruction",
                }
            )
        elif blocker in {"all_zero_data", "data_like_directive"}:
            result.append(
                {
                    "blocker": blocker,
                    "classification": "factual_non_actionable",
                    "reason": "target_data_does_not_look_like_terminal_callback_code",
                    "target_bytes": list(target_bytes),
                }
            )
        else:
            result.append(
                {
                    "blocker": blocker,
                    "classification": "unknown",
                    "reason": "unclassified_callback_blocker",
                }
            )
    return result


def _missing_stored_source_offset_reason(
    *,
    operand_text: str,
    stored_register: object,
    value_source: Mapping[str, object] | None,
    provenance: Mapping[str, object] | None,
) -> str:
    if provenance is not None and isinstance(provenance.get("reason"), str):
        return str(provenance["reason"])
    if "#" in operand_text:
        return "direct_immediate_store_requires_address_model_proof"
    if isinstance(stored_register, str) and value_source is None:
        return "stored_register_has_no_nearby_symbol_load"
    if stored_register is None:
        return "store_does_not_write_an_address_register_value"
    return "stored_value_is_not_symbol_backed"


def _callback_blocker_triage_summary(slot_reports: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_blocker: dict[str, int] = {}
    by_classification: dict[str, int] = {}
    for slot in slot_reports:
        assignments = slot.get("assignments")
        if not isinstance(assignments, Sequence) or isinstance(assignments, str):
            continue
        for assignment in assignments:
            if not isinstance(assignment, Mapping):
                continue
            packet = assignment.get("evidence_packet")
            packet = packet if isinstance(packet, Mapping) else {}
            for item in _mapping_sequence(packet.get("blocker_triage")):
                blocker = item.get("blocker")
                classification = item.get("classification")
                if isinstance(blocker, str):
                    by_blocker[blocker] = by_blocker.get(blocker, 0) + 1
                if isinstance(classification, str):
                    by_classification[classification] = by_classification.get(classification, 0) + 1
    return {
        "by_blocker": dict(sorted(by_blocker.items())),
        "by_classification": dict(sorted(by_classification.items())),
    }


def _callback_false_positive_checks(
    row: Mapping[str, object] | None,
    target_bytes: Sequence[int],
) -> list[dict[str, object]]:
    text = str(row.get("text") or "") if row is not None else ""
    directive = str(row.get("opcode_or_directive") or "").lower() if row is not None else ""
    all_zero = bool(target_bytes) and all(value == 0 for value in target_bytes)
    missing_bytes = row is None or (row.get("kind") == "data" and not target_bytes)
    return [
        {"kind": "all_zero_data", "status": "risk" if all_zero or _dcb_zero_fill(text) else "clear"},
        {"kind": "data_like_directive", "status": "risk" if directive.startswith("dcb") else "clear"},
        {"kind": "missing_target_bytes", "status": "risk" if missing_bytes else "clear"},
    ]


def _looks_like_terminal_code_bytes(values: Sequence[int]) -> bool:
    if len(values) < 4:
        return False
    return values[-2:] == [0x4E, 0x75] or values[:2] in ([0x4E, 0x75], [0x4E, 0xF9], [0x4E, 0xD0])


def _row_bytes(row: Mapping[str, object] | None) -> list[int]:
    if row is None:
        return []
    raw = row.get("bytes")
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        values = [value for value in raw if isinstance(value, int) and not isinstance(value, bool)]
        if values:
            return [value & 0xFF for value in values]
    text = str(row.get("text") or "")
    return [int(match, 16) for match in re.findall(r"\$([0-9A-Fa-f]{2})\b", text)]


def _dcb_zero_fill(text: str) -> bool:
    normalized = text.replace(" ", "").lower()
    return "dcb" in normalized and (",$00" in normalized or ",0" in normalized)


def _callback_report_assignments(callback_report: Mapping[str, object]) -> list[Mapping[str, object]]:
    result: list[Mapping[str, object]] = []
    slots = callback_report.get("slots")
    if not isinstance(slots, Sequence) or isinstance(slots, str):
        return result
    for slot in slots:
        if not isinstance(slot, Mapping):
            continue
        assignments = slot.get("assignments")
        if not isinstance(assignments, Sequence) or isinstance(assignments, str):
            continue
        result.extend(assignment for assignment in assignments if isinstance(assignment, Mapping))
    return result


def _analysis_section(sections: list[object], section_index: int) -> dict[str, object]:
    for section in sections:
        if isinstance(section, dict) and _int_or_none(section.get("section_index")) == section_index:
            return section
    section: dict[str, object] = {"section_index": section_index, "section_size": 0}
    sections.append(section)
    return section


def _first_app_slot_ref(
    row: Mapping[str, object],
    *,
    access: str,
    slot_filter: Callable[[Mapping[str, object]], bool],
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
        if _destination_register(candidate) == register:
            return None
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
    source, _blocker = _previous_symbol_load_or_blocker(rows, index, register, lookback_rows=lookback_rows)
    return source


def _previous_symbol_load_or_blocker(
    rows: list[Mapping[str, object]],
    index: int,
    register: str | None,
    *,
    lookback_rows: int,
) -> tuple[Mapping[str, object] | None, str | None]:
    if register is None:
        return None, "store_does_not_write_an_address_register_value"
    saw_label_boundary = False
    for candidate in reversed(rows[max(0, index - lookback_rows) : index]):
        if candidate.get("kind") == "label":
            saw_label_boundary = True
            continue
        destination = _destination_register(candidate)
        if destination is None:
            continue
        if destination != register:
            continue
        if _symbol_operand(candidate) is not None:
            if saw_label_boundary:
                return None, "register_symbol_load_crosses_label_boundary"
            return candidate, None
        return None, "stored_register_clobbered_before_store"
    return None, "stored_register_has_no_nearby_symbol_load"


def _store_immediate_value(row: Mapping[str, object]) -> int | str | None:
    text = str(row.get("operand_text") or "")
    match = re.search(r"#(?:\$([0-9A-Fa-f]+)|([0-9]+)|([A-Za-z_][\w.]*)).*?,", text)
    if match is None:
        return None
    if match.group(1) is not None:
        return int(match.group(1), 16)
    if match.group(2) is not None:
        return int(match.group(2), 10)
    return match.group(3)


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


def _rows_by_runtime_address(rows: Sequence[Mapping[str, object]]) -> dict[int, Mapping[str, object]]:
    result: dict[int, Mapping[str, object]] = {}
    for row in rows:
        runtime_address = row.get("runtime_address")
        if not isinstance(runtime_address, int) or isinstance(runtime_address, bool):
            continue
        if row.get("kind") in {"instruction", "data"} and runtime_address not in result:
            result[runtime_address] = row
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
        "bytes": _row_bytes(row),
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


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _row_hunk(row: Mapping[str, object] | None) -> int | None:
    if row is None:
        return None
    row_key = row.get("row_key")
    if isinstance(row_key, str):
        match = re.match(r"s(\d+):", row_key)
        if match:
            return int(match.group(1))
    return _int_or_none(row.get("section_index"))


def _row_id(row: Mapping[str, object] | None) -> str | None:
    if row is None:
        return None
    row_key = row.get("row_key")
    if isinstance(row_key, str) and row_key:
        return row_key
    start = _int_or_none(row.get("start_offset"))
    if start is None:
        return None
    return f"offset:{start:08X}"


def _string_sequence(mapping: object, key: str) -> list[str]:
    if not isinstance(mapping, Mapping):
        return []
    value = mapping.get(key)
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [item for item in value if isinstance(item, str)]


def _mapping_sequence(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _packet_selected_identity(packet: Mapping[str, object], target_id: str) -> dict[str, object]:
    raw = packet.get("selected_identity")
    raw = raw if isinstance(raw, Mapping) else {}
    hunk = _int_or_none(raw.get("hunk")) or 0
    addr = _int_or_none(raw.get("addr")) or 0
    operand_index = _int_or_none(raw.get("operand_index")) or 0
    selected_use_id = raw.get("selected_use_id")
    if not isinstance(selected_use_id, str) or not selected_use_id:
        selected_use_id = f"s{hunk}:{addr:08X}:op{operand_index}"
    segment_id = raw.get("segment_id")
    if not isinstance(segment_id, str) or not segment_id:
        segment_id = f"s{hunk}"
    return {
        "target_id": target_id,
        "segment_id": segment_id,
        "hunk": hunk,
        "addr": addr,
        "operand_index": operand_index,
        "selected_use_id": selected_use_id,
    }


def _matching_callback_decisions(value: object, packet: Mapping[str, object]) -> list[dict[str, object]]:
    candidate_id = packet.get("candidate_id")
    return [
        dict(record)
        for record in _mapping_sequence(value)
        if record.get("fact_type") in {None, "callback_derived_code"}
        and (candidate_id is None or record.get("candidate_id") == candidate_id)
    ]


def _packet_target_end(packet: Mapping[str, object]) -> int:
    target = packet.get("target")
    target = target if isinstance(target, Mapping) else {}
    target_range = target.get("range")
    target_range = target_range if isinstance(target_range, Mapping) else {}
    end = _int_or_none(target_range.get("end"))
    if end is not None:
        return end
    selected = packet.get("selected_identity")
    selected = selected if isinstance(selected, Mapping) else {}
    return (_int_or_none(selected.get("addr")) or 0) + 1
