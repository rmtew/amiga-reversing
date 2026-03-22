from __future__ import annotations

from dataclasses import dataclass

from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble


@dataclass(frozen=True, slots=True)
class AssemblerCoverageGap:
    gap_id: str
    sample: str
    reason: str


@dataclass(frozen=True, slots=True)
class _AssemblerProbe:
    gap_id: str
    sample: str
    expected_len: int | None = None
    expected_text_prefix: str | None = None


_PROBES: tuple[_AssemblerProbe, ...] = (
    _AssemblerProbe("pack-dn", "pack d0,d1,#1", expected_text_prefix="pack"),
    _AssemblerProbe("pack-predec", "pack -(a0),-(a1),#1", expected_text_prefix="pack"),
    _AssemblerProbe("unpk-dn", "unpk d0,d1,#1", expected_text_prefix="unpk"),
    _AssemblerProbe("link-w", "link a0,#-4", expected_len=4, expected_text_prefix="link"),
    _AssemblerProbe("link-l", "link.l a0,#-4", expected_len=6, expected_text_prefix="link.l"),
    _AssemblerProbe(
        "full-ext-preindexed",
        "move.l (4,[8,a0,d0.w]),d1",
        expected_text_prefix="move.l",
    ),
    _AssemblerProbe(
        "full-ext-postindexed",
        "move.l ([8,a0,d0.w],4),d1",
        expected_text_prefix="move.l",
    ),
    _AssemblerProbe(
        "full-ext-pc-preindexed",
        "move.l (4,[8,pc,d0.w]),d1",
        expected_text_prefix="move.l",
    ),
    _AssemblerProbe(
        "full-ext-pc-postindexed",
        "move.l ([8,pc,d0.w],4),d1",
        expected_text_prefix="move.l",
    ),
)


def _probe_gap(probe: _AssemblerProbe) -> AssemblerCoverageGap | None:
    try:
        raw = assemble_instruction(probe.sample)
    except Exception as exc:
        return AssemblerCoverageGap(
            gap_id=probe.gap_id,
            sample=probe.sample,
            reason=f"assemble failed: {exc}",
        )
    if probe.expected_len is not None and len(raw) != probe.expected_len:
        return AssemblerCoverageGap(
            gap_id=probe.gap_id,
            sample=probe.sample,
            reason=f"wrong encoding length {len(raw)} != {probe.expected_len}",
        )
    if probe.expected_text_prefix is not None:
        decoded = disassemble(raw, max_cpu="68020")[0].text
        if not decoded.lower().startswith(probe.expected_text_prefix):
            return AssemblerCoverageGap(
                gap_id=probe.gap_id,
                sample=probe.sample,
                reason=f"round-trip text mismatch: {decoded!r}",
            )
    return None


def audit_local_assembler_support() -> tuple[AssemblerCoverageGap, ...]:
    gaps: list[AssemblerCoverageGap] = []
    for probe in _PROBES:
        gap = _probe_gap(probe)
        if gap is not None:
            gaps.append(gap)
    return tuple(gaps)


def find_gap(gaps: tuple[AssemblerCoverageGap, ...], gap_id: str) -> AssemblerCoverageGap | None:
    for gap in gaps:
        if gap.gap_id == gap_id:
            return gap
    return None
