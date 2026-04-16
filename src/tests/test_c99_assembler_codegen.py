from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = ROOT / "src" / "scripts" / "generate_c99_assembler_subset.py"
SRC_DIR = ROOT / "src"
KB_PATH = ROOT / "knowledge" / "m68k_instructions.json"
SUBSET_MANIFEST_PATH = ROOT / "src" / "scripts" / "m68k_assembler_subset.json"
CPU_BITS = {"68000": 0, "68010": 1, "68020": 2, "68030": 3, "68040": 4, "68060": 5}

EXPECTED_TABLE_ROWS = (
    ('"abcd", "ABCD Dy,Dx"'),
    ('"abcd", "ABCD -(Ay),-(Ax)"'),
    ('"bchg", "BCHG Dn,<ea>"'),
    ('"bchg", "BCHG # <data>,<ea>"'),
    ('"bclr", "BCLR Dn,<ea>"'),
    ('"bclr", "BCLR # <data>,<ea>"'),
    ('"bhi", "BHI <label>"'),
    ('"bset", "BSET Dn,<ea>"'),
    ('"bset", "BSET # <data>,<ea>"'),
    ('"beq", "BEQ <label>"'),
    ('"bne", "BNE <label>"'),
    ('"btst", "BTST Dn,<ea>"'),
    ('"btst", "BTST # <data>,<ea>"'),
    ('"add", "ADD <ea>,Dn"'),
    ('"add", "ADD Dn,<ea>"'),
    ('"addi", "ADDI # <data>,<ea>"'),
    ('"adda", "ADDA <ea>,An"'),
    ('"addx", "ADDX Dy,Dx"'),
    ('"addx", "ADDX -(Ay),-(Ax)"'),
    ('"addq", "ADDQ # <data>,<ea>"'),
    ('"and", "AND <ea>,Dn"'),
    ('"and", "AND Dn,<ea>"'),
    ('"andi", "ANDI # <data>,<ea>"'),
    ('"andi", "ANDI # <data>,CCR"'),
    ('"andi", "ANDI # <data>,SR"'),
    ('"asl", "ASL Dx,Dy"'),
    ('"asl", "ASL # <data>,Dy"'),
    ('"asl", "ASL <ea>"'),
    ('"asr", "ASR Dx,Dy"'),
    ('"asr", "ASR # <data>,Dy"'),
    ('"asr", "ASR <ea>"'),
    ('"bkpt", "BKPT # <data>"'),
    ('"callm", "CALLM # <data>,<ea>"'),
    ('"cas", "CAS Dc,Du,<ea>"'),
    ('"bra", "BRA <label>"'),
    ('"bsr", "BSR <label>"'),
    ('"chk", "CHK <ea>,Dn"'),
    ('"chk2", "CHK2 <ea>,Rn"'),
    ('"clr", "CLR <ea>"'),
    ('"cmp", "CMP <ea>,Dn"'),
    ('"cmp2", "CMP2 <ea>,Rn"'),
    ('"cmpa", "CMPA <ea>,An"'),
    ('"cmpi", "CMPI # <data>,<ea>"'),
    ('"cmpm", "CMPM (Ay)+,(Ax)+"'),
    ('"divs", "DIVS.W <ea>,Dn"'),
    ('"divu", "DIVU.W <ea>,Dn"'),
    ('"dbeq", "DBEQ Dn,<label>"'),
    ('"dbne", "DBNE Dn,<label>"'),
    ('"eor", "EOR Dn,<ea>"'),
    ('"eori", "EORI # <data>,<ea>"'),
    ('"eori", "EORI # <data>,CCR"'),
    ('"eori", "EORI # <data>,SR"'),
    ('"exg", "EXG Dx,Dy"'),
    ('"exg", "EXG Ax,Ay"'),
    ('"exg", "EXG Dx,Ay"'),
    ('"ext", "EXT.W Dn"'),
    ('"ext", "EXT.L Dn"'),
    ('"illegal", "ILLEGAL"'),
    ('"jmp", "JMP <ea>"'),
    ('"jsr", "JSR <ea>"'),
    ('"lea", "LEA <ea>,An"'),
    ('"link", "LINK An,# <displacement>"'),
    ('"lsl", "LSL Dx,Dy"'),
    ('"lsl", "LSL # <data>,Dy"'),
    ('"lsl", "LSL <ea>"'),
    ('"lsr", "LSR Dx,Dy"'),
    ('"lsr", "LSR # <data>,Dy"'),
    ('"lsr", "LSR <ea>"'),
    ('"move", "MOVE <ea>,<ea>"'),
    ('"movea", "MOVEA <ea>,An"'),
    ('"movem", "MOVEM <list>,<ea>"'),
    ('"movem", "MOVEM <ea>,<list>"'),
    ('"movep", "MOVEP Dx,(d16,Ay)"'),
    ('"movep", "MOVEP (d16,Ay),Dx"'),
    ('"move16", "MOVE16 (Ax)+,(Ay)+"'),
    ('"move16", "MOVE16 (xxx).L,(An)"'),
    ('"move16", "MOVE16 (xxx).L,(An)+"'),
    ('"move16", "MOVE16 (An),(xxx).L"'),
    ('"move16", "MOVE16 (An)+,(xxx).L"'),
    ('"moveq", "MOVEQ # <data>,Dn"'),
    ('"moves", "MOVES Rn,<ea>"'),
    ('"moves", "MOVES <ea>,Rn"'),
    ('"move", "MOVE CCR,<ea>"'),
    ('"move", "MOVE SR,<ea>"'),
    ('"move", "MOVE <ea>,CCR"'),
    ('"move", "MOVE <ea>,SR"'),
    ('"move", "MOVE USP,An"'),
    ('"move", "MOVE An,USP"'),
    ('"muls", "MULS.W <ea>,Dn"'),
    ('"mulu", "MULU.W <ea>,Dn"'),
    ('"nbcd", "NBCD <ea>"'),
    ('"neg", "NEG <ea>"'),
    ('"negx", "NEGX <ea>"'),
    ('"nop", "NOP"'),
    ('"not", "NOT <ea>"'),
    ('"or", "OR <ea>,Dn"'),
    ('"or", "OR Dn,<ea>"'),
    ('"ori", "ORI # <data>,<ea>"'),
    ('"ori", "ORI # <data>,CCR"'),
    ('"ori", "ORI # <data>,SR"'),
    ('"pack", "PACK -(Ax),-(Ay),# <adjustment>"'),
    ('"pack", "PACK Dx,Dy,# <adjustment>"'),
    ('"pea", "PEA <ea>"'),
    ('"reset", "RESET"'),
    ('"rol", "ROL Dx,Dy"'),
    ('"rol", "ROL # <data>,Dy"'),
    ('"rol", "ROL <ea>"'),
    ('"roxl", "ROXL Dx,Dy"'),
    ('"roxl", "ROXL # <data>,Dy"'),
    ('"roxl", "ROXL <ea>"'),
    ('"ror", "ROR Dx,Dy"'),
    ('"ror", "ROR # <data>,Dy"'),
    ('"ror", "ROR <ea>"'),
    ('"roxr", "ROXR Dx,Dy"'),
    ('"roxr", "ROXR # <data>,Dy"'),
    ('"roxr", "ROXR <ea>"'),
    ('"rtm", "RTM Rn"'),
    ('"rtd", "RTD # <displacement>"'),
    ('"rts", "RTS"'),
    ('"sbcd", "SBCD Dx,Dy"'),
    ('"sbcd", "SBCD -(Ax),-(Ay)"'),
    ('"rte", "RTE"'),
    ('"rtr", "RTR"'),
    ('"stop", "STOP # <data>"'),
    ('"trapeq", "TRAPEQ"'),
    ('"trapne", "TRAPNE.W # <data>"'),
    ('"trapt", "TRAPT.L # <data>"'),
    ('"seq", "SEQ <ea>"'),
    ('"sne", "SNE <ea>"'),
    ('"st", "ST <ea>"'),
    ('"sub", "SUB <ea>,Dn"'),
    ('"sub", "SUB Dn,<ea>"'),
    ('"suba", "SUBA <ea>,An"'),
    ('"subi", "SUBI # <data>,<ea>"'),
    ('"subq", "SUBQ # <data>,<ea>"'),
    ('"subx", "SUBX Dx,Dy"'),
    ('"subx", "SUBX -(Ax),-(Ay)"'),
    ('"swap", "SWAP Dn"'),
    ('"tas", "TAS <ea>"'),
    ('"tst", "TST <ea>"'),
    ('"trapv", "TRAPV"'),
    ('"trap", "TRAP # <vector>"'),
    ('"unpk", "UNPK -(Ax),-(Ay),# <adjustment>"'),
    ('"unpk", "UNPK Dx,Dy,# <adjustment>"'),
    ('"unlk", "UNLK An"'),
)

EXPECTED_HEADER_SNIPPETS = (
    "M68kAsmInstructionSpec",
    "uint8_t mnemonic_id;",
    "M68K_ASM_CONTROL_REGISTER_USP",
    "M68K_ASM_CONTROL_REGISTER_VBR",
    "char size_suffix;",
    "uint8_t target_cpu;",
    "M68K_ASM_CPU_ANY",
    "M68K_ASM_EA_FULL_EXTENSION_CPU_MIN",
    "uint8_t cpu_mask;",
    "M68K_ASM_EXTENSION_EA_IMMEDIATE",
    "M68K_ASM_FIELD_VALUE_UNSET = 255",
    "M68K_ASM_FULL_EXT_BD_WORD",
    "full_ext_base_suppress",
    "m68k_asm_build_patch_values",
    "m68k_asm_assemble_instruction",
    "M68kAsmEaTextFormDef",
    "m68k_asm_find_ea_text_form",
    "m68k_asm_form_supports_size_suffix",
    "m68k_asm_form_supports_cpu",
    "target_cpu",
    "m68k_asm_form_effective_size_mask",
    "m68k_asm_choose_size_suffix",
    "m68k_asm_form_index_for_id",
    "m68k_asm_form_index_for_operands_id",
    "m68k_asm_operand_extension_word_count",
    "g_m68k_asm_ea_text_forms",
    "base_token",
    "uses_base_register",
    "prefix_token",
    "suffix_token",
    "value_kind",
    "index_required",
    "m68k_asm_encode_full_ext_word",
)

EXPECTED_SPECIAL_REGISTER_FORMS = (
    ("ORI", ("imm", "ccr")),
    ("ORI", ("imm", "sr")),
    ("ANDI", ("imm", "ccr")),
    ("ANDI", ("imm", "sr")),
    ("EORI", ("imm", "ccr")),
    ("EORI", ("imm", "sr")),
    ("MOVE", ("ccr", "ea")),
    ("MOVE", ("sr", "ea")),
    ("MOVE", ("ea", "ccr")),
    ("MOVE", ("ea", "sr")),
    ("MOVE", ("usp", "an")),
    ("MOVE", ("an", "usp")),
)

FAMILY_EXPECTATIONS = {
    "alu_binary": (
        ("ABCD", "ABCD Dy,Dx", ("dn", "dn")),
        ("ABCD", "ABCD -(Ay),-(Ax)", ("ea", "ea")),
        ("SBCD", "SBCD Dx,Dy", ("dn", "dn")),
        ("SBCD", "SBCD -(Ax),-(Ay)", ("ea", "ea")),
        ("ADDX", "ADDX Dy,Dx", ("dn", "dn")),
        ("ADDX", "ADDX -(Ay),-(Ax)", ("ea", "ea")),
        ("SUBX", "SUBX Dx,Dy", ("dn", "dn")),
        ("SUBX", "SUBX -(Ax),-(Ay)", ("ea", "ea")),
        ("CMPM", "CMPM (Ay)+,(Ax)+", ("postinc", "postinc")),
    ),
    "shift_rotate": (
        ("ASL", "ASL Dx,Dy", ("dn", "dn")),
        ("ASL", "ASL # <data>,Dy", ("imm", "dn")),
        ("ASL", "ASL <ea>", ("ea",)),
        ("ASR", "ASR Dx,Dy", ("dn", "dn")),
        ("ASR", "ASR # <data>,Dy", ("imm", "dn")),
        ("ASR", "ASR <ea>", ("ea",)),
        ("LSL", "LSL Dx,Dy", ("dn", "dn")),
        ("LSL", "LSL # <data>,Dy", ("imm", "dn")),
        ("LSL", "LSL <ea>", ("ea",)),
        ("LSR", "LSR Dx,Dy", ("dn", "dn")),
        ("LSR", "LSR # <data>,Dy", ("imm", "dn")),
        ("LSR", "LSR <ea>", ("ea",)),
        ("ROL", "ROL Dx,Dy", ("dn", "dn")),
        ("ROL", "ROL # <data>,Dy", ("imm", "dn")),
        ("ROL", "ROL <ea>", ("ea",)),
        ("ROR", "ROR Dx,Dy", ("dn", "dn")),
        ("ROR", "ROR # <data>,Dy", ("imm", "dn")),
        ("ROR", "ROR <ea>", ("ea",)),
        ("ROXL", "ROXL Dx,Dy", ("dn", "dn")),
        ("ROXL", "ROXL # <data>,Dy", ("imm", "dn")),
        ("ROXL", "ROXL <ea>", ("ea",)),
        ("ROXR", "ROXR Dx,Dy", ("dn", "dn")),
        ("ROXR", "ROXR # <data>,Dy", ("imm", "dn")),
        ("ROXR", "ROXR <ea>", ("ea",)),
    ),
    "bit_ops": (
        ("BTST", "BTST Dn,<ea>", ("dn", "ea")),
        ("BTST", "BTST # <data>,<ea>", ("imm", "ea")),
        ("BCHG", "BCHG Dn,<ea>", ("dn", "ea")),
        ("BCHG", "BCHG # <data>,<ea>", ("imm", "ea")),
        ("BCLR", "BCLR Dn,<ea>", ("dn", "ea")),
        ("BCLR", "BCLR # <data>,<ea>", ("imm", "ea")),
        ("BSET", "BSET Dn,<ea>", ("dn", "ea")),
        ("BSET", "BSET # <data>,<ea>", ("imm", "ea")),
    ),
    "data_movement": (
        ("MOVEP", "MOVEP Dx,(d16,Ay)", ("dn", "ea")),
        ("MOVEP", "MOVEP (d16,Ay),Dx", ("ea", "dn")),
        ("MOVEM", "MOVEM <list>,<ea>", ("reglist", "ea")),
        ("MOVEM", "MOVEM <ea>,<list>", ("ea", "reglist")),
        ("MOVES", "MOVES Rn,<ea>", ("rn", "ea")),
        ("MOVES", "MOVES <ea>,Rn", ("ea", "rn")),
        ("MOVEC", "MOVEC Rc,Rn", ("ctrl_reg", "rn")),
        ("MOVEC", "MOVEC Rn,Rc", ("rn", "ctrl_reg")),
        ("MOVE16", "MOVE16 (Ax)+,(Ay)+", ("postinc", "postinc")),
        ("MOVE16", "MOVE16 (xxx).L,(An)", ("absl", "ind")),
        ("MOVE16", "MOVE16 (xxx).L,(An)+", ("absl", "postinc")),
        ("MOVE16", "MOVE16 (An),(xxx).L", ("ind", "absl")),
        ("MOVE16", "MOVE16 (An)+,(xxx).L", ("postinc", "absl")),
        ("PACK", "PACK -(Ax),-(Ay),# <adjustment>", ("ea", "ea", "imm")),
        ("PACK", "PACK Dx,Dy,# <adjustment>", ("dn", "dn", "imm")),
        ("UNPK", "UNPK -(Ax),-(Ay),# <adjustment>", ("ea", "ea", "imm")),
        ("UNPK", "UNPK Dx,Dy,# <adjustment>", ("dn", "dn", "imm")),
    ),
    "mul_div": (
        ("MULS", "MULS.W <ea>,Dn", ("ea", "dn")),
        ("MULU", "MULU.W <ea>,Dn", ("ea", "dn")),
        ("DIVS", "DIVS.W <ea>,Dn", ("ea", "dn")),
        ("DIVU", "DIVU.W <ea>,Dn", ("ea", "dn")),
    ),
    "system_misc": (
        ("RTM", "RTM Rn", ("rn",)),
        ("CALLM", "CALLM # <data>,<ea>", ("imm", "ea")),
        ("CAS", "CAS Dc,Du,<ea>", ("dn", "dn", "ea")),
        ("CAS2", "CAS2 Dc1:Dc2,Du1:Du2,(Rn1):(Rn2)", ("dn_pair", "dn_pair", "rn_pair")),
        ("CHK2", "CHK2 <ea>,Rn", ("ea", "rn")),
        ("CMP2", "CMP2 <ea>,Rn", ("ea", "rn")),
        ("JMP", "JMP <ea>", ("ea",)),
        ("JSR", "JSR <ea>", ("ea",)),
        ("TRAP", "TRAP # <vector>", ("imm",)),
        ("MOVEQ", "MOVEQ # <data>,Dn", ("imm", "dn")),
        ("BKPT", "BKPT # <data>", ("imm",)),
        ("RTD", "RTD # <displacement>", ("imm",)),
    ),
}


def _assert_contains_all(text: str, snippets: tuple[str, ...]) -> None:
    for snippet in snippets:
        assert snippet in text


def _load_module():
    spec = importlib.util.spec_from_file_location("src_c99_codegen", GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _generator_module():
    return _load_module()


@lru_cache(maxsize=1)
def _load_kb():
    return json.loads(KB_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_subset_manifest():
    return json.loads(SUBSET_MANIFEST_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_supported_kb_mnemonics():
    manifest = _load_subset_manifest()
    return tuple(mnemonic for group in manifest.values() for mnemonic in group)


@lru_cache(maxsize=1)
def _load_forms():
    module = _generator_module()
    return module._load_forms(module.KB_PATH)


@lru_cache(maxsize=1)
def _forms_by_key():
    return {(form.mnemonic, form.syntax, form.operand_kinds): form for form in _load_forms()}


@lru_cache(maxsize=1)
def _generate_files():
    module = _generator_module()
    return module.generate_files(SRC_DIR / "generated", module.KB_PATH)


def _form_supports_cpu(form, cpu_name: str) -> bool:
    return (int(form.cpu_mask) & (1 << CPU_BITS[cpu_name])) != 0


class C99AssemblerCodegenTests(unittest.TestCase):
    def test_generated_files_match_checked_in_src(self) -> None:
        generated = _generate_files()
        for name, expected in generated.items():
            actual = (SRC_DIR / "generated" / name).read_text(encoding="ascii")
            assert actual == expected

    def test_generated_tables_expose_generic_assembly_api(self) -> None:
        generated = _generate_files()
        metadata_header = (SRC_DIR / "m68k_asm_metadata.h").read_text(encoding="ascii")
        _assert_contains_all(generated["m68k_asm_tables.h"] + metadata_header, EXPECTED_HEADER_SNIPPETS)

    def test_subset_manifest_contract(self) -> None:
        module = _generator_module()
        manifest = _load_subset_manifest()
        assert set(manifest) == {"alu", "branches", "data_movement", "system", "unary"}
        assert "ADD" in manifest["alu"]
        assert "ABCD" in manifest["alu"]
        assert "ADDX" in manifest["alu"]
        assert "ASL, ASR" in manifest["alu"]
        assert "LSL, LSR" in manifest["alu"]
        assert "BCHG" in manifest["alu"]
        assert "BCLR" in manifest["alu"]
        assert "BSET" in manifest["alu"]
        assert "BTST" in manifest["alu"]
        assert "Bcc" in manifest["branches"]
        assert "MOVE" in manifest["data_movement"]
        assert "MOVEM" in manifest["data_movement"]
        assert "MOVES" in manifest["data_movement"]
        assert "MOVEC" in manifest["data_movement"]
        assert "MOVE16" in manifest["data_movement"]
        assert "MOVEP" in manifest["data_movement"]
        assert "MULS" in manifest["data_movement"]
        assert "MULU" in manifest["data_movement"]
        assert "PACK" in manifest["data_movement"]
        assert "UNPK" in manifest["data_movement"]
        assert "CHK2" in manifest["alu"]
        assert "CMP2" in manifest["alu"]
        assert "CMPM" in manifest["alu"]
        assert "DIVS, DIVSL" in manifest["alu"]
        assert "DIVU, DIVUL" in manifest["alu"]
        assert "ROL, ROR" in manifest["alu"]
        assert "ROXL, ROXR" in manifest["alu"]
        assert "BKPT" in manifest["system"]
        assert "CALLM" in manifest["system"]
        assert "ILLEGAL" in manifest["system"]
        assert "NOP" in manifest["system"]
        assert "RTM" in manifest["system"]
        assert "RTD" in manifest["system"]
        assert "STOP" in manifest["system"]
        assert "TAS" in manifest["unary"]
        assert _load_supported_kb_mnemonics() == tuple(module._load_supported_mnemonics(SUBSET_MANIFEST_PATH))
        assert _load_supported_kb_mnemonics() == module.SUPPORTED_MNEMONICS

    def test_manifest_enabled_kb_mnemonics_produce_generated_forms(self) -> None:
        present_kb_mnemonics = {form.kb_mnemonic for form in _load_forms()}
        for mnemonic in _load_supported_kb_mnemonics():
            assert mnemonic in present_kb_mnemonics

    def test_generated_tables_contain_expected_subset_rows(self) -> None:
        tables = _generate_files()["m68k_asm_tables.c"]
        _assert_contains_all(tables, EXPECTED_TABLE_ROWS)

    def test_grouped_family_expansions_exist(self) -> None:
        forms = _forms_by_key()
        for family in FAMILY_EXPECTATIONS.values():
            for mnemonic, syntax, operand_kinds in family:
                assert (mnemonic, syntax, operand_kinds) in forms

    def test_condition_code_families_expand_correctly(self) -> None:
        forms = _load_forms()
        b_forms = [form for form in forms if form.kb_mnemonic == "Bcc"]
        db_forms = [form for form in forms if form.kb_mnemonic == "DBcc"]
        s_forms = [form for form in forms if form.kb_mnemonic == "Scc"]
        trap_forms = [form for form in forms if form.kb_mnemonic == "TRAPcc"]
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("BHI", "BHI <label>", ("label",)) for form in b_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("BEQ", "BEQ <label>", ("label",)) for form in b_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("BNE", "BNE <label>", ("label",)) for form in b_forms)
        assert not any(form.mnemonic in {"BT", "BF"} for form in b_forms)
        assert all(form.operand_kinds == ("label",) for form in b_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("DBEQ", "DBEQ Dn,<label>", ("dn", "label")) for form in db_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("DBNE", "DBNE Dn,<label>", ("dn", "label")) for form in db_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("DBF", "DBF Dn,<label>", ("dn", "label")) for form in db_forms)
        assert all(form.operand_kinds == ("dn", "label") for form in db_forms)
        assert all(form.has_bound_word_extension for form in db_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("SEQ", "SEQ <ea>", ("ea",)) for form in s_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("SNE", "SNE <ea>", ("ea",)) for form in s_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("ST", "ST <ea>", ("ea",)) for form in s_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("TRAPEQ", "TRAPEQ", ()) for form in trap_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("TRAPNE", "TRAPNE.W # <data>", ("imm",)) for form in trap_forms)
        assert any((form.mnemonic, form.syntax, form.operand_kinds) == ("TRAPT", "TRAPT.L # <data>", ("imm",)) for form in trap_forms)
        trapt = next(form for form in trap_forms if form.mnemonic == "TRAPT" and form.syntax == "TRAPT")
        assert trapt.size_mask == 0

    def test_special_register_forms_and_cpu_contracts(self) -> None:
        forms = _load_forms()
        for mnemonic, operand_kinds in EXPECTED_SPECIAL_REGISTER_FORMS:
            assert any(form.mnemonic == mnemonic and form.operand_kinds == operand_kinds for form in forms)
        move_from_ccr = next(form for form in forms if form.kb_mnemonic == "MOVE from CCR")
        move_to_ccr = next(form for form in forms if form.kb_mnemonic == "MOVE to CCR")
        assert move_from_ccr.mnemonic == "MOVE"
        assert move_from_ccr.syntax == "MOVE CCR,<ea>"
        assert move_from_ccr.operand_kinds == ("ccr", "ea")
        assert _form_supports_cpu(move_from_ccr, "68010")
        assert not _form_supports_cpu(move_from_ccr, "68000")
        assert move_to_ccr.mnemonic == "MOVE"
        assert move_to_ccr.syntax == "MOVE <ea>,CCR"
        assert move_to_ccr.operand_kinds == ("ea", "ccr")
        assert _form_supports_cpu(move_to_ccr, "68000")

    def test_key_form_semantics_and_cpu_limits(self) -> None:
        module = _generator_module()
        forms = _forms_by_key()
        assert forms[("ASL", "ASL <ea>", ("ea",))].size_mask == module.SIZE_BIT["w"]
        assert forms[("LSL", "LSL <ea>", ("ea",))].size_mask == module.SIZE_BIT["w"]
        assert forms[("ROL", "ROL <ea>", ("ea",))].size_mask == module.SIZE_BIT["w"]
        assert forms[("ROXL", "ROXL <ea>", ("ea",))].size_mask == module.SIZE_BIT["w"]
        btst = forms[("BTST", "BTST Dn,<ea>", ("dn", "ea"))]
        assert btst.ea_dn_size_mask != 0
        assert btst.ea_memory_size_mask != 0
        chk = forms[("CHK", "CHK <ea>,Dn", ("ea", "dn"))]
        assert chk.size_mask == (module.SIZE_BIT["w"] | module.SIZE_BIT["l"])
        assert chk.size_mask_68000 == module.SIZE_BIT["w"]
        adda = forms[("ADDA", "ADDA <ea>,An", ("ea", "an"))]
        cmpa = forms[("CMPA", "CMPA <ea>,An", ("ea", "an"))]
        suba = forms[("SUBA", "SUBA <ea>,An", ("ea", "an"))]
        assert adda.opmode_values == (0xFF, 3, 7)
        assert cmpa.opmode_values == (0xFF, 3, 7)
        assert suba.opmode_values == (0xFF, 3, 7)
        addq = forms[("ADDQ", "ADDQ # <data>,<ea>", ("imm", "ea"))]
        subq = forms[("SUBQ", "SUBQ # <data>,<ea>", ("imm", "ea"))]
        assert addq.size_mask_68000 == (module.SIZE_BIT["b"] | module.SIZE_BIT["w"] | module.SIZE_BIT["l"])
        assert subq.size_mask_68000 == (module.SIZE_BIT["b"] | module.SIZE_BIT["w"] | module.SIZE_BIT["l"])
        bsr = forms[("BSR", "BSR <label>", ("label",))]
        assert bsr.branch_word_signal == 0
        assert bsr.branch_long_signal == 0xFF
        link_forms = [form for form in _load_forms() if form.mnemonic == "LINK"]
        assert len(link_forms) == 2
        assert {form.size_mask for form in link_forms} == {module.SIZE_BIT["w"], module.SIZE_BIT["l"]}
        assert {form.size_mask_68000 for form in link_forms} == {0, module.SIZE_BIT["w"]}
        ext_forms = [form for form in _load_forms() if form.mnemonic == "EXT" and form.operand_kinds == ("dn",)]
        assert {form.size_mask_68000 for form in ext_forms} == {module.SIZE_BIT["w"], module.SIZE_BIT["l"]}
        assert any(
            form.mnemonic == "EXTB" and
            form.syntax == "EXTB.L Dn" and
            _form_supports_cpu(form, "68020") and
            not _form_supports_cpu(form, "68010")
            for form in _load_forms()
        )
        rtd = forms[("RTD", "RTD # <displacement>", ("imm",))]
        assert _form_supports_cpu(rtd, "68010")
        assert not _form_supports_cpu(rtd, "68000")

    def test_supported_immediate_routing(self) -> None:
        module = _generator_module()
        routed = module._supported_immediate_routes(_load_forms(), module.KB_PATH)
        assert routed["ADD"] == "ADDI"
        assert routed["AND"] == "ANDI"
        assert routed["CMP"] == "CMPI"
        assert routed["EOR"] == "EORI"
        assert routed["OR"] == "ORI"
        assert routed["SUB"] == "SUBI"

    def test_kb_uses_templates_and_asserted_fixes(self) -> None:
        kb = _load_kb()
        field_templates = kb["_meta"].get("field_binding_templates", {})
        form_templates = kb["_meta"].get("form_templates", {})
        encoding_templates = kb["_meta"].get("encoding_templates", {})
        assert field_templates
        assert form_templates
        assert encoding_templates
        assert any("field_binding_template" in item for item in kb["instructions"])
        assert any("form_template" in item for item in kb["instructions"])
        assert any("encoding_template" in item for item in kb["instructions"])
        lea = next(item for item in kb["instructions"] if item["mnemonic"] == "LEA")
        assert lea.get("field_binding_template")
        assert lea.get("form_template")
        assert lea.get("form_syntaxes")
        assert "field_bindings" not in lea
        assert "forms" not in lea
        add = next(item for item in kb["instructions"] if item["mnemonic"] == "ADD")
        bindings = add.get("field_bindings") or field_templates[add["field_binding_template"]]
        assert any(binding["field"] == "OPMODE" and binding["value_source"] == "opmode" for binding in bindings)
        cmpi = next(item for item in kb["instructions"] if item["mnemonic"] == "CMPI")
        assert "pcdisp" not in cmpi["ea_modes"]["dst"]
        assert "pcindex" not in cmpi["ea_modes"]["dst"]
        subq = next(item for item in kb["instructions"] if item["mnemonic"] == "SUBQ")
        assert "an" in subq["ea_modes"]["dst"]
        assert "an" not in subq.get("ea_modes_020", {}).get("dst", [])

    def test_kb_exposes_ea_text_forms(self) -> None:
        ea_text_forms = _load_kb()["_meta"].get("ea_text_forms", [])
        assert ea_text_forms
        assert any(entry["syntax_family"] == "pc_disp" and entry["mode_name"] == "pcdisp" for entry in ea_text_forms)
        assert any(entry["syntax_family"] == "absolute" and entry["size_suffix"] == "w" for entry in ea_text_forms)
        assert any(entry["syntax_family"] == "an_index" and entry["base_token"] == "a" and entry["uses_base_register"] for entry in ea_text_forms)
        assert any(entry["syntax_family"] == "pc_index" and entry["base_token"] == "pc" and not entry["uses_base_register"] for entry in ea_text_forms)
        assert any(entry["syntax_family"] == "immediate" and entry["prefix_token"] == "#" for entry in ea_text_forms)
        assert any(entry["syntax_family"] == "an_postinc" and entry["suffix_token"] == ")+" for entry in ea_text_forms)
        assert any(entry["syntax_family"] == "pc_disp" and entry["value_kind"] == "numeric_or_label" for entry in ea_text_forms)
        assert any(entry["syntax_family"] == "an_index" and entry["index_required"] for entry in ea_text_forms)

    def test_kb_exposes_structured_coprocessor_forms(self) -> None:
        kb = _load_kb()
        by_mnemonic = {item["mnemonic"]: item for item in kb["instructions"]}
        field_templates = kb["_meta"]["field_binding_templates"]

        pbcc = by_mnemonic["PBcc"]
        assert pbcc["syntax"] == ["PBcc.W <label>", "PBcc.L <label>"]
        assert pbcc["uses_label"]
        assert pbcc["field_form_values"] == [{"field": "SIZE", "form_field_value": {"0": 0, "1": 1}}]
        assert "field_binding_template" not in pbcc
        assert "field_bindings" not in pbcc

        pdbcc = by_mnemonic["PDBcc"]
        assert pdbcc["form_syntaxes"] == ["PDBcc Dn,<label>"]
        assert pdbcc["uses_label"]
        assert pdbcc["field_bindings"] == [
            {"form_index": 0, "field": "COUNT REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
            {"form_index": 0, "field": "16-BIT DISPLACEMENT", "occurrence": 0, "operand_index": 1, "value_source": "value"},
        ]

        pscc = by_mnemonic["PScc"]
        assert pscc["form_syntaxes"] == ["PScc <ea>"]
        assert field_templates[pscc["field_binding_template"]] == [
            {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
            {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
        ]

        ptrapcc = by_mnemonic["PTRAPcc"]
        assert ptrapcc["form_syntaxes"] == ["PTRAPcc", "PTRAPcc.W # <data>", "PTRAPcc.L # <data>"]
        assert ptrapcc["field_form_values"] == [{"field": "OPMODE", "form_field_value": {"0": 4, "1": 2, "2": 3}}]
        assert field_templates[ptrapcc["field_binding_template"]] == [
            {"form_index": 1, "field": "DATA", "occurrence": 0, "operand_index": 0, "value_source": "value"},
            {"form_index": 2, "field": "DATA", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        ]

        pvalid = by_mnemonic["PVALID"]
        assert pvalid["syntax"] == ["PVALID VAL,<ea>", "PVALID An,<ea>"]
        assert pvalid["forms"] == [
            {
                "syntax": "PVALID VAL,<ea>",
                "encoding_group_index": 0,
                "encoding_group_span": 2,
                "control_registers": ["val"],
                "operands": [{"type": "ctrl_reg"}, {"type": "ea"}],
            },
            {"syntax": "PVALID An,<ea>", "encoding_group_index": 1, "encoding_group_span": 2, "operands": [{"type": "an"}, {"type": "ea"}]},
        ]
        assert pvalid["constraints"]["control_registers"] == [
            {"hex": "000", "name": "Valid Access Level Register", "abbrev": "val", "processor_min": "68020",
                "processor_set": ["68020", "68030", "68040", "68060"]}
        ]
        assert pvalid["field_bindings"] == [
            {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
            {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
            {"form_index": 0, "field": "REGISTER", "occurrence": 1, "operand_index": 0, "value_source": "value"},
            {"form_index": 1, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
            {"form_index": 1, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
            {"form_index": 1, "field": "REGISTER", "occurrence": 1, "operand_index": 0, "value_source": "reg"},
        ]
        pvalid_fields = pvalid["encodings"][3]["fields"]
        assert {"name": "1", "bit_hi": 10, "bit_lo": 10, "width": 1} in pvalid_fields
        assert {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3} in pvalid_fields

        cpbcc = by_mnemonic["cpBcc"]
        assert cpbcc["form_syntaxes"] == ["cpBcc <label>"]
        assert cpbcc["uses_label"]
        assert "field_binding_template" not in cpbcc
        assert cpbcc["encodings"] == [
            {
                "fields": [
                    {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
                    {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
                    {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                    {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
                    {"name": "ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
                    {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                    {"name": "1", "bit_hi": 7, "bit_lo": 7, "width": 1},
                    {"name": "SIZE", "bit_hi": 6, "bit_lo": 6, "width": 1},
                    {"name": "COPROCESSOR CONDITION", "bit_hi": 5, "bit_lo": 0, "width": 6},
                ]
            }
        ]

        cpdbcc = by_mnemonic["cpDBcc"]
        assert cpdbcc["form_syntaxes"] == ["cpDBcc Dn,<label>"]
        assert cpdbcc["uses_label"]
        assert cpdbcc["encodings"] == [
            {
                "fields": [
                    {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
                    {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
                    {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                    {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
                    {"name": "ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
                    {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                    {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                    {"name": "1", "bit_hi": 6, "bit_lo": 6, "width": 1},
                    {"name": "0", "bit_hi": 5, "bit_lo": 5, "width": 1},
                    {"name": "0", "bit_hi": 4, "bit_lo": 4, "width": 1},
                    {"name": "1", "bit_hi": 3, "bit_lo": 3, "width": 1},
                    {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3},
                ]
            },
            {
                "fields": [
                    {"name": "0", "bit_hi": 15, "bit_lo": 15, "width": 1},
                    {"name": "0", "bit_hi": 14, "bit_lo": 14, "width": 1},
                    {"name": "0", "bit_hi": 13, "bit_lo": 13, "width": 1},
                    {"name": "0", "bit_hi": 12, "bit_lo": 12, "width": 1},
                    {"name": "0", "bit_hi": 11, "bit_lo": 11, "width": 1},
                    {"name": "0", "bit_hi": 10, "bit_lo": 10, "width": 1},
                    {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                    {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                    {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                    {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
                    {"name": "COPROCESSOR CONDITION", "bit_hi": 5, "bit_lo": 0, "width": 6},
                ]
            },
            {
                "fields": [
                    {"name": "16-BIT DISPLACEMENT", "bit_hi": 15, "bit_lo": 0, "width": 16}
                ]
            },
        ]
        assert field_templates[cpdbcc["field_binding_template"]] == [
            {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
            {"form_index": 0, "field": "16-BIT DISPLACEMENT", "occurrence": 0, "operand_index": 1, "value_source": "value"},
        ]

        cpscc = by_mnemonic["cpScc"]
        assert cpscc["form_syntaxes"] == ["cpScc <ea>"]
        assert field_templates[cpscc["field_binding_template"]] == [
            {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
            {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
        ]

        cptrapcc = by_mnemonic["cpTRAPcc"]
        assert cptrapcc["form_syntaxes"] == ["cpTRAPcc", "cpTRAPcc.W # <data>", "cpTRAPcc.L # <data>"]
        assert cptrapcc["encodings"] == [
            {
                "fields": [
                    {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
                    {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
                    {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                    {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
                    {"name": "ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
                    {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                    {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                    {"name": "1", "bit_hi": 6, "bit_lo": 6, "width": 1},
                    {"name": "1", "bit_hi": 5, "bit_lo": 5, "width": 1},
                    {"name": "1", "bit_hi": 4, "bit_lo": 4, "width": 1},
                    {"name": "1", "bit_hi": 3, "bit_lo": 3, "width": 1},
                    {"name": "OPMODE", "bit_hi": 2, "bit_lo": 0, "width": 3},
                ]
            },
            {
                "fields": [
                    {"name": "0", "bit_hi": 15, "bit_lo": 15, "width": 1},
                    {"name": "0", "bit_hi": 14, "bit_lo": 14, "width": 1},
                    {"name": "0", "bit_hi": 13, "bit_lo": 13, "width": 1},
                    {"name": "0", "bit_hi": 12, "bit_lo": 12, "width": 1},
                    {"name": "0", "bit_hi": 11, "bit_lo": 11, "width": 1},
                    {"name": "0", "bit_hi": 10, "bit_lo": 10, "width": 1},
                    {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                    {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                    {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                    {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
                    {"name": "COPROCESSOR CONDITION", "bit_hi": 5, "bit_lo": 0, "width": 6},
                ]
            },
            {
                "fields": [
                    {"name": "OPTIONAL WORD", "bit_hi": 15, "bit_lo": 0, "width": 16}
                ]
            },
        ]
        assert cptrapcc["field_form_values"] == [{"field": "OPMODE", "form_field_value": {"0": 4, "1": 2, "2": 3}}]
        assert field_templates[cptrapcc["field_binding_template"]] == [
            {"form_index": 1, "field": "DATA", "occurrence": 0, "operand_index": 0, "value_source": "value"},
            {"form_index": 2, "field": "DATA", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        ]

        cprestore = by_mnemonic["cpRESTORE"]
        assert cprestore["form_syntaxes"] == ["cpRESTORE <ea>"]

        cpsave = by_mnemonic["cpSAVE"]
        assert cpsave["form_syntaxes"] == ["cpSAVE <ea>"]

        cpgen = by_mnemonic["cpGEN"]
        assert cpgen["syntax"] == ["cpGEN < parameters as defined by coprocessor >"]
        assert cpgen["forms"] == [{"syntax": "cpGEN < parameters as defined by coprocessor >", "operands": [{"type": "unknown", "raw": "< parameters as defined by coprocessor >"}]}]
        assert cpgen["encodings"] == [
            {
                "fields": [
                    {"name": "ID", "bit_hi": 15, "bit_lo": 0, "width": 16}
                ]
            },
            {
                "fields": [
                    {"name": "MODE", "bit_hi": 15, "bit_lo": 3, "width": 13},
                    {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3},
                ]
            },
        ]
        assert "field_binding_template" not in cpgen
        assert "field_bindings" not in cpgen


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_EXPLICIT_TESTS") == "1":
        return tests
    suite = unittest.TestSuite()

    def append_filtered(test):
        if isinstance(test, unittest.TestSuite):
          for item in test:
            append_filtered(item)
          return
        if getattr(test, "_testMethodName", "") == "test_generated_files_match_checked_in_src":
          return
        suite.addTest(test)

    append_filtered(tests)
    return suite
