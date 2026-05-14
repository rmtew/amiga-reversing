from __future__ import annotations

from pathlib import Path

import pytest

from amiga_reversing.tools import winuae_session


def test_winuae_session_command_uses_cli_root_and_debugger() -> None:
    session = winuae_session.WinUaeSession(
        winuae_exe=Path(r"C:\Tools\WinUAE\winuae64.exe"),
        cli_root=Path(r"C:\work\cli root"),
        config_path=Path(r"C:\work\debug.uae"),
    )

    assert session.command() == [
        r"C:\Tools\WinUAE\winuae64.exe",
        "-G",
        "-D",
        r"-cli=C:\work\cli root",
        r"-config=C:\work\debug.uae",
    ]
    assert winuae_session.command_line(session.command()) == (
        r"C:\Tools\WinUAE\winuae64.exe -G -D "
        r'"-cli=C:\work\cli root" -config=C:\work\debug.uae'
    )


def test_write_cmd_file_forwards_extra_args(tmp_path: Path) -> None:
    cmd_path = tmp_path / "run-winuae.cmd"
    session = winuae_session.WinUaeSession(
        winuae_exe=Path("winuae64.exe"),
        cli_root=tmp_path / "cli",
        start_debugger=False,
        no_gui=False,
    )

    winuae_session.write_cmd_file(cmd_path, session)

    assert cmd_path.read_text(encoding="utf-8") == f"@echo off\nwinuae64.exe -cli={tmp_path}\\cli %*\n"


def test_main_prints_and_writes_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cmd_path = tmp_path / "session.cmd"
    result = winuae_session.main(
        [
            "--winuae",
            "winuae64.exe",
            "--cli-root",
            str(tmp_path / "cli"),
            "--no-debugger",
            "--show-gui",
            "--cmd-out",
            str(cmd_path),
        ]
    )

    assert result == 0
    assert capsys.readouterr().out == f"winuae64.exe -cli={tmp_path}\\cli\n"
    assert cmd_path.read_text(encoding="utf-8") == f"@echo off\nwinuae64.exe -cli={tmp_path}\\cli %*\n"
