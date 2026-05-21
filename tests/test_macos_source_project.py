from __future__ import annotations

from amiga_reversing.disasm.macos_source_project import build_macos_source_project

MPW_DEPENDENCY = "\u00c4"
MPW_CONTINUATION = "\u00b6"

SAMPLE_H = """
#define rMenuBar 128
#define rWindow 128
"""

SAMPLE_INC1 = """
rMenuBar EQU 128
rWindow EQU 128
"""

SAMPLE_A = """
\tINCLUDE 'Sample.inc1.a'
\tIMPORT\t_WaitNextEvent
\tSEG\t'Initialize'
Initialize\tPROC
EventRecord\tRECORD\t0
\tENDR
\tENDP
\tSEG\t'Main'
StartUp\tMAIN
\tIMPORT\t_GetResource
\tENDP
"""

SAMPLE_MISC_A = """
\tSEG\t'Initialize'
GoGetRect\tFUNC\tEXPORT
\tENDF
"""

SAMPLE_R = """
resource 'MBAR' (rMenuBar, preload) {
};
resource 'WIND' (rWindow, preload, purgeable) {
};
"""

SAMPLE_MAKE = f"""
AObjs           = Sample.a.o {MPW_CONTINUATION}
                    SampleMisc.a.o {MPW_CONTINUATION}
                    "{{Libraries}}"MacRuntime.o

Sample          {MPW_DEPENDENCY}{MPW_DEPENDENCY} {{AObjs}} Sample.make
    Link -o {{Targ}} {{AObjs}}
    SetFile {{Targ}} -t APPL -c 'MOOS' -a B

Sample          {MPW_DEPENDENCY}{MPW_DEPENDENCY} Sample.r Sample.h Sample.make
    Rez -rd -o {{Targ}} Sample.r -append

Sample.a.o      {MPW_DEPENDENCY}{MPW_DEPENDENCY} Sample.make Sample.inc1.a Sample.a
SampleMisc.a.o  {MPW_DEPENDENCY}{MPW_DEPENDENCY} Sample.make Sample.inc1.a SampleMisc.a
"""

def _sample_project() -> dict[str, object]:
    return build_macos_source_project(
        project_id="mpw-sample",
        source_files={
            "MPW-GM/MPW/Examples/AExamples/Sample.a": SAMPLE_A,
            "MPW-GM/MPW/Examples/AExamples/SampleMisc.a": SAMPLE_MISC_A,
            "MPW-GM/MPW/Examples/AExamples/Sample.inc1.a": SAMPLE_INC1,
        },
        resource_files={"MPW-GM/MPW/Examples/AExamples/Sample.r": SAMPLE_R},
        build_files={"MPW-GM/MPW/Examples/AExamples/Sample.make": SAMPLE_MAKE},
        c_header_text=SAMPLE_H,
        asm_include_text=SAMPLE_INC1,
    )


def test_source_project_model_represents_sample_without_binary_runtime() -> None:
    project = _sample_project()

    assert project["kind"] == "macos_source_project"
    assert project["platform"] == "macos"
    assert project["project_model"] == {
        "kind": "source_first",
        "requires_built_binary": False,
        "requires_rom": False,
        "requires_emulator": False,
        "imports_executable_code_resources": False,
        "maps_source_segments_to_observed_code_resources": False,
    }
    assert "executable CODE resource import" in project["unsupported"]


def test_source_project_entities_cover_sources_resources_and_build_provenance() -> None:
    entities = _sample_project()["entities"]

    assert [segment["name"] for segment in entities["segments"]] == ["Initialize", "Main", "Initialize"]
    assert [routine["name"] for routine in entities["routines"]] == ["Initialize", "StartUp", "GoGetRect"]
    assert entities["routines"][1]["source_fact_kind"] == "source_entry_marker"
    assert [resource["type"] for resource in entities["resource_declarations"]] == ["MBAR", "WIND"]
    assert entities["resource_declarations"][0]["numeric_id"] == 128
    assert entities["build_products"][0]["target"] == "Sample"
    assert entities["build_products"][0]["source_view_provenance"] is True
    assert entities["build_products"][0]["executable_import_provenance"] is False


def test_source_project_attaches_generated_mac_os_fact_annotations() -> None:
    annotations = _sample_project()["mac_os_annotations"]
    keyed = {(annotation["kind"], annotation["name"]): annotation for annotation in annotations}

    assert keyed[("mac_os_call", "_WaitNextEvent")]["fact"]["opword"] == 0xA860
    assert keyed[("mac_os_call", "_GetResource")]["fact"]["opword"] == 0xA9A0
    assert keyed[("mac_os_record", "EventRecord")]["fact"]["size"] == 16
    assert _sample_project()["mac_os_metadata_source"]["generated_path"] == "src/generated/mac_os_runtime.json"


def test_source_project_links_resource_xrefs_without_observed_code_mapping() -> None:
    project = _sample_project()

    assert project["resource_xrefs"] == [
        {
            "source": "MPW-GM/MPW/Examples/AExamples/Sample.a",
            "line": 11,
            "call": "_GetResource",
            "resource_type": None,
            "id_source": "caller_supplied_parameter",
            "resource": None,
        }
    ]
    assert all(
        segment["maps_to_observed_code_resource"] is False
        for source_file in project["source_files"]
        for segment in source_file["segments"]
    )
