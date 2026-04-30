from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.scripts.platform_manifest_io import (
    load_disk_image_bytes,
    read_jsonl_manifest,
    reconstruct_file_bytes,
    sha256,
    write_jsonl_manifest,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "corpus" / "platform_disk_manifest.jsonl"
DEFAULT_OUTPUT = ROOT / "corpus" / "platform_file_manifest.jsonl"
FILE_DLL = ROOT / "src" / "build" / "platform_file_lib.dll"
AMIGA_HUNK_RUNTIME_JSON = ROOT / "src" / "generated" / "amiga_hunk_file_runtime.json"
M68K_DIAG_SEVERITY_ERROR = 3
M68K_DIAG_MESSAGE_SIZE = 160
M68K_DIAG_LIST_CAPACITY = 8


class M68kDiag(ctypes.Structure):
    _fields_ = [
        ("severity", ctypes.c_uint32),
        ("code", ctypes.c_uint32),
        ("message", ctypes.c_char * M68K_DIAG_MESSAGE_SIZE),
    ]


class M68kDiagList(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_size_t),
        ("dropped_count", ctypes.c_size_t),
        ("items", M68kDiag * M68K_DIAG_LIST_CAPACITY),
    ]


class PlatformFileTextResult(ctypes.Structure):
    _fields_ = [
        ("text", ctypes.c_void_p),
        ("diagnostics", M68kDiagList),
    ]


def _diag_message(diagnostics: M68kDiagList) -> str:
    for index in range(diagnostics.count):
        if diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR:
            return diagnostics.items[index].message.decode("utf-8")
    if diagnostics.count:
        return diagnostics.items[0].message.decode("utf-8")
    return ""


def _diag_has_errors(diagnostics: M68kDiagList) -> bool:
    return any(
        diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR
        for index in range(diagnostics.count)
    )


def _ensure_tools_built() -> None:
    result = subprocess.run(
        ["cmd", "/c", "src\\build.bat"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)


def _load_amiga_hunk_top_level_magics() -> set[int]:
    payload = json.loads(AMIGA_HUNK_RUNTIME_JSON.read_text(encoding="utf-8"))
    return {int(value) for value in payload.get("container_magic_wire_ids", [])}


AMIGA_HUNK_TOP_LEVEL_MAGICS = _load_amiga_hunk_top_level_magics()


def _is_probable_amiga_hunk(file_bytes: bytes) -> bool:
    if len(file_bytes) < 4:
        return False
    magic = int.from_bytes(file_bytes[:4], "big")
    return magic in AMIGA_HUNK_TOP_LEVEL_MAGICS


def _is_probable_amiga_iff(file_bytes: bytes) -> bool:
    return len(file_bytes) >= 12 and file_bytes[:4] == b"FORM"


def _is_probable_amiga_text(file_bytes: bytes) -> bool:
    allowed = 0
    if not file_bytes or len(file_bytes) < 8 or b"\x00" in file_bytes:
        return False
    for value in file_bytes:
        if value in (9, 10, 13) or 32 <= value <= 126:
            allowed += 1
    return (allowed / len(file_bytes)) >= 0.95


def _inspect_amiga_iff(file_bytes: bytes) -> dict[str, Any]:
    return {
        "platform": "amiga-iff",
        "file_kind": "iff",
        "declared_size": int.from_bytes(file_bytes[4:8], "big"),
        "form_type": file_bytes[8:12].decode("latin-1", errors="replace"),
    }


def _inspect_amiga_text(file_bytes: bytes) -> dict[str, Any]:
    return {
        "platform": "amiga-text",
        "file_kind": "text",
        "line_count": file_bytes.count(b"\n") + 1,
        "preview": file_bytes[:80].decode("latin-1", errors="replace"),
    }


def _inspect_file(platform_name: str, suffix: str, file_bytes: bytes) -> dict[str, Any]:
    del suffix
    library = _platform_file_library()
    data_array = (ctypes.c_ubyte * len(file_bytes)).from_buffer_copy(file_bytes if file_bytes else b"\0")
    result = library.platform_file_inspect_buffer_json(
        platform_name.encode("utf-8"),
        data_array,
        len(file_bytes),
    )
    if _diag_has_errors(result.diagnostics):
        raise RuntimeError(_diag_message(result.diagnostics))
    try:
        payload = json.loads(ctypes.string_at(result.text).decode("utf-8"))
        assert isinstance(payload, dict)
        return payload
    finally:
        library.platform_file_free_text(result.text)


@lru_cache(maxsize=1)
def _platform_file_library() -> Any:
    fd, copied_path = tempfile.mkstemp(prefix="platform_file_lib_", suffix=".dll")
    os.close(fd)
    shutil.copy2(FILE_DLL, copied_path)
    library = ctypes.CDLL(copied_path)
    library.platform_file_inspect_buffer_json.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
    ]
    library.platform_file_inspect_buffer_json.restype = PlatformFileTextResult
    library.platform_file_free_text.argtypes = [ctypes.c_void_p]
    library.platform_file_free_text.restype = None
    return library


def _candidate_entries(disk_entry: dict[str, Any]) -> list[dict[str, Any]]:
    inspect = disk_entry["expect"].get("inspect") or {}
    entries = inspect.get("entries", [])
    candidates: list[dict[str, Any]] = []
    if disk_entry["platform"] == "atari-st-disk":
        for entry in entries:
            if entry.get("kind") == 1 and entry.get("is_executable_candidate") == 1 and entry.get("file_size", 0) > 0:
                candidates.append({"backend": "atari-st", "suffix": ".prg", "entry": entry})
    elif disk_entry["platform"] == "amiga-disk":
        for entry in entries:
            if entry.get("kind") == 1 and entry.get("byte_size", 0) > 0:
                candidates.append({"entry": entry})
    return candidates


def _file_origin(disk_entry: dict[str, Any], file_entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "display_name": disk_entry["origin"]["display_name"],
        "source_relpath": disk_entry["origin"]["source_relpath"],
        "container_relpath": disk_entry["origin"]["container_relpath"],
        "member_name": disk_entry["origin"]["member_name"],
        "in_image_path": file_entry["path"],
        "alternate_origins": [],
    }


def _file_ref(disk_entry: dict[str, Any], file_entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "disk_platform": disk_entry["platform"],
        "disk_id": disk_entry["id"],
        "extents": file_entry.get("extents", []),
        "alternate_refs": [],
    }


def _manifest_id(backend_name: str, file_bytes: bytes, disk_entry: dict[str, Any], file_entry: dict[str, Any]) -> str:
    if file_bytes:
        return f"{backend_name}/{sha256(file_bytes)[:12]}"
    key = f"{backend_name}\0{disk_entry['id']}\0{file_entry.get('path', '')}".encode("utf-8")
    return f"{backend_name}/{sha256(key)[:12]}"


def _error_manifest_entry(
    disk_entry: dict[str, Any],
    backend_name: str,
    file_entry: dict[str, Any],
    file_bytes: bytes,
    error: str,
) -> dict[str, Any]:
    return {
        "id": _manifest_id(backend_name, file_bytes, disk_entry, file_entry),
        "platform": backend_name,
        "sha256": sha256(file_bytes),
        "size": len(file_bytes),
        "disk_sha256": disk_entry["sha256"],
        "origin": _file_origin(disk_entry, file_entry),
        "file_ref": _file_ref(disk_entry, file_entry),
        "expect": {
            "summary_version": 1,
            "status": "error",
            "error": error,
        },
    }


def _manifest_entry(
    disk_entry: dict[str, Any],
    backend_name: str,
    file_entry: dict[str, Any],
    file_bytes: bytes,
    inspect: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": _manifest_id(backend_name, file_bytes, disk_entry, file_entry),
        "platform": backend_name,
        "sha256": sha256(file_bytes),
        "size": len(file_bytes),
        "disk_sha256": disk_entry["sha256"],
        "origin": _file_origin(disk_entry, file_entry),
        "file_ref": _file_ref(disk_entry, file_entry),
        "expect": {
            "summary_version": 1,
            "status": "ok",
            "inspect": inspect,
        },
    }


def _without_alternates(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    result = dict(mapping)
    result.pop(key, None)
    return result


def _append_unique(items: list[dict[str, Any]], item: dict[str, Any]) -> None:
    if item not in items:
        items.append(item)


def _merge_duplicate_manifest_entry(existing: dict[str, Any], duplicate: dict[str, Any]) -> None:
    origin = existing.setdefault("origin", {})
    alternate_origins = origin.setdefault("alternate_origins", [])
    duplicate_origin = _without_alternates(duplicate.get("origin", {}), "alternate_origins")
    canonical_origin = _without_alternates(origin, "alternate_origins")
    if duplicate_origin != canonical_origin:
        _append_unique(alternate_origins, duplicate_origin)

    file_ref = existing.setdefault("file_ref", {})
    alternate_refs = file_ref.setdefault("alternate_refs", [])
    duplicate_ref = _without_alternates(duplicate.get("file_ref", {}), "alternate_refs")
    canonical_ref = _without_alternates(file_ref, "alternate_refs")
    if duplicate_ref != canonical_ref:
        _append_unique(alternate_refs, duplicate_ref)


def _dedupe_manifest(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for entry in entries:
        existing = by_id.get(entry["id"])
        if existing is None:
            by_id[entry["id"]] = entry
            result.append(entry)
        else:
            _merge_duplicate_manifest_entry(existing, entry)
    return result


def build_manifest(disk_manifest_path: Path) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for disk_entry in read_jsonl_manifest(disk_manifest_path):
        if disk_entry.get("expect", {}).get("status") != "ok":
            continue
        image_bytes = load_disk_image_bytes(disk_entry["origin"], root=ROOT)
        for candidate in _candidate_entries(disk_entry):
            backend_name = candidate.get("backend")
            suffix = candidate.get("suffix", ".bin")
            file_entry = candidate["entry"]
            file_bytes = b""
            try:
                file_bytes = reconstruct_file_bytes(disk_entry["platform"], file_entry, image_bytes)
            except RuntimeError as exc:
                manifest.append(_error_manifest_entry(disk_entry, backend_name or "amiga-unknown", file_entry, b"", str(exc)))
                continue
            if disk_entry["platform"] == "amiga-disk":
                if _is_probable_amiga_hunk(file_bytes):
                    backend_name = "amiga-hunk"
                    try:
                        inspect = _inspect_file(backend_name, suffix, file_bytes)
                    except RuntimeError as exc:
                        manifest.append(_error_manifest_entry(disk_entry, backend_name, file_entry, file_bytes, str(exc)))
                        continue
                elif _is_probable_amiga_iff(file_bytes):
                    backend_name = "amiga-iff"
                    inspect = _inspect_amiga_iff(file_bytes)
                elif _is_probable_amiga_text(file_bytes):
                    backend_name = "amiga-text"
                    inspect = _inspect_amiga_text(file_bytes)
                else:
                    continue
            else:
                try:
                    inspect = _inspect_file(backend_name, suffix, file_bytes)
                except RuntimeError as exc:
                    manifest.append(_error_manifest_entry(disk_entry, backend_name, file_entry, file_bytes, str(exc)))
                    continue
            manifest.append(_manifest_entry(disk_entry, backend_name, file_entry, file_bytes, inspect))
    return _dedupe_manifest(manifest)


def write_manifest(path: Path, entries: list[dict[str, Any]]) -> None:
    write_jsonl_manifest(path, entries)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build in-situ platform file corpus manifest from disk-image manifest extents.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    _ensure_tools_built()
    entries = build_manifest(args.input)
    write_manifest(args.output, entries)
    print(f"Wrote {args.output}")
    print(f"Entries: {len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
