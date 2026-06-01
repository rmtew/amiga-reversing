from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "src" / "scripts" / "generate_mac_os_runtime.py"


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("generate_mac_os_runtime", GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _field_by_name(record: dict[str, object], name: str) -> dict[str, object]:
    fields = record["fields"]
    assert isinstance(fields, list)
    return next(field for field in fields if isinstance(field, dict) and field["name"] == name)


def test_record_extraction_covers_struct_offsets_from_small_fixture() -> None:
    generator = _load_generator()
    rect = generator.parse_record(
        [
            "Rect RECORD 0",
            "topLeft ds Point ; offset: $0000 (0)",
            "bottom ds.w 1 ; offset: $0004 (4)",
            "right ds.w 1 ; offset: $0006 (6)",
            "sizeof EQU * ; size: $0008 (8)",
            " ENDR",
        ],
        "Rect",
        "fixture/MacTypes.a",
        {"Point": 4},
    )

    assert rect["size"] == 8
    assert rect["source"] == "fixture/MacTypes.a"
    assert rect["line"] == 1
    assert _field_by_name(rect, "right")["offset"] == 6
    assert _field_by_name(rect, "right")["size"] == 2
    assert _field_by_name(rect, "topLeft")["offset"] == 0
    assert _field_by_name(rect, "topLeft")["size"] == 4


def test_trap_extraction_covers_call_kinds_and_register_protocol_from_small_fixture() -> None:
    generator = _load_generator()
    opword_call = generator.parse_call_asm(
        [
            "; paramBlock => A0",
            "; result <= D0",
            "_PBHGetVInfoSync: OPWORD $A207",
        ],
        "_PBHGetVInfoSync",
        "Files",
        "fixture/Files.a",
    )
    prototype = generator.parse_c_prototype_metadata(
        [
            "EXTERN_API( void ) GetFNum(",
            "  ConstStr255Param name,",
            "  short * familyID",
            ") ONEWORDINLINE(0xA900);",
        ],
        "GetFNum",
    )
    package_call = generator.parse_call_asm(
        [
            "NumToString PROC",
            " dc.w $A9EE",
            " ENDP",
        ],
        "NumToString",
        "NumberFormatting",
        "fixture/NumberFormatting.a",
    )

    assert opword_call["kind"] == "opword"
    assert opword_call["opword"] == 0xA207
    assert opword_call["family"] == "Files"
    assert opword_call["parameter_register"] == "A0"
    assert opword_call["result_register"] == "D0"
    assert prototype is not None
    assert prototype["c_name"] == "GetFNum"
    assert prototype["return_type"] == "void"
    assert prototype["parameters"] == [
        {
            "name": "name",
            "type": "ConstStr255Param",
            "pointer_depth": 0,
            "direction": "input_value",
            "index": 0,
        },
        {
            "name": "familyID",
            "type": "short *",
            "pointer_depth": 1,
            "direction": "output_or_inout_pointer",
            "index": 1,
        },
    ]
    assert package_call["kind"] == "package_macro"
    assert package_call["opword"] == 0
    assert package_call["package_word"] == 0xA9EE


def test_num_to_string_is_package_macro_not_opword_alias() -> None:
    generator = _load_generator()
    call = generator.parse_call_asm(
        [
            "NumToString PROC",
            " move.l (a7)+,a0",
            " dc.w $A9EE",
            " jmp (a0)",
            " ENDP",
        ],
        "NumToString",
        "NumberFormatting",
        "fixture/NumberFormatting.a",
    )

    assert call["kind"] == "package_macro"
    assert call["opword"] == 0
    assert call["package_word"] == 0xA9EE
    assert call["source"] == "fixture/NumberFormatting.a"


def test_generated_mac_os_runtime_metadata_is_current() -> None:
    generator = _load_generator()
    metadata = generator.extract_baseline_metadata()

    assert (ROOT / "src" / "generated" / "mac_os_runtime.h").read_text(encoding="ascii") == (
        generator.render_header(metadata)
    )
    assert (ROOT / "src" / "generated" / "mac_os_runtime.c").read_text(encoding="ascii") == (
        generator.render_source(metadata)
    )
    assert (ROOT / "src" / "generated" / "mac_os_runtime.json").read_text(encoding="ascii") == (
        generator.render_json(metadata)
    )
