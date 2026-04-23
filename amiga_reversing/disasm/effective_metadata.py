from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from amiga_reversing.disasm.target_metadata import TargetMetadata, load_target_metadata
from amiga_reversing.disasm.target_ui_edits import (
    apply_target_ui_edits,
    load_target_ui_edits,
    target_ui_edits_stamp_text,
)


def effective_target_metadata(target_dir: Path) -> TargetMetadata | None:
    return apply_target_ui_edits(load_target_metadata(target_dir), load_target_ui_edits(target_dir))


def effective_metadata_text(target_dir: Path) -> str:
    metadata = effective_target_metadata(target_dir)
    if metadata is None:
        return ""
    return json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n"


def effective_metadata_hash(target_dir: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(effective_metadata_text(target_dir).encode("utf-8"))
    edits_text = target_ui_edits_stamp_text(target_dir)
    if edits_text:
        hasher.update(b"\n--target-ui-edits--\n")
        hasher.update(edits_text.encode("utf-8"))
    return hasher.hexdigest()


@contextmanager
def effective_metadata_file(target_dir: Path) -> Iterator[Path | None]:
    text = effective_metadata_text(target_dir)
    if not text:
        yield None
        return
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as temp_file:
            temp_file.write(text)
            temp_path = Path(temp_file.name)
        yield temp_path
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
