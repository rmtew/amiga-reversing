from __future__ import annotations


def find_containing_sub(addr: int, sorted_subs: list[dict]) -> int | None:
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
