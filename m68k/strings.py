from __future__ import annotations


def read_string_at(data: bytes, addr: int, max_len: int = 64) -> str | None:
    if addr >= len(data):
        return None
    end = min(addr + max_len, len(data))
    result = []
    for i in range(addr, end):
        b = data[i]
        if b == 0:
            break
        if b < 0x20 or b > 0x7E:
            return None
        result.append(b)
    if not result:
        return None
    return bytes(result).decode("ascii")


def read_c_string_span(data: bytes, addr: int, max_len: int | None = None) -> tuple[str, int] | None:
    if addr < 0 or addr >= len(data):
        return None
    end = len(data) if max_len is None else min(addr + max_len, len(data))
    result = []
    for i in range(addr, end):
        b = data[i]
        if b == 0:
            if not result:
                return None
            return bytes(result).decode("ascii"), i + 1
        if b < 0x20 or b > 0x7E:
            return None
        result.append(b)
    return None
