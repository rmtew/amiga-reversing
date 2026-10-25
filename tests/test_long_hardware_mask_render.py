from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import (
    RawBinarySource, BinarySourceKind, RawAddressModel,
)
from amiga_reversing.disasm.c_backend import (
    render_project_source_with_c_backend,
    assemble_platform_source_text_with_c_backend,
)


def test_composite_cia_mask_keeps_last_symbol_and_exact_bytes(tmp_path: Path):
    # CIAA CRA, through an evidenced hardware base. The symbolic BF mask is
    # longer than the old 95-character planned-access evidence capacity.
    original = bytes.fromhex("41f900bfe001022800bf0e004e75")
    path = tmp_path / "mask.bin"
    path.write_bytes(original)
    source = RawBinarySource(BinarySourceKind.RAW_BINARY, path,
        RawAddressModel.RUNTIME_ABSOLUTE, 0x1000, 0x1000, 0,
        str(path), path.with_suffix(".analysis"))
    text = render_project_source_with_c_backend(source)
    assert "CIACRAF_PBON|CIACRAF_START" in text
    assert "andi.b #CIACRAF_TODIN|" in text
    includes = Path(__file__).resolve().parents[1] / "ext/amiga_includes/ndk_2.0/include"
    rebuilt, _ = assemble_platform_source_text_with_c_backend("amiga-raw", text, include_dir=includes)
    assert rebuilt == original


@pytest.mark.parametrize("word, spelling", [(0x7FFF, "$7FFF.w"),
    (0x8000, "$FFFF8000.w"), (0x8800, "$FFFF8800.w"), (0xFFFF, "$FFFFFFFF.w")])
def test_absolute_short_numeric_address_sign_extension(tmp_path, word, spelling):
    # MOVE.B #7,absolute.W; RTS. The spelling changes, the WORD does not.
    original = bytes.fromhex("11fc0007") + word.to_bytes(2, "big") + bytes.fromhex("4e75")
    path = tmp_path / "short.bin"
    path.write_bytes(original)
    source = RawBinarySource(BinarySourceKind.RAW_BINARY, path,
        RawAddressModel.RUNTIME_ABSOLUTE, 0x1000, 0x1000, 0,
        str(path), path.with_suffix(".analysis"))
    text = render_project_source_with_c_backend(source)
    assert (spelling if word >= 0x8000 else spelling.removesuffix(".w")) in text
    rebuilt, _ = assemble_platform_source_text_with_c_backend("amiga-raw", text)
    assert rebuilt == original
