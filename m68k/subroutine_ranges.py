from __future__ import annotations

from typing import Mapping, Sequence


def find_containing_sub(addr: int, sorted_subs: Sequence[Mapping[str, int]]) -> int | None:
    lo, hi = 0, len(sorted_subs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        sub = sorted_subs[mid]
        if addr < sub["addr"]:
            hi = mid - 1
        elif addr >= sub["end"]:
            lo = mid + 1
        else:
            return sub["addr"]
    return None
