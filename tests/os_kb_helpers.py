from __future__ import annotations

from types import SimpleNamespace

from m68k.os_calls import OsKb
from m68k_kb import runtime_os


def make_empty_os_kb() -> OsKb:
    return SimpleNamespace(
        META=runtime_os.META,
        STRUCTS={},
        CONSTANTS={},
        LIBRARIES={},
    )
