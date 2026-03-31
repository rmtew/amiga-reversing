from __future__ import annotations

import struct
from types import SimpleNamespace
from typing import cast

from disasm.instruction_rows import render_instruction_text
from disasm.target_metadata import (
    CustomStructFieldMetadata,
    CustomStructMetadata,
)
from disasm.types import HunkDisassemblySession
from m68k.m68k_disasm import Instruction
from m68k.memory_provenance import (
    MemoryRegionAddressSpace,
    provenance_base_displacement,
)
from m68k.os_calls import OsKb, TypedMemoryRegion
from tests.os_kb_helpers import make_empty_os_kb
from tests.platform_helpers import make_platform


def _instruction_at(hunk: HunkDisassemblySession, addr: int) -> Instruction:
    for block in hunk.blocks.values():
        for inst in block.instructions:
            if inst.offset == addr:
                return inst
    raise ValueError(f"Instruction not found at ${addr:04X}")


def _render_at(
    hunk: HunkDisassemblySession,
    addr: int,
) -> tuple[str, str, tuple[str, ...]]:
    inst = _instruction_at(hunk, addr)
    text, comment, comment_parts = render_instruction_text(
        inst, hunk, set(), include_arg_subs=True)
    return text, comment, comment_parts


def _custom_node_hunk_session() -> HunkDisassemblySession:
    os_kb = make_empty_os_kb()
    os_kb.STRUCTS = {
        "GenAmNode": CustomStructMetadata(
            name="GenAmNode",
            size=36,
            fields=(
                CustomStructFieldMetadata(
                    name="genam_node_flags",
                    type="BYTE",
                    offset=16,
                    size=1,
                ),
                CustomStructFieldMetadata(
                    name="genam_node_type",
                    type="WORD",
                    offset=18,
                    size=2,
                ),
            ),
            seed_origin="manual_analysis",
            review_status="seeded",
            citation="synthetic regression fixture",
        ),
    }
    node_region = TypedMemoryRegion(
        struct="GenAmNode",
        size=36,
        provenance=provenance_base_displacement(
            MemoryRegionAddressSpace.APP,
            "a6",
            422,
        ),
    )
    blocks = {
        0: SimpleNamespace(
            start=0,
            end=16,
            successors=(),
            predecessors=(),
            xrefs=(),
            is_entry=True,
            is_return=False,
            instructions=(
                Instruction(
                    offset=0x0000,
                    size=6,
                    opcode=0x0C6B,
                    text="corrupted",
                    raw=struct.pack(">HHH", 0x0C6B, 0x03EB, 0x0012),
                    kb_mnemonic="cmpi",
                    operand_size="w",
                    operand_texts=("#$3eb", "18(a3)"),
                    opcode_text="cmpi.w",
                ),
                Instruction(
                    offset=0x0006,
                    size=4,
                    opcode=0x302B,
                    text="corrupted",
                    raw=struct.pack(">HH", 0x302B, 0x0012),
                    kb_mnemonic="move",
                    operand_size="w",
                    operand_texts=("18(a3)", "d0"),
                    opcode_text="move.w",
                ),
                Instruction(
                    offset=0x000A,
                    size=6,
                    opcode=0x082B,
                    text="corrupted",
                    raw=struct.pack(">HHH", 0x082B, 0x0001, 0x0010),
                    kb_mnemonic="btst",
                    operand_size="b",
                    operand_texts=("#1", "16(a3)"),
                    opcode_text="btst",
                ),
            ),
        )
    }
    return HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks=blocks,
        platform=make_platform(app_base=(6, 0)),
        os_kb=cast(OsKb, os_kb),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        region_map={
            0x0000: {"a3": node_region},
            0x0006: {"a3": node_region},
            0x000A: {"a3": node_region},
        },
        app_offsets={422: "app_current_node"},
    )


def test_custom_node_walk_uses_seeded_metadata_struct_fields() -> None:
    hunk = _custom_node_hunk_session()

    assert _render_at(hunk, 0x0000) == ("cmpi.w #$3eb,genam_node_type(a3)", "", ())
    assert _render_at(hunk, 0x0006) == ("move.w genam_node_type(a3),d0", "", ())
    assert _render_at(hunk, 0x000A) == ("btst #1,genam_node_flags(a3)", "", ())

