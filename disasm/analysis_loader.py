from __future__ import annotations
"""Load cached or fresh hunk analysis for disassembly sessions."""

from collections.abc import Sequence
from pathlib import Path

from m68k_kb import runtime_os
from m68k.analysis import AnalysisCacheError, HunkAnalysis, RelocLike, analyze_hunk


def analysis_cache_is_current(binary_path: str | Path) -> bool:
    cache_path = Path(binary_path).with_suffix(".analysis")
    if not cache_path.exists():
        return False
    try:
        HunkAnalysis.load(cache_path, runtime_os)
    except AnalysisCacheError:
        return False
    return True


def load_hunk_analysis(
    *,
    binary_path: str | Path,
    code: bytes,
    relocs: Sequence[RelocLike],
    hunk_index: int,
    base_addr: int,
    code_start: int,
) -> HunkAnalysis:
    cache_path = Path(binary_path).with_suffix(".analysis")
    if cache_path.exists():
        try:
            return HunkAnalysis.load(cache_path, runtime_os)
        except AnalysisCacheError:
            pass
    analysis = analyze_hunk(code, list(relocs), hunk_index,
                            base_addr=base_addr,
                            code_start=code_start)
    analysis.save(cache_path)
    return analysis
