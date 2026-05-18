from __future__ import annotations

from amiga_reversing.disasm.manual_action_catalog import listing_catalog_manual_payload


def test_runtime_label_rename_uses_generated_absolute_address() -> None:
    row = {
        "kind": "label",
        "label": "abs_0_0001001E",
        "section_index": 0,
        "start_offset": 0x1E,
        "end_offset": 0x1E,
        "runtime_address": 0x2001E,
        "row_index": 245,
        "stable_key": "s0:0000001E:label:245",
    }

    kind, payload = listing_catalog_manual_payload(
        row,
        "label.rename",
        element_context={"element_kind": "label", "symbol": "abs_0_0001001E"},
        parameters={"name": "runtime_loop"},
    )

    assert kind == "create_manual_label"
    assert payload["label"]["address_domain"] == "runtime"
    assert payload["label"]["addr"] == 0x1001E
    assert payload["label"]["label_id"] == "catalog-label-runtime-h0-0001001E-sk-s0_0000001E_label_245"


def test_suppress_seeded_item_command_uses_row_seed_identity() -> None:
    row = {
        "kind": "data",
        "section_index": 0,
        "start_offset": 0x100,
        "row_index": 12,
        "stable_key": "s0:00000100:data:12",
        "suppressible_seeded_items": [
            {"kind": "seeded_entity", "hunk": 0, "addr": 0x100, "source_id": "generated:table"}
        ],
    }

    kind, payload = listing_catalog_manual_payload(
        row,
        "correction.suppress_seeded_item.seeded_entity",
    )

    assert kind == "suppress_seeded_item"
    assert payload == {
        "suppressed_seeded_item": {"kind": "seeded_entity", "hunk": 0, "addr": 0x100}
    }
