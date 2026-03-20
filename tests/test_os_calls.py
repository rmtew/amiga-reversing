"""Tests for OS call type propagation.

Tests return value store tracing and argument annotation
from identified library calls.
"""

import struct

from m68k.os_calls import (trace_return_stores, annotate_call_arguments,
                           build_app_memory_types)
from m68k.m68k_executor import analyze, BasicBlock


def _make_lib_call(addr, block, function, library="dos.library",
                   lvo=-60, output=None, inputs=None):
    """Build a lib_call dict matching the format from identify_library_calls."""
    lc = {
        "addr": addr, "block": block, "lvo": lvo,
        "library": library, "function": function,
    }
    if output:
        lc["output"] = output
    if inputs:
        lc["inputs"] = inputs
    return lc


def _corrupt_instruction_texts(blocks):
    for block in blocks.values():
        for inst in block.instructions:
            inst.text = "corrupted"


# -- Gap 1: Return value store tracing --------------------------------

def test_return_store_to_app_memory():
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

    platform = {
        "scratch_regs": [],
        "initial_base_reg": (6, sentinel),
    }
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
    assert info["function"] == "Output"
    assert info["name"] == "file"


def test_return_store_multiple_calls():
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

    platform = {
        "scratch_regs": [],
        "initial_base_reg": (6, sentinel),
    }
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
    assert 100 in stores and stores[100]["function"] == "Output"
    assert 104 in stores and stores[104]["function"] == "Input"


def test_return_store_no_output():
    """Call without output field produces no stores."""
    code = b''
    code += struct.pack('>HH', 0x6100, 0x0004)  # bsr.w $06
    code += struct.pack('>HH', 0x2D40, 0x0064)  # move.l d0,100(a6)
    code += struct.pack('>H', 0x4E75)

    platform = {"scratch_regs": [], "initial_base_reg": (6, 0x80000002)}
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    lib_calls = [_make_lib_call(addr=0x00, block=0x00, function="Close")]
    stores = trace_return_stores(result["blocks"], lib_calls, base_reg=6)
    assert len(stores) == 0


# -- Gap 2: Argument annotation ---------------------------------------

def test_annotate_argument_from_app_memory():
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

    platform = {"scratch_regs": [], "initial_base_reg": (6, sentinel)}
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
    annotations = annotate_call_arguments(result["blocks"], lib_calls)
    # Should annotate $00 (move.l 100(a6),d1) as "file" argument
    assert 0x00 in annotations, (
        f"Expected annotation at $00 for D1=file, got {annotations}")
    assert annotations[0x00]["arg_name"] == "file"


def test_annotate_multiple_arguments():
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

    platform = {"scratch_regs": [], "initial_base_reg": (6, sentinel)}
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

    annotations = annotate_call_arguments(result["blocks"], lib_calls)
    assert 0x00 in annotations  # D1 = file
    assert 0x06 in annotations  # D2 = buffer
    assert 0x08 in annotations  # D3 = length


# -- Gaps 3-6: Unified app memory type map ----------------------------

def test_backward_type_names_app_slot():
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

    platform = {"scratch_regs": [], "initial_base_reg": (6, sentinel)}
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    lib_calls = [_make_lib_call(
        addr=0x04, block=0x00, function="Write", lvo=-48,
        inputs=[{"name": "file", "reg": "D1", "type": "BPTR"}],
    )]

    types = build_app_memory_types(result["blocks"], lib_calls, base_reg=6)
    assert 100 in types, f"Expected offset 100 typed from Write input, got {types}"
    assert types[100]["name"] == "file"


def test_forward_through_register_copy():
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

    platform = {"scratch_regs": [], "initial_base_reg": (6, sentinel)}
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
    assert types[100]["function"] == "Output"


def test_cross_sub_type_flow():
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

    platform = {"scratch_regs": [], "initial_base_reg": (6, sentinel)}
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


def test_conditional_store_after_return():
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

    platform = {"scratch_regs": [], "initial_base_reg": (6, sentinel)}
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
