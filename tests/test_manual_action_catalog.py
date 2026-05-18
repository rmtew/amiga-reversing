from __future__ import annotations

from amiga_reversing.disasm.manual_action_catalog import (
    listing_catalog_manual_payload,
    listing_element_action_catalog,
    target_catalog_manual_payload,
)


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


def test_target_execution_view_command_payload() -> None:
    kind, payload = target_catalog_manual_payload(
        "target.execution_view.add",
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
