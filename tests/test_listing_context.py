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
