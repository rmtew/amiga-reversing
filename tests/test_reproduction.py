from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from amiga_reversing.disasm import reproduction
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    DiskEntryBinarySource,
    HunkFileBinarySource,
    RawAddressModel,
    RawBinarySource,
    write_source_descriptor,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_text
from amiga_reversing.disasm.reproduction import (
    diff_issues_for_lookup,
    first_diff,
    grouped_diff_ranges,
    parse_assembler_diagnostics,
    reproduction_input_stamp,
    reproduction_options_for_target,
    run_reproduction,
)
from amiga_reversing.disasm.reproduction_report import (
    ReportContext,
    ReproductionOutcome,
    ReproductionReportStatus,
    RoundTripReportBuilder,
)
from tests.listing_row_fixtures import serialize_row
from tests.listing_types_fixtures import ListingRow


def _rows(*rows: ListingRow) -> list[dict[str, object]]:
    return [dict(serialize_row(row)) for row in rows]


def _row_for_section_offset(
    rows: list[dict[str, object]],
    section_index: int | None,
    offset: int,
) -> dict[str, object] | None:
    for row_index, row in enumerate(rows):
        start_offset = row.get("start_offset")
        end_offset = row.get("end_offset")
        if not isinstance(start_offset, int) or not isinstance(end_offset, int):
            continue
        row_section_index = row.get("section_index")
        if section_index is not None and isinstance(row_section_index, int) and row_section_index != section_index:
            continue
        if start_offset <= offset < end_offset:
            payload = dict(row)
            payload["row_index"] = row_index
            return payload
    return None


def _diff_issues_for_rows(
    diff_ranges: list[dict[str, object]],
    rows: list[dict[str, object]],
    *,
    file_layout: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    return diff_issues_for_lookup(
        diff_ranges,
        lambda section_index, offset: _row_for_section_offset(rows, section_index, offset),
        file_layout=file_layout,
    )


def _u16(value: int) -> bytes:
    return value.to_bytes(2, "big")


def _u32(value: int) -> bytes:
    return value.to_bytes(4, "big")


def _empty_metadata() -> dict[str, object]:
    return {
        "target_type": "program",
        "entry_register_seeds": [],
        "bootblock": None,
        "resident": None,
        "library": None,
        "custom_structs": [],
        "rsset_layout_regions": [],
        "seeded_entities": [],
        "seeded_code_labels": [],
        "seeded_code_entrypoints": [],
        "absolute_code_labels": [],
        "execution_views": [],
        "suppressed_seeded_items": [],
    }


def _hunk_with_reloc_order(offsets: list[int]) -> bytes:
    return _hunk_with_reloc_groups([(1, offsets)])


def _hunk_with_reloc_groups(groups: list[tuple[int, list[int]]]) -> bytes:
    payload = bytearray()
    payload += _u32(1011)
    payload += _u32(0)
    payload += _u32(2)
    payload += _u32(0)
    payload += _u32(1)
    payload += _u32(2)
    payload += _u32(1)
    payload += _u32(1001)
    payload += _u32(2)
    payload += b"\x00" * 8
    payload += _u32(1004)
    for target_section, offsets in groups:
        payload += _u32(len(offsets))
        payload += _u32(target_section)
        for offset in offsets:
            payload += _u32(offset)
    payload += _u32(0)
    payload += _u32(1010)
    payload += _u32(1001)
    payload += _u32(1)
    payload += b"\x4e\x75\x00\x00"
    payload += _u32(1010)
    return bytes(payload)


def _mock_c_compare_profile(original: bytes, rebuilt: bytes) -> dict[str, object]:
    exact = original == rebuilt
    return {
        "facts_v2_reproduction_compare": True,
        "reproduction_compare_status_id": 1 if exact else 3,
        "reproduction_compare_exactness_id": 1 if exact else 3,
        "reproduction_compare_issue_group_flags": 0 if exact else 1,
        "reproduction_compare_payload_exact": exact,
        "reproduction_compare_relocation_semantics_exact": exact,
        "reproduction_compare_content_exact": exact,
        "reproduction_compare_container_oddity": False,
    }


def test_round_trip_report_builder_completed_shape(tmp_path: Path) -> None:
    builder = RoundTripReportBuilder(
        ReportContext(
            target_name="demo",
            started_at=10.0,
            input_stamp={
                "assembler_cpu": "any",
                "analysis_backend": "facts_v2",
                "original_size": 4,
                "original_sha256": "orig",
            },
            assembler="our",
            backend="amiga-hunk",
            source_path=tmp_path / "source.s",
            rebuilt_path=tmp_path / "rebuilt.bin",
        )
    )

    report = builder.completed(
        ReproductionOutcome(
            status=ReproductionReportStatus.EXACT,
            exact=True,
            original_size=4,
            rebuilt_size=4,
            rebuilt_sha256="rebuilt",
            canonical_rebuilt_size=4,
            canonical_rebuilt_sha256="rebuilt",
            canonical_rebuilt_path=tmp_path / "rebuilt.bin",
            first_diff=None,
            diff_ranges=[],
            canonical_diff_ranges=[],
            file_layout=[],
            row_mappings=[],
            issues=[],
            assembler_diagnostics=[],
            assembler_stdout="",
            assembler_stderr="",
            file_shape_adjustments=[],
            file_shape_diagnostics=[],
            canonical_file_shape_diagnostics=[],
            comparison={"full_file_exact": True},
            listing_profile={"generation": "facts_v2_asm_source"},
            profile={"total_seconds": 0.1},
        )
    )

    assert report["target"] == "demo"
    assert report["status"] == "exact"
    assert report["exact"] is True
    assert report["canonical_rebuilt_path"] == str(tmp_path / "rebuilt.bin")
    assert report["comparison"] == {"full_file_exact": True}
    assert report["listing_profile"] == {"generation": "facts_v2_asm_source"}
    assert report["profile"] == {"total_seconds": 0.1}


def test_round_trip_report_builder_error_shape(tmp_path: Path) -> None:
    builder = RoundTripReportBuilder(
        ReportContext(
            target_name="demo",
            started_at=10.0,
            input_stamp={},
            assembler="our",
            backend="amiga-hunk",
            source_path=tmp_path / "source.s",
            rebuilt_path=tmp_path / "rebuilt.bin",
        )
    )

    report = builder.error(
        status=ReproductionReportStatus.TOOL_ERROR,
        tool_error="boom",
        issues=[{"kind": "tool", "message": "boom"}],
        profile={"total_seconds": 0.1},
    )

    assert report["status"] == "tool_error"
    assert report["tool_error"] == "boom"
    assert report["issues"] == [{"kind": "tool", "message": "boom"}]
    assert report["profile"] == {"total_seconds": 0.1}


def test_reproduction_diff_finds_first_byte_and_grouped_ranges() -> None:
    original = b"\x00\x01\x02\x03\x04"
    rebuilt = b"\x00\xff\xfe\x03"

    assert first_diff(original, rebuilt) == {"offset": 1, "original": 1, "rebuilt": 255}
    assert grouped_diff_ranges(original, rebuilt) == [
        {"start": 1, "end": 3, "length": 2, "original_hex": "0102", "rebuilt_hex": "fffe"},
        {"start": 4, "end": 5, "length": 1, "original_hex": "04", "rebuilt_hex": ""},
    ]
    assert reproduction._first_diff_from_ranges(original, rebuilt, grouped_diff_ranges(original, rebuilt)) == {
        "offset": 1,
        "original": 1,
        "rebuilt": 255,
    }

def test_comparison_profile_shape_diagnostics_expands_c_transport() -> None:
    diagnostics = reproduction._comparison_profile_shape_diagnostics(
        {
            "reproduction_compare_file_shape_diagnostics": [
                {"kind": "atari_header_field_mismatch", "field": "symbol_size", "original": 4, "rebuilt": 0},
                {"kind": "atari_header_field_mismatch", "field": "flags", "original": 1, "rebuilt": 0},
            ]
        },
        "reproduction_compare",
    )

    assert diagnostics[0] == {
        "kind": "atari_header_field_mismatch",
        "field": "symbol_size",
        "original": 4,
        "rebuilt": 0,
        "group": "original_file_structure",
        "source": "facts_v2_reproduction_compare",
    }
    assert diagnostics[1]["field"] == "flags"

def test_reproduction_diff_maps_ranges_to_rows() -> None:
    rows = _rows(
        ListingRow(
            row_id="r0",
            kind="data",
            text="dc.b",
            addr=0x100,
            start_offset=1,
            end_offset=3,
            stable_key="s0:1:data",
            opcode_or_directive="DC.B",
            operand_text="$01,$02",
        )
    )

    issues = _diff_issues_for_rows([{"start": 1, "end": 3, "length": 2}], rows)

    assert issues[0]["row_index"] == 0
    assert issues[0]["addr"] == 0x100
    assert issues[0]["stable_key"] == "s0:1:data"


def test_reproduction_diff_uses_file_layout_before_mapping_rows() -> None:
    rows = _rows(
        ListingRow(row_id="text", kind="instruction", text="rts\n", section_index=0, start_offset=0, end_offset=2, addr=0),
        ListingRow(row_id="data", kind="data", text="dc.w 1\n", section_index=1, start_offset=0, end_offset=2, addr=0x200),
    )

    layout = [
        {"kind": "header", "file_start": 0, "file_end": 28, "length": 28},
        {
            "kind": "section_payload",
            "file_start": 28,
            "file_end": 30,
            "length": 2,
            "section_index": 0,
            "hunk": 0,
            "section_offset_start": 0,
        },
        {
            "kind": "section_payload",
            "file_start": 30,
            "file_end": 32,
            "length": 2,
            "section_index": 1,
            "hunk": 1,
            "section_offset_start": 0,
        },
    ]
    issues = _diff_issues_for_rows([{"start": 30, "end": 31, "length": 1}], rows, file_layout=layout)

    assert issues[0]["row_index"] == 1
    assert issues[0]["addr"] == 0x200
    assert issues[0]["section_index"] == 1
    assert issues[0]["hunk"] == 1
    assert issues[0]["section_offset"] == 0


def test_reproduction_diff_uses_artifact_row_lookup() -> None:
    layout = [
        {"kind": "header", "file_start": 0, "file_end": 24, "length": 24},
        {
            "kind": "section_payload",
            "file_start": 32,
            "file_end": 36,
            "length": 4,
            "section_index": 0,
            "hunk": 0,
            "section_offset_start": 0,
        },
    ]

    def lookup(section_index: int | None, offset: int) -> dict[str, object] | None:
        assert section_index == 0
        assert offset == 0
        return {
            "row_index": 7,
            "addr": 0,
            "section_index": 0,
            "start_offset": 0,
            "end_offset": 2,
            "stable_key": "s0:00000000:instruction:7",
        }

    issues = diff_issues_for_lookup([{"start": 32, "end": 33, "length": 1}], lookup, file_layout=layout)

    assert issues[0]["kind"] == "diff"
    assert issues[0]["row_index"] == 7
    assert issues[0]["stable_key"] == "s0:00000000:instruction:7"


def test_reproduction_diff_reports_header_ranges_without_row() -> None:
    layout = [{"kind": "header", "file_start": 0, "file_end": 28, "length": 28}]
    issues = diff_issues_for_lookup([{"start": 2, "end": 3, "length": 1}], None, file_layout=layout)

    assert issues[0]["kind"] == "diff_header"
    assert issues[0]["row_index"] is None
    assert issues[0]["layout_kind"] == "header"


def test_reproduction_diff_maps_amiga_hunk_payload_after_header() -> None:
    rows = _rows(
        ListingRow(
            row_id="code",
            kind="instruction",
            text="rts\n",
            section_index=0,
            start_offset=0,
            end_offset=2,
            addr=0,
        )
    )

    layout = [
        {
            "kind": "section_payload",
            "file_start": 32,
            "file_end": 36,
            "length": 4,
            "section_index": 0,
            "hunk": 0,
            "section_offset_start": 0,
        }
    ]
    issues = _diff_issues_for_rows([{"start": 32, "end": 33, "length": 1}], rows, file_layout=layout)

    assert issues[0]["row_index"] == 0
    assert issues[0]["section_offset"] == 0


def test_reproduction_assembler_diagnostics_map_to_rows() -> None:
    rows = _rows(
        ListingRow(row_id="r0", kind="directive", text="section\n"),
        ListingRow(row_id="r1", kind="instruction", text="bad\n", addr=0x20),
    )

    diagnostics = parse_assembler_diagnostics("demo.s:2: bad operand", rows=rows)

    assert diagnostics[0]["row_index"] == 1
    assert diagnostics[0]["addr"] == 0x20


def test_run_reproduction_captures_assembler_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x4e\x75")
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    calls: list[dict[str, object]] = []

    def render_source(*args: object, **kwargs: object) -> tuple[str, dict[str, object]]:
        calls.append({"args": args, "kwargs": kwargs})
        return "bad\n", {"facts_v2": {"asm_source_refused": False}}

    monkeypatch.setattr(
        reproduction,
        "listing_artifact_source_text_with_c_backend_profile",
        render_source,
    )
    assemble_calls: list[dict[str, object]] = []

    def fail_assemble(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object]]:
        assemble_calls.append({"args": args, "kwargs": kwargs})
        raise RuntimeError("demo.s:1: bad operand")

    monkeypatch.setattr(reproduction, "assemble_platform_source_text_with_c_backend", fail_assemble)

    report = run_reproduction("demo", source_assembly_debug=True)

    assert report["status"] == "assembler_error"
    assert "target_cpu" not in calls[0]["kwargs"]
    assert assemble_calls[0]["kwargs"]["target_cpu"] == "any"
    assert cast(list[dict[str, object]], report["assembler_diagnostics"])[0]["message"] == "demo.s:1: bad operand"
    assert cast(list[dict[str, object]], report["assembler_diagnostics"])[0]["row_index"] is None
    assert (target_dir / "reproduction.json").exists()


def test_run_reproduction_exact_match_skips_file_layout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    original = b"\x00\x00\x03\xf3"
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    render_calls: list[dict[str, object]] = []
    assemble_calls: list[dict[str, object]] = []

    def render_exact(*args: object, **kwargs: object) -> tuple[str, dict[str, object]]:
        render_calls.append({"args": args, "kwargs": kwargs})
        return "dc.l $000003F3\n", {"facts_v2": {"asm_source_refused": False}, "source_bytes": len(original)}

    def assemble_exact(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object]]:
        assemble_calls.append({"args": args, "kwargs": kwargs})
        output_path = kwargs.get("output_path")
        if isinstance(output_path, Path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(original)
        return original, {"assemble_c_api": True}

    monkeypatch.setattr(
        reproduction,
        "listing_artifact_source_text_with_c_backend_profile",
        render_exact,
    )
    monkeypatch.setattr(reproduction, "assemble_platform_source_text_with_c_backend", assemble_exact)
    monkeypatch.setattr(
        reproduction,
        "reproduction_compare_rebuilt_bytes_with_c_backend_profile",
        lambda _source, rebuilt_bytes, **_kwargs: _mock_c_compare_profile(original, rebuilt_bytes),
    )

    def fail_layout(*args: object, **kwargs: object) -> list[dict[str, object]]:
        raise AssertionError("exact reproduction should not need file layout")

    monkeypatch.setattr(reproduction, "file_layout_for_binary_source", fail_layout)

    report = run_reproduction("demo", project_root=tmp_path, profile=True, source_assembly_debug=True)

    assert report["status"] == "exact"
    assert report["file_layout"] == []
    assert "output_path" not in render_calls[0]["kwargs"]
    assert assemble_calls[0]["kwargs"]["output_path"] == tmp_path / "bin" / "rebuilt" / "demo" / "rebuilt.bin"
    assert report["canonical_rebuilt_path"] == str(tmp_path / "bin" / "rebuilt" / "demo" / "rebuilt.bin")
    assert (tmp_path / "bin" / "rebuilt" / "demo" / "rebuilt.bin").exists()
    assert cast(dict[str, object], report["profile"])["file_layout_seconds"] == 0.0


def test_run_reproduction_uses_listing_artifact_source_assembly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    original = b"\x00\x00\x03\xf3"
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    render_calls: list[dict[str, object]] = []
    assemble_calls: list[dict[str, object]] = []

    def render_source(*args: object, **kwargs: object) -> tuple[str, dict[str, object]]:
        render_calls.append({"args": args, "kwargs": kwargs})
        return "dc.l $000003F3\n", {"generation": "facts_v2_asm_source", "facts_v2": {"asm_source_refused": False}}

    def assemble_source(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object]]:
        assemble_calls.append({"args": args, "kwargs": kwargs})
        output_path = kwargs.get("output_path")
        if isinstance(output_path, Path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(original)
        return original, {"assemble_c_api": True, "total_seconds": 0.02}

    monkeypatch.setattr(reproduction, "listing_artifact_source_text_with_c_backend_profile", render_source)
    monkeypatch.setattr(reproduction, "assemble_platform_source_text_with_c_backend", assemble_source)
    monkeypatch.setattr(
        reproduction,
        "reproduction_compare_rebuilt_bytes_with_c_backend_profile",
        lambda _source, rebuilt_bytes, **_kwargs: _mock_c_compare_profile(original, rebuilt_bytes),
    )

    report = run_reproduction("demo", project_root=tmp_path, profile=True, source_assembly_debug=True)

    assert report["status"] == "exact"
    assert report["listing_profile"] == {
        "generation": "facts_v2_asm_source",
        "facts_v2": {"asm_source_refused": False},
    }
    assert cast(dict[str, object], report["profile"])["listing_artifact_source_assembly"] == 1.0
    assert "output_path" not in render_calls[0]["kwargs"]
    assert assemble_calls[0]["kwargs"]["output_path"] == tmp_path / "bin" / "rebuilt" / "demo" / "rebuilt.bin"
    assert not (tmp_path / "bin" / "rebuilt" / "demo" / "source.s").exists()


def test_run_reproduction_preserves_pre_rendered_source_profile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    original = b"\x00\x00\x03\xf3"
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    monkeypatch.setattr(
        reproduction,
        "listing_artifact_source_text_with_c_backend_profile",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("source should already be rendered")),
    )
    source_profile = {
        "generation": "facts_v2_listing_artifact_source_text",
        "facts_v2": {"asm_source_refused": False, "asm_source_bytes": 16},
        "timing": {"total_seconds": 0.125},
    }

    def assemble_source(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object]]:
        output_path = kwargs.get("output_path")
        if isinstance(output_path, Path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(original)
        return original, {"assemble_c_api": True, "total_seconds": 0.02}

    monkeypatch.setattr(reproduction, "assemble_platform_source_text_with_c_backend", assemble_source)
    monkeypatch.setattr(
        reproduction,
        "reproduction_compare_rebuilt_bytes_with_c_backend_profile",
        lambda _source, rebuilt_bytes, **_kwargs: _mock_c_compare_profile(original, rebuilt_bytes),
    )

    report = run_reproduction(
        "demo",
        project_root=tmp_path,
        profile=True,
        source_assembly_debug=True,
        pre_rendered_source_text="dc.l $000003F3\n",
        pre_rendered_source_profile=source_profile,
    )

    assert report["status"] == "exact"
    assert report["listing_profile"] == source_profile
    profile = cast(dict[str, object], report["profile"])
    assert profile["render_seconds"] == 0.125
    assert profile["reused_source_text"] == 1.0
    assert (tmp_path / "bin" / "rebuilt" / "demo" / "source.s").exists()


def test_run_reproduction_uses_listing_artifact_source_assembly_for_raw_binary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    original = b"\x4E\x75"
    binary_path.write_bytes(original)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=0x4000,
        entrypoint=0x4000,
        code_start_offset=0,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    monkeypatch.setattr(
        reproduction,
        "facts_v2_direct_rebuild_project_source_with_c_backend_profile",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("raw direct rebuild should not run")),
    )
    render_calls: list[dict[str, object]] = []
    assemble_calls: list[dict[str, object]] = []

    def render_source(*args: object, **kwargs: object) -> tuple[str, dict[str, object]]:
        render_calls.append({"args": args, "kwargs": kwargs})
        return "\trts\n", {"generation": "facts_v2_asm_source", "facts_v2": {"asm_source_refused": False}}

    def assemble_source(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object]]:
        assemble_calls.append({"args": args, "kwargs": kwargs})
        output_path = kwargs.get("output_path")
        if isinstance(output_path, Path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(original)
        return original, {"assemble_c_api": True, "total_seconds": 0.02}

    monkeypatch.setattr(reproduction, "listing_artifact_source_text_with_c_backend_profile", render_source)
    monkeypatch.setattr(reproduction, "assemble_platform_source_text_with_c_backend", assemble_source)
    monkeypatch.setattr(
        reproduction,
        "reproduction_compare_rebuilt_bytes_with_c_backend_profile",
        lambda _source, rebuilt_bytes, **_kwargs: _mock_c_compare_profile(original, rebuilt_bytes),
    )

    report = run_reproduction("demo", project_root=tmp_path, profile=True, source_assembly_debug=True)

    assert report["status"] == "exact"
    assert report["backend"] == "amiga-raw"
    profile = cast(dict[str, object], report["profile"])
    assert profile["listing_artifact_source_assembly"] == 1.0
    assert "facts_v2_direct_rebuild_c_api" not in profile
    assert "output_path" not in render_calls[0]["kwargs"]
    assert assemble_calls[0]["kwargs"]["output_path"] == tmp_path / "bin" / "rebuilt" / "demo" / "rebuilt.bin"


def test_run_reproduction_uses_facts_v2_direct_rebuild_fast_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    original = b"\x00\x00\x03\xf3"
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    monkeypatch.setattr(
        reproduction,
        "listing_artifact_source_text_with_c_backend_profile",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("source render should not run")),
    )
    monkeypatch.setattr(
        reproduction,
        "assemble_platform_source_text_with_c_backend",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("separate assemble should not run")),
    )
    calls: list[dict[str, object]] = []

    def direct(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object], dict[str, object]]:
        calls.append({"args": args, "kwargs": kwargs})
        assert kwargs["compare_original"] is True
        output_path = kwargs.get("output_path")
        if isinstance(output_path, Path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(original)
        return (
            original,
            {"generation": "facts_v2_asm_source", "facts_v2": {"asm_source_refused": False, "asm_source_bytes": 32}},
            {
                "facts_v2_direct_rebuild": True,
                "direct_rebuild_refused": False,
                "direct_rebuild_compared": True,
                "direct_rebuild_exact": True,
                "direct_compare_status_id": 1,
                "direct_compare_exactness_id": 1,
                "direct_compare_issue_group_flags": 0,
                "rebuilt_bytes": len(original),
            },
        )

    monkeypatch.setattr(reproduction, "facts_v2_direct_rebuild_project_source_with_c_backend_profile", direct)

    report = run_reproduction("demo", project_root=tmp_path, profile=True)

    assert report["status"] == "exact"
    assert report["listing_profile"] == {
        "generation": "facts_v2_asm_source",
        "facts_v2": {"asm_source_refused": False, "asm_source_bytes": 32},
    }
    profile = cast(dict[str, object], report["profile"])
    assert profile["facts_v2_direct_rebuild_c_api"] == 1.0
    assert "listing_artifact_source_assembly" not in profile
    assert calls[0]["kwargs"]["output_path"] == tmp_path / "bin" / "rebuilt" / "demo" / "rebuilt.bin"
    assert not (tmp_path / "bin" / "rebuilt" / "demo" / "source.s").exists()


def test_run_reproduction_accepts_lossy_hunk_reloc32_direct_rebuild_refusal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    original = b"\x00\x00\x03\xf3"
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    source_profile = {
        "generation": "facts_v2_asm_source",
        "facts_v2": {
            "asm_source_refused": False,
            "asm_source_lossy_numeric_hunk_relocations": 0,
            "unassemblable_hunk_data_relocations": 1,
        },
    }
    direct_profile = {
        "facts_v2_direct_rebuild": True,
        "direct_rebuild_refused": True,
        "direct_rebuild_refusal_reason": "lossy_numeric_hunk_relocations",
    }

    def direct(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object], dict[str, object]]:
        raise reproduction.FactsV2DirectRebuildRefused(source_profile, direct_profile)

    monkeypatch.setattr(reproduction, "facts_v2_direct_rebuild_project_source_with_c_backend_profile", direct)
    monkeypatch.setattr(
        reproduction,
        "listing_artifact_source_text_with_c_backend_profile",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("direct rebuild refusal must not render source")),
    )

    report = run_reproduction("demo", project_root=tmp_path, profile=True)

    assert report["status"] == "accepted_mismatch"
    assert report["accepted_mismatch_kind"] == "lossy_hunk_reloc32"
    assert "direct rebuild refused" in str(report["accepted_mismatch_reason"])
    assert report["tool_error"] is None
    profile = cast(dict[str, object], report["profile"])
    assert profile["facts_v2_direct_rebuild_refusal_reason"] == "lossy_numeric_hunk_relocations"
    assert "listing_artifact_source_assembly" not in profile


def test_run_reproduction_direct_source_compare_does_not_override_direct_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(reproduction.FACTS_V2_DIRECT_SOURCE_COMPARE_ENV, "1")
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    original = _hunk_with_reloc_order([0])
    direct_payload = bytearray(original)
    direct_payload[-1] ^= 1
    direct_bytes = bytes(direct_payload)
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    source_profile = {
        "generation": "facts_v2_asm_source",
        "facts_v2": {"asm_source_refused": False, "asm_source_bytes": 32},
    }

    def direct(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object], dict[str, object]]:
        output_path = kwargs.get("output_path")
        if isinstance(output_path, Path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(direct_bytes)
        return (
            direct_bytes,
            source_profile,
            {"facts_v2_direct_rebuild": True, "direct_rebuild_refused": False, "rebuilt_bytes": len(direct_bytes)},
        )

    def render_source(*args: object, **kwargs: object) -> tuple[str, dict[str, object]]:
        return "dc.l $000003F3\n", source_profile

    def assemble_source(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object]]:
        assert kwargs.get("output_path") is None
        return original, {"assemble_c_api": True, "total_seconds": 0.01}

    monkeypatch.setattr(reproduction, "facts_v2_direct_rebuild_project_source_with_c_backend_profile", direct)
    monkeypatch.setattr(reproduction, "listing_artifact_source_text_with_c_backend_profile", render_source)
    monkeypatch.setattr(reproduction, "assemble_platform_source_text_with_c_backend", assemble_source)
    monkeypatch.setattr(
        reproduction,
        "reproduction_compare_rebuilt_bytes_with_c_backend_profile",
        lambda _source, rebuilt_bytes, **_kwargs: _mock_c_compare_profile(original, rebuilt_bytes),
    )
    monkeypatch.setattr(
        reproduction,
        "apply_reproduction_output_policy",
        lambda *_args, **_kwargs: pytest.fail("normal direct rebuild should not use Python output policy"),
    )

    report = run_reproduction("demo", project_root=tmp_path, profile=True)

    assert report["status"] == "binary_mismatch"
    assert (tmp_path / "bin" / "rebuilt" / "demo" / "rebuilt.bin").read_bytes() == direct_bytes
    profile = cast(dict[str, object], report["profile"])
    assert profile["facts_v2_direct_source_compare"] == 1.0
    assert profile["facts_v2_direct_source_match"] == 0.0
    assert profile["facts_v2_direct_source_mismatch"] == 1.0
    assert profile["facts_v2_source_full_file_exact"] == 1.0
    assert profile["facts_v2_source_content_exact"] == 1.0
    assert profile["facts_v2_source_payload_exact"] == 1.0
    assert "facts_v2_direct_source_compare_fell_back" not in profile
    assert report["direct_source_exact"] is True
    assert report["direct_source_assembler"] == "our"
    assert report["direct_source_diff_range_count"] == 0
    assert report["direct_source_first_diff"] is None


def test_run_reproduction_direct_compare_exact_skips_python_diff(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    original = b"\x00\x00\x03\xf3"
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    source_profile = {
        "generation": "facts_v2_asm_source",
        "facts_v2": {"asm_source_refused": False, "asm_source_bytes": 32},
    }

    def direct(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object], dict[str, object]]:
        assert kwargs.get("compare_original") is True
        output_path = kwargs.get("output_path")
        if isinstance(output_path, Path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(original)
        return (
            original,
            source_profile,
            {
                "facts_v2_direct_rebuild": True,
                "direct_rebuild_refused": False,
                "direct_rebuild_compared": True,
                "direct_rebuild_exact": True,
                "rebuilt_bytes": len(original),
            },
        )

    monkeypatch.setattr(reproduction, "facts_v2_direct_rebuild_project_source_with_c_backend_profile", direct)
    monkeypatch.setattr(
        reproduction,
        "grouped_diff_ranges",
        lambda *_args, **_kwargs: pytest.fail("direct exact fast path should skip Python diff"),
    )

    report = run_reproduction("demo", project_root=tmp_path, profile=True)

    assert report["status"] == "exact"
    assert report["exact"] is True
    assert report["diff_ranges"] == []
    assert report["comparison"]["canonical_full_file_exact"] is True
    assert report["direct_source_exact"] is None
    assert report["direct_source_assembler"] is None
    profile = cast(dict[str, object], report["profile"])
    assert profile["facts_v2_direct_exact_fast_path"] == 1.0
    assert profile["facts_v2_direct_rebuild_exact"] == 1.0


def test_run_reproduction_direct_compare_semantic_container_oddity_skips_python_diff(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    metadata = _empty_metadata()
    metadata["reproduction"] = {"requested_exactness": "content"}
    (target_dir / "target_metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )
    binary_path = tmp_path / "demo.bin"
    original = b"\x00\x00\x03\xf3\x00\x00\x03\xf2"
    rebuilt = b"\x00\x00\x03\xf3"
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    source_profile = {
        "generation": "facts_v2_asm_source",
        "facts_v2": {"asm_source_refused": False, "asm_source_bytes": 32},
    }

    def direct(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object], dict[str, object]]:
        output_path = kwargs.get("output_path")
        if isinstance(output_path, Path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(rebuilt)
        return (
            rebuilt,
            source_profile,
            {
                "facts_v2_direct_rebuild": True,
                "direct_rebuild_refused": False,
                "direct_rebuild_compared": True,
                "direct_rebuild_exact": False,
                "direct_compare_status": "semantic_container_oddity",
                "direct_compare_payload_exact": True,
                "direct_compare_relocation_semantics_exact": True,
                "direct_compare_semantic_exact": True,
                "direct_compare_container_oddity": True,
                "direct_compare_status_id": 2,
                "direct_compare_exactness_id": 2,
                "direct_compare_issue_group_flags": 4 | 32 | 256,
                "direct_compare_source_hints": [
                    {"issue_group_flags": 32, "section_index": 0, "offset": 4},
                ],
                "rebuilt_bytes": len(rebuilt),
                "original_bytes": len(original),
            },
        )

    monkeypatch.setattr(reproduction, "facts_v2_direct_rebuild_project_source_with_c_backend_profile", direct)
    monkeypatch.setattr(
        reproduction,
        "grouped_diff_ranges",
        lambda *_args, **_kwargs: pytest.fail("direct semantic fast path should skip Python diff"),
    )

    def row_for_section_offset(section_index: int | None, offset: int) -> Mapping[str, object] | None:
        if section_index == 0 and offset == 4:
            return {
                "row_index": 9,
                "section_index": 0,
                "addr": 0x104,
                "stable_key": "row-9",
                "text": "dc.l target",
            }
        return None

    report = run_reproduction(
        "demo", project_root=tmp_path, profile=True, row_for_section_offset=row_for_section_offset
    )

    assert report["status"] == "exact"
    assert report["exact"] is True
    assert report["original_size"] == len(original)
    assert report["rebuilt_size"] == len(rebuilt)
    assert report["comparison"]["full_file_exact"] is False
    assert report["comparison"]["content_exact"] is True
    assert report["comparison"]["status"] == "semantic_container_oddity"
    assert report["comparison"]["requested_exactness"] == "content"
    assert report["comparison"]["requested_exactness_id"] == 2
    assert report["comparison"]["content_exact_accepted"] is True
    assert report["comparison"]["content_exact_unaccepted"] is False
    assert report["comparison"]["content_issue_kinds"] == []
    assert report["comparison"]["file_structure_issue_kinds"] == [
        "container_shape_mismatch",
        "hunk_relocation_order_mismatch",
        "policy_divergence",
    ]
    assert report["file_shape_diagnostics"][0]["group"] == "original_file_structure"
    assert "row_index" not in report["file_shape_diagnostics"][0]
    assert report["file_shape_diagnostics"][1]["kind"] == "hunk_relocation_order_mismatch"
    assert report["file_shape_diagnostics"][1]["row_index"] == 9
    assert report["row_mappings"][0]["kind"] == "hunk_relocation_order_mismatch"
    assert report["row_mappings"][0]["row_index"] == 9
    profile = cast(dict[str, object], report["profile"])
    assert profile["facts_v2_direct_semantic_fast_path"] == 1.0
    assert profile["facts_v2_direct_compare_semantic_exact"] == 1.0


def test_direct_compare_content_exact_is_unaccepted_by_default() -> None:
    comparison = reproduction._direct_compare_reproduction_comparison(
        "amiga-hunk",
        reproduction.reproduction_policy_for_options(reproduction._default_reproduction_options()),
        {
            "direct_rebuild_exact": False,
            "direct_compare_semantic_exact": True,
            "direct_compare_status_id": 2,
            "direct_compare_exactness_id": 2,
            "direct_compare_issue_group_flags": 4,
        },
    )

    assert comparison["requested_exactness"] == "full_file"
    assert comparison["requested_exactness_id"] == 1
    assert comparison["selected_exact"] is False
    assert comparison["content_exact"] is True
    assert comparison["content_exact_accepted"] is False
    assert comparison["content_exact_unaccepted"] is True


def test_run_reproduction_fast_path_does_not_late_render_source_on_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    original = _hunk_with_reloc_order([4, 0])
    rebuilt = bytearray(original)
    rebuilt[-8] ^= 1
    binary_path.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    def render_source(*args: object, **kwargs: object) -> tuple[str, dict[str, object]]:
        return "dc.l $000003F3\n", {"generation": "facts_v2_asm_source", "facts_v2": {"asm_source_refused": False}}

    def assemble_source(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object]]:
        output_path = kwargs.get("output_path")
        if isinstance(output_path, Path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(rebuilt)
        return bytes(rebuilt), {"assemble_c_api": True, "total_seconds": 0.02}

    monkeypatch.setattr(reproduction, "listing_artifact_source_text_with_c_backend_profile", render_source)
    monkeypatch.setattr(reproduction, "assemble_platform_source_text_with_c_backend", assemble_source)
    monkeypatch.setattr(
        reproduction,
        "reproduction_compare_rebuilt_bytes_with_c_backend_profile",
        lambda _source, rebuilt_bytes, **_kwargs: _mock_c_compare_profile(original, rebuilt_bytes),
    )

    report = run_reproduction("demo", project_root=tmp_path, profile=True, source_assembly_debug=True)

    assert report["status"] == "binary_mismatch"
    assert not (tmp_path / "bin" / "rebuilt" / "demo" / "source.s").exists()


def test_run_reproduction_captures_renderer_failure_as_render_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x4e\x75")
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )

    def fail_render(*args: object, **kwargs: object) -> tuple[str, dict[str, object]]:
        raise reproduction.FactsV2SourceRefused(
            {
                "facts_v2": {
                    "asm_source_refused": True,
                    "asm_source_first_failure_kind": "renderer_crashed",
                }
            }
        )

    monkeypatch.setattr(reproduction, "listing_artifact_source_text_with_c_backend_profile", fail_render)

    report = run_reproduction("demo", source_assembly_debug=True)

    assert report["status"] == "render_error"
    assert "renderer_crashed" in str(report["tool_error"])
    assert cast(list[dict[str, object]], report["issues"])[0]["kind"] == "renderer"


def test_run_reproduction_refuses_facts_v2_source_before_assemble(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x00\x00\x03\xf3")
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary_path,
        display_path="demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    listing_profile = {
        "facts_v2": {
            "asm_source_refused": True,
            "asm_source_first_failure_kind": "unresolved_label",
            "asm_source_first_failure_section": 0,
            "asm_source_first_failure_offset": 4,
        }
    }
    def refuse_source(*args: object, **kwargs: object) -> tuple[str, dict[str, object]]:
        raise reproduction.FactsV2SourceRefused(listing_profile)

    monkeypatch.setattr(
        reproduction,
        "listing_artifact_source_text_with_c_backend_profile",
        refuse_source,
    )

    def fail_assemble(*args: object, **kwargs: object) -> tuple[bytes, dict[str, object]]:
        raise AssertionError("facts_v2 refused source must not be assembled")

    monkeypatch.setattr(reproduction, "assemble_platform_source_text_with_c_backend", fail_assemble)

    report = run_reproduction("demo", project_root=tmp_path, profile=True, source_assembly_debug=True)

    assert report["status"] == "render_error"
    assert str(report["tool_error"]).startswith("facts_v2 asm source refused")
    assert report["listing_profile"] == listing_profile
    assert cast(dict[str, object], report["input_stamp"])["analysis_backend"] == "facts_v2"


def test_run_reproduction_writes_tool_error_when_stamp_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    missing_binary_path = tmp_path / "missing.bin"
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=missing_binary_path,
        display_path="missing.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_dir",
        lambda target, project_root: target_dir,
    )

    report = run_reproduction("demo", project_root=tmp_path)

    assert report["status"] == "tool_error"
    assert "missing.bin" in str(report["tool_error"])
    assert cast(dict[str, object], report["input_stamp"])["stamp_error"]
    assert (target_dir / "reproduction.json").exists()


def test_load_reproduction_report_keeps_tool_error_when_current_stamp_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=tmp_path / "missing.bin",
        display_path="missing.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    monkeypatch.setattr(reproduction, "resolve_project_dir", lambda target, project_root: target_dir)

    run_reproduction("demo", project_root=tmp_path)
    report = reproduction.load_reproduction_report("demo", project_root=tmp_path)

    assert report["status"] == "tool_error"
    assert "current_input_stamp" in report
    assert cast(dict[str, object], report["current_input_stamp"])["stamp_error"]


def test_load_reproduction_report_reads_saved_report_when_source_resolution_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    input_stamp = reproduction.unresolved_reproduction_input_stamp(
        "demo",
        project_root=tmp_path,
        error="Unable to resolve binary source",
        target_dir=target_dir,
    )
    (target_dir / "reproduction.json").write_text(
        json.dumps(
            {
                "target": "demo",
                "status": "tool_error",
                "exact": False,
                "stale": False,
                "input_stamp": input_stamp,
                "assembler": "our",
                "issues": [{"kind": "tool", "message": "Unable to resolve binary source"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        reproduction,
        "resolve_project_paths",
        lambda target, project_root: (_ for _ in ()).throw(
            FileNotFoundError("Unable to resolve binary source")
        ),
    )
    monkeypatch.setattr(reproduction, "resolve_project_dir", lambda target, project_root: target_dir)

    report = reproduction.load_reproduction_report("demo", project_root=tmp_path)

    assert report["status"] == "tool_error"
    assert cast(dict[str, object], report["current_input_stamp"])["stamp_error"] == "Unable to resolve binary source"


def test_disk_entry_read_bytes_uses_source_project_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: dict[str, object] = {}

    def fake_extract(disk_path: Path, entry_path: str, *, project_root: Path) -> bytes:
        seen["disk_path"] = disk_path
        seen["entry_path"] = entry_path
        seen["project_root"] = project_root
        return b"entry"

    monkeypatch.setattr(
        "amiga_reversing.disasm.c_backend.extract_disk_entry_with_c_backend",
        fake_extract,
    )
    source = DiskEntryBinarySource(
        kind=BinarySourceKind.DISK_ENTRY,
        disk_id="demo",
        adf_path=tmp_path / "demo.st",
        entry_path="AUTO/BOOT.PRG",
        display_path="demo.st::AUTO/BOOT.PRG",
        analysis_cache_path=tmp_path / "binary.analysis",
        project_root=tmp_path,
    )

    assert source.read_bytes() == b"entry"
    assert seen["project_root"] == tmp_path


def test_append_layout_range_keeps_unlabelled_range() -> None:
    layout: list[dict[str, object]] = []

    reproduction._append_layout_range(layout, "header", 0, 4, data_len=8)

    assert layout == [{"kind": "header", "file_start": 0, "file_end": 4, "length": 4}]


def test_reproduction_stamp_changes_when_binary_or_metadata_changes(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x01\x02")
    write_source_descriptor(target_dir, {"kind": "hunk_file", "path": str(binary_path)})

    initial = reproduction_input_stamp("demo", project_root=tmp_path)
    binary_path.write_bytes(b"\x01\x03")
    binary_changed = reproduction_input_stamp("demo", project_root=tmp_path)
    metadata = _empty_metadata()
    metadata["seeded_code_entrypoints"] = [
        {
            "addr": 0,
            "name": "start",
            "seed_origin": "manual_analysis",
            "review_status": "seeded",
            "citation": "test",
        }
    ]
    (target_dir / "target_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    metadata_changed = reproduction_input_stamp("demo", project_root=tmp_path)

    assert initial["original_sha256"] != binary_changed["original_sha256"]
    assert binary_changed["effective_metadata_sha256"] != metadata_changed["effective_metadata_sha256"]


def test_reproduction_stamp_records_facts_v2_analysis_backend(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x01\x02")
    write_source_descriptor(target_dir, {"kind": "hunk_file", "path": str(binary_path)})

    default = reproduction_input_stamp("demo", project_root=tmp_path)

    assert default["analysis_backend"] == "facts_v2"


def test_reproduction_stamp_changes_when_c_backend_tool_changes(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x01\x02")
    write_source_descriptor(target_dir, {"kind": "hunk_file", "path": str(binary_path)})

    initial = reproduction_input_stamp("demo", project_root=tmp_path)
    build_dir = tmp_path / "src" / "build"
    build_dir.mkdir(parents=True)
    (build_dir / "platform_file_lib.dll").write_bytes(b"renderer")
    changed = reproduction_input_stamp("demo", project_root=tmp_path)

    assert initial["source_renderer_tool_stamps"] != changed["source_renderer_tool_stamps"]


def test_reproduction_options_read_file_shape_policy(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    metadata = _empty_metadata()
    metadata["reproduction"] = {
        "file_shape": {
            "relocation_order": "match_original",
        },
    }
    (target_dir / "target_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    options = reproduction_options_for_target(target_dir)

    assert (
        cast(dict[str, object], options["file_shape"])["relocation_order"]
        is reproduction.ReproductionFileShapeOrder.MATCH_ORIGINAL
    )


def test_builtin_reproduction_profiles_expand_to_concrete_options() -> None:
    profiles = reproduction.builtin_reproduction_profiles()
    by_id = {str(profile["profile_id"]): profile for profile in profiles}

    assert set(by_id) == {"exact-framework", "source-vasm", "source-devpac", "content-semantic"}
    for profile_id, profile in by_id.items():
        options = cast(dict[str, object], profile["options"])
        policy = reproduction.reproduction_policy_for_options(
            reproduction.validated_reproduction_options_payload(options)
        )
        assert options["profile_id"] == profile_id
        assert options["assembler"] == "our"
        assert policy["requested_exactness_id"] in {1, 2}

    assert cast(dict[str, object], by_id["source-vasm"]["options"])["oracle_modes"] == ["vasm"]
    assert cast(dict[str, object], by_id["source-devpac"]["options"])["oracle_modes"] == ["devpac"]
    semantic_policy = reproduction.reproduction_policy_for_options(
        reproduction.validated_reproduction_options_payload(cast(dict[str, object], by_id["content-semantic"]["options"]))
    )
    assert semantic_policy["mode"] == "semantic"
    assert semantic_policy["comparison"] == "semantic"
    assert semantic_policy["requested_exactness"] == "content"


def test_reproduction_options_merge_metadata_and_corrections(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    manual = _empty_metadata()
    manual["reproduction"] = {
        "mode": "canonical",
        "assembler": "our",
        "cpu": "68020",
        "backend": "amiga-hunk",
        "include_dirs": ["custom/include"],
        "oracle_modes": ["vasm"],
        "comparison": "full_file",
        "requested_exactness": "content",
        "file_shape": {"relocation_order": "assembler_default"},
    }
    corrections = _empty_metadata()
    corrections["reproduction"] = {
        "mode": "content",
        "cpu": "68060",
        "container_policy": "preserve_original",
        "relocation_policy": "preserve_original_encoding",
        "file_shape": {
            "relocation_order": "match_original",
            "relocation_record": "short",
            "section_aux_order": "match_original",
        }
    }
    (target_dir / "target_metadata.json").write_text(json.dumps(manual), encoding="utf-8")
    (target_dir / "target_corrections.json").write_text(json.dumps(corrections), encoding="utf-8")

    options = reproduction_options_for_target(target_dir)

    assert options["assembler"] == "our"
    assert options["mode"] == "content"
    assert options["cpu"] == "68060"
    assert options["backend"] == "amiga-hunk"
    assert options["include_dirs"] == ["custom/include"]
    assert options["oracle_modes"] == ["vasm"]
    assert options["container_policy"] == "preserve_original"
    assert options["relocation_policy"] == "preserve_original_encoding"
    assert options["comparison"] == "full_file"
    assert options["requested_exactness"] == "content"
    assert options["requested_exactness_id"] == 2
    assert options["raw_output"] is None
    file_shape = cast(dict[str, object], options["file_shape"])
    assert file_shape["relocation_order"] is reproduction.ReproductionFileShapeOrder.MATCH_ORIGINAL
    assert file_shape["relocation_record"] is reproduction.ReproductionRelocationRecord.SHORT
    assert file_shape["section_aux_order"] is reproduction.ReproductionFileShapeOrder.MATCH_ORIGINAL
    assert reproduction.reproduction_policy_for_options(options) == {
        "mode": "content",
        "container_policy": "preserve_original",
        "relocation_policy": "preserve_original_encoding",
        "comparison": "content",
        "requested_exactness": "content",
        "requested_exactness_id": 2,
    }


def test_reproduction_options_reject_invalid_typed_values(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    metadata = _empty_metadata()
    metadata["reproduction"] = {"backend": "unknown", "oracle_modes": ["bad"]}
    (target_dir / "target_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid reproduction option 'backend'"):
        reproduction_options_for_target(target_dir)


def test_reproduction_input_stamp_includes_profile_concrete_policy(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x00\x01")
    write_source_descriptor(
        target_dir,
        {
            "kind": "raw_binary",
            "path": str(binary_path),
            "address_model": "local_offset",
            "load_address": 0,
            "entrypoint": 0,
            "code_start_offset": 0,
        },
    )
    reproduction.write_target_reproduction_options(
        target_dir,
        reproduction.expand_reproduction_profile("source-devpac"),
    )

    stamp = reproduction_input_stamp("demo", project_root=tmp_path)
    options = cast(dict[str, object], stamp["reproduction_options"])
    policy = cast(dict[str, object], stamp["reproduction_policy"])

    assert options["profile_id"] == "source-devpac"
    assert options["assembler"] == "our"
    assert options["oracle_modes"] == ["devpac"]
    assert policy["mode"] == "exact"
    assert policy["requested_exactness"] == "full_file"
    availability = cast(list[dict[str, object]], stamp["oracle_tool_availability"])
    assert [record["tool_id"] for record in availability] == ["genam", "vamos"]
    assert all(record["required"] is True for record in availability)


def test_reproduction_input_stamp_omits_unrequested_oracle_availability(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x00\x01")
    write_source_descriptor(
        target_dir,
        {
            "kind": "raw_binary",
            "path": str(binary_path),
            "address_model": "local_offset",
            "load_address": 0,
            "entrypoint": 0,
            "code_start_offset": 0,
        },
    )

    stamp = reproduction_input_stamp("demo", project_root=tmp_path)

    assert stamp["oracle_tool_availability"] == []


def test_report_with_oracle_compatibility_keeps_gate_status_separate(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        reproduction,
        "oracle_compatibility_reports_for_options",
        lambda target, options, project_root=None: [
            {"oracle_id": "vasm", "comparison_level": "oracle.full_file_match"}
        ],
    )
    report = {
        "target": "demo",
        "status": "exact",
        "input_stamp": {
            "reproduction_options": {
                "oracle_modes": ["vasm"],
            }
        },
    }

    payload = reproduction._report_with_oracle_compatibility(report, project_root=tmp_path)

    assert payload["status"] == "exact"
    assert payload["oracle_compatibility"] == [
        {"oracle_id": "vasm", "comparison_level": "oracle.full_file_match"}
    ]


def test_reproduction_options_reject_alias_spellings(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    metadata = _empty_metadata()
    metadata["reproduction"] = {"mode": "template-preserved"}
    (target_dir / "target_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid reproduction option 'mode'"):
        reproduction_options_for_target(target_dir)


def test_reproduction_options_reject_file_shape_alias_spellings(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    metadata = _empty_metadata()
    metadata["reproduction"] = {"file_shape": {"relocation_order": "assembler-default"}}
    (target_dir / "target_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid reproduction option 'relocation_order'"):
        reproduction_options_for_target(target_dir)


def test_effective_metadata_merge_includes_seeded_and_corrections_without_ui_edits(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    manual = _empty_metadata()
    seeded = _empty_metadata()
    corrections = _empty_metadata()
    seeded["seeded_entities"] = [
        {
            "addr": 0x10,
            "end": 0x20,
            "hunk": 0,
            "type": "data",
            "subtype": "pointer_table",
            "seed_origin": "primary_doc",
            "review_status": "seeded",
            "citation": "doc",
            "source_id": "doc",
            "source_path": "resources/demo.asm",
            "source_locator": "PTRS",
        }
    ]
    corrections["seeded_code_labels"] = [
        {
            "addr": 0x30,
            "hunk": 0,
            "name": "corrected_label",
            "seed_origin": "manual_analysis",
            "review_status": "seeded",
            "citation": "fix",
        }
    ]
    corrections["seeded_code_entrypoints"] = [
        {
            "addr": 0x40,
            "hunk": 0,
            "name": "corrected_entry",
            "seed_origin": "manual_analysis",
            "review_status": "seeded",
            "citation": "fix",
        }
    ]
    (target_dir / "target_metadata.json").write_text(json.dumps(manual), encoding="utf-8")
    (target_dir / "target_seeded_metadata.json").write_text(json.dumps(seeded), encoding="utf-8")
    (target_dir / "target_corrections.json").write_text(json.dumps(corrections), encoding="utf-8")

    text = effective_metadata_text(target_dir)

    assert "pointer_table" in text
    assert "corrected_label" in text
    assert "corrected_entry" in text
    assert not (target_dir / "target_ui_edits.json").exists()
