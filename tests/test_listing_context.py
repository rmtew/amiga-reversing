from __future__ import annotations

from amiga_reversing.disasm.listing_context import (
    listing_element_contexts,
    selected_listing_element_context,
)


def test_listing_element_id_uses_normalized_row_key() -> None:
    row = {
        "row_key": "s0:00000552:instruction:338",
        "kind": "instruction",
        "section_index": 0,
        "start_offset": 0x552,
        "end_offset": 0x55A,
        "addr": 0x552,
        "operand_parts": [
            {
                "kind": "displacement",
                "operand_index": 1,
                "base_register": "A6",
                "displacement": 0x1D8,
            }
        ],
        "operand_accesses": ["memory_read", "memory_write"],
    }

    context = listing_element_contexts(row)[0]

    assert context["element_id"] == "s0:00000552:instruction:338:displacement:1:operand"
    assert selected_listing_element_context(row, {"element_id": context["element_id"]}) == context


def test_app_cursor_context_keeps_logical_and_operand_coordinates_separate():
    row = dict(row_key='s0:00000006:instruction', kind='instruction', section_index=0,
               start_offset=6, end_offset=10, addr=6, app_slot_refs=[dict(
                   symbol='previous_view_points', displacement=0xC3E, base_register='A4',
                   operand_index=0, access='address', derived=True, base_displacement=0xBC6,
                   operand_displacement=0x78, data_access_size=0, base_evidence='a6_fallback')])
    context, = [c for c in listing_element_contexts(row) if c['element_kind'] == 'app_slot']
    assert context['displacement'] == 0xC3E
    assert context['base_displacement'] == 0xBC6
    assert context['operand_displacement'] == 0x78
    assert context['data_access_size'] == 0
    assert context['base_evidence'] == 'a6_fallback'
    assert context['derived'] is True


def test_derived_app_target_cannot_be_bound_as_layout_origin_operand():
    from amiga_reversing.disasm import manual_action_catalog as catalog
    context = dict(element_kind="app_slot", symbol="cache", displacement=0xC3E,
        base_register="A4", operand_index=0, access="address", derived=True,
        base_displacement=0xBC6, operand_displacement=0x78, base_evidence="a6_fallback")
    assert catalog._rsset_use_site_binding_parameters(context, require_evidence=False) is None
    assert catalog._rsset_use_site_binding_parameters(context, require_evidence=True) is None
    classification = catalog._provenance_classification(context, {})
    assert classification["status"] == "path_specific"
    assert "a6_fallback" in classification["reason"]
    assert "rsset.binding" not in catalog._provenance_consumers(context)
    assert not any(a["command_id"].startswith("rsset.binding")
        for a in catalog._provenance_possible_actions(context, classification))
