from __future__ import annotations

from collections import defaultdict
from itertools import product

import pytest

from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble
from m68k_kb import runtime_m68k_asm

pytestmark = pytest.mark.runtime_coverage

type CanonicalForm = tuple[str, tuple[str, ...]]

_UNSUPPORTED_FORM_REASONS: dict[CanonicalForm, str] = {
    ("BFCHG", ("bf_ea",)): "bitfield syntax is not assembled yet",
    ("BFCLR", ("bf_ea",)): "bitfield syntax is not assembled yet",
    ("BFEXTS", ("bf_ea", "dn")): "bitfield syntax is not assembled yet",
    ("BFEXTU", ("bf_ea", "dn")): "bitfield syntax is not assembled yet",
    ("BFFFO", ("bf_ea", "dn")): "bitfield syntax is not assembled yet",
    ("BFINS", ("dn", "bf_ea")): "bitfield syntax is not assembled yet",
    ("BFSET", ("bf_ea",)): "bitfield syntax is not assembled yet",
    ("BFTST", ("bf_ea",)): "bitfield syntax is not assembled yet",
    ("CAS CAS2", ("dn", "dn", "ea")): "CAS/CAS2 special operand forms are not assembled yet",
    ("CAS CAS2", ("dn_pair", "dn_pair", "unknown")): "CAS/CAS2 special operand forms are not assembled yet",
    ("CHK2", ("ea", "rn")): "CHK2/CMP2 special forms are not assembled yet",
    ("CMP2", ("ea", "rn")): "CHK2/CMP2 special forms are not assembled yet",
    ("FRESTORE", ("ea",)): "FPU save/restore forms are not assembled yet",
    ("FSAVE", ("ea",)): "FPU save/restore forms are not assembled yet",
    ("MOVE16", ("postinc", "postinc")): "MOVE16 forms are not assembled yet",
    ("MOVE16", ("unknown", "unknown")): "MOVE16 forms are not assembled yet",
    ("MOVEC", ("ctrl_reg", "rn")): "MOVEC control-register syntax is not assembled yet",
    ("MOVEC", ("rn", "ctrl_reg")): "MOVEC control-register syntax is not assembled yet",
    ("MOVES", ("rn", "ea")): "MOVES forms are not assembled yet",
    ("MOVES", ("ea", "rn")): "MOVES forms are not assembled yet",
    ("MULS", ("ea", "dn_pair")): "long multiply register-pair syntax is not assembled yet",
    ("MULU", ("ea", "dn_pair")): "long multiply register-pair syntax is not assembled yet",
    ("PFLUSH", ("unknown", "unknown")): "PMMU special operand forms are not assembled yet",
    ("PFLUSH", ("unknown", "unknown", "ea")): "PMMU special operand forms are not assembled yet",
    ("PFLUSH PFLUSHA", ()): "PMMU special operand forms are not assembled yet",
    ("PFLUSH PFLUSHA", ("unknown", "unknown")): "PMMU special operand forms are not assembled yet",
    ("PFLUSH PFLUSHA", ("unknown", "unknown", "ea")): "PMMU special operand forms are not assembled yet",
    ("PFLUSHR", ("ea",)): "PMMU special operand forms are not assembled yet",
    ("PMOVE", ("unknown", "ea")): "PMMU special operand forms are not assembled yet",
    ("PMOVE", ("ea", "unknown")): "PMMU special operand forms are not assembled yet",
    ("PRESTORE", ("ea",)): "PMMU special operand forms are not assembled yet",
    ("PSAVE", ("ea",)): "PMMU special operand forms are not assembled yet",
    ("PScc", ("ea",)): "PMMU special operand forms are not assembled yet",
    ("PTRAPcc", ()): "PMMU special operand forms are not assembled yet",
    ("PTRAPcc", ("imm",)): "PMMU special operand forms are not assembled yet",
    ("PVALID", ("unknown", "ea")): "PMMU special operand forms are not assembled yet",
    ("PVALID", ("an", "ea")): "PMMU special operand forms are not assembled yet",
    ("RTD", ("imm",)): "RTD immediate extension encoding is not assembled yet",
    ("STOP", ("imm",)): "STOP immediate extension encoding is not assembled yet",
    ("TRAPcc", ()): "TRAPcc condition-code forms are not assembled yet",
    ("TRAPcc", ("imm",)): "TRAPcc condition-code forms are not assembled yet",
    ("PBcc", ("label",)): "PMMU branch family is not assembled yet",
    ("PDBcc", ("dn", "label")): "PMMU branch family is not assembled yet",
    ("cpBcc", ("label",)): "coprocessor branch family is not assembled yet",
    ("cpDBcc", ("dn", "label")): "coprocessor branch family is not assembled yet",
    ("cpGEN", ("unknown",)): "generic coprocessor forms are not assembled yet",
    ("cpRESTORE", ("ea",)): "coprocessor save/restore forms are not assembled yet",
    ("cpSAVE", ("ea",)): "coprocessor save/restore forms are not assembled yet",
    ("cpScc", ("ea",)): "coprocessor condition-code forms are not assembled yet",
    ("cpTRAPcc", ()): "coprocessor TRAPcc forms are not assembled yet",
    ("cpTRAPcc", ("imm",)): "coprocessor TRAPcc forms are not assembled yet",
    ("DIVS, DIVSL", ("ea", "dn_pair")): "long divide register-pair syntax is not assembled yet",
    ("DIVU, DIVUL", ("ea", "dn_pair")): "long divide register-pair syntax is not assembled yet",
}

_SYNTAX_OVERRIDES: dict[CanonicalForm, tuple[str, ...]] = {
    ("ASL, ASR", ("dn", "dn")): ("asl",),
    ("ASL, ASR", ("imm", "dn")): ("asl",),
    ("ASL, ASR", ("ea",)): ("asl",),
    ("LSL, LSR", ("dn", "dn")): ("lsl",),
    ("LSL, LSR", ("imm", "dn")): ("lsl",),
    ("LSL, LSR", ("ea",)): ("lsl",),
    ("ROL, ROR", ("dn", "dn")): ("rol",),
    ("ROL, ROR", ("imm", "dn")): ("rol",),
    ("ROL, ROR", ("ea",)): ("rol",),
    ("ROXL, ROXR", ("dn", "dn")): ("roxl",),
    ("ROXL, ROXR", ("imm", "dn")): ("roxl",),
    ("ROXL, ROXR", ("ea",)): ("roxl",),
}

_MODE_SAMPLE_TEXT: dict[str, tuple[str, ...]] = {
    "dn": ("d0",),
    "an": ("a0",),
    "ind": ("(a0)",),
    "postinc": ("(a0)+",),
    "predec": ("-(a0)",),
    "disp": ("4(a0)",),
    "index": ("4(a0,d0.w)",),
    "absw": ("$1234.w",),
    "absl": ("$12345678.l",),
    "pcdisp": ("4(pc)",),
    "pcindex": ("4(pc,d0.w)",),
    "imm": ("#1",),
}

_MODE_PREFERENCE: tuple[str, ...] = (
    "ind",
    "disp",
    "dn",
    "postinc",
    "predec",
    "index",
    "absw",
    "absl",
    "pcdisp",
    "pcindex",
    "imm",
)


def _canonical_forms() -> tuple[CanonicalForm, ...]:
    forms: set[CanonicalForm] = set()
    for kb_mnemonic, form_types in runtime_m68k_asm.FORM_OPERAND_TYPES.items():
        for form in form_types:
            forms.add((kb_mnemonic, form))
    return tuple(sorted(forms))


def _syntax_by_canonical_form() -> dict[CanonicalForm, tuple[str, ...]]:
    by_form: dict[CanonicalForm, set[str]] = defaultdict(set)
    for (syntax_mnemonic, syntax_types), (kb_mnemonic, canonical_types) in runtime_m68k_asm.ASM_SYNTAX_INDEX.items():
        if syntax_types == canonical_types:
            by_form[(kb_mnemonic, canonical_types)].add(syntax_mnemonic)
    return {
        form: tuple(sorted(mnemonics))
        for form, mnemonics in sorted(by_form.items())
    }


_SYNTAX_BY_FORM = _syntax_by_canonical_form()


def _ea_candidates(kb_mnemonic: str, form_types: tuple[str, ...], operand_index: int) -> tuple[str, ...]:
    source_modes, dest_modes, ea_modes = runtime_m68k_asm.EA_MODE_TABLES[kb_mnemonic]
    if len(form_types) == 1:
        allowed_modes = source_modes or dest_modes or ea_modes
    elif operand_index == 0 and form_types[operand_index] == "ea":
        allowed_modes = source_modes or ea_modes
    elif operand_index > 0 and form_types[operand_index] == "ea":
        allowed_modes = dest_modes or ea_modes
    else:
        allowed_modes = ea_modes or source_modes or dest_modes

    candidates: list[str] = []
    for mode_name in _MODE_PREFERENCE:
        if mode_name in allowed_modes:
            candidates.extend(_MODE_SAMPLE_TEXT[mode_name])
    return tuple(candidates or ("(a0)",))


def _operand_candidates(kb_mnemonic: str, form_types: tuple[str, ...], operand_index: int) -> tuple[str, ...]:
    operand_type = form_types[operand_index]
    if operand_type == "ea":
        return _ea_candidates(kb_mnemonic, form_types, operand_index)
    if operand_type == "dn":
        return ("d0",)
    if operand_type == "an":
        return ("a0",)
    if operand_type == "imm":
        if kb_mnemonic == "LINK":
            return ("#-4",)
        return ("#1",)
    if operand_type == "label":
        return ("$0004",)
    if operand_type == "disp":
        return ("4(a0)",)
    if operand_type == "postinc":
        return ("(a0)+",)
    if operand_type == "predec":
        return ("-(a0)",)
    if operand_type == "reglist":
        return ("d0-d1",)
    if operand_type == "rn":
        return ("d0", "a0")
    if operand_type == "sr":
        return ("sr",)
    if operand_type == "ccr":
        return ("ccr",)
    if operand_type == "usp":
        return ("usp",)
    if operand_type == "ctrl_reg":
        return ("sfc",)
    if operand_type == "dn_pair":
        return ("d0:d1",)
    if operand_type == "bf_ea":
        return ("d0{0:8}", "(a0){0:8}")
    if operand_type == "unknown":
        return ("unknown",)
    raise AssertionError(f"Unhandled operand type {operand_type!r}")


def _form_sample(form: CanonicalForm) -> str | None:
    kb_mnemonic, form_types = form
    syntax_mnemonics = _SYNTAX_OVERRIDES.get(form, _SYNTAX_BY_FORM.get(form, ()))
    if not syntax_mnemonics:
        return None

    operand_candidates = [
        _operand_candidates(kb_mnemonic, form_types, index)
        for index in range(len(form_types))
    ]
    for syntax_mnemonic in syntax_mnemonics:
        for operands in product(*operand_candidates):
            text = syntax_mnemonic if not operands else f"{syntax_mnemonic} {','.join(operands)}"
            try:
                raw = assemble_instruction(text)
                inst = disassemble(raw, max_cpu="68020")[0]
            except Exception:
                continue
            if inst.kb_mnemonic == kb_mnemonic:
                return text
    return None


@pytest.mark.parametrize("form", _canonical_forms())
def test_runtime_forms_are_classified_for_coverage(form: CanonicalForm) -> None:
    sample = _form_sample(form)
    if sample is not None:
        return
    assert form in _UNSUPPORTED_FORM_REASONS, form


@pytest.mark.parametrize(
    "form",
    [form for form in _canonical_forms() if form not in _UNSUPPORTED_FORM_REASONS],
)
def test_supported_runtime_forms_have_roundtrip_samples(form: CanonicalForm) -> None:
    sample = _form_sample(form)
    assert sample is not None, form


def test_unsupported_form_reasons_are_current() -> None:
    forms = set(_canonical_forms())
    assert set(_UNSUPPORTED_FORM_REASONS).issubset(forms)


def test_asm_runtime_exports_operand_mode_tables() -> None:
    assert hasattr(runtime_m68k_asm, "OPERAND_MODE_TABLES")
    assert runtime_m68k_asm.OPERAND_MODE_TABLES["ABCD"][0] == "R/M"
