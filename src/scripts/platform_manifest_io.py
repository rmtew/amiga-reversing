from __future__ import annotations

import gzip
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl_manifest(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if isinstance(payload, dict):
                entries.append(payload)
    return entries


def write_jsonl_manifest(path: Path, entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries), encoding="utf-8")


def decode_archive_member(container_path: Path, member_name: str) -> bytes:
    with zipfile.ZipFile(container_path) as archive:
        raw = archive.read(member_name)
    if member_name.lower().endswith(".adz"):
        return gzip.decompress(raw)
    return raw


def load_disk_image_bytes(origin: dict[str, Any], *, root: Path = ROOT) -> bytes:
    source_relpath = origin["source_relpath"]
    if not isinstance(source_relpath, str):
        raise RuntimeError("Disk origin source_relpath must be a string")
    path = root / source_relpath
    container_relpath = origin.get("container_relpath")
    member_name = origin.get("member_name")
    if isinstance(container_relpath, str) and container_relpath and isinstance(member_name, str) and member_name:
        return decode_archive_member(root / container_relpath, member_name)
    return path.read_bytes()


def reconstruct_file_bytes(platform: str, file_entry: dict[str, Any], image_bytes: bytes) -> bytes:
    parts = []
    if platform == "atari-st-disk":
        file_size = int(file_entry["file_size"])
    else:
        file_size = int(file_entry["byte_size"])
    if file_size < 0:
        raise RuntimeError("Negative file size in disk manifest")
    if file_size == 0:
        return b""
    if not file_entry.get("extents"):
        raise RuntimeError("Missing file extents for non-empty in-image file")
    for extent in file_entry.get("extents", []):
        image_offset = int(extent["image_offset"])
        byte_size = int(extent["byte_size"])
        if image_offset < 0 or byte_size < 0 or image_offset + byte_size > len(image_bytes):
            raise RuntimeError("In-image file extent lies outside disk image")
        parts.append(image_bytes[image_offset : image_offset + byte_size])
    data = b"".join(parts)
    if len(data) < file_size:
        raise RuntimeError("In-image file extents do not cover declared file size")
    return data[:file_size]
