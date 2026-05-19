from __future__ import annotations

import pytest

from amiga_reversing.disasm.manual_action_catalog import (
    _provenance_source_evidence_id,
    listing_catalog_manual_payload,
    listing_element_action_catalog,
    listing_range_catalog_manual_payload,
    listing_row_action_catalog,
    target_catalog_manual_payload,
)


def test_target_equate_catalog_payloads() -> None:
    kind, payload = target_catalog_manual_payload(
        "target.equate.add",
        {"name": "PLAYER_START_LIVES", "value": 3},
    )

    assert kind == "create_manual_target_equate"
    assert payload == {
        "target_equate": {
            "target_equate_id": "catalog-target-equate-PLAYER_START_LIVES",
            "name": "PLAYER_START_LIVES",
            "value": 3,
        }
    }

    kind, payload = target_catalog_manual_payload(
        "target.equate.rename",
        {"previous_name": "PLAYER_START_LIVES", "name": "PLAYER_INITIAL_LIVES"},
    )

    assert kind == "rename_manual_target_equate"
    assert payload == {
        "target_equate": {
            "target_equate_id": "catalog-target-equate-PLAYER_START_LIVES",
            "previous_name": "PLAYER_START_LIVES",
            "name": "PLAYER_INITIAL_LIVES",
        }
    }

    kind, payload = target_catalog_manual_payload(
        "target.equate.represent",
        {
            "name": "PLAYER_START_LIVES",
            "value": 3,
            "value_representation": "binary",
        },
    )

    assert kind == "create_manual_target_equate"
    assert payload == {
        "target_equate": {
            "target_equate_id": "catalog-target-equate-PLAYER_START_LIVES",
            "name": "PLAYER_START_LIVES",
            "value": 3,
            "value_representation": "binary",
        }
    }


def test_provenance_source_evidence_id_includes_all_parent_evidence_ids() -> None:
    subject = {
        "target": "demo",
        "hunk": 0,
        "addr": 0x120,
        "operand_index": 0,
        "register": "A6",
        "displacement": 0x102,
    }
    base_classification = {
        "source_family": "rsset_app_base",
        "status": "path_specific",
        "origin_kind": "explicit_base_evidence",
        "path_lifetime_scope": {"kind": "selected_use"},
    }

    first = _provenance_source_evidence_id(
        {},
        subject,
        {**base_classification, "parent_evidence_ids": ["seed:A6", "path:left"]},
    )
    second = _provenance_source_evidence_id(
        {},
        subject,
        {**base_classification, "parent_evidence_ids": ["seed:A6", "path:right"]},
    )

    assert "seed_A6__path_left" in first
    assert "seed_A6__path_right" in second
    assert first != second


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


def test_data_symbol_rename_command_uses_seeded_entity_identity() -> None:
    row = {
        "kind": "data",
        "section_index": 0,
        "start_offset": 0x100,
        "end_offset": 0x104,
        "suppressible_seeded_items": [
            {
                "kind": "seeded_entity",
                "hunk": 0,
                "addr": 0x100,
                "end": 0x104,
                "name": "auto_data",
                "source_locator": "GeneratedData",
            }
        ],
    }

    kind, payload = listing_catalog_manual_payload(
        row,
        "data_symbol.rename",
        parameters={"name": "player_table"},
    )

    assert kind == "rename_data_symbol"
    assert payload == {
        "data_symbol": {
            "data_symbol_id": "data-symbol:h0:00000100",
            "hunk": 0,
            "addr": 0x100,
            "end": 0x104,
            "previous_name": "auto_data",
            "source_locator": "GeneratedData",
            "name": "player_table",
        }
    }

    kind, payload = listing_catalog_manual_payload(
        row,
        "data_symbol.rename_existing",
        parameters={"name": "player_table"},
    )

    assert kind == "rename_data_symbol"
    assert payload == {
        "data_symbol": {
            "data_symbol_id": "data-symbol:h0:00000100",
            "hunk": 0,
            "addr": 0x100,
            "end": 0x104,
            "previous_name": "auto_data",
            "source_locator": "GeneratedData",
            "name": "player_table",
        }
    }


def test_data_symbol_remove_command_suppresses_seeded_entity_identity() -> None:
    row = {
        "kind": "data",
        "section_index": 0,
        "start_offset": 0x100,
        "end_offset": 0x104,
        "suppressible_seeded_items": [
            {
                "kind": "seeded_entity",
                "hunk": 0,
                "addr": 0x100,
                "end": 0x104,
                "name": "auto_data",
                "source_locator": "GeneratedData",
            }
        ],
    }

    kind, payload = listing_catalog_manual_payload(row, "data_symbol.remove")

    assert kind == "suppress_seeded_item"
    assert payload == {
        "suppressed_seeded_item": {"kind": "seeded_entity", "hunk": 0, "addr": 0x100}
    }


def test_data_symbol_remove_command_removes_manual_seed_identity() -> None:
    row = {
        "kind": "data",
        "section_index": 0,
        "start_offset": 0x100,
        "end_offset": 0x104,
        "suppressible_seeded_items": [
            {
                "kind": "seeded_entity",
                "hunk": 0,
                "addr": 0x100,
                "end": 0x104,
                "name": "player_table",
                "source_locator": "ManualSeed:data-symbol:h0:00000100",
            }
        ],
    }

    actions = listing_row_action_catalog(row)
    remove_action = next(action for action in actions if action["action_id"] == "data_symbol.remove")
    kind, payload = listing_catalog_manual_payload(row, "data_symbol.remove")

    assert remove_action["action"] == "remove_manual_seed"
    assert remove_action["parameters"] == {"seed_id": "data-symbol:h0:00000100"}
    assert kind == "remove_manual_seed"
    assert payload == {"seed_id": "data-symbol:h0:00000100"}


def test_data_symbol_rename_command_uses_data_row_identity_without_seeded_entity() -> None:
    row = {
        "kind": "data",
        "section_index": 1,
        "start_offset": 0x120,
        "end_offset": 0x128,
        "label": "loc_1_00000120",
    }

    kind, payload = listing_catalog_manual_payload(
        row,
        "data_symbol.rename",
        parameters={"name": "player_table"},
    )

    assert kind == "rename_data_symbol"
    assert payload == {
        "data_symbol": {
            "data_symbol_id": "data-symbol:h1:00000120",
            "hunk": 1,
            "addr": 0x120,
            "end": 0x128,
            "previous_name": "loc_1_00000120",
            "name": "player_table",
        }
    }

    kind, payload = listing_catalog_manual_payload(
        row,
        "data_symbol.rename_existing",
        parameters={"name": "player_table"},
    )

    assert kind == "rename_data_symbol"
    assert payload["data_symbol"]["previous_name"] == "loc_1_00000120"


def test_data_block_element_commands_infer_active_layout_identity() -> None:
    row = {
        "kind": "data",
        "section_index": 0,
        "start_offset": 0x1430,
        "end_offset": 0x143A,
        "active_data_block_layout": {
            "layout_id": "ascii-hex",
            "hunk": 0,
            "source_start": 0x1400,
            "source_end": 0x1480,
        },
    }

    actions = listing_row_action_catalog(row)
    set_action = next(action for action in actions if action["action_id"] == "row.data_block.element.set")
    represent_action = next(action for action in actions if action["action_id"] == "row.data_block.element.represent")
    kind, payload = listing_catalog_manual_payload(
        row,
        "row.data_block.element.set",
        parameters={"kind": "array", "name": "digits", "array_count": 10, "array_stride": 1},
    )
    represent_kind, represent_payload = listing_catalog_manual_payload(
        row,
        "row.data_block.element.represent",
        parameters={"representation": "hex"},
    )

    assert set_action["parameters"] == {"layout_id": "ascii-hex", "offset": 0x30, "width": 10}
    assert set_action["parameter_schema"]["required"] == []
    assert represent_action["parameters"] == {"layout_id": "ascii-hex", "offset": 0x30}
    assert represent_action["parameter_schema"]["required"] == ["representation"]
    assert kind == "set_manual_data_block_element"
    assert payload == {
        "data_block_element": {
            "data_block_element_id": "ascii-hex:30",
            "layout_id": "ascii-hex",
            "offset": 0x30,
            "width": 10,
            "kind": "array",
            "name": "digits",
            "array_count": 10,
            "array_stride": 1,
        }
    }
    assert represent_kind == "represent_manual_data_block_element"
    assert represent_payload == {
        "data_block_element": {"layout_id": "ascii-hex", "offset": 0x30, "representation": "hex"}
    }


def test_data_block_type_binding_commands_preserve_element_identity() -> None:
    row = {
        "kind": "data",
        "section_index": 0,
        "start_offset": 0x1430,
        "end_offset": 0x1434,
        "active_data_block_layout": {
            "layout_id": "events",
            "hunk": 0,
            "source_start": 0x1400,
            "source_end": 0x1480,
        },
        "active_data_block_element": {
            "data_block_element_id": "events:30",
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            "kind": "scalar",
            "name": "event_ptr",
            "representation": "hex",
            "type_binding": {
                "type_binding_id": "events:30:4:custom_struct:InputEvent",
                "layout_id": "events",
                "element_offset": 0x30,
                "element_width": 4,
                "binding_kind": "custom_struct",
                "bound_type_id": "InputEvent",
            },
        },
    }

    actions = listing_row_action_catalog(row)
    bind_action = next(action for action in actions if action["action_id"] == "row.data_block.element.bind_type")
    clear_action = next(action for action in actions if action["action_id"] == "row.data_block.element.clear_type")
    bind_schema_properties = bind_action["parameter_schema"]["properties"]
    bind_kind, bind_payload = listing_catalog_manual_payload(
        row,
        "row.data_block.element.bind_type",
        parameters={
            "binding_kind": "platform_struct",
            "type_id": "Node",
            "source_evidence_id": "prov-node-table",
            "source_family": "data_block_pointer",
            "source_evidence_status": "analysis_proven",
            "parent_evidence_ids": ["prov-table-base"],
        },
    )
    clear_kind, clear_payload = listing_catalog_manual_payload(row, "row.data_block.element.clear_type")

    assert bind_action["parameters"]["kind"] == "scalar"
    assert {
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
    }.issubset(bind_schema_properties)
    assert clear_action["parameter_schema"]["required"] == []
    assert bind_kind == "set_manual_data_block_element"
    assert bind_payload == {
        "data_block_element": {
            "data_block_element_id": "events:30",
            "layout_id": "events",
            "offset": 0x30,
            "width": 4,
            "kind": "platform_struct",
            "name": "event_ptr",
            "representation": "hex",
            "type_binding": {
                "type_binding_id": "events:30:4:platform_struct:Node",
                "layout_id": "events",
                "element_offset": 0x30,
                "element_width": 4,
                "binding_kind": "platform_struct",
                "bound_type_id": "Node",
                "source_evidence_id": "prov-node-table",
                "source_family": "data_block_pointer",
                "source_evidence_status": "analysis_proven",
                "parent_evidence_ids": ["prov-table-base"],
            },
        }
    }
    assert clear_kind == "set_manual_data_block_element"
    assert clear_payload["data_block_element"]["kind"] == "scalar"
    assert clear_payload["data_block_element"]["previous_type_binding"]["bound_type_id"] == "InputEvent"
    assert "type_binding" not in clear_payload["data_block_element"]


def test_data_block_interpreted_ref_commands_build_durable_payloads() -> None:
    row = {
        "kind": "data",
        "section_index": 0,
        "start_offset": 0x1430,
        "end_offset": 0x1432,
        "bytes": "2000",
        "active_data_block_layout": {
            "layout_id": "ptr-table",
            "hunk": 0,
            "source_start": 0x1400,
            "source_end": 0x1480,
        },
        "active_data_block_interpreted_ref": {
            "data_block_ref_id": "ptr-table:30:absolute:h0:00002000",
            "layout_id": "ptr-table",
            "offset": 0x30,
            "reference_kind": "absolute",
            "target_hunk": 0,
            "target_offset": 0x2000,
        },
    }

    actions = listing_row_action_catalog(row)
    interpret_action = next(action for action in actions if action["action_id"] == "row.data_block.element.interpret_ref")
    clear_action = next(action for action in actions if action["action_id"] == "row.data_block.element.clear_ref")
    interpret_kind, interpret_payload = listing_catalog_manual_payload(
        row,
        "row.data_block.element.interpret_ref",
        parameters={"target_hunk": 0, "target_offset": 0x2000},
    )
    clear_kind, clear_payload = listing_catalog_manual_payload(row, "row.data_block.element.clear_ref")

    assert interpret_action["parameters"] == {
        "layout_id": "ptr-table",
        "offset": 0x30,
        "width": 2,
        "reference_kind": "absolute",
        "confidence": "manual",
        "xref_generation_mode": "bidirectional",
    }
    assert interpret_action["parameter_schema"]["required"] == ["reference_kind", "target_hunk", "target_offset"]
    assert clear_action["parameters"] == {
        "layout_id": "ptr-table",
        "offset": 0x30,
        "data_block_ref_id": "ptr-table:30:absolute:h0:00002000",
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x2000,
    }
    assert clear_action["parameters"]["data_block_ref_id"] == "ptr-table:30:absolute:h0:00002000"
    assert clear_action["parameter_schema"]["required"] == []
    assert interpret_kind == "interpret_manual_data_block_element_ref"
    assert interpret_payload == {
        "data_block_interpreted_ref": {
            "data_block_ref_id": "ptr-table:30:absolute:h0:00002000",
            "layout_id": "ptr-table",
            "offset": 0x30,
            "width": 2,
            "reference_kind": "absolute",
            "target_hunk": 0,
            "target_offset": 0x2000,
            "target_locator": {"hunk": 0, "offset": 0x2000},
            "source_value": 0x2000,
            "confidence": "manual",
            "xref_generation_mode": "bidirectional",
        }
    }
    assert clear_kind == "remove_manual_data_block_element_ref"
    assert clear_payload == {
        "data_block_interpreted_ref": {
            "data_block_ref_id": "ptr-table:30:absolute:h0:00002000",
            "layout_id": "ptr-table",
            "offset": 0x30,
            "reference_kind": "absolute",
            "target_hunk": 0,
            "target_offset": 0x2000,
        }
    }


def test_data_block_interpreted_ref_payload_rejects_target_not_matching_source_bytes() -> None:
    row = {
        "kind": "data",
        "section_index": 0,
        "start_offset": 0x1430,
        "end_offset": 0x1432,
        "bytes": "2000",
        "active_data_block_layout": {
            "layout_id": "ptr-table",
            "hunk": 0,
            "source_start": 0x1400,
            "source_end": 0x1480,
        },
    }

    with pytest.raises(ValueError, match="target_offset must match selected source bytes"):
        listing_catalog_manual_payload(
            row,
            "row.data_block.element.interpret_ref",
            parameters={"target_hunk": 0, "target_offset": 0x2001},
        )


def test_range_data_block_element_represent_uses_applicable_subranges() -> None:
    layout = {"layout_id": "ascii-hex", "hunk": 0, "source_start": 0x1400, "source_end": 0x1500}
    rows = [
        {
            "kind": "data",
            "row_index": 1,
            "section_index": 0,
            "start_offset": 0x1430,
            "end_offset": 0x1431,
            "active_data_block_layout": layout,
        },
        {"kind": "instruction", "row_index": 2, "section_index": 0, "start_offset": 0x1432, "end_offset": 0x1434},
        {
            "kind": "data",
            "row_index": 3,
            "section_index": 0,
            "start_offset": 0x1440,
            "end_offset": 0x1441,
            "active_data_block_layout": layout,
        },
    ]

    payloads = listing_range_catalog_manual_payload(
        rows,
        "range.data_block.element.represent",
        parameters={"representation": "hex"},
    )

    assert payloads == [
        (
            "represent_manual_data_block_element",
            {"data_block_element": {"layout_id": "ascii-hex", "offset": 0x30, "representation": "hex"}},
        ),
        (
            "represent_manual_data_block_element",
            {"data_block_element": {"layout_id": "ascii-hex", "offset": 0x40, "representation": "hex"}},
        ),
    ]


def test_data_ref_symbol_rename_command_uses_referenced_data_identity() -> None:
    row = {
        "kind": "instruction",
        "section_index": 0,
        "start_offset": 0x20,
        "end_offset": 0x24,
        "stable_key": "code-row",
        "runtime_address_refs": [
            {
                "offset": 0x20,
                "operand_index": 0,
                "target_section_index": 1,
                "target_offset": 0x120,
                "runtime_address": 0x40120,
                "confidence": 2,
                "data_class": "bitmap",
                "size": 0x20,
                "symbol": "old_bitmap",
            }
        ],
    }
    selector = {"element_kind": "data_ref", "operand_index": 0}

    actions = listing_element_action_catalog(row, selector)
    rename_action = next(action for action in actions if action["action_id"] == "data_symbol.rename")
    rename_existing_action = next(action for action in actions if action["action_id"] == "data_symbol.rename_existing")
    kind, payload = listing_catalog_manual_payload(
        row,
        "data_symbol.rename",
        element_context=selector,
        parameters={"name": "player_bitmap"},
    )

    assert rename_action["parameters"] == {
        "source": "data_ref",
        "hunk": 1,
        "addr": 0x120,
        "end": 0x140,
        "data_class": "bitmap",
        "previous_name": "old_bitmap",
    }
    assert rename_existing_action["action"] == "rename_existing_data_symbol"
    assert rename_existing_action["parameters"] == rename_action["parameters"]
    assert kind == "rename_data_symbol"
    assert payload == {
        "data_symbol": {
            "data_symbol_id": "data-symbol:h1:00000120",
            "hunk": 1,
            "addr": 0x120,
            "end": 0x140,
            "data_class": "bitmap",
            "previous_name": "old_bitmap",
            "name": "player_bitmap",
        }
    }


def test_app_slot_rename_command_uses_selected_slot_displacement() -> None:
    row = {
        "kind": "instruction",
        "section_index": 0,
        "start_offset": 0x20,
        "end_offset": 0x24,
        "stable_key": "app-write",
        "app_slot_refs": [
            {
                "symbol": "app_0234",
                "displacement": 0x234,
                "base_register": "A6",
                "operand_index": 1,
                "access": "write",
            }
        ],
    }
    selector = {"element_kind": "app_slot", "symbol": "app_0234", "operand_index": 1, "access": "write"}

    actions = listing_element_action_catalog(row, selector)
    rename_action = next(action for action in actions if action["action_id"] == "app_slot.rename")
    edit_action = next(action for action in actions if action["action_id"] == "app_slot.edit")
    kind, payload = listing_catalog_manual_payload(
        row,
        "app_slot.rename",
        element_context=selector,
        parameters={"symbol": "app_player_state", "size": 4, "storage_kind": "pointer"},
    )
    edit_kind, edit_payload = listing_catalog_manual_payload(
        row,
        "app_slot.edit",
        element_context=selector,
        parameters={"symbol": "app_player_state", "size": 4, "storage_kind": "pointer"},
    )

    assert rename_action["parameters"] == {"offset": 0x234, "previous_symbol": "app_0234"}
    assert rename_action["parameter_schema"]["required"] == ["symbol", "size"]
    assert edit_action["parameters"] == {"offset": 0x234, "previous_symbol": "app_0234"}
    assert edit_action["parameter_schema"]["required"] == ["symbol", "size"]
    assert kind == "create_manual_rsset_layout_region"
    assert payload == {
        "rsset_layout_region": {
            "rsset_layout_region_id": "catalog-rsset-region-app-0234",
            "offset": 0x234,
            "size": 4,
            "symbol": "app_player_state",
            "storage_kind": "pointer",
        }
    }
    assert edit_kind == kind
    assert edit_payload == payload


def test_app_slot_remove_command_uses_selected_slot_identity() -> None:
    row = {
        "kind": "instruction",
        "section_index": 0,
        "start_offset": 0x20,
        "end_offset": 0x24,
        "stable_key": "app-write",
        "app_slot_refs": [
            {
                "symbol": "app_0234",
                "displacement": 0x234,
                "base_register": "A6",
                "operand_index": 1,
                "access": "write",
            }
        ],
    }
    selector = {"element_kind": "app_slot", "symbol": "app_0234", "operand_index": 1, "access": "write"}

    actions = listing_element_action_catalog(row, selector)
    remove_action = next(action for action in actions if action["action_id"] == "app_slot.remove")
    kind, payload = listing_catalog_manual_payload(
        row,
        "app_slot.remove",
        element_context=selector,
    )

    assert remove_action["parameters"] == {"offset": 0x234, "previous_symbol": "app_0234"}
    assert kind == "remove_manual_rsset_layout_region"
    assert payload == {"rsset_layout_region": {"offset": 0x234}}


def test_target_execution_view_add_and_edit_command_payloads() -> None:
    for command_id in ("target.execution_view.add", "target.execution_view.edit"):
        kind, payload = target_catalog_manual_payload(
            command_id,
            {
                "source_start": 0x20,
                "source_end": 0x80,
                "base_addr": 0x4000,
                "name": "stage_code",
            },
        )

        assert kind == "create_manual_execution_view"
        assert payload == {
            "execution_view": {
                "execution_view_id": "catalog-execution-view-00000020-00000080-00004000",
                "source_start": 0x20,
                "source_end": 0x80,
                "base_addr": 0x4000,
                "name": "stage_code",
            }
        }


def test_target_execution_view_remove_command_payload() -> None:
    kind, payload = target_catalog_manual_payload(
        "target.execution_view.remove",
        {
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
        },
    )

    assert kind == "remove_manual_execution_view"
    assert payload == {
        "execution_view": {
            "source_start": 0x20,
            "source_end": 0x80,
            "base_addr": 0x4000,
        }
    }


def test_target_custom_struct_add_and_edit_command_payloads() -> None:
    for command_id in ("target.custom_struct.add", "target.custom_struct.edit"):
        kind, payload = target_catalog_manual_payload(
            command_id,
            {
                "name": "InputEvent",
                "size": 22,
                "fields": [
                    {
                        "name": "ie_Class",
                        "type": "UBYTE",
                        "offset": 4,
                        "size": 1,
                        "available_since": "1.0",
                    }
                ],
            },
        )

        assert kind == "create_manual_custom_struct"
        assert payload == {
            "custom_struct": {
                "name": "InputEvent",
                "size": 22,
                "fields": [
                    {
                        "name": "ie_Class",
                        "type": "UBYTE",
                        "offset": 4,
                        "size": 1,
                        "available_since": "1.0",
                    }
                ],
            }
        }


def test_target_custom_struct_remove_command_payload() -> None:
    kind, payload = target_catalog_manual_payload(
        "target.custom_struct.remove",
        {"name": "InputEvent"},
    )

    assert kind == "remove_manual_custom_struct"
    assert payload == {"custom_struct": {"name": "InputEvent"}}


def test_target_custom_struct_rename_command_payload() -> None:
    kind, payload = target_catalog_manual_payload(
        "target.custom_struct.rename",
        {"previous_name": "InputEvent", "name": "GameInput"},
    )

    assert kind == "rename_manual_custom_struct"
    assert payload == {"custom_struct": {"previous_name": "InputEvent", "name": "GameInput"}}


def test_target_custom_struct_field_add_and_edit_command_payloads() -> None:
    for command_id in ("target.custom_struct_field.add", "target.custom_struct_field.edit"):
        kind, payload = target_catalog_manual_payload(
            command_id,
            {
                "struct_name": "InputEvent",
                "name": "ie_Class",
                "type": "UBYTE",
                "offset": 4,
                "size": 1,
            },
        )

        assert kind == "create_manual_custom_struct_field"
        assert payload == {
            "custom_struct_field": {
                "struct_name": "InputEvent",
                "name": "ie_Class",
                "type": "UBYTE",
                "offset": 4,
                "size": 1,
            }
        }


def test_target_custom_struct_field_remove_command_payload() -> None:
    kind, payload = target_catalog_manual_payload(
        "target.custom_struct_field.remove",
        {"struct_name": "InputEvent", "offset": 4, "name": "ie_Class"},
    )

    assert kind == "remove_manual_custom_struct_field"
    assert payload == {"custom_struct_field": {"struct_name": "InputEvent", "offset": 4, "name": "ie_Class"}}


def test_target_custom_struct_field_rename_command_payload() -> None:
    kind, payload = target_catalog_manual_payload(
        "target.custom_struct_field.rename",
        {"struct_name": "InputEvent", "offset": 4, "name": "ie_Code"},
    )

    assert kind == "rename_manual_custom_struct_field"
    assert payload == {"custom_struct_field": {"struct_name": "InputEvent", "offset": 4, "name": "ie_Code"}}


def test_typed_gap_field_add_command_uses_gap_identity() -> None:
    row = {
        "kind": "instruction",
        "section_index": 0,
        "start_offset": 0x34,
        "stable_key": "gap-row",
        "unresolved_typed_accesses": [
            {
                "operand_index": 1,
                "base_register": "A0",
                "displacement": 36,
                "root_struct_name": "InputEvent",
                "refined_struct_name": "DerivedEvent",
                "classification": "prefix_extension",
            }
        ],
    }
    selector = {"element_kind": "typed_gap", "operand_index": 1}

    actions = listing_element_action_catalog(row, selector)
    add_action = next(action for action in actions if action["action_id"] == "typed_gap.field.add")
    kind, payload = listing_catalog_manual_payload(
        row,
        "typed_gap.field.add",
        element_context=selector,
        parameters={"name": "de_Code", "type": "UWORD", "size": 2},
    )

    assert add_action["parameters"]["struct_name"] == "DerivedEvent"
    assert add_action["parameters"]["offset"] == 36
    assert add_action["parameters"]["source_family"] == "struct_pointer"
    assert add_action["parameters"]["source_evidence_status"] == "analysis_proven"
    assert add_action["parameter_schema"]["required"] == ["name", "type", "size"]
    assert kind == "create_manual_custom_struct_field"
    assert payload == {
        "custom_struct_field": {
            "struct_name": "DerivedEvent",
            "name": "de_Code",
            "type": "UWORD",
            "offset": 36,
            "size": 2,
            "source_evidence_id": add_action["parameters"]["source_evidence_id"],
            "source_family": "struct_pointer",
            "source_evidence_status": "analysis_proven",
            "path_lifetime_scope": add_action["parameters"]["path_lifetime_scope"],
            "confidence": "high",
            "conflicts": [],
            "parent_evidence_ids": [],
        }
    }


def test_typed_access_field_commands_use_resolved_identity() -> None:
    row = {
        "kind": "instruction",
        "section_index": 0,
        "start_offset": 0x30,
        "stable_key": "typed-row",
        "typed_accesses": [
            {
                "operand_index": 1,
                "base_register": "A0",
                "displacement": 20,
                "field_offset": 20,
                "root_struct_name": "Library",
                "owner_struct_name": "Library",
                "field_name": "LIB_VERSION",
                "field_expr": "LIB_VERSION",
            }
        ],
    }
    selector = {"element_kind": "typed_access", "operand_index": 1}

    actions = listing_element_action_catalog(row, selector)
    rename_action = next(action for action in actions if action["action_id"] == "typed_access.field.rename")
    rename_schema_properties = rename_action["parameter_schema"]["properties"]
    rename_kind, rename_payload = listing_catalog_manual_payload(
        row,
        "typed_access.field.rename",
        element_context=selector,
        parameters={"name": "LIB_REVISION"},
    )
    remove_kind, remove_payload = listing_catalog_manual_payload(
        row,
        "typed_access.field.remove",
        element_context=selector,
    )

    assert {
        "struct_name": rename_action["parameters"]["struct_name"],
        "offset": rename_action["parameters"]["offset"],
        "name": rename_action["parameters"]["name"],
        "source_family": rename_action["parameters"]["source_family"],
        "source_evidence_status": rename_action["parameters"]["source_evidence_status"],
    } == {
        "struct_name": "Library",
        "offset": 20,
        "name": "LIB_VERSION",
        "source_family": "struct_pointer",
        "source_evidence_status": "analysis_proven",
    }
    assert {
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
    }.issubset(rename_schema_properties)
    assert rename_kind == "rename_manual_custom_struct_field"
    assert rename_payload == {
        "custom_struct_field": {
            "struct_name": "Library",
            "offset": 20,
            "name": "LIB_REVISION",
            "source_evidence_id": rename_action["parameters"]["source_evidence_id"],
            "source_family": "struct_pointer",
            "source_evidence_status": "analysis_proven",
            "path_lifetime_scope": rename_action["parameters"]["path_lifetime_scope"],
            "confidence": "high",
            "conflicts": [],
            "parent_evidence_ids": [],
        }
    }
    assert remove_kind == "remove_manual_custom_struct_field"
    assert remove_payload == {
        "custom_struct_field": {
            "struct_name": "Library",
            "offset": 20,
            "name": "LIB_VERSION",
            "source_evidence_id": rename_action["parameters"]["source_evidence_id"],
            "source_family": "struct_pointer",
            "source_evidence_status": "analysis_proven",
            "path_lifetime_scope": rename_action["parameters"]["path_lifetime_scope"],
            "confidence": "high",
            "conflicts": [],
            "parent_evidence_ids": [],
        }
    }


def test_target_rsset_layout_region_command_payload() -> None:
    kind, payload = target_catalog_manual_payload(
        "target.rsset_region.add",
        {
            "offset": 4,
            "size": 2,
            "layout_name": "work",
            "base_symbol": "__game_work_base__",
            "sizeof_symbol": "work_SIZEOF",
            "symbol": "work_counter",
            "storage_kind": "scalar",
            "parser_role": "option_source",
            "parser_routine": "parse_options",
            "parse_order": 0,
        },
    )

    assert kind == "create_manual_rsset_layout_region"
    assert payload == {
        "rsset_layout_region": {
            "rsset_layout_region_id": "catalog-rsset-region-work-0004",
            "offset": 4,
            "size": 2,
            "layout_name": "work",
            "base_symbol": "__game_work_base__",
            "sizeof_symbol": "work_SIZEOF",
            "symbol": "work_counter",
            "storage_kind": "scalar",
            "parser_role": "option_source",
            "parser_routine": "parse_options",
            "parse_order": 0,
        }
    }


def test_target_rsset_layout_region_edit_and_rename_command_payloads() -> None:
    for command_id in ("target.rsset_region.edit", "target.rsset_region.rename"):
        kind, payload = target_catalog_manual_payload(
            command_id,
            {
                "offset": 4,
                "size": 2,
                "layout_name": "work",
                "base_symbol": "__game_work_base__",
                "sizeof_symbol": "work_SIZEOF",
                "symbol": "work_counter",
                "storage_kind": "scalar",
                "parser_role": "option_source",
                "parser_routine": "parse_options",
                "parse_order": 0,
            },
        )

        assert kind == "create_manual_rsset_layout_region"
        assert payload == {
            "rsset_layout_region": {
                "rsset_layout_region_id": "catalog-rsset-region-work-0004",
                "offset": 4,
                "size": 2,
                "layout_name": "work",
                "base_symbol": "__game_work_base__",
                "sizeof_symbol": "work_SIZEOF",
                "symbol": "work_counter",
                "storage_kind": "scalar",
                "parser_role": "option_source",
                "parser_routine": "parse_options",
                "parse_order": 0,
            }
        }


def test_target_rsset_layout_region_remove_command_payload() -> None:
    kind, payload = target_catalog_manual_payload(
        "target.rsset_region.remove",
        {
            "offset": 4,
            "layout_name": "work",
            "base_symbol": "__game_work_base__",
        },
    )

    assert kind == "remove_manual_rsset_layout_region"
    assert payload == {
        "rsset_layout_region": {
            "offset": 4,
            "layout_name": "work",
            "base_symbol": "__game_work_base__",
        }
    }
