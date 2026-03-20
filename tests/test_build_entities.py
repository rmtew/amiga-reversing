from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_build_entities_help_loads_cleanly():
    script = Path(__file__).resolve().parent.parent / "scripts" / "build_entities.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Build entities.jsonl from hunk binary analysis" in result.stdout
