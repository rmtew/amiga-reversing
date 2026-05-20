from __future__ import annotations

from pathlib import Path

from amiga_reversing.disasm.macos_source_structure import (
    parse_mpw_source_files,
    parse_mpw_source_text,
)


def test_sample_source_structure_preserves_segments_routines_and_continued_imports() -> None:
    parsed = parse_mpw_source_text(
        "\n".join(
            [
                "\tINCLUDE 'LowMemEqu.a'",
                "\tINCLUDE 'Sample.inc1.a'",
                "\tEXPORT\t(QD,G):DATA",
                "\tSEG 'Initialize'",
                "Initialize\tPROC",
                "StackFrame\tRECORD\t{A6Link},DECR",
                "\tENDR",
                "\tIMPORT\tGoGetRect,AlertUser,SysEnvirons,\t\\",
                "\t\tTrapAvailable",
                "\tWITH\tStackFrame",
                "\tENDP",
                "\tSEG\t'Main'",
                "DoContentClick\tPROC",
                "\tIMPORT\tSetLight",
                "\tENDP",
                "StartUp\tMAIN",
                "\tIMPORT\t_DataInit,Initialize,\t\\",
                "\t\tEventLoop,Terminate",
                "\tENDP",
            ]
        ),
        path="MPW-GM/MPW/Examples/AExamples/Sample.a",
    )

    assert [include["path"] for include in parsed["includes"]] == ["LowMemEqu.a", "Sample.inc1.a"]
    assert parsed["exports"] == [
        {"symbol": "QD", "type": "DATA", "line": 3, "line_end": 3, "routine": None, "segment": None},
        {"symbol": "G", "type": "DATA", "line": 3, "line_end": 3, "routine": None, "segment": None},
    ]
    assert parsed["segments"] == [
        {
            "name": "Initialize",
            "line": 4,
            "line_end": 4,
            "source_fact_kind": "source_segment",
            "maps_to_observed_code_resource": False,
        },
        {
            "name": "Main",
            "line": 12,
            "line_end": 12,
            "source_fact_kind": "source_segment",
            "maps_to_observed_code_resource": False,
        },
    ]
    assert parsed["routines"] == [
        {
            "name": "Initialize",
            "kind": "proc",
            "line": 5,
            "line_end": 11,
            "segment": "Initialize",
            "source_fact_kind": "source_routine",
            "exported": False,
            "maps_to_observed_code_resource": False,
        },
        {
            "name": "DoContentClick",
            "kind": "proc",
            "line": 13,
            "line_end": 15,
            "segment": "Main",
            "source_fact_kind": "source_routine",
            "exported": False,
            "maps_to_observed_code_resource": False,
        },
        {
            "name": "StartUp",
            "kind": "main",
            "line": 16,
            "line_end": 19,
            "segment": "Main",
            "source_fact_kind": "source_entry_marker",
            "exported": False,
            "maps_to_observed_code_resource": False,
        },
    ]
    initialize_imports = [item["symbol"] for item in parsed["imports"] if item["routine"] == "Initialize"]
    assert initialize_imports == ["GoGetRect", "AlertUser", "SysEnvirons", "TrapAvailable"]
    assert [record["name"] for record in parsed["records"]] == ["StackFrame"]
    assert parsed["with_scopes"] == [
        {"targets": ["StackFrame"], "line": 10, "line_end": 10, "routine": "Initialize", "segment": "Initialize"}
    ]


def test_sample_misc_func_export_and_nested_with_scope() -> None:
    parsed = parse_mpw_source_text(
        "\n".join(
            [
                "\tINCLUDE 'Resources.a'",
                "\tIMPORT\tQD:QDGlobals",
                "\tSEG\t'Initialize'",
                "GoGetRect\tFUNC\tEXPORT",
                "StackFrame\tRECORD\t{A6Link},DECR",
                "\tENDR",
                "\tWITH\tStackFrame",
                "\tENDF",
                "\tSEG\t'Main'",
                "IsDAWindow\tFUNC\tEXPORT",
                "\tWITH\tStackFrame",
                "\tWITH\tWindowRecord",
                "\tENDF",
            ]
        ),
        path="MPW-GM/MPW/Examples/AExamples/SampleMisc.a",
    )

    assert parsed["imports"] == [
        {"symbol": "QD", "type": "QDGlobals", "line": 2, "line_end": 2, "routine": None, "segment": None}
    ]
    assert parsed["routines"][0]["name"] == "GoGetRect"
    assert parsed["routines"][0]["kind"] == "func"
    assert parsed["routines"][0]["exported"] is True
    assert parsed["routines"][0]["segment"] == "Initialize"
    assert parsed["routines"][1]["name"] == "IsDAWindow"
    assert parsed["routines"][1]["segment"] == "Main"
    assert parsed["with_scopes"][-1] == {
        "targets": ["WindowRecord"],
        "line": 12,
        "line_end": 12,
        "routine": "IsDAWindow",
        "segment": "Main",
    }


def test_memory_src_bare_main_is_source_entry_marker_not_code_one_claim() -> None:
    parsed = parse_mpw_source_text(
        "\n".join(
            [
                "\tSTRING\tPASCAL",
                "\tMAIN",
                "OLDROUTINENAMES\tSet\t1",
                "\tINCLUDE\t'Events.a'",
            ]
        ),
        path="MPW-GM/MPW/Examples/AExamples/MemorySrc.a",
    )

    assert parsed["entry_markers"] == [
        {
            "name": "MAIN",
            "kind": "source_main_entry",
            "line": 2,
            "line_end": 2,
            "segment": None,
            "program_kind_claim": None,
            "maps_to_observed_code_resource": False,
        }
    ]
    assert parsed["routines"][0]["source_fact_kind"] == "source_entry_marker"
    assert parsed["routines"][0]["maps_to_observed_code_resource"] is False


def test_parse_required_source_files_without_mapping_segments_to_asm_code_resources(tmp_path: Path) -> None:
    sources = {
        "Sample.a": "\tSEG 'Main'\nStartUp\tMAIN\n\tENDP\n",
        "SampleMisc.a": "\tSEG 'Initialize'\nGoGetRect\tFUNC\tEXPORT\n\tENDF\n",
        "Sample.inc1.a": "Point\tRECORD\t0\n\tENDR\n",
        "MemorySrc.a": "\tMAIN\n",
        "Count.a": "\tINCLUDE 'Stubs.a'\nCountMain\tPROC\n\tENDP\n",
    }
    paths: list[Path] = []
    for name, text in sources.items():
        path = tmp_path / name
        path.write_bytes(text.encode("mac_roman"))
        paths.append(path)

    parsed = parse_mpw_source_files(paths)

    assert [file["file_name"] for file in parsed["files"]] == list(sources)
    assert parsed["source_segment_mapping"] == {
        "kind": "source_membership_only",
        "maps_to_observed_code_resources": False,
        "reason": "source SEG facts are not linked to MPW/Tools/Asm CODE resources by name alone",
    }
    for file in parsed["files"]:
        assert file["encoding"] == "mac_roman"
        assert file["source_segment_mapping"]["maps_to_observed_code_resources"] is False
        for segment in file["segments"]:
            assert segment["maps_to_observed_code_resource"] is False
        for routine in file["routines"]:
            assert routine["maps_to_observed_code_resource"] is False
