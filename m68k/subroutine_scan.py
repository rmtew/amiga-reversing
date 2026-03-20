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

from knowledge import runtime_m68k_analysis
from knowledge import runtime_m68k_decode

from .decode_errors import DecodeError
from .instruction_kb import instruction_flow
from .m68k_disasm import _Decoder, _decode_one
from .m68k_executor import BasicBlock


_FLOW_BRANCH = runtime_m68k_analysis.FlowType.BRANCH
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
_FLOW_RETURN = runtime_m68k_analysis.FlowType.RETURN


def _decode_at(code: bytes, pos: int, cache: dict[int, object]):
    if pos in cache:
        cached = cache[pos]
        if isinstance(cached, Exception):
            raise cached
        return cached
    try:
        d = _Decoder(code, 0)
        d.pos = pos
        inst = _decode_one(d, None)
    except (DecodeError, struct.error) as exc:
        cache[pos] = exc
        raise
    cache[pos] = inst
    return inst


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
                           decode_cache: dict[int, object]) -> dict | None:
    """Try to decode a subroutine starting at `start` within [start, end).

    Returns candidate dict or None. Stops at return/unconditional-jump
    or decode failure.
    """
    instrs = 0
    has_flow = False  # contains call or branch
    pos = start

    while pos < end:
        try:
            inst = _decode_at(code, pos, decode_cache)
        except (DecodeError, struct.error):
            return None
        if inst is None:
            return None

        instrs += 1
        next_pos = pos + inst.size
        if next_pos > end:
            return None  # would overlap known code

        ft, conditional = instruction_flow(inst)

        if ft in (_FLOW_CALL, _FLOW_BRANCH):
            has_flow = True

        if ft == _FLOW_RETURN:
            if instrs < 2:
                return None  # too short (bare return)
            return {
                "addr": start,
                "end": next_pos,
                "instr_count": instrs,
                "has_flow": has_flow,
            }

        if ft in (_FLOW_JUMP, _FLOW_BRANCH) and not conditional:
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
    gaps = _uncovered_ranges(blocks, len(code))
    candidates = []

    for gap_start, gap_end in gaps:
        decode_cache: dict[int, object] = {}
        pos = gap_start
        while pos + runtime_m68k_decode.OPWORD_BYTES <= gap_end:
            cand = _try_decode_subroutine(code, pos, gap_end, decode_cache)
            if cand:
                candidates.append(cand)
                # Candidate end is always word-aligned (return instruction end)
                pos = cand["end"]
            else:
                pos += runtime_m68k_decode.OPWORD_BYTES

    return candidates


def score_candidates(candidates: list[dict],
                     blocks: dict[int, BasicBlock],
                     reloc_targets: set[int],
                     call_targets: set[int],
                     code: bytes) -> list[dict]:
    """Score and filter candidates. Adds 'score' field.

    Returns only candidates with score >= 1.0, sorted by score descending.
    """
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
        if addr >= runtime_m68k_decode.OPWORD_BYTES:
            try:
                d = _Decoder(code, 0)
                d.pos = addr - runtime_m68k_decode.OPWORD_BYTES
                prev_inst = _decode_one(d, None)
                if prev_inst and prev_inst.size == runtime_m68k_decode.OPWORD_BYTES:
                    ft, _ = instruction_flow(prev_inst)
                    if ft == _FLOW_RETURN:
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
