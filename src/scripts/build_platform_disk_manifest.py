from __future__ import annotations

import argparse
import ctypes
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESOURCES = ROOT / "resources"
DEFAULT_OUTPUT = ROOT / "corpus" / "platform_disk_manifest.jsonl"
DISK_DLL = ROOT / "src" / "build" / "platform_disk_lib.dll"


def _ensure_cli_built() -> None:
    result = subprocess.run(
        ["cmd", "/c", "src\\build.bat"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=1)
def _platform_disk_library() -> Any:
    fd, copied_path = tempfile.mkstemp(prefix="platform_disk_lib_", suffix=".dll")
    os.close(fd)
    for _ in range(10):
        try:
            shutil.copy2(DISK_DLL, copied_path)
            break
        except PermissionError:
            time.sleep(0.1)
    else:
        shutil.copy2(DISK_DLL, copied_path)
    library = ctypes.CDLL(copied_path)
    library.platform_disk_inspect_buffer_json.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]
    library.platform_disk_inspect_buffer_json.restype = ctypes.c_int
    library.platform_disk_free_json.argtypes = [ctypes.c_void_p]
    library.platform_disk_free_json.restype = None
    return library


def _run_inspect(platform_name: str, image_name: str, image_bytes: bytes) -> dict[str, Any]:
    library = _platform_disk_library()
    json_ptr = ctypes.c_void_p()
    error_buf = ctypes.create_string_buffer(512)
    data_array = (ctypes.c_ubyte * len(image_bytes)).from_buffer_copy(image_bytes if image_bytes else b"\0")
    result = library.platform_disk_inspect_buffer_json(
        platform_name.encode("utf-8"),
        data_array,
        len(image_bytes),
        ctypes.byref(json_ptr),
        error_buf,
        len(error_buf),
    )
    if result != 0:
        raise RuntimeError(f"{image_name}: {error_buf.value.decode('utf-8')}")
    try:
        payload = json.loads(ctypes.string_at(json_ptr).decode("utf-8"))
        assert isinstance(payload, dict)
        return payload
    finally:
        library.platform_disk_free_json(json_ptr)


def _iter_atari_sources() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    directory = RESOURCES / "platform_atari_st"
    for path in sorted(directory.glob("*.st")):
        data = path.read_bytes()
        results.append(
            {
                "platform": "atari-st-disk",
                "source_relpath": str(path.relative_to(ROOT)).replace("\\", "/"),
                "display_name": path.name,
                "container_relpath": None,
                "member_name": None,
                "image_name": path.name,
                "image_bytes": data,
            }
        )
    for zip_path in sorted(directory.glob("*.zip")):
        with zipfile.ZipFile(zip_path) as archive:
            for member in sorted(archive.infolist(), key=lambda item: item.filename.lower()):
                lower = member.filename.lower()
                if not lower.endswith(".st"):
                    continue
                data = _decode_zip_member(zip_path, member)
                image_name = Path(member.filename).name
                results.append(
                    {
                        "platform": "atari-st-disk",
                        "source_relpath": str(zip_path.relative_to(ROOT)).replace("\\", "/"),
                        "display_name": zip_path.name,
                        "container_relpath": str(zip_path.relative_to(ROOT)).replace("\\", "/"),
                        "member_name": member.filename.replace("\\", "/"),
                        "image_name": image_name,
                        "image_bytes": data,
                    }
                )
    return results


def _decode_zip_member(zip_path: Path, member: zipfile.ZipInfo) -> bytes:
    with zipfile.ZipFile(zip_path) as archive:
        raw = archive.read(member)
    if member.filename.lower().endswith(".adz"):
        return gzip.decompress(raw)
    return raw


def _iter_amiga_sources() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    directory = RESOURCES / "platform_amiga"
    for zip_path in sorted(directory.glob("*.zip")):
        with zipfile.ZipFile(zip_path) as archive:
            for member in sorted(archive.infolist(), key=lambda item: item.filename.lower()):
                lower = member.filename.lower()
                if lower.endswith(".adf") or lower.endswith(".adz"):
                    data = _decode_zip_member(zip_path, member)
                    image_name = Path(member.filename).name
                    results.append(
                        {
                            "platform": "amiga-disk",
                            "source_relpath": str(zip_path.relative_to(ROOT)).replace("\\", "/"),
                            "display_name": zip_path.name,
                            "container_relpath": str(zip_path.relative_to(ROOT)).replace("\\", "/"),
                            "member_name": member.filename.replace("\\", "/"),
                            "image_name": image_name[:-4] if image_name.lower().endswith(".adz") else image_name,
                            "image_bytes": data,
                        }
                    )
        # fall through for zips without supported disk members: just omit for now
    return results


def _manifest_entry(source: dict[str, Any]) -> dict[str, Any]:
    image_bytes = source["image_bytes"]
    inspect: dict[str, Any] | None = None
    status = "ok"
    error: str | None = None
    executable_paths: list[str] = []
    try:
        inspect = _run_inspect(source["platform"], source["image_name"], image_bytes)
        entries = inspect.get("entries", [])
        executable_paths = [
            entry["path"]
            for entry in entries
            if isinstance(entry, dict)
            and (
                entry.get("is_executable_candidate") == 1
                or (
                    source["platform"] == "amiga-disk"
                    and entry.get("kind") == 1
                    and isinstance(entry.get("path"), str)
                )
            )
        ]
    except RuntimeError as exc:
        status = "error"
        error = str(exc)
    return {
        "id": f'{source["platform"]}/{_sha256(image_bytes)[:12]}',
        "platform": source["platform"],
        "sha256": _sha256(image_bytes),
        "size": len(image_bytes),
        "origin": {
            "display_name": source["display_name"],
            "source_relpath": source["source_relpath"],
            "container_relpath": source["container_relpath"],
            "member_name": source["member_name"],
        },
        "expect": {
            "summary_version": 1,
            "status": status,
            "entry_count": inspect.get("entry_count") if inspect is not None else None,
            "executable_paths": executable_paths,
            "error": error,
            "inspect": inspect,
        },
    }


def build_manifest() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen_by_sha: dict[str, dict[str, Any]] = {}
    for source in _iter_atari_sources():
        entry = _manifest_entry(source)
        existing = seen_by_sha.get(entry["sha256"])
        if existing is None:
            entry["origin"]["alternate_origins"] = []
            seen_by_sha[entry["sha256"]] = entry
            entries.append(entry)
        else:
            existing["origin"]["alternate_origins"].append(
                {
                    "display_name": source["display_name"],
                    "source_relpath": source["source_relpath"],
                    "container_relpath": source["container_relpath"],
                    "member_name": source["member_name"],
                }
            )
    for source in _iter_amiga_sources():
        entry = _manifest_entry(source)
        existing = seen_by_sha.get(entry["sha256"])
        if existing is None:
            entry["origin"]["alternate_origins"] = []
            seen_by_sha[entry["sha256"]] = entry
            entries.append(entry)
        else:
            existing["origin"]["alternate_origins"].append(
                {
                    "display_name": source["display_name"],
                    "source_relpath": source["source_relpath"],
                    "container_relpath": source["container_relpath"],
                    "member_name": source["member_name"],
                }
            )
    return entries


def write_manifest(path: Path, entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build checked-in platform disk corpus manifest from local real images.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    _ensure_cli_built()
    entries = build_manifest()
    write_manifest(args.output, entries)
    print(f"Wrote {args.output}")
    print(f"Entries: {len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
