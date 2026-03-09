"""Extend m68k_instructions.json with structured fields.

Adds:
  - processor_min: "68000", "68010", "68020", etc.
  - sizes: ["b"], ["w","l"], ["b","w","l"], [] for unsized
  - test_cases: [{"asm": "...", "desc": "..."}, ...]

This is a one-time migration script. Run once, verify, commit.
"""

import json
import re
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
KB_PATH = PROJ_ROOT / "knowledge" / "m68k_instructions.json"

# Map from test suite mnemonic keys to test cases
# Migrated from test_m68k_roundtrip.py TEST_CASES_68000
TEST_CASES = {
    "ABCD": [
        ("abcd d0,d1", "register"),
        ("abcd -(a0),-(a1)", "memory"),
    ],
    "ADD": [
        ("add.b d0,d1", "byte reg-reg"),
        ("add.w d0,d1", "word reg-reg"),
        ("add.l d0,d1", "long reg-reg"),
        ("add.w (a0),d1", "memory to reg"),
        ("add.l d0,(a0)", "reg to memory"),
        ("add.w #$1234,d0", "immediate"),
        ("add.l #$12345678,d0", "long immediate"),
    ],
    "ADDA": [
        ("adda.w d0,a0", "word"),
        ("adda.l d0,a0", "long"),
        ("adda.l #$1000,a0", "immediate"),
    ],
    "ADDI": [
        ("addi.b #$12,d0", "byte"),
        ("addi.w #$1234,d0", "word"),
        ("addi.l #$12345678,d0", "long"),
        ("addi.w #$10,(a0)", "memory"),
    ],
    "ADDQ": [
        ("addq.b #1,d0", "byte min"),
        ("addq.l #8,d0", "long max"),
        ("addq.w #3,(a0)", "memory"),
        ("addq.l #1,a0", "address reg"),
    ],
    "ADDX": [
        ("addx.b d0,d1", "byte reg"),
        ("addx.w d0,d1", "word reg"),
        ("addx.l d0,d1", "long reg"),
        ("addx.l -(a0),-(a1)", "memory"),
    ],
    "AND": [
        ("and.b d0,d1", "byte"),
        ("and.w d0,d1", "word"),
        ("and.l d0,d1", "long"),
        ("and.w (a0),d1", "memory to reg"),
        ("and.l d0,(a0)", "reg to memory"),
    ],
    "ANDI": [
        ("andi.b #$ff,d0", "byte"),
        ("andi.w #$ff00,d0", "word"),
        ("andi.l #$ff00ff00,d0", "long"),
    ],
    "ANDI to CCR": [
        ("andi.b #$1f,ccr", ""),
    ],
    "ANDI to SR": [
        ("andi.w #$f8ff,sr", ""),
    ],
    "ASL, ASR": [
        ("asl.b #1,d0", "byte imm"),
        ("asl.w #4,d0", "word imm"),
        ("asl.l #8,d0", "long imm"),
        ("asl.l d1,d0", "register count"),
        ("asr.b #1,d0", "right byte"),
        ("asr.w #4,d0", "right word"),
        ("asr.l d1,d0", "right reg count"),
        ("asl.w (a0)", "memory left"),
        ("asr.w (a0)", "memory right"),
    ],
    "Bcc": [
        ("beq.s .t\nnop\n.t:", "equal short"),
        ("bne.s .t\nnop\n.t:", "not equal short"),
        ("bgt.s .t\nnop\n.t:", "greater short"),
        ("bge.s .t\nnop\n.t:", "greater/equal short"),
        ("blt.s .t\nnop\n.t:", "less short"),
        ("ble.s .t\nnop\n.t:", "less/equal short"),
        ("bhi.s .t\nnop\n.t:", "higher short"),
        ("bls.s .t\nnop\n.t:", "lower/same short"),
        ("bcc.s .t\nnop\n.t:", "carry clear short"),
        ("bcs.s .t\nnop\n.t:", "carry set short"),
        ("bpl.s .t\nnop\n.t:", "plus short"),
        ("bmi.s .t\nnop\n.t:", "minus short"),
        ("bvc.s .t\nnop\n.t:", "overflow clear short"),
        ("bvs.s .t\nnop\n.t:", "overflow set short"),
        ("beq.w .t\n.t:", "equal word"),
    ],
    "BCHG": [
        ("bchg d0,d1", "dynamic reg"),
        ("bchg #7,d0", "static reg"),
        ("bchg d0,(a0)", "dynamic mem"),
        ("bchg #3,(a0)", "static mem"),
    ],
    "BCLR": [
        ("bclr d0,d1", "dynamic reg"),
        ("bclr #31,d0", "static reg"),
        ("bclr d0,(a0)", "dynamic mem"),
        ("bclr #7,(a0)", "static mem"),
    ],
    "BRA": [
        ("bra.s .t\nnop\n.t:", "short"),
        ("bra.w .t\n.t:", "word"),
    ],
    "BSET": [
        ("bset d0,d1", "dynamic reg"),
        ("bset #0,d0", "static reg"),
        ("bset d0,(a0)", "dynamic mem"),
        ("bset #0,(a0)", "static mem"),
    ],
    "BSR": [
        ("bsr.s .t\nnop\n.t:", "short"),
        ("bsr.w .t\n.t:", "word"),
    ],
    "BTST": [
        ("btst d0,d1", "dynamic reg"),
        ("btst #7,d0", "static reg"),
        ("btst d0,(a0)", "dynamic mem"),
        ("btst #7,(a0)", "static mem"),
    ],
    "CHK": [
        ("chk d0,d1", "register"),
        ("chk (a0),d1", "memory"),
    ],
    "CLR": [
        ("clr.b d0", "byte reg"),
        ("clr.w d0", "word reg"),
        ("clr.l d0", "long reg"),
        ("clr.w (a0)", "memory"),
    ],
    "CMP": [
        ("cmp.b d0,d1", "byte"),
        ("cmp.w d0,d1", "word"),
        ("cmp.l d0,d1", "long"),
        ("cmp.w (a0),d1", "memory"),
        ("cmp.l #$1234,d0", "immediate"),
    ],
    "CMPA": [
        ("cmpa.w d0,a0", "word"),
        ("cmpa.l d0,a0", "long"),
        ("cmpa.l #$1000,a0", "immediate"),
    ],
    "CMPI": [
        ("cmpi.b #$12,d0", "byte"),
        ("cmpi.w #$1234,d0", "word"),
        ("cmpi.l #$12345678,d0", "long"),
    ],
    "CMPM": [
        ("cmpm.b (a0)+,(a1)+", "byte"),
        ("cmpm.w (a0)+,(a1)+", "word"),
        ("cmpm.l (a0)+,(a1)+", "long"),
    ],
    "DBcc": [
        ("dbf d0,.t\n.t:", "false (= dbra)"),
        ("dbeq d0,.t\n.t:", "equal"),
        ("dbne d0,.t\n.t:", "not equal"),
        ("dbhi d0,.t\n.t:", "higher"),
    ],
    "DIVS, DIVSL": [
        ("divs.w d1,d0", "register"),
        ("divs.w (a0),d0", "memory"),
    ],
    "DIVU, DIVUL": [
        ("divu.w d1,d0", "register"),
        ("divu.w (a0),d0", "memory"),
    ],
    "EOR": [
        ("eor.b d0,d1", "byte"),
        ("eor.w d0,d1", "word"),
        ("eor.l d0,d1", "long"),
        ("eor.l d0,(a0)", "memory"),
    ],
    "EORI": [
        ("eori.b #$ff,d0", "byte"),
        ("eori.w #$ffff,d0", "word"),
        ("eori.l #$ffffffff,d0", "long"),
    ],
    "EORI to CCR": [
        ("eori.b #$1f,ccr", ""),
    ],
    "EORI to SR": [
        ("eori.w #$0700,sr", ""),
    ],
    "EXG": [
        ("exg d0,d1", "data-data"),
        ("exg a0,a1", "addr-addr"),
        ("exg d0,a0", "data-addr"),
    ],
    "EXT, EXTB": [
        ("ext.w d0", "byte to word"),
        ("ext.l d0", "word to long"),
    ],
    "ILLEGAL": [
        ("illegal", ""),
    ],
    "JMP": [
        ("jmp (a0)", "indirect"),
        ("jmp 4(a0)", "displacement"),
    ],
    "JSR": [
        ("jsr (a0)", "indirect"),
        ("jsr -198(a6)", "LVO call"),
    ],
    "LEA": [
        ("lea (a0),a1", "indirect"),
        ("lea 4(a0),a1", "displacement"),
        ("lea 0(a0,d0.w),a1", "index"),
    ],
    "LINK": [
        ("link a6,#-100", "negative"),
        ("link a5,#0", "zero"),
    ],
    "LSL, LSR": [
        ("lsl.b #1,d0", "byte imm"),
        ("lsl.w #4,d0", "word imm"),
        ("lsl.l #8,d0", "long imm"),
        ("lsl.l d1,d0", "register count"),
        ("lsr.b #1,d0", "right byte"),
        ("lsr.l d1,d0", "right reg count"),
        ("lsl.w (a0)", "memory left"),
        ("lsr.w (a0)", "memory right"),
    ],
    "MOVE": [
        ("move.b d0,d1", "byte reg-reg"),
        ("move.w d0,d1", "word reg-reg"),
        ("move.l d0,d1", "long reg-reg"),
        ("move.l (a0),d0", "mem to reg"),
        ("move.l d0,(a0)", "reg to mem"),
        ("move.w (a0)+,d0", "postinc"),
        ("move.l -(a0),d0", "predec"),
        ("move.w 4(a0),d0", "displacement"),
        ("move.l 0(a0,d0.w),d1", "index"),
        ("move.w $4.w,d0", "abs short"),
        ("move.l $00fc0000,d0", "abs long"),
        ("move.l #$12345678,d0", "immediate"),
    ],
    "MOVEA": [
        ("movea.w d0,a0", "word"),
        ("movea.l d0,a0", "long"),
        ("movea.l (a0),a1", "memory"),
    ],
    "MOVE from SR": [
        ("move.w sr,d0", "to reg"),
        ("move.w sr,(a0)", "to memory"),
    ],
    "MOVE to CCR": [
        ("move.w d0,ccr", "from reg"),
    ],
    "MOVE to SR": [
        ("move.w d0,sr", "from reg"),
    ],
    "MOVE USP": [
        ("move.l a0,usp", "to usp"),
        ("move.l usp,a0", "from usp"),
    ],
    "MOVEM": [
        ("movem.l d0-d7/a0-a6,-(sp)", "save all"),
        ("movem.l (sp)+,d0-d7/a0-a6", "restore all"),
        ("movem.w d0-d3,-(sp)", "save partial word"),
        ("movem.w (sp)+,d0-d3", "restore partial word"),
        ("movem.l d0/d2/a0/a3,-(sp)", "save sparse"),
        ("movem.l (sp)+,d0/d2/a0/a3", "restore sparse"),
    ],
    "MOVEP": [
        ("movep.w 0(a0),d0", "word mem to reg"),
        ("movep.l 0(a0),d0", "long mem to reg"),
        ("movep.w d0,0(a0)", "word reg to mem"),
        ("movep.l d0,0(a0)", "long reg to mem"),
    ],
    "MOVEQ": [
        ("moveq #0,d0", "zero"),
        ("moveq #127,d0", "max positive"),
        ("moveq #-128,d0", "max negative"),
        ("moveq #-1,d0", "minus one"),
    ],
    "MULS": [
        ("muls.w d0,d1", "register"),
        ("muls.w (a0),d1", "memory"),
    ],
    "MULU": [
        ("mulu.w d0,d1", "register"),
        ("mulu.w (a0),d1", "memory"),
    ],
    "NBCD": [
        ("nbcd d0", "register"),
        ("nbcd (a0)", "memory"),
    ],
    "NEG": [
        ("neg.b d0", "byte"),
        ("neg.w d0", "word"),
        ("neg.l d0", "long"),
        ("neg.w (a0)", "memory"),
    ],
    "NEGX": [
        ("negx.b d0", "byte"),
        ("negx.w d0", "word"),
        ("negx.l d0", "long"),
    ],
    "NOP": [
        ("nop", ""),
    ],
    "NOT": [
        ("not.b d0", "byte"),
        ("not.w d0", "word"),
        ("not.l d0", "long"),
        ("not.w (a0)", "memory"),
    ],
    "OR": [
        ("or.b d0,d1", "byte"),
        ("or.w d0,d1", "word"),
        ("or.l d0,d1", "long"),
        ("or.w (a0),d1", "memory to reg"),
        ("or.l d0,(a0)", "reg to memory"),
    ],
    "ORI": [
        ("ori.b #$ff,d0", "byte"),
        ("ori.w #$ff00,d0", "word"),
        ("ori.l #$ff00ff00,d0", "long"),
    ],
    "ORI to CCR": [
        ("ori.b #$1f,ccr", ""),
    ],
    "ORI to SR": [
        ("ori.w #$0700,sr", ""),
    ],
    "PEA": [
        ("pea (a0)", "indirect"),
        ("pea 4(a0)", "displacement"),
    ],
    "RESET": [
        ("reset", ""),
    ],
    "ROL, ROR": [
        ("rol.b #1,d0", "byte imm"),
        ("rol.w #4,d0", "word imm"),
        ("rol.l d1,d0", "register count"),
        ("ror.b #1,d0", "right byte"),
        ("ror.l d1,d0", "right reg count"),
        ("rol.w (a0)", "memory left"),
        ("ror.w (a0)", "memory right"),
    ],
    "RTE": [
        ("rte", ""),
    ],
    "RTR": [
        ("rtr", ""),
    ],
    "RTS": [
        ("rts", ""),
    ],
    "SBCD": [
        ("sbcd d0,d1", "register"),
        ("sbcd -(a0),-(a1)", "memory"),
    ],
    "Scc": [
        ("st d0", "true"),
        ("sf d0", "false"),
        ("seq d0", "equal"),
        ("sne d0", "not equal"),
        ("sgt d0", "greater"),
        ("slt d0", "less"),
        ("shi d0", "higher"),
        ("scc d0", "carry clear"),
        ("scs d0", "carry set"),
    ],
    "STOP": [
        ("stop #$2000", ""),
    ],
    "SUB": [
        ("sub.b d0,d1", "byte"),
        ("sub.w d0,d1", "word"),
        ("sub.l d0,d1", "long"),
        ("sub.w (a0),d1", "memory to reg"),
        ("sub.l d0,(a0)", "reg to memory"),
    ],
    "SUBA": [
        ("suba.w d0,a0", "word"),
        ("suba.l d0,a0", "long"),
    ],
    "SUBI": [
        ("subi.b #$12,d0", "byte"),
        ("subi.w #$1234,d0", "word"),
        ("subi.l #$12345678,d0", "long"),
    ],
    "SUBQ": [
        ("subq.b #1,d0", "byte min"),
        ("subq.l #8,d0", "long max"),
        ("subq.w #3,(a0)", "memory"),
    ],
    "SUBX": [
        ("subx.b d0,d1", "byte reg"),
        ("subx.w d0,d1", "word reg"),
        ("subx.l d0,d1", "long reg"),
        ("subx.l -(a0),-(a1)", "memory"),
    ],
    "SWAP": [
        ("swap d0", ""),
        ("swap d7", "d7"),
    ],
    "TAS": [
        ("tas d0", "register"),
        ("tas (a0)", "memory"),
    ],
    "TRAP": [
        ("trap #0", "min"),
        ("trap #15", "max"),
    ],
    "TRAPV": [
        ("trapv", ""),
    ],
    "TST": [
        ("tst.b d0", "byte reg"),
        ("tst.w d0", "word reg"),
        ("tst.l d0", "long reg"),
        ("tst.w (a0)", "memory"),
    ],
    "UNLK": [
        ("unlk a6", ""),
        ("unlk a5", "a5"),
    ],
    "ROXL, ROXR": [
        ("roxl.b #1,d0", "byte imm"),
        ("roxl.w #4,d0", "word imm"),
        ("roxl.l d1,d0", "register count"),
        ("roxr.b #1,d0", "right byte"),
        ("roxr.l d1,d0", "right reg count"),
        ("roxl.w (a0)", "memory left"),
        ("roxr.w (a0)", "memory right"),
    ],
}


def parse_processor_min(proc_str: str) -> str:
    """Extract minimum processor from processors string."""
    if not proc_str:
        return "68000"
    if "M68000 Family" in proc_str:
        return "68000"
    if "MC68000" in proc_str or "MC68008" in proc_str:
        return "68000"
    if "MC68EC000" in proc_str:
        return "68000"  # EC000 is basically 68000
    if "MC68010" in proc_str:
        return "68010"
    if "MC68020" in proc_str:
        return "68020"
    if "MC68030" in proc_str:
        return "68030"
    if "MC68040" in proc_str:
        return "68040"
    if "MC68060" in proc_str:
        return "68060"
    if "MC68881" in proc_str or "MC68882" in proc_str:
        return "68881"
    if "MC68851" in proc_str or "M68851" in proc_str:
        return "68851"
    if "CPU32" in proc_str:
        return "cpu32"
    return "68000"


def parse_sizes(attrs_str: str) -> list[str]:
    """Extract structured size list from attributes string."""
    if not attrs_str:
        return []
    # "Size = (Byte, Word, Long)" -> ["b", "w", "l"]
    # "Unsized" -> []
    # "Size = (Byte, Word, Long*)" -> ["b", "w", "l"]  (* = 68020+ only)
    m = re.search(r"Size\s*=\s*\(([^)]+)\)", attrs_str, re.IGNORECASE)
    if not m:
        return []
    size_str = m.group(1)
    sizes = []
    for part in size_str.split(","):
        part = part.strip().rstrip("*").strip().lower()
        if part == "byte":
            sizes.append("b")
        elif part == "word":
            sizes.append("w")
        elif part == "long":
            sizes.append("l")
        elif part == "quad":
            sizes.append("q")
        elif part == "line":
            sizes.append("line")
    return sizes


def main():
    with open(KB_PATH, encoding="utf-8") as f:
        data = json.load(f)

    for inst in data:
        mnemonic = inst["mnemonic"]

        # Add processor_min
        inst["processor_min"] = parse_processor_min(inst.get("processors", ""))

        # Add structured sizes
        inst["sizes"] = parse_sizes(inst.get("attributes", ""))

        # Add test_cases from our hand-written set
        if mnemonic in TEST_CASES:
            inst["test_cases"] = [
                {"asm": asm, "desc": desc}
                for asm, desc in TEST_CASES[mnemonic]
            ]
        else:
            inst["test_cases"] = []

    # Check for ROXL, ROXR which is in our tests but may not be in KB
    kb_mnemonics = {inst["mnemonic"] for inst in data}
    for tc_mnemonic in TEST_CASES:
        if tc_mnemonic not in kb_mnemonics:
            print(f"WARNING: test mnemonic '{tc_mnemonic}' not in KB")

    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Summary
    total = len(data)
    with_tests = sum(1 for inst in data if inst["test_cases"])
    total_tests = sum(len(inst["test_cases"]) for inst in data)
    m68000 = sum(1 for inst in data if inst["processor_min"] == "68000")

    print(f"Updated {total} instructions")
    print(f"  {with_tests} with test cases ({total_tests} total tests)")
    print(f"  {m68000} are 68000-level")
    print(f"  Sizes: {sum(1 for i in data if i['sizes'])} with sizes, "
          f"{sum(1 for i in data if not i['sizes'])} unsized")


if __name__ == "__main__":
    main()
