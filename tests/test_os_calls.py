"""Tests for OS call type propagation.

Tests return value store tracing and argument annotation
from identified library calls.
"""

import struct
from collections.abc import Iterable, Mapping
from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast

import pytest
from _pytest.monkeypatch import MonkeyPatch

from m68k.abstract_values import _unknown
from m68k.instruction_primitives import Operand
from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble
from m68k.m68k_executor import (
    AbstractMemory,
    BasicBlock,
    CPUState,
    InstructionTrace,
    analyze,
)
from m68k.memory_provenance import (
    MemoryRegionAddressSpace,
    MemoryRegionDerivation,
    MemoryRegionDerivationKind,
    MemoryRegionProvenance,
)
from m68k.os_calls import (
    AppMemoryDirection,
    AppMemoryType,
    LibraryBaseTag,
    LibraryCall,
    RegisterFact,
    TypedMemoryRegion,
    _build_lvo_lookup,
    _refined_named_base_struct,
    _region_from_typed_address,
    _resolve_lvo,
    analyze_call_setups,
    app_memory_type_priority,
    build_app_memory_types,
    build_app_named_bases,
    build_app_pointer_regions,
    build_app_slot_infos,
    build_app_struct_regions,
    identify_library_calls,
    propagate_typed_memory_regions,
    refine_opened_base_calls,
    select_primary_app_memory_type,
    trace_return_stores,
)
from m68k.os_structs import resolve_struct_field
from m68k_kb import runtime_os
from tests.platform_helpers import make_platform


def _prov_base(address_space: MemoryRegionAddressSpace, base_register: str,
               displacement: int) -> MemoryRegionProvenance:
    return MemoryRegionProvenance(
        address_space=address_space,
        derivation=MemoryRegionDerivation(
            kind=MemoryRegionDerivationKind.BASE_DISPLACEMENT,
            base_register=base_register,
            displacement=displacement,
        ),
    )


def _prov_ptr(base_register: str, displacement: int) -> MemoryRegionProvenance:
    return MemoryRegionProvenance(
        address_space=MemoryRegionAddressSpace.REGISTER,
        derivation=MemoryRegionDerivation(
            kind=MemoryRegionDerivationKind.FIELD_POINTER,
            base_register=base_register,
            displacement=displacement,
        ),
    )


def _prov_named(named_base: str) -> MemoryRegionProvenance:
    return MemoryRegionProvenance(
        address_space=MemoryRegionAddressSpace.REGISTER,
        derivation=MemoryRegionDerivation(
            kind=MemoryRegionDerivationKind.NAMED_BASE,
            named_base=named_base,
        ),
    )


def _make_lib_call(addr: int, block: int, function: str, library: str = "dos.library",
                   lvo: int = -60, output: Mapping[str, str | None] | None = None,
                   inputs: Iterable[Mapping[str, object]] | None = None) -> LibraryCall:
    """Build a LibraryCall matching identify_library_calls output."""
    typed_output = None
    if output is not None:
        output_name = output["name"]
        output_reg = output["reg"]
        assert output_name is not None
        assert output_reg is not None
        typed_output = runtime_os.OsOutput(
            name=output_name,
            reg=output_reg,
            type=output.get("type"),
            i_struct=output.get("i_struct"),
        )
    typed_inputs = tuple(
        runtime_os.OsInput(
            name=cast(str, input_name),
            regs=cast(tuple[str, ...], input_regs),
            type=cast(str | None, inp.get("type")),
            i_struct=cast(str | None, inp.get("i_struct")),
            semantic_kind=cast(str | None, inp.get("semantic_kind")),
            semantic_note=cast(str | None, inp.get("semantic_note")),
        )
        for inp in (inputs or ())
        for input_name, input_regs in [(
            inp["name"],
            tuple(inp["regs"]) if "regs" in inp else (inp["reg"],),
        )]
        if input_name is not None and all(reg is not None for reg in input_regs)
    )
    return LibraryCall(
        addr=addr,
        block=block,
        library=library,
        function=function,
        lvo=lvo,
        inputs=typed_inputs,
        output=typed_output,
    )


def _corrupt_instruction_texts(blocks: Mapping[int, BasicBlock]) -> None:
    for block in blocks.values():
        for inst in block.instructions:
            inst.text = "corrupted"


# -- Gap 1: Return value store tracing --------------------------------

def test_return_store_to_app_memory() -> None:
    """D0 from library call stored to d(A6) -> names the app memory slot.

    Pattern:
        bsr.w   dos_dispatch    ; returns D0 = file handle
        move.l  d0,100(a6)      ; store to app memory
    """
    sentinel = 0x80000002
    code = b''
    # $00: bsr.w $0A (dos_dispatch call)
    code += struct.pack('>HH', 0x6100, 0x0008)
    # $04: move.l d0,100(a6)
    code += struct.pack('>HH', 0x2D40, 0x0064)
    # $08: rts
    code += struct.pack('>H', 0x4E75)
    # $0A: rts (dummy dos_dispatch)
    code += struct.pack('>H', 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)
    blocks = result["blocks"]

    lib_calls = [_make_lib_call(
        addr=0x00, block=0x00, function="Output",
        output={"name": "file", "reg": "D0", "type": "BPTR"},
    )]

    _corrupt_instruction_texts(blocks)
    stores = trace_return_stores(blocks, lib_calls, base_reg=6)
    # Should find: offset 100 -> "Output_file" or similar
    assert 100 in stores, (
        f"Expected app offset 100 from D0 store after Output(), "
        f"got {stores}")
    info = stores[100]
    assert info.function == "Output"
    assert info.name == "file"


def test_return_store_multiple_calls() -> None:
    """Two different calls store to different app memory slots.

    Each call is in its own block (separated by branches).
    """
    sentinel = 0x80000002
    code = b''
    # Block 0: Output call
    # $00: bsr.w $14 (Output call)
    code += struct.pack('>HH', 0x6100, 0x0012)
    # $04: move.l d0,100(a6)     (fallthrough block)
    code += struct.pack('>HH', 0x2D40, 0x0064)
    # $08: bra.s $0A             (force new block for next call)
    code += struct.pack('>H', 0x6000 | 0)  # bra.w with 0 disp
    # need bra.w: 0x6000 + word disp
    # Actually bra.s can't have disp 0. Use bra.w:
    # $08: bra.w $0C
    code = b''
    # $00: bsr.w $14
    code += struct.pack('>HH', 0x6100, 0x0012)
    # Fallthrough $04: move.l d0,100(a6)
    # But this is in the fallthrough block after BSR. Let me restructure.

    # Simpler: two separate subroutines, each calls and stores
    # sub_a at $00:
    # $00: bsr.w $14 (Output)
    code = struct.pack('>HH', 0x6100, 0x0012)
    # $04: move.l d0,100(a6)
    code += struct.pack('>HH', 0x2D40, 0x0064)
    # $08: rts
    code += struct.pack('>H', 0x4E75)
    # sub_b at $0A:
    # $0A: bsr.w $14 (Input)
    code += struct.pack('>HH', 0x6100, 0x0008)
    # $0E: move.l d0,104(a6)
    code += struct.pack('>HH', 0x2D40, 0x0068)
    # $12: rts
    code += struct.pack('>H', 0x4E75)
    # dispatch at $14: rts
    code += struct.pack('>H', 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0, 0x0A],
                     platform=platform)
    blocks = result["blocks"]

    lib_calls = [
        _make_lib_call(addr=0x00, block=0x00, function="Output",
                       output={"name": "file", "reg": "D0"}),
        _make_lib_call(addr=0x0A, block=0x0A, function="Input",
                       lvo=-54,
                       output={"name": "file", "reg": "D0"}),
    ]

    stores = trace_return_stores(blocks, lib_calls, base_reg=6)
    assert 100 in stores and stores[100].function == "Output"
    assert 104 in stores and stores[104].function == "Input"


def test_return_store_no_output() -> None:
    """Call without output field produces no stores."""
    code = b''
    code += struct.pack('>HH', 0x6100, 0x0004)  # bsr.w $06
    code += struct.pack('>HH', 0x2D40, 0x0064)  # move.l d0,100(a6)
    code += struct.pack('>H', 0x4E75)

    platform = make_platform(app_base=(6, 0x80000002), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    lib_calls = [_make_lib_call(addr=0x00, block=0x00, function="Close")]
    stores = trace_return_stores(result["blocks"], lib_calls, base_reg=6)
    assert len(stores) == 0


# -- Gap 2: Argument annotation ---------------------------------------

def test_annotate_argument_from_app_memory() -> None:
    """Argument loaded from d(A6) before call gets annotation.

    Pattern:
        move.l  100(a6),d1      ; load file handle -> D1 = file arg
        bsr.w   dos_dispatch    ; Write(file, buffer, length)
    """
    sentinel = 0x80000002
    code = b''
    # $00: move.l 100(a6),d1
    code += struct.pack('>HH', 0x222E, 0x0064)
    # $04: bsr.w $0A
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $08: rts
    code += struct.pack('>H', 0x4E75)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="Write", lvo=-48,
        inputs=[
            {"name": "file", "reg": "D1"},
            {"name": "buffer", "reg": "D2"},
            {"name": "length", "reg": "D3"},
        ],
    )]

    _corrupt_instruction_texts(result["blocks"])
    annotations = analyze_call_setups(result["blocks"], lib_calls, runtime_os, code, platform).arg_annotations
    # Should annotate $00 (move.l 100(a6),d1) as "file" argument
    assert 0x00 in annotations, (
        f"Expected annotation at $00 for D1=file, got {annotations}")
    assert annotations[0x00].arg_name == "file"


def test_analyze_call_setups_promotes_code_pointer_seed() -> None:
    code = b""
    code += struct.pack(">HH", 0x4BFA, 0x0008)  # lea $0c(pc),a5
    code += struct.pack(">HH", 0x6100, 0x0008)  # bsr.w $0e
    code += struct.pack(">H", 0x4E75)           # rts
    code += struct.pack(">HH", 0x7000, 0x4E73)  # moveq #0,d0 ; rte
    code += struct.pack(">H", 0x4E75)           # dispatcher rts

    platform = make_platform()
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x04,
        block=0x00,
        function="Supervisor",
        library="exec.library",
        lvo=-30,
        inputs=[{
            "name": "userFunction",
            "reg": "A5",
            "type": "void *",
            "semantic_kind": "code_ptr",
        }],
    )]

    setup = analyze_call_setups(result["blocks"], lib_calls, runtime_os, code, platform, base_addr=0)

    assert setup.code_entry_points == (0x0A,)
    assert setup.segment_code_symbols[0x0A] == "supervisor_userfunction"


def test_analyze_call_setups_skips_non_literal_string_seed() -> None:
    code = b""
    code += struct.pack(">HI", 0x223C, 0x0000000E)  # move.l #$0000000E,d1
    code += struct.pack(">HH", 0x6100, 0x0006)      # bsr.w $0c
    code += struct.pack(">HH", 0x7000, 0x4E75)      # moveq #0,d0 ; rts
    code += struct.pack(">H", 0x4E75)               # dispatcher rts
    code += b"\xFF\x00"

    platform = make_platform()
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x06,
        block=0x00,
        function="Open",
        library="dos.library",
        lvo=-30,
        inputs=[{
            "name": "name",
            "reg": "D1",
            "type": "STRPTR",
            "semantic_kind": "string_ptr",
        }],
    )]

    setup = analyze_call_setups(result["blocks"], lib_calls, runtime_os, code, platform, base_addr=0)

    assert setup.string_ranges == {}
    assert setup.segment_data_symbols == {}


def test_annotate_multiple_arguments() -> None:
    """Multiple argument registers get separate annotations."""
    sentinel = 0x80000002
    code = b''
    # $00: move.l 100(a6),d1  (file)
    code += struct.pack('>HH', 0x222E, 0x0064)
    # $04: movea.l a0,a2       (not an arg setup)
    code += struct.pack('>H', 0x2448)
    # $06: move.l a4,d2        (buffer)
    code += struct.pack('>H', 0x240C)
    # $08: moveq #21,d3        (length)
    code += struct.pack('>H', 0x7615)
    # $0A: bsr.w $10
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $0E: rts
    code += struct.pack('>H', 0x4E75)
    # $10: rts
    code += struct.pack('>H', 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x0A, block=0x00, function="Write", lvo=-48,
        inputs=[
            {"name": "file", "reg": "D1"},
            {"name": "buffer", "reg": "D2"},
            {"name": "length", "reg": "D3"},
        ],
    )]

    annotations = analyze_call_setups(result["blocks"], lib_calls, runtime_os, code, platform).arg_annotations
    assert 0x00 in annotations  # D1 = file
    assert 0x06 in annotations  # D2 = buffer
    assert 0x08 in annotations  # D3 = length


def test_open_device_annotates_iorequest_on_a1_not_flags() -> None:
    """LEA d(A6),A1 sets OpenDevice ioRequest, not D1 flags."""
    sentinel = 0x80000002
    code = b""
    # $00: lea 100(a6),a1
    code += struct.pack(">HH", 0x43EE, 0x0064)
    # $04: moveq #0,d1
    code += struct.pack(">H", 0x7200)
    # $06: bsr.w $0C
    code += struct.pack(">HH", 0x6100, 0x0004)
    # $0A: rts
    code += struct.pack(">H", 0x4E75)
    # $0C: rts
    code += struct.pack(">H", 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x06, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[
            {"name": "devName", "reg": "A0", "type": "STRPTR"},
            {"name": "unit", "reg": "D0", "type": "ULONG"},
            {"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
             "i_struct": "IO"},
            {"name": "flags", "reg": "D1", "type": "ULONG"},
        ],
    )]

    annotations = analyze_call_setups(result["blocks"], lib_calls, runtime_os, code, platform).arg_annotations
    assert annotations[0x00].arg_name == "ioRequest"
    assert annotations[0x00].arg_reg == "A1"
    assert annotations[0x04].arg_name == "flags"
    assert annotations[0x04].arg_reg == "D1"

    types = build_app_memory_types(result["blocks"], lib_calls, base_reg=6)
    assert types[100].name == "ioRequest"
    assert types[100].type == "struct IORequest *"


def test_analyze_call_setups_tracks_zero_terminated_strptr_segment_range() -> None:
    code = b""
    code += struct.pack(">HH", 0x41FA, 0x0008)      # $00 lea $0A(pc),a0
    code += struct.pack(">HH", 0x6100, 0x0008)      # $04 bsr.w $0E
    code += struct.pack(">H", 0x4E75)               # $08 rts
    code += b"con.device\x00"                       # $0A
    code += struct.pack(">H", 0x4E75)               # $15 rts

    result = analyze(code, propagate=True, entry_points=[0], platform=make_platform())
    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[
            {"name": "devName", "reg": "A0", "type": "STRPTR"},
        ],
    )]

    setup = analyze_call_setups(result["blocks"], lib_calls, runtime_os, code, make_platform())
    assert setup.segment_data_symbols == {0x000A: "opendevice_devname"}
    assert setup.string_ranges == {0x000A: 0x0015}


def test_analyze_call_setups_tracks_internal_absolute_strptr_segment_range() -> None:
    code = b""
    code += struct.pack(">HI", 0x41F9, 0x0000000A)   # $00 lea $0000000A,a0
    code += struct.pack(">HH", 0x6100, 0x0008)       # $06 bsr.w $10
    code += b"con.device\x00"                        # $0A
    code += struct.pack(">H", 0x4E75)                # $15 rts
    code += struct.pack(">H", 0x4E75)                # $17 rts

    result = analyze(code, propagate=True, entry_points=[0], platform=make_platform())
    lib_calls = [_make_lib_call(
        addr=0x06, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[
            {"name": "devName", "reg": "A0", "type": "STRPTR"},
        ],
    )]

    setup = analyze_call_setups(result["blocks"], lib_calls, runtime_os, code, make_platform())
    assert setup.segment_data_symbols == {0x000A: "opendevice_devname"}
    assert setup.string_ranges == {0x000A: 0x0015}


def test_propagate_typed_memory_regions_tracks_struct_typed_register_and_resolves_nested_fields() -> None:
    sentinel = 0x80000002
    code = b""
    # $00: lea 100(a6),a1
    code += struct.pack(">HH", 0x43EE, 0x0064)
    # $04: bsr.w $0A
    code += struct.pack(">HH", 0x6100, 0x0004)
    # $08: rts
    code += struct.pack(">H", 0x4E75)
    # $0A: rts
    code += struct.pack(">H", 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[
            {"name": "devName", "reg": "A0", "type": "STRPTR"},
            {"name": "unit", "reg": "D0", "type": "ULONG"},
            {"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
             "i_struct": "IO"},
            {"name": "flags", "reg": "D1", "type": "ULONG"},
        ],
    )]
    os_kb = type("FakeOsKb", (), {
        "META": runtime_os.META,
        "STRUCTS": {
            "LN": runtime_os.OsStruct(
                source="exec/types.i",
                base_offset=0,
                base_offset_symbol=None,
                size=14,
                fields=(
                    runtime_os.OsStructField("LN_SUCC", "APTR", 0, 4),
                    runtime_os.OsStructField("LN_PRED", "APTR", 4, 4),
                    runtime_os.OsStructField("LN_TYPE", "UBYTE", 8, 1),
                    runtime_os.OsStructField("LN_PRI", "BYTE", 9, 1),
                    runtime_os.OsStructField("LN_NAME", "APTR", 10, 4),
                    runtime_os.OsStructField("LN_SIZE", "LABEL", 14, 0),
                ),
            ),
            "MN": runtime_os.OsStruct(
                source="exec/ports.i",
                base_offset=14,
                base_offset_symbol=None,
                size=20,
                fields=(
                    runtime_os.OsStructField("MN_REPLYPORT", "APTR", 14, 4),
                    runtime_os.OsStructField("MN_LENGTH", "UWORD", 18, 2),
                    runtime_os.OsStructField("MN_SIZE", "LABEL", 20, 0),
                ),
                base_struct="LN",
            ),
            "IO": runtime_os.OsStruct(
                source="exec/io.i",
                base_offset=20,
                base_offset_symbol=None,
                size=48,
                fields=(
                    runtime_os.OsStructField("IO_DEVICE", "APTR", 20, 4),
                    runtime_os.OsStructField("IO_SIZE", "LABEL", 32, 0),
                ),
                base_struct="MN",
            ),
        },
        "CONSTANTS": {},
        "LIBRARIES": {"exec.library": runtime_os.LIBRARIES["exec.library"]},
    })()

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, os_kb, platform)

    assert types[0x04]["a1"] == TypedMemoryRegion(
        struct="IO",
        size=48,
        provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 100),
    )
    succ = resolve_struct_field(os_kb.STRUCTS, "IO", 0)
    assert succ is not None
    assert succ.owner_struct == "LN"
    assert succ.field.name == "LN_SUCC"

    reply_port = resolve_struct_field(os_kb.STRUCTS, "IO", 14)
    assert reply_port is not None
    assert reply_port.owner_struct == "MN"
    assert reply_port.field.name == "MN_REPLYPORT"

    device = resolve_struct_field(os_kb.STRUCTS, "IO", 20)
    assert device is not None
    assert device.owner_struct == "IO"
    assert device.field.name == "IO_DEVICE"


def test_propagate_typed_memory_regions_survives_past_call_fallthrough() -> None:
    sentinel = 0x80000002
    code = b""
    # $00: lea 100(a6),a1
    code += struct.pack(">HH", 0x43EE, 0x0064)
    # $04: bsr.w $0C
    code += struct.pack(">HH", 0x6100, 0x0004)
    # $08: move.l 20(a1),d0
    code += struct.pack(">HH", 0x2029, 0x0014)
    # $0C: rts
    code += struct.pack(">H", 0x4E75)
    # $0E: rts
    code += struct.pack(">H", 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[
            {"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
             "i_struct": "IO"},
        ],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)
    assert types[0x08]["a1"].struct == "IO"


def test_propagate_typed_memory_regions_loads_pointee_struct_from_field() -> None:
    sentinel = 0x80000002
    code = b""
    # $00: lea 100(a6),a1
    code += struct.pack(">HH", 0x43EE, 0x0064)
    # $04: bsr.w $0E
    code += struct.pack(">HH", 0x6100, 0x0008)
    # $08: movea.l 20(a1),a0
    code += struct.pack(">HH", 0x2069, 0x0014)
    # $0C: move.l 14(a0),d0
    code += struct.pack(">HH", 0x2028, 0x000E)
    # $10: rts
    code += struct.pack(">H", 0x4E75)
    # $12: rts
    code += struct.pack(">H", 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[
            {"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
             "i_struct": "IO"},
        ],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)
    assert types[0x0C]["a0"] == TypedMemoryRegion(
        struct="DD",
        size=34,
        provenance=_prov_ptr("a1", 20),
    )


def test_propagate_typed_memory_regions_loads_reply_port_pointee_struct() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43EE, 0x0064)  # lea 100(a6),a1
    code += struct.pack(">HH", 0x6100, 0x0008)  # bsr.w $0E
    code += struct.pack(">HH", 0x2069, 0x000E)  # movea.l 14(a1),a0
    code += struct.pack(">HH", 0x2028, 0x0010)  # move.l 16(a0),d0
    code += struct.pack(">H", 0x4E75)           # rts
    code += struct.pack(">H", 0x4E75)           # rts

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[{"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)
    assert types[0x0C]["a0"] == TypedMemoryRegion(
        struct="MP",
        size=34,
        provenance=_prov_ptr("a1", 14),
    )


def test_propagate_typed_memory_regions_loads_unit_pointee_struct() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43EE, 0x0064)  # lea 100(a6),a1
    code += struct.pack(">HH", 0x6100, 0x0008)  # bsr.w $0E
    code += struct.pack(">HH", 0x2069, 0x0018)  # movea.l 24(a1),a0
    code += struct.pack(">HH", 0x2028, 0x0022)  # move.l 34(a0),d0
    code += struct.pack(">H", 0x4E75)           # rts
    code += struct.pack(">H", 0x4E75)           # rts

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[{"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)
    assert types[0x0C]["a0"] == TypedMemoryRegion(
        struct="UNIT",
        size=38,
        provenance=_prov_ptr("a1", 24),
    )


def test_propagate_typed_memory_regions_loads_pointee_from_static_full_extension_index() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43EE, 0x0064)      # $00 lea 100(a6),a1
    code += struct.pack(">HH", 0x6100, 0x000C)      # $04 bsr.w $14
    code += bytes.fromhex("207101600014")           # $08 movea.l (20,a1),a0 [full ext, index suppressed]
    code += struct.pack(">HH", 0x2028, 0x000E)      # $0E move.l 14(a0),d0
    code += struct.pack(">H", 0x4E75)               # $12 rts
    code += struct.pack(">H", 0x4E75)               # $14 rts

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[{"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)
    assert types[0x0E]["a0"] == TypedMemoryRegion(
        struct="DD",
        size=34,
        provenance=_prov_ptr("a1", 20),
    )


def test_propagate_typed_memory_regions_loads_pointee_from_brief_index_with_concrete_reg() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43EE, 0x0064)      # $00 lea 100(a6),a1
    code += struct.pack(">H", 0x7004)               # $04 moveq #4,d0
    code += struct.pack(">HH", 0x6100, 0x0008)      # $06 bsr.w $12
    code += struct.pack(">HH", 0x2071, 0x0010)      # $0A movea.l 16(a1,d0.w),a0
    code += struct.pack(">HH", 0x2028, 0x000E)      # $0E move.l 14(a0),d0
    code += struct.pack(">H", 0x4E75)               # $12 rts
    code += struct.pack(">H", 0x4E75)               # $14 rts

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x06, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[{"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)
    assert types[0x0E]["a0"] == TypedMemoryRegion(
        struct="DD",
        size=34,
        provenance=_prov_ptr("a1", 20),
    )


def test_propagate_typed_memory_regions_loads_pointee_from_full_extension_index_with_concrete_reg() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43EE, 0x0064)      # $00 lea 100(a6),a1
    code += struct.pack(">H", 0x7004)               # $04 moveq #4,d0
    code += struct.pack(">HH", 0x6100, 0x000A)      # $06 bsr.w $14
    code += bytes.fromhex("207101200010")           # $0A movea.l (16,a1,d0.w),a0 [full ext]
    code += struct.pack(">HH", 0x2028, 0x000E)      # $10 move.l 14(a0),d0
    code += struct.pack(">H", 0x4E75)               # $14 rts
    code += struct.pack(">H", 0x4E75)               # $16 rts

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x06, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[{"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)
    assert types[0x10]["a0"] == TypedMemoryRegion(
        struct="DD",
        size=34,
        provenance=_prov_ptr("a1", 20),
    )


def test_propagate_typed_memory_regions_supports_pc_relative_storage() -> None:
    code = b""
    # $00: lea 8(pc),a1 -> target = $0A
    code += struct.pack(">HH", 0x43FA, 0x0008)
    # $04: bsr.w $0A
    code += struct.pack(">HH", 0x6100, 0x0004)
    # $08: rts
    code += struct.pack(">H", 0x4E75)
    # $0A: rts
    code += struct.pack(">H", 0x4E75)
    code += b"\x00" * 8

    platform = make_platform(scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[
            {"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
             "i_struct": "IO"},
        ],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)
    assert types[0x04]["a1"] == TypedMemoryRegion(
        struct="IO",
        size=runtime_os.STRUCTS["IO"].size,
            provenance=MemoryRegionProvenance(
                address_space=MemoryRegionAddressSpace.SEGMENT,
                segment_addr=0x0A,
            ),
    )


def test_build_app_struct_regions_persists_open_device_iorequest_region() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43EE, 0x0064)  # lea 100(a6),a1
    code += struct.pack(">HH", 0x6100, 0x0004)  # bsr.w $0A
    code += struct.pack(">H", 0x4E75)           # rts
    code += struct.pack(">H", 0x4E75)           # rts
    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[{"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"}],
    )]

    regions = build_app_struct_regions(result["blocks"], lib_calls, runtime_os, platform)

    assert regions == {
        100: TypedMemoryRegion(
            struct="IO",
            size=runtime_os.STRUCTS["IO"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 100),
        )
    }


def test_build_app_pointer_regions_refines_openlibrary_slot_to_concrete_struct() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43FA, 0x0018)      # $00 lea $1A(pc),a1
    code += struct.pack(">H", 0x7000)               # $04 moveq #0,d0
    code += struct.pack(">HH", 0x6100, 0x000E)      # $06 bsr.w $18
    code += struct.pack(">HH", 0x2D40, 0x0064)      # $0A move.l d0,100(a6)
    code += struct.pack(">HH", 0x206E, 0x0064)      # $0E movea.l 100(a6),a0
    code += struct.pack(">HH", 0x2028, 0x003A)      # $12 move.l 58(a0),d0
    code += struct.pack(">H", 0x4E75)               # $16 rts
    code += struct.pack(">H", 0x4E75)               # $18 rts
    code += b"dos.library\x00"                      # $1A

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x06, block=0x00, function="OpenLibrary", library="exec.library",
        lvo=-552,
        output={"name": "library", "reg": "D0", "type": "struct Library *",
                "i_struct": "LIB"},
        inputs=[{"name": "libName", "reg": "A1", "type": "STRPTR"}],
    )]

    regions = build_app_pointer_regions(result["blocks"], lib_calls, code, runtime_os, platform)

    assert regions == {
        100: TypedMemoryRegion(
            struct="DosLibrary",
            size=runtime_os.STRUCTS["DosLibrary"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 100),
        )
    }


def test_refined_named_base_struct_requires_kb_mapping() -> None:
    os_kb = SimpleNamespace(
        META=replace(runtime_os.META, named_base_structs={}),
        STRUCTS=runtime_os.STRUCTS,
    )

    with pytest.raises(KeyError, match="dos\\.library.*LIB"):
        _refined_named_base_struct(os_kb, "dos.library", "LIB")


def test_propagate_typed_memory_regions_loads_concrete_named_base_from_app_slot() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43FA, 0x0018)      # $00 lea $1A(pc),a1
    code += struct.pack(">H", 0x7000)               # $04 moveq #0,d0
    code += struct.pack(">HH", 0x6100, 0x000E)      # $06 bsr.w $18
    code += struct.pack(">HH", 0x2D40, 0x0064)      # $0A move.l d0,100(a6)
    code += struct.pack(">HH", 0x206E, 0x0064)      # $0E movea.l 100(a6),a0
    code += struct.pack(">HH", 0x2028, 0x003A)      # $12 move.l 58(a0),d0
    code += struct.pack(">H", 0x4E75)               # $16 rts
    code += struct.pack(">H", 0x4E75)               # $18 rts
    code += b"dos.library\x00"                      # $1A

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x06, block=0x00, function="OpenLibrary", library="exec.library",
        lvo=-552,
        output={"name": "library", "reg": "D0", "type": "struct Library *",
                "i_struct": "LIB"},
        inputs=[{"name": "libName", "reg": "A1", "type": "STRPTR"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)

    assert types[0x12]["a0"] == TypedMemoryRegion(
        struct="DosLibrary",
        size=runtime_os.STRUCTS["DosLibrary"].size,
        provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 100),
    )


def test_propagate_typed_memory_regions_uses_summary_produced_named_base_region() -> None:
    code = b""
    code += struct.pack(">HH", 0x6100, 0x000A)      # $00 bsr.w $0C
    code += struct.pack(">HH", 0x2040, 0x2028)      # $04 movea.l d0,a0; move.l 58(a0),d0
    code += struct.pack(">HH", 0x003A, 0x4E75)      # $08 ext word; rts
    code += struct.pack(">HH", 0x43FA, 0x0012)      # $0C lea $20(pc),a1
    code += struct.pack(">H", 0x7000)               # $10 moveq #0,d0
    code += struct.pack(">H", 0x2F0E)               # $12 move.l a6,-(sp)
    code += struct.pack(">I", 0x2C780004)           # $14 movea.l ($0004).w,a6
    code += struct.pack(">HH", 0x4EAE, 0xFDD8)      # $18 jsr -552(a6)
    code += struct.pack(">H", 0x2C5F)               # $1C movea.l (sp)+,a6
    code += struct.pack(">H", 0x4E75)               # $1E rts
    code += b"dos.library\x00"                      # $20

    platform = make_platform()
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x18, block=0x0C, function="OpenLibrary", library="exec.library",
        lvo=-552,
        output={"name": "library", "reg": "D0", "type": "struct Library *",
                "i_struct": "LIB"},
        inputs=[{"name": "libName", "reg": "A1", "type": "STRPTR"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)

    assert types[0x06]["a0"] == TypedMemoryRegion(
        struct="DosLibrary",
        size=runtime_os.STRUCTS["DosLibrary"].size,
        provenance=_prov_named("dos.library"),
    )


def test_propagate_typed_memory_regions_uses_summary_field_pointer_transfer() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43EE, 0x0064)      # $00 lea 100(a6),a1
    code += struct.pack(">HH", 0x6100, 0x000A)      # $04 bsr.w $12 (OpenDevice stub)
    code += struct.pack(">HH", 0x6100, 0x000A)      # $08 bsr.w $16 (wrapper)
    code += struct.pack(">HH", 0x2028, 0x0014)      # $0C move.l 20(a0),d0
    code += struct.pack(">H", 0x4E75)               # $10 rts
    code += struct.pack(">H", 0x4E75)               # $12 rts
    code += struct.pack(">HH", 0x2069, 0x0014)      # $14 movea.l 20(a1),a0
    code += struct.pack(">H", 0x4E75)               # $18 rts

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[{"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)

    assert types[0x0C]["a0"] == TypedMemoryRegion(
        struct="DD",
        size=runtime_os.STRUCTS["DD"].size,
        provenance=_prov_ptr("a1", 20),
    )


def test_propagate_typed_memory_regions_loads_pointee_from_app_region_access() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43EE, 0x0064)  # $00 lea 100(a6),a1
    code += struct.pack(">HH", 0x6100, 0x0008)  # $04 bsr.w $0E
    code += struct.pack(">HH", 0x206E, 0x0078)  # $08 movea.l 120(a6),a0
    code += struct.pack(">HH", 0x2028, 0x0014)  # $0C move.l 20(a0),d0
    code += struct.pack(">H", 0x4E75)           # $10 rts
    code += struct.pack(">H", 0x4E75)           # $12 rts
    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[{"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)

    assert types[0x0C]["a0"] == TypedMemoryRegion(
        struct="DD",
        size=runtime_os.STRUCTS["DD"].size,
        provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 120),
    )


def test_build_app_named_bases_reads_constant_device_name() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x41FA, 0x000E)      # $00 lea $10(pc),a0
    code += struct.pack(">HH", 0x43EE, 0x0064)      # $04 lea 100(a6),a1
    code += struct.pack(">HH", 0x6100, 0x0004)      # $08 bsr.w $0E
    code += struct.pack(">H", 0x4E75)               # $0C rts
    code += struct.pack(">H", 0x4E75)               # $0E rts
    code += b"timer.device\x00"                     # $10
    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x08, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[
            {"name": "devName", "reg": "A0", "type": "STRPTR"},
            {"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
             "i_struct": "IO"},
        ],
    )]

    bases = build_app_named_bases(result["blocks"], lib_calls, code, runtime_os, platform)

    assert bases == {100: "timer.device"}


def test_refine_opened_base_calls_resolves_timer_device_from_open_device_seed() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x41FA, 0x001C)      # $00 lea $1E(pc),a0
    code += struct.pack(">HH", 0x43EE, 0x0064)      # $04 lea 100(a6),a1
    code += struct.pack(">HH", 0x6100, 0x0012)      # $08 bsr.w $1C
    code += struct.pack(">HH", 0x2C6E, 0x0078)      # $0C movea.l 120(a6),a6
    code += struct.pack(">HH", 0x4EAE, 0xFFBE)      # $10 jsr -66(a6)
    code += struct.pack(">H", 0x4E75)               # $14 rts
    code += b"\x00\x00\x00\x00\x00\x00"            # padding
    code += struct.pack(">H", 0x4E75)               # $1C rts
    code += b"timer.device\x00"                     # $1E
    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [
        _make_lib_call(
            addr=0x08, block=0x00, function="OpenDevice", library="exec.library",
            lvo=-444,
            inputs=[
                {"name": "devName", "reg": "A0", "type": "STRPTR"},
                {"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"},
            ],
        ),
        _make_lib_call(
            addr=0x10, block=0x00, function="LVO_66", library="unknown",
            lvo=-66,
        ),
    ]

    refined = refine_opened_base_calls(result["blocks"], lib_calls, code, runtime_os, platform)

    assert refined[1].library == "timer.device"
    assert refined[1].function == "GetSysTime"
    assert refined[1].lvo == -66


def test_build_app_named_bases_reads_openlibrary_store_name() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43FA, 0x0012)      # $00 lea $14(pc),a1
    code += struct.pack(">H", 0x7000)               # $04 moveq #0,d0
    code += struct.pack(">HH", 0x6100, 0x0008)      # $06 bsr.w $10
    code += struct.pack(">HH", 0x2D40, 0x0064)      # $0A move.l d0,100(a6)
    code += struct.pack(">H", 0x4E75)               # $0E rts
    code += struct.pack(">H", 0x4E75)               # $10 rts
    code += b"\x00\x00"                            # $12 padding
    code += b"dos.library\x00"                      # $14
    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x06, block=0x00, function="OpenLibrary", library="exec.library",
        lvo=-552,
        output={"name": "library", "reg": "D0", "type": "struct Library *", "i_struct": "LIB"},
        inputs=[
            {"name": "libName", "reg": "A1", "type": "STRPTR"},
            {"name": "version", "reg": "D0", "type": "ULONG"},
        ],
    )]

    bases = build_app_named_bases(result["blocks"], lib_calls, code, runtime_os, platform)

    assert bases == {100: "dos.library"}


def test_build_app_slot_infos_infers_pointer_struct_for_openlibrary_store() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43FA, 0x0010)      # $00 lea $12(pc),a1
    code += struct.pack(">H", 0x7000)               # $04 moveq #0,d0
    code += struct.pack(">HH", 0x6100, 0x0008)      # $06 bsr.w $10
    code += struct.pack(">HH", 0x2D40, 0x0064)      # $0A move.l d0,100(a6)
    code += struct.pack(">H", 0x4E75)               # $0E rts
    code += struct.pack(">H", 0x4E75)               # $10 rts
    code += b"dos.library\x00"                      # $12

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x06, block=0x00, function="OpenLibrary", library="exec.library",
        lvo=-552,
        output={"name": "library", "reg": "D0", "type": "struct Library *", "i_struct": "LIB"},
        inputs=[
            {"name": "libName", "reg": "A1", "type": "STRPTR"},
            {"name": "version", "reg": "D0", "type": "ULONG"},
        ],
    )]

    infos = build_app_slot_infos(result["blocks"], lib_calls, code, runtime_os, platform)

    assert len(infos) == 1
    info = infos[0]
    assert info.offset == 100
    assert info.symbol == "app_dos_library_base"
    assert info.struct is None
    assert info.size is None
    assert info.pointer_struct == "DosLibrary"
    assert info.named_base == "dos.library"


def test_refine_opened_base_calls_resolves_library_call_from_app_slot() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43FA, 0x001C)      # $00 lea $1E(pc),a1
    code += struct.pack(">H", 0x7000)               # $04 moveq #0,d0
    code += struct.pack(">HH", 0x6100, 0x0012)      # $06 bsr.w $1C
    code += struct.pack(">HH", 0x2D40, 0x0064)      # $0A move.l d0,100(a6)
    code += struct.pack(">HH", 0x2C6E, 0x0064)      # $0E movea.l 100(a6),a6
    code += struct.pack(">HH", 0x4EAE, 0xFFD0)      # $12 jsr -48(a6)
    code += struct.pack(">H", 0x4E75)               # $16 rts
    code += b"\x00\x00\x00\x00"                    # $18 padding
    code += struct.pack(">H", 0x4E75)               # $1C rts
    code += b"dos.library\x00"                      # $1E
    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [
        _make_lib_call(
            addr=0x06, block=0x00, function="OpenLibrary", library="exec.library",
            lvo=-552,
            output={"name": "library", "reg": "D0", "type": "struct Library *", "i_struct": "LIB"},
            inputs=[
                {"name": "libName", "reg": "A1", "type": "STRPTR"},
                {"name": "version", "reg": "D0", "type": "ULONG"},
            ],
        ),
        _make_lib_call(
            addr=0x12, block=0x0A, function="LVO_48", library="unknown", lvo=-48,
        ),
    ]

    refined = refine_opened_base_calls(result["blocks"], lib_calls, code, runtime_os, platform)

    assert refined[1].library == "dos.library"
    assert refined[1].function == "Write"
    assert refined[1].lvo == -48


def test_refine_opened_base_calls_resolves_resource_call_from_app_slot() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43FA, 0x0016)      # $00 lea $18(pc),a1
    code += struct.pack(">HH", 0x6100, 0x0010)      # $04 bsr.w $16
    code += struct.pack(">HH", 0x2D40, 0x0064)      # $08 move.l d0,100(a6)
    code += struct.pack(">HH", 0x2C6E, 0x0064)      # $0C movea.l 100(a6),a6
    code += struct.pack(">HH", 0x4EAE, 0xFFFA)      # $10 jsr -6(a6)
    code += struct.pack(">H", 0x4E75)               # $14 rts
    code += struct.pack(">H", 0x4E75)               # $16 rts
    code += b"misc.resource\x00"                    # $18
    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [
        _make_lib_call(
            addr=0x04, block=0x00, function="OpenResource", library="exec.library",
            lvo=-498,
            output={"name": "resource", "reg": "D0", "type": "APTR"},
            inputs=[{"name": "resName", "reg": "A1", "type": "STRPTR"}],
        ),
        _make_lib_call(
            addr=0x10, block=0x08, function="LVO_6", library="unknown", lvo=-6,
        ),
    ]

    refined = refine_opened_base_calls(result["blocks"], lib_calls, code, runtime_os, platform)

    assert refined[1].library == "misc.resource"
    assert refined[1].function == "AllocMiscResource"
    assert refined[1].lvo == -6


def test_identify_library_calls_resolves_direct_wrapper_call_per_caller() -> None:
    code = b""
    code += struct.pack(">H", 0x2F0E)               # $00 move.l a6,-(sp)
    code += struct.pack(">I", 0x2C780004)           # $02 movea.l ($0004).w,a6
    code += struct.pack(">HH", 0x6100, 0x000C)      # $06 bsr.w $14
    code += struct.pack(">H", 0x2C5F)               # $0A movea.l (sp)+,a6
    code += struct.pack(">H", 0x4E75)               # $0C rts
    code += struct.pack(">HH", 0x6100, 0x0004)      # $0E bsr.w $14
    code += struct.pack(">H", 0x4E75)               # $12 rts
    code += struct.pack(">HH", 0x4EAE, 0xFDD8)      # $14 jsr -552(a6)
    code += struct.pack(">H", 0x4E75)               # $18 rts

    platform = make_platform()
    result = analyze(code, propagate=True, entry_points=[0, 0x0E], platform=platform)

    calls = identify_library_calls(
        result["blocks"],
        code,
        runtime_os,
        result["exit_states"],
        result["call_targets"],
        platform,
    )

    assert len(calls) == 1
    call = calls[0]
    assert call.addr == 0x06
    assert call.block == 0x00
    assert call.dispatch == 0x14
    assert call.library == "exec.library"
    assert call.function == "OpenLibrary"
    assert call.lvo == -552


def test_identify_library_calls_uses_entry_initial_states() -> None:
    code = b""
    code += b"\x4e\x71" * 0x44
    code += struct.pack(">HH", 0x4EAE, 0xFDD8)      # $88 jsr -552(a6)
    code += struct.pack(">H", 0x4E75)               # $8C rts
    code += struct.pack(">HH", 0x4EAE, 0xFFBE)      # $8E jsr -66(a6)
    code += struct.pack(">H", 0x4E75)               # $92 rts

    init_state = CPUState()
    init_state.set_reg("an", 6, _unknown(tag=LibraryBaseTag(library_base="exec.library")))
    vector_state = CPUState()
    vector_state.set_reg("an", 6, _unknown(tag=LibraryBaseTag(library_base="icon.library")))
    platform = make_platform()
    result = analyze(
        code,
        propagate=True,
        entry_points=[0x88, 0x8E],
        platform=platform,
        entry_initial_states={0x88: init_state, 0x8E: vector_state},
    )

    calls = identify_library_calls(
        result["blocks"],
        code,
        runtime_os,
        result["exit_states"],
        result["call_targets"],
        platform,
        entry_initial_states={0x88: init_state, 0x8E: vector_state},
    )

    assert {(call.addr, call.library, call.function, call.lvo) for call in calls} == {
        (0x88, "exec.library", "OpenLibrary", -552),
        (0x8E, "icon.library", "iconPrivate6", -66),
    }


def test_identify_library_calls_does_not_reuse_caller_a6_after_local_overwrite() -> None:
    code = b""
    code += struct.pack(">HH", 0x6100, 0x000A)      # $00 bsr.w $0C
    code += struct.pack(">H", 0x4E75)               # $04 rts
    code += b"\x4e\x71" * 3                         # $06 padding
    code += struct.pack(">H", 0x2F0E)               # $0C move.l a6,-(sp)
    code += struct.pack(">HH", 0x2C6E, 0x0022)      # $0E movea.l 34(a6),a6
    code += struct.pack(">HH", 0x4EAE, 0xFF2E)      # $12 jsr -210(a6)
    code += struct.pack(">H", 0x2C5F)               # $16 movea.l (sp)+,a6
    code += struct.pack(">H", 0x4E75)               # $18 rts

    vector_state = CPUState()
    vector_state.set_reg("an", 6, _unknown(tag=LibraryBaseTag(library_base="icon.library")))
    platform = make_platform()
    result = analyze(
        code,
        propagate=True,
        entry_points=[0, 0x0C],
        platform=platform,
        entry_initial_states={0x0C: vector_state},
    )

    calls = identify_library_calls(
        result["blocks"],
        code,
        runtime_os,
        result["exit_states"],
        result["call_targets"],
        platform,
        entry_initial_states={0x0C: vector_state},
    )

    assert any(
        call.addr == 0x12 and call.block == 0x0C and call.library == "unknown" and call.lvo == -210
        for call in calls
    )


def test_identify_library_calls_ignores_unreached_blocks_without_traces() -> None:
    code = b"\x4e\x75\x4e\x71\x4e\xae\xff\xa0"
    entry_block = BasicBlock(start=0, end=2, instructions=[disassemble(code, 0)[0]], is_entry=True)
    unreached_block = BasicBlock(
        start=4,
        end=8,
        instructions=[disassemble(code[4:], 4)[0]],
        is_entry=False,
    )
    calls = identify_library_calls(
        {0: entry_block, 4: unreached_block},
        code,
        runtime_os,
        {},
        set(),
        make_platform(),
    )

    assert calls == []


def test_identify_library_calls_defers_shared_indexed_dispatch_to_real_call_sites() -> None:
    code = b""
    code += struct.pack(">H", 0x70E2)               # $00 moveq #-30,d0
    code += struct.pack(">HH", 0x6100, 0x0012)      # $02 bsr.w $16
    code += struct.pack(">H", 0x7000)               # $06 moveq #0,d0
    code += struct.pack(">H", 0x4E75)               # $08 rts
    code += struct.pack(">H", 0x70DC)               # $0A moveq #-36,d0
    code += struct.pack(">HH", 0x6100, 0x0008)      # $0C bsr.w $16
    code += struct.pack(">H", 0x7000)               # $10 moveq #0,d0
    code += struct.pack(">H", 0x4E75)               # $12 rts
    code += b"\x4e\x71"                             # $14 padding
    code += struct.pack(">HH", 0x2C6E, 0x0064)      # $16 movea.l 100(a6),a6
    code += assemble_instruction("jsr 0(a6,d0.w)") # $1A jsr 0(a6,d0.w)
    code += struct.pack(">H", 0x4E75)               # $1E rts

    sentinel = 0x80000000
    init_mem = AbstractMemory()
    init_mem.write(
        sentinel + 100,
        _unknown(tag=LibraryBaseTag(library_base="dos.library")),
        "l",
    )
    platform = make_platform(
        app_base=(6, sentinel),
        initial_mem=init_mem,
        scratch_regs=(),
    )
    result = analyze(
        code,
        propagate=True,
        entry_points=[0, 0x0A],
        platform=platform,
    )

    calls = identify_library_calls(
        result["blocks"],
        code,
        runtime_os,
        result["exit_states"],
        result["call_targets"],
        platform,
    )

    assert {(call.addr, call.block, call.library, call.function, call.dispatch) for call in calls} == {
        (0x02, 0x00, "dos.library", "Open", 0x1A),
        (0x0C, 0x0A, "dos.library", "Close", 0x1A),
    }


def test_identify_library_calls_recovers_caller_index_from_local_block_when_traces_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    code = b""
    code += struct.pack(">H", 0x70E2)               # $00 moveq #-30,d0
    code += struct.pack(">HH", 0x6100, 0x0012)      # $02 bsr.w $16
    code += struct.pack(">H", 0x7000)               # $06 moveq #0,d0
    code += struct.pack(">H", 0x4E75)               # $08 rts
    code += struct.pack(">H", 0x70DC)               # $0A moveq #-36,d0
    code += struct.pack(">HH", 0x6100, 0x0008)      # $0C bsr.w $16
    code += struct.pack(">H", 0x7000)               # $10 moveq #0,d0
    code += struct.pack(">H", 0x4E75)               # $12 rts
    code += b"\x4e\x71"                             # $14 padding
    code += struct.pack(">HH", 0x2C6E, 0x0064)      # $16 movea.l 100(a6),a6
    code += assemble_instruction("jsr 0(a6,d0.w)") # $1A jsr 0(a6,d0.w)
    code += struct.pack(">H", 0x4E75)               # $1E rts

    sentinel = 0x80000000
    init_mem = AbstractMemory()
    init_mem.write(
        sentinel + 100,
        _unknown(tag=LibraryBaseTag(library_base="dos.library")),
        "l",
    )
    platform = make_platform(
        app_base=(6, sentinel),
        initial_mem=init_mem,
        scratch_regs=(),
    )
    result = analyze(
        code,
        propagate=True,
        entry_points=[0, 0x0A],
        platform=platform,
    )

    from m68k import m68k_executor

    real_collect = m68k_executor.collect_instruction_traces

    def without_caller_traces(*args: Any, **kwargs: Any) -> list[InstructionTrace]:
        traces = real_collect(*args, **kwargs)
        return [
            trace for trace in traces
            if trace.instruction.offset not in {0x02, 0x0C}
        ]

    monkeypatch.setattr(m68k_executor, "collect_instruction_traces", without_caller_traces)

    calls = identify_library_calls(
        result["blocks"],
        code,
        runtime_os,
        result["exit_states"],
        result["call_targets"],
        platform,
    )

    assert {(call.addr, call.block, call.library, call.function, call.dispatch) for call in calls} == {
        (0x02, 0x00, "dos.library", "Open", 0x1A),
        (0x0C, 0x0A, "dos.library", "Close", 0x1A),
    }


def test_identify_library_calls_keeps_direct_execbase_calls_without_traces(
    monkeypatch: MonkeyPatch,
) -> None:
    code = b""
    code += struct.pack(">HH", 0x2C78, 0x0004)      # $00 movea.l ($0004).w,a6
    code += struct.pack(">HH", 0x4EAE, 0xFF2E)      # $04 jsr -210(a6)
    code += struct.pack(">H", 0x4E75)               # $08 rts

    platform = make_platform()
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)

    from m68k import m68k_executor

    monkeypatch.setattr(m68k_executor, "collect_instruction_traces", lambda *args, **kwargs: [])

    calls = identify_library_calls(
        result["blocks"],
        code,
        runtime_os,
        result["exit_states"],
        result["call_targets"],
        platform,
    )

    assert len(calls) == 1
    call = calls[0]
    assert call.addr == 0x04
    assert call.library == "exec.library"
    assert call.function == "FreeMem"


def test_identify_library_calls_does_not_collect_traces_for_simple_direct_execbase_call(
    monkeypatch: MonkeyPatch,
) -> None:
    code = b""
    code += struct.pack(">HH", 0x2C78, 0x0004)      # $00 movea.l ($0004).w,a6
    code += struct.pack(">HH", 0x4EAE, 0xFF2E)      # $04 jsr -210(a6)
    code += struct.pack(">H", 0x4E75)               # $08 rts

    platform = make_platform()
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)

    from m68k import m68k_executor

    def should_not_collect(*args: object, **kwargs: object) -> list[InstructionTrace]:
        raise AssertionError("collect_instruction_traces should not be called")

    monkeypatch.setattr(m68k_executor, "collect_instruction_traces", should_not_collect)

    calls = identify_library_calls(
        result["blocks"],
        code,
        runtime_os,
        result["exit_states"],
        result["call_targets"],
        platform,
    )

    assert len(calls) == 1
    assert calls[0].function == "FreeMem"


def test_identify_library_calls_keeps_direct_app_slot_base_calls_without_traces(
    monkeypatch: MonkeyPatch,
) -> None:
    code = b""
    code += struct.pack(">HH", 0x2C6E, 0x0004)      # $00 movea.l 4(a6),a6
    code += struct.pack(">HH", 0x4EAE, 0xFFB8)      # $04 jsr -72(a6)
    code += struct.pack(">H", 0x4E75)               # $08 rts

    sentinel = 0x80000000
    init_mem = AbstractMemory()
    init_mem.write(
        sentinel + 4,
        _unknown(tag=LibraryBaseTag(library_base="intuition.library")),
        "l",
    )
    platform = make_platform(
        app_base=(6, sentinel),
        initial_mem=init_mem,
        scratch_regs=(),
    )
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)

    from m68k import m68k_executor

    monkeypatch.setattr(m68k_executor, "collect_instruction_traces", lambda *args, **kwargs: [])

    calls = identify_library_calls(
        result["blocks"],
        code,
        runtime_os,
        result["exit_states"],
        result["call_targets"],
        platform,
    )

    assert len(calls) == 1
    call = calls[0]
    assert call.addr == 0x04
    assert call.library == "intuition.library"
    assert call.function == "CloseWindow"


def test_propagate_typed_memory_regions_handles_movea_pointee_load_to_a6() -> None:
    sentinel = 0x80000002
    code = b""
    code += struct.pack(">HH", 0x43EE, 0x0064)      # $00 lea 100(a6),a1
    code += struct.pack(">HH", 0x6100, 0x0008)      # $04 bsr.w $0E
    code += struct.pack(">HH", 0x2C6E, 0x0078)      # $08 movea.l 120(a6),a6
    code += struct.pack(">HH", 0x4EAE, 0xFFBE)      # $0C jsr -66(a6)
    code += struct.pack(">H", 0x4E75)               # $10 rts
    code += struct.pack(">H", 0x4E75)               # $12 rts
    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0], platform=platform)
    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="OpenDevice", library="exec.library",
        lvo=-444,
        inputs=[{"name": "ioRequest", "reg": "A1", "type": "struct IORequest *",
                 "i_struct": "IO"}],
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, platform)

    assert types[0x0C]["a6"] == TypedMemoryRegion(
        struct="DD",
        size=runtime_os.STRUCTS["DD"].size,
        provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 120),
    )


def test_propagate_typed_memory_regions_seeds_struct_typed_os_call_output_register() -> None:
    code = b""
    code += struct.pack(">HH", 0x4EAE, 0xFFA0)      # $00 jsr -96(a6)
    code += struct.pack(">H", 0x2040)               # $04 movea.l d0,a0
    code += struct.pack(">HH", 0x2068, 0x0016)      # $06 movea.l 22(a0),a0
    code += struct.pack(">H", 0x4E75)               # $0A rts

    result = analyze(code, propagate=True, entry_points=[0], platform=make_platform())
    lib_calls = [_make_lib_call(
        addr=0x00, block=0x00, function="FindResident", library="exec.library",
        lvo=-96,
        inputs=[{"name": "name", "reg": "A1", "type": "STRPTR"}],
        output={"name": "resident", "reg": "D0", "type": "struct Resident *", "i_struct": "RT"},
    )]

    types = propagate_typed_memory_regions(result["blocks"], lib_calls, code, runtime_os, make_platform())

    assert types[0x06]["a0"] == TypedMemoryRegion(
        struct="RT",
        size=runtime_os.STRUCTS["RT"].size,
        provenance=MemoryRegionProvenance(address_space=MemoryRegionAddressSpace.REGISTER),
    )


def test_region_from_typed_address_keeps_struct_offset_for_direct_displacement() -> None:
    current = {
        "a1": RegisterFact(region=TypedMemoryRegion(
            struct="MP",
            size=runtime_os.STRUCTS["MP"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.REGISTER, "a0", 14),
            struct_offset=14,
        )),
    }
    op = Operand(mode="disp", reg=1, value=2)

    region = _region_from_typed_address(current, op, runtime_os, {}, None)

    assert region == TypedMemoryRegion(
        struct="MP",
        size=runtime_os.STRUCTS["MP"].size,
        provenance=_prov_base(MemoryRegionAddressSpace.REGISTER, "a0", 14),
        struct_offset=16,
    )


def test_region_from_typed_address_loads_memory_indirect_preindexed_pointee() -> None:
    current = {
        "a1": RegisterFact(region=TypedMemoryRegion(
            struct="IO",
            size=runtime_os.STRUCTS["IO"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 100),
        )),
        "d0": RegisterFact(concrete=4),
    }
    op = Operand(
        mode="index",
        reg=1,
        value=20,
        index_reg=0,
        index_is_addr=False,
        index_size="w",
        index_scale=1,
        full_extension=True,
        memory_indirect=True,
        postindexed=False,
        base_suppressed=False,
        index_suppressed=False,
        base_displacement=16,
        outer_displacement=0,
    )

    region = _region_from_typed_address(current, op, runtime_os, {}, None)

    assert region == TypedMemoryRegion(
        struct="DD",
        size=runtime_os.STRUCTS["DD"].size,
        provenance=_prov_ptr("a1", 20),
    )


def test_region_from_typed_address_loads_memory_indirect_postindexed_pointee_offset() -> None:
    current = {
        "a1": RegisterFact(region=TypedMemoryRegion(
            struct="IO",
            size=runtime_os.STRUCTS["IO"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 100),
        )),
        "d0": RegisterFact(concrete=16),
    }
    op = Operand(
        mode="index",
        reg=1,
        value=20,
        index_reg=0,
        index_is_addr=False,
        index_size="w",
        index_scale=1,
        full_extension=True,
        memory_indirect=True,
        postindexed=True,
        base_suppressed=False,
        index_suppressed=False,
        base_displacement=20,
        outer_displacement=0,
    )

    region = _region_from_typed_address(current, op, runtime_os, {}, None)

    assert region == TypedMemoryRegion(
        struct="DD",
        size=runtime_os.STRUCTS["DD"].size,
        provenance=_prov_ptr("a1", 20),
        struct_offset=16,
    )


# -- Gaps 3-6: Unified app memory type map ----------------------------

def test_backward_type_names_app_slot() -> None:
    """Gap 3: argument load from d(A6) names the app memory slot.

    Write(file=D1) where D1 loaded from 100(a6) -> offset 100 typed
    as 'file' for Write.
    """
    sentinel = 0x80000002
    code = b''
    # $00: move.l 100(a6),d1  (load file handle for Write)
    code += struct.pack('>HH', 0x222E, 0x0064)
    # $04: bsr.w $0A
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $08: rts
    code += struct.pack('>H', 0x4E75)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="Write", lvo=-48,
        inputs=[{"name": "file", "reg": "D1", "type": "BPTR"}],
    )]

    types = build_app_memory_types(result["blocks"], lib_calls, base_reg=6)
    assert 100 in types, f"Expected offset 100 typed from Write input, got {types}"
    assert types[100].name == "file"


def test_select_primary_app_memory_type_prefers_backward_usage() -> None:
    forward = AppMemoryType(
        name="dest",
        function="GetSysTime",
        type="struct timeval *",
        library="timer.device",
        direction=AppMemoryDirection.FORWARD,
    )
    backward = AppMemoryType(
        name="src",
        function="SubTime",
        type="struct timeval *",
        library="timer.device",
        direction=AppMemoryDirection.BACKWARD,
    )

    assert app_memory_type_priority(backward) < app_memory_type_priority(forward)
    assert select_primary_app_memory_type((forward, backward)) == backward


def test_forward_through_register_copy() -> None:
    """Gap 4: return value flows through register copy to store.

    Output() returns D0, then move.l d0,d1; move.l d1,100(a6).
    The store should still be traced to Output's return value.
    """
    sentinel = 0x80000002
    code = b''
    # $00: bsr.w $0C (Output call)
    code += struct.pack('>HH', 0x6100, 0x000A)
    # $04: move.l d0,d1  (copy return value)
    code += struct.pack('>H', 0x2200)
    # $06: move.l d1,100(a6)  (store via copy)
    code += struct.pack('>HH', 0x2D41, 0x0064)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)
    # $0C: rts (dummy dispatch)
    code += struct.pack('>H', 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x00, block=0x00, function="Output",
        output={"name": "file", "reg": "D0", "type": "BPTR"},
    )]

    _corrupt_instruction_texts(result["blocks"])
    types = build_app_memory_types(result["blocks"], lib_calls, base_reg=6)
    assert 100 in types, (
        f"Expected offset 100 from Output via D0->D1 copy, got {types}")
    assert types[100].function == "Output"


def test_cross_sub_type_flow() -> None:
    """Gap 5: type flows through app memory across subroutines.

    Sub A: Output() -> store to 100(a6)
    Sub B: load 100(a6) -> D1 -> Write(file=D1)

    Both forward (Output -> store) and backward (Write input -> load)
    should name offset 100.
    """
    sentinel = 0x80000002
    code = b''
    # sub_a at $00: calls Output, stores result
    # $00: bsr.w $14 (Output)
    code += struct.pack('>HH', 0x6100, 0x0012)
    # $04: move.l d0,100(a6)
    code += struct.pack('>HH', 0x2D40, 0x0064)
    # $08: rts
    code += struct.pack('>H', 0x4E75)
    # sub_b at $0A: loads from 100(a6), calls Write
    # $0A: move.l 100(a6),d1
    code += struct.pack('>HH', 0x222E, 0x0064)
    # $0E: bsr.w $14 (Write dispatch)
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $12: rts
    code += struct.pack('>H', 0x4E75)
    # dispatch at $14: rts
    code += struct.pack('>H', 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0, 0x0A],
                     platform=platform)

    lib_calls = [
        _make_lib_call(addr=0x00, block=0x00, function="Output",
                       output={"name": "file", "reg": "D0", "type": "BPTR"}),
        _make_lib_call(addr=0x0E, block=0x0A, function="Write", lvo=-48,
                       inputs=[{"name": "file", "reg": "D1", "type": "BPTR"}]),
    ]

    types = build_app_memory_types(result["blocks"], lib_calls, base_reg=6)
    assert 100 in types, (
        f"Expected offset 100 typed from Output store or Write load, "
        f"got {types}")


def test_conditional_store_after_return() -> None:
    """Gap 6: return value stored after conditional check.

    Output() -> tst.l d0 -> beq skip -> move.l d0,100(a6)
    The store should still be found despite the intervening tst/beq.
    """
    sentinel = 0x80000002
    code = b''
    # $00: bsr.w $10 (Output)
    code += struct.pack('>HH', 0x6100, 0x000E)
    # $04: tst.l d0
    code += struct.pack('>H', 0x4A80)
    # $06: beq.s $0E (skip store if null)
    code += struct.pack('>H', 0x6706)
    # $08: move.l d0,100(a6)
    code += struct.pack('>HH', 0x2D40, 0x0064)
    # $0C: bra.s $0E
    code += struct.pack('>H', 0x6000 | 0)
    # Actually bra.s $0E from $0C: PC=$0E, disp=0 -> bra.w
    # Let me restructure:
    # $00: bsr.w $0E (Output)
    code = b''
    code += struct.pack('>HH', 0x6100, 0x000C)
    # fallthrough at $04:
    # $04: tst.l d0
    code += struct.pack('>H', 0x4A80)
    # $06: beq.s $0C (skip, disp = $0C - $08 = 4)
    code += struct.pack('>H', 0x6704)
    # $08: move.l d0,100(a6)
    code += struct.pack('>HH', 0x2D40, 0x0064)
    # $0C: rts
    code += struct.pack('>H', 0x4E75)
    # $0E: rts (dummy dispatch)
    code += struct.pack('>H', 0x4E75)

    platform = make_platform(app_base=(6, sentinel), scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x00, block=0x00, function="Output",
        output={"name": "file", "reg": "D0", "type": "BPTR"},
    )]

    types = build_app_memory_types(result["blocks"], lib_calls, base_reg=6)
    assert 100 in types, (
        f"Expected offset 100 from Output despite conditional store, "
        f"got {types}")


def test_resolve_lvo_requires_known_kb_mapping() -> None:
    lookup = _build_lvo_lookup(runtime_os)

    with pytest.raises(KeyError, match=r"Missing KB LVO mapping for exec\.library:-9990"):
        _resolve_lvo(-9990, "exec.library", lookup)

