from __future__ import annotations

PRINTABLE_MIN = 0x20
PRINTABLE_MAX = 0x7E


def is_printable_ascii(value: int) -> bool:
    return PRINTABLE_MIN <= value <= PRINTABLE_MAX
