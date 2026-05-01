from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

ContentProvider = Callable[[dict[str, Any]], dict[str, object] | None]


def browser_payload(
    *,
    disk: dict[str, object],
    entries: list[dict[str, Any]],
    path: str = "",
    target_index: dict[str, str] | None = None,
    content_for_entry: ContentProvider | None = None,
) -> dict[str, object]:
    target_index = target_index or {}
    current_path = normalise_path(path)
    selected_entry = entry_for_path(entries, current_path) if current_path else None
    if selected_entry is not None and not entry_is_directory(selected_entry):
        children: list[dict[str, object]] = []
        parent_path = parent_path_for(current_path)
    else:
        children = [
            entry_payload(entry, target_index)
            for entry in entries
            if entry_parent_path(entry) == current_path and not entry_is_volume(entry)
        ]
        children.sort(key=lambda item: (0 if item.get("is_directory") else 1, str(item.get("name", "")).lower()))
        parent_path = parent_path_for(current_path) if current_path else None
    volume = next((entry_payload(entry, target_index) for entry in entries if entry_is_volume(entry)), None)
    selected_payload = entry_payload(selected_entry, target_index) if selected_entry is not None else None
    if (
        selected_payload is not None
        and selected_entry is not None
        and not entry_is_directory(selected_entry)
        and content_for_entry is not None
    ):
        content = content_for_entry(selected_entry)
        if content is not None:
            selected_payload["content"] = content
    return {
        "disk": disk,
        "path": current_path,
        "parent_path": parent_path,
        "volume": volume,
        "selected_entry": selected_payload,
        "entries": children,
    }


def payload_from_project_manifest(
    manifest: dict[str, object],
    path: str = "",
    *,
    content_for_entry: ContentProvider | None = None,
) -> dict[str, object]:
    analysis = manifest.get("analysis")
    analysis = analysis if isinstance(analysis, dict) else {}
    disk_info = analysis.get("disk_info")
    disk_info = disk_info if isinstance(disk_info, dict) else {}
    filesystem = analysis.get("filesystem")
    filesystem = filesystem if isinstance(filesystem, dict) else {}
    disk_name = filesystem.get("volume_name") or disk_info.get("path") or manifest.get("disk_id")
    disk = {
        "id": manifest.get("disk_id"),
        "platform": "amiga-disk",
        "display_name": disk_name,
        "disk_name": disk_name,
        "size": disk_info.get("size"),
    }
    return browser_payload(
        disk=disk,
        entries=project_manifest_entries(manifest),
        path=path,
        content_for_entry=content_for_entry,
    )


def project_manifest_entries(manifest: dict[str, object]) -> list[dict[str, Any]]:
    analysis = manifest.get("analysis")
    analysis = analysis if isinstance(analysis, dict) else {}
    filesystem = analysis.get("filesystem")
    filesystem = filesystem if isinstance(filesystem, dict) else {}
    volume_name = filesystem.get("volume_name")
    entries: list[dict[str, Any]] = []
    if isinstance(volume_name, str) and volume_name:
        entries.append({"path": volume_name, "name": volume_name, "kind_name": "volume", "kind": 3})
    for directory in analysis.get("directories") or []:
        if isinstance(directory, dict):
            entry = dict(directory)
            entry["path"] = entry.get("full_path") or entry.get("path") or entry.get("name")
            entry["kind_name"] = "directory"
            entry["kind"] = 2
            entries.append(entry)
    for file_entry in analysis.get("files") or []:
        if isinstance(file_entry, dict):
            entry = dict(file_entry)
            entry["path"] = entry.get("full_path") or entry.get("path") or entry.get("name")
            entry["kind_name"] = "file"
            entry["kind"] = 1
            entries.append(entry)
    return entries


def normalise_path(path: str) -> str:
    return "/".join(part for part in str(path or "").replace("\\", "/").split("/") if part not in {"", "."})


def entry_for_path(entries: list[dict[str, Any]], path: str) -> dict[str, Any] | None:
    needle = path.lower()
    for entry in entries:
        entry_path = entry_path_value(entry)
        if entry_path.lower() == needle:
            return entry
    return None


def entry_parent_path(entry: dict[str, Any]) -> str:
    path = entry_path_value(entry)
    if not path or entry_is_volume(entry):
        return ""
    return parent_path_for(path) or ""


def parent_path_for(path: str) -> str | None:
    normalised = normalise_path(path)
    if not normalised:
        return None
    return normalised.rsplit("/", 1)[0] if "/" in normalised else ""


def entry_payload(entry: dict[str, Any] | None, target_index: dict[str, str]) -> dict[str, object] | None:
    if entry is None:
        return None
    path = entry_path_value(entry)
    name = entry.get("name")
    if not isinstance(name, str) or not name:
        name = path.rsplit("/", 1)[-1] if path else str(entry.get("path") or entry.get("full_path") or "")
    result: dict[str, object] = {
        "name": name,
        "path": path,
        "kind": entry.get("kind"),
        "kind_name": entry.get("kind_name"),
        "type": entry_type(entry),
        "size": entry_size(entry),
        "is_directory": entry_is_directory(entry),
        "is_volume": entry_is_volume(entry),
    }
    target_id = target_index.get(path.lower())
    if target_id is not None:
        result["target_id"] = target_id
    for key in ("date", "protection", "comment"):
        value = entry.get(key)
        if isinstance(value, (str, int)) and value != "":
            result[key] = value
    return result


def entry_path_value(entry: dict[str, Any]) -> str:
    value = entry.get("path")
    if not isinstance(value, str) or not value:
        value = entry.get("full_path")
    return normalise_path(value if isinstance(value, str) else "")


def entry_is_directory(entry: dict[str, Any]) -> bool:
    kind_name = entry.get("kind_name")
    return kind_name == "directory" or entry.get("kind") == 2


def entry_is_volume(entry: dict[str, Any]) -> bool:
    kind_name = entry.get("kind_name")
    return kind_name == "volume" or entry.get("kind") == 3


def entry_size(entry: dict[str, Any]) -> int | None:
    for key in ("byte_size", "file_size", "size"):
        value = entry.get(key)
        if isinstance(value, int):
            return value
    content = entry.get("content")
    if isinstance(content, dict) and isinstance(content.get("size"), int):
        return content["size"]
    return None


def entry_type(entry: dict[str, Any]) -> str:
    if entry_is_directory(entry):
        return "directory"
    if entry_is_volume(entry):
        return "volume"
    content = entry.get("content")
    if isinstance(content, dict):
        kind = content.get("kind")
        if kind == "amiga_hunk_executable":
            target_type = content.get("target_type")
            return f"Amiga HUNK {target_type}" if isinstance(target_type, str) and target_type else "Amiga HUNK"
        if kind == "atari_st_executable":
            return "Atari ST executable"
        if isinstance(kind, str) and kind and kind != "unknown":
            return kind.replace("_", " ")
    if entry.get("is_executable_candidate"):
        return "executable candidate"
    suffix = Path(entry_path_value(entry)).suffix.lower().lstrip(".")
    if suffix:
        return suffix.upper()
    kind_name = entry.get("kind_name")
    return str(kind_name) if isinstance(kind_name, str) and kind_name else "file"


def content_payload_from_bytes(data: bytes, *, limit: int = 4096) -> dict[str, object]:
    sample = data[:limit]
    text_available = bytes_look_textual(sample)
    return {
        "size": len(data),
        "truncated": len(data) > limit,
        "text_available": text_available,
        "text": decode_text_preview(sample) if text_available else "",
        "bytes": bytes_preview(sample),
        "hexdump": hexdump_preview(sample),
    }


def content_error_payload(error: str, size: int | None = None) -> dict[str, object]:
    return {
        "error": error,
        "size": size,
        "truncated": False,
        "text_available": False,
        "text": "",
        "bytes": "",
        "hexdump": [],
    }


def bytes_look_textual(data: bytes) -> bool:
    if not data:
        return True
    bad = 0
    for byte in data:
        if byte in {9, 10, 12, 13} or 32 <= byte <= 126 or byte >= 160:
            continue
        bad += 1
    return bad / len(data) <= 0.05


def decode_text_preview(data: bytes) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def bytes_preview(data: bytes, *, bytes_per_line: int = 32) -> str:
    lines = []
    for offset in range(0, len(data), bytes_per_line):
        chunk = data[offset : offset + bytes_per_line]
        lines.append(" ".join(f"{byte:02X}" for byte in chunk))
    return "\n".join(lines)


def hexdump_preview(data: bytes, *, bytes_per_line: int = 16) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for offset in range(0, len(data), bytes_per_line):
        chunk = data[offset : offset + bytes_per_line]
        rows.append({
            "offset": offset,
            "hex": " ".join(f"{byte:02X}" for byte in chunk),
            "ascii": "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in chunk),
        })
    return rows
