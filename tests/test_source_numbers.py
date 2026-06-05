from __future__ import annotations

import pytest

from amiga_reversing.disasm.source_numbers import SourceNumberError, parse_source_int


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("$400", 0x400),
        ("0x400", 0x400),
        ("1024", 1024),
        ("%10000000000", 0x400),
        ("'A'", 65),
        ("-$10", -16),
        ("+%10", 2),
        ("010", 10),
    ],
)
def test_parse_source_int_accepts_source_numeric_spellings(text: str, expected: int) -> None:
    assert parse_source_int(text) == expected


@pytest.mark.parametrize("text", ["", "$", "0x", "%", "123x", "'AB'"])
def test_parse_source_int_rejects_invalid_source_numeric_spellings(text: str) -> None:
    with pytest.raises(SourceNumberError):
        parse_source_int(text)
