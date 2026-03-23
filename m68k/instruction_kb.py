"""Shared M68K instruction KB lookup helpers."""

from __future__ import annotations

from typing import Protocol

from m68k_kb import runtime_m68k_analysis


class InstructionKbLike(Protocol):
    @property
    def offset(self) -> int: ...

    @property
    def kb_mnemonic(self) -> str | None: ...


def find_kb_entry(mnemonic: str) -> str | None:
    """Find canonical KB mnemonic from generated lookup tables."""
    if mnemonic in runtime_m68k_analysis.FLOW_TYPES:
        return mnemonic
    mn_upper = mnemonic.upper()
    kb_name = runtime_m68k_analysis.LOOKUP_CANONICAL.get(mn_upper)
    if kb_name is not None:
        return kb_name
    for prefix_upper, family_mnemonic in runtime_m68k_analysis.LOOKUP_NUMERIC_CC_PREFIXES.items():
        if mn_upper.startswith(prefix_upper) and mn_upper[len(prefix_upper):].startswith("#"):
            return family_mnemonic
    return None


def instruction_kb(inst: InstructionKbLike) -> str:
    if not inst.kb_mnemonic:
        raise KeyError(f"Instruction at ${inst.offset:06x} is missing kb_mnemonic")
    mnemonic = find_kb_entry(inst.kb_mnemonic)
    if mnemonic is None:
        raise KeyError(
            f"KB missing instruction entry for {inst.kb_mnemonic!r} at ${inst.offset:06x}"
        )
    return mnemonic


def instruction_flow(inst: InstructionKbLike) -> tuple[runtime_m68k_analysis.FlowType, bool]:
    mnemonic = instruction_kb(inst)
    return (
        runtime_m68k_analysis.FLOW_TYPES[mnemonic],
        runtime_m68k_analysis.FLOW_CONDITIONAL[mnemonic],
    )
