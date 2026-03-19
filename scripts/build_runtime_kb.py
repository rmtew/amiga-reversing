"""Build runtime-oriented knowledge artifacts from canonical JSON KB files."""

from __future__ import annotations

import argparse
import json
import pprint
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"


def _load_json(name: str) -> dict:
    with open(KNOWLEDGE_DIR / name, encoding="utf-8") as handle:
        return json.load(handle)


def _write_python(path: Path, variable: str, payload: object, *, header: str) -> None:
    rendered = pprint.pformat(payload, width=100, sort_dicts=False)
    text = (
        '"""' + header + '"""\n\n'
        f"{variable} = {rendered}\n"
    )
    path.write_text(text, encoding="utf-8")


def _iter_mnemonic_tokens(text: str):
    start = None
    for i, ch in enumerate(text):
        if ch.isspace() or ch == ",":
            if start is not None:
                yield text[start:i]
                start = None
            continue
        if start is None:
            start = i
    if start is not None:
        yield text[start:]


def _derive_varying_bits(mask_val_pairs: list[tuple[int, int]]) -> tuple[int, int]:
    if len(mask_val_pairs) < 2:
        raise RuntimeError("need at least 2 mask/val pairs to derive varying bits")
    varying = 0
    base_val = mask_val_pairs[0][1]
    for _, val in mask_val_pairs[1:]:
        varying |= base_val ^ val
    for i in range(len(mask_val_pairs)):
        for j in range(i + 1, len(mask_val_pairs)):
            varying |= mask_val_pairs[i][1] ^ mask_val_pairs[j][1]
    if varying == 0:
        raise RuntimeError("all vals are identical")
    bit_lo = (varying & -varying).bit_length() - 1
    bit_hi = varying.bit_length() - 1
    return bit_hi, bit_lo


def _runtime_size_encodings(inst: dict) -> tuple[dict[str, int], dict[int, int]]:
    size_desc = inst.get("field_descriptions", {}).get("Size", "")
    requires_size_encoding = bool(
        re.search(r"\bByte\b|\bWord\b|\bLong\b", size_desc)
    ) or inst["mnemonic"] in {"DIVS, DIVSL", "DIVU, DIVUL", "MULS", "MULU"}

    if "size_encoding" not in inst:
        if requires_size_encoding:
            raise KeyError(f"{inst['mnemonic']}: missing required size_encoding")
        return {}, {}

    size_encoding = inst["size_encoding"]
    if size_encoding["field"] != "SIZE":
        raise ValueError(
            f"{inst['mnemonic']}: size_encoding.field must be 'SIZE', got {size_encoding['field']!r}"
        )

    size_name_to_const = {"b": 0, "w": 1, "l": 2}
    asm_map = {}
    disasm_map = {}
    for entry in size_encoding["values"]:
        size = entry["size"]
        bits = entry["bits"]
        if size in asm_map:
            raise ValueError(f"{inst['mnemonic']}: duplicate size {size!r} in size_encoding")
        if bits in disasm_map:
            raise ValueError(f"{inst['mnemonic']}: duplicate SIZE bits {bits!r} in size_encoding")
        asm_map[size] = bits
        disasm_map[bits] = size_name_to_const[size]
    if not asm_map:
        raise ValueError(f"{inst['mnemonic']}: size_encoding.values must not be empty")
    return asm_map, disasm_map


def _build_m68k_runtime() -> dict:
    payload = _load_json("m68k_instructions.json")
    instructions = payload["instructions"]
    meta = payload["_meta"]
    by_name = {inst["mnemonic"]: inst for inst in instructions}

    mnemonic_index: dict[str, tuple[str, ...]] = {}
    for inst in instructions:
        lowered = inst["mnemonic"].lower()
        keys = {lowered, lowered.partition(" ")[0]}
        keys.update(_iter_mnemonic_tokens(lowered))
        for key in sorted(keys):
            mnemonic_index.setdefault(key, [])
            mnemonic_index[key].append(inst["mnemonic"])
    mnemonic_index = {
        key: tuple(values)
        for key, values in sorted(mnemonic_index.items())
    }

    encoding_masks_by_idx: list[dict[str, tuple[int, int]]] = []
    field_maps_by_idx: list[dict[str, dict[str, tuple[int, int, int]]]] = []
    raw_fields_by_idx: list[dict[str, tuple[tuple[str, int, int, int], ...]]] = []
    for enc_idx in range(3):
        masks: dict[str, tuple[int, int]] = {}
        field_maps: dict[str, dict[str, tuple[int, int, int]]] = {}
        raw_fields: dict[str, tuple[tuple[str, int, int, int], ...]] = {}
        for inst in instructions:
            encodings = inst.get("encodings", [])
            if len(encodings) <= enc_idx:
                continue
            mask = val = 0
            fields_map: dict[str, tuple[int, int, int]] = {}
            raw_fields_list = []
            for field in encodings[enc_idx]["fields"]:
                name = field["name"]
                if name in ("0", "1"):
                    bit = 1 if name == "1" else 0
                    for bit_index in range(field["bit_lo"], field["bit_hi"] + 1):
                        mask |= (1 << bit_index)
                        val |= (bit << bit_index)
                    continue
                spec = (field["bit_hi"], field["bit_lo"], field["width"])
                fields_map[name] = spec
                raw_fields_list.append((name, field["bit_hi"], field["bit_lo"], field["width"]))
            if mask:
                masks[inst["mnemonic"]] = (mask, val)
            if fields_map:
                field_maps[inst["mnemonic"]] = fields_map
            if raw_fields_list:
                raw_fields[inst["mnemonic"]] = tuple(raw_fields_list)
        encoding_masks_by_idx.append(dict(sorted(masks.items())))
        field_maps_by_idx.append(dict(sorted(field_maps.items())))
        raw_fields_by_idx.append(dict(sorted(raw_fields.items())))

    fixed_opcodes = {
        val: mnemonic
        for mnemonic, (mask, val) in encoding_masks_by_idx[0].items()
        if mask == 0xFFFF
    }

    ext_field_names = {
        mnemonic: tuple(sorted(field_map))
        for mnemonic, field_map in field_maps_by_idx[1].items()
    }

    ea_brief_fields = {
        field["name"]: (field["bit_hi"], field["bit_lo"], field["bit_hi"] - field["bit_lo"] + 1)
        for field in meta["ea_brief_ext_word"]
    }

    size_encodings_asm = {}
    size_encodings_disasm = {}
    for inst in instructions:
        asm_map, disasm_map = _runtime_size_encodings(inst)
        if asm_map:
            size_encodings_asm[inst["mnemonic"]] = asm_map
            size_encodings_disasm[inst["mnemonic"]] = disasm_map

    cc_index = {name: index for index, name in enumerate(meta["condition_codes"])}
    cc_families = {}
    for inst in instructions:
        cc_param = inst.get("constraints", {}).get("cc_parameterized")
        if cc_param:
            cc_families[cc_param["prefix"]] = (inst["mnemonic"], cc_param)

    immediate_ranges = {
        inst["mnemonic"]: inst["constraints"]["immediate_range"]
        for inst in instructions
        if inst.get("constraints", {}).get("immediate_range")
    }

    opmode_tables_list = {
        inst["mnemonic"]: inst["constraints"]["opmode_table"]
        for inst in instructions
        if inst.get("constraints", {}).get("opmode_table")
    }
    opmode_tables_by_value = {
        mnemonic: {entry["opmode"]: entry for entry in table}
        for mnemonic, table in opmode_tables_list.items()
    }

    pmmu_codes = tuple(code.lower() for code in meta["pmmu_condition_codes"])
    cpu_codes = set(meta["cc_test_definitions"])
    cpu_codes.update(meta["cc_aliases"])
    derived_cc_families = {}
    for inst in instructions:
        cc_param = inst.get("constraints", {}).get("cc_parameterized")
        is_pmmu = "68851" in inst.get("processors", "")
        codes = pmmu_codes if is_pmmu else tuple(sorted(cpu_codes))
        if cc_param:
            derived_cc_families[cc_param["prefix"].lower()] = {
                "mnemonic": inst["mnemonic"],
                "codes": tuple(codes),
                "numeric_suffix": is_pmmu,
            }
            continue
        for raw_name in inst["mnemonic"].split(","):
            name = raw_name.strip()
            if not name.endswith("cc"):
                continue
            prefix = name[:-2].lower()
            if not prefix or prefix in derived_cc_families:
                continue
            derived_cc_families[prefix] = {
                "mnemonic": name,
                "codes": tuple(codes),
                "numeric_suffix": is_pmmu,
            }

    asm_mnemonic_index = {}
    for syntax_key, kb_mnemonic in meta["asm_syntax_index"].items():
        asm_mnemonic, _, operand_types = syntax_key.partition(":")
        if operand_types:
            continue
        existing = asm_mnemonic_index.get(asm_mnemonic)
        if existing is not None and existing != kb_mnemonic:
            raise ValueError(f"duplicate bare mnemonic mapping for {asm_mnemonic!r}")
        if kb_mnemonic not in by_name:
            raise ValueError(f"asm_syntax_index maps {asm_mnemonic!r} to missing {kb_mnemonic!r}")
        asm_mnemonic_index[asm_mnemonic] = kb_mnemonic

    reg_masks = meta["movem_reg_masks"]["normal"]
    data_regs = [reg for reg in reg_masks if reg.startswith("d")]
    addr_regs = [reg for reg in reg_masks if reg.startswith("a")]
    if not addr_regs:
        raise KeyError("KB movem_reg_masks has no address registers")
    derived_meta = {
        "_cc_families": dict(sorted(derived_cc_families.items())),
        "_asm_mnemonic_index": dict(sorted(asm_mnemonic_index.items())),
        "_num_data_regs": len(data_regs),
        "_num_addr_regs": len(addr_regs),
        "_sp_reg_num": int(addr_regs[-1][1:]),
    }

    dest_reg_field = {}
    for mnemonic, fields in raw_fields_by_idx[0].items():
        reg_fields = [(name, hi, lo, width) for name, hi, lo, width in fields if name == "REGISTER"]
        if len(reg_fields) >= 2:
            upper = max(reg_fields, key=lambda item: item[1])
            dest_reg_field[mnemonic] = (upper[1], upper[2], upper[3])
        elif len(reg_fields) == 1 and reg_fields[0][1] >= 9:
            dest_reg_field[mnemonic] = (reg_fields[0][1], reg_fields[0][2], reg_fields[0][3])

    bf_mnemonics = tuple(sorted(mn for mn in encoding_masks_by_idx[0] if mn.startswith("BF")))

    def _derive_name_table(mnemonics: tuple[str, ...], names: tuple[str, ...], enc_idx: int = 0):
        pairs = [encoding_masks_by_idx[enc_idx][mn] for mn in mnemonics]
        hi, lo = _derive_varying_bits(pairs)
        width = hi - lo + 1
        table = {}
        for mnemonic, label in zip(mnemonics, names):
            _, val = encoding_masks_by_idx[enc_idx][mnemonic]
            table[(val >> lo) & ((1 << width) - 1)] = label
        return table, (hi, lo, width)

    bitop_names, bitop_field = _derive_name_table(
        ("BTST", "BCHG", "BCLR", "BSET"),
        ("btst", "bchg", "bclr", "bset"),
    )
    imm_names, imm_field = _derive_name_table(
        ("ORI", "ANDI", "SUBI", "ADDI", "EORI", "CMPI"),
        ("ori", "andi", "subi", "addi", "eori", "cmpi"),
    )
    shift_names, _ = _derive_name_table(
        ("ASL, ASR", "LSL, LSR", "ROXL, ROXR", "ROL, ROR"),
        ("as", "ls", "rox", "ro"),
    )
    reg_shift_field = _derive_varying_bits([encoding_masks_by_idx[0][mn] for mn in ("ASL, ASR", "LSL, LSR", "ROXL, ROXR", "ROL, ROR")])
    mem_shift_field = _derive_varying_bits([encoding_masks_by_idx[1][mn] for mn in ("ASL, ASR", "LSL, LSR", "ROXL, ROXR", "ROL, ROR")])
    shift_type_fields = (
        (reg_shift_field[0], reg_shift_field[1], reg_shift_field[0] - reg_shift_field[1] + 1),
        (mem_shift_field[0], mem_shift_field[1], mem_shift_field[0] - mem_shift_field[1] + 1),
    )

    shift_fields = None
    for inst in instructions:
        if inst["mnemonic"].startswith("ASL"):
            dv = inst["constraints"]["direction_variants"]
            shift_fields = {
                "dr_values": {int(key): value for key, value in dv["values"].items()},
                "zero_means": inst["constraints"]["immediate_range"]["zero_means"],
            }
            break
    if shift_fields is None:
        raise RuntimeError("KB missing ASL/ASR")

    rm_field = {}
    for inst in instructions:
        operand_modes = inst.get("constraints", {}).get("operand_modes")
        if not operand_modes or operand_modes.get("field") != "R/M":
            continue
        field = field_maps_by_idx[0].get(inst["mnemonic"], {}).get("R/M")
        if field:
            rm_field[inst["mnemonic"]] = (field[0], {int(key): value for key, value in operand_modes["values"].items()})

    addq_zero_means = immediate_ranges["ADDQ"]["zero_means"]
    control_registers = {}
    for control in by_name["MOVEC"]["constraints"]["control_registers"]:
        hex_value = int(control["hex"], 16)
        control_registers.setdefault(hex_value, control["abbrev"])

    processor_mins = {}
    for inst in instructions:
        min_cpu = inst["processor_min"]
        for part in inst["mnemonic"].split(","):
            tokens = part.strip().split()
            for token in tokens:
                processor_mins[token.lower()] = min_cpu[2:] if min_cpu.startswith("-m") else min_cpu

    condition_families = tuple(
        {
            "prefix": entry["prefix"],
            "canonical": entry["canonical"],
            "codes": tuple(entry["codes"]),
            "match_numeric_suffix": entry["match_numeric_suffix"],
            "exclude_from_family": tuple(entry["exclude_from_family"]),
        }
        for entry in meta["condition_families"]
    )

    move_raw = raw_fields_by_idx[0]["MOVE"]
    move_modes = sorted([(hi, lo, width) for name, hi, lo, width in move_raw if name == "MODE"], reverse=True)
    move_regs = sorted([(hi, lo, width) for name, hi, lo, width in move_raw if name == "REGISTER"], reverse=True)
    move_fields = (move_regs[0], move_modes[0], move_modes[1], move_regs[1])

    frestore = by_name["FRESTORE"]
    id_field = next(field for field in frestore["encodings"][0]["fields"] if field["name"] == "ID")
    cpid_field = (id_field["bit_lo"], id_field["width"])

    ea_modes = set(meta["ea_mode_encoding"].keys())
    generic_types = ea_modes | {"ea", "imm", "label", "reglist", "ctrl_reg",
                                "rn", "bf_ea", "unknown", "dn_pair",
                                "disp", "postinc", "predec"}
    asm_syntax_index = {}
    all_types = set()
    for key, kb_mnemonic in sorted(meta["asm_syntax_index"].items()):
        mnemonic, _, raw_operand_types = key.partition(":")
        operand_types = tuple(raw_operand_types.split(",")) if raw_operand_types else ()
        asm_syntax_index[(mnemonic, operand_types)] = kb_mnemonic
        all_types.update(operand_types)
    special_operand_types = tuple(sorted(all_types - generic_types))

    return {
        "derived_meta": derived_meta,
        "tables": {
            "mnemonic_index": mnemonic_index,
            "encoding_masks": tuple(encoding_masks_by_idx),
            "fixed_opcodes": dict(sorted(fixed_opcodes.items())),
            "ext_field_names": dict(sorted(ext_field_names.items())),
            "field_maps": tuple(field_maps_by_idx),
            "raw_fields": tuple(raw_fields_by_idx),
            "ea_brief_fields": ea_brief_fields,
            "size_encodings_asm": dict(sorted(size_encodings_asm.items())),
            "size_encodings_disasm": dict(sorted(size_encodings_disasm.items())),
            "cc_index": cc_index,
            "cc_families": dict(sorted(cc_families.items())),
            "immediate_ranges": dict(sorted(immediate_ranges.items())),
            "opmode_tables_list": dict(sorted(opmode_tables_list.items())),
            "opmode_tables_by_value": dict(sorted(opmode_tables_by_value.items())),
            "dest_reg_field": dict(sorted(dest_reg_field.items())),
            "bf_mnemonics": bf_mnemonics,
            "bitop_names": (dict(sorted(bitop_names.items())), bitop_field),
            "imm_names": (dict(sorted(imm_names.items())), imm_field),
            "shift_names": dict(sorted(shift_names.items())),
            "shift_type_fields": shift_type_fields,
            "shift_fields": shift_fields,
            "rm_field": dict(sorted(rm_field.items())),
            "addq_zero_means": addq_zero_means,
            "control_registers": dict(sorted(control_registers.items())),
            "processor_mins": dict(sorted(processor_mins.items())),
            "condition_families": tuple(condition_families),
            "move_fields": move_fields,
            "cpid_field": cpid_field,
            "asm_syntax_index": asm_syntax_index,
            "special_operand_types": special_operand_types,
        },
    }


def _build_os_runtime() -> dict:
    canonical = _load_json("amiga_os_reference.json")
    runtime = {
        "_meta": {
            "calling_convention": canonical["_meta"]["calling_convention"],
            "exec_base_addr": canonical["_meta"]["exec_base_addr"],
            "lvo_slot_size": canonical["_meta"]["lvo_slot_size"],
            "constant_domains": canonical["_meta"]["constant_domains"],
        },
        "structs": canonical["structs"],
        "constants": canonical["constants"],
        "libraries": {},
    }
    for library_name, library_data in sorted(canonical["libraries"].items()):
        funcs = {}
        for func_name, func_data in sorted(library_data["functions"].items()):
            compact = {}
            for key in ("returns_base", "returns_memory", "output", "no_return", "inputs"):
                if key in func_data:
                    compact[key] = func_data[key]
            funcs[func_name] = compact
        runtime["libraries"][library_name] = {
            "lvo_index": library_data["lvo_index"],
            "functions": funcs,
        }
    return runtime


def _build_passthrough(name: str) -> dict:
    return _load_json(name)


def build_runtime_artifacts() -> list[Path]:
    outputs = []
    outputs.append(KNOWLEDGE_DIR / "runtime_m68k.py")
    _write_python(outputs[-1], "RUNTIME", _build_m68k_runtime(),
                  header="Generated runtime M68K knowledge artifact. Do not edit directly.")
    outputs.append(KNOWLEDGE_DIR / "runtime_os.py")
    _write_python(outputs[-1], "RUNTIME", _build_os_runtime(),
                  header="Generated runtime Amiga OS knowledge artifact. Do not edit directly.")
    outputs.append(KNOWLEDGE_DIR / "runtime_hunk.py")
    _write_python(outputs[-1], "RUNTIME", _build_passthrough("amiga_hunk_format.json"),
                  header="Generated runtime hunk knowledge artifact. Do not edit directly.")
    outputs.append(KNOWLEDGE_DIR / "runtime_naming.py")
    _write_python(outputs[-1], "RUNTIME", _build_passthrough("naming_rules.json"),
                  header="Generated runtime naming knowledge artifact. Do not edit directly.")
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build runtime knowledge artifacts from canonical JSON")
    parser.parse_args()
    outputs = build_runtime_artifacts()
    for output in outputs:
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
