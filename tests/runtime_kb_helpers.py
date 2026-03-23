from __future__ import annotations

import importlib
import json
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any, Sequence, TypeVar, cast

from kb.schemas import (
    HardwareSymbolsPayload,
    HunkFormatPayload,
    M68kInstructionsPayload,
    NamingRulesPayload,
    OsReferencePayload,
)


PROJ_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = PROJ_ROOT / "knowledge"
RUNTIME_PY = PROJ_ROOT / "m68k_kb"


JsonObject = dict[str, object]
T = TypeVar("T")


def _load_json(name: str) -> JsonObject:
    path = KNOWLEDGE / name
    with open(path, encoding="utf-8") as handle:
        return cast(JsonObject, json.load(handle))


@lru_cache(maxsize=1)
def load_canonical_m68k_kb() -> M68kInstructionsPayload:
    return cast(M68kInstructionsPayload, _load_json("m68k_instructions.json"))


@lru_cache(maxsize=1)
def load_canonical_os_kb() -> OsReferencePayload:
    return cast(OsReferencePayload, _load_json("amiga_os_reference.json"))


@lru_cache(maxsize=1)
def load_canonical_hunk_kb() -> HunkFormatPayload:
    return cast(HunkFormatPayload, _load_json("amiga_hunk_format.json"))


@lru_cache(maxsize=1)
def load_canonical_naming_rules() -> NamingRulesPayload:
    return cast(NamingRulesPayload, _load_json("naming_rules.json"))


@lru_cache(maxsize=1)
def load_canonical_hardware_symbols() -> HardwareSymbolsPayload:
    return cast(HardwareSymbolsPayload, _load_json("amiga_hw_symbols.json"))


def _load_runtime_module(module_name: str) -> ModuleType:
    return importlib.import_module(f"m68k_kb.{module_name}")


def _require_attr(module: object, name: str) -> object:
    if not hasattr(module, name):
        raise KeyError(f"runtime KB missing attribute {name!r}")
    return getattr(module, name)


def _require_dict_attr(module: object, name: str) -> dict[str, object]:
    value = _require_attr(module, name)
    if not isinstance(value, dict):
        raise KeyError(f"runtime KB missing dict attribute {name!r}")
    return cast(dict[str, object], value)


def _require_sequence_attr(module: object, name: str) -> Sequence[object]:
    value = _require_attr(module, name)
    if not isinstance(value, (list, tuple)):
        raise KeyError(f"runtime KB missing sequence attribute {name!r}")
    return cast(Sequence[object], value)


@lru_cache(maxsize=1)
def load_m68k_runtime_module() -> ModuleType:
    module = _load_runtime_module("runtime_m68k")
    meta = _require_dict_attr(module, "META")
    required_attrs = (
        "MNEMONIC_INDEX", "ENCODING_COUNTS", "ENCODING_MASKS", "FIXED_OPCODES", "EXT_FIELD_NAMES",
        "FIELD_MAPS", "RAW_FIELDS", "FORM_OPERAND_TYPES", "EA_BRIEF_FIELDS",
        "SIZE_ENCODINGS_ASM", "SIZE_ENCODINGS_DISASM", "CC_FAMILIES",
        "IMMEDIATE_RANGES", "COMPUTE_FORMULAS", "SP_EFFECTS",
        "IMPLICIT_OPERANDS", "BIT_MODULI", "ROTATE_EXTRA_BITS", "SIGNED_RESULTS",
        "INSTRUCTION_SIZES", "OPERATION_TYPES", "OPERATION_CLASSES",
        "SOURCE_SIGN_EXTEND", "BOUNDS_CHECKS", "SHIFT_COUNT_MODULI",
        "OPMODE_TABLES_LIST", "OPMODE_TABLES_BY_VALUE", "FORM_OPERAND_TYPES",
        "FORM_FLAGS_020", "PRIMARY_DATA_SIZES", "EA_MODE_TABLES", "AN_SIZES",
        "OPERAND_MODE_TABLES", "DIRECTION_VARIANTS", "REGISTER_FIELDS",
        "DEST_REG_FIELD", "RM_FIELD", "SHIFT_FIELDS", "CONTROL_REGISTERS",
        "CONDITION_FAMILIES", "FLOW_TYPES", "FLOW_CONDITIONAL",
        "BRANCH_INLINE_DISPLACEMENTS", "BRANCH_EXTENSION_DISPLACEMENTS",
        "MOVE_FIELDS", "MOVEM_FIELDS", "CPID_FIELD", "ASM_SYNTAX_INDEX",
        "SPECIAL_OPERAND_TYPES", "USES_LABELS", "DIRECTION_FORM_VALUES",
        "SHIFT_VARIANT_BEHAVIORS", "PROCESSOR_020_VARIANTS",
    )
    for name in required_attrs:
        _require_attr(module, name)
    _require_attr(module, "META")
    if not isinstance(meta, dict):
        raise KeyError("runtime KB missing dict attribute 'META'")
    return module


@lru_cache(maxsize=1)
def load_m68k_decode_runtime_module() -> ModuleType:
    module = _load_runtime_module("runtime_m68k_decode")
    for name in (
        "OPWORD_BYTES", "ALIGN_MASK", "DEFAULT_OPERAND_SIZE", "SIZE_BYTE_COUNT",
        "EA_MODE_ENCODING", "REG_INDIRECT_MODES", "MOVEM_REG_MASKS", "SP_REG_NUM",
        "EA_BRIEF_FIELDS", "EA_FULL_FIELDS", "EA_FULL_BD_SIZE", "ENCODING_MASKS", "FIELD_MAPS",
        "RAW_FIELDS", "ENCODING_COUNTS", "EA_FIELD_SPECS", "FORM_OPERAND_TYPES", "OPERATION_TYPES",
        "SOURCE_SIGN_EXTEND", "OPMODE_TABLES_BY_VALUE",
        "OPERAND_MODE_TABLES", "EA_MODE_TABLES", "IMMEDIATE_RANGES",
        "REGISTER_FIELDS", "DEST_REG_FIELD", "DIRECTION_VARIANTS", "SHIFT_FIELDS",
        "RM_FIELD", "CONTROL_REGISTERS", "MOVE_FIELDS", "MOVEM_FIELDS", "CPID_FIELD",
    ):
        _require_attr(module, name)
    return module


@lru_cache(maxsize=1)
def load_m68k_asm_runtime_module() -> ModuleType:
    module = _load_runtime_module("runtime_m68k_asm")
    for name in (
        "ENCODING_COUNTS", "ENCODING_MASKS", "FIELD_MAPS", "RAW_FIELDS", "LOOKUP_UPPER",
        "EA_MODE_ENCODING", "EA_BRIEF_FIELDS",
        "SIZE_BYTE_COUNT", "CONDITION_CODES", "CC_ALIASES", "MOVEM_REG_MASKS",
        "IMMEDIATE_ROUTING", "SIZE_ENCODINGS_ASM", "OPMODE_TABLES_LIST",
        "INSTRUCTION_SIZES", "OPERATION_TYPES", "SOURCE_SIGN_EXTEND",
        "FORM_OPERAND_TYPES", "FORM_FLAGS_020", "EA_MODE_TABLES", "CC_FAMILIES",
        "IMMEDIATE_RANGES", "DIRECTION_VARIANTS", "BRANCH_INLINE_DISPLACEMENTS",
        "AN_SIZES", "USES_LABELS", "DIRECTION_FORM_VALUES",
        "SPECIAL_OPERAND_TYPES", "ASM_SYNTAX_INDEX",
    ):
        _require_attr(module, name)
    return module


@lru_cache(maxsize=1)
def load_m68k_analysis_runtime_module() -> ModuleType:
    module = _load_runtime_module("runtime_m68k_analysis")
    for name in (
        "OPWORD_BYTES", "DEFAULT_OPERAND_SIZE", "SIZE_BYTE_COUNT",
        "EA_MODE_ENCODING", "EA_REVERSE", "EA_BRIEF_FIELDS", "EA_MODE_SIZES",
        "MOVEM_REG_MASKS", "CC_TEST_DEFINITIONS", "CC_ALIASES", "REGISTER_ALIASES",
        "NUM_DATA_REGS", "NUM_ADDR_REGS", "SP_REG_NUM", "RTS_SP_INC", "ADDR_SIZE",
        "ADDR_MASK", "CCR_FLAG_NAMES", "FLOW_TYPES", "FLOW_CONDITIONAL",
        "OPERATION_TYPES", "OPERATION_CLASSES", "SOURCE_SIGN_EXTEND",
        "COMPUTE_FORMULAS", "SP_EFFECTS", "EA_MODE_TABLES", "AN_SIZES",
        "PROCESSOR_MINS", "PROCESSOR_020_VARIANTS", "LOOKUP_UPPER",
        "LOOKUP_CANONICAL", "LOOKUP_NUMERIC_CC_PREFIXES",
        "LOOKUP_CC_FAMILIES", "LOOKUP_ASM_MNEMONIC_INDEX",
    ):
        _require_attr(module, name)
    return module


@lru_cache(maxsize=1)
def load_m68k_compute_runtime_module() -> ModuleType:
    module = _load_runtime_module("runtime_m68k_compute")
    for name in (
        "OPERATION_TYPES", "COMPUTE_FORMULAS", "IMPLICIT_OPERANDS",
        "SP_EFFECTS", "PRIMARY_DATA_SIZES",
    ):
        _require_attr(module, name)
    return module


@lru_cache(maxsize=1)
def load_m68k_executor_runtime_module() -> ModuleType:
    module = _load_runtime_module("runtime_m68k_executor")
    for name in (
        "FIELD_MAPS", "RAW_FIELDS", "OPERAND_MODE_TABLES", "REGISTER_FIELDS",
        "RM_FIELD", "IMPLICIT_OPERANDS", "OPMODE_TABLES_BY_VALUE",
        "MOVEM_FIELDS", "IMMEDIATE_RANGES", "DEST_REG_FIELD",
        "OPERATION_TYPES", "OPERATION_CLASSES", "SOURCE_SIGN_EXTEND",
        "BOUNDS_CHECKS", "BIT_MODULI", "SHIFT_COUNT_MODULI", "ROTATE_EXTRA_BITS",
        "DIRECTION_VARIANTS", "SHIFT_FIELDS", "SHIFT_VARIANT_BEHAVIORS",
        "PRIMARY_DATA_SIZES", "SIGNED_RESULTS",
        "BRANCH_INLINE_DISPLACEMENTS", "BRANCH_EXTENSION_DISPLACEMENTS",
    ):
        _require_attr(module, name)
    return module


@lru_cache(maxsize=1)
def load_os_runtime_kb() -> ModuleType:
    module = _load_runtime_module("runtime_os")
    for name in ("META", "STRUCTS", "CONSTANTS", "LIBRARIES"):
        _require_attr(module, name)
    return module


@lru_cache(maxsize=1)
def load_hunk_runtime_kb() -> ModuleType:
    module = _load_runtime_module("runtime_hunk")
    for name in (
        "META", "HUNK_TYPES", "EXT_TYPES", "MEMORY_FLAGS", "MEMORY_TYPE_CODES",
        "EXT_TYPE_CATEGORIES", "COMPATIBILITY_NOTES", "RELOC_FORMATS",
        "RELOCATION_SEMANTICS", "HUNK_CONTENT_FORMATS",
    ):
        _require_attr(module, name)
    return module


@lru_cache(maxsize=1)
def load_naming_runtime_kb() -> ModuleType:
    module = _load_runtime_module("runtime_naming")
    for name in ("META", "PATTERNS", "TRIVIAL_FUNCTIONS", "GENERIC_PREFIX"):
        _require_attr(module, name)
    return module


@lru_cache(maxsize=1)
def load_hardware_runtime_kb() -> ModuleType:
    module = _load_runtime_module("runtime_hardware")
    for name in ("META", "REGISTER_DEFS"):
        _require_attr(module, name)
    return module
