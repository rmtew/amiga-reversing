from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REAL_TARGET_FIXTURES = (
    {
        "name": "GenAm",
        "backend": "amiga-hunk",
        "binary": ROOT / "bin" / "GenAm",
        "source": ROOT / "bin" / "GenAm.latest.s",
        "benchmark": ROOT / "bin" / "GenAm.benchmark.json",
        "include_dir": ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include",
    },
    {
        "name": "BIN_GEN",
        "backend": "atari-st",
        "binary": ROOT / "bin" / "BIN_GEN.TTP",
        "source": ROOT / "bin" / "BIN_GEN.latest.s",
        "benchmark": ROOT / "bin" / "BIN_GEN.benchmark.json",
        "include_dir": ROOT / "ext" / "atarist_includes" / "devpac_3_10" / "include",
    },
)


def get_real_target_fixture(name: str) -> dict[str, Path | str]:
    for fixture in REAL_TARGET_FIXTURES:
        if fixture["name"] == name:
            return fixture
    raise KeyError(name)
