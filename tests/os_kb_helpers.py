from types import SimpleNamespace

from m68k_kb import runtime_os


def make_empty_os_kb():
    return SimpleNamespace(
        META=runtime_os.META,
        STRUCTS={},
        CONSTANTS={},
        LIBRARIES={},
    )
