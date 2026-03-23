"""M68K disassembler round-trip tests -- KB-driven, batch-assembled.

Generates test cases from m68k_instructions.json + vasm_compat.json.
Batch assembly via vasm for performance (~0.3s for all ~1800 cases).
Each test: assemble -> disassemble -> reassemble -> binary compare.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeAlias, cast

import pytest

from m68k.hunk_parser import parse_file
from m68k.decode_errors import DecodeError
from m68k.m68k_disasm import disassemble


# -- Paths ----------------------------------------------------------------

PROJ_ROOT = Path(__file__).resolve().parent.parent
VASM = PROJ_ROOT / "tools" / "vasmm68k_mot.exe"
KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"
VASM_COMPAT = PROJ_ROOT / "knowledge" / "vasm_compat.json"

JsonDict: TypeAlias = dict[str, Any]
CaseSpec: TypeAlias = tuple[str, str] | tuple[str, str, str]
DisasmInfo: TypeAlias = tuple[str | None, bytes | None, str | None]
_FixtureDecorator: TypeAlias = Callable[[Callable[..., list[str | None]]], Callable[..., list[str | None]]]
_TestFn: TypeAlias = Callable[..., object]
_Decorator: TypeAlias = Callable[[_TestFn], _TestFn]


# -- KB + vasm compat loading ---------------------------------------------

def _load_kb() -> tuple[list[JsonDict], JsonDict]:
    with open(KNOWLEDGE, encoding="utf-8") as f:
        data = cast(JsonDict, json.load(f))
    instructions = cast(list[JsonDict], data["instructions"])
    meta = cast(JsonDict, data["_meta"])
    if "condition_codes" not in meta:
        raise RuntimeError("KB _meta missing 'condition_codes'")
    return instructions, meta


def _load_vasm_compat() -> JsonDict:
    with open(VASM_COMPAT, encoding="utf-8") as f:
        return cast(JsonDict, json.load(f))


KB_INSTRUCTIONS, KB_META = _load_kb()
VASM_DATA = _load_vasm_compat()
VASM_META = cast(JsonDict, VASM_DATA["_meta"])
CPU_FLAG_MAP = cast(dict[str, str], VASM_META["default_cpu_flag_map"])
EA_SYNTAX = cast(dict[str, str], VASM_META["ea_mode_syntax"])
TEST_IMM = cast(dict[str, str], VASM_META["test_immediate_values"])
INST_COMPAT = cast(dict[str, JsonDict], VASM_DATA["instructions"])
BRANCH_SIZE_MAP = cast(dict[str, JsonDict], VASM_DATA["branch_size_map"])
CC_ALL = cast(list[str], list(KB_META["condition_codes"]))
KB_BY_MNEMONIC = {i["mnemonic"].lower(): i for i in KB_INSTRUCTIONS}
LABEL_MNEMONICS = frozenset(
    i["mnemonic"] for i in KB_INSTRUCTIONS if i.get("uses_label"))


# -- Test case ------------------------------------------------------------

@dataclass(frozen=True)
class Case:
    asm: str
    desc: str
    cpu_flag: str
    mnemonic: str
    max_cpu: str

    @property
    def test_id(self) -> str:
        d = self.desc.replace(" ", "_") if self.desc else ""
        return f"{self.mnemonic}:{d}" if d else self.mnemonic


# -- EA / immediate helpers (KB-driven from vasm_compat) ------------------

def ea_syntax(mode: str, size: str | None = None, imm_val: str | None = None) -> str:
    """Assembly syntax for an EA mode, from vasm_compat ea_mode_syntax."""
    if mode == "imm":
        if imm_val is not None:
            return f"#{imm_val}"
        if size is None:
            return TEST_IMM["w"]
        return TEST_IMM.get(size, TEST_IMM["w"])
    return EA_SYNTAX[mode]


def _imm_for_size(size: str | None) -> str:
    if size is None:
        return TEST_IMM["w"]
    return TEST_IMM.get(size, TEST_IMM["w"])


def _imm_for_constraint(constraint: JsonDict | None, size: str | None = None) -> str:
    if constraint is None:
        return _imm_for_size(size)
    mn, mx = constraint["min"], constraint["max"]
    val = (mn + mx) // 2
    if val == 0 and mn >= 0:
        val = mn
    return f"#{val}"


def _is_memory_ea(mode: str) -> bool:
    return mode not in ("dn", "an")


def _filter_modes_for_size(modes: list[str], sz: str | None,
                           mem_size_only: str | None = None,
                           bit_op_sizes: JsonDict | None = None) -> list[str]:
    result: list[str] = []
    for mode in modes:
        if mode == "an" and sz == "b":
            continue
        if mem_size_only and _is_memory_ea(mode) and sz != mem_size_only:
            continue
        if bit_op_sizes:
            if mode == "dn" and sz != bit_op_sizes.get("dn"):
                continue
            if _is_memory_ea(mode) and sz != bit_op_sizes.get("memory"):
                continue
        result.append(mode)
    return result


def _mnemonic_variants(inst_mnemonic: str) -> list[str]:
    return [p.strip().lower() for p in re.split(r"[ ,]+", inst_mnemonic) if p.strip()]


def _form_mnemonics(m_variants: list[str], dir_variants: JsonDict | None,
                    form_syntax: str) -> list[str]:
    if not form_syntax:
        return [m_variants[0]]
    raw = form_syntax.split(None, 1)[0]
    candidate = re.sub(r"[^a-z0-9]", "", raw.split(".", 1)[0].lower())
    if candidate in m_variants:
        return [candidate]
    if dir_variants:
        base = (dir_variants.get("base") or "").lower()
        variants = [v.lower() for v in (dir_variants.get("variants") or []) if v.strip()]
        if base and candidate.startswith(base):
            suffix = candidate[len(base):]
            if suffix and all(ch == "d" for ch in suffix):
                return variants
    raise RuntimeError(
        f"Unresolved form syntax: '{form_syntax}' not in {m_variants}")


# -- Test generation (from KB forms/ea_modes/sizes/constraints) -----------

def _gen_label_tests(m_lower: str, op_types: list[str], cc_param: JsonDict | None,
                     sizes: list[str]) -> list[tuple[str, str]]:
    tests: list[tuple[str, str]] = []
    if cc_param:
        excluded = set(cc_param.get("excluded", []))
        mnemonics = [f"{cc_param['prefix']}{cc}"
                     for cc in CC_ALL if cc not in excluded]
    else:
        mnemonics = [m_lower]

    branch_sizes: list[tuple[str, bool]] = []
    if sizes:
        for sz in sizes:
            if sz in BRANCH_SIZE_MAP:
                entry = BRANCH_SIZE_MAP[sz]
                if entry.get("skip_for_68000"):
                    continue
                branch_sizes.append((cast(str, entry["suffix"]).lstrip("."),
                                     cast(bool, entry.get("needs_nop_filler", False))))
    else:
        branch_sizes.append(("w", False))

    has_dn = "dn" in op_types
    for mn in mnemonics:
        if has_dn:
            for sz_sfx, _ in branch_sizes:
                tests.append((f"{mn} d0,.t\n.t:", mn))
        else:
            for sz_sfx, needs_nop in branch_sizes:
                if needs_nop:
                    tests.append((f"{mn}.{sz_sfx} .t\nnop\n.t:", f"{mn}.{sz_sfx}"))
                else:
                    tests.append((f"{mn}.{sz_sfx} .t\n.t:", f"{mn}.{sz_sfx}"))
    return tests


def _gen_movem_tests(m_lower: str, sz: str | None, modes: list[str],
                     movem_dir: object) -> list[tuple[str, str]]:
    sfx = f".{sz}" if sz else ""
    inst_data = KB_BY_MNEMONIC.get(m_lower)
    if not inst_data:
        raise RuntimeError(f"{m_lower}: not found in KB")
    dir_modes = inst_data.get("ea_modes_by_direction")
    if not dir_modes:
        raise RuntimeError(f"{m_lower}: KB missing ea_modes_by_direction")
    r2m = set(dir_modes["reg-to-mem"])
    m2r = set(dir_modes["mem-to-reg"])
    tests: list[tuple[str, str]] = []
    for mode in modes:
        ea_str = ea_syntax(mode)
        if mode in r2m:
            if mode == "predec":
                ea_str = "-(a7)"
            tests.append((f"{m_lower}{sfx} d0-d3/a0-a1,{ea_str}",
                          f"reg-to-mem ea={mode} sz={sz}"))
        if mode in m2r:
            if mode == "postinc":
                ea_str = "(a7)+"
            tests.append((f"{m_lower}{sfx} {ea_str},d0-d3/a0-a1",
                          f"mem-to-reg ea={mode} sz={sz}"))
    return tests


def _gen_long_mul_div_tests(mnemonic: str) -> list[tuple[str, str, str]]:
    cpu = "-m68020"
    tests: list[tuple[str, str, str]] = []
    m = mnemonic.upper()
    if m in ("MULS", "MULU"):
        name = m.lower()
        tests.append((f"{name}.l d0,d1", f"{name}.l 32-bit", cpu))
        tests.append((f"{name}.l d0,d2:d1", f"{name}.l 64-bit", cpu))
        tests.append((f"{name}.l (a0),d3", f"{name}.l ind", cpu))
        tests.append((f"{name}.l #$1234,d4", f"{name}.l imm", cpu))
    elif m == "DIVS, DIVSL":
        tests.append(("divs.l d0,d1", "divs.l 32q", cpu))
        tests.append(("divsl.l d0,d2:d1", "divsl.l 32r:32q", cpu))
        tests.append(("divs.l d0,d2:d1", "divs.l 64/32", cpu))
        tests.append(("divs.l (a0),d3", "divs.l ind", cpu))
    elif m == "DIVU, DIVUL":
        tests.append(("divu.l d0,d1", "divu.l 32q", cpu))
        tests.append(("divul.l d0,d2:d1", "divul.l 32r:32q", cpu))
        tests.append(("divu.l d0,d2:d1", "divu.l 64/32", cpu))
        tests.append(("divu.l #$1234,d4", "divu.l imm", cpu))
    return tests


def _generate_tests(inst: JsonDict, compat: JsonDict | None = None) -> list[CaseSpec]:
    """Generate all test cases for one KB instruction."""
    mnemonic = inst["mnemonic"]
    sizes = inst.get("sizes", [])
    ea = inst.get("ea_modes", {})
    forms = inst.get("forms", [])
    constraints = inst.get("constraints", {})
    m_variants = _mnemonic_variants(mnemonic)
    m_lower = m_variants[0]

    tests: list[CaseSpec] = []
    ea_020 = inst.get("ea_modes_020", {}) if inst.get("processor_min", "68000") == "68000" else {}

    def filt020(modes: list[str], role: str) -> list[str]:
        exc = set(ea_020.get(role, []))
        return [m for m in modes if m not in exc] if exc else modes

    src_modes = filt020(ea.get("src", []), "src")
    dst_modes = filt020(ea.get("dst", []), "dst")
    ea_modes = filt020(ea.get("ea", []), "ea")
    all_ea_modes = src_modes or dst_modes or ea_modes

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
    effective_sizes = sizes_68000 if sizes_68000 is not None else sizes

    def _emit_dir(start: int, primary: str, extras: list[str]) -> None:
        for v in extras:
            for case in tests[start:]:
                asm, desc = case[0], case[1]
                if asm == primary:
                    tests.append((v, desc))
                elif asm.startswith(f"{primary}.") or asm.startswith(f"{primary} "):
                    tests.append((v + asm[len(primary):], desc))

    for form in forms:
        if form.get("processor_020"):
            continue
        raw_form = form.get("syntax", "").split(None, 1)[0].lower()
        if raw_form and any(raw_form.startswith(p) for p in skip_form_prefixes):
            continue

        operands = form.get("operands", [])
        op_types = [o["type"] for o in operands]
        form_syntax = form.get("syntax", "")
        form_mns = _form_mnemonics(m_variants, dir_variants, form_syntax)
        form_mn = form_mns[0]
        form_start = len(tests)

        if not op_types:
            tests.append((form_mn, ""))
            _emit_dir(form_start, form_mn, form_mns[1:])
            continue

        if "label" in op_types:
            tests.extend(_gen_label_tests(m_lower, op_types, cc_param, effective_sizes))
            continue

        form_size = None
        fi = form_syntax.split(None, 1)[0] if form_syntax else ""
        if "." in fi:
            sz_char = fi.split(".")[-1].lower()
            if sz_char in ("b", "w", "l"):
                form_size = sz_char

        iter_sizes = [form_size] if form_size else (effective_sizes or [None])

        for sz in iter_sizes:
            sfx = f".{sz}" if sz else ""
            imm = _imm_for_constraint(imm_range, sz) if imm_range else _imm_for_size(sz)

            if op_types == ["ea"] and all_ea_modes:
                for mode in _filter_modes_for_size(all_ea_modes, sz, mem_size_only, bit_op_sizes):
                    tests.append((f"{form_mn}{sfx} {ea_syntax(mode, sz)}", f"ea={mode} sz={sz}"))

            elif op_types == ["ea", "ea"] and src_modes and dst_modes:
                for mode in _filter_modes_for_size(src_modes, sz, mem_size_only, bit_op_sizes):
                    tests.append((f"{form_mn}{sfx} {ea_syntax(mode, sz)},d1", f"src={mode} sz={sz}"))
                for mode in _filter_modes_for_size(dst_modes, sz, mem_size_only, bit_op_sizes):
                    if mode == "dn":
                        continue
                    tests.append((f"{form_mn}{sfx} d0,{ea_syntax(mode, sz)}", f"dst={mode} sz={sz}"))

            elif op_types == ["dn", "ea"] and all_ea_modes:
                if src_modes:
                    for mode in _filter_modes_for_size(src_modes, sz, mem_size_only, bit_op_sizes):
                        tests.append((f"{form_mn}{sfx} {ea_syntax(mode, sz)},d1", f"src={mode} sz={sz}"))
                for mode in _filter_modes_for_size(dst_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes):
                    tests.append((f"{form_mn}{sfx} d0,{ea_syntax(mode, sz)}", f"dst={mode} sz={sz}"))

            elif op_types == ["ea", "dn"]:
                for mode in _filter_modes_for_size(src_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes):
                    tests.append((f"{form_mn}{sfx} {ea_syntax(mode, sz)},d1", f"src={mode} sz={sz}"))

            elif op_types == ["ea", "an"]:
                for mode in _filter_modes_for_size(src_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes):
                    tests.append((f"{form_mn}{sfx} {ea_syntax(mode, sz)},a1", f"src={mode} sz={sz}"))

            elif op_types == ["imm", "ea"] and all_ea_modes:
                fdst = _filter_modes_for_size(dst_modes or all_ea_modes, sz, mem_size_only, bit_op_sizes)
                if bit_op_sizes:
                    this_imm = "#4"
                    fdst = [m for m in fdst if m != "imm"]
                else:
                    this_imm = imm
                for mode in fdst:
                    tests.append((f"{form_mn}{sfx} {this_imm},{ea_syntax(mode, sz)}", f"dst={mode} sz={sz}"))

            elif op_types == ["imm", "dn"]:
                tests.append((f"{form_mn}{sfx} {imm},d0", f"imm sz={sz}"))

            elif op_types == ["ea", "reglist"]:
                tests.extend(_gen_movem_tests(m_lower, sz, all_ea_modes, movem_dir))

            elif op_types == ["reglist", "ea"]:
                pass  # handled by ea,reglist

            elif op_types == ["predec", "predec"]:
                if op_modes:
                    for _, mode_type in op_modes["values"].items():
                        if mode_type == "predec,predec":
                            tests.append((f"{form_mn}{sfx} -(a0),-(a1)", f"predec sz={sz}"))
                        elif mode_type == "dn,dn":
                            tests.append((f"{form_mn}{sfx} d0,d1", f"reg sz={sz}"))
                else:
                    tests.append((f"{form_mn}{sfx} -(a0),-(a1)", f"predec sz={sz}"))

            elif op_types == ["postinc", "postinc"]:
                tests.append((f"{form_mn}{sfx} (a0)+,(a1)+", f"postinc sz={sz}"))

            elif op_types == ["sr", "ea"]:
                for mode in (dst_modes or all_ea_modes):
                    tests.append((f"{form_mn}{sfx} sr,{ea_syntax(mode, sz)}", f"dst={mode}"))
                break
            elif op_types == ["ea", "sr"]:
                for mode in (src_modes or all_ea_modes):
                    tests.append((f"{form_mn}{sfx} {ea_syntax(mode, sz)},sr", f"src={mode}"))
                break
            elif op_types == ["ea", "ccr"]:
                for mode in (src_modes or all_ea_modes):
                    tests.append((f"{form_mn}{sfx} {ea_syntax(mode, sz)},ccr", f"src={mode}"))
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
                for mode in _filter_modes_for_size(dst_modes or all_ea_modes, sz):
                    tests.append((f"{form_mn} ccr,{ea_syntax(mode, sz)}", f"dst={mode}"))
                break
            elif op_types == ["rn"]:
                tests.append((f"{form_mn} d0", "dn"))
                tests.append((f"{form_mn} a0", "an"))
            elif op_types == ["rn", "ea"]:
                for mode in _filter_modes_for_size(all_ea_modes, sz):
                    tests.append((f"{form_mn}{sfx} d0,{ea_syntax(mode, sz)}", f"rn-to={mode}"))
            elif op_types == ["ea", "rn"]:
                for mode in _filter_modes_for_size(all_ea_modes, sz):
                    tests.append((f"{form_mn}{sfx} {ea_syntax(mode, sz)},d0", f"ea-to-rn={mode}"))
            elif op_types == ["ctrl_reg", "rn"]:
                ctrl_regs = constraints.get("control_registers")
                if not ctrl_regs:
                    raise RuntimeError(f"{mnemonic}: KB missing control_registers")
                seen = set()
                for cr in ctrl_regs:
                    abbrev = cr["abbrev"]
                    if abbrev not in seen:
                        seen.add(abbrev)
                        cpu = CPU_FLAG_MAP[cast(str, cr.get("processor_min", "68010"))]
                        tests.append((f"{form_mn} {abbrev},d0", f"{abbrev}-to-d0", cpu))
                break
            elif op_types == ["rn", "ctrl_reg"]:
                ctrl_regs = constraints.get("control_registers")
                if not ctrl_regs:
                    raise RuntimeError(f"{mnemonic}: KB missing control_registers")
                seen = set()
                for cr in ctrl_regs:
                    abbrev = cr["abbrev"]
                    if abbrev not in seen:
                        seen.add(abbrev)
                        cpu = CPU_FLAG_MAP[cast(str, cr.get("processor_min", "68010"))]
                        tests.append((f"{form_mn} d0,{abbrev}", f"d0-to-{abbrev}", cpu))
                break
            elif op_types == ["bf_ea"]:
                for mode in _filter_modes_for_size(all_ea_modes, sz):
                    tests.append((f"{form_mn} {ea_syntax(mode)}{{2:8}}", f"ea={mode}"))
            elif op_types == ["bf_ea", "dn"]:
                for mode in _filter_modes_for_size(all_ea_modes, sz):
                    tests.append((f"{form_mn} {ea_syntax(mode)}{{2:8}},d1", f"ea={mode}"))
            elif op_types == ["dn", "bf_ea"]:
                for mode in _filter_modes_for_size(all_ea_modes, sz):
                    tests.append((f"{form_mn} d0,{ea_syntax(mode)}{{2:8}}", f"ea={mode}"))
            elif op_types == ["dn", "dn", "imm"]:
                tests.append((f"{form_mn} d0,d1,#0", "reg-reg"))
            elif op_types == ["predec", "predec", "imm"]:
                tests.append((f"{form_mn} -(a0),-(a1),#0", "mem-mem"))
            elif op_types == ["dn", "dn", "ea"]:
                for mode in _filter_modes_for_size(all_ea_modes, sz):
                    tests.append((f"{form_mn}{sfx} d0,d1,{ea_syntax(mode, sz)}", f"ea={mode}"))

        _emit_dir(form_start, form_mn, form_mns[1:])

    # CC expansion
    if cc_param and not inst.get("uses_label", False):
        prefix = cc_param["prefix"]
        excluded = set(cc_param.get("excluded", []))
        codes = [c for c in CC_ALL if c not in excluded]
        if prefix and tests:
            cc_tests: list[CaseSpec] = []
            for cc in codes:
                full = f"{prefix}{cc}"
                for case in tests:
                    asm, desc = case[0], case[1]
                    cc_tests.append((asm.replace(m_lower, full, 1), f"{full} {desc}"))
            tests = cc_tests

    if mnemonic in ("MULS", "MULU", "DIVS, DIVSL", "DIVU, DIVUL"):
        tests.extend(_gen_long_mul_div_tests(mnemonic))

    return tests


# -- Generate all cases ---------------------------------------------------

def _generate_all_cases() -> list[Case]:
    cases: list[Case] = []
    for inst in KB_INSTRUCTIONS:
        mnemonic = inst["mnemonic"]
        vasm_info = INST_COMPAT.get(mnemonic, {})
        if vasm_info.get("supported") is False:
            continue
        proc_min = inst.get("processor_min", "68000")
        cpu_override = vasm_info.get("cpu_flag")
        raw_cases = _generate_tests(inst, vasm_info)
        for case in raw_cases:
            if len(case) == 3:
                asm, desc, case_cpu = case
            else:
                asm, desc = case
                case_cpu = None
            cpu = case_cpu or cpu_override or CPU_FLAG_MAP[proc_min]
            max_cpu = case_cpu.lstrip("-m") if case_cpu else proc_min
            cases.append(Case(asm, desc, cpu, mnemonic, max_cpu))
    return cases


# -- Batch assembly -------------------------------------------------------

def _batch_assemble(cases: list[Case], cpu_flag: str, tmpdir: str) -> list[bytes]:
    """Assemble multiple cases in a single vasm call.

    Returns list of bytes for each case (instruction + trailing scaffolding).
    Uses per-case labels for offset extraction from the symbol table.
    Branch label .t is mangled to ._l{i} to avoid collisions.
    """
    lines = ["    section code,code"]
    for i, case in enumerate(cases):
        lines.append(f"_t{i}:")
        mangled = re.sub(r"\.t\b", f"._l{i}", case.asm)
        for part in mangled.split("\n"):
            part = part.strip()
            if not part:
                continue
            if part.endswith(":"):
                lines.append(part)
            else:
                lines.append(f"    {part}")
    lines.append("_end:")
    source = "\n".join(lines) + "\n"

    src_path = os.path.join(tmpdir, f"batch_{cpu_flag.lstrip('-')}.s")
    obj_path = src_path[:-2] + ".o"
    with open(src_path, "w") as f:
        f.write(source)

    result = subprocess.run(
        [str(VASM), "-Fhunk", "-no-opt", "-quiet", "-x", cpu_flag,
         "-o", obj_path, src_path],
        capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if result.returncode != 0:
        raise AssertionError(
            f"Batch assembly failed for {cpu_flag}:\n{result.stderr}")

    hf = parse_file(obj_path)
    data = hf.hunks[0].data
    sym = {s.name: s.value for s in hf.hunks[0].symbols}

    results: list[bytes] = []
    for i in range(len(cases)):
        start = sym[f"_t{i}"]
        end = sym.get(f"_t{i+1}", sym["_end"])
        results.append(data[start:end])
    return results


# -- Roundtrip engine -----------------------------------------------------

def _run_all_roundtrips(cases: list[Case], tmpdir: str) -> list[str | None]:
    """Batch assemble -> disassemble -> batch reassemble -> compare.

    Returns list: None for pass, error string for failure.
    """
    # Group by CPU flag
    groups: dict[str, list[int]] = {}
    for i, case in enumerate(cases):
        groups.setdefault(case.cpu_flag, []).append(i)

    # Phase 1: batch assemble
    orig_bytes: list[bytes | None] = [None] * len(cases)
    for cpu_flag, idxs in groups.items():
        batch = [cases[i] for i in idxs]
        results = _batch_assemble(batch, cpu_flag, tmpdir)
        for j, idx in enumerate(idxs):
            orig_bytes[idx] = results[j]

    # Phase 2: disassemble, prepare reassembly
    disasm_info: list[DisasmInfo] = [(None, None, None)] * len(cases)
    for i, case in enumerate(cases):
        raw = orig_bytes[i]
        try:
            assert raw is not None
            instructions = disassemble(raw, max_cpu=case.max_cpu)
        except DecodeError as e:
            disasm_info[i] = (f"DISASM: {e}", None, None)
            continue
        if not instructions:
            disasm_info[i] = ("DISASM: empty", None, None)
            continue

        first = instructions[0]
        first_bytes = raw[:first.size]
        text = first.text

        is_branch = case.mnemonic in LABEL_MNEMONICS and "$" in text
        if is_branch:
            parts = text.rsplit("$", 1)
            hex_str = parts[1].split("(")[0].split()[0]
            segment_addr = int(hex_str, 16)
            nops = max(0, (segment_addr - first.size) // 2)
            reasm_source = f"{parts[0]}.t" + "\nnop" * nops + "\n.t:"
        else:
            reasm_source = text

        disasm_info[i] = (None, first_bytes, reasm_source)

    # Phase 3: batch reassemble
    reasm_groups: dict[str, list[int]] = {}
    for i, case in enumerate(cases):
        err, _, reasm_src = disasm_info[i]
        if err is not None:
            continue
        reasm_groups.setdefault(case.cpu_flag, []).append(i)

    reasm_bytes: list[bytes | None] = [None] * len(cases)
    for cpu_flag, idxs in reasm_groups.items():
        reasm_cases = [Case(cast(str, disasm_info[i][2]), "", cpu_flag, "", "")
                       for i in idxs]
        results = _batch_assemble(reasm_cases, cpu_flag, tmpdir)
        for j, idx in enumerate(idxs):
            reasm_bytes[idx] = results[j]

    # Phase 4: compare
    errors: list[str | None] = []
    for i, case in enumerate(cases):
        err, orig_first_bytes, reasm_src = disasm_info[i]
        if err is not None:
            errors.append(err)
            continue
        rb = reasm_bytes[i]
        if rb is None:
            errors.append(f"REASSEMBLE: '{reasm_src}'")
            continue
        try:
            ri = disassemble(rb, max_cpu=case.max_cpu)
        except DecodeError as e:
            errors.append(f"REDISASM: {e}")
            continue
        if not ri:
            errors.append("REDISASM: empty")
            continue
        assert orig_first_bytes is not None
        reasm_first = rb[:ri[0].size]
        if orig_first_bytes == reasm_first:
            errors.append(None)
        else:
            errors.append(
                f"MISMATCH: orig=[{orig_first_bytes.hex()}] "
                f"reasm=[{reasm_first.hex()}]")
    return errors


# -- Pytest integration ---------------------------------------------------

ALL_CASES = _generate_all_cases()
_RESULTS: list[str | None] | None = None


_fixture = cast(_FixtureDecorator, pytest.fixture(scope="session"))
_parametrize = cast(Callable[..., _Decorator], pytest.mark.parametrize)
@_fixture
def roundtrip_results(tmp_path_factory: pytest.TempPathFactory) -> list[str | None]:
    global _RESULTS
    if _RESULTS is None:
        tmpdir = str(tmp_path_factory.mktemp("roundtrip"))
        _RESULTS = _run_all_roundtrips(ALL_CASES, tmpdir)
    return _RESULTS


@_parametrize(
    "idx", range(len(ALL_CASES)),
    ids=[c.test_id for c in ALL_CASES])
def test_roundtrip(idx: int, roundtrip_results: list[str | None]) -> None:
    error = roundtrip_results[idx]
    assert error is None, f"{ALL_CASES[idx].asm}: {error}"
