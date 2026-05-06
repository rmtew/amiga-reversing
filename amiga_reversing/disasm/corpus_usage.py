from __future__ import annotations

import base64
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from amiga_reversing.disasm import disk_browser
from src.scripts import target_usage_manifest as usage
from src.scripts.platform_manifest_io import (
    load_disk_image_bytes,
    read_jsonl_manifest,
    reconstruct_file_bytes,
)

MANIFEST_PATH = ROOT / "corpus" / "target_usage_manifest.jsonl"
XREFS_PATH = ROOT / "corpus" / "target_usage_xrefs.jsonl"
SNIPPET_ROWS_PATH = ROOT / "corpus" / "target_usage_snippet_rows"
VARIANTS_PATH = ROOT / "corpus" / "target_variant_index.jsonl"
DISK_MANIFEST_PATH = ROOT / "corpus" / "platform_disk_manifest.jsonl"
FILE_MANIFEST_PATH = ROOT / "corpus" / "platform_file_manifest.jsonl"

_JSONL_CACHE: dict[Path, tuple[int, int, list[dict[str, Any]]]] = {}
_SNIPPET_TARGET_CACHE: dict[str, tuple[tuple[int, int] | tuple[int, int, int, int], list[dict[str, Any]]]] = {}
LOW_VALUE_FEATURE_PREFIXES = (
    "analysis:",
    "analysis_generation:",
    "platform:",
    "status:",
    "file_platform:",
    "inspect_platform:",
)
_VALUE_TOKEN_RE = re.compile(
    r"(?P<imm>#)?(?P<token>loc_[A-Za-z0-9]+_[0-9A-Fa-f]{8}|\$[0-9A-Fa-f]+|\b\d+\b)(?P<suffix>\.[bwlBWL])?"
)


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
    return usage.read_usage_snippet_rows(SNIPPET_ROWS_PATH)


def read_snippet_rows_for_target(target_id: str) -> list[dict[str, Any]]:
    stamp = _snippet_rows_storage_stamp()
    cached = _SNIPPET_TARGET_CACHE.get(target_id)
    if cached is not None and cached[0] == stamp:
        return list(cached[1])
    rows = usage.read_usage_snippet_rows_for_target(target_id, SNIPPET_ROWS_PATH)
    _SNIPPET_TARGET_CACHE[target_id] = (stamp, rows)
    return list(rows)


def _snippet_rows_storage_stamp() -> tuple[int, int] | tuple[int, int, int, int]:
    index_path = usage.snippet_rows_index_path(SNIPPET_ROWS_PATH)
    blob_path = usage.snippet_rows_blob_path(SNIPPET_ROWS_PATH)
    index_stat = index_path.stat()
    blob_stat = blob_path.stat()
    return (index_stat.st_mtime_ns, index_stat.st_size, blob_stat.st_mtime_ns, blob_stat.st_size)


def read_variants() -> list[dict[str, Any]]:
    if not VARIANTS_PATH.exists():
        return []
    return _read_jsonl_cached(VARIANTS_PATH)


def feature_list() -> list[dict[str, object]]:
    summary = usage.feature_summary(read_manifest())
    row_counts, row_targets = _row_backed_feature_counts(read_xrefs())
    rows = [
        {
            **item,
            "source_example_count": row_counts.get(str(item.get("feature")), 0),
            "source_target_count": len(row_targets.get(str(item.get("feature")), set())),
            "user_visible": _feature_user_visible(str(item.get("feature")), row_counts.get(str(item.get("feature")), 0)),
            "label": _feature_label(str(item.get("feature"))),
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
    limit: int | None = None,
    offset: int = 0,
    projects: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    rows = usage.query_usage_manifest(
        read_manifest(),
        feature or "",
        group=group or None,
        platform=platform or None,
        q=q or None,
    )
    manifest_by_id = {
        str(row.get("id")): row
        for row in read_manifest()
        if isinstance(row.get("id"), str)
    }
    variants_by_target = _variants_by_target_id()
    row_counts = _row_backed_target_counts(read_xrefs(), feature=feature or None, group=group or None)
    enriched = [
        {
            **row,
            "sha256": _full_manifest_row(row, manifest_by_id).get("sha256"),
            "size": _full_manifest_row(row, manifest_by_id).get("size"),
            "source_example_count": row_counts.get(str(row.get("id")), 0),
            "selected_feature_label": _feature_label(feature or group or ""),
            "source_context": _target_source_context(_full_manifest_row(row, manifest_by_id)),
            "project_coverage": _project_coverage_for_target(_full_manifest_row(row, manifest_by_id), projects or []),
            "variant_group_id": variants_by_target.get(str(row.get("id")), {}).get("id"),
            "variant_count": variants_by_target.get(str(row.get("id")), {}).get("target_count", 1),
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
    return _page(enriched, limit=limit, offset=offset)


def _full_manifest_row(row: dict[str, object], manifest_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    target_id = row.get("id")
    if isinstance(target_id, str):
        return manifest_by_id.get(target_id, row)
    return row


def target_row(target_id: str) -> dict[str, Any]:
    for row in read_manifest():
        if row.get("id") == target_id:
            return row
    raise FileNotFoundError(f"Unknown corpus target: {target_id}")


def variants_payload(target_id: str) -> dict[str, object]:
    target = target_row(target_id)
    group = _variants_by_target_id().get(target_id)
    if group is None:
        return {
            "target": target,
            "group": None,
            "variants": [],
        }
    variants = [
        {
            **variant,
            "selected": variant.get("target_id") == target_id,
        }
        for variant in group.get("targets", [])
        if isinstance(variant, dict)
    ]
    return {
        "target": target,
        "group": {
            key: group.get(key)
            for key in (
                "id",
                "platform",
                "title_family",
                "display_path",
                "target_count",
                "unique_hash_count",
            )
        },
        "variants": variants,
    }


def disk_browser_payload(
    target_id: str,
    path: str = "",
    *,
    projects: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    target = target_row(target_id)
    disk_target = target if _is_disk_platform(str(target.get("platform"))) else _parent_disk_target_row(target)
    if disk_target is None:
        raise ValueError(f"Corpus target {target_id} has no indexed disk container")
    disk_row = _disk_manifest_row(disk_target)
    entries = _disk_entries(disk_row)
    target_index = _disk_entry_target_index(disk_target)
    disk = _diff_target_summary(disk_target)
    disk["corpus_target_id"] = disk_target.get("id")
    disk["project_coverage"] = _project_coverage_for_target(disk_target, projects or [])
    return disk_browser.browser_payload(
        disk=disk,
        entries=entries,
        path=path,
        target_index=target_index,
        content_for_entry=lambda entry: _disk_entry_content_payload(disk_row, entry),
    )


def diff_payload(left_target_id: str, right_target_id: str) -> dict[str, object]:
    left = target_row(left_target_id)
    right = target_row(right_target_id)
    variant_group = _variant_group_for_pair(left_target_id, right_target_id)
    if variant_group is None:
        raise ValueError("Targets are not variants of the same corpus item")
    left_bytes = _target_media_bytes(left)
    right_bytes = _target_media_bytes(right)
    left_space = _target_diff_space(left_target_id, left_bytes)
    right_space = _target_diff_space(right_target_id, right_bytes)
    return {
        "left": _diff_target_summary(left),
        "right": _diff_target_summary(right),
        "variant_group": {
            key: variant_group.get(key)
            for key in ("id", "platform", "title_family", "display_path")
        },
        "byte_diff": _byte_diff_summary(
            left_space["bytes"],
            right_space["bytes"],
            left_rows=left_space["rows"],
            right_rows=right_space["rows"],
            left_space_kind=str(left_space["kind"]),
            right_space_kind=str(right_space["kind"]),
        ),
    }


def query_xrefs(
    *,
    target_id: str | None = None,
    feature: str | None = None,
    group: str | None = None,
    source_only: bool = False,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, object]]:
    rows = usage.query_usage_xrefs(
        read_xrefs(),
        target_id=target_id or None,
        feature=feature or None,
        group=group or None,
    )
    if source_only:
        rows = [row for row in rows if isinstance(row.get("row_index"), int)]
    rows.sort(key=_xref_display_key)
    return _page(rows, limit=limit, offset=offset)


def _page(rows: list[dict[str, object]], *, limit: int | None, offset: int) -> list[dict[str, object]]:
    safe_offset = max(0, offset)
    if limit is None:
        return rows[safe_offset:]
    safe_limit = max(0, min(limit, 1000))
    return rows[safe_offset:safe_offset + safe_limit]


def _feature_user_visible(feature: str, source_example_count: int) -> bool:
    if not feature:
        return False
    if source_example_count > 0:
        return not feature.startswith(LOW_VALUE_FEATURE_PREFIXES)
    return not feature.startswith(LOW_VALUE_FEATURE_PREFIXES) and feature.startswith((
        "format:",
        "disk:",
        "amiga:",
    ))


def _feature_label(feature: str) -> str:
    if feature == "os_call:any":
        return "All OS calls"
    if feature.startswith("os_call_library:"):
        return f"Library calls: {feature.split(':', 1)[1]}"
    if feature.startswith("os:"):
        return feature.split(":", 1)[1].replace("/", " / ")
    if feature.startswith("device:"):
        return f"Device: {feature.split(':', 1)[1]}"
    if feature.startswith("device_call:"):
        return f"Device call: {feature.split(':', 1)[1].replace('/', ' / ')}"
    if feature.startswith("device_call_function:"):
        return f"Device call: {feature.split(':', 1)[1]}"
    if feature.startswith("os_library:"):
        return f"Library: {feature.split(':', 1)[1]}"
    if feature.startswith("hardware_register:"):
        return f"Register: {feature.split(':', 1)[1]}"
    if feature.startswith("hardware:"):
        return feature.split(":", 1)[1].replace("/", " / ")
    if feature.startswith("copper_register:"):
        return f"Copper register: {feature.split(':', 1)[1]}"
    if feature.startswith("display:bitplanes:"):
        return f"Display: {feature.rsplit(':', 1)[1]} bitplanes"
    if feature.startswith("display:"):
        return f"Display: {feature.split(':', 1)[1].replace('_', ' ')}"
    if feature.startswith("data:"):
        return feature.split(":", 1)[1].replace("_", " ")
    if feature.startswith("app_slot:"):
        return f"App slot: {feature.split(':', 1)[1]}"
    if feature.startswith("runtime:"):
        return feature.split(":", 1)[1].replace("_", " ")
    if feature.startswith("label:"):
        return f"Labels: {feature.split(':', 1)[1]}"
    if feature.startswith("xref:"):
        return feature.split(":", 1)[1].replace("_", " ")
    if feature.startswith("diagnostic:"):
        return f"Diagnostic: {feature.split(':', 1)[1].replace('_', ' ')}"
    return feature


def _xref_display_key(row: dict[str, object]) -> tuple[object, ...]:
    kind_priority = {
        "data_class": 0,
        "display_ref": 1,
        "hardware_ref": 2,
        "copper_ref": 3,
        "os_call": 4,
        "device_call": 5,
        "os_library": 6,
        "platform_effect": 7,
        "value_domain": 8,
        "struct": 9,
        "type": 10,
        "app_slot_ref": 11,
        "runtime_view": 12,
    }
    resolution_priority = {
        "direct": 0,
        "direct_os_call": 1,
        "indexed_vector": 2,
        "callback_field": 3,
        "local_wrapper": 4,
        "stack_cleanup": 5,
    }
    return (
        0 if isinstance(row.get("row_index"), int) else 1,
        kind_priority.get(str(row.get("kind")), 20),
        resolution_priority.get(str(row.get("resolution")), 9),
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


def corpus_import_media_body(target_id: str, *, mode: str = "target") -> dict[str, object]:
    requested_target = target_row(target_id)
    target = _import_target_for_mode(requested_target, mode=mode)
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
        "project_origin": _corpus_project_origin(
            requested_target=requested_target,
            imported_target=target,
            mode=mode,
        ),
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
    for row in _read_jsonl_cached(DISK_MANIFEST_PATH):
        if row.get("id") == source_id:
            origin = row.get("origin")
            if not isinstance(origin, dict):
                raise RuntimeError("Corpus disk row has no origin")
            return _corpus_filename(target, ".adf"), load_disk_image_bytes(origin)
    raise FileNotFoundError(f"Missing disk corpus row {source_id}")


def _file_target_media(target: dict[str, Any]) -> tuple[str, bytes]:
    source_id = str(target.get("source_id"))
    disk_entries = _read_jsonl_cached(DISK_MANIFEST_PATH)
    resolver = usage.DiskFileResolver(disk_entries)
    for row in _read_jsonl_cached(FILE_MANIFEST_PATH):
        if row.get("id") == source_id:
            return _corpus_filename(target, ""), resolver.file_bytes(row)
    raise FileNotFoundError(f"Missing file corpus row {source_id}")


def _target_media_bytes(target: dict[str, Any]) -> bytes:
    platform = str(target.get("platform"))
    if platform.endswith("-disk"):
        _filename, media = _disk_target_media(target)
        return media
    _filename, media = _file_target_media(target)
    return media


def _target_diff_space(target_id: str, raw_bytes: bytes) -> dict[str, object]:
    rows = _source_rows_for_target(target_id)
    listing_space = _listing_diff_space(rows)
    if listing_space is not None:
        return listing_space
    return {"kind": "file", "bytes": raw_bytes, "rows": rows}


def _listing_diff_space(rows: list[dict[str, object]]) -> dict[str, object] | None:
    byte_rows: list[tuple[int, int, bytes, dict[str, object]]] = []
    for row in rows:
        row_bytes = _listing_row_bytes(row)
        if row_bytes is None:
            continue
        start, data = row_bytes
        if not data:
            continue
        section = row.get("section_index")
        section_index = section if isinstance(section, int) else 0
        byte_rows.append((section_index, start, data, row))
    if not byte_rows:
        return None

    section_sizes: dict[int, int] = {}
    for section_index, start, data, _row in byte_rows:
        section_sizes[section_index] = max(section_sizes.get(section_index, 0), start + len(data))

    section_bases: dict[int, int] = {}
    cursor = 0
    for section_index in sorted(section_sizes):
        if cursor:
            cursor = (cursor + 15) & ~15
        section_bases[section_index] = cursor
        cursor += section_sizes[section_index]

    image = bytearray(cursor)
    mapped_rows: list[dict[str, object]] = []
    for section_index, start, data, row in byte_rows:
        diff_start = section_bases[section_index] + start
        diff_end = diff_start + len(data)
        image[diff_start:diff_end] = data
        mapped = dict(row)
        mapped["diff_start_offset"] = diff_start
        mapped["diff_end_offset"] = diff_end
        mapped_rows.append(mapped)
    mapped_rows.sort(key=lambda row: (int(row.get("row_index")) if isinstance(row.get("row_index"), int) else 1_000_000_000))
    return {"kind": "listing", "bytes": bytes(image), "rows": mapped_rows}


def _listing_row_bytes(row: dict[str, object]) -> tuple[int, bytes] | None:
    start = row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr")
    if not isinstance(start, int):
        return None
    data = _dcb_row_bytes(row)
    if data is None:
        hex_bytes = row.get("bytes")
        if not isinstance(hex_bytes, str) or not hex_bytes:
            return None
        try:
            data = bytes.fromhex(hex_bytes)
        except ValueError:
            return None
    end = row.get("end_offset")
    if isinstance(end, int) and end > start and len(data) > end - start:
        data = data[:end - start]
    return start, data


def _dcb_row_bytes(row: dict[str, object]) -> bytes | None:
    directive = str(row.get("opcode_or_directive") or "").lower()
    units = {"dcb.b": 1, "dcb.w": 2, "dcb.l": 4}
    unit = units.get(directive)
    if unit is None:
        return None
    operands = [part.strip() for part in str(row.get("operand_text") or "").split(",")]
    if not operands or not operands[0]:
        return None
    count = _parse_simple_asm_int(operands[0])
    value = _parse_simple_asm_int(operands[1]) if len(operands) > 1 and operands[1] else 0
    if count is None or value is None or count < 0:
        return None
    mask = (1 << (unit * 8)) - 1
    item = int(value & mask).to_bytes(unit, "big")
    data = item * count
    start = row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr")
    end = row.get("end_offset")
    if isinstance(start, int) and isinstance(end, int) and end > start:
        expected = end - start
        if len(data) > expected:
            return data[:expected]
    return data


def _parse_simple_asm_int(text: str) -> int | None:
    value = text.strip()
    if not value:
        return None
    if value.startswith("#"):
        value = value[1:].strip()
    sign = 1
    if value.startswith("-"):
        sign = -1
        value = value[1:].strip()
    if value.startswith("$"):
        digits = value[1:]
        base = 16
    elif value.startswith("%"):
        digits = value[1:]
        base = 2
    else:
        digits = value
        base = 10
    if not digits:
        return None
    try:
        return sign * int(digits, base)
    except ValueError:
        return None


def _diff_target_summary(target: dict[str, Any]) -> dict[str, object]:
    origin = target.get("origin") if isinstance(target.get("origin"), dict) else {}
    return {
        "id": target.get("id"),
        "platform": target.get("platform"),
        "sha256": target.get("sha256"),
        "size": target.get("size"),
        "display_name": (
            origin.get("in_image_path")
            or origin.get("member_name")
            or origin.get("display_name")
            or target.get("id")
        ),
        "disk_name": _target_source_context(target).get("disk_name"),
    }


def _byte_diff_summary(
    left: bytes,
    right: bytes,
    *,
    left_rows: list[dict[str, object]] | None = None,
    right_rows: list[dict[str, object]] | None = None,
    left_space_kind: str = "file",
    right_space_kind: str = "file",
    max_regions: int = 80,
    merge_equal_gap: int = 32,
    hex_limit: int = 96,
) -> dict[str, object]:
    raw_regions = _byte_diff_regions(left, right, merge_equal_gap=merge_equal_gap)
    left_context_rows = left_rows if left_rows is not None else []
    right_context_rows = right_rows if right_rows is not None else []
    regions: list[dict[str, object]] = []
    previous_left_end = 0
    previous_right_end = 0
    first_diff: int | None = None
    for region in raw_regions:
        left_start, left_end, right_start, right_end, kind = region
        if first_diff is None:
            first_diff = min(left_start, right_start)
        if len(regions) < max_regions:
            left_context = _source_rows_for_range(left_context_rows, left_start, left_end)
            right_context = _source_rows_for_range(right_context_rows, right_start, right_end)
            context_pairs = _paired_context_rows(left_context, right_context)
            regions.append(
                {
                    "kind": kind,
                    "left_start": left_start,
                    "left_end": left_end,
                    "left_length": left_end - left_start,
                    "right_start": right_start,
                    "right_end": right_end,
                    "right_length": right_end - right_start,
                    "skipped_left": max(0, left_start - previous_left_end),
                    "skipped_right": max(0, right_start - previous_right_end),
                    "left_hex": left[left_start:min(left_end, left_start + hex_limit)].hex(),
                    "right_hex": right[right_start:min(right_end, right_start + hex_limit)].hex(),
                    "left_hex_truncated": max(0, left_end - left_start - hex_limit),
                    "right_hex_truncated": max(0, right_end - right_start - hex_limit),
                    "left_context": left_context,
                    "right_context": right_context,
                    "context_pairs": context_pairs,
                    "diff_summary": _context_pair_summary(context_pairs),
                }
            )
        previous_left_end = left_end
        previous_right_end = right_end
    return {
        "left_size": len(left),
        "right_size": len(right),
        "left_space": left_space_kind,
        "right_space": right_space_kind,
        "first_diff": first_diff,
        "region_count": len(raw_regions),
        "truncated_region_count": max(0, len(raw_regions) - len(regions)),
        "trailing_skipped_left": max(0, len(left) - previous_left_end),
        "trailing_skipped_right": max(0, len(right) - previous_right_end),
        "regions": regions,
    }


def _byte_diff_regions(
    left: bytes,
    right: bytes,
    *,
    merge_equal_gap: int,
    block_size: int = 16,
) -> list[tuple[int, int, int, int, str]]:
    left_blocks = [left[index:index + block_size] for index in range(0, len(left), block_size)]
    right_blocks = [right[index:index + block_size] for index in range(0, len(right), block_size)]
    matcher = difflib.SequenceMatcher(None, left_blocks, right_blocks)
    regions: list[tuple[int, int, int, int, str]] = []
    pending: list[tuple[str, int, int, int, int]] = []
    for tag, left_block_start, left_block_end, right_block_start, right_block_end in matcher.get_opcodes():
        left_start = min(len(left), left_block_start * block_size)
        left_end = min(len(left), left_block_end * block_size)
        right_start = min(len(right), right_block_start * block_size)
        right_end = min(len(right), right_block_end * block_size)
        if tag == "equal" and not pending:
            continue
        if tag == "equal" and left_end - left_start > merge_equal_gap and right_end - right_start > merge_equal_gap:
            if pending:
                regions.extend(_refined_diff_regions(left, right, _merged_diff_region(pending), merge_equal_gap=merge_equal_gap))
                pending = []
            continue
        pending.append((tag, left_start, left_end, right_start, right_end))
    if pending:
        regions.extend(_refined_diff_regions(left, right, _merged_diff_region(pending), merge_equal_gap=merge_equal_gap))
    return regions


def _merged_diff_region(ops: list[tuple[str, int, int, int, int]]) -> tuple[int, int, int, int, str]:
    left_start = ops[0][1]
    right_start = ops[0][3]
    left_end = ops[-1][2]
    right_end = ops[-1][4]
    tags = {tag for tag, _left_start, _left_end, _right_start, _right_end in ops if tag != "equal"}
    kind = next(iter(tags)) if len(tags) == 1 else "mixed"
    return left_start, left_end, right_start, right_end, kind


def _trim_diff_region(
    left: bytes,
    right: bytes,
    region: tuple[int, int, int, int, str],
) -> tuple[int, int, int, int, str]:
    left_start, left_end, right_start, right_end, kind = region
    while left_start < left_end and right_start < right_end and left[left_start] == right[right_start]:
        left_start += 1
        right_start += 1
    while left_start < left_end and right_start < right_end and left[left_end - 1] == right[right_end - 1]:
        left_end -= 1
        right_end -= 1
    return left_start, left_end, right_start, right_end, kind


def _refined_diff_regions(
    left: bytes,
    right: bytes,
    region: tuple[int, int, int, int, str],
    *,
    merge_equal_gap: int,
    refine_limit: int = 8192,
) -> list[tuple[int, int, int, int, str]]:
    left_start, left_end, right_start, right_end, kind = _trim_diff_region(left, right, region)
    if left_start == left_end and right_start == right_end:
        return []
    if max(left_end - left_start, right_end - right_start) > refine_limit:
        return [(left_start, left_end, right_start, right_end, kind)]
    matcher = difflib.SequenceMatcher(None, left[left_start:left_end], right[right_start:right_end])
    refined: list[tuple[int, int, int, int, str]] = []
    pending: list[tuple[str, int, int, int, int]] = []
    for tag, rel_left_start, rel_left_end, rel_right_start, rel_right_end in matcher.get_opcodes():
        abs_left_start = left_start + rel_left_start
        abs_left_end = left_start + rel_left_end
        abs_right_start = right_start + rel_right_start
        abs_right_end = right_start + rel_right_end
        if tag == "equal" and not pending:
            continue
        if tag == "equal" and abs_left_end - abs_left_start > merge_equal_gap and abs_right_end - abs_right_start > merge_equal_gap:
            if pending:
                refined_region = _trim_diff_region(left, right, _merged_diff_region(pending))
                if refined_region[0] != refined_region[1] or refined_region[2] != refined_region[3]:
                    refined.append(refined_region)
                pending = []
            continue
        pending.append((tag, abs_left_start, abs_left_end, abs_right_start, abs_right_end))
    if pending:
        refined_region = _trim_diff_region(left, right, _merged_diff_region(pending))
        if refined_region[0] != refined_region[1] or refined_region[2] != refined_region[3]:
            refined.append(refined_region)
    return refined or [(left_start, left_end, right_start, right_end, kind)]


def _paired_context_rows(
    left_rows: list[dict[str, object]],
    right_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    left_keys = [_context_pair_key(row) for row in left_rows]
    right_keys = [_context_pair_key(row) for row in right_rows]
    matcher = difflib.SequenceMatcher(None, left_keys, right_keys, autojunk=False)
    pairs: list[dict[str, object]] = []
    for tag, left_start, left_end, right_start, right_end in matcher.get_opcodes():
        if tag == "equal":
            for left_index, right_index in zip(range(left_start, left_end), range(right_start, right_end)):
                pairs.append(_context_pair(left_rows[left_index], right_rows[right_index]))
            continue
        count = max(left_end - left_start, right_end - right_start)
        for index in range(count):
            left = left_rows[left_start + index] if left_start + index < left_end else None
            right = right_rows[right_start + index] if right_start + index < right_end else None
            pairs.append(_context_pair(left, right))
    _classify_context_pairs(pairs)
    return pairs


def _context_pair(left: dict[str, object] | None, right: dict[str, object] | None) -> dict[str, object]:
    left_text = _normalised_context_text(left)
    right_text = _normalised_context_text(right)
    left_start = _row_start_offset(left) if left is not None else None
    right_start = _row_start_offset(right) if right is not None else None
    return {
        "left": left,
        "right": right,
        "same_text": left_text == right_text and left_text != "",
        "same_offset": left_start is not None and right_start is not None and left_start == right_start,
    }


def _classify_context_pairs(pairs: list[dict[str, object]]) -> None:
    analyses = [_context_pair_analysis(pair) for pair in pairs]
    delta_counts: Counter[int] = Counter()
    for analysis in analyses:
        if analysis.get("diff_class") not in {"address_only", "target_change"}:
            continue
        for delta in analysis.get("address_deltas", []):
            if isinstance(delta, int):
                delta_counts[delta] += 1
    dominant_deltas = {delta for delta, count in delta_counts.items() if count >= 2}

    for pair, analysis in zip(pairs, analyses):
        diff_class = str(analysis.get("diff_class") or "semantic")
        pair_deltas = [delta for delta in analysis.get("address_deltas", []) if isinstance(delta, int)]
        dominant = next((delta for delta in pair_deltas if delta in dominant_deltas), None)
        if diff_class in {"address_only", "target_change"} and dominant is not None:
            diff_class = "shifted_address"
        pair["diff_class"] = diff_class
        pair["diff_label"] = _context_diff_label(diff_class, dominant)
        if dominant is not None:
            pair["dominant_delta"] = dominant


def _context_pair_summary(pairs: list[dict[str, object]]) -> dict[str, object]:
    counts: Counter[str] = Counter()
    deltas: Counter[int] = Counter()
    for pair in pairs:
        diff_class = pair.get("diff_class")
        if isinstance(diff_class, str) and diff_class != "unchanged":
            counts[diff_class] += 1
        delta = pair.get("dominant_delta")
        if isinstance(delta, int):
            deltas[delta] += 1
    return {
        "classes": dict(sorted(counts.items())),
        "dominant_deltas": [
            {"delta": delta, "count": count}
            for delta, count in deltas.most_common(4)
        ],
    }


def _context_pair_analysis(pair: dict[str, object]) -> dict[str, object]:
    left = pair.get("left")
    right = pair.get("right")
    if not isinstance(left, dict) or not isinstance(right, dict):
        return {"diff_class": "missing_row", "address_deltas": []}
    left_text = _normalised_context_text(left)
    right_text = _normalised_context_text(right)
    if left_text == right_text:
        return {"diff_class": "unchanged", "address_deltas": []}

    left_tokens = _extract_value_tokens(left_text)
    right_tokens = _extract_value_tokens(right_text)
    value_pairs = list(zip(left_tokens, right_tokens))
    changed_pairs = [
        (left_token, right_token)
        for left_token, right_token in value_pairs
        if left_token["value"] != right_token["value"]
        or left_token["text"].lower() != right_token["text"].lower()
        or left_token.get("suffix") != right_token.get("suffix")
    ]
    address_pairs = [
        (left_token, right_token)
        for left_token, right_token in changed_pairs
        if _value_token_is_address_like(left_token) and _value_token_is_address_like(right_token)
    ]
    address_deltas = [
        int(left_token["value"]) - int(right_token["value"])
        for left_token, right_token in address_pairs
        if isinstance(left_token.get("value"), int) and isinstance(right_token.get("value"), int)
    ]
    mode_change = any(
        left_token["value"] == right_token["value"]
        and left_token.get("suffix")
        and right_token.get("suffix")
        and left_token.get("suffix") != right_token.get("suffix")
        for left_token, right_token in value_pairs
    )
    immediate_change = any(
        (left_token.get("immediate") or right_token.get("immediate"))
        and not (_value_token_is_address_like(left_token) and _value_token_is_address_like(right_token))
        and left_token["value"] != right_token["value"]
        for left_token, right_token in changed_pairs
    )
    same_shape = _normalise_value_text(left_text) == _normalise_value_text(right_text)
    opcode_same = _row_opcode(left) == _row_opcode(right)
    if mode_change and same_shape:
        diff_class = "addressing_mode"
    elif immediate_change and same_shape:
        diff_class = "immediate_semantic"
    elif same_shape and address_pairs and len(address_pairs) == len(changed_pairs):
        diff_class = "target_change" if _row_has_label_value(left) or _row_has_label_value(right) else "address_only"
    elif opcode_same and address_pairs and not immediate_change:
        diff_class = "address_only"
    else:
        diff_class = "semantic"
    return {
        "diff_class": diff_class,
        "address_deltas": address_deltas,
    }


def _context_diff_label(diff_class: str, delta: int | None) -> str:
    labels = {
        "unchanged": "unchanged",
        "missing_row": "missing row",
        "shifted_address": "shifted address",
        "address_only": "address-only",
        "target_change": "target change",
        "immediate_semantic": "immediate value",
        "addressing_mode": "address mode",
        "semantic": "semantic",
    }
    label = labels.get(diff_class, diff_class.replace("_", " "))
    if delta is not None and diff_class == "shifted_address":
        sign = "+" if delta >= 0 else "-"
        label = f"{label} {sign}${abs(delta):X}"
    return label


def _context_pair_key(row: dict[str, object]) -> str:
    opcode = _row_opcode(row)
    if opcode:
        operand_text = str(row.get("operand_text") or _normalised_context_text(row))
        return f"{opcode}:{_normalise_value_text(operand_text)}"
    return _normalise_value_text(_normalised_context_text(row))


def _row_opcode(row: dict[str, object] | None) -> str:
    if row is None:
        return ""
    opcode = row.get("opcode_or_directive")
    if isinstance(opcode, str) and opcode:
        return opcode.strip().lower()
    text = _normalised_context_text(row)
    parts = text.split(None, 1)
    return parts[0].rstrip(":").lower() if parts else ""


def _normalise_value_text(text: str) -> str:
    lowered = text.strip().lower()
    lowered = _VALUE_TOKEN_RE.sub(_normalise_value_token_match, lowered)
    return re.sub(r"\s+", " ", lowered)


def _normalise_value_token_match(match: re.Match[str]) -> str:
    immediate = "#" if match.group("imm") else ""
    suffix = match.group("suffix")
    suffix_text = ".size" if suffix else ""
    return f"{immediate}<value>{suffix_text}"


def _extract_value_tokens(text: str) -> list[dict[str, object]]:
    tokens: list[dict[str, object]] = []
    for match in _VALUE_TOKEN_RE.finditer(text):
        token = match.group("token")
        value = _value_token_int(token)
        if value is None:
            continue
        tokens.append(
            {
                "text": token,
                "value": value,
                "kind": _value_token_kind(token),
                "immediate": bool(match.group("imm")),
                "suffix": match.group("suffix").lower() if match.group("suffix") else "",
            }
        )
    return tokens


def _value_token_int(token: str) -> int | None:
    lowered = token.lower()
    if lowered.startswith("loc_"):
        tail = lowered.rsplit("_", 1)[-1]
        try:
            return int(tail, 16)
        except ValueError:
            return None
    return _parse_simple_asm_int(token)


def _value_token_kind(token: str) -> str:
    lowered = token.lower()
    if lowered.startswith("loc_"):
        return "label"
    if lowered.startswith("$"):
        return "hex"
    return "decimal"


def _value_token_is_address_like(token: dict[str, object]) -> bool:
    kind = token.get("kind")
    if kind == "label":
        return True
    if kind == "hex":
        value = token.get("value")
        if not isinstance(value, int):
            return False
        return not token.get("immediate") or value >= 0x100
    return False


def _row_has_label_value(row: dict[str, object]) -> bool:
    return any(token.get("kind") == "label" for token in _extract_value_tokens(_normalised_context_text(row)))


def _normalised_context_text(row: dict[str, object] | None) -> str:
    if row is None:
        return ""
    return str(row.get("text") or "").strip()


def _source_rows_for_target(target_id: str | None) -> list[dict[str, object]]:
    if not target_id:
        return []
    rows: list[dict[str, object]] = []
    for item in read_snippet_rows_for_target(target_id):
        row = item.get("row")
        if not isinstance(row, dict):
            continue
        payload = dict(row)
        row_index = item.get("row_index")
        if isinstance(row_index, int):
            payload["row_index"] = row_index
        rows.append(payload)
    rows.sort(key=lambda row: (int(row.get("row_index")) if isinstance(row.get("row_index"), int) else 1_000_000_000))
    return rows


def _source_rows_for_range(
    rows: list[dict[str, object]],
    start: int,
    end: int,
    *,
    limit: int = 6,
    before: int = 3,
) -> list[dict[str, object]]:
    overlapping: list[dict[str, object]] = []
    preceding: list[dict[str, object]] = []
    for row in rows:
        row_start = _row_start_offset(row)
        if row_start is None:
            continue
        row_end = _row_end_offset(row, row_start)
        compact = _compact_context_row(row)
        if row_end <= start:
            preceding.append(compact)
            if len(preceding) > before:
                preceding = preceding[-before:]
            continue
        if row_start >= end:
            break
        overlapping.append(compact)
        if len(overlapping) >= limit:
            break
    return (preceding + overlapping)[:limit]


def _row_start_offset(row: dict[str, object]) -> int | None:
    value = (
        row.get("diff_start_offset")
        if isinstance(row.get("diff_start_offset"), int)
        else (row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"))
    )
    return value if isinstance(value, int) else None


def _row_end_offset(row: dict[str, object], row_start: int) -> int:
    diff_end = row.get("diff_end_offset")
    if isinstance(diff_end, int) and diff_end > row_start:
        return diff_end
    end = row.get("end_offset")
    if isinstance(end, int) and end > row_start:
        diff_start = row.get("diff_start_offset")
        original_start = row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr")
        if isinstance(diff_start, int) and isinstance(original_start, int):
            return diff_start + (end - original_start)
        return end
    raw_bytes = row.get("bytes")
    if isinstance(raw_bytes, str) and len(raw_bytes) >= 2:
        return row_start + max(1, len(raw_bytes) // 2)
    return row_start + 1


def _compact_context_row(row: dict[str, object]) -> dict[str, object]:
    keys = (
        "row_index",
        "kind",
        "text",
        "section_index",
        "start_offset",
        "end_offset",
        "diff_start_offset",
        "diff_end_offset",
        "addr",
        "bytes",
        "opcode_or_directive",
        "operand_text",
        "data_class",
    )
    return {
        key: row[key]
        for key in keys
        if key in row and isinstance(row.get(key), (str, int, float, bool))
    }


def _variants_by_target_id() -> dict[str, dict[str, Any]]:
    by_target: dict[str, dict[str, Any]] = {}
    for group in read_variants():
        targets = group.get("targets")
        if not isinstance(targets, list):
            continue
        for target in targets:
            if isinstance(target, dict) and isinstance(target.get("target_id"), str):
                by_target[target["target_id"]] = group
    return by_target


def _variant_group_for_pair(left_target_id: str, right_target_id: str) -> dict[str, Any] | None:
    for group in read_variants():
        targets = group.get("targets")
        if not isinstance(targets, list):
            continue
        target_ids = {
            str(target.get("target_id"))
            for target in targets
            if isinstance(target, dict) and isinstance(target.get("target_id"), str)
        }
        if left_target_id in target_ids and right_target_id in target_ids:
            return group
    return None


def _is_disk_platform(platform: str) -> bool:
    return platform in {"amiga-disk", "atari-st-disk"}


def _disk_manifest_row(disk_target: dict[str, Any]) -> dict[str, Any]:
    source_id = disk_target.get("source_id")
    if not isinstance(source_id, str):
        raise FileNotFoundError(f"Corpus disk target {disk_target.get('id')} has no source id")
    for row in _read_jsonl_cached(DISK_MANIFEST_PATH):
        if row.get("id") == source_id:
            return row
    raise FileNotFoundError(f"Missing disk corpus row {source_id}")


def _disk_entries(disk_row: dict[str, Any]) -> list[dict[str, Any]]:
    expect = disk_row.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    entries = inspect.get("entries") if isinstance(inspect, dict) else None
    return [entry for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []


def _disk_entry_content_payload(disk_row: dict[str, Any], entry: dict[str, Any]) -> dict[str, object]:
    try:
        origin = disk_row.get("origin")
        if not isinstance(origin, dict):
            raise RuntimeError("Corpus disk row has no origin")
        image_bytes = load_disk_image_bytes(origin)
        data = reconstruct_file_bytes(str(disk_row.get("platform")), entry, image_bytes)
    except Exception as exc:
        return disk_browser.content_error_payload(str(exc), disk_browser.entry_size(entry))
    return disk_browser.content_payload_from_bytes(data)


def _disk_entry_target_index(disk_target: dict[str, Any]) -> dict[str, str]:
    disk_sha256 = disk_target.get("sha256")
    if not isinstance(disk_sha256, str):
        return {}
    file_rows = {
        str(row.get("id")): row
        for row in _read_jsonl_cached(FILE_MANIFEST_PATH)
        if isinstance(row.get("id"), str)
    }
    result: dict[str, str] = {}
    for target in read_manifest():
        source_id = target.get("source_id")
        file_row = file_rows.get(source_id) if isinstance(source_id, str) else None
        if file_row is None or file_row.get("disk_sha256") != disk_sha256:
            continue
        origin = file_row.get("origin")
        entry_path = origin.get("in_image_path") if isinstance(origin, dict) else None
        target_id = target.get("id")
        if isinstance(entry_path, str) and isinstance(target_id, str):
            result[disk_browser.normalise_path(entry_path).lower()] = target_id
    return result


def _import_target_for_mode(target: dict[str, Any], *, mode: str) -> dict[str, Any]:
    platform = str(target.get("platform"))
    if mode == "target":
        if platform != "amiga-hunk":
            raise ValueError(f"Corpus target import is not supported for platform {platform}")
        return target
    if mode == "disk":
        if platform == "amiga-disk":
            return target
        if platform == "amiga-hunk":
            disk_target = _parent_disk_target_row(target)
            if disk_target is None:
                raise ValueError(f"Corpus target {target.get('id')} has no indexed disk container")
            return disk_target
        raise ValueError(f"Corpus disk import is not supported for platform {platform}")
    raise ValueError(f"Unsupported corpus import mode: {mode}")


def _corpus_project_origin(
    *,
    requested_target: dict[str, Any],
    imported_target: dict[str, Any],
    mode: str,
) -> dict[str, object]:
    origin = imported_target.get("origin")
    requested_origin = requested_target.get("origin")
    assert isinstance(origin, dict)
    result: dict[str, object] = {
        "kind": "corpus_disk" if str(imported_target.get("platform")) == "amiga-disk" else "corpus_file",
        "corpus_target_id": str(imported_target.get("id")),
        "source_id": str(imported_target.get("source_id")),
        "source_manifest": str(imported_target.get("source_manifest")),
        "platform": str(imported_target.get("platform")),
        "size": int(imported_target.get("size")) if isinstance(imported_target.get("size"), int) else None,
        "sha256": str(imported_target.get("sha256")) if isinstance(imported_target.get("sha256"), str) else None,
    }
    for key in ("display_name", "source_relpath", "container_relpath", "member_name", "in_image_path"):
        value = origin.get(key)
        if isinstance(value, str) and value:
            result[key] = value
    if requested_target.get("id") != imported_target.get("id"):
        result["requested_corpus_target_id"] = str(requested_target.get("id"))
        if isinstance(requested_origin, dict):
            requested_name = (
                requested_origin.get("in_image_path")
                or requested_origin.get("member_name")
                or requested_origin.get("display_name")
            )
            if isinstance(requested_name, str) and requested_name:
                result["requested_display_name"] = requested_name
    result["import_mode"] = mode
    return {key: value for key, value in result.items() if value is not None}


def _parent_disk_target_row(target: dict[str, Any]) -> dict[str, Any] | None:
    file_row = _file_manifest_row(target)
    if file_row is None:
        return None
    disk_sha256 = file_row.get("disk_sha256")
    if not isinstance(disk_sha256, str):
        return None
    for row in read_manifest():
        if _is_disk_platform(str(row.get("platform"))) and row.get("sha256") == disk_sha256:
            return row
    return None


def _file_manifest_row(target: dict[str, Any]) -> dict[str, Any] | None:
    source_id = target.get("source_id")
    if not isinstance(source_id, str):
        return None
    for row in _read_jsonl_cached(FILE_MANIFEST_PATH):
        if row.get("id") == source_id:
            return row
    return None


def _target_source_context(target: dict[str, Any]) -> dict[str, object]:
    origin = target.get("origin")
    if not isinstance(origin, dict):
        return {}
    result: dict[str, object] = {}
    target_name = origin.get("in_image_path") or origin.get("member_name") or origin.get("display_name")
    if isinstance(target_name, str) and target_name:
        result["target_name"] = target_name
    disk_target = None if _is_disk_platform(str(target.get("platform"))) else _parent_disk_target_row(target)
    if disk_target is not None and isinstance(disk_target.get("id"), str):
        result["disk_target_id"] = disk_target["id"]
    disk_origin = disk_target.get("origin") if disk_target is not None else origin
    if isinstance(disk_origin, dict):
        disk_name = disk_origin.get("member_name") or disk_origin.get("display_name")
        if isinstance(disk_name, str) and disk_name:
            result["disk_name"] = disk_name
    return result


def _project_coverage_for_target(
    target: dict[str, Any],
    projects: list[dict[str, object]],
) -> dict[str, object]:
    target_id = str(target.get("id"))
    exact_project = _project_covering_target(projects, target)
    disk_target = target if target.get("platform") == "amiga-disk" else _parent_disk_target_row(target)
    disk_target_id = str(disk_target.get("id")) if disk_target is not None else None
    disk_project = _project_covering_target(projects, disk_target) if disk_target is not None else None
    modes: list[dict[str, object]] = []
    if target.get("platform") == "amiga-hunk":
        modes.append({
            "mode": "target",
            "label": "Promote file" if exact_project is None else "File in Projects",
            "available": exact_project is None,
            "covered_project_id": exact_project,
        })
    if disk_target_id is not None:
        disk_label = "Promote disk" if target.get("platform") == "amiga-disk" else "Promote containing disk"
        modes.append({
            "mode": "disk",
            "label": disk_label if disk_project is None else "Disk in Projects",
            "available": disk_project is None,
            "covered_project_id": disk_project,
            "corpus_target_id": disk_target_id,
        })
    return {
        "target_project_id": exact_project,
        "disk_project_id": disk_project,
        "parent_disk_target_id": disk_target_id,
        "import_modes": modes,
    }


def _project_covering_target(projects: list[dict[str, object]], target: dict[str, Any] | None) -> str | None:
    if target is None:
        return None
    target_id = target.get("id")
    target_sha256 = target.get("sha256")
    target_size = target.get("size")
    target_platform = target.get("platform")
    for project in projects:
        origin = project.get("origin")
        if not isinstance(origin, dict):
            continue
        if isinstance(target_id, str) and origin.get("corpus_target_id") == target_id:
            project_id = project.get("id")
            return str(project_id) if isinstance(project_id, str) else None
        if (
            isinstance(target_sha256, str)
            and origin.get("sha256") == target_sha256
            and (not isinstance(target_size, int) or origin.get("size") == target_size)
            and (not isinstance(target_platform, str) or origin.get("platform") == target_platform)
        ):
            project_id = project.get("id")
            return str(project_id) if isinstance(project_id, str) else None
    return None


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
