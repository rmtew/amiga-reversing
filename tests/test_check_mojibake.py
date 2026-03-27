from __future__ import annotations

from pathlib import Path

from scripts import check_mojibake


def test_find_mojibake_detects_suspicious_sequences(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text(
        f"title {check_mojibake._seq(0x00E2, 0x20AC, 0x201D)} broken\n",
        encoding="utf-8",
    )

    original_root = check_mojibake.ROOT
    original_files = check_mojibake.tracked_text_files
    try:
        check_mojibake.ROOT = tmp_path
        check_mojibake.tracked_text_files = lambda: [bad]
        failures = check_mojibake.find_mojibake()
    finally:
        check_mojibake.ROOT = original_root
        check_mojibake.tracked_text_files = original_files

    assert failures == [
        f"bad.md:1: suspicious mojibake sequence {check_mojibake._seq(0x00E2, 0x20AC, 0x201D)!r}"
    ]


def test_find_mojibake_accepts_clean_utf8(tmp_path: Path) -> None:
    good = tmp_path / "good.md"
    good.write_text("title \u2014 clean\n", encoding="utf-8")

    original_root = check_mojibake.ROOT
    original_files = check_mojibake.tracked_text_files
    try:
        check_mojibake.ROOT = tmp_path
        check_mojibake.tracked_text_files = lambda: [good]
        failures = check_mojibake.find_mojibake()
    finally:
        check_mojibake.ROOT = original_root
        check_mojibake.tracked_text_files = original_files

    assert failures == []
