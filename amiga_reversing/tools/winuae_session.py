from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WINUAE_EXE = ROOT / "resources" / "clone_common" / "WinUAE" / "winuae64.exe"


@dataclass(frozen=True, slots=True)
class WinUaeSession:
    winuae_exe: Path
    cli_root: Path
    config_path: Path | None = None
    start_debugger: bool = True
    no_gui: bool = True

    def command(self) -> list[str]:
        args = [str(self.winuae_exe)]
        if self.no_gui:
            args.append("-G")
        if self.start_debugger:
            args.append("-D")
        args.append(f"-cli={self.cli_root}")
        if self.config_path is not None:
            args.append(f"-config={self.config_path}")
        return args


def command_line(args: list[str]) -> str:
    return subprocess.list2cmdline(args)


def write_cmd_file(path: Path, session: WinUaeSession) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"@echo off\n{command_line(session.command())} %*\n", encoding="utf-8", newline="\r\n")


def write_startup_sequence(cli_root: Path, commands: list[str]) -> Path:
    startup_path = cli_root / "S" / "startup-sequence"
    startup_path.parent.mkdir(parents=True, exist_ok=True)
    startup_path.write_text("".join(f"{command}\n" for command in commands), encoding="ascii", newline="\n")
    return startup_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a WinUAE CLI/debugger session command.")
    parser.add_argument("--winuae", type=Path, default=DEFAULT_WINUAE_EXE)
    parser.add_argument("--cli-root", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--no-debugger", action="store_true")
    parser.add_argument("--show-gui", action="store_true")
    parser.add_argument("--cmd-out", type=Path)
    parser.add_argument("--startup-command", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    session = WinUaeSession(
        winuae_exe=args.winuae,
        cli_root=args.cli_root,
        config_path=args.config,
        start_debugger=not args.no_debugger,
        no_gui=not args.show_gui,
    )
    line = command_line(session.command())
    if args.cmd_out is not None:
        write_cmd_file(args.cmd_out, session)
    if args.startup_command:
        write_startup_sequence(args.cli_root, args.startup_command)
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
