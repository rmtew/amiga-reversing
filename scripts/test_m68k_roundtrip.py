"""M68K disassembler round-trip test suite.

For each 68000 instruction, assembles with vasm, disassembles with our
disassembler, reassembles, and checks binary identity.

Also reconciles coverage against knowledge/m68k_instructions.json.
"""

import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

# Resolve paths relative to project root
PROJ_ROOT = Path(__file__).resolve().parent.parent
VASM = PROJ_ROOT / "tools" / "vasmm68k_mot.exe"
KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"

sys.path.insert(0, str(PROJ_ROOT / "scripts"))
from hunk_parser import parse_file, HunkType
from m68k_disasm import disassemble


# ---------------------------------------------------------------------------
# Test case definitions: mnemonic -> list of (assembly_line, description)
# Each test case is a single instruction line in Motorola syntax.
# We group by mnemonic matching the knowledge base.
# ---------------------------------------------------------------------------

# 68000 instructions only (no 020+, no FPU, no MMU, no coprocessor)
TEST_CASES_68000 = {
    "ABCD": [
        ("abcd    d0,d1", "register"),
        ("abcd    -(a0),-(a1)", "memory"),
    ],
    "ADD": [
        ("add.b   d0,d1", "byte reg-reg"),
        ("add.w   d0,d1", "word reg-reg"),
        ("add.l   d0,d1", "long reg-reg"),
        ("add.w   (a0),d1", "memory to reg"),
        ("add.l   d0,(a0)", "reg to memory"),
        ("add.w   #$1234,d0", "immediate"),
        ("add.l   #$12345678,d0", "long immediate"),
    ],
    "ADDA": [
        ("adda.w  d0,a0", "word"),
        ("adda.l  d0,a0", "long"),
        ("adda.l  #$1000,a0", "immediate"),
    ],
    "ADDI": [
        ("addi.b  #$12,d0", "byte"),
        ("addi.w  #$1234,d0", "word"),
        ("addi.l  #$12345678,d0", "long"),
        ("addi.w  #$10,(a0)", "memory"),
    ],
    "ADDQ": [
        ("addq.b  #1,d0", "byte min"),
        ("addq.l  #8,d0", "long max"),
        ("addq.w  #3,(a0)", "memory"),
        ("addq.l  #1,a0", "address reg"),
    ],
    "ADDX": [
        ("addx.b  d0,d1", "byte reg"),
        ("addx.w  d0,d1", "word reg"),
        ("addx.l  d0,d1", "long reg"),
        ("addx.l  -(a0),-(a1)", "memory"),
    ],
    "AND": [
        ("and.b   d0,d1", "byte"),
        ("and.w   d0,d1", "word"),
        ("and.l   d0,d1", "long"),
        ("and.w   (a0),d1", "memory to reg"),
        ("and.l   d0,(a0)", "reg to memory"),
    ],
    "ANDI": [
        ("andi.b  #$ff,d0", "byte"),
        ("andi.w  #$ff00,d0", "word"),
        ("andi.l  #$ff00ff00,d0", "long"),
    ],
    "ANDI to CCR": [
        ("andi.b  #$1f,ccr", ""),
    ],
    "ANDI to SR": [
        ("andi.w  #$f8ff,sr", ""),
    ],
    "ASL, ASR": [
        ("asl.b   #1,d0", "byte imm"),
        ("asl.w   #4,d0", "word imm"),
        ("asl.l   #8,d0", "long imm"),
        ("asl.l   d1,d0", "register count"),
        ("asr.b   #1,d0", "right byte"),
        ("asr.w   #4,d0", "right word"),
        ("asr.l   d1,d0", "right reg count"),
        ("asl.w   (a0)", "memory left"),
        ("asr.w   (a0)", "memory right"),
    ],
    "Bcc": [
        ("beq.s   .t\nnop\n.t:", "equal short"),
        ("bne.s   .t\nnop\n.t:", "not equal short"),
        ("bgt.s   .t\nnop\n.t:", "greater short"),
        ("bge.s   .t\nnop\n.t:", "greater/equal short"),
        ("blt.s   .t\nnop\n.t:", "less short"),
        ("ble.s   .t\nnop\n.t:", "less/equal short"),
        ("bhi.s   .t\nnop\n.t:", "higher short"),
        ("bls.s   .t\nnop\n.t:", "lower/same short"),
        ("bcc.s   .t\nnop\n.t:", "carry clear short"),
        ("bcs.s   .t\nnop\n.t:", "carry set short"),
        ("bpl.s   .t\nnop\n.t:", "plus short"),
        ("bmi.s   .t\nnop\n.t:", "minus short"),
        ("bvc.s   .t\nnop\n.t:", "overflow clear short"),
        ("bvs.s   .t\nnop\n.t:", "overflow set short"),
        ("beq.w   .t\n.t:", "equal word"),
    ],
    "BCHG": [
        ("bchg    d0,d1", "dynamic reg"),
        ("bchg    #7,d0", "static reg"),
        ("bchg    d0,(a0)", "dynamic mem"),
        ("bchg    #3,(a0)", "static mem"),
    ],
    "BCLR": [
        ("bclr    d0,d1", "dynamic reg"),
        ("bclr    #31,d0", "static reg"),
        ("bclr    d0,(a0)", "dynamic mem"),
        ("bclr    #7,(a0)", "static mem"),
    ],
    "BSET": [
        ("bset    d0,d1", "dynamic reg"),
        ("bset    #0,d0", "static reg"),
        ("bset    d0,(a0)", "dynamic mem"),
        ("bset    #0,(a0)", "static mem"),
    ],
    "BTST": [
        ("btst    d0,d1", "dynamic reg"),
        ("btst    #7,d0", "static reg"),
        ("btst    d0,(a0)", "dynamic mem"),
        ("btst    #7,(a0)", "static mem"),
    ],
    "BRA": [
        ("bra.s   .t\nnop\n.t:", "short"),
        ("bra.w   .t\n.t:", "word"),
    ],
    "BSR": [
        ("bsr.s   .t\nnop\n.t:", "short"),
        ("bsr.w   .t\n.t:", "word"),
    ],
    "CHK": [
        ("chk     d0,d1", "register"),
        ("chk     (a0),d1", "memory"),
    ],
    "CLR": [
        ("clr.b   d0", "byte reg"),
        ("clr.w   d0", "word reg"),
        ("clr.l   d0", "long reg"),
        ("clr.w   (a0)", "memory"),
    ],
    "CMP": [
        ("cmp.b   d0,d1", "byte"),
        ("cmp.w   d0,d1", "word"),
        ("cmp.l   d0,d1", "long"),
        ("cmp.w   (a0),d1", "memory"),
        ("cmp.l   #$1234,d0", "immediate"),
    ],
    "CMPA": [
        ("cmpa.w  d0,a0", "word"),
        ("cmpa.l  d0,a0", "long"),
        ("cmpa.l  #$1000,a0", "immediate"),
    ],
    "CMPI": [
        ("cmpi.b  #$12,d0", "byte"),
        ("cmpi.w  #$1234,d0", "word"),
        ("cmpi.l  #$12345678,d0", "long"),
    ],
    "CMPM": [
        ("cmpm.b  (a0)+,(a1)+", "byte"),
        ("cmpm.w  (a0)+,(a1)+", "word"),
        ("cmpm.l  (a0)+,(a1)+", "long"),
    ],
    "DBcc": [
        ("dbf     d0,.t\n.t:", "false (= dbra)"),
        ("dbeq    d0,.t\n.t:", "equal"),
        ("dbne    d0,.t\n.t:", "not equal"),
        ("dbhi    d0,.t\n.t:", "higher"),
    ],
    "DIVS, DIVSL": [
        ("divs.w  d1,d0", "register"),
        ("divs.w  (a0),d0", "memory"),
    ],
    "DIVU, DIVUL": [
        ("divu.w  d1,d0", "register"),
        ("divu.w  (a0),d0", "memory"),
    ],
    "EOR": [
        ("eor.b   d0,d1", "byte"),
        ("eor.w   d0,d1", "word"),
        ("eor.l   d0,d1", "long"),
        ("eor.l   d0,(a0)", "memory"),
    ],
    "EORI": [
        ("eori.b  #$ff,d0", "byte"),
        ("eori.w  #$ffff,d0", "word"),
        ("eori.l  #$ffffffff,d0", "long"),
    ],
    "EORI to CCR": [
        ("eori.b  #$1f,ccr", ""),
    ],
    "EORI to SR": [
        ("eori.w  #$0700,sr", ""),
    ],
    "EXG": [
        ("exg     d0,d1", "data-data"),
        ("exg     a0,a1", "addr-addr"),
        ("exg     d0,a0", "data-addr"),
    ],
    "EXT, EXTB": [
        ("ext.w   d0", "byte to word"),
        ("ext.l   d0", "word to long"),
    ],
    "ILLEGAL": [
        ("illegal", ""),
    ],
    "JMP": [
        ("jmp     (a0)", "indirect"),
        ("jmp     4(a0)", "displacement"),
    ],
    "JSR": [
        ("jsr     (a0)", "indirect"),
        ("jsr     -198(a6)", "LVO call"),
    ],
    "LEA": [
        ("lea     (a0),a1", "indirect"),
        ("lea     4(a0),a1", "displacement"),
        ("lea     0(a0,d0.w),a1", "index"),
    ],
    "LINK": [
        ("link    a6,#-100", "negative"),
        ("link    a5,#0", "zero"),
    ],
    "LSL, LSR": [
        ("lsl.b   #1,d0", "byte imm"),
        ("lsl.w   #4,d0", "word imm"),
        ("lsl.l   #8,d0", "long imm"),
        ("lsl.l   d1,d0", "register count"),
        ("lsr.b   #1,d0", "right byte"),
        ("lsr.l   d1,d0", "right reg count"),
        ("lsl.w   (a0)", "memory left"),
        ("lsr.w   (a0)", "memory right"),
    ],
    "MOVE": [
        ("move.b  d0,d1", "byte reg-reg"),
        ("move.w  d0,d1", "word reg-reg"),
        ("move.l  d0,d1", "long reg-reg"),
        ("move.l  (a0),d0", "mem to reg"),
        ("move.l  d0,(a0)", "reg to mem"),
        ("move.w  (a0)+,d0", "postinc"),
        ("move.l  -(a0),d0", "predec"),
        ("move.w  4(a0),d0", "displacement"),
        ("move.l  0(a0,d0.w),d1", "index"),
        ("move.w  $4.w,d0", "abs short"),
        ("move.l  $00fc0000,d0", "abs long"),
        ("move.l  #$12345678,d0", "immediate"),
    ],
    "MOVEA": [
        ("movea.w d0,a0", "word"),
        ("movea.l d0,a0", "long"),
        ("movea.l (a0),a1", "memory"),
    ],
    "MOVE from CCR": [
        # 68010+ only, skip for 68000
    ],
    "MOVE from SR": [
        ("move.w  sr,d0", "to reg"),
        ("move.w  sr,(a0)", "to memory"),
    ],
    "MOVE to CCR": [
        ("move.w  d0,ccr", "from reg"),
    ],
    "MOVE to SR": [
        ("move.w  d0,sr", "from reg"),
    ],
    "MOVE USP": [
        ("move.l  a0,usp", "to usp"),
        ("move.l  usp,a0", "from usp"),
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
        ("moveq   #0,d0", "zero"),
        ("moveq   #127,d0", "max positive"),
        ("moveq   #-128,d0", "max negative"),
        ("moveq   #-1,d0", "minus one"),
    ],
    "MULS": [
        ("muls.w  d0,d1", "register"),
        ("muls.w  (a0),d1", "memory"),
    ],
    "MULU": [
        ("mulu.w  d0,d1", "register"),
        ("mulu.w  (a0),d1", "memory"),
    ],
    "NBCD": [
        ("nbcd    d0", "register"),
        ("nbcd    (a0)", "memory"),
    ],
    "NEG": [
        ("neg.b   d0", "byte"),
        ("neg.w   d0", "word"),
        ("neg.l   d0", "long"),
        ("neg.w   (a0)", "memory"),
    ],
    "NEGX": [
        ("negx.b  d0", "byte"),
        ("negx.w  d0", "word"),
        ("negx.l  d0", "long"),
    ],
    "NOP": [
        ("nop", ""),
    ],
    "NOT": [
        ("not.b   d0", "byte"),
        ("not.w   d0", "word"),
        ("not.l   d0", "long"),
        ("not.w   (a0)", "memory"),
    ],
    "OR": [
        ("or.b    d0,d1", "byte"),
        ("or.w    d0,d1", "word"),
        ("or.l    d0,d1", "long"),
        ("or.w    (a0),d1", "memory to reg"),
        ("or.l    d0,(a0)", "reg to memory"),
    ],
    "ORI": [
        ("ori.b   #$ff,d0", "byte"),
        ("ori.w   #$ff00,d0", "word"),
        ("ori.l   #$ff00ff00,d0", "long"),
    ],
    "ORI to CCR": [
        ("ori.b   #$1f,ccr", ""),
    ],
    "ORI to SR": [
        ("ori.w   #$0700,sr", ""),
    ],
    "PEA": [
        ("pea     (a0)", "indirect"),
        ("pea     4(a0)", "displacement"),
    ],
    "RESET": [
        ("reset", ""),
    ],
    "ROL, ROR": [
        ("rol.b   #1,d0", "byte imm"),
        ("rol.w   #4,d0", "word imm"),
        ("rol.l   d1,d0", "register count"),
        ("ror.b   #1,d0", "right byte"),
        ("ror.l   d1,d0", "right reg count"),
        ("rol.w   (a0)", "memory left"),
        ("ror.w   (a0)", "memory right"),
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
        ("sbcd    d0,d1", "register"),
        ("sbcd    -(a0),-(a1)", "memory"),
    ],
    "Scc": [
        ("st      d0", "true"),
        ("sf      d0", "false"),
        ("seq     d0", "equal"),
        ("sne     d0", "not equal"),
        ("sgt     d0", "greater"),
        ("slt     d0", "less"),
        ("shi     d0", "higher"),
        ("scc     d0", "carry clear"),
        ("scs     d0", "carry set"),
    ],
    "STOP": [
        ("stop    #$2000", ""),
    ],
    "SUB": [
        ("sub.b   d0,d1", "byte"),
        ("sub.w   d0,d1", "word"),
        ("sub.l   d0,d1", "long"),
        ("sub.w   (a0),d1", "memory to reg"),
        ("sub.l   d0,(a0)", "reg to memory"),
    ],
    "SUBA": [
        ("suba.w  d0,a0", "word"),
        ("suba.l  d0,a0", "long"),
    ],
    "SUBI": [
        ("subi.b  #$12,d0", "byte"),
        ("subi.w  #$1234,d0", "word"),
        ("subi.l  #$12345678,d0", "long"),
    ],
    "SUBQ": [
        ("subq.b  #1,d0", "byte min"),
        ("subq.l  #8,d0", "long max"),
        ("subq.w  #3,(a0)", "memory"),
    ],
    "SUBX": [
        ("subx.b  d0,d1", "byte reg"),
        ("subx.w  d0,d1", "word reg"),
        ("subx.l  d0,d1", "long reg"),
        ("subx.l  -(a0),-(a1)", "memory"),
    ],
    "SWAP": [
        ("swap    d0", ""),
        ("swap    d7", ""),
    ],
    "TAS": [
        ("tas     d0", "register"),
        ("tas     (a0)", "memory"),
    ],
    "TRAP": [
        ("trap    #0", "min"),
        ("trap    #15", "max"),
    ],
    "TRAPV": [
        ("trapv", ""),
    ],
    "TST": [
        ("tst.b   d0", "byte reg"),
        ("tst.w   d0", "word reg"),
        ("tst.l   d0", "long reg"),
        ("tst.w   (a0)", "memory"),
    ],
    "UNLK": [
        ("unlk    a6", ""),
        ("unlk    a5", ""),
    ],
    # 68020+ instructions we handle but mark as such
    "PACK": [],
    "UNPK": [],
    "RTD": [],
    "BKPT": [],
    "CALLM": [],
    "RTM": [],
    "TRAPcc": [],
    "CAS CAS2": [],
    "CHK2": [],
    "CMP2": [],
    "MOVE16": [],
    "MOVEC": [],
    "MOVES": [],
    # FPU
    "FRESTORE": [],
    "FSAVE": [],
    # MMU
    "CINV": [],
    "CPUSH": [],
    "PBcc": [],
    "PDBcc": [],
    "PFLUSH": [],
    "PFLUSH PFLUSHA": [],
    "PFLUSHR": [],
    "PLOAD": [],
    "PMOVE": [],
    "PRESTORE": [],
    "PSAVE": [],
    "PScc": [],
    "PTEST": [],
    "PTRAPcc": [],
    "PVALID": [],
    # Coprocessor
    "cpBcc": [],
    "cpDBcc": [],
    "cpGEN": [],
    "cpRESTORE": [],
    "cpSAVE": [],
    "cpScc": [],
    "cpTRAPcc": [],
    # Bit field (68020+)
    "BFCHG": [],
    "BFCLR": [],
    "BFEXTS": [],
    "BFEXTU": [],
    "BFFFO": [],
    "BFINS": [],
    "BFSET": [],
    "BFTST": [],
    # Extended (68020+)
    "EXT, EXTB": [
        ("ext.w   d0", "byte to word"),
        ("ext.l   d0", "word to long"),
        # extb.l is 68020+, skip for now
    ],
}


def assemble(source: str, tmpdir: str) -> bytes | None:
    """Assemble source with vasm, return code hunk data or None on failure."""
    src_path = os.path.join(tmpdir, "test.s")
    obj_path = os.path.join(tmpdir, "test.o")

    # Labels (lines ending with ':') must be at column 1;
    # instructions must be indented.
    lines = []
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped.endswith(":"):
            lines.append(stripped)
        elif stripped:
            lines.append(f"    {stripped}")
    full_source = "    section code,code\n" + "\n".join(lines) + "\n"
    with open(src_path, "w") as f:
        f.write(full_source)

    result = subprocess.run(
        [str(VASM), "-Fhunk", "-no-opt", "-quiet", "-x", "-o", obj_path, src_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None

    hf = parse_file(obj_path)
    if not hf.hunks:
        return None
    return hf.hunks[0].data


def run_tests():
    """Run all round-trip tests."""
    # Load knowledge base
    with open(KNOWLEDGE, encoding="utf-8") as f:
        kb_instructions = json.load(f)
    kb_mnemonics = set(inst["mnemonic"] for inst in kb_instructions)

    # Check coverage
    tested_mnemonics = set()
    untested_mnemonics = set()
    missing_from_kb = set()

    for mnemonic in TEST_CASES_68000:
        if mnemonic not in kb_mnemonics:
            missing_from_kb.add(mnemonic)

    for mnemonic in kb_mnemonics:
        if mnemonic not in TEST_CASES_68000:
            untested_mnemonics.add(mnemonic)

    total = 0
    passed = 0
    failed = 0
    skipped = 0
    failures = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for mnemonic, cases in sorted(TEST_CASES_68000.items()):
            if not cases:
                skipped += len(cases) if cases else 1
                continue

            for asm_line, desc in cases:
                total += 1
                test_name = f"{mnemonic}: {desc}" if desc else mnemonic

                # Step 1: Assemble original
                orig_data = assemble(asm_line, tmpdir)
                if orig_data is None:
                    failures.append((test_name, asm_line, "ASSEMBLE FAILED"))
                    failed += 1
                    continue

                # Step 2: Disassemble
                instructions = disassemble(orig_data)
                if not instructions:
                    failures.append((test_name, asm_line, "DISASSEMBLE EMPTY"))
                    failed += 1
                    continue

                # For branch/label tests, only check first instruction
                first_inst = instructions[0]
                first_size = first_inst.size
                orig_first = orig_data[:first_size]

                # Step 3: Reassemble disassembled text
                # For branches, need to reconstruct with a target label
                disasm_text = first_inst.text
                is_branch = disasm_text.startswith(("b", "db")) and "$" in disasm_text
                if is_branch:
                    # Replace absolute target with label
                    # Calculate how many nops needed to match displacement
                    parts = disasm_text.rsplit("$", 1)
                    target_addr = int(parts[1].split("(")[0], 16)
                    # Target is relative to start of code; branch is at offset 0
                    # Need filler between branch and label
                    filler_size = target_addr - first_size
                    nops = max(0, filler_size // 2)
                    nop_lines = "\nnop" * nops
                    reasm_source = f"{parts[0]}.t{nop_lines}\n.t:"
                else:
                    reasm_source = disasm_text

                reasm_data = assemble(reasm_source, tmpdir)
                if reasm_data is None:
                    failures.append((test_name, asm_line,
                                     f"REASSEMBLE FAILED: '{reasm_source}'"))
                    failed += 1
                    continue

                # Step 4: Compare binaries (first instruction only)
                reasm_first = reasm_data[:first_size]
                if orig_first == reasm_first:
                    passed += 1
                    tested_mnemonics.add(mnemonic)
                else:
                    orig_hex = " ".join(f"{b:02x}" for b in orig_first)
                    reasm_hex = " ".join(f"{b:02x}" for b in reasm_first)
                    failures.append((test_name, asm_line,
                                     f"BINARY MISMATCH: orig=[{orig_hex}] "
                                     f"reasm=[{reasm_hex}] disasm='{disasm_text}'"))
                    failed += 1

    # Report
    print(f"=== M68K Round-Trip Test Results ===")
    print(f"Passed: {passed}/{total}  Failed: {failed}  Skipped: {skipped}")
    print()

    if failures:
        print(f"--- Failures ({len(failures)}) ---")
        for name, asm, reason in failures:
            print(f"  FAIL {name}")
            print(f"       input:  {asm}")
            print(f"       reason: {reason}")
        print()

    # Coverage report
    kb_68000 = set()
    kb_not_68000 = set()
    for inst in kb_instructions:
        proc = inst.get("processors", "")
        # Consider 68000 if it mentions M68000 or 68000 or is generic "M68000 Family"
        if "68020" in proc or "68030" in proc or "68040" in proc or "68060" in proc:
            if "68000" not in proc and "Family" not in proc:
                kb_not_68000.add(inst["mnemonic"])
                continue
        kb_68000.add(inst["mnemonic"])

    tested_68000 = tested_mnemonics & kb_68000
    untested_68000 = kb_68000 - tested_mnemonics - {m for m, c in TEST_CASES_68000.items() if not c}

    print(f"--- Coverage ---")
    print(f"KB total mnemonics:    {len(kb_mnemonics)}")
    print(f"KB 68000 mnemonics:    ~{len(kb_68000)}")
    print(f"Tested (68000):        {len(tested_68000)}")
    print(f"Defined but skipped:   {len([m for m, c in TEST_CASES_68000.items() if not c])}")

    if untested_68000:
        print(f"\nUntested 68000 instructions not in test suite ({len(untested_68000)}):")
        for m in sorted(untested_68000):
            # Show processor info from KB
            proc = ""
            for inst in kb_instructions:
                if inst["mnemonic"] == m:
                    proc = inst.get("processors", "")
                    break
            print(f"  {m:20s} [{proc}]")

    if missing_from_kb:
        print(f"\nIn tests but not in KB ({len(missing_from_kb)}):")
        for m in sorted(missing_from_kb):
            print(f"  {m}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
