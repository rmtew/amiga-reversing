"""External byte oracle for typed fields without versus with displacement words."""

from __future__ import annotations

import json
import subprocess
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


@pytest.mark.parametrize(
    ("encoded", "instruction", "field"),
    [
        ("4a90", "tst.l (a0)", "record_first"),
        ("4aa80000", "tst.l Record_record_first.w(a0)", "record_first"),
        ("4aa80004", "tst.l Record_record_next(a0)", "record_next"),
        ("2080", "move.l d0,(a0)", "record_first"),
        ("21400000", "move.l d0,Record_record_first.w(a0)", "record_first"),
        ("21400004", "move.l d0,Record_record_next(a0)", "record_next"),
    ],
)
def test_typed_field_rendering_preserves_encoding_with_both_assemblers(
    tmp_path, encoded, instruction, field
):
    vasm = ROOT / "tools/vasmm68k_mot.exe"
    if not vasm.exists() or not (ROOT / "src/build/platform_file_lib.dll").exists():
        pytest.skip("Build native backend and vasm to run the external encoding oracle")
    original = bytes.fromhex(encoded + "4e75")
    binary = tmp_path / "input.bin"
    binary.write_bytes(original)
    metadata = tmp_path / "metadata.json"
    metadata.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "entry_register_seeds": [
                    {
                        "entry_offset": None,
                        "hunk": 0,
                        "register": "A0",
                        "kind": "struct_ptr",
                        "note": "Record",
                        "struct_name": "Record",
                        "context_name": None,
                    }
                ],
                "custom_structs": [
                    {
                        "name": "Record",
                        "size": 8,
                        "fields": [
                            {
                                "name": name,
                                "type": "long",
                                "offset": offset,
                                "size": 4,
                                "struct": None,
                                "pointer_struct": None,
                                "named_base": None,
                            }
                            for name, offset in [
                                ("record_first", 0),
                                ("record_next", 4),
                            ]
                        ],
                    }
                ],
            }
        )
    )
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
        source, metadata_path=metadata, project_root=ROOT
    )
    lines = [
        line
        for line in rendered.splitlines()
        if line.strip().startswith(instruction.split()[0])
    ]
    assert len(lines) == 1
    assert lines[0].split(";", 1)[0].strip() == instruction
    assert field in lines[0], (
        "Keep field meaning on the access, not only in a declaration"
    )
    built, _ = assemble_platform_source_text_with_c_backend(
        "amiga-raw", rendered, target_cpu="68000"
    )
    assert built == original
    asm = tmp_path / "rendered.s"
    asm.write_text(rendered)
    output = tmp_path / "vasm.bin"
    completed = subprocess.run(
        [
            str(vasm),
            "-Fbin",
            "-m68000",
            "-no-opt",
            "-quiet",
            "-nosym",
            "-o",
            str(output),
            str(asm),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == original
