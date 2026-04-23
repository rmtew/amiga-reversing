from __future__ import annotations

import json
from pathlib import Path

from amiga_reversing.disasm.reproduction_worker import _write_json_atomic


def test_write_json_atomic_replaces_target_and_cleans_temp(tmp_path: Path) -> None:
    path = tmp_path / "worker.progress.json"
    temp_path = tmp_path / ".worker.progress.json.tmp"
    path.write_text('{"phase":"old"}\n', encoding="utf-8")

    _write_json_atomic(path, {"phase": "prepare", "row_count": 3})

    assert json.loads(path.read_text(encoding="utf-8")) == {"phase": "prepare", "row_count": 3}
    assert not temp_path.exists()
