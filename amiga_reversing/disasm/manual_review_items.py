from __future__ import annotations

from amiga_reversing.disasm.manual_actions import finalize_review_items


def analysis_review_items(
    analysis: dict[str, object],
    *,
    resolutions: tuple[dict[str, object], ...] = (),
) -> tuple[dict[str, object], ...]:
    items: list[dict[str, object]] = []
    policy_items = _structured_data_ranges(analysis)
    sections = analysis.get("sections")
    if not isinstance(sections, list):
        return ()
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_index = _int_field(section, "section_index", 0)
        section_size = _int_field(section, "section_size", 0)
        items.extend(_orphan_code_items(section, section_index))
        items.extend(_suspicious_instruction_items(section, section_index))
        items.extend(_unreconciled_data_items(section, section_index, section_size, policy_items))
    return finalize_review_items(tuple(items), resolutions)


def _orphan_code_items(section: dict[str, object], section_index: int) -> list[dict[str, object]]:
    signals = section.get("orphan_code_signals")
    if not isinstance(signals, list):
        return []
    items: list[dict[str, object]] = []
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        status = signal.get("status_name") or signal.get("status")
        if status in {"rejected", "suppressed", "linked", "promoted"}:
            continue
        start = _int_field(signal, "offset", _int_field(signal, "start_offset", 0))
        size = max(1, _int_field(signal, "size", 2))
        items.append(
            {
                "kind": "orphan_code_candidate",
                "scope": "range",
                "state": "open",
                "hunk": section_index,
                "start": start,
                "end": start + size,
                "review_confidence": "medium",
                "reason": signal.get("reason_name") or signal.get("reason"),
                "signal_status": status,
                "message": "Potential code has no accepted inbound evidence",
                "source": "analysis",
            }
        )
    return items


def _suspicious_instruction_items(section: dict[str, object], section_index: int) -> list[dict[str, object]]:
    violations = section.get("violations")
    if not isinstance(violations, list):
        return []
    items: list[dict[str, object]] = []
    for violation in violations:
        if not isinstance(violation, dict):
            continue
        start = _int_field(violation, "offset", _int_field(violation, "start_offset", 0))
        size = max(1, _int_field(violation, "size", 2))
        items.append(
            {
                "kind": "suspicious_instruction_decode",
                "scope": "range",
                "state": "open",
                "hunk": section_index,
                "start": start,
                "end": start + size,
                "review_confidence": "high",
                "violation_kind": violation.get("kind_name") or violation.get("kind"),
                "required_cpu": violation.get("required_cpu_name") or violation.get("required_cpu"),
                "message": "Accepted or candidate instruction decode violates target policy",
                "source": "analysis",
            }
        )
    return items


def _unreconciled_data_items(
    section: dict[str, object],
    section_index: int,
    section_size: int,
    policy_items: dict[int, list[tuple[int, int]]],
) -> list[dict[str, object]]:
    if section_size <= 0:
        return []
    covered = _ranges_from_blocks(section)
    covered.extend(policy_items.get(section_index, []))
    covered.extend(_ranges_from_entity_hints(section))
    merged = _merge_ranges(covered, section_size)
    gaps: list[dict[str, object]] = []
    cursor = 0
    for start, end in merged:
        if cursor < start:
            gaps.append(_unreconciled_item(section_index, cursor, start))
        cursor = max(cursor, end)
    if cursor < section_size:
        gaps.append(_unreconciled_item(section_index, cursor, section_size))
    return gaps


def _unreconciled_item(section_index: int, start: int, end: int) -> dict[str, object]:
    return {
        "kind": "unreconciled_data_range",
        "scope": "range",
        "state": "open",
        "hunk": section_index,
        "start": start,
        "end": end,
        "review_confidence": "low",
        "message": "Range has no accepted code, data, metadata, policy, or manual seed evidence",
        "source": "analysis",
    }


def _ranges_from_blocks(section: dict[str, object]) -> list[tuple[int, int]]:
    blocks = section.get("blocks")
    if not isinstance(blocks, list):
        return []
    ranges: list[tuple[int, int]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        start = _int_field(block, "start_offset", 0)
        end = _int_field(block, "end_offset", start)
        if end > start:
            ranges.append((start, end))
    return ranges


def _ranges_from_entity_hints(section: dict[str, object]) -> list[tuple[int, int]]:
    hints = section.get("entity_hints")
    if not isinstance(hints, list):
        return []
    ranges: list[tuple[int, int]] = []
    for hint in hints:
        if not isinstance(hint, dict):
            continue
        start = _int_field(hint, "offset", _int_field(hint, "start_offset", 0))
        end = _int_field(hint, "end_offset", start + max(1, _int_field(hint, "size", 1)))
        if end > start:
            ranges.append((start, end))
    return ranges


def _structured_data_ranges(analysis: dict[str, object]) -> dict[int, list[tuple[int, int]]]:
    policy = analysis.get("analysis_policy")
    if not isinstance(policy, dict):
        return {}
    raw_items = policy.get("structured_data_items")
    if not isinstance(raw_items, list):
        return {}
    result: dict[int, list[tuple[int, int]]] = {}
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        section = _int_field(item, "section_index", 0)
        start = _int_field(item, "offset", 0)
        size = max(1, _int_field(item, "size", 1))
        result.setdefault(section, []).append((start, start + size))
    return result


def _merge_ranges(ranges: list[tuple[int, int]], section_size: int) -> list[tuple[int, int]]:
    normalized = sorted(
        (max(0, start), min(section_size, end))
        for start, end in ranges
        if end > start and start < section_size
    )
    merged: list[tuple[int, int]] = []
    for start, end in normalized:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
            continue
        merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _int_field(payload: dict[str, object], key: str, default: int) -> int:
    value = payload.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else default
