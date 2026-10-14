"""Schema presentation and the emitted artifact's two real assembly paths."""
import json
import subprocess

import pytest

from amiga_reversing.disasm.binary_source import BinarySourceKind, HunkFileBinarySource
from amiga_reversing.disasm.c_backend import (
    assemble_platform_source_path_with_c_backend,
    assemble_platform_source_text_with_c_backend,
    listing_artifact_source_package_with_c_backend,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import build_target_identity
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.structure_macro_rendering import render_structure_macros
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def projection_fixture():
    fields = [{"name": "pixels", "offset": 0, "size": 4, "type": "long"},
              {"name": "mask", "offset": 4, "size": 4, "type": "long"},
              *[{"name": f"word{i}", "offset": 8 + i * 2, "size": 2, "type": "word"} for i in range(5)]]
    metadata = {"custom_structs": [{"name": "Frame", "size": 18, "fields": fields}],
                "data_block_layouts": [{"layout_id": "frames", "hunk": 0, "source_start": 0,
                    "source_end": 36, "name": "frames", "elements": [{"offset": 0, "width": 36,
                    "array_count": 2, "array_stride": 18,
                    "type_binding": {"binding_kind": "custom_struct", "bound_type_id": "Frame", "array_count": 2}}]}]}
    rows, labels = [], []
    start = 0
    for instance in range(2):
        for index, field in enumerate(fields):
            offset = instance * 18 + field["offset"]
            label = "frames" if instance == index == 0 else f"frames_{field['name']}_{instance}"
            for kind, size, text in [(8, 0, f"{label}:\n"),
                (10, field["size"], f"\tdc.{'l' if field['size'] == 4 else 'w'} "
                 + ("target_value" if index == 0 else f"${index + 1:04X}")
                 + f"\t; {field['name']}" + (" consumer verified" if index == 1 else "") + "\n")]:
                rows.append({"kind": kind, "source_section_index": 0, "source_offset": offset,
                    "source_size": size, "has_source_range": True, "start_byte": start,
                    "byte_count": len(text), "text": text})
                start += len(text)
            labels.append({"source_section_index": 0, "source_offset": offset, "name": label})
    text = "".join(r["text"] for r in rows)
    return text, metadata, {"rows": rows, "labels": labels}


def test_schema_macros_keep_prefix_array_suffix_symbols_field_order_and_annotations():
    text, metadata, plan = projection_fixture()
    rendered, report = render_structure_macros(text, canonical_source_text=text, metadata=metadata, source_plan=plan)
    assert report["instances"] == 2 and report["definitions"] == 2
    assert report["fallback_record_count"] == 0
    assert "prefix, index, pixels@0:4, mask@4:4" in rendered
    assert "\\1_mask_\\2:" in rendered
    assert "frames,0,target_value" in rendered and "frames,1,target_value" in rendered
    assert rendered.count("mask consumer verified") == 2
    assert "frames:\n" in rendered
    assert all(name not in rendered for name in ["frames_mask_0:", "frames_word4_1:"])


@pytest.mark.parametrize(("change", "reason"), [("interior_label", "noncanonical_interior_label"),
                                          ("overlap", "native_range_overlap_or_field_boundary"),
                                          ("field_count", "positional_argument_limit_9")])
def test_unsupported_records_stay_expanded_with_explicit_counts(change, reason):
    text, metadata, plan = projection_fixture()
    if change == "interior_label":
        plan["labels"][1]["name"] = "unrelated_label"
    elif change == "overlap":
        plan["rows"].append(dict(plan["rows"][1]))
    else:
        fields = metadata["custom_structs"][0]["fields"]
        fields[0]["size"] = fields[1]["size"] = 2
        fields[1]["offset"] = 2
        fields[2:] = [{"name": f"w{i}", "offset": 4 + i * 2, "size": 2} for i in range(7)]
    rendered, report = render_structure_macros(text, canonical_source_text=text, metadata=metadata, source_plan=plan)
    assert report["fallback_reason_counts"][reason] > 0
    assert report["fallback_record_count"] + report["instances"] == 2
    if change == "field_count":
        assert rendered == text and report["fallback_group_count"] == 1


def test_package_projection_requires_native_span_and_unique_content():
    text, metadata, plan = projection_fixture()
    package = 'INCBIN "assets/one.bin"\n' + text
    rendered, report = render_structure_macros(package, canonical_source_text=text, metadata=metadata, source_plan=plan)
    assert report["instances"] == 2 and 'INCBIN "assets/one.bin"' in rendered
    duplicated, report = render_structure_macros(package + text, canonical_source_text=text, metadata=metadata, source_plan=plan)
    assert report["instances"] == 0 and duplicated == package + text


def _vasm(source, tmp_path, *, hunk=False):
    path = tmp_path / "macro.s"
    path.write_text(source)
    output = tmp_path / "macro.bin"
    command = [str(PROJECT_ROOT / "tools/vasmm68k_mot.exe"), "-Fhunkexe" if hunk else "-Fbin",
               "-m68000", "-no-opt", "-nosym", "-quiet", *(["-kick1hunks"] if hunk else []),
               "-o", str(output), str(path)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return output.read_bytes()


def test_emitted_schema_macro_artifact_assembles_with_c_and_vasm(tmp_path):
    text, metadata, plan = projection_fixture()
    rendered, report = render_structure_macros(text, canonical_source_text=text, metadata=metadata, source_plan=plan)
    prefix = "target_value EQU $12345678\n SECTION section,code\n ORG $0\n"
    original, _ = assemble_platform_source_text_with_c_backend("amiga-raw", prefix + text, project_root=PROJECT_ROOT)
    rebuilt, _ = assemble_platform_source_text_with_c_backend("amiga-raw", prefix + rendered, project_root=PROJECT_ROOT)
    assert report["instances"] == 2 and rebuilt == original == _vasm(prefix + rendered, tmp_path)


@pytest.mark.parametrize("body", [" INNER \\1\n", " REPT \\1\n ENDR\n", " dc.w \\@\n"])
def test_invoked_unsupported_macro_fails_without_recursion(body):
    source = "INNER MACRO\n dc.w \\1\n ENDM\n OUTER MACRO\n" + body + " ENDM\n ORG 0\n OUTER 2\n"
    with pytest.raises(RuntimeError, match="macro expansion"):
        assemble_platform_source_text_with_c_backend("amiga-raw", source, project_root=PROJECT_ROOT)


def test_unused_complex_source_macro_quotes_comments_and_sdk_scanner_remain_compatible(tmp_path):
    source = "UNUSED MACRO\n REPT \\@\n ENDR\n ENDM\n"
    source += "Bytes MACRO\n dc.b \\1\n ENDM\n SECTION section,code\n ORG 0\n Bytes 'a,b'\n dc.b 'Bytes' ; Bytes ignored\n"
    rebuilt, _ = assemble_platform_source_text_with_c_backend("amiga-raw", source, project_root=PROJECT_ROOT)
    assert rebuilt == b"a,bBytes"
    assert _vasm(source.replace(" REPT \\@\n ENDR\n", " dc.w \\1\n"), tmp_path) == rebuilt


def test_macro_source_crlf_filepath_matches_text_assembly(tmp_path):
    source = "Record MACRO\r\n dc.w \\1\r\n ENDM\r\n SECTION section,code\r\n Record $1234\r\n"
    path = tmp_path / "crlf.s"
    path.write_bytes(source.encode("ascii"))
    from_path, _ = assemble_platform_source_path_with_c_backend("amiga-raw", path, project_root=PROJECT_ROOT)
    from_text, _ = assemble_platform_source_text_with_c_backend("amiga-raw", source, project_root=PROJECT_ROOT)
    assert from_path == from_text == b"\x12\x34"


def test_native_bound_frame_array_macro_projection_preserves_full_hunk_bytes(tmp_path):
    text, metadata, _ = projection_fixture()
    fields = metadata["custom_structs"][0]["fields"]
    binary = tmp_path / "input.hunk"
    original, _ = assemble_platform_source_text_with_c_backend("amiga-hunk",
        " SECTION section,code\n bra.b after\n dc.b " + ",".join(f"${b:02X}" for b in bytes(range(36)))
        + "\nafter:\n rts\n", output_path=binary, project_root=PROJECT_ROOT)
    source = HunkFileBinarySource(kind=BinarySourceKind.HUNK_FILE, path=binary,
        display_path=str(binary), analysis_cache_path=tmp_path / "analysis")
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    (tmp_path / "source_binary.json").write_text(json.dumps({"kind": "hunk_file", "path": str(binary)}))
    actions = [("create_manual_custom_struct", "custom_struct", {"name": "Frame", "size": 18, "fields": fields}),
        ("create_manual_data_block_layout", "data_block_layout", {"layout_id": "frames", "hunk": 0,
            "source_start": 2, "source_end": 38, "name": "frames", "default_unit": "byte"}),
        ("set_manual_data_block_element", "data_block_element", {"layout_id": "frames", "offset": 0,
            "width": 36, "kind": "struct", "array_count": 2, "array_stride": 18,
            "type_binding": {"binding_kind": "custom_struct", "bound_type_id": "Frame", "array_count": 2,
                "layout_id": "frames", "element_offset": 0, "element_width": 36,
                "type_binding_id": "frames:0:36:custom_struct:Frame", "owner_action_id": "a3"}})]
    records = [{"record": "manual_action_log_header", "version": 1, "target_identity": build_target_identity(source)}]
    records += [{"record": "manual_action", "action_id": f"a{i}", "sequence": i,
        "created_at": "2026-10-13T00:00:00+00:00", "kind": kind, key: value}
        for i, (kind, key, value) in enumerate(actions, 1)]
    (tmp_path / "manual_actions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    with effective_metadata_file(tmp_path) as path:
        projected = listing_artifact_source_package_with_c_backend(source, metadata_path=path,
            minimum_asset_size=0xFFFFFFFF, structure_macros=True, project_root=PROJECT_ROOT)
    assert projected["structure_macros"]["instances"] == 2, projected["structure_macros"]
    assert projected["assets"] == []
    rebuilt, _ = assemble_platform_source_text_with_c_backend("amiga-hunk", projected["source_text"], project_root=PROJECT_ROOT)
    assert rebuilt == original == _vasm(projected["source_text"], tmp_path, hunk=True)
