from __future__ import annotations

from typing import TypedDict

from disasm.types import ListingRow


def render_rows(rows: list[ListingRow]) -> str:
    return "".join(row.text for row in rows)


class ListingWindow(TypedDict):
    anchor_addr: int | None
    rows: list[ListingRow]
    start: int
    end: int
    has_more_before: bool
    has_more_after: bool
    total_rows: int


def listing_window(rows: list[ListingRow], addr: int | None,
                   before: int = 80, after: int = 160) -> ListingWindow:
    anchor_index = 0
    if addr is not None:
        anchor_index = max(0, len(rows) - 1)
        for idx, row in enumerate(rows):
            if row.addr is not None and row.addr >= addr:
                anchor_index = idx
                break
    start = max(0, anchor_index - before)
    end = min(len(rows), anchor_index + after + 1)
    return {
        "anchor_addr": addr,
        "rows": rows[start:end],
        "start": start,
        "end": end,
        "has_more_before": start > 0,
        "has_more_after": end < len(rows),
        "total_rows": len(rows),
    }
