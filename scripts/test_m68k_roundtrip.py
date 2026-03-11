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
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
VASM = PROJ_ROOT / "tools" / "vasmm68k_mot.exe"
KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"
VASM_COMPAT = PROJ_ROOT / "knowledge" / "vasm_compat.json"

sys.path.insert(0, str(PROJ_ROOT / "scripts"))
from hunk_parser import parse_file
from m68k_disasm import DecodeError, disassemble


def _load_kb_payload():
    with open(KNOWLEDGE, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("instructions", []), data.get("_meta", {})
    return data, {}


KB_INSTRUCTIONS, KB_META = _load_kb_payload()
if "condition_codes" not in KB_META:
    raise RuntimeError(
        "KB _meta missing 'condition_codes' — regenerate m68k_instructions.json"
    )
CC_ALL = list(KB_META["condition_codes"])

# Index KB instructions by lowercase mnemonic for quick lookup
_KB_BY_MNEMONIC = {inst["mnemonic"].lower(): inst for inst in KB_INSTRUCTIONS}


def _find_inst(m_lower):
    """Find a KB instruction by lowercase mnemonic."""
    return _KB_BY_MNEMONIC.get(m_lower)


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


def _mnemonic_variants(inst_mnemonic):
    """Return base mnemonic aliases for this instruction.

    Examples:
      "MOVE" -> ["move"]
      "ASL, ASR" -> ["asl", "asr"]
      "PFLUSH PFLUSHA" -> ["pflush", "pfusha"]
    """
    return [part.strip().lower() for part in re.split(r"[ ,]+", inst_mnemonic)
            if part.strip()]


def _form_mnemonics_from_syntax(inst_mnemonic_variants, dir_variants, form_syntax):
    """Get mnemonic tokens for a form syntax entry from KB data.

    Use form syntax if it maps to a known variant.
    For direction placeholders like "ASd" derive variants from constraints.
    Return None when the form cannot be resolved.
    """
    if not form_syntax:
        return [inst_mnemonic_variants[0]]

    raw = form_syntax.split(None, 1)[0]
    candidate = raw.split(".", 1)[0].lower()
    # Strip non-alphanumeric syntax adornments if parser captured any.
    candidate = re.sub(r"[^a-z0-9]", "", candidate)

    if candidate in inst_mnemonic_variants:
        return [candidate]

    if dir_variants:
        base = (dir_variants.get("base") or "").lower()
        variants = [v.lower() for v in (dir_variants.get("variants") or [])
                    if v.strip()]
        # Direction forms use a placeholder suffix, e.g. ASd -> asl/asr.
        if base and candidate.startswith(base):
            suffix = candidate[len(base):]
            if suffix and all(ch == "d" for ch in suffix):
                return variants

    return None


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
    return f"#{val}"


# ── Data-driven test generator ─────────────────────────────────────────────

def generate_tests(inst, compat=None):
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
    m_variants = _mnemonic_variants(mnemonic)
    m_lower = m_variants[0]

    tests = []

    # For 68000 instructions, filter out 020+ only EA modes;
    # for 020+ instructions, use all EA modes
    ea_020 = inst.get("ea_modes_020", {}) if proc_min == "68000" else {}
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

    compat = compat or {}
    skip_form_prefixes = [p.lower() for p in compat.get("skip_forms", [])]

    # Use 68000-filtered sizes if available (removes 020+ starred sizes)
    effective_sizes = sizes_68000 if sizes_68000 is not None else sizes

    def _emit_direction_variants(start_idx, primary_mn, extra_mnemonics):
        for variant in extra_mnemonics:
            for asm, desc in tests[start_idx:]:
                if asm == primary_mn:
                    tests.append((variant, desc))
                elif asm.startswith(f"{primary_mn}.") or asm.startswith(f"{primary_mn} "):
                    tests.append((variant + asm[len(primary_mn):], desc))


    for form in forms:
        # Skip 020+ forms (marked with * in PDF syntax)
        if form.get("processor_020"):
            continue

        raw_form = form.get("syntax", "").split(None, 1)[0].lower()
        if raw_form and any(raw_form.startswith(prefix) for prefix in skip_form_prefixes):
            continue

        operands = form.get("operands", [])
        op_types = [o["type"] for o in operands]
        form_syntax = form.get("syntax", "")
        form_mnemonics = _form_mnemonics_from_syntax(
            m_variants,
            dir_variants,
            form_syntax,
        )
        if form_mnemonics is None:
            raise RuntimeError(
                f"Unresolved form syntax for {mnemonic}: '{form_syntax}'. "
                f"No valid mnemonic variant from header or direction_variants."
            )
        form_mn = form_mnemonics[0]
        form_test_start = len(tests)

        if not op_types:
            # Use form syntax if available (handles PFLUSHA vs PFLUSH)
            tests.append((form_mn, ""))
            _emit_direction_variants(form_test_start, form_mn, form_mnemonics[1:])
            continue

        # Label instructions
        if "label" in op_types:
            tests.extend(_gen_label_tests(m_lower, op_types, cc_param, effective_sizes))
            continue

        # Determine which sizes to iterate.
        # If the form syntax specifies a size (e.g., "DIVS.W"), restrict to that size
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
                    tests.append((f"{form_mn}{sfx} {operand}",
                                  f"ea={mode} sz={sz}"))

            elif op_types == ["ea", "ea"] and src_modes and dst_modes:
                fsrc = _filter_modes_for_size(src_modes, sz, mem_size_only, bit_op_sizes)
                fdst = _filter_modes_for_size(dst_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fsrc:
                    src = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {src},d1",
                                  f"src={mode} sz={sz}"))
                for mode in fdst:
                    if mode == "dn":
                        continue
                    dst = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} d0,{dst}",
                                  f"dst={mode} sz={sz}"))

            elif op_types == ["dn", "ea"] and all_ea_modes:
                if src_modes:
                    fsrc = _filter_modes_for_size(src_modes, sz, mem_size_only, bit_op_sizes)
                    for mode in fsrc:
                        src = ea_syntax(mode, sz)
                        tests.append((f"{form_mn}{sfx} {src},d1",
                                      f"src={mode} sz={sz}"))
                fdst = _filter_modes_for_size(dst_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fdst:
                    dst = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} d0,{dst}",
                                  f"dst={mode} sz={sz}"))

            elif op_types == ["ea", "dn"]:
                fsrc = _filter_modes_for_size(src_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fsrc:
                    src = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {src},d1",
                                  f"src={mode} sz={sz}"))

            elif op_types == ["ea", "an"]:
                fsrc = _filter_modes_for_size(src_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fsrc:
                    src = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {src},a1",
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
                    tests.append((f"{form_mn}{sfx} {this_imm},{dst}",
                                  f"dst={mode} sz={sz}"))

            elif op_types == ["imm", "dn"]:
                tests.append((f"{form_mn}{sfx} {imm},d0",
                              f"imm sz={sz}"))

            elif op_types == ["ea", "reglist"]:
                tests.extend(_gen_movem_tests(m_lower, sz, all_ea_modes, movem_dir))

            elif op_types == ["reglist", "ea"]:
                # Handled by ("ea","reglist") — _gen_movem_tests covers both directions
                pass

            elif op_types == ["predec", "predec"]:
                # From constraints.operand_modes (R/M field from PDF)
                if op_modes:
                    for bit_val, mode_type in op_modes["values"].items():
                        if mode_type == "predec,predec":
                            tests.append((f"{form_mn}{sfx} -(a0),-(a1)",
                                          f"predec sz={sz}"))
                        elif mode_type == "dn,dn":
                            tests.append((f"{form_mn}{sfx} d0,d1",
                                          f"reg sz={sz}"))
                else:
                    tests.append((f"{form_mn}{sfx} -(a0),-(a1)",
                                  f"predec sz={sz}"))

            elif op_types == ["postinc", "postinc"]:
                tests.append((f"{form_mn}{sfx} (a0)+,(a1)+",
                              f"postinc sz={sz}"))

            elif op_types == ["sr", "ea"]:
                for mode in (dst_modes or all_ea_modes):
                    dst = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} sr,{dst}", f"dst={mode}"))
                break

            elif op_types == ["ea", "sr"]:
                for mode in (src_modes or all_ea_modes):
                    src = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {src},sr", f"src={mode}"))
                break

            elif op_types == ["ea", "ccr"]:
                for mode in (src_modes or all_ea_modes):
                    src = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {src},ccr", f"src={mode}"))
                break

            elif op_types == ["imm", "ccr"]:
                tests.append((f"{form_mn}{sfx} #$1f,ccr", ""))
                break

            elif op_types == ["imm", "sr"]:
                tests.append((f"{form_mn}{sfx} #$0700,sr", ""))
                break

            elif op_types == ["an", "usp"]:
                tests.append((f"{form_mn} a0,usp", "to usp"))
                break

            elif op_types == ["usp", "an"]:
                tests.append((f"{form_mn} usp,a0", "from usp"))
                break

            elif op_types == ["an", "imm"]:
                an_imm = _imm_for_constraint(imm_range, sz)
                tests.append((f"{form_mn} a6,{an_imm}", f"imm={an_imm}"))
                if imm_range and imm_range.get("signed"):
                    tests.append((f"{form_mn} a5,#{imm_range['min']}", "min"))
                break

            elif op_types == ["an"]:
                tests.append((f"{form_mn} a6", "a6"))
                tests.append((f"{form_mn} a5", "a5"))

            elif op_types == ["dn"]:
                tests.append((f"{form_mn}{sfx} d0", f"d0 sz={sz}"))
                tests.append((f"{form_mn}{sfx} d7", f"d7 sz={sz}"))

            elif op_types == ["disp", "dn"]:
                tests.append((f"{form_mn}{sfx} 0(a0),d0", f"mem-to-reg sz={sz}"))

            elif op_types == ["dn", "disp"]:
                tests.append((f"{form_mn}{sfx} d0,0(a0)", f"reg-to-mem sz={sz}"))

            elif op_types == ["dn", "dn"]:
                tests.append((f"{form_mn}{sfx} d1,d0", f"reg-reg sz={sz}"))

            elif op_types == ["an", "an"]:
                tests.append((f"{form_mn} a0,a1", "addr-addr"))

            elif op_types == ["dn", "an"]:
                tests.append((f"{form_mn} d0,a0", "data-addr"))

            elif op_types == ["imm"]:
                if imm_range:
                    tests.append((f"{form_mn}{sfx} #{imm_range['min']}", "min"))
                    tests.append((f"{form_mn}{sfx} #{imm_range['max']}", "max"))
                else:
                    tests.append((f"{form_mn}{sfx} {imm}", ""))

            elif op_types == ["ccr", "ea"]:
                # MOVE from CCR: MOVE CCR,<ea> — no size suffix needed
                fdst = _filter_modes_for_size(dst_modes or all_ea_modes, sz)
                for mode in fdst:
                    dst = ea_syntax(mode, sz)
                    tests.append((f"{form_mn} ccr,{dst}", f"dst={mode}"))
                break

            elif op_types == ["rn"]:
                # RTM Rn: generic register (dn or an), no sizes
                tests.append((f"{form_mn} d0", "dn"))
                tests.append((f"{form_mn} a0", "an"))

            elif op_types == ["rn", "ea"]:
                # MOVES Rn,<ea>: register to memory EA
                fmodes = _filter_modes_for_size(all_ea_modes, sz)
                for mode in fmodes:
                    dst = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} d0,{dst}", f"rn-to={mode}"))

            elif op_types == ["ea", "rn"]:
                # MOVES <ea>,Rn or CMP2/CHK2 <ea>,Rn
                fmodes = _filter_modes_for_size(all_ea_modes, sz)
                for mode in fmodes:
                    src = ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {src},d0", f"ea-to-rn={mode}"))

            elif op_types == ["ctrl_reg", "rn"]:
                # MOVEC Rc,Rn — from control register to general register
                ctrl_regs = inst.get("constraints", {}).get("control_registers")
                if not ctrl_regs:
                    raise RuntimeError(f"{mnemonic}: KB missing control_registers")
                seen_abbrevs = set()
                for cr in ctrl_regs:
                    abbrev = cr["abbrev"]
                    if abbrev not in seen_abbrevs:
                        seen_abbrevs.add(abbrev)
                        cpu = VASM_CPU_FLAG_MAP.get(cr.get("processor_min", "68010"))
                        tests.append((f"{form_mn} {abbrev},d0",
                                      f"{abbrev}-to-d0", cpu))
                break

            elif op_types == ["rn", "ctrl_reg"]:
                # MOVEC Rn,Rc — from general register to control register
                ctrl_regs = inst.get("constraints", {}).get("control_registers")
                if not ctrl_regs:
                    raise RuntimeError(f"{mnemonic}: KB missing control_registers")
                seen_abbrevs = set()
                for cr in ctrl_regs:
                    abbrev = cr["abbrev"]
                    if abbrev not in seen_abbrevs:
                        seen_abbrevs.add(abbrev)
                        cpu = VASM_CPU_FLAG_MAP.get(cr.get("processor_min", "68010"))
                        tests.append((f"{form_mn} d0,{abbrev}",
                                      f"d0-to-{abbrev}", cpu))
                break

            elif op_types == ["bf_ea"]:
                # BFTST/BFCHG/BFCLR/BFSET <ea>{offset:width}
                fmodes = _filter_modes_for_size(all_ea_modes, sz)
                for mode in fmodes:
                    tests.append((f"{form_mn} {ea_syntax(mode)}{{2:8}}", f"ea={mode}"))

            elif op_types == ["bf_ea", "dn"]:
                # BFEXTS/BFEXTU/BFFFO <ea>{offset:width},Dn
                fmodes = _filter_modes_for_size(all_ea_modes, sz)
                for mode in fmodes:
                    tests.append((f"{form_mn} {ea_syntax(mode)}{{2:8}},d1", f"ea={mode}"))

            elif op_types == ["dn", "bf_ea"]:
                # BFINS Dn,<ea>{offset:width}
                fmodes = _filter_modes_for_size(all_ea_modes, sz)
                for mode in fmodes:
                    tests.append((f"{form_mn} d0,{ea_syntax(mode)}{{2:8}}", f"ea={mode}"))

            elif op_types == ["dn", "dn", "imm"]:
                # PACK Dx,Dy,#adj or UNPK Dx,Dy,#adj (register form)
                tests.append((f"{form_mn} d0,d1,#0", "reg-reg"))

            elif op_types == ["predec", "predec", "imm"]:
                # PACK -(Ax),-(Ay),#adj or UNPK -(Ax),-(Ay),#adj (memory form)
                tests.append((f"{form_mn} -(a0),-(a1),#0", "mem-mem"))

            elif op_types == ["dn", "dn", "ea"]:
                # CAS Dc,Du,<ea>
                fmodes = _filter_modes_for_size(all_ea_modes, sz)
                for mode in fmodes:
                    tests.append((f"{form_mn}{sfx} d0,d1,{ea_syntax(mode, sz)}",
                                  f"ea={mode}"))

            else:
                pass

        _emit_direction_variants(form_test_start, form_mn, form_mnemonics[1:])

    # CC parameterization from constraints
    if cc_param and not inst.get("uses_label", False):
        prefix = cc_param["prefix"]
        excluded = set(cc_param.get("excluded", []))
        codes = [c for c in CC_ALL if c not in excluded]
        if prefix and tests:
            cc_tests = []
            for cc in codes:
                full_mn = f"{prefix}{cc}"
                for asm, desc in tests:
                    cc_tests.append((asm.replace(m_lower, full_mn, 1),
                                     f"{full_mn} {desc}"))
            tests = cc_tests

    # Long MUL/DIV (68020+): add long-form tests alongside existing word-form tests
    if mnemonic in ("MULS", "MULU", "DIVS, DIVSL", "DIVU, DIVUL"):
        tests.extend(_gen_long_mul_div_tests(mnemonic))

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

    # Determine size variants from KB sizes via vasm_compat branch_size_map
    branch_sizes = []
    for sz in (sizes or [None]):
        if sz is None:
            branch_sizes.append(("w", False))
        elif sz in VASM_BRANCH_SIZE_MAP:
            entry = VASM_BRANCH_SIZE_MAP[sz]
            if entry.get("skip_for_68000"):
                continue
            sfx = entry["suffix"].lstrip(".")
            branch_sizes.append((sfx, entry.get("needs_nop_filler", False)))

    if not branch_sizes:
        raise RuntimeError(f"{m_lower}: no valid branch sizes from KB/vasm_compat")

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
    """Generate MOVEM tests using direction constraint and per-direction EA modes from KB."""
    sfx = f".{sz}" if sz else ""
    tests = []

    # Get per-direction EA mode sets from KB (parsed from separate PDF tables)
    inst_data = _find_inst(m_lower)
    if not inst_data:
        raise RuntimeError(f"{m_lower}: not found in KB")
    dir_modes = inst_data.get("ea_modes_by_direction")
    if not dir_modes:
        raise RuntimeError(f"{m_lower}: KB missing ea_modes_by_direction")
    r2m_modes = set(dir_modes["reg-to-mem"])
    m2r_modes = set(dir_modes["mem-to-reg"])

    for mode in modes:
        ea_str = ea_syntax(mode)
        if mode in r2m_modes:
            if mode == "predec":
                ea_str = "-(a7)"
            tests.append((f"{m_lower}{sfx} d0-d3/a0-a1,{ea_str}",
                          f"reg-to-mem ea={mode} sz={sz}"))
        if mode in m2r_modes:
            if mode == "postinc":
                ea_str = "(a7)+"
            tests.append((f"{m_lower}{sfx} {ea_str},d0-d3/a0-a1",
                          f"mem-to-reg ea={mode} sz={sz}"))

    return tests


def _gen_long_mul_div_tests(mnemonic):
    """Generate test cases for 68020+ long MUL/DIV forms.

    These instructions use a separate opword (group 4) and extension word,
    distinct from the 68000 word-size forms in groups 8/C.
    """
    cpu = "-m68020"
    tests = []
    m = mnemonic.upper()

    if m in ("MULS", "MULU"):
        name = m.lower()
        # 32x32→32 (SIZE=0, single register)
        tests.append((f"{name}.l d0,d1", f"{name}.l 32-bit", cpu))
        # 32x32→64 (SIZE=1, register pair)
        tests.append((f"{name}.l d0,d2:d1", f"{name}.l 64-bit", cpu))
        # Control mode EA
        tests.append((f"{name}.l (a0),d3", f"{name}.l ind", cpu))
        # Immediate EA
        tests.append((f"{name}.l #$1234,d4", f"{name}.l imm", cpu))

    elif m == "DIVS, DIVSL":
        # divs.l: SIZE=0+Dq==Dr or SIZE=1
        tests.append(("divs.l d0,d1", "divs.l 32q", cpu))
        # divsl.l: SIZE=0+Dq!=Dr
        tests.append(("divsl.l d0,d2:d1", "divsl.l 32r:32q", cpu))
        # divs.l with pair: SIZE=1
        tests.append(("divs.l d0,d2:d1", "divs.l 64/32", cpu))
        # Control mode EA
        tests.append(("divs.l (a0),d3", "divs.l ind", cpu))

    elif m == "DIVU, DIVUL":
        tests.append(("divu.l d0,d1", "divu.l 32q", cpu))
        tests.append(("divul.l d0,d2:d1", "divul.l 32r:32q", cpu))
        tests.append(("divu.l d0,d2:d1", "divu.l 64/32", cpu))
        tests.append(("divu.l #$1234,d4", "divu.l imm", cpu))

    return tests


# ── Assembly / round-trip infrastructure ───────────────────────────────────

# Load vasm compatibility data
with open(VASM_COMPAT, encoding="utf-8") as _f:
    _vasm_data = json.load(_f)
VASM_CPU_FLAG_MAP = _vasm_data["_meta"]["default_cpu_flag_map"]
VASM_INST_COMPAT = _vasm_data["instructions"]
VASM_BRANCH_SIZE_MAP = _vasm_data["branch_size_map"]


def assemble(source, tmpdir, cpu_flag="-m68000", debug=False):
    """Assemble source with vasm, return code hunk data or None on failure.

    cpu_flag: vasm -m flag (e.g. "-m68000", "-m68851")
    """
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
        [str(VASM), "-Fhunk", "-no-opt", "-quiet", "-x", cpu_flag,
         "-o", obj_path, src_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        if debug:
            print(f"    [vasm src]\n{full_source}")
            print(f"    [vasm stdout] {result.stdout.strip()}")
            print(f"    [vasm stderr] {result.stderr.strip()}")
        return None

    hf = parse_file(obj_path)
    if not hf.hunks:
        return None
    return hf.hunks[0].data


def run_tests(filter_mnemonic=None, verbose=False, max_cpu=None, debug_asm=False):
    """Run all data-driven round-trip tests."""
    kb_instructions = KB_INSTRUCTIONS

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

            # Check vasm compatibility data
            vasm_info = VASM_INST_COMPAT.get(mnemonic, {})
            if vasm_info.get("supported") is False:
                if verbose:
                    print(f"  SKIP {mnemonic} ({vasm_info.get('reason', 'vasm unsupported')})")
                skipped_mnemonics += 1
                continue

            # Use vasm-specific CPU flag if provided, else default from processor_min
            cpu_flag_override = vasm_info.get("cpu_flag")

            cases = generate_tests(inst, vasm_info)
            if not cases:
                if verbose:
                    print(f"  SKIP {mnemonic} (no tests generated)")
                skipped_mnemonics += 1
                continue

            for case in cases:
                # Cases can be 2-tuple (asm, desc) or 3-tuple (asm, desc, cpu_flag)
                if len(case) == 3:
                    asm_line, desc, case_cpu_flag = case
                else:
                    asm_line, desc = case
                    case_cpu_flag = None
                total += 1
                test_name = f"{mnemonic}: {desc}" if desc else mnemonic

                # Step 1: Assemble
                cpu_flag = case_cpu_flag or cpu_flag_override or VASM_CPU_FLAG_MAP[proc_min]
                orig_data = assemble(asm_line, tmpdir, cpu_flag, debug=debug_asm)
                if orig_data is None:
                    failures.append((test_name, asm_line, "ASSEMBLE FAILED"))
                    failed += 1
                    continue

                # Step 2: Disassemble
                # Derive disasm CPU from case-level flag if present
                if case_cpu_flag:
                    # Convert vasm flag "-m68020" to "68020"
                    case_cpu = case_cpu_flag.lstrip("-m")
                    disasm_max_cpu = max_cpu or case_cpu
                else:
                    disasm_max_cpu = max_cpu or proc_min
                try:
                    instructions = disassemble(orig_data, max_cpu=disasm_max_cpu)
                except DecodeError as e:
                    failures.append((test_name, asm_line, f"DISASM FAILED: {e}"))
                    failed += 1
                    continue
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
                    hex_str = parts[1].split("(")[0].split()[0]
                    try:
                        target_addr = int(hex_str, 16)
                    except ValueError:
                        failures.append((test_name, asm_line,
                                         f"DISASM UNPARSEABLE: '{disasm_text}'"))
                        failed += 1
                        continue
                    filler_size = target_addr - first_size
                    nops = max(0, filler_size // 2)
                    nop_lines = "\nnop" * nops
                    reasm_source = f"{parts[0]}.t{nop_lines}\n.t:"
                else:
                    reasm_source = disasm_text

                reasm_data = assemble(reasm_source, tmpdir, cpu_flag, debug=debug_asm)
                if reasm_data is None:
                    failures.append((test_name, asm_line,
                                     f"REASSEMBLE FAILED: '{reasm_source}'"))
                    failed += 1
                    continue

                try:
                    disassemble(reasm_data, max_cpu=disasm_max_cpu)
                except DecodeError as e:
                    failures.append((test_name, asm_line, f"REDISASM FAILED: {e}"))
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
    all_mnemonics = {inst["mnemonic"] for inst in kb_instructions}
    untested = all_mnemonics - tested_mnemonics
    print(f"--- Coverage ---")
    print(f"Mnemonics in KB:        {len(all_mnemonics)}")
    print(f"Tested:                 {len(tested_mnemonics)}")
    print(f"Generated test cases:   {total}")
    if untested:
        print(f"\nUntested mnemonics ({len(untested)}): {', '.join(sorted(untested))}")

    return failed == 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--filter", "-f", help="Test only mnemonics matching this")
    parser.add_argument("--max-cpu", help="Maximum CPU to permit in disassembler checks")
    parser.add_argument("--debug-asm", action="store_true", help="Print vasm output on assemble failure")
    args = parser.parse_args()

    success = run_tests(filter_mnemonic=args.filter, verbose=args.verbose, max_cpu=args.max_cpu, debug_asm=args.debug_asm)
    sys.exit(0 if success else 1)
