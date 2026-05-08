from __future__ import annotations

import ctypes
import re
import subprocess
import unittest
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.tests._build_helpers import prepare_test_dll
from src.tests._build_helpers import prepare_test_exe
from src.tests._build_helpers import require_built_tools

import machine68k

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
ASM_EXE = BUILD_DIR / "m68k_assembler_app.exe"
DISASM_DLL = BUILD_DIR / "m68k_disassembler_lib.dll"
CPU_BITS = {"68000": 0, "68010": 1, "68020": 2, "68030": 3, "68040": 4}
ASM_TABLES_C = ROOT / "src" / "generated" / "m68k_asm_tables.c"
M68K_DIAG_SEVERITY_ERROR = 3
M68K_DIAG_MESSAGE_SIZE = 160
M68K_DIAG_LIST_CAPACITY = 8
CONTROL_REGISTER_LINES = ASM_TABLES_C.read_text(encoding="utf-8").splitlines()
CONTROL_REGISTER_RE = re.compile(r'\{\s*"([^"]+)",\s*(\d+)u,\s*0x([0-9A-Fa-f]+),')
GLOBAL_CONTROL_REGISTER_SLOTS = {
    match.group(1).upper(): int(match.group(2))
    for line in CONTROL_REGISTER_LINES
    if (match := CONTROL_REGISTER_RE.search(line))
}
SUPPORTED_MACHINE68K_CONTROL_REGS = ["CAAR", "CACR", "DFC", "ISP", "MSP", "SFC", "USP", "VBR"]
SUPPORTED_MACHINE68K_CONTROL_SLOTS = {
    name: GLOBAL_CONTROL_REGISTER_SLOTS[name] for name in SUPPORTED_MACHINE68K_CONTROL_REGS
}


class M68kDiag(ctypes.Structure):
    _fields_ = [
        ("severity", ctypes.c_uint32),
        ("code", ctypes.c_uint32),
        ("message", ctypes.c_char * M68K_DIAG_MESSAGE_SIZE),
    ]


class M68kDiagList(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_size_t),
        ("dropped_count", ctypes.c_size_t),
        ("items", M68kDiag * M68K_DIAG_LIST_CAPACITY),
    ]


class M68kSimConcreteRunResult(ctypes.Structure):
    _fields_ = [("diagnostics", M68kDiagList)]


def _diag_message(diagnostics: M68kDiagList) -> str:
    for index in range(diagnostics.count):
        if diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR:
            return diagnostics.items[index].message.decode("utf-8")
    if diagnostics.count:
        return diagnostics.items[0].message.decode("utf-8")
    return ""


def _diag_has_errors(diagnostics: M68kDiagList) -> bool:
    return any(
        diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR
        for index in range(diagnostics.count)
    )


@dataclass(frozen=True)
class OracleCase:
    case_id: str
    family: str
    asm_text: str
    code_hex: str | None = None
    cpu: str = "68000"
    compare_sr: bool = False
    memory_size: int = 0
    memory_writes: tuple[tuple[int, bytes], ...] = ()
    d: tuple[int, ...] = ()
    a: tuple[int, ...] = ()
    c: tuple[tuple[str, int], ...] = ()
    sr: int = 0
    skip_reason: str | None = None

    def control_slots(self) -> dict[str, int]:
        return {name: SUPPORTED_MACHINE68K_CONTROL_SLOTS[name] for name, enabled in self.c if enabled}

    def build_state(self) -> "M68kSimConcreteState":
        state = M68kSimConcreteState()
        for index, value in enumerate(self.d):
            state.d[index] = value
        for index, value in enumerate(self.a):
            state.a[index] = value
        for name, value in self.c:
            state.c[SUPPORTED_MACHINE68K_CONTROL_SLOTS[name]] = value
        state.sr = self.sr
        return state

    def build_code_and_memory(self) -> tuple[bytes, bytes]:
        code = bytes.fromhex(self.code_hex) if self.code_hex is not None else _assemble_line_hex(self.cpu, self.asm_text)
        size = max(len(code), self.memory_size)
        memory = bytearray(size)
        memory[:len(code)] = code
        for offset, data in self.memory_writes:
            memory[offset:offset + len(data)] = data
        return code, bytes(memory)


class M68kSimConcreteState(ctypes.Structure):
    _fields_ = [
        ("d", ctypes.c_uint32 * 8),
        ("a", ctypes.c_uint32 * 8),
        ("c", ctypes.c_uint32 * 32),
        ("pc", ctypes.c_uint32),
        ("sr", ctypes.c_uint16),
    ]


@lru_cache(maxsize=1)
def _disasm_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(DISASM_DLL)))
    library.m68k_simulate_one_concrete_for_cpu.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_uint8,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(M68kSimConcreteState),
    ]
    library.m68k_simulate_one_concrete_for_cpu.restype = M68kSimConcreteRunResult
    return library


def _assemble_line_hex(cpu: str, text: str) -> bytes:
    result = subprocess.run(
        [str(prepare_test_exe(ASM_EXE)), "assemble-line", "--cpu", cpu, text],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return bytes.fromhex(result.stdout.strip())


def _run_machine68k_one(
    memory_image: bytes,
    setup_state: M68kSimConcreteState,
    cpu: str = "68000",
    control_slots: dict[str, int] | None = None,
) -> tuple[list[int], list[int], dict[str, int], int, int, bytes, list[str]]:
    mach = machine68k.Machine(getattr(machine68k.CPUType, f"M{cpu}"), max(64, len(memory_image) + 16))
    mem = mach.mem
    cpu_state = mach.cpu
    mem.w_block(0, memory_image)
    for index, value in enumerate(setup_state.d):
        cpu_state.w_reg(getattr(machine68k.Register, f"D{index}"), int(value))
    for index, value in enumerate(setup_state.a):
        cpu_state.w_reg(getattr(machine68k.Register, f"A{index}"), int(value))
    cpu_state.w_pc(int(setup_state.pc))
    cpu_state.w_sr(int(setup_state.sr))
    for name, slot in (control_slots or {}).items():
        cpu_state.w_reg(getattr(machine68k.Register, name), int(setup_state.c[slot]))
    seen = {"count": 0}

    def hook(_pc: int) -> None:
        seen["count"] += 1
        if seen["count"] >= 1:
            raise RuntimeError("stop")

    cpu_state.set_instr_hook_callback(hook)
    try:
        cpu_state.execute(100)
    except RuntimeError as exc:
        if str(exc) != "stop":
            raise
    return (
        [cpu_state.r_reg(getattr(machine68k.Register, f"D{index}")) for index in range(8)],
        [cpu_state.r_reg(getattr(machine68k.Register, f"A{index}")) for index in range(8)],
        {name: cpu_state.r_reg(getattr(machine68k.Register, name)) for name in (control_slots or {})},
        cpu_state.r_pc(),
        cpu_state.r_sr(),
        bytes(mem.r_block(0, len(memory_image))),
        [],
    )


@lru_cache(maxsize=1)
def _oracle_case_cache() -> tuple[OracleCase, ...]:
    return (
        OracleCase("moveq-basic", "core", "moveq #7,d0"),
        OracleCase("lea-pc-relative", "ea", "lea $0006(pc),a0"),
        OracleCase("lea-indexed", "ea", "lea 4(a0,d1.w),a1", a=(0x100,), d=(0, 0x00000002)),
        OracleCase("addq-address", "arith", "addq.l #4,a0", a=(0x20,)),
        OracleCase("exg-d0-a1", "core", "exg d0,a1", d=(0x11111111,), a=(0, 0x22222222)),
        OracleCase("jmp-indirect", "control", "jmp (a0)", a=(0x1234,)),
        OracleCase("clr-d0", "logic", "clr.l d0", d=(0x11223344,)),
        OracleCase("bra-short", "control", "bra.s 4"),
        OracleCase("bsr-short", "control", "bsr.s 4", a=(0, 0, 0, 0, 0, 0, 0, 0x20), memory_size=0x24),
        OracleCase("rts-stack", "control", "rts", a=(0, 0, 0, 0, 0, 0, 0, 0x20), memory_size=0x24,
            memory_writes=((0x20, (0x12345678).to_bytes(4, "big")),)),
        OracleCase("rtd-adjust", "control", "rtd #6", cpu="68010", a=(0, 0, 0, 0, 0, 0, 0, 0x20), memory_size=0x30,
            memory_writes=((0x20, (0x12345678).to_bytes(4, "big")),)),
        OracleCase("rtr-stack", "control", "rtr", a=(0, 0, 0, 0, 0, 0, 0, 0x20), sr=0x2700, compare_sr=True,
            memory_size=0x26, memory_writes=((0x20, (0x0015).to_bytes(2, "big")), (0x22, (0x12345678).to_bytes(4, "big")))),
        OracleCase("rte-supervisor", "control", "rte", cpu="68010", a=(0, 0, 0, 0, 0, 0, 0, 0x20), sr=0x2000,
            c=(("USP", 0x120), ("ISP", 0x20), ("VBR", 0)), compare_sr=True, memory_size=0x40,
            memory_writes=((0x20, (0x201F).to_bytes(2, "big")), (0x22, (0x12345678).to_bytes(4, "big")), (0x26, (0x0010).to_bytes(2, "big")))),
        OracleCase("rte-user", "control", "rte", cpu="68010", a=(0, 0, 0, 0, 0, 0, 0, 0x20), sr=0x2000,
            c=(("USP", 0x120), ("ISP", 0x20), ("VBR", 0)), compare_sr=True, memory_size=0x40,
            memory_writes=((0x20, (0x001F).to_bytes(2, "big")), (0x22, (0x12345678).to_bytes(4, "big")), (0x26, (0x0010).to_bytes(2, "big")))),
        OracleCase("dbne-taken", "control", "dbne d0,4", d=(2,), sr=0x0004),
        OracleCase("sne-d0", "control", "sne d0", d=(0x12345678,), sr=0x0000),
        OracleCase("cmp-d0-d1", "compare", "cmp.l d0,d1", d=(0x12345678, 0x12345670), compare_sr=True),
        OracleCase("tst-d0", "compare", "tst.l d0", d=(0x12345678,), compare_sr=True),
        OracleCase("tas-d0", "bit", "tas d0", d=(0x12345634,), compare_sr=True),
        OracleCase("btst-imm-d0", "bit", "btst #2,d0", d=(0x12345634,), compare_sr=True),
        OracleCase("bset-imm-d0", "bit", "bset #3,d0", d=(0x12345634,), compare_sr=True),
        OracleCase("bclr-imm-d0", "bit", "bclr #4,d0", d=(0x12345634,), compare_sr=True),
        OracleCase("bchg-imm-d0", "bit", "bchg #1,d0", d=(0x12345634,), compare_sr=True),
        OracleCase("pea-pc", "stack", "pea 8(pc)", a=(0, 0, 0, 0, 0, 0, 0, 0x20), memory_size=0x24),
        OracleCase("link-a6", "stack", "link a6,#-8", a=(0, 0, 0, 0, 0, 0, 0x11223344, 0x20), memory_size=0x24),
        OracleCase("unlk-a6", "stack", "unlk a6", a=(0, 0, 0, 0, 0, 0, 0x18), memory_size=0x24,
            memory_writes=((0x18, (0x12345678).to_bytes(4, "big")),)),
        OracleCase("movem-reg-mem", "movem", "movem.l d0-d1/a2,(a0)", a=(0x20, 0, 0x33333333), d=(0x11111111, 0x22222222), memory_size=0x40),
        OracleCase("movem-mem-reg", "movem", "movem.l (a0),d0-d1/a2", a=(0x20,), memory_size=0x40,
            memory_writes=((0x20, (0x11111111).to_bytes(4, "big")), (0x24, (0x22222222).to_bytes(4, "big")), (0x28, (0x33333333).to_bytes(4, "big")))),
        OracleCase("movem-predec", "movem", "movem.l d0-d1/a2,-(a7)", a=(0, 0, 0x33333333, 0, 0, 0, 0, 0x30), d=(0x11111111, 0x22222222), memory_size=0x40),
        OracleCase("movem-postinc", "movem", "movem.l (a0)+,d0-d1/a2", a=(0x20,), memory_size=0x40,
            memory_writes=((0x20, (0x11111111).to_bytes(4, "big")), (0x24, (0x22222222).to_bytes(4, "big")), (0x28, (0x33333333).to_bytes(4, "big")))),
        OracleCase("movem-word-reg-mem", "movem", "movem.w d0-d1/a2,(a0)", a=(0x20, 0, 0x55556666), d=(0x11112222, 0x33334444), memory_size=0x40),
        OracleCase("movem-word-mem-reg", "movem", "movem.w (a0),d0-d1/a2", a=(0x20,), memory_size=0x40,
            memory_writes=((0x20, (0x8222).to_bytes(2, "big")), (0x22, (0x0444).to_bytes(2, "big")), (0x24, (0xF666).to_bytes(2, "big")))),
        OracleCase("movem-predec-base", "movem", "movem.l d0/a7,-(a7)", a=(0, 0, 0, 0, 0, 0, 0, 0x30), d=(0x11111111,), memory_size=0x50),
        OracleCase("movem-postinc-base", "movem", "movem.l (a0)+,d0/a0", a=(0x20,), memory_size=0x40,
            memory_writes=((0x20, (0x11111111).to_bytes(4, "big")), (0x24, (0x22222222).to_bytes(4, "big")))),
        OracleCase("movep-word-reg-mem", "movep", "movep.w d0,0(a0)", a=(0x20,), d=(0x11223344,), memory_size=0x40),
        OracleCase("movep-long-reg-mem", "movep", "movep.l d0,0(a0)", a=(0x20,), d=(0x11223344,), memory_size=0x50),
        OracleCase("movep-word-mem-reg", "movep", "movep.w 0(a0),d0", a=(0x20,), memory_size=0x40,
            memory_writes=((0x20, b"\x82"), (0x22, b"\x44"))),
        OracleCase("movep-long-mem-reg", "movep", "movep.l 0(a0),d0", a=(0x20,), memory_size=0x50,
            memory_writes=((0x20, b"\x11"), (0x22, b"\x22"), (0x24, b"\x33"), (0x26, b"\x44"))),
        OracleCase("moves-reg-mem", "special", "moves.l d0,(a0)", cpu="68010", sr=0x2000, a=(0x20,), d=(0x11223344,), memory_size=0x40),
        OracleCase("moves-mem-a1", "special", "moves.l (a0),a1", cpu="68010", sr=0x2000, a=(0x20,), memory_size=0x40,
            memory_writes=((0x20, (0x11223344).to_bytes(4, "big")),)),
        OracleCase("movec-vbr-d0", "special", "movec vbr,d0", cpu="68010", sr=0x2000, c=(("VBR", 0x12345678),), memory_size=0x20),
        OracleCase("movec-d0-vbr", "special", "movec d0,vbr", cpu="68010", sr=0x2000, d=(0x89ABCDEF,), memory_size=0x20),
        OracleCase("move-from-ccr", "special", "move ccr,d0", cpu="68010", sr=0x2015),
        OracleCase("move-to-ccr", "special", "move d0,ccr", d=(0x0000000A,), sr=0x2700, compare_sr=True),
        OracleCase("move-imm-to-ccr", "special", "move #$000a,ccr", cpu="68010", sr=0x2700, compare_sr=True),
        OracleCase("move-from-sr", "special", "move sr,d0", sr=0x2700),
        OracleCase("move-to-sr", "special", "move d0,sr", d=(0x00002713,), sr=0x2000, compare_sr=True),
        OracleCase("move-imm-to-sr", "special", "move #$2100,sr", sr=0x2000, compare_sr=True),
        OracleCase("move-ccr-mem", "special", "move ccr,(a0)", code_hex="42d0", cpu="68010", sr=0x2015, a=(0x20,), memory_size=0x40),
        OracleCase("move-sr-mem", "special", "move sr,(a0)", code_hex="40d0", cpu="68000", sr=0x2700, a=(0x20,), memory_size=0x40),
        OracleCase("move-usp-a0", "special", "move usp,a0", sr=0x2000, c=(("USP", 0x12345678),)),
        OracleCase("move-a0-usp", "special", "move a0,usp", sr=0x2000, a=(0x89ABCDEF,)),
        OracleCase("movec-cacr-d0", "special", "movec cacr,d0", cpu="68020", sr=0x2000, c=(("CACR", 0x13579BDF),), memory_size=0x20),
        OracleCase("movec-d0-cacr", "special", "movec d0,cacr", cpu="68020", sr=0x2000, d=(0x2468ACE0,), memory_size=0x20),
        OracleCase("andi-ccr", "logic", "andi #$0a,ccr", sr=0x201F, compare_sr=True),
        OracleCase("andi-d0", "logic", "andi.l #$00ff00ff,d0", d=(0x1234ABCD,)),
        OracleCase("eor-d0-d1", "logic", "eor.l d0,d1", d=(0x00FF00FF, 0x12345678)),
        OracleCase("eori-sr", "logic", "eori #$0700,sr", sr=0x2700, compare_sr=True),
        OracleCase("ori-d0", "logic", "ori.l #$0000f00f,d0", d=(0x12003400,), compare_sr=True),
        OracleCase("clr-d0-sr", "logic", "clr.l d0", d=(0x12003400,), compare_sr=True),
        OracleCase("neg-w-d0", "unary", "neg.w d0", d=(0x12340080,), compare_sr=True),
        OracleCase("addx-reg", "arith", "addx.l d0,d1", d=(0xFFFFFFFF, 0x00000000), sr=0x0010, compare_sr=True),
        OracleCase("addx-self", "arith", "addx.l d2,d2", d=(0, 0, 0x80000000), sr=0x0010, compare_sr=True),
        OracleCase("subx-reg", "arith", "subx.w d0,d1", d=(0x00000002, 0x00000000), sr=0x0010, compare_sr=True),
        OracleCase("addx-predec", "arith", "addx.l -(a0),-(a1)", a=(0x24, 0x2C), sr=0x0010,
            memory_size=0x40,
            memory_writes=((0x20, (0x00000001).to_bytes(4, "big")), (0x28, (0x00000002).to_bytes(4, "big"))),
            compare_sr=True),
        OracleCase("not-b-d0", "unary", "not.b d0", d=(0x123456A5,), compare_sr=True),
        OracleCase("swap-d0", "unary", "swap d0", d=(0x12345678,), compare_sr=True),
        OracleCase("ext-l-d0", "unary", "ext.l d0", d=(0x00008000,), compare_sr=True),
        OracleCase("ori-sr", "logic", "ori #$0013,sr", sr=0x2000, compare_sr=True),
        OracleCase("asl-imm", "shift", "asl.l #1,d0", d=(0x12345678,), compare_sr=True),
        OracleCase("asr-imm", "shift", "asr.w #1,d0", d=(0x12348000,), compare_sr=True),
        OracleCase("ror-imm", "shift", "ror.w #1,d0", d=(0x00008001,), compare_sr=True),
        OracleCase("rol-reg", "shift", "rol.l d1,d0", d=(0x12345678, 1), compare_sr=True),
        OracleCase("roxl-x", "shift", "roxl.l #1,d0", d=(0x80000000,), sr=0x0010, compare_sr=True),
        OracleCase("roxr-x", "shift", "roxr.w #1,d0", d=(0x00000001,), sr=0x0010, compare_sr=True),
        OracleCase("roxl-zero", "shift", "roxl.l #1,d0", d=(0x00000000,), sr=0x0000, compare_sr=True),
        OracleCase("lsr-mem", "shift", "lsr (a0)", a=(8,), memory_size=16, memory_writes=((8, b"\x80\x01"),), compare_sr=True),
        OracleCase("cmpm-postinc", "compare", "cmpm.b (a0)+,(a1)+", a=(0x20, 0x24), memory_size=0x40, compare_sr=True,
            memory_writes=((0x20, b"\x12"), (0x24, b"\x34"))),
        OracleCase("mulu-basic", "muldiv", "mulu.w d0,d1", d=(3, 4), compare_sr=True),
        OracleCase("muls-basic", "muldiv", "muls.w d0,d1", d=(0xFFFF, 4), compare_sr=True),
        OracleCase("divu-basic", "muldiv", "divu.w d0,d1", d=(3, 8), compare_sr=True),
        OracleCase("divs-basic", "muldiv", "divs.w d0,d1", d=(0xFFFF, 8), compare_sr=True),
        OracleCase("divu-flags", "muldiv", "divu.w d0,d1", d=(8, 0), compare_sr=True),
        OracleCase("divu-overflow", "muldiv", "divu.w d0,d1", d=(2, 0x00080000), compare_sr=True),
        OracleCase("divs-flags", "muldiv", "divs.w d0,d1", d=(2, 0xFFFFFFF8), compare_sr=True),
        OracleCase("divs-overflow", "muldiv", "divs.w d0,d1", d=(0xFFFE, 0x80000000), compare_sr=True),
        OracleCase("chk-basic", "bounds", "chk.w d0,d1", d=(5, 3), compare_sr=True),
        OracleCase("chk2-in-range", "bounds", "chk2.w (a0),d0", cpu="68020", a=(0x20,), d=(5,),
            memory_size=0x40, memory_writes=((0x20, (2).to_bytes(2, "big")), (0x22, (8).to_bytes(2, "big")))),
        OracleCase("cmp2-in-range", "bounds", "cmp2.w (a0),d0", cpu="68020", a=(0x20,), d=(5,),
            memory_size=0x40, memory_writes=((0x20, (2).to_bytes(2, "big")), (0x22, (8).to_bytes(2, "big")))),
        OracleCase("cmp2-flags", "bounds", "cmp2.w (a0),d0", cpu="68020", a=(0x20,), d=(9,), compare_sr=True,
            memory_size=0x40, memory_writes=((0x20, (2).to_bytes(2, "big")), (0x22, (8).to_bytes(2, "big")))),
        OracleCase("cas-basic", "cas", "cas.w d0,d1,(a0)", cpu="68020", d=(0x0011, 0x0022), a=(0x20,), compare_sr=True,
            memory_size=0x40, memory_writes=((0x20, (0x0011).to_bytes(2, "big")),)),
        OracleCase("cas2-basic", "cas", "cas2.w d0:d1,d2:d3,(a0):(a1)", cpu="68020", compare_sr=True,
            d=(0x11, 0x22, 0x33, 0x44), a=(0x20, 0x24), memory_size=0x40,
            memory_writes=((0x20, (0x11).to_bytes(2, "big")), (0x24, (0x22).to_bytes(2, "big")))),
        OracleCase("cas2-fail", "cas", "cas2.w d0:d1,d2:d3,(a0):(a1)", cpu="68020", compare_sr=True,
            d=(0x11, 0x22, 0x33, 0x44), a=(0x20, 0x24), memory_size=0x40,
            memory_writes=((0x20, (0x99).to_bytes(2, "big")), (0x24, (0x22).to_bytes(2, "big")))),
        OracleCase("bfextu-basic", "bf", "bfextu d0{0:8},d1", cpu="68020", d=(0x12345678, 0), compare_sr=True),
        OracleCase("bfexts-basic", "bf", "bfexts d0{0:8},d1", cpu="68020", d=(0x123456F8, 0), compare_sr=True),
        OracleCase("bfins-basic", "bf", "bfins d1,d0{8:8}", cpu="68020", d=(0x12345678, 0x000000AB)),
        OracleCase("bfchg-basic", "bf", "bfchg d0{0:8}", cpu="68020", d=(0x12345678,), compare_sr=True),
        OracleCase("bfclr-basic", "bf", "bfclr d0{8:8}", cpu="68020", d=(0x12345678,), compare_sr=True),
        OracleCase("bfset-basic", "bf", "bfset d0{16:8}", cpu="68020", d=(0x12345678,), compare_sr=True),
        OracleCase("bftst-basic", "bf", "bftst d0{0:8}", cpu="68020", d=(0x12345678,), compare_sr=True),
        OracleCase("bfffo-basic", "bf", "bfffo d0{0:8},d1", cpu="68020", d=(0x12345678, 0), compare_sr=True),
        OracleCase("bfextu-mem", "bf", "bfextu (a0){12:8},d1", cpu="68020", a=(0x20,), d=(0, 0), compare_sr=True,
            memory_size=0x40, memory_writes=((0x20, b"\x12\x34\x56\x78\x9a"),)),
        OracleCase("bfins-mem", "bf", "bfins d1,(a0){8:8}", cpu="68020", a=(0x20,), d=(0, 0xAB),
            memory_size=0x40, memory_writes=((0x20, b"\x12\x34\x56\x78"),)),
        OracleCase("bfclr-mem", "bf", "bfclr (a0){8:8}", cpu="68020", a=(0x20,), compare_sr=True,
            memory_size=0x40, memory_writes=((0x20, b"\x12\x34\x56\x78"),)),
        OracleCase("bfffo-mem", "bf", "bfffo (a0){12:8},d1", cpu="68020", a=(0x20,), d=(0, 0), compare_sr=True,
            memory_size=0x40, memory_writes=((0x20, b"\x12\x34\x56\x78\x9a"),)),
        OracleCase("trapv-clear", "trap", "trapv", sr=0x0000, compare_sr=True),
        OracleCase("pack-dn", "pack", "pack d0,d1,#1", cpu="68020", d=(0x00000102, 0x12345678),
            skip_reason="machine68k marks Dn-form PACK invalid; covered by direct concrete regression"),
        OracleCase("unpk-dn", "pack", "unpk d0,d1,#1", cpu="68020", d=(0x00000012, 0x12345678),
            skip_reason="machine68k marks Dn-form UNPK invalid; covered by direct concrete regression"),
    )


class M68kSimulatorOracleTests(unittest.TestCase):
    def _simulate_memory_and_compare(
        self,
        code: bytes,
        memory: bytes,
        setup: M68kSimConcreteState,
        cpu: str = "68000",
        control_slots: dict[str, int] | None = None,
        compare_sr: bool = False,
    ) -> M68kSimConcreteState:
        state = M68kSimConcreteState()
        ctypes.memmove(ctypes.byref(state), ctypes.byref(setup), ctypes.sizeof(state))
        buf = (ctypes.c_uint8 * len(code)).from_buffer_copy(code)
        mem = (ctypes.c_uint8 * len(memory)).from_buffer_copy(memory)
        result = _disasm_library().m68k_simulate_one_concrete_for_cpu(
            buf, len(code), CPU_BITS[cpu], mem, len(memory), ctypes.byref(state)
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        oracle_setup = M68kSimConcreteState()
        ctypes.memmove(ctypes.byref(oracle_setup), ctypes.byref(setup), ctypes.sizeof(oracle_setup))
        oracle_d, oracle_a, oracle_c, oracle_pc, oracle_sr, oracle_memory, invalid_lines = _run_machine68k_one(
            memory, oracle_setup, cpu, control_slots
        )
        self.assertEqual(invalid_lines, [])
        self.assertEqual(list(state.d), oracle_d)
        self.assertEqual(list(state.a), oracle_a)
        for name, slot in (control_slots or {}).items():
            self.assertEqual(state.c[slot], oracle_c[name], name)
        self.assertEqual(state.pc, oracle_pc)
        if compare_sr:
            self.assertEqual(state.sr, oracle_sr)
        self.assertEqual(bytes(mem), oracle_memory)
        return state

    def _simulate_and_compare(
        self,
        asm_text: str,
        setup: M68kSimConcreteState | None = None,
        cpu: str = "68000",
        control_slots: dict[str, int] | None = None,
        compare_sr: bool = False,
    ) -> M68kSimConcreteState:
        code = _assemble_line_hex(cpu, asm_text)
        memory = code
        state = M68kSimConcreteState()
        if setup is not None:
            ctypes.memmove(ctypes.byref(state), ctypes.byref(setup), ctypes.sizeof(state))
        buf = (ctypes.c_uint8 * len(code)).from_buffer_copy(code)
        mem = (ctypes.c_uint8 * len(memory)).from_buffer_copy(memory)
        result = _disasm_library().m68k_simulate_one_concrete_for_cpu(
            buf, len(code), CPU_BITS[cpu], mem, len(memory), ctypes.byref(state)
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        oracle_setup = M68kSimConcreteState()
        if setup is not None:
            ctypes.memmove(ctypes.byref(oracle_setup), ctypes.byref(setup), ctypes.sizeof(oracle_setup))
        oracle_d, oracle_a, oracle_c, oracle_pc, oracle_sr, oracle_memory, invalid_lines = _run_machine68k_one(
            memory, oracle_setup, cpu, control_slots
        )
        self.assertEqual(invalid_lines, [])
        self.assertEqual(list(state.d), oracle_d)
        self.assertEqual(list(state.a), oracle_a)
        for name, slot in (control_slots or {}).items():
            self.assertEqual(state.c[slot], oracle_c[name], name)
        self.assertEqual(state.pc, oracle_pc)
        if compare_sr:
            self.assertEqual(state.sr, oracle_sr)
        self.assertEqual(bytes(mem), oracle_memory)
        return state

    def _oracle_cases(self) -> list[OracleCase]:
        return list(_oracle_case_cache())

    def _run_oracle_cases(self, cases: list[OracleCase]) -> None:
        for case in cases:
            with self.subTest(case=case.case_id, family=case.family, asm=case.asm_text):
                if case.skip_reason is not None:
                    continue
                code, memory = case.build_code_and_memory()
                state = case.build_state()
                self._simulate_memory_and_compare(
                    code,
                    memory,
                    state,
                    cpu=case.cpu,
                    control_slots=case.control_slots(),
                    compare_sr=case.compare_sr,
                )

    def test_manifest_has_cases(self) -> None:
        self.assertNotEqual(self._oracle_cases(), [])

    def _concrete_exception_entry_matches_machine68k(self) -> None:
        cases = [
            ("68000", "trap #0", 32, 0x40, (), 0, ()),
            ("68010", "trap #15", 47, 0x40, (), 0, ()),
            ("68020", "trap #7", 39, 0x40, (), 0, ()),
            ("68000", "illegal", 4, 0x40, (), 0, ()),
            ("68010", "illegal", 4, 0x40, (), 0, ()),
            ("68020", "illegal", 4, 0x40, (), 0, ()),
            ("68010", "bkpt #0", 4, 0x40, (), 0x2000, ()),
            ("68020", "bkpt #0", 4, 0x40, (), 0x2000, ()),
            ("68000", "trapv", 7, 0x40, (), 0x0002, ()),
            ("68000", "chk.w (a0),d0", 6, 0x40, ((0x60, (2).to_bytes(2, "big")),), 0, (("D0", 9), ("A0", 0x60))),
            ("68020", "chk2.w (a0),d0", 6, 0x40,
                ((0x60, (2).to_bytes(2, "big")), (0x62, (8).to_bytes(2, "big"))), 0, (("D0", 9), ("A0", 0x60))),
            ("68000", "stop #$2700", 8, 0x40, (), 0, ()),
        ]
        for cpu, asm_text, vector, pc, writes, sr, regs in cases:
            with self.subTest(cpu=cpu, asm=asm_text):
                code = _assemble_line_hex(cpu, asm_text)
                memory = bytearray(0x200)
                memory[pc:pc + len(code)] = code
                memory[vector * 4:vector * 4 + 4] = (0x120).to_bytes(4, "big")
                for offset, data in writes:
                    memory[offset:offset + len(data)] = data
                state = M68kSimConcreteState()
                state.pc = pc
                state.sr = sr
                state.a[7] = 0x80
                state.c[SUPPORTED_MACHINE68K_CONTROL_SLOTS["USP"]] = 0x80
                state.c[SUPPORTED_MACHINE68K_CONTROL_SLOTS["ISP"]] = 0xA0
                state.c[SUPPORTED_MACHINE68K_CONTROL_SLOTS["VBR"]] = 0
                for reg_name, value in regs:
                    if reg_name.startswith("D"):
                        state.d[int(reg_name[1:])] = value
                    elif reg_name.startswith("A"):
                        state.a[int(reg_name[1:])] = value
                self._simulate_memory_and_compare(
                    code,
                    bytes(memory),
                    state,
                    cpu=cpu,
                    control_slots={name: SUPPORTED_MACHINE68K_CONTROL_SLOTS[name] for name in ("USP", "ISP", "VBR")},
                    compare_sr=False,
                )

    def test_concrete_trap_admin_limitations_are_explicit(self) -> None:
        cases = [
            ("68000", "reset", None, "unsupported concrete admin instruction"),
            ("68020", "callm #1,(a0)", None, "unsupported concrete admin instruction"),
            ("68040", "cinvl bc,(a0)", None, "unsupported concrete admin instruction"),
            ("68040", "cinvp bc,(a0)", None, "unsupported concrete admin instruction"),
            ("68040", "cinva bc", None, "unsupported concrete admin instruction"),
            ("68040", "cpushl bc,(a0)", None, "unsupported concrete admin instruction"),
            ("68040", "cpushp bc,(a0)", None, "unsupported concrete admin instruction"),
            ("68040", "cpusha bc", None, "unsupported concrete admin instruction"),
            ("68030", "pflusha", None, "unsupported concrete admin instruction"),
            ("68030", "pflush sfc,#0,(a0)", None, "unsupported concrete admin instruction"),
            ("68040", "pflusha", None, "unsupported concrete admin instruction"),
            ("68040", "pflush (a0)", None, "unsupported concrete admin instruction"),
            ("68030", "pflushr (a0)", None, "unsupported concrete admin instruction"),
            ("68030", "ploadr sfc,(a0)", None, "unsupported concrete admin instruction"),
            ("68030", "ploadw sfc,(a0)", None, "unsupported concrete admin instruction"),
            ("68030", "pmove tc,(a0)", None, "unsupported concrete admin instruction"),
            ("68030", "pmove (a0),tc", None, "unsupported concrete admin instruction"),
            ("68030", "ptestw sfc,(a0),#0", None, "unsupported concrete admin instruction"),
            ("68030", "ptestr sfc,(a0),#0,a1", None, "unsupported concrete admin instruction"),
            ("68020", "psave (a0)", None, "unsupported concrete admin instruction"),
            ("68020", "prestore (a0)", None, "unsupported concrete admin instruction"),
            ("68040", "fsave (a0)", None, "unsupported concrete admin instruction"),
            ("68040", "frestore (a0)", None, "unsupported concrete admin instruction"),
        ]
        for cpu, asm_text, code_hex, expected_error in cases:
            with self.subTest(cpu=cpu, asm=asm_text):
                code = bytes.fromhex(code_hex) if code_hex is not None else _assemble_line_hex(cpu, asm_text)
                memory = code
                state = M68kSimConcreteState()
                buf = (ctypes.c_uint8 * len(code)).from_buffer_copy(code)
                mem = (ctypes.c_uint8 * len(memory)).from_buffer_copy(memory)
                result = _disasm_library().m68k_simulate_one_concrete_for_cpu(
                    buf, len(code), CPU_BITS[cpu], mem, len(memory), ctypes.byref(state)
                )
                self.assertTrue(_diag_has_errors(result.diagnostics))
                self.assertIn(expected_error, _diag_message(result.diagnostics))

    def test_concrete_pack_unpk_dn_forms_are_directly_covered(self) -> None:
        cases = [
            ("pack d0,d1,#1", 0x00000102, 0x12345678, 0x12345613),
            ("unpk d0,d1,#1", 0x00000012, 0x12345678, 0x12340103),
        ]
        for asm_text, source_value, dest_before, dest_after in cases:
            with self.subTest(asm=asm_text):
                code = _assemble_line_hex("68020", asm_text)
                state = M68kSimConcreteState()
                state.d[0] = source_value
                state.d[1] = dest_before
                buf = (ctypes.c_uint8 * len(code)).from_buffer_copy(code)
                mem = (ctypes.c_uint8 * len(code)).from_buffer_copy(code)
                result = _disasm_library().m68k_simulate_one_concrete_for_cpu(
                    buf, len(code), CPU_BITS["68020"], mem, len(code), ctypes.byref(state)
                )
                self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
                self.assertEqual(state.d[0], source_value)
                self.assertEqual(state.d[1], dest_after)
                self.assertEqual(state.pc, len(code))
                self.assertEqual(state.sr, 0)

    def _concrete_rte_restore_matches_machine68k(self) -> None:
        cases = [
            ("68000", 0x001F, b"", 0x26, 0x120),
            ("68010", 0x001F, (0x0010).to_bytes(2, "big"), 0x28, 0x120),
            ("68020", 0x001F, (0x2018).to_bytes(2, "big") + (0x9ABCDEF0).to_bytes(4, "big"), 0x2C, 0x120),
            ("68010", 0x201F, (0x0010).to_bytes(2, "big"), 0x28, 0x28),
            ("68020", 0x201F, (0x2018).to_bytes(2, "big") + (0x9ABCDEF0).to_bytes(4, "big"), 0x2C, 0x2C),
        ]
        for cpu, restored_sr, trailer, expected_isp, expected_a7 in cases:
            with self.subTest(cpu=cpu, restored_sr=hex(restored_sr)):
                code = _assemble_line_hex(cpu, "rte")
                memory = bytearray(0x200)
                memory[0x40:0x40 + len(code)] = code
                frame = (restored_sr).to_bytes(2, "big") + (0x12345678).to_bytes(4, "big") + trailer
                memory[0x20:0x20 + len(frame)] = frame
                state = M68kSimConcreteState()
                state.pc = 0x40
                state.sr = 0x2000
                state.a[7] = 0x20
                state.c[SUPPORTED_MACHINE68K_CONTROL_SLOTS["USP"]] = 0x120
                state.c[SUPPORTED_MACHINE68K_CONTROL_SLOTS["ISP"]] = 0x20
                state.c[SUPPORTED_MACHINE68K_CONTROL_SLOTS["VBR"]] = 0
                result = self._simulate_memory_and_compare(
                    code,
                    bytes(memory),
                    state,
                    cpu=cpu,
                    control_slots={name: SUPPORTED_MACHINE68K_CONTROL_SLOTS[name] for name in ("USP", "ISP", "VBR")},
                    compare_sr=True,
                )
                self.assertEqual(result.pc, 0x12345678)
                self.assertEqual(result.c[SUPPORTED_MACHINE68K_CONTROL_SLOTS["ISP"]], expected_isp)
                self.assertEqual(result.a[7], expected_a7)

    def test_bulk_oracle_manifest_smoke(self) -> None:
        smoke_ids = {
            "moveq-basic",
            "lea-indexed",
            "movem-predec",
            "move-to-sr",
            "move-imm-to-ccr",
            "move-imm-to-sr",
            "addx-self",
            "addx-predec",
            "roxl-x",
        }
        cases = [case for case in self._oracle_cases() if case.case_id in smoke_ids]
        self._run_oracle_cases(cases)


if __name__ == "__main__":
    unittest.main()
