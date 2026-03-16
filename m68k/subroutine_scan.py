"""Heuristic subroutine discovery in unknown code regions.

Scans gaps between known basic blocks for valid instruction sequences
that look like subroutines (end with a return, contain control flow).
Scores candidates against known references (relocs, call targets).

All flow type detection (return, call, branch) from KB pc_effects.
No hardcoded mnemonic names.

Usage:
    from subroutine_scan import scan_and_score
    candidates = scan_and_score(blocks, code, reloc_targets, call_targets)
"""

import struct

from .m68k_disasm import _Decoder, _decode_one, DecodeError
from .m68k_executor import BasicBlock, _extract_mnemonic
from .kb_util import KB


def _uncovered_ranges(blocks: dict[int, BasicBlock],
                      code_size: int) -> list[tuple[int, int]]:
    """Compute word-aligned gaps not covered by any block."""
    covered = []
    for b in blocks.values():
        covered.append((b.start, b.end))
    covered.sort()

    # Merge overlapping ranges
    merged = []
    for start, end in covered:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Compute gaps. Block ends are always word-aligned (M68K instructions
    # are word-aligned), so gap starts are already even.
    gaps = []
    prev_end = 0
    for start, end in merged:
        if start > prev_end:
            gaps.append((prev_end, start))
        prev_end = max(prev_end, end)
    if prev_end < code_size:
        gaps.append((prev_end, code_size))

    return gaps


def _try_decode_subroutine(code: bytes, start: int, end: int,
                           kb: KB) -> dict | None:
    """Try to decode a subroutine starting at `start` within [start, end).

    Returns candidate dict or None. Stops at return/unconditional-jump
    or decode failure.
    """
    instrs = 0
    has_flow = False  # contains call or branch
    pos = start

    while pos < end:
        try:
            d = _Decoder(code, 0)
            d.pos = pos
            inst = _decode_one(d, None)
        except (DecodeError, struct.error):
            return None
        if inst is None:
            return None

        instrs += 1
        next_pos = pos + inst.size
        if next_pos > end:
            return None  # would overlap known code

        ikb = kb.find(_extract_mnemonic(inst.text))
        if ikb is None:
            return None  # unrecognized instruction
        pc_effects = ikb.get("pc_effects")
        if pc_effects is None:
            ft = None
            conditional = False
        else:
            flow = pc_effects["flow"]
            ft = flow["type"]
            conditional = flow.get("conditional", False)

        if ft in ("call", "branch"):
            has_flow = True

        if ft == "return":
            if instrs < 2:
                return None  # too short (bare return)
            return {
                "addr": start,
                "end": next_pos,
                "instr_count": instrs,
                "has_flow": has_flow,
            }

        if ft in ("jump", "branch") and not conditional:
            # Unconditional jump/branch — could be tail call
            if instrs >= 3 and has_flow:
                return {
                    "addr": start,
                    "end": next_pos,
                    "instr_count": instrs,
                    "has_flow": has_flow,
                }
            return None

        pos = next_pos

    return None  # ran out of gap without finding return


def scan_candidates(blocks: dict[int, BasicBlock],
                    code: bytes) -> list[dict]:
    """Scan unknown regions for subroutine candidates.

    Returns list of candidate dicts with keys:
        addr, end, instr_count, has_flow
    """
    kb = KB()
    gaps = _uncovered_ranges(blocks, len(code))
    candidates = []

    for gap_start, gap_end in gaps:
        pos = gap_start
        while pos + kb.opword_bytes <= gap_end:
            cand = _try_decode_subroutine(code, pos, gap_end, kb)
            if cand:
                candidates.append(cand)
                # Candidate end is always word-aligned (return instruction end)
                pos = cand["end"]
            else:
                pos += kb.opword_bytes

    return candidates


def score_candidates(candidates: list[dict],
                     blocks: dict[int, BasicBlock],
                     reloc_targets: set[int],
                     call_targets: set[int],
                     code: bytes) -> list[dict]:
    """Score and filter candidates. Adds 'score' field.

    Returns only candidates with score >= 1.0, sorted by score descending.
    """
    kb = KB()

    scored = []
    for cand in candidates:
        addr = cand["addr"]
        score = 0.0

        # Reloc target — linker/loader knows this address
        if addr in reloc_targets:
            score += 3.0

        # Referenced by discovered code (call target)
        if addr in call_targets:
            score += 3.0

        # Contains calls or branches (real control flow)
        if cand["has_flow"]:
            score += 1.0

        # Longer sequences are more likely real
        if cand["instr_count"] >= 8:
            score += 0.5
        if cand["instr_count"] >= 16:
            score += 0.5

        # Preceded by a return instruction (end of previous subroutine)
        if addr >= kb.opword_bytes:
            try:
                d = _Decoder(code, 0)
                d.pos = addr - kb.opword_bytes
                prev_inst = _decode_one(d, None)
                if prev_inst and prev_inst.size == kb.opword_bytes:
                    ft, _ = kb.flow_type(prev_inst)
                    if ft == "return":
                        score += 1.0
            except (DecodeError, struct.error):
                pass

        if score >= 1.0:
            cand["score"] = score
            scored.append(cand)

    scored.sort(key=lambda c: (-c["score"], c["addr"]))
    return scored


def scan_and_score(blocks: dict[int, BasicBlock],
                   code: bytes,
                   reloc_targets: set[int],
                   call_targets: set[int]) -> list[dict]:
    """Full pipeline: scan, score, filter. Returns accepted candidates."""
    candidates = scan_candidates(blocks, code)
    return score_candidates(candidates, blocks, reloc_targets,
                            call_targets, code)
