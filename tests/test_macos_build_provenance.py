from __future__ import annotations

from amiga_reversing.disasm.macos_build_provenance import parse_mpw_build_text

MPW_CONTINUATION_DISPLAY = "\u00b6"
MPW_CONTINUATION_MAC_ROMAN = "\u2202"
MPW_DEPENDENCY_DISPLAY = "\u00c4"
MPW_DEPENDENCY_MAC_ROMAN = "\u0192"

SAMPLE_MAKE = f"""
AOptions        = -w -D SystemSevenOrLater

AObjs           = Sample.a.o {MPW_CONTINUATION_DISPLAY}
                    SampleMisc.a.o {MPW_CONTINUATION_DISPLAY}
                    "{{Libraries}}"MacRuntime.o {MPW_CONTINUATION_DISPLAY}
                    "{{Libraries}}"Interface.o

Sample          {MPW_DEPENDENCY_DISPLAY}{MPW_DEPENDENCY_DISPLAY} {{AObjs}} Sample.make
    Link -o {{Targ}} {{AObjs}}
    SetFile {{Targ}} -t APPL -c 'MOOS' -a B

Sample          {MPW_DEPENDENCY_DISPLAY}{MPW_DEPENDENCY_DISPLAY} Sample.r Sample.h Sample.make
    Rez -rd -o {{Targ}} Sample.r -append

Sample.a.o      {MPW_DEPENDENCY_DISPLAY}{MPW_DEPENDENCY_DISPLAY} Sample.make Sample.inc1.a Sample.a
SampleMisc.a.o  {MPW_DEPENDENCY_DISPLAY}{MPW_DEPENDENCY_DISPLAY} Sample.make Sample.inc1.a SampleMisc.a
"""


SAMPLE_MAKE_REAL_GLYPHS = SAMPLE_MAKE.replace(
    MPW_CONTINUATION_DISPLAY, MPW_CONTINUATION_MAC_ROMAN
).replace(MPW_DEPENDENCY_DISPLAY, MPW_DEPENDENCY_MAC_ROMAN)


COUNT_MEMORY_MAKEFILE = f"""
all             {MPW_DEPENDENCY_DISPLAY}{MPW_DEPENDENCY_DISPLAY}  Count Memory

Count           {MPW_DEPENDENCY_DISPLAY}{MPW_DEPENDENCY_DISPLAY}  Count.r
    Rez Count.r -o Count -append
Count           {MPW_DEPENDENCY_DISPLAY}{MPW_DEPENDENCY_DISPLAY}  Count.a.o FStubs.a.o
    Link -w -c 'MPS ' -t MPST Count.a.o FStubs.a.o {MPW_CONTINUATION_DISPLAY}
        -sn INTENV=Main {MPW_CONTINUATION_DISPLAY}
        -sn %A5Init=Main {MPW_CONTINUATION_DISPLAY}
        "{{Libraries}}"Stubs.o {MPW_CONTINUATION_DISPLAY}
        "{{Libraries}}"MacRuntime.o {MPW_CONTINUATION_DISPLAY}
        "{{Libraries}}"IntEnv.o {MPW_CONTINUATION_DISPLAY}
        "{{Libraries}}"ToolLibs.o {MPW_CONTINUATION_DISPLAY}
        "{{Libraries}}"Interface.o {MPW_CONTINUATION_DISPLAY}
        -o Count
Count.a.o       {MPW_DEPENDENCY_DISPLAY}   Count.a
    Asm Count.a
FStubs.a.o      {MPW_DEPENDENCY_DISPLAY}   FStubs.a
    Asm FStubs.a

Memory          {MPW_DEPENDENCY_DISPLAY}   MemorySrc.a.o
    Link -da -t dfil -c movr -rt DRVR=12 -sg Memory {MPW_CONTINUATION_DISPLAY}
        MemorySrc.a.o -o Memory
MemorySrc.a.o   {MPW_DEPENDENCY_DISPLAY}   MemorySrc.a
    Asm MemorySrc.a
"""


def test_sample_make_parses_options_objects_link_setfile_and_rez() -> None:
    parsed = parse_mpw_build_text(SAMPLE_MAKE, path="MPW-GM/MPW/Examples/AExamples/Sample.make")

    variables = {variable["name"]: variable for variable in parsed["variables"]}
    assert variables["AOptions"]["tokens"] == ["-w", "-D", "SystemSevenOrLater"]
    assert variables["AObjs"]["tokens"] == [
        "Sample.a.o",
        "SampleMisc.a.o",
        "{Libraries}MacRuntime.o",
        "{Libraries}Interface.o",
    ]
    sample = _product(parsed, "Sample")
    assert sample["source_view_provenance"] is True
    assert sample["executable_import_provenance"] is False
    assert sample["byte_for_byte_roundtrip"] is False
    assert sample["link"]["output"] == "Sample"
    assert sample["link"]["object_inputs"] == ["Sample.a.o", "SampleMisc.a.o"]
    assert sample["link"]["library_inputs"] == ["{Libraries}MacRuntime.o", "{Libraries}Interface.o"]
    assert sample["setfile"]["file_type"] == "APPL"
    assert sample["setfile"]["creator"] == "MOOS"
    assert sample["setfile"]["attributes"] == "B"
    assert sample["rez"][0]["resource_inputs"] == ["Sample.r"]
    assert sample["rez"][0]["append"] is True
    object_recipes = {recipe["object"]: recipe for recipe in parsed["object_recipes"]}
    assert object_recipes["Sample.a.o"]["source_inputs"] == ["Sample.a"]
    assert object_recipes["Sample.a.o"]["dependency_inputs"] == ["Sample.make", "Sample.inc1.a", "Sample.a"]
    assert object_recipes["Sample.a.o"]["binary_object_imported"] is False


def test_sample_make_accepts_real_mac_roman_mpw_glyphs() -> None:
    parsed = parse_mpw_build_text(SAMPLE_MAKE_REAL_GLYPHS, path="Sample.make")

    sample = _product(parsed, "Sample")
    assert sample["link"]["output"] == "Sample"
    assert sample["rez"][0]["resource_inputs"] == ["Sample.r"]


def test_makefile_count_recipe_records_tool_link_libraries_and_resources() -> None:
    parsed = parse_mpw_build_text(COUNT_MEMORY_MAKEFILE, path="MPW-GM/MPW/Examples/AExamples/MakeFile")

    count = _product(parsed, "Count")
    assert count["rez"][0]["resource_inputs"] == ["Count.r"]
    assert count["rez"][0]["output"] == "Count"
    assert count["link"]["program_kind"] == "mpw_tool"
    assert count["link"]["output_type"] == "MPST"
    assert count["link"]["output_creator"] == "MPS "
    assert count["link"]["object_inputs"] == ["Count.a.o", "FStubs.a.o"]
    assert count["link"]["library_inputs"] == [
        "{Libraries}Stubs.o",
        "{Libraries}MacRuntime.o",
        "{Libraries}IntEnv.o",
        "{Libraries}ToolLibs.o",
        "{Libraries}Interface.o",
    ]
    assert count["link"]["segment_names"] == ["INTENV=Main", "%A5Init=Main"]
    asm_commands = [command for command in parsed["commands"] if command["tool"] == "Asm"]
    assert asm_commands[0]["source_inputs"] == ["Count.a"]
    assert asm_commands[0]["object_outputs"] == ["Count.a.o"]


def test_makefile_memory_recipe_records_driver_link_provenance() -> None:
    parsed = parse_mpw_build_text(COUNT_MEMORY_MAKEFILE, path="MPW-GM/MPW/Examples/AExamples/MakeFile")

    memory = _product(parsed, "Memory")
    assert memory["link"]["output"] == "Memory"
    assert memory["link"]["program_kind"] == "driver"
    assert memory["link"]["output_type"] == "dfil"
    assert memory["link"]["output_creator"] == "movr"
    assert memory["link"]["resource_type"] == "DRVR=12"
    assert memory["link"]["segment_group"] == "Memory"
    assert memory["link"]["object_inputs"] == ["MemorySrc.a.o"]
    object_recipes = {recipe["object"]: recipe for recipe in parsed["object_recipes"]}
    assert object_recipes["MemorySrc.a.o"]["source_inputs"] == ["MemorySrc.a"]


def test_build_provenance_schema_keeps_source_recipes_separate_from_binary_import() -> None:
    parsed = parse_mpw_build_text(SAMPLE_MAKE, path="Sample.make")

    assert sorted(parsed.keys()) == [
        "commands",
        "kind",
        "object_recipes",
        "path",
        "products",
        "provenance_scope",
        "schema_version",
        "targets",
        "variables",
    ]
    assert parsed["schema_version"] == 1
    assert parsed["kind"] == "mpw_build_provenance"
    assert parsed["provenance_scope"] == {
        "kind": "source_build_recipe",
        "source_view_provenance": True,
        "executable_import_provenance": False,
        "maps_to_observed_asm_code_resources": False,
        "byte_for_byte_roundtrip": False,
    }


def _product(parsed: dict[str, object], target: str) -> dict[str, object]:
    products = parsed["products"]
    assert isinstance(products, list)
    for product in products:
        assert isinstance(product, dict)
        if product["target"] == target:
            return product
    raise AssertionError(target)
