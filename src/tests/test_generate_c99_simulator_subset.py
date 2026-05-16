from __future__ import annotations

import importlib.util
import json
import os
from types import SimpleNamespace
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src" / "scripts" / "generate_c99_simulator_subset.py"
STYLE_CHECKER = ROOT / "src" / "scripts" / "check_c_style.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateC99SimulatorSubsetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls._outdir = Path(cls._tmp.name)
        cls._generator = _load_module(SCRIPT, "src_test_generate_c99_simulator_subset")
        cls._tables = cls._generator._emit_tables_include(
            cls._generator._load_forms(),
            cls._generator._load_kb(),
        )
        (cls._outdir / "m68k_simulator_tables.h").write_text(cls._tables, encoding="ascii")
        cls._checker = _load_module(STYLE_CHECKER, "src_test_generate_c99_simulator_style_checker")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_generates_form_metadata(self) -> None:
        self.assertIn("static const M68kSimFormLookup g_m68k_sim_form_lookup[", self._tables)
        self.assertIn(
            "static const uint16_t g_m68k_sim_lookup_index_by_canonical_id[M68K_CANONICAL_FORM_COUNT + 1u] = {",
            self._tables,
        )
        self.assertIn(
            "static const uint8_t g_m68k_sim_semantic_status_by_canonical_id[M68K_CANONICAL_FORM_COUNT + 1u] = {",
            self._tables,
        )
        self.assertIn("static const uint16_t g_m68k_sim_condition_masks[16] = {", self._tables)
        self.assertIn("M68K_SIM_FLOW_JUMP", self._tables)
        self.assertIn("M68K_SIM_FLOW_CALL", self._tables)
        self.assertIn("M68K_SIM_SEMANTICS_AVAILABLE", self._tables)
        self.assertIn("M68K_SIM_OP_COMPARE", self._tables)
        self.assertIn("M68K_SIM_OP_TEST", self._tables)
        self.assertIn("M68K_SIM_FLOW_BRANCH", self._tables)
        self.assertIn("0xF0F0u", self._tables)

    def test_generates_sp_effect_rows(self) -> None:
        self.assertIn("static const M68kSimSpEffectDef g_m68k_sim_sp_effects[] = {", self._tables)
        self.assertIn("M68K_SIM_SP_DECREMENT", self._tables)

    def test_first_slice_execution_metadata_exists_in_kb(self) -> None:
        kb = json.loads((ROOT / "knowledge" / "m68k_instructions.json").read_text(encoding="utf-8"))
        instructions = {entry["mnemonic"]: entry for entry in kb["instructions"]}
        for mnemonic in ("LEA", "MOVE", "MOVEA", "MOVEQ", "ADDQ", "SUBQ", "JMP", "JSR", "CLR", "EXG", "BRA", "BSR", "RTS", "Bcc", "DBcc", "Scc", "TRAPcc", "CMP", "CMPI", "CMPA", "TST", "PEA", "LINK", "UNLK", "TAS", "BTST", "BSET", "BCLR", "BCHG", "MOVEC", "MOVEP", "MOVES", "MOVE from CCR", "MOVE to CCR", "MOVE from SR", "MOVE to SR", "MOVE USP", "AND", "ANDI", "EOR", "EORI", "OR", "ORI", "NEG", "NOT", "SWAP", "EXT, EXTB", "ANDI to CCR", "ANDI to SR", "EORI to CCR", "EORI to SR", "ORI to CCR", "ORI to SR", "NOP", "RESET", "RTM", "ILLEGAL", "BKPT", "STOP", "TRAPV", "ASL, ASR", "LSL, LSR", "ROL, ROR", "ROXL, ROXR", "ABCD", "SBCD", "ADDX", "SUBX", "NEGX", "NBCD", "CHK", "CHK2", "CMP2", "MULS", "MULU", "DIVS, DIVSL", "DIVU, DIVUL", "CAS CAS2", "CALLM", "BFCHG", "BFCLR", "BFEXTS", "BFEXTU", "BFFFO", "BFINS", "BFSET", "BFTST", "CINV", "CPUSH", "PFLUSH", "PFLUSH PFLUSHA", "PFLUSHR", "PLOAD", "FSAVE", "FRESTORE", "PSAVE", "PRESTORE", "PMOVE", "PTEST", "TRAP"):
            self.assertIn("execution", instructions[mnemonic])
        self.assertEqual(instructions["LEA"]["execution"]["semantic_op"], "compute_ea")
        self.assertEqual(instructions["MOVEM"]["execution"]["form_overrides"]["1"]["multi_transfer"]["address_update"], "postincrement_if_postinc")
        self.assertNotIn("ea_address_shape", instructions["MOVEP"]["execution"]["operands"][1])
        self.assertEqual(instructions["MOVEP"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_address_shape"], "displacement")
        self.assertEqual(instructions["MOVEP"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_base_kind"], "an")
        self.assertTrue(instructions["MOVEP"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_uses_displacement"])
        self.assertEqual(instructions["LEA"]["execution"]["operands"][0]["ea_pc_base_bias_bytes"], 0)
        self.assertEqual(instructions["MOVE16"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_address_literal_width_bytes"], 4)
        self.assertEqual(instructions["MOVE16"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_address_formula"], "absolute_literal")
        self.assertEqual(instructions["MOVE16"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_index_extension_format"], "none")
        self.assertEqual(instructions["MOVE16"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_index_register_class"], "none")
        self.assertEqual(instructions["MOVE16"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_index_value_width_source"], "none")
        self.assertEqual(instructions["MOVE16"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_index_scale_source"], "none")
        self.assertEqual(instructions["MOVE16"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_index_sign_source"], "none")
        self.assertEqual(instructions["MOVE16"]["execution"]["form_overrides"]["1"]["operands"][0]["ea_displacement_source"], "none")
        self.assertEqual(instructions["CMPM"]["execution"]["operands"][0]["ea_register_update"], "postincrement")
        self.assertEqual(instructions["PACK"]["execution"]["operands"][0]["ea_register_update"], "predecrement")
        self.assertEqual(instructions["JMP"]["execution"]["flow"]["target_kind"], "ea_address")
        self.assertEqual(instructions["BRA"]["execution"]["flow"]["target_kind"], "branch_disp")
        self.assertEqual(instructions["CLR"]["execution"]["semantic_op"], "write_constant")
        self.assertEqual(instructions["Bcc"]["execution"]["flow"]["target_kind"], "branch_disp")
        self.assertEqual(instructions["DBcc"]["execution"]["semantic_op"], "dbcc")
        self.assertEqual(instructions["Scc"]["execution"]["semantic_op"], "set_condition")
        self.assertEqual(instructions["Scc"]["execution"]["operands"][0]["access"]["kind"], "memory_write")
        self.assertTrue(instructions["TRAPcc"]["execution"]["flow"]["conditional"])
        self.assertEqual(instructions["TRAPcc"]["execution"]["flow"]["kind"], "trap")
        self.assertEqual(instructions["TRAPcc"]["execution"]["form_overrides"]["1"]["operands"][0]["access"]["width"], 2)
        self.assertEqual(instructions["TRAPcc"]["execution"]["form_overrides"]["2"]["operands"][0]["access"]["width"], 4)
        self.assertEqual(instructions["CMP"]["execution"]["semantic_op"], "compare")
        self.assertEqual(instructions["CMPI"]["execution"]["operands"][1]["usage"], "value")
        self.assertEqual(instructions["CMPA"]["execution"]["result"]["formula"], "sub")
        self.assertEqual(instructions["TST"]["execution"]["semantic_op"], "test")
        self.assertEqual(instructions["PEA"]["execution"]["semantic_op"], "push_ea")
        self.assertEqual(instructions["PEA"]["execution"]["operands"][0]["usage"], "address")
        self.assertEqual(instructions["PEA"]["execution"]["operands"][0]["ea_address_formula"], "decoded_ea")
        self.assertEqual(instructions["LINK"]["execution"]["semantic_op"], "link")
        self.assertEqual(instructions["UNLK"]["execution"]["semantic_op"], "unlk")
        self.assertEqual(instructions["MOVEM"]["execution"]["semantic_op"], "move_multiple")
        self.assertEqual(instructions["MOVEM"]["execution"]["operands"][0]["access"]["kind"], "register_list_read")
        self.assertEqual(instructions["MOVEM"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["MOVEM"]["execution"]["form_overrides"]["1"]["operands"][1]["access"]["kind"], "register_list_write")
        self.assertEqual(instructions["MOVEM"]["execution"]["form_overrides"]["1"]["operands"][1]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["MOVEM"]["execution"]["multi_transfer"]["direction"], "register_to_memory")
        self.assertEqual(instructions["MOVEM"]["execution"]["form_overrides"]["1"]["multi_transfer"]["direction"], "memory_to_register")
        self.assertEqual(instructions["MOVEM"]["execution"]["multi_transfer"]["address_update"], "predecrement_if_predec")
        self.assertEqual(instructions["MOVEM"]["execution"]["form_overrides"]["1"]["multi_transfer"]["address_update"], "postincrement_if_postinc")
        self.assertEqual(instructions["MOVEM"]["execution"]["multi_transfer"]["reg_iteration"], "ascending_mask_bits")
        self.assertEqual(instructions["MOVEM"]["execution"]["multi_transfer"]["source_snapshot"], "before_write")
        self.assertEqual(instructions["MOVEM"]["execution"]["form_overrides"]["1"]["multi_transfer"]["source_snapshot"], "none")
        self.assertEqual(instructions["MOVEP"]["execution"]["semantic_op"], "move_peripheral")
        self.assertEqual(instructions["MOVEP"]["execution"]["striped_transfer"]["direction"], "register_to_memory")
        self.assertEqual(instructions["MOVEP"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["MOVEP"]["execution"]["form_overrides"]["1"]["striped_transfer"]["direction"], "memory_to_register")
        self.assertEqual(instructions["MOVEP"]["execution"]["striped_transfer"]["stride"], 2)
        self.assertEqual(instructions["MOVEC"]["execution"]["semantic_op"], "move_value")
        self.assertFalse(instructions["MOVEC"]["execution"]["ccr"]["writes"])
        self.assertEqual(instructions["MOVEC"]["execution"]["operands"][0]["access"]["kind"], "register_read")
        self.assertEqual(instructions["MOVEC"]["execution"]["form_overrides"]["1"]["operands"][1]["access"]["kind"], "register_write")
        self.assertEqual(instructions["MOVES"]["execution"]["semantic_op"], "move_value")
        self.assertFalse(instructions["MOVES"]["execution"]["ccr"]["writes"])
        self.assertEqual(instructions["MOVES"]["execution"]["operands"][0]["access"]["kind"], "register_read")
        self.assertEqual(instructions["MOVES"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["MOVES"]["execution"]["form_overrides"]["1"]["operands"][1]["access"]["kind"], "register_write")
        self.assertEqual(instructions["MOVE from CCR"]["execution"]["operands"][0]["access"]["kind"], "register_read")
        self.assertEqual(instructions["MOVE to CCR"]["execution"]["operands"][1]["access"]["kind"], "register_write")
        self.assertEqual(instructions["MOVE to CCR"]["execution"]["ccr"]["formula"], "write_ccr")
        self.assertEqual(instructions["MOVE from SR"]["execution"]["operands"][0]["access"]["kind"], "register_read")
        self.assertEqual(instructions["MOVE to SR"]["execution"]["operands"][1]["access"]["kind"], "register_write")
        self.assertEqual(instructions["MOVE to SR"]["execution"]["ccr"]["formula"], "write_sr")
        self.assertEqual(instructions["MOVE USP"]["execution"]["semantic_op"], "move_value")
        self.assertEqual(instructions["MOVE USP"]["execution"]["operands"][0]["access"]["kind"], "register_read")
        self.assertEqual(instructions["AND"]["execution"]["semantic_op"], "logic_and")
        self.assertEqual(instructions["MOVE"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["MOVE"]["execution"]["operands"][1]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["ADD"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["SUB"]["execution"]["operands"][1]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["CMP"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["TST"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["ANDI"]["execution"]["result"]["formula"], "bitwise_and")
        self.assertEqual(instructions["AND"]["execution"]["operands"][1]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["EOR"]["execution"]["semantic_op"], "logic_xor")
        self.assertEqual(instructions["ORI"]["execution"]["semantic_op"], "logic_or")
        self.assertEqual(instructions["CLR"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["NEG"]["execution"]["semantic_op"], "negate")
        self.assertEqual(instructions["NEG"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["NOT"]["execution"]["semantic_op"], "bitwise_not")
        self.assertEqual(instructions["NOT"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["SWAP"]["execution"]["semantic_op"], "swap_words")
        self.assertEqual(instructions["SWAP"]["execution"]["operands"][0]["access"]["width_source"], "full_register")
        self.assertEqual(instructions["EXT, EXTB"]["execution"]["semantic_op"], "sign_extend")
        self.assertEqual(instructions["EXT, EXTB"]["execution"]["operands"][0]["access"]["width"], 2)
        self.assertEqual(instructions["EXT, EXTB"]["execution"]["form_overrides"]["0"]["operands"][0]["access"]["width"], 2)
        self.assertEqual(instructions["EXT, EXTB"]["execution"]["form_overrides"]["1"]["operands"][0]["access"]["width"], 4)
        self.assertEqual(instructions["EXT, EXTB"]["execution"]["form_overrides"]["2"]["operands"][0]["access"]["width"], 4)
        self.assertEqual(instructions["ANDI to CCR"]["execution"]["semantic_op"], "logic_and")
        self.assertEqual(instructions["ANDI to CCR"]["execution"]["operands"][1]["access"]["kind"], "register_write")
        self.assertEqual(instructions["EORI to SR"]["execution"]["semantic_op"], "logic_xor")
        self.assertEqual(instructions["ORI to SR"]["execution"]["semantic_op"], "logic_or")
        self.assertEqual(instructions["TAS"]["execution"]["semantic_op"], "test_and_set")
        self.assertEqual(instructions["TAS"]["execution"]["operands"][0]["usage"], "read_modify_write")
        self.assertEqual(instructions["BTST"]["execution"]["semantic_op"], "bit_test")
        self.assertEqual(instructions["BTST"]["execution"]["operands"][1]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["BSET"]["execution"]["semantic_op"], "bit_set")
        self.assertEqual(instructions["BSET"]["execution"]["operands"][1]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["BCLR"]["execution"]["semantic_op"], "bit_clear")
        self.assertEqual(instructions["BCLR"]["execution"]["operands"][1]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["BCHG"]["execution"]["semantic_op"], "bit_change")
        self.assertEqual(instructions["BCHG"]["execution"]["operands"][1]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["NOP"]["execution"]["semantic_op"], "nop")
        self.assertEqual(instructions["RESET"]["execution"]["semantic_op"], "reset")
        self.assertEqual(instructions["RTM"]["execution"]["semantic_op"], "rtm")
        self.assertEqual(instructions["ILLEGAL"]["execution"]["semantic_op"], "illegal")
        self.assertEqual(instructions["BKPT"]["execution"]["semantic_op"], "bkpt")
        self.assertEqual(instructions["STOP"]["execution"]["semantic_op"], "stop")
        self.assertEqual(instructions["STOP"]["execution"]["operands"][0]["access"]["width"], 2)
        self.assertEqual(instructions["TRAPV"]["execution"]["semantic_op"], "trapv")
        self.assertEqual(instructions["TRAP"]["execution"]["exception"]["vector_source"], "trap_immediate")
        self.assertEqual(instructions["TRAP"]["execution"]["exception"]["pc_source"], "next")
        self.assertEqual(instructions["ILLEGAL"]["execution"]["exception"]["vector"], 4)
        self.assertEqual(instructions["BKPT"]["execution"]["exception"]["vector"], 4)
        self.assertEqual(instructions["TRAPV"]["execution"]["exception"]["trigger"], "if_overflow")
        self.assertEqual(instructions["STOP"]["execution"]["exception"]["trigger"], "if_user_mode")
        self.assertEqual(instructions["RTE"]["execution"]["return"]["restore"], "exception_frame")
        self.assertEqual(instructions["RTE"]["execution"]["exception"]["trigger"], "if_user_mode")
        self.assertEqual(instructions["RTR"]["execution"]["return"]["restore"], "ccr_then_pc")
        self.assertEqual(instructions["RTD"]["execution"]["return"]["stack_adjust_operand_index"], 0)
        self.assertEqual(instructions["CHK"]["execution"]["exception"]["vector"], 6)
        self.assertEqual(instructions["CHK2"]["execution"]["exception"]["address_source"], "current_pc")
        self.assertEqual(instructions["ASL, ASR"]["execution"]["semantic_op"], "shift")
        self.assertEqual(instructions["ABCD"]["execution"]["semantic_op"], "add_decimal")
        self.assertEqual(instructions["ABCD"]["execution"]["form_overrides"]["1"]["operands"][0]["expected_kind"], "predec")
        self.assertEqual(instructions["ADDX"]["execution"]["semantic_op"], "addx")
        self.assertEqual(instructions["SUBX"]["execution"]["semantic_op"], "subx")
        self.assertEqual(instructions["NEGX"]["execution"]["semantic_op"], "negx")
        self.assertEqual(instructions["NBCD"]["execution"]["semantic_op"], "negx")
        self.assertEqual(instructions["CHK"]["execution"]["semantic_op"], "bounds_check")
        self.assertEqual(instructions["CHK2"]["execution"]["operands"][1]["expected_kind"], "rn")
        self.assertEqual(instructions["CMP2"]["execution"]["result"]["kind"], "none")
        self.assertEqual(instructions["MULS"]["execution"]["semantic_op"], "multiply")
        self.assertEqual(instructions["MULU"]["execution"]["operands"][1]["expected_kind"], "dn")
        self.assertEqual(instructions["DIVS, DIVSL"]["execution"]["semantic_op"], "divide")
        self.assertEqual(instructions["DIVU, DIVUL"]["execution"]["operands"][0]["expected_kind"], "ea")
        self.assertEqual(instructions["CAS CAS2"]["execution"]["semantic_op"], "compare_swap")
        self.assertEqual(instructions["CAS CAS2"]["execution"]["operands"][2]["usage"], "read_modify_write")
        self.assertEqual(instructions["CAS CAS2"]["execution"]["form_overrides"]["1"]["operands"][2]["expected_kind"], "rn")
        self.assertEqual(instructions["CALLM"]["execution"]["semantic_op"], "call_module")
        self.assertEqual(instructions["CALLM"]["execution"]["flow"]["kind"], "call")
        self.assertEqual(instructions["CALLM"]["execution"]["operands"][0]["access"]["width"], 1)
        self.assertEqual(instructions["BFCHG"]["execution"]["semantic_op"], "bitfield_change")
        self.assertEqual(instructions["BFCLR"]["execution"]["semantic_op"], "bitfield_clear")
        self.assertEqual(instructions["BFEXTS"]["execution"]["semantic_op"], "bitfield_extract_signed")
        self.assertEqual(instructions["BFEXTS"]["execution"]["operands"][1]["usage"], "write")
        self.assertEqual(instructions["BFEXTU"]["execution"]["semantic_op"], "bitfield_extract_unsigned")
        self.assertEqual(instructions["BFFFO"]["execution"]["semantic_op"], "bitfield_find_first_one")
        self.assertEqual(instructions["BFINS"]["execution"]["semantic_op"], "bitfield_insert")
        self.assertEqual(instructions["BFINS"]["execution"]["operands"][1]["usage"], "read_modify_write")
        self.assertEqual(instructions["BFSET"]["execution"]["semantic_op"], "bitfield_set")
        self.assertEqual(instructions["BFTST"]["execution"]["semantic_op"], "bitfield_test")
        self.assertEqual(instructions["CINV"]["execution"]["semantic_op"], "cache_invalidate")
        self.assertEqual(instructions["CINV"]["execution"]["form_overrides"]["2"]["operands"][0]["expected_kind"], "ctrl_reg")
        self.assertEqual(instructions["CPUSH"]["execution"]["semantic_op"], "cache_push")
        self.assertEqual(instructions["PFLUSH"]["execution"]["semantic_op"], "pflush")
        pflush_address_operands = [
            operand
            for form in instructions["PFLUSH"]["execution"]["form_overrides"].values()
            for operand in form["operands"]
            if operand["index"] == 2
        ]
        self.assertTrue(any(operand["usage"] == "address" for operand in pflush_address_operands))
        self.assertEqual(instructions["PFLUSH PFLUSHA"]["execution"]["semantic_op"], "pflush")
        self.assertEqual(instructions["PFLUSHR"]["execution"]["semantic_op"], "pflushr")
        self.assertEqual(instructions["PFLUSHR"]["execution"]["operands"][0]["access"]["kind"], "compute_address")
        self.assertEqual(instructions["PLOAD"]["execution"]["semantic_op"], "pload")
        self.assertEqual(instructions["PLOAD"]["execution"]["operands"][1]["usage"], "address")
        self.assertEqual(instructions["FSAVE"]["execution"]["semantic_op"], "fsave")
        self.assertEqual(instructions["FSAVE"]["execution"]["operands"][0]["access"]["kind"], "memory_write")
        self.assertEqual(instructions["FRESTORE"]["execution"]["semantic_op"], "frestore")
        self.assertEqual(instructions["FRESTORE"]["execution"]["operands"][0]["access"]["kind"], "memory_read")
        self.assertEqual(instructions["PSAVE"]["execution"]["semantic_op"], "psave")
        self.assertEqual(instructions["PRESTORE"]["execution"]["semantic_op"], "prestore")
        self.assertEqual(instructions["cpSAVE"]["execution"]["semantic_op"], "cpsave")
        self.assertEqual(instructions["cpSAVE"]["execution"]["operands"][0]["access"]["kind"], "memory_write")
        self.assertEqual(instructions["cpRESTORE"]["execution"]["semantic_op"], "cprestore")
        self.assertEqual(instructions["cpRESTORE"]["execution"]["operands"][0]["access"]["kind"], "memory_read")
        self.assertEqual(instructions["PMOVE"]["execution"]["semantic_op"], "pmove")
        self.assertEqual(instructions["PMOVE"]["execution"]["form_overrides"]["1"]["operands"][1]["expected_kind"], "ctrl_reg")
        self.assertEqual(instructions["PTEST"]["execution"]["semantic_op"], "ptest")
        ptest_writeback_operands = [
            operand
            for form in instructions["PTEST"]["execution"]["form_overrides"].values()
            for operand in form["operands"]
            if operand["index"] == 3
        ]
        self.assertTrue(any(operand["expected_kind"] == "an" for operand in ptest_writeback_operands))
        self.assertEqual(instructions["TRAP"]["execution"]["semantic_op"], "trap")
        self.assertEqual(instructions["ASL, ASR"]["execution"]["operands"][0]["access"]["width_source"], "instruction_size")
        self.assertEqual(instructions["LSL, LSR"]["execution"]["semantic_op"], "shift")
        self.assertEqual(instructions["ROL, ROR"]["execution"]["semantic_op"], "rotate")
        self.assertEqual(instructions["ROXL, ROXR"]["execution"]["semantic_op"], "rotate_extend")

    def test_only_width_irrelevant_accesses_remain_widthless(self) -> None:
        kb = json.loads((ROOT / "knowledge" / "m68k_instructions.json").read_text(encoding="utf-8"))
        unexpected = []
        widthless_ok = {"BFCHG", "BFCLR", "BFEXTS", "BFEXTU", "BFFFO", "BFINS", "BFSET", "BFTST", "CINV", "CPUSH", "PFLUSH", "PFLUSH PFLUSHA", "PFLUSHR", "PLOAD", "FSAVE", "FRESTORE", "PSAVE", "PRESTORE", "cpSAVE", "cpRESTORE", "PMOVE", "PTEST", "TRAP"}
        for inst in kb["instructions"]:
            execution = inst.get("execution")
            if not isinstance(execution, dict):
                continue
            for operand in execution.get("operands", []):
                access = operand.get("access", {})
                if isinstance(access, dict) and access.get("width") is None and access.get("width_source") is None:
                    if access.get("kind") not in {"branch_target", "compute_address"} and inst["mnemonic"] not in widthless_ok:
                        unexpected.append((inst["mnemonic"], "base", operand.get("index"), access.get("kind")))
            overrides = execution.get("form_overrides", {})
            if not isinstance(overrides, dict):
                continue
            for key, override in overrides.items():
                if not isinstance(override, dict):
                    continue
                for operand in override.get("operands", []):
                    access = operand.get("access", {})
                    if isinstance(access, dict) and access.get("width") is None and access.get("width_source") is None:
                        if access.get("kind") not in {"branch_target", "compute_address"} and inst["mnemonic"] not in widthless_ok:
                            unexpected.append((inst["mnemonic"], key, operand.get("index"), access.get("kind")))
        self.assertEqual(unexpected, [])

    def test_generated_tables_pass_style_checker(self) -> None:
        issues = self._checker.check_file(self._outdir / "m68k_simulator_tables.h", self._checker.DEFAULT_LINE_LENGTH)
        self.assertEqual(issues, [])

    def test_generates_exception_tables(self) -> None:
        self.assertIn("static const M68kSimExceptionFrameDef g_m68k_sim_exception_frames[] = {", self._tables)
        self.assertIn("M68K_SIM_EXCEPTION_FRAME_MC68000_GROUP_1_2", self._tables)
        self.assertIn("M68K_SIM_EXCEPTION_FRAME_FORMAT_0", self._tables)
        self.assertIn("M68K_SIM_EXCEPTION_FRAME_FORMAT_2", self._tables)

    def test_ea_metadata_validator_rejects_inconsistent_index_metadata(self) -> None:
        with self.assertRaises(AssertionError):
            self._generator._validate_ea_metadata(
                "TEST", 0, 0, "ea",
                "an_plus_disp", "none", "brief", "data_or_address",
                "extension_word", "extension_word", "extension_word",
                "operand_value", "displacement", "an", True, False,
            )

    def test_require_execution_for_forms_raises_on_missing_execution_metadata(self) -> None:
        kb = {"instructions": [{"mnemonic": "TRAP", "forms": [{"form_index": 0}]}]}
        fake_form = SimpleNamespace(mnemonic="TRAP", kb_mnemonic="TRAP", form_index=0, operand_kinds=())
        with self.assertRaisesRegex(AssertionError, r"Missing execution metadata"):
            self._generator._require_execution_for_forms([fake_form], kb)

    def test_current_subset_has_no_missing_execution_metadata(self) -> None:
        kb = self._generator._load_kb()
        forms = self._generator._load_forms()
        self._generator._require_execution_for_forms(forms, kb)


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
        if getattr(test, "_testMethodName", "") == "test_generated_tables_pass_style_checker":
          return
        suite.addTest(test)

    append_filtered(tests)
    return suite
