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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m68k_disasm import _Decoder, _decode_one, DecodeError
from m68k_executor import (BasicBlock, _extract_mnemonic, _load_kb,
                            _find_kb_entry)


def _get_flow_type(inst, kb_by_name, cc_defs, cc_aliases) -> str | None:
    """Get KB flow type for a decoded instruction."""
    mn = _extract_mnemonic(inst.text)
    kb = _find_kb_entry(kb_by_name, mn, cc_defs, cc_aliases)
    if kb is None:
        return None
    return kb.get("pc_effects", {}).get("flow", {}).get("type")


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

    # Compute gaps
    gaps = []
    prev_end = 0
    for start, end in merged:
        if start > prev_end:
            # Word-align the gap start
            gap_start = (prev_end + 1) & ~1
            if gap_start < start:
                gaps.append((gap_start, start))
        prev_end = max(prev_end, end)
    if prev_end < code_size:
        gap_start = (prev_end + 1) & ~1
        if gap_start < code_size:
            gaps.append((gap_start, code_size))

    return gaps


def _try_decode_subroutine(code: bytes, start: int, end: int,
                           kb_by_name, cc_defs, cc_aliases,
                           ) -> dict | None:
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

        ft = _get_flow_type(inst, kb_by_name, cc_defs, cc_aliases)

        if ft in ("call", "branch"):
            has_flow = True

        if ft == "return":
            # Valid subroutine end
            if instrs < 2:
                return None  # too short (bare RTS)
            return {
                "addr": start,
                "end": next_pos,
                "instr_count": instrs,
                "has_flow": has_flow,
            }

        if ft == "jump":
            # Unconditional jump — could be tail call
            # Only accept if we had some real content
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
    kb_by_name, _, meta = _load_kb()
    cc_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})
    opword_bytes = meta["opword_bytes"]

    gaps = _uncovered_ranges(blocks, len(code))
    candidates = []

    for gap_start, gap_end in gaps:
        pos = gap_start
        while pos + opword_bytes <= gap_end:
            cand = _try_decode_subroutine(
                code, pos, gap_end, kb_by_name, cc_defs, cc_aliases)
            if cand:
                candidates.append(cand)
                pos = cand["end"]
                # Word-align for next candidate
                pos = (pos + 1) & ~1
            else:
                pos += opword_bytes  # advance one opword

    return candidates


def score_candidates(candidates: list[dict],
                     blocks: dict[int, BasicBlock],
                     reloc_targets: set[int],
                     call_targets: set[int],
                     code: bytes) -> list[dict]:
    """Score and filter candidates. Adds 'score' field.

    Returns only candidates with score >= 1.0, sorted by score descending.
    """
    kb_by_name, _, meta = _load_kb()
    cc_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})
    opword_bytes = meta["opword_bytes"]

    # Build set of all known block start addresses
    known_addrs = set(blocks.keys())

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
        if addr >= opword_bytes:
            try:
                d = _Decoder(code, 0)
                d.pos = addr - opword_bytes
                prev_inst = _decode_one(d, None)
                if prev_inst and prev_inst.size == opword_bytes:
                    ft = _get_flow_type(
                        prev_inst, kb_by_name, cc_defs, cc_aliases)
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
