from __future__ import annotations

from amiga_reversing.tools.gdb_symbols import _eligible_functions


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


def test_eligible_functions_use_only_canonical_named_accepted_run_starts() -> None:
    view, functions = _eligible_functions("unused", _Artifact())

    assert view == {"base_addr": 0x10000, "source_start": 0x200, "source_end": 0x400}
    assert [(item.name, item.source_start, item.source_end) for item in functions] == [("accepted", 0x220, 0x230)]
