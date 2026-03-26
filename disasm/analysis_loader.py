from __future__ import annotations

"""Load cached or fresh hunk analysis for disassembly sessions."""

import hashlib
from collections.abc import Sequence
from pathlib import Path

from m68k.analysis import AnalysisCacheError, HunkAnalysis, RelocLike, analyze_hunk
from m68k.m68k_executor import CPUState
from m68k_kb import runtime_os


def hunk_analysis_cache_path(cache_path: str | Path, hunk_index: int) -> Path:
    path = Path(cache_path)
    return path.with_name(f"{path.name}.hunk-{hunk_index}")


def analysis_cache_is_current(cache_path: str | Path) -> bool:
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return False
    try:
        HunkAnalysis.load(cache_path, runtime_os)
    except AnalysisCacheError:
        return False
    return True


def analysis_cache_root(
    cache_path: str | Path,
    *,
    seed_key: str,
    base_addr: int,
    code_start: int,
    entry_points: Sequence[int],
) -> Path:
    cache_root = Path(cache_path)
    layout_payload = (
        f"base={base_addr:X};code_start={code_start:X};"
        f"entry_points={','.join(f'{entry:X}' for entry in entry_points)}"
    )
    layout_key = hashlib.sha1(layout_payload.encode("utf-8")).hexdigest()[:12]
    cache_root = cache_root.with_name(f"{cache_root.name}.{layout_key}")
    if seed_key != "default":
        cache_root = cache_root.with_name(f"{cache_root.name}.{seed_key}")
    return cache_root


def load_hunk_analysis(
    *,
    analysis_cache_path: str | Path,
    code: bytes,
    relocs: Sequence[RelocLike],
    hunk_index: int,
    base_addr: int,
    code_start: int,
    entry_points: Sequence[int] = (),
    seed_key: str = "default",
    initial_state: CPUState | None = None,
    entry_initial_states: dict[int, CPUState] | None = None,
) -> HunkAnalysis:
    cache_root = analysis_cache_root(
        analysis_cache_path,
        seed_key=seed_key,
        base_addr=base_addr,
        code_start=code_start,
        entry_points=entry_points,
    )
    cache_path = hunk_analysis_cache_path(cache_root, hunk_index)
    if cache_path.exists():
        try:
            return HunkAnalysis.load(cache_path, runtime_os)
        except AnalysisCacheError:
            pass
    if initial_state is None:
        analysis = analyze_hunk(
            code,
            list(relocs),
            hunk_index,
            base_addr=base_addr,
            code_start=code_start,
            entry_points=entry_points,
            entry_initial_states=entry_initial_states,
        )
    else:
        analysis = analyze_hunk(
            code,
            list(relocs),
            hunk_index,
            base_addr=base_addr,
            code_start=code_start,
            entry_points=entry_points,
            initial_state=initial_state,
            entry_initial_states=entry_initial_states,
        )
    analysis.save(cache_path)
    return analysis
