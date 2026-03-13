"""Shared KB utilities for M68K analysis tools.

Provides common helpers used across jump_tables, os_calls, name_entities,
subroutine_scan, and build_entities. Single source of truth for KB access
patterns and encoding field extraction.
"""

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m68k_executor import _load_kb, _find_kb_entry, _extract_mnemonic


class KB:
    """Cached KB access with common lookups pre-resolved."""

    def __init__(self):
        self.by_name, _, self.meta = _load_kb()
        self.cc_defs = self.meta["cc_test_definitions"]
        self.cc_aliases = self.meta["cc_aliases"]
        self.opword_bytes = self.meta["opword_bytes"]
        self.ea_enc = self.meta["ea_mode_encoding"]

    def find(self, mnemonic: str) -> dict | None:
        """Look up KB entry for a mnemonic (handles CC families)."""
        return _find_kb_entry(self.by_name, mnemonic,
                              self.cc_defs, self.cc_aliases)

    def flow_type(self, inst) -> tuple[str | None, bool]:
        """Get (flow_type, conditional) for a decoded instruction.

        Returns (None, False) if instruction has no flow effect or is
        not in KB.
        """
        mn = _extract_mnemonic(inst.text)
        ikb = self.find(mn)
        if ikb is None:
            return None, False
        flow = ikb.get("pc_effects", {}).get("flow", {})
        return flow.get("type"), flow.get("conditional", False)

    def ea_field_spec(self, inst_kb: dict) -> tuple | None:
        """Extract (mode_field, reg_field) from KB encoding for EA instructions.

        Returns ((hi, lo, width), (hi, lo, width)) for source MODE and
        REGISTER fields, or None.
        """
        encodings = inst_kb.get("encodings", [])
        if not encodings:
            return None
        fields = encodings[0].get("fields", [])
        mode_f = reg_f = None
        for f in fields:
            if f["name"] == "MODE":
                mode_f = (f["bit_hi"], f["bit_lo"],
                          f["bit_hi"] - f["bit_lo"] + 1)
            elif f["name"] == "REGISTER" and f["bit_hi"] <= 5:
                reg_f = (f["bit_hi"], f["bit_lo"],
                         f["bit_hi"] - f["bit_lo"] + 1)
        if mode_f and reg_f:
            return mode_f, reg_f
        return None

    def dst_reg_field(self, inst_kb: dict) -> tuple | None:
        """Extract destination REGISTER field (higher bits) for MOVEA etc.

        For instructions with two REGISTER fields, returns the one at
        higher bit positions.
        """
        encodings = inst_kb.get("encodings", [])
        if not encodings:
            return None
        fields = encodings[0].get("fields", [])
        reg_fields = [f for f in fields if f["name"] == "REGISTER"]
        if len(reg_fields) < 2:
            return None
        reg_fields.sort(key=lambda f: f["bit_lo"], reverse=True)
        dst = reg_fields[0]
        return (dst["bit_hi"], dst["bit_lo"],
                dst["bit_hi"] - dst["bit_lo"] + 1)


def xf(opcode: int, field: tuple) -> int:
    """Extract a bit field from an opcode. field = (bit_hi, bit_lo, width)."""
    return (opcode >> field[1]) & ((1 << field[2]) - 1)


def find_containing_sub(addr: int, sorted_subs: list[dict]) -> int | None:
    """Binary search for the subroutine containing addr.

    sorted_subs: list of dicts with int "addr" and "end" keys, sorted by addr.
    Returns the subroutine's start address, or None.
    """
    lo, hi = 0, len(sorted_subs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        s = sorted_subs[mid]
        if addr < s["addr"]:
            hi = mid - 1
        elif addr >= s["end"]:
            lo = mid + 1
        else:
            return s["addr"]
    return None
