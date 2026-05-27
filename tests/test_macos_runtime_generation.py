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


def _record_by_name(metadata: dict[str, object], name: str) -> dict[str, object]:
    records = metadata["records"]
    assert isinstance(records, list)
    return next(record for record in records if isinstance(record, dict) and record["name"] == name)


def _field_by_name(record: dict[str, object], name: str) -> dict[str, object]:
    fields = record["fields"]
    assert isinstance(fields, list)
    return next(field for field in fields if isinstance(field, dict) and field["name"] == name)


def _call_by_name(metadata: dict[str, object], name: str) -> dict[str, object]:
    calls = metadata["calls"]
    assert isinstance(calls, list)
    return next(call for call in calls if isinstance(call, dict) and call["name"] == name)


def test_record_extraction_covers_baseline_structs_with_source_evidence() -> None:
    generator = _load_generator()
    metadata = generator.extract_baseline_metadata()

    rect = _record_by_name(metadata, "Rect")
    assert rect["size"] == 8
    assert rect["source"] == "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacTypes.a"
    assert rect["line"] == 490
    assert _field_by_name(rect, "right")["offset"] == 6
    assert _field_by_name(rect, "right")["size"] == 2
    assert _field_by_name(rect, "topLeft")["offset"] == 0
    assert _field_by_name(rect, "topLeft")["size"] == 4

    event = _record_by_name(metadata, "EventRecord")
    assert event["size"] == 16
    assert event["source"] == "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Events.a"
    assert _field_by_name(event, "where")["offset"] == 10
    assert _field_by_name(event, "where")["size"] == 4
    assert _field_by_name(event, "where")["line"] == 135

    volume = _record_by_name(metadata, "HVolumeParam")
    assert volume["size"] == 122
    assert volume["source"] == "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Files.a"
    assert _field_by_name(volume, "ioNamePtr")["offset"] == 18
    assert _field_by_name(volume, "ioNamePtr")["size"] == 4
    assert _field_by_name(volume, "ioVolIndex")["offset"] == 28
    assert _field_by_name(volume, "ioVFndrInfo")["size"] == 32


def test_trap_extraction_covers_baseline_calls_with_register_protocol() -> None:
    generator = _load_generator()
    metadata = generator.extract_baseline_metadata()
    calls = metadata["calls"]
    assert isinstance(calls, list)
    assert len(calls) > 800

    get_resource = _call_by_name(metadata, "_GetResource")
    assert get_resource["kind"] == "opword"
    assert get_resource["opword"] == 0xA9A0
    assert get_resource["family"] == "Resources"
    assert get_resource["line"] == 425
    assert "GetResource(" in get_resource["prototype"]

    wait_next_event = _call_by_name(metadata, "_WaitNextEvent")
    assert wait_next_event["opword"] == 0xA860
    assert wait_next_event["family"] == "Events"

    unload_seg = _call_by_name(metadata, "_UnloadSeg")
    assert unload_seg["opword"] == 0xA9F1
    assert unload_seg["family"] == "SegLoad"
    assert unload_seg["kind"] == "opword"

    load_seg = _call_by_name(metadata, "_LoadSeg")
    assert load_seg["kind"] == "trap_constant"
    assert load_seg["opword"] == 0xA9F0
    assert load_seg["family"] == "Traps"
    assert load_seg["source"] == "ext/macos_includes/mpw_gm/Interfaces/CIncludes/Traps.h"

    get_fnum = _call_by_name(metadata, "_GetFNum")
    assert get_fnum["opword"] == 0xA900
    assert get_fnum["source"] == "ext/macos_includes/mpw_gm/Interfaces/AIncludes/Fonts.a"
    assert get_fnum["c_name"] == "GetFNum"
    assert get_fnum["return_type"] == "void"
    assert get_fnum["parameters"] == [
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

    hget_vinfo = _call_by_name(metadata, "_PBHGetVInfoSync")
    assert hget_vinfo["opword"] == 0xA207
    assert hget_vinfo["parameter_register"] == "A0"
    assert hget_vinfo["result_register"] == "D0"
    assert "PBHGetVInfoSync(HParmBlkPtr paramBlock)" in hget_vinfo["prototype"]

    new_ptr = _call_by_name(metadata, "_NewPtr")
    assert new_ptr["opword"] == 0xA11E
    assert new_ptr["source"] == "ext/macos_includes/mpw_gm/Interfaces/AIncludes/MacMemory.a"
    assert new_ptr["parameter_register"] == "D0"
    assert new_ptr["result_register"] == "A0"

    close_sync = _call_by_name(metadata, "_PBCloseSync")
    assert close_sync["opword"] == 0xA001
    assert close_sync["parameter_register"] == "A0"
    assert close_sync["result_register"] == "D0"


def test_num_to_string_is_package_macro_not_opword_alias() -> None:
    generator = _load_generator()
    call = _call_by_name(generator.extract_baseline_metadata(), "_NumToString")

    assert call["kind"] == "package_macro"
    assert call["opword"] == 0
    assert call["package_word"] == 0xA9EE
    assert call["source"] == "ext/macos_includes/mpw_gm/Interfaces/AIncludes/NumberFormatting.a"
    assert "NumToString(" in call["prototype"]


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
