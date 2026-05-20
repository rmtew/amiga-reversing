from __future__ import annotations

from amiga_reversing.disasm.macos_source_project import build_macos_source_project
from amiga_reversing.disasm.macos_source_render import render_macos_source_views

MPW_DEPENDENCY = "\u00c4"
MPW_CONTINUATION = "\u00b6"

SAMPLE_H = """
#define rMenuBar 128
#define rStopRect 128
#define rGoRect 129
"""

SAMPLE_INC = """
rMenuBar EQU 128
rStopRect EQU 128
rGoRect EQU 129
"""

SAMPLE_A = """
\tSEG\t'Initialize'
Initialize\tPROC
\tIMPORT\t_WaitNextEvent
StackFrame\tRECORD\t0
\tENDR
\tMOVE.W #rMenuBar,-(SP)
\t_GetNewMBar
\tENDP
\tSEG\t'Main'
StartUp\tMAIN
\tMOVE.W #rStopRect,-(SP)
\tBSR GoGetRect
\tMOVE.W #rGoRect,-(SP)
\tBSR GoGetRect
\tENDP
"""

SAMPLE_MISC_A = """
\tSEG\t'Initialize'
GoGetRect\tFUNC\tEXPORT
\tIMPORT\t_GetResource
\tMOVE.L #'RECT',-(SP)
\tMOVE.W RectID(A6),-(SP)
\t_GetResource
\tENDF
"""

MEMORY_SRC_A = """
\tSEG\t'Memory'
MemoryMain\tMAIN
\tIMPORT\t_PBHGetVInfoSync
HVolumeParam\tRECORD\t0
\tENDR
\t_PBHGetVInfoSync
\tENDP
"""

COUNT_A = """
\tSEG\t'Main'
CountMain\tPROC
\tIMPORT\t_NumToString
\t_NumToString
\tENDP
"""

RESOURCES = {
    "MPW-GM/MPW/Examples/AExamples/Sample.r": """
resource 'MBAR' (rMenuBar, preload) {
};
resource 'RECT' (rStopRect, preload) {
};
resource 'RECT' (rGoRect, preload) {
};
""",
    "MPW-GM/MPW/Examples/AExamples/Count.r": """
resource 'cmdo' (128) {
};
""",
}

MAKE = f"""
AObjs           = Sample.a.o {MPW_CONTINUATION}
                    SampleMisc.a.o {MPW_CONTINUATION}
                    "{{Libraries}}"MacRuntime.o
Sample          {MPW_DEPENDENCY}{MPW_DEPENDENCY} {{AObjs}} Sample.make
    Link -o {{Targ}} {{AObjs}}
    SetFile {{Targ}} -t APPL -c 'MOOS' -a B
Sample          {MPW_DEPENDENCY}{MPW_DEPENDENCY} Sample.r
    Rez -rd -o {{Targ}} Sample.r -append
Count           {MPW_DEPENDENCY}{MPW_DEPENDENCY} Count.r
    Rez Count.r -o Count -append
Count           {MPW_DEPENDENCY}{MPW_DEPENDENCY} Count.a.o
    Link -w -c 'MPS ' -t MPST Count.a.o "{{Libraries}}"MacRuntime.o "{{Libraries}}"Interface.o -o Count
Memory          {MPW_DEPENDENCY}{MPW_DEPENDENCY} MemorySrc.a.o
    Link -da -t dfil -c movr -rt DRVR=12 -sg Memory MemorySrc.a.o -o Memory
"""

def _views() -> dict[str, object]:
    project = build_macos_source_project(
        project_id="mpw-aexamples",
        source_files={
            "MPW-GM/MPW/Examples/AExamples/Sample.a": SAMPLE_A,
            "MPW-GM/MPW/Examples/AExamples/SampleMisc.a": SAMPLE_MISC_A,
            "MPW-GM/MPW/Examples/AExamples/MemorySrc.a": MEMORY_SRC_A,
            "MPW-GM/MPW/Examples/AExamples/Count.a": COUNT_A,
        },
        resource_files=RESOURCES,
        build_files={"MPW-GM/MPW/Examples/AExamples/MakeFile": MAKE},
        c_header_text=SAMPLE_H,
        asm_include_text=SAMPLE_INC,
    )
    return render_macos_source_views(project)


def _routine(views: dict[str, object], name: str) -> dict[str, object]:
    routines = views["routine_views"]
    assert isinstance(routines, list)
    return next(routine for routine in routines if isinstance(routine, dict) and routine["name"] == name)


def test_initialize_render_shows_source_context_resources_and_mac_api_fact() -> None:
    initialize = _routine(_views(), "Initialize")

    assert initialize["file"].endswith("Sample.a")
    assert initialize["segment"] == "Initialize"
    assert initialize["imports"] == ["_WaitNextEvent"]
    assert initialize["records"] == ["StackFrame"]
    assert initialize["api_calls"][0]["opword"] == 0xA860
    assert initialize["api_calls"][0]["source"].endswith("Events.a")
    assert initialize["resource_xrefs"][0]["call"] == "_GetNewMBar"
    assert initialize["source_project_only"] is True


def test_go_get_rect_render_shows_resource_lookup_and_rect_callers() -> None:
    go_get_rect = _routine(_views(), "GoGetRect")

    assert go_get_rect["api_calls"][0]["name"] == "_GetResource"
    assert "resource_lookup" in go_get_rect["intent_hints"]
    caller_resource_ids = [
        xref["resource"]["symbolic_id"]
        for xref in go_get_rect["resource_xrefs"]
        if isinstance(xref.get("resource"), dict)
    ]
    assert caller_resource_ids == ["rStopRect", "rGoRect"]


def test_memory_render_shows_parameter_block_call_shape_and_intent() -> None:
    memory = _routine(_views(), "MemoryMain")

    assert memory["api_calls"][0]["name"] == "_PBHGetVInfoSync"
    assert memory["api_calls"][0]["parameter_register"] == "A0"
    assert memory["api_calls"][0]["result_register"] == "D0"
    assert memory["api_calls"][0]["family"] == "FileManager"
    assert memory["record_facts"][0]["name"] == "HVolumeParam"
    assert memory["record_facts"][0]["source"].endswith("Files.a")
    assert "volume_free_space_query" in memory["intent_hints"]


def test_count_render_shows_tool_kind_resources_and_runtime_provenance() -> None:
    product_views = _views()["product_views"]
    assert isinstance(product_views, list)
    count = next(product for product in product_views if isinstance(product, dict) and product["target"] == "Count")

    assert count["program_kind"] == "mpw_tool"
    assert count["file_type"] == "MPST"
    assert count["creator"] == "MPS "
    assert "cmdo" in count["resource_types"]
    assert count["library_inputs"] == ["{Libraries}MacRuntime.o", "{Libraries}Interface.o"]
    assert count["byte_for_byte_roundtrip"] is False


def test_render_exposes_unknowns_without_guessing_missing_facts() -> None:
    count_main = _routine(_views(), "CountMain")

    assert count_main["api_calls"][0]["name"] == "_NumToString"
    assert count_main["api_calls"][0]["package_word"] == 0xA9EE
    assert count_main["unknown_imports"] == []
    assert "byte-for-byte MPW Link/Rez roundtrip" in _views()["unsupported"]


def test_render_records_generated_mac_os_metadata_source() -> None:
    source = _views()["mac_os_metadata_source"]

    assert source == {
        "kind": "mac_os_baseline_runtime",
        "schema_version": 1,
        "generated_path": "src/generated/mac_os_runtime.json",
    }
