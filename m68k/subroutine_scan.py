"""Heuristic subroutine discovery in unknown code regions.

Scans gaps between known basic blocks for valid instruction sequences
that look like subroutines (end with a return, contain control flow).
Scores candidates against known references (relocs, call targets).

All flow type detection comes from generated KB runtime data.
"""

import struct
from typing import TypedDict

from m68k_kb import runtime_m68k_analysis, runtime_m68k_decode

from .decode_errors import DecodeError
from .instruction_kb import find_kb_entry, instruction_flow
from .m68k_disasm import Instruction, _decode_one, _Decoder
from .m68k_executor import BasicBlock
from .typing_protocols import InstructionLike

_FLOW_BRANCH = runtime_m68k_analysis.FlowType.BRANCH
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
_FLOW_RETURN = runtime_m68k_analysis.FlowType.RETURN


class SubroutineCandidate(TypedDict):
    addr: int
    end: int
    instr_count: int
    has_flow: bool
    score: float


class UnscoredSubroutineCandidate(TypedDict):
    addr: int
    end: int
    instr_count: int
    has_flow: bool


def _flow_for_inst(
    inst: InstructionLike,
    flow_cache: dict[str, tuple[runtime_m68k_analysis.FlowType, bool]],
) -> tuple[runtime_m68k_analysis.FlowType, bool]:
    if not inst.kb_mnemonic:
        raise KeyError(f"Instruction at ${inst.offset:06x} is missing kb_mnemonic")
    cached = flow_cache.get(inst.kb_mnemonic)
    if cached is not None:
        return cached
    mnemonic = find_kb_entry(inst.kb_mnemonic)
    if mnemonic is None:
        raise KeyError(
            f"KB missing instruction entry for {inst.kb_mnemonic!r} at ${inst.offset:06x}"
        )
    result = (
        runtime_m68k_analysis.FLOW_TYPES[mnemonic],
        runtime_m68k_analysis.FLOW_CONDITIONAL[mnemonic],
    )
    flow_cache[inst.kb_mnemonic] = result
    return result


def _decode_at(code: bytes, pos: int, cache: dict[int, Instruction | Exception]) -> Instruction:
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
    covered: list[tuple[int, int]] = []
    for b in blocks.values():
        covered.append((b.start, b.end))
    covered.sort()

    merged: list[tuple[int, int]] = []
    for start, end in covered:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    gaps: list[tuple[int, int]] = []
    prev_end = 0
    for start, end in merged:
        if start > prev_end:
            gaps.append((prev_end, start))
        prev_end = max(prev_end, end)
    if prev_end < code_size:
        gaps.append((prev_end, code_size))

    return gaps


def _try_decode_subroutine(code: bytes, start: int, end: int,
                           decode_cache: dict[int, Instruction | Exception],
                           scan_cache: dict[tuple[int, int], UnscoredSubroutineCandidate | None],
                           flow_cache: dict[str, tuple[runtime_m68k_analysis.FlowType, bool]]
                           ) -> UnscoredSubroutineCandidate | None:
    """Try to decode a subroutine starting at `start` within [start, end)."""
    cache_key = (start, end)
    if cache_key in scan_cache:
        return scan_cache[cache_key]

    instrs = 0
    has_flow = False
    pos = start

    while pos < end:
        try:
            inst = _decode_at(code, pos, decode_cache)
        except (DecodeError, struct.error):
            scan_cache[cache_key] = None
            return None
        if inst is None:
            scan_cache[cache_key] = None
            return None

        instrs += 1
        next_pos = pos + inst.size
        if next_pos > end:
            scan_cache[cache_key] = None
            return None

        ft, conditional = _flow_for_inst(inst, flow_cache)

        # Subroutine entries that immediately transfer control are noise.
        if instrs == 1 and (
            ft in (_FLOW_RETURN, _FLOW_JUMP)
            or (ft == _FLOW_BRANCH and not conditional)
        ):
            scan_cache[cache_key] = None
            return None

        if ft in (_FLOW_CALL, _FLOW_BRANCH):
            has_flow = True

        if ft == _FLOW_RETURN:
            if instrs < 2:
                scan_cache[cache_key] = None
                return None
            candidate: UnscoredSubroutineCandidate = {
                "addr": start,
                "end": next_pos,
                "instr_count": instrs,
                "has_flow": has_flow,
            }
            scan_cache[cache_key] = candidate
            return candidate

        if ft in (_FLOW_JUMP, _FLOW_BRANCH) and not conditional:
            if instrs >= 3 and has_flow:
                candidate = {
                    "addr": start,
                    "end": next_pos,
                    "instr_count": instrs,
                    "has_flow": has_flow,
                }
                scan_cache[cache_key] = candidate
                return candidate
            scan_cache[cache_key] = None
            return None

        pos = next_pos

    scan_cache[cache_key] = None
    return None


def _scan_candidates_with_cache(blocks: dict[int, BasicBlock],
                                code: bytes) -> tuple[list[UnscoredSubroutineCandidate], dict[int, Instruction | Exception]]:
    gaps = _uncovered_ranges(blocks, len(code))
    candidates: list[UnscoredSubroutineCandidate] = []
    decode_cache: dict[int, Instruction | Exception] = {}
    scan_cache: dict[tuple[int, int], UnscoredSubroutineCandidate | None] = {}
    flow_cache: dict[str, tuple[runtime_m68k_analysis.FlowType, bool]] = {}

    for gap_start, gap_end in gaps:
        pos = gap_start
        while pos + runtime_m68k_decode.OPWORD_BYTES <= gap_end:
            cand = _try_decode_subroutine(
                code, pos, gap_end, decode_cache, scan_cache, flow_cache
            )
            if cand:
                candidates.append(cand)
                pos = cand["end"]
            else:
                pos += runtime_m68k_decode.OPWORD_BYTES

    return candidates, decode_cache


def scan_candidates(blocks: dict[int, BasicBlock],
                    code: bytes) -> list[UnscoredSubroutineCandidate]:
    """Scan unknown regions for subroutine candidates."""
    candidates, _ = _scan_candidates_with_cache(blocks, code)
    return candidates


def score_candidates(candidates: list[UnscoredSubroutineCandidate],
                     blocks: dict[int, BasicBlock],
                     reloc_targets: set[int],
                     call_targets: set[int],
                     code: bytes) -> list[SubroutineCandidate]:
    """Score and filter candidates. Adds 'score' field."""
    scored: list[SubroutineCandidate] = []
    for cand in candidates:
        addr = cand["addr"]
        score = 0.0

        if addr in reloc_targets:
            score += 3.0
        if addr in call_targets:
            score += 3.0
        if cand["has_flow"]:
            score += 1.0
        if cand["instr_count"] >= 8:
            score += 0.5
        if cand["instr_count"] >= 16:
            score += 0.5

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
            scored.append({**cand, "score": score})

    scored.sort(key=lambda c: (-c["score"], c["addr"]))
    return scored


def _score_candidates_with_cache(candidates: list[UnscoredSubroutineCandidate],
                                 blocks: dict[int, BasicBlock],
                                 reloc_targets: set[int],
                                 call_targets: set[int],
                                 code: bytes,
                                 decode_cache: dict[int, Instruction | Exception]) -> list[SubroutineCandidate]:
    """Score candidates while reusing the scan decode cache."""
    scored: list[SubroutineCandidate] = []
    for cand in candidates:
        addr = cand["addr"]
        score = 0.0

        if addr in reloc_targets:
            score += 3.0
        if addr in call_targets:
            score += 3.0
        if cand["has_flow"]:
            score += 1.0
        if cand["instr_count"] >= 8:
            score += 0.5
        if cand["instr_count"] >= 16:
            score += 0.5

        if addr >= runtime_m68k_decode.OPWORD_BYTES:
            try:
                prev_inst = _decode_at(
                    code, addr - runtime_m68k_decode.OPWORD_BYTES, decode_cache
                )
                if prev_inst and prev_inst.size == runtime_m68k_decode.OPWORD_BYTES:
                    ft, _ = instruction_flow(prev_inst)
                    if ft == _FLOW_RETURN:
                        score += 1.0
            except (DecodeError, struct.error):
                pass

        if score >= 1.0:
            scored.append({**cand, "score": score})

    scored.sort(key=lambda c: (-c["score"], c["addr"]))
    return scored


def scan_and_score(blocks: dict[int, BasicBlock],
                   code: bytes,
                   reloc_targets: set[int],
                   call_targets: set[int]) -> list[SubroutineCandidate]:
    """Full pipeline: scan, score, filter. Returns accepted candidates."""
    candidates, decode_cache = _scan_candidates_with_cache(blocks, code)
    return _score_candidates_with_cache(
        candidates, blocks, reloc_targets, call_targets, code, decode_cache
    )
