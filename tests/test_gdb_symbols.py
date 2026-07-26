from __future__ import annotations

import struct

from amiga_reversing.tools import gdb_symbols


class _Artifact:
    _runtime_observation_views = ({"base_addr": 0x10000, "source_start": 0x200, "source_end": 0x400},)

    def analysis_payload(self):
        return ({"sections": [{
            "accepted_code_runs": [
                {"start_offset": 0x220, "end_offset": 0x230},
                {"start_offset": 0x240, "end_offset": 0x250},
            ],
            "symbol_origins": [
                {"origin_kind": "manual_label", "symbol_name": "accepted", "offset": 0x220},
                {"origin_kind": "manual_label", "symbol_name": "not_a_range", "offset": 0x222},
                {"origin_kind": "manual_label", "symbol_name": "ambiguous", "offset": 0x240},
                {"origin_kind": "manual_label", "symbol_name": "ambiguous", "offset": 0x220},
            ],
        }]}, {})


def test_eligible_functions_use_only_canonical_named_accepted_run_starts(monkeypatch) -> None:
    monkeypatch.setattr(gdb_symbols, "_canonical_labels", lambda *_: [
        {"name": "accepted", "source_start": 0x220},
        {"name": "not_a_range", "source_start": 0x222},
        {"name": "ambiguous", "source_start": 0x240},
        {"name": "ambiguous", "source_start": 0x220},
    ])
    view, functions = gdb_symbols._eligible_functions("unused", _Artifact())

    assert view == {"base_addr": 0x10000, "source_start": 0x200, "source_end": 0x400}
    assert [(item.name, item.source_start, item.source_end) for item in functions] == [("accepted", 0x220, 0x230)]


def test_native_elf_is_big_endian_m68k_with_debug_sections() -> None:
    image = gdb_symbols._elf_bytes((gdb_symbols.FunctionSymbol("accepted", 0x220, 0x230),))

    assert image[:7] == b"\x7fELF\x01\x02\x01"
    assert struct.unpack_from(">H", image, 18)[0] == 4
    assert b".debug_info\0" in image
    assert b".debug_abbrev\0" in image
