from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"
GENERATED_DIR = SRC_DIR / "generated"
KB_PATH = ROOT / "knowledge" / "m68k_instructions.json"
SUBSET_GENERATOR_PATH = SRC_DIR / "scripts" / "generate_c99_assembler_subset.py"
OUT_PATH = GENERATED_DIR / "m68k_simulator_tables.h"

FLOW_ENUM = {
    "none": "M68K_SIM_FLOW_NONE",
    "sequential": "M68K_SIM_FLOW_SEQUENTIAL",
    "branch": "M68K_SIM_FLOW_BRANCH",
    "jump": "M68K_SIM_FLOW_JUMP",
    "call": "M68K_SIM_FLOW_CALL",
    "return": "M68K_SIM_FLOW_RETURN",
    "trap": "M68K_SIM_FLOW_TRAP",
}

OP_TYPE_ENUM = {
    None: "M68K_SIM_OP_NONE",
    "nop": "M68K_SIM_OP_NONE",
    "reset": "M68K_SIM_OP_NONE",
    "rtm": "M68K_SIM_OP_NONE",
    "illegal": "M68K_SIM_OP_NONE",
    "bkpt": "M68K_SIM_OP_NONE",
    "stop": "M68K_SIM_OP_NONE",
    "trapv": "M68K_SIM_OP_TRAPV",
    "pack": "M68K_SIM_OP_PACK",
    "unpack": "M68K_SIM_OP_UNPACK",
    "multiply": "M68K_SIM_OP_MULTIPLY",
    "divide": "M68K_SIM_OP_DIVIDE",
    "bounds_check": "M68K_SIM_OP_BOUNDS_CHECK",
    "compare_swap": "M68K_SIM_OP_COMPARE_SWAP",
    "bitfield_change": "M68K_SIM_OP_BITFIELD_CHANGE",
    "bitfield_clear": "M68K_SIM_OP_BITFIELD_CLEAR",
    "bitfield_extract_signed": "M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED",
    "bitfield_extract_unsigned": "M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED",
    "bitfield_find_first_one": "M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE",
    "bitfield_insert": "M68K_SIM_OP_BITFIELD_INSERT",
    "bitfield_set": "M68K_SIM_OP_BITFIELD_SET",
    "bitfield_test": "M68K_SIM_OP_BITFIELD_TEST",
    "compute_ea": "M68K_SIM_OP_NONE",
    "add": "M68K_SIM_OP_ADD",
    "clear": "M68K_SIM_OP_CLEAR",
    "compare": "M68K_SIM_OP_COMPARE",
    "dbcc": "M68K_SIM_OP_DBCC",
    "move": "M68K_SIM_OP_MOVE",
    "move_value": "M68K_SIM_OP_MOVE",
    "move_address": "M68K_SIM_OP_MOVE",
    "move_multiple": "M68K_SIM_OP_MOVE_MULTIPLE",
    "move_peripheral": "M68K_SIM_OP_MOVE_PERIPHERAL",
    "logic_and": "M68K_SIM_OP_LOGIC_AND",
    "logic_or": "M68K_SIM_OP_LOGIC_OR",
    "logic_xor": "M68K_SIM_OP_LOGIC_XOR",
    "negate": "M68K_SIM_OP_NEGATE",
    "bitwise_not": "M68K_SIM_OP_NOT",
    "push_ea": "M68K_SIM_OP_PUSH_EA",
    "bit_test": "M68K_SIM_OP_BIT_TEST",
    "bit_set": "M68K_SIM_OP_BIT_SET",
    "bit_clear": "M68K_SIM_OP_BIT_CLEAR",
    "bit_change": "M68K_SIM_OP_BIT_CHANGE",
    "set_condition": "M68K_SIM_OP_SET_COND",
    "sub": "M68K_SIM_OP_SUB",
    "swap": "M68K_SIM_OP_SWAP",
    "swap_words": "M68K_SIM_OP_SWAP_WORDS",
    "shift": "M68K_SIM_OP_SHIFT",
    "rotate": "M68K_SIM_OP_ROTATE",
    "rotate_extend": "M68K_SIM_OP_ROTATE_EXTEND",
    "exchange": "M68K_SIM_OP_SWAP",
    "sign_extend": "M68K_SIM_OP_SIGN_EXTEND",
    "test": "M68K_SIM_OP_TEST",
    "test_and_set": "M68K_SIM_OP_TEST_AND_SET",
    "link": "M68K_SIM_OP_LINK",
    "unlk": "M68K_SIM_OP_UNLK",
    "write_constant": "M68K_SIM_OP_CLEAR",
}

OP_CLASS_ENUM = {
    None: "M68K_SIM_CLASS_NONE",
    "load_effective_address": "M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS",
    "multi_register_transfer": "M68K_SIM_CLASS_MULTI_REGISTER_TRANSFER",
}

SP_ACTION_ENUM = {
    "decrement": "M68K_SIM_SP_DECREMENT",
    "increment": "M68K_SIM_SP_INCREMENT",
    "adjust": "M68K_SIM_SP_ADJUST",
    "store_reg_to_stack": "M68K_SIM_SP_STORE_REG_TO_STACK",
    "save_to_reg": "M68K_SIM_SP_SAVE_TO_REG",
    "load_from_reg": "M68K_SIM_SP_LOAD_FROM_REG",
    "load_from_stack_to_reg": "M68K_SIM_SP_LOAD_FROM_STACK_TO_REG",
}

ACCESS_KIND_ENUM = {
    "register_read": "M68K_SIM_ACCESS_REGISTER_READ",
    "register_write": "M68K_SIM_ACCESS_REGISTER_WRITE",
    "memory_read": "M68K_SIM_ACCESS_MEMORY_READ",
    "memory_write": "M68K_SIM_ACCESS_MEMORY_WRITE",
    "compute_address": "M68K_SIM_ACCESS_COMPUTE_ADDRESS",
    "immediate": "M68K_SIM_ACCESS_IMMEDIATE",
    "branch_target": "M68K_SIM_ACCESS_BRANCH_TARGET",
    "register_list_read": "M68K_SIM_ACCESS_REGISTER_LIST_READ",
    "register_list_write": "M68K_SIM_ACCESS_REGISTER_LIST_WRITE",
}

EXPECTED_OPERAND_KIND_ENUM = {
    None: "M68K_SIM_EXPECT_ANY",
    "dn": "M68K_SIM_EXPECT_DN",
    "an": "M68K_SIM_EXPECT_AN",
    "rn": "M68K_SIM_EXPECT_RN",
    "ea": "M68K_SIM_EXPECT_EA",
    "ind": "M68K_SIM_EXPECT_IND",
    "postinc": "M68K_SIM_EXPECT_POSTINC",
    "predec": "M68K_SIM_EXPECT_PREDEC",
    "disp": "M68K_SIM_EXPECT_DISP",
    "index": "M68K_SIM_EXPECT_INDEX",
    "absw": "M68K_SIM_EXPECT_ABSW",
    "absl": "M68K_SIM_EXPECT_ABSL",
    "pcdisp": "M68K_SIM_EXPECT_PCDISP",
    "pcindex": "M68K_SIM_EXPECT_PCINDEX",
    "imm": "M68K_SIM_EXPECT_IMM",
    "label": "M68K_SIM_EXPECT_LABEL",
    "ccr": "M68K_SIM_EXPECT_CCR",
    "ctrl_reg": "M68K_SIM_EXPECT_CTRL_REG",
    "sr": "M68K_SIM_EXPECT_SR",
    "usp": "M68K_SIM_EXPECT_USP",
    "reglist": "M68K_SIM_EXPECT_REGLIST",
}

EA_ADDRESS_SHAPE_ENUM = {
    None: "M68K_SIM_EA_SHAPE_NONE",
    "indirect": "M68K_SIM_EA_SHAPE_INDIRECT",
    "postincrement": "M68K_SIM_EA_SHAPE_POSTINCREMENT",
    "predecrement": "M68K_SIM_EA_SHAPE_PREDECREMENT",
    "displacement": "M68K_SIM_EA_SHAPE_DISPLACEMENT",
    "index": "M68K_SIM_EA_SHAPE_INDEX",
    "absolute_word": "M68K_SIM_EA_SHAPE_ABSOLUTE_WORD",
    "absolute_long": "M68K_SIM_EA_SHAPE_ABSOLUTE_LONG",
    "pc_displacement": "M68K_SIM_EA_SHAPE_PC_DISPLACEMENT",
    "pc_index": "M68K_SIM_EA_SHAPE_PC_INDEX",
}

EA_ADDRESS_FORMULA_ENUM = {
    None: "M68K_SIM_EA_FORMULA_NONE",
    "decoded_ea": "M68K_SIM_EA_FORMULA_DECODED_EA",
    "an": "M68K_SIM_EA_FORMULA_AN",
    "an_plus_disp": "M68K_SIM_EA_FORMULA_AN_PLUS_DISP",
    "an_plus_disp_plus_index": "M68K_SIM_EA_FORMULA_AN_PLUS_DISP_PLUS_INDEX",
    "absolute_literal": "M68K_SIM_EA_FORMULA_ABSOLUTE_LITERAL",
    "pc_plus_disp": "M68K_SIM_EA_FORMULA_PC_PLUS_DISP",
    "pc_plus_disp_plus_index": "M68K_SIM_EA_FORMULA_PC_PLUS_DISP_PLUS_INDEX",
}

EA_REGISTER_UPDATE_ENUM = {
    None: "M68K_SIM_EA_UPDATE_NONE",
    "none": "M68K_SIM_EA_UPDATE_NONE",
    "postincrement": "M68K_SIM_EA_UPDATE_POSTINCREMENT",
    "predecrement": "M68K_SIM_EA_UPDATE_PREDECREMENT",
}

EA_INDEX_EXTENSION_FORMAT_ENUM = {
    None: "M68K_SIM_EA_INDEX_EXT_NONE",
    "none": "M68K_SIM_EA_INDEX_EXT_NONE",
    "brief": "M68K_SIM_EA_INDEX_EXT_BRIEF",
}

EA_INDEX_REGISTER_CLASS_ENUM = {
    None: "M68K_SIM_EA_INDEX_REG_NONE",
    "none": "M68K_SIM_EA_INDEX_REG_NONE",
    "data_or_address": "M68K_SIM_EA_INDEX_REG_DATA_OR_ADDRESS",
}

EA_INDEX_VALUE_WIDTH_SOURCE_ENUM = {
    None: "M68K_SIM_EA_INDEX_WIDTH_NONE",
    "none": "M68K_SIM_EA_INDEX_WIDTH_NONE",
    "extension_word": "M68K_SIM_EA_INDEX_WIDTH_EXTENSION_WORD",
}

EA_INDEX_SCALE_SOURCE_ENUM = {
    None: "M68K_SIM_EA_INDEX_SCALE_NONE",
    "none": "M68K_SIM_EA_INDEX_SCALE_NONE",
    "extension_word": "M68K_SIM_EA_INDEX_SCALE_EXTENSION_WORD",
}

EA_INDEX_SIGN_SOURCE_ENUM = {
    None: "M68K_SIM_EA_INDEX_SIGN_NONE",
    "none": "M68K_SIM_EA_INDEX_SIGN_NONE",
    "extension_word": "M68K_SIM_EA_INDEX_SIGN_EXTENSION_WORD",
}

EA_DISPLACEMENT_SOURCE_ENUM = {
    None: "M68K_SIM_EA_DISP_NONE",
    "none": "M68K_SIM_EA_DISP_NONE",
    "operand_value": "M68K_SIM_EA_DISP_OPERAND_VALUE",
}

EA_BASE_KIND_ENUM = {
    None: "M68K_SIM_EA_BASE_NONE",
    "an": "M68K_SIM_EA_BASE_AN",
    "pc": "M68K_SIM_EA_BASE_PC",
    "absolute": "M68K_SIM_EA_BASE_ABSOLUTE",
}

RESULT_KIND_ENUM = {
    "scalar": "M68K_SIM_RESULT_SCALAR",
    "address": "M68K_SIM_RESULT_ADDRESS",
    "control_target": "M68K_SIM_RESULT_CONTROL_TARGET",
}

WIDTH_MODE_ENUM = {
    None: "M68K_SIM_WIDTH_NONE",
    "fixed": "M68K_SIM_WIDTH_FIXED",
    "instruction_size": "M68K_SIM_WIDTH_INSTRUCTION_SIZE",
    "full_register": "M68K_SIM_WIDTH_FULL_REGISTER",
}

SHIFT_DIRECTION_ENUM = {
    None: "M68K_SIM_SHIFT_DIR_NONE",
    "left": "M68K_SIM_SHIFT_DIR_LEFT",
    "right": "M68K_SIM_SHIFT_DIR_RIGHT",
}

SHIFT_FILL_ENUM = {
    None: "M68K_SIM_SHIFT_FILL_NONE",
    "zero": "M68K_SIM_SHIFT_FILL_ZERO",
    "sign": "M68K_SIM_SHIFT_FILL_SIGN",
    "rotate": "M68K_SIM_SHIFT_FILL_ROTATE",
}

SHIFT_COUNT_SOURCE_ENUM = {
    "none": "M68K_SIM_SHIFT_COUNT_NONE",
    "operand": "M68K_SIM_SHIFT_COUNT_OPERAND",
    "implicit_one": "M68K_SIM_SHIFT_COUNT_IMPLICIT_ONE",
}

BOUNDS_MODE_ENUM = {
    "upper_only": "M68K_SIM_BOUNDS_UPPER_ONLY",
    "lower_upper_pair": "M68K_SIM_BOUNDS_LOWER_UPPER_PAIR",
}

EXCEPTION_VECTOR_SOURCE_ENUM = {
    None: "M68K_SIM_EXCEPTION_VECTOR_NONE",
    "fixed": "M68K_SIM_EXCEPTION_VECTOR_FIXED",
    "trap_immediate": "M68K_SIM_EXCEPTION_VECTOR_TRAP_IMMEDIATE",
}

EXCEPTION_TRIGGER_ENUM = {
    None: "M68K_SIM_EXCEPTION_TRIGGER_NONE",
    "always": "M68K_SIM_EXCEPTION_TRIGGER_ALWAYS",
    "if_overflow": "M68K_SIM_EXCEPTION_TRIGGER_IF_OVERFLOW",
    "if_bounds_fail": "M68K_SIM_EXCEPTION_TRIGGER_IF_BOUNDS_FAIL",
    "if_user_mode": "M68K_SIM_EXCEPTION_TRIGGER_IF_USER_MODE",
}

EXCEPTION_PC_SOURCE_ENUM = {
    None: "M68K_SIM_EXCEPTION_PC_CURRENT",
    "current": "M68K_SIM_EXCEPTION_PC_CURRENT",
    "next": "M68K_SIM_EXCEPTION_PC_NEXT",
}

EXCEPTION_ADDRESS_SOURCE_ENUM = {
    None: "M68K_SIM_EXCEPTION_ADDRESS_NONE",
    "none": "M68K_SIM_EXCEPTION_ADDRESS_NONE",
    "current_pc": "M68K_SIM_EXCEPTION_ADDRESS_CURRENT_PC",
}

EXCEPTION_STACKED_SR_SOURCE_ENUM = {
    None: "M68K_SIM_EXCEPTION_STACKED_SR_CURRENT",
    "current": "M68K_SIM_EXCEPTION_STACKED_SR_CURRENT",
    "updated_flags": "M68K_SIM_EXCEPTION_STACKED_SR_UPDATED_FLAGS",
}

RETURN_RESTORE_ENUM = {
    None: "M68K_SIM_RETURN_RESTORE_NONE",
    "pc_only": "M68K_SIM_RETURN_RESTORE_PC_ONLY",
    "ccr_then_pc": "M68K_SIM_RETURN_RESTORE_CCR_THEN_PC",
    "exception_frame": "M68K_SIM_RETURN_RESTORE_EXCEPTION_FRAME",
}

EXCEPTION_FRAME_KIND_ENUM = {
    "mc68000_group_1_2": "M68K_SIM_EXCEPTION_FRAME_MC68000_GROUP_1_2",
    "format_0": "M68K_SIM_EXCEPTION_FRAME_FORMAT_0",
    "format_2": "M68K_SIM_EXCEPTION_FRAME_FORMAT_2",
}

MULTI_TRANSFER_DIRECTION_ENUM = {
    "register_to_memory": "M68K_SIM_MULTI_REGISTER_TO_MEMORY",
    "memory_to_register": "M68K_SIM_MULTI_MEMORY_TO_REGISTER",
}

MULTI_TRANSFER_ADDRESS_UPDATE_ENUM = {
    "predecrement_if_predec": "M68K_SIM_MULTI_UPDATE_PREDECREMENT_IF_PREDEC",
    "postincrement_if_postinc": "M68K_SIM_MULTI_UPDATE_POSTINCREMENT_IF_POSTINC",
}

MULTI_TRANSFER_REG_ITERATION_ENUM = {
    "ascending_mask_bits": "M68K_SIM_MULTI_REG_ITERATION_ASCENDING_MASK_BITS",
}

MULTI_TRANSFER_SOURCE_SNAPSHOT_ENUM = {
    "before_write": "M68K_SIM_MULTI_SNAPSHOT_BEFORE_WRITE",
}

STRIPED_TRANSFER_DIRECTION_ENUM = {
    "register_to_memory": "M68K_SIM_STRIPED_REGISTER_TO_MEMORY",
    "memory_to_register": "M68K_SIM_STRIPED_MEMORY_TO_REGISTER",
}

CPU_MASK_ENUM = {
    "68000": "M68K_ASM_CPU_MASK_68000",
    "68010": "M68K_ASM_CPU_MASK_68010",
    "68020": "M68K_ASM_CPU_MASK_68020",
    "68030": "M68K_ASM_CPU_MASK_68030",
    "68040": "M68K_ASM_CPU_MASK_68040",
    "68EC040": "M68K_ASM_CPU_MASK_68040",
    "68LC040": "M68K_ASM_CPU_MASK_68040",
}


def _load_module(path: Path, name: str):
    root_text = str(ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_subset_module():
    return _load_module(SUBSET_GENERATOR_PATH, "src_c99_simulator_subset")


def _load_forms():
    subset = _load_subset_module()
    return subset._load_forms(KB_PATH, supported_mnemonics=subset.SUPPORTED_MNEMONICS)


def _load_kb() -> dict[str, object]:
    data = json.loads(KB_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _local_form_index(form: object) -> int:
    return int(getattr(form, "local_form_index", getattr(form, "form_index")))


def _eval_condition_expr(expr: str, n: int, z: int, v: int, c: int) -> bool:
    py_expr = expr.replace("!", " not ").replace("&", " and ").replace("|", " or ")
    return bool(eval(py_expr, {"__builtins__": {}}, {"N": bool(n), "Z": bool(z), "V": bool(v), "C": bool(c), "true": True, "false": False}))


def _condition_code_for_form(form: object, kb: dict[str, object]) -> int:
    meta = kb.get("_meta", {})
    if not isinstance(meta, dict):
        return 0xFF
    families = meta.get("condition_families", [])
    aliases = meta.get("cc_aliases", {})
    cc_defs = meta.get("cc_test_definitions", {})
    if not isinstance(families, list) or not isinstance(aliases, dict) or not isinstance(cc_defs, dict):
        return 0xFF
    mnemonic = str(form.mnemonic).lower()
    kb_mnemonic = str(form.kb_mnemonic).lower()
    for family in families:
        if not isinstance(family, dict):
            continue
        if str(family.get("canonical", "")) != kb_mnemonic.lower():
            continue
        prefix = str(family.get("prefix", "")).lower()
        if not mnemonic.startswith(prefix):
            continue
        suffix = mnemonic[len(prefix):]
        if not suffix:
            return 0xFF
        suffix = str(aliases.get(suffix, suffix)).lower()
        entry = cc_defs.get(suffix)
        if isinstance(entry, dict) and "encoding" in entry:
            return int(entry["encoding"])
    return 0xFF


def _condition_masks(kb: dict[str, object]) -> list[int]:
    meta = kb.get("_meta", {})
    assert isinstance(meta, dict)
    cc_defs = meta.get("cc_test_definitions", {})
    assert isinstance(cc_defs, dict)
    masks = [0] * 16
    for entry in cc_defs.values():
        assert isinstance(entry, dict)
        encoding = int(entry["encoding"])
        expr = str(entry["test"])
        mask = 0
        for n in (0, 1):
            for z in (0, 1):
                for v in (0, 1):
                    for c in (0, 1):
                        if _eval_condition_expr(expr, n, z, v, c):
                            state = (n << 3) | (z << 2) | (v << 1) | c
                            mask |= 1 << state
        masks[encoding] = mask
    return masks


def _instruction_by_mnemonic(kb: dict[str, object]) -> dict[str, dict[str, object]]:
    instructions = kb.get("instructions", [])
    assert isinstance(instructions, list)
    result: dict[str, dict[str, object]] = {}
    for entry in instructions:
        if isinstance(entry, dict) and isinstance(entry.get("mnemonic"), str):
            result[str(entry["mnemonic"])] = entry
    return result


def _cpu_mask_expr(processors: list[object]) -> str:
    parts: list[str] = []
    seen: set[str] = set()
    for processor in processors:
        if processor in CPU_MASK_ENUM:
            mask = CPU_MASK_ENUM[str(processor)]
            if mask not in seen:
                parts.append(mask)
                seen.add(mask)
    if not parts:
        return "0u"
    return " | ".join(parts)


def _frame_size_bytes(fields: list[object]) -> int:
    size_words = 0
    for field in fields:
        if isinstance(field, dict):
            offset = int(field.get("offset", 0))
            width_words = int(field.get("size_words", 1))
            size_words = max(size_words, (offset // 2) + width_words)
    return size_words * 2


def _emit_exception_tables(kb: dict[str, object]) -> list[str]:
    meta = kb.get("_meta", {})
    assert isinstance(meta, dict)
    frames = meta.get("exception_stack_frames", [])
    rules = meta.get("exception_frame_rules", [])
    assert isinstance(frames, list)
    assert isinstance(rules, list)

    frame_rows = []
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        frame_id = str(frame.get("frame_id", ""))
        if frame_id not in EXCEPTION_FRAME_KIND_ENUM:
            continue
        frame_rows.append(
            "    { "
            f"{EXCEPTION_FRAME_KIND_ENUM[frame_id]}, "
            f"{int(str(frame.get('format_code', '$0')).replace('$', '0x'), 16) if frame.get('format_code') else 0}u, "
            f"{_frame_size_bytes(frame.get('fields', []))}u, 0u "
            "},"
        )

    rule_rows = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        selection = str(rule.get("selection", ""))
        frame_ids = rule.get("frame_ids", [])
        processors = rule.get("processors", [])
        if selection != "always" or not isinstance(frame_ids, list) or not isinstance(processors, list) or not frame_ids:
            continue
        frame_id = str(frame_ids[0])
        if frame_id not in EXCEPTION_FRAME_KIND_ENUM:
            continue
        cpu_mask_expr = _cpu_mask_expr(processors)
        if len(cpu_mask_expr) > 72:
            rule_rows.extend([
                f"    {{ {int(rule.get('vector_start', 0))}u, {int(rule.get('vector_end', 0))}u,",
                f"      {cpu_mask_expr},",
                f"      {EXCEPTION_FRAME_KIND_ENUM[frame_id]} }},",
            ])
        else:
            rule_rows.append(
                "    { "
                f"{int(rule.get('vector_start', 0))}u, "
                f"{int(rule.get('vector_end', 0))}u, "
                f"{cpu_mask_expr}, "
                f"{EXCEPTION_FRAME_KIND_ENUM[frame_id]} "
                "},"
            )

    return [
        "static const M68kSimExceptionFrameDef g_m68k_sim_exception_frames[] = {",
        *frame_rows,
        "};",
        "",
        "static const M68kSimExceptionFrameRule g_m68k_sim_exception_frame_rules[] = {",
        *rule_rows,
        "};",
        "",
    ]


def _form_operand_kind(form: object, operand_index: int) -> str | None:
    operand_kinds = getattr(form, "operand_kinds", ())
    if operand_index < 0 or operand_index >= len(operand_kinds):
        return None
    return str(operand_kinds[operand_index])


def _specialized_expected_kind(operand: dict[str, object], form: object, operand_index: int) -> str:
    expected_kind = str(operand.get("expected_kind", "any"))
    form_kind = _form_operand_kind(form, operand_index)
    if expected_kind in {"ea", "any"} and form_kind in EXPECTED_OPERAND_KIND_ENUM:
        return form_kind
    return expected_kind


def _specialized_ea_field(operand: dict[str, object], form: object, operand_index: int, key: str,
                          mapper) -> object:
    value = operand.get(key)
    form_kind = _form_operand_kind(form, operand_index)
    if value not in (None, False) or form_kind is None:
        return value
    return mapper(form_kind)


def _validate_ea_metadata(mnemonic: str, asm_form_index: int, operand_index: int, expected_kind: str,
                          ea_formula: object, ea_update: object, ea_index_ext_format: object,
                          ea_index_reg_class: object, ea_index_width_source: object,
                          ea_index_scale_source: object, ea_index_sign_source: object,
                          ea_displacement_source: object, ea_shape: object,
                          ea_base_kind: object, ea_uses_displacement: bool,
                          ea_uses_index: bool) -> None:
    label = f"{mnemonic} form {asm_form_index} operand {operand_index}"
    indexed_formulas = {"an_plus_disp_plus_index", "pc_plus_disp_plus_index"}
    displacement_formulas = {"an_plus_disp", "an_plus_disp_plus_index", "pc_plus_disp", "pc_plus_disp_plus_index"}
    if ea_update == "postincrement":
        assert ea_shape == "postincrement", f"{label}: postincrement update requires postincrement shape"
    if ea_update == "predecrement":
        assert ea_shape == "predecrement", f"{label}: predecrement update requires predecrement shape"
    if ea_displacement_source == "operand_value":
        assert ea_uses_displacement, f"{label}: displacement source requires displacement"
        assert ea_formula in displacement_formulas, f"{label}: displacement source requires displacement formula"
    if ea_uses_index:
        assert ea_formula in indexed_formulas, f"{label}: indexed EA requires indexed formula"
        assert ea_shape in {"index", "pc_index"}, f"{label}: indexed EA requires indexed shape"
        assert ea_index_ext_format != "none", f"{label}: indexed EA requires index extension format"
        assert ea_index_reg_class != "none", f"{label}: indexed EA requires index register class"
        assert ea_index_width_source != "none", f"{label}: indexed EA requires index width source"
        assert ea_index_scale_source != "none", f"{label}: indexed EA requires index scale source"
        assert ea_index_sign_source != "none", f"{label}: indexed EA requires index sign source"
    else:
        assert ea_index_ext_format == "none", f"{label}: non-indexed EA must not carry index extension format"
        assert ea_index_reg_class == "none", f"{label}: non-indexed EA must not carry index register class"
        assert ea_index_width_source == "none", f"{label}: non-indexed EA must not carry index width source"
        assert ea_index_scale_source == "none", f"{label}: non-indexed EA must not carry index scale source"
        assert ea_index_sign_source == "none", f"{label}: non-indexed EA must not carry index sign source"
    if ea_formula == "absolute_literal":
        assert ea_base_kind == "absolute", f"{label}: absolute literal requires absolute base"
    if ea_formula in {"pc_plus_disp", "pc_plus_disp_plus_index"}:
        assert ea_base_kind == "pc", f"{label}: PC-relative formula requires PC base"
    if expected_kind in {"postinc", "predec", "disp", "index", "absw", "absl", "pcdisp", "pcindex"}:
        assert ea_shape not in (None, "none"), f"{label}: concrete EA kind requires EA shape"


def _operand_index_by_role(execution: dict[str, object] | None, role: str) -> int:
    if execution is None:
        return 0xFF
    operands = execution.get("operands", [])
    if not isinstance(operands, list):
        return 0xFF
    for operand in operands:
        if isinstance(operand, dict) and operand.get("role") == role:
            return int(operand.get("index", 0xFF))
    if role == "dest":
        for operand in operands:
            if isinstance(operand, dict) and operand.get("usage") == "read_modify_write":
                return int(operand.get("index", 0xFF))
    return 0xFF


def _execution_for_form(entry: dict[str, object], mnemonic: str, kb_mnemonic: str,
                        asm_form_index: int | None = None) -> dict[str, object] | None:
    execution = entry.get("execution")
    if execution is None:
        return None
    if not isinstance(execution, dict):
        raise AssertionError(f"Missing execution metadata for {mnemonic} (kb={kb_mnemonic})")
    overrides = execution.get("form_overrides")
    if isinstance(overrides, dict):
        override = overrides.get(str(asm_form_index)) if asm_form_index is not None else None
    else:
        override = None
    if not isinstance(override, dict):
        return execution
    merged = dict(execution)
    for key, value in override.items():
        merged[key] = value
    return merged


def _shift_variant_for_form(entry: dict[str, object], form: object) -> dict[str, object] | None:
    variants = entry.get("variants", [])
    mnemonic = str(form.mnemonic).upper()
    if not isinstance(variants, list):
        return None
    for variant in variants:
        if isinstance(variant, dict) and str(variant.get("mnemonic", "")).upper() == mnemonic:
            return variant
    return None


def _specialize_shift_execution(entry: dict[str, object], execution: dict[str, object], form: object) -> dict[str, object]:
    semantic_op = str(execution.get("semantic_op", ""))
    constraints = entry.get("constraints", {})
    operand_kinds = tuple(str(kind) for kind in getattr(form, "operand_kinds", ()))
    width_is_memory_word_only = isinstance(constraints, dict) and constraints.get("memory_size_only") == "w"
    variant = _shift_variant_for_form(entry, form)
    if semantic_op not in {"shift", "rotate", "rotate_extend"} or not operand_kinds:
        return execution
    specialized = dict(execution)
    operands: list[dict[str, object]] = []
    if len(operand_kinds) == 2:
        source_kind, dest_kind = operand_kinds
        operands = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": source_kind,
                "access": {
                    "kind": "immediate" if source_kind == "imm" else "register_read",
                    "width": None,
                    "width_source": "instruction_size",
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "dest",
                "usage": "read_modify_write",
                "expected_kind": dest_kind,
                "access": {
                    "kind": "register_write",
                    "width": None,
                    "width_source": "instruction_size",
                    "result_kind": "scalar",
                },
            },
        ]
    elif len(operand_kinds) == 1:
        dest_kind = operand_kinds[0]
        operands = [
            {
                "index": 0,
                "role": "dest",
                "usage": "read_modify_write",
                "expected_kind": dest_kind,
                "access": {
                    "kind": "memory_write",
                    "width": 2 if width_is_memory_word_only else None,
                    "width_source": None if width_is_memory_word_only else "instruction_size",
                    "result_kind": "scalar",
                },
            },
        ]
    specialized["operands"] = operands
    specialized["shift"] = {
        "direction": variant.get("direction") if isinstance(variant, dict) else None,
        "fill": variant.get("fill") if isinstance(variant, dict) else None,
        "count_source": "implicit_one" if len(operand_kinds) == 1 else "operand",
        "count_modulus": int(entry.get("shift_count_modulus", 0) or 0),
        "rotate_extra_bits": int(entry.get("rotate_extra_bits", 0) or 0),
    }
    return specialized


def _collect_missing_execution_forms(forms: list[object], kb: dict[str, object]) -> list[tuple[str, str, int]]:
    by_mnemonic = _instruction_by_mnemonic(kb)
    missing: list[tuple[str, str, int]] = []
    for form in forms:
        mnemonic = str(form.mnemonic)
        kb_mnemonic = str(form.kb_mnemonic)
        entry = by_mnemonic.get(kb_mnemonic, by_mnemonic.get(mnemonic))
        assert entry is not None
        execution = _execution_for_form(entry, mnemonic, kb_mnemonic, _local_form_index(form))
        if execution is None:
            missing.append((mnemonic, kb_mnemonic, _local_form_index(form)))
    return missing


def _require_execution_for_forms(forms: list[object], kb: dict[str, object]) -> None:
    missing = _collect_missing_execution_forms(forms, kb)
    if not missing:
        return
    preview = ", ".join(
        f"{mnemonic}/{kb_mnemonic}#{asm_form_index}"
        for mnemonic, kb_mnemonic, asm_form_index in missing[:12]
    )
    if len(missing) > 12:
        preview += ", ..."
    raise AssertionError(f"Missing execution metadata for {len(missing)} emitted simulator forms: {preview}")


def _emit_tables_include(forms: list[object], kb: dict[str, object]) -> str:
    _require_execution_for_forms(forms, kb)
    by_mnemonic = _instruction_by_mnemonic(kb)
    meta = kb.get("_meta", {})
    assert isinstance(meta, dict)
    ccr_bits = meta.get("ccr_bit_positions", {})
    assert isinstance(ccr_bits, dict)
    condition_masks = _condition_masks(kb)
    condition_mask_rows = [
        "    " + ", ".join(f"0x{mask:04X}u" for mask in condition_masks[index:index + 8]) + ","
        for index in range(0, len(condition_masks), 8)
    ]
    sp_rows: list[str] = []
    form_rows: list[str] = []
    emitted_form_count = 0
    sp_start = 0
    for form in forms:
        mnemonic = str(form.mnemonic)
        kb_mnemonic = str(form.kb_mnemonic)
        entry = by_mnemonic.get(kb_mnemonic, by_mnemonic.get(mnemonic))
        assert entry is not None
        execution = _execution_for_form(entry, mnemonic, kb_mnemonic, _local_form_index(form))
        if execution is None:
            continue
        execution = _specialize_shift_execution(entry, execution, form)
        flow = execution.get("flow", {}) if isinstance(execution, dict) else {}
        assert isinstance(flow, dict)
        flow_type = str(flow.get("kind", "none"))
        execution_operands = execution.get("operands", []) if isinstance(execution, dict) else []
        assert isinstance(execution_operands, list)
        stack = execution.get("stack", {}) if isinstance(execution, dict) else {}
        assert isinstance(stack, dict)
        multi_transfer = execution.get("multi_transfer", {}) if isinstance(execution, dict) else {}
        assert isinstance(multi_transfer, dict)
        striped_transfer = execution.get("striped_transfer", {}) if isinstance(execution, dict) else {}
        assert isinstance(striped_transfer, dict)
        unary = execution.get("unary", {}) if isinstance(execution, dict) else {}
        assert isinstance(unary, dict)
        shift = execution.get("shift", {}) if isinstance(execution, dict) else {}
        assert isinstance(shift, dict)
        bounds = entry.get("bounds_check", {})
        assert isinstance(bounds, dict)
        exception = execution.get("exception", {}) if isinstance(execution, dict) else {}
        assert isinstance(exception, dict)
        return_effect = execution.get("return", {}) if isinstance(execution, dict) else {}
        assert isinstance(return_effect, dict)
        bounds_mode = "none"
        if bounds.get("lower_bound") == "zero" and bounds.get("upper_bound") == "source":
            bounds_mode = "upper_only"
        elif bounds.get("lower_bound") == "ea_lower" and bounds.get("upper_bound") == "ea_upper":
            bounds_mode = "lower_upper_pair"
        numeric_is_signed = 1 if entry.get("signed") or bounds.get("comparison") == "signed" else 0
        sp_effects = stack.get("effects", []) if isinstance(execution, dict) else []
        assert isinstance(sp_effects, list)
        access_kinds = ["M68K_SIM_ACCESS_NONE"] * 4
        expected_kinds = ["M68K_SIM_EXPECT_ANY"] * 4
        ea_formulas = ["M68K_SIM_EA_FORMULA_NONE"] * 4
        ea_updates = ["M68K_SIM_EA_UPDATE_NONE"] * 4
        ea_index_ext_formats = ["M68K_SIM_EA_INDEX_EXT_NONE"] * 4
        ea_index_reg_classes = ["M68K_SIM_EA_INDEX_REG_NONE"] * 4
        ea_index_width_sources = ["M68K_SIM_EA_INDEX_WIDTH_NONE"] * 4
        ea_index_scale_sources = ["M68K_SIM_EA_INDEX_SCALE_NONE"] * 4
        ea_index_sign_sources = ["M68K_SIM_EA_INDEX_SIGN_NONE"] * 4
        ea_displacement_sources = ["M68K_SIM_EA_DISP_NONE"] * 4
        ea_shapes = ["M68K_SIM_EA_SHAPE_NONE"] * 4
        ea_base_kinds = ["M68K_SIM_EA_BASE_NONE"] * 4
        ea_uses_displacement = ["0u"] * 4
        ea_uses_index = ["0u"] * 4
        ea_pc_base_biases = ["0u"] * 4
        ea_literal_widths = ["0u"] * 4
        result_kinds = ["M68K_SIM_RESULT_NONE"] * 4
        operand_width_modes = ["M68K_SIM_WIDTH_NONE"] * 4
        operand_widths = ["0u"] * 4
        for operand in execution_operands:
            if not isinstance(operand, dict):
                continue
            operand_index = int(operand.get("index", -1))
            if operand_index < 0 or operand_index >= 4:
                continue
            access = operand.get("access", {})
            if not isinstance(access, dict):
                continue
            access_kind = str(access.get("kind", ""))
            access_kinds[operand_index] = ACCESS_KIND_ENUM.get(
                access_kind,
                "M68K_SIM_ACCESS_NONE",
            )
            expected_kind = _specialized_expected_kind(operand, form, operand_index)
            expected_kinds[operand_index] = EXPECTED_OPERAND_KIND_ENUM.get(
                expected_kind,
                "M68K_SIM_EXPECT_ANY",
            )
            ea_formula = _specialized_ea_field(
                operand, form, operand_index, "ea_address_formula",
                lambda kind: {
                    "ind": "an",
                    "postinc": "an",
                    "predec": "an",
                    "disp": "an_plus_disp",
                    "index": "an_plus_disp_plus_index",
                    "absw": "absolute_literal",
                    "absl": "absolute_literal",
                    "pcdisp": "pc_plus_disp",
                    "pcindex": "pc_plus_disp_plus_index",
                }.get(kind),
            )
            ea_formulas[operand_index] = EA_ADDRESS_FORMULA_ENUM.get(
                ea_formula,
                "M68K_SIM_EA_FORMULA_NONE",
            )
            ea_update = _specialized_ea_field(
                operand, form, operand_index, "ea_register_update",
                lambda kind: "postincrement" if kind == "postinc" else (
                    "predecrement" if kind == "predec" else "none"
                ),
            )
            ea_updates[operand_index] = EA_REGISTER_UPDATE_ENUM.get(
                ea_update,
                "M68K_SIM_EA_UPDATE_NONE",
            )
            ea_index_ext_format = _specialized_ea_field(
                operand, form, operand_index, "ea_index_extension_format",
                lambda kind: "brief" if kind in {"index", "pcindex"} else "none",
            )
            ea_index_ext_formats[operand_index] = EA_INDEX_EXTENSION_FORMAT_ENUM.get(
                ea_index_ext_format,
                "M68K_SIM_EA_INDEX_EXT_NONE",
            )
            ea_index_reg_class = _specialized_ea_field(
                operand, form, operand_index, "ea_index_register_class",
                lambda kind: "data_or_address" if kind in {"index", "pcindex"} else "none",
            )
            ea_index_reg_classes[operand_index] = EA_INDEX_REGISTER_CLASS_ENUM.get(
                ea_index_reg_class,
                "M68K_SIM_EA_INDEX_REG_NONE",
            )
            ea_index_width_source = _specialized_ea_field(
                operand, form, operand_index, "ea_index_value_width_source",
                lambda kind: "extension_word" if kind in {"index", "pcindex"} else "none",
            )
            ea_index_width_sources[operand_index] = EA_INDEX_VALUE_WIDTH_SOURCE_ENUM.get(
                ea_index_width_source,
                "M68K_SIM_EA_INDEX_WIDTH_NONE",
            )
            ea_index_scale_source = _specialized_ea_field(
                operand, form, operand_index, "ea_index_scale_source",
                lambda kind: "extension_word" if kind in {"index", "pcindex"} else "none",
            )
            ea_index_scale_sources[operand_index] = EA_INDEX_SCALE_SOURCE_ENUM.get(
                ea_index_scale_source,
                "M68K_SIM_EA_INDEX_SCALE_NONE",
            )
            ea_index_sign_source = _specialized_ea_field(
                operand, form, operand_index, "ea_index_sign_source",
                lambda kind: "extension_word" if kind in {"index", "pcindex"} else "none",
            )
            ea_index_sign_sources[operand_index] = EA_INDEX_SIGN_SOURCE_ENUM.get(
                ea_index_sign_source,
                "M68K_SIM_EA_INDEX_SIGN_NONE",
            )
            ea_displacement_source = _specialized_ea_field(
                operand, form, operand_index, "ea_displacement_source",
                lambda kind: "operand_value" if kind in {"disp", "index", "pcdisp", "pcindex"} else "none",
            )
            ea_displacement_sources[operand_index] = EA_DISPLACEMENT_SOURCE_ENUM.get(
                ea_displacement_source,
                "M68K_SIM_EA_DISP_NONE",
            )
            ea_shape = _specialized_ea_field(
                operand, form, operand_index, "ea_address_shape",
                lambda kind: {
                    "ind": "indirect",
                    "postinc": "postincrement",
                    "predec": "predecrement",
                    "disp": "displacement",
                    "index": "index",
                    "absw": "absolute_word",
                    "absl": "absolute_long",
                    "pcdisp": "pc_displacement",
                    "pcindex": "pc_index",
                }.get(kind),
            )
            ea_shapes[operand_index] = EA_ADDRESS_SHAPE_ENUM.get(
                ea_shape,
                "M68K_SIM_EA_SHAPE_NONE",
            )
            ea_base_kind = _specialized_ea_field(
                operand, form, operand_index, "ea_base_kind",
                lambda kind: {
                    "ind": "an",
                    "postinc": "an",
                    "predec": "an",
                    "disp": "an",
                    "index": "an",
                    "pcdisp": "pc",
                    "pcindex": "pc",
                    "absw": "absolute",
                    "absl": "absolute",
                }.get(kind),
            )
            ea_base_kinds[operand_index] = EA_BASE_KIND_ENUM.get(
                ea_base_kind,
                "M68K_SIM_EA_BASE_NONE",
            )
            uses_displacement = bool(_specialized_ea_field(
                operand, form, operand_index, "ea_uses_displacement",
                lambda kind: kind in {"disp", "index", "pcdisp", "pcindex"},
            ))
            ea_uses_displacement[operand_index] = "1u" if uses_displacement else "0u"
            uses_index = bool(_specialized_ea_field(
                operand, form, operand_index, "ea_uses_index",
                lambda kind: kind in {"index", "pcindex"},
            ))
            ea_uses_index[operand_index] = "1u" if uses_index else "0u"
            ea_pc_base_bias = _specialized_ea_field(
                operand,
                form,
                operand_index,
                "ea_pc_base_bias_bytes",
                lambda kind: 2 if kind in {"pcdisp", "pcindex"} else 0,
            )
            ea_pc_base_biases[operand_index] = f"{int(ea_pc_base_bias)}u"
            ea_literal_width = _specialized_ea_field(
                operand,
                form,
                operand_index,
                "ea_address_literal_width_bytes",
                lambda kind: 2 if kind == "absw" else (4 if kind == "absl" else 0),
            )
            ea_literal_widths[operand_index] = f"{int(ea_literal_width)}u"
            result_kinds[operand_index] = RESULT_KIND_ENUM.get(
                str(access.get("result_kind", "")),
                "M68K_SIM_RESULT_NONE",
            )
            width_source = access.get("width_source")
            width = access.get("width")
            if width is not None:
                operand_width_modes[operand_index] = WIDTH_MODE_ENUM["fixed"]
                operand_widths[operand_index] = f"{int(width)}u"
            elif width_source in WIDTH_MODE_ENUM:
                operand_width_modes[operand_index] = WIDTH_MODE_ENUM[width_source]
                operand_widths[operand_index] = "0u"
            _validate_ea_metadata(
                mnemonic,
                _local_form_index(form),
                operand_index,
                expected_kind,
                ea_formula,
                ea_update,
                ea_index_ext_format,
                ea_index_reg_class,
                ea_index_width_source,
                ea_index_scale_source,
                ea_index_sign_source,
                ea_displacement_source,
                ea_shape,
                ea_base_kind,
                uses_displacement,
                uses_index,
            )
        for effect in sp_effects:
            assert isinstance(effect, dict)
            sp_rows.append(
                "    { "
                f"{SP_ACTION_ENUM[str(effect.get('action', 'adjust'))]}, "
                f"{int(effect.get('bytes', 0))}, "
                f"\"{str(effect.get('reg', ''))}\", "
                f"\"{str(effect.get('operand', ''))}\" "
                "},"
            )
        row_mnemonic = kb_mnemonic if (" " in kb_mnemonic and "," not in kb_mnemonic) else str(form.mnemonic)
        mnemonic_enum = f"M68K_ASM_MNEMONIC_{str(form.mnemonic)}"
        form_rows.extend([
            "    {",
            f"      {mnemonic_enum}, {form.form_index}u, {{ 0u, 0u }},",
            "      {",
            "      "
            f"{OP_TYPE_ENUM.get(execution.get('semantic_op') if isinstance(execution, dict) else None, 'M68K_SIM_OP_NONE')}, "
            f"{OP_CLASS_ENUM.get(execution.get('operation_class') if isinstance(execution, dict) else None, 'M68K_SIM_CLASS_NONE')}, "
            f"{FLOW_ENUM.get(flow_type, 'M68K_SIM_FLOW_NONE')}, "
            f"{1 if bool(flow.get('conditional', False)) else 0}u, "
            f"{1 if isinstance(execution, dict) and isinstance(execution.get('result'), dict) and execution['result'].get('formula') else 0}u,",
            "      { "
            f"{access_kinds[0]}, {access_kinds[1]}, {access_kinds[2]}, {access_kinds[3]} "
            "},",
            "      { "
            f"{expected_kinds[0]}, {expected_kinds[1]}, {expected_kinds[2]}, {expected_kinds[3]} "
            "},",
            "      { "
            f"{ea_formulas[0]}, {ea_formulas[1]}, {ea_formulas[2]}, {ea_formulas[3]} "
            "},",
            "      { "
            f"{ea_updates[0]}, {ea_updates[1]}, {ea_updates[2]}, {ea_updates[3]} "
            "},",
            "      { "
            f"{ea_index_ext_formats[0]}, {ea_index_ext_formats[1]}, {ea_index_ext_formats[2]}, {ea_index_ext_formats[3]} "
            "},",
            "      { "
            f"{ea_index_reg_classes[0]}, {ea_index_reg_classes[1]}, {ea_index_reg_classes[2]}, {ea_index_reg_classes[3]} "
            "},",
            "      { "
            f"{ea_index_width_sources[0]}, {ea_index_width_sources[1]}, {ea_index_width_sources[2]}, {ea_index_width_sources[3]} "
            "},",
            "      { "
            f"{ea_index_scale_sources[0]}, {ea_index_scale_sources[1]}, {ea_index_scale_sources[2]}, {ea_index_scale_sources[3]} "
            "},",
            "      { "
            f"{ea_index_sign_sources[0]}, {ea_index_sign_sources[1]}, {ea_index_sign_sources[2]}, {ea_index_sign_sources[3]} "
            "},",
            "      { "
            f"{ea_displacement_sources[0]}, {ea_displacement_sources[1]}, {ea_displacement_sources[2]}, {ea_displacement_sources[3]} "
            "},",
            "      { "
            f"{ea_shapes[0]}, {ea_shapes[1]}, {ea_shapes[2]}, {ea_shapes[3]} "
            "},",
            "      { "
            f"{ea_base_kinds[0]}, {ea_base_kinds[1]}, {ea_base_kinds[2]}, {ea_base_kinds[3]} "
            "},",
            "      { "
            f"{ea_uses_displacement[0]}, {ea_uses_displacement[1]}, {ea_uses_displacement[2]}, {ea_uses_displacement[3]} "
            "},",
            "      { "
            f"{ea_uses_index[0]}, {ea_uses_index[1]}, {ea_uses_index[2]}, {ea_uses_index[3]} "
            "},",
            "      { "
            f"{ea_pc_base_biases[0]}, {ea_pc_base_biases[1]}, {ea_pc_base_biases[2]}, {ea_pc_base_biases[3]} "
            "},",
            "      { "
            f"{ea_literal_widths[0]}, {ea_literal_widths[1]}, {ea_literal_widths[2]}, {ea_literal_widths[3]} "
            "},",
            "      { "
            f"{result_kinds[0]}, {result_kinds[1]}, {result_kinds[2]}, {result_kinds[3]} "
            "},",
            "      { "
            f"{operand_width_modes[0]}, {operand_width_modes[1]}, {operand_width_modes[2]}, {operand_width_modes[3]} "
            "},",
            "      { "
            f"{operand_widths[0]}, {operand_widths[1]}, {operand_widths[2]}, {operand_widths[3]} "
            "},",
            "      "
            f"{sp_start}u, {len(sp_effects)}u, "
            f"{_operand_index_by_role(execution, 'source') if isinstance(execution, dict) else 0xFF}u, "
            f"{_operand_index_by_role(execution, 'dest') if isinstance(execution, dict) else 0xFF}u, "
            f"{_operand_index_by_role(execution, 'target') if isinstance(execution, dict) else 0xFF}u, "
            f"{_condition_code_for_form(form, kb)}u,",
            "      "
            f"{int(multi_transfer.get('reglist_operand_index', 0xFF))}u, "
            f"{int(multi_transfer.get('address_operand_index', 0xFF))}u, "
            f"{MULTI_TRANSFER_DIRECTION_ENUM.get(str(multi_transfer.get('direction', '')), 'M68K_SIM_MULTI_NONE')}, "
            f"{MULTI_TRANSFER_ADDRESS_UPDATE_ENUM.get(str(multi_transfer.get('address_update', '')), 'M68K_SIM_MULTI_UPDATE_NONE')},",
            "      "
            f"{MULTI_TRANSFER_REG_ITERATION_ENUM.get(str(multi_transfer.get('reg_iteration', '')), 'M68K_SIM_MULTI_REG_ITERATION_NONE')}, "
            f"{MULTI_TRANSFER_SOURCE_SNAPSHOT_ENUM.get(str(multi_transfer.get('source_snapshot', '')), 'M68K_SIM_MULTI_SNAPSHOT_NONE')}, "
            f"{int(striped_transfer.get('reg_operand_index', 0xFF))}u, "
            f"{int(striped_transfer.get('address_operand_index', 0xFF))}u,",
            "      "
            f"{STRIPED_TRANSFER_DIRECTION_ENUM.get(str(striped_transfer.get('direction', '')), 'M68K_SIM_STRIPED_NONE')}, "
            f"{int(striped_transfer.get('stride', 0))}u, "
            f"{1 if str(striped_transfer.get('byte_order', '')) == 'big_endian' else 0}u, "
            f"{int(unary.get('sign_extend_source_bits', 0))}u, ",
            "      "
            f"{SHIFT_DIRECTION_ENUM.get(shift.get('direction'), 'M68K_SIM_SHIFT_DIR_NONE')}, "
            f"{SHIFT_FILL_ENUM.get(shift.get('fill'), 'M68K_SIM_SHIFT_FILL_NONE')}, "
            f"{SHIFT_COUNT_SOURCE_ENUM.get(str(shift.get('count_source', 'none')), 'M68K_SIM_SHIFT_COUNT_NONE')}, "
            f"{int(shift.get('count_modulus', 0))}u, "
            f"{int(shift.get('rotate_extra_bits', 0))}u, "
            f"{numeric_is_signed}u, "
            f"{BOUNDS_MODE_ENUM.get(bounds_mode, 'M68K_SIM_BOUNDS_NONE')}, "
            f"{1 if bounds.get('trap_on_out_of_bounds') else 0}u,",
            "      "
            f"{EXCEPTION_VECTOR_SOURCE_ENUM.get(exception.get('vector_source'), 'M68K_SIM_EXCEPTION_VECTOR_NONE')}, "
            f"{EXCEPTION_TRIGGER_ENUM.get(exception.get('trigger'), 'M68K_SIM_EXCEPTION_TRIGGER_NONE')}, "
            f"{EXCEPTION_PC_SOURCE_ENUM.get(exception.get('pc_source'), 'M68K_SIM_EXCEPTION_PC_CURRENT')},",
            "      "
            f"{EXCEPTION_ADDRESS_SOURCE_ENUM.get(exception.get('address_source'), 'M68K_SIM_EXCEPTION_ADDRESS_NONE')}, "
            f"{EXCEPTION_STACKED_SR_SOURCE_ENUM.get(exception.get('stacked_sr_source'), 'M68K_SIM_EXCEPTION_STACKED_SR_CURRENT')}, "
            f"{RETURN_RESTORE_ENUM.get(return_effect.get('restore'), 'M68K_SIM_RETURN_RESTORE_NONE')}, "
            f"{int(return_effect.get('stack_adjust_operand_index', 0xFF)) if return_effect.get('stack_adjust_operand_index') is not None else 0xFF}u, "
            f"{int(exception.get('vector', 0))}u",
            "      }",
            "    },",
        ])
        emitted_form_count += 1
        sp_start += len(sp_effects)
    return "\n".join(line.rstrip() for line in [
        f"static const uint8_t g_m68k_sim_ccr_bit_n = {int(ccr_bits['N'])}u;",
        f"static const uint8_t g_m68k_sim_ccr_bit_z = {int(ccr_bits['Z'])}u;",
        f"static const uint8_t g_m68k_sim_ccr_bit_v = {int(ccr_bits['V'])}u;",
        f"static const uint8_t g_m68k_sim_ccr_bit_c = {int(ccr_bits['C'])}u;",
        "static const uint16_t g_m68k_sim_condition_masks[16] = {",
        *condition_mask_rows,
        "};",
        "",
        "static const M68kSimSpEffectDef g_m68k_sim_sp_effects[] = {",
        *sp_rows,
        "};",
        "",
        *_emit_exception_tables(kb),
        f"static const M68kSimFormLookup g_m68k_sim_form_lookup[{emitted_form_count}] = {{",
        *form_rows,
        "};",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate KB-driven simulator metadata for the C subset.")
    parser.add_argument("--output", type=Path, default=OUT_PATH)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_emit_tables_include(_load_forms(), _load_kb()), encoding="ascii")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
