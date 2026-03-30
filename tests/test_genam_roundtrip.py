from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from scripts import genam_roundtrip as roundtrip_mod


def test_devpac_output_args_use_documented_to_form() -> None:
    assert roundtrip_mod._devpac_output_args("devpac", "GenAm.out") == [
        "TO",
        "TMP:GenAm.out",
    ]


def test_roundtrip_genam_target_reports_first_diff(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "amiga_hunk_genam"
    bin_dir = tmp_path / "bin"
    include_dir = tmp_path / "ext" / "amiga_includes" / "ndk_2.0" / "include"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    include_dir.mkdir(parents=True)
    binary_path = bin_dir / "GenAm"
    entities_path = target_dir / "entities.jsonl"
    source_path = target_dir / "GenAm.s"
    binary_path.write_bytes(b"\x01\x02\x03\x04")
    entities_path.write_text("", encoding="utf-8")
    (include_dir / "dummy.i").write_text("", encoding="utf-8")

    monkeypatch.setattr(
        roundtrip_mod,
        "resolve_project_paths",
        lambda target, project_root, require_entities=False: SimpleNamespace(
            target_dir=target_dir,
            entities_path=entities_path,
            binary_source=SimpleNamespace(
                path=Path("bin/GenAm"),
                display_path="bin/GenAm",
            ),
        ),
    )

    def fake_gen_disasm(binary_path: str, entities_path: str, output_path: str, **_kwargs: object) -> None:
        Path(output_path).write_text("SECTION code,code\n", encoding="utf-8", newline="\n")

    monkeypatch.setattr(roundtrip_mod, "gen_disasm", fake_gen_disasm)

    def fake_run(cmd: list[str], cwd: Path, capture_output: bool, text: bool, timeout: int) -> subprocess.CompletedProcess[str]:
        assert cmd[0] == "vamos"
        assert "TO" in cmd
        out_index = cmd.index("TO") + 1
        out_name = cmd[out_index].removeprefix("TMP:")
        temp_root = Path(cmd[2].removeprefix("TMP:"))
        (temp_root / out_name).write_bytes(b"\x01\xFF\x03\x04")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(roundtrip_mod, "ROOT", tmp_path)

    result = roundtrip_mod.roundtrip_genam_target("amiga_hunk_genam")

    assert result.output_exists is True
    assert result.exact_match is False
    assert result.first_diff_offset == 1
    assert result.generated_size == 4
    assert result.original_size == 4
    assert result.source_path == source_path
