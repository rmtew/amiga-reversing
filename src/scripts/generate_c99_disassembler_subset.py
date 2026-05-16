from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"
GENERATED_DIR = SRC_DIR / "generated"
SUBSET_GENERATOR_PATH = SRC_DIR / "scripts" / "generate_c99_assembler_subset.py"
KB_PATH = ROOT / "knowledge" / "m68k_instructions.json"
STYLE_LINE_LENGTH = 140
BUCKET_BITS = 12
BUCKET_COUNT = 1 << BUCKET_BITS

if str(SRC_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(SRC_DIR / "scripts"))

import m68k_canonical_model


@dataclass(frozen=True, slots=True)
class FormBucket:
    start: int
    count: int


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_subset_module():
    return _load_module(SUBSET_GENERATOR_PATH, "src_c99_disassembler_subset")


def _load_forms():
    subset = _load_subset_module()
    kb = _load_kb()
    mnemonics: list[str] = []
    for item in kb["instructions"]:
        mnemonic: str
        if not isinstance(item, dict) or "mnemonic" not in item:
            continue
        if item.get("forms") is None and item.get("form_template") is None:
            continue
        mnemonic = str(item["mnemonic"])
        try:
            subset._load_forms(KB_PATH, supported_mnemonics=(mnemonic,))
        except AssertionError:
            continue
        mnemonics.append(mnemonic)
    return [
        form
        for form in subset._load_forms(KB_PATH, supported_mnemonics=tuple(mnemonics))
        if not (int(form.opword_mask) == 0 and str(form.mnemonic).lower() in {"cpbcc", "cpdbcc", "cptrapcc"})
    ]


def _load_kb() -> dict[str, object]:
    data = json.loads(KB_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _popcount16(value: int) -> int:
    return bin(value & 0xFFFF).count("1")


def _form_bucket_matches(form, bucket_index: int) -> bool:
    top_mask = int(form.opword_mask) & 0xFFF0
    top_base = int(form.opword_base) & 0xFFF0
    return (((bucket_index << 4) & top_mask) == top_base)


def _operand_specificity(kind: str) -> int:
    if kind == "ea":
        return 0
    if kind in {"label", "rn", "rn_pair"}:
        return 1
    return 2


def _form_specificity(form) -> tuple[int, int, int]:
    return (
        _popcount16(int(form.opword_mask)),
        sum(_popcount16(int(form.bound_word_masks[word_index])) for word_index in range(int(form.bound_word_count))),
        sum(_operand_specificity(str(kind)) for kind in form.sampling_operand_kinds),
    )


def _decode_signature(form) -> tuple[object, ...]:
    return (
        int(form.opword_mask),
        int(form.opword_base),
        tuple(int(form.bound_word_masks[word_index]) for word_index in range(int(form.bound_word_count))),
        tuple(int(form.bound_word_bases[word_index]) for word_index in range(int(form.bound_word_count))),
        tuple(str(kind) for kind in form.sampling_operand_kinds),
        tuple(int(mask) for mask in form.ea_mode_masks),
    )


def _find_equal_specificity_ambiguities(forms: list[object]) -> list[tuple[int, int]]:
    seen: dict[tuple[object, ...], int] = {}
    ambiguities: list[tuple[int, int]] = []
    for index, form in enumerate(forms):
        key = (*_decode_signature(form), *_form_specificity(form))
        previous = seen.get(key)
        if previous is None:
            seen[key] = index
            continue
        previous_form = forms[previous]
        if str(previous_form.mnemonic) == str(form.mnemonic) and str(previous_form.syntax) == str(form.syntax):
            continue
        ambiguities.append((previous, index))
    return ambiguities


def _build_buckets(forms: list[object]) -> tuple[list[FormBucket], list[int]]:
    ambiguities = _find_equal_specificity_ambiguities(forms)
    if ambiguities:
        first, second = ambiguities[0]
        raise AssertionError(
            "ambiguous equal-specificity decode forms: "
            f"{forms[first].syntax!r} and {forms[second].syntax!r}"
        )
    candidate_indexes: list[int] = []
    buckets: list[FormBucket] = []
    form_order = list(range(len(forms)))
    form_order.sort(
        key=lambda index: (
            -_popcount16(int(forms[index].opword_mask)),
            -sum(
                _popcount16(int(forms[index].bound_word_masks[word_index]))
                for word_index in range(int(forms[index].bound_word_count))
            ),
            -sum(_operand_specificity(str(kind)) for kind in forms[index].sampling_operand_kinds),
            index,
        )
    )
    for bucket_index in range(BUCKET_COUNT):
        start = len(candidate_indexes)
        for form_index in form_order:
            if _form_bucket_matches(forms[form_index], bucket_index):
                candidate_indexes.append(form_index)
        buckets.append(FormBucket(start=start, count=len(candidate_indexes) - start))
    return buckets, candidate_indexes


def _load_zero_means_eight_flags(forms: list[object], kb: dict[str, object]) -> list[int]:
    instructions = kb.get("instructions", [])
    assert isinstance(instructions, list)
    by_mnemonic = {str(item["mnemonic"]): item for item in instructions if isinstance(item, dict) and "mnemonic" in item}
    flags: list[int] = []
    for form in forms:
        item = by_mnemonic.get(str(form.kb_mnemonic))
        flag = 0
        if isinstance(item, dict):
            fields = item.get("field_explanations", {})
            if isinstance(fields, dict):
                for field_name in ("Count/Register", "DATA", "Data", "Immediate Data"):
                    explanation = fields.get(field_name)
                    if isinstance(explanation, dict) and explanation.get("zero_means") == 8:
                        flag = 1
                        break
            if flag == 0:
                constraints = item.get("constraints", {})
                if isinstance(constraints, dict):
                    immediate_range = constraints.get("immediate_range")
                    if isinstance(immediate_range, dict) and immediate_range.get("zero_means") == 8:
                        flag = 1
        flags.append(flag)
    return flags


def _load_operand_shape_codes(forms: list[object]) -> list[list[int]]:
    mapping = {
        "predec": 1,
        "disp": 2,
    }
    rows: list[list[int]] = []
    for form in forms:
        row = [0, 0, 0, 0]
        for index, kind in enumerate(form.sampling_operand_kinds[:4]):
            row[index] = mapping.get(str(kind), 0)
        rows.append(row)
    return rows


def _load_operand_ea_mode_masks(forms: list[object]) -> list[list[int]]:
    rows: list[list[int]] = []
    for form in forms:
        masks = list(getattr(form, "ea_mode_masks", (0, 0, 0, 0)))[:4]
        rows.append(masks + [0] * (4 - len(masks)))
    return rows


def _wrapped_lines(values: list[int]) -> list[str]:
    lines: list[str] = []
    current = "    "
    for value in values:
        token = f"{value}u, "
        if len(current) + len(token) > STYLE_LINE_LENGTH:
            lines.append(current.rstrip())
            current = "    " + token
        else:
            current += token
    if current.strip():
        lines.append(current.rstrip())
    return lines


def _asm_form_index_map(subset) -> dict[tuple[object, ...], int]:
    return {
        m68k_canonical_model.form_identity_key(form): int(form.form_index)
        for form in subset._load_forms(KB_PATH, supported_mnemonics=subset.SUPPORTED_MNEMONICS)
    }


def _emit_form_table_lines(forms: list[object], subset) -> tuple[list[str], list[str], list[str], list[str]]:
    patch_rows: list[str] = []
    extension_rows: list[str] = []
    form_rows: list[str] = []
    control_register_rows: list[str] = []
    canonical_forms = m68k_canonical_model.load_canonical_forms(KB_PATH, subset._load_forms)
    canonical_form_ids = m68k_canonical_model.canonical_form_id_map(canonical_forms)
    asm_form_indexes = _asm_form_index_map(subset)
    patch_index = 0
    extension_index = 0
    control_register_index = 0
    extension_kind_enum = {
        "ea_single_word": "M68K_ASM_EXTENSION_EA_SINGLE_WORD",
        "ea_long_address": "M68K_ASM_EXTENSION_EA_LONG_ADDRESS",
        "ea_immediate": "M68K_ASM_EXTENSION_EA_IMMEDIATE",
        "ea_brief_index": "M68K_ASM_EXTENSION_EA_INDEX",
        "label_disp16_if_zero": "M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO",
        "label_disp16_always": "M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS",
        "disp16_always": "M68K_ASM_EXTENSION_DISP16_ALWAYS",
    }
    for form in forms:
        form_key = m68k_canonical_model.form_identity_key(form)
        asm_form_index = asm_form_indexes.get(form_key)
        canonical_form_id = canonical_form_ids[form_key]
        asm_form_index_expr = f"{asm_form_index}u" if asm_form_index is not None else "M68K_ASM_FORM_NONE"
        canonical_form_id_expr = f"{canonical_form_id}u"
        extension_defs = subset._extension_defs(form)
        for patch in form.patches:
            patch_rows.append(
                "    { "
                f"{subset.FIELD_KIND_ENUM[patch.field_kind]}, "
                f"{patch.word_index}u, "
                f"{patch.occurrence}u, "
                f"{patch.bit_hi}u, "
                f"{patch.bit_lo}u, "
                f"{patch.operand_index}, "
                f"{subset.VALUE_SOURCE_ENUM[patch.value_source]} "
                "},"
            )
        for extension in extension_defs:
            extension_rows.append(
                "    { "
                f"{extension_kind_enum[extension.kind]}, "
                f"{extension.operand_index}u, "
                f"{extension.patch_index}u "
                "},"
            )
        operand_kinds = list(form.operand_kinds) + ["none"] * (4 - len(form.operand_kinds))
        line1 = (
            "    { "
            f"\"{form.mnemonic.lower()}\", "
            f"\"{form.syntax}\", "
            f"M68K_ASM_MNEMONIC_{form.mnemonic}, "
            f"{asm_form_index_expr}, "
            f"{canonical_form_id_expr}, "
            f"{len(form.operand_kinds)}u,"
        )
        line2 = (
            "        { "
            f"{subset.OPERAND_KIND_ENUM.get(operand_kinds[0], 'M68K_ASM_OPERAND_NONE')}, "
            f"{subset.OPERAND_KIND_ENUM.get(operand_kinds[1], 'M68K_ASM_OPERAND_NONE')}, "
            f"{subset.OPERAND_KIND_ENUM.get(operand_kinds[2], 'M68K_ASM_OPERAND_NONE')}, "
            f"{subset.OPERAND_KIND_ENUM.get(operand_kinds[3], 'M68K_ASM_OPERAND_NONE')} "
            "}, "
            f"{form.size_mask}u, {form.size_mask_68000}u, {form.ea_dn_size_mask}u, {form.ea_memory_size_mask}u,"
        )
        line3 = (
            f"        0x{form.cpu_mask:02X}u, {control_register_index}u, {len(form.control_register_ids)}u, "
            f"0x{form.opword_base:04X}, 0x{form.opword_mask:04X}, "
            f"{patch_index}u, {len(form.patches)}u, {form.bound_word_count}u, {extension_index}u, {len(extension_defs)}u,"
        )
        line4 = (
            "        { "
            f"0x{form.bound_word_bases[0]:04X}, 0x{form.bound_word_bases[1]:04X} "
            "}, { "
            f"0x{form.bound_word_masks[0]:04X}, 0x{form.bound_word_masks[1]:04X} "
            "},"
        )
        line5 = (
            f"        {form.size_values[0]}u, {form.size_values[1]}u, {form.size_values[2]}u, {form.opmode_values[0]}u, "
            f"{form.opmode_values[1]}u, {form.opmode_values[2]}u, {form.branch_word_signal}u, {form.branch_word_bytes}u,"
        )
        line6 = (
            f"        {form.branch_long_signal}u, {form.branch_long_bytes}u, "
            f"{1 if form.has_bound_word_extension else 0}u }},"
        )
        form_rows.extend((
            line1,
            line2,
            line3,
            line4,
            line5,
            line6,
        ))
        patch_index += len(form.patches)
        extension_index += len(extension_defs)
        for control_register_id in form.control_register_ids:
            control_register_rows.append(f"    {control_register_id}u,")
        control_register_index += len(form.control_register_ids)
    return patch_rows, extension_rows, form_rows, control_register_rows


def _emit_tables_include(forms: list[object], kb: dict[str, object], subset) -> str:
    buckets, candidate_indexes = _build_buckets(forms)
    zero_means_eight = _load_zero_means_eight_flags(forms, kb)
    operand_shape_codes = _load_operand_shape_codes(forms)
    operand_ea_mode_masks = _load_operand_ea_mode_masks(forms)
    patch_rows, extension_rows, form_rows, control_register_rows = _emit_form_table_lines(forms, subset)
    bucket_lines = [f"    {{ {bucket.start}u, {bucket.count}u }}," for bucket in buckets]
    candidate_lines = _wrapped_lines(candidate_indexes)
    zero_means_lines = _wrapped_lines([*zero_means_eight, 0])
    operand_shape_lines = [
        f"    {{ {row[0]}u, {row[1]}u, {row[2]}u, {row[3]}u }},"
        for row in [*operand_shape_codes, [0, 0, 0, 0]]
    ]
    operand_ea_mode_mask_lines = [
        f"    {{ 0x{row[0]:016X}ULL, 0x{row[1]:016X}ULL, 0x{row[2]:016X}ULL, 0x{row[3]:016X}ULL }},"
        for row in [*operand_ea_mode_masks, [0, 0, 0, 0]]
    ]
    nil_form_row = [
        '    { "", "", M68K_ASM_MNEMONIC_NONE, M68K_ASM_FORM_NONE, M68K_FORM_ID_NONE, 0u,',
        "        { M68K_ASM_OPERAND_NONE, M68K_ASM_OPERAND_NONE, M68K_ASM_OPERAND_NONE, M68K_ASM_OPERAND_NONE }, 0u, 0u, 0u, 0u,",
        "        0x00u, 0u, 0u, 0x0000, 0x0000, 0u, 0u, 0u, 0u, 0u,",
        "        { 0x0000, 0x0000 }, { 0x0000, 0x0000 },",
        "        M68K_ASM_FIELD_VALUE_UNSET, M68K_ASM_FIELD_VALUE_UNSET, M68K_ASM_FIELD_VALUE_UNSET,",
        "        M68K_ASM_FIELD_VALUE_UNSET, M68K_ASM_FIELD_VALUE_UNSET, M68K_ASM_FIELD_VALUE_UNSET, 0u, 0u, 0u, 0u, 0u },",
    ]
    lines = [
        "/* Auto-generated by src/scripts/generate_c99_disassembler_subset.py. */",
        '#include "m68k_disassembler_metadata.h"',
        "#include <stdint.h>",
        "",
        f"static const M68kAsmFieldPatch g_m68k_disasm_patches[{len(patch_rows)}] = {{",
        *patch_rows,
        "};",
        "",
        f"static const M68kAsmExtensionDef g_m68k_disasm_extensions[{len(extension_rows)}] = {{",
        *extension_rows,
        "};",
        "",
        f"static const uint16_t g_m68k_disasm_form_control_register_ids[{max(1, len(control_register_rows))}] = {{",
        *(control_register_rows or ["    0u,"]),
        "};",
        "",
        "static const M68kAsmFormDef g_m68k_disasm_forms[M68K_DISASM_FORM_SLOT_COUNT] = {",
        *form_rows,
        *nil_form_row,
        "};",
        "",
        "static const M68kDisasmBucket g_m68k_disasm_buckets[] = {",
        *bucket_lines,
        "};",
        "",
        "static const uint16_t g_m68k_disasm_bucket_candidates[] = {",
        *candidate_lines,
        "};",
        "",
        "static const uint8_t g_m68k_disasm_inline_zero_means_eight[M68K_DISASM_FORM_SLOT_COUNT] = {",
        *zero_means_lines,
        "};",
        "",
        "static const uint8_t g_m68k_disasm_operand_shapes[M68K_DISASM_FORM_SLOT_COUNT][4] = {",
        *operand_shape_lines,
        "};",
        "",
        "static const uint64_t g_m68k_disasm_operand_ea_mode_masks[M68K_DISASM_FORM_SLOT_COUNT][4] = {",
        *operand_ea_mode_mask_lines,
        "};",
    ]
    return "\n".join(lines) + "\n"


def _emit_metadata_header(forms: list[object]) -> str:
    lines = [
        "/* Auto-generated by src/scripts/generate_c99_disassembler_subset.py. */",
        "#ifndef M68K_DISASSEMBLER_METADATA_H",
        "#define M68K_DISASSEMBLER_METADATA_H",
        "",
        "#define M68K_DISASM_FORM_COUNT " + str(len(forms)) + "u",
        "#define M68K_DISASM_FORM_NONE M68K_DISASM_FORM_COUNT",
        "#define M68K_DISASM_FORM_SLOT_COUNT (M68K_DISASM_FORM_COUNT + 1u)",
        "",
        "#endif",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate metadata-driven C disassembler subset.")
    parser.add_argument("--output-dir", type=Path, default=GENERATED_DIR)
    args = parser.parse_args()
    subset = _load_subset_module()
    forms = _load_forms()
    kb = _load_kb()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "m68k_disassembler_tables.h").write_text(
        _emit_tables_include(forms, kb, subset),
        encoding="ascii",
    )
    (output_dir / "m68k_disassembler_metadata.h").write_text(
        _emit_metadata_header(forms),
        encoding="ascii",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
