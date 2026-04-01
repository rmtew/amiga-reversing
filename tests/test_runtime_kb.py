from __future__ import annotations

import ast
import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest
from _pytest.monkeypatch import MonkeyPatch

from disasm.assembler_profiles import load_assembler_profile
from kb import runtime_builder
from kb.ndk_parser import parse_fd_file
from kb.os_reference import (
    merge_os_reference_payloads,
    normalize_os_reference_corrections,
)
from m68k import m68k_asm
from m68k.os_structs import resolve_struct_field
from scripts.oracle_m68k_asm import ORACLE_MAP, PROJ_ROOT, VamosDriver
from tests.runtime_kb_helpers import (
    RUNTIME_PY,
    load_canonical_hardware_reference,
    load_canonical_hardware_symbols,
    load_canonical_hunk_kb,
    load_canonical_m68k_kb,
    load_canonical_naming_rules,
    load_canonical_os_kb,
    load_canonical_os_kb_corrections,
    load_canonical_os_kb_includes_parsed,
    load_canonical_os_kb_other_parsed,
    load_hardware_runtime_kb,
    load_hunk_runtime_kb,
    load_m68k_analysis_runtime_module,
    load_m68k_asm_runtime_module,
    load_m68k_compute_runtime_module,
    load_m68k_decode_runtime_module,
    load_m68k_executor_runtime_module,
    load_m68k_runtime_module,
    load_naming_runtime_kb,
    load_os_runtime_kb,
)


def test_production_modules_import_generated_runtime_modules_directly() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    for path in list((repo_root / "m68k").glob("*.py")) + list((repo_root / "disasm").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "runtime_kb":
                raise AssertionError(f"{path} still imports runtime_kb relatively")
            if isinstance(node, ast.ImportFrom) and node.module == "m68k.runtime_kb":
                raise AssertionError(f"{path} still imports m68k.runtime_kb")


def test_production_modules_do_not_read_canonical_instruction_bag_fields() -> None:
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


def test_source_modules_use_ascii_only_text() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    for path in (
        list((repo_root / "m68k").glob("*.py"))
        + list((repo_root / "disasm").glob("*.py"))
        + list((repo_root / "tests").glob("*.py"))
    ):
        text = path.read_text(encoding="utf-8")
        if any(ord(ch) > 127 for ch in text):
            raise AssertionError(f"{path} contains non-ASCII source text")


def test_assembler_profiles_load_from_kb() -> None:
    vasm = load_assembler_profile("vasm")
    devpac = load_assembler_profile("devpac")

    assert vasm.render.header_generated_syntax == "vasm Motorola syntax"
    assert vasm.render.directives.section == "section"
    assert vasm.render.current_location_token == "*"
    assert vasm.render.omit_zero_pc_index_displacement is False
    assert vasm.render.auto_align_dc_w is False
    assert vasm.render.auto_align_dc_l is False
    assert vasm.local_include_root is None
    assert vasm.output_file_option == "-o <filename>"
    assert devpac.render.header_generated_syntax == "GenAm Motorola syntax"
    assert devpac.render.directives.section == "SECTION"
    assert devpac.render.current_location_token == "*"
    assert devpac.render.omit_zero_pc_index_displacement is False
    assert devpac.render.require_label_anchor_for_self_relative_data is True
    assert devpac.render.auto_align_dc_w is True
    assert devpac.render.auto_align_dc_l is True
    assert devpac.local_include_root == "ext/amiga_includes/ndk_2.0/include"
    assert devpac.output_file_option == "TO <filename>"


def test_vendored_amiga_includes_are_lf_only() -> None:
    root = Path("ext/amiga_includes")
    for path in root.rglob("*"):
        if path.is_file():
            assert b"\r\n" not in path.read_bytes(), str(path)


def test_devpac_oracle_driver_stages_local_includes_and_passes_incdir(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    oracle_cfg = json.loads(ORACLE_MAP["devpac"].read_text(encoding="utf-8"))
    monkeypatch.setenv("TEMP", str(tmp_path))
    recorded: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        recorded.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    driver = VamosDriver(oracle_cfg, PROJ_ROOT)
    driver.setup()
    try:
        assert driver._include_arg is not None
        staged = tmp_path / driver._include_arg.removeprefix("TMP:").rstrip("/\\")
        assert staged.is_dir()
        assert (staged / "exec" / "types.i").is_file()

        src = tmp_path / "probe.s"
        out = tmp_path / "probe.o"
        src.write_text(" dc.b 0\n", encoding="latin-1")
        driver._run_vamos(str(src), str(out))

        assert recorded
        cmd = recorded[-1]
        assert cmd[-2:] == ["INCDIR", driver._include_arg]
    finally:
        driver.teardown()


def test_runtime_kb_generation_is_deterministic() -> None:
    script = Path(__file__).resolve().parent.parent / "scripts" / "build_runtime_kb.py"
    targets = [
        RUNTIME_PY / "runtime_m68k.py",
        RUNTIME_PY / "runtime_m68k_decode.py",
        RUNTIME_PY / "runtime_m68k_disasm.py",
        RUNTIME_PY / "runtime_m68k_asm.py",
        RUNTIME_PY / "runtime_m68k_analysis.py",
        RUNTIME_PY / "runtime_m68k_compute.py",
        RUNTIME_PY / "runtime_m68k_executor.py",
        RUNTIME_PY / "runtime_os.py",
        RUNTIME_PY / "runtime_hunk.py",
        RUNTIME_PY / "runtime_naming.py",
        RUNTIME_PY / "runtime_hardware.py",
    ]
    before = {path: path.read_bytes() for path in targets}
    subprocess.run([sys.executable, str(script)], check=True)
    middle = {path: path.read_bytes() for path in targets}
    subprocess.run([sys.executable, str(script)], check=True)
    after = {path: path.read_bytes() for path in targets}
    assert before == middle == after


def test_canonical_os_kb_is_strict_merge_of_parsed_and_extensions() -> None:
    includes = load_canonical_os_kb_includes_parsed()
    other = load_canonical_os_kb_other_parsed()
    corrections = load_canonical_os_kb_corrections()
    merged = load_canonical_os_kb()

    assert merge_os_reference_payloads(
        includes=includes,
        other=other,
        corrections=corrections,
    ) == merged


def test_includes_parsed_os_kb_inlines_constant_availability() -> None:
    includes = load_canonical_os_kb_includes_parsed()

    assert "function_min_versions" not in includes["_meta"]
    assert "constant_min_versions" not in includes["_meta"]
    constant = includes["constants"]["A2024FIFTEENHERTZ_KEY"]
    assert constant["available_since"] == "2.0"
    func = includes["libraries"]["amigaguide.library"]["functions"]["AddAmigaGuideHostA"]
    assert "available_since" not in func


def test_other_parsed_os_kb_owns_function_availability() -> None:
    other = load_canonical_os_kb_other_parsed()

    func = other["functions"]["amigaguide.library"]["AddAmigaGuideHostA"]
    assert func["available_since"] == "3.1"


def test_os_reference_corrections_only_carry_correction_data() -> None:
    corrections = normalize_os_reference_corrections(load_canonical_os_kb_corrections())

    assert set(corrections) == {"_meta"}
    assert corrections["_meta"]["api_input_value_bindings"]
    assert set(corrections["_meta"]) == {
        "calling_convention",
        "exec_base_addr",
        "absolute_symbols",
        "value_domains",
        "api_input_value_bindings",
        "api_input_type_overrides",
        "api_input_semantic_assertions",
        "struct_field_value_bindings",
    }


def test_runtime_os_meta_has_named_base_structs() -> None:
    os_kb = load_os_runtime_kb()

    assert os_kb.META.named_base_structs["dos.library"] == "DosLibrary"
    assert os_kb.META.named_base_structs["graphics.library"] == "GfxBase"
    assert os_kb.META.named_base_structs["intuition.library"] == "IntuitionBase"
    assert os_kb.META.named_base_structs["locale.library"] == "LocaleBase"
    assert os_kb.META.named_base_structs["realtime.library"] == "RealTimeBase"
    assert os_kb.META.named_base_structs["utility.library"] == "UtilityBase"
    assert os_kb.META.named_base_structs["expansion.library"] == "ExpansionBase"


def test_runtime_os_input_semantic_kinds_cover_callback_cases() -> None:
    os_kb = load_os_runtime_kb()

    assert os_kb.META.calling_convention.seed_origin == "primary_doc"
    assert os_kb.META.calling_convention.review_status == "seeded"
    assert os_kb.META.exec_base_addr.seed_origin == "primary_doc"
    assert os_kb.META.exec_base_addr.review_status == "seeded"
    assert os_kb.META.absolute_symbols[0].seed_origin == "primary_doc"
    assert os_kb.META.absolute_symbols[0].review_status == "seeded"
    assert os_kb.LIBRARIES["graphics.library"].functions["SetCollision"].inputs[1].semantic_kind == "code_ptr"
    assert os_kb.LIBRARIES["exec.library"].functions["AddTask"].inputs[1].semantic_kind == "code_ptr"
    assert os_kb.LIBRARIES["exec.library"].functions["AddTask"].inputs[2].semantic_kind == "code_ptr"
    assert os_kb.LIBRARIES["exec.library"].functions["ObtainQuickVector"].inputs[0].semantic_kind == "code_ptr"
    assert os_kb.LIBRARIES["exec.library"].functions["ObtainQuickVector"].inputs[0].semantic_note
    assert os_kb.LIBRARIES["lowlevel.library"].functions["AddKBInt"].inputs[0].semantic_kind == "code_ptr"
    assert os_kb.LIBRARIES["lowlevel.library"].functions["AddTimerInt"].inputs[0].semantic_kind == "code_ptr"
    assert os_kb.LIBRARIES["lowlevel.library"].functions["AddVBlankInt"].inputs[0].semantic_kind == "code_ptr"


def test_os_reference_corrections_reject_unknown_correction_status() -> None:
    includes = load_canonical_os_kb_includes_parsed()
    other = load_canonical_os_kb_other_parsed()
    corrections = copy.deepcopy(load_canonical_os_kb_corrections())
    corrections["_meta"]["api_input_value_bindings"][0]["seed_origin"] = "unknown"

    with pytest.raises(ValueError, match="api_input_value_binding extension uses unknown seed_origin"):
        merge_os_reference_payloads(
            includes=includes,
            other=other,
            corrections=corrections,
        )


def test_os_reference_merge_rejects_missing_exact_match_policy() -> None:
    includes = load_canonical_os_kb_includes_parsed()
    other = load_canonical_os_kb_other_parsed()
    corrections = copy.deepcopy(load_canonical_os_kb_corrections())
    del corrections["_meta"]["value_domains"]["exec.signal_mask"]["exact_match_policy"]

    with pytest.raises(ValueError, match="exec.signal_mask is missing exact_match_policy"):
        merge_os_reference_payloads(
            includes=includes,
            other=other,
            corrections=corrections,
        )


def test_os_reference_merge_rejects_missing_flag_remainder_policy() -> None:
    includes = load_canonical_os_kb_includes_parsed()
    other = load_canonical_os_kb_other_parsed()
    corrections = copy.deepcopy(load_canonical_os_kb_corrections())
    del corrections["_meta"]["value_domains"]["exec.signal_mask"]["remainder_policy"]

    with pytest.raises(ValueError, match="exec.signal_mask is missing remainder_policy"):
        merge_os_reference_payloads(
            includes=includes,
            other=other,
            corrections=corrections,
        )


def test_runtime_hardware_matches_canonical_hardware_symbols() -> None:
    canonical = load_canonical_hardware_symbols()
    hardware_reference = load_canonical_hardware_reference()
    runtime = load_hardware_runtime_kb()

    assert canonical["_meta"] == runtime.META
    expected = {
        int(entry["cpu_address"], 16): {
            "symbol": entry["symbols"][0],
            "aliases": tuple(entry["symbols"][1:]),
            "family": entry["family"],
            "include": entry["include"],
            "base_symbol": entry["base_symbol"],
            "offset": int(entry["offset"], 16),
        }
        for entry in canonical["registers"]
    }
    assert expected == runtime.REGISTER_DEFS
    expected_interrupts = {
        entry["name"]: {
            "bit": entry["bit"],
            "level": entry["level"],
            "vector_number": entry["vector_number"],
            "vector_address": int(entry["vector_address"], 16),
            "enable_registers": tuple(entry["enable_registers"]),
            "request_registers": tuple(entry["request_registers"]),
            "description": entry["description"],
            **({"category": entry["category"]} if "category" in entry else {}),
            **({"producer": entry["producer"]} if "producer" in entry else {}),
            **({"channel": entry["channel"]} if "channel" in entry else {}),
            **({"related_registers": tuple(entry["related_registers"])} if "related_registers" in entry else {}),
        }
        for entry in hardware_reference["interrupt_sources"]
    }
    assert expected_interrupts == runtime.INTERRUPT_SOURCES
    expected_routes = {
        (entry["source_register"], entry["source_bit"]): {
            "source_register": entry["source_register"],
            "source_bit": entry["source_bit"],
            "parent_interrupt": entry["parent_interrupt"],
            "level": entry["level"],
            "vector_number": entry["vector_number"],
            "vector_address": int(entry["vector_address"], 16),
            "description": entry["description"],
        }
        for entry in hardware_reference["interrupt_routes"]
    }
    assert expected_routes == runtime.INTERRUPT_ROUTES


def test_canonical_hardware_reference_interrupt_sources_include_levels_and_vectors() -> None:
    hardware_reference = load_canonical_hardware_reference()
    by_name = {entry["name"]: entry for entry in hardware_reference["interrupt_sources"]}

    assert by_name["EXTER"]["level"] == 6
    assert by_name["EXTER"]["vector_number"] == 30
    assert by_name["EXTER"]["vector_address"] == "0x78"
    assert by_name["PORTS"]["level"] == 2
    assert by_name["PORTS"]["vector_number"] == 26
    assert by_name["PORTS"]["vector_address"] == "0x68"
    assert by_name["TBE"]["level"] == 1
    assert by_name["TBE"]["vector_number"] == 25
    assert by_name["TBE"]["vector_address"] == "0x64"
    assert by_name["DSKSYN"]["category"] == "disk"
    assert by_name["DSKSYN"]["producer"] == "paula_disk"
    assert by_name["DSKSYN"]["related_registers"] == ["DSKSYNC"]
    assert by_name["RBF"]["category"] == "serial"
    assert by_name["RBF"]["producer"] == "paula_uart"
    assert by_name["RBF"]["related_registers"] == ["SERDATR"]
    assert by_name["AUD0"]["category"] == "audio"
    assert by_name["AUD0"]["producer"] == "paula_audio"
    assert by_name["AUD0"]["channel"] == 0
    assert by_name["AUD0"]["related_registers"] == ["AUD0LC", "AUD0LEN", "AUD0PER", "AUD0VOL", "AUD0DAT"]
    assert by_name["BLIT"]["category"] == "blitter"
    assert by_name["BLIT"]["producer"] == "agnus_blitter"
    assert by_name["BLIT"]["related_registers"] == ["BLTSIZE", "BLTSIZV", "BLTSIZH"]
    assert by_name["VERTB"]["category"] == "video"
    assert by_name["VERTB"]["producer"] == "beam_counter"
    assert by_name["COPER"]["category"] == "copper"
    assert by_name["COPER"]["producer"] == "copper"
    assert by_name["SOFT"]["category"] == "software"
    assert by_name["SOFT"]["producer"] == "cpu_software"
    assert by_name["PORTS"]["category"] == "external_io"
    assert by_name["PORTS"]["producer"] == "peripherals"
    assert by_name["PORTS"]["related_registers"] == ["CIAA_ICR"]
    assert by_name["EXTER"]["category"] == "external_io"
    assert by_name["EXTER"]["producer"] == "peripherals"
    assert by_name["EXTER"]["related_registers"] == ["CIAB_ICR"]


def test_canonical_hardware_reference_interrupt_routes_bridge_cia_to_parent_interrupts() -> None:
    hardware_reference = load_canonical_hardware_reference()
    by_key = {
        (entry["source_register"], entry["source_bit"]): entry
        for entry in hardware_reference["interrupt_routes"]
    }

    assert by_key[("CIAA_ICR", 0)]["parent_interrupt"] == "PORTS"
    assert by_key[("CIAA_ICR", 0)]["level"] == 2
    assert by_key[("CIAA_ICR", 0)]["vector_number"] == 26
    assert by_key[("CIAA_ICR", 0)]["vector_address"] == "0x68"
    assert by_key[("CIAB_ICR", 0)]["parent_interrupt"] == "EXTER"
    assert by_key[("CIAB_ICR", 0)]["level"] == 6
    assert by_key[("CIAB_ICR", 0)]["vector_number"] == 30
    assert by_key[("CIAB_ICR", 0)]["vector_address"] == "0x78"


def test_runtime_size_encodings_match_canonical_structured_size_encoding() -> None:
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


def test_runtime_special_case_tables_match_canonical_data() -> None:
    load_m68k_runtime_module.cache_clear()
    payload = load_m68k_runtime_module()
    canonical = load_canonical_m68k_kb()
    by_name = {inst["mnemonic"]: inst for inst in canonical["instructions"]}

    expected_structured = {}
    for key, kb_mnemonic in canonical["_meta"]["asm_syntax_index"].items():
        mnemonic, _, raw_operand_types = key.partition(":")
        operand_types = tuple(raw_operand_types.split(",")) if raw_operand_types else ()
        expected_structured[mnemonic, operand_types] = (kb_mnemonic, operand_types)
    for key, value in expected_structured.items():
        assert payload.ASM_SYNTAX_INDEX[key] == value

    assert by_name["ADDQ"]["constraints"]["immediate_range"]["zero_means"] == payload.ADDQ_ZERO_MEANS

    expected_control: dict[int, str] = {}
    for entry in by_name["MOVEC"]["constraints"]["control_registers"]:
        expected_control.setdefault(int(entry["hex"], 16), entry["abbrev"])
    assert expected_control == payload.CONTROL_REGISTERS

    assert payload.META["_sp_reg_num"] == 7
    assert payload.META["_num_data_regs"] == 8
    assert payload.META["_num_addr_regs"] == 8
    assert payload.ASM_SYNTAX_INDEX["move", ("ea", "sr")] == ("MOVE to SR", ("ea", "sr"))
    assert payload.ASM_SYNTAX_INDEX["move", ("dn", "sr")] == ("MOVE to SR", ("ea", "sr"))
    assert payload.ASM_SYNTAX_INDEX["move", ("sr", "dn")] == ("MOVE from SR", ("sr", "ea"))
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
    assert payload.OPERATION_TYPES["NOP"] is None
    assert payload.OPERATION_CLASSES["LEA"] == payload.OperationClass.LOAD_EFFECTIVE_ADDRESS
    assert payload.OPERATION_CLASSES["MOVEQ"] is None
    assert payload.BOUNDS_CHECKS["CHK"] == (
        "destination",
        "zero",
        "source",
        "signed",
        False,
        True,
    )
    assert payload.BOUNDS_CHECKS["CHK2"] == (
        "rn",
        "ea_lower",
        "ea_upper",
        None,
        True,
        True,
    )
    assert payload.BOUNDS_CHECKS["CMP2"] == (
        "rn",
        "ea_lower",
        "ea_upper",
        None,
        True,
        False,
    )
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


def test_canonical_bounds_checks_are_structured_for_chk_family() -> None:
    canonical = load_canonical_m68k_kb()
    by_name = {inst["mnemonic"]: inst for inst in canonical["instructions"]}

    assert by_name["CHK"]["bounds_check"] == {
        "register_operand": "destination",
        "lower_bound": "zero",
        "upper_bound": "source",
        "comparison": "signed",
        "sign_extend_bounds_for_address_register": False,
        "trap_on_out_of_bounds": True,
    }
    assert by_name["CHK2"]["bounds_check"] == {
        "register_operand": "rn",
        "lower_bound": "ea_lower",
        "upper_bound": "ea_upper",
        "comparison": None,
        "sign_extend_bounds_for_address_register": True,
        "trap_on_out_of_bounds": True,
    }
    assert by_name["CMP2"]["bounds_check"] == {
        "register_operand": "rn",
        "lower_bound": "ea_lower",
        "upper_bound": "ea_upper",
        "comparison": None,
        "sign_extend_bounds_for_address_register": True,
        "trap_on_out_of_bounds": False,
    }


def test_runtime_hunk_relocation_semantics_are_typed() -> None:
    payload = load_hunk_runtime_kb()
    assert payload.RELOCATION_SEMANTICS["HUNK_RELOC32"] == (4, payload.RelocMode.ABSOLUTE)
    assert payload.RELOCATION_SEMANTICS["HUNK_RELOC16"] == (2, payload.RelocMode.PC_RELATIVE)


def test_runtime_decode_module_exposes_direct_decode_constants() -> None:
    payload = load_m68k_decode_runtime_module()
    canonical = load_canonical_m68k_kb()
    assert canonical["_meta"]["opword_bytes"] == payload.OPWORD_BYTES
    assert canonical["_meta"]["opword_bytes"] - 1 == payload.ALIGN_MASK
    assert canonical["_meta"]["default_operand_size"] == payload.DEFAULT_OPERAND_SIZE
    assert canonical["_meta"]["size_byte_count"] == payload.SIZE_BYTE_COUNT
    assert canonical["_meta"]["ea_mode_encoding"] == payload.EA_MODE_ENCODING
    assert "ind" in payload.REG_INDIRECT_MODES
    assert "dn" not in payload.REG_INDIRECT_MODES
    assert "postinc" not in payload.REG_INDIRECT_MODES
    assert canonical["_meta"]["movem_reg_masks"] == payload.MOVEM_REG_MASKS
    assert payload.SP_REG_NUM == 7
    assert payload.ENCODING_COUNTS["MOVE16"] == 5
    assert payload.EA_FULL_FIELDS["I/IS"] == (2, 0, 3)
    assert payload.EA_BRIEF_FIELDS["REGISTER"] == (14, 12, 3)
    assert payload.EA_FIELD_SPECS["LEA"] == ((5, 3, 3), (2, 0, 3))
    assert payload.MOVEM_FIELDS["dr"] == (10, 10, 1)
    assert payload.IMMEDIATE_RANGES["MOVEQ"] == ("DATA", 8, True, -128, 127, None)
    assert payload.FORM_OPERAND_TYPES["RTS"] == ((),)
def test_runtime_asm_module_exposes_direct_asm_constants() -> None:
    payload = load_m68k_asm_runtime_module()
    canonical = load_canonical_m68k_kb()
    assert canonical["_meta"]["ea_mode_encoding"] == payload.EA_MODE_ENCODING
    assert canonical["_meta"]["size_byte_count"] == payload.SIZE_BYTE_COUNT
    assert tuple(canonical["_meta"]["condition_codes"]) == payload.CONDITION_CODES
    assert payload.ENCODING_COUNTS["MOVE"] == 1
    assert canonical["_meta"]["cc_aliases"] == payload.CC_ALIASES
    assert canonical["_meta"]["movem_reg_masks"] == payload.MOVEM_REG_MASKS
    assert canonical["_meta"]["immediate_routing"] == payload.IMMEDIATE_ROUTING
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
    assert payload.RAW_FIELDS[0]["RTS"] == ()
    assert payload.FORM_OPERAND_TYPES["RTS"] == ((),)


def test_runtime_analysis_module_exposes_direct_analysis_constants() -> None:
    payload = load_m68k_analysis_runtime_module()
    canonical = load_canonical_m68k_kb()
    assert not hasattr(payload, "BY_NAME")
    assert canonical["_meta"]["opword_bytes"] == payload.OPWORD_BYTES
    assert canonical["_meta"]["default_operand_size"] == payload.DEFAULT_OPERAND_SIZE
    assert canonical["_meta"]["size_byte_count"] == payload.SIZE_BYTE_COUNT
    assert canonical["_meta"]["ea_mode_encoding"] == payload.EA_MODE_ENCODING
    assert canonical["_meta"]["ea_mode_sizes"] == payload.EA_MODE_SIZES
    assert {
        name: (entry["encoding"], entry["test"])
        for name, entry in canonical["_meta"]["cc_test_definitions"].items()
    } == payload.CC_TEST_DEFINITIONS
    assert canonical["_meta"]["cc_aliases"] == payload.CC_ALIASES
    assert canonical["_meta"]["movem_reg_masks"] == payload.MOVEM_REG_MASKS
    assert canonical["_meta"]["register_aliases"] == payload.REGISTER_ALIASES
    assert payload.SP_REG_NUM == 7
    assert payload.RTS_SP_INC == 4
    assert payload.ADDR_SIZE == "l"
    assert payload.ADDR_MASK == 0xFFFFFFFF
    assert tuple(canonical["_meta"]["ccr_bit_positions"]) == payload.CCR_FLAG_NAMES
    assert payload.LOOKUP_UPPER["PFLUSHA"] == "PFLUSH PFLUSHA"
    assert payload.LOOKUP_CANONICAL["PFLUSHA"] == "PFLUSH PFLUSHA"
    assert payload.LOOKUP_CANONICAL["PBBS"] == "PBcc"
    assert payload.LOOKUP_NUMERIC_CC_PREFIXES["PB"] == "PBcc"
    assert payload.LOOKUP_CC_FAMILIES["pb"][0] == "PBcc"
    assert payload.LOOKUP_ASM_MNEMONIC_INDEX["illegal"] == "ILLEGAL"
    assert payload.EA_REVERSE[7, 4] == "imm"
    assert payload.OPERATION_TYPES["MOVE"] == payload.OperationType.MOVE
    assert payload.OPERATION_CLASSES["LEA"] == payload.OperationClass.LOAD_EFFECTIVE_ADDRESS
    assert "MOVEA" in payload.SOURCE_SIGN_EXTEND


def test_runtime_compute_module_exposes_direct_compute_constants() -> None:
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


def test_runtime_executor_module_exposes_direct_executor_constants() -> None:
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


def test_runtime_root_module_exposes_no_instruction_bag() -> None:
    payload = load_m68k_runtime_module()
    assert not hasattr(payload, "INSTRUCTIONS")
    assert not hasattr(payload, "BY_NAME")
    assert "MOVEQ" in payload.MNEMONIC_INDEX["moveq"]


def test_runtime_projection_keeps_only_minimal_constraint_fields() -> None:
    payload = load_m68k_runtime_module()
    assert payload.AN_SIZES["ADDQ"] == ("w", "l")
    assert payload.AN_SIZES["RTS"] == ()
    assert payload.OPERAND_MODE_TABLES["ABCD"] == (
        "R/M",
        {0: ("dn", "dn"), 1: ("predec", "predec")},
    )
    assert payload.FORM_OPERAND_TYPES["MOVEQ"] == (("imm", "dn"),)
    assert payload.FORM_OPERAND_TYPES["RTS"] == ((),)
    assert payload.EA_MODE_TABLES["ADD"] == (
        ("dn", "an", "ind", "postinc", "predec", "disp", "index", "absw", "absl", "pcdisp", "pcindex", "imm"),
        ("ind", "postinc", "predec", "disp", "index", "absw", "absl"),
        (),
    )
    assert payload.EA_MODE_TABLES["RTS"] == ((), (), ())


def test_m68k_exception_vectors_include_autovectors_and_traps() -> None:
    canonical = load_canonical_m68k_kb()
    vectors = {entry["vector"]: entry for entry in canonical["_meta"]["exception_vectors"]}

    assert vectors[25]["address"] == 0x64
    assert vectors[25]["name"] == "Level 1 Interrupt Autovector"
    assert vectors[27]["address"] == 0x6C
    assert vectors[27]["name"] == "Level 3 Interrupt Autovector"
    assert vectors[32]["address"] == 0x80
    assert vectors[47]["address"] == 0xBC
    assert vectors[25]["seed_origin"] == "primary_doc"
    assert vectors[25]["review_status"] == "seeded"


def test_m68k_exception_stack_frames_include_format_families() -> None:
    canonical = load_canonical_m68k_kb()
    frames = canonical["_meta"]["exception_stack_frames"]
    by_format = {entry["format_code"]: entry for entry in frames if entry["format_code"] is not None}

    assert by_format["$0"]["name"] == "Four-Word Stack Frame"
    assert by_format["$2"]["name"] == "Six-Word Stack Frame"
    assert by_format["$7"]["name"] == "Access Error Stack Frame"
    assert by_format["$8"]["processors"] == ["68010"]
    assert by_format["$9"]["processors"] == ["68020", "68030"]
    assert by_format["$C"]["processors"] == ["CPU32"]
    assert by_format["$0"]["fields"] == [
        {"offset": 0x00, "name": "status_register", "size_words": 1},
        {"offset": 0x02, "name": "program_counter", "size_words": 2},
        {"offset": 0x06, "name": "format_and_vector_offset", "size_words": 1},
    ]
    assert by_format["$7"]["fields"][0] == {
        "offset": 0x00,
        "name": "special_status_word",
        "size_words": 1,
    }
    assert by_format["$7"]["fields"][-1] == {
        "offset": 0x3A,
        "name": "status_register",
        "size_words": 1,
    }
    assert by_format["$8"]["fields"][3]["name"] == "special_status_word"
    assert by_format["$9"]["fields"][2] == {
        "offset": 0x08,
        "name": "internal_registers",
        "size_words": 4,
    }
    assert by_format["$C"]["fields"][-1]["name"] == "current_instruction_program_counter_low"
    assert all(entry["seed_origin"] == "primary_doc" for entry in frames)
    assert all(entry["review_status"] == "seeded" for entry in frames)


def test_m68k_exception_frame_rules_bridge_vectors_to_frames() -> None:
    canonical = load_canonical_m68k_kb()
    rules = canonical["_meta"]["exception_frame_rules"]

    assert {
        "vector_start": 24,
        "vector_end": 47,
        "processors": ["68000"],
        "frame_ids": ["mc68000_group_1_2"],
        "selection": "always",
        "review_status": "seeded",
        "seed_origin": "primary_doc",
        "citation": "M68K PRM Rev 1 Appendix B exception vectors/stack frames; parser-authored mapping",
    } in rules
    assert {
        "vector_start": 24,
        "vector_end": 47,
        "processors": ["68010", "68020", "68030", "68040", "68EC040", "68LC040", "CPU32"],
        "frame_ids": ["format_0"],
        "selection": "always",
        "review_status": "seeded",
        "seed_origin": "primary_doc",
        "citation": "M68K PRM Rev 1 Appendix B exception vectors/stack frames; parser-authored mapping",
    } in rules
    assert {
        "vector_start": 2,
        "vector_end": 2,
        "processors": ["68020", "68030"],
        "frame_ids": ["format_a", "format_b"],
        "selection": "depends_on_bus_cycle_length",
        "review_status": "seeded",
        "seed_origin": "primary_doc",
        "citation": "M68K PRM Rev 1 Appendix B exception vectors/stack frames; parser-authored mapping",
    } in rules


def test_canonical_m68k_runtime_fields_are_structured() -> None:
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


def test_canonical_m68k_flow_entries_are_total() -> None:
    canonical = load_canonical_m68k_kb()
    for inst in canonical["instructions"]:
        flow = inst["pc_effects"]["flow"]
        assert "type" in flow
        assert "conditional" in flow
        assert isinstance(flow["conditional"], bool)


def test_runtime_builder_requires_structured_size_encoding(monkeypatch: MonkeyPatch) -> None:
    broken = copy.deepcopy(load_canonical_m68k_kb())
    target = next(inst for inst in broken["instructions"] if "size_encoding" in inst)
    del target["size_encoding"]

    def fake_load_json(name: str) -> object:
        if name == "m68k_instructions.json":
            return broken
        raise AssertionError(f"unexpected load for {name}")

    monkeypatch.setattr(runtime_builder, "_load_json", fake_load_json)
    with pytest.raises(KeyError, match="size_encoding"):
        runtime_builder._build_m68k_runtime()


def test_runtime_builder_requires_condition_families(monkeypatch: MonkeyPatch) -> None:
    broken = copy.deepcopy(load_canonical_m68k_kb())
    del broken["_meta"]["condition_families"]

    def fake_load_json(name: str) -> object:
        if name == "m68k_instructions.json":
            return broken
        raise AssertionError(f"unexpected load for {name}")

    monkeypatch.setattr(runtime_builder, "_load_json", fake_load_json)
    with pytest.raises(KeyError, match="condition_families"):
        runtime_builder._build_m68k_runtime()


def test_runtime_builder_requires_flow_type(monkeypatch: MonkeyPatch) -> None:
    broken = copy.deepcopy(load_canonical_m68k_kb())
    target = next(inst for inst in broken["instructions"] if inst["mnemonic"] == "BRA")
    del target["pc_effects"]["flow"]["type"]

    def fake_load_json(name: str) -> object:
        if name == "m68k_instructions.json":
            return broken
        raise AssertionError(f"unexpected load for {name}")

    monkeypatch.setattr(runtime_builder, "_load_json", fake_load_json)
    with pytest.raises(KeyError, match="type"):
        runtime_builder._build_m68k_runtime()


def test_runtime_builder_requires_flow_conditional(monkeypatch: MonkeyPatch) -> None:
    broken = copy.deepcopy(load_canonical_m68k_kb())
    target = next(inst for inst in broken["instructions"] if inst["mnemonic"] == "BRA")
    del target["pc_effects"]["flow"]["conditional"]

    def fake_load_json(name: str) -> object:
        if name == "m68k_instructions.json":
            return broken
        raise AssertionError(f"unexpected load for {name}")

    monkeypatch.setattr(runtime_builder, "_load_json", fake_load_json)
    with pytest.raises(KeyError, match="conditional"):
        runtime_builder._build_m68k_runtime()


def _runtime_module_attrs() -> dict[str, object]:
    real = load_m68k_runtime_module()
    return {
        name: copy.deepcopy(getattr(real, name))
        for name in dir(real)
        if name.isupper()
    }


def test_runtime_builder_emits_compare_swap_effects() -> None:
    runtime = load_m68k_executor_runtime_module()

    assert runtime.COMPARE_SWAP_EFFECTS["CAS CAS2"] == (
        (
            ("dn", "dn", "ea"),
            (("destination", "compare"),),
            (("destination", "update"),),
            (("compare", "destination"),),
        ),
        (
            ("dn_pair", "dn_pair", "unknown"),
            (("destination1", "compare1"), ("destination2", "compare2")),
            (("destination1", "update1"), ("destination2", "update2")),
            (("compare1", "destination1"), ("compare2", "destination2")),
        ),
    )


def _fake_module(**attrs: object) -> type[object]:
    return type("FakeModule", (), dict(attrs))


def test_runtime_loader_does_not_fallback_to_canonical_m68k(monkeypatch: MonkeyPatch) -> None:
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


def test_runtime_loader_requires_runtime_mnemonic_index(monkeypatch: MonkeyPatch) -> None:
    load_m68k_runtime_module.cache_clear()
    fake_module = _fake_module(META={})

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="MNEMONIC_INDEX"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_meta(monkeypatch: MonkeyPatch) -> None:
    load_m68k_runtime_module.cache_clear()
    fake_module = _fake_module(MNEMONIC_INDEX={})

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="META"):
            load_m68k_runtime_module()
    finally:
        load_m68k_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_control_register_table(monkeypatch: MonkeyPatch) -> None:
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


def test_runtime_loader_requires_runtime_register_fields_table(monkeypatch: MonkeyPatch) -> None:
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


def test_runtime_loader_requires_runtime_branch_displacement_table(monkeypatch: MonkeyPatch) -> None:
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


def test_runtime_loader_requires_runtime_movem_fields_table(monkeypatch: MonkeyPatch) -> None:
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


def test_runtime_loader_requires_decode_opword_bytes(monkeypatch: MonkeyPatch) -> None:
    load_m68k_decode_runtime_module.cache_clear()
    attrs: dict[str, object] = {
        "ALIGN_MASK": 1,
        "DEFAULT_OPERAND_SIZE": "w",
        "SIZE_BYTE_COUNT": {},
        "EA_MODE_ENCODING": {},
        "REG_INDIRECT_MODES": frozenset(),
        "MOVEM_REG_MASKS": {},
        "SP_REG_NUM": 7,
        "EA_BRIEF_FIELDS": {},
        "EA_FULL_FIELDS": {},
        "EA_FULL_BD_SIZE": {},
        "ENCODING_MASKS": (),
        "FIELD_MAPS": (),
        "RAW_FIELDS": (),
        "ENCODING_COUNTS": {},
        "EA_FIELD_SPECS": {},
        "FORM_OPERAND_TYPES": {},
        "OPMODE_TABLES_BY_VALUE": {},
        "OPERAND_MODE_TABLES": {},
        "EA_MODE_TABLES": {},
        "IMMEDIATE_RANGES": {},
        "REGISTER_FIELDS": {},
        "DEST_REG_FIELD": {},
        "DIRECTION_VARIANTS": {},
        "SHIFT_FIELDS": {},
        "RM_FIELD": {},
        "CONTROL_REGISTERS": {},
        "MOVE_FIELDS": (),
        "MOVEM_FIELDS": {},
        "CPID_FIELD": (),
    }
    fake_module = _fake_module(**attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="OPWORD_BYTES"):
            load_m68k_decode_runtime_module()
    finally:
        load_m68k_decode_runtime_module.cache_clear()


def test_runtime_loader_requires_asm_immediate_routing(monkeypatch: MonkeyPatch) -> None:
    load_m68k_asm_runtime_module.cache_clear()
    attrs: dict[str, object] = {
        "ENCODING_COUNTS": {},
        "ENCODING_MASKS": (),
        "FIELD_MAPS": (),
        "RAW_FIELDS": (),
        "LOOKUP_UPPER": {},
        "EA_MODE_ENCODING": {},
        "EA_BRIEF_FIELDS": {},
        "SIZE_BYTE_COUNT": {},
        "CONDITION_CODES": (),
        "CC_ALIASES": {},
        "MOVEM_REG_MASKS": {},
        "SIZE_ENCODINGS_ASM": {},
        "OPMODE_TABLES_LIST": {},
        "FORM_OPERAND_TYPES": {},
        "FORM_FLAGS_020": {},
        "EA_MODE_TABLES": {},
        "CC_FAMILIES": {},
        "IMMEDIATE_RANGES": {},
        "DIRECTION_VARIANTS": {},
        "BRANCH_INLINE_DISPLACEMENTS": {},
        "AN_SIZES": {},
        "USES_LABELS": {},
        "DIRECTION_FORM_VALUES": {},
        "SPECIAL_OPERAND_TYPES": (),
        "ASM_SYNTAX_INDEX": {},
    }
    fake_module = _fake_module(**attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="IMMEDIATE_ROUTING"):
            load_m68k_asm_runtime_module()
    finally:
        load_m68k_asm_runtime_module.cache_clear()


def test_runtime_loader_requires_analysis_lookup_cc_families(monkeypatch: MonkeyPatch) -> None:
    load_m68k_analysis_runtime_module.cache_clear()
    attrs: dict[str, object] = {
        "OPWORD_BYTES": 2,
        "DEFAULT_OPERAND_SIZE": "w",
        "SIZE_BYTE_COUNT": {},
        "EA_MODE_ENCODING": {},
        "EA_REVERSE": {},
        "EA_BRIEF_FIELDS": {},
        "EA_MODE_SIZES": {},
        "MOVEM_REG_MASKS": {},
        "CC_TEST_DEFINITIONS": {},
        "CC_ALIASES": {},
        "REGISTER_ALIASES": {},
        "NUM_DATA_REGS": 8,
        "NUM_ADDR_REGS": 8,
        "SP_REG_NUM": 7,
        "RTS_SP_INC": 4,
        "ADDR_SIZE": "l",
        "ADDR_MASK": 0xFFFFFFFF,
        "CCR_FLAG_NAMES": (),
        "OPERATION_TYPES": {},
        "OPERATION_CLASSES": {},
        "SOURCE_SIGN_EXTEND": (),
        "FLOW_TYPES": {},
        "FLOW_CONDITIONAL": {},
        "COMPUTE_FORMULAS": {},
        "SP_EFFECTS": {},
        "EA_MODE_TABLES": {},
        "AN_SIZES": {},
        "PROCESSOR_MINS": {},
        "PROCESSOR_020_VARIANTS": {},
        "LOOKUP_UPPER": {},
        "LOOKUP_CANONICAL": {},
        "LOOKUP_NUMERIC_CC_PREFIXES": {},
        "LOOKUP_ASM_MNEMONIC_INDEX": {},
    }
    fake_module = _fake_module(**attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="LOOKUP_CC_FAMILIES"):
            load_m68k_analysis_runtime_module()
    finally:
        load_m68k_analysis_runtime_module.cache_clear()


def test_runtime_loader_requires_compute_formulas(monkeypatch: MonkeyPatch) -> None:
    load_m68k_compute_runtime_module.cache_clear()
    fake_module = _fake_module(
        OPERATION_TYPES={},
        IMPLICIT_OPERANDS={},
        SP_EFFECTS={},
        PRIMARY_DATA_SIZES={},
    )

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="COMPUTE_FORMULAS"):
            load_m68k_compute_runtime_module()
    finally:
        load_m68k_compute_runtime_module.cache_clear()


def test_runtime_loader_requires_executor_branch_table(monkeypatch: MonkeyPatch) -> None:
    load_m68k_executor_runtime_module.cache_clear()
    attrs: dict[str, object] = {
        "FIELD_MAPS": (),
        "RAW_FIELDS": (),
        "OPERAND_MODE_TABLES": {},
        "REGISTER_FIELDS": {},
        "RM_FIELD": {},
        "IMPLICIT_OPERANDS": {},
        "OPMODE_TABLES_BY_VALUE": {},
        "MOVEM_FIELDS": {},
        "IMMEDIATE_RANGES": {},
        "DEST_REG_FIELD": {},
        "OPERATION_TYPES": {},
        "OPERATION_CLASSES": {},
        "SOURCE_SIGN_EXTEND": (),
        "BOUNDS_CHECKS": {},
        "BIT_MODULI": {},
        "SHIFT_COUNT_MODULI": {},
        "ROTATE_EXTRA_BITS": {},
        "DIRECTION_VARIANTS": {},
        "SHIFT_FIELDS": (),
        "SHIFT_VARIANT_BEHAVIORS": {},
        "PRIMARY_DATA_SIZES": {},
        "SIGNED_RESULTS": {},
        "BRANCH_INLINE_DISPLACEMENTS": {},
    }
    fake_module = _fake_module(**attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="BRANCH_EXTENSION_DISPLACEMENTS"):
            load_m68k_executor_runtime_module()
    finally:
        load_m68k_executor_runtime_module.cache_clear()


def test_runtime_loader_requires_runtime_direction_variants_table(monkeypatch: MonkeyPatch) -> None:
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


def test_runtime_loader_requires_runtime_compute_formulas(monkeypatch: MonkeyPatch) -> None:
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


def test_runtime_loader_requires_runtime_sp_effects(monkeypatch: MonkeyPatch) -> None:
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


def test_assembler_requires_kb_size_encoding(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(m68k_asm.runtime_m68k_asm, "SIZE_ENCODINGS_ASM", {})
    with pytest.raises(KeyError, match="size encoding"):
        m68k_asm._get_size_encoding("MOVE", "w")


def test_assembler_requires_runtime_raw_fields_for_mnemonic(monkeypatch: MonkeyPatch) -> None:
    raw_fields = list(copy.deepcopy(m68k_asm.runtime_m68k_asm.RAW_FIELDS))
    raw_fields0 = dict(cast(dict[str, object], raw_fields[0]))
    del raw_fields0["MOVE"]
    raw_fields[0] = raw_fields0
    monkeypatch.setattr(m68k_asm.runtime_m68k_asm, "RAW_FIELDS", tuple(raw_fields))

    with pytest.raises(KeyError, match="MOVE"):
        m68k_asm.assemble_instruction("move.w d0,d1")


def test_assembler_requires_runtime_encoding_mask_for_mnemonic(monkeypatch: MonkeyPatch) -> None:
    encoding_masks = list(copy.deepcopy(m68k_asm.runtime_m68k_asm.ENCODING_MASKS))
    encoding_masks[0] = dict(encoding_masks[0])
    del encoding_masks[0]["MOVE"]
    monkeypatch.setattr(m68k_asm.runtime_m68k_asm, "ENCODING_MASKS", tuple(encoding_masks))

    with pytest.raises(KeyError, match="MOVE"):
        m68k_asm.assemble_instruction("move.w d0,d1")


def test_build_opword_requires_value_for_named_field() -> None:
    with pytest.raises(KeyError, match="MODE"):
        m68k_asm._build_opword("MOVE", {"REGISTER": [1, 0], "SIZE": 3})


def test_build_opword_requires_value_for_duplicate_field_occurrence() -> None:
    with pytest.raises(KeyError, match="REGISTER"):
        m68k_asm._build_opword("MOVE", {"MODE": [0, 0], "REGISTER": [1], "SIZE": 3})


def test_runtime_loader_requires_os_meta(monkeypatch: MonkeyPatch) -> None:
    load_os_runtime_kb.cache_clear()
    fake_module = _fake_module(STRUCTS={}, CONSTANTS={}, LIBRARIES={})

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="META"):
            load_os_runtime_kb()
    finally:
        load_os_runtime_kb.cache_clear()


def test_runtime_loader_requires_hunk_types(monkeypatch: MonkeyPatch) -> None:
    load_hunk_runtime_kb.cache_clear()
    attrs: dict[str, object] = {
        "META": {},
        "EXT_TYPES": {},
        "MEMORY_FLAGS": {},
        "MEMORY_TYPE_CODES": {},
        "EXT_TYPE_CATEGORIES": {},
        "COMPATIBILITY_NOTES": [],
        "RELOC_FORMATS": {},
        "RELOCATION_SEMANTICS": {},
        "HUNK_CONTENT_FORMATS": {},
        "HUNKEXE_SUPPORTED_RELOCATION_TYPES": (),
    }
    fake_module = _fake_module(**attrs)

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="HUNK_TYPES"):
            load_hunk_runtime_kb()
    finally:
        load_hunk_runtime_kb.cache_clear()


def test_runtime_loader_requires_naming_patterns(monkeypatch: MonkeyPatch) -> None:
    load_naming_runtime_kb.cache_clear()
    fake_module = _fake_module(META={}, TRIVIAL_FUNCTIONS=[], GENERIC_PREFIX="call_")

    monkeypatch.setattr("tests.runtime_kb_helpers._load_runtime_module", lambda _: fake_module)
    try:
        with pytest.raises(KeyError, match="PATTERNS"):
            load_naming_runtime_kb()
    finally:
        load_naming_runtime_kb.cache_clear()


def test_runtime_os_meta_is_typed() -> None:
    runtime = load_os_runtime_kb()

    assert runtime.META.calling_convention.base_reg == "A6"
    assert runtime.META.calling_convention.return_reg == "D0"
    assert runtime.META.exec_base_addr.address == 4
    assert runtime.META.exec_base_addr.library == "exec.library"
    assert runtime.API_INPUT_VALUE_DOMAINS["exec.library"]["AllocMem"]["attributes"] == (
        "exec.allocmem.attributes")
    assert runtime.API_INPUT_VALUE_DOMAINS["exec.library"]["AvailMem"]["attributes"] == (
        "exec.allocmem.attributes")
    assert runtime.API_INPUT_VALUE_DOMAINS["dos.library"]["Seek"]["mode"] == "dos.seek.mode"
    assert runtime.API_INPUT_VALUE_DOMAINS["dos.library"]["Lock"]["accessMode"] == (
        "dos.lock.access_mode")
    assert runtime.API_INPUT_VALUE_DOMAINS["dos.library"]["Open"]["accessMode"] == (
        "dos.open.access_mode")
    assert runtime.API_INPUT_VALUE_DOMAINS["exec.library"]["SetSignal"]["signalMask"] == (
        "exec.signal_mask")
    assert "OpenDevice" not in runtime.API_INPUT_VALUE_DOMAINS["exec.library"]
    assert runtime.STRUCT_FIELD_VALUE_DOMAINS["IO.IO_COMMAND"][None] == "exec.io.command"
    assert runtime.STRUCT_FIELD_VALUE_DOMAINS["IO.IO_COMMAND"]["trackdisk.device"] == "trackdisk.device.io_command"
    assert runtime.STRUCT_FIELD_VALUE_DOMAINS["DosPacket.dp_Type"][None] == "dos.packet.action"
    assert runtime.VALUE_DOMAINS["exec.io.command"].kind == "enum"
    assert "CMD_READ" in runtime.VALUE_DOMAINS["exec.io.command"].members
    assert runtime.VALUE_DOMAINS["exec.io.command"].exact_match_policy == "error"
    assert "ACTION_FINDUPDATE" in runtime.VALUE_DOMAINS["dos.packet.action"].members
    assert runtime.VALUE_DOMAINS["exec.signal_mask"].kind == "flags"
    assert runtime.VALUE_DOMAINS["exec.signal_mask"].composition == "bit_or"
    assert runtime.VALUE_DOMAINS["exec.signal_mask"].remainder_policy == "error"
    initstruct = runtime.META.typed_data_stream_formats["exec.InitStruct"]
    assert runtime.META.resident_autoinit_word_stream_formats == {
        "structure_init": "exec.InitStruct"
    }
    assert runtime.META.resident_entry_register_seeds["library"]["init"] == (
        {
            "register": "D0",
            "kind": "library_base",
            "named_base_source": "current_target",
        },
        {
            "register": "A6",
            "kind": "library_base",
            "named_base_source": "fixed",
            "named_base_name": "exec.library",
        },
    )
    assert runtime.META.include_min_versions["exec/initializers.i"] == "1.3"
    assert "hardware/custom.i" in runtime.META.include_min_versions
    assert "hardware/cia.i" in runtime.META.include_min_versions
    assert initstruct["include_path"] == "exec/initializers.i"
    assert initstruct["available_since"] == "1.3"
    assert initstruct["constructors"][0]["name"] == "INITBYTE"
    assert not hasattr(runtime, "RUNTIME")


def test_runtime_os_struct_entries_are_typed() -> None:
    runtime = load_os_runtime_kb()

    io_struct = runtime.STRUCTS["IO"]
    assert io_struct.base_struct == "MN"
    assert io_struct.base_offset == 20
    assert io_struct.base_offset_symbol == "MN_SIZE"
    assert io_struct.size == 48

    msg_list = next(field for field in runtime.STRUCTS["MP"].fields
                    if field.name == "MP_MSGLIST")
    assert msg_list.type == "STRUCT"
    assert msg_list.size_symbol == "LH_SIZE"
    assert msg_list.struct == "LH"
    assert msg_list.size == 14


def test_runtime_os_library_function_entries_are_typed() -> None:
    runtime = load_os_runtime_kb()

    open_device = runtime.LIBRARIES["exec.library"].functions["OpenDevice"]
    assert open_device.lvo == -444
    assert tuple(arg.name for arg in open_device.inputs) == (
        "devName", "unitNumber", "iORequest", "flags")
    assert tuple(arg.regs for arg in open_device.inputs) == (
        ("A0",), ("D0",), ("A1",), ("D1",))
    assert open_device.inputs[2].i_struct == "IO"
    assert open_device.output is not None
    assert open_device.output.name == "error"
    assert open_device.output.reg == "D0"


def test_canonical_os_kb_preserves_embedded_struct_metadata() -> None:
    canonical = load_canonical_os_kb()

    io_struct = canonical["structs"]["IO"]
    assert io_struct["base_offset"] == 20
    assert io_struct["base_offset_symbol"] == "MN_SIZE"
    assert io_struct["base_struct"] == "MN"

    mp_struct = canonical["structs"]["MP"]
    msg_list = next(field for field in mp_struct["fields"]
                    if field["name"] == "MP_MSGLIST")
    assert msg_list["type"] == "STRUCT"
    assert msg_list["size_symbol"] == "LH_SIZE"
    assert msg_list["struct"] == "LH"
    assert msg_list["size"] == 14

    io_audio = canonical["structs"]["IOAudio"]
    assert io_audio["base_struct"] == "IO"
    assert io_audio["base_offset"] == 32
    write_msg = next(field for field in io_audio["fields"]
                     if field["name"] == "ioa_WriteMsg")
    assert write_msg["struct"] == "MN"
    assert write_msg["size"] == 20

    timer_request = canonical["structs"]["TIMEREQUEST"]
    assert timer_request["base_struct"] == "IO"
    assert timer_request["base_offset"] == 32

    rexx_task = canonical["structs"]["RexxTask"]
    assert rexx_task["base_offset"] == 200
    assert rexx_task["base_offset_symbol"] == "GLOBALSZ"
    assert "base_struct" not in rexx_task


def test_runtime_os_resolves_nested_struct_fields_on_demand() -> None:
    structs = load_os_runtime_kb().STRUCTS

    succ = resolve_struct_field(structs, "IO", 0)
    assert succ is not None
    assert succ.owner_struct == "LN"
    assert succ.field.name == "LN_SUCC"

    reply_port = resolve_struct_field(structs, "IO", 14)
    assert reply_port is not None
    assert reply_port.owner_struct == "MN"
    assert reply_port.field.name == "MN_REPLYPORT"

    device = resolve_struct_field(structs, "IO", 20)
    assert device is not None
    assert device.owner_struct == "IO"
    assert device.field.name == "IO_DEVICE"


def test_runtime_os_struct_fields_include_pointer_struct_metadata() -> None:
    os_kb = load_os_runtime_kb()
    io_fields = {field.name: field for field in os_kb.STRUCTS["IO"].fields}
    mn_fields = {field.name: field for field in os_kb.STRUCTS["MN"].fields}

    assert io_fields["IO_DEVICE"].c_type == "struct Device *"
    assert io_fields["IO_DEVICE"].pointer_struct == "DD"
    assert io_fields["IO_UNIT"].c_type == "struct Unit *"
    assert io_fields["IO_UNIT"].pointer_struct == "UNIT"
    assert mn_fields["MN_REPLYPORT"].c_type == "struct MsgPort *"
    assert mn_fields["MN_REPLYPORT"].pointer_struct == "MP"


def test_parse_fd_file_recognizes_release_marker_for_private_blocks(tmp_path: Path) -> None:
    fd_path = tmp_path / "AMIGAGUIDE_LIB.FD"
    fd_path.write_text(
        "##base _AmigaGuideBase\n"
        "##bias 30\n"
        "*--- functions in V40 or higher (Release 3.1) ---\n"
        "##private\n"
        "amigaguidePrivate1()()\n",
        encoding="utf-8",
    )

    parsed = parse_fd_file(str(fd_path))

    func = parsed["functions"]["amigaguidePrivate1"]
    assert func["fd_version"] == "40"
    assert func["available_since"] == "3.1"


def test_runtime_hunk_and_naming_match_canonical_payloads() -> None:
    hunk_runtime = load_hunk_runtime_kb()
    hunk_canonical = load_canonical_hunk_kb()
    assert hunk_canonical["_meta"] == hunk_runtime.META
    assert hunk_canonical["hunk_types"] == hunk_runtime.HUNK_TYPES
    assert hunk_canonical["ext_types"] == hunk_runtime.EXT_TYPES
    assert hunk_canonical["memory_flags"] == hunk_runtime.MEMORY_FLAGS
    assert hunk_canonical["memory_type_codes"] == hunk_runtime.MEMORY_TYPE_CODES
    assert hunk_canonical["ext_type_categories"] == hunk_runtime.EXT_TYPE_CATEGORIES
    assert hunk_canonical["compatibility_notes"] == hunk_runtime.COMPATIBILITY_NOTES
    assert hunk_canonical["reloc_formats"] == hunk_runtime.RELOC_FORMATS
    assert {
        name: (entry["bytes"], getattr(hunk_runtime.RelocMode, entry["mode"].upper()))
        for name, entry in hunk_canonical["relocation_semantics"].items()
    } == hunk_runtime.RELOCATION_SEMANTICS
    assert hunk_canonical["hunk_content_formats"] == hunk_runtime.HUNK_CONTENT_FORMATS
    assert hunk_runtime.HUNK_CONTENT_FORMATS["HUNK_DEBUG"]["sub_formats"]["LINE"]["fields"][0] == {
        "name": "base_offset",
        "type": "ULONG",
    }
    assert tuple(hunk_canonical["hunkexe_supported_relocation_types"]) == (
        hunk_runtime.HUNKEXE_SUPPORTED_RELOCATION_TYPES
    )
    assert not hasattr(hunk_runtime, "RUNTIME")

    naming_runtime = load_naming_runtime_kb()
    naming_canonical = load_canonical_naming_rules()
    assert naming_canonical["_meta"] == naming_runtime.META
    assert naming_canonical["patterns"] == naming_runtime.PATTERNS
    assert naming_canonical["trivial_functions"] == naming_runtime.TRIVIAL_FUNCTIONS
    assert naming_canonical["generic_prefix"] == naming_runtime.GENERIC_PREFIX
    assert not hasattr(naming_runtime, "RUNTIME")
