"""Hardware-base identities follow full register values and conservative joins."""

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


@pytest.mark.parametrize(
    ("left", "right", "known"),
    [
        ("nop", "nop", True),
        ("moveq #0,d4", "nop", False),
        ("move.w #$F000,d4", "nop", False),
        ("jsr (a0)", "nop", False),
        ("moveq #0,d4", "move.l #$DFF000,d4", False),
        ("nop", "moveq #0,d4", False),
        ("move.l #$DFF000,d4", "move.l #$DFF000,d4", True),
    ],
)
def test_rendered_exchange_requires_the_same_base_on_every_path(
    tmp_path, left, right, known
):
    text = f""" SECTION code,code
 ORG 0
 move.l #$DFF000,d4
 tst.l d0
 beq.b alternate
 {left}
 bra.b joined
alternate:
 {right}
joined:
 exg d4,a5
 move.w #$40,$9C(a5)
 rts
"""
    binary = tmp_path / "input.bin"
    original, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", text, output_path=binary
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(binary),
        analysis_cache_path=tmp_path / "analysis",
    )
    write_target_metadata(
        tmp_path, TargetMetadata(target_type="program", entry_register_seeds=())
    )
    rendered = c_backend.render_project_source_with_c_backend(source)
    assert ("intreq(a5)" in rendered) == known, rendered
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        rendered,
        include_dir=PROJECT_ROOT / "ext/amiga_includes/ndk_2.0/include",
    )
    assert rebuilt == original


@pytest.mark.parametrize(
    ("setup", "change", "known"),
    [
        ("lea.l $DFF000.l,a5", "exg d4,a5", False),
        ("lea.l $DFF000.l,a5", "exg a4,a5", False),
        ("lea.l $DFF000.l,a5", "addq.l #2,a5", False),
        ("lea.l $DFF000.l,a5", "move.w (a5)+,d0", False),
        ("lea.l $DFF000.l,a5", "jsr (a0)", False),
        ("lea.l $DFF000.l,a4", "exg a4,a5", True),
        ("lea.l $DFF000.l,a5", "exg a5,a5", True),
        ("lea.l $DFF000.l,a5", "jmp next(pc)\nnext:", True),
        ("lea.l $DFF000.l,a5", "bsr helper\n bra next\nhelper:\n rts\nnext:", True),
        ("lea.l $DFF000.l,a5", "bsr helper\n bra next\nhelper:\n suba.l a5,a5\n rts\nnext:", False),
    ],
)
def test_native_hardware_facts_do_not_retain_a_swapped_away_base(
    tmp_path, setup, change, known
):
    binary = tmp_path / "input.bin"
    text = (
        f" SECTION code,code\n ORG 0\n {setup}\n {change}\n move.w #$40,$9C(a5)\n rts\n"
    )
    original, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", text, output_path=binary
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(binary),
        analysis_cache_path=tmp_path / "analysis",
    )
    write_target_metadata(
        tmp_path, TargetMetadata(target_type="program", entry_register_seeds=())
    )
    rendered = c_backend.render_project_source_with_c_backend(source)
    assert ("intreq(a5)" in rendered) == known, rendered
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        rendered,
        include_dir=PROJECT_ROOT / "ext/amiga_includes/ndk_2.0/include",
    )
    assert rebuilt == original
