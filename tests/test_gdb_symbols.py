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
    monkeypatch.setattr(gdb_symbols, "canonical_function_facts", lambda *_: {"functions": [
        {"name": "accepted", "entry_offset": 0x220, "status": "accepted", "ranges": [{"start_offset": 0x220, "end_offset": 0x230}]},
        {"name": "not_a_range", "entry_offset": 0x222, "status": "rejected", "reason": "entry_not_accepted_block"},
        {"name": "ambiguous", "entry_offset": 0x240, "status": "rejected", "reason": "overlapping_cfg_ownership"},
    ]})
    view, functions = gdb_symbols._eligible_functions("unused", _Artifact())

    assert view == {"base_addr": 0x10000, "source_start": 0x200, "source_end": 0x400}
    assert [(item.name, item.source_start, item.source_end) for item in functions] == [("accepted", 0x220, 0x230)]


def test_native_elf_is_big_endian_m68k_with_debug_sections() -> None:
    image = gdb_symbols._elf_bytes((gdb_symbols.FunctionSymbol("accepted", 0x220, 0x230),))

    assert image[:7] == b"\x7fELF\x01\x02\x01"
    assert struct.unpack_from(">H", image, 18)[0] == 4
    assert b".debug_info\0" in image
    assert b".debug_abbrev\0" in image


def test_coverage_report_lists_only_symbol_decisions(monkeypatch) -> None:
    artifact = _Artifact()
    artifact.close = lambda: None
    monkeypatch.setattr(gdb_symbols, "build_project_listing_artifact_profile", lambda _: (0, {}, artifact))
    monkeypatch.setattr(gdb_symbols, "canonical_function_facts", lambda *_: {"functions": [
        {
            "name": "accepted",
            "entry_offset": 0x220,
            "status": "accepted",
            "ranges": [{"start_offset": 0x220, "end_offset": 0x230}],
        },
        {"name": "ambiguous", "entry_offset": 0x240, "status": "rejected", "reason": "overlapping_cfg_ownership"},
    ]})

    report = gdb_symbols.symbol_coverage_report("unused")

    assert report["counts"] == {"emitted": 1, "omitted": 1}
    assert report["emitted"] == [{"name": "accepted", "source_start": 0x220, "source_end": 0x230, "range_count": 1}]
    assert report["omitted"] == [{"name": "ambiguous", "entry_offset": 0x240, "reason": "overlapping_cfg_ownership"}]


def test_eligible_functions_reject_noncontiguous_ranges() -> None:
    functions, omitted = gdb_symbols._gdb_eligible_facts([
        {
            "name": "split_function",
            "entry_offset": 0x220,
            "status": "accepted",
            "ranges": [
                {"start_offset": 0x220, "end_offset": 0x230},
                {"start_offset": 0x240, "end_offset": 0x250},
            ],
        },
    ])

    assert functions == []
    assert omitted == [{"name": "split_function", "entry_offset": 0x220, "reason": "noncontiguous_function_ranges"}]
