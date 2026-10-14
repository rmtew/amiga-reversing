"""Independent vasm encoding for the simulator path used by frame proofs."""

import ctypes
import os
import subprocess

import pytest

from amiga_reversing.tools.direct_payload_adapter import VASM
from src.tests.test_m68k_simulator_abstract import (
    M68kDiagList,
    M68kSimCpuState,
    _const,
    _diag_has_errors,
    _diag_message,
    _disasm_library,
    _section_ptr,
)


class ConcreteState(ctypes.Structure):
    _fields_ = [
        ("d", ctypes.c_uint32 * 8),
        ("a", ctypes.c_uint32 * 8),
        ("c", ctypes.c_uint32 * 32),
        ("pc", ctypes.c_uint32),
        ("sr", ctypes.c_uint16),
    ]


class ConcreteResult(ctypes.Structure):
    _fields_ = [("diagnostics", M68kDiagList)]


ARITHMETIC_CASES = [
    ("adda.w #-4,a7", 0, -4),
    ("suba.w #-4,a7", 0, 4),
    ("adda.w #$8000,a7", 0, -32768),
    ("suba.w #$8000,a7", 0, 32768),
    ("adda.w d0,a7", 0x1234FFFC, -4),
    ("suba.w d0,a7", 0x1234FFFC, 4),
    ("adda.w d0,a7", 0xFFFF0004, 4),
    ("adda.l d0,a7", 0x1234FFFC, 0x1234FFFC),
    ("suba.l d0,a7", 0x1234FFFC, -0x1234FFFC),
]


def assemble_arithmetic(tmp_path, instruction):
    if not VASM.exists():
        pytest.skip("Installed vasm required for independent fixture encoding")
    asm = tmp_path / "arithmetic.s"
    binary = tmp_path / "arithmetic.bin"
    asm.write_text("    org 0\n    " + instruction + "\n")
    result = subprocess.run(
        [str(VASM), "-Fbin", "-m68000", "-no-opt", "-o", str(binary), str(asm)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return binary.read_bytes()


@pytest.mark.parametrize(("instruction", "source", "delta"), ARITHMETIC_CASES)
def test_address_arithmetic_extends_source_width_in_both_simulators(
    tmp_path, instruction, source, delta
):
    code = assemble_arithmetic(tmp_path, instruction)
    buf = (ctypes.c_uint8 * len(code)).from_buffer_copy(code)
    library = _disasm_library()
    state = M68kSimCpuState()
    state.a[7] = _const(0x10452)
    state.d[0] = _const(source)
    state.sr = 0x271F
    abstract = library.m68k_simulate_one_abstract_for_cpu(
        buf, len(code), 0, ctypes.byref(state)
    )
    assert not _diag_has_errors(abstract.diagnostics), _diag_message(
        abstract.diagnostics
    )
    assert abstract.step.next_state.a[7].kind == 1
    assert abstract.step.next_state.a[7].value == (0x10452 + delta) & 0xFFFFFFFF
    assert abstract.step.next_state.sr == state.sr
    # Signed deltas preserve a destination section pointer's identity.
    state.a[7] = _section_ptr(0x10452)
    pointer = library.m68k_simulate_one_abstract_for_cpu(
        buf, len(code), 0, ctypes.byref(state)
    )
    assert pointer.step.next_state.a[7].kind == 2
    assert pointer.step.next_state.a[7].value == (0x10452 + delta) & 0xFFFFFFFF
    concrete_step = library.m68k_simulate_one_concrete_for_cpu
    concrete_step.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_uint8,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ConcreteState),
    ]
    concrete_step.restype = ConcreteResult
    concrete = ConcreteState()
    concrete.a[7] = 0x10452
    concrete.d[0] = source
    concrete.sr = 0x271F
    outcome = concrete_step(buf, len(code), 0, buf, len(code), ctypes.byref(concrete))
    assert not _diag_has_errors(outcome.diagnostics), _diag_message(outcome.diagnostics)
    assert concrete.a[7] == (0x10452 + delta) & 0xFFFFFFFF
    assert concrete.sr == 0x271F


@pytest.mark.parametrize(
    "instruction", ["adda.w d0,a7", "suba.w d0,a7", "adda.l d0,a7"]
)
@pytest.mark.parametrize("source_kind", ["unknown", "section_pointer"])
def test_unproved_arithmetic_source_cannot_retain_known_destination(
    tmp_path, instruction, source_kind
):
    code = assemble_arithmetic(tmp_path, instruction)
    buf = (ctypes.c_uint8 * len(code)).from_buffer_copy(code)
    state = M68kSimCpuState()
    state.a[7] = _const(0x10452)
    if source_kind == "section_pointer":
        state.d[0] = _section_ptr(0xFFFC)
    outcome = _disasm_library().m68k_simulate_one_abstract_for_cpu(
        buf, len(code), 0, ctypes.byref(state)
    )
    assert not _diag_has_errors(outcome.diagnostics), _diag_message(outcome.diagnostics)
    assert outcome.step.next_state.a[7].kind == 0


@pytest.mark.parametrize(
    ("instruction", "start", "expected"),
    [
        ("adda.w #4,a7", 0x7FFFFFFE, 0x80000002),
        ("suba.w #4,a7", 0x80000002, 0x7FFFFFFE),
        ("adda.w #-4,a7", 2, 0xFFFFFFFE),
        ("suba.w #-4,a7", 0xFFFFFFFE, 2),
    ],
)
def test_section_pointer_arithmetic_wraps_without_signed_overflow(
    tmp_path, instruction, start, expected
):
    code = assemble_arithmetic(tmp_path, instruction)
    buf = (ctypes.c_uint8 * len(code)).from_buffer_copy(code)
    state = M68kSimCpuState()
    state.a[7] = _section_ptr(start)
    outcome = _disasm_library().m68k_simulate_one_abstract_for_cpu(
        buf, len(code), 0, ctypes.byref(state)
    )
    assert not _diag_has_errors(outcome.diagnostics), _diag_message(outcome.diagnostics)
    assert outcome.step.next_state.a[7].kind == 2
    assert outcome.step.next_state.a[7].value == expected


@pytest.mark.skipif(
    not os.environ.get("COPPERLINE_BINARY"),
    reason="Set COPPERLINE_BINARY for the independent execution oracle",
)
def test_real_copperline_address_arithmetic_oracle(tmp_path):
    from amiga_reversing.tools.copperline_control import CopperlineProcess

    with CopperlineProcess(
        os.environ["COPPERLINE_BINARY"], rom=os.environ.get("COPPERLINE_ROM")
    ) as process:
        client = process.client
        for instruction, source, delta in ARITHMETIC_CASES:
            code = assemble_arithmetic(tmp_path, instruction)
            client.request(
                "mem.write", {"addr": 0xC10000, "data": code.hex(), "encoding": "hex"}
            )
            for reg, value in (
                ("sr", 0x271F),
                ("a7", 0x10452),
                ("d0", source),
                ("pc", 0xC10000),
            ):
                client.request("regs.set", {"reg": reg, "value": value})
            stop = client.request("step", {"n": 1})
            assert stop["reason"] == "step", (instruction, stop)
            registers = client.registers()
            assert registers["a7"] == (0x10452 + delta) & 0xFFFFFFFF, instruction
            assert registers["sr"] == 0x271F, instruction
