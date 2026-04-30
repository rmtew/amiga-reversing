from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scripts import target_usage_manifest as usage
from src.scripts.platform_manifest_io import (
    load_disk_image_bytes,
    read_jsonl_manifest,
)

MANIFEST_PATH = ROOT / "corpus" / "target_usage_manifest.jsonl"
XREFS_PATH = ROOT / "corpus" / "target_usage_xrefs.jsonl"
SNIPPET_ROWS_PATH = ROOT / "corpus" / "target_usage_snippet_rows.jsonl"
DISK_MANIFEST_PATH = ROOT / "corpus" / "platform_disk_manifest.jsonl"
FILE_MANIFEST_PATH = ROOT / "corpus" / "platform_file_manifest.jsonl"

_JSONL_CACHE: dict[Path, tuple[int, int, list[dict[str, Any]]]] = {}


def _read_jsonl_cached(path: Path) -> list[dict[str, Any]]:
    stat = path.stat()
    cached = _JSONL_CACHE.get(path)
    if cached is not None and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
        return list(cached[2])
    rows = read_jsonl_manifest(path)
    _JSONL_CACHE[path] = (stat.st_mtime_ns, stat.st_size, rows)
    return list(rows)


def read_manifest() -> list[dict[str, Any]]:
    return _read_jsonl_cached(MANIFEST_PATH)


def read_xrefs() -> list[dict[str, Any]]:
    return _read_jsonl_cached(XREFS_PATH)


def read_snippet_rows() -> list[dict[str, Any]]:
    return _read_jsonl_cached(SNIPPET_ROWS_PATH)


def feature_list() -> list[dict[str, object]]:
    summary = usage.feature_summary(read_manifest())
    row_counts, row_targets = _row_backed_feature_counts(read_xrefs())
    rows = [
        {
            **item,
            "source_example_count": row_counts.get(str(item.get("feature")), 0),
            "source_target_count": len(row_targets.get(str(item.get("feature")), set())),
        }
        for item in summary
    ]
    rows.sort(
        key=lambda item: (
            -int(item.get("source_target_count", 0)),
            -int(item.get("source_example_count", 0)),
            str(item.get("feature", "")),
        )
    )
    return rows


def query_targets(
    *,
    feature: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    q: str | None = None,
    source_only: bool = False,
) -> list[dict[str, object]]:
    rows = usage.query_usage_manifest(
        read_manifest(),
        feature or "",
        group=group or None,
        platform=platform or None,
        q=q or None,
    )
    row_counts = _row_backed_target_counts(read_xrefs(), feature=feature or None, group=group or None)
    enriched = [
        {
            **row,
            "source_example_count": row_counts.get(str(row.get("id")), 0),
        }
        for row in rows
        if not source_only or row_counts.get(str(row.get("id")), 0) > 0
    ]
    enriched.sort(
        key=lambda row: (
            -int(row.get("source_example_count", 0)),
            str(row.get("platform", "")),
            str(row.get("origin", {}).get("display_name", "") if isinstance(row.get("origin"), dict) else ""),
            str(row.get("id", "")),
        )
    )
    return enriched


def target_payload(target_id: str) -> dict[str, object]:
    row = target_row(target_id)
    return {
        "target": row,
        "xrefs": query_xrefs(target_id=target_id)[:500],
    }


def target_row(target_id: str) -> dict[str, Any]:
    for row in read_manifest():
        if row.get("id") == target_id:
            return row
    raise FileNotFoundError(f"Unknown corpus target: {target_id}")


def query_xrefs(
    *,
    target_id: str | None = None,
    feature: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    q: str | None = None,
    source_only: bool = False,
) -> list[dict[str, object]]:
    rows = usage.query_usage_xrefs(
        read_xrefs(),
        target_id=target_id or None,
        feature=feature or None,
        group=group or None,
        platform=platform or None,
        q=q or None,
    )
    if source_only:
        rows = [row for row in rows if isinstance(row.get("row_index"), int)]
    rows.sort(key=_xref_display_key)
    return rows


def _xref_display_key(row: dict[str, object]) -> tuple[object, ...]:
    kind_priority = {
        "data_class": 0,
        "hardware_ref": 1,
        "os_call": 2,
        "os_library": 3,
        "platform_effect": 4,
        "value_domain": 5,
        "struct": 6,
        "type": 7,
        "app_slot_ref": 8,
        "runtime_view": 9,
    }
    return (
        0 if isinstance(row.get("row_index"), int) else 1,
        kind_priority.get(str(row.get("kind")), 20),
        str(row.get("feature", "")),
        int(row.get("section")) if isinstance(row.get("section"), int) else 1_000_000_000,
        int(row.get("offset")) if isinstance(row.get("offset"), int) else 1_000_000_000,
        int(row.get("row_index")) if isinstance(row.get("row_index"), int) else 1_000_000_000,
        str(row.get("id", "")),
    )


def snippet_payload(xref_id: str, *, before: int = 20, after: int = 20) -> dict[str, object]:
    xref = _xref_row(xref_id)
    target_id = str(xref.get("target_id"))
    target = target_row(target_id)
    row_index = xref.get("row_index")
    if not isinstance(row_index, int):
        raise ValueError(f"Corpus xref {xref_id} has no listing row")
    snippet_rows = [
        row
        for row in read_snippet_rows()
        if row.get("target_id") == target_id and isinstance(row.get("row_index"), int)
    ]
    start = max(0, row_index - max(0, before))
    end = row_index + max(0, after) + 1
    rows_by_index = {
        int(row["row_index"]): row.get("row")
        for row in snippet_rows
        if start <= int(row["row_index"]) < end and isinstance(row.get("row"), dict)
    }
    if row_index not in rows_by_index:
        raise ValueError(f"Corpus snippet cache has no row {row_index} for {target_id}")
    rows = []
    for index in sorted(rows_by_index):
        payload = dict(rows_by_index[index])
        payload["row_index"] = index
        rows.append(payload)
    return {
        "xref": xref,
        "target": target,
        "start": start,
        "end": max(rows_by_index) + 1 if rows_by_index else start,
        "highlighted_row_index": row_index,
        "rows": rows,
    }


def corpus_import_media_body(target_id: str) -> dict[str, object]:
    target = target_row(target_id)
    platform = str(target.get("platform"))
    if platform == "amiga-disk":
        filename, media = _disk_target_media(target)
    elif platform == "amiga-hunk":
        filename, media = _file_target_media(target)
    else:
        raise ValueError(f"Corpus import is not supported for platform {platform}")
    return {
        "filename": filename,
        "media_base64": base64.b64encode(media).decode("ascii"),
    }


def _xref_row(xref_id: str) -> dict[str, Any]:
    for row in read_xrefs():
        if row.get("id") == xref_id:
            return row
    raise FileNotFoundError(f"Unknown corpus xref: {xref_id}")


def _row_backed_feature_counts(
    xrefs: list[dict[str, Any]],
) -> tuple[dict[str, int], dict[str, set[str]]]:
    counts: dict[str, int] = {}
    targets: dict[str, set[str]] = {}
    for row in xrefs:
        if not isinstance(row.get("row_index"), int):
            continue
        feature = row.get("feature")
        target_id = row.get("target_id")
        if not isinstance(feature, str) or not isinstance(target_id, str):
            continue
        counts[feature] = counts.get(feature, 0) + 1
        targets.setdefault(feature, set()).add(target_id)
    return counts, targets


def _row_backed_target_counts(
    xrefs: list[dict[str, Any]], *, feature: str | None, group: str | None
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in xrefs:
        if not isinstance(row.get("row_index"), int):
            continue
        row_feature = row.get("feature")
        if feature is not None and row_feature != feature:
            continue
        if group is not None and not usage.feature_matches_group(str(row_feature or ""), group):
            continue
        target_id = row.get("target_id")
        if not isinstance(target_id, str):
            continue
        counts[target_id] = counts.get(target_id, 0) + 1
    return counts


def _disk_target_media(target: dict[str, Any]) -> tuple[str, bytes]:
    source_id = str(target.get("source_id"))
    for row in read_jsonl_manifest(DISK_MANIFEST_PATH):
        if row.get("id") == source_id:
            origin = row.get("origin")
            if not isinstance(origin, dict):
                raise RuntimeError("Corpus disk row has no origin")
            return _corpus_filename(target, ".adf"), load_disk_image_bytes(origin)
    raise FileNotFoundError(f"Missing disk corpus row {source_id}")


def _file_target_media(target: dict[str, Any]) -> tuple[str, bytes]:
    source_id = str(target.get("source_id"))
    disk_entries = read_jsonl_manifest(DISK_MANIFEST_PATH)
    resolver = usage.DiskFileResolver(disk_entries)
    for row in read_jsonl_manifest(FILE_MANIFEST_PATH):
        if row.get("id") == source_id:
            return _corpus_filename(target, ""), resolver.file_bytes(row)
    raise FileNotFoundError(f"Missing file corpus row {source_id}")


def _corpus_filename(target: dict[str, Any], default_suffix: str) -> str:
    origin = target.get("origin")
    if isinstance(origin, dict):
        in_image_path = origin.get("in_image_path")
        if isinstance(in_image_path, str) and in_image_path:
            return Path(in_image_path).name
        member_name = origin.get("member_name")
        if isinstance(member_name, str) and member_name:
            return Path(member_name).name
        display_name = origin.get("display_name")
        if isinstance(display_name, str) and display_name:
            candidate = Path(display_name).name
            if default_suffix and not candidate.lower().endswith(default_suffix.lower()):
                candidate += default_suffix
            return candidate
    source_id = str(target.get("source_id") or "corpus_target").replace("/", "_")
    return source_id + default_suffix
