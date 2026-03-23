from __future__ import annotations

"""Entity loading helpers for disassembly sessions."""

import json
from pathlib import Path

from disasm.types import EntityRecord


def load_entities(path: str | Path) -> list[EntityRecord]:
    entities: list[EntityRecord] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                entities.append(json.loads(line))
    return entities


def infer_target_name(target_dir: Path | None,
                      entities_path: str | Path) -> str | None:
    if target_dir is not None:
        return target_dir.name
    path = Path(entities_path)
    parent = path.parent
    if parent != path:
        return parent.name
    return None
