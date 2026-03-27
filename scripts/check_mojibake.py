#!/usr/bin/env py.exe
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".json",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
    ".ini",
    ".cfg",
}


def _seq(*codepoints: int) -> str:
    return "".join(chr(codepoint) for codepoint in codepoints)


SUSPICIOUS_SEQUENCES = tuple(
    (label, label.encode("utf-8"))
    for label in (
        _seq(0x00E2, 0x20AC, 0x201D),  # mojibake em dash pattern
        _seq(0x00E2, 0x20AC, 0x201C),  # mojibake en dash pattern
        _seq(0x00E2, 0x20AC, 0x02DC),  # mojibake left single quote pattern
        _seq(0x00E2, 0x20AC, 0x2122),  # mojibake right single quote pattern
        _seq(0x00E2, 0x20AC, 0x0153),  # mojibake left double quote pattern
        _seq(0x00E2, 0x20AC, 0x00A6),  # mojibake ellipsis pattern
        _seq(0x00E2, 0x2020, 0x2019),  # mojibake right arrow pattern
        _seq(0x00C2, 0x00A9),          # mojibake copyright pattern
        _seq(0x00C2, 0x00AE),          # mojibake registered pattern
        _seq(0x00C2, 0x2122),          # mojibake trademark pattern
        _seq(0x00C3, 0x00A9),          # mojibake e acute pattern
        _seq(0x00C3, 0x00A8),          # mojibake e grave pattern
        _seq(0x00C3, 0x00B6),          # mojibake o umlaut pattern
        _seq(0x00C3, 0x00BC),          # mojibake u umlaut pattern
        _seq(0x00C3, 0x00B1),          # mojibake n tilde pattern
    )
)


def tracked_text_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        ROOT / line
        for line in completed.stdout.splitlines()
        if (ROOT / line).suffix.lower() in TEXT_SUFFIXES
    ]


def find_mojibake() -> list[str]:
    failures: list[str] = []
    for path in tracked_text_files():
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{path}: invalid utf-8 ({exc})")
            continue
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(text.splitlines(), 1):
            line_bytes = line.encode("utf-8")
            hit = next((label for label, pattern in SUSPICIOUS_SEQUENCES if pattern in line_bytes), None)
            if hit is not None:
                failures.append(f"{rel}:{lineno}: suspicious mojibake sequence {hit!r}")
    return failures


def main() -> int:
    failures = find_mojibake()
    if not failures:
        print("mojibake: ok")
        return 0
    for failure in failures:
        print(failure)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
