"""M68K disassembler round-trip test suite — data-driven from knowledge base.

Generates test cases from m68k_instructions.json structured fields:
  - forms: operand type patterns (ea, dn, an, imm, label, etc.)
  - ea_modes: valid EA modes for each operand role
  - sizes: valid operation sizes
  - uses_label: whether instruction uses PC-relative label
  - constraints: immediate ranges, CC parameterization, direction variants,
    operand modes, MOVEM direction (all extracted from PDF)

For each test: assemble with vasm -> disassemble -> reassemble -> binary diff.

Usage:
    python test_m68k_roundtrip.py [--verbose] [--filter MNEMONIC]
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
VASM = PROJ_ROOT / "tools" / "vasmm68k_mot.exe"
KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"

sys.path.insert(0, str(PROJ_ROOT / "scripts"))
from hunk_parser import parse_file
from m68k_disasm import disassemble

# Standard M68K condition code encoding (architectural, like MODE_MAP in parse_ea_modes.py)
# Defined by the M68K architecture, encoded in 4 bits of conditional instructions.
CC_TABLE = {
    0: "t", 1: "f", 2: "hi", 3: "ls", 4: "cc", 5: "cs", 6: "ne", 7: "eq",
    8: "vc", 9: "vs", 10: "pl", 11: "mi", 12: "ge", 13: "lt", 14: "gt", 15: "le",
}
CC_ALL = list(CC_TABLE.values())


# ── EA mode to assembly syntax ─────────────────────────────────────────────
# FORMAT-CONVENTION: These are arbitrary valid operand values for testing.
# Register choices (d0, a0, d1, a1) and immediate values are not from the PDF.

def ea_syntax(mode, size=None, imm_val=None):
    """Generate assembly syntax for an EA mode."""
    if mode == "imm":
        if imm_val is not None:
            return f"#{imm_val}"
        return _imm_for_size(size)
    return {
        "dn":      "d0",
        "an":      "a0",
        "ind":     "(a0)",
        "postinc": "(a0)+",
        "predec":  "-(a0)",
        "disp":    "4(a0)",
        "index":   "0(a0,d0.w)",
        "absw":    "$4.w",
        "absl":    "$10000",
        "pcdisp":  "4(pc)",
        "pcindex": "0(pc,d0.w)",
    }[mode]


def ea_syntax_alt(mode, size=None, imm_val=None):
    """Alternate registers to avoid collisions in two-operand instructions."""
    if mode == "imm":
        if imm_val is not None:
            return f"#{imm_val}"
        return _imm_for_size(size)
    return {
        "dn":      "d1",
        "an":      "a1",
        "ind":     "(a1)",
        "postinc": "(a1)+",
        "predec":  "-(a1)",
        "disp":    "4(a1)",
        "index":   "0(a1,d0.w)",
        "absw":    "$4.w",
        "absl":    "$10000",
        "pcdisp":  "4(pc)",
        "pcindex": "0(pc,d0.w)",
    }[mode]


def _imm_for_size(size):
    if size == "b":
        return "#$12"
    elif size == "l":
        return "#$12345678"
    return "#$1234"


def _is_memory_ea(mode):
    """Return True if the EA mode accesses memory (not register-direct)."""
    return mode not in ("dn", "an")


def _filter_modes_for_size(modes, sz, mem_size_only=None, bit_op_sizes=None):
    """Filter EA modes based on size and constraints.

    Applies:
    - An mode excluded for byte size (M68K architectural: An is word/long only)
    - Memory EA excluded for non-word sizes when mem_size_only="w" (shift/rotate)
    - Bit ops: only Dn valid for long, only memory valid for byte
    """
    result = []
    for mode in modes:
        # An can't be byte-sized (M68K architectural constraint)
        if mode == "an" and sz == "b":
            continue

        # Memory shift/rotate is word-only
        if mem_size_only and _is_memory_ea(mode) and sz != mem_size_only:
            continue

        # Bit operations: Dn = long, memory = byte
        if bit_op_sizes:
            if mode == "dn" and sz != bit_op_sizes.get("dn"):
                continue
            if _is_memory_ea(mode) and sz != bit_op_sizes.get("memory"):
                continue

        result.append(mode)
    return result


def _imm_for_constraint(constraint, size=None):
    """Generate an immediate value that satisfies the constraint.

    Uses constraint's min/max range from the KB.
    """
    if constraint is None:
        return _imm_for_size(size)
    mn, mx = constraint["min"], constraint["max"]
    # Pick a value in the middle of the range
    val = (mn + mx) // 2
    if val == 0 and mn >= 0:
        val = mn  # avoid 0 for ranges starting at 0
    if constraint.get("signed"):
        return f"#{val}"
    return f"#{val}"


# ── Data-driven test generator ─────────────────────────────────────────────

def generate_tests(inst):
    """Generate all test cases for one instruction from its KB data.

    Uses forms, ea_modes, sizes, uses_label, and constraints to enumerate
    valid combinations. Returns list of (asm_line, description) tuples.
    """
    mnemonic = inst["mnemonic"]
    proc_min = inst.get("processor_min", "68000")
    sizes = inst.get("sizes", [])
    ea = inst.get("ea_modes", {})
    forms = inst.get("forms", [])
    constraints = inst.get("constraints", {})
    m_lower = mnemonic.split(",")[0].split()[0].lower()  # "ASL, ASR" -> "asl"

    if proc_min != "68000":
        return []

    tests = []

    # Get all EA mode lists, filtering out 020+ only modes
    ea_020 = inst.get("ea_modes_020", {})
    def _filter_020(modes, role):
        """Remove modes that are 020+ only from a mode list."""
        exclude = set(ea_020.get(role, []))
        return [m for m in modes if m not in exclude] if exclude else modes

    src_modes = _filter_020(ea.get("src", []), "src")
    dst_modes = _filter_020(ea.get("dst", []), "dst")
    ea_modes = _filter_020(ea.get("ea", []), "ea")
    all_ea_modes = src_modes or dst_modes or ea_modes

    # Get constraints
    imm_range = constraints.get("immediate_range")
    cc_param = constraints.get("cc_parameterized")
    dir_variants = constraints.get("direction_variants")
    op_modes = constraints.get("operand_modes")
    movem_dir = constraints.get("movem_direction")
    mem_size_only = constraints.get("memory_size_only")
    bit_op_sizes = constraints.get("bit_op_sizes")
    sizes_68000 = constraints.get("sizes_68000")

    # Use 68000-filtered sizes if available (removes 020+ starred sizes)
    effective_sizes = sizes_68000 if sizes_68000 is not None else sizes

    for form in forms:
        # Skip 020+ forms (marked with * in PDF syntax)
        if form.get("processor_020"):
            continue
        operands = form.get("operands", [])
        op_types = [o["type"] for o in operands]

        if not op_types:
            tests.append((m_lower, ""))
            continue

        # Label instructions
        if "label" in op_types:
            tests.extend(_gen_label_tests(m_lower, op_types, cc_param, effective_sizes))
            continue

        # Determine which sizes to iterate.
        # If the form syntax specifies a size (e.g., "DIVS.W"), restrict to that size
        form_syntax = form.get("syntax", "")
        form_size = None
        form_inst = form_syntax.split(None, 1)[0] if form_syntax else ""
        if "." in form_inst:
            sz_char = form_inst.split(".")[-1].lower()
            if sz_char in ("b", "w", "l"):
                form_size = sz_char

        if form_size:
            iter_sizes = [form_size] if form_size in (effective_sizes or []) else [form_size]
        else:
            iter_sizes = effective_sizes if effective_sizes else [None]

        for sz in iter_sizes:
            sfx = f".{sz}" if sz else ""
            imm = _imm_for_constraint(imm_range, sz) if imm_range else _imm_for_size(sz)

            if op_types == ["ea"] and all_ea_modes:
                fmodes = _filter_modes_for_size(all_ea_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fmodes:
                    operand = ea_syntax(mode, sz)
                    tests.append((f"{m_lower}{sfx} {operand}",
                                  f"ea={mode} sz={sz}"))

            elif op_types == ["ea", "ea"] and src_modes and dst_modes:
                fsrc = _filter_modes_for_size(src_modes, sz, mem_size_only, bit_op_sizes)
                fdst = _filter_modes_for_size(dst_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fsrc:
                    src = ea_syntax(mode, sz)
                    tests.append((f"{m_lower}{sfx} {src},d1",
                                  f"src={mode} sz={sz}"))
                for mode in fdst:
                    if mode == "dn":
                        continue
                    dst = ea_syntax(mode, sz)
                    tests.append((f"{m_lower}{sfx} d0,{dst}",
                                  f"dst={mode} sz={sz}"))

            elif op_types == ["dn", "ea"] and all_ea_modes:
                if src_modes:
                    fsrc = _filter_modes_for_size(src_modes, sz, mem_size_only, bit_op_sizes)
                    for mode in fsrc:
                        src = ea_syntax(mode, sz)
                        tests.append((f"{m_lower}{sfx} {src},d1",
                                      f"src={mode} sz={sz}"))
                fdst = _filter_modes_for_size(dst_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fdst:
                    dst = ea_syntax(mode, sz)
                    tests.append((f"{m_lower}{sfx} d0,{dst}",
                                  f"dst={mode} sz={sz}"))

            elif op_types == ["ea", "dn"]:
                fsrc = _filter_modes_for_size(src_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fsrc:
                    src = ea_syntax(mode, sz)
                    tests.append((f"{m_lower}{sfx} {src},d1",
                                  f"src={mode} sz={sz}"))

            elif op_types == ["ea", "an"]:
                fsrc = _filter_modes_for_size(src_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fsrc:
                    src = ea_syntax(mode, sz)
                    tests.append((f"{m_lower}{sfx} {src},a1",
                                  f"src={mode} sz={sz}"))

            elif op_types == ["imm", "ea"] and all_ea_modes:
                fdst = _filter_modes_for_size(dst_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes)
                # For bit operations, use bit number (small value) not size-based immediate
                if bit_op_sizes:
                    this_imm = "#4"
                    # Exclude imm destination for immediate-source bit ops
                    # (can't do BTST #n,#m — only BTST Dn,#m is valid)
                    fdst = [m for m in fdst if m != "imm"]
                else:
                    this_imm = imm
                for mode in fdst:
                    dst = ea_syntax(mode, sz)
                    tests.append((f"{m_lower}{sfx} {this_imm},{dst}",
                                  f"dst={mode} sz={sz}"))

            elif op_types == ["imm", "dn"]:
                tests.append((f"{m_lower}{sfx} {imm},d0",
                              f"imm sz={sz}"))

            elif op_types == ["ea", "reglist"]:
                tests.extend(_gen_movem_tests(m_lower, sz, all_ea_modes, movem_dir))

            elif op_types == ["predec", "predec"]:
                # From constraints.operand_modes (R/M field from PDF)
                if op_modes:
                    for bit_val, mode_type in op_modes["values"].items():
                        if mode_type == "predec,predec":
                            tests.append((f"{m_lower}{sfx} -(a0),-(a1)",
                                          f"predec sz={sz}"))
                        elif mode_type == "dn,dn":
                            tests.append((f"{m_lower}{sfx} d0,d1",
                                          f"reg sz={sz}"))
                else:
                    tests.append((f"{m_lower}{sfx} -(a0),-(a1)",
                                  f"predec sz={sz}"))

            elif op_types == ["postinc", "postinc"]:
                tests.append((f"{m_lower}{sfx} (a0)+,(a1)+",
                              f"postinc sz={sz}"))

            elif op_types == ["sr", "ea"]:
                for mode in (dst_modes or all_ea_modes):
                    dst = ea_syntax(mode, sz)
                    tests.append((f"move.w sr,{dst}", f"dst={mode}"))
                break

            elif op_types == ["ea", "sr"]:
                for mode in (src_modes or all_ea_modes):
                    src = ea_syntax(mode, sz)
                    tests.append((f"move.w {src},sr", f"src={mode}"))
                break

            elif op_types == ["ea", "ccr"]:
                for mode in (src_modes or all_ea_modes):
                    src = ea_syntax(mode, sz)
                    tests.append((f"move.w {src},ccr", f"src={mode}"))
                break

            elif op_types == ["imm", "ccr"]:
                tests.append((f"{m_lower}.b #$1f,ccr", ""))
                break

            elif op_types == ["imm", "sr"]:
                tests.append((f"{m_lower}.w #$0700,sr", ""))
                break

            elif op_types == ["an", "usp"]:
                tests.append(("move.l a0,usp", "to usp"))
                tests.append(("move.l usp,a0", "from usp"))
                break

            elif op_types == ["an", "imm"]:
                tests.append((f"{m_lower} a6,#-100", "negative"))
                tests.append((f"{m_lower} a5,#0", "zero"))
                break

            elif op_types == ["an"]:
                tests.append((f"{m_lower} a6", "a6"))
                tests.append((f"{m_lower} a5", "a5"))

            elif op_types == ["dn"]:
                tests.append((f"{m_lower}{sfx} d0", f"d0 sz={sz}"))
                tests.append((f"{m_lower}{sfx} d7", f"d7 sz={sz}"))

            elif op_types == ["disp", "dn"]:
                tests.append((f"{m_lower}{sfx} 0(a0),d0", f"mem-to-reg sz={sz}"))
                tests.append((f"{m_lower}{sfx} d0,0(a0)", f"reg-to-mem sz={sz}"))

            elif op_types == ["dn", "dn"]:
                tests.append((f"{m_lower}{sfx} d1,d0", f"reg-reg sz={sz}"))

            elif op_types == ["an", "an"]:
                tests.append((f"{m_lower} a0,a1", "addr-addr"))

            elif op_types == ["dn", "an"]:
                tests.append((f"{m_lower} d0,a0", "data-addr"))

            elif op_types == ["imm"]:
                if imm_range:
                    tests.append((f"{m_lower} #{imm_range['min']}", "min"))
                    tests.append((f"{m_lower} #{imm_range['max']}", "max"))
                else:
                    tests.append((f"{m_lower} {imm}", ""))

            else:
                pass

    # Direction variants from constraints (shift/rotate L/R)
    if dir_variants:
        variants = dir_variants["variants"]
        base = variants[0]  # e.g. "asl"
        if m_lower == base and len(variants) > 1:
            alt = variants[1]  # e.g. "asr"
            extra = []
            for asm, desc in tests:
                extra.append((asm.replace(base, alt, 1), desc))
            tests.extend(extra)

    # CC parameterization from constraints
    if cc_param and not inst.get("uses_label", False):
        prefix = cc_param["prefix"]
        excluded = set(cc_param.get("excluded", []))
        codes = [c for c in CC_ALL if c not in excluded]
        cc_tests = []
        for cc in codes:
            for asm, desc in tests:
                cc_tests.append((asm.replace(prefix, prefix.replace(prefix, f"{prefix[:-len(prefix)]}{cc}" if len(prefix) > 0 else cc, 1), 1),
                                 f"{prefix}{cc} {desc}"))
        # Simpler approach: replace the base mnemonic with each CC variant
        if prefix and tests:
            cc_tests = []
            for cc in codes:
                full_mn = f"{prefix}{cc}"
                for asm, desc in tests:
                    cc_tests.append((asm.replace(m_lower, full_mn, 1),
                                     f"{full_mn} {desc}"))
            tests = cc_tests

    return tests


def _gen_label_tests(m_lower, op_types, cc_param, sizes):
    """Generate tests for label-using instructions.

    Uses cc_parameterized constraint from KB to determine which
    condition codes to expand.
    """
    tests = []

    # Determine base mnemonics to test
    if cc_param:
        excluded = set(cc_param.get("excluded", []))
        codes = [c for c in CC_ALL if c not in excluded]
        prefix = cc_param["prefix"]
        mnemonics = [f"{prefix}{cc}" for cc in codes]
    else:
        mnemonics = [m_lower]

    # Determine size variants from KB sizes
    # Branch sizes: "b" = .s (8-bit), "w" = .w (16-bit), "l" = .l (32-bit, 020+)
    branch_sizes = []
    for sz in (sizes or [None]):
        if sz == "b":
            branch_sizes.append(("s", True))   # .s needs nop filler for min displacement
        elif sz == "w":
            branch_sizes.append(("w", False))
        elif sz == "l":
            pass  # Skip .l for 68000 tests (020+)
        elif sz is None:
            branch_sizes.append(("w", False))

    if not branch_sizes:
        branch_sizes = [("w", False)]

    has_dn = "dn" in op_types

    for mn in mnemonics:
        if has_dn:
            # DBcc pattern: dbCC dn,<label>
            for sz_sfx, needs_nop in branch_sizes:
                tests.append((f"{mn} d0,.t\n.t:", f"{mn}"))
        else:
            for sz_sfx, needs_nop in branch_sizes:
                if needs_nop:
                    tests.append((f"{mn}.{sz_sfx} .t\nnop\n.t:", f"{mn}.{sz_sfx}"))
                else:
                    tests.append((f"{mn}.{sz_sfx} .t\n.t:", f"{mn}.{sz_sfx}"))

    return tests


def _gen_movem_tests(m_lower, sz, modes, movem_dir):
    """Generate MOVEM tests using direction constraint from KB.

    movem_dir from constraints tells us which EA modes are valid
    for each direction (reg-to-mem vs mem-to-reg).
    """
    sfx = f".{sz}" if sz else ""
    tests = []

    for mode in modes:
        ea_str = ea_syntax(mode)

        if mode == "predec":
            # Predecrement only valid for reg-to-mem (from PDF dr field)
            tests.append((f"movem{sfx} d0-d3/a0-a1,-(a7)",
                          f"reg-to-mem predec sz={sz}"))
        elif mode == "postinc":
            # Postincrement only valid for mem-to-reg
            tests.append((f"movem{sfx} (a7)+,d0-d3/a0-a1",
                          f"mem-to-reg postinc sz={sz}"))
        elif mode in ("pcdisp", "pcindex"):
            # PC-relative only valid for mem-to-reg
            tests.append((f"movem{sfx} {ea_str},d0-d3/a0-a1",
                          f"mem-to-reg ea={mode} sz={sz}"))
        else:
            # Other modes valid for both directions
            tests.append((f"movem{sfx} d0-d3/a0-a1,{ea_str}",
                          f"reg-to-mem ea={mode} sz={sz}"))
            tests.append((f"movem{sfx} {ea_str},d0-d3/a0-a1",
                          f"mem-to-reg ea={mode} sz={sz}"))

    return tests


# ── Assembly / round-trip infrastructure ───────────────────────────────────

def assemble(source, tmpdir):
    """Assemble source with vasm, return code hunk data or None on failure."""
    src_path = os.path.join(tmpdir, "test.s")
    obj_path = os.path.join(tmpdir, "test.o")

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


def run_tests(filter_mnemonic=None, verbose=False):
    """Run all data-driven round-trip tests."""
    with open(KNOWLEDGE, encoding="utf-8") as f:
        kb_instructions = json.load(f)

    # Build set of label-using mnemonics from KB
    label_mnemonics = {inst["mnemonic"] for inst in kb_instructions
                       if inst.get("uses_label", False)}

    total = 0
    passed = 0
    failed = 0
    skipped_mnemonics = 0
    tested_mnemonics = set()
    failures = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for inst in kb_instructions:
            mnemonic = inst["mnemonic"]
            proc_min = inst.get("processor_min", "68000")

            if filter_mnemonic and filter_mnemonic.upper() not in mnemonic.upper():
                continue

            if proc_min != "68000":
                skipped_mnemonics += 1
                continue

            cases = generate_tests(inst)
            if not cases:
                if verbose:
                    print(f"  SKIP {mnemonic} (no tests generated)")
                skipped_mnemonics += 1
                continue

            for asm_line, desc in cases:
                total += 1
                test_name = f"{mnemonic}: {desc}" if desc else mnemonic

                # Step 1: Assemble
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

                first_inst = instructions[0]
                first_size = first_inst.size
                orig_first = orig_data[:first_size]

                # Step 3: Reassemble
                disasm_text = first_inst.text
                # Detect label instructions using KB uses_label field
                is_branch = mnemonic in label_mnemonics and "$" in disasm_text
                if is_branch:
                    parts = disasm_text.rsplit("$", 1)
                    target_addr = int(parts[1].split("(")[0], 16)
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

                # Step 4: Binary compare
                reasm_first = reasm_data[:first_size]
                if orig_first == reasm_first:
                    passed += 1
                    tested_mnemonics.add(mnemonic)
                    if verbose:
                        print(f"  OK   {test_name}")
                else:
                    orig_hex = " ".join(f"{b:02x}" for b in orig_first)
                    reasm_hex = " ".join(f"{b:02x}" for b in reasm_first)
                    failures.append((test_name, asm_line,
                                     f"BINARY MISMATCH: orig=[{orig_hex}] "
                                     f"reasm=[{reasm_hex}] disasm='{disasm_text}'"))
                    failed += 1

    # Report
    print(f"=== M68K Round-Trip Test Results ===")
    print(f"Passed: {passed}/{total}  Failed: {failed}  "
          f"Skipped mnemonics: {skipped_mnemonics}")
    print()

    if failures:
        print(f"--- Failures ({len(failures)}) ---")
        for name, asm, reason in failures:
            print(f"  FAIL {name}")
            print(f"       input:  {asm}")
            print(f"       reason: {reason}")
        print()

    # Coverage
    kb_68000 = set()
    for inst in kb_instructions:
        if inst.get("processor_min", "68000") == "68000":
            kb_68000.add(inst["mnemonic"])

    untested = kb_68000 - tested_mnemonics
    print(f"--- Coverage ---")
    print(f"68000 mnemonics in KB:  {len(kb_68000)}")
    print(f"Tested:                 {len(tested_mnemonics)}")
    print(f"Generated test cases:   {total}")
    if untested:
        print(f"\nUntested 68000 mnemonics ({len(untested)}):")
        for m in sorted(untested):
            print(f"  {m}")

    return failed == 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--filter", "-f", help="Test only mnemonics matching this")
    args = parser.parse_args()

    success = run_tests(filter_mnemonic=args.filter, verbose=args.verbose)
    sys.exit(0 if success else 1)
