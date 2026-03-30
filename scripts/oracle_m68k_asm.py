"""Unified oracle test harness for KB-driven M68K assembler.

Generates test cases from m68k_instructions.json structured fields (forms,
ea_modes, sizes, constraints) and binary-diffs our assembler output against
an external oracle assembler.

Supported oracles:
  vasm   - vasmm68k_mot (direct invocation, raw binary output)
  devpac - DevPac GenAm 3.18 (via vamos, hunk output, sentinel batching)

Usage:
    python oracle_m68k_asm.py vasm [--verbose] [--filter MNEMONIC]
    python oracle_m68k_asm.py devpac [--verbose] [--filter MNEMONIC]
"""

import abc
import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT))
from m68k.m68k_asm import assemble_instruction

KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"
ORACLE_MAP = {
    "vasm": PROJ_ROOT / "knowledge" / "asm_vasm.json",
    "devpac": PROJ_ROOT / "knowledge" / "asm_devpac.json",
}


# ── KB loader ─────────────────────────────────────────────────────────────

JsonDict = dict[str, Any]
TestCase = tuple[str, str]
BranchTestCase = tuple[str, str, int]
AssembledCase = tuple[str, bytes, str, str, str, int]
FailureCase = tuple[str, str, str, str, str | None]
BatchInput = tuple[str, int]


def _load_kb() -> tuple[list[JsonDict], JsonDict]:
    with open(KNOWLEDGE, encoding="utf-8") as f:
        data = json.load(f)
    return data["instructions"], data["_meta"]


KB_INSTRUCTIONS, KB_META = _load_kb()
KB_BY_MNEMONIC = {inst["mnemonic"]: inst for inst in KB_INSTRUCTIONS}
CC_ALL = list(KB_META["condition_codes"])
IMM_ROUTING = KB_META["immediate_routing"]
EA_MODE_SIZES = KB_META["ea_mode_sizes"]


# ── EA mode to assembly syntax ────────────────────────────────────────────
# These are arbitrary valid operand values for testing — not from the PDF.

def _ea_syntax(mode: str, size: str | None = None) -> str:
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


def _imm_for_size(size: str | None) -> str:
    if size == "b":
        return "#$12"
    if size == "l":
        return "#$12345678"
    return "#$1234"


def _imm_for_constraint(constraint: JsonDict | None, size: str | None = None) -> str:
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


def _filter_020(modes: Sequence[str], ea_020_set: set[str]) -> list[str]:
    """Remove 020+-only EA modes."""
    return [m for m in modes if m not in ea_020_set]


def _filter_supported(modes: Sequence[str]) -> list[str]:
    """Keep only EA modes our assembler supports."""
    return [m for m in modes if m in SUPPORTED_EA_MODES]


def _filter_for_size(
    modes: Sequence[str],
    sz: str | None,
    mem_size_only: str | None = None,
    bit_op_sizes: JsonDict | None = None,
) -> list[str]:
    """Filter EA modes by size constraints from KB ea_mode_sizes."""
    result = []
    for mode in modes:
        if sz and sz not in EA_MODE_SIZES[mode]:
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


def _mnemonic_variants(inst_mnemonic: str) -> list[str]:
    """Return base mnemonic aliases: 'ASL, ASR' -> ['asl', 'asr']."""
    return [p.strip().lower() for p in re.split(r"[ ,]+", inst_mnemonic)
            if p.strip()]


def _form_mnemonics(
    inst_variants: Sequence[str],
    dir_variants: JsonDict | None,
    form_syntax: str,
) -> list[str] | None:
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

def generate_tests(inst: JsonDict) -> list[TestCase]:
    """Generate assembly test lines for one instruction from KB data.

    Returns list of (asm_line, description) tuples.
    Skips forms that our assembler can't handle yet.
    """
    mnemonic = inst["mnemonic"]
    proc_min = inst["processor_min"]
    sizes = inst["sizes"]
    ea = inst.get("ea_modes", {})
    forms = inst["forms"]
    constraints = inst.get("constraints", {})
    m_variants = _mnemonic_variants(mnemonic)

    # Skip 020+ instructions
    if proc_min != "68000":
        return []

    # Skip label-using instructions (branches, DBcc)
    if inst.get("uses_label"):
        return []

    tests: list[TestCase] = []

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

    def _add_direction_variants(start_idx: int, primary_mn: str, extra_mns: Sequence[str]) -> None:
        """Duplicate tests for direction variants (asl/asr from asl tests)."""
        for variant in extra_mns:
            for asm, desc in tests[start_idx:]:
                if asm.startswith((f"{primary_mn}.", f"{primary_mn} ")):
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
                    for _bit_val, mode_type in op_modes["values"].items():
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

def _generate_movem_tests() -> list[TestCase]:
    """Generate MOVEM tests using KB ea_modes_by_direction."""
    tests: list[TestCase] = []
    inst: JsonDict | None = None
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

def _generate_branch_tests() -> list[BranchTestCase]:
    """Generate branch/DBcc tests from KB uses_label instructions.

    Tests use absolute target addresses with a fixed pc=0x1000.
    Returns list of (asm_line, description, pc) tuples.
    """
    tests: list[BranchTestCase] = []
    pc = 0x1000

    for inst in KB_INSTRUCTIONS:
        if not inst.get("uses_label"):
            continue
        if inst["processor_min"] != "68000":
            continue

        mnemonic = inst["mnemonic"]
        constraints = inst.get("constraints", {})
        cc_param = constraints.get("cc_parameterized")
        sizes_68000 = constraints.get("sizes_68000")
        sizes = sizes_68000 if sizes_68000 is not None else inst["sizes"]
        forms = inst["forms"]

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
                              "fwd .b disp=10", pc))
            else:
                tests.append((f"{base_mn}.s ${target_b_fwd:x}",
                              "fwd .b disp=10", pc))

        # Backward .b: target = pc + 2 - 10 = pc - 8
        if "b" in sizes:
            target_b_bwd = pc - 8
            if is_dbcc:
                tests.append((f"{base_mn} d0,${target_b_bwd:x}",
                              "bwd .b disp=-10", pc))
            else:
                tests.append((f"{base_mn}.s ${target_b_bwd:x}",
                              "bwd .b disp=-10", pc))

        # Forward .w: target = pc + 2 + 200 = pc + 202
        if "w" in sizes:
            target_w_fwd = pc + 202
            if is_dbcc:
                tests.append((f"{base_mn} d0,${target_w_fwd:x}",
                              "fwd .w disp=200", pc))
            else:
                tests.append((f"{base_mn}.w ${target_w_fwd:x}",
                              "fwd .w disp=200", pc))

        # Backward .w: target = pc + 2 - 200 = pc - 198
        if "w" in sizes:
            target_w_bwd = pc - 198
            if is_dbcc:
                tests.append((f"{base_mn} d0,${target_w_bwd:x}",
                              "bwd .w disp=-200", pc))
            else:
                tests.append((f"{base_mn}.w ${target_w_bwd:x}",
                              "bwd .w disp=-200", pc))

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
    for alias_suffix, _canonical_suffix in cc_aliases.items():
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


# ── Divergence checks ────────────────────────────────────────────────────

def _build_imm_divergence_set(oracle_cfg: JsonDict) -> set[str]:
    """Extract the set of mnemonics where this oracle diverges on imm routing.

    Reads encoding_behaviors from the oracle JSON.  Our assembler always
    routes #imm to the dedicated immediate instruction (ADDI, CMPI, etc.).
    Oracles may differ:

    - "no_route" oracles (e.g. vasm -no-opt) keep the general-purpose
      encoding → affected_mnemonics diverge from us.
    - "auto_route" oracles (e.g. DevPac) route to immediate like us →
      affected_mnemonics agree with us, not_affected diverge.
    """
    divergent: set[str] = set()
    for behavior in oracle_cfg.get("encoding_behaviors", []):
        bid = behavior.get("id", "")
        if "imm" not in bid:
            continue
        affected = set(behavior.get("affected_mnemonics", []))
        not_affected = set(behavior.get("not_affected", []))
        if "no_route" in bid:
            # Oracle keeps general encoding for these → diverges from us
            divergent.update(mn for mn in affected if mn in IMM_ROUTING)
        elif "auto_route" in bid:
            # Oracle routes same as us for affected → not_affected diverge
            divergent.update(mn for mn in not_affected if mn in IMM_ROUTING)
    return divergent


def _check_known_divergence(
    mnemonic: str,
    asm: str,
    our_bytes: bytes,
    oracle_bytes: bytes,
    imm_divergence_set: set[str],
) -> str | None:
    """Check if mismatch is a known acceptable divergence.

    Returns a reason string if it's a known divergence, None otherwise.
    imm_divergence_set: mnemonics where this oracle encodes imm differently,
    built from oracle JSON encoding_behaviors.
    """
    if (mnemonic in imm_divergence_set
            and _is_imm_routing_divergence(mnemonic, asm, our_bytes,
                                           oracle_bytes)):
        return f"imm routing: {mnemonic}\u2192{IMM_ROUTING[mnemonic]}"
    if _is_commutative_match(mnemonic, our_bytes, oracle_bytes):
        return "commutative"
    return None


def _is_imm_routing_divergence(
    mnemonic: str,
    asm: str,
    our_bytes: bytes,
    oracle_bytes: bytes,
) -> bool:
    """Check if a mismatch is a known immediate routing divergence.

    We route ADD #imm -> ADDI (DevPac-style), some oracles keep the
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
    if len(our_bytes) != len(oracle_bytes):
        return False
    # Extension words must be identical (only opword differs)
    return our_bytes[2:] == oracle_bytes[2:]


def _is_commutative_match(mnemonic: str, our_bytes: bytes, oracle_bytes: bytes) -> bool:
    """Check if a mismatch is due to commutative register assignment.

    For instructions whose KB operation field indicates commutativity
    (e.g. EXG: "Rx <-> Ry"), swapping the two register fields in the opword
    produces identical behavior.  Accept as equivalent if swapping Rx/Ry
    in our encoding matches the oracle's encoding.
    """
    inst = KB_BY_MNEMONIC.get(mnemonic)
    if inst is None or len(our_bytes) != 2 or len(oracle_bytes) != 2:
        return False
    # Detect commutativity from KB operation field (exchange symbol)
    operation = inst.get("operation", "")
    if "\u2194" not in operation and "\u2190\u2192" not in operation:
        return False
    # Find the two REGISTER fields in the encoding
    enc = inst["encodings"][0]
    reg_fields = [f for f in enc["fields"]
                  if "REGISTER" in f["name"].upper()
                  and f["name"] not in ("0", "1")]
    if len(reg_fields) != 2:
        return False
    # Extract register values from our opword, swap them, rebuild
    our_word = struct.unpack(">H", our_bytes)[0]
    r0, r1 = reg_fields[0], reg_fields[1]
    r0_width = int(r0["width"])
    r1_width = int(r1["width"])
    r0_bit_lo = int(r0["bit_lo"])
    r1_bit_lo = int(r1["bit_lo"])
    mask0 = ((1 << r0_width) - 1) << r0_bit_lo
    mask1 = ((1 << r1_width) - 1) << r1_bit_lo
    val0 = (our_word & mask0) >> r0_bit_lo
    val1 = (our_word & mask1) >> r1_bit_lo
    # Rebuild with swapped register values
    swapped = (our_word & ~mask0 & ~mask1) | (val1 << r0_bit_lo) | (val0 << r1_bit_lo)
    oracle_word = struct.unpack(">H", oracle_bytes)[0]
    return bool(swapped == oracle_word)


# ── Hunk code extraction (for Amiga hunk format output) ──────────────────

HUNK_CODE_ID = 0x3E9
HUNK_END_ID = 0x3F2
HUNK_HEADER_ID = 0x3F3


def _extract_hunk_code(data: bytes) -> bytes | None:
    """Extract code bytes from an Amiga hunk executable.

    Returns the raw code bytes from the first HUNK_CODE section,
    stripped of long-word padding.
    """
    if len(data) < 4:
        return None
    magic = struct.unpack(">I", data[:4])[0]
    if magic != HUNK_HEADER_ID:
        return None

    # Skip HUNK_HEADER: magic, string_count(0), num_hunks, first, last, sizes
    pos = 4
    # resident library names (terminated by 0)
    while pos < len(data) - 4:
        name_longs = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4
        if name_longs == 0:
            break
        pos += name_longs * 4

    # table_size, first_hunk, last_hunk
    if pos + 12 > len(data):
        return None
    table_size, first_hunk, last_hunk = struct.unpack(">III", data[pos:pos + 12])
    pos += 12

    # hunk sizes
    num_hunks = last_hunk - first_hunk + 1
    pos += num_hunks * 4

    # Find HUNK_CODE
    while pos < len(data) - 4:
        hunk_id = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4
        if hunk_id == HUNK_CODE_ID:
            n_longs = struct.unpack(">I", data[pos:pos + 4])[0]
            pos += 4
            return data[pos:pos + n_longs * 4]
        if hunk_id == HUNK_END_ID:
            continue
        # Skip unknown hunk
        if pos + 4 <= len(data):
            n_longs = struct.unpack(">I", data[pos:pos + 4])[0]
            pos += 4 + n_longs * 4
        else:
            break
    return None


# ── Oracle drivers ────────────────────────────────────────────────────────

class OracleDriver(abc.ABC):
    """Base class for oracle assembler drivers."""

    def __init__(self, oracle_cfg: JsonDict, proj_root: Path) -> None:
        self.cfg = oracle_cfg
        self.proj_root = proj_root
        driver = oracle_cfg["driver"]
        self.exe_path = proj_root / driver["executable_path"]

    def setup(self) -> None:
        """Called before test run. Override for pre-run setup."""
        return

    def teardown(self) -> None:
        """Called after test run. Override for cleanup."""
        return

    @abc.abstractmethod
    def assemble_one(self, text: str, pc: int = 0) -> bytes | None:
        """Assemble one instruction, return bytes or None."""

    def assemble_batch(self, items: Sequence[BatchInput]) -> list[bytes | None] | None:
        """Assemble multiple (text, pc) items. Returns list of bytes|None.

        Default implementation calls assemble_one for each item.
        Override for batched invocation.
        """
        return [self.assemble_one(text, pc) for text, pc in items]

    def prepare_branch_text(self, asm_text: str, pc: int) -> str:
        """Convert branch asm text for this oracle. Default: unchanged."""
        return asm_text

    def smoke_test(self) -> bool:
        """Optional smoke test before main run. Returns True on success."""
        return True

    @property
    def supports_batching(self) -> bool:
        return False

    @property
    def batch_size(self) -> int:
        return 0


class VasmDriver(OracleDriver):
    """Direct invocation of vasm, raw binary output."""

    def __init__(self, oracle_cfg: JsonDict, proj_root: Path) -> None:
        super().__init__(oracle_cfg, proj_root)
        if sys.platform == "win32" and not self.exe_path.suffix:
            self.exe_path = self.exe_path.with_suffix(".exe")
        self.output_fmt = oracle_cfg["cli"]["output_formats"]["raw_binary"]
        self.no_opt = oracle_cfg["options"]["no_optimization"]

    def assemble_one(self, text: str, pc: int = 0) -> bytes | None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".s", delete=False,
                                         encoding="utf-8") as f:
            if pc:
                f.write(f" org ${pc:x}\n")
            f.write(f" {text}\n")
            f.flush()
            src_path = f.name
        out_path = src_path + ".bin"
        try:
            result = subprocess.run(
                [str(self.exe_path), self.output_fmt, self.no_opt,
                 "-o", out_path, src_path],
                capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return None
            with open(out_path, "rb") as f:
                return f.read()
        except Exception:
            return None
        finally:
            for p in (src_path, out_path):
                with suppress(OSError):
                    os.unlink(p)


class VamosDriver(OracleDriver):
    """Invocation via vamos (Amiga emulator), hunk output with sentinel batching."""

    def __init__(self, oracle_cfg: JsonDict, proj_root: Path) -> None:
        super().__init__(oracle_cfg, proj_root)
        self.cpu_select = oracle_cfg["options"]["cpu_select"]
        self.no_opt = oracle_cfg["options"]["no_optimization"]
        self.quiet = oracle_cfg["options"]["quiet"]
        output_file_option = oracle_cfg["options"]["output_file"]
        assert isinstance(output_file_option, str) and output_file_option, (
            "DevPac output_file option must be a non-empty string"
        )
        self.output_file_option = output_file_option
        self.win_temp = os.environ.get("TEMP", os.environ.get("TMP", ""))
        driver = oracle_cfg["driver"]
        self._batch_size = driver.get("batch_size", 50)
        sentinel_str = driver.get("sentinel_word", "0xA5A5")
        self._sentinel = int(sentinel_str, 16)
        self._sentinel_bytes = struct.pack(">H", self._sentinel)
        self._opts_bak = None
        include_root = oracle_cfg.get("local_include_root")
        assert include_root is None or isinstance(include_root, str), (
            "local_include_root must be a string when present"
        )
        self.local_include_root = include_root
        self._staged_include_dir: str | None = None
        self._include_arg: str | None = None

    def setup(self) -> None:
        # Temporarily rename GenAm.opts to prevent auto-load errors under vamos
        opts_file = self.cfg.get("platform_notes", {}).get(
            "auto_config", {}).get("opts_file")
        if opts_file:
            opts = self.exe_path.parent / opts_file
            bak = opts.with_suffix(".opts.bak")
            if opts.exists():
                opts.rename(bak)
                self._opts_bak = bak
        if self.local_include_root is not None:
            include_src = (self.proj_root / self.local_include_root).resolve()
            assert include_src.is_dir(), f"Missing local_include_root: {include_src}"
            staged_name = f"_oracle_devpac_include_{os.getpid()}"
            staged_dir = Path(self.win_temp) / staged_name
            if staged_dir.exists():
                shutil.rmtree(staged_dir)
            shutil.copytree(include_src, staged_dir)
            self._staged_include_dir = str(staged_dir)
            self._include_arg = f"TMP:{staged_name}/"

    def teardown(self) -> None:
        if self._opts_bak and self._opts_bak.exists():
            opts_name = self.cfg.get("platform_notes", {}).get(
                "auto_config", {}).get("opts_file", "GenAm.opts")
            opts = self.exe_path.parent / opts_name
            self._opts_bak.rename(opts)
        if self._staged_include_dir is not None:
            shutil.rmtree(self._staged_include_dir, ignore_errors=True)
            self._staged_include_dir = None
            self._include_arg = None

    def _write_source(self, path: str, lines: Sequence[str]) -> None:
        with open(path, "wb") as f:
            f.write(f" {self.cpu_select}\n".encode("latin-1"))
            f.write(f" {self.no_opt}\n".encode("latin-1"))
            for line in lines:
                f.write(f" {line}\n".encode("latin-1"))

    def _run_vamos(self, src_path: str, out_path: str, timeout: int = 15) -> subprocess.CompletedProcess[str]:
        src_name = os.path.basename(src_path)
        out_name = os.path.basename(out_path)
        if self.output_file_option == "TO <filename>":
            output_args = ["TO", f"TMP:{out_name}"]
        elif self.output_file_option == "-O<filename>":
            output_args = [f"-OTMP:{out_name}"]
        else:
            raise ValueError(
                f"Unsupported DevPac output_file option template: {self.output_file_option}"
            )
        cmd = [
            "vamos",
            "-V", f"TMP:{self.win_temp}",
            "--", str(self.exe_path),
            f"TMP:{src_name}",
            *output_args,
            self.quiet,
        ]
        if self._include_arg is not None:
            cmd.extend(["INCDIR", self._include_arg])
        return subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout)

    def assemble_one(self, text: str, pc: int = 0) -> bytes | None:
        src_name = f"_oracle_test_{os.getpid()}.s"
        out_name = f"_oracle_test_{os.getpid()}"
        src_path = os.path.join(self.win_temp, src_name)
        out_path = os.path.join(self.win_temp, out_name)
        try:
            self._write_source(src_path, [text])
            result = self._run_vamos(src_path, out_path)
            if result.returncode != 0 or not os.path.exists(out_path):
                return None
            with open(out_path, "rb") as f:
                return _extract_hunk_code(f.read())
        except Exception:
            return None
        finally:
            for p in (src_path, out_path):
                with suppress(OSError):
                    os.unlink(p)

    def assemble_batch(self, items: Sequence[BatchInput]) -> list[bytes | None] | None:
        """Assemble multiple items in one invocation using sentinel splitting."""
        src_name = f"_oracle_batch_{os.getpid()}.s"
        out_name = f"_oracle_batch_{os.getpid()}"
        src_path = os.path.join(self.win_temp, src_name)
        out_path = os.path.join(self.win_temp, out_name)
        texts = [text for text, pc in items]
        try:
            lines = []
            for text in texts:
                lines.append(text)
                lines.append(f"dc.w ${self._sentinel:X}")
            self._write_source(src_path, lines)
            result = self._run_vamos(src_path, out_path, timeout=30)
            if result.returncode != 0 or not os.path.exists(out_path):
                return None
            with open(out_path, "rb") as f:
                code = _extract_hunk_code(f.read())
            if code is None:
                return None
            # Split on sentinel to recover per-instruction bytes
            results: list[bytes | None] = []
            pos = 0
            for _ in texts:
                sentinel_pos = code.find(self._sentinel_bytes, pos)
                if sentinel_pos < 0:
                    results.append(None)
                    continue
                results.append(code[pos:sentinel_pos])
                pos = sentinel_pos + 2
            return results
        except Exception:
            return None
        finally:
            for p in (src_path, out_path):
                with suppress(OSError):
                    os.unlink(p)

    def prepare_branch_text(self, asm_text: str, pc: int) -> str:
        """Convert $target to *+N syntax (GenAm can't use ORG)."""
        parts = asm_text.rsplit("$", 1)
        if len(parts) != 2:
            return asm_text
        target = int(parts[1], 16)
        offset = target - pc
        star_expr = f"*+{offset}" if offset >= 0 else f"*-{-offset}"
        return parts[0] + star_expr

    def smoke_test(self) -> bool:
        print("Smoke test: oracle assembly...")
        smoke = self.assemble_one("move.l d0,d1")
        if smoke is None:
            print("FATAL: Oracle smoke test failed. Check vamos setup.")
            return False
        expected = b"\x22\x00"
        if smoke[:len(expected)] != expected:
            print(f"FATAL: Smoke test mismatch: {smoke.hex()} != {expected.hex()}")
            return False
        print(f"  OK: move.l d0,d1 -> {smoke.hex()}")
        return True

    @property
    def supports_batching(self) -> bool:
        return True

    @property
    def batch_size(self) -> int:
        return int(self._batch_size)


DRIVER_TYPES = {
    "direct": VasmDriver,
    "vamos": VamosDriver,
}


# ── Main test runner ──────────────────────────────────────────────────────

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Test KB-driven assembler against oracle")
    parser.add_argument("oracle", choices=sorted(ORACLE_MAP.keys()),
                        help="Oracle assembler to test against")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--filter", "-f", help="Filter by mnemonic substring")
    parser.add_argument("--limit", "-n", type=int, default=0,
                        help="Limit total tests (0=unlimited)")
    parser.add_argument("--batch-size", "-b", type=int, default=0,
                        help="Override batch size (0=use oracle default)")
    args = parser.parse_args(argv)

    # Load oracle config and create driver
    oracle_path = ORACLE_MAP[args.oracle]
    with open(oracle_path, encoding="utf-8") as f:
        oracle_cfg = json.load(f)
    driver_type = oracle_cfg["driver"]["type"]
    driver = DRIVER_TYPES[driver_type](oracle_cfg, PROJ_ROOT)

    if args.batch_size and isinstance(driver, VamosDriver):
        driver._batch_size = args.batch_size

    oracle_name = oracle_cfg["_meta"]["description"]
    print(f"Oracle: {oracle_name}")

    # Setup and smoke test
    driver.setup()
    try:
        if not driver.smoke_test():
            return 1
        return _run_tests(driver, oracle_cfg, args)
    finally:
        driver.teardown()


def _run_tests(driver: OracleDriver, oracle_cfg: JsonDict, args: Any) -> int:
    """Generate tests, run against oracle, report results."""
    t0 = time.time()
    imm_divergent = _build_imm_divergence_set(oracle_cfg)

    results: JsonDict = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "oracle_errors": 0,
        "known_divergences": 0,
        "failures": [],
        "tested_mnemonics": set(),
        "imm_divergent": imm_divergent,
    }

    # ── Collect all tests ─────────────────────────────────────────────
    # Each entry: (mnemonic, asm_text, desc, pc)
    all_tests: list[tuple[str, str, str, int]] = []

    for inst in KB_INSTRUCTIONS:
        mnemonic = inst["mnemonic"]
        if args.filter and args.filter.lower() not in mnemonic.lower():
            continue
        for asm, desc in generate_tests(inst):
            all_tests.append((mnemonic, asm, desc, 0))

    if not args.filter or "movem" in args.filter.lower():
        for asm, desc in _generate_movem_tests():
            all_tests.append(("MOVEM", asm, desc, 0))

    # Branch tests
    branch_tests = _generate_branch_tests()
    if args.filter:
        branch_tests = [t for t in branch_tests
                        if args.filter.lower() in
                        t[0].split(".")[0].split()[0].lower()]

    for asm, desc, pc in branch_tests:
        br_mn = asm.split(".")[0].split()[0].upper()
        all_tests.append((br_mn, asm, desc, pc))

    if args.limit:
        all_tests = all_tests[:args.limit]

    # ── Assemble with our assembler (fast, no subprocess) ─────────────
    assembled: list[AssembledCase] = []
    for mnemonic, asm, desc, pc in all_tests:
        try:
            our_bytes = assemble_instruction(asm, pc=pc)
        except Exception as e:
            if args.verbose:
                print(f"  ASM ERROR: {asm}: {e}")
            results["errors"] += 1
            results["failures"].append(
                (mnemonic, asm, desc, f"asm: {e}", None))
            continue
        # Prepare oracle-specific asm text
        oracle_text = driver.prepare_branch_text(asm, pc) if pc else asm
        assembled.append((mnemonic, our_bytes, asm, desc, oracle_text, pc))

    # ── Run against oracle ────────────────────────────────────────────
    if driver.supports_batching:
        batch_sz = driver.batch_size
        batch: list[AssembledCase] = []
        for item in assembled:
            mnemonic, our_bytes, asm, desc, oracle_text, pc = item
            batch.append(item)
            if len(batch) >= batch_sz:
                _run_batch(driver, batch, results, args)
                batch = []
        if batch:
            _run_batch(driver, batch, results, args)
    else:
        # No batching — assemble one at a time
        for mnemonic, our_bytes, asm, desc, oracle_text, pc in assembled:
            oracle_bytes = driver.assemble_one(oracle_text, pc=pc)
            _compare_one(mnemonic, our_bytes, asm, desc, oracle_bytes,
                         results, args)

    elapsed = time.time() - t0

    # ── Summary ───────────────────────────────────────────────────────
    total = (results["passed"] + results["failed"] + results["errors"]
             + results["known_divergences"])
    print(f"\n{'='*60}")
    print(f"Results: {results['passed']}/{total} passed, "
          f"{results['failed']} mismatches, "
          f"{results['errors']} assembler errors, "
          f"{results['oracle_errors']} oracle errors"
          + (f", {results['known_divergences']} known divergences"
             if results["known_divergences"] else ""))
    print(f"Tested mnemonics: {len(results['tested_mnemonics'])}")
    print(f"Time: {elapsed:.1f}s ({len(assembled)} instructions)")

    if results["failures"]:
        by_mn: dict[str, list[tuple[str, str, str, str | None]]] = {}
        for mn, asm, desc, ours, oracle in results["failures"]:
            by_mn.setdefault(mn, []).append((asm, desc, ours, oracle))
        print(f"\nFailures ({len(results['failures'])} total):")
        for mn, items in sorted(by_mn.items()):
            print(f"  {mn}:")
            for asm, _desc, ours, oracle in items[:5]:
                if oracle is None:
                    print(f"    {asm}: {ours}")
                else:
                    print(f"    {asm}: ours={ours} oracle={oracle}")
            if len(items) > 5:
                print(f"    ... and {len(items) - 5} more")

    return 0 if (results["failed"] == 0 and results["errors"] == 0) else 1


def _run_batch(driver: OracleDriver, batch: Sequence[AssembledCase], results: JsonDict, args: Any) -> None:
    """Run a batch of tests against oracle and accumulate results."""
    items = [(oracle_text, pc) for _, _, _, _, oracle_text, pc in batch]
    oracle_results = driver.assemble_batch(items)

    if oracle_results is None:
        # Batch failed — fall back to individual assembly
        for mnemonic, our_bytes, asm, desc, oracle_text, pc in batch:
            oracle_bytes = driver.assemble_one(oracle_text, pc=pc)
            _compare_one(mnemonic, our_bytes, asm, desc, oracle_bytes,
                         results, args)
        return

    for i, (mnemonic, our_bytes, asm, desc, _oracle_text, _pc) in enumerate(batch):
        oracle_bytes = oracle_results[i] if i < len(oracle_results) else None
        _compare_one(mnemonic, our_bytes, asm, desc, oracle_bytes,
                     results, args)


def _compare_one(
    mnemonic: str,
    our_bytes: bytes,
    asm: str,
    desc: str,
    oracle_bytes: bytes | None,
    results: JsonDict,
    args: Any,
) -> None:
    """Compare one instruction's output against oracle result."""
    if oracle_bytes is None:
        if args.verbose:
            print(f"  ORACLE ERROR: {asm}")
        results["oracle_errors"] += 1
        return

    if len(oracle_bytes) == 0:
        if args.verbose:
            print(f"  ORACLE EMPTY: {asm}")
        results["oracle_errors"] += 1
        return

    # Trim oracle output for hunk long-word padding (at most 2 bytes)
    oracle_code = oracle_bytes
    padding = len(oracle_bytes) - len(our_bytes)
    if 0 < padding <= 2 and oracle_bytes[len(our_bytes):] == b'\x00' * padding:
        oracle_code = oracle_bytes[:len(our_bytes)]

    if our_bytes == oracle_code:
        results["passed"] += 1
        results["tested_mnemonics"].add(mnemonic)
        if args.verbose:
            print(f"  OK: {asm}")
    else:
        reason = _check_known_divergence(mnemonic, asm, our_bytes, oracle_code,
                                                results["imm_divergent"])
        if reason:
            results["known_divergences"] += 1
            results["tested_mnemonics"].add(mnemonic)
            if args.verbose:
                print(f"  KNOWN: {asm} ({reason})")
        else:
            results["failed"] += 1
            results["tested_mnemonics"].add(mnemonic)
            print(f"  MISMATCH: {asm} ({desc})")
            print(f"    ours:   {our_bytes.hex()}")
            print(f"    oracle: {oracle_bytes.hex()}")
            results["failures"].append(
                (mnemonic, asm, desc, our_bytes.hex(), oracle_bytes.hex()))


if __name__ == "__main__":
    sys.exit(main())
