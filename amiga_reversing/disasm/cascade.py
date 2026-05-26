from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

CASCADE_SCHEMA = "analysis-cascade/v1"
CURRENT_PARENT_STATUS = "accepted"
CURRENT_SOURCE_STATUS = "current"

CascadeObject = dict[str, object]
CascadeDeriver = Callable[["CascadeRuleContext", Mapping[str, object]], Iterable[Mapping[str, object]]]


@dataclass(frozen=True)
class CascadeRule:
    rule_id: str
    input_fact_types: tuple[str, ...]
    derive: CascadeDeriver


@dataclass(frozen=True)
class CascadeRuleContext:
    schema: str
    source_state_identity: str


def stable_json_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def parent_fact(
    *,
    fact_id: str,
    fact_type: str,
    scope: Mapping[str, object],
    provenance: Mapping[str, object],
    payload: Mapping[str, object] | None = None,
    status: str = CURRENT_PARENT_STATUS,
    source_state_status: str = CURRENT_SOURCE_STATUS,
    source_state_identity: str | None = None,
    conflicts: Sequence[Mapping[str, object]] = (),
    invalidated_by: Sequence[Mapping[str, object]] = (),
) -> CascadeObject:
    fact: CascadeObject = {
        "schema": CASCADE_SCHEMA,
        "object_kind": "parent_fact",
        "fact_id": fact_id,
        "fact_type": fact_type,
        "status": status,
        "source_state_status": source_state_status,
        "scope": dict(scope),
        "provenance": dict(provenance),
        "conflicts": [dict(item) for item in conflicts],
        "invalidated_by": [dict(item) for item in invalidated_by],
    }
    if source_state_identity is not None:
        fact["source_state_identity"] = source_state_identity
    if payload is not None:
        fact["payload"] = dict(payload)
    return fact


def derived_fact(
    *,
    fact_id: str,
    fact_type: str,
    parent_fact_ids: Sequence[str],
    rule_id: str,
    scope: Mapping[str, object],
    provenance: Mapping[str, object],
    payload: Mapping[str, object] | None = None,
    render_effect: Mapping[str, object] | None = None,
    verifier_delta: Mapping[str, object] | None = None,
    conflicts: Sequence[Mapping[str, object]] = (),
    status: str = "derived",
) -> CascadeObject:
    fact: CascadeObject = {
        "schema": CASCADE_SCHEMA,
        "object_kind": "derived_fact",
        "fact_id": fact_id,
        "fact_type": fact_type,
        "status": status,
        "parent_fact_ids": list(parent_fact_ids),
        "rule_id": rule_id,
        "scope": dict(scope),
        "provenance": dict(provenance),
        "conflicts": [dict(item) for item in conflicts],
    }
    if payload is not None:
        fact["payload"] = dict(payload)
    if render_effect is not None:
        fact["render_effect"] = dict(render_effect)
    if verifier_delta is not None:
        fact["verifier_delta"] = dict(verifier_delta)
    return fact


def blocked_child(
    *,
    blocker_id: str,
    child_fact_type: str,
    parent_fact_ids: Sequence[str],
    rule_id: str,
    blockers: Sequence[str],
    scope: Mapping[str, object],
    provenance: Mapping[str, object],
    payload: Mapping[str, object] | None = None,
    conflicts: Sequence[Mapping[str, object]] = (),
) -> CascadeObject:
    child: CascadeObject = {
        "schema": CASCADE_SCHEMA,
        "object_kind": "blocked_child",
        "blocker_id": blocker_id,
        "child_fact_type": child_fact_type,
        "parent_fact_ids": list(parent_fact_ids),
        "rule_id": rule_id,
        "blockers": list(blockers),
        "scope": dict(scope),
        "provenance": dict(provenance),
        "conflicts": [dict(item) for item in conflicts],
    }
    if payload is not None:
        child["payload"] = dict(payload)
    return child


def render_effect(
    *,
    status: str,
    mode: str,
    changed_rows: Sequence[Mapping[str, object]] = (),
    blockers: Sequence[str] = (),
    baseline_status: str = "not_run",
    effective_status: str = "not_run",
) -> CascadeObject:
    return {
        "status": status,
        "mode": mode,
        "changed_rows": [dict(row) for row in changed_rows],
        "blockers": list(blockers),
        "baseline_status": baseline_status,
        "effective_status": effective_status,
    }


def verifier_delta(
    *,
    status: str,
    baseline_state: str,
    effective_state: str,
    changed_rows: Sequence[Mapping[str, object]] = (),
    blockers: Sequence[str] = (),
    exact_round_trip: str = "not_required",
    bounded_effect: str = "not_run",
    negative_safety: str = "not_run",
    fixed_point: str = "not_run",
) -> CascadeObject:
    return {
        "status": status,
        "baseline_state": baseline_state,
        "effective_state": effective_state,
        "changed_rows": [dict(row) for row in changed_rows],
        "blockers": list(blockers),
        "exact_round_trip": exact_round_trip,
        "bounded_effect": bounded_effect,
        "negative_safety": negative_safety,
        "fixed_point": fixed_point,
    }


def validate_cascade_object(value: Mapping[str, object]) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    if value.get("schema") != CASCADE_SCHEMA:
        diagnostics.append({"field": "schema", "message": f"expected {CASCADE_SCHEMA}"})
    object_kind = value.get("object_kind")
    if object_kind == "parent_fact":
        _require_string(value, diagnostics, "fact_id")
        _require_string(value, diagnostics, "fact_type")
        _require_mapping(value, diagnostics, "scope")
        _require_mapping(value, diagnostics, "provenance")
        _require_sequence(value, diagnostics, "conflicts")
        _require_sequence(value, diagnostics, "invalidated_by")
    elif object_kind == "derived_fact":
        _require_string(value, diagnostics, "fact_id")
        _require_string(value, diagnostics, "fact_type")
        _require_string(value, diagnostics, "rule_id")
        _require_sequence(value, diagnostics, "parent_fact_ids")
        _require_mapping(value, diagnostics, "scope")
        _require_mapping(value, diagnostics, "provenance")
    elif object_kind == "blocked_child":
        _require_string(value, diagnostics, "blocker_id")
        _require_string(value, diagnostics, "child_fact_type")
        _require_string(value, diagnostics, "rule_id")
        _require_sequence(value, diagnostics, "parent_fact_ids")
        _require_sequence(value, diagnostics, "blockers")
        _require_mapping(value, diagnostics, "scope")
        _require_mapping(value, diagnostics, "provenance")
    else:
        diagnostics.append({"field": "object_kind", "message": "unknown cascade object kind"})
    return diagnostics


def validate_cascade_state(state: Mapping[str, object]) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    if state.get("schema") != CASCADE_SCHEMA:
        diagnostics.append({"field": "schema", "message": f"expected {CASCADE_SCHEMA}"})
    for collection in ("parent_facts", "derived_facts", "blocked_children"):
        values = state.get(collection)
        if not isinstance(values, Sequence) or isinstance(values, str):
            diagnostics.append({"field": collection, "message": "expected sequence"})
            continue
        for index, item in enumerate(values):
            if not isinstance(item, Mapping):
                diagnostics.append({"field": f"{collection}[{index}]", "message": "expected object"})
                continue
            for diagnostic in validate_cascade_object(item):
                diagnostics.append({**diagnostic, "field": f"{collection}[{index}].{diagnostic['field']}"})
    fixed_point = state.get("fixed_point")
    if not isinstance(fixed_point, Mapping):
        diagnostics.append({"field": "fixed_point", "message": "expected object"})
    return diagnostics


def run_cascade(
    parent_facts: Sequence[Mapping[str, object]],
    rules: Sequence[CascadeRule],
    *,
    source_state_identity: str,
    max_iterations: int = 16,
) -> CascadeObject:
    context = CascadeRuleContext(schema=CASCADE_SCHEMA, source_state_identity=source_state_identity)
    rule_map: dict[str, list[CascadeRule]] = {}
    for rule in sorted(rules, key=lambda item: item.rule_id):
        for fact_type in rule.input_fact_types:
            rule_map.setdefault(fact_type, []).append(rule)

    normalized_parents = sorted((dict(fact) for fact in parent_facts), key=lambda item: str(item.get("fact_id") or ""))
    facts: dict[str, CascadeObject] = {}
    blocked: dict[str, CascadeObject] = {}
    executions: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []

    for fact in normalized_parents:
        fact_id = str(fact.get("fact_id") or "")
        fact_type = str(fact.get("fact_type") or "")
        blockers = _parent_fact_blockers(fact, source_state_identity=source_state_identity)
        if blockers:
            skipped.append({"fact_id": fact_id, "fact_type": fact_type, "blockers": blockers})
            blocked[f"blocked-parent:{fact_id or stable_json_hash(fact)[:16]}"] = blocked_child(
                blocker_id=f"blocked-parent:{fact_id or stable_json_hash(fact)[:16]}",
                child_fact_type=f"{fact_type or 'unknown'}.*",
                parent_fact_ids=[fact_id] if fact_id else [],
                rule_id="cascade.parent_validation.v1",
                blockers=blockers,
                scope=dict(fact.get("scope")) if isinstance(fact.get("scope"), Mapping) else {},
                provenance={"source": "cascade_engine", "parent_fact": fact},
            )
            continue
        facts[fact_id] = fact
        if fact_type not in rule_map:
            blocked[f"missing-rule:{fact_id}"] = blocked_child(
                blocker_id=f"missing-rule:{fact_id}",
                child_fact_type=f"{fact_type}.*",
                parent_fact_ids=[fact_id],
                rule_id="cascade.rule_dispatch.v1",
                blockers=["missing_rule_support"],
                scope=dict(fact.get("scope")) if isinstance(fact.get("scope"), Mapping) else {},
                provenance={"source": "cascade_engine", "parent_fact_type": fact_type},
            )

    executed: set[tuple[str, str]] = set()
    stop_reason = "no_rules" if not rules else "fixed_point_no_new_facts"
    iteration = 0
    if rules:
        for iteration in range(1, max_iterations + 1):
            added = 0
            source_facts = sorted(facts.values(), key=lambda item: str(item.get("fact_id") or ""))
            for fact in source_facts:
                fact_id = str(fact.get("fact_id") or "")
                fact_type = str(fact.get("fact_type") or "")
                for rule in rule_map.get(fact_type, []):
                    key = (rule.rule_id, fact_id)
                    if key in executed:
                        continue
                    executed.add(key)
                    derived_count = 0
                    blocked_count = 0
                    for item in rule.derive(context, fact):
                        candidate = dict(item)
                        object_kind = candidate.get("object_kind")
                        if object_kind == "derived_fact":
                            child_id = str(candidate.get("fact_id") or "")
                            if child_id and child_id not in facts:
                                facts[child_id] = candidate
                                added += 1
                                derived_count += 1
                        elif object_kind == "blocked_child":
                            blocker_id = str(candidate.get("blocker_id") or "")
                            if blocker_id and blocker_id not in blocked:
                                blocked[blocker_id] = candidate
                                blocked_count += 1
                    executions.append(
                        {
                            "iteration": iteration,
                            "rule_id": rule.rule_id,
                            "input_fact_id": fact_id,
                            "input_fact_type": fact_type,
                            "derived_count": derived_count,
                            "blocked_count": blocked_count,
                        }
                    )
            if added == 0:
                stop_reason = "fixed_point_no_new_facts"
                break
        else:
            stop_reason = "max_iterations"

    parent_ids = {str(fact.get("fact_id") or "") for fact in normalized_parents}
    derived = [fact for fact_id, fact in facts.items() if fact_id not in parent_ids]
    state: CascadeObject = {
        "schema": CASCADE_SCHEMA,
        "source_state_identity": source_state_identity,
        "parent_facts": normalized_parents,
        "derived_facts": sorted(derived, key=lambda item: str(item.get("fact_id") or "")),
        "blocked_children": sorted(blocked.values(), key=lambda item: str(item.get("blocker_id") or "")),
        "rule_executions": executions,
        "skipped_parent_facts": skipped,
        "fixed_point": {
            "status": "reached" if stop_reason == "fixed_point_no_new_facts" else "blocked",
            "stop_reason": stop_reason,
            "iterations": iteration if rules else 0,
            "max_iterations": max_iterations,
            "executed_rule_inputs": len(executed),
        },
    }
    diagnostics = validate_cascade_state(state)
    state["validation"] = {"valid": not diagnostics, "diagnostics": diagnostics}
    return state


def summarize_cascade_state(state: Mapping[str, object]) -> CascadeObject:
    derived = list(_mapping_sequence(state.get("derived_facts")))
    blocked = list(_mapping_sequence(state.get("blocked_children")))
    render_effects = [item.get("render_effect") for item in derived if isinstance(item.get("render_effect"), Mapping)]
    verifier_deltas = [item.get("verifier_delta") for item in derived if isinstance(item.get("verifier_delta"), Mapping)]
    return {
        "parent_fact_count": len(_mapping_sequence(state.get("parent_facts"))),
        "derived_fact_count": len(derived),
        "blocked_child_count": len(blocked),
        "review_packet_count": sum(1 for item in blocked if "review_packet" in _sequence_strings(item.get("blockers"))),
        "render_effect_count": len(render_effects),
        "render_effects_by_status": _count_by_key(render_effects, "status"),
        "verifier_deltas_by_status": _count_by_key(verifier_deltas, "status"),
        "blocked_by_reason": _count_blockers(blocked),
    }


def _parent_fact_blockers(fact: Mapping[str, object], *, source_state_identity: str) -> list[str]:
    blockers: list[str] = []
    if fact.get("schema") != CASCADE_SCHEMA:
        blockers.append("invalid_schema")
    if not isinstance(fact.get("fact_id"), str) or not fact.get("fact_id"):
        blockers.append("missing_fact_id")
    if not isinstance(fact.get("fact_type"), str) or not fact.get("fact_type"):
        blockers.append("missing_fact_type")
    if fact.get("status") != CURRENT_PARENT_STATUS:
        blockers.append("parent_not_accepted")
    if fact.get("source_state_status") != CURRENT_SOURCE_STATUS:
        blockers.append("source_state_not_current")
    fact_source_identity = fact.get("source_state_identity")
    if isinstance(fact_source_identity, str) and fact_source_identity and fact_source_identity != source_state_identity:
        blockers.append("source_state_identity_mismatch")
    if not isinstance(fact.get("scope"), Mapping) or not fact.get("scope"):
        blockers.append("missing_parent_scope")
    conflicts = fact.get("conflicts")
    if isinstance(conflicts, Sequence) and not isinstance(conflicts, str) and len(conflicts) > 0:
        blockers.append("parent_conflicts_not_empty")
    invalidated_by = fact.get("invalidated_by")
    if isinstance(invalidated_by, Sequence) and not isinstance(invalidated_by, str) and len(invalidated_by) > 0:
        blockers.append("parent_invalidated")
    return blockers


def _require_string(value: Mapping[str, object], diagnostics: list[dict[str, object]], field: str) -> None:
    if not isinstance(value.get(field), str) or not value.get(field):
        diagnostics.append({"field": field, "message": "expected non-empty string"})


def _require_mapping(value: Mapping[str, object], diagnostics: list[dict[str, object]], field: str) -> None:
    if not isinstance(value.get(field), Mapping):
        diagnostics.append({"field": field, "message": "expected object"})


def _require_sequence(value: Mapping[str, object], diagnostics: list[dict[str, object]], field: str) -> None:
    if not isinstance(value.get(field), Sequence) or isinstance(value.get(field), str):
        diagnostics.append({"field": field, "message": "expected sequence"})


def _mapping_sequence(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _sequence_strings(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [item for item in value if isinstance(item, str)]


def _count_by_key(values: Sequence[object], key: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        if not isinstance(value, Mapping):
            continue
        name = str(value.get(key) or "unknown")
        result[name] = result.get(name, 0) + 1
    return result


def _count_blockers(values: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        for blocker in _sequence_strings(value.get("blockers")):
            result[blocker] = result.get(blocker, 0) + 1
    return result
