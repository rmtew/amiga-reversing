"""Canonical CFG source identities through the real native facts pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    analyze_project_source_with_c_backend,
    assemble_platform_source_text_with_c_backend,
    render_project_source_with_c_backend,
)
from amiga_reversing.disasm.function_facts import analysis_function_facts

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("base", [0x100, 0x1000])
def test_absolute_call_uses_native_source_identity_and_preserves_bytes(tmp_path, base):
    if not (ROOT / "src/build/platform_file_lib.dll").exists():
        pytest.skip("Build native backend before exercising canonical CFG")
    original = bytearray(0x300)
    original[:8] = (
        bytes.fromhex("4eb9") + (base + 0x20).to_bytes(4, "big") + bytes.fromhex("4e75")
    )
    original[0x20:0x22] = bytes.fromhex("4e75")
    binary = tmp_path / "absolute-call.bin"
    binary.write_bytes(original)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=base,
        entrypoint=base,
        code_start_offset=0,
        display_path=str(binary),
        analysis_cache_path=tmp_path / "analysis",
    )
    analysis = analyze_project_source_with_c_backend(
        source, metadata_path=None, project_root=ROOT
    )
    section = analysis["sections"][0]
    runtime_ref = next(
        r
        for r in section["runtime_address_refs"]
        if r["offset"] == 0 and r["operand_index"] == 0
    )
    assert runtime_ref["target_offset"] == 0x20
    edge = next(
        e for e in section["edges"] if e["source_offset"] == 0 and e["kind"] == 3
    )
    assert edge["target_offset"] == runtime_ref["target_offset"]
    assert section["blocks"][edge["target_block_index"]]["start_offset"] == 0x20
    functions = analysis_function_facts("synthetic", analysis)["functions"]
    callee = next(f for f in functions if f["entry_offset"] == 0x20)
    assert callee["callers"][0]["source_offset"] == 0
    assert not any(f["entry_offset"] == base + 0x20 for f in functions)
    rendered = render_project_source_with_c_backend(
        source, metadata_path=None, project_root=ROOT
    )
    rebuilt, _ = assemble_platform_source_text_with_c_backend(
        "amiga-raw", rendered, target_cpu="68000", project_root=ROOT
    )
    assert rebuilt == original


def test_object_relocation_control_target_remains_source_relative(tmp_path):
    from amiga_reversing.disasm.binary_source import HunkFileBinarySource

    if not (ROOT / "src/build/platform_file_lib.dll").exists():
        pytest.skip("Build native backend before exercising canonical CFG")
    original, _ = assemble_platform_source_text_with_c_backend(
        "amiga-hunk",
        "    SECTION section,code\n    jsr target.l\n    rts\ntarget:\n    rts\n    dc.w 0\n",
        project_root=ROOT,
    )
    binary = tmp_path / "relocated-call.hunk"
    binary.write_bytes(original)
    source = HunkFileBinarySource(
        kind=BinarySourceKind.HUNK_FILE,
        path=binary,
        display_path=str(binary),
        analysis_cache_path=tmp_path / "analysis",
    )
    section = analyze_project_source_with_c_backend(
        source, metadata_path=None, project_root=ROOT
    )["sections"][0]
    edge = next(
        e for e in section["edges"] if e["source_offset"] == 0 and e["kind"] == 3
    )
    assert edge["target_offset"] == 8
    assert section["blocks"][edge["target_block_index"]]["start_offset"] == 8
    rendered = render_project_source_with_c_backend(
        source, metadata_path=None, project_root=ROOT
    )
    rebuilt, _ = assemble_platform_source_text_with_c_backend(
        "amiga-hunk", rendered, project_root=ROOT
    )
    assert rebuilt == original
