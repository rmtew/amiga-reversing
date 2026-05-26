from __future__ import annotations

from collections.abc import Mapping

from amiga_reversing.disasm.cascade import (
    CASCADE_SCHEMA,
    CascadeRule,
    CascadeRuleContext,
    blocked_child,
    derived_fact,
    parent_fact,
    render_effect,
    run_cascade,
    validate_cascade_object,
    verifier_delta,
)


def _a5_parent() -> dict[str, object]:
    return parent_fact(
        fact_id="a5-lifetime:a5-def-custom:b0000",
        fact_type="a5_custom_base_lifetime",
        scope={"kind": "straight_line_lifetime", "definition_row_key": "a5-def-custom"},
        provenance={"source": "fixture"},
        payload={
            "safe_uses": [
                {"source_evidence_id": "a5-use-1", "row_key": "a5-use-96", "symbol": "dmacon"},
                {"source_evidence_id": "a5-use-2", "row_key": "a5-use-9a", "symbol": "intena"},
            ],
            "blocked_uses": [{"source_evidence_id": "a5-use-branch", "blockers": ["branch_before_use"]}],
        },
    )


def _address_parent() -> dict[str, object]:
    return parent_fact(
        fact_id="address:runtime:0005C72A",
        fact_type="runtime_address",
        scope={"address_space": "runtime", "value": 0x5C72A},
        provenance={"source": "fixture"},
        payload={"target_offset": 0x12A},
    )


def _derive_a5(ctx: CascadeRuleContext, fact: Mapping[str, object]) -> list[dict[str, object]]:
    payload = fact.get("payload") if isinstance(fact.get("payload"), Mapping) else {}
    results: list[dict[str, object]] = []
    for use in payload.get("safe_uses", []) if isinstance(payload, Mapping) else []:
        if not isinstance(use, Mapping):
            continue
        evidence_id = str(use["source_evidence_id"])
        results.append(
            derived_fact(
                fact_id=f"a5-hardware-ref:{evidence_id}",
                fact_type="a5_hardware_ref",
                parent_fact_ids=[str(fact["fact_id"])],
                rule_id="a5.lifetime.hardware_refs.v1",
                scope={"row_key": use.get("row_key")},
                provenance={"source": "fixture", "source_state_identity": ctx.source_state_identity},
                payload={"symbol": use.get("symbol")},
                render_effect=render_effect(
                    status="pending_verifier",
                    mode="operand_or_entry_comment",
                    baseline_status="not_run",
                    effective_status="not_run",
                ),
            )
        )
    for use in payload.get("blocked_uses", []) if isinstance(payload, Mapping) else []:
        if not isinstance(use, Mapping):
            continue
        evidence_id = str(use["source_evidence_id"])
        results.append(
            blocked_child(
                blocker_id=f"a5-blocked:{evidence_id}",
                child_fact_type="a5_hardware_ref",
                parent_fact_ids=[str(fact["fact_id"])],
                rule_id="a5.lifetime.hardware_refs.v1",
                blockers=[str(item) for item in use.get("blockers", [])],
                scope={"source_evidence_id": evidence_id},
                provenance={"source": "fixture"},
            )
        )
    return results


def _derive_address(_ctx: CascadeRuleContext, fact: Mapping[str, object]) -> list[dict[str, object]]:
    payload = fact.get("payload") if isinstance(fact.get("payload"), Mapping) else {}
    return [
        derived_fact(
            fact_id=f"address-label:{fact['fact_id']}",
            fact_type="address_label",
            parent_fact_ids=[str(fact["fact_id"])],
            rule_id="address.runtime.labels.v1",
            scope={"target_offset": payload.get("target_offset") if isinstance(payload, Mapping) else None},
            provenance={"source": "fixture"},
            verifier_delta=verifier_delta(
                status="verified_delta",
                baseline_state="without_parent",
                effective_state="with_parent",
                changed_rows=[{"row_key": "code-row"}],
                exact_round_trip="passed",
                bounded_effect="passed",
                negative_safety="passed",
                fixed_point="passed",
            ),
        )
    ]


def test_cascade_schema_objects_validate() -> None:
    parent = _a5_parent()
    child = _derive_a5(CascadeRuleContext(CASCADE_SCHEMA, "fixture-state"), parent)[0]

    assert validate_cascade_object(parent) == []
    assert validate_cascade_object(child) == []


def test_cascade_engine_runs_deterministic_fixed_point_for_two_domains() -> None:
    rules = [
        CascadeRule("address.runtime.labels.v1", ("runtime_address",), _derive_address),
        CascadeRule("a5.lifetime.hardware_refs.v1", ("a5_custom_base_lifetime",), _derive_a5),
    ]

    first = run_cascade([_address_parent(), _a5_parent()], rules, source_state_identity="fixture-state")
    second = run_cascade([_a5_parent(), _address_parent()], rules, source_state_identity="fixture-state")

    assert first == second
    assert first["fixed_point"]["status"] == "reached"
    assert first["fixed_point"]["stop_reason"] == "fixed_point_no_new_facts"
    assert [fact["fact_type"] for fact in first["derived_facts"]] == [
        "a5_hardware_ref",
        "a5_hardware_ref",
        "address_label",
    ]
    assert first["derived_facts"][0]["parent_fact_ids"] == ["a5-lifetime:a5-def-custom:b0000"]
    assert first["derived_facts"][0]["rule_id"] == "a5.lifetime.hardware_refs.v1"
    assert first["blocked_children"][0]["blockers"] == ["branch_before_use"]


def test_cascade_engine_fails_closed_for_stale_or_incomplete_parent() -> None:
    stale = _a5_parent()
    stale["source_state_identity"] = "old-state"
    incomplete = _address_parent()
    incomplete["scope"] = {}

    state = run_cascade(
        [stale, incomplete],
        [CascadeRule("a5.lifetime.hardware_refs.v1", ("a5_custom_base_lifetime",), _derive_a5)],
        source_state_identity="fixture-state",
    )

    assert state["derived_facts"] == []
    blockers = {item["blocker_id"]: item["blockers"] for item in state["blocked_children"]}
    assert blockers["blocked-parent:a5-lifetime:a5-def-custom:b0000"] == ["source_state_identity_mismatch"]
    assert "missing_parent_scope" in blockers["blocked-parent:address:runtime:0005C72A"]


def test_cascade_engine_reports_missing_rule_support() -> None:
    state = run_cascade([_address_parent()], [], source_state_identity="fixture-state")

    assert state["fixed_point"]["stop_reason"] == "no_rules"
    assert state["blocked_children"][0]["blockers"] == ["missing_rule_support"]
