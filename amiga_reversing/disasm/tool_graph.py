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
TOOL_REGISTRY_VERSION = 2
TOOL_REGISTRY_KEYS = frozenset({"version", "runtime_tools", "functional_tools"})

RUNTIME_TOOL_IDS = ("host", "vamos", "winuae")
PERSISTED_RUNTIME_TOOL_IDS = ("vamos", "winuae")
FUNCTIONAL_TOOL_IDS = ("vasm", "genam")
CAPABILITY_IDS = ("assemble_vasm_source", "assemble_devpac_source", "assemble_m68k_source")
TOOL_STATUS_VALUES = ("available", "missing", "unsupported", "error")

_TOOL_EXECUTABLE_NAMES: dict[str, tuple[str, ...]] = {
    "vasm": ("vasmm68k_mot.exe", "vasmm68k_mot"),
    "genam": ("GenAm", "GenAm.exe", "genam"),
    "vamos": ("vamos", "vamos.exe"),
    "winuae": ("winuae", "winuae.exe"),
}
_BUNDLED_FUNCTIONAL_PATHS: dict[str, tuple[Path, ...]] = {
    "vasm": (Path("tools") / "vasmm68k_mot.exe", Path("ext") / "vasm" / "vasmm68k_mot.exe"),
    "genam": (Path("bin") / "GenAm",),
}
_FUNCTIONAL_DEFINITIONS: dict[str, dict[str, object]] = {
    "vasm": {
        "supported_runtimes": ("host",),
        "capabilities": ("assemble_vasm_source", "assemble_m68k_source"),
    },
    "genam": {
        "supported_runtimes": ("vamos",),
        "capabilities": ("assemble_devpac_source", "assemble_m68k_source"),
    },
}
_CAPABILITY_PREFERENCES: dict[str, tuple[str, ...]] = {
    "assemble_vasm_source": ("vasm",),
    "assemble_devpac_source": ("genam",),
    "assemble_m68k_source": ("vasm", "genam"),
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


def set_tool_artifact_path(
    kind: str,
    tool_id: str,
    path: str | None,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    bucket = _bucket_for_kind(kind)
    _require_tool_id(kind, tool_id)
    if tool_id == "host":
        raise ValueError("host runtime is synthetic and cannot be configured")
    registry = load_tool_registry(project_root=project_root)
    entries = cast(dict[str, object], registry.setdefault(bucket, {}))
    entry = dict(cast(dict[str, object], entries.get(tool_id, {}))) if isinstance(entries.get(tool_id), dict) else {}
    if path is None or not str(path).strip():
        entry.pop("path", None)
    else:
        entry["path"] = str(path)
    entries[tool_id] = entry
    save_tool_registry(registry, project_root=project_root)
    return load_tool_registry(project_root=project_root)


def runtime_tool_records(
    *,
    project_root: Path = PROJECT_ROOT,
    env_path: str | None = None,
) -> list[dict[str, object]]:
    registry = load_tool_registry(project_root=project_root)
    return [
        runtime_tool_record(runtime_id, registry=registry, project_root=project_root, env_path=env_path)
        for runtime_id in RUNTIME_TOOL_IDS
    ]


def functional_tool_records(
    *,
    project_root: Path = PROJECT_ROOT,
    env_path: str | None = None,
) -> list[dict[str, object]]:
    registry = load_tool_registry(project_root=project_root)
    runtimes = {
        cast(str, record["runtime_tool_id"]): record
        for record in runtime_tool_records(project_root=project_root, env_path=env_path)
    }
    return [
        functional_tool_record(
            functional_id,
            registry=registry,
            runtime_records=runtimes,
            project_root=project_root,
            env_path=env_path,
        )
        for functional_id in FUNCTIONAL_TOOL_IDS
    ]


def runtime_tool_record(
    runtime_tool_id: str,
    *,
    registry: Mapping[str, object] | None = None,
    project_root: Path = PROJECT_ROOT,
    env_path: str | None = None,
) -> dict[str, object]:
    _require_tool_id("runtime", runtime_tool_id)
    if runtime_tool_id == "host":
        return {
            "runtime_tool_id": "host",
            "tool_id": "host",
            "tool_kind": "runtime",
            "status": "available",
            "resolved_path": None,
            "discovery_source": "synthetic",
            "message": "host runtime is available",
            "probe_evidence": {
                "probe_method": "native_version",
                "probe_status": "unsupported",
                "version_text": None,
                "executable_stamp": None,
            },
        }
    registry_payload = registry if registry is not None else load_tool_registry(project_root=project_root)
    configured_path = _configured_tool_path(registry_payload, "runtime", runtime_tool_id)
    if configured_path:
        return _availability_for_path(
            runtime_tool_id,
            _resolve_configured_path(configured_path, project_root),
            tool_kind="runtime",
            discovery_source="configured_path",
            probe_method="native_version",
        )
    looked_up = _path_lookup(runtime_tool_id, env_path=env_path)
    if looked_up is not None:
        return _availability_for_path(
            runtime_tool_id,
            looked_up,
            tool_kind="runtime",
            discovery_source="path_lookup",
            probe_method="native_version",
        )
    return _missing_record(runtime_tool_id, tool_kind="runtime")


def functional_tool_record(
    functional_tool_id: str,
    *,
    registry: Mapping[str, object] | None = None,
    runtime_records: Mapping[str, Mapping[str, object]] | None = None,
    project_root: Path = PROJECT_ROOT,
    env_path: str | None = None,
) -> dict[str, object]:
    _require_tool_id("functional", functional_tool_id)
    registry_payload = registry if registry is not None else load_tool_registry(project_root=project_root)
    artifact = _functional_artifact_record(
        functional_tool_id,
        registry=registry_payload,
        project_root=project_root,
        env_path=env_path,
    )
    runtimes = runtime_records or {
        cast(str, record["runtime_tool_id"]): record
        for record in runtime_tool_records(project_root=project_root, env_path=env_path)
    }
    supported = tuple(cast(Sequence[str], _FUNCTIONAL_DEFINITIONS[functional_tool_id]["supported_runtimes"]))
    runtime_statuses = {runtime_id: runtimes[runtime_id]["status"] for runtime_id in supported if runtime_id in runtimes}
    missing_runtime_ids = [
        runtime_id for runtime_id in supported if runtime_statuses.get(runtime_id) != "available"
    ]
    artifact_status = cast(str, artifact.get("artifact_status") or artifact["status"])
    artifact_runnable_status = cast(str, artifact.get("runnable_status") or artifact_status)
    runnable_status = (
        "available"
        if artifact_runnable_status == "available" and not missing_runtime_ids
        else artifact_runnable_status
    )
    if artifact_runnable_status == "available" and missing_runtime_ids:
        runnable_status = "missing"
    return {
        "functional_tool_id": functional_tool_id,
        "tool_id": functional_tool_id,
        "tool_kind": "functional",
        "status": runnable_status,
        "runnable_status": runnable_status,
        "artifact_status": artifact_status,
        "runtime_statuses": runtime_statuses,
        "missing_runtime_ids": missing_runtime_ids,
        "supported_runtime_ids": list(supported),
        "capability_ids": list(cast(Sequence[str], _FUNCTIONAL_DEFINITIONS[functional_tool_id]["capabilities"])),
        "resolved_path": artifact["resolved_path"],
        "discovery_source": artifact["discovery_source"],
        "message": _functional_message(functional_tool_id, artifact_status, runnable_status, missing_runtime_ids),
        "probe_evidence": artifact["probe_evidence"],
        "version": cast(Mapping[str, object], artifact["probe_evidence"]).get("version_text"),
        "executable_stamp": cast(Mapping[str, object], artifact["probe_evidence"]).get("executable_stamp"),
    }


def resolve_capability(
    capability_id: str,
    *,
    project_root: Path = PROJECT_ROOT,
    env_path: str | None = None,
) -> dict[str, object]:
    _require_capability_id(capability_id)
    registry = load_tool_registry(project_root=project_root)
    runtimes = {
        cast(str, record["runtime_tool_id"]): record
        for record in runtime_tool_records(project_root=project_root, env_path=env_path)
    }
    functional = {
        functional_id: functional_tool_record(
            functional_id,
            registry=registry,
            runtime_records=runtimes,
            project_root=project_root,
            env_path=env_path,
        )
        for functional_id in _CAPABILITY_PREFERENCES[capability_id]
    }
    candidates: list[dict[str, object]] = []
    for functional_id in _CAPABILITY_PREFERENCES[capability_id]:
        functional_record = functional[functional_id]
        for runtime_id in cast(Sequence[str], functional_record["supported_runtime_ids"]):
            runtime_record = runtimes[runtime_id]
            candidates.append(_capability_candidate(capability_id, functional_record, runtime_record))
    selected = next((candidate for candidate in candidates if candidate["runnable_status"] == "available"), None)
    if selected is None and candidates:
        selected = candidates[0]
    return {
        "capability_id": capability_id,
        "status": selected["runnable_status"] if selected else "missing",
        "available": bool(selected and selected["runnable_status"] == "available"),
        "selected": selected,
        "candidates": candidates,
    }


def capability_ids_for_oracle_modes(oracle_modes: Sequence[object]) -> tuple[str, ...]:
    capability_ids: list[str] = []
    for mode in oracle_modes:
        if mode == "vasm":
            capability_ids.append("assemble_vasm_source")
        elif mode == "devpac":
            capability_ids.append("assemble_devpac_source")
    return tuple(dict.fromkeys(capability_ids))


def capability_availability_for_modes(
    oracle_modes: Sequence[object],
    *,
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, object]]:
    return [
        _availability_record_from_resolution(resolve_capability(capability_id, project_root=project_root))
        for capability_id in capability_ids_for_oracle_modes(oracle_modes)
    ]


def _availability_record_from_resolution(resolution: Mapping[str, object]) -> dict[str, object]:
    selected = resolution.get("selected")
    if not isinstance(selected, dict):
        return {
            "capability_id": resolution.get("capability_id"),
            "tool_id": None,
            "status": "missing",
            "message": "no tool candidate found",
        }
    return {
        "capability_id": resolution["capability_id"],
        "tool_id": selected["functional_tool_id"],
        "functional_tool_id": selected["functional_tool_id"],
        "runtime_tool_id": selected["runtime_tool_id"],
        "tool_chain": selected["tool_chain"],
        "status": selected["runnable_status"],
        "runnable_status": selected["runnable_status"],
        "artifact_status": selected["artifact_status"],
        "runtime_status": selected["runtime_status"],
        "missing_runtime_ids": selected["missing_runtime_ids"],
        "resolved_path": selected["functional_resolved_path"],
        "runtime_resolved_path": selected["runtime_resolved_path"],
        "required": True,
        "message": selected["message"],
        "probe_evidence": selected["probe_evidence"],
        "version": cast(Mapping[str, object], selected["probe_evidence"]).get("version_text"),
        "executable_stamp": cast(Mapping[str, object], selected["probe_evidence"]).get("executable_stamp"),
    }


def _capability_candidate(
    capability_id: str,
    functional_record: Mapping[str, object],
    runtime_record: Mapping[str, object],
) -> dict[str, object]:
    functional_id = cast(str, functional_record["functional_tool_id"])
    runtime_id = cast(str, runtime_record["runtime_tool_id"])
    runtime_status = cast(str, runtime_record["status"])
    artifact_status = cast(str, functional_record["artifact_status"])
    functional_runnable_status = cast(str, functional_record["runnable_status"])
    missing_runtime_ids = [] if runtime_status == "available" else [runtime_id]
    runnable_status = (
        "available"
        if functional_runnable_status == "available" and runtime_status == "available"
        else functional_runnable_status
    )
    if functional_runnable_status == "available" and runtime_status != "available":
        runnable_status = "missing"
    tool_chain = [functional_id] if runtime_id == "host" else [runtime_id, functional_id]
    return {
        "capability_id": capability_id,
        "functional_tool_id": functional_id,
        "runtime_tool_id": runtime_id,
        "tool_chain": tool_chain,
        "runnable_status": runnable_status,
        "artifact_status": artifact_status,
        "runtime_status": runtime_status,
        "missing_runtime_ids": missing_runtime_ids,
        "functional_resolved_path": functional_record["resolved_path"],
        "runtime_resolved_path": runtime_record["resolved_path"],
        "probe_evidence": functional_record["probe_evidence"],
        "message": _functional_message(functional_id, artifact_status, runnable_status, missing_runtime_ids),
    }


def _functional_artifact_record(
    functional_tool_id: str,
    *,
    registry: Mapping[str, object],
    project_root: Path,
    env_path: str | None,
) -> dict[str, object]:
    configured_path = _configured_tool_path(registry, "functional", functional_tool_id)
    probe_method = "hash_only" if functional_tool_id == "genam" else "native_version"
    if configured_path:
        return _availability_for_path(
            functional_tool_id,
            _resolve_configured_path(configured_path, project_root),
            tool_kind="functional",
            discovery_source="configured_path",
            probe_method=probe_method,
        )
    for relative in _BUNDLED_FUNCTIONAL_PATHS[functional_tool_id]:
        candidate = project_root / relative
        if candidate.exists():
            return _availability_for_path(
                functional_tool_id,
                candidate,
                tool_kind="functional",
                discovery_source="bundled",
                probe_method=probe_method,
            )
    looked_up = _path_lookup(functional_tool_id, env_path=env_path)
    if looked_up is not None:
        return _availability_for_path(
            functional_tool_id,
            looked_up,
            tool_kind="functional",
            discovery_source="path_lookup",
            probe_method=probe_method,
        )
    return _missing_record(functional_tool_id, tool_kind="functional")


def _empty_registry() -> dict[str, object]:
    return {"version": TOOL_REGISTRY_VERSION, "runtime_tools": {}, "functional_tools": {}}


def _normalized_registry(registry: Mapping[str, object]) -> dict[str, object]:
    payload = dict(registry)
    payload.setdefault("runtime_tools", {})
    payload.setdefault("functional_tools", {})
    return payload


def _validate_registry_payload(payload: Mapping[str, object]) -> None:
    unknown_keys = set(payload) - TOOL_REGISTRY_KEYS
    if unknown_keys:
        raise ValueError(f"tool registry has unknown top-level keys: {', '.join(sorted(unknown_keys))}")
    if "version" not in payload:
        raise ValueError("tool registry version is required")
    if payload.get("version") != TOOL_REGISTRY_VERSION:
        raise ValueError(f"unsupported tool registry version: {payload.get('version')!r}")
    for kind, bucket in (("runtime", "runtime_tools"), ("functional", "functional_tools")):
        entries = payload.get(bucket, {})
        if not isinstance(entries, dict):
            raise ValueError(f"tool registry {bucket} must be an object")
        for tool_id, entry in entries.items():
            if not isinstance(tool_id, str):
                raise ValueError(f"tool registry {kind} tool id must be a string")
            if kind == "runtime" and tool_id == "host":
                raise ValueError("host runtime is synthetic and must not be persisted")
            _require_tool_id(kind, tool_id)
            if not isinstance(entry, dict):
                raise ValueError(f"tool registry entry for {tool_id} must be an object")
            path = entry.get("path")
            if path is not None and not isinstance(path, str):
                raise ValueError(f"tool registry path for {tool_id} must be a string")


def _require_tool_id(kind: str, tool_id: str) -> None:
    if kind == "runtime":
        allowed = PERSISTED_RUNTIME_TOOL_IDS if tool_id != "host" else RUNTIME_TOOL_IDS
        valid = tool_id in RUNTIME_TOOL_IDS
    elif kind == "functional":
        allowed = FUNCTIONAL_TOOL_IDS
        valid = tool_id in FUNCTIONAL_TOOL_IDS
    else:
        raise ValueError(f"unsupported tool kind {kind!r}; expected runtime or functional")
    if not valid:
        raise ValueError(f"unsupported {kind} tool id {tool_id!r}; expected one of {', '.join(allowed)}")


def _require_capability_id(capability_id: str) -> None:
    if capability_id not in CAPABILITY_IDS:
        raise ValueError(f"unsupported capability id {capability_id!r}; expected one of {', '.join(CAPABILITY_IDS)}")


def _bucket_for_kind(kind: str) -> str:
    if kind == "runtime":
        return "runtime_tools"
    if kind == "functional":
        return "functional_tools"
    raise ValueError(f"unsupported tool kind {kind!r}; expected runtime or functional")


def _configured_tool_path(registry: Mapping[str, object], kind: str, tool_id: str) -> str | None:
    bucket = registry.get(_bucket_for_kind(kind))
    if not isinstance(bucket, dict):
        return None
    entry = bucket.get(tool_id)
    if not isinstance(entry, dict):
        return None
    path = entry.get("path")
    return path if isinstance(path, str) and path.strip() else None


def _resolve_configured_path(path: str, project_root: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else project_root / candidate


def _path_lookup(tool_id: str, *, env_path: str | None) -> Path | None:
    for executable in _TOOL_EXECUTABLE_NAMES[tool_id]:
        found = shutil.which(executable, path=env_path)
        if found:
            return Path(found)
    return None


def _missing_record(tool_id: str, *, tool_kind: str) -> dict[str, object]:
    id_key = "runtime_tool_id" if tool_kind == "runtime" else "functional_tool_id"
    return {
        id_key: tool_id,
        "tool_id": tool_id,
        "tool_kind": tool_kind,
        "status": "missing",
        "resolved_path": None,
        "discovery_source": "not_checked",
        "message": f"{tool_id} was not found",
        "probe_evidence": {
            "probe_method": "hash_only" if tool_id == "genam" else "native_version",
            "probe_status": "missing",
            "version_text": None,
            "executable_stamp": None,
        },
    }


def _availability_for_path(
    tool_id: str,
    path: Path,
    *,
    tool_kind: str,
    discovery_source: str,
    probe_method: str,
) -> dict[str, object]:
    id_key = "runtime_tool_id" if tool_kind == "runtime" else "functional_tool_id"
    if not path.exists():
        return {
            id_key: tool_id,
            "tool_id": tool_id,
            "tool_kind": tool_kind,
            "status": "missing",
            "artifact_status": "missing",
            "runnable_status": "missing",
            "resolved_path": str(path),
            "discovery_source": discovery_source,
            "message": f"{tool_id} configured path does not exist: {path}",
            "probe_evidence": _probe_evidence(probe_method, "missing", None, None),
        }
    if path.is_dir():
        return {
            id_key: tool_id,
            "tool_id": tool_id,
            "tool_kind": tool_kind,
            "status": "unsupported",
            "artifact_status": "unsupported",
            "runnable_status": "unsupported",
            "resolved_path": str(path),
            "discovery_source": discovery_source,
            "message": f"{tool_id} path is a directory: {path}",
            "probe_evidence": _probe_evidence(probe_method, "unsupported", None, None),
        }
    try:
        stamp = _executable_stamp(path)
        probe = _probe_for_path(path, probe_method)
        runnable_status = _runnable_status_from_probe(probe_method, probe)
        return {
            id_key: tool_id,
            "tool_id": tool_id,
            "tool_kind": tool_kind,
            "status": runnable_status,
            "artifact_status": "available",
            "runnable_status": runnable_status,
            "resolved_path": str(path),
            "discovery_source": discovery_source,
            "message": f"{tool_id} is available" if runnable_status == "available" else f"{tool_id} is not runnable",
            "probe_evidence": _probe_evidence(
                probe_method,
                cast(str, probe["probe_status"]),
                cast(str | None, probe["version_text"]),
                stamp,
                extra=probe,
            ),
        }
    except OSError as exc:
        return {
            id_key: tool_id,
            "tool_id": tool_id,
            "tool_kind": tool_kind,
            "status": "error",
            "artifact_status": "error",
            "runnable_status": "error",
            "resolved_path": str(path),
            "discovery_source": discovery_source,
            "message": str(exc),
            "probe_evidence": _probe_evidence(probe_method, "error", None, None),
        }


def _probe_evidence(
    probe_method: str,
    probe_status: str,
    version_text: str | None,
    executable_stamp: Mapping[str, object] | None,
    *,
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    evidence: dict[str, object] = {
        "probe_method": probe_method,
        "probe_status": probe_status,
        "version_text": version_text,
        "executable_stamp": dict(executable_stamp) if executable_stamp is not None else None,
    }
    if extra is not None:
        for key in ("stdout_excerpt", "stderr_excerpt", "probe_error"):
            value = extra.get(key)
            if value:
                evidence[key] = value
    return evidence


def _probe_for_path(path: Path, probe_method: str) -> dict[str, object]:
    if probe_method == "hash_only":
        return {"probe_status": "available", "version_text": None}
    if probe_method == "native_version":
        return _native_version_probe(path)
    return {"probe_status": "unsupported", "version_text": None}


def _runnable_status_from_probe(probe_method: str, probe: Mapping[str, object]) -> str:
    if probe_method == "hash_only":
        return "available"
    probe_status = probe.get("probe_status")
    if probe_status in {"available", "unsupported"}:
        return "available"
    return "error"


def _native_version_probe(path: Path) -> dict[str, object]:
    if os.name == "nt" and path.suffix.lower() not in {".exe", ".bat", ".cmd"}:
        return {"probe_status": "unsupported", "version_text": None}
    try:
        result = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "probe_status": "error",
            "version_text": None,
            "probe_error": f"version probe timed out after {exc.timeout:g}s",
        }
    except OSError as exc:
        return {
            "probe_status": "error",
            "version_text": None,
            "probe_error": str(exc),
        }
    text = (result.stdout or result.stderr).strip().splitlines()
    if result.returncode != 0:
        probe_status = "unsupported" if text else "error"
        return {
            "probe_status": probe_status,
            "version_text": None,
            "stdout_excerpt": _first_output_line(result.stdout),
            "stderr_excerpt": _first_output_line(result.stderr),
        }
    version_text = text[0][:160] if text else None
    return {
        "probe_status": "available" if version_text else "unsupported",
        "version_text": version_text,
    }


def _first_output_line(value: str) -> str | None:
    lines = value.strip().splitlines()
    return lines[0][:160] if lines else None


def _executable_stamp(path: Path) -> dict[str, object]:
    stat = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "sha256": digest,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _functional_message(
    functional_tool_id: str,
    artifact_status: str,
    runnable_status: str,
    missing_runtime_ids: Sequence[str],
) -> str:
    if runnable_status == "available":
        return f"{functional_tool_id} is runnable"
    if artifact_status == "available" and missing_runtime_ids:
        return f"{functional_tool_id} artifact is available but missing runtime: {', '.join(missing_runtime_ids)}"
    if artifact_status == "available":
        return f"{functional_tool_id} artifact is available but not runnable: {runnable_status}"
    return f"{functional_tool_id} artifact is {artifact_status}"
