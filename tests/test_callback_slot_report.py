from __future__ import annotations

from amiga_reversing.disasm.callback_slot_report import callback_slot_report


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
