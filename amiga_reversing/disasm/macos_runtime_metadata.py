"""Classic Mac OS runtime metadata loaded from generated platform facts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from amiga_reversing.disasm.project_paths import PROJECT_ROOT

GENERATED_METADATA_PATH = PROJECT_ROOT / "src" / "generated" / "mac_os_runtime.json"


@lru_cache(maxsize=1)
def load_generated_mac_os_runtime_metadata(path: Path = GENERATED_METADATA_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} does not contain a JSON object")
    return payload
