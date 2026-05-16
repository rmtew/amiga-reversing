from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[2]
KB_PATH = ROOT / "knowledge" / "m68k_instructions.json"
SRC_DIR = ROOT / "src"
GENERATED_DIR = SRC_DIR / "generated"
SUBSET_MANIFEST_PATH = ROOT / "src" / "scripts" / "m68k_assembler_subset.json"

OPERAND_KIND_ENUM = {
    "absl": "M68K_ASM_OPERAND_ABSL",
    "an": "M68K_ASM_OPERAND_AN",
    "bf_ea": "M68K_ASM_OPERAND_BF_EA",
    "cache_sel": "M68K_ASM_OPERAND_CACHE_SEL",
    "ccr": "M68K_ASM_OPERAND_CCR",
    "ctrl_reg": "M68K_ASM_OPERAND_CTRL_REG",
    "dn": "M68K_ASM_OPERAND_DN",
    "dn_pair": "M68K_ASM_OPERAND_DN_PAIR",
    "ea": "M68K_ASM_OPERAND_EA",
    "imm": "M68K_ASM_OPERAND_IMM",
    "ind": "M68K_ASM_OPERAND_IND",
    "label": "M68K_ASM_OPERAND_LABEL",
    "postinc": "M68K_ASM_OPERAND_POSTINC",
    "predec": "M68K_ASM_OPERAND_PREDEC",
    "reglist": "M68K_ASM_OPERAND_REGLIST",
    "rn": "M68K_ASM_OPERAND_RN",
    "rn_pair": "M68K_ASM_OPERAND_RN_PAIR",
    "sr": "M68K_ASM_OPERAND_SR",
    "usp": "M68K_ASM_OPERAND_USP",
}

FIELD_KIND_ENUM = {
    "8-BIT DISPLACEMENT": "M68K_ASM_FIELD_DISPLACEMENT_8",
    "16-BIT DISPLACEMENT": "M68K_ASM_FIELD_DISPLACEMENT_16",
    "BITFIELD_OFFSET_DA": "M68K_ASM_FIELD_BITFIELD_OFFSET_DA",
    "BITFIELD_WIDTH_DA": "M68K_ASM_FIELD_BITFIELD_WIDTH_DA",
    "CACHE": "M68K_ASM_FIELD_CACHE",
    "D/A": "M68K_ASM_FIELD_DA",
    "DATA": "M68K_ASM_FIELD_DATA",
    "ID": "M68K_ASM_FIELD_ID",
    "MODE": "M68K_ASM_FIELD_MODE",
    "OPMODE": "M68K_ASM_FIELD_OPMODE",
    "OFFSET": "M68K_ASM_FIELD_OFFSET",
    "REGISTER LIST MASK": "M68K_ASM_FIELD_REGLIST_MASK",
    "REGISTER": "M68K_ASM_FIELD_REGISTER",
    "SIZE": "M68K_ASM_FIELD_SIZE",
    "VECTOR": "M68K_ASM_FIELD_DATA",
    "WIDTH": "M68K_ASM_FIELD_WIDTH",
}

VALUE_SOURCE_ENUM = {
    "bf_offset": "M68K_ASM_VALUE_BF_OFFSET",
    "bf_offset_kind": "M68K_ASM_VALUE_BF_OFFSET_KIND",
    "bf_width": "M68K_ASM_VALUE_BF_WIDTH",
    "bf_width_kind": "M68K_ASM_VALUE_BF_WIDTH_KIND",
    "none": "M68K_ASM_VALUE_NONE",
    "opmode": "M68K_ASM_VALUE_OPMODE",
    "reg": "M68K_ASM_VALUE_REG",
    "reg_first": "M68K_ASM_VALUE_REG_FIRST",
    "reg_second": "M68K_ASM_VALUE_REG_SECOND",
    "ea_reg": "M68K_ASM_VALUE_EA_REG",
    "ea_mode": "M68K_ASM_VALUE_EA_MODE",
    "reg_kind": "M68K_ASM_VALUE_REG_KIND",
    "reg_kind_first": "M68K_ASM_VALUE_REG_KIND_FIRST",
    "reg_kind_second": "M68K_ASM_VALUE_REG_KIND_SECOND",
    "value_hi16": "M68K_ASM_VALUE_VALUE_HI16",
    "value_lo16": "M68K_ASM_VALUE_VALUE_LO16",
    "value": "M68K_ASM_VALUE_VALUE",
}

SUPPORTED_OPERAND_KINDS = frozenset({
    "dn",
    "dn_pair",
    "bf_ea",
    "cache_sel",
    "ind",
    "an",
    "rn",
    "rn_pair",
    "ea",
    "absl",
    "imm",
    "label",
    "predec",
    "postinc",
    "disp",
    "reglist",
    "ccr",
    "ctrl_reg",
    "sr",
    "usp",
})

CPU_MIN_ENUM = {
    "68000": "M68K_ASM_CPU_68000",
    "68010": "M68K_ASM_CPU_68010",
    "68020": "M68K_ASM_CPU_68020",
    "68030": "M68K_ASM_CPU_68030",
    "68040": "M68K_ASM_CPU_68040",
    "68060": "M68K_ASM_CPU_68060",
}

CPU_ORDER = tuple(CPU_MIN_ENUM.keys())
EA_MODE_BITS = {
    "dn": tuple((0, reg) for reg in range(8)),
    "an": tuple((1, reg) for reg in range(8)),
    "ind": tuple((2, reg) for reg in range(8)),
    "postinc": tuple((3, reg) for reg in range(8)),
    "predec": tuple((4, reg) for reg in range(8)),
    "disp": tuple((5, reg) for reg in range(8)),
    "index": tuple((6, reg) for reg in range(8)),
    "absw": ((7, 0),),
    "absl": ((7, 1),),
    "pcdisp": ((7, 2),),
    "pcindex": ((7, 3),),
    "imm": ((7, 4),),
}


def _cpu_mask_value(cpu_names: tuple[str, ...] | list[str]) -> int:
    mask = 0
    for cpu_name in cpu_names:
        mask |= 1 << CPU_ORDER.index(cpu_name)
    return mask


def _filter_cpu_set_min(cpu_names: tuple[str, ...] | list[str], minimum_cpu: str) -> tuple[str, ...]:
    minimum_index = CPU_ORDER.index(minimum_cpu)
    return tuple(cpu_name for cpu_name in cpu_names if CPU_ORDER.index(cpu_name) >= minimum_index)


def _cpu_names_for_entry(entry: dict[str, object]) -> tuple[str, ...]:
    processor_set = entry.get("processor_set")
    if isinstance(processor_set, list) and processor_set:
        return tuple(str(cpu_name) for cpu_name in processor_set)
    minimum_cpu = str(entry.get("processor_min", "68000"))
    minimum_index = CPU_ORDER.index(minimum_cpu)
    return tuple(CPU_ORDER[minimum_index:])


def _cpu_names_for_form(entry: dict[str, object], form_source: dict[str, object]) -> tuple[str, ...]:
    processor_set = form_source.get("processor_set")
    if isinstance(processor_set, list) and processor_set:
        return tuple(str(cpu_name) for cpu_name in processor_set)
    base_cpu_names = _cpu_names_for_entry(entry)
    minimum_cpu = form_source.get("processor_min")
    if isinstance(minimum_cpu, str) and minimum_cpu in CPU_ORDER:
        return _filter_cpu_set_min(base_cpu_names, minimum_cpu)
    return base_cpu_names

SIZE_BIT = {"b": 1 << 0, "w": 1 << 1, "l": 1 << 2}
UNSET_FIELD_VALUE = 0xFF
MAX_BOUND_WORDS = 2
STYLE_LINE_LENGTH = 140
SINGLE_CLAUSE_BODY_RE = re.compile(r"^\s*(?:return\b.*|break;|continue;)\s*$")


@dataclass(frozen=True, slots=True)
class PatchDef:
    field_kind: str
    word_index: int
    occurrence: int
    bit_hi: int
    bit_lo: int
    operand_index: int
    value_source: str


@dataclass(frozen=True, slots=True)
class FormDef:
    mnemonic: str
    kb_mnemonic: str
    local_form_index: int
    form_index: int
    syntax: str
    sampling_operand_kinds: tuple[str, ...]
    operand_kinds: tuple[str, ...]
    size_mask: int
    size_mask_68000: int
    ea_dn_size_mask: int
    ea_memory_size_mask: int
    ea_mode_masks: tuple[int, int, int, int]
    cpu_mask: int
    control_register_ids: tuple[int, ...]
    opword_base: int
    opword_mask: int
    bound_word_count: int
    bound_word_bases: tuple[int, int]
    bound_word_masks: tuple[int, int]
    patches: tuple[PatchDef, ...]
    size_values: tuple[int, int, int]
    opmode_values: tuple[int, int, int]
    branch_word_signal: int
    branch_word_bytes: int
    branch_long_signal: int
    branch_long_bytes: int
    has_bound_word_extension: bool


@dataclass(frozen=True, slots=True)
class ExtensionDef:
    kind: str
    operand_index: int
    patch_index: int


EA_TEXT_FAMILY_ENUM = {
    "reg_direct": "M68K_ASM_EA_TEXT_REG_DIRECT",
    "immediate": "M68K_ASM_EA_TEXT_IMMEDIATE",
    "an_indirect": "M68K_ASM_EA_TEXT_AN_INDIRECT",
    "an_postinc": "M68K_ASM_EA_TEXT_AN_POSTINC",
    "an_predec": "M68K_ASM_EA_TEXT_AN_PREDEC",
    "an_disp": "M68K_ASM_EA_TEXT_AN_DISP",
    "an_index": "M68K_ASM_EA_TEXT_AN_INDEX",
    "pc_disp": "M68K_ASM_EA_TEXT_PC_DISP",
    "pc_index": "M68K_ASM_EA_TEXT_PC_INDEX",
    "absolute": "M68K_ASM_EA_TEXT_ABSOLUTE",
}

EA_TEXT_VALUE_KIND_ENUM = {
    "none": "M68K_ASM_EA_VALUE_NONE",
    "numeric": "M68K_ASM_EA_VALUE_NUMERIC",
    "numeric_or_label": "M68K_ASM_EA_VALUE_NUMERIC_OR_LABEL",
}


def _load_supported_mnemonics(manifest_path: Path = SUBSET_MANIFEST_PATH) -> tuple[str, ...]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    mnemonics: list[str] = []
    for group_name, group_entries in data.items():
        assert isinstance(group_name, str)
        assert isinstance(group_entries, list)
        for mnemonic in group_entries:
            assert isinstance(mnemonic, str)
            mnemonics.append(mnemonic)
    return tuple(mnemonics)


SUPPORTED_MNEMONICS = _load_supported_mnemonics()
MAX_FORM_OPERANDS = 4


def _load_kb(kb_path: Path) -> dict[str, object]:
    data = json.loads(kb_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _kb_meta(kb: dict[str, object], key: str) -> object:
    meta = kb.get("_meta", {})
    assert isinstance(meta, dict)
    return meta[key]


def _load_immediate_routing(kb: dict[str, object]) -> dict[str, str]:
    routing = _kb_meta(kb, "immediate_routing")
    assert isinstance(routing, dict)
    return {str(mnemonic): str(routed) for mnemonic, routed in routing.items()}


def _supported_immediate_routes(
    forms: list[FormDef],
    kb_path: Path = KB_PATH,
    kb: dict[str, object] | None = None,
) -> dict[str, str]:
    routed_targets = {form.mnemonic for form in forms}
    kb_data = kb if kb is not None else _load_kb(kb_path)
    return {
        mnemonic: routed
        for mnemonic, routed in _load_immediate_routing(kb_data).items()
        if mnemonic in SUPPORTED_MNEMONICS and routed in routed_targets
    }


def _supports_direct_immediate_source(
    mnemonic: str,
    forms: list[FormDef],
    kb_path: Path = KB_PATH,
    kb: dict[str, object] | None = None,
) -> bool:
    routed = _load_immediate_routing(kb if kb is not None else _load_kb(kb_path)).get(mnemonic)
    return routed is None


def _load_ea_text_forms(kb: dict[str, object]) -> list[dict[str, object]]:
    forms = _kb_meta(kb, "ea_text_forms")
    assert isinstance(forms, list)
    return [dict(entry) for entry in forms]


def _load_condition_family_map(kb: dict[str, object]) -> dict[str, dict[str, object]]:
    families = _kb_meta(kb, "condition_families")
    assert isinstance(families, list)
    result: dict[str, dict[str, object]] = {}
    for entry in families:
        assert isinstance(entry, dict)
        result[str(entry.get("canonical", ""))] = dict(entry)
    return result


def _load_cc_test_definitions(kb: dict[str, object]) -> dict[str, dict[str, object]]:
    defs = _kb_meta(kb, "cc_test_definitions")
    assert isinstance(defs, dict)
    return {str(key): dict(value) for key, value in defs.items() if isinstance(value, dict)}


def _asm_mnemonic_from_syntax(syntax: str) -> str:
    token = syntax.split()[0]
    if "." in token:
        token = token.split(".", 1)[0]
    return token.upper()


def _expand_direction_variant_syntax(syntax: str, base: str, variant: str) -> str:
    token, *rest = syntax.split(" ", 1)
    if token.lower().startswith(base.lower()) and token.endswith("d"):
        token = variant.upper() + token[len(base) + 1:]
    return " ".join((token, *rest)).strip()


def _normalize_field_name(name: str) -> str:
    if name == "REGISTER LIST MASK":
        return name
    if name == "Do":
        return "BITFIELD_OFFSET_DA"
    if name == "Dw":
        return "BITFIELD_WIDTH_DA"
    if name.startswith("REGISTER"):
        return "REGISTER"
    if re.fullmatch(r"(?:D[cu]|Rn)\d*", name):
        return "REGISTER"
    if name in {"DATA REGISTER", "ADDRESS REGISTER"}:
        return "REGISTER"
    if re.fullmatch(r"D/A\d*", name):
        return "D/A"
    if name == "A/D":
        return "D/A"
    if name == "A-REGISTER":
        return "REGISTER"
    if name == "BIT NUMBER":
        return "DATA"
    if name in {
        "VECTOR",
        "ARGUMENT COUNT",
        "IMMEDIATE DATA",
        "CONTROL REGISTER",
        "HIGH-ORDER ADDRESS",
        "LOW-ORDER ADDRESS",
        "FC",
        "FC-MODE",
        "MASK",
        "LEVEL",
        "P-REGISTER",
    }:
        return "DATA"
    return name


def _normalize_runtime_operand_kind(kind: str) -> str:
    if kind in {"disp", "predec"}:
        return "ea"
    return kind


def _ea_mode_mask(mode_names: object) -> int:
    if not isinstance(mode_names, list):
        return 0
    mask = 0
    for mode_name in mode_names:
        for mode, reg in EA_MODE_BITS.get(str(mode_name), ()):
            mask |= 1 << (mode * 8 + reg)
    return mask


def _merged_ea_mode_masks_by_role(item: dict[str, object]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for table_name in ("ea_modes", "ea_modes_020"):
        table = item.get(table_name)
        if not isinstance(table, dict):
            continue
        for role, mode_names in table.items():
            merged[str(role)] = merged.get(str(role), 0) | _ea_mode_mask(mode_names)
    return merged


def _form_ea_mode_masks(item: dict[str, object], form_source: dict[str, object]) -> tuple[int, int, int, int]:
    masks = [0, 0, 0, 0]
    role_masks = _merged_ea_mode_masks_by_role(item)
    if not role_masks:
        return tuple(masks)
    operand_types = [str(operand["type"]) for operand in form_source["operands"]]
    ea_indexes = [
        index
        for index, operand_type in enumerate(operand_types[:4])
        if _normalize_runtime_operand_kind(operand_type) in {"ea", "bf_ea"}
    ]
    if not ea_indexes:
        return tuple(masks)
    if "ea" in role_masks:
        for index in ea_indexes:
            masks[index] = role_masks["ea"]
        return tuple(masks)
    if len(ea_indexes) == 2 and {"src", "dst"}.issubset(role_masks):
        masks[ea_indexes[0]] = role_masks["src"]
        masks[ea_indexes[1]] = role_masks["dst"]
        return tuple(masks)
    if len(ea_indexes) == 1:
        index = ea_indexes[0]
        if len(role_masks) == 1:
            masks[index] = next(iter(role_masks.values()))
        elif index == 0 and "src" in role_masks:
            masks[index] = role_masks["src"]
        elif index == len(operand_types) - 1 and "dst" in role_masks:
            masks[index] = role_masks["dst"]
    return tuple(masks)


def _default_field_binding(
    form_source: dict[str, object], raw_name: str, name: str, occurrence: int, word_index: int
) -> tuple[int, str]:
    operand_types = [str(operand["type"]) for operand in form_source["operands"]]
    bf_ea_index = next((index for index, operand_type in enumerate(operand_types) if operand_type == "bf_ea"), -1)
    if name == "MODE" and bf_ea_index >= 0:
        return bf_ea_index, "ea_mode"
    if name == "REGISTER":
        if word_index == 0 and bf_ea_index >= 0:
            return bf_ea_index, "ea_reg"
        if occurrence < len(operand_types):
            operand_type = operand_types[occurrence]
            if operand_type in {"dn", "an", "rn"}:
                return occurrence, "reg"
        rn_operand_indexes = [index for index, operand_type in enumerate(operand_types) if operand_type == "rn"]
        if len(rn_operand_indexes) == 1:
            return rn_operand_indexes[0], "reg"
        dn_operand_indexes = [index for index, operand_type in enumerate(operand_types) if operand_type == "dn"]
        if len(dn_operand_indexes) == 1:
            return dn_operand_indexes[0], "reg"
    if name == "D/A" and occurrence < len(operand_types) and operand_types[occurrence] == "rn":
        return occurrence, "reg_kind"
    if name == "CACHE":
        if occurrence < len(operand_types) and operand_types[occurrence] == "cache_sel":
            return occurrence, "value"
        cache_indexes = [index for index, operand_type in enumerate(operand_types) if operand_type == "cache_sel"]
        if len(cache_indexes) == 1:
            return cache_indexes[0], "value"
    if bf_ea_index >= 0:
        if name == "BITFIELD_OFFSET_DA":
            return bf_ea_index, "bf_offset_kind"
        if name == "BITFIELD_WIDTH_DA":
            return bf_ea_index, "bf_width_kind"
        if name == "OFFSET":
            return bf_ea_index, "bf_offset"
        if name == "WIDTH":
            return bf_ea_index, "bf_width"
    return -1, "none"


def _build_encoding_variants(
    *,
    mnemonic: str,
    item: dict[str, object],
    forms_source: list[dict[str, object]],
    encoding_groups: list[list[dict[str, object]]],
    size_mask: int,
    size_mask_68000: int,
) -> list[tuple[list[dict[str, object]], tuple[list[dict[str, object]], ...], int, int, bool, tuple[int, ...] | None]]:
    variants: list[tuple[list[dict[str, object]], tuple[list[dict[str, object]], ...], int, int, bool, tuple[int, ...] | None]] = []
    has_form_group_indexes = any(form.get("encoding_group_index") is not None for form in forms_source)
    has_generic_bound_extension = (
        len(encoding_groups) == 2
        and all(len(group) == 1 for group in encoding_groups)
        and not has_form_group_indexes
    )
    if len(encoding_groups) == 1:
        group = encoding_groups[0]
        group_fields = cast(list[dict[str, object]], group[0]["fields"])
        bound_word_groups = tuple(
            cast(list[dict[str, object]], ext_group["fields"])
            for ext_group in group[1:]
            if _is_bound_extension_encoding(cast(list[dict[str, object]], ext_group.get("fields", [])))
        )
        has_bound_word_extension = any(
            len(ext_fields) == 1
            and str(ext_fields[0].get("name")) == "16-BIT DISPLACEMENT"
            and int(ext_fields[0].get("width", 0)) == 16
            for ext_fields in bound_word_groups
        )
        return [(group_fields, bound_word_groups, size_mask, size_mask_68000, has_bound_word_extension, None)]
    if has_generic_bound_extension:
        group_fields = cast(list[dict[str, object]], encoding_groups[0][0]["fields"])
        ext_fields = cast(list[dict[str, object]], encoding_groups[1][0]["fields"])
        return [(group_fields, (ext_fields,), size_mask, size_mask_68000, False, None)]
    if has_form_group_indexes:
        for group_index, group in enumerate(encoding_groups):
            group_fields = cast(list[dict[str, object]], group[0]["fields"])
            bound_word_groups = tuple(
                cast(list[dict[str, object]], ext_group["fields"])
                for ext_group in group[1:]
            )
            variants.append((
                group_fields,
                bound_word_groups,
                size_mask,
                size_mask_68000,
                any(_is_bound_extension_encoding(ext_fields) for ext_fields in bound_word_groups),
                tuple(
                    form_index
                    for form_index, form_source in enumerate(forms_source)
                    if int(form_source.get("encoding_group_index", -1)) == group_index
                ),
            ))
        return variants
    if len(encoding_groups) == len(forms_source) and all(len(group) >= 1 for group in encoding_groups):
        for form_index, group in enumerate(encoding_groups):
            group_fields = cast(list[dict[str, object]], group[0]["fields"])
            bound_word_groups = tuple(
                cast(list[dict[str, object]], ext_group["fields"])
                for ext_group in group[1:]
            )
            variants.append((
                group_fields,
                bound_word_groups,
                size_mask,
                size_mask_68000,
                any(_is_bound_extension_encoding(ext_fields) for ext_fields in bound_word_groups),
                (form_index,),
            ))
        return variants
    size_variants = tuple(str(size) for size in item.get("sizes", ()))
    sizes_68000 = frozenset(str(size) for size in item.get("constraints", {}).get("sizes_68000", item.get("sizes", ())))
    assert size_variants and len(size_variants) == len(encoding_groups), f"{mnemonic} expected size-aligned encoding groups"
    for size_name, group in zip(size_variants, encoding_groups, strict=True):
        group_fields = cast(list[dict[str, object]], group[0]["fields"])
        bit = SIZE_BIT[size_name]
        variants.append((group_fields, (), bit, bit if size_name in sizes_68000 else 0, False, None))
    return variants


def _is_extension_only_encoding(fields: list[dict[str, object]]) -> bool:
    non_constant_fields = [field for field in fields if str(field.get("name", "")) not in {"0", "1"}]
    return (
        sum(int(field.get("width", 0)) for field in fields) == 16
        and len(non_constant_fields) == 1
        and str(non_constant_fields[0].get("name", "")) not in {"MODE", "REGISTER", "MODE REGISTER"}
    )


def _is_bound_extension_encoding(fields: list[dict[str, object]]) -> bool:
    non_constant_fields = [field for field in fields if str(field.get("name", "")) not in {"0", "1"}]
    if sum(int(field.get("width", 0)) for field in fields) != 16 or not non_constant_fields:
        return False
    if len(non_constant_fields) != 1:
        return True
    raw_name = str(non_constant_fields[0].get("name", ""))
    return _normalize_field_name(raw_name) not in {"DATA"}


def _control_register_id_key(entry: dict[str, object]) -> tuple[str, int, int]:
    return (
        str(entry.get("abbrev", "")).lower(),
        int(str(entry["hex"]), 16),
        _cpu_mask_value(_cpu_names_for_entry(entry)),
    )


def _allowed_control_register_ids_for_form(
    item: dict[str, object],
    form_source: dict[str, object],
    control_register_ids_by_name: dict[str, list[int]],
    control_register_id_by_key: dict[tuple[str, int, int], int],
) -> tuple[int, ...]:
    names = [str(name).lower() for name in form_source.get("control_registers", [])]
    constraints = item.get("constraints", {})
    assert isinstance(constraints, dict)
    instruction_registers = constraints.get("control_registers", [])
    assert isinstance(instruction_registers, list)
    if not names:
        operand_kinds = [str(operand.get("type", "")) for operand in form_source.get("operands", [])]
        if "ctrl_reg" not in operand_kinds or not instruction_registers:
            return ()
        names = [
            str(entry.get("abbrev", "")).lower()
            for entry in instruction_registers
            if isinstance(entry, dict)
        ]
    result: list[int] = []
    seen: set[int] = set()
    for name in names:
        matched = [
            control_register_id_by_key[_control_register_id_key(entry)]
            for entry in instruction_registers
            if isinstance(entry, dict) and str(entry.get("abbrev", "")).lower() == name
        ]
        if not matched:
            matched = control_register_ids_by_name[name]
        for control_register_id in matched:
            if control_register_id in seen:
                continue
            seen.add(control_register_id)
            result.append(control_register_id)
    return tuple(result)


def _load_forms(kb_path: Path, supported_mnemonics: tuple[str, ...] | None = None) -> list[FormDef]:
    data = _load_kb(kb_path)
    instructions = data["instructions"]
    meta = data["_meta"]
    control_registers = _load_control_registers(data)
    control_register_ids: dict[str, list[int]] = {}
    for entry in control_registers:
        control_register_ids.setdefault(str(entry["abbrev"]), []).append(int(entry["id"]))
    control_register_id_by_key = {
        (str(entry["abbrev"]), int(entry["value"]), int(entry["cpu_mask"])): int(entry["id"])
        for entry in control_registers
    }
    condition_families = _load_condition_family_map(data)
    cc_test_definitions = _load_cc_test_definitions(data)
    encoding_templates = meta.get("encoding_templates", {})
    field_binding_templates = meta.get("field_binding_templates", {})
    form_templates = meta.get("form_templates", {})
    forms: list[FormDef] = []
    mnemonics = supported_mnemonics if supported_mnemonics is not None else SUPPORTED_MNEMONICS
    for mnemonic in mnemonics:
        item = next(entry for entry in instructions if entry["mnemonic"] == mnemonic)
        encodings = item.get("encodings")
        if encodings is None and "encoding_template" in item:
            encodings = encoding_templates[item["encoding_template"]]
        bindings_source = item.get("field_bindings")
        if bindings_source is None and "field_binding_template" in item:
            bindings_source = field_binding_templates[item["field_binding_template"]]
        forms_source = item.get("forms")
        if forms_source is None and "form_template" in item:
            forms_source = []
            for syntax, form_body in zip(
                item.get("form_syntaxes", []),
                form_templates[item["form_template"]],
                strict=True,
            ):
                form_with_syntax = dict(form_body)
                form_with_syntax["syntax"] = syntax
                forms_source.append(form_with_syntax)
        raw_field_bindings = [
            {
                "form_index": int(binding.get("form_index", 0)),
                "field": str(binding["field"]),
                "occurrence": int(binding["occurrence"]),
                "operand_index": int(binding["operand_index"]),
                "value_source": str(binding["value_source"]),
            }
            for binding in bindings_source or []
        ]
        assert encodings, f"{mnemonic} missing encodings"
        encoding_groups: list[list[dict[str, object]]] = []
        if any("encoding_group_span" in form_source for form_source in forms_source):
            encoding_offset = 0
            grouped_indexes: set[int] = set()
            for form_source in forms_source:
                group_index = int(form_source.get("encoding_group_index", len(grouped_indexes)))
                if group_index in grouped_indexes:
                    continue
                grouped_indexes.add(group_index)
                span = int(form_source.get("encoding_group_span", 1))
                encoding_group = [dict(encoding) for encoding in encodings[encoding_offset:encoding_offset + span]]
                assert encoding_group, f"{mnemonic} empty encoding group span"
                encoding_groups.append(encoding_group)
                encoding_offset += span
            assert encoding_offset == len(encodings), f"{mnemonic} encoding_group_span does not cover encodings"
        else:
            for encoding in encodings:
                fields = cast(list[dict[str, object]], encoding.get("fields", []))
                if not encoding_groups or not _is_extension_only_encoding(fields):
                    encoding_groups.append([dict(encoding)])
                else:
                    encoding_groups[-1].append(dict(encoding))
        assert encoding_groups, f"{mnemonic} missing encoding groups"
        size_mask = 0
        for size in item.get("sizes", []):
            size_mask |= SIZE_BIT[size]
        size_mask_68000 = 0
        for size in item.get("constraints", {}).get("sizes_68000", item.get("sizes", [])):
            size_mask_68000 |= SIZE_BIT[size]
        size_values_map = {entry["size"]: int(entry["bits"]) for entry in item.get("size_encoding", {}).get("values", [])}
        displacement_encoding = item.get("constraints", {}).get("displacement_encoding", {})
        direction_field_values = item.get("direction_field_values", {})
        direction_field_name = str(direction_field_values.get("field", ""))
        direction_form_values_raw = direction_field_values.get("form_field_value", {})
        assert isinstance(direction_form_values_raw, dict)
        direction_form_values = {int(form_idx): int(value) for form_idx, value in direction_form_values_raw.items()}
        field_form_values_raw = item.get("field_form_values", [])
        assert isinstance(field_form_values_raw, list)
        field_form_values: dict[tuple[int, str, int], int] = {}
        for entry in field_form_values_raw:
            assert isinstance(entry, dict)
            field_name = str(entry.get("field", ""))
            occurrence = int(entry.get("occurrence", 0))
            form_values_raw = entry.get("form_field_value", {})
            assert isinstance(form_values_raw, dict)
            for raw_form_index, raw_value in form_values_raw.items():
                field_form_values[(int(raw_form_index), field_name, occurrence)] = int(raw_value)
        assert forms_source, f"{mnemonic} missing forms"
        cc_parameterized = item.get("constraints", {}).get("cc_parameterized", {})
        assert isinstance(cc_parameterized, dict)
        direction_variants = item.get("constraints", {}).get("direction_variants", {})
        assert isinstance(direction_variants, dict)
        expanded_forms_source: list[dict[str, object]] = []
        expanded_form_values: dict[tuple[int, str], int] = {}
        expanded_field_bindings: list[dict[str, object]] = []
        if cc_parameterized:
            excluded = {str(code).lower() for code in cc_parameterized.get("excluded", []) if isinstance(code, str)}
            family = condition_families.get(mnemonic.lower())
            assert family is not None, f"{mnemonic} missing condition family"
            codes = [
                str(code).lower()
                for code in family.get("codes", [])
                if isinstance(code, str) and str(code).lower() not in excluded
            ]
            for base_form_index, form_source in enumerate(forms_source):
                for condition_code in codes:
                    condition_def = cc_test_definitions.get(condition_code)
                    assert condition_def is not None, f"{mnemonic} missing CC definition for {condition_code}"
                    expanded_form_index = len(expanded_forms_source)
                    syntax = str(form_source["syntax"]).replace("cc", condition_code.upper())
                    expanded_form = dict(form_source)
                    expanded_form["syntax"] = syntax
                    expanded_forms_source.append(expanded_form)
                    expanded_form_values[(expanded_form_index, "CONDITION", 0)] = int(condition_def["encoding"])
                    for binding in raw_field_bindings:
                        if int(binding["form_index"]) == base_form_index:
                            expanded_field_bindings.append(
                                {
                                    **binding,
                                    "form_index": expanded_form_index,
                                }
                            )
                    for (raw_form_index, field_name, occurrence), value in field_form_values.items():
                        if raw_form_index == base_form_index:
                            expanded_form_values[(expanded_form_index, field_name, occurrence)] = value
            forms_source = expanded_forms_source
            field_form_values = expanded_form_values
            raw_field_bindings = expanded_field_bindings
        elif direction_variants:
            values = direction_variants.get("values", {})
            assert isinstance(values, dict)
            inverse_values = {str(label).lower(): int(bits) for bits, label in values.items()}
            base = str(direction_variants.get("base", ""))
            variants = item.get("variants", [])
            assert isinstance(variants, list)
            for base_form_index, form_source in enumerate(forms_source):
                for variant in variants:
                    assert isinstance(variant, dict)
                    variant_mnemonic = str(variant.get("mnemonic", ""))
                    direction = str(variant.get("direction", "")).lower()
                    if direction not in {"left", "right"}:
                        continue
                    expanded_form_index = len(expanded_forms_source)
                    expanded_form = dict(form_source)
                    expanded_form["syntax"] = _expand_direction_variant_syntax(
                        str(form_source["syntax"]),
                        base,
                        variant_mnemonic,
                    )
                    expanded_forms_source.append(expanded_form)
                    expanded_form_values[(expanded_form_index, str(direction_variants["field"]), 0)] = (
                        inverse_values["l" if direction == "left" else "r"]
                    )
                    for binding in raw_field_bindings:
                        if int(binding["form_index"]) == base_form_index:
                            expanded_field_bindings.append(
                                {
                                    **binding,
                                    "form_index": expanded_form_index,
                                }
                            )
                    for (raw_form_index, field_name, occurrence), value in field_form_values.items():
                        if raw_form_index == base_form_index:
                            expanded_form_values[(expanded_form_index, field_name, occurrence)] = value
            forms_source = expanded_forms_source
            field_form_values = expanded_form_values
            raw_field_bindings = expanded_field_bindings
        field_bindings_all = {
            (int(binding["form_index"]), str(binding["field"]), int(binding["occurrence"])): (
                int(binding["operand_index"]),
                str(binding["value_source"]),
            )
            for binding in raw_field_bindings
        }
        opmode_entries = item.get("constraints", {}).get("opmode_table", [])
        encoding_variants = _build_encoding_variants(
            mnemonic=mnemonic,
            item=item,
            forms_source=forms_source,
            encoding_groups=encoding_groups,
            size_mask=size_mask,
            size_mask_68000=size_mask_68000,
        )
        for encoding_variant_index, (
            encoding_fields,
            bound_word_field_groups,
            variant_size_mask,
            variant_size_mask_68000,
            has_bound_word_extension,
            restricted_form_indices,
        ) in enumerate(encoding_variants):
            for form_index, form_source in enumerate(forms_source):
                if restricted_form_indices is not None and form_index not in restricted_form_indices:
                    continue
                if restricted_form_indices is None:
                    encoding_group_index = form_source.get("encoding_group_index")
                    if encoding_group_index is not None and len(encoding_variants) > 1 and encoding_variant_index != int(encoding_group_index):
                        continue
                sampling_operand_kinds = tuple(str(operand["type"]) for operand in form_source["operands"])
                if any(kind not in SUPPORTED_OPERAND_KINDS for kind in sampling_operand_kinds):
                    continue
                operand_kinds = tuple(_normalize_runtime_operand_kind(kind) for kind in sampling_operand_kinds)
                allowed_control_register_ids = _allowed_control_register_ids_for_form(
                    item,
                    form_source,
                    control_register_ids,
                    control_register_id_by_key,
                )
                if opmode_entries and operand_kinds not in {("ea", "dn"), ("ea", "an"), ("dn", "ea")}:
                    matching_opmodes = [
                        int(entry["opmode"])
                        for entry in opmode_entries
                        if tuple(
                            str(entry.get(role, ""))
                            for role in ("rx_mode", "ry_mode")
                        ) == operand_kinds
                    ]
                    if len(matching_opmodes) == 1 and (form_index, "OPMODE", 0) not in field_form_values:
                        field_form_values[(form_index, "OPMODE", 0)] = matching_opmodes[0]
                opword_base = 0
                opword_mask = 0
                bound_word_count = len(bound_word_field_groups)
                assert bound_word_count <= MAX_BOUND_WORDS, f"{mnemonic} exceeds MAX_BOUND_WORDS"
                bound_word_bases = [0] * MAX_BOUND_WORDS
                bound_word_masks = [0] * MAX_BOUND_WORDS
                occurrences: dict[str, int] = {}
                raw_occurrences: dict[str, int] = {}
                patches: list[PatchDef] = []
                for field in encoding_fields:
                    raw_name = str(field["name"])
                    name = _normalize_field_name(raw_name)
                    bit_hi = int(field["bit_hi"])
                    bit_lo = int(field["bit_lo"])
                    width = int(field["width"])
                    if raw_name in {"0", "1"}:
                        opword_mask |= ((1 << width) - 1) << bit_lo
                        if raw_name == "1":
                            opword_base |= ((1 << width) - 1) << bit_lo
                        continue
                    raw_occurrence = raw_occurrences.get(raw_name, 0)
                    occurrence = occurrences.get(name, 0)
                    if name in FIELD_KIND_ENUM:
                        raw_occurrences[raw_name] = raw_occurrence + 1
                        occurrences[name] = occurrence + 1
                    if raw_name == direction_field_name and form_index in direction_form_values:
                        opword_mask |= ((1 << width) - 1) << bit_lo
                        opword_base |= (direction_form_values[form_index] & ((1 << width) - 1)) << bit_lo
                        continue
                    if (form_index, raw_name, raw_occurrence) in field_form_values:
                        opword_mask |= ((1 << width) - 1) << bit_lo
                        opword_base |= (field_form_values[(form_index, raw_name, raw_occurrence)] & ((1 << width) - 1)) << bit_lo
                        continue
                    if (form_index, name, occurrence) in field_form_values:
                        opword_mask |= ((1 << width) - 1) << bit_lo
                        opword_base |= (field_form_values[(form_index, name, occurrence)] & ((1 << width) - 1)) << bit_lo
                        continue
                    if name not in FIELD_KIND_ENUM:
                        continue
                    binding_operand_index, binding_value_source = field_bindings_all.get((form_index, raw_name, raw_occurrence), (-1, "none"))
                    if binding_operand_index < 0:
                        binding_operand_index, binding_value_source = field_bindings_all.get((form_index, name, occurrence), (-1, "none"))
                    if binding_operand_index < 0:
                        binding_operand_index, binding_value_source = _default_field_binding(
                            form_source, raw_name, name, occurrence, 0
                        )
                    patches.append(
                        PatchDef(
                            field_kind=name,
                            word_index=0,
                            occurrence=occurrence,
                            bit_hi=bit_hi,
                            bit_lo=bit_lo,
                            operand_index=binding_operand_index,
                            value_source=binding_value_source,
                        )
                    )
                for bound_word_index, extension_fields in enumerate(bound_word_field_groups, start=1):
                    for field in extension_fields:
                        raw_name = str(field["name"])
                        name = _normalize_field_name(raw_name)
                        bit_hi = int(field["bit_hi"])
                        bit_lo = int(field["bit_lo"])
                        width = int(field["width"])
                        if raw_name in {"0", "1"}:
                            bound_word_masks[bound_word_index - 1] |= ((1 << width) - 1) << bit_lo
                            if raw_name == "1":
                                bound_word_bases[bound_word_index - 1] |= ((1 << width) - 1) << bit_lo
                            continue
                        raw_occurrence = raw_occurrences.get(raw_name, 0)
                        occurrence = occurrences.get(name, 0)
                        if name in FIELD_KIND_ENUM:
                            raw_occurrences[raw_name] = raw_occurrence + 1
                            occurrences[name] = occurrence + 1
                        if raw_name == direction_field_name and form_index in direction_form_values:
                            bound_word_masks[bound_word_index - 1] |= ((1 << width) - 1) << bit_lo
                            bound_word_bases[bound_word_index - 1] |= (direction_form_values[form_index] & ((1 << width) - 1)) << bit_lo
                            continue
                        if (form_index, raw_name, raw_occurrence) in field_form_values:
                            bound_word_masks[bound_word_index - 1] |= ((1 << width) - 1) << bit_lo
                            bound_word_bases[bound_word_index - 1] |= (field_form_values[(form_index, raw_name, raw_occurrence)] & ((1 << width) - 1)) << bit_lo
                            continue
                        if (form_index, name, occurrence) in field_form_values:
                            bound_word_masks[bound_word_index - 1] |= ((1 << width) - 1) << bit_lo
                            bound_word_bases[bound_word_index - 1] |= (field_form_values[(form_index, name, occurrence)] & ((1 << width) - 1)) << bit_lo
                            continue
                        if name not in FIELD_KIND_ENUM:
                            continue
                        binding_operand_index, binding_value_source = field_bindings_all.get((form_index, raw_name, raw_occurrence), (-1, "none"))
                        if binding_operand_index < 0:
                            binding_operand_index, binding_value_source = field_bindings_all.get((form_index, name, occurrence), (-1, "none"))
                        if binding_operand_index < 0:
                            binding_operand_index, binding_value_source = _default_field_binding(
                                form_source, raw_name, name, occurrence, bound_word_index
                            )
                        patches.append(
                            PatchDef(
                                field_kind=name,
                                word_index=bound_word_index,
                                occurrence=occurrence,
                                bit_hi=bit_hi,
                                bit_lo=bit_lo,
                                operand_index=binding_operand_index,
                                value_source=binding_value_source,
                            )
                        )
                syntax_size_mask = 0
                syntax_head = str(form_source["syntax"]).split()[0].lower()
                if "." in syntax_head:
                    syntax_suffix = syntax_head.split(".", 1)[1]
                    if syntax_suffix in SIZE_BIT:
                        syntax_size_mask = SIZE_BIT[syntax_suffix]
                opmode_values_map = {"b": UNSET_FIELD_VALUE, "w": UNSET_FIELD_VALUE, "l": UNSET_FIELD_VALUE}
                if opmode_entries:
                    if operand_kinds in {("ea", "dn"), ("ea", "an")}:
                        ea_is_source = True
                    elif operand_kinds == ("dn", "ea"):
                        ea_is_source = False
                    else:
                        ea_is_source = None
                    if ea_is_source is not None:
                        for entry in opmode_entries:
                            if "ea_is_source" in entry:
                                if bool(entry.get("ea_is_source")) != ea_is_source:
                                    continue
                            else:
                                description = str(entry.get("description", "")).lower()
                                if ea_is_source and "memory to register" not in description:
                                    continue
                                if not ea_is_source and "register to memory" not in description:
                                    continue
                            size = str(entry.get("size"))
                            if size in opmode_values_map:
                                opmode_values_map[size] = int(entry["opmode"])
                form_size_mask = syntax_size_mask if syntax_size_mask else variant_size_mask
                form_size_mask_68000 = syntax_size_mask if syntax_size_mask else variant_size_mask_68000
                memory_size_only = str(item.get("constraints", {}).get("memory_size_only", ""))
                if memory_size_only in SIZE_BIT and operand_kinds == ("ea",):
                    form_size_mask = SIZE_BIT[memory_size_only]
                    form_size_mask_68000 = SIZE_BIT[memory_size_only]
                if (
                    not syntax_size_mask
                    and (form_index, "OPMODE", 0) in field_form_values
                    and any(
                        int(entry["opmode"]) == field_form_values[(form_index, "OPMODE", 0)]
                        and entry.get("size") is None
                        for entry in opmode_entries
                    )
                ):
                    form_size_mask = 0
                    form_size_mask_68000 = 0
                bit_op_sizes = item.get("constraints", {}).get("bit_op_sizes", {})
                assert isinstance(bit_op_sizes, dict)
                ea_dn_size_mask = 0
                ea_memory_size_mask = 0
                if bit_op_sizes and "ea" in operand_kinds:
                    dn_size = bit_op_sizes.get("dn")
                    memory_size = bit_op_sizes.get("memory")
                    if isinstance(dn_size, str) and dn_size in SIZE_BIT:
                        ea_dn_size_mask = SIZE_BIT[dn_size]
                    if isinstance(memory_size, str) and memory_size in SIZE_BIT:
                        ea_memory_size_mask = SIZE_BIT[memory_size]
                form_cpu_names = _cpu_names_for_form(item, form_source)
                if bool(form_source.get("processor_020")):
                    form_cpu_names = _filter_cpu_set_min(form_cpu_names, "68020")
                forms.append(
                    FormDef(
                        mnemonic=_asm_mnemonic_from_syntax(str(form_source["syntax"])),
                        kb_mnemonic=mnemonic,
                        local_form_index=form_index,
                        form_index=len(forms),
                        syntax=form_source["syntax"],
                        sampling_operand_kinds=sampling_operand_kinds,
                        operand_kinds=operand_kinds,
                        size_mask=form_size_mask,
                        size_mask_68000=form_size_mask_68000,
                        ea_dn_size_mask=ea_dn_size_mask,
                        ea_memory_size_mask=ea_memory_size_mask,
                        ea_mode_masks=_form_ea_mode_masks(item, form_source),
                        cpu_mask=_cpu_mask_value(form_cpu_names),
                        control_register_ids=allowed_control_register_ids,
                        opword_base=opword_base,
                        opword_mask=opword_mask,
                        bound_word_count=bound_word_count,
                        bound_word_bases=(bound_word_bases[0], bound_word_bases[1]),
                        bound_word_masks=(bound_word_masks[0], bound_word_masks[1]),
                        patches=tuple(patches),
                        size_values=(
                            size_values_map.get("b", UNSET_FIELD_VALUE),
                            size_values_map.get("w", UNSET_FIELD_VALUE),
                            size_values_map.get("l", UNSET_FIELD_VALUE),
                        ),
                        opmode_values=(
                            opmode_values_map["b"],
                            opmode_values_map["w"],
                            opmode_values_map["l"],
                        ),
                        branch_word_signal=int(displacement_encoding.get("word_signal", 0)),
                        branch_word_bytes=int(displacement_encoding.get("word_bits", 0)) // 8,
                        branch_long_signal=int(displacement_encoding.get("long_signal", 0)),
                        branch_long_bytes=int(displacement_encoding.get("long_bits", 0)) // 8,
                        has_bound_word_extension=has_bound_word_extension,
                    )
                )
    return forms


def _load_brief_ext_fields(kb: dict[str, object]) -> dict[str, tuple[int, int]]:
    fields = _kb_meta(kb, "ea_brief_ext_word")
    assert isinstance(fields, list)
    return {
        str(field["name"]): (int(field["bit_hi"]), int(field["bit_lo"]))
        for field in fields
    }


def _load_full_ext_fields(kb: dict[str, object]) -> dict[str, tuple[int, int]]:
    fields = _kb_meta(kb, "ea_full_ext_word")
    assert isinstance(fields, list)
    return {
        str(field["name"]): (int(field["bit_hi"]), int(field["bit_lo"]))
        for field in fields
    }


def _load_full_ext_bd_sizes(kb: dict[str, object]) -> dict[int, str]:
    values = _kb_meta(kb, "ea_full_ext_bd_size")
    assert isinstance(values, dict)
    return {int(key): str(value) for key, value in values.items()}


def _load_control_registers(kb: dict[str, object]) -> list[dict[str, object]]:
    instructions = kb["instructions"]
    assert isinstance(instructions, list)
    result: list[dict[str, object]] = []
    seen: set[tuple[str, int, int]] = set()
    for item in instructions:
        assert isinstance(item, dict)
        constraints = item.get("constraints", {})
        assert isinstance(constraints, dict)
        control_registers = constraints.get("control_registers", [])
        assert isinstance(control_registers, list)
        for entry in control_registers:
            assert isinstance(entry, dict)
            abbrev = str(entry.get("abbrev", "")).lower()
            if not abbrev:
                continue
            value = int(str(entry["hex"]), 16)
            cpu_mask = _cpu_mask_value(_cpu_names_for_entry(entry))
            key = (abbrev, value, cpu_mask)
            if key in seen:
                continue
            seen.add(key)
            result.append({"abbrev": abbrev, "value": value, "cpu_mask": cpu_mask})
    result.sort(key=lambda entry: (str(entry["abbrev"]), int(entry["value"]), int(entry["cpu_mask"])))
    for index, entry in enumerate(result):
        entry["id"] = index
    return result


def _extension_defs(form: FormDef) -> tuple[ExtensionDef, ...]:
    defs: list[ExtensionDef] = []
    for operand_index, operand_kind in enumerate(form.sampling_operand_kinds):
        if operand_kind in {"ea", "bf_ea"}:
            defs.append(ExtensionDef(kind="ea_single_word", operand_index=operand_index, patch_index=0))
            defs.append(ExtensionDef(kind="ea_long_address", operand_index=operand_index, patch_index=0))
            if operand_kind == "ea":
                defs.append(ExtensionDef(kind="ea_immediate", operand_index=operand_index, patch_index=0))
            defs.append(ExtensionDef(kind="ea_brief_index", operand_index=operand_index, patch_index=0))
        elif operand_kind == "disp":
            if not any(
                patch.operand_index == operand_index and patch.value_source == "value"
                for patch in form.patches
                if patch.word_index != 0
            ):
                defs.append(ExtensionDef(kind="disp16_always", operand_index=operand_index, patch_index=0))
        elif operand_kind == "absl":
            if not any(patch.operand_index == operand_index for patch in form.patches):
                defs.append(ExtensionDef(kind="ea_long_address", operand_index=operand_index, patch_index=0))
        elif operand_kind == "imm":
            if not any(patch.operand_index == operand_index for patch in form.patches):
                defs.append(ExtensionDef(kind="ea_immediate", operand_index=operand_index, patch_index=0))
        elif operand_kind == "label":
            for patch_index, patch in enumerate(form.patches):
                if patch.field_kind == "8-BIT DISPLACEMENT":
                    defs.append(
                        ExtensionDef(
                            kind="label_disp16_if_zero",
                            operand_index=operand_index,
                            patch_index=patch_index,
                        )
                    )
                    break
    return tuple(defs)


def _runtime_mnemonic_list(forms: list[FormDef], kb_path: Path = KB_PATH) -> list[str]:
    mnemonic_list = list(dict.fromkeys(form.mnemonic for form in forms))
    seen = set(mnemonic_list)
    kb = _load_kb(kb_path)
    instructions = kb.get("instructions", [])
    assert isinstance(instructions, list)
    for item in instructions:
        if not isinstance(item, dict) or "mnemonic" not in item:
            continue
        if item.get("forms") is None and item.get("form_template") is None:
            continue
        try:
            candidate_forms = _load_forms(kb_path, supported_mnemonics=(str(item["mnemonic"]),))
        except AssertionError:
            continue
        for form in candidate_forms:
            if form.mnemonic in seen:
                continue
            seen.add(form.mnemonic)
            mnemonic_list.append(form.mnemonic)
    return mnemonic_list


def _render_header(forms: list[FormDef], kb: dict[str, object], mnemonic_list: list[str] | None = None) -> str:
    if mnemonic_list is None:
        mnemonic_list = _runtime_mnemonic_list(forms)
    mnemonic_ids = "\n".join(
        f"    M68K_ASM_MNEMONIC_{mnemonic} = {index},"
        for index, mnemonic in enumerate(mnemonic_list, start=1)
    )
    control_registers = _load_control_registers(kb)
    control_register_name_counts: dict[str, int] = {}
    for entry in control_registers:
        abbrev = str(entry["abbrev"]).upper()
        control_register_name_counts[abbrev] = control_register_name_counts.get(abbrev, 0) + 1
    control_register_ids = "\n".join(
        f"    M68K_ASM_CONTROL_REGISTER_{str(entry['abbrev']).upper()}"
        f"{'_' + str(int(entry['id'])) if control_register_name_counts[str(entry['abbrev']).upper()] > 1 else ''} = "
        f"{int(entry['id'])},"
        for entry in control_registers
    )
    brief_fields = _load_brief_ext_fields(kb)
    full_fields = _load_full_ext_fields(kb)
    bd_sizes = _load_full_ext_bd_sizes(kb)
    ea_text_forms = _load_ea_text_forms(kb)
    ea_full_extension_cpu_min = CPU_MIN_ENUM[str(_kb_meta(kb, "ea_full_extension_cpu_min"))]
    ea_text_family_ids = "\n".join(
        f"    {enum_name} = {index},"
        for index, enum_name in enumerate(dict.fromkeys(EA_TEXT_FAMILY_ENUM[str(entry['syntax_family'])] for entry in ea_text_forms))
    )
    return f"""/* Auto-generated by src/scripts/generate_c99_assembler_subset.py. */
#ifndef M68K_ASM_TABLES_H
#define M68K_ASM_TABLES_H

typedef enum {{
    M68K_ASM_MNEMONIC_NONE = 0,
{mnemonic_ids}
    M68K_ASM_MNEMONIC_COUNT = {len(mnemonic_list) + 1}
}} M68kAsmMnemonicId;

typedef enum {{
    M68K_ASM_CONTROL_REGISTER_NONE = 255,
{control_register_ids}
}} M68kAsmControlRegisterId;

typedef enum {{
    M68K_ASM_CPU_68000 = 0,
    M68K_ASM_CPU_68010 = 1,
    M68K_ASM_CPU_68020 = 2,
    M68K_ASM_CPU_68030 = 3,
    M68K_ASM_CPU_68040 = 4,
    M68K_ASM_CPU_68060 = 5
}} M68kAsmCpuMin;

#define M68K_ASM_CPU_MASK_68000 (1u << M68K_ASM_CPU_68000)
#define M68K_ASM_CPU_MASK_68010 (1u << M68K_ASM_CPU_68010)
#define M68K_ASM_CPU_MASK_68020 (1u << M68K_ASM_CPU_68020)
#define M68K_ASM_CPU_MASK_68030 (1u << M68K_ASM_CPU_68030)
#define M68K_ASM_CPU_MASK_68040 (1u << M68K_ASM_CPU_68040)
#define M68K_ASM_CPU_MASK_68060 (1u << M68K_ASM_CPU_68060)

#define M68K_ASM_CPU_ANY 0xFF
#define M68K_ASM_EA_FULL_EXTENSION_CPU_MIN {ea_full_extension_cpu_min}

typedef enum {{
    M68K_ASM_OPERAND_NONE = 0,
    M68K_ASM_OPERAND_AN,
    M68K_ASM_OPERAND_ABSL,
    M68K_ASM_OPERAND_BF_EA,
    M68K_ASM_OPERAND_CACHE_SEL,
    M68K_ASM_OPERAND_CCR,
    M68K_ASM_OPERAND_CTRL_REG,
    M68K_ASM_OPERAND_DN,
    M68K_ASM_OPERAND_DN_PAIR,
    M68K_ASM_OPERAND_EA,
    M68K_ASM_OPERAND_IMM,
    M68K_ASM_OPERAND_IND,
    M68K_ASM_OPERAND_LABEL,
    M68K_ASM_OPERAND_POSTINC,
    M68K_ASM_OPERAND_PREDEC,
    M68K_ASM_OPERAND_REGLIST,
    M68K_ASM_OPERAND_RN,
    M68K_ASM_OPERAND_RN_PAIR,
    M68K_ASM_OPERAND_SR,
    M68K_ASM_OPERAND_USP
}} M68kAsmOperandKind;

typedef enum {{
    M68K_ASM_FIELD_REGISTER = 0,
    M68K_ASM_FIELD_BITFIELD_OFFSET_DA,
    M68K_ASM_FIELD_BITFIELD_WIDTH_DA,
    M68K_ASM_FIELD_CACHE,
    M68K_ASM_FIELD_DA,
    M68K_ASM_FIELD_MODE,
    M68K_ASM_FIELD_ID,
    M68K_ASM_FIELD_OPMODE,
    M68K_ASM_FIELD_OFFSET,
    M68K_ASM_FIELD_SIZE,
    M68K_ASM_FIELD_DATA,
    M68K_ASM_FIELD_DISPLACEMENT_8,
    M68K_ASM_FIELD_DISPLACEMENT_16,
    M68K_ASM_FIELD_REGLIST_MASK,
    M68K_ASM_FIELD_WIDTH
}} M68kAsmFieldKind;

typedef enum {{
    M68K_ASM_VALUE_NONE = 0,
    M68K_ASM_VALUE_BF_OFFSET,
    M68K_ASM_VALUE_BF_OFFSET_KIND,
    M68K_ASM_VALUE_BF_WIDTH,
    M68K_ASM_VALUE_BF_WIDTH_KIND,
    M68K_ASM_VALUE_OPMODE,
    M68K_ASM_VALUE_REG,
    M68K_ASM_VALUE_REG_FIRST,
    M68K_ASM_VALUE_REG_SECOND,
    M68K_ASM_VALUE_REG_KIND,
    M68K_ASM_VALUE_REG_KIND_FIRST,
    M68K_ASM_VALUE_REG_KIND_SECOND,
    M68K_ASM_VALUE_EA_REG,
    M68K_ASM_VALUE_EA_MODE,
    M68K_ASM_VALUE_VALUE_HI16,
    M68K_ASM_VALUE_VALUE_LO16,
    M68K_ASM_VALUE_VALUE
}} M68kAsmValueSource;

typedef enum {{
    M68K_ASM_EXTENSION_EA_SINGLE_WORD = 0,
    M68K_ASM_EXTENSION_EA_LONG_ADDRESS = 1,
    M68K_ASM_EXTENSION_EA_IMMEDIATE = 2,
    M68K_ASM_EXTENSION_EA_INDEX = 3,
    M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO = 4,
    M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS = 5,
    M68K_ASM_EXTENSION_DISP16_ALWAYS = 6
}} M68kAsmExtensionKind;

typedef enum {{
{ea_text_family_ids}
}} M68kAsmEaTextSyntaxFamily;

typedef enum {{
    M68K_ASM_EA_VALUE_NONE = 0,
    M68K_ASM_EA_VALUE_NUMERIC,
    M68K_ASM_EA_VALUE_NUMERIC_OR_LABEL
}} M68kAsmEaTextValueKind;

enum {{
    M68K_ASM_SIZE_B = 1 << 0,
    M68K_ASM_SIZE_W = 1 << 1,
    M68K_ASM_SIZE_L = 1 << 2
}};

enum {{
    M68K_ASM_FIELD_VALUE_UNSET = {UNSET_FIELD_VALUE}
}};

enum {{
    M68K_ASM_BRIEF_EXT_DA_BIT_LO = {brief_fields["D/A"][1]},
    M68K_ASM_BRIEF_EXT_REGISTER_BIT_LO = {brief_fields["REGISTER"][1]},
    M68K_ASM_BRIEF_EXT_WL_BIT_LO = {brief_fields["W/L"][1]},
    M68K_ASM_BRIEF_EXT_SCALE_BIT_LO = {brief_fields["SCALE"][1]},
    M68K_ASM_BRIEF_EXT_FORMAT_BIT_LO = {brief_fields["0"][1]},
    M68K_ASM_BRIEF_EXT_DISPLACEMENT_BIT_LO = {brief_fields["DISPLACEMENT"][1]}
}};

enum {{
    M68K_ASM_FULL_EXT_DA_BIT_LO = {full_fields["D/A"][1]},
    M68K_ASM_FULL_EXT_REGISTER_BIT_LO = {full_fields["REGISTER"][1]},
    M68K_ASM_FULL_EXT_WL_BIT_LO = {full_fields["W/L"][1]},
    M68K_ASM_FULL_EXT_SCALE_BIT_LO = {full_fields["SCALE"][1]},
    M68K_ASM_FULL_EXT_FORMAT_BIT_LO = {full_fields["1"][1]},
    M68K_ASM_FULL_EXT_BS_BIT_LO = {full_fields["BS"][1]},
    M68K_ASM_FULL_EXT_IS_BIT_LO = {full_fields["IS"][1]},
    M68K_ASM_FULL_EXT_BD_SIZE_BIT_LO = {full_fields["BD SIZE"][1]},
    M68K_ASM_FULL_EXT_IIS_BIT_LO = {full_fields["I/IS"][1]}
}};

enum {{
    M68K_ASM_FULL_EXT_BD_RESERVED = {next(key for key, value in bd_sizes.items() if value == "reserved")},
    M68K_ASM_FULL_EXT_BD_NULL = {next(key for key, value in bd_sizes.items() if value == "null")},
    M68K_ASM_FULL_EXT_BD_WORD = {next(key for key, value in bd_sizes.items() if value == "word")},
    M68K_ASM_FULL_EXT_BD_LONG = {next(key for key, value in bd_sizes.items() if value == "long")}
}};

enum {{
    M68K_ASM_FORM_COUNT = {len(forms)},
    M68K_ASM_FORM_NONE = M68K_ASM_FORM_COUNT,
    M68K_ASM_FORM_SLOT_COUNT = M68K_ASM_FORM_COUNT + 1,
    M68K_ASM_PATCH_COUNT = {sum(len(form.patches) for form in forms)},
    M68K_ASM_EXTENSION_DEF_COUNT = {sum(len(_extension_defs(form)) for form in forms)},
    M68K_ASM_EA_TEXT_FORM_COUNT = {len(ea_text_forms)}
}};

#endif
"""


def _render_tables(forms: list[FormDef], kb: dict[str, object], mnemonic_list: list[str] | None = None) -> str:
    if mnemonic_list is None:
        mnemonic_list = _runtime_mnemonic_list(forms)
    mnemonic_name_rows = ['    "",'] + [f'    "{mnemonic.lower()}",' for mnemonic in mnemonic_list]
    sorted_mnemonics = sorted(mnemonic_list, key=str.lower)
    mnemonic_lookup_rows = [
        f'    {{ "{mnemonic.lower()}", M68K_ASM_MNEMONIC_{mnemonic} }},'
        for mnemonic in sorted_mnemonics
    ]
    forms_by_mnemonic: dict[str, list[FormDef]] = {}
    for form in forms:
        forms_by_mnemonic.setdefault(form.mnemonic, []).append(form)
    mnemonic_range_rows = ["    { 0u, 0u },"]
    for mnemonic in mnemonic_list:
        mnemonic_forms = forms_by_mnemonic.get(mnemonic, [])
        if mnemonic_forms:
            start = min(form.form_index for form in mnemonic_forms)
            count = max(form.form_index for form in mnemonic_forms) - start + 1
        else:
            start = 0
            count = 0
        mnemonic_range_rows.append(f"    {{ {start}u, {count}u }},")
    mnemonic_lookup_array_len = max(1, len(mnemonic_lookup_rows))
    if not mnemonic_lookup_rows:
        mnemonic_lookup_rows = ['    { NULL, M68K_ASM_MNEMONIC_NONE },']
    control_registers = _load_control_registers(kb)
    ea_text_forms = _load_ea_text_forms(kb)
    movem_masks = _kb_meta(kb, "movem_reg_masks")
    assert isinstance(movem_masks, dict)
    movem_mask_normal = cast(list[str], movem_masks.get("normal", []))
    movem_mask_predecrement = cast(list[str], movem_masks.get("predecrement", []))
    patch_rows: list[str] = []
    extension_rows: list[str] = []
    form_rows: list[str] = []
    control_register_rows: list[str] = []
    form_control_register_rows: list[str] = []
    ea_text_rows: list[str] = []
    patch_index = 0
    extension_index = 0
    form_control_register_index = 0
    for form in forms:
        extension_defs = _extension_defs(form)
        for patch in form.patches:
            patch_rows.append(
                "    { "
                f"{FIELD_KIND_ENUM[patch.field_kind]}, {patch.word_index}, {patch.occurrence}, {patch.bit_hi}, {patch.bit_lo}, {patch.operand_index}, {VALUE_SOURCE_ENUM[patch.value_source]}"
                " },"
            )
        for extension in extension_defs:
            extension_rows.append(
                "    { "
                f"{'M68K_ASM_EXTENSION_EA_SINGLE_WORD' if extension.kind == 'ea_single_word' else 'M68K_ASM_EXTENSION_EA_LONG_ADDRESS' if extension.kind == 'ea_long_address' else 'M68K_ASM_EXTENSION_EA_IMMEDIATE' if extension.kind == 'ea_immediate' else 'M68K_ASM_EXTENSION_EA_INDEX' if extension.kind == 'ea_brief_index' else 'M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO' if extension.kind == 'label_disp16_if_zero' else 'M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS' if extension.kind == 'label_disp16_always' else 'M68K_ASM_EXTENSION_DISP16_ALWAYS'}, "
                f"{extension.operand_index}, "
                f"{extension.patch_index}"
                " },"
            )
        operand_kinds = list(form.operand_kinds) + ["none"] * (MAX_FORM_OPERANDS - len(form.operand_kinds))
        form_rows.append(
            "    { "
            f"\"{form.mnemonic.lower()}\", "
            f"\"{form.syntax}\", "
            f"M68K_ASM_MNEMONIC_{form.mnemonic}, "
            f"{form.form_index}, "
            f"{form.form_index + 1}u, "
            f"{len(form.operand_kinds)}, "
            "{ "
            f"{OPERAND_KIND_ENUM.get(operand_kinds[0], 'M68K_ASM_OPERAND_NONE')}, "
            f"{OPERAND_KIND_ENUM.get(operand_kinds[1], 'M68K_ASM_OPERAND_NONE')}, "
            f"{OPERAND_KIND_ENUM.get(operand_kinds[2], 'M68K_ASM_OPERAND_NONE')}, "
            f"{OPERAND_KIND_ENUM.get(operand_kinds[3], 'M68K_ASM_OPERAND_NONE')} "
            "}, "
            f"{form.size_mask}, "
            f"{form.size_mask_68000}, "
            f"{form.ea_dn_size_mask}, "
            f"{form.ea_memory_size_mask}, "
            f"0x{form.cpu_mask:02X}u, "
            f"{form_control_register_index}, "
            f"{len(form.control_register_ids)}, "
            f"0x{form.opword_base:04X}, "
            f"0x{form.opword_mask:04X}, "
            f"{patch_index}, "
            f"{len(form.patches)}, "
            f"{form.bound_word_count}, "
            f"{extension_index}, "
            f"{len(extension_defs)}, "
            "{ "
            f"0x{form.bound_word_bases[0]:04X}, "
            f"0x{form.bound_word_bases[1]:04X} "
            "}, "
            "{ "
            f"0x{form.bound_word_masks[0]:04X}, "
            f"0x{form.bound_word_masks[1]:04X} "
            "}, "
            f"{form.size_values[0]}, "
            f"{form.size_values[1]}, "
            f"{form.size_values[2]}, "
            f"{form.opmode_values[0]}, "
            f"{form.opmode_values[1]}, "
            f"{form.opmode_values[2]}, "
            f"{form.branch_word_signal}, "
            f"{form.branch_word_bytes}, "
            f"{form.branch_long_signal}, "
            f"{form.branch_long_bytes}, "
            f"{1 if form.has_bound_word_extension else 0}"
            " },"
        )
        patch_index += len(form.patches)
        extension_index += len(extension_defs)
        for control_register_id in form.control_register_ids:
            form_control_register_rows.append(f"    {control_register_id}u,")
        form_control_register_index += len(form.control_register_ids)
    for entry in control_registers:
        control_register_rows.append(
            "    { "
            f"\"{entry['abbrev']}\", "
            f"{int(entry['id'])}u, "
            f"0x{int(entry['value']):03X}, "
            f"0x{int(entry['cpu_mask']):02X}u"
            " },"
        )
    ea_mode_encoding_map = _kb_meta(kb, "ea_mode_encoding")
    assert isinstance(ea_mode_encoding_map, dict)
    def c_char_literal(value: str | None) -> str:
        if not value:
            return r"'\0'"
        return f"'{value[0]}'"
    for entry in ea_text_forms:
        mode_name = str(entry["mode_name"])
        mode_bits = ea_mode_encoding_map[mode_name]
        ea_text_rows.append(
            "    { "
            f"\"{entry['name']}\", "
            f"{EA_TEXT_FAMILY_ENUM[str(entry['syntax_family'])]}, "
            f"{int(mode_bits[0])}, "
            f"{-1 if mode_bits[1] is None else int(mode_bits[1])}, "
            f"0x{_cpu_mask_value(_filter_cpu_set_min(CPU_ORDER, str(entry.get('cpu_min', '68000')))):02X}u, "
            f"{json.dumps(str(entry.get('base_token', '')))}, "
            f"{1 if entry.get('uses_base_register') else 0}, "
            f"{json.dumps(str(entry.get('prefix_token', '')))}, "
            f"{json.dumps(str(entry.get('suffix_token', '')))}, "
            f"{c_char_literal(cast(str | None, entry.get('register_prefix')))}, "
            f"{c_char_literal(cast(str | None, entry.get('size_suffix')))}, "
            f"{1 if entry.get('allow_label') else 0}, "
            f"{EA_TEXT_VALUE_KIND_ENUM[str(entry.get('value_kind', 'none'))]}, "
            f"{1 if entry.get('index_required') else 0}"
            " },"
        )
    nil_form_row = (
        '    { "", "", M68K_ASM_MNEMONIC_NONE, M68K_ASM_FORM_NONE, M68K_FORM_ID_NONE, 0, '
        '{ M68K_ASM_OPERAND_NONE, M68K_ASM_OPERAND_NONE, M68K_ASM_OPERAND_NONE, M68K_ASM_OPERAND_NONE }, '
        '0, 0, 0, 0, 0x00u, 0, 0, 0x0000, 0x0000, 0, 0, 0, 0, 0, '
        '{ 0x0000, 0x0000 }, { 0x0000, 0x0000 }, '
        'M68K_ASM_FIELD_VALUE_UNSET, M68K_ASM_FIELD_VALUE_UNSET, M68K_ASM_FIELD_VALUE_UNSET, '
        'M68K_ASM_FIELD_VALUE_UNSET, M68K_ASM_FIELD_VALUE_UNSET, M68K_ASM_FIELD_VALUE_UNSET, '
        '0, 0, 0, 0, 0 },'
    )
    return f"""/* Auto-generated by src/scripts/generate_c99_assembler_subset.py. */
#include "m68k_asm_metadata.h"

const char *const g_m68k_asm_mnemonic_names[M68K_ASM_MNEMONIC_COUNT] = {{
{chr(10).join(mnemonic_name_rows)}
}};

const M68kAsmMnemonicLookupEntry g_m68k_asm_mnemonic_lookup[{mnemonic_lookup_array_len}] = {{
{chr(10).join(mnemonic_lookup_rows)}
}};

const M68kAsmFormRange g_m68k_asm_mnemonic_form_ranges[M68K_ASM_MNEMONIC_COUNT] = {{
{chr(10).join(mnemonic_range_rows)}
}};

const M68kAsmFieldPatch g_m68k_asm_patches[{len(patch_rows)}] = {{
{chr(10).join(patch_rows)}
}};

const M68kAsmExtensionDef g_m68k_asm_extensions[{len(extension_rows)}] = {{
{chr(10).join(extension_rows)}
}};

const M68kAsmControlRegisterDef g_m68k_asm_control_registers[{max(1, len(control_register_rows))}] = {{
{chr(10).join(control_register_rows or ['    { NULL, 0u, 0x000, M68K_ASM_CPU_68010 },'])}
}};

const uint16_t g_m68k_asm_form_control_register_ids[{max(1, len(form_control_register_rows))}] = {{
{chr(10).join(form_control_register_rows or ['    0u,'])}
}};

const M68kAsmFormDef g_m68k_asm_forms[M68K_ASM_FORM_SLOT_COUNT] = {{
{chr(10).join(form_rows)}
{nil_form_row}
}};

const M68kAsmEaTextFormDef g_m68k_asm_ea_text_forms[{len(ea_text_rows)}] = {{
{chr(10).join(ea_text_rows)}
}};

const char *const g_m68k_asm_movem_mask_normal[16] = {{
{chr(10).join(f'    "{name}",' for name in movem_mask_normal)}
}};

const char *const g_m68k_asm_movem_mask_predecrement[16] = {{
{chr(10).join(f'    "{name}",' for name in movem_mask_predecrement)}
}};

const size_t g_m68k_asm_mnemonic_lookup_count = {len(sorted_mnemonics)};
const size_t g_m68k_asm_control_register_count = {len(control_register_rows)};
const size_t g_m68k_asm_ea_text_form_count = {len(ea_text_rows)};
"""


def _compact_three_line_if(lines: list[str]) -> list[str]:
    output: list[str] = []
    index = 0
    while index < len(lines):
        if index + 2 < len(lines):
            first = lines[index].rstrip()
            second = lines[index + 1].strip()
            third = lines[index + 2].strip()
            if first.strip().startswith("if (") and first.strip().endswith("{") and SINGLE_CLAUSE_BODY_RE.match(second) and third == "}":
                indent = re.match(r"^\s*", first).group(0)
                head = first.strip()[:-1].rstrip()
                compact = f"{indent}{head} {second}"
                if len(compact) <= STYLE_LINE_LENGTH:
                    output.append(compact)
                    index += 3
                    continue
                wrapped = _wrap_single_clause_if(indent, head, second)
                if wrapped is not None:
                    output.extend(wrapped)
                    index += 3
                    continue
        output.append(lines[index])
        index += 1
    return output


def _wrap_single_clause_if(indent: str, head: str, body: str) -> list[str] | None:
    continuation_indent = indent + " " * 4
    for operator in (" || ", " && "):
        split_at = head.rfind(operator)
        if split_at < 0:
            continue
        first = head[: split_at + len(operator)].rstrip()
        second = head[split_at + len(operator):].lstrip()
        line1 = indent + first
        line2 = continuation_indent + second + " " + body
        if len(line1) <= STYLE_LINE_LENGTH and len(line2) <= STYLE_LINE_LENGTH:
            return [line1, line2]
    return None


def _is_function_signature_start(line: str) -> bool:
    stripped = line.lstrip()
    if not stripped or not stripped.endswith("("):
        return False
    if "=" in stripped:
        return False
    if re.match(r"^(if|for|while|switch)\b", stripped):
        return False
    return re.match(r"^(?:static\s+)?(?:[A-Za-z_]\w*[\s\*]+)+[A-Za-z_]\w*\($", stripped) is not None


def _wrap_signature(start_line: str, continued_lines: list[str], closing_suffix: str) -> list[str]:
    start = start_line.rstrip()
    continuation_indent = " " * 4
    arguments: list[str] = []
    for i, raw in enumerate(continued_lines):
        stripped = raw.strip()
        if i == len(continued_lines) - 1:
            stripped = stripped[:-len(closing_suffix)].rstrip()
        if stripped.endswith(","):
            stripped = stripped[:-1].rstrip()
        if stripped:
            arguments.append(stripped)
    if not arguments:
        return [start + closing_suffix]
    output: list[str] = []
    current = start
    for i, argument in enumerate(arguments):
        suffix = "," if i < len(arguments) - 1 else closing_suffix
        token = argument + suffix
        separator = " " if current.endswith(",") else ""
        candidate = current + separator + token
        if len(candidate) <= STYLE_LINE_LENGTH:
            current = candidate
            continue
        output.append(current)
        current = continuation_indent + token
    output.append(current)
    return output


def _split_comma_tokens(text: str) -> list[str]:
    depth_paren = 0
    depth_brace = 0
    depth_bracket = 0
    in_string = False
    escaped = False
    token_start = 0
    tokens: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == "(":
                depth_paren += 1
            elif char == ")":
                depth_paren -= 1
            elif char == "{":
                depth_brace += 1
            elif char == "}":
                depth_brace -= 1
            elif char == "[":
                depth_bracket += 1
            elif char == "]":
                depth_bracket -= 1
            elif char == "," and depth_paren == 0 and depth_brace == 0 and depth_bracket == 0:
                tokens.append(text[token_start:index].strip())
                token_start = index + 1
        index += 1
    tail = text[token_start:].strip()
    if tail:
        tokens.append(tail)
    return tokens


def _wrap_initializer_line(line: str) -> list[str]:
    stripped = line.strip()
    if len(line) <= STYLE_LINE_LENGTH or not stripped.startswith("{ ") or not stripped.endswith(" },"):
        return [line.rstrip()]
    indent = re.match(r"^\s*", line).group(0)
    inner = stripped[2:-3].strip()
    tokens = _split_comma_tokens(inner)
    if len(tokens) < 2:
        return [line.rstrip()]
    output: list[str] = []
    current = indent + "{ "
    continuation_indent = indent + " " * 4
    for index, token in enumerate(tokens):
        suffix = "," if index < len(tokens) - 1 else " },"
        candidate = current + token + suffix
        if len(candidate) <= STYLE_LINE_LENGTH:
            current = candidate
            if index < len(tokens) - 1:
                current += " "
            continue
        if current.strip() == "{":
            return [line.rstrip()]
        output.append(current.rstrip())
        current = continuation_indent + token + suffix
        if index < len(tokens) - 1:
            current += " "
    output.append(current.rstrip())
    return output


def _compact_wrapped_if_conditions(lines: list[str]) -> list[str]:
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped == "if (" and index + 2 < len(lines):
            first_condition = lines[index + 1].strip()
            end_index = index + 2
            closing_line: str | None = None
            while end_index < len(lines):
                closing_candidate = lines[end_index].strip()
                if closing_candidate == ") {":
                    closing_line = lines[end_index]
                    break
                end_index += 1
            if closing_line is not None and first_condition:
                indent = re.match(r"^\s*", line).group(0)
                output.append(f"{indent}if ({first_condition}")
                middle_index = index + 2
                if middle_index < end_index:
                    while middle_index < end_index - 1:
                        output.append(lines[middle_index].rstrip())
                        middle_index += 1
                    output.append(lines[end_index - 1].rstrip() + ") {")
                else:
                    output[-1] = output[-1] + ") {"
                index = end_index + 1
                continue
        output.append(line.rstrip())
        index += 1
    return output


def _compact_if_closing_lines(lines: list[str]) -> list[str]:
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        if index + 1 < len(lines) and lines[index + 1].strip() == ") {":
            merged = line + ") {"
            if len(merged) <= STYLE_LINE_LENGTH:
                output.append(merged)
                index += 2
                continue
        output.append(line)
        index += 1
    return output


def _style_generated_c_text(text: str) -> str:
    lines = _compact_three_line_if(text.splitlines())
    lines = _compact_wrapped_if_conditions(lines)
    lines = _compact_if_closing_lines(lines)
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if _is_function_signature_start(line):
            next_index = index + 1
            collected: list[str] = []
            closing_suffix: str | None = None
            while next_index < len(lines):
                stripped = lines[next_index].strip()
                collected.append(lines[next_index])
                if stripped.endswith(") {"):
                    closing_suffix = ") {"
                    break
                if stripped.endswith(");"):
                    closing_suffix = ");"
                    break
                next_index += 1
            if closing_suffix is not None and collected:
                output.extend(_wrap_signature(line, collected, closing_suffix))
                index = next_index + 1
                continue
        if line.strip().startswith("{ ") and line.strip().endswith(" },"):
            output.extend(_wrap_initializer_line(line))
            index += 1
            continue
        output.append(line.rstrip())
        index += 1
    return "\n".join(output) + "\n"


def _render_form_model_header(forms: list[FormDef]) -> str:
    form_rows = [
        (
            f"    {{ {index + 1}u, {index}u, \"{form.mnemonic}\", \"{form.kb_mnemonic}\", "
            f"{form.local_form_index}u, \"{form.syntax}\", {len(form.operand_kinds)}u }},"
        )
        for index, form in enumerate(forms)
    ]
    id_by_row = [f"    {index + 1}u," for index in range(len(forms))]
    row_by_id = ["    M68K_FORM_ROW_NONE,"] + [f"    {index}u," for index in range(len(forms))]
    return "\n".join([
        "/* Auto-generated by src/scripts/generate_c99_assembler_subset.py. */",
        "#ifndef M68K_FORM_MODEL_H",
        "#define M68K_FORM_MODEL_H",
        "",
        "#include <stdint.h>",
        "",
        "typedef uint16_t M68kFormId;",
        "typedef uint16_t M68kFormRow;",
        "typedef uint8_t M68kOperandSlot;",
        "",
        "enum {",
        "    M68K_FORM_ID_NONE = 0u,",
        "    M68K_FORM_ROW_NONE = 0xFFFFu,",
        "    M68K_OPERAND_SLOT_NONE = 0xFFu,",
        "    M68K_OPERAND_SLOT_COUNT = 4u,",
        f"    M68K_CANONICAL_FORM_COUNT = {len(forms)}u",
        "};",
        "",
        "typedef struct {",
        "    M68kFormId id;",
        "    M68kFormRow row;",
        "    const char *mnemonic;",
        "    const char *kb_mnemonic;",
        "    uint16_t local_form_index;",
        "    const char *syntax;",
        "    M68kOperandSlot operand_count;",
        "} M68kCanonicalFormDef;",
        "",
        "static const M68kCanonicalFormDef g_m68k_canonical_forms[M68K_CANONICAL_FORM_COUNT] = {",
        *form_rows,
        "};",
        "",
        "static const M68kFormId g_m68k_canonical_form_id_by_row[M68K_CANONICAL_FORM_COUNT] = {",
        *id_by_row,
        "};",
        "",
        "static const M68kFormRow g_m68k_canonical_form_row_by_id[M68K_CANONICAL_FORM_COUNT + 1u] = {",
        *row_by_id,
        "};",
        "",
        "static inline M68kFormId m68k_form_id_for_row(M68kFormRow row) {",
        "    return row < M68K_CANONICAL_FORM_COUNT ? g_m68k_canonical_form_id_by_row[row] : M68K_FORM_ID_NONE;",
        "}",
        "",
        "static inline M68kFormRow m68k_form_row_for_id(M68kFormId id) {",
        "    return id <= M68K_CANONICAL_FORM_COUNT ? g_m68k_canonical_form_row_by_id[id] : M68K_FORM_ROW_NONE;",
        "}",
        "",
        "#endif",
        "",
    ])


def generate_files(output_dir: Path, kb_path: Path = KB_PATH) -> dict[str, str]:
    kb = _load_kb(kb_path)
    forms = _load_forms(kb_path)
    mnemonic_list = _runtime_mnemonic_list(forms, kb_path)
    tables_header = _style_generated_c_text(_render_header(forms, kb, mnemonic_list))
    tables_source = _style_generated_c_text(_render_tables(forms, kb, mnemonic_list))
    form_model_header = _style_generated_c_text(_render_form_model_header(forms))
    files = {
        "m68k_form_model.h": form_model_header,
        "m68k_asm_tables.h": tables_header,
        "m68k_asm_tables.c": tables_source,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (output_dir / name).write_text(text, encoding="ascii", newline="\n")
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb-path", type=Path, default=KB_PATH)
    parser.add_argument("--output-dir", type=Path, default=GENERATED_DIR)
    args = parser.parse_args()
    generate_files(args.output_dir, args.kb_path)


if __name__ == "__main__":
    main()
