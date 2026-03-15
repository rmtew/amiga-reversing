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
        pc_effects = ikb.get("pc_effects")
        if pc_effects is None:
            return None, False
        flow = pc_effects["flow"]
        return flow["type"], flow.get("conditional", False)

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


def parse_reg_name(name: str) -> tuple[str, int]:
    """Parse a register name like "D0"/"A1" to ("dn", 0)/("an", 1).

    Raises ValueError on unrecognized format.
    """
    name = name.strip().upper()
    if len(name) == 2 and name[1].isdigit():
        if name[0] == "D":
            return ("dn", int(name[1]))
        if name[0] == "A":
            return ("an", int(name[1]))
    raise ValueError(f"Cannot parse register name: {name}")


def read_string_at(data: bytes, addr: int, max_len: int = 64) -> str | None:
    """Read a null-terminated ASCII string from data bytes.

    Returns None if addr is out of range or string is empty/non-ASCII.
    """
    if addr >= len(data):
        return None
    end = min(addr + max_len, len(data))
    result = []
    for i in range(addr, end):
        b = data[i]
        if b == 0:
            break
        result.append(b)
    if not result:
        return None
    try:
        return bytes(result).decode("ascii")
    except UnicodeDecodeError:
        return None


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
