"""Test KB-driven assembler against vasm oracle — data-driven from knowledge base.

Generates test cases from m68k_instructions.json structured fields (forms,
ea_modes, sizes, constraints) and binary-diffs our assembler output against
vasm for each instruction × operand × size combination.

Skips:
  - 020+ instructions — assembler targets 68000
  - PC-relative EA modes — vasm adjusts displacement by -2, we encode raw

Usage:
    python test_m68k_asm.py [--verbose] [--filter MNEMONIC]
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT / "scripts"))

from m68k_asm import assemble_instruction  # noqa: E402

KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"
ORACLE_JSON = PROJ_ROOT / "knowledge" / "asm_vasm.json"


# ── KB loader ─────────────────────────────────────────────────────────────

def _load_kb():
    with open(KNOWLEDGE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("instructions", []), data.get("_meta", {})


def _load_oracle():
    with open(ORACLE_JSON, encoding="utf-8") as f:
        return json.load(f)


KB_INSTRUCTIONS, KB_META = _load_kb()
CC_ALL = list(KB_META["condition_codes"])
IMM_ROUTING = KB_META["immediate_routing"]

ORACLE = _load_oracle()
VASM = PROJ_ROOT / "tools" / ORACLE["cli"]["executable"]
if sys.platform == "win32" and not VASM.suffix:
    VASM = VASM.with_suffix(".exe")
VASM_OUTPUT_FMT = ORACLE["cli"]["output_formats"]["raw_binary"]
VASM_NO_OPT = ORACLE["options"]["no_optimization"]


# ── EA mode to assembly syntax ────────────────────────────────────────────
# These are arbitrary valid operand values for testing — not from the PDF.

def _ea_syntax(mode, size=None):
    """Generate assembly syntax for an EA mode."""
    if mode == "imm":
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
        # PC-relative modes excluded — displacement semantics differ
    }[mode]


def _imm_for_size(size):
    if size == "b":
        return "#$12"
    elif size == "l":
        return "#$12345678"
    return "#$1234"


def _imm_for_constraint(constraint, size=None):
    """Generate an immediate value satisfying the constraint's min/max range."""
    if constraint is None:
        return _imm_for_size(size)
    mn, mx = constraint["min"], constraint["max"]
    val = (mn + mx) // 2
    if val == 0 and mn >= 0:
        val = mn
    return f"#{val}"


# ── Filtering helpers ─────────────────────────────────────────────────────

# Modes our assembler can handle (excludes PC-relative)
SUPPORTED_EA_MODES = {"dn", "an", "ind", "postinc", "predec", "disp",
                      "index", "absw", "absl", "imm"}

# Operand types our assembler can't handle yet
UNSUPPORTED_OP_TYPES = {"reglist", "ctrl_reg", "rn", "bf_ea"}


def _filter_020(modes, ea_020_set):
    """Remove 020+-only EA modes."""
    return [m for m in modes if m not in ea_020_set]


def _filter_supported(modes):
    """Keep only EA modes our assembler supports."""
    return [m for m in modes if m in SUPPORTED_EA_MODES]


def _filter_for_size(modes, sz, mem_size_only=None, bit_op_sizes=None):
    """Filter EA modes by size constraints (An excluded for .b, etc.)."""
    result = []
    for mode in modes:
        if mode == "an" and sz == "b":
            continue
        if mem_size_only and mode not in ("dn", "an") and sz != mem_size_only:
            continue
        if bit_op_sizes:
            if mode == "dn" and sz != bit_op_sizes.get("dn"):
                continue
            if mode not in ("dn", "an") and sz != bit_op_sizes.get("memory"):
                continue
        result.append(mode)
    return result


def _mnemonic_variants(inst_mnemonic):
    """Return base mnemonic aliases: 'ASL, ASR' -> ['asl', 'asr']."""
    return [p.strip().lower() for p in re.split(r"[ ,]+", inst_mnemonic)
            if p.strip()]


def _form_mnemonics(inst_variants, dir_variants, form_syntax):
    """Resolve form syntax to concrete mnemonic list."""
    if not form_syntax:
        return [inst_variants[0]]

    raw = form_syntax.split(None, 1)[0]
    candidate = re.sub(r"[^a-z0-9]", "", raw.split(".", 1)[0].lower())

    if candidate in inst_variants:
        return [candidate]

    if dir_variants:
        base = (dir_variants.get("base") or "").lower()
        variants = [v.lower() for v in (dir_variants.get("variants") or [])
                    if v.strip()]
        if base and candidate.startswith(base):
            suffix = candidate[len(base):]
            if suffix and all(ch == "d" for ch in suffix):
                return variants

    return None


# ── KB-driven test generator ─────────────────────────────────────────────

def generate_tests(inst):
    """Generate assembly test lines for one instruction from KB data.

    Returns list of (asm_line, description) tuples.
    Skips forms that our assembler can't handle yet.
    """
    mnemonic = inst["mnemonic"]
    proc_min = inst.get("processor_min", "68000")
    sizes = inst.get("sizes", [])
    ea = inst.get("ea_modes", {})
    forms = inst.get("forms", [])
    constraints = inst.get("constraints", {})
    m_variants = _mnemonic_variants(mnemonic)

    # Skip 020+ instructions
    if proc_min != "68000":
        return []

    # Skip label-using instructions (branches, DBcc)
    if inst.get("uses_label"):
        return []

    tests = []

    imm_range = constraints.get("immediate_range")
    dir_variants = constraints.get("direction_variants")
    op_modes = constraints.get("operand_modes")
    mem_size_only = constraints.get("memory_size_only")
    bit_op_sizes = constraints.get("bit_op_sizes")
    sizes_68000 = constraints.get("sizes_68000")

    # EA mode sets from KB, filtered to supported and non-020+
    ea_020 = set()
    for role_modes in inst.get("ea_modes_020", {}).values():
        ea_020.update(role_modes)

    src_modes = _filter_supported(_filter_020(ea.get("src", []), ea_020))
    dst_modes = _filter_supported(_filter_020(ea.get("dst", []), ea_020))
    ea_modes = _filter_supported(_filter_020(ea.get("ea", []), ea_020))
    all_ea = src_modes or dst_modes or ea_modes

    effective_sizes = sizes_68000 if sizes_68000 is not None else sizes

    def _add_direction_variants(start_idx, primary_mn, extra_mns):
        """Duplicate tests for direction variants (asl/asr from asl tests)."""
        for variant in extra_mns:
            for asm, desc in tests[start_idx:]:
                if asm.startswith(f"{primary_mn}.") or asm.startswith(f"{primary_mn} "):
                    tests.append((variant + asm[len(primary_mn):],
                                  desc.replace(primary_mn, variant)))
                elif asm == primary_mn:
                    tests.append((variant, desc))

    for form in forms:
        if form.get("processor_020"):
            continue

        operands = form.get("operands", [])
        op_types = [o["type"] for o in operands]

        # Skip forms with unsupported operand types
        if any(t in UNSUPPORTED_OP_TYPES for t in op_types):
            continue

        form_syntax = form.get("syntax", "")
        form_mns = _form_mnemonics(m_variants, dir_variants, form_syntax)
        if form_mns is None:
            continue
        form_mn = form_mns[0]
        form_start = len(tests)

        # No operands
        if not op_types:
            tests.append((form_mn, "no-op"))
            _add_direction_variants(form_start, form_mn, form_mns[1:])
            continue

        # Determine form-specific size override
        form_size = None
        form_inst = form_syntax.split(None, 1)[0] if form_syntax else ""
        if "." in form_inst:
            sz_char = form_inst.split(".")[-1].lower()
            if sz_char in ("b", "w", "l"):
                form_size = sz_char

        iter_sizes = [form_size] if form_size else (effective_sizes or [None])

        for sz in iter_sizes:
            sfx = f".{sz}" if sz else ""
            imm = _imm_for_constraint(imm_range, sz) if imm_range else _imm_for_size(sz)

            # ── Route by operand type pattern ──

            if op_types == ["ea"] and all_ea:
                fmodes = _filter_for_size(all_ea, sz, mem_size_only, bit_op_sizes)
                for mode in fmodes:
                    op = _ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {op}",
                                  f"ea={mode} sz={sz}"))

            elif op_types == ["ea", "ea"] and src_modes and dst_modes:
                fsrc = _filter_for_size(src_modes, sz, mem_size_only, bit_op_sizes)
                fdst = _filter_for_size(dst_modes, sz, mem_size_only, bit_op_sizes)
                for mode in fsrc:
                    src = _ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {src},d1",
                                  f"src={mode} sz={sz}"))
                for mode in fdst:
                    if mode == "dn":
                        continue  # already tested as source
                    dst = _ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} d0,{dst}",
                                  f"dst={mode} sz={sz}"))

            elif op_types == ["dn", "ea"] and all_ea:
                if src_modes:
                    fsrc = _filter_for_size(src_modes, sz, mem_size_only, bit_op_sizes)
                    for mode in fsrc:
                        src = _ea_syntax(mode, sz)
                        tests.append((f"{form_mn}{sfx} {src},d1",
                                      f"src={mode} sz={sz}"))
                fdst = _filter_for_size(dst_modes or all_ea, sz, mem_size_only, bit_op_sizes)
                for mode in fdst:
                    dst = _ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} d0,{dst}",
                                  f"dst={mode} sz={sz}"))

            elif op_types == ["ea", "dn"]:
                fsrc = _filter_for_size(src_modes or all_ea, sz, mem_size_only, bit_op_sizes)
                for mode in fsrc:
                    src = _ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {src},d1",
                                  f"src={mode} sz={sz}"))

            elif op_types == ["ea", "an"]:
                fsrc = _filter_for_size(src_modes or all_ea, sz, mem_size_only, bit_op_sizes)
                for mode in fsrc:
                    src = _ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {src},a1",
                                  f"src={mode} sz={sz}"))

            elif op_types == ["imm", "ea"] and all_ea:
                fdst = _filter_for_size(dst_modes or all_ea, sz, mem_size_only, bit_op_sizes)
                if bit_op_sizes:
                    this_imm = "#4"
                    fdst = [m for m in fdst if m != "imm"]
                else:
                    this_imm = imm
                for mode in fdst:
                    dst = _ea_syntax(mode, sz)
                    tests.append((f"{form_mn}{sfx} {this_imm},{dst}",
                                  f"dst={mode} sz={sz}"))

            elif op_types == ["imm", "dn"]:
                tests.append((f"{form_mn}{sfx} {imm},d0",
                              f"imm sz={sz}"))

            elif op_types == ["predec", "predec"]:
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

            elif op_types == ["an", "imm"]:
                an_imm = _imm_for_constraint(imm_range, sz)
                tests.append((f"{form_mn} a6,{an_imm}", f"imm={an_imm}"))
                break  # LINK only has one size

            elif op_types == ["an"]:
                tests.append((f"{form_mn} a6", "a6"))

            elif op_types == ["dn"]:
                tests.append((f"{form_mn}{sfx} d0", f"d0 sz={sz}"))
                tests.append((f"{form_mn}{sfx} d7", f"d7 sz={sz}"))

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

            elif op_types == ["imm", "ccr"]:
                tests.append((f"{form_mn} #$12,ccr", "imm-to-ccr"))

            elif op_types == ["imm", "sr"]:
                tests.append((f"{form_mn} #$1234,sr", "imm-to-sr"))

            elif op_types == ["ea", "ccr"]:
                fsrc = _filter_for_size(src_modes or all_ea, "w")
                for mode in fsrc:
                    if mode == "imm":
                        continue
                    src = _ea_syntax(mode, "w")
                    tests.append((f"{form_mn} {src},ccr", f"ea={mode}-to-ccr"))

            elif op_types == ["ea", "sr"]:
                fsrc = _filter_for_size(src_modes or all_ea, "w")
                for mode in fsrc:
                    if mode == "imm":
                        continue
                    src = _ea_syntax(mode, "w")
                    tests.append((f"{form_mn} {src},sr", f"ea={mode}-to-sr"))

            elif op_types == ["sr", "ea"] or op_types == ["ccr", "ea"]:
                fdst = _filter_for_size(dst_modes or all_ea, "w")
                reg_name = "sr" if "sr" in op_types else "ccr"
                for mode in fdst:
                    if mode in ("an", "imm"):
                        continue
                    dst = _ea_syntax(mode, "w")
                    tests.append((f"{form_mn} {reg_name},{dst}",
                                  f"{reg_name}-to-ea={mode}"))

            elif op_types == ["usp", "an"]:
                tests.append((f"{form_mn} usp,a0", "usp-to-an"))

            elif op_types == ["an", "usp"]:
                tests.append((f"{form_mn} a0,usp", "an-to-usp"))

            elif op_types == ["disp", "dn"]:
                tests.append((f"{form_mn}{sfx} 0(a0),d0", f"mem-to-reg sz={sz}"))

            elif op_types == ["dn", "disp"]:
                tests.append((f"{form_mn}{sfx} d0,0(a0)", f"reg-to-mem sz={sz}"))

        _add_direction_variants(form_start, form_mn, form_mns[1:])

    # CC parameterization: expand base tests with all condition codes
    cc_param = constraints.get("cc_parameterized")
    if cc_param and tests:
        prefix = cc_param["prefix"]
        excluded = set(cc_param.get("excluded", []))
        codes = [c for c in CC_ALL if c not in excluded]
        m_lower = m_variants[0]
        cc_tests = []
        for cc in codes:
            full_mn = f"{prefix}{cc}"
            for asm, desc in tests:
                cc_tests.append((asm.replace(m_lower, full_mn, 1),
                                 f"{full_mn} {desc}"))
        # Also add CC alias variants (e.g. slo for scs)
        cc_aliases = KB_META["cc_aliases"]
        for alias_suffix, canonical_suffix in cc_aliases.items():
            if canonical_suffix in excluded:
                continue
            alias_mn = f"{prefix}{alias_suffix}"
            # Use first base test as template
            asm0, desc0 = tests[0]
            cc_tests.append((asm0.replace(m_lower, alias_mn, 1),
                             f"{alias_mn} alias {desc0}"))
        tests = cc_tests

    return tests


# ── MOVEM test generator (separate because of register list handling) ─────

def _generate_movem_tests():
    """Generate MOVEM tests using KB ea_modes_by_direction."""
    tests = []
    inst = None
    for i in KB_INSTRUCTIONS:
        if i["mnemonic"] == "MOVEM":
            inst = i
            break
    if not inst:
        return tests

    dir_modes = inst.get("ea_modes_by_direction", {})
    r2m_modes = set(dir_modes.get("reg-to-mem", []))
    m2r_modes = set(dir_modes.get("mem-to-reg", []))
    sizes = inst.get("sizes", [])

    for sz in sizes:
        sfx = f".{sz}"
        for mode in _filter_supported(list(r2m_modes)):
            ea_str = _ea_syntax(mode)
            if mode == "predec":
                ea_str = "-(a7)"
            tests.append((f"movem{sfx} d0-d3/a0-a1,{ea_str}",
                          f"reg-to-mem ea={mode} sz={sz}"))
        for mode in _filter_supported(list(m2r_modes)):
            ea_str = _ea_syntax(mode)
            if mode == "postinc":
                ea_str = "(a7)+"
            tests.append((f"movem{sfx} {ea_str},d0-d3/a0-a1",
                          f"mem-to-reg ea={mode} sz={sz}"))
    return tests


# ── Branch test generator ────────────────────────────────────────────────

def _generate_branch_tests():
    """Generate branch/DBcc tests from KB uses_label instructions.

    Tests use absolute target addresses with a fixed pc=0x1000.
    Returns list of (asm_line, description, pc, inst_size) tuples.
    The extra fields (pc, inst_size) distinguish branch tests from
    regular tests in the runner.
    """
    tests = []
    pc = 0x1000

    for inst in KB_INSTRUCTIONS:
        if not inst.get("uses_label"):
            continue
        if inst.get("processor_min", "68000") != "68000":
            continue

        mnemonic = inst["mnemonic"]
        constraints = inst.get("constraints", {})
        cc_param = constraints.get("cc_parameterized")
        sizes_68000 = constraints.get("sizes_68000")
        sizes = sizes_68000 if sizes_68000 is not None else inst.get("sizes", [])
        forms = inst.get("forms", [])

        # Determine form type: Bcc-style (1 label) or DBcc-style (dn + label)
        form_ops = []
        if forms:
            form_ops = [o["type"] for o in forms[0].get("operands", [])]

        is_dbcc = form_ops == ["dn", "label"]

        # Pick one CC variant for base test (use base mnemonic)
        base_mn = _mnemonic_variants(mnemonic)[0]

        # Forward .b: target = pc + 2 + 10 = pc + 12
        if "b" in sizes:
            target_b_fwd = pc + 12
            if is_dbcc:
                tests.append((f"{base_mn} d0,${target_b_fwd:x}",
                              f"fwd .b disp=10", pc))
            else:
                tests.append((f"{base_mn}.s ${target_b_fwd:x}",
                              f"fwd .b disp=10", pc))

        # Backward .b: target = pc + 2 - 10 = pc - 8
        if "b" in sizes:
            target_b_bwd = pc - 8
            if is_dbcc:
                tests.append((f"{base_mn} d0,${target_b_bwd:x}",
                              f"bwd .b disp=-10", pc))
            else:
                tests.append((f"{base_mn}.s ${target_b_bwd:x}",
                              f"bwd .b disp=-10", pc))

        # Forward .w: target = pc + 2 + 200 = pc + 202
        if "w" in sizes:
            target_w_fwd = pc + 202
            if is_dbcc:
                tests.append((f"{base_mn} d0,${target_w_fwd:x}",
                              f"fwd .w disp=200", pc))
            else:
                tests.append((f"{base_mn}.w ${target_w_fwd:x}",
                              f"fwd .w disp=200", pc))

        # Backward .w: target = pc + 2 - 200 = pc - 198
        if "w" in sizes:
            target_w_bwd = pc - 198
            if is_dbcc:
                tests.append((f"{base_mn} d0,${target_w_bwd:x}",
                              f"bwd .w disp=-200", pc))
            else:
                tests.append((f"{base_mn}.w ${target_w_bwd:x}",
                              f"bwd .w disp=-200", pc))

        # CC variants: test a representative subset from KB condition_codes
        if cc_param:
            prefix = cc_param["prefix"]
            excluded = set(cc_param.get("excluded", []))
            available = [c for c in CC_ALL if c not in excluded]
            # Sample up to 4 evenly spaced conditions from KB
            step = max(1, len(available) // 4)
            cc_sample = available[::step][:4]
            for cc in cc_sample:
                full_mn = f"{prefix}{cc}"
                target = pc + 20
                if is_dbcc:
                    tests.append((f"{full_mn} d0,${target:x}",
                                  f"{full_mn} fwd .w disp=18", pc))
                else:
                    if "b" in sizes:
                        tests.append((f"{full_mn}.s ${target:x}",
                                      f"{full_mn} fwd .b disp=18", pc))
                    if "w" in sizes:
                        target_w = pc + 502
                        tests.append((f"{full_mn}.w ${target_w:x}",
                                      f"{full_mn} fwd .w disp=500", pc))

    # CC alias tests — driven by KB _meta.cc_aliases
    cc_aliases = KB_META["cc_aliases"]
    for alias_suffix, canonical_suffix in cc_aliases.items():
        # Test alias with each cc-parameterized family (Bcc, DBcc, Scc)
        for inst in KB_INSTRUCTIONS:
            if not inst.get("uses_label"):
                continue
            if inst.get("processor_min", "68000") != "68000":
                continue
            cc_param = inst.get("constraints", {}).get("cc_parameterized")
            if not cc_param:
                continue
            prefix = cc_param["prefix"]
            alias_mn = f"{prefix}{alias_suffix}"
            form_ops = [o["type"] for o in inst.get("forms", [{}])[0].get("operands", [])]
            is_dbcc = form_ops == ["dn", "label"]
            target = pc + 20
            if is_dbcc:
                tests.append((f"{alias_mn} d0,${target:x}",
                              f"{alias_mn} alias fwd .w", pc))
            else:
                tests.append((f"{alias_mn}.w ${target:x}",
                              f"{alias_mn} alias fwd .w", pc))

    return tests


# ── Vasm oracle ───────────────────────────────────────────────────────────

def _vasm_assemble(text):
    """Assemble a single instruction with vasm, return bytes or None."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".s", delete=False,
                                     encoding="utf-8") as f:
        f.write(f" {text}\n")
        f.flush()
        src_path = f.name
    out_path = src_path + ".bin"
    try:
        result = subprocess.run(
            [str(VASM), VASM_OUTPUT_FMT, VASM_NO_OPT, "-o", out_path, src_path],
            capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None
        with open(out_path, "rb") as f:
            return f.read()
    except Exception:
        return None
    finally:
        for p in (src_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def _vasm_assemble_at(text, org=0x1000):
    """Assemble an instruction with vasm using org directive, return bytes."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".s", delete=False,
                                     encoding="utf-8") as f:
        f.write(f" org ${org:x}\n")
        f.write(f" {text}\n")
        f.flush()
        src_path = f.name
    out_path = src_path + ".bin"
    try:
        result = subprocess.run(
            [str(VASM), VASM_OUTPUT_FMT, VASM_NO_OPT, "-o", out_path, src_path],
            capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None
        with open(out_path, "rb") as f:
            return f.read()
    except Exception:
        return None
    finally:
        for p in (src_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def _is_imm_routing_divergence(mnemonic, asm, our_bytes, vasm_bytes):
    """Check if a mismatch is a known immediate routing divergence.

    We route ADD #imm → ADDI (DevPac-style), vasm -no-opt keeps the
    general-purpose encoding.  Both are valid M68K.

    Validates structurally: mnemonic must be in IMM_ROUTING, asm must have
    #imm as first operand, and both encodings must have the same length
    and identical extension words (only the opword differs).
    """
    if mnemonic not in IMM_ROUTING:
        return False
    # First operand must be immediate
    parts = asm.split(None, 1)
    if len(parts) < 2:
        return False
    operands = parts[1].split(",")
    if not operands[0].strip().startswith("#"):
        return False
    # Both encodings must have same length (both valid, just different opword)
    if len(our_bytes) != len(vasm_bytes):
        return False
    # Extension words must be identical (only opword differs)
    if our_bytes[2:] != vasm_bytes[2:]:
        return False
    return True


# ── Main test runner ──────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test assembler vs vasm")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--filter", "-f", help="Filter by mnemonic substring")
    args = parser.parse_args()

    passed = 0
    failed = 0
    errors = 0
    vasm_errors = 0
    skipped = 0
    known_divergences = 0
    failures = []
    tested_mnemonics = set()

    all_tests = []

    # Generate tests from KB
    for inst in KB_INSTRUCTIONS:
        mnemonic = inst["mnemonic"]
        if args.filter and args.filter.lower() not in mnemonic.lower():
            continue

        tests = generate_tests(inst)
        for asm, desc in tests:
            all_tests.append((mnemonic, asm, desc))

    # Add MOVEM tests (handled separately due to register lists)
    if not args.filter or "movem" in args.filter.lower():
        for asm, desc in _generate_movem_tests():
            all_tests.append(("MOVEM", asm, desc))

    for mnemonic, asm, desc in all_tests:
        # Our assembler
        try:
            our_bytes = assemble_instruction(asm)
        except Exception as e:
            if args.verbose:
                print(f"  ASM ERROR: {asm}: {e}")
            errors += 1
            failures.append((mnemonic, asm, desc, f"asm: {e}", None))
            continue

        # Vasm oracle
        vasm_bytes = _vasm_assemble(asm)
        if vasm_bytes is None:
            if args.verbose:
                print(f"  VASM ERROR: {asm}")
            vasm_errors += 1
            continue

        if our_bytes == vasm_bytes:
            passed += 1
            tested_mnemonics.add(mnemonic)
            if args.verbose:
                print(f"  OK: {asm}")
        elif _is_imm_routing_divergence(mnemonic, asm, our_bytes, vasm_bytes):
            # Known divergence: we route ADD #imm → ADDI (DevPac-style),
            # vasm -no-opt keeps the general encoding.  Both are valid.
            known_divergences += 1
            tested_mnemonics.add(mnemonic)
            if args.verbose:
                print(f"  KNOWN: {asm} (imm routing: {mnemonic}→{IMM_ROUTING[mnemonic]})")
        else:
            failed += 1
            tested_mnemonics.add(mnemonic)
            print(f"  MISMATCH: {asm} ({desc})")
            print(f"    ours: {our_bytes.hex()}")
            print(f"    vasm: {vasm_bytes.hex()}")
            failures.append((mnemonic, asm, desc, our_bytes.hex(), vasm_bytes.hex()))

    # ── Branch tests (separate loop — need pc and vasm org) ──────────
    branch_tests = _generate_branch_tests()
    if args.filter:
        branch_tests = [t for t in branch_tests
                        if args.filter.lower() in t[0].split(".")[0].split()[0].lower()]

    for asm, desc, pc in branch_tests:
        # Our assembler
        try:
            our_bytes = assemble_instruction(asm, pc=pc)
        except Exception as e:
            if args.verbose:
                print(f"  ASM ERROR: {asm} @pc={pc:#x}: {e}")
            errors += 1
            failures.append(("BRANCH", asm, desc, f"asm: {e}", None))
            continue

        # Vasm oracle (with org to set same pc)
        vasm_bytes = _vasm_assemble_at(asm, org=pc)
        if vasm_bytes is None:
            if args.verbose:
                print(f"  VASM ERROR: {asm} @pc={pc:#x}")
            vasm_errors += 1
            continue

        if our_bytes == vasm_bytes:
            passed += 1
            # Extract mnemonic for tracking
            br_mn = asm.split(".")[0].split()[0].upper()
            tested_mnemonics.add(br_mn)
            if args.verbose:
                print(f"  OK: {asm} @pc={pc:#x}")
        else:
            failed += 1
            br_mn = asm.split(".")[0].split()[0].upper()
            tested_mnemonics.add(br_mn)
            print(f"  MISMATCH: {asm} @pc={pc:#x} ({desc})")
            print(f"    ours: {our_bytes.hex()}")
            print(f"    vasm: {vasm_bytes.hex()}")
            failures.append((br_mn, asm, desc, our_bytes.hex(), vasm_bytes.hex()))

    total = passed + failed + errors + known_divergences
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed, {failed} mismatches, "
          f"{errors} assembler errors, {vasm_errors} vasm errors"
          + (f", {known_divergences} known divergences" if known_divergences else ""))
    print(f"Tested mnemonics: {len(tested_mnemonics)}")

    if failures:
        # Group by mnemonic
        by_mn = {}
        for mn, asm, desc, ours, vasm in failures:
            by_mn.setdefault(mn, []).append((asm, desc, ours, vasm))
        print(f"\nFailures ({len(failures)} total):")
        for mn, items in sorted(by_mn.items()):
            print(f"  {mn}:")
            for asm, desc, ours, vasm in items[:5]:
                if vasm is None:
                    print(f"    {asm}: {ours}")
                else:
                    print(f"    {asm}: ours={ours} vasm={vasm}")
            if len(items) > 5:
                print(f"    ... and {len(items) - 5} more")

    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
