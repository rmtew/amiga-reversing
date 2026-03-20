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
        result.append(b)
    if not result:
        return None
    try:
        return bytes(result).decode("ascii")
    except UnicodeDecodeError:
        return None
