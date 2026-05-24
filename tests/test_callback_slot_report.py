from __future__ import annotations

from amiga_reversing.disasm import decision_journal
from amiga_reversing.disasm.callback_slot_report import (
    analysis_with_accepted_callback_code,
    analysis_with_callback_orphan_code_signals,
    callback_decision_lane,
    callback_decision_record,
    callback_orphan_code_signals,
    callback_render_effect,
    callback_slot_report,
    callback_verifier_gate,
)
from amiga_reversing.disasm.manual_review_items import analysis_review_items


def test_callback_slot_report_links_stored_symbol_to_indirect_consumer() -> None:
    rows = [
        {
            "kind": "label",
            "label": "abs_0_00010AA2",
            "start_offset": 0x0AA2,
            "row_key": "s0:00000AA2:label:1",
        },
        {
            "kind": "data",
            "start_offset": 0x0AA2,
            "end_offset": 0x0AB8,
            "row_key": "s0:00000AA2:data:2",
            "opcode_or_directive": "dc.b",
            "text": "\tdc.b $4E,$75\n",
        },
        {
            "kind": "instruction",
            "start_offset": 0x1000,
            "end_offset": 0x1004,
            "row_key": "s0:00001000:instruction:3",
            "opcode_or_directive": "lea.l",
            "operand_registers": [None, "A0"],
            "operand_parts": [
                {
                    "kind": "symbol",
                    "metadata": {"symbol": "abs_0_00010AA2"},
                    "operand_index": 0,
                }
            ],
            "operand_text": "abs_0_00010AA2(pc),a0",
            "text": "\tlea.l abs_0_00010AA2(pc),a0\n",
        },
        {
            "kind": "instruction",
            "start_offset": 0x1004,
            "end_offset": 0x1008,
            "row_key": "s0:00001004:instruction:4",
            "opcode_or_directive": "move.l",
            "operand_registers": ["A0", None],
            "operand_text": "a0,app_0360(a6)",
            "app_slot_refs": [
                {
                    "access": "write",
                    "base_register": "A6",
                    "displacement": 0x0360,
                    "symbol": "app_0360",
                }
            ],
            "text": "\tmove.l a0,app_0360(a6)\n",
        },
        {
            "kind": "instruction",
            "start_offset": 0x2000,
            "end_offset": 0x2004,
            "row_key": "s0:00002000:instruction:5",
            "opcode_or_directive": "movea.l",
            "operand_registers": [None, "A0"],
            "operand_text": "app_0360(a6),a0",
            "app_slot_refs": [
                {
                    "access": "read",
                    "base_register": "A6",
                    "displacement": 0x0360,
                    "symbol": "app_0360",
                }
            ],
            "text": "\tmovea.l app_0360(a6),a0\n",
        },
        {
            "kind": "instruction",
            "start_offset": 0x2004,
            "end_offset": 0x2006,
            "row_key": "s0:00002004:instruction:6",
            "opcode_or_directive": "jsr",
            "operand_text": "(a0)",
            "text": "\tjsr (a0)\n",
        },
    ]
    review_items = [
        {
            "kind": "orphan_code_candidate",
            "item_id": "orphan_code_candidate:h0:$00000aa2-$00000ab8",
            "start": 0x0AA2,
            "end": 0x0AB8,
            "evidence_fingerprint": "abc",
            "review_confidence": "medium",
            "reason": "callback",
        }
    ]

    report = callback_slot_report(rows, review_items, slot_symbol="app_0360")

    assert report["summary"]["consumer_count"] == 1
    assert report["summary"]["assignment_count"] == 1
    assert report["summary"]["concrete_missed_code_target_count"] == 1
    slot = report["slots"][0]
    assert slot["slot_symbol"] == "app_0360"
    assignment = slot["assignments"][0]
    assert assignment["stored_symbol"] == "abs_0_00010AA2"
    assert assignment["stored_source_offset"] == 0x0AA2
    assert assignment["target_kind"] == "data"
    assert assignment["review_item"]["item_id"] == "orphan_code_candidate:h0:$00000aa2-$00000ab8"
    assert assignment["action_readiness"]["status"] == "ready_for_review_seed_code"
    assert slot["consumers"][0]["indirect_transfer"]["opcode_or_directive"] == "jsr"


def test_callback_slot_report_blocks_without_review_item_identity() -> None:
    rows = [
        {"kind": "label", "label": "abs_0_00010E14", "start_offset": 0x0E14},
        {"kind": "data", "start_offset": 0x0E14, "end_offset": 0x0E20, "row_key": "data"},
        {
            "kind": "instruction",
            "start_offset": 0x1000,
            "opcode_or_directive": "lea.l",
            "operand_registers": [None, "A0"],
            "operand_parts": [{"kind": "symbol", "metadata": {"symbol": "abs_0_00010E14"}}],
        },
        {
            "kind": "instruction",
            "start_offset": 0x1004,
            "opcode_or_directive": "move.l",
            "operand_registers": ["A0", None],
            "app_slot_refs": [{"access": "write", "symbol": "app_0360", "displacement": 0x0360}],
        },
    ]

    report = callback_slot_report(rows, slot_symbol="app_0360")

    assignment = report["slots"][0]["assignments"][0]
    assert assignment["target_kind"] == "data"
    assert assignment["review_item"] is None
    assert assignment["action_readiness"] == {
        "status": "blocked",
        "blockers": ["missing_orphan_code_review_item"],
    }


def test_callback_slot_report_ignores_store_after_source_register_clobber() -> None:
    rows = [
        {"kind": "label", "label": "abs_0_00010E14", "start_offset": 0x0E14},
        {"kind": "data", "start_offset": 0x0E14, "end_offset": 0x0E20, "row_key": "data"},
        {
            "kind": "instruction",
            "start_offset": 0x1000,
            "opcode_or_directive": "lea.l",
            "operand_registers": [None, "A0"],
            "operand_parts": [{"kind": "symbol", "metadata": {"symbol": "abs_0_00010E14"}}],
        },
        {
            "kind": "instruction",
            "start_offset": 0x1004,
            "opcode_or_directive": "movea.l",
            "operand_registers": [None, "A0"],
            "operand_parts": [],
        },
        {
            "kind": "instruction",
            "start_offset": 0x1008,
            "opcode_or_directive": "move.l",
            "operand_registers": ["A0", None],
            "app_slot_refs": [{"access": "write", "symbol": "app_0360", "displacement": 0x0360}],
        },
    ]

    report = callback_slot_report(rows, slot_symbol="app_0360")

    assignment = report["slots"][0]["assignments"][0]
    assert assignment["stored_symbol"] is None
    assert assignment["stored_source_offset"] is None
    assert assignment["target"] is None


def test_callback_slot_report_ignores_consumer_after_transfer_register_clobber() -> None:
    rows = [
        {
            "kind": "instruction",
            "start_offset": 0x2000,
            "opcode_or_directive": "movea.l",
            "operand_registers": [None, "A0"],
            "operand_text": "app_0360(a6),a0",
            "app_slot_refs": [{"access": "read", "symbol": "app_0360", "displacement": 0x0360}],
        },
        {
            "kind": "instruction",
            "start_offset": 0x2004,
            "opcode_or_directive": "movea.l",
            "operand_registers": [None, "A0"],
            "operand_text": "(a1),a0",
        },
        {
            "kind": "instruction",
            "start_offset": 0x2008,
            "opcode_or_directive": "jsr",
            "operand_text": "(a0)",
        },
    ]

    report = callback_slot_report(rows, slot_symbol="app_0360")

    assert report["summary"]["consumer_count"] == 0
    assert report["slot_count"] == 0


def test_callback_slot_report_does_not_treat_data_review_item_as_code_seed_ready() -> None:
    rows = [
        {"kind": "label", "label": "abs_0_00010E14", "start_offset": 0x0E14},
        {"kind": "data", "start_offset": 0x0E14, "end_offset": 0x0E20, "row_key": "data"},
        {
            "kind": "instruction",
            "start_offset": 0x1000,
            "opcode_or_directive": "lea.l",
            "operand_registers": [None, "A0"],
            "operand_parts": [{"kind": "symbol", "metadata": {"symbol": "abs_0_00010E14"}}],
        },
        {
            "kind": "instruction",
            "start_offset": 0x1004,
            "opcode_or_directive": "move.l",
            "operand_registers": ["A0", None],
            "app_slot_refs": [{"access": "write", "symbol": "app_0360", "displacement": 0x0360}],
        },
    ]
    review_items = [
        {
            "kind": "unreconciled_data_range",
            "item_id": "unreconciled_data_range:h0:$00000e14-$00000ed8",
            "start": 0x0E14,
            "end": 0x0ED8,
        }
    ]

    report = callback_slot_report(rows, review_items, slot_symbol="app_0360")

    assignment = report["slots"][0]["assignments"][0]
    assert assignment["review_item"]["kind"] == "unreconciled_data_range"
    assert assignment["action_readiness"] == {
        "status": "blocked",
        "blockers": ["review_item_is_not_code_classification"],
        "review_item_kind": "unreconciled_data_range",
    }


def test_callback_slot_report_emits_structured_evidence_packet_for_assignment() -> None:
    report = callback_slot_report(_eligible_callback_rows(), slot_symbol="app_0360")

    assignment = report["slots"][0]["assignments"][0]
    packet = assignment["evidence_packet"]

    assert packet["packet_kind"] == "callback_derived_code_evidence_packet"
    assert packet["selected_identity"] == {
        "segment_id": "s0",
        "hunk": 0,
        "addr": 0x0AA2,
        "operand_index": 0,
        "selected_use_id": "s0:00000AA2:op0",
    }
    assert packet["callback_slot"]["slot_symbol"] == "app_0360"
    assert packet["callback_store"]["stored_symbol"] == "abs_0_00010AA2"
    assert packet["target"]["bytes"] == [0x70, 0x01, 0x4E, 0x75]
    assert packet["conflicts"]["explicit_empty"] is True
    assert packet["status"] == "action_ready"


def test_callback_orphan_code_signal_generates_reviewable_candidate_for_eligible_fixture() -> None:
    report = callback_slot_report(_eligible_callback_rows(), slot_symbol="app_0360")
    signals = callback_orphan_code_signals(report)

    assert len(signals) == 1
    signal = signals[0]
    assert signal["reason_name"] == "callback_slot"
    assert signal["missing_inbound"] == "callback"
    assert signal["offset"] == 0x0AA2

    analysis = analysis_with_callback_orphan_code_signals(
        {"sections": [{"section_index": 0, "section_size": 0x0AB0}]},
        signals,
    )
    items = analysis_review_items(analysis)
    item = next(item for item in items if item["kind"] == "orphan_code_candidate")
    assert item["start"] == 0x0AA2
    assert item["orphan_code_score"]["category"] == "evidence_led"


def test_callback_orphan_code_signal_blocks_zero_fill_and_data_like_targets() -> None:
    rows = _eligible_callback_rows()
    rows[1] = {
        "kind": "data",
        "start_offset": 0x0AA2,
        "end_offset": 0x0AA6,
        "row_key": "s0:00000AA2:data:2",
        "opcode_or_directive": "dcb.b",
        "text": "\tdcb.b $04,$00\n",
        "bytes": [0, 0, 0, 0],
    }

    report = callback_slot_report(rows, slot_symbol="app_0360")
    assignment = report["slots"][0]["assignments"][0]

    assert callback_orphan_code_signals(report) == ()
    generated = assignment["generated_orphan_code_signal"]
    assert generated["status"] == "blocked"
    assert "all_zero_data" in generated["blockers"]
    assert "data_like_directive" in generated["blockers"]


def test_callback_decision_record_dry_run_and_replay_projection() -> None:
    packet = _eligible_callback_packet()
    record = callback_decision_record(
        packet,
        "accept_fact",
        target_id="demo",
        decision_id="decision-callback-0aa2",
    )

    assert decision_journal.validate_decision_record(record)["valid"] is True
    projection = decision_journal.project_decision_journal([record])
    lane = callback_decision_lane(packet, projection, target_id="demo")
    assert lane["status"] == "accepted"

    analysis = analysis_with_accepted_callback_code({"sections": [{"section_index": 0}]}, projection)
    accepted = analysis["sections"][0]["accepted_callback_code_ranges"]
    assert accepted == [
        {
            "offset": 0x0AA2,
            "size": 1,
            "source_evidence_id": "decision-callback-0aa2",
            "source_family": "callback_derived_code",
            "status": "accepted",
        }
    ]


def test_callback_defer_record_preserves_reason_without_replay_effect() -> None:
    packet = _eligible_callback_packet()
    record = callback_decision_record(
        packet,
        "defer_fact",
        target_id="demo",
        decision_id="decision-callback-defer",
        reason="needs human validation",
    )
    projection = decision_journal.project_decision_journal([record])

    assert decision_journal.validate_decision_record(record)["valid"] is True
    assert record["defer_reason"] == "needs human validation"
    assert callback_decision_lane(packet, projection, target_id="demo")["status"] == "deferred"
    analysis = analysis_with_accepted_callback_code({"sections": [{"section_index": 0}]}, projection)
    assert analysis["accepted_callback_code_facts"] == []


def test_callback_render_and_verifier_gates_fail_closed_until_all_layers_pass() -> None:
    packet = _eligible_callback_packet()
    record = callback_decision_record(
        packet,
        "accept_fact",
        target_id="demo",
        decision_id="decision-callback-0aa2",
    )
    projection = decision_journal.project_decision_journal([record])

    missing = callback_verifier_gate(packet, projection, target_id="demo", verifier_report=None)
    assert missing["status"] == "blocked"
    assert "missing_exact_round_trip" in missing["blockers"]
    assert callback_render_effect(packet, projection, target_id="demo", verifier_report=None)["status"] == "blocked"

    passed = {
        "semantic_reload": "passed",
        "generated_source": "passed",
        "negative_safety": "passed",
        "exact_round_trip": "passed",
    }
    assert callback_verifier_gate(packet, projection, target_id="demo", verifier_report=passed)["status"] == "passed"
    effect = callback_render_effect(packet, projection, target_id="demo", verifier_report=passed)
    assert effect["effect"] == {
        "kind": "classify_range_as_code",
        "hunk": 0,
        "start": 0x0AA2,
        "end": 0x0AA6,
        "source": "accepted_callback_derived_code",
    }


def _eligible_callback_rows() -> list[dict[str, object]]:
    return [
        {
            "kind": "label",
            "label": "abs_0_00010AA2",
            "start_offset": 0x0AA2,
            "row_key": "s0:00000AA2:label:1",
        },
        {
            "kind": "data",
            "start_offset": 0x0AA2,
            "end_offset": 0x0AA6,
            "row_key": "s0:00000AA2:data:2",
            "opcode_or_directive": "dc.b",
            "text": "\tdc.b $70,$01,$4E,$75\n",
            "bytes": [0x70, 0x01, 0x4E, 0x75],
        },
        {
            "kind": "instruction",
            "start_offset": 0x1000,
            "opcode_or_directive": "lea.l",
            "operand_registers": [None, "A0"],
            "operand_parts": [{"kind": "symbol", "metadata": {"symbol": "abs_0_00010AA2"}}],
        },
        {
            "kind": "instruction",
            "start_offset": 0x1004,
            "row_key": "s0:00001004:instruction:4",
            "opcode_or_directive": "move.l",
            "operand_registers": ["A0", None],
            "app_slot_refs": [{"access": "write", "symbol": "app_0360", "displacement": 0x0360}],
        },
        {
            "kind": "instruction",
            "start_offset": 0x2000,
            "opcode_or_directive": "movea.l",
            "operand_registers": [None, "A0"],
            "app_slot_refs": [{"access": "read", "symbol": "app_0360", "displacement": 0x0360}],
        },
        {
            "kind": "instruction",
            "start_offset": 0x2004,
            "opcode_or_directive": "jsr",
            "operand_text": "(a0)",
        },
    ]


def _eligible_callback_packet() -> dict[str, object]:
    report = callback_slot_report(_eligible_callback_rows(), slot_symbol="app_0360")
    return report["slots"][0]["assignments"][0]["evidence_packet"]
