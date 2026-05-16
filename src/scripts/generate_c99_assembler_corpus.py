from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KB_PATH = ROOT / "knowledge" / "m68k_instructions.json"
DEFAULT_OUTPUT_DIR = ROOT / "src" / "tests" / "generated"
SUBSET_GENERATOR_PATH = ROOT / "src" / "scripts" / "generate_c99_assembler_subset.py"
VASM = ROOT / "tools" / "vasmm68k_mot.exe"

SIZE_BIT_TO_SUFFIX = {1 << 0: "b", 1 << 1: "w", 1 << 2: "l"}
SIZE_BIT = {"b": 1 << 0, "w": 1 << 1, "l": 1 << 2}
SIZE_TO_ENCODING = {"b": 0, "w": 1, "l": 2}
CPU_RANK = {
    "68000": 0,
    "68010": 1,
    "68020": 2,
    "68030": 3,
    "68040": 4,
    "68060": 5,
}


def _entry_cpu_names(entry: dict[str, object]) -> tuple[str, ...]:
    processor_set = entry.get("processor_set")
    if isinstance(processor_set, list) and processor_set:
        return tuple(str(cpu_name) for cpu_name in processor_set)
    minimum_cpu = str(entry.get("processor_min", "68000"))
    minimum_rank = CPU_RANK[minimum_cpu]
    return tuple(cpu_name for cpu_name, rank in CPU_RANK.items() if rank >= minimum_rank)


def _control_register_entry_map(kb: dict[str, object]) -> dict[tuple[str, int], int]:
    instructions = kb["instructions"]
    assert isinstance(instructions, list)
    entries: list[tuple[str, int, int]] = []
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
            cpu_mask = 0
            for cpu_name in _entry_cpu_names(entry):
                cpu_mask |= 1 << CPU_RANK[cpu_name]
            key = (abbrev, value, cpu_mask)
            if key in seen:
                continue
            seen.add(key)
            entries.append(key)
    entries.sort()
    return {(abbrev, value): index for index, (abbrev, value, _cpu_mask) in enumerate(entries)}


def _form_cpu_names(entry: dict[str, object], form_source: dict[str, object]) -> tuple[str, ...]:
    processor_set = form_source.get("processor_set")
    if isinstance(processor_set, list) and processor_set:
        return tuple(str(cpu_name) for cpu_name in processor_set)
    minimum_cpu = form_source.get("processor_min")
    base_cpu_names = _entry_cpu_names(entry)
    if isinstance(minimum_cpu, str) and minimum_cpu in CPU_RANK:
        return tuple(cpu_name for cpu_name in base_cpu_names if CPU_RANK[cpu_name] >= CPU_RANK[minimum_cpu])
    return base_cpu_names


def _instruction_has_oracle_cpu(item: dict[str, object], form_source: dict[str, object] | None, target_cpu: str) -> bool:
    processors = str(item.get("processors", ""))
    if target_cpu == "68000":
        return "M68000 Family" in processors or "MC68000" in processors
    if form_source is not None:
        return target_cpu in _form_cpu_names(item, form_source)
    return target_cpu in _entry_cpu_names(item)


def _raw_form_for_generated_form(kb: dict[str, object], item: dict[str, object], form: object) -> dict[str, object] | None:
    forms = _item_forms(kb, item)
    form_index = int(form.local_form_index if hasattr(form, "local_form_index") else form.form_index)
    if 0 <= form_index < len(forms):
        return forms[form_index]
    return None


@dataclass(frozen=True, slots=True)
class CorpusCase:
    case_id: str
    mnemonic: str
    asm_lines: tuple[str, ...]
    expected_hex: str
    instruction_specs: tuple[dict[str, object], ...]
    offset: int = 0
    size: int = 0


@dataclass(frozen=True, slots=True)
class RegisterSample:
    asm_text: str
    reg: int
    reg_is_address: int = 0


@dataclass(frozen=True, slots=True)
class RegisterPairSample:
    asm_text: str
    reg: int
    pair_reg: int
    reg_is_address: int = 0
    pair_reg_is_address: int = 0


@dataclass(frozen=True, slots=True)
class ImmediateSample:
    asm_text: str
    value: int


@dataclass(frozen=True, slots=True)
class DispSample:
    asm_text: str
    reg: int
    value: int


@dataclass(frozen=True, slots=True)
class ReglistSample:
    asm_text: str
    value: int


@dataclass(frozen=True, slots=True)
class AbsoluteLongSample:
    asm_text: str
    value: int


@dataclass(frozen=True, slots=True)
class EASample:
    asm_text: str
    mode: int
    reg: int
    ext_words: tuple[int, ...] = ()
    value: int = 0
    index_is_address: int = 0
    index_reg: int = 0
    index_long: int = 0
    scale: int = 0
    full_ext_base_suppress: int = 0
    full_ext_index_suppress: int = 0
    full_ext_base_disp_size: int = 0
    full_ext_outer_disp_size: int = 0
    full_ext_iis: int = 0
    full_ext_base_disp_value: int = 0
    full_ext_outer_disp_value: int = 0
    bf_offset_is_register: int = 0
    bf_offset: int = 0
    bf_width_is_register: int = 0
    bf_width: int = 0
    post_lines: tuple[str, ...] = ()
    trailing_specs: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class LabelSample:
    size: str
    displacement: int
    trailing_specs: tuple[dict[str, object], ...] = ()
    post_lines: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FixedOperandSample:
    asm_text: str


@dataclass(frozen=True, slots=True)
class ControlRegisterSample:
    asm_text: str
    reg_id: int
    value: int


@dataclass(frozen=True, slots=True)
class CacheSelectorSample:
    asm_text: str
    value: int


@dataclass(frozen=True, slots=True)
class RegisterOperandSpec:
    kind: str
    reg: int


@dataclass(frozen=True, slots=True)
class RegisterPairOperandSpec:
    kind: str
    reg: int
    pair_reg: int


@dataclass(frozen=True, slots=True)
class RnOperandSpec:
    reg_is_address: int
    reg: int


@dataclass(frozen=True, slots=True)
class RnPairOperandSpec:
    reg_is_address: int
    reg: int
    pair_reg_is_address: int
    pair_reg: int


@dataclass(frozen=True, slots=True)
class ValueOperandSpec:
    kind: str
    value: int


@dataclass(frozen=True, slots=True)
class DispOperandSpec:
    reg: int
    value: int


@dataclass(frozen=True, slots=True)
class FixedNameOperandSpec:
    name: str


@dataclass(frozen=True, slots=True)
class ControlRegisterOperandSpec:
    reg_id: int
    value: int


@dataclass(frozen=True, slots=True)
class EaOperandSpec:
    mode: int
    reg: int
    value: int | None = None
    index_is_address: int = 0
    index_reg: int = 0
    index_long: int = 0
    scale: int = 0
    full_ext_base_suppress: int = 0
    full_ext_index_suppress: int = 0
    full_ext_base_disp_size: int = 0
    full_ext_outer_disp_size: int = 0
    full_ext_iis: int = 0
    full_ext_base_disp_value: int = 0
    full_ext_outer_disp_value: int = 0


@dataclass(frozen=True, slots=True)
class BitfieldEaOperandSpec:
    mode: int
    reg: int
    value: int | None = None
    index_is_address: int = 0
    index_reg: int = 0
    index_long: int = 0
    scale: int = 0
    full_ext_base_suppress: int = 0
    full_ext_index_suppress: int = 0
    full_ext_base_disp_size: int = 0
    full_ext_outer_disp_size: int = 0
    full_ext_iis: int = 0
    full_ext_base_disp_value: int = 0
    full_ext_outer_disp_value: int = 0
    bf_offset_is_register: int = 0
    bf_offset: int = 0
    bf_width_is_register: int = 0
    bf_width: int = 0


@dataclass(frozen=True, slots=True)
class FormContext:
    form: object
    size: str | None
    syntax: str
    operand_kinds: tuple[str, ...]
    operand_roles: tuple[str | None, ...]
    target_cpu: str = "68000"
    form_source: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class SampleCoverageEntry:
    mnemonic: str
    kb_mnemonic: str
    local_form_index: int
    form_index: int
    syntax: str
    size: str | None
    target_cpu: str
    status: str
    reason: str
    missing_operand_kinds: tuple[str, ...] = ()


SAMPLE_STATUS_SAMPLED = "sampled"
SAMPLE_STATUS_MISSING_SAMPLE_STRATEGY = "missing_sample_strategy"
SAMPLE_STATUS_INTENTIONALLY_UNSUPPORTED = "intentionally_unsupported"
SAMPLE_STATUS_IMPLEMENTED_UNSUPPORTED = "implemented_unsupported"
SAMPLE_STATUS_NOT_TARGET_CPU = "not_target_cpu"
SAMPLE_STATUS_ORACLE_UNAVAILABLE = "oracle_unavailable"


@dataclass(frozen=True, slots=True)
class EncodedCase:
    patch_values: tuple[int, ...]
    ext_words: tuple[int, ...]
    operand_specs: tuple[object, ...]
    trailing_specs: tuple[dict[str, object], ...]
    encoded: bytes


def _load_subset_module():
    spec = importlib.util.spec_from_file_location("src_c99_subset_codegen", SUBSET_GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_forms_and_kb() -> tuple[object, list[object], dict[str, object]]:
    module = _load_subset_module()
    forms = list(module._load_forms(KB_PATH))
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    return module, forms, kb


def _word(value: int) -> bytes:
    return value.to_bytes(2, "big", signed=False)


def _csv_or_dash(values: tuple[int, ...], *, hex_mode: bool = False) -> str:
    if not values:
        return "-"
    if hex_mode:
        return ",".join(f"{value:04x}" for value in values)
    return ",".join(str(value) for value in values)


def _mnemonic_item(kb: dict[str, object], mnemonic: str) -> dict[str, object]:
    instructions = kb["instructions"]
    assert isinstance(instructions, list)
    return next(item for item in instructions if item["mnemonic"] == mnemonic)


def _item_forms(kb: dict[str, object], item: dict[str, object]) -> list[dict[str, object]]:
    forms = item.get("forms")
    if isinstance(forms, list):
        return forms
    template_id = item.get("form_template")
    if not isinstance(template_id, str):
        return []
    syntaxes = item.get("form_syntaxes", [])
    assert isinstance(syntaxes, list)
    form_templates = _kb_meta(kb, "form_templates")
    template_forms = form_templates[template_id]
    assert isinstance(template_forms, list)
    resolved: list[dict[str, object]] = []
    for syntax, form_body in zip(syntaxes, template_forms, strict=True):
        assert isinstance(form_body, dict)
        form = dict(form_body)
        form["syntax"] = syntax
        resolved.append(form)
    return resolved


def _kb_meta(kb: dict[str, object], key: str) -> dict[str, object]:
    meta = kb["_meta"]
    assert isinstance(meta, dict)
    value = meta[key]
    assert isinstance(value, dict)
    return value


def _sizes_for_mask(size_mask: int) -> tuple[str | None, ...]:
    if size_mask == 0:
        return (None,)
    sizes: list[str] = []
    for bit, suffix in SIZE_BIT_TO_SUFFIX.items():
        if size_mask & bit:
            sizes.append(suffix)
    return tuple(sizes)


def _form_supports_cpu(form: object, target_cpu: str) -> bool:
    return (int(form.cpu_mask) & (1 << CPU_RANK[target_cpu])) != 0


def _sizes_for_target_form(form: object, target_cpu: str) -> tuple[str | None, ...]:
    size_mask = int(getattr(form, "size_mask", 0))
    size_mask_68000 = int(getattr(form, "size_mask_68000", 0))
    if target_cpu == "68000":
        if size_mask != 0 and size_mask_68000 == 0:
            return ()
        mask = size_mask_68000 or size_mask
    else:
        mask = size_mask
    return _sizes_for_mask(mask)


REGISTER_DOMAIN = (0, 7)
DISP_DOMAIN = ((0, 0x0010), (7, 0x7FFC))
ABSW_DOMAIN = (0x1234, 0x7FFE)
ABSL_DOMAIN = (0x00123456, 0x00FFFEF0)
INDEX_DOMAIN = (
    {"index_is_address": 0, "index_reg": 1, "index_long": 0, "scale": 0, "brief_word_prefix": 0x1000, "suffix": "d1.w"},
    {"index_is_address": 1, "index_reg": 3, "index_long": 1, "scale": 0, "brief_word_prefix": 0xB800, "suffix": "a3.l"},
)


def _register_samples(prefix: str) -> tuple[RegisterSample, ...]:
    return tuple(
        RegisterSample(asm_text=f"{prefix}{reg}", reg=reg)
        for reg in REGISTER_DOMAIN
    )


def _rn_samples() -> tuple[RegisterSample, ...]:
    return _register_samples("d") + tuple(
        RegisterSample(asm_text=f"a{reg}", reg=reg, reg_is_address=1)
        for reg in REGISTER_DOMAIN
    )


def _control_register_samples(
    item: dict[str, object],
    target_cpu: str,
    form_source: dict[str, object] | None = None,
    kb: dict[str, object] | None = None,
) -> tuple[ControlRegisterSample, ...]:
    constraints = item.get("constraints", {})
    assert isinstance(constraints, dict)
    entries = constraints.get("control_registers", [])
    assert isinstance(entries, list)
    register_ids = _control_register_entry_map(kb) if kb is not None else {}
    allowed_names = None
    if isinstance(form_source, dict):
        control_registers = form_source.get("control_registers", [])
        if isinstance(control_registers, list) and control_registers:
            allowed_names = {str(name).lower() for name in control_registers}
    allowed = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and target_cpu in _entry_cpu_names(entry)
        and (allowed_names is None or str(entry.get("abbrev", "")).lower() in allowed_names)
    ]
    samples: list[ControlRegisterSample] = []
    seen: set[str] = set()
    for entry in allowed:
        abbrev = str(entry.get("abbrev", "")).lower()
        if not abbrev or abbrev in seen:
            continue
        seen.add(abbrev)
        value = int(str(entry["hex"]), 16)
        samples.append(ControlRegisterSample(
            asm_text=abbrev,
            reg_id=register_ids[(abbrev, value)],
            value=value,
        ))
    return tuple(samples[:4])


def _cache_selector_samples() -> tuple[CacheSelectorSample, ...]:
    return (
        CacheSelectorSample(asm_text="nc", value=0),
        CacheSelectorSample(asm_text="dc", value=1),
        CacheSelectorSample(asm_text="ic", value=2),
        CacheSelectorSample(asm_text="bc", value=3),
    )


def _ea_mode_encoding(kb: dict[str, object]) -> dict[str, tuple[int, int | None]]:
    encoding = _kb_meta(kb, "ea_mode_encoding")
    return {
        str(name): (int(bits[0]), None if bits[1] is None else int(bits[1]))
        for name, bits in encoding.items()
    }


def _full_ext_fields(kb: dict[str, object]) -> dict[str, tuple[int, int]]:
    meta = kb["_meta"]
    assert isinstance(meta, dict)
    fields = meta["ea_full_ext_word"]
    assert isinstance(fields, list)
    return {
        str(field["name"]): (int(field["bit_hi"]), int(field["bit_lo"]))
        for field in fields
    }


def _full_ext_bd_sizes(kb: dict[str, object]) -> dict[str, int]:
    values = _kb_meta(kb, "ea_full_ext_bd_size")
    return {str(value): int(key) for key, value in values.items()}


def _index_full_ext_samples(
    kb: dict[str, object],
    *,
    mode: int,
    reg: int,
    disp: int,
    index: dict[str, object],
) -> tuple[EASample, ...]:
    bd_sizes = _full_ext_bd_sizes(kb)
    suffix = str(index["suffix"])
    return (
        EASample(
            asm_text=f"${disp:02x}(a{reg},{suffix}){{full}}",
            mode=mode,
            reg=reg,
            value=disp,
            index_is_address=int(index["index_is_address"]),
            index_reg=int(index["index_reg"]),
            index_long=int(index["index_long"]),
            scale=int(index["scale"]),
            full_ext_base_disp_size=bd_sizes["word"],
            full_ext_base_disp_value=disp,
        ),
        EASample(
            asm_text=f"${disp:02x}(a{reg},{suffix}){{full,bs}}",
            mode=mode,
            reg=reg,
            value=disp,
            index_is_address=int(index["index_is_address"]),
            index_reg=int(index["index_reg"]),
            index_long=int(index["index_long"]),
            scale=int(index["scale"]),
            full_ext_base_suppress=1,
            full_ext_base_disp_size=bd_sizes["word"],
            full_ext_base_disp_value=disp,
        ),
        EASample(
            asm_text=f"${disp:02x}(a{reg},{suffix}){{full,is}}",
            mode=mode,
            reg=reg,
            value=disp,
            index_is_address=int(index["index_is_address"]),
            index_reg=int(index["index_reg"]),
            index_long=int(index["index_long"]),
            scale=int(index["scale"]),
            full_ext_index_suppress=1,
            full_ext_base_disp_size=bd_sizes["word"],
            full_ext_base_disp_value=disp,
        ),
        EASample(
            asm_text=f"${disp:02x}(a{reg},{suffix}){{full,bdw=$1234,odw=$5678,iis=3}}",
            mode=mode,
            reg=reg,
            value=disp,
            index_is_address=int(index["index_is_address"]),
            index_reg=int(index["index_reg"]),
            index_long=int(index["index_long"]),
            scale=int(index["scale"]),
            full_ext_base_disp_size=bd_sizes["word"],
            full_ext_outer_disp_size=bd_sizes["word"],
            full_ext_iis=3,
            full_ext_base_disp_value=0x1234,
            full_ext_outer_disp_value=0x5678,
        ),
    )


def _ea_mode_sizes(kb: dict[str, object]) -> dict[str, frozenset[str]]:
    sizes = _kb_meta(kb, "ea_mode_sizes")
    return {
        str(name): frozenset(str(size) for size in values)
        for name, values in sizes.items()
    }


def _instruction_spec(
    *, mnemonic: str, size_suffix: str | None, operand_count: int, patch_values: tuple[int, ...], operand_specs: tuple[object, ...]
) -> dict[str, object]:
    return {
        "mnemonic": mnemonic.lower(),
        "size_suffix": size_suffix or "",
        "operand_count": operand_count,
        "patch_values": patch_values,
        "operand_specs": operand_specs,
    }


def _text_manifest(case_list: list[CorpusCase]) -> str:
    return "\n".join(
        "|".join(
            (
                case.case_id,
                case.expected_hex,
                str(len(case.instruction_specs)),
                *(
                    "^".join(
                        (
                            str(spec["mnemonic"]),
                            str(spec.get("size_suffix", "")) or "-",
                            str(spec["operand_count"]),
                            _csv_or_dash(tuple(int(v) for v in spec["patch_values"])),
                            ";".join(_serialize_operand_spec(v) for v in spec["operand_specs"]) or "-",
                        )
                    )
                    for spec in case.instruction_specs
                ),
            )
        )
        for case in case_list
    ) + "\n"


def _serialize_operand_spec(spec: object) -> str:
    if isinstance(spec, RegisterOperandSpec):
        return f"{spec.kind}:{spec.reg}"
    if isinstance(spec, RegisterPairOperandSpec):
        return f"{spec.kind}:{spec.reg}:{spec.pair_reg}"
    if isinstance(spec, ControlRegisterOperandSpec):
        return f"ctrlreg:{spec.reg_id}:{spec.value:03x}"
    if isinstance(spec, ValueOperandSpec) and spec.kind == "cache":
        return f"cache:{spec.value}"
    if isinstance(spec, RnOperandSpec):
        return f"rn:{spec.reg_is_address}:{spec.reg}"
    if isinstance(spec, RnPairOperandSpec):
        return f"rnpair:{spec.reg_is_address}:{spec.reg}:{spec.pair_reg_is_address}:{spec.pair_reg}"
    if isinstance(spec, ValueOperandSpec):
        if spec.kind == "imm":
            return f"imm:{spec.value & 0xFFFFFFFF:08x}"
        return f"{spec.kind}:{spec.value & 0xFFFF:04x}"
    if isinstance(spec, DispOperandSpec):
        return f"disp:{spec.reg}:{spec.value & 0xFFFF:04x}"
    if isinstance(spec, FixedNameOperandSpec):
        return spec.name
    if isinstance(spec, EaOperandSpec):
        if (
            spec.full_ext_base_suppress
            or spec.full_ext_index_suppress
            or spec.full_ext_base_disp_size
            or spec.full_ext_outer_disp_size
            or spec.full_ext_iis
        ):
            return (
                f"eaf:{spec.mode}:{spec.reg}:{(spec.value or 0) & 0xFF:x}:"
                f"{spec.index_is_address}:{spec.index_reg}:{spec.index_long}:{spec.scale}:"
                f"{spec.full_ext_base_suppress}:{spec.full_ext_index_suppress}:"
                f"{spec.full_ext_base_disp_size}:{spec.full_ext_outer_disp_size}:"
                f"{spec.full_ext_iis}:{spec.full_ext_base_disp_value:x}:{spec.full_ext_outer_disp_value:x}"
            )
        if spec.value is None:
            return f"ea:{spec.mode}:{spec.reg}"
        if spec.mode == 7 and spec.reg in {1, 4}:
            return f"ea:{spec.mode}:{spec.reg}:{spec.value:08x}"
        if spec.mode == 6 or (spec.mode == 7 and spec.reg == 3):
            return (
                f"ea:{spec.mode}:{spec.reg}:{spec.value & 0xFF:02x}:"
                f"{spec.index_is_address}:{spec.index_reg}:{spec.index_long}:{spec.scale}"
            )
        return f"ea:{spec.mode}:{spec.reg}:{spec.value & 0xFFFF:04x}"
    if isinstance(spec, BitfieldEaOperandSpec):
        if (
            spec.full_ext_base_suppress
            or spec.full_ext_index_suppress
            or spec.full_ext_base_disp_size
            or spec.full_ext_outer_disp_size
            or spec.full_ext_iis
        ):
            return (
                f"bfeaf:{spec.mode}:{spec.reg}:{(spec.value or 0) & 0xFF:x}:"
                f"{spec.index_is_address}:{spec.index_reg}:{spec.index_long}:{spec.scale}:"
                f"{spec.full_ext_base_suppress}:{spec.full_ext_index_suppress}:"
                f"{spec.full_ext_base_disp_size}:{spec.full_ext_outer_disp_size}:"
                f"{spec.full_ext_iis}:{spec.full_ext_base_disp_value:x}:{spec.full_ext_outer_disp_value:x}:"
                f"{spec.bf_offset_is_register}:{spec.bf_offset}:{spec.bf_width_is_register}:{spec.bf_width}"
            )
        if spec.value is None:
            return (
                f"bfea:{spec.mode}:{spec.reg}:0:{spec.index_is_address}:{spec.index_reg}:{spec.index_long}:"
                f"{spec.bf_offset_is_register}:{spec.bf_offset}:{spec.bf_width_is_register}:{spec.bf_width}"
            )
        if spec.mode == 7 and spec.reg == 1:
            return (
                f"bfea:{spec.mode}:{spec.reg}:{spec.value:08x}:{spec.index_is_address}:{spec.index_reg}:{spec.index_long}:"
                f"{spec.bf_offset_is_register}:{spec.bf_offset}:{spec.bf_width_is_register}:{spec.bf_width}"
            )
        if spec.mode == 6 or (spec.mode == 7 and spec.reg == 3):
            return (
                f"bfea:{spec.mode}:{spec.reg}:{spec.value & 0xFF:02x}:{spec.index_is_address}:{spec.index_reg}:{spec.index_long}:"
                f"{spec.bf_offset_is_register}:{spec.bf_offset}:{spec.bf_width_is_register}:{spec.bf_width}"
            )
        return (
            f"bfea:{spec.mode}:{spec.reg}:{spec.value & 0xFFFF:04x}:{spec.index_is_address}:{spec.index_reg}:{spec.index_long}:"
            f"{spec.bf_offset_is_register}:{spec.bf_offset}:{spec.bf_width_is_register}:{spec.bf_width}"
        )
    raise AssertionError(f"unsupported operand spec {spec!r}")


def _default_trailing_specs(forms: list[object]) -> tuple[dict[str, object], ...]:
    candidates = [form for form in forms if len(form.operand_kinds) == 0]
    if not candidates:
        return ()
    form = sorted(candidates, key=lambda item: item.mnemonic.lower())[0]
    return (
        _instruction_spec(
            mnemonic=form.mnemonic,
            size_suffix="",
            operand_count=0,
            patch_values=(),
            operand_specs=(),
        ),
    )


def _form_for_spec(spec: dict[str, object], forms: list[object]) -> object:
    size_suffix = str(spec.get("size_suffix", ""))
    candidates = [
        form
        for form in forms
        if form.mnemonic.lower() == str(spec["mnemonic"]) and len(form.operand_kinds) == int(spec["operand_count"])
    ]
    if size_suffix:
        sized = [
            form
            for form in candidates
            if (form.size_mask_68000 or form.size_mask) & SIZE_BIT[size_suffix]
        ]
        if sized:
            return sized[0]
    return candidates[0]


def _spec_asm_line(spec: dict[str, object], forms: list[object]) -> str:
    form = _form_for_spec(spec, forms)
    sizes = _sizes_for_target_form(form, "68000")
    mnemonic = form.mnemonic.lower()
    if sizes == (None,) or len(tuple(size for size in sizes if size is not None)) <= 1:
        return mnemonic
    size_suffix = str(spec.get("size_suffix", "")) or sizes[0]
    return f"{mnemonic}.{size_suffix}"


def _instruction_size_from_spec(spec: dict[str, object], forms: list[object]) -> int:
    _form_for_spec(spec, forms)
    ext_word_count = 0
    for operand_spec in spec["operand_specs"]:
        if isinstance(operand_spec, (EaOperandSpec, BitfieldEaOperandSpec)):
            if operand_spec.value is None:
                ext_word_count += 0
            elif operand_spec.mode == 7 and operand_spec.reg == 1:
                ext_word_count += 2
            else:
                ext_word_count += 1
        elif isinstance(operand_spec, ValueOperandSpec) and operand_spec.kind == "label":
            ext_word_count += 1
    return 2 + (ext_word_count * 2)


def _operand_has_inline_patch(form: object, operand_index: int) -> bool:
    return any(patch.operand_index == operand_index for patch in form.patches)


def _operand_has_bound_extension_patch(form: object, operand_index: int) -> bool:
    return any(patch.operand_index == operand_index and patch.word_index != 0 for patch in form.patches)


def _operand_extension_words(sample: object, size: str | None, *, uses_inline_patch: bool = False) -> int:
    if isinstance(sample, ImmediateSample):
        if uses_inline_patch:
            return 0
        return 2 if size == "l" else 1
    if isinstance(sample, DispSample):
        return 1
    if not isinstance(sample, EASample):
        return 0
    if sample.mode == 7 and sample.reg == 1:
        return 2
    if sample.mode == 7 and sample.reg == 4:
        return 2 if size == "l" else 1
    if sample.mode == 6 or (sample.mode == 7 and sample.reg == 3):
        if (
            getattr(sample, "full_ext_base_suppress", 0)
            or getattr(sample, "full_ext_index_suppress", 0)
            or getattr(sample, "full_ext_base_disp_size", 0)
            or getattr(sample, "full_ext_outer_disp_size", 0)
            or getattr(sample, "full_ext_iis", 0)
        ):
            count = 1
            if getattr(sample, "full_ext_base_disp_size", 0) == 2:
                count += 1
            elif getattr(sample, "full_ext_base_disp_size", 0) == 3:
                count += 2
            if getattr(sample, "full_ext_outer_disp_size", 0) == 2:
                count += 1
            elif getattr(sample, "full_ext_outer_disp_size", 0) == 3:
                count += 2
            return count
        return 1
    return len(sample.ext_words)


def _ea_samples_for_mode(
    mode_name: str,
    kb: dict[str, object],
    forms: list[object],
    item: dict[str, object],
    size: str | None,
    target_cpu: str,
) -> tuple[EASample, ...]:
    mode, reg_override = _ea_mode_encoding(kb)[mode_name]
    trailing_specs = _default_trailing_specs(forms)
    trailing_lines = tuple(_spec_asm_line(spec, forms) for spec in trailing_specs)
    if mode_name == "dn":
        return tuple(EASample(asm_text=f"d{reg}", mode=mode, reg=reg) for reg in REGISTER_DOMAIN)
    if mode_name == "an":
        return tuple(EASample(asm_text=f"a{reg}", mode=mode, reg=reg) for reg in REGISTER_DOMAIN)
    if mode_name == "ind":
        return tuple(EASample(asm_text=f"(a{reg})", mode=mode, reg=reg) for reg in REGISTER_DOMAIN)
    if mode_name == "postinc":
        return tuple(EASample(asm_text=f"(a{reg})+", mode=mode, reg=reg) for reg in REGISTER_DOMAIN)
    if mode_name == "predec":
        return tuple(EASample(asm_text=f"-(a{reg})", mode=mode, reg=reg) for reg in REGISTER_DOMAIN)
    if mode_name == "disp":
        return tuple(
            EASample(
                asm_text=f"${value:04x}(a{reg})",
                mode=mode,
                reg=reg,
                ext_words=(value,),
                value=value,
            )
            for reg, value in DISP_DOMAIN
        )
    if mode_name == "index":
        samples = [
            EASample(
                asm_text=f"${disp:02x}(a{reg},{index['suffix']})",
                mode=mode,
                reg=reg,
                ext_words=(index["brief_word_prefix"] | disp,),
                value=disp,
                index_is_address=index["index_is_address"],
                index_reg=index["index_reg"],
                index_long=index["index_long"],
                scale=index["scale"],
            )
            for (reg, disp), index in zip(((0, 0x10), (7, 0x20)), INDEX_DOMAIN, strict=True)
        ]
        if CPU_RANK[target_cpu] >= CPU_RANK["68020"]:
            samples.extend(
                sample
                for (reg, disp), index in zip(((0, 0x10), (7, 0x20)), INDEX_DOMAIN, strict=True)
                for sample in _index_full_ext_samples(kb, mode=mode, reg=reg, disp=disp, index=index)
            )
        return tuple(samples)
    if mode_name == "pcdisp":
        return (
            EASample(
                asm_text="target(pc)",
                mode=mode,
                reg=reg_override if reg_override is not None else 0,
                ext_words=(0x0004,),
                value=0x0004,
                post_lines=(*trailing_lines, "target:"),
                trailing_specs=trailing_specs,
            ),
        )
    if mode_name == "pcindex":
        return tuple(
            EASample(
                asm_text=f"target(pc,{index['suffix']})",
                mode=mode,
                reg=reg_override if reg_override is not None else 0,
                ext_words=(index["brief_word_prefix"] | 0x0004,),
                value=0x04,
                index_is_address=index["index_is_address"],
                index_reg=index["index_reg"],
                index_long=index["index_long"],
                scale=index["scale"],
                post_lines=(*trailing_lines, "target:"),
                trailing_specs=trailing_specs,
            )
            for index in INDEX_DOMAIN
        )
    if mode_name == "absw":
        return tuple(
            EASample(
                asm_text=f"${value:04x}.w",
                mode=mode,
                reg=reg_override if reg_override is not None else 0,
                ext_words=(value,),
                value=value,
            )
            for value in ABSW_DOMAIN
        )
    if mode_name == "absl":
        return tuple(
            EASample(
                asm_text=f"${value:08x}.l",
                mode=mode,
                reg=reg_override if reg_override is not None else 0,
                ext_words=((value >> 16) & 0xFFFF, value & 0xFFFF),
                value=value,
            )
            for value in ABSL_DOMAIN
        )
    if mode_name == "imm":
        return tuple(
            EASample(
                asm_text=sample.asm_text,
                mode=mode,
                reg=reg_override if reg_override is not None else 4,
                ext_words=((sample.value >> 16) & 0xFFFF, sample.value & 0xFFFF) if size == "l" else (sample.value & 0xFFFF,),
                value=sample.value,
            )
            for sample in _immediate_samples(item, size, kb)
        )
    return ()


def _disp_samples() -> tuple[DispSample, ...]:
    return tuple(
        DispSample(
            asm_text=f"${value:04x}(a{reg})",
            reg=reg,
            value=value,
        )
        for reg, value in DISP_DOMAIN
    )


def _fixed_operand_samples(asm_text: str) -> tuple[FixedOperandSample, ...]:
    return (FixedOperandSample(asm_text=asm_text),)


def _movem_reglist_mask(registers: tuple[str, ...], *, use_predecrement: bool, kb: dict[str, object]) -> int:
    movem_masks = _kb_meta(kb, "movem_reg_masks")
    order_key = "predecrement" if use_predecrement else "normal"
    order = tuple(str(name) for name in movem_masks[order_key])
    index_by_name = {name: index for index, name in enumerate(order)}
    mask = 0
    for register in registers:
        mask |= 1 << index_by_name[register]
    return mask


def _reglist_samples(context: FormContext, samples: tuple[object, ...], kb: dict[str, object]) -> tuple[ReglistSample, ...]:
    use_predecrement = False
    if context.operand_kinds == ("reglist", "ea"):
        ea_sample = samples[1]
        use_predecrement = isinstance(ea_sample, EASample) and ea_sample.mode == 4
    groups = (
        (("d0", "d7", "a0", "a7"), "d0/d7/a0/a7"),
        (("d0", "d1", "a6", "a7"), "d0-d1/a6-a7"),
    )
    return tuple(
        ReglistSample(
            asm_text=text,
            value=_movem_reglist_mask(registers, use_predecrement=use_predecrement, kb=kb),
        )
        for registers, text in groups
    )


def _bounded_immediate_values(min_value: int, max_value: int) -> tuple[int, ...]:
    candidates = (min_value, -1, 0, 1, max_value)
    values = tuple(value for value in candidates if min_value <= value <= max_value)
    return tuple(dict.fromkeys(values))


def _operand_roles(kb: dict[str, object], item: dict[str, object], operand_kinds: tuple[str, ...]) -> tuple[str | None, ...]:
    forms = _item_forms(kb, item)
    form0 = forms[0]
    operands = form0["operands"]
    assert isinstance(operands, list)
    roles = tuple(operand.get("role") for operand in operands)
    if any(role is not None for role in roles):
        return roles
    ea_modes = item.get("ea_modes", {})
    assert isinstance(ea_modes, dict)
    ea_operand_indexes = [index for index, kind in enumerate(operand_kinds) if kind == "ea"]
    inferred: list[str | None] = [None] * len(operand_kinds)
    if len(ea_operand_indexes) == 1:
        if "src" in ea_modes and "dst" in ea_modes:
            if operand_kinds == ("ea", "dn"):
                role = "src"
            elif operand_kinds == ("dn", "ea"):
                role = "dst"
            else:
                role = "src"
        else:
            role = "src" if "src" in ea_modes else "dst" if "dst" in ea_modes else "ea" if "ea" in ea_modes else None
        inferred[ea_operand_indexes[0]] = role
    elif len(ea_operand_indexes) == 2 and "src" in ea_modes and "dst" in ea_modes:
        inferred[ea_operand_indexes[0]] = "src"
        inferred[ea_operand_indexes[1]] = "dst"
    return tuple(inferred)


def _encode_immediate_value(value: int, bits: int) -> int:
    mask = (1 << bits) - 1
    return value & mask


def _encode_full_ext_word(
    kb: dict[str, object],
    *,
    index_is_address: int,
    index_reg: int,
    index_long: int,
    scale: int,
    base_suppress: int,
    index_suppress: int,
    base_disp_size: int,
    iis: int,
) -> int:
    fields = _full_ext_fields(kb)
    ext = 0
    ext |= 1 << fields["1"][1]
    ext |= (index_is_address & 0x1) << fields["D/A"][1]
    ext |= (index_reg & 0x7) << fields["REGISTER"][1]
    ext |= (index_long & 0x1) << fields["W/L"][1]
    ext |= (scale & 0x3) << fields["SCALE"][1]
    ext |= (base_suppress & 0x1) << fields["BS"][1]
    ext |= (index_suppress & 0x1) << fields["IS"][1]
    ext |= (base_disp_size & 0x3) << fields["BD SIZE"][1]
    ext |= (iis & 0x7) << fields["I/IS"][1]
    return ext


def _immediate_samples(item: dict[str, object], size: str | None, kb: dict[str, object]) -> tuple[ImmediateSample, ...]:
    constraints = item.get("constraints", {})
    assert isinstance(constraints, dict)
    immediate_range = constraints.get("immediate_range")
    if isinstance(immediate_range, dict):
        min_value = int(immediate_range["min"])
        max_value = int(immediate_range["max"])
        bits = int(immediate_range["bits"])
        return tuple(
            ImmediateSample(
                asm_text=f"#{value}",
                value=_encode_immediate_value(value, bits),
            )
            for value in _bounded_immediate_values(min_value, max_value)
        )
    if size is None:
        return (ImmediateSample(asm_text="#0", value=0),)
    byte_count = int(_kb_meta(kb, "size_byte_count")[size])
    bits = byte_count * 8
    return tuple(
        ImmediateSample(
            asm_text=f"#{value}",
            value=_encode_immediate_value(value, bits),
        )
        for value in _bounded_immediate_values(0, (1 << bits) - 1)
    )


def _label_samples(form: object, size: str | None, forms: list[object]) -> tuple[LabelSample, ...]:
    if size is None:
        return ()
    supported_sizes = _sizes_for_mask(form.size_mask_68000)
    if size not in supported_sizes:
        return ()
    trailing_specs = _default_trailing_specs(forms)
    trailing_lines = tuple(_spec_asm_line(spec, forms) for spec in trailing_specs)
    displacement = sum(_instruction_size_from_spec(spec, forms) for spec in trailing_specs)
    if size == "b":
        signal = form.branch_word_signal
        if displacement == signal:
            return ()
    elif size == "w":
        signal = form.branch_word_signal
        if signal != 0:
            return ()
        displacement += form.branch_word_bytes
        if getattr(form, "has_bound_word_extension", False):
            displacement += 2
    elif size == "l":
        signal = form.branch_long_signal
        if signal != 0xFF:
            return ()
        displacement += form.branch_long_bytes
    else:
        return ()
    return (
        LabelSample(
            size=size,
            displacement=displacement,
            trailing_specs=trailing_specs,
            post_lines=(*trailing_lines, "target:"),
        ),
    )


def _ea_allowed_modes(item: dict[str, object], role: str | None) -> frozenset[str]:
    ea_modes = item.get("ea_modes", {})
    assert isinstance(ea_modes, dict)
    ea_modes_020 = item.get("ea_modes_020", {})
    assert isinstance(ea_modes_020, dict)

    def _base_modes(mode_role: str | None) -> frozenset[str]:
        if mode_role is not None and mode_role in ea_modes:
            modes = ea_modes[mode_role]
            assert isinstance(modes, list)
            return frozenset(str(mode) for mode in modes)
        if "ea" in ea_modes:
            modes = ea_modes["ea"]
            assert isinstance(modes, list)
            return frozenset(str(mode) for mode in modes)
        allowed: set[str] = set()
        for modes in ea_modes.values():
            assert isinstance(modes, list)
            allowed.update(str(mode) for mode in modes)
        return frozenset(allowed)

    def _modes_020_only(mode_role: str | None) -> frozenset[str]:
        if mode_role is not None and mode_role in ea_modes_020:
            modes = ea_modes_020[mode_role]
            assert isinstance(modes, list)
            return frozenset(str(mode) for mode in modes)
        if "ea" in ea_modes_020:
            modes = ea_modes_020["ea"]
            assert isinstance(modes, list)
            return frozenset(str(mode) for mode in modes)
        allowed: set[str] = set()
        for modes in ea_modes_020.values():
            assert isinstance(modes, list)
            allowed.update(str(mode) for mode in modes)
        return frozenset(allowed)

    allowed_modes = _base_modes(role)
    if role is None:
        return allowed_modes
    return frozenset(mode for mode in allowed_modes if mode not in _modes_020_only(role))


def _ea_allowed_modes_for_form(item: dict[str, object], operand_kinds: tuple[str, ...], role: str | None) -> frozenset[str]:
    directional = item.get("ea_modes_by_direction")
    assert directional is None or isinstance(directional, dict)
    if isinstance(directional, dict):
        direction_constraints = item.get("constraints", {}).get("movem_direction", {})
        assert isinstance(direction_constraints, dict)
        direction_values = direction_constraints.get("values", {})
        assert isinstance(direction_values, dict)
        allowed = None
        if operand_kinds == ("reglist", "ea"):
            allowed = direction_values.get("0")
        elif operand_kinds == ("ea", "reglist"):
            allowed = direction_values.get("1")
        if isinstance(allowed, str):
            modes = directional.get(allowed)
            if isinstance(modes, list):
                return frozenset(str(mode) for mode in modes)
    return _ea_allowed_modes(item, role)


def _filter_routed_immediate_modes(
    item: dict[str, object],
    allowed_modes: frozenset[str],
    role: str | None,
    forms: list[object],
    subset_module: object,
    kb: dict[str, object],
) -> frozenset[str]:
    if role != "src" or "imm" not in allowed_modes:
        return allowed_modes
    if subset_module._supports_direct_immediate_source(
        str(item["mnemonic"]),
        forms,
        kb=kb,
    ):
        return allowed_modes
    return frozenset(mode for mode in allowed_modes if mode != "imm")


def _ea_sample_options(
    context: FormContext,
    item: dict[str, object],
    kb: dict[str, object],
    forms: list[object],
    subset_module: object,
    operand_role: str | None,
) -> tuple[object, ...]:
    constraints = item.get("constraints", {})
    assert isinstance(constraints, dict)
    an_sizes = frozenset(str(size) for size in constraints.get("an_sizes", ()))
    bit_op_sizes_raw = constraints.get("bit_op_sizes", {})
    assert isinstance(bit_op_sizes_raw, dict)
    bit_op_sizes = {str(key): str(value) for key, value in bit_op_sizes_raw.items()}
    ea_mode_sizes = _ea_mode_sizes(kb)
    allowed_ea_modes = _filter_routed_immediate_modes(
        item,
        _ea_allowed_modes_for_form(item, context.operand_kinds, operand_role),
        operand_role,
        forms,
        subset_module,
        kb,
    )
    ea_mode_order = tuple(name for name in _ea_mode_encoding(kb) if name in allowed_ea_modes)
    return tuple(
        sample
        for mode_name in ea_mode_order
        for sample in _ea_samples_for_mode(mode_name, kb, forms, item, context.size, context.target_cpu)
        if context.size is None or context.size in ea_mode_sizes.get(mode_name, frozenset())
        if not (
            an_sizes
            and mode_name == "an"
            and context.size is not None
            and context.size not in an_sizes
        )
        if not (
            bit_op_sizes
            and operand_role == "dst"
            and context.size is not None
            and (
                (mode_name == "dn" and context.size != bit_op_sizes.get("dn"))
                or (mode_name != "dn" and context.size != bit_op_sizes.get("memory"))
            )
        )
    )


def _bf_ea_sample_options(
    context: FormContext,
    item: dict[str, object],
    kb: dict[str, object],
    forms: list[object],
    subset_module: object,
) -> tuple[object, ...]:
    base_samples = _ea_sample_options(context, item, kb, forms, subset_module, "ea")
    selected: list[EASample] = []
    for sample in base_samples:
        if not isinstance(sample, EASample):
            continue
        if sample.mode == 7 and sample.reg == 4:
            continue
        selected.append(EASample(
            asm_text=f"{sample.asm_text}{{0:1}}",
            mode=sample.mode,
            reg=sample.reg,
            ext_words=sample.ext_words,
            value=sample.value,
            index_is_address=sample.index_is_address,
            index_reg=sample.index_reg,
            index_long=sample.index_long,
            scale=sample.scale,
            full_ext_base_suppress=sample.full_ext_base_suppress,
            full_ext_index_suppress=sample.full_ext_index_suppress,
            full_ext_base_disp_size=sample.full_ext_base_disp_size,
            full_ext_outer_disp_size=sample.full_ext_outer_disp_size,
            full_ext_iis=sample.full_ext_iis,
            full_ext_base_disp_value=sample.full_ext_base_disp_value,
            full_ext_outer_disp_value=sample.full_ext_outer_disp_value,
            bf_offset=0,
            bf_width=1,
            post_lines=sample.post_lines,
            trailing_specs=sample.trailing_specs,
        ))
        selected.append(EASample(
            asm_text=f"{sample.asm_text}{{d0:8}}",
            mode=sample.mode,
            reg=sample.reg,
            ext_words=sample.ext_words,
            value=sample.value,
            index_is_address=sample.index_is_address,
            index_reg=sample.index_reg,
            index_long=sample.index_long,
            scale=sample.scale,
            full_ext_base_suppress=sample.full_ext_base_suppress,
            full_ext_index_suppress=sample.full_ext_index_suppress,
            full_ext_base_disp_size=sample.full_ext_base_disp_size,
            full_ext_outer_disp_size=sample.full_ext_outer_disp_size,
            full_ext_iis=sample.full_ext_iis,
            full_ext_base_disp_value=sample.full_ext_base_disp_value,
            full_ext_outer_disp_value=sample.full_ext_outer_disp_value,
            bf_offset_is_register=1,
            bf_offset=0,
            bf_width=8,
            post_lines=sample.post_lines,
            trailing_specs=sample.trailing_specs,
        ))
        break
    return tuple(selected)


def _sample_options_for_operand(
    context: FormContext,
    item: dict[str, object],
    kb: dict[str, object],
    forms: list[object],
    subset_module: object,
    operand_kind: str,
    operand_role: str | None,
) -> tuple[object, ...]:
    if operand_kind == "dn":
        return _register_samples("d")
    if operand_kind == "dn_pair":
        return (
            RegisterPairSample(asm_text="d0:d1", reg=0, pair_reg=1),
            RegisterPairSample(asm_text="d6:d7", reg=6, pair_reg=7),
        )
    if operand_kind == "an":
        return _register_samples("a")
    if operand_kind == "rn":
        return _rn_samples()
    if operand_kind == "rn_pair":
        return (
            RegisterPairSample(asm_text="(a0):(a1)", reg=0, pair_reg=1, reg_is_address=1, pair_reg_is_address=1),
            RegisterPairSample(asm_text="(d0):(a7)", reg=0, pair_reg=7, reg_is_address=0, pair_reg_is_address=1),
        )
    if operand_kind == "ctrl_reg":
        return _control_register_samples(item, context.target_cpu, context.form_source, kb)
    if operand_kind == "cache_sel":
        return _cache_selector_samples()
    if operand_kind == "ccr":
        return _fixed_operand_samples("ccr")
    if operand_kind == "imm":
        return _immediate_samples(item, context.size, kb)
    if operand_kind == "label":
        return _label_samples(context.form, context.size, forms)
    if operand_kind == "ind":
        return _ea_samples_for_mode("ind", kb, forms, item, context.size, context.target_cpu)
    if operand_kind == "postinc":
        return _ea_samples_for_mode("postinc", kb, forms, item, context.size, context.target_cpu)
    if operand_kind == "predec":
        return _ea_samples_for_mode("predec", kb, forms, item, context.size, context.target_cpu)
    if operand_kind == "absl":
        return tuple(
            AbsoluteLongSample(asm_text=sample.asm_text, value=sample.value)
            for sample in _ea_samples_for_mode("absl", kb, forms, item, context.size, context.target_cpu)
        )
    if operand_kind == "disp":
        return _disp_samples()
    if operand_kind == "reglist":
        return _fixed_operand_samples("reglist")
    if operand_kind == "ea":
        return _ea_sample_options(context, item, kb, forms, subset_module, operand_role)
    if operand_kind == "bf_ea":
        return _bf_ea_sample_options(context, item, kb, forms, subset_module)
    if operand_kind == "sr":
        return _fixed_operand_samples("sr")
    if operand_kind == "usp":
        return _fixed_operand_samples("usp")
    return ()


def _sample_options(
    context: FormContext,
    item: dict[str, object],
    kb: dict[str, object],
    forms: list[object],
    subset_module: object,
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        _sample_options_for_operand(
            context,
            item,
            kb,
            forms,
            subset_module,
            operand_kind,
            operand_role,
        )
        for operand_kind, operand_role in zip(context.operand_kinds, context.operand_roles, strict=True)
    )


def _sample_coverage_entry(
    context: FormContext,
    status: str,
    reason: str,
    missing_operand_kinds: tuple[str, ...] = (),
) -> SampleCoverageEntry:
    return SampleCoverageEntry(
        mnemonic=str(context.form.mnemonic),
        kb_mnemonic=str(context.form.kb_mnemonic),
        local_form_index=int(context.form.local_form_index),
        form_index=int(context.form.form_index),
        syntax=str(context.form.syntax),
        size=context.size,
        target_cpu=context.target_cpu,
        status=status,
        reason=reason,
        missing_operand_kinds=missing_operand_kinds,
    )


def _sample_status_for_options(context: FormContext, options: tuple[tuple[object, ...], ...]) -> SampleCoverageEntry:
    missing = tuple(
        operand_kind
        for operand_kind, choices in zip(context.operand_kinds, options, strict=True)
        if not choices
    )
    if missing and "reglist" not in context.operand_kinds:
        return _sample_coverage_entry(
            context,
            SAMPLE_STATUS_MISSING_SAMPLE_STRATEGY,
            "one or more operands produced no sample options",
            missing,
        )
    return _sample_coverage_entry(context, SAMPLE_STATUS_SAMPLED, "sample options available")


def _expand_reglist_options(context: FormContext, base_samples: tuple[object, ...], kb: dict[str, object]) -> tuple[tuple[object, ...], ...]:
    reglist_indexes = [index for index, kind in enumerate(context.operand_kinds) if kind == "reglist"]
    if not reglist_indexes:
        return (base_samples,)
    expanded = [list(base_samples)]
    for reglist_index in reglist_indexes:
        next_expanded: list[list[object]] = []
        for partial in expanded:
            current = tuple(partial)
            for reglist_sample in _reglist_samples(context, current, kb):
                updated = list(partial)
                updated[reglist_index] = reglist_sample
                next_expanded.append(updated)
        expanded = next_expanded
    return tuple(tuple(partial) for partial in expanded)


def _size_bits(item: dict[str, object], size: str | None) -> int | None:
    if size is None:
        return None
    size_encoding = item.get("size_encoding")
    if size_encoding is None:
        return None
    values = size_encoding["values"]
    return next(entry["bits"] for entry in values if entry["size"] == size)


def _build_case_encoding(
    context: FormContext,
    item: dict[str, object],
    samples: tuple[object, ...],
    forms: list[object],
    kb: dict[str, object],
) -> EncodedCase:
    size_bits = _size_bits(item, context.size)
    patch_values: list[int] = []
    for patch in context.form.patches:
        if patch.field_kind == "SIZE":
            assert size_bits is not None
            patch_values.append(size_bits)
        elif patch.field_kind == "OPMODE":
            if context.size == "b":
                patch_values.append(context.form.opmode_values[0])
            elif context.size == "w":
                patch_values.append(context.form.opmode_values[1])
            elif context.size == "l":
                patch_values.append(context.form.opmode_values[2])
            else:
                raise AssertionError("opmode requires explicit size")
        elif patch.value_source == "none":
            patch_values.append(0)
        else:
            sample = samples[patch.operand_index]
            if patch.value_source in {"reg", "ea_reg", "reg_first"}:
                patch_values.append(sample.reg)
            elif patch.value_source == "reg_second":
                patch_values.append(sample.pair_reg)
            elif patch.value_source in {"reg_kind", "reg_kind_first"}:
                patch_values.append(sample.reg_is_address)
            elif patch.value_source == "reg_kind_second":
                patch_values.append(sample.pair_reg_is_address)
            elif patch.value_source == "ea_mode":
                patch_values.append(sample.mode)
            elif patch.value_source == "bf_offset":
                patch_values.append(0 if sample.bf_offset == 32 else sample.bf_offset)
            elif patch.value_source == "bf_offset_kind":
                patch_values.append(sample.bf_offset_is_register)
            elif patch.value_source == "bf_width":
                patch_values.append(0 if sample.bf_width == 32 else sample.bf_width)
            elif patch.value_source == "bf_width_kind":
                patch_values.append(sample.bf_width_is_register)
            elif patch.value_source in {"value", "value_hi16", "value_lo16"}:
                if patch.field_kind == "8-BIT DISPLACEMENT":
                    if context.size == "b":
                        raw_value = sample.displacement
                    elif context.size == "w":
                        raw_value = 0
                    elif context.size == "l":
                        raw_value = 0xFF
                    else:
                        raise AssertionError("branch displacement field requires explicit size")
                elif isinstance(sample, LabelSample):
                    raw_value = sample.displacement
                else:
                    raw_value = sample.value
                if patch.value_source == "value_hi16":
                    patch_values.append((raw_value >> 16) & 0xFFFF)
                elif patch.value_source == "value_lo16":
                    patch_values.append(raw_value & 0xFFFF)
                else:
                    patch_values.append(raw_value)
            else:
                raise AssertionError(f"unsupported patch binding {patch.value_source}")
    trailing_specs: tuple[dict[str, object], ...] = ()
    for _operand_index, (operand_kind, sample) in enumerate(zip(context.operand_kinds, samples, strict=True)):
        if operand_kind == "label" or (operand_kind in {"ea", "bf_ea"} and sample.trailing_specs):
            trailing_specs = sample.trailing_specs
    trailing_bytes = sum(_instruction_size_from_spec(spec, forms) for spec in trailing_specs)
    instruction_size = 2 + (
        2 * sum(
            _operand_extension_words(sample, context.size, uses_inline_patch=_operand_has_inline_patch(context.form, index))
            for index, sample in enumerate(samples)
        )
    )
    instruction_size += 2 * context.form.bound_word_count
    ext_words: list[int] = []
    operand_specs: list[object] = []
    ext_offset = 2 + (2 * context.form.bound_word_count)
    for operand_index, (operand_kind, sample) in enumerate(zip(context.operand_kinds, samples, strict=True)):
        if operand_kind in {"ea", "bf_ea"}:
            sample_value = sample.value
            sample_ext_words = sample.ext_words
            sample_uses_full_ext = (
                sample.full_ext_base_suppress
                or sample.full_ext_index_suppress
                or sample.full_ext_base_disp_size
                or sample.full_ext_outer_disp_size
                or sample.full_ext_iis
            )
            if sample.mode == 7 and sample.reg == 2 and sample.trailing_specs:
                sample_value = instruction_size + trailing_bytes - ext_offset
                sample_ext_words = (sample_value & 0xFFFF,)
            elif sample.mode == 7 and sample.reg == 3 and sample.trailing_specs:
                sample_value = instruction_size + trailing_bytes - ext_offset
                sample_ext_words = (sample.ext_words[0] & 0xFF00) | (sample_value & 0x00FF),
            elif sample_uses_full_ext:
                sample_ext_words = (
                    _encode_full_ext_word(
                        kb,
                        index_is_address=sample.index_is_address,
                        index_reg=sample.index_reg,
                        index_long=sample.index_long,
                        scale=sample.scale,
                        base_suppress=sample.full_ext_base_suppress,
                        index_suppress=sample.full_ext_index_suppress,
                        base_disp_size=sample.full_ext_base_disp_size,
                        iis=sample.full_ext_iis,
                    ),
                )
                if sample.full_ext_base_disp_size == 2:
                    sample_ext_words += (sample.full_ext_base_disp_value & 0xFFFF,)
                elif sample.full_ext_base_disp_size == 3:
                    sample_ext_words += (
                        (sample.full_ext_base_disp_value >> 16) & 0xFFFF,
                        sample.full_ext_base_disp_value & 0xFFFF,
                    )
                if sample.full_ext_outer_disp_size == 2:
                    sample_ext_words += (sample.full_ext_outer_disp_value & 0xFFFF,)
                elif sample.full_ext_outer_disp_size == 3:
                    sample_ext_words += (
                        (sample.full_ext_outer_disp_value >> 16) & 0xFFFF,
                        sample.full_ext_outer_disp_value & 0xFFFF,
                    )
            ext_words.extend(sample_ext_words)
            encoded_value = (
                sample_value
                if (sample.mode == 7 and sample.reg in {1, 4})
                else (sample_value & 0xFF if sample.mode == 6 or (sample.mode == 7 and sample.reg == 3) else sample_ext_words[0] if sample_ext_words else None)
            )
            if operand_kind == "bf_ea":
                operand_specs.append(
                    BitfieldEaOperandSpec(
                        mode=sample.mode,
                        reg=sample.reg,
                        value=encoded_value,
                        index_is_address=sample.index_is_address,
                        index_reg=sample.index_reg,
                        index_long=sample.index_long,
                        scale=sample.scale,
                        full_ext_base_suppress=sample.full_ext_base_suppress,
                        full_ext_index_suppress=sample.full_ext_index_suppress,
                        full_ext_base_disp_size=sample.full_ext_base_disp_size,
                        full_ext_outer_disp_size=sample.full_ext_outer_disp_size,
                        full_ext_iis=sample.full_ext_iis,
                        full_ext_base_disp_value=sample.full_ext_base_disp_value,
                        full_ext_outer_disp_value=sample.full_ext_outer_disp_value,
                        bf_offset_is_register=sample.bf_offset_is_register,
                        bf_offset=sample.bf_offset,
                        bf_width_is_register=sample.bf_width_is_register,
                        bf_width=sample.bf_width,
                    )
                )
            else:
                operand_specs.append(
                    EaOperandSpec(
                        mode=sample.mode,
                        reg=sample.reg,
                        value=encoded_value,
                        index_is_address=sample.index_is_address,
                        index_reg=sample.index_reg,
                        index_long=sample.index_long,
                        scale=sample.scale,
                        full_ext_base_suppress=sample.full_ext_base_suppress,
                        full_ext_index_suppress=sample.full_ext_index_suppress,
                        full_ext_base_disp_size=sample.full_ext_base_disp_size,
                        full_ext_outer_disp_size=sample.full_ext_outer_disp_size,
                        full_ext_iis=sample.full_ext_iis,
                        full_ext_base_disp_value=sample.full_ext_base_disp_value,
                        full_ext_outer_disp_value=sample.full_ext_outer_disp_value,
                    )
                )
            ext_offset += 2 * len(sample_ext_words)
        elif operand_kind == "ind":
            operand_specs.append(EaOperandSpec(mode=2, reg=sample.reg))
        elif operand_kind == "absl":
            operand_specs.append(EaOperandSpec(mode=7, reg=1, value=sample.value))
        elif operand_kind == "predec":
            operand_specs.append(RegisterOperandSpec(kind="predec", reg=sample.reg))
        elif operand_kind == "postinc":
            operand_specs.append(RegisterOperandSpec(kind="postinc", reg=sample.reg))
        elif operand_kind == "disp":
            if not _operand_has_bound_extension_patch(context.form, operand_index):
                ext_words.append(sample.value & 0xFFFF)
            operand_specs.append(DispOperandSpec(reg=sample.reg, value=sample.value))
        elif operand_kind == "reglist":
            operand_specs.append(ValueOperandSpec(kind="reglist", value=sample.value))
        elif operand_kind == "dn":
            operand_specs.append(RegisterOperandSpec(kind="dn", reg=sample.reg))
        elif operand_kind == "dn_pair":
            operand_specs.append(RegisterPairOperandSpec(kind="dnpair", reg=sample.reg, pair_reg=sample.pair_reg))
        elif operand_kind == "an":
            operand_specs.append(RegisterOperandSpec(kind="an", reg=sample.reg))
        elif operand_kind == "rn":
            operand_specs.append(RnOperandSpec(reg_is_address=sample.reg_is_address, reg=sample.reg))
        elif operand_kind == "rn_pair":
            operand_specs.append(
                RnPairOperandSpec(
                    reg_is_address=sample.reg_is_address,
                    reg=sample.reg,
                    pair_reg_is_address=sample.pair_reg_is_address,
                    pair_reg=sample.pair_reg,
                )
            )
        elif operand_kind == "ctrl_reg":
            operand_specs.append(ControlRegisterOperandSpec(reg_id=sample.reg_id, value=sample.value))
        elif operand_kind == "cache_sel":
            operand_specs.append(ValueOperandSpec(kind="cache", value=sample.value))
        elif operand_kind == "ccr":
            operand_specs.append(FixedNameOperandSpec(name="ccr"))
        elif operand_kind == "imm":
            if not _operand_has_inline_patch(context.form, operand_index):
                if context.size == "l":
                    ext_words.extend(((sample.value >> 16) & 0xFFFF, sample.value & 0xFFFF))
                else:
                    ext_words.append(sample.value & 0xFFFF)
            operand_specs.append(ValueOperandSpec(kind="imm", value=sample.value))
        elif operand_kind == "label" and context.size == "w":
            if not _operand_has_bound_extension_patch(context.form, operand_index):
                ext_words.append(sample.displacement & 0xFFFF)
            operand_specs.append(ValueOperandSpec(kind="label", value=sample.displacement))
        elif operand_kind == "label":
            operand_specs.append(ValueOperandSpec(kind="label", value=sample.displacement))
        elif operand_kind == "sr":
            operand_specs.append(FixedNameOperandSpec(name="sr"))
        elif operand_kind == "usp":
            operand_specs.append(FixedNameOperandSpec(name="usp"))
    patch_values_tuple = tuple(patch_values)
    ext_words_tuple = tuple(ext_words)
    operand_specs_tuple = tuple(operand_specs)
    opword = context.form.opword_base & context.form.opword_mask
    bound_words = list(context.form.bound_word_bases[:context.form.bound_word_count])
    for patch, value in zip(context.form.patches, patch_values_tuple, strict=True):
        width = patch.bit_hi - patch.bit_lo + 1
        mask = (1 << width) - 1
        if patch.word_index == 0:
            opword |= (value & mask) << patch.bit_lo
        else:
            bound_words[patch.word_index - 1] |= (value & mask) << patch.bit_lo
    encoded = (
        _word(opword)
        + b"".join(_word(word) for word in bound_words)
        + b"".join(_word(word) for word in ext_words_tuple)
    )
    for trailing_spec in trailing_specs:
        trailing_form = next(
            form for form in forms
            if form.mnemonic.lower() == str(trailing_spec["mnemonic"]) and len(form.operand_kinds) == int(trailing_spec["operand_count"])
        )
        trailing_opword = trailing_form.opword_base & trailing_form.opword_mask
        encoded += _word(trailing_opword)
    return EncodedCase(
        patch_values=patch_values_tuple,
        ext_words=ext_words_tuple,
        operand_specs=operand_specs_tuple,
        trailing_specs=trailing_specs,
        encoded=encoded,
    )


def _asm_lines_for_case(context: FormContext, samples: tuple[object, ...]) -> tuple[str, ...]:
    if "label" in context.operand_kinds:
        label_sample = next(sample for operand_kind, sample in zip(context.operand_kinds, samples, strict=True) if operand_kind == "label")
        mnemonic = context.form.mnemonic.lower()
        explicit_syntax_size = "." in str(context.form.syntax).split()[0]
        size_variants = tuple(size for size in _sizes_for_mask(context.form.size_mask) if size is not None)
        operands = ",".join(
            "target" if operand_kind == "label" else sample.asm_text
            for operand_kind, sample in zip(context.operand_kinds, samples, strict=True)
        )
        if label_sample.size is None or (len(size_variants) <= 1 and not explicit_syntax_size):
            first_line = f"{mnemonic} {operands}".rstrip()
        else:
            first_line = f"{mnemonic}.{label_sample.size} {operands}".rstrip()
        return (first_line, *label_sample.post_lines)
    ea_post = next(
        (
            sample.post_lines
            for operand_kind, sample in zip(context.operand_kinds, samples, strict=True)
            if operand_kind == "ea" and sample.post_lines
        ),
        (),
    )
    operands = ",".join(sample.asm_text for sample in samples)
    mnemonic = context.form.mnemonic.lower()
    explicit_syntax_size = "." in str(context.form.syntax).split()[0]
    size_variants = tuple(size for size in _sizes_for_mask(context.form.size_mask) if size is not None)
    if context.size is None or (len(size_variants) <= 1 and not explicit_syntax_size):
        first_line = f"{mnemonic} {operands}".rstrip()
    else:
        first_line = f"{mnemonic}.{context.size} {operands}".rstrip()
    if ea_post:
        return (first_line, *ea_post)
    return (first_line,)


def _case_id(context: FormContext, samples: tuple[object, ...]) -> str:
    syntax_tag = (
        context.syntax.lower()
        .replace("#", "imm_")
        .replace("<", "")
        .replace(">", "")
        .replace(".", "_")
        .replace(",", "_")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .replace("+", "post")
        .replace("-", "neg")
    )
    parts = [context.form.mnemonic.lower(), syntax_tag]
    if context.size is not None:
        parts.append(context.size)
    for sample in samples:
        if isinstance(sample, ImmediateSample):
            imm_text = sample.asm_text.removeprefix("#").lower().replace("-", "neg")
            parts.append(f"imm_{imm_text}")
            continue
        if isinstance(sample, RegisterSample):
            parts.append(sample.asm_text.lower())
            continue
        if isinstance(sample, FixedOperandSample):
            parts.append(sample.asm_text.lower())
            continue
        if isinstance(sample, LabelSample):
            parts.append(f"label_{sample.size}_{sample.displacement:04x}")
            continue
        if isinstance(sample, ReglistSample):
            parts.append(sample.asm_text.lower().replace("/", "_").replace("-", "_"))
            continue
        if isinstance(sample, EASample):
            parts.append(f"ea_{sample.mode}_{sample.reg}")
            sample_text = sample.asm_text
        else:
            sample_text = sample.asm_text if hasattr(sample, "asm_text") else "sample"
        parts.append(
            sample_text.lower()
            .replace("#", "imm_")
            .replace("$", "abs_")
            .replace(".", "_")
            .replace("(", "")
            .replace(")", "")
            .replace(",", "_")
            .replace("+", "post")
            .replace("*", "x")
            .replace("-", "neg")
            .replace(":", "")
        )
    return "_".join(part for part in parts if part)


def generate_cases(target_cpu: str = "68000", require_oracle_cpu: bool = False) -> list[CorpusCase]:
    subset_module, forms, kb = _load_forms_and_kb()
    routed_immediates = subset_module._supported_immediate_routes(forms, KB_PATH)
    cases: list[CorpusCase] = []
    for form in forms:
        if not _form_supports_cpu(form, target_cpu):
            continue
        item = _mnemonic_item(kb, form.kb_mnemonic)
        form_source = _raw_form_for_generated_form(kb, item, form)
        if require_oracle_cpu and not _instruction_has_oracle_cpu(item, form_source, target_cpu):
            continue
        operand_roles = _operand_roles(kb, item, form.sampling_operand_kinds)
        for size in _sizes_for_target_form(form, target_cpu):
            context = FormContext(
                form=form,
                size=size,
                syntax=form.syntax,
                operand_kinds=form.sampling_operand_kinds,
                operand_roles=operand_roles,
                target_cpu=target_cpu,
                form_source=form_source,
            )
            options = _sample_options(context, item, kb, forms, subset_module)
            if any(not choice for choice in options) and "reglist" not in context.operand_kinds:
                continue
            for base_samples in itertools.product(*options):
                for samples in _expand_reglist_options(context, base_samples, kb):
                    asm_lines = _asm_lines_for_case(context, samples)
                    encoded_case = _build_case_encoding(context, item, samples, forms, kb)
                    semantic_mnemonic = context.form.mnemonic
                    if any(isinstance(sample, ImmediateSample) for sample in samples):
                        semantic_mnemonic = routed_immediates.get(semantic_mnemonic, semantic_mnemonic)
                    instruction_specs = (
                        _instruction_spec(
                            mnemonic=semantic_mnemonic,
                            size_suffix=context.size,
                            operand_count=len(context.operand_kinds),
                            patch_values=encoded_case.patch_values,
                            operand_specs=encoded_case.operand_specs,
                        ),
                        *encoded_case.trailing_specs,
                    )
                    cases.append(
                        CorpusCase(
                            case_id=_case_id(context, samples),
                            mnemonic=form.mnemonic,
                            asm_lines=asm_lines,
                            expected_hex=encoded_case.encoded.hex(),
                            instruction_specs=instruction_specs,
                        )
                    )
    return cases


def generate_sample_coverage(target_cpu: str = "68000", require_oracle_cpu: bool = False) -> list[SampleCoverageEntry]:
    subset_module, forms, kb = _load_forms_and_kb()
    entries: list[SampleCoverageEntry] = []
    for form in forms:
        item = _mnemonic_item(kb, form.kb_mnemonic)
        form_source = _raw_form_for_generated_form(kb, item, form)
        operand_roles = _operand_roles(kb, item, form.sampling_operand_kinds)
        if not _form_supports_cpu(form, target_cpu):
            entries.append(SampleCoverageEntry(
                mnemonic=str(form.mnemonic),
                kb_mnemonic=str(form.kb_mnemonic),
                local_form_index=int(form.local_form_index),
                form_index=int(form.form_index),
                syntax=str(form.syntax),
                size=None,
                target_cpu=target_cpu,
                status=SAMPLE_STATUS_NOT_TARGET_CPU,
                reason=f"form does not support {target_cpu}",
            ))
            continue
        if require_oracle_cpu and not _instruction_has_oracle_cpu(item, form_source, target_cpu):
            entries.append(SampleCoverageEntry(
                mnemonic=str(form.mnemonic),
                kb_mnemonic=str(form.kb_mnemonic),
                local_form_index=int(form.local_form_index),
                form_index=int(form.form_index),
                syntax=str(form.syntax),
                size=None,
                target_cpu=target_cpu,
                status=SAMPLE_STATUS_ORACLE_UNAVAILABLE,
                reason=f"oracle unavailable for {target_cpu}",
            ))
            continue
        for size in _sizes_for_target_form(form, target_cpu):
            context = FormContext(
                form=form,
                size=size,
                syntax=form.syntax,
                operand_kinds=form.sampling_operand_kinds,
                operand_roles=operand_roles,
                target_cpu=target_cpu,
                form_source=form_source,
            )
            options = _sample_options(context, item, kb, forms, subset_module)
            entries.append(_sample_status_for_options(context, options))
    return entries


def generate_full_ext_cases() -> list[CorpusCase]:
    _, forms, kb = _load_forms_and_kb()
    item = _mnemonic_item(kb, "LEA")
    form = next(form for form in forms if form.mnemonic == "LEA")
    bd_sizes = _full_ext_bd_sizes(kb)
    cases: list[CorpusCase] = []
    samples = (
        {
            "case_id": "lea_l_full_index_null",
            "asm_lines": ("lea.l $10(a0,d1.w){full},a0",),
            "operand_spec": EaOperandSpec(
                mode=6,
                reg=0,
                value=0x10,
                index_is_address=0,
                index_reg=1,
                index_long=0,
                scale=0,
                full_ext_base_disp_size=bd_sizes["word"],
                full_ext_base_disp_value=0x10,
            ),
            "ea_sample": EASample(
                asm_text="",
                mode=6,
                reg=0,
                value=0x10,
                index_is_address=0,
                index_reg=1,
                index_long=0,
                scale=0,
                full_ext_base_disp_size=bd_sizes["word"],
                full_ext_base_disp_value=0x10,
            ),
        },
        {
            "case_id": "lea_l_full_index_bdw_odw",
            "asm_lines": ("lea.l $10(a0,d1.w){full,bdw=$1234,odw=$5678,iis=3},a0",),
            "operand_spec": EaOperandSpec(
                mode=6,
                reg=0,
                value=0x10,
                index_is_address=0,
                index_reg=1,
                index_long=0,
                scale=0,
                full_ext_base_disp_size=bd_sizes["word"],
                full_ext_outer_disp_size=bd_sizes["word"],
                full_ext_iis=3,
                full_ext_base_disp_value=0x1234,
                full_ext_outer_disp_value=0x5678,
            ),
            "ea_sample": EASample(
                asm_text="",
                mode=6,
                reg=0,
                value=0x10,
                index_is_address=0,
                index_reg=1,
                index_long=0,
                scale=0,
                full_ext_base_disp_size=bd_sizes["word"],
                full_ext_outer_disp_size=bd_sizes["word"],
                full_ext_iis=3,
                full_ext_base_disp_value=0x1234,
                full_ext_outer_disp_value=0x5678,
            ),
        },
    )
    for sample in samples:
        context = FormContext(
            form=form,
            size="l",
            syntax=form.syntax,
            operand_kinds=form.sampling_operand_kinds,
            operand_roles=_operand_roles(kb, item, form.sampling_operand_kinds),
            target_cpu="68020",
        )
        patch_values = (0, 6, 0)
        encoded_case = _build_case_encoding(
            context,
            item,
            (sample["ea_sample"], RegisterSample(asm_text="a0", reg=0)),
            forms,
            kb,
        )
        assert encoded_case.patch_values == patch_values
        assert encoded_case.trailing_specs == ()
        instruction_specs = (
            _instruction_spec(
                mnemonic="lea",
                size_suffix="",
                operand_count=2,
                patch_values=patch_values,
                operand_specs=(sample["operand_spec"], RegisterOperandSpec(kind="an", reg=0)),
            ),
        )
        cases.append(
            CorpusCase(
                case_id=str(sample["case_id"]),
                mnemonic="LEA",
                asm_lines=tuple(sample["asm_lines"]),
                expected_hex=encoded_case.encoded.hex(),
                instruction_specs=instruction_specs,
            )
        )
    return cases


def write_corpus(output_dir: Path = DEFAULT_OUTPUT_DIR) -> tuple[Path, Path, Path | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_cases = generate_cases("68000", require_oracle_cpu=True)
    cases: list[CorpusCase] = []
    offset = 0
    for case in raw_cases:
        size = len(bytes.fromhex(case.expected_hex))
        cases.append(
            CorpusCase(
                case_id=case.case_id,
                mnemonic=case.mnemonic,
                asm_lines=case.asm_lines,
                expected_hex=case.expected_hex,
                instruction_specs=case.instruction_specs,
                offset=offset,
                size=size,
            )
        )
        offset += size
    source_lines = ["; Auto-generated by src/scripts/generate_c99_assembler_corpus.py"]
    for case in cases:
        case_label = f"case_{case.case_id}"
        target_label = f"{case_label}_target"
        source_lines.append(f"{case_label}:")
        for line in case.asm_lines:
            rewritten = (
                line
                .replace("target:", f"{target_label}:")
                .replace(",target", f",{target_label}")
                .replace(" target", f" {target_label}")
            )
            source_lines.append(f"    {rewritten}" if not rewritten.endswith(":") else rewritten)
    source_text = "\n".join(source_lines) + "\n"
    manifest_text = json.dumps([asdict(case) for case in cases], indent=2) + "\n"
    text_manifest = _text_manifest(cases)
    source_path = output_dir / "all_cases.s"
    manifest_path = output_dir / "all_cases.json"
    text_manifest_path = output_dir / "all_cases.txt"
    binary_path = output_dir / "all_cases.bin"
    source_path.write_text(source_text, encoding="utf-8", newline="\n")
    manifest_path.write_text(manifest_text, encoding="utf-8", newline="\n")
    text_manifest_path.write_text(text_manifest, encoding="utf-8", newline="\n")
    if VASM.exists():
        cpu_cases = {
            "68020": generate_cases("68020"),
            "68040": generate_cases("68040"),
            "68060": generate_cases("68060"),
        }
        result = subprocess.run(
            [
                str(VASM),
                "-Fbin",
                "-no-opt",
                "-quiet",
                "-m68000",
                "-o",
                str(binary_path),
                str(source_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"vasm failed generating corpus: {result.stderr}")
        internal_cases = generate_full_ext_cases()
        (output_dir / "full_ext_cases.txt").write_text(_text_manifest(internal_cases), encoding="utf-8", newline="\n")
        for cpu_name, cpu_cases_list in cpu_cases.items():
            (output_dir / f"all_cases_{cpu_name}.txt").write_text(
                _text_manifest(cpu_cases_list),
                encoding="utf-8",
                newline="\n",
            )
            (output_dir / f"all_cases_{cpu_name}.json").write_text(
                json.dumps([asdict(case) for case in cpu_cases_list], indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        return source_path, manifest_path, binary_path
    return source_path, manifest_path, None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    write_corpus(args.output_dir)


if __name__ == "__main__":
    main()
