from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from amiga_reversing.disasm.project_paths import PROJECT_ROOT

TOOL_REGISTRY_FILE_NAME = "tool_registry.json"
TOOL_REGISTRY_DIR_NAME = ".amiga_reversing"
TOOL_REGISTRY_VERSION = 1
TOOL_IDS = ("vasm", "genam", "vamos")
TOOL_STATUS_VALUES = ("available", "missing", "unsupported", "error")
TOOL_DISCOVERY_SOURCES = ("configured_path", "path_lookup", "bundled", "not_checked")

_TOOL_EXECUTABLE_NAMES: dict[str, tuple[str, ...]] = {
    "vasm": ("vasmm68k_mot.exe", "vasmm68k_mot"),
    "genam": ("GenAm", "GenAm.exe", "genam"),
    "vamos": ("vamos", "vamos.exe"),
}
_BUNDLED_TOOL_PATHS: dict[str, tuple[Path, ...]] = {
    "vasm": (Path("tools") / "vasmm68k_mot.exe", Path("ext") / "vasm" / "vasmm68k_mot.exe"),
    "genam": (Path("bin") / "GenAm",),
    "vamos": (),
}


def tool_registry_path(*, project_root: Path = PROJECT_ROOT) -> Path:
    return project_root / TOOL_REGISTRY_DIR_NAME / TOOL_REGISTRY_FILE_NAME


def load_tool_registry(*, project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    path = tool_registry_path(project_root=project_root)
    if not path.exists():
        return _empty_registry()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Bad {path.name}: expected object")
    registry = cast(dict[str, object], payload)
    _validate_registry_payload(registry)
    return _normalized_registry(registry)


def save_tool_registry(registry: Mapping[str, object], *, project_root: Path = PROJECT_ROOT) -> Path:
    payload = _normalized_registry(registry)
    _validate_registry_payload(payload)
    path = tool_registry_path(project_root=project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def set_tool_path(tool_id: str, path: str | None, *, project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    _require_tool_id(tool_id)
    registry = load_tool_registry(project_root=project_root)
    tools = cast(dict[str, object], registry.setdefault("tools", {}))
    entry = dict(cast(dict[str, object], tools.get(tool_id, {}))) if isinstance(tools.get(tool_id), dict) else {}
    if path is None or not str(path).strip():
        entry.pop("path", None)
    else:
        entry["path"] = str(path)
    tools[tool_id] = entry
    save_tool_registry(registry, project_root=project_root)
    return registry


def tool_availability_records(
    tool_ids: Sequence[str] | None = None,
    *,
    required_tool_ids: Sequence[str] = (),
    project_root: Path = PROJECT_ROOT,
    env_path: str | None = None,
) -> list[dict[str, object]]:
    registry = load_tool_registry(project_root=project_root)
    ids = tuple(tool_ids or TOOL_IDS)
    return [
        tool_availability_record(
            tool_id,
            registry=registry,
            required=tool_id in set(required_tool_ids),
            project_root=project_root,
            env_path=env_path,
        )
        for tool_id in ids
    ]


def oracle_tool_ids_for_modes(oracle_modes: Sequence[object]) -> tuple[str, ...]:
    tool_ids: list[str] = []
    for mode in oracle_modes:
        if mode == "vasm":
            tool_ids.append("vasm")
        elif mode == "devpac":
            tool_ids.extend(("genam", "vamos"))
    return tuple(dict.fromkeys(tool_ids))


def tool_availability_record(
    tool_id: str,
    *,
    registry: Mapping[str, object] | None = None,
    required: bool = False,
    project_root: Path = PROJECT_ROOT,
    env_path: str | None = None,
) -> dict[str, object]:
    _require_tool_id(tool_id)
    registry_payload = registry if registry is not None else load_tool_registry(project_root=project_root)
    configured_path = _configured_tool_path(registry_payload, tool_id)
    if configured_path:
        return _availability_for_path(
            tool_id,
            _resolve_configured_path(configured_path, project_root),
            required=required,
            discovery_source="configured_path",
        )
    bundled = _bundled_tool_path(tool_id, project_root)
    if bundled is not None:
        return _availability_for_path(tool_id, bundled, required=required, discovery_source="bundled")
    looked_up = _path_lookup(tool_id, env_path=env_path)
    if looked_up is not None:
        return _availability_for_path(tool_id, looked_up, required=required, discovery_source="path_lookup")
    return {
        "tool_id": tool_id,
        "status": "missing",
        "required": required,
        "resolved_path": None,
        "version": None,
        "discovery_source": "not_checked",
        "message": f"{tool_id} was not found",
        "executable_stamp": None,
    }


def _empty_registry() -> dict[str, object]:
    return {"version": TOOL_REGISTRY_VERSION, "tools": {}}


def _normalized_registry(registry: Mapping[str, object]) -> dict[str, object]:
    payload = dict(registry)
    payload.setdefault("version", TOOL_REGISTRY_VERSION)
    payload.setdefault("tools", {})
    return payload


def _validate_registry_payload(payload: dict[str, object]) -> None:
    if payload.get("version", TOOL_REGISTRY_VERSION) != TOOL_REGISTRY_VERSION:
        raise ValueError(f"unsupported tool registry version: {payload.get('version')!r}")
    tools = payload.get("tools", {})
    if not isinstance(tools, dict):
        raise ValueError("tool registry tools must be an object")
    for tool_id, entry in tools.items():
        if not isinstance(tool_id, str):
            raise ValueError("tool registry tool id must be a string")
        _require_tool_id(tool_id)
        if not isinstance(entry, dict):
            raise ValueError(f"tool registry entry for {tool_id} must be an object")
        path = entry.get("path")
        if path is not None and not isinstance(path, str):
            raise ValueError(f"tool registry path for {tool_id} must be a string")
        hints = entry.get("hints")
        if hints is not None and (not isinstance(hints, list) or not all(isinstance(item, str) for item in hints)):
            raise ValueError(f"tool registry hints for {tool_id} must be a list of strings")


def _require_tool_id(tool_id: str) -> None:
    if tool_id not in TOOL_IDS:
        allowed = ", ".join(TOOL_IDS)
        raise ValueError(f"unsupported tool id {tool_id!r}; expected one of {allowed}")


def _configured_tool_path(registry: Mapping[str, object], tool_id: str) -> str | None:
    tools = registry.get("tools")
    if not isinstance(tools, dict):
        return None
    entry = tools.get(tool_id)
    if not isinstance(entry, dict):
        return None
    path = entry.get("path")
    return path if isinstance(path, str) and path.strip() else None


def _resolve_configured_path(path: str, project_root: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else project_root / candidate


def _bundled_tool_path(tool_id: str, project_root: Path) -> Path | None:
    for relative in _BUNDLED_TOOL_PATHS[tool_id]:
        candidate = project_root / relative
        if candidate.exists():
            return candidate
    return None


def _path_lookup(tool_id: str, *, env_path: str | None) -> Path | None:
    for executable in _TOOL_EXECUTABLE_NAMES[tool_id]:
        found = shutil.which(executable, path=env_path)
        if found:
            return Path(found)
    return None


def _availability_for_path(
    tool_id: str,
    path: Path,
    *,
    required: bool,
    discovery_source: str,
) -> dict[str, object]:
    if not path.exists():
        return {
            "tool_id": tool_id,
            "status": "missing",
            "required": required,
            "resolved_path": str(path),
            "version": None,
            "discovery_source": discovery_source,
            "message": f"{tool_id} configured path does not exist: {path}",
            "executable_stamp": None,
        }
    if path.is_dir():
        return {
            "tool_id": tool_id,
            "status": "unsupported",
            "required": required,
            "resolved_path": str(path),
            "version": None,
            "discovery_source": discovery_source,
            "message": f"{tool_id} path is a directory: {path}",
            "executable_stamp": None,
        }
    try:
        return {
            "tool_id": tool_id,
            "status": "available",
            "required": required,
            "resolved_path": str(path),
            "version": _cheap_version(path),
            "discovery_source": discovery_source,
            "message": f"{tool_id} is available",
            "executable_stamp": _executable_stamp(path),
        }
    except OSError as exc:
        return {
            "tool_id": tool_id,
            "status": "error",
            "required": required,
            "resolved_path": str(path),
            "version": None,
            "discovery_source": discovery_source,
            "message": str(exc),
            "executable_stamp": None,
        }


def _cheap_version(path: Path) -> str | None:
    if os.name == "nt" and path.suffix.lower() not in {".exe", ".bat", ".cmd"}:
        return None
    try:
        result = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (result.stdout or result.stderr).strip().splitlines()
    return text[0][:160] if text else None


def _executable_stamp(path: Path) -> dict[str, object]:
    stat = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "sha256": digest,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
