"""Runtime references must not select a named storage alias before ORG."""

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    assemble_platform_source_text_with_c_backend,
    render_project_source_with_c_backend,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("runtime_name", [None, "copied_runtime_entry"])
def test_named_storage_entry_does_not_replace_runtime_operand(tmp_path, runtime_name):
    # Copies source $20..$40 to $100 and enters it. The copied routine takes
    # its own absolute runtime address, while the source alias stays at $20.
    original = bytes.fromhex(
        "41fa001e43f900000100702012d8538066fa4ef900000100"
        "0000000000000000"
        "41f9000001004e75" + "00" * 24
    )
    binary = tmp_path / "copy.bin"
    binary.write_bytes(original)
    metadata = {
        "seeded_code_labels": [{"hunk": 0, "addr": 0x20, "name": "stored_entry"}]
    }
    if runtime_name:
        metadata["absolute_code_labels"] = [{"addr": 0x100, "name": runtime_name}]
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(metadata))
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(binary),
        analysis_cache_path=tmp_path / "analysis",
    )
    rendered = render_project_source_with_c_backend(
        source, metadata_path=path, project_root=ROOT
    )
    runtime_label = runtime_name or "abs_0_00000100"
    assert rendered.index("stored_entry:") < rendered.index("    ORG $100")
    assert f"lea.l {runtime_label}.l,a0" in rendered
    rebuilt, _ = assemble_platform_source_text_with_c_backend(
        "amiga-raw", rendered, project_root=ROOT
    )
    assert rebuilt == original


@pytest.mark.parametrize("copied", [False, True])
def test_source_name_remains_valid_for_identity_or_interior_target(tmp_path, copied):
    if copied:
        original = bytes.fromhex(
            "41fa001e43f900000100702012d8538066fa4ef900000100"
            + "00" * 8
            + "41f9000001064e75"
            + "00" * 24
        )
        target = 0x26
    else:
        original = bytes.fromhex("41f9000000004e75")
        target = 0
    binary = tmp_path / "control.bin"
    binary.write_bytes(original)
    path = tmp_path / "metadata.json"
    metadata = {
        "seeded_code_labels": [{"hunk": 0, "addr": target, "name": "named_target"}]
    }
    if not copied:
        metadata["execution_views"] = [
            {
                "source_start": 0,
                "source_end": len(original),
                "base_addr": 0,
                "name": "identity",
            }
        ]
    path.write_text(json.dumps(metadata))
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(binary),
        analysis_cache_path=tmp_path / "analysis",
    )
    rendered = render_project_source_with_c_backend(
        source, metadata_path=path, project_root=ROOT
    )
    assert "lea.l named_target.l,a0" in rendered
    rebuilt, _ = assemble_platform_source_text_with_c_backend(
        "amiga-raw", rendered, project_root=ROOT
    )
    assert rebuilt == original
