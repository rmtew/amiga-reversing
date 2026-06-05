from __future__ import annotations


class SourceNumberError(ValueError):
    pass


def parse_source_int(text: str) -> int:
    value = text.strip()
    if not value:
        raise SourceNumberError("empty integer")

    sign = 1
    if value[0] == "+":
        value = value[1:]
    elif value[0] == "-":
        sign = -1
        value = value[1:]
    if not value:
        raise SourceNumberError("empty integer")

    if len(value) == 3 and value[0] == "'" and value[2] == "'":
        return sign * ord(value[1])

    if value.startswith("$"):
        digits = value[1:]
        base = 16
    elif value.lower().startswith("0x"):
        digits = value[2:]
        base = 16
    elif value.startswith("%"):
        digits = value[1:]
        base = 2
    else:
        digits = value
        base = 10

    if not digits:
        raise SourceNumberError("empty integer")
    try:
        return sign * int(digits, base)
    except ValueError as exc:
        raise SourceNumberError(f"invalid integer: {text}") from exc
