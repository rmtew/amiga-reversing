from __future__ import annotations

import ast
import copy
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import build_runtime_kb
from m68k import m68k_asm
from tests.runtime_kb_helpers import (
    KNOWLEDGE,
    load_m68k_asm_runtime_module,
    load_m68k_analysis_runtime_module,
    load_m68k_compute_runtime_module,
    load_canonical_hunk_kb,
    load_canonical_m68k_kb,
    load_m68k_decode_runtime_module,
    load_m68k_disasm_runtime_module,
    load_m68k_executor_runtime_module,
    load_canonical_naming_rules,
    load_canonical_os_kb,
    load_hunk_runtime_kb,
    load_m68k_runtime_module,
    load_naming_runtime_kb,
    load_os_runtime_kb,
)


def test_production_modules_import_generated_runtime_modules_directly():
    repo_root = Path(__file__).resolve().parent.parent
    for path in list((repo_root / "m68k").glob("*.py")) + list((repo_root / "disasm").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "runtime_kb":
                raise AssertionError(f"{path} still imports runtime_kb relatively")
            if isinstance(node, ast.ImportFrom) and node.module == "m68k.runtime_kb":
                raise AssertionError(f"{path} still imports m68k.runtime_kb")


def test_production_modules_do_not_read_canonical_instruction_bag_fields():
    repo_root = Path(__file__).resolve().parent.parent
    forbidden = {
        "forms",
        "constraints",
        "ea_modes",
        "pc_effects",
        "encodings",
        "processor_min",
        "operation_type",
        "operation_class",
    }
    for path in list((repo_root / "m68k").glob("*.py")) + list((repo_root / "disasm").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Subscript):
                continue
            key = node.slice
            if isinstance(key, ast.Constant) and isinstance(key.value, str) and key.value in forbidden:
                raise AssertionError(
                    f"{path} still reads canonical instruction field {key.value!r}")


def test_production_modules_do_not_contain_mojibake_markers():
    repo_root = Path(__file__).resolve().parent.parent
    bad_markers = ("\u00c3", "\u00e2\u20ac", "\u00e2\u2020")
    for path in list((repo_root / "m68k").glob("*.py")) + list((repo_root / "disasm").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in bad_markers):
            raise AssertionError(f"{path} contains mojibake markers")


def test_runtime_kb_generation_is_deterministic():
    script = Path(__file__).resolve().parent.parent / "scripts" / "build_runtime_kb.py"
    targets = [
        KNOWLEDGE / "runtime_m68k.py",
        KNOWLEDGE / "runtime_m68k_decode.py",
        KNOWLEDGE / "runtime_m68k_disasm.py",
        KNOWLEDGE / "runtime_m68k_asm.py",
        KNOWLEDGE / "runtime_m68k_analysis.py",
        KNOWLEDGE / "runtime_m68k_compute.py",
        KNOWLEDGE / "runtime_m68k_executor.py",
        KNOWLEDGE / "runtime_os.py",
        KNOWLEDGE / "runtime_hunk.py",
        KNOWLEDGE / "runtime_naming.py",
    ]
    before = {path: path.read_bytes() for path in targets}
    subprocess.run([sys.executable, str(script)], check=True)
    middle = {path: path.read_bytes() for path in targets}
    subprocess.run([sys.executable, str(script)], check=True)
    after = {path: path.read_bytes() for path in targets}
    assert before == middle == after


def test_runtime_size_encodings_match_canonical_structured_size_encoding():
    runtime = load_m68k_runtime_module().SIZE_ENCODINGS_ASM
    expected = {}
    for inst in load_canonical_m68k_kb()["instructions"]:
        if "size_encoding" in inst:
            mapping = {entry["size"]: entry["bits"] for entry in inst["size_encoding"]["values"]}
            expected[inst["mnemonic"]] = (
                mapping.get("b"),
                mapping.get("w"),
                mapping.get("l"),
            )
    assert runtime == expected


def test_runtime_special_case_tables_match_canonical_data():
    load_m68k_runtime_module.cache_clear()
    payload = load_m68k_runtime_module()
    canonical = load_canonical_m68k_kb()
    by_name = {inst["mnemonic"]: inst for inst in canonical["instructions"]}

    expected_structured = {}
    for key, kb_mnemonic in canonical["_meta"]["asm_syntax_index"].items():
        mnemonic, _, raw_operand_types = key.partition(":")
        operand_types = tuple(raw_operand_types.split(",")) if raw_operand_types else ()
        expected_structured[(mnemonic, operand_types)] = kb_mnemonic
    assert payload.ASM_SYNTAX_INDEX == expected_structured

    assert payload.ADDQ_ZERO_MEANS == by_name["ADDQ"]["constraints"]["immediate_range"]["zero_means"]

    expected_control = {}
    for entry in by_name["MOVEC"]["constraints"]["control_registers"]:
        expected_control.setdefault(int(entry["hex"], 16), entry["abbrev"])
    assert payload.CONTROL_REGISTERS == expected_control

    assert payload.META["_sp_reg_num"] == 7
    assert payload.META["_num_data_regs"] == 8
    assert payload.META["_num_addr_regs"] == 8
    assert payload.ASM_SYNTAX_INDEX[("move", ("ea", "sr"))] == "MOVE to SR"
    expected_families = tuple(
        (
            entry["prefix"],
            entry["canonical"],
            tuple(entry["codes"]),
            entry["match_numeric_suffix"],
            tuple(entry["exclude_from_family"]),
        )
        for entry in canonical["_meta"]["condition_families"]
    )
    assert tuple(payload.CONDITION_FAMILIES) == expected_families
    assert payload.BRANCH_INLINE_DISPLACEMENTS["BRA"] == (
        "8-BIT DISPLACEMENT",
        (7, 0, 8),
        0,
        255,
        2,
        4,
    )
    assert payload.BRANCH_EXTENSION_DISPLACEMENTS["DBcc"] == (2, 2)
    assert payload.BRANCH_EXTENSION_DISPLACEMENTS["PDBcc"] == (4, 2)
    assert payload.REGISTER_FIELDS["SWAP"] == ((2, 0, 3),)
    assert payload.REGISTER_FIELDS["EXG"] == ((11, 9, 3), (2, 0, 3))
    assert payload.OPMODE_TABLES_BY_VALUE["EXG"][17][5:] == ("dn", "an")
    assert payload.DIRECTION_VARIANTS["ASL, ASR"] == (
        (8, 8, 1),
        "as",
        ("asl", "asr"),
        {0: "r", 1: "l"},
    )
    assert payload.MOVEM_FIELDS == {
        "dr": (10, 10, 1),
        "size": (6, 6, 1),
        "mode": (5, 3, 3),
        "register": (2, 0, 3),
    }
    assert payload.SP_EFFECTS["RTS"] == (
        (payload.SpEffectAction.INCREMENT, 4, None),
    )
    assert payload.COMPUTE_FORMULAS["ADD"] == (
        payload.ComputeOp.ADD,
        (payload.FormulaTerm.SOURCE, payload.FormulaTerm.DESTINATION),
        None,
        None,
        (),
        None,
    )
    assert payload.COMPUTE_FORMULAS["SWAP"] == (
        payload.ComputeOp.EXCHANGE,
        (),
        (31, 16),
        (15, 0),
        (),
        None,
    )
    assert payload.COMPUTE_FORMULAS["DIVS, DIVSL"][5] == payload.TruncationMode.TOWARD_ZERO
    assert payload.SHIFT_VARIANT_BEHAVIORS["ASL, ASR"] == (
        ("ASL", payload.ShiftDirection.LEFT, payload.ShiftFill.ZERO, True),
        ("ASR", payload.ShiftDirection.RIGHT, payload.ShiftFill.SIGN, True),
    )
    assert payload.PROCESSOR_020_VARIANTS["DIVS, DIVSL"] == frozenset({"DIVSL"})
    assert payload.IMPLICIT_OPERANDS["CLR"] == 0
    assert payload.BIT_MODULI["BTST"] == (32, 8)
    assert payload.ROTATE_EXTRA_BITS["ROXL, ROXR"] == 1
    assert payload.SIGNED_RESULTS["MULS"] is True
    assert payload.INSTRUCTION_SIZES["MOVEQ"] == ("l",)
    assert payload.OPERATION_TYPES["MOVEQ"] == payload.OperationType.MOVE
    assert payload.OPERATION_CLASSES["LEA"] == payload.OperationClass.LOAD_EFFECTIVE_ADDRESS
    assert payload.PRIMARY_DATA_SIZES["MULS"] == (
        payload.PrimaryDataSizeKind.MULTIPLY,
        16,
        16,
        32,
    )
    assert "MOVEA" in payload.SOURCE_SIGN_EXTEND
    assert payload.SHIFT_COUNT_MODULI["ASL, ASR"] == 64
    assert payload.PROCESSOR_MINS["move"] == payload.Processor.M68000
    assert payload.FLOW_TYPES["BRA"] == payload.FlowType.BRANCH
    assert not hasattr(payload, "RUNTIME")


def test_runtime_hunk_relocation_semantics_are_typed():
    payload = load_hunk_runtime_kb()
    assert payload.RELOCATION_SEMANTICS["HUNK_RELOC32"] == (4, payload.RelocMode.ABSOLUTE)
    assert payload.RELOCATION_SEMANTICS["HUNK_RELOC16"] == (2, payload.RelocMode.PC_RELATIVE)


def test_runtime_decode_module_exposes_direct_decode_constants():
    payload = load_m68k_decode_runtime_module()
    canonical = load_canonical_m68k_kb()
    assert payload.OPWORD_BYTES == canonical["_meta"]["opword_bytes"]
    assert payload.ALIGN_MASK == canonical["_meta"]["opword_bytes"] - 1
    assert payload.DEFAULT_OPERAND_SIZE == canonical["_meta"]["default_operand_size"]
    assert payload.SIZE_BYTE_COUNT == canonical["_meta"]["size_byte_count"]
    assert payload.EA_MODE_ENCODING == canonical["_meta"]["ea_mode_encoding"]
    assert "ind" in payload.REG_INDIRECT_MODES
    assert "dn" not in payload.REG_INDIRECT_MODES
    assert "postinc" not in payload.REG_INDIRECT_MODES
    assert payload.MOVEM_REG_MASKS == canonical["_meta"]["movem_reg_masks"]
    assert payload.SP_REG_NUM == 7
    assert payload.ENCODING_COUNTS["MOVE16"] == 5
    assert payload.EA_FULL_FIELDS["I/IS"] == (2, 0, 3)
    assert payload.EA_BRIEF_FIELDS["REGISTER"] == (14, 12, 3)
    assert payload.EA_FIELD_SPECS["LEA"] == ((5, 3, 3), (2, 0, 3))
    assert payload.MOVEM_FIELDS["dr"] == (10, 10, 1)
    assert payload.IMMEDIATE_RANGES["MOVEQ"] == ("DATA", 8, True, -128, 127, None)


def test_runtime_disasm_module_exposes_direct_disasm_constants():
    payload = load_m68k_disasm_runtime_module()
    canonical = load_canonical_m68k_kb()
    assert payload.MOVEM_REG_MASKS == canonical["_meta"]["movem_reg_masks"]
    assert payload.CONDITION_CODES == tuple(canonical["_meta"]["condition_codes"])
    assert payload.CPU_HIERARCHY == canonical["_meta"]["cpu_hierarchy"]
    assert payload.PMMU_CONDITION_CODES == tuple(canonical["_meta"]["pmmu_condition_codes"])
    assert payload.DEFAULT_OPERAND_SIZE == canonical["_meta"]["default_operand_size"]
    assert payload.FORM_OPERAND_TYPES["BFINS"][0][0] == "dn"
    assert payload.CPID_FIELD == (9, 3)


def test_runtime_asm_module_exposes_direct_asm_constants():
    payload = load_m68k_asm_runtime_module()
    canonical = load_canonical_m68k_kb()
    assert payload.EA_MODE_ENCODING == canonical["_meta"]["ea_mode_encoding"]
    assert payload.SIZE_BYTE_COUNT == canonical["_meta"]["size_byte_count"]
    assert payload.CONDITION_CODES == tuple(canonical["_meta"]["condition_codes"])
    assert payload.ENCODING_COUNTS["MOVE"] == 1
    assert payload.CC_ALIASES == canonical["_meta"]["cc_aliases"]
    assert payload.MOVEM_REG_MASKS == canonical["_meta"]["movem_reg_masks"]
    assert payload.IMMEDIATE_ROUTING == canonical["_meta"]["immediate_routing"]
    assert payload.SIZE_ENCODINGS_ASM["MOVE"] == (1, 3, 2)
    assert payload.BRANCH_INLINE_DISPLACEMENTS["BRA"] == (
        "8-BIT DISPLACEMENT",
        (7, 0, 8),
        0,
        255,
        2,
        4,
    )
    assert payload.SPECIAL_OPERAND_TYPES == ("ccr", "sr", "usp")


def test_runtime_analysis_module_exposes_direct_analysis_constants():
    payload = load_m68k_analysis_runtime_module()
    canonical = load_canonical_m68k_kb()
    assert not hasattr(payload, "BY_NAME")
    assert payload.OPWORD_BYTES == canonical["_meta"]["opword_bytes"]
    assert payload.DEFAULT_OPERAND_SIZE == canonical["_meta"]["default_operand_size"]
    assert payload.SIZE_BYTE_COUNT == canonical["_meta"]["size_byte_count"]
    assert payload.EA_MODE_ENCODING == canonical["_meta"]["ea_mode_encoding"]
    assert payload.EA_MODE_SIZES == canonical["_meta"]["ea_mode_sizes"]
    assert payload.CC_TEST_DEFINITIONS == {
        name: (entry["encoding"], entry["test"])
        for name, entry in canonical["_meta"]["cc_test_definitions"].items()
    }
    assert payload.CC_ALIASES == canonical["_meta"]["cc_aliases"]
    assert payload.MOVEM_REG_MASKS == canonical["_meta"]["movem_reg_masks"]
    assert payload.REGISTER_ALIASES == canonical["_meta"]["register_aliases"]
    assert payload.SP_REG_NUM == 7
    assert payload.RTS_SP_INC == 4
    assert payload.ADDR_SIZE == "l"
    assert payload.ADDR_MASK == 0xFFFFFFFF
    assert payload.CCR_FLAG_NAMES == tuple(canonical["_meta"]["ccr_bit_positions"])
    assert payload.LOOKUP_UPPER["PFLUSHA"] == "PFLUSH PFLUSHA"
    assert payload.LOOKUP_CANONICAL["PFLUSHA"] == "PFLUSH PFLUSHA"
    assert payload.LOOKUP_CANONICAL["PBBS"] == "PBcc"
    assert payload.LOOKUP_NUMERIC_CC_PREFIXES["PB"] == "PBcc"
    assert payload.LOOKUP_CC_FAMILIES["pb"][0] == "PBcc"
    assert payload.LOOKUP_ASM_MNEMONIC_INDEX["illegal"] == "ILLEGAL"
    assert payload.EA_REVERSE[(7, 4)] == "imm"
    assert payload.OPERATION_TYPES["MOVE"] == payload.OperationType.MOVE
    assert payload.OPERATION_CLASSES["LEA"] == payload.OperationClass.LOAD_EFFECTIVE_ADDRESS
    assert "MOVEA" in payload.SOURCE_SIGN_EXTEND


def test_runtime_compute_module_exposes_direct_compute_constants():
    payload = load_m68k_compute_runtime_module()
    assert payload.OPERATION_TYPES["MOVE"] == payload.OperationType.MOVE
    assert payload.COMPUTE_FORMULAS["ADD"] == (
        payload.ComputeOp.ADD,
        (payload.FormulaTerm.SOURCE, payload.FormulaTerm.DESTINATION),
        None,
        None,
        (),
        None,
    )
    assert payload.IMPLICIT_OPERANDS["CLR"] == 0
    assert payload.SP_EFFECTS["RTS"] == (
        (payload.SpEffectAction.INCREMENT, 4, None),
    )
    assert payload.PRIMARY_DATA_SIZES["MULS"] == (
        payload.PrimaryDataSizeKind.MULTIPLY,
        16,
        16,
        32,
    )


def test_runtime_executor_module_exposes_direct_executor_constants():
    payload = load_m68k_executor_runtime_module()
    assert payload.REGISTER_FIELDS["SWAP"] == ((2, 0, 3),)
    assert payload.OPMODE_TABLES_BY_VALUE["EXG"][17][5:] == ("dn", "an")
    assert payload.SHIFT_FIELDS == ((8, 8, 1), ("r", "l"), 8)
    assert payload.MOVEM_FIELDS == {
        "dr": (10, 10, 1),
        "size": (6, 6, 1),
        "mode": (5, 3, 3),
        "register": (2, 0, 3),
    }
    assert payload.BRANCH_INLINE_DISPLACEMENTS["BRA"] == (
        "8-BIT DISPLACEMENT",
        (7, 0, 8),
        0,
        255,
        2,
        4,
    )
    assert payload.SHIFT_VARIANT_BEHAVIORS["ASL, ASR"] == (
        ("ASL", payload.ShiftDirection.LEFT, payload.ShiftFill.ZERO, True),
        ("ASR", payload.ShiftDirection.RIGHT, payload.ShiftFill.SIGN, True),
    )


def test_runtime_root_module_exposes_no_instruction_bag():
    payload = load_m68k_runtime_module()
    assert not hasattr(payload, "INSTRUCTIONS")
    assert not hasattr(payload, "BY_NAME")
    assert "MOVEQ" in payload.MNEMONIC_INDEX["moveq"]


def test_runtime_projection_keeps_only_minimal_constraint_fields():
    payload = load_m68k_runtime_module()
    assert payload.AN_SIZES["ADDQ"] == ("w", "l")
    assert payload.OPERAND_MODE_TABLES["ABCD"] == (
        "R/M",
        {0: ("dn", "dn"), 1: ("predec", "predec")},
    )
    assert payload.FORM_OPERAND_TYPES["MOVEQ"] == (("imm", "dn"),)
    assert payload.EA_MODE_TABLES["ADD"] == (
        ("dn", "an", "ind", "postinc", "predec", "disp", "index", "absw", "absl", "pcdisp", "pcindex", "imm"),
        ("ind", "postinc", "predec", "disp", "index", "absw", "absl"),
        (),
    )


def test_canonical_m68k_runtime_fields_are_structured():
    canonical = load_canonical_m68k_kb()
    assert canonical["_meta"]["condition_families"]
    for inst in canonical["instructions"]:
        if "size_encoding" in inst:
            assert inst["size_encoding"]["field"] == "SIZE"
            assert inst["size_encoding"]["values"]
    for mnemonic in ("DIVS, DIVSL", "DIVU, DIVUL", "MULS", "MULU"):
        inst = next(item for item in canonical["instructions"] if item["mnemonic"] == mnemonic)
        assert {
            entry["size"]: entry["bits"]
            for entry in inst["size_encoding"]["values"]
        } == {"w": 0, "l": 1}


def test_runtime_builder_requires_structured_size_encoding(monkeypatch):
    broken = copy.deepcopy(load_canonical_m68k_kb())
    target = next(inst for inst in broken["instructions"] if "size_encoding" in inst)
    del target["size_encoding"]

    def fake_load_json(name: str):
        if name == "m68k_instructions.json":
            return broken
        raise AssertionError(f"unexpected load for {name}")

    monkeypatch.setattr(build_runtime_kb, "_load_json", fake_load_json)
    with pytest.raises(KeyError, match="size_encoding"):
        build_runtime_kb._build_m68k_runtime()


def test_runtime_builder_requires_condition_families(monkeypatch):
    broken = copy.deepcopy(load_canonical_m68k_kb())
    del broken["_meta"]["condition_families"]

    def fake_load_json(name: str):
        if name == "m68k_instructions.json":
            return broken
        raise AssertionError(f"unexpected load for {name}")

    monkeypatch.setattr(build_runtime_kb, "_load_json", fake_load_json)
    with pytest.raises(KeyError, match="condition_families"):
        build_runtime_kb._build_m68k_runtime()


def _runtime_module_attrs():
    real = load_m68k_runtime_module()
    return {
        name: copy.deepcopy(getattr(real, name))
        for name in dir(real)
        if name.isupper()
    }


def test_runtime_loader_does_not_fallback_to_canonical_m68k(monkeypatch):
    load_m68k_runtime_module.cache_clear()
    monkeypatch.setattr(
        "tests.runtime_kb_helpers.load_canonical_m68k_kb",
        lambda: pytest.fail("canonical KB should not be loaded by runtime loader"),
    )
    try:
        payload = load_m68k_runtime_module()
        assert payload.MNEMONIC_INDEX
        assert payload.META["condition_codes"]
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_mnemonic_index(monkeypatch):
    load_m68k_runtime_module.cache_clear()

    class FakeModule:
        META = {}

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="MNEMONIC_INDEX"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_meta(monkeypatch):
    load_m68k_runtime_module.cache_clear()

    class FakeModule:
        MNEMONIC_INDEX = {}

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="META"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_control_register_table(monkeypatch):
    load_m68k_runtime_module.cache_clear()
    attrs = _runtime_module_attrs()
    del attrs["CONTROL_REGISTERS"]
    load_m68k_runtime_module.cache_clear()
    FakeModule = type("FakeModule", (), attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="CONTROL_REGISTERS"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_register_fields_table(monkeypatch):
    load_m68k_runtime_module.cache_clear()
    attrs = _runtime_module_attrs()
    del attrs["REGISTER_FIELDS"]
    load_m68k_runtime_module.cache_clear()
    FakeModule = type("FakeModule", (), attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="REGISTER_FIELDS"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_branch_displacement_table(monkeypatch):
    load_m68k_runtime_module.cache_clear()
    attrs = _runtime_module_attrs()
    del attrs["BRANCH_INLINE_DISPLACEMENTS"]
    load_m68k_runtime_module.cache_clear()
    FakeModule = type("FakeModule", (), attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="BRANCH_INLINE_DISPLACEMENTS"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_movem_fields_table(monkeypatch):
    load_m68k_runtime_module.cache_clear()
    attrs = _runtime_module_attrs()
    del attrs["MOVEM_FIELDS"]
    load_m68k_runtime_module.cache_clear()
    FakeModule = type("FakeModule", (), attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="MOVEM_FIELDS"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_decode_opword_bytes(monkeypatch):
    load_m68k_decode_runtime_module.cache_clear()

    class FakeModule:
        ALIGN_MASK = 1
        DEFAULT_OPERAND_SIZE = "w"
        SIZE_BYTE_COUNT = {}
        EA_MODE_ENCODING = {}
        REG_INDIRECT_MODES = frozenset()
        MOVEM_REG_MASKS = {}
        SP_REG_NUM = 7
        EA_BRIEF_FIELDS = {}
        EA_FULL_FIELDS = {}
        EA_FULL_BD_SIZE = {}
        ENCODING_MASKS = ()
        FIELD_MAPS = ()
        RAW_FIELDS = ()
        ENCODING_COUNTS = {}
        EA_FIELD_SPECS = {}
        FORM_OPERAND_TYPES = {}
        OPMODE_TABLES_BY_VALUE = {}
        OPERAND_MODE_TABLES = {}
        EA_MODE_TABLES = {}
        IMMEDIATE_RANGES = {}
        REGISTER_FIELDS = {}
        DEST_REG_FIELD = {}
        DIRECTION_VARIANTS = {}
        SHIFT_FIELDS = {}
        RM_FIELD = {}
        CONTROL_REGISTERS = {}
        MOVE_FIELDS = ()
        MOVEM_FIELDS = {}
        CPID_FIELD = ()

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="OPWORD_BYTES"):
            load_m68k_decode_runtime_module()
    finally:
        load_m68k_decode_runtime_module.cache_clear()


def test_runtime_loader_requires_disasm_condition_codes(monkeypatch):
    load_m68k_disasm_runtime_module.cache_clear()

    class FakeModule:
        MNEMONIC_INDEX = {}
        ENCODING_COUNTS = {}
        ENCODING_MASKS = ()
        FIXED_OPCODES = {}
        EXT_FIELD_NAMES = {}
        FIELD_MAPS = ()
        RAW_FIELDS = ()
        FORM_OPERAND_TYPES = {}
        EA_BRIEF_FIELDS = {}
        MOVEM_REG_MASKS = {}
        DEST_REG_FIELD = {}
        BF_MNEMONICS = ()
        BITOP_NAMES = ({}, (0, 0, 0))
        IMM_NAMES = ({}, (0, 0, 0))
        SHIFT_NAMES = {}
        SHIFT_TYPE_FIELDS = ()
        SHIFT_FIELDS = {}
        RM_FIELD = {}
        ADDQ_ZERO_MEANS = 8
        CONTROL_REGISTERS = {}
        SIZE_ENCODINGS_DISASM = {}
        PROCESSOR_MINS = {}
        OPMODE_TABLES_BY_VALUE = {}
        CONDITION_FAMILIES = ()
        CPU_HIERARCHY = {}
        PMMU_CONDITION_CODES = ()
        DEFAULT_OPERAND_SIZE = "w"
        MOVE_FIELDS = ()
        CPID_FIELD = ()

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="CONDITION_CODES"):
            load_m68k_disasm_runtime_module()
    finally:
        load_m68k_disasm_runtime_module.cache_clear()


def test_runtime_loader_requires_asm_immediate_routing(monkeypatch):
    load_m68k_asm_runtime_module.cache_clear()

    class FakeModule:
        ENCODING_COUNTS = {}
        ENCODING_MASKS = ()
        FIELD_MAPS = ()
        RAW_FIELDS = ()
        LOOKUP_UPPER = {}
        EA_MODE_ENCODING = {}
        EA_BRIEF_FIELDS = {}
        SIZE_BYTE_COUNT = {}
        CONDITION_CODES = ()
        CC_ALIASES = {}
        MOVEM_REG_MASKS = {}
        SIZE_ENCODINGS_ASM = {}
        OPMODE_TABLES_LIST = {}
        FORM_OPERAND_TYPES = {}
        FORM_FLAGS_020 = {}
        EA_MODE_TABLES = {}
        CC_FAMILIES = {}
        IMMEDIATE_RANGES = {}
        DIRECTION_VARIANTS = {}
        BRANCH_INLINE_DISPLACEMENTS = {}
        AN_SIZES = {}
        USES_LABELS = {}
        DIRECTION_FORM_VALUES = {}
        SPECIAL_OPERAND_TYPES = ()
        ASM_SYNTAX_INDEX = {}

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="IMMEDIATE_ROUTING"):
            load_m68k_asm_runtime_module()
    finally:
        load_m68k_asm_runtime_module.cache_clear()


def test_runtime_loader_requires_analysis_lookup_cc_families(monkeypatch):
    load_m68k_analysis_runtime_module.cache_clear()

    class FakeModule:
        OPWORD_BYTES = 2
        DEFAULT_OPERAND_SIZE = "w"
        SIZE_BYTE_COUNT = {}
        EA_MODE_ENCODING = {}
        EA_REVERSE = {}
        EA_BRIEF_FIELDS = {}
        EA_MODE_SIZES = {}
        MOVEM_REG_MASKS = {}
        CC_TEST_DEFINITIONS = {}
        CC_ALIASES = {}
        REGISTER_ALIASES = {}
        NUM_DATA_REGS = 8
        NUM_ADDR_REGS = 8
        SP_REG_NUM = 7
        RTS_SP_INC = 4
        ADDR_SIZE = "l"
        ADDR_MASK = 0xFFFFFFFF
        CCR_FLAG_NAMES = ()
        OPERATION_TYPES = {}
        OPERATION_CLASSES = {}
        SOURCE_SIGN_EXTEND = ()
        FLOW_TYPES = {}
        FLOW_CONDITIONAL = {}
        COMPUTE_FORMULAS = {}
        SP_EFFECTS = {}
        EA_MODE_TABLES = {}
        AN_SIZES = {}
        PROCESSOR_MINS = {}
        PROCESSOR_020_VARIANTS = {}
        LOOKUP_UPPER = {}
        LOOKUP_CANONICAL = {}
        LOOKUP_NUMERIC_CC_PREFIXES = {}
        LOOKUP_ASM_MNEMONIC_INDEX = {}

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="LOOKUP_CC_FAMILIES"):
            load_m68k_analysis_runtime_module()
    finally:
        load_m68k_analysis_runtime_module.cache_clear()


def test_runtime_loader_requires_compute_formulas(monkeypatch):
    load_m68k_compute_runtime_module.cache_clear()

    class FakeModule:
        OPERATION_TYPES = {}
        IMPLICIT_OPERANDS = {}
        SP_EFFECTS = {}
        PRIMARY_DATA_SIZES = {}

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="COMPUTE_FORMULAS"):
            load_m68k_compute_runtime_module()
    finally:
        load_m68k_compute_runtime_module.cache_clear()


def test_runtime_loader_requires_executor_branch_table(monkeypatch):
    load_m68k_executor_runtime_module.cache_clear()

    class FakeModule:
        FIELD_MAPS = ()
        RAW_FIELDS = ()
        OPERAND_MODE_TABLES = {}
        REGISTER_FIELDS = {}
        RM_FIELD = {}
        IMPLICIT_OPERANDS = {}
        OPMODE_TABLES_BY_VALUE = {}
        MOVEM_FIELDS = {}
        IMMEDIATE_RANGES = {}
        DEST_REG_FIELD = {}
        OPERATION_TYPES = {}
        OPERATION_CLASSES = {}
        SOURCE_SIGN_EXTEND = ()
        BIT_MODULI = {}
        SHIFT_COUNT_MODULI = {}
        ROTATE_EXTRA_BITS = {}
        DIRECTION_VARIANTS = {}
        SHIFT_FIELDS = ()
        SHIFT_VARIANT_BEHAVIORS = {}
        PRIMARY_DATA_SIZES = {}
        SIGNED_RESULTS = {}
        BRANCH_INLINE_DISPLACEMENTS = {}

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="BRANCH_EXTENSION_DISPLACEMENTS"):
            load_m68k_executor_runtime_module()
    finally:
        load_m68k_executor_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_direction_variants_table(monkeypatch):
    load_m68k_runtime_module.cache_clear()
    attrs = _runtime_module_attrs()
    del attrs["DIRECTION_VARIANTS"]
    load_m68k_runtime_module.cache_clear()
    FakeModule = type("FakeModule", (), attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="DIRECTION_VARIANTS"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_compute_formulas(monkeypatch):
    load_m68k_runtime_module.cache_clear()
    attrs = _runtime_module_attrs()
    del attrs["COMPUTE_FORMULAS"]
    load_m68k_runtime_module.cache_clear()
    FakeModule = type("FakeModule", (), attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="COMPUTE_FORMULAS"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_sp_effects(monkeypatch):
    load_m68k_runtime_module.cache_clear()
    attrs = _runtime_module_attrs()
    del attrs["SP_EFFECTS"]
    load_m68k_runtime_module.cache_clear()
    FakeModule = type("FakeModule", (), attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="SP_EFFECTS"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_assembler_requires_kb_size_encoding(monkeypatch):
    monkeypatch.setattr(m68k_asm.runtime_m68k_asm, "SIZE_ENCODINGS_ASM", {})
    with pytest.raises(KeyError, match="size encoding"):
        m68k_asm._get_size_encoding("MOVE", "w")


def test_assembler_requires_runtime_direction_variants(monkeypatch):
    monkeypatch.setattr(m68k_asm.runtime_m68k_asm, "DIRECTION_VARIANTS", {})
    assert m68k_asm._resolve_direction_mnemonic("asl") is None


def test_runtime_loader_requires_os_meta(monkeypatch):
    load_os_runtime_kb.cache_clear()

    class FakeModule:
        STRUCTS = {}
        CONSTANTS = {}
        LIBRARIES = {}

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="META"):
            load_os_runtime_kb()
    finally:
        load_os_runtime_kb.cache_clear()


def test_runtime_loader_requires_hunk_types(monkeypatch):
    load_hunk_runtime_kb.cache_clear()

    class FakeModule:
        META = {}
        EXT_TYPES = {}
        MEMORY_FLAGS = {}
        MEMORY_TYPE_CODES = {}
        EXT_TYPE_CATEGORIES = {}
        COMPATIBILITY_NOTES = []
        RELOC_FORMATS = {}
        RELOCATION_SEMANTICS = {}
        HUNK_CONTENT_FORMATS = {}

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="HUNK_TYPES"):
            load_hunk_runtime_kb()
    finally:
        load_hunk_runtime_kb.cache_clear()


def test_runtime_loader_requires_naming_patterns(monkeypatch):
    load_naming_runtime_kb.cache_clear()

    class FakeModule:
        META = {}
        TRIVIAL_FUNCTIONS = []
        GENERIC_PREFIX = "call_"

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: FakeModule)
    try:
        with pytest.raises(KeyError, match="PATTERNS"):
            load_naming_runtime_kb()
    finally:
        load_naming_runtime_kb.cache_clear()


def test_runtime_os_is_compact_subset_of_canonical_os_kb():
    runtime = load_os_runtime_kb()
    canonical = load_canonical_os_kb()
    assert runtime.META["calling_convention"] == canonical["_meta"]["calling_convention"]
    assert runtime.META["exec_base_addr"] == canonical["_meta"]["exec_base_addr"]
    assert runtime.META["constant_domains"] == canonical["_meta"]["constant_domains"]
    assert runtime.STRUCTS == canonical["structs"]
    assert runtime.CONSTANTS == canonical["constants"]
    assert not hasattr(runtime, "RUNTIME")
    for library, library_data in runtime.LIBRARIES.items():
        source_library = canonical["libraries"][library]
        assert library_data["lvo_index"] == source_library["lvo_index"]
        for func_name, func_data in library_data["functions"].items():
            source_func = source_library["functions"][func_name]
            for key, value in func_data.items():
                assert source_func[key] == value


def test_runtime_hunk_and_naming_match_canonical_payloads():
    hunk_runtime = load_hunk_runtime_kb()
    hunk_canonical = load_canonical_hunk_kb()
    assert hunk_runtime.META == hunk_canonical["_meta"]
    assert hunk_runtime.HUNK_TYPES == hunk_canonical["hunk_types"]
    assert hunk_runtime.EXT_TYPES == hunk_canonical["ext_types"]
    assert hunk_runtime.MEMORY_FLAGS == hunk_canonical["memory_flags"]
    assert hunk_runtime.MEMORY_TYPE_CODES == hunk_canonical["memory_type_codes"]
    assert hunk_runtime.EXT_TYPE_CATEGORIES == hunk_canonical["ext_type_categories"]
    assert hunk_runtime.COMPATIBILITY_NOTES == hunk_canonical["compatibility_notes"]
    assert hunk_runtime.RELOC_FORMATS == hunk_canonical["reloc_formats"]
    assert hunk_runtime.RELOCATION_SEMANTICS == {
        name: (entry["bytes"], getattr(hunk_runtime.RelocMode, entry["mode"].upper()))
        for name, entry in hunk_canonical["relocation_semantics"].items()
    }
    assert hunk_runtime.HUNK_CONTENT_FORMATS == hunk_canonical["hunk_content_formats"]
    assert not hasattr(hunk_runtime, "RUNTIME")

    naming_runtime = load_naming_runtime_kb()
    naming_canonical = load_canonical_naming_rules()
    assert naming_runtime.META == naming_canonical["_meta"]
    assert naming_runtime.PATTERNS == naming_canonical["patterns"]
    assert naming_runtime.TRIVIAL_FUNCTIONS == naming_canonical["trivial_functions"]
    assert naming_runtime.GENERIC_PREFIX == naming_canonical["generic_prefix"]
    assert not hasattr(naming_runtime, "RUNTIME")
