from __future__ import annotations

import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm.binary_source import BinarySourceKind
from amiga_reversing.tools import vasm_roundtrip


def test_roundtrip_vasm_target_reports_first_diff(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "amiga_hunk_demo"
    tools_dir = tmp_path / "tools"
    include_dir = tmp_path / "ext" / "amiga_includes" / "ndk_2.0" / "include"
    binary_path = tmp_path / "bin" / "Demo"
    target_dir.mkdir(parents=True)
    include_dir.mkdir(parents=True)
    tools_dir.mkdir()
    binary_path.parent.mkdir()
    binary_path.write_bytes(b"\x01\x02\x03\x04")
    (tools_dir / "vasmm68k_mot.exe").write_bytes(b"fake")

    monkeypatch.setattr(
        vasm_roundtrip,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=SimpleNamespace(
                kind=BinarySourceKind.HUNK_FILE,
                display_path="bin/Demo",
                read_bytes=lambda: b"\x01\x02\x03\x04",
            ),
        ),
    )
    monkeypatch.setattr(
        vasm_roundtrip,
        "render_source_from_binary_source_or_raise",
        lambda *args, **kwargs: type(
            "Rendering",
            (),
            {"source_text": "    SECTION code,CODE\n    rts\n"},
        )(),
    )

    @contextmanager
    def fake_metadata_file(target_dir: Path) -> Iterator[Path | None]:
        yield None

    monkeypatch.setattr(vasm_roundtrip, "effective_metadata_file", fake_metadata_file)

    def fake_run(
        cmd: list[str],
        cwd: Path,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        assert cmd[0] == str(tools_dir / "vasmm68k_mot.exe")
        assert "-Fhunkexe" in cmd
        assert "-no-opt" in cmd
        assert "-nosym" in cmd
        assert "-kick1hunks" in cmd
        assert f"-I{include_dir}" in cmd
        output_path = Path(cmd[cmd.index("-o") + 1])
        output_path.write_bytes(b"\x01\xFF\x03\x04")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = vasm_roundtrip.roundtrip_vasm_target("amiga_hunk_demo", project_root=tmp_path)

    assert result.output_exists is True
    assert result.exact_match is False
    assert result.first_diff_offset == 1
    assert result.generated_size == 4
    assert result.original_size == 4


def test_roundtrip_vasm_target_rejects_disk_entries(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "disk_entry"
    target_dir.mkdir(parents=True)
    monkeypatch.setattr(
        vasm_roundtrip,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=SimpleNamespace(kind=BinarySourceKind.DISK_ENTRY),
        ),
    )

    with pytest.raises(ValueError, match="file-backed"):
        vasm_roundtrip.roundtrip_vasm_target("disk_entry", project_root=tmp_path)
