from __future__ import annotations
"""Load cached or fresh hunk analysis for disassembly sessions."""

from pathlib import Path

from m68k.analysis import HunkAnalysis, analyze_hunk
from m68k.os_calls import load_os_kb


def load_hunk_analysis(*, binary_path: str | Path, code: bytes, relocs,
                       hunk_index: int, base_addr: int, code_start: int):
    cache_path = Path(binary_path).with_suffix(".analysis")
    if cache_path.exists():
        return HunkAnalysis.load(cache_path, load_os_kb())
    return analyze_hunk(code, relocs, hunk_index,
                        base_addr=base_addr,
                        code_start=code_start)
